

class Player:

    def __init__(self):
        self.country_code = None
        self.join_date = None
        self.username = None
        self.id = None

        self.avatar_url = None
        self.is_online = None
        self.cover_url = None
        self.play_mode = None
        self.statistics = None
        self.badges = None
        self.rank = None
        pass

    def from_dict(self, player_dict):
        # Rarely or never updated values, kept in DB
        self.country_code = player_dict["country_code"]
        self.join_date = player_dict["join_date"]
        self.username = player_dict["username"]
        self.id = player_dict["id"]

        # Frequently updated values, gotten from API
        self.avatar_url = player_dict["avatar_url"]
        self.is_online = player_dict["is_online"]
        self.cover_url = player_dict["cover_url"]
        self.play_mode = player_dict["playmode"]
        self.statistics = player_dict["statistics"]
        self.badges = player_dict["badges"]
        self.rank = player_dict["rank"]

    def from_db(self, player_tuple):
        self.country_code = player_tuple["country_code"]
        self.join_date = player_tuple["join_date"]
        self.username = player_tuple["username"]
        self.id = player_tuple["id"]

