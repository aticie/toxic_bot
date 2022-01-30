import logging

import nextcord
from nextcord import Interaction
from nextcord.ui import Item

from toxic_bot.bots.discord import DiscordOsuBot
from toxic_bot.cogs.map_interactions import MapInteractions

logger = logging.getLogger('toxic-bot')


class ScoreExtrasDropdown(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label='Compare', description='Shows your score on this map.', emoji='🟥'),
            nextcord.SelectOption(label='Map info', description='Shows information about the map.', emoji='🟩'),
            nextcord.SelectOption(label='Profile', description=f'Shows the profile of the user.', emoji='🟦')
        ]
        super().__init__(placeholder='Choose extra options...', options=options)

    async def callback(self, interaction: nextcord.Interaction):

        await interaction.response.defer()
        logger.debug(f'{interaction.user.name} selected {self.values[0]}')

        bot: DiscordOsuBot = interaction.client

        if self.values[0] == 'Compare':
            score_cog = bot.get_cog('ScoreInteractions')
            await score_cog._compare_core(interaction)
        elif self.values[0] == 'Map info':
            map_cog: MapInteractions = bot.get_cog('MapInteractions')
            await map_cog._map_info_core(interaction)
        elif self.values[0] == 'Profile':
            author_name = interaction.message.embeds[0].author.name
            played_by = ' '.join(author_name.split(' ')[2:])
            await bot.get_cog('Profile')._profile_core(interaction, played_by)

        return


class ScoreExtrasView(nextcord.ui.View):
    def __init__(self):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(ScoreExtrasDropdown())

    async def on_error(self, error: Exception, item: Item, interaction: Interaction) -> None:
        logger.error(f'Error in {self.__class__.__name__}', exc_info=error)

        embed = nextcord.Embed(title="An error occurred", colour=0xFF0000)
        embed.description = str(error)
        await interaction.send(embed=embed)
