import datetime

from data.beatmap import Beatmap
from data.player import Player


class OsuScore:

    def __init__(self, score_details: dict, player: Player = None, beatmap: Beatmap = None):
        self.player = player
        self.bmap = beatmap
        self.score = score_details["score"]
        self.max_combo = score_details["maxcombo"]
        self.count50 = score_details["count50"]
        self.count100 = score_details["count100"]
        self.count300 = score_details["count300"]
        self.count_miss = score_details["countmiss"]
        self.count_katu = score_details["countkatu"]
        self.count_geki = score_details["countgeki"]
        self.perfect = score_details["perfect"]
        self.date = datetime.datetime.strptime(score_details["date"], "%Y-%m-%d %H:%M:%S")
        self.enabled_mods = score_details["enabled_mods"]
        self.rank = score_details["rank"]

    def set_player(self, player: Player):
        self.player = player

    def set_beatmap(self, beatmap: Beatmap):
        self.bmap = beatmap
