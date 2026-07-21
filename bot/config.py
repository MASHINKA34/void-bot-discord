from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DATA_DIR = PACKAGE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"


class ConfigError(RuntimeError):
    pass


def _get_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_int(name: str) -> int | None:
    raw = _get_str(name)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} должен быть числом, получено: {raw!r}") from exc


def _get_int_list(name: str) -> list[int]:
    raw = _get_str(name).replace(",", " ")
    try:
        return [int(part) for part in raw.split()]
    except ValueError as exc:
        raise ConfigError(f"{name} должен быть списком чисел, получено: {raw!r}") from exc


def _get_positive_int(name: str, default: int) -> int:
    value = _get_int(name)
    if value is None:
        return default
    if value <= 0:
        raise ConfigError(f"{name} должен быть больше нуля")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    token: str
    command_prefix: str
    test_guilds: list[int] | None
    welcome_channel_id: int | None
    autorole_id: int | None
    bunker_channel_name: str
    reveal_duration: int
    voting_duration: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(PROJECT_DIR / ".env")

        token = _get_str("DISCORD_TOKEN")
        if not token:
            raise ConfigError(
                "DISCORD_TOKEN не задан. Скопируйте .env.example в .env и укажите токен бота."
            )

        test_guilds = _get_int_list("TEST_GUILD_IDS")

        return cls(
            token=token,
            command_prefix=_get_str("COMMAND_PREFIX", "!"),
            test_guilds=test_guilds or None,
            welcome_channel_id=_get_int("WELCOME_CHANNEL_ID"),
            autorole_id=_get_int("AUTOROLE_ID"),
            bunker_channel_name=_get_str("BUNKER_CHANNEL_NAME", "🎮bunker-game"),
            reveal_duration=_get_positive_int("REVEAL_DURATION", 30),
            voting_duration=_get_positive_int("VOTING_DURATION", 30),
        )
