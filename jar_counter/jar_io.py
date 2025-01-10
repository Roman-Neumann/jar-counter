import argparse
import configparser
import dataclasses
import os
import json
from pathlib import Path

from .data import ArgData, ConfigData, GuildData, JarData, Jars


def read_args() -> ArgData:
    python = "py" if os.name == "nt" else "python3"  # "nt" is Windows
    parser = argparse.ArgumentParser(usage=f"{python} -m jar_counter [-h] [-s]")
    parser.add_argument(
        "-s",
        "--sync",
        action="store_true",
        help=("sync commands and exit"),
    )

    return ArgData(parser.parse_args().sync)


def read_config() -> ConfigData:
    parser = configparser.ConfigParser()
    parser.read("config.ini")

    token = parser["mandatory"]["token"]
    host_contact = parser["optional"]["contact"]
    return ConfigData(token, host_contact)


def read_guild(id_: int) -> GuildData:
    with _get_guild_path(id_).open() as file:
        json_dict = json.load(file)
        jars = Jars(
            {
                int(id_): JarData(**jar)
                for id_, jar in json_dict.pop("jars").items()
            },
        )
        return GuildData(jars, **json_dict)


def write_guild(id_: int, data: GuildData) -> None:
    with _get_guild_path(id_).open("w") as file:
        json.dump(
            dataclasses.asdict(data),
            file,
            indent=4,
        )


def _get_guild_path(id_: int) -> Path:
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir()

    return Path(data_dir, f"guild_{id_}.json")
