from discord.ext import commands

from helpers.util import *


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

        try:
            await parser.parse_args(args, mentions)
        except:
            return

        # Get recent plays of the user
        plays = await get_recent_plays(parser)

        # Get player details
        player = await get_player_details(parser)

        # Converts game mode from int to str. Ex: 1 -> Mania
        game_mode = game_mode_enum[parser.game_mode]

        if len(plays) == 0:
            await ctx.send(f"`{parser.user}` has not played recently in osu!{game_mode} :pensive:")
            return

        if parser.is_multi:
            await send_multi_play_embed(ctx, parser, player, plays)
        else:
            # Get beatmap information
            play = plays[parser.which_play]
            await send_single_play_image(ctx, parser, player, play)



def setup(bot):
    bot.add_cog(Scores(bot))
