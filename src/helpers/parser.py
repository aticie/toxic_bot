import os
from typing import List

from discord.ext.commands import BadArgument
from discord import Member

from database import Database


class Parser:

    def __init__(self, ctx):
        self.ctx = ctx
        self.user = None
        self.is_multi = False
        self.game_mode = 0
        self.which_play = 0
        self.db = Database(os.environ["DB_PATH"])

    async def parse_args(self, args: tuple, mentions: List[Member]):

        args = list(args)
        prefix = self.db.get_prefix(self.ctx.guild.id)
        prefix = "*" if prefix is None else prefix[0]

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
                self.game_mode = int(args[args.index("-m") + 1])
                if self.game_mode not in [0, 1, 2, 3]:
                    self.game_mode = 0
                    await self.ctx.send(f"Argument after -m must be one of [0, 1, 2, 3].")
                    raise ParserExceptionBadMode
            except (ValueError, IndexError):
                await self.ctx.send(f"Argument after -m must exist and must be one of [0, 1, 2, 3].")
                raise ParserExceptionBadMode

            del args[args.index("-m") + 1]
            args.remove("-m")

        if len(mentions) > 0:
            self.user = mentions[0]
            user_or_none = self.db.get_user(self.user.id)
            if user_or_none is None:
                self.user = self.user.display_name
            else:
                self.user = user_or_none[1]

        elif len(args) == 1:
            self.user = args[0]
        elif len(args) > 0:
            self.user = " ".join(args)
        else:
            user_or_none = self.db.get_user(self.ctx.author.id)
            if user_or_none is None:
                await self.ctx.send(f"You should link your profile first. Usage: `{prefix}link <osu_username>`")
                raise ParserExceptionNoUserFound
            else:
                self.user = user_or_none[1]

        return


class ParserExceptionNoUserFound(Exception):

    def __init__(self):
        super().__init__()


class ParserExceptionBadMode(Exception):

    def __init__(self):
        super().__init__()


class ParserExceptionBadPlayNo(Exception):

    def __init__(self):
        super().__init__()
