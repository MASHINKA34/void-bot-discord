from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Final

import disnake
from disnake.ext import commands

from bot.client import VoidBot
from bot.config import DATA_DIR

logger = logging.getLogger(__name__)

SELECT_CUSTOM_ID: Final = "void:lane-roles"


@dataclass(frozen=True, slots=True)
class Lane:
    label: str
    role_id: int
    emoji: str | None = None


def _load_config() -> tuple[tuple[Lane, ...], str | None]:
    path = DATA_DIR / "lane_roles.json"
    if not path.is_file():
        return (), None
    raw = json.loads(path.read_text(encoding="utf-8"))
    lanes = tuple(
        Lane(label=item["label"], role_id=int(item["role_id"]), emoji=item.get("emoji"))
        for item in raw.get("lanes", [])
    )
    return lanes, raw.get("image_url")


LANES, IMAGE_URL = _load_config()


class LaneSelect(disnake.ui.Select):
    def __init__(self, lanes: tuple[Lane, ...]) -> None:
        super().__init__(
            placeholder="Выберите роль",
            custom_id=SELECT_CUSTOM_ID,
            min_values=0,
            max_values=max(len(lanes), 1),
            options=[
                disnake.SelectOption(label=lane.label, value=str(lane.role_id), emoji=lane.emoji)
                for lane in lanes
            ],
        )
        self.managed_ids = {lane.role_id for lane in lanes}

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        member = interaction.author
        if not isinstance(member, disnake.Member):
            return

        await interaction.response.defer(ephemeral=True)

        chosen = {int(value) for value in self.values}
        current = {role.id for role in member.roles}

        to_add = [
            role
            for role_id in chosen - current
            if (role := interaction.guild.get_role(role_id)) is not None
        ]
        to_remove = [
            role
            for role_id in (self.managed_ids - chosen) & current
            if (role := interaction.guild.get_role(role_id)) is not None
        ]

        try:
            if to_remove:
                await member.remove_roles(*to_remove, reason="Меню выбора позиции")
            if to_add:
                await member.add_roles(*to_add, reason="Меню выбора позиции")
        except disnake.Forbidden:
            await interaction.followup.send(
                "У меня нет прав управлять этими ролями", ephemeral=True
            )
            return

        await interaction.followup.send("Роли обновлены", ephemeral=True)


class LaneRolesView(disnake.ui.View):
    def __init__(self, lanes: tuple[Lane, ...]) -> None:
        super().__init__(timeout=None)
        self.add_item(LaneSelect(lanes))


class Roles(commands.Cog):
    def __init__(self, bot: VoidBot) -> None:
        self.bot = bot
        self._view_registered = False

    @commands.Cog.listener()
    async def on_connect(self) -> None:
        if self._view_registered or not LANES:
            return
        self.bot.add_view(LaneRolesView(LANES))
        self._view_registered = True

    @commands.slash_command(name="games", description="Опубликовать меню выбора позиции")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def games(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not LANES:
            await inter.response.send_message(
                "Роли не настроены: заполните bot/data/lane_roles.json", ephemeral=True
            )
            return

        embed = disnake.Embed(color=0x2F3136)
        embed.set_author(name="Выбери свою позицию:")
        embed.description = (
            "Под этим постом ты можешь выбрать свою позицию и получить роль.\n\n"
            + "\n".join(f"{lane.emoji or ''} — {lane.label}".strip() for lane in LANES)
        )
        if IMAGE_URL:
            embed.set_image(url=IMAGE_URL)

        await inter.response.send_message(embed=embed, view=LaneRolesView(LANES))


def setup(bot: VoidBot) -> None:
    bot.add_cog(Roles(bot))
