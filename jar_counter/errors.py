from __future__ import annotations

import logging

from discord.app_commands import (
    AppCommandError,
    CheckFailure,
    CommandInvokeError,
    CommandOnCooldown,
    CommandSignatureMismatch,
    MissingRole,
    NoPrivateMessage,
)


class NeedsSyncError(RuntimeError):
    pass


class GuildNotSetupError(CheckFailure):
    pass


class NoSuchRoleError(CheckFailure):
    pass


class NoJarError(CheckFailure):
    pass


class DuplicateJarError(CheckFailure):
    pass


class OwnJarAccessError(CheckFailure):
    pass


class NoReuseMemberError(ValueError, CheckFailure):
    pass


def get_error_message(exc: AppCommandError) -> str:
    for error_subtype, get_message in _messages.items():
        if issubclass(type(exc), error_subtype):
            msg = get_message(exc)
            if msg:
                return msg

    logging.getLogger("discord.jar.error").exception(exc)
    return (
        "An unspecified error occurred. Please contact the bot author via "
        "`/jar contact`."
    )


def _get_command_invoke_error_message(
    exc: CommandInvokeError,
) -> str | None:
    if issubclass(type(exc), NoReuseMemberError):
        return _get_no_reuse_member_error_message()
    return None


def _get_no_private_message_message(_: NoPrivateMessage) -> str:
    return "This command may only be used in a server context."


def _get_missing_role_message(exc: MissingRole) -> str:
    return f"You need the {exc.missing_role} role to run this command."


def _get_command_on_cooldown_message(
    exc: CommandOnCooldown,
) -> str:
    return (
        f"This command is on cooldown. Try again after "
        f"{exc.retry_after:.2f} seconds."
    )


def _get_check_failure_message(exc: CheckFailure) -> str | None:
    messages = {
        GuildNotSetupError: (
            "The bot has not been setup properly. Use `/jar setup` and "
            "ensure a moderator role is passed."
        ),
        NoSuchRoleError: (
            f"A role with name `{exc}` is unknown. Maybe the "
            "previous role has been removed. Use `/jar setup` to set a new "
            "one."
        ),
        NoJarError: (
            "The specified member has no jar. Use `/jar create` to create one."
        ),
        DuplicateJarError: "The specified member already has a jar.",
        OwnJarAccessError: "This command may not be called for your own jar.",
        NoReuseMemberError: _get_no_reuse_member_error_message(),
    }

    for error_subtype, msg in messages.items():
        if issubclass(type(exc), error_subtype):
            return msg

    return None


def _get_no_reuse_member_error_message() -> str:
    return (
        "There is no reusable previous member available. Please "
        "explicitly specify a member and try again."
    )


def _get_command_signature_mismatch_message(
    exc: CommandSignatureMismatch,
) -> str:
    cmd_name = exc.command.qualified_name
    msg = f"Signature mismatch on the command `/{cmd_name}`. "

    if cmd_name == "jar sync":
        return (
            msg + "Contact your bot host and send them the contents of this "
            "message. https://github.com/Roman-Neumann/jar-counter"
            "#command-synchronization"
        )

    return msg + "Call `/jar sync` to fix the issue."


# Must be defined after function declarations.
_messages = {
    CommandInvokeError: _get_command_invoke_error_message,
    NoPrivateMessage: _get_no_private_message_message,
    MissingRole: _get_missing_role_message,
    CommandOnCooldown: _get_command_on_cooldown_message,
    # Due to inheritance hierarchy this must be inserted after (if present):
    # NoPrivateMessage, MissingRole, MissingAnyRole, MissingPermissions,
    # BotMissingPermissions, CommandOnCooldown
    CheckFailure: _get_check_failure_message,
    CommandSignatureMismatch: (_get_command_signature_mismatch_message),
}
