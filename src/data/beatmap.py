class Beatmap:

    def __init__(self):
        self.beatmap_id = None
        self.beatmapset_id = None
        self.mode = None
        self.version = None
        self.bpm = None
        self.ar = None
        self.od = None
        self.hp = None
        self.cs = None
        self.hit_length = None
        self.total_length = None
        self.creator = None
        self.title = None
        self.artist = None
        self.sr = None
        self.ez = None

    def from_api_json(self, beatmap_json):
        self.beatmapset_id = beatmap_json["beatmapset_id"]
        self.beatmap_id = beatmap_json["beatmap_id"]
        self.total_length = beatmap_json["total_length"]
        self.hit_length = beatmap_json["hit_length"]
        self.version = beatmap_json["version"]
        self.cs = beatmap_json["diff_size"]
        self.ar = beatmap_json["diff_approach"]
        self.od = beatmap_json["diff_overall"]
        self.hp = beatmap_json["diff_drain"]
        self.mode = beatmap_json["mode"]
        self.creator = beatmap_json["creator"]
        self.title = beatmap_json["title"]
        self.artist = beatmap_json["artist"]
        self.bpm = beatmap_json["bpm"]
        self.sr = beatmap_json["difficultyrating"]

    def from_db_object(self, beatmap_tuple):
        self.beatmap_id = beatmap_tuple[0]
        self.beatmapset_id = beatmap_tuple[1]
        self.mode = beatmap_tuple[2]
        self.version = beatmap_tuple[3]
        self.bpm = beatmap_tuple[4]
        self.ar = beatmap_tuple[5]
        self.od = beatmap_tuple[6]
        self.hp = beatmap_tuple[7]
        self.cs = beatmap_tuple[8]
        self.hit_length = beatmap_tuple[9]
        self.total_length = beatmap_tuple[10]
        self.creator = beatmap_tuple[11]
        self.title = beatmap_tuple[12]
        self.artist = beatmap_tuple[13]
        self.sr = beatmap_tuple[14]

    def to_list(self):
        return [v for k, v in self.__dict__.items()][:-1]

    def set_ezpp_obj(self, ezpp):
        self.ez = ezpp
