import dataclasses
import enum

import discord as dc
from discord.ext import tasks

from .errors import GuildNotSetupError


@dataclasses.dataclass
class ArgData:
    sync: bool


@dataclasses.dataclass
class ConfigData:
    token: str
    host_contact: str


class Visibility(str, enum.Enum):
    hidden = "hidden"
    visible = "visible"

    def __str__(self) -> str:
        return self.value


@dataclasses.dataclass
class JarData:
    currency: str
    suffix: bool
    count: int = 0

    def __str__(self) -> str:
        s = "s" if self.suffix and self.count != 1 else ""
        return f"**{self.count} {self.currency}{s}**"


class Jars(dict):  # inherit from dict for simple serialization
    def __getitem__(self, member: dc.Member) -> JarData:
        return super().__getitem__(member.id)

    def __setitem__(self, member: dc.Member, jar: JarData) -> None:
        return super().__setitem__(member.id, jar)

    def __delitem__(self, member: dc.Member) -> None:
        return super().__delitem__(member.id)

    def __contains__(self, member: object) -> bool:
        if not isinstance(member, dc.Member):
            raise TypeError
        return super().__contains__(member.id)


@dataclasses.dataclass
class GuildData:
    jars: Jars
    moderator_role_id: int
    moderator_role_name: str  # store for error message in case role is changed
    responses_visibility: Visibility
    mentions_use: bool

    def __post_init__(self) -> None:
        self.dirty = False  # exclude from written data


class Guilds:
    from . import jar_io  # prevent circular import

    def __init__(self) -> None:
        self._guilds: dict[int, GuildData] = {}  # lazy load

    def __getitem__(self, intr: dc.Interaction) -> GuildData:
        id_ = _assert_guild_id(intr)
        if id_ not in self._guilds:
            try:
                self._guilds[id_] = Guilds.jar_io.read_guild(id_)
            except FileNotFoundError as exc:
                raise GuildNotSetupError from exc
        return self._guilds[id_]

    def __setitem__(self, intr: dc.Interaction, data: GuildData) -> None:
        id_ = _assert_guild_id(intr)
        self._guilds[id_] = data

    @tasks.loop(seconds=10)
    async def write_loop(self) -> None:
        for id_, data in self._guilds.items():
            if data.dirty:
                Guilds.jar_io.write_guild(id_, data)
                data.dirty = False


def _assert_guild_id(intr: dc.Interaction) -> int:
    if not intr.guild_id:
        raise dc.app_commands.NoPrivateMessage
    return intr.guild_id
