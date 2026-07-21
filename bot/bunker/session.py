from __future__ import annotations

import random
from enum import Enum, auto

import disnake

from bot.bunker.player import Player


class JoinResult(Enum):
    JOINED = auto()
    ALREADY_JOINED = auto()


class VoteResult(Enum):
    ACCEPTED = auto()
    NOT_IN_GAME = auto()
    ALREADY_VOTED = auto()
    SELF_VOTE = auto()
    INVALID_TARGET = auto()


class GameSession:
    def __init__(self, guild_id: int, channel: disnake.TextChannel, host_id: int) -> None:
        self.guild_id = guild_id
        self.channel = channel
        self.host_id = host_id
        self.players: dict[int, Player] = {}
        self.reveal_round_active = False
        self.voting_active = False
        self._revealed_this_round: set[int] = set()
        self._votes: dict[int, int] = {}
        self._voted: set[int] = set()

    @property
    def alive_players(self) -> list[Player]:
        return [player for player in self.players.values() if player.alive]

    def get(self, user_id: int) -> Player | None:
        return self.players.get(user_id)

    def join(self, user: disnake.User | disnake.Member) -> tuple[JoinResult, Player]:
        existing = self.players.get(user.id)
        if existing is not None:
            return JoinResult.ALREADY_JOINED, existing
        player = Player(user)
        self.players[user.id] = player
        return JoinResult.JOINED, player

    def start_reveal_round(self) -> None:
        self.reveal_round_active = True
        self._revealed_this_round.clear()

    def finish_reveal_round(self) -> list[Player]:
        self.reveal_round_active = False
        pending = [p for p in self.alive_players if p.id not in self._revealed_this_round]
        self._revealed_this_round.clear()
        return pending

    def mark_revealed(self, player: Player) -> None:
        self._revealed_this_round.add(player.id)

    def has_revealed_this_round(self, player: Player) -> bool:
        return player.id in self._revealed_this_round

    def start_voting(self) -> None:
        self.voting_active = True
        self._voted.clear()
        self._votes = {player.id: 0 for player in self.alive_players}

    def register_vote(self, voter_id: int, target_id: int) -> VoteResult:
        voter = self.players.get(voter_id)
        if voter is None or not voter.alive:
            return VoteResult.NOT_IN_GAME
        if voter_id in self._voted:
            return VoteResult.ALREADY_VOTED
        if voter_id == target_id:
            return VoteResult.SELF_VOTE
        target = self.players.get(target_id)
        if target is None or not target.alive:
            return VoteResult.INVALID_TARGET
        self._voted.add(voter_id)
        self._votes[target_id] += 1
        return VoteResult.ACCEPTED

    def finish_voting(self) -> Player | None:
        self.voting_active = False
        if not any(self._votes.values()):
            return None
        top = max(self._votes.values())
        candidates = [pid for pid, count in self._votes.items() if count == top]
        loser = self.players.get(random.choice(candidates))
        if loser is not None:
            loser.kick()
        return loser
