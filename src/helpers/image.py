import os
from re import sub
from typing import Any, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from colour import Color
from ossapi import Mod, Score
from ossapi.enums import Grade, Statistics

from helpers.primitives import Point


class TextBox:
    def __init__(self, text, color, font_size=24):
        self.text = text
        self.font: ImageFont.FreeTypeFont = ImageFont.truetype(
            os.path.join("assets", "fonts", "Torus Semibold.otf"), font_size)
        self.color = color
        self.anchor = 'mm'

    def draw(self, draw: ImageDraw.ImageDraw, position: Point, max_width: int = None):
        text_width, text_height = self.get_real_textsize(self.text, self.font)
        if max_width is None:
            max_width = text_width
        position = Point(position[0], position[1])
        self.text, width, height = self.clamp_text(self.font, self.text, max_width)
        draw.text(position, self.text, fill=self.color, font=self.font, anchor=self.anchor)

    @staticmethod
    def get_real_textsize(text, font):
        offset_x, offset_y = font.getoffset(text)
        width, height = font.getsize(text)
        width += offset_x
        height += offset_y
        return width, height

    @staticmethod
    def clamp_text(font, title_text, max_width):
        initial_text = title_text
        title_width, title_height = TextBox.get_real_textsize(title_text, font)
        while title_width > max_width:
            title_text = title_text[:-1]
            title_width, title_height = TextBox.get_real_textsize(title_text, font)

        new_text = title_text.strip()
        if new_text != initial_text:
            new_text = new_text[:-3] + '...'

        title_width, title_height = TextBox.get_real_textsize(new_text, font)
        return new_text, title_width, title_height


class TitleTextBox(TextBox):
    def __init__(self, text):
        color = (255, 255, 255, 255)
        super().__init__(text, color)


class DifficultyTextBox(TextBox):
    def __init__(self, text):
        color = (255, 255, 255, 255)
        super().__init__(text, color, font_size=16)


