import logging

import aioredis

from toxic_bot.helpers.primitives import singleton

logger = logging.getLogger('toxic-bot')


@singleton
class Database:

    def __init__(self, redis_url):
        self.redis_url = redis_url
        self.conn = None
        self.c = None

    async def initialize(self):
        """
        Initialize database
        :return: Creates tables
        """
        self.c = aioredis.from_url(self.redis_url)
        logger.debug(f"Connected to redis {self.redis_url}")

    async def set_encrypt_key(self, encryption_key: bytes):
        await self.c.set("encrypt_key", encryption_key.decode("utf-8"))
        return

    async def get_encrypt_key(self) -> bytes:
        return await self.c.get("encrypt_key").encode("utf-8")

    async def get_prefix(self, guild_id: int):
        """
        Get server prefix from database
        :param guild_id: Discord server id
        :return: Prefix of the server
        """
        prefix = await self.c.get(f"{guild_id}")
        return prefix

    async def set_prefix(self, guild_id: int, new_prefix: str):
        """
        Set new prefix for a server
        :param guild_id: Discord server id
        :param new_prefix: New prefix to be set
        :return: Insert prefix into database
        """
        await self.c.set(f"{guild_id}", new_prefix)
        logger.debug(f"Set prefix of {guild_id} to {new_prefix}")

    async def get_user(self, discord_id: int):
        """
        Get user properties from database
        :param discord_id: Discord user id
        :return: Osu related properties of user
        """
        return await self.c.hgetall(f"{discord_id}")

    async def close(self):
        """
        Closes the database connection
        """
        await self.c.close()
        logger.debug('Closed database connection')
        return
