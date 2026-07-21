from __future__ import annotations

import logging
import pkgutil

import disnake
from disnake.ext import commands

from bot.config import Settings
from bot.storage import GuildConfig, GuildConfigStore

logger = logging.getLogger(__name__)

COGS_PACKAGE = "bot.cogs"


class VoidBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = disnake.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(settings.command_prefix),
            help_command=None,
            intents=intents,
            test_guilds=settings.test_guilds,
        )
        self.settings = settings
        self.guild_config = GuildConfigStore(
            settings.storage_path,
            defaults=GuildConfig(
                welcome_channel_id=settings.welcome_channel_id,
                autorole_id=settings.autorole_id,
            ),
        )

    def load_all_extensions(self) -> None:
        from bot import cogs

        for module in pkgutil.iter_modules(cogs.__path__):
            name = f"{COGS_PACKAGE}.{module.name}"
            try:
                self.load_extension(name)
            except commands.ExtensionError:
                logger.exception("Не удалось загрузить расширение %s", name)
            else:
                logger.info("Расширение %s загружено", name)

    async def on_ready(self) -> None:
        logger.info("Бот %s подключён к %d серверам", self.user, len(self.guilds))
        await self.change_presence(
            status=disnake.Status.online,
            activity=disnake.Activity(name="--Пустота--", type=disnake.ActivityType.watching),
        )
