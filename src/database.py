import sqlite3
import datetime
from typing import List, Any
from data.player import Player
from data.beatmap import Beatmap


class Database:

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()

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
            print(f"Inserted {guild_id, new_prefix} into prefixes")
        else:
            self.c.execute(f"UPDATE prefixes SET prefix=? WHERE guild_id=?", [new_prefix, guild_id])
            self.conn.commit()
            print(f"Updated prefix to {new_prefix} into prefixes of {guild_id}")

    def get_user(self, discord_id: int):
        """
        Get user properties from database
        :param discord_id: Discord user id
        :return: Osu related properties of user
        """
        return self.c.execute(f"SELECT * FROM osu_players WHERE discord_id=?", [discord_id]).fetchone()

    def add_user(self, discord_id: int, user_properties: List[Any]):
        """
        Add or update new user to the database
        :param discord_id: Discord user id
        :param user_properties: Osu related user properties
        :return: Insert new user into database
        """
        user = self.c.execute(f"SELECT * FROM osu_players WHERE discord_id=?", [discord_id]).fetchone()
        if user is None:
            self.c.execute(f"INSERT INTO osu_players VALUES (?, ?, ?, ?, ?, ?, ?)", [discord_id, user_properties])
            self.conn.commit()
            print(f"Inserted {user_properties} into osu_players")
        else:
            self.c.execute(
                f"UPDATE osu_players SET "
                f"osu_username=?, osu_id=?,"
                f"osu_rank=?, osu_badges=?,"
                f"last_updated=?, ping_me=? WHERE discord_id=?", [user_properties, discord_id])
            self.conn.commit()
            print(f"Updated {user_properties} in osu_players")
        return

    def get_player(self, username: str):
        """
        Get user properties from database
        :param username: Player username
        :return: Osu related properties of user
        """
        uname = username.lower()
        return self.c.execute(f"SELECT * FROM osu_players WHERE osu_username=?", [uname]).fetchone()

    def set_player(self, player: Player, discord_id=None):
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
        else:
            self.c.execute(f"UPDATE osu_players SET discord_id=?, osu_username=?, last_updated=?, country=?, badges=?",
                           [discord_id, osu_username, last_updated, country, badges])
            self.conn.commit()

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
        Get linked osu profile from discord id
        :param discord_id: Discord user id
        :param osu_id: Osu id of the linked player
        :return: Osu profile id of discord user
        """
        result = self.c.execute(f"SELECT * FROM links WHERE discord_id=?", [discord_id]).fetchone()

        if result is None:
            self.c.execute(f"INSERT INTO links VALUES (?, ?)", [discord_id, osu_id])
            self.conn.commit()
        else:
            self.c.execute(f"UPDATE links SET osu_id=? WHERE discord_id=?", [osu_id, discord_id])
            self.conn.commit()

        return

    def delete_link(self, discord_id: int):
        self.c.execute(f"DELETE FROM links WHERE discord_id=?", [discord_id])
        self.conn.commit()
        return

    def get_beatmap(self, beatmap_id: int):
        return self.c.execute("SELECT * FROM beatmaps WHERE beatmap_id=?", [beatmap_id]).fetchone()

    def set_beatmap(self, beatmap: Beatmap):

        result = self.c.execute("SELECT * FROM beatmaps WHERE beatmap_id=?", [beatmap.beatmap_id]).fetchone()
        if result is None:
            self.c.execute("INSERT INTO beatmaps VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", beatmap.to_list())
            self.conn.commit()
        else:
            return

