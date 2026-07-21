from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Final

import disnake

from bot.config import DATA_DIR, IMAGES_DIR


@dataclass(frozen=True, slots=True)
class Scenario:
    title: str
    description: str
    color: int
    image: str | None = None

    def to_message(self) -> tuple[disnake.Embed, disnake.File | None]:
        embed = disnake.Embed(
            title=self.title,
            description=self.description,
            color=self.color,
        )
        if not self.image:
            return embed, None

        path = IMAGES_DIR / self.image
        if not path.is_file():
            return embed, None

        file = disnake.File(path, filename=path.name)
        embed.set_image(url=f"attachment://{path.name}")
        return embed, file


def _load_scenarios() -> tuple[Scenario, ...]:
    raw = json.loads((DATA_DIR / "scenarios.json").read_text(encoding="utf-8"))
    return tuple(
        Scenario(
            title=item["title"],
            description=item["description"],
            color=int(str(item.get("color", "#2F3136")).lstrip("#"), 16),
            image=item.get("image"),
        )
        for item in raw
    )


SCENARIOS: Final[tuple[Scenario, ...]] = _load_scenarios()


def random_scenario() -> Scenario:
    return random.choice(SCENARIOS)
