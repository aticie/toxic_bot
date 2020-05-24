import datetime

from PIL import Image
from oppai import *

from data.player import Player
from data.beatmap import Beatmap


class OsuScore:

    def __init__(self, score_details: dict,
                 player: Player = None,
                 beatmap=None,
                 game_mode: int = 0,
                 cover_img: Image = None):
        self.player = player
        self.bmap = beatmap
        self.cover = cover_img
        self.score = int(score_details["score"])
        self.max_combo = int(score_details["maxcombo"])
        self.count50 = int(score_details["count50"])
        self.count100 = int(score_details["count100"])
        self.count300 = int(score_details["count300"])
        self.count_miss = int(score_details["countmiss"])
        self.count_katu = int(score_details["countkatu"])
        self.count_geki = int(score_details["countgeki"])
        self.perfect = bool(score_details["perfect"])
        self.date = datetime.datetime.strptime(score_details["date"], "%Y-%m-%d %H:%M:%S")
        self.enabled_mods = int(score_details["enabled_mods"])
        self.game_mode = game_mode
        self.rank = score_details["rank"]

    def set_player(self, player: Player):
        self.player = player

    def set_beatmap(self, beatmap: Beatmap):
        self.bmap = beatmap
        ezpp_set_mods(self.bmap.ez, self.enabled_mods)
        ezpp_set_accuracy(self.bmap.ez, self.count100, self.count50)
        ezpp_set_combo(self.bmap.ez, self.max_combo)
        ezpp_set_nmiss(self.bmap.ez, self.count_miss)

    def set_cover(self, cover_img: Image):
        self.cover = cover_img
