from abc import ABC
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import List, Tuple, Union

import PIL
import nextcord
from PIL import Image, ImageFilter, ImageDraw
from ossapi import Mod
from ossapi.enums import Grade
from rosu_pp_py import Calculator, ScoreParams

from toxic_bot.helpers.http_downloader import download_and_save_asset, download_and_save_beatmap
from toxic_bot.helpers.image import PPTextBox, ScoreBox, StarRatingTextBox, TitleTextBox, DifficultyTextBox, \
    JudgementsBox, ModsIcon, ScoreGradeVisual, pillow_image_to_discord_file
from toxic_bot.helpers.primitives import Point
from toxic_bot.helpers.time import time_ago


class ScoreCard:
    def __init__(self, scores: List[SimpleNamespace]):
        self.scores = scores

    def to_embed(self):
        """
        Generates an embed object for the scorecard.

        Implemented in subclasses.
        """
        raise NotImplementedError()


class EmbedScoreCard(ScoreCard, ABC):
    pass


class ImageScoreCard(ScoreCard, ABC):

    def __init__(self, scores: List[SimpleNamespace]):
        super().__init__(scores)
        self.image = None
        self.score = None

    async def draw_image(self, score: SimpleNamespace):
        """
        Draws the play card and returns it
        """
        raise NotImplementedError

    async def to_embed(self) -> Tuple[nextcord.Embed, nextcord.File]:
        """
        Sends the play card to the current context channel
        """
        file = pillow_image_to_discord_file(self.image, 'score.png')
        embed = nextcord.Embed(
            title=f'{self.score.beatmapset.artist} - {self.score.beatmapset.title} [{self.score.beatmap.version}]',
            url=self.score.beatmap.url)
        embed.set_author(name=f"Played by {self.score.user.username}",
                         url=f"https://osu.ppy.sh/users/{self.score.user.id}",
                         icon_url=self.score.user.avatar_url)
        embed.set_image(url="attachment://score.png")
        footer_time = time_ago(datetime.now(tz=timezone.utc), datetime.fromisoformat(self.score.created_at))
        embed.set_footer(text=f'▸ Score set {footer_time}Ago | {self.score.beatmap.id},{self.score.user.id}')
        return embed, file


class SingleImageScoreCard(ImageScoreCard, ABC):

    def __init__(self, scores: List[SimpleNamespace], index: int):
        super().__init__(scores)
        self.score = scores[index]
        if not hasattr(self.score, 'id'):
            self.score = self.score.score

    async def draw_image(self, score: SimpleNamespace):
        cover_image_path = await download_and_save_asset(score.beatmapset.covers.__getattribute__('card@2x'))
        beatmap_path = await download_and_save_beatmap(score.beatmap.id)
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

        try:
            cover = Image.open(cover_image_path)
        except PIL.UnidentifiedImageError:
            cover = Image.new('RGB', (800, 280), (45, 45, 45))
        cover = cover.resize((800, 280), Image.ANTIALIAS)
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

        scorebox_pos = judgement_pos + Point(0, 90)
        ScoreBox(score, cover.width - right_offset).draw(cover_draw, scorebox_pos)

        score_grade = Grade(score.rank)

        StarRatingTextBox(score.beatmap.difficulty_rating, mods).draw(cover_draw,
                                                                      Point(cover.width - right_offset + 70, 70))
        ModsIcon(mods).draw(cover, Point(cover.width - right_offset + 80, 130))
        ScoreGradeVisual(score_grade).draw(cover_draw, Point(cover.width - right_offset + 160, 40))
        PPTextBox(score.pp, score_grade).draw(cover_draw, Point(cover.width - right_offset + 150, cover.height - 80))

        return cover

    async def to_embed(self) -> Tuple[nextcord.Embed, nextcord.File]:
        """
        Sends the image file to the channel
        """
        self.image = await self.draw_image(self.score)
        return await super().to_embed()


class MultiEmbedScoreCard(ImageScoreCard, ABC):
    pass


class ScoreCardFactory(object):
    """
    Factory class for creating ScoreCard objects.
    """

    def __init__(self, scores: List[SimpleNamespace], index: int = 0, mode: str = 'single'):
        if mode == 'multi':
            self.score_card = MultiEmbedScoreCard(scores)
        else:
            self.score_card = SingleImageScoreCard(scores, index)

    def get_card(self) -> Union[SingleImageScoreCard, MultiEmbedScoreCard]:
        return self.score_card
