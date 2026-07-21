from __future__ import annotations

import logging
import re

import disnake
from disnake.ext import commands

from bot.client import VoidBot
from bot.config import DATA_DIR

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _load_banned_words() -> frozenset[str]:
    path = DATA_DIR / "banned_words.txt"
    if not path.is_file():
        return frozenset()
    return frozenset(
        word.strip().lower() for word in path.read_text(encoding="utf-8").split() if word.strip()
    )


class Moderation(commands.Cog):
    def __init__(self, bot: VoidBot) -> None:
        self.bot = bot
        self.banned_words = _load_banned_words()

    def _contains_banned(self, content: str) -> bool:
        if not self.banned_words:
            return False
        return any(word.lower() in self.banned_words for word in _WORD_RE.findall(content))

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        if not self._contains_banned(message.content):
            return

        try:
            await message.delete()
        except disnake.NotFound:
            return
        except disnake.Forbidden:
            logger.warning("Нет прав удалять сообщения в канале %s", message.channel.id)
            return

        await message.channel.send(f"{message.author.mention} нормально общайся!")


def setup(bot: VoidBot) -> None:
    bot.add_cog(Moderation(bot))
