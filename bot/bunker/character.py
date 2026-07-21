from __future__ import annotations

import json
import random
from typing import Final

from bot.config import DATA_DIR

GENDER_TITLE: Final = "║⚤ Пол"
BAGGAGE_TITLE: Final = "║🎒 Багаж"
EXTRA_BAGGAGE_TITLE: Final = "║🎒 Доп. багаж"


def _load_pool() -> dict[str, list[str]]:
    raw: dict[str, list[str]] = json.loads(
        (DATA_DIR / "characters.json").read_text(encoding="utf-8")
    )
    if BAGGAGE_TITLE in raw:
        raw[EXTRA_BAGGAGE_TITLE] = list(raw[BAGGAGE_TITLE])
    return raw


CHARACTER_POOL: Final[dict[str, list[str]]] = _load_pool()


class Character:
    __slots__ = ("title", "value", "revealed")

    def __init__(self, title: str, value: str) -> None:
        self.title = title
        self.value = value
        self.revealed = False

    @classmethod
    def random(cls, title: str) -> "Character":
        return cls(title, random.choice(CHARACTER_POOL[title]))

    def reveal(self) -> None:
        self.revealed = True

    def __str__(self) -> str:
        return f"{self.title}: {self.value}"
