class Player:

    def __init__(self):
        self.id = None
        self.username = None
        self.last_updated = None
        self.country_code = None
        self.badges = None  # Will implement with apiv2

        #self.avatar_url = None  # Will implement with apiv2
        #self.statistics = None  # Will implement with apiv2
        #self.cover_url = None  # Will implement with apiv2
        #self.is_online = None  # Will implement with apiv2
        #self.play_mode = None  # Will implement with apiv2
        self.pp_rank = None
        self.country_rank = None
        self.pp_raw = None
        self.accuracy = None
        self.join_date = None
        self.total_seconds_played = None
        self.play_count = None
        self.level = None

        pass

    def from_dict(self, player_dict):
        # Rarely or never updated values, kept in DB
        self.country_code = player_dict["country"]
        self.username = player_dict["username"]
        self.badges = []  # Will implement with apiv2
        self.id = player_dict["user_id"]

        # Frequently updated values, gotten from API
        #self.avatar_url = player_dict["avatar_url"]
        #self.is_online = player_dict["is_online"]  # Will implement with apiv2
        #self.cover_url = player_dict["cover_url"]  # Will implement with apiv2
        #self.play_mode = player_dict["playmode"]  # Will implement with apiv2
        self.join_date = player_dict["join_date"]
        self.country_rank = player_dict["pp_country_rank"]
        self.total_seconds_played = player_dict["total_seconds_played"]
        self.play_count = player_dict["playcount"]
        self.pp_rank = player_dict["pp_rank"]
        self.pp_raw = player_dict["pp_raw"]
        self.level = player_dict["level"]
        self.accuracy = player_dict["accuracy"]

    def from_db(self, player_tuple):
        self.username = player_tuple[0]
        self.id = player_tuple[1]
        self.last_updated = player_tuple[2]
        self.country_code = player_tuple[3]
        self.badges = player_tuple[4]

