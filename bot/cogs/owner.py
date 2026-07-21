from __future__ import annotations

from disnake.ext import commands

from bot.client import COGS_PACKAGE, VoidBot


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

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        await ctx.send(f"Ошибка: `{error}`")


def setup(bot: VoidBot) -> None:
    bot.add_cog(Owner(bot))
