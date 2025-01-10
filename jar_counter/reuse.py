from __future__ import annotations

from typing import TYPE_CHECKING

from .errors import NoReuseMemberError


if TYPE_CHECKING:
    import discord as dc


_previous: dc.Member | None = None


def get_member() -> dc.Member:
    if not _previous:
        raise NoReuseMemberError
    return _previous


def set_member(value: dc.Member | None) -> None:
    global _previous  # noqa: PLW0603
    _previous = value
