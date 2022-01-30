import datetime
import logging

import nextcord
from nextcord import Interaction
from nextcord.ext import commands
from nextcord.ui import Item

from toxic_bot.bots.discord import DiscordOsuBot

logger = logging.getLogger('toxic-bot')

profile_extras_cooldown_secs = datetime.timedelta(seconds=10)
profile_extras_user_cooldowns = {}


class ProfileExtrasView(nextcord.ui.View):
    def __init__(self):
        super().__init__()

    @nextcord.ui.button(label='Show mine!', style=nextcord.ButtonStyle.blurple)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self._check_cooldown(interaction)
        await interaction.response.defer()

        bot: DiscordOsuBot = interaction.client
        profile_cog = bot.get_cog('Profile')
        await profile_cog._profile_core(interaction, osu_username=None)

    async def _check_cooldown(self, interaction: Interaction):
        user_id = interaction.user.id
        if user_id in profile_extras_user_cooldowns:
            if datetime.datetime.now() < profile_extras_user_cooldowns[user_id] + profile_extras_cooldown_secs:
                retry_after = profile_extras_user_cooldowns[
                                  user_id] + profile_extras_cooldown_secs - datetime.datetime.now()
                raise commands.CommandOnCooldown(cooldown=None, retry_after=retry_after.total_seconds(),
                                                 type=commands.BucketType.user)
        profile_extras_user_cooldowns[user_id] = datetime.datetime.now()

    async def on_error(self, error: Exception, item: Item, interaction: Interaction) -> None:
        logger.error(f'Error in {self.__class__.__name__}', exc_info=error)

        embed = nextcord.Embed(title="An error occurred", colour=0xFF0000)
        embed.description = str(error)
        await interaction.send(embed=embed)
