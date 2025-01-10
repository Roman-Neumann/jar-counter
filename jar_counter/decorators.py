import functools
from typing import Any, Callable

import discord as dc

from . import reuse
from .errors import (
    DuplicateJarError,
    GuildNotSetupError,
    NoJarError,
    NoSuchRoleError,
    OwnJarAccessError,
)


def is_moderator(*, allow_setup: bool = False) -> Callable:
    def predicate(intr: dc.Interaction) -> bool:
        if isinstance(intr.user, dc.User) or not intr.guild:
            raise dc.app_commands.NoPrivateMessage

        try:
            data = _get_guild_data(intr)
        except GuildNotSetupError:
            if allow_setup:
                return True
            raise

        mod_role = dc.utils.get(intr.guild.roles, id=data.moderator_role_id)
        if not mod_role:
            if allow_setup:
                return True
            raise NoSuchRoleError(data.moderator_role_name)

        if intr.user.get_role(mod_role.id) is not None:
            return True
        raise dc.app_commands.MissingRole(mod_role.mention)

    return dc.app_commands.check(predicate)


def has_jar() -> Callable:
    def predicate(intr: dc.Interaction) -> bool:
        data = _get_guild_data(intr)
        if (member := intr.namespace.member) is None:
            member = reuse.get_member()
        if member not in data.jars:
            raise NoJarError
        return True

    return dc.app_commands.check(predicate)


def has_no_jar() -> Callable:
    def predicate(intr: dc.Interaction) -> bool:
        data = _get_guild_data(intr)
        if (member := intr.namespace.member) is None:
            member = reuse.get_member()
        if member in data.jars:
            raise DuplicateJarError
        return True

    return dc.app_commands.check(predicate)


def is_not_own_jar() -> Callable:
    def predicate(intr: dc.Interaction) -> bool:
        if (member := intr.namespace.member) is None:
            member = reuse.get_member()
        if intr.user.id == member.id:
            raise OwnJarAccessError
        return True

    return dc.app_commands.check(predicate)


def is_not_on_cooldown(*, seconds: float = 3.0) -> Callable:
    return dc.app_commands.checks.cooldown(
        rate=1,
        per=seconds,
        key=lambda intr: intr.guild_id,
    )


def confirmation(describe_action: Callable) -> Callable:
    def decorator(callback: Callable) -> Callable:
        @functools.wraps(callback)
        async def wrapper(intr: dc.Interaction, **kwargs: Any) -> None:
            await intr.response.send_message(
                f"Are you sure you want to {describe_action(**kwargs)}?",
                ephemeral=True,
                view=_ConfirmView(intr, callback, **kwargs),
            )

        return wrapper

    return decorator


def _get_guild_data(intr: dc.Interaction) -> Any:
    from .bot import bot  # prevent circular import

    return bot.data[intr]


class _ConfirmView(dc.ui.View):
    def __init__(
        self,
        outer_intr: dc.Interaction,
        on_confirm: Callable,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self._outer_intr = outer_intr
        self._on_confirm = on_confirm
        self._kwargs = kwargs

    @dc.ui.button(label="Confirm", style=dc.ButtonStyle.primary)
    async def confirm(
        self,
        inner_intr: dc.Interaction,
        _: dc.ui.Button,
    ) -> None:
        if self._outer_intr:
            await self._outer_intr.edit_original_response(view=None)
        await self._on_confirm(inner_intr, **self._kwargs)
        self._cleanup()

    @dc.ui.button(label="Cancel", style=dc.ButtonStyle.secondary)
    async def cancel(self, intr: dc.Interaction, _: dc.ui.Button) -> None:
        if self._outer_intr:
            await self._outer_intr.delete_original_response()
        await intr.response.send_message(
            "Canceled.",
            ephemeral=True,
            delete_after=2,
        )
        self._cleanup()

    def _cleanup(self) -> None:
        self._outer_intr = None  # remove strong ref; may not be necessary
        self.stop()
