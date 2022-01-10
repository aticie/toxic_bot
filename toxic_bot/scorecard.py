import io
import os
from abc import ABC
from types import SimpleNamespace
from typing import List, Dict
from urllib.parse import urlparse

import aiohttp
import nextcord
from PIL import Image, ImageFilter, ImageDraw
from ossapi import Mod
from ossapi.enums import Grade
from rosu_pp_py import Calculator, ScoreParams

from toxic_bot.helpers.image import PPTextBox, ScoreBox, StarRatingTextBox, TitleTextBox, DifficultyTextBox, \
    JudgementsBox, ModsIcon, ScoreGradeVisual
from toxic_bot.helpers.parser import Parser
from toxic_bot.helpers.primitives import Point


class ScoreCard:
    def __init__(self, parser: Parser, scores: List[SimpleNamespace]):
        self.parser = parser
        self.scores = scores

    async def send(self):
        """
        Implemented in subclasses
        """
        raise NotImplementedError


class EmbedScoreCard(ScoreCard, ABC):
    pass


class ImageScoreCard(ScoreCard, ABC):

    def __init__(self, parser: Parser, scores: List[SimpleNamespace]):
        super().__init__(parser, scores)
        self.image = None

    async def draw_image(self, score: SimpleNamespace):
        """
        Draws the play card and returns it
        """
        raise NotImplementedError

    async def download_and_save_asset(self, url) -> str:
        """
        Downloads image from url and returns PIL Image
        """
        url_path = urlparse(url).path
        folder_name, filename = os.path.split(url_path)
        local_folder_path = os.path.join('assets', f'.{folder_name}')
        asset_file_path = os.path.join(local_folder_path, filename)
        os.makedirs(local_folder_path, exist_ok=True)

        if os.path.exists(asset_file_path):
            return asset_file_path

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                response_bytes = await resp.read()

        with open(asset_file_path, "wb") as f:
            f.write(response_bytes)

        return asset_file_path

    async def download_and_save_beatmap(self, beatmap_id) -> str:
        beatmap_download_url = f"https://osu.ppy.sh/osu/{beatmap_id}"
        return await self.download_and_save_asset(beatmap_download_url)

    async def send(self):
        """
        Sends the play card to the current context channel
        """
        img_to_send = io.BytesIO()
        self.image.save(img_to_send, format='PNG')
        img_to_send.seek(0)
        file = nextcord.File(img_to_send, "score.png")
        await self.parser.ctx.send(file=file)


class SingleImageScoreCard(ImageScoreCard, ABC):

    def __init__(self, parser: Parser, scores: List[SimpleNamespace]):
        super().__init__(parser, scores)
        self.score = scores[parser.which_play]

    async def draw_image(self, score: SimpleNamespace):
        cover_image_path = await self.download_and_save_asset(score.beatmapset.covers.__getattribute__('card@2x'))
        beatmap_path = await self.download_and_save_beatmap(score.beatmap.id)
        calculator = Calculator(beatmap_path)
        mods = Mod(score.mods)
        [rosupp_result] = calculator.calculate(ScoreParams(mods=mods.value,
                                                           n300=score.statistics.count_300,
                                                           n100=score.statistics.count_100,
                                                           n50=score.statistics.count_50,
                                                           nMisses=score.statistics.count_miss,
                                                           combo=score.max_combo))
        beatmap = score.beatmap
        beatmap.max_combo = rosupp_result.maxCombo
        beatmap.difficulty_rating = rosupp_result.stars
        score.pp = rosupp_result.pp
        score.accuracy *= 100

        cover = Image.open(cover_image_path)
        cover = cover.filter(ImageFilter.GaussianBlur(radius=1.25))
        cover_draw = ImageDraw.Draw(cover, "RGBA")
        cover_draw.rounded_rectangle((Point(10, 10), Point(cover.width - 10, cover.height - 10)), radius=10,
                                     fill=(0, 0, 0, 200))
        right_offset = int(cover.width / 8 * 3)
        title = TitleTextBox(score.beatmapset.title)
        difficulty = DifficultyTextBox(f'[{beatmap.version}]')

        left_side = (cover.width - right_offset, cover.height)

        title_margin = Point(10 + left_side[0] // 2, 35)
        difficulty_height = title.get_real_textsize(title.text, title.font)[1] // 2 + \
                            difficulty.get_real_textsize(difficulty.text, difficulty.font)[1] // 2
        difficulty_margin = title_margin + Point(0, difficulty_height)
        title.draw(cover_draw, title_margin, cover.width - right_offset)
        difficulty.draw(cover_draw, difficulty_margin, cover.width - right_offset)
        difficulty_height = difficulty.get_real_textsize(difficulty.text, difficulty.font)[1]
        judgement_pos = Point(20, difficulty_margin[1] + difficulty_height)
        JudgementsBox(score.statistics, cover.width - right_offset).draw(cover_draw, judgement_pos)
        scorebox_pos = judgement_pos + Point(0, 65)
        ScoreBox(score, cover.width - right_offset).draw(cover_draw, scorebox_pos)

        StarRatingTextBox(score.beatmap.difficulty_rating).draw(cover_draw, Point(cover.width - right_offset + 70, 50))
        ModsIcon(mods).draw(cover, Point(cover.width - right_offset + 80, 110))
        ScoreGradeVisual(Grade(score.rank)).draw(cover_draw, Point(cover.width - right_offset + 150, 30))
        PPTextBox(score.pp).draw(cover_draw, Point(cover.width - right_offset + 150, cover.height - 60))

        return cover

    async def send(self):
        """
        Sends the image file to the channel
        """
        self.image = await self.draw_image(self.score)
        await super(SingleImageScoreCard, self).send()


class MultiEmbedScoreCard(ImageScoreCard, ABC):
    pass


class ScoreCardFactory(object):
    """
    Factory class for creating ScoreCard objects.
    """

    def __init__(self, parser: Parser, scores: List[SimpleNamespace]):
        if parser.is_multi:
            self.score_card = MultiEmbedScoreCard(parser, scores)
        else:
            self.score_card = SingleImageScoreCard(parser, scores)
        pass

    def get_play_card(self) -> ScoreCard:
        return self.score_card
