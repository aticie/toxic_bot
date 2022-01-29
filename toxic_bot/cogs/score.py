import logging
from types import SimpleNamespace
from typing import Union, List

import nextcord
from nextcord import SlashOption, Interaction
from nextcord.ext import commands
from nextcord.ext.commands import Context, CommandError

from toxic_bot.bots.discord import DiscordOsuBot
from toxic_bot.helpers.osu_api import OsuApiV2
from toxic_bot.helpers.parser import ParserExceptionNoUserFound
from toxic_bot.scorecard import ScoreCardFactory

logger = logging.getLogger('toxic-bot')


class Scores(commands.Cog):
    def __init__(self, bot: DiscordOsuBot):
        self.bot = bot
        self.api: OsuApiV2 = bot.api

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

        plays = await self.get_user_plays(context=interaction, game_mode=game_mode, name=name, passes_only=passes_only,
                                          score_type='recent')
        if len(plays) == 0:
            raise CommandError(f"`{name}` has not played {game_mode} recently... :pensive:")

        if as_list:
            await self._multi_score_core(plays, context=interaction)
        else:
            await self._single_score_core(index, plays, context=interaction)

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

        plays = await self.get_user_plays(context=interaction, game_mode=game_mode, name=name, score_type='best')

        if len(plays) == 0:
            raise CommandError(f"`{name}` has not played {game_mode} recently... :pensive:")

        plays.sort(key=lambda x: x.created_at, reverse=True)
        if as_list:
            await self._multi_score_core(plays, context=interaction)
        else:
            await self._single_score_core(index, plays, context=interaction)

    async def _multi_score_core(self, plays: List[SimpleNamespace],
                                context: Union[Interaction, Context]):
        embed = nextcord.Embed(title="We are sorry", description="This feature is not yet implemented")
        await context.send(embed=embed)

    async def _single_score_core(self, play_index: int, plays: List[SimpleNamespace],
                                 context: Union[Interaction, Context]):
        """
        Core function for single score commands
        """
        play_card = ScoreCardFactory(plays, play_index).get_play_card()
        if not hasattr(play_card.score, 'beatmapset'):
            beatmap = await self.api.get_beatmap(play_card.score.beatmap.id)
            play_card.score.beatmapset = beatmap[0].beatmapset
        embed, file = await play_card.to_embed()
        await context.send(embed=embed, file=file)

    async def get_user_plays(self, context: Union[Interaction, Context], game_mode: str, name: str, score_type: str,
                             passes_only: bool = False):
        user_id = await self.get_user_id(context, name)
        plays = await self.api.get_user_scores(user_id=user_id, score_type=score_type, mode=game_mode,
                                               include_fails=0 if passes_only else 1)
        return plays

    async def get_user_beatmap_scores(self, context: Union[Interaction, Context], name: str, beatmap_id: int):
        user_id = await self.get_user_id(context, name)
        plays = await self.api.get_user_beatmap_score(user_id=user_id, beatmap_id=beatmap_id)
        return plays

    async def get_user_id(self, context: Union[Context, Interaction], name: str):
        if name is None:
            if isinstance(context, Interaction):
                user_discord_id = context.user.id
            else:
                user_discord_id = context.author.id

            user_details = await self.bot.db.get_user(user_discord_id)
            if user_details is None:
                server_prefix = self.bot.db.get_prefix(context.guild.id)
                raise ParserExceptionNoUserFound(f"Please link your osu! profile. Use `{server_prefix}link`")
            else:
                user_id = user_details['osu_id']
        else:
            if name.startswith('<@'):
                user_discord_id = int(name[2:-1])
                user_details = await self.bot.db.get_user(user_discord_id)
                if user_details is None:
                    raise ParserExceptionNoUserFound(f'User `{name}` was not found')

                user_id = user_details['osu_id']
            else:
                user_details = await self.api.get_user(name, key='username')
                if user_details is None:
                    raise ParserExceptionNoUserFound(f'User `{name}` was not found')

                user_id = user_details[0].id
        return user_id

    @nextcord.message_command(guild_ids=[571853176752308244], name="Compare")
    async def compare_command(self, interaction: Interaction, message: nextcord.Message):
        await interaction.response.defer()
        if not message.author.id == self.bot.application_id:
            await interaction.channel.send("Couldn't find a score on this message. Please use it on a score.")
            return

        if message.embeds:
            embed = message.embeds[0]
            footer = embed.footer.text
            if not footer.startswith('▸'):
                await interaction.channel.send("Couldn't find a score on this message. Please use it on a score.")
                return
            else:
                beatmap_id = footer.split('|')[1].strip().split(',')[0]
                user_id = f'<@{interaction.user.id}>'
                plays = await self.get_user_beatmap_scores(interaction, user_id, beatmap_id)
                if plays is None:
                    raise CommandError("You don't have any scores on this map.")
                elif len(plays) == 1:
                    await self._single_score_core(0, plays, interaction)
                else:
                    await self._multi_score_core(plays, interaction)
                return

        return

def setup(bot):
    bot.add_cog(Scores(bot))
