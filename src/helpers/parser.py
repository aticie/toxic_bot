from typing import List

from nextcord import Member
from nextcord.ext.commands import BadArgument, CommandError

from database import Database
from helpers.config import Config
from helpers.ossapi_wrapper import api

config = Config()


class Parser:

    def __init__(self, ctx):
        self.ctx = ctx
        self.username = None
        self.user_id = None
        self.is_multi = False
        self.game_mode = 'osu'
        self.which_play = 0
        self.db = Database()

    async def parse_args(self, args: tuple, mentions: List[Member]):

        args = list(args)
        prefix = self.db.get_prefix(self.ctx.guild.id)
        prefix = config["DISCORD"]["defaultprefix"] if prefix is None else prefix[0]

        if "-l" in args:
            if "-p" in args:
                raise BadArgument("-p and -l can\'t be used together.")
            self.is_multi = True
            args.remove("-l")

        if "-p" in args:
            try:
                self.which_play = int(args[args.index("-p") + 1]) - 1
                if 0 > self.which_play > 99:
                    self.which_play = 0
                    await self.ctx.send(f"Argument after -p must be within 1-100.")
                    raise ParserExceptionBadPlayNo
            except (ValueError, IndexError):
                await self.ctx.send(f"Argument after -p must exist and must be within 1-100.")
                raise ParserExceptionBadPlayNo

            del args[args.index("-p") + 1]
            args.remove("-p")

        if "-m" in args:
            try:
                self.game_mode = args[args.index("-m") + 1]
                if self.game_mode not in ['osu', 'mania', 'taiko', 'fruits']:
                    self.game_mode = 'osu'
                    await self.ctx.send(
                        f"Argument after -m must be one of ['osu', 'taiko', 'fruits', 'mania']. Defaulting to osu.")
                else:
                    del args[args.index("-m") + 1]

            except (ValueError, IndexError):
                raise ParserExceptionBadMode(
                    f"Argument after -m must exist and must be one of ['osu', 'taiko', 'fruits', 'mania'].")

            args.remove("-m")

        if len(mentions) > 0:
            discord_user = mentions[0]
            user_or_none = self.db.get_user(discord_user.id)
            if user_or_none is None:
                raise ParserExceptionNoUserFound(f'{discord_user.display_name} has not linked their osu! account.')
            else:
                self.username = user_or_none['osu_username']
                self.user_id = user_or_none['osu_id']

        elif len(args) == 1:
            self.username = args[0]
        elif len(args) > 0:
            self.username = " ".join(args)
        else:
            user_or_none = self.db.get_user(self.ctx.author.id)
            if user_or_none is None:
                raise ParserExceptionNoUserFound(f'You should link your profile first. Usage: `{prefix}link <osu_username>`')
            else:
                self.username = user_or_none['osu_username']
                self.user_id = user_or_none['osu_id']

        if self.username.isdigit():
            self.user_id = int(self.username)
        else:
            user_details = api.user(self.username)
            self.user_id = user_details.id

        return


class ParserExceptionNoUserFound(CommandError):
    pass


class ParserExceptionBadMode(CommandError):
    pass


class ParserExceptionBadPlayNo(CommandError):
    pass
