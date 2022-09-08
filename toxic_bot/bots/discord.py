import logging
import os
from abc import ABC
from typing import Union

from nextcord import Interaction
from nextcord.ext import commands
from nextcord.ext.commands import Context

from toxic_bot.helpers.crypto import generate_encryption_key
from toxic_bot.helpers.database import Database
from toxic_bot.helpers.osu_api import OsuApiV2
from toxic_bot.helpers.parser import ParserExceptionNoUserFound

logger = logging.getLogger('toxic-bot')


class DiscordOsuBot(commands.Bot, ABC):

    def __init__(self, default_prefix: str,
                 osu_client_id: str,
                 osu_client_secret: str,
                 osu_redirect_uri: str,
                 osu_session_key: str,
                 *args, **kwargs):
        super().__init__(command_prefix=self.get_prefix, *args, **kwargs)
        self.db: Database = Database(os.getenv("REDIS_URL"))
        self.default_prefix = default_prefix
        self.osu_client_id = osu_client_id
        self.osu_client_secret = osu_client_secret
        self.osu_redirect_uri = osu_redirect_uri
        self.api = OsuApiV2(osu_client_id, osu_client_secret, osu_session_key)

        # Generate encryption key for web server communication
        self.encryption_key = None
        self.encryption_key_path = '/database/key.bin'

    async def close(self) -> None:
        await super().close()
        await self.db.close()
        await self.api.close()

    async def on_message(self, message):
        await self.wait_until_ready()
        await super(DiscordOsuBot, self).on_message(message)

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
        logger.info(f'Logged in as: {self.user.name} - {self.user.id}')
        await self.db.initialize()
        self.encryption_key = generate_encryption_key(self.encryption_key_path)

    async def get_user_id(self, interaction: Interaction, name: str):

        user_details = await self.get_user_from_db(interaction, name)

        if user_details is None:
            user_from_api = await self.api.get_user(name, key='username')
            user_id = user_from_api.id
        else:
            user_id = user_details['osu_id']

        return user_id

    async def get_user_from_db(self, interaction: Union[Context, Interaction], name: str):
        if isinstance(interaction, Interaction):
            interaction_user = interaction.user
        else:
            interaction_user = interaction.author

        if name is None:
            user_discord_id = interaction_user.id
            user_details = await self._get_user_db(interaction, user_discord_id)
        else:
            if name.startswith('<@'):
                user_discord_id = int(name[2:-1])
                user_details = await self._get_user_db(interaction, user_discord_id)
            else:
                user_details = None

        return user_details

    async def _get_user_db(self, interaction, user_discord_id):

        server_prefix = await self.db.get_prefix(interaction.guild.id)
        if server_prefix is None:
            server_prefix = self.default_prefix

        user_details = await self.db.get_user(user_discord_id)
        if user_details is None:
            raise ParserExceptionNoUserFound(
                f'User <@{user_discord_id}> was not found. '
                f'If this is you, please link your osu! profile with `{server_prefix}link` or /link')

        return user_details
