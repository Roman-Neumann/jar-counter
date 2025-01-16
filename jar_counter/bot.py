from __future__ import annotations

import logging
import re
from typing import Any, Callable

import discord as dc

from . import change, reuse, sync
from .data import (
    ArgData,
    ConfigData,
    GuildData,
    Guilds,
    JarData,
    Jars,
    Visibility,
)
from .decorators import (
    confirmation,
    has_jar,
    has_no_jar,
    is_moderator,
    is_not_on_cooldown,
    is_not_own_jar,
)
from .errors import GuildNotSetupError, NeedsSyncError, get_error_message


# ruff: noqa: D417 <- docstring only documents the interface discord-side


class _ErrorMessageCommandTree(dc.app_commands.CommandTree):
    async def on_error(
        self,
        intr: dc.Interaction,
        exc: dc.app_commands.AppCommandError,
    ) -> None:
        await intr.response.send_message(get_error_message(exc), ephemeral=True)


class _JarBot(dc.Client):
    def __init__(self) -> None:
        super().__init__(intents=dc.Intents(message_content=True, guilds=True))
        self.data = Guilds()
        self._command_tree = _ErrorMessageCommandTree(self)
        self._jar_command_group = dc.app_commands.Group(
            name="jar",
            description="Primary command group.",
            guild_only=True,
        )
        self._command_tree.add_command(self._jar_command_group)

        # init deferred until _JarBot.prepare_run
        self._sync_and_exit: bool
        self._token: str
        self.host_contact: str

    def prepare_run(self, args: ArgData, config: ConfigData) -> None:
        will_be_synced = args.sync
        if sync.needs_sync() and not will_be_synced:
            raise NeedsSyncError

        self._sync_and_exit = args.sync
        self._token = config.token
        self.host_contact = config.host_contact

    def run(self) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().run(self._token)

    def command(self, callback: Callable) -> dc.app_commands.Command:
        return self._jar_command_group.command(name=callback.__name__[1:])(
            callback,
        )

    async def sync_commands(
        self,
        *,
        caller: dc.User | dc.Member | None,
    ) -> None:
        logger = logging.getLogger("discord.jar.bot")
        if caller:
            logger.info("start sync called by %s (%d)", caller, caller.id)
        else:
            logger.info("start sync")

        await self._command_tree.sync()
        logger.info("finished sync")
        sync.mark_synced()

    async def setup_hook(self) -> None:
        if self._sync_and_exit:
            await self.sync_commands(caller=None)
            await self.close()  # will exit

        self.data.write_loop.start()

    async def respond(
        self,
        intr: dc.Interaction,
        content: str,
        member: dc.Member,
    ) -> None:
        name = (
            member.mention
            if self.data[intr].mentions_use
            else f"**{member.display_name}**"
        )
        content = content.replace("%@", name, 1)

        ephemeral = self.data[intr].responses_visibility == Visibility.hidden
        await intr.response.send_message(content, ephemeral=ephemeral)


bot = _JarBot()


@bot.command
async def _help(intr: dc.Interaction) -> None:
    """Show a short command overview and description."""

    def get_doc(command: Any) -> str:
        if not (doc := command.callback.__doc__):
            raise ValueError
        return doc[: doc.find(".")].lower()

    content = f"""\
This bot manages a counter for a server member.

The following commands are available:
- `/jar help`: {get_doc(_help)}
- `/jar contact`: {get_doc(_contact)}
- `/jar sync` `[MOD]`: {get_doc(_sync)}
- `/jar setup` `[MOD*]`: {get_doc(_setup)}
- `/jar create` `[MOD]`: {get_doc(_create)}
- `/jar edit` `[MOD]`: {get_doc(_edit)}
- `/jar add` `[COOLDOWN]` `[REUSE]`: {get_doc(_add)}
- `/jar subtract` `[NOT-SELF]` `[COOLDOWN]` `[REUSE]`: {get_doc(_subtract)}
- `/jar show` `[REUSE]`: {get_doc(_show)}
- `/jar empty` `[MOD]` `[NOT-SELF]` `[CONFIRM]`: {get_doc(_empty)}
- `/jar delete` `[MOD]` `[NOT-SELF]` `[CONFIRM]`: {get_doc(_delete)}

Some commands are paired with modifiers:
- `[MOD]`: requires moderator role to be called
- `[MOD*]`: requires moderator role only if a valid role is known
- `[NOT-SELF]`: may not be called for your own jar
- `[COOLDOWN]`: has a short (server-wide) cooldown after each call
- `[REUSE]`: not specifying a server member will reuse the last used one
- `[CONFIRM]`: requires confirmation

If the bot has just been invited to the server, you must specify a moderator \
role using `/jar setup`. Additionally the response visibility and mention-use \
can be configured in the same command. These options will affects responses to \
all commands with the exception of `help`, `contact`, `sync` and `setup`.
"""
    await intr.response.send_message(content, ephemeral=True)


@bot.command
async def _contact(intr: dc.Interaction) -> None:
    """Show contact information."""
    content = (
        "For bug reports or feature requests open an issue at "
        "https://github.com/Roman-Neumann/jar-counter"
    )
    if bot.host_contact:
        content += (
            f"\nFor questions related to hosting, contact:\n{bot.host_contact}"
        )
    await intr.response.send_message(content, ephemeral=True)


@bot.command
@is_not_on_cooldown(seconds=60 * 5)
@is_moderator()
async def _sync(intr: dc.Interaction) -> None:
    """Sync command interface. Call only if instructed by an error message."""
    await intr.response.send_message("Start Syncing.", ephemeral=True)
    await bot.sync_commands(caller=intr.user)
    await intr.followup.send(
        "Finished syncing. Try calling the offending command again. May take "
        "up to one hour for the updates to take effect.",
        ephemeral=True,
    )


class _SetupDummyData:
    moderator_role_id = None
    responses_visibility = None
    mentions_use = None


def _setup_guild(
    intr: dc.Interaction,
    moderator: dc.Role,
    responses: Visibility,
    mentions: bool,  # noqa: FBT001
) -> _SetupDummyData:
    guild_data = GuildData(
        Jars(),
        moderator.id,
        moderator.name,
        responses,
        mentions,
    )
    bot.data[intr] = guild_data

    return _SetupDummyData()


@bot.command
@is_moderator(allow_setup=True)
async def _setup(
    intr: dc.Interaction,
    moderator: dc.Role | None = None,
    responses: Visibility | None = None,
    mentions: bool | None = None,
) -> None:
    """Configure different options of the bot.

    Args:
        moderator: the role to use to prevent misuse on privileged commands
        responses: visible = public responses always visible; hidden =
            responses visible to caller only
        mentions: True = @-mention jar owner in responses; False = refer to jar
            owner with display name

    """
    try:
        data = bot.data[intr]
        if moderator:
            data.moderator_role_name = moderator.name

    except GuildNotSetupError:
        if not moderator:
            raise
        responses = responses or Visibility.visible
        mentions = mentions if mentions is not None else True
        data = _setup_guild(intr, moderator, responses, mentions)

    mod_id = moderator.id if moderator else None
    mod_change = change.document_change(data, "moderator_role_id", mod_id)
    res_change = change.document_change(data, "responses_visibility", responses)
    ment_change = change.document_change(data, "mentions_use", mentions)
    if mod_change:
        mod_change.name = "moderator role"

    content = change.combine_message(mod_change, res_change, ment_change)
    content = re.sub(r"(\d+)", r"<@&\1>", content)  # format ids to @-mentions
    await intr.response.send_message(content, ephemeral=True)

    if mod_change or res_change or ment_change:
        bot.data[intr].dirty = True


@bot.command
@has_no_jar()
@is_moderator()
async def _create(
    intr: dc.Interaction,
    member: dc.Member,
    currency: str,
    suffix: bool,  # noqa: FBT001 <- kw-only arg would break command interface
) -> None:
    """Create a new jar for a server member.

    Args:
        member: the owner of the jar
        currency: the currency of the jar; can be any text like emojis
        suffix: automatically append an 's' to the currency when appropriate
            e.g. '1 coin', '2 coins'

    """
    jar = JarData(currency, suffix)
    bot.data[intr].jars[member] = jar

    await bot.respond(intr, f"Created a jar for %@ filled with {jar}!", member)

    reuse.set_member(member)
    bot.data[intr].dirty = True


