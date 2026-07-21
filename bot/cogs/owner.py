from __future__ import annotations

import io
import json
from datetime import datetime, timezone

import disnake
from disnake.ext import commands

from bot.client import COGS_PACKAGE, VoidBot

MAX_BACKUP_SIZE = 1024 * 1024


class Owner(commands.Cog):
    def __init__(self, bot: VoidBot) -> None:
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await self.bot.is_owner(ctx.author)

    @commands.command(name="load")
    async def load(self, ctx: commands.Context, extension: str) -> None:
        self.bot.load_extension(f"{COGS_PACKAGE}.{extension}")
        await ctx.send(f"Расширение `{extension}` загружено")

    @commands.command(name="unload")
    async def unload(self, ctx: commands.Context, extension: str) -> None:
        self.bot.unload_extension(f"{COGS_PACKAGE}.{extension}")
        await ctx.send(f"Расширение `{extension}` выгружено")

    @commands.command(name="reload")
    async def reload(self, ctx: commands.Context, extension: str) -> None:
        self.bot.reload_extension(f"{COGS_PACKAGE}.{extension}")
        await ctx.send(f"Расширение `{extension}` перезагружено")

    @commands.command(name="backup")
    async def backup(self, ctx: commands.Context) -> None:
        store = self.bot.guild_config
        if not len(store):
            await ctx.send("Настройки серверов пусты, сохранять нечего")
            return

        payload = store.dumps().encode("utf-8")
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        file = disnake.File(io.BytesIO(payload), filename=f"guilds-{stamp}.json")
        await ctx.send(
            f"Настройки {len(store)} серверов. Восстановить: `{ctx.prefix}restore` с этим файлом",
            file=file,
        )

    @commands.command(name="restore")
    async def restore(self, ctx: commands.Context) -> None:
        if not ctx.message.attachments:
            await ctx.send(f"Прикрепите файл настроек к сообщению с `{ctx.prefix}restore`")
            return

        attachment = ctx.message.attachments[0]
        if attachment.size > MAX_BACKUP_SIZE:
            await ctx.send("Файл слишком большой")
            return

        raw = await attachment.read()
        try:
            count = await self.bot.guild_config.load_dump(raw.decode("utf-8"))
        except UnicodeDecodeError:
            await ctx.send("Файл не в кодировке UTF-8")
            return
        except json.JSONDecodeError as error:
            await ctx.send(f"Файл не является корректным JSON: `{error}`")
            return
        except ValueError as error:
            await ctx.send(f"Не удалось прочитать файл: `{error}`")
            return

        await ctx.send(f"Восстановлены настройки {count} серверов")

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        await ctx.send(f"Ошибка: `{error}`")


def setup(bot: VoidBot) -> None:
    bot.add_cog(Owner(bot))
