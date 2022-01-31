from nextcord import Interaction
from nextcord.ext import commands

from toxic_bot.bots.discord import DiscordOsuBot
from toxic_bot.cards.mapcard import MapCardFactory


class MapInteractions(commands.Cog):
    def __init__(self, bot):
        self.bot: DiscordOsuBot = bot

    async def _map_info_core(self, interaction: Interaction) -> dict:
        embed_footer = interaction.message.embeds[0].footer.text
        beatmap_id = int(embed_footer.split('|')[-1].split(',')[0])
        beatmap_info = await self.bot.api.get_beatmap(beatmap_id)
        map_card = MapCardFactory(beatmap_info).get_card()
        embed = await map_card.to_embed()
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(MapInteractions(bot))
