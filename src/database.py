import datetime
import logging
import os
import sqlite3
from typing import List

from ossapi import User

from helpers.config import Config

logger = logging.getLogger('toxic-bot')

config = Config()
db_path = config["GENERAL"]["database_path"]


class DatabaseSingleton(object):
    """
    Creates a singleton database class
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseSingleton, cls).__new__(cls)
        return cls._instance


class Database(DatabaseSingleton):

    def __init__(self, db_path=db_path):
        os.makedirs(os.path.split(db_path)[0], exist_ok=True)
        self.conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.initialize()

    def initialize(self):
        """
        Initialize database
        :return: Creates tables
        """
        self.c.execute("CREATE TABLE IF NOT EXISTS prefixes (guild_id INTEGER, prefix TEXT)")
        self.c.execute("CREATE TABLE IF NOT EXISTS osu_players "
                       "(discord_id INTEGER, "
                       "osu_username TEXT, "
                       "osu_id INTEGER, "
                       "osu_rank INTEGER, "
                       "osu_badges TEXT, "
                       "last_updated TIMESTAMP, "
                       "ping_me INTEGER)")
        self.c.execute("CREATE TABLE IF NOT EXISTS links (discord_id INTEGER, osu_id INTEGER)")
        self.conn.commit()
        logger.debug("Created tables")

    def get_prefix(self, guild_id: int):
        """
        Get server prefix from database
        :param guild_id: Discord server id
        :return: Prefix of the server
        """
        return self.c.execute(f"SELECT prefix FROM prefixes WHERE guild_id=?", [guild_id]).fetchone()

    def set_prefix(self, guild_id: int, new_prefix: str):
        """
        Set new prefix for a server
        :param guild_id: Discord server id
        :param new_prefix: New prefix to be set
        :return: Insert prefix into database
        """
        prefix = self.c.execute(f"SELECT prefix FROM prefixes WHERE guild_id=?", [guild_id]).fetchone()
        if prefix is None:
            self.c.execute(f"INSERT INTO prefixes VALUES (?, ?)", [guild_id, new_prefix])
            self.conn.commit()
            logger.debug(f"Inserted {guild_id, new_prefix} into prefixes")
        else:
            self.c.execute(f"UPDATE prefixes SET prefix=? WHERE guild_id=?", [new_prefix, guild_id])
            self.conn.commit()
            logger.debug(f"Updated prefix to {new_prefix} into prefixes of {guild_id}")

    def get_user(self, discord_id: int):
        """
        Get user properties from database
        :param discord_id: Discord user id
        :return: Osu related properties of user
        """
        return self.c.execute(f"SELECT * FROM osu_players WHERE discord_id=?", [discord_id]).fetchone()

    def get_user_by_username(self, osu_username: str):
        """
        Get user properties from database
        :param osu_username: Player username
        :return: Osu related properties of user
        """
        return self.c.execute(f"SELECT * FROM osu_players WHERE osu_username=?", [osu_username]).fetchone()

    def add_user(self, discord_id: int, osu_username: str, osu_id: int, osu_rank: int,
                 osu_badges: int,
                 ping_me: bool = False):
        """
        Add or update new user to the database
        :param discord_id: Discord user id
        :param osu_username: osu! username
        :param osu_id: osu! user id
        :param osu_rank: osu! rank
        :param osu_badges: osu! badges
        :param ping_me: Whether to ping user for tournaments
        :return: Insert new user into database
        """
        last_updated = datetime.datetime.now()
        user = self.c.execute(f"SELECT * FROM osu_players WHERE discord_id=?", [discord_id]).fetchone()
        if user is None:
            self.c.execute(f"INSERT INTO osu_players "
                           f"(discord_id, osu_username, osu_id, osu_rank, osu_badges, last_updated, ping_me) "
                           f"VALUES (?, ?, ?, ?, ?, ?, ?)",
                           [discord_id, osu_username, osu_id, osu_rank, osu_badges, last_updated, ping_me])
            self.conn.commit()
            logger.debug(f"Inserted {osu_username} into osu_players")
        else:
            self.c.execute(
                f"UPDATE osu_players SET "
                f"osu_username=?, osu_id=?,"
                f"osu_rank=?, osu_badges=?,"
                f"last_updated=?, ping_me=? WHERE discord_id=?",
                [osu_username, osu_id, osu_rank, osu_badges, last_updated, ping_me, discord_id])
            self.conn.commit()
            logger.debug(f"Updated {osu_username} in osu_players")
        return

    def get_player(self, username: str):
        """
        Get user properties from database
        :param username: Player username
        :return: Osu related properties of user
        """
        uname = username.lower()
        return self.c.execute(f"SELECT * FROM osu_players WHERE osu_username=?", [uname]).fetchone()

    def set_player(self, player: User, discord_id=None):
        """
        Set user properties on database
        :param player: Player object
        :param discord_id: Discord id of the linked player
        :return: Sets osu related properties of user
        """
        osu_id = player.id
        osu_username = player.username
        last_updated = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        country = player.country_code
        badges = len(player.badges)

        result = self.c.execute(f"SELECT * FROM osu_players WHERE osu_id=?", [osu_id]).fetchone()

        if result is None:
            self.c.execute(f"INSERT INTO osu_players VALUES (?, ?, ?, ?, ?, ?)",
                           [discord_id, osu_username, osu_id, last_updated, country, badges])
            self.conn.commit()
            logger.debug('Inserted {} into osu_players'.format(player))
        else:
            self.c.execute(f"UPDATE osu_players SET discord_id=?, osu_username=?, last_updated=?, country=?, badges=?",
                           [discord_id, osu_username, last_updated, country, badges])
            self.conn.commit()
            logger.debug('Updated {} in osu_players'.format(player))
        return

    def get_link(self, discord_id: int):
        """
        Get linked osu profile from discord id
        :param discord_id: Discord user id
        :return: Osu profile id of discord user
        """
        return self.c.execute(f"SELECT * FROM links WHERE discord_id=?", [discord_id]).fetchone()

    def set_link(self, discord_id: int, osu_id: int):
        """
        Links user osu profile with their discord id
        :param discord_id: Discord user id
        :param osu_id: Osu id of the linked player
        :return: Osu profile id of discord user
        """
        result = self.c.execute(f"SELECT * FROM links WHERE discord_id=?", [discord_id]).fetchone()

        if result is None:
            self.c.execute(f"INSERT INTO links VALUES (?, ?)", [discord_id, osu_id])
            self.conn.commit()
            logger.debug('Inserted {} into links'.format(osu_id))
        else:
            self.c.execute(f"UPDATE links SET osu_id=? WHERE discord_id=?", [osu_id, discord_id])
            self.conn.commit()
            logger.debug('Updated {} in links'.format(osu_id))
        return

    def delete_link(self, discord_id: int):
        """
        Deletes linked osu profile associated with discord id
        :param discord_id: Discord user id
        """
        self.c.execute(f"DELETE FROM links WHERE discord_id=?", [discord_id])
        self.conn.commit()
        logger.debug('Deleted {} from links'.format(discord_id))
        return