@bot.command
@has_jar()
@is_moderator()
async def _edit(
    intr: dc.Interaction,
    member: dc.Member,
    currency: str | None = None,
    suffix: bool | None = None,
) -> None:
    """Edit the currency and suffix of a jar.

    Args:
        member: the owner of the jar
        currency: the currency of the jar; can be any text like emojis
        suffix: automatically append an 's' to the currency when appropriate
            e.g. '1 coin', '2 coins'

    """
    jar = bot.data[intr].jars[member]
    cur_change = change.document_change(jar, "currency", currency)
    suf_change = change.document_change(jar, "suffix", suffix)

    await bot.respond(
        intr,
        change.combine_message(cur_change, suf_change, prefix="Jar of %@"),
        member,
    )

    reuse.set_member(member)
    if cur_change or suf_change:
        bot.data[intr].dirty = True


async def _change_jar_counter(
    intr: dc.Interaction,
    amount: int,
    member: dc.Member | None,
    *,
    should_subtract: bool,
) -> None:
    member = member or reuse.get_member()
    jar = bot.data[intr].jars[member]

    if should_subtract:
        amount = min(amount, jar.count)
        jar.count -= amount
    else:
        jar.count += amount

    change = JarData(jar.currency, jar.suffix, count=amount)
    if should_subtract:
        msg = f"Removed {change} from the jar of %@!"
    else:
        msg = f"Added {change} to the jar of %@!"
    await bot.respond(intr, msg, member)

    reuse.set_member(member)
    if amount > 0:
        bot.data[intr].dirty = True


@bot.command
@is_not_on_cooldown()
@has_jar()
async def _add(
    intr: dc.Interaction,
    amount: dc.app_commands.Range[int, 1, None] = 1,
    member: dc.Member | None = None,
) -> None:
    """Add some amount to a jar.

    Args:
        amount: the amount to add; or 1 if empty
        member: the owner of the jar; or if empty reuse the last used one

    """
    await _change_jar_counter(intr, amount, member, should_subtract=False)


@bot.command
@is_not_on_cooldown()
@is_not_own_jar()
@has_jar()
async def _subtract(
    intr: dc.Interaction,
    amount: dc.app_commands.Range[int, 1, None] = 1,
    member: dc.Member | None = None,
) -> None:
    """Remove some amount from a jar.

    Args:
        amount: the amount to subtract; or 1 if empty
        member: the owner of the jar; or if empty reuse the last used one

    """
    await _change_jar_counter(intr, amount, member, should_subtract=True)


@bot.command
@has_jar()
async def _show(intr: dc.Interaction, member: dc.Member | None = None) -> None:
    """Show the contents of a jar.

    Args:
        member: the owner of the jar; or if empty reuse the last used one

    """
    member = member or reuse.get_member()
    jar = bot.data[intr].jars[member]
    await bot.respond(intr, f"%@ has {jar} in the jar!", member)

    reuse.set_member(member)


@bot.command
@confirmation(lambda member: f"empty the jar of {member.mention}")
@is_not_own_jar()
@has_jar()
@is_moderator()
async def _empty(intr: dc.Interaction, member: dc.Member) -> None:
    """Reset the counter of a jar to zero.

    Args:
        member: the owner of the jar

    """
    jar = bot.data[intr].jars[member]
    await bot.respond(intr, f"Emptied the jar of %@ by {jar}!", member)
    change = jar.count
    jar.count = 0

    reuse.set_member(member)
    if change > 0:
        bot.data[intr].dirty = True


@bot.command
@confirmation(lambda member: f"delete the jar of {member.mention}")
@is_not_own_jar()
@has_jar()
@is_moderator()
async def _delete(intr: dc.Interaction, member: dc.Member) -> None:
    """Delete the jar of a member.

    Args:
        member: the owner of the jar

    """
    jar = bot.data[intr].jars[member]
    del bot.data[intr].jars[member]
    await bot.respond(intr, f"Deleted the jar of %@ with {jar}!", member)

    reuse.set_member(None)
    bot.data[intr].dirty = True
