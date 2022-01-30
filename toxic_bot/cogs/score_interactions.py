import logging
from types import SimpleNamespace
from typing import List

import nextcord
from nextcord import SlashOption, Interaction
from nextcord.embeds import _EmptyEmbed
from nextcord.ext import commands
from nextcord.ext.commands import CommandError

from toxic_bot.bots.discord import DiscordOsuBot
from toxic_bot.cards.scorecard import ScoreCardFactory
from toxic_bot.helpers.database import Database
from toxic_bot.helpers.osu_api import OsuApiV2
from toxic_bot.views.score_extras import ScoreExtrasView

logger = logging.getLogger('toxic-bot')


class ScoreInteractions(commands.Cog):
    def __init__(self, bot: DiscordOsuBot):
        self.bot = bot
        self.api: OsuApiV2 = bot.api
        self.db: Database = bot.db

    @nextcord.slash_command(guild_ids=[571853176752308244], name="rs",
                            description="Shows the most recent play of a player")
    async def recent(self,
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
                         default=0,
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

    @nextcord.slash_command(guild_ids=[571853176752308244], name="rb",
                            description="Shows the most recent top play of a player")
    async def recent_best(self,
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
                              default=0,
                              required=False),
                          as_list: bool = SlashOption(
                              name="as_list",
                              description="Show scores as a list",
                              default=False,
                              required=False),
                          ):

        logger.debug(f'Recent slash command called with args: {name, game_mode, index, as_list}')
        await interaction.response.defer()

        plays = await self.get_user_plays(interaction=interaction, game_mode=game_mode, name=name, score_type='best')

        if len(plays) == 0:
            raise CommandError(f"`{name}` has not played {game_mode} recently... :pensive:")

        plays.sort(key=lambda x: x.created_at, reverse=True)
        if as_list:
            await self._multi_score_core(plays, interaction=interaction)
        else:
            await self._single_score_core(index, plays, interaction=interaction)

    @nextcord.message_command(guild_ids=[571853176752308244], name="Compare")
    async def compare_command(self, interaction: Interaction, message: nextcord.Message):
        """
        Can be used as an Application Command, or from the drop-down view of another message.
        """
        await interaction.response.defer()
        await self._compare_core(interaction)

    async def _compare_core(self, interaction):
        message = interaction.message
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
                beatmap_id, score_user_id = footer.split('|')[1].strip().split(',')
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

    async def _multi_score_core(self, plays: List[SimpleNamespace],
                                interaction: Interaction):
        embed = nextcord.Embed(title="We are sorry", description="This feature is not yet implemented")
        await interaction.send(embed=embed)

    async def _single_score_core(self, play_index: int, plays: List[SimpleNamespace],
                                 interaction: Interaction):
        """
        Core function for single score commands
        """
        play_card = ScoreCardFactory(plays, play_index).get_card()
        if not hasattr(play_card.score, 'beatmapset'):
            beatmap = await self.api.get_beatmap(play_card.score.beatmap.id)
            play_card.score.beatmapset = beatmap.beatmapset
        embed, file = await play_card.to_embed()
        view = ScoreExtrasView()
        await interaction.send(embed=embed, file=file, view=view)

    async def get_user_plays(self, interaction: Interaction, game_mode: str, name: str, score_type: str,
                             passes_only: bool = False):
        user_id = await self.bot.get_user_id(interaction, name)
        plays = await self.api.get_user_scores(user_id=user_id, score_type=score_type, mode=game_mode,
                                               include_fails=0 if passes_only else 1)
        return plays

    async def get_user_beatmap_scores(self, interaction: Interaction, name: str, beatmap_id: int):
        user_id = await self.bot.get_user_id(interaction, name)
        plays = await self.api.get_user_beatmap_score(user_id=user_id, beatmap_id=beatmap_id)
        return plays


def setup(bot):
    bot.add_cog(ScoreInteractions(bot))