class JudgementTextBox(TextBox):
    def __init__(self, judgement: tuple, judgement_color, box_width):
        self.judgement_text, self.text = judgement
        color = (255, 255, 255, 255)
        super().__init__(self.text, color)
        self.judgement_width = box_width
        self.judgement_color = judgement_color
        self.judgement_font_size = 14
        self.judgement_font = ImageFont.truetype(self.font.path, self.judgement_font_size)
        self.judgement_anchor = 'mm'
        self.anchor = 'mm'

    def draw(self, draw: ImageDraw.ImageDraw, position: Point, max_width: int = None):
        self.draw_judgement_text(draw, position)
        text_position = position + Point(self.judgement_width // 2, 34)
        super(JudgementTextBox, self).draw(draw, text_position, max_width)

    def draw_judgement_text(self, draw: ImageDraw.ImageDraw, position: Point):
        text_width, text_height = self.get_real_textsize(self.judgement_text, self.judgement_font)
        draw.rounded_rectangle(
            (position,
             position + (self.judgement_width, text_height)),
            radius=10,
            fill=(0, 0, 0, 160))
        draw.text(position + (self.judgement_width // 2, text_height // 2), self.judgement_text,
                  fill=self.judgement_color, font=self.judgement_font,
                  anchor=self.judgement_anchor)


class JudgementsBox:
    judgement_mapping = {'GREAT': 'count_300',
                         'OK': 'count_100',
                         'MEH': 'count_50',
                         'MISS': 'count_miss'}
    judgement_colors = {'GREAT': (100, 200, 255, 255),
                        'OK': (140, 200, 0, 255),
                        'MEH': (255, 205, 35, 255),
                        'MISS': (240, 20, 30, 255)}

    def __init__(self, judgements: Union[Statistics, Score], box_width=500):
        self.judgements = judgements
        self.box_width = box_width
        self.margin = Point(10, 10)
        self.box_inter_margin = 3
        self.inner_box_width = self.box_width - self.margin[0] - self.box_inter_margin * len(self.judgement_mapping)

    def draw(self, draw: ImageDraw.ImageDraw, position: Point):
        position += self.margin
        for i, (judgement_text, ossapi_attr) in enumerate(self.judgement_mapping.items()):
            judgement_count = self.judgements.__getattribute__(ossapi_attr)
            judgement_count = self.preprocess_judgement_text(judgement_text, judgement_count)
            judgement_box_width = self.inner_box_width // len(self.judgement_mapping)
            text_box = JudgementTextBox((judgement_text, judgement_count), self.judgement_colors[judgement_text],
                                        judgement_box_width)
            text_box.draw(draw, position, judgement_box_width)
            position += Point(judgement_box_width + self.box_inter_margin, 0)

    def preprocess_judgement_text(self, judgement: str, count: Any):
        if judgement == 'SCORE':
            count = int(count)
            count = f'{count:,}'
        elif judgement == 'ACCURACY':
            count = count
            count = f'{count:.2f}%'
        elif judgement == 'COMBO':
            count = f'{count}x/{self.judgements.beatmap.max_combo}'
            count.strip()
        else:
            count = f'{count}'
        return count


class ScoreGradeVisual:
    def __init__(self, grade: Grade, radius=120):
        self.grade = grade
        self.radius = radius
        self.grade_colors = {"F": (250, 22, 63, 30),
                             "D": (250, 122, 36, 30),
                             "C": (139, 47, 151, 30),
                             "B": (70, 179, 230, 30),
                             "A": (148, 252, 19, 30),
                             "S": (253, 212, 22, 30),
                             "X": (253, 212, 22, 30),
                             "SH": (239, 239, 239, 30),
                             "XH": (239, 239, 239, 30)}
        font_size = 72
        self.font: ImageFont.FreeTypeFont = ImageFont.truetype(
            os.path.join("assets", "fonts", "Torus Semibold.otf"), font_size)

    def draw(self, draw: ImageDraw.ImageDraw, position: Point):
        grade_name = self.grade.name[:-1] if self.grade.name.endswith('H') else self.grade.name
        fill = self.grade_colors[self.grade.value]
        draw.ellipse((position, position + (self.radius, self.radius)), fill=fill)
        draw.text(position + (self.radius // 2, self.radius // 2), grade_name, font=self.font,
                  fill=fill, anchor='mm')


class ScoreBox(JudgementsBox):
    judgement_mapping = {'SCORE': 'score',
                         'COMBO': 'max_combo',
                         'ACCURACY': 'accuracy'}
    judgement_colors = {'SCORE': (255, 255, 255, 255),
                        'COMBO': (255, 255, 255, 255),
                        'ACCURACY': (255, 255, 255, 255)}

    def __init__(self, judgements: Score, box_width=500):
        super().__init__(judgements, box_width)


class PPTextBox(TextBox):
    pp_domain = np.asarray([0, 1.25, 2, 2.5, 3.3, 4.2, 4.9, 5.8, 6.7, 7.7, 9, 100]) * 100
    font_sizes = [50, 52, 54, 56, 60, 62, 64, 66, 70, 72, 76, 80]
    color_domain = np.asarray(
        ['#c85fc9', '#985acd', '#5f55d1', '#5081d5', '#4bc0d9', '#45ddb3', '#40e16b', '#5ae63b', '#a9ea35', '#eedd30',
         '#f3852a', '#f72525'])

    def __init__(self, pp: float):
        self.pp = pp
        self.pp_text = f'{pp:.0f}pp'
        font_size = self.font_sizes[self.find_biggest(self.pp_domain, self.pp)]
        color = self.find_gradient_color()
        super().__init__(self.pp_text, color, font_size=font_size)

    @staticmethod
    def find_biggest(array, value):
        return np.argmax(array > value)

    def find_gradient_color(self):
        idx = self.find_biggest(self.pp_domain, self.pp)

        max_pp = self.pp_domain[idx]
        min_pp = self.pp_domain[idx - 1] if idx > 0 else 0

        max_color = self.color_domain[idx]
        min_color = self.color_domain[idx - 1]

        begin_hsl = Color(min_color).get_hsl()
        end_hsl = Color(max_color).get_hsl()

        # Find the color between begin_hsl and end_hsl that is closest to the pp
        nb = 10
        step = tuple([float(end_hsl[i] - begin_hsl[i]) / nb for i in range(0, 3)]) \
            if nb > 0 else (0, 0, 0)

        def mul(step, value):
            return tuple([v * value for v in step])

        def add_v(step, step2):
            return tuple([v + step2[i] for i, v in enumerate(step)])

        r = int((self.pp - min_pp) / (max_pp - min_pp) * 10)
        clr = add_v(begin_hsl, mul(step, r))
        rgb_clr = Color(hsl=clr).get_rgb()
        return tuple(map(int, mul(rgb_clr, 255)))


class ModsIcon:
    def __init__(self, mods: Mod):
        self.mods = mods

    def draw(self, image: Image.Image, position: Point):
        all_mods = self.mods.decompose()
        mod_img_size = (45, 32)
        inner_margin = len(all_mods) * 4
        mods_width, mods_height = (mod_img_size[0] - inner_margin) * len(all_mods), mod_img_size[1]
        top_left = self.get_top_left(position, Point(mods_width, mods_height))
        for mod in all_mods:
            mod_name = self.kebab(mod.long_name())
            self.icon_path = os.path.join("assets", "icons", "mods", f"mod_{mod_name}.png")
            mod_img = Image.open(self.icon_path)

            image.paste(mod_img, (top_left[0], top_left[1]), mod_img)
            top_left = (top_left[0] + mod_img.size[0] - inner_margin, top_left[1])

    def get_top_left(self, center_position: Point, offset: Point):
        return center_position - (offset // 2)

    @staticmethod
    def kebab(s):
        return '-'.join(
            sub(r"(\s|_|-)+", " ",
                sub(r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                    lambda mo: ' ' + mo.group(0).lower(), s)).split())


class StarRatingTextBox(TextBox):
    def __init__(self, rating: float):
        self.rating = rating
        self.rating_text = f'{rating:.2f}'
        self.star_icon_path = os.path.join("assets", "icons", "star.png")
        super().__init__(self.rating_text, (255, 255, 255, 255), font_size=48)

    def draw(self, draw: ImageDraw.ImageDraw, position: Point, max_width: int = None):
        self.draw_star_icon(position, image=draw._image)
        super().draw(draw, position)

    def draw_star_icon(self, position: Point, image: Image.Image):
        star_icon = Image.open(self.star_icon_path)
        star_icon.thumbnail((32, 32))
        text_width, text_height = self.get_real_textsize(self.text, self.font)
        new_position = (position[0] + text_width // 2 + 5, position[1] - 14)
        image.paste(star_icon, new_position, star_icon)
