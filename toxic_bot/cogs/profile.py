import logging
from typing import Optional

import nextcord
from nextcord import SlashOption, Interaction
from nextcord.ext import commands
from nextcord.ext.commands import Context

from toxic_bot.bots.discord import DiscordOsuBot
from toxic_bot.cards.profilecard import ProfileCardFactory
from toxic_bot.helpers.database import Database
from toxic_bot.helpers.osu_api import OsuApiV2

logger = logging.getLogger('toxic-bot')


class Profile(commands.Cog):
    def __init__(self, bot: DiscordOsuBot):
        self.bot = bot
        self.api: OsuApiV2 = self.bot.api
        self.db: Database = self.bot.db

    @commands.command(name="link")
    async def link(self, ctx: Context, osu_username: str):
        """Link the discord account to user's osu! account"""
        await self._link_core(osu_username, ctx.author.id)
        await ctx.message.add_reaction('👍')

    @nextcord.slash_command(guild_ids=[571853176752308244], name="link",
                            description="Links your osu! account to your discord account.")
    async def link_slash(self, interaction: Interaction,
                         osu_username: str = SlashOption(
                             name="name",
                             description="Your osu! username",
                             required=True)):
        """Link the discord account to user's osu! account"""
        await self._link_core(osu_username, interaction.user.id)
        embed = nextcord.Embed(title="Link successful!",
                               description=f'Successfully linked your profile to `{osu_username}`.')
        await interaction.send(embed=embed, ephemeral=True)

    async def _link_core(self, osu_username: str, discord_id: int):
        user_details = await self.api.get_user(osu_username, key='username')
        await self.db.add_user(discord_id=discord_id,
                               osu_username=osu_username,
                               osu_id=user_details.id)

    @nextcord.slash_command(guild_ids=[571853176752308244], name="profile",
                            description="Shows the specified user's osu! profile.")
    async def profile_slash(self, interaction: Interaction,
                            osu_username: str = SlashOption(
                                name="name",
                                description="Specify the username or mention of the player",
                                required=False),
                            mode: str = SlashOption(
                                name="mode",
                                description="Specify the game mode",
                                required=False,
                                default="osu",
                                choices=["osu", "taiko", "fruits", "mania"])):
        await interaction.response.defer()
        embed, file = await self._profile_core(interaction.user, osu_username)
        await interaction.send(embed=embed, file=file)

    async def _profile_core(self, discord_user: nextcord.User, osu_username: Optional[str]):
        if osu_username is None:
            user_db = await self.db.get_user(discord_user.id)
            user_details = await self.api.get_user(user_db['osu_id'])
        else:
            user_details = await self.api.get_user(osu_username, key='username')
        profile_card = ProfileCardFactory(user_details).get_card()
        embed, file = await profile_card.to_embed()
        return embed, file

    @commands.command(name="osu")
    async def profile(self, ctx: Context, osu_username: Optional[str], mode: str = 'osu'):
        """Shows the specified user's osu! profile"""
        embed, file = await self._profile_core(ctx.author, osu_username)
        await ctx.send(embed=embed, file=file)


def setup(bot):
    bot.add_cog(Profile(bot))
