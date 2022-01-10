import logging

from nextcord.ext import commands

from toxic_bot.bots.discord import DiscordOsuBot

logger = logging.getLogger('toxic-bot')


class Profile(commands.Cog):
    def __init__(self, bot: DiscordOsuBot):
        self.bot = bot
        self.api = self.bot.api
        self.db = self.bot.db

    @commands.command(name="link")
    async def link(self, ctx, osu_username: str):
        """Link the discord account to user's osu! account"""
        user_details = self.api.user(osu_username)
        await self.db.set_link(discord_id=ctx.author.id, osu_id=user_details.id)

        await self.db.add_user(discord_id=ctx.author.id,
                               osu_username=osu_username,
                               osu_id=user_details.id,
                               osu_rank=user_details.statistics.global_rank,
                               osu_badges=len(user_details.badges) if user_details is not None else 0)
        logger.info(f"{ctx.author.name} linked to {osu_username}")
        await ctx.reply(f"Linked your profile to `{osu_username}`")


def setup(bot):
    bot.add_cog(Profile(bot))
