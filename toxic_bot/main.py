import argparse
import logging
import sys
import traceback

import nextcord
from nextcord import Interaction
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
parser.add_argument('--default_prefix', type=str, default='*', help='Default prefix for commands.')
parser.add_argument('--client_id', type=str, default='', help='Client ID for the osu!api v2.')
parser.add_argument('--client_secret', type=str, default='', help='Client secret for the osu!api v2.')
parser.add_argument('--redirect_uri', type=str, default='https://auth.ronnia.me/',
                    help='Redirect uri, required for linking osu! account.')

args = parser.parse_args()

logger = logging.getLogger("toxic-bot")
logger.setLevel(args.log_level.upper())
loggers_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(process)d | %(name)s | %(funcName)s | %(message)s',
    datefmt='%d/%m/%Y %I:%M:%S')

ch = logging.StreamHandler()
ch.setFormatter(loggers_formatter)

logger.addHandler(ch)
# logger.propagate = False

default_prefix = args.default_prefix

initial_extensions = ["cogs.score_interactions",
                      "cogs.map_interactions",
                      "cogs.profile"]

bot = DiscordOsuBot(default_prefix=default_prefix,
                    osu_client_id=args.client_id,
                    osu_client_secret=args.client_secret,
                    case_insensitive=True,
                    description=f"{default_prefix} is my default prefix",
                    osu_redirect_uri=args.redirect_uri)


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
    logger.error(f"{ctx.author} in {ctx.guild} failed to execute {ctx.command} with error.", exc_info=exception)
    embed = nextcord.Embed(title="An error occurred", colour=0xFF0000)

    if isinstance(exception, errors.BadArgument):
        embed.description = f"Invalid argument: {exception}"
    elif isinstance(exception, ParserExceptionNoUserFound):
        embed.description = f"{exception}"
    elif isinstance(exception, commands.CommandOnCooldown):
        embed.description = f"You are on cooldown, please try again in {exception.retry_after} seconds later."
    else:
        embed.description = f"Details: {exception}"

    await ctx.send(embed=embed)

@bot.event
async def on_application_command_error(interaction: Interaction, exception: nextcord.ApplicationError):
    """
    Logs errors to the console and sends a message to chat.
    """
    logger.error(f"{interaction.user} in {interaction.guild} failed to execute {interaction.application_command}"
                 f" with error.", exc_info=exception)
    embed = nextcord.Embed(title="An error occurred", colour=0xFF0000)

    if isinstance(exception, nextcord.ApplicationInvokeError):
        embed.description = f"{exception.original}"
    else:
        embed.description = f"{exception}"

    await interaction.send(embed=embed)



@bot.event
async def on_error(event: str, *args, **kwargs):
    exception = sys.exc_info()
    logger.error(f"An error occurred in {event} with args: {args} and kwargs: {kwargs}", exc_info=exception)

    embed = nextcord.Embed(title="An error occurred", colour=0xFF0000)

    if event == 'on_interaction':
        interaction: Interaction = args[0]
        exception_text = str(exception[1])
        embed.description = exception_text
        await interaction.send(embed=embed)


@commands.check
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
