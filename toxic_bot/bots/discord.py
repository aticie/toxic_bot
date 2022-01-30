import logging
from abc import ABC
from types import SimpleNamespace

from nextcord import Interaction
from nextcord.ext import commands

from toxic_bot.cards.profilecard import ProfileCardFactory
from toxic_bot.helpers.database import Database
from toxic_bot.helpers.osu_api import OsuApiV2
from toxic_bot.helpers.parser import ParserExceptionNoUserFound

logger = logging.getLogger('toxic-bot')


class DiscordOsuBot(commands.Bot, ABC):

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
        test_channel = await self.fetch_channel(609718050543108135)

        user_details = await self.api.get_user('toy', key='username')

        profile_card = ProfileCardFactory(user_details).get_card()
        embed, file = await profile_card.to_embed()
        await test_channel.send(embed=embed, file=file)

    async def get_user_id(self, interaction: Interaction, name: str):

        if name is None:
            user_discord_id = interaction.user.id
            user_details = await self.get_user_details(interaction, user_discord_id)
        else:
            if name.startswith('<@'):
                user_discord_id = int(name[2:-1])
                user_details = await self.get_user_details(interaction, user_discord_id)
            else:
                user_details = await self.api.get_user(name, key='username')
                if user_details is None:
                    raise ParserExceptionNoUserFound(f'User `{name}` was not found.')

        if isinstance(user_details, SimpleNamespace):
            user_id = user_details.id
        else:
            user_id = user_details['osu_id']

        return user_id

    async def get_user_details(self, interaction, user_discord_id):

        server_prefix = await self.db.get_prefix(interaction.guild.id)
        if server_prefix is None:
            server_prefix = self.default_prefix

        user_details = await self.db.get_user(user_discord_id)
        if user_details is None:
            raise ParserExceptionNoUserFound(
                f'User <@{user_discord_id}> was not found. '
                f'If this is you, please link your osu! profile with `{server_prefix}link` or /link')

        return user_details