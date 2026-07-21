from __future__ import annotations

import asyncio
import logging

import disnake
from disnake.ext import commands

from bot.bunker.session import GameSession, JoinResult
from bot.bunker.story import random_scenario
from bot.bunker.views import RevealView, VotingView
from bot.client import VoidBot

logger = logging.getLogger(__name__)

NO_GAME = "Игра ещё не началась. Запустите её командой /start-game"
NOT_A_PLAYER = "Вы не в игре"


def _box(title: str, rows: list[str]) -> str:
    body = "\n".join(f"║{row}" for row in rows)
    return f">>> ╔═══════════╗\n║{title}\n╠═══════════╣\n{body}\n╚═══════════╝"


class Bunker(commands.Cog):
    def __init__(self, bot: VoidBot) -> None:
        self.bot = bot
        self._sessions: dict[int, GameSession] = {}

    def _session(self, inter: disnake.ApplicationCommandInteraction) -> GameSession | None:
        return self._sessions.get(inter.guild_id) if inter.guild_id else None

    async def _resolve(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> GameSession | None:
        session = self._session(inter)
        if session is None:
            await inter.response.send_message(NO_GAME, ephemeral=True)
            return None
        if session.get(inter.user.id) is None:
            await inter.response.send_message(NOT_A_PLAYER, ephemeral=True)
            return None
        return session

    @commands.slash_command(name="start-game", description="Начать игру «Бункер»")
    @commands.guild_only()
    async def start_game(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if inter.guild_id in self._sessions:
            await inter.response.send_message("Игра уже идёт", ephemeral=True)
            return

        guild = inter.guild
        assert guild is not None

        if not guild.me.guild_permissions.manage_channels:
            await inter.response.send_message(
                "Мне нужно право «Управление каналами», чтобы создать игровой канал",
                ephemeral=True,
            )
            return

        await inter.response.defer()
        category = inter.channel.category if isinstance(inter.channel, disnake.TextChannel) else None
        channel = await guild.create_text_channel(
            self.bot.settings.bunker_channel_name,
            category=category,
            reason=f"Игра «Бункер», запустил {inter.user}",
        )

        self._sessions[guild.id] = GameSession(guild.id, channel, inter.user.id)

        await inter.edit_original_response(
            f"Игра началась в канале {channel.mention}, присоединяйтесь командой /join"
        )
        embed, file = random_scenario().to_message()
        if file is None:
            await channel.send(embed=embed)
        else:
            await channel.send(embed=embed, file=file)

    @commands.slash_command(name="join", description="Присоединиться к игре")
    @commands.guild_only()
    async def join(self, inter: disnake.ApplicationCommandInteraction) -> None:
        session = self._session(inter)
        if session is None:
            await inter.response.send_message(NO_GAME, ephemeral=True)
            return

        result, player = session.join(inter.user)
        if result is JoinResult.ALREADY_JOINED:
            await inter.response.send_message("Вы уже в игре", ephemeral=True)
            return

        await inter.response.send_message(
            f"Список ваших характеристик:\n{player.card(full=True)}", ephemeral=True
        )
        await session.channel.send(f"{player.name} присоединился к игре")

    @commands.slash_command(name="stat", description="Показать свои характеристики")
    @commands.guild_only()
    async def stat(self, inter: disnake.ApplicationCommandInteraction) -> None:
        session = await self._resolve(inter)
        if session is None:
            return
        player = session.get(inter.user.id)
        assert player is not None
        await inter.response.send_message(
            f"Список ваших характеристик:\n{player.card(full=True)}", ephemeral=True
        )

    @commands.slash_command(name="list", description="Показать список игроков")
    @commands.guild_only()
    async def player_list(self, inter: disnake.ApplicationCommandInteraction) -> None:
        session = await self._resolve(inter)
        if session is None:
            return
        rows = [player.card() for player in session.players.values()]
        await inter.response.send_message(_box("Список игроков:", rows))

    @commands.slash_command(name="open", description="Раунд открытия характеристик")
    @commands.guild_only()
    async def open_round(self, inter: disnake.ApplicationCommandInteraction) -> None:
        session = await self._resolve(inter)
        if session is None:
            return
        if session.reveal_round_active:
            await inter.response.send_message("Раунд открытия уже идёт", ephemeral=True)
            return
        if session.voting_active:
            await inter.response.send_message("Сейчас идёт голосование", ephemeral=True)
            return

        duration = self.bot.settings.reveal_duration
        session.start_reveal_round()
        view = RevealView(session, timeout=duration)

        await inter.response.send_message("Раунд открытия начат", ephemeral=True)
        message = await session.channel.send(
            f"Откройте одну из своих характеристик.\n"
            f"На это даётся {duration} секунд, иначе характеристика откроется случайно.",
            view=view,
        )

        await asyncio.sleep(duration)
        view.stop()

        try:
            await message.delete()
        except disnake.HTTPException:
            logger.warning("Не удалось удалить сообщение раунда открытия", exc_info=True)

        rows: list[str] = []
        for player in session.finish_reveal_round():
            character = player.reveal_random()
            if character is not None:
                rows.append(
                    f"***{player.name}*** ══➧ {character.title}: __**{character.value}**__"
                )
        if rows:
            await session.channel.send(_box("Открыто по таймауту:", rows))

    @commands.slash_command(name="golosovanie", description="Голосование за исключение")
    @commands.guild_only()
    async def voting(self, inter: disnake.ApplicationCommandInteraction) -> None:
        session = await self._resolve(inter)
        if session is None:
            return
        if session.voting_active:
            await inter.response.send_message("Голосование уже идёт", ephemeral=True)
            return
        if len(session.alive_players) < 2:
            await inter.response.send_message(
                "Для голосования нужно минимум два живых игрока", ephemeral=True
            )
            return

        duration = self.bot.settings.voting_duration
        session.start_voting()
        view = VotingView(session, timeout=duration)

        await inter.response.send_message("Голосование начато", ephemeral=True)
        message = await session.channel.send(
            f"Начинаем голосование, отведено {duration} секунд.\nКто же не попадёт в бункер?",
            view=view,
        )

        await asyncio.sleep(duration)
        view.stop()
        view.clear_items()

        try:
            await message.edit(content="Голосование окончено", view=view)
        except disnake.HTTPException:
            logger.warning("Не удалось обновить сообщение голосования", exc_info=True)

        loser = session.finish_voting()
        if loser is None:
            await session.channel.send("Никто не проголосовал, никто не исключён")
        else:
            await session.channel.send(f"{loser.name} не попал в бункер")

    @commands.slash_command(name="end-game", description="Завершить игру")
    @commands.guild_only()
    async def end_game(self, inter: disnake.ApplicationCommandInteraction) -> None:
        session = await self._resolve(inter)
        if session is None:
            return

        survivors = [f"🥳 {player.name}" for player in session.alive_players]
        await inter.response.send_message(
            _box("Игра закончилась! Победили:", survivors or ["никто"])
        )

        self._sessions.pop(session.guild_id, None)
        await asyncio.sleep(5)

        try:
            await session.channel.delete(reason="Игра «Бункер» завершена")
        except disnake.HTTPException:
            logger.warning("Не удалось удалить игровой канал", exc_info=True)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.abc.GuildChannel) -> None:
        session = self._sessions.get(channel.guild.id)
        if session is not None and session.channel.id == channel.id:
            self._sessions.pop(channel.guild.id, None)


def setup(bot: VoidBot) -> None:
    bot.add_cog(Bunker(bot))
