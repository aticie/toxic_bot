from discord.ext import commands


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Profile(bot))
