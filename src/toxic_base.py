import os
import logging
from database import Database
from discord.ext import commands

db = Database(os.environ["DB_PATH"])


def get_prefix(bot, message):
    """Gets the prefixes linked with servers from the database."""

    prefixes = db.get_prefix(message.guild.id)
    if prefixes is None:
        prefixes = ["*"]

    # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, description="* is my default prefix")


@bot.command(name="prefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix):
    """
    Sets the prefix for this server.

    prefix: New prefix
    return: A message if successful, an error if fails.
    """

    db.set_prefix(ctx.guild.id, prefix)

    await ctx.send(f"Succesfully changed prefix to: `{prefix}`")

    return


initial_extensions = ['cogs.score',
                      'cogs.map',
                      'cogs.profile']

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

bot.run(os.environ["TOKEN"], bot=True, reconnect=True)