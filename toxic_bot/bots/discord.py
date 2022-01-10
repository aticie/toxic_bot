from typing import List

from nextcord.ext import commands

from toxic_bot.helpers.database import Database
from toxic_bot.helpers.osu_api import OsuApiV2


class DiscordOsuBot(commands.Bot):

    def __init__(self, db_path: str, default_prefix: str,
                 osu_client_id, osu_client_secret, *args, **kwargs):
        super().__init__(command_prefix=self.get_prefix, *args, **kwargs)
        self.db = Database(db_path)
        self.default_prefix = default_prefix
        self.api = OsuApiV2(osu_client_id, osu_client_secret)

    async def close(self) -> None:
        await super().close()
        await self.db.close()
        await self.api.close()

    async def get_prefix(self, message):
        """Gets the prefixes linked with servers from the database."""

        prefixes = await self.db.get_prefix(message.guild.id)
        if prefixes is None:
            prefixes = [self.default_prefix]

        # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
        return commands.when_mentioned_or(*prefixes)(self, message)

    async def set_prefix(self, guild_id: int, prefix: str):
        """Sets the prefix for a guild."""
        await self.db.set_prefix(guild_id, prefix)

    async def on_ready(self):
        print(f'Logged in as: {self.user.name} - {self.user.id}')
        await self.db.initialize()
