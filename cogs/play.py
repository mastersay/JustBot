import datetime
import game
import discord
from discord.ext import commands
from discord import app_commands




# Class grouping used embeds in play command
class Embeds(object):
    # Send after clicking the JOIN button
    in_waiting_room = discord.Embed(title="In waiting room",
                                    description="If you wish to leave, click the leave button.",
                                    color=0xFFFFFF)
    # Send after clicking the LEAVE button in ephemeral message
    left_waiting_room = discord.Embed(title="You have left the waiting room.")

    class DoubleLineEmbed(discord.Embed):

        def __init__(self, **kwargs):
            super(Embeds.DoubleLineEmbed, self).__init__(**kwargs)
            self._first_line = self._second_line = None

        @property
        def second_line(self):
            return self._second_line

        @second_line.setter
        def second_line(self, value):
            if value is not None:
                self._second_line = str(value)

        @property
        def description(self):
            if getattr(self, "_second_line", None):
                return f"{self._first_line}\n{self._second_line}"
            return self._first_line

        @description.setter
        def description(self, value):
            self._first_line = value

    @staticmethod
    def new_game() -> DoubleLineEmbed:
        # return discord.Embed(title="Starting a new game", color=0xFFCC00)
        return Embeds.DoubleLineEmbed(title="Starting a new game", color=0xFFCC00)

    # new_game = discord.Embed(title="Starting a new game", color=0xFFCC00)
    time_out = discord.Embed(title="Waiting room time out", color=0xFF0000)
    time_out_not_enough_players = discord.Embed(title="Waiting room time out",
                                                description="Not enough players to start a game", color=0xFF0000)
    game_started = discord.Embed(title="Game started", color=0x00FF00)


timeout = 30


class JoinView(discord.ui.View):
    def __init__(self, play_interaction: discord.Interaction, new_game_embed: discord.Embed,
                 new_game: game.Game):
        super(JoinView, self).__init__()
        self.play_interaction: discord.Interaction = play_interaction
        self.new_game_embed: discord.Embed = new_game_embed
        self.new_game: game.Game = new_game

    @discord.ui.button(style=discord.ButtonStyle.green, emoji="\u2934", label="JOIN",
                       custom_id="join")
    async def join_callback(self, button_interaction: discord.Interaction, button: discord.ui.Button):
        leave_view: discord.ui.View = LeaveView(play_interaction=self.play_interaction,
                                                join_view=self,
                                                new_game_embed=self.new_game_embed,
                                                new_game=self.new_game)
        if self.new_game.add_player(button_interaction.user):
            if self.new_game.players_amount + 1 > self.new_game.players_limit:
                await button_interaction.response.edit_message(view=None)
                self.new_game_embed.description = ""
            else:
                self.new_game_embed.description = f"Waiting for players to join " \
                                                  f"**{self.new_game.players_amount}/{self.new_game.players_limit}**"
            if not button_interaction.response.is_done():
                await button_interaction.response.defer()
            self.new_game_embed.add_field(name=f"{button_interaction.user.name}", value="\u2705 Joined")
            await self.play_interaction.edit_original_message(embed=self.new_game_embed)
            leave_message = await button_interaction.followup.send(embed=Embeds.in_waiting_room, view=leave_view,
                                                                   ephemeral=True)

            # noinspection PyShadowingNames
            async def on_timeout(self: LeaveView) -> None:
                await leave_message.edit(embed=Embeds.time_out, view=None)

            leave_view.on_timeout = on_timeout.__get__(leave_view, LeaveView)
        else:
            await button_interaction.response.defer()


class LeaveView(discord.ui.View):
    def __init__(self, play_interaction: discord.Interaction, join_view: JoinView, new_game_embed: discord.Embed,
                 new_game: game.Game):
        super(LeaveView, self).__init__(timeout=timeout)
        self.play_interaction: discord.Interaction = play_interaction
        self.new_game_embed: discord.Embed = new_game_embed
        self.new_game: game.Game = new_game
        self.join_view = join_view

    @discord.ui.button(style=discord.ButtonStyle.red, emoji="\u2935", label="LEAVE",
                       custom_id="leave")
    async def leave_callback(self, button_interaction: discord.Interaction, button: discord.ui.Button):
        await button_interaction.response.edit_message(embed=Embeds.left_waiting_room, view=None)
        leave_player_index = self.new_game.players.index(button_interaction.user)
        self.new_game.players.pop(leave_player_index)
        self.new_game_embed.description = f"Waiting for players to join **{self.new_game.players_amount}/{self.new_game.players_limit}**"
        self.new_game_embed.remove_field(leave_player_index)
        await self.play_interaction.edit_original_message(embed=self.new_game_embed, view=self.join_view)


class Play(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="test command")
    @app_commands.guilds(discord.Object(id=g_id))
    @app_commands.describe(number_of_players="Possible amount of players in the game")
    async def play(self, interaction: discord.Interaction, number_of_players: app_commands.Range[int, 2, 8]) -> None:
        new_game_embed = Embeds.new_game()
        new_game_embed.description = f"Waiting for players to join **1/{number_of_players}**"
        new_game_embed.add_field(name=f"{interaction.user.name}", value="\u2705 Joined")
        new_game = game.Game(self.bot, players_limit=number_of_players)
        new_game.add_player(interaction.user)
        # join_view = JoinView(start_game_embed, number_of_players, joined_players)
        # Embed with joined players and button for join
        join_view = JoinView(play_interaction=interaction, new_game_embed=new_game_embed,
                             new_game=new_game)
        await interaction.response.send_message(embed=new_game_embed, view=join_view)
        # Embed with LEAVE button and status information
        leave_view = LeaveView(play_interaction=interaction, join_view=join_view, new_game_embed=new_game_embed,
                               new_game=new_game)
        leave_message = await interaction.followup.send(embed=Embeds.in_waiting_room,
                                                        view=leave_view,
                                                        ephemeral=True)

        # noinspection PyShadowingNames
        async def on_timeout(self: LeaveView):
            await leave_message.edit(embed=Embeds.time_out, view=None)

        leave_view.on_timeout = on_timeout.__get__(leave_view, LeaveView)
        # Timeout for game start
        # leave_view.timeout = timeout
        starting_game_timeout = discord.utils.utcnow() + datetime.timedelta(seconds=timeout)
        new_game_embed.second_line = f"Game is starting: {discord.utils.format_dt(starting_game_timeout, 'R')}"
        await interaction.edit_original_message(embed=new_game_embed)
        await discord.utils.sleep_until(starting_game_timeout)
        # If message was not deleted, edit it to time out embed
        if new_game.players_amount < 2:
            try:
                await interaction.edit_original_message(embed=Embeds.time_out_not_enough_players, view=None)
            except discord.errors.NotFound:
                print("Message was deleted")
        else:
            print("Game started")
            try:
                await interaction.edit_original_message(embed=Embeds.game_started, view=None)
            except discord.errors.NotFound:
                print("Message was deleted")
        # for time_step in range(timeout, -1, -1):
        #     start = time.perf_counter_ns()
        #     new_game_embed.set_footer(text=f"Game is starting in: {time_step}s")
        #     await interaction.edit_original_message(embed=new_game_embed)
        #     interaction_time = (time.perf_counter_ns() - start) / 1e9
        #     await asyncio.sleep(1 - interaction_time)
        #     print(f"{interaction_time}s")
        # else:
        # Sends information about why the game couldn't be started
        # await interaction.edit_original_message(embed=Embeds.time_out_not_enough_players, view=None)


async def setup(bot: commands.bot.Bot):
    await bot.add_cog(Play(bot))
