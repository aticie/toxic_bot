import argparse
import logging

import nextcord
from nextcord.ext import commands
from nextcord.ext.commands import Context, errors

from toxic_bot.bots.discord import DiscordOsuBot
from toxic_bot.helpers.parser import ParserExceptionNoUserFound

parser = argparse.ArgumentParser(description='Arguments required for running toxic-bot')
parser.add_argument('--discord_token',
                    type=str,
                    help='Discord bot token. You can get it from '
                         'https://discordapp.com/developers/applications/me',
                    required=True)
parser.add_argument('--log_level', type=str, default='INFO', help='Log level. Default is INFO.')
parser.add_argument('--database_path', type=str, default='./database/database.db',
                    help='Path to database file.')
parser.add_argument('--default_prefix', type=str, default='*', help='Default prefix for commands.')
parser.add_argument('--client_id', type=str, default='', help='Client ID for the osu!api v2.')
parser.add_argument('--client_secret', type=str, default='', help='Client secret for the osu!api v2.')

args = parser.parse_args()

logger = logging.getLogger("toxic-bot")
logger.setLevel(args.log_level.upper())

default_prefix = args.default_prefix

db_path = args.database_path

initial_extensions = ["cogs.score",
                      "cogs.map",
                      "cogs.profile"]

bot = DiscordOsuBot(db_path=db_path,
                    default_prefix=default_prefix,
                    osu_client_id=args.client_id,
                    osu_client_secret=args.client_secret,
                    case_insensitive=True,
                    description=f"{default_prefix} is my default prefix")


@bot.command(name="prefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx: nextcord.ext.commands.Context, prefix):
    """
    Sets the prefix for this server.

    prefix: New prefix
    return: A message if successful, an error if fails.
    """
    await ctx.bot.set_prefix(ctx.guild.id, prefix)
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

@bot.check
async def check_if_bot_is_ready(ctx: Context):
    """
    Checks if the bot is ready.
    """
    return ctx.bot.is_ready()


if __name__ == "__main__":
    for extension in initial_extensions:
        bot.load_extension(extension)

intents = nextcord.Intents.all()
bot.run(args.discord_token, reconnect=True)