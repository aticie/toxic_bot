import sys
import traceback

from nextcord.ext.commands import Context, errors

from helpers.config import Config
import logging

import nextcord
from nextcord.ext import commands

from database import Database
from helpers.parser import ParserExceptionNoUserFound

config = Config()
default_prefix = config["DISCORD"]["defaultprefix"]

logger = logging.getLogger("toxic-bot")
logger.setLevel(config["GENERAL"]["loglevel"].upper())

db = Database()


def get_prefix(bot, message):
    """Gets the prefixes linked with servers from the database."""

    prefixes = db.get_prefix(message.guild.id)
    if prefixes is None:
        prefixes = [default_prefix]

    # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True,
                   description=f"{default_prefix} is my default prefix")


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


@bot.event
async def on_command_error(ctx: Context, exception: errors.CommandError):
    """
    Logs errors to the console.
    """

    logger.error(f"{ctx.author} in {ctx.guild} failed to execute {ctx.command} with error: {exception}")

    if isinstance(exception, errors.BadArgument):
        await ctx.send(f"Invalid argument: {exception}")
        return

    if isinstance(exception, ParserExceptionNoUserFound):
        await ctx.send(f'{exception}')

    if isinstance(exception, errors.CommandError):
        await ctx.send(f"An error occurred: {exception}")

initial_extensions = ["cogs.score",
                      "cogs.map",
                      "cogs.profile"]

if __name__ == "__main__":
    for extension in initial_extensions:
        bot.load_extension(extension)


intents = nextcord.Intents.all()
bot.run(config["DISCORD"]["token"], reconnect=True)
