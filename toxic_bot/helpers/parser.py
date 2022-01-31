from nextcord.ext.commands import CommandError


class ParserExceptionNoUserFound(CommandError):
    pass


class ParserExceptionBadMode(CommandError):
    pass


class ParserExceptionBadPlayNo(CommandError):
    pass
