from nextcord.ext import commands

from helpers.ossapi_wrapper import api
from helpers.parser import Parser
from scorecard import ScoreCardFactory


class Scores(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="recent", aliases=["rs", "r"])
    async def recent(self, ctx, *args: str):
        """ Shows the most recent play of a player

            Optional arguments:
            <osu_username> or <discord_mention>: Username or discord mention of the player with the recent play
            -l: Displays the most recent plays as a list
            -p <play_no>: Shows the n'th recent play. (use -p 5 for 5th recent play)
            -m <game_mode>: Shows results for selected game mode. (0 = std, 1 = taiko, 2 = ctb, 3 = mania)
        """

        mentions = ctx.message.mentions

        parser = Parser(ctx)

        await parser.parse_args(args, mentions)

        # Get recent plays of the user
        plays = api.user_scores(user_id=parser.user_id, type_="recent", mode=parser.game_mode, include_fails=True)

        if len(plays) == 0:
            await ctx.send(f"`{parser.username}` has not played {parser.game_mode} recently... :pensive:")
            return

        play_card = ScoreCardFactory(parser, plays).get_play_card()
        await play_card.send()


def setup(bot):
    bot.add_cog(Scores(bot))
