from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

import disnake

from bot.bunker.character import CHARACTER_POOL
from bot.bunker.session import GameSession, VoteResult

_VOTE_MESSAGES = {
    VoteResult.NOT_IN_GAME: "Вы не в игре или выбыли",
    VoteResult.ALREADY_VOTED: "Вы уже проголосовали",
    VoteResult.SELF_VOTE: "Нельзя голосовать за себя",
    VoteResult.INVALID_TARGET: "Этот игрок не участвует в голосовании",
}

Callback = Callable[[disnake.MessageInteraction], Coroutine[Any, Any, None]]


def _frame(text: str) -> str:
    return f">>> ╔══════════╗\n║{text}\n╚══════════╝"


class RevealView(disnake.ui.View):
    def __init__(self, session: GameSession, timeout: float) -> None:
        super().__init__(timeout=timeout)
        self.session = session
        for title in CHARACTER_POOL:
            button = disnake.ui.Button(
                label=title.removeprefix("║"),
                style=disnake.ButtonStyle.success,
            )
            button.callback = self._make_callback(title)
            self.add_item(button)

    def _make_callback(self, title: str) -> Callback:
        async def callback(interaction: disnake.MessageInteraction) -> None:
            player = self.session.get(interaction.user.id)
            if player is None or not player.alive:
                await interaction.response.send_message("__**Вы не в игре**__", ephemeral=True)
                return
            if self.session.has_revealed_this_round(player):
                await interaction.response.send_message(
                    "В этом раунде вы уже открыли характеристику", ephemeral=True
                )
                return

            character = player.reveal(title)
            if character is None:
                await interaction.response.send_message(
                    _frame(f"***{player.name}*** ══➧ {title} __**уже открыто**__"),
                    ephemeral=True,
                )
                return

            self.session.mark_revealed(player)
            await interaction.response.send_message(
                _frame(
                    f"***{player.name}*** ══➧ {character.title}: __**{character.value}**__"
                )
            )

        return callback


class VotingView(disnake.ui.View):
    def __init__(self, session: GameSession, timeout: float) -> None:
        super().__init__(timeout=timeout)
        self.session = session
        for player in session.alive_players[:25]:
            button = disnake.ui.Button(
                label=player.name[:80],
                style=disnake.ButtonStyle.secondary,
            )
            button.callback = self._make_callback(player.id)
            self.add_item(button)

    def _make_callback(self, target_id: int) -> Callback:
        async def callback(interaction: disnake.MessageInteraction) -> None:
            result = self.session.register_vote(interaction.user.id, target_id)
            if result is not VoteResult.ACCEPTED:
                await interaction.response.send_message(
                    _VOTE_MESSAGES[result], ephemeral=True
                )
                return
            target = self.session.get(target_id)
            name = target.name if target else "игрока"
            await interaction.response.send_message(
                f"Вы проголосовали за {name}", ephemeral=True
            )

        return callback
