import sqlite3
from typing import List, Any


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
        return self.c.execute(f"SELECT * FROM users WHERE discord_id=?", [discord_id]).fetchone()

    def add_user(self, discord_id: int, user_properties: List[Any]):
        """
        Add or update new user to the database
        :param discord_id: Discord user id
        :param user_properties: Osu related user properties
        :return: Insert new user into database
        """
        user = self.c.execute(f"SELECT * FROM users WHERE discord_id=?", [discord_id]).fetchone()
        if user is None:
            self.c.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", [discord_id, user_properties])
            self.conn.commit()
            print(f"Inserted {user_properties} into users")
        else:
            self.c.execute(
                f"UPDATE users SET "
                f"osu_username=?, osu_id=?,"
                f"osu_rank=?, osu_badges=?,"
                f"last_updated=?, ping_me=? WHERE discord_id=?", [user_properties, discord_id])
            self.conn.commit()
            print(f"Updated {user_properties} in users")
        return
