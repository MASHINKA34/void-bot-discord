from __future__ import annotations

import datetime as dt
import logging
import random

import disnake
from disnake.ext import commands

from bot.client import VoidBot
from bot.config import DATA_DIR

logger = logging.getLogger(__name__)


def _load_gifs() -> tuple[str, ...]:
    path = DATA_DIR / "welcome_gifs.txt"
    if not path.is_file():
        return ()
    lines = path.read_text(encoding="utf-8").splitlines()
    return tuple(line.strip() for line in lines if line.strip())


class Greetings(commands.Cog):
    def __init__(self, bot: VoidBot) -> None:
        self.bot = bot
        self.gifs = _load_gifs()

    def _random_gif(self) -> str | None:
        return random.choice(self.gifs) if self.gifs else None

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        await self._assign_autorole(member)
        await self._announce(member)

    async def _assign_autorole(self, member: disnake.Member) -> None:
        role_id = self.bot.settings.autorole_id
        if role_id is None:
            return
        role = member.guild.get_role(role_id)
        if role is None:
            logger.warning("Роль автовыдачи %s не найдена на сервере %s", role_id, member.guild.id)
            return
        try:
            await member.add_roles(role, reason="Автовыдача роли новому участнику")
        except disnake.Forbidden:
            logger.warning("Нет прав выдать роль %s на сервере %s", role_id, member.guild.id)

    async def _announce(self, member: disnake.Member) -> None:
        channel_id = self.bot.settings.welcome_channel_id
        if channel_id is None:
            return
        channel = member.guild.get_channel(channel_id)
        if not isinstance(channel, disnake.TextChannel):
            logger.warning("Канал приветствий %s не найден", channel_id)
            return

        embed = disnake.Embed(
            title="Новый участник!?",
            description=member.mention,
            color=disnake.Colour.random(),
            timestamp=dt.datetime.now(dt.timezone.utc),
        )
        embed.set_author(name="Сюда делаем спам атаку обязательно!!!", icon_url=self._random_gif())
        embed.set_footer(text="Время прибытия", icon_url=self._random_gif())

        try:
            await channel.send(embed=embed)
        except disnake.Forbidden:
            logger.warning("Нет прав писать в канал приветствий %s", channel_id)


def setup(bot: VoidBot) -> None:
    bot.add_cog(Greetings(bot))
