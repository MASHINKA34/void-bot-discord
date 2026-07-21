from __future__ import annotations

import datetime as dt
import logging
import random
from typing import Literal

import disnake
from disnake.ext import commands

from bot.client import VoidBot
from bot.config import DATA_DIR
from bot.storage import GuildConfig

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

    def _build_embed(self, member: disnake.Member) -> disnake.Embed:
        embed = disnake.Embed(
            title="Новый участник!?",
            description=member.mention,
            color=disnake.Colour.random(),
            timestamp=dt.datetime.now(dt.timezone.utc),
        )
        embed.set_author(name="Сюда делаем спам атаку обязательно!!!", icon_url=self._random_gif())
        embed.set_footer(text="Время прибытия", icon_url=self._random_gif())
        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        config = self.bot.guild_config.get(member.guild.id)
        await self._assign_autorole(member, config)
        await self._announce(member, config)

    async def _assign_autorole(self, member: disnake.Member, config: GuildConfig) -> None:
        if config.autorole_id is None:
            return
        role = member.guild.get_role(config.autorole_id)
        if role is None:
            logger.warning("Роль автовыдачи %s не найдена на сервере %s", config.autorole_id, member.guild.id)
            return
        try:
            await member.add_roles(role, reason="Автовыдача роли новому участнику")
        except disnake.Forbidden:
            logger.warning("Нет прав выдать роль %s на сервере %s", role.id, member.guild.id)

    async def _announce(self, member: disnake.Member, config: GuildConfig) -> None:
        if config.welcome_channel_id is None:
            return
        channel = member.guild.get_channel(config.welcome_channel_id)
        if not isinstance(channel, disnake.TextChannel):
            logger.warning("Канал приветствий %s не найден", config.welcome_channel_id)
            return
        try:
            await channel.send(embed=self._build_embed(member))
        except disnake.Forbidden:
            logger.warning("Нет прав писать в канал приветствий %s", channel.id)

    @commands.slash_command(
        name="welcome",
        description="Настройка приветствия новичков",
        default_member_permissions=disnake.Permissions(manage_guild=True),
        contexts=disnake.InteractionContextTypes(guild=True),
    )
    @commands.guild_only()
    async def welcome(self, inter: disnake.ApplicationCommandInteraction) -> None:
        pass

    @welcome.sub_command(name="show", description="Показать текущие настройки приветствия")
    async def welcome_show(self, inter: disnake.ApplicationCommandInteraction) -> None:
        config = self.bot.guild_config.get(inter.guild_id)
        channel = f"<#{config.welcome_channel_id}>" if config.welcome_channel_id else "не задан"
        role = f"<@&{config.autorole_id}>" if config.autorole_id else "не задана"
        source = (
            "настроено на этом сервере"
            if self.bot.guild_config.is_configured(inter.guild_id)
            else "значения по умолчанию из .env"
        )

        embed = disnake.Embed(title="Приветствие новичков", color=0x2F3136)
        embed.add_field(name="Канал", value=channel, inline=False)
        embed.add_field(name="Автовыдача роли", value=role, inline=False)
        embed.set_footer(text=source)
        await inter.response.send_message(embed=embed, ephemeral=True)

    @welcome.sub_command(name="channel", description="Выбрать канал для приветствий")
    async def welcome_channel(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(description="Канал, куда писать приветствие"),
    ) -> None:
        permissions = channel.permissions_for(inter.guild.me)
        if not (permissions.send_messages and permissions.embed_links):
            await inter.response.send_message(
                f"Мне не хватает прав в {channel.mention}: нужны «Отправлять сообщения» и «Встраивать ссылки»",
                ephemeral=True,
            )
            return

        await self.bot.guild_config.update(inter.guild_id, welcome_channel_id=channel.id)
        await inter.response.send_message(
            f"Приветствия будут приходить в {channel.mention}", ephemeral=True
        )

    @welcome.sub_command(name="role", description="Выбрать роль для автовыдачи новичкам")
    async def welcome_role(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role = commands.Param(description="Роль, которую получит новый участник"),
    ) -> None:
        me = inter.guild.me
        if not me.guild_permissions.manage_roles:
            await inter.response.send_message(
                "У меня нет права «Управление ролями»", ephemeral=True
            )
            return
        if role.is_default() or role.managed:
            await inter.response.send_message(
                "Эту роль нельзя выдать вручную", ephemeral=True
            )
            return
        if role >= me.top_role:
            await inter.response.send_message(
                f"Роль {role.mention} выше моей — поднимите мою роль в списке выше неё",
                ephemeral=True,
            )
            return

        await self.bot.guild_config.update(inter.guild_id, autorole_id=role.id)
        await inter.response.send_message(
            f"Новичкам будет выдаваться роль {role.mention}", ephemeral=True
        )

    @welcome.sub_command(name="off", description="Отключить приветствие или автовыдачу роли")
    async def welcome_off(
        self,
        inter: disnake.ApplicationCommandInteraction,
        target: Literal["канал", "роль", "всё"] = commands.Param(
            description="Что отключить", name="что"
        ),
    ) -> None:
        changes: dict[str, None] = {}
        if target in ("канал", "всё"):
            changes["welcome_channel_id"] = None
        if target in ("роль", "всё"):
            changes["autorole_id"] = None

        await self.bot.guild_config.update(inter.guild_id, **changes)
        await inter.response.send_message(f"Отключено: {target}", ephemeral=True)

    @welcome.sub_command(name="test", description="Прислать пример приветствия")
    async def welcome_test(self, inter: disnake.ApplicationCommandInteraction) -> None:
        config = self.bot.guild_config.get(inter.guild_id)
        if config.welcome_channel_id is None:
            await inter.response.send_message(
                "Канал приветствий не задан, используйте /welcome channel", ephemeral=True
            )
            return

        channel = inter.guild.get_channel(config.welcome_channel_id)
        if not isinstance(channel, disnake.TextChannel):
            await inter.response.send_message(
                "Заданный канал больше не существует, выберите новый", ephemeral=True
            )
            return

        try:
            await channel.send(embed=self._build_embed(inter.author))
        except disnake.Forbidden:
            await inter.response.send_message(
                f"Нет прав писать в {channel.mention}", ephemeral=True
            )
            return

        await inter.response.send_message(f"Отправил пример в {channel.mention}", ephemeral=True)


def setup(bot: VoidBot) -> None:
    bot.add_cog(Greetings(bot))
