from typing import Iterable

import nextcord.ui
from nextcord import Embed


class PaginatedView(nextcord.ui.View):
    
    def __init__(self, embeds: Iterable[Embed]):
        super(PaginatedView, self).__init__(timeout=None)
        self.embeds = embeds
        self.embed_idx = 0

    @nextcord.ui.button(label="Previous", style=nextcord.ButtonStyle.primary)
    async def previous(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        self.embed_idx = max(self.embed_idx - 1, 0)
        await interaction.message.edit(embed=self.embeds[self.embed_idx])

    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.primary)
    async def next(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        self.embed_idx = min(self.embed_idx + 1, len(self.embeds) - 1)
        await interaction.message.edit(embed=self.embeds[self.embed_idx])
