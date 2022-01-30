import logging
from typing import Optional, Union
import urllib.parse

import nextcord
from nextcord import SlashOption, Interaction
from nextcord.ext import commands
from nextcord.ext.commands import Context

from toxic_bot.bots.discord import DiscordOsuBot
from toxic_bot.cards.profilecard import ProfileCardFactory
from toxic_bot.helpers.database import Database
from toxic_bot.helpers.osu_api import OsuApiV2
from toxic_bot.views.profile_extras import ProfileExtrasView
from toxic_bot.helpers.crypto import encrypt

logger = logging.getLogger('toxic-bot')


class Profile(commands.Cog):
    def __init__(self, bot: DiscordOsuBot):
        self.bot = bot
        self.api: OsuApiV2 = self.bot.api
        self.db: Database = self.bot.db

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="link")
    async def link(self, ctx: Context):
        """Link the discord account to user's osu! account"""
        embed = await self._link_core(ctx.author.id)
        await ctx.author.send(embed=embed)

    @nextcord.slash_command(guild_ids=[...], name="link",
                            description="Links your osu! account to your discord account.")
    async def link_slash(self, interaction: Interaction):
        """Link the discord account to user's osu! account"""
        embed = await self._link_core(interaction.user.id)
        await interaction.send(embed=embed, ephemeral=True)

    async def _link_core(self, discord_id: int):
        # Encrypt the discord id using the bot's key
        encrypted_id = encrypt(self.bot.encryption_key, discord_id).decode('utf-8')
        params = {
            'client_id': self.api._osu_client_id,
            'redirect_uri': self.bot.osu_redirect_uri,
            'state': encrypted_id,
            'response_type': 'code',
            'scope': 'identify'
        }
        url_query = urllib.parse.urlencode(params)
        url = urllib.parse.urlparse(f'https://osu.ppy.sh/oauth/authorize')
        url = url._replace(query=url_query)
        embed = nextcord.Embed(title='Link your osu! account',
                               description=f'[Click here]({urllib.parse.urlunparse(url)}) to link your discord account to your osu! account.')
        return embed

    @nextcord.slash_command(guild_ids=[...], name="profile",
                            description="Shows the specified user's osu! profile.")
    async def profile_slash(self, interaction: Interaction,
                            osu_username: str = SlashOption(
                                name="name",
                                description="Specify the username or mention the player",
                                required=False),
                            mode: str = SlashOption(
                                name="mode",
                                description="Specify the game mode",
                                required=False,
                                default="osu",
                                choices=["osu", "taiko", "fruits", "mania"])):
        await interaction.response.defer()
        await self._profile_core(interaction, osu_username)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="osu")
    async def profile(self, ctx: Context, osu_username: Optional[str], mode: str = 'osu'):
        """Shows the specified user's osu! profile"""
        await self._profile_core(ctx, osu_username)

    async def get_user_details(self, interaction: Union[Context, Interaction], name: str):
        user_from_db = await self.bot.get_user_from_db(interaction, name)

        if user_from_db is None:
            user_details = await self.api.get_user(name, key='username')
        else:
            user_details = await self.api.get_user(user_from_db['osu_id'])

        return user_details

    async def _profile_core(self, interaction: Interaction, osu_username: Optional[str]):
        user_details = await self.get_user_details(interaction, osu_username)
        profile_card = ProfileCardFactory(user_details).get_card()
        embed, file = await profile_card.to_embed()
        view = ProfileExtrasView()
        await interaction.send(embed=embed, file=file, view=view)


def setup(bot):
    bot.add_cog(Profile(bot))
