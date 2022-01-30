import datetime
import logging
import os
import sqlite3

import aiosqlite

from toxic_bot.helpers.primitives import singleton

logger = logging.getLogger('toxic-bot')


@singleton
class Database:

    def __init__(self, db_path='toxic_bot.db'):
        self.db_path = db_path
        self.conn = None
        self.c = None

    async def initialize(self):
        """
        Initialize database
        :return: Creates tables
        """
        os.makedirs(os.path.split(self.db_path)[0], exist_ok=True)
        self.c = await aiosqlite.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.c.row_factory = aiosqlite.Row
        await self.c.execute('pragma journal_mode=wal')
        await self.c.execute("CREATE TABLE IF NOT EXISTS prefixes (guild_id INTEGER, prefix TEXT)")
        await self.c.execute("CREATE TABLE IF NOT EXISTS osu_players "
                             "(discord_id INTEGER, "
                             "osu_username TEXT, "
                             "osu_id INTEGER, "
                             "last_updated TIMESTAMP, "
                             "ping_me INTEGER)")
        await self.c.commit()
        logger.debug("Created tables")

    async def get_prefix(self, guild_id: int):
        """
        Get server prefix from database
        :param guild_id: Discord server id
        :return: Prefix of the server
        """
        cursor = await self.c.execute(f"SELECT prefix FROM prefixes WHERE guild_id=?", [guild_id])
        return await cursor.fetchone()

    async def set_prefix(self, guild_id: int, new_prefix: str):
        """
        Set new prefix for a server
        :param guild_id: Discord server id
        :param new_prefix: New prefix to be set
        :return: Insert prefix into database
        """
        cursor = await self.c.execute(f"SELECT prefix FROM prefixes WHERE guild_id=?", [guild_id])
        prefix = await cursor.fetchone()
        if prefix is None:
            await self.c.execute(f"INSERT INTO prefixes VALUES (?, ?)", [guild_id, new_prefix])
            logger.debug(f"Inserted {guild_id, new_prefix} into prefixes")
        else:
            await self.c.execute(f"UPDATE prefixes SET prefix=? WHERE guild_id=?", [new_prefix, guild_id])
            logger.debug(f"Updated prefix to {new_prefix} into prefixes of {guild_id}")
        await self.c.commit()

    async def get_user(self, discord_id: int):
        """
        Get user properties from database
        :param discord_id: Discord user id
        :return: Osu related properties of user
        """
        cursor = await self.c.execute(f"SELECT * FROM osu_players WHERE discord_id=?", [discord_id])
        return await cursor.fetchone()

    async def get_user_by_username(self, osu_username: str):
        """
        Get user properties from database
        :param osu_username: Player username
        :return: Osu related properties of user
        """
        cursor = await self.c.execute(f"SELECT * FROM osu_players WHERE osu_username=?", [osu_username])
        return await cursor.fetchone()

    async def add_user(self, discord_id: int, osu_username: str, osu_id: int,
                 ping_me: bool = False):
        """
        Add or update new user to the database
        :param discord_id: Discord user id
        :param osu_username: osu! username
        :param osu_id: osu! user id
        :param ping_me: Whether to ping user for tournaments
        :return: Insert new user into database
        """
        last_updated = datetime.datetime.now()
        cursor = await self.c.execute(f"SELECT * FROM osu_players WHERE discord_id=?", [discord_id])
        user = await cursor.fetchone()
        if user is None:
            await self.c.execute(f"INSERT INTO osu_players "
                                 f"(discord_id, osu_username, osu_id ,last_updated, ping_me) "
                                 f"VALUES (?, ?, ?, ?, ?)",
                                 [discord_id, osu_username, osu_id, last_updated, ping_me])
            logger.debug(f"Inserted {osu_username} into osu_players")
        else:
            await self.c.execute(
                f"UPDATE osu_players SET "
                f"osu_username=?, osu_id=?,"
                f"last_updated=?, ping_me=? WHERE discord_id=?",
                [osu_username, osu_id, last_updated, ping_me, discord_id])
            logger.debug(f"Updated {osu_username} in osu_players")

        await self.c.commit()
        return

    async def close(self):
        """
        Closes the database connection
        """
        await self.c.close()
        logger.debug('Closed database connection')
        return