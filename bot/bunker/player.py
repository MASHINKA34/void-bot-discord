from __future__ import annotations

import random

import disnake

from bot.bunker.character import CHARACTER_POOL, GENDER_TITLE, Character


class Player:
    __slots__ = ("user", "alive", "characters")

    def __init__(self, user: disnake.User | disnake.Member) -> None:
        self.user = user
        self.alive = True
        self.characters: dict[str, Character] = {
            title: Character.random(title) for title in CHARACTER_POOL
        }

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def name(self) -> str:
        return self.user.display_name

    @property
    def revealed_count(self) -> int:
        return sum(character.revealed for character in self.characters.values())

    def kick(self) -> None:
        self.alive = False

    def reveal(self, title: str) -> Character | None:
        if not self.alive:
            return None
        character = self.characters.get(title)
        if character is None or character.revealed:
            return None
        character.reveal()
        return character

    def reveal_random(self) -> Character | None:
        if not self.alive:
            return None
        gender = self.characters.get(GENDER_TITLE)
        if gender is not None and not gender.revealed:
            gender.reveal()
            return gender
        hidden = [c for c in self.characters.values() if not c.revealed]
        if not hidden:
            return None
        character = random.choice(hidden)
        character.reveal()
        return character

    def card(self, full: bool = False) -> str:
        if not self.alive:
            return f"{self.name} — __**мёртв**__"
        rows = [str(c) for c in self.characters.values() if full or c.revealed]
        return "\n".join([self.name, *rows])

    def __hash__(self) -> int:
        return hash(self.user.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Player) and self.user.id == other.user.id

    def __str__(self) -> str:
        return self.card()
