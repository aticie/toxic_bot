import datetime
import logging
from types import SimpleNamespace
from typing import List, Optional, Union

import nextcord
from nextcord import SlashOption, Interaction
from nextcord.embeds import _EmptyEmbed, Embed
from nextcord.ext import commands
from nextcord.ext.commands import CommandError, Context

from toxic_bot.bots.discord import DiscordOsuBot
from toxic_bot.cards.scorecard import ScoreCardFactory, SingleImageScoreCard
from toxic_bot.helpers.database import Database
from toxic_bot.helpers.osu_api import OsuApiV2
from toxic_bot.helpers.paginated_view import PaginatedView
from toxic_bot.views.score_extras import ScoreExtrasView

logger = logging.getLogger('toxic-bot')


class ScoreInteractions(commands.Cog):
    def __init__(self, bot: DiscordOsuBot):
        self.bot = bot
        self.api: OsuApiV2 = bot.api
        self.db: Database = bot.db

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="recentbest", aliases=["rb"])
    async def recent_best(self, ctx: Context, osu_username: Optional[str] = None,
                          index: int = 1, game_mode: str = "osu"):
        """
        Shows the recent top play of a player
        """
        index -= 1
        plays = await self.get_user_plays(interaction=ctx, game_mode=game_mode, name=osu_username, score_type='best',
                                          all_scores=True)

        if len(plays) == 0:
            raise CommandError(f"`{osu_username}` has not played {game_mode} recently... :pensive:")

        plays.sort(key=lambda x: x.created_at, reverse=True)

        await self._single_score_core(index, plays, interaction=ctx)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="recent", aliases=["r", "rs"])
    async def recent(self, ctx: Context, osu_username: Optional[str] = None, index: int = 1, game_mode: str = "osu",
                     passes_only: bool = False):
        """
        Shows the recent play of a player
        """
        index -= 1
        plays = await self.get_user_plays(interaction=ctx, game_mode=game_mode, name=osu_username,
                                          passes_only=passes_only,
                                          score_type='recent')
        if len(plays) == 0:
            raise CommandError(f"`{osu_username}` has not played {game_mode} recently... :pensive:")

        await self._single_score_core(index, plays, interaction=ctx)

    @nextcord.slash_command(name="rs",
                            description="Shows the most recent play of a player")
    async def recent_interaction(self,
                                 interaction: Interaction,
                                 name: str = SlashOption(
                                     name="name",
                                     description="Specify the username or mention of the player",
                                     required=False),
                                 game_mode: str = SlashOption(
                                     name="mode",
                                     description="Specify the gamemode",
                                     default="osu",
                                     choices=["osu", "taiko", "fruits", "mania"],
                                     required=False),
                                 index: int = SlashOption(
                                     name="index",
                                     description="Specify the index of the score to show",
                                     default=1,
                                     required=False),
                                 passes_only: bool = SlashOption(
                                     name="passes",
                                     description="Show scores that are passes",
                                     default=False,
                                     required=False),
                                 as_list: bool = SlashOption(
                                     name="as_list",
                                     description="Show scores as a list",
                                     default=False,
                                     required=False),
                                 ):
        """
        Shows the most recent play of a player
        """

        index -= 1
        logger.debug(f'Recent slash command called with args: {name, game_mode, index, passes_only}')
        await interaction.response.defer()

        plays = await self.get_user_plays(interaction=interaction, game_mode=game_mode, name=name,
                                          passes_only=passes_only,
                                          score_type='recent')
        if len(plays) == 0:
            raise CommandError(f"`{name}` has not played {game_mode} recently... :pensive:")

        if as_list:
            await self._multi_score_core(plays, interaction=interaction)
        else:
            await self._single_score_core(index, plays, interaction=interaction)

    @nextcord.slash_command(name="rb",
                            description="Shows the most recent top play of a player")
    async def recent_best_interaction(self,
                                      interaction: Interaction,
                                      name: str = SlashOption(
                                          name="name",
                                          description="Specify the username or mention of the player",
                                          required=False),
                                      game_mode: str = SlashOption(
                                          name="mode",
                                          description="Specify the gamemode",
                                          default="osu",
                                          choices=["osu", "taiko", "fruits", "mania"],
                                          required=False),
                                      index: int = SlashOption(
                                          name="index",
                                          description="Specify the index of the score to show",
                                          default=1,
                                          required=False),
                                      as_list: bool = SlashOption(
                                          name="as_list",
                                          description="Show scores as a list",
                                          default=False,
                                          required=False),
                                      ):
        index -= 1
        logger.debug(f'Recent slash command called with args: {name, game_mode, index, as_list}')
        await interaction.response.defer()

        plays = await self.get_user_plays(interaction=interaction, game_mode=game_mode, name=name, score_type='best',
                                          all_scores=True)

        if len(plays) == 0:
            raise CommandError(f"`{name}` has not played {game_mode} recently... :pensive:")

        plays.sort(key=lambda x: x.created_at, reverse=True)
        if as_list:
            await self._multi_score_core(plays, interaction=interaction)
        else:
            await self._single_score_core(index, plays, interaction=interaction)

    @nextcord.message_command(name="Compare")
    async def compare_command(self, interaction: Interaction, message: nextcord.Message):
        """
        Can be used as an Application Command, or from the drop-down view of another message.
        """
        await interaction.response.defer()
        await self.compare_core(interaction, message)

    @nextcord.slash_command(name="ct",
                            description="Shows the Turkish leaderboard of the beatmap")
    async def country_interaction(self,
                                  interaction: Interaction,
                                  beatmap_id: int = SlashOption(
                                      name="beatmap_id",
                                      description="Beatmap ID for the country rankings",
                                      required=True)):
        """
        Shows the Turkish country rankings for the beatmap
        """
        logger.debug(f'Country slash command called with args: {beatmap_id}')
        await interaction.response.defer()
        await self.country_core(interaction, beatmap_id)

    async def compare_core(self, interaction, message: nextcord.Message):
        if not message.author.id == self.bot.application_id:
            raise CommandError("Couldn't find a score on this message. Please use it on a score.")
        # Check message embeds if it contains a score
        if message.embeds:
            embed = message.embeds[0]
            footer = embed.footer.text
            # Check if footer is empty or doesn't startswith special character
            if isinstance(footer, _EmptyEmbed) or not footer.startswith('▸'):
                raise CommandError("Couldn't find a score on this message. Please use compare on a score.")
            else:
                # Get beatmap_id and score_user_id from the footer
                beatmap_id = embed.url.split('/')[-1]
                # Get the user id of the interaction user
                user_id = f'<@{interaction.user.id}>'
                plays = await self.get_user_beatmap_scores(interaction, user_id, beatmap_id)
                if plays is None:
                    raise CommandError("You don't have any scores on this map.")
                if isinstance(plays, SimpleNamespace):
                    await self._single_score_core(0, [plays], interaction)
                else:
                    await self._multi_score_core(plays, interaction)
        else:
            raise CommandError("Couldn't find a score on this message. Please use compare on a score.")

    async def country_core(self, interaction, beatmap_id: int):
        country_scores = await self.api.get_country_beatmap_scores(beatmap_id=beatmap_id)
        beatmap_metadata = await self.api.get_beatmap(beatmap_id=beatmap_id)
        await self._country_scores_core(country_scores, beatmap_metadata, interaction)

    async def _country_scores_core(self, plays: List[SimpleNamespace],
                                   beatmap_meta: SimpleNamespace,
                                   interaction: Interaction):
        embeds = await self.country_scores_to_embed(plays, beatmap_meta)
        view = PaginatedView(embeds)
        await interaction.send(embed=embeds[0], view=view)

    @staticmethod
    async def country_scores_to_embed(plays: List[SimpleNamespace], beatmap_meta: SimpleNamespace) -> List[Embed]:
        embeds: List[Embed] = []
        for i in range(0, len(plays), 5):
            embed = Embed()
            beatmap_artist = beatmap_meta.beatmapset.artist
            beatmap_title = beatmap_meta.beatmapset.title
            beatmap_version = beatmap_meta.version
            beatmap_stars = f"{beatmap_meta.difficulty_rating:.2f}"
            beatmap_creator = beatmap_meta.beatmapset.creator
            beatmap_url = beatmap_meta.url
            beatmap_cover_url = beatmap_meta.beatmapset.covers.cover

            embed.title = f"{beatmap_artist} - {beatmap_title} ({beatmap_creator}) [{beatmap_version}] {beatmap_stars}⭐"
            embed.url = beatmap_url

            embed.set_image(url=beatmap_cover_url)
            embed.set_author(name="Turkey Country Ranks", icon_url="https://osu.ppy.sh/images/flags/TR.png")

            plays_chunked = plays[i:i + 5]

            embed_desc = ""
            for offset, play in enumerate(plays_chunked):
                player_name = play.user.username
                player_id = play.user_id
                player_score = f"{play.total_score:,}"
                player_combo = play.max_combo
                mods_list = play.mods
                player_mods = "".join([mod["acronym"] for mod in mods_list]) if len(mods_list) > 0 else "NoMod"
                player_acc = f"{play.accuracy * 100:.2f}%"
                player_pp = play.pp
                player_rank = play.rank
                player_statistics = play.statistics
                player_miss = player_statistics.miss if hasattr(player_statistics, "miss") else 0
                play_ts = int(datetime.datetime.fromisoformat(play.ended_at).timestamp())
                player_url = f"https://osu.ppy.sh/users/{player_id}"
                embed_desc += f"**{i + offset + 1}. [{player_name}]({player_url})** - <t:{play_ts}:d>\n"
                if player_pp is None:
                    embed_desc += f"**{player_rank} Rank** - {player_score} (x{player_combo}) -" \
                                  f" {player_acc} {player_mods} - ({player_miss} miss)\n\n"
                else:
                    embed_desc += f"**{player_rank} Rank** - {player_score} (x{player_combo}) -" \
                                  f" {player_acc} {player_mods} - **{player_pp:.2f}pp** ({player_miss} miss)\n\n"

            embed.description = embed_desc
            embeds.append(embed)

        return embeds

    async def _multi_score_core(self, plays: List[SimpleNamespace],
                                interaction: Interaction):
        embed = nextcord.Embed(title="We are sorry", description="This feature is not yet implemented")
        await interaction.send(embed=embed)

    async def _single_score_core(self, play_index: int, plays: List[SimpleNamespace],
                                 interaction: Union[Interaction, Context]):
        """
        Core function for single score commands
        """
        play_card: SingleImageScoreCard = ScoreCardFactory(plays, play_index).get_card()
        if not hasattr(play_card.score, 'beatmapset'):
            beatmap = await self.api.get_beatmap(play_card.score.beatmap.id)
            play_card.score.beatmapset = beatmap.beatmapset
        embed, file = await play_card.to_embed()
        view = ScoreExtrasView()
        await interaction.send(embed=embed, file=file, view=view)

    async def get_user_plays(self, interaction: Union[Context, Interaction], game_mode: str, name: str, score_type: str,
                             passes_only: bool = False, all_scores: bool = False):
        user_id = await self.bot.get_user_id(interaction, name)
        plays = await self.api.get_user_scores(user_id=user_id, score_type=score_type, mode=game_mode,
                                               include_fails=0 if passes_only else 1)
        if all_scores:
            plays.extend(await self.api.get_user_scores(user_id=user_id, score_type=score_type, mode=game_mode,
                                                        include_fails=0 if passes_only else 1, offset=50))
        return plays

    async def get_user_beatmap_scores(self, interaction: Union[Context, Interaction], name: str, beatmap_id: int):
        user_id = await self.bot.get_user_id(interaction, name)
        plays = await self.api.get_user_beatmap_score(user_id=user_id, beatmap_id=beatmap_id)
        return plays


def setup(bot):
    bot.add_cog(ScoreInteractions(bot))
