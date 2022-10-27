import discord
from discord.ext import commands


class Game:
    def __init__(self, bot: commands.Bot, players_limit: int):
        self.bot = bot
        self._players: list[discord.User] = []
        self._players_limit = players_limit

    @property
    def players_limit(self):
        return self._players_limit

    @property
    def players_amount(self):
        return len(self._players)

    @property
    def players(self):
        return self._players

    def add_player(self, new_player: discord.User) -> bool:
        if self.players_amount + 1 <= self.players_limit and new_player not in self._players:
            self._players.append(new_player)
            return True
        return False
