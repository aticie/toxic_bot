import os
from types import SimpleNamespace

import nextcord
from PIL import Image, ImageFont
from PIL import ImageDraw
from colour import Color
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

from toxic_bot.helpers.http_downloader import download_and_save_asset
from toxic_bot.helpers.image import pillow_image_to_discord_file


class ProfileCard:
    game_mode_dict = {'osu': 'Standard',
                      'taiko': 'Taiko',
                      'fruits': 'Ctb',
                      'mania': 'Mania'}

    def __init__(self, user_details: SimpleNamespace):
        self.user = user_details
        self.game_mode = self.game_mode_dict[user_details.playmode]

    def to_embed(self):
        """
        Returns a discord.Embed object with the user's profile information.

        Implemented in the subclasses.
        """

        embed = nextcord.Embed()
        embed.set_image(url="attachment://profile.png")
        embed.set_author(name=f'osu! {self.game_mode} profile for {self.user.username}',
                         url=f'https://osu.ppy.sh/users/{self.user.id}')
        return embed


class ImageProfileCard(ProfileCard):
    osu_light_pink = (255, 102, 171, 255)
    osu_text_pink = (224, 184, 190, 255)
    osu_text_white = (255, 255, 255, 255)

    osu_dark_bg = (42, 34, 38, 255)
    osu_light_bg = (56, 46, 50, 255)

    country_separator_color = (224, 184, 202, 255)
    playtime_separator_color = (255, 102, 171, 255)
    medals_separator_color = (179, 217, 68, 255)
    pp_separator_color = (237, 18, 33, 255)

    avatar_size = (200, 200)
    avatar_rounded_rectangle_radius = avatar_size[0] // 5
    avatar_margin = (15, 25)

    separator_height = 4
    separator_rounded_radius = separator_height // 2

    username_margin = (20, 15)
    username_size = 44
    title_margin = (0, 5)
    title_size = int(username_size * .75)
    supporter_bg_size = (90, 40)
    supporter_bg_margin = (0, 20)
    supporter_bg_rounded_radius = supporter_bg_size[0] // 3
    supporter_icon_font_size = 28
    groups_margin = (5, 0)
    groups_bg_size = (80, 40)
    groups_bg_color = (32, 26, 28, 255)
    country_separator_margin = (0, 10)
    country_separator_width = 200
    country_flag_margin = (0, 10)
    country_name_font_size = 32
    country_name_margin = (65, 22)

    upper_part_size = (800, 268)
    lower_part_size = (800, 92)

    global_rank_margin = (upper_part_size[0] * 2 // 3 + 50, 20)
    global_rank_width = 200
    country_rank_margin = (global_rank_margin[0], 150)
    country_rank_width = 200

    playtime_margin = (15, upper_part_size[1] + 15)
    playtime_width = 200
    medals_margin = (230, upper_part_size[1] + 15)
    medals_width = 100
    pp_margin = (345, upper_part_size[1] + 15)
    pp_width = 100

    card_size = (800, 360)

    text_font_path = os.path.join("assets", "fonts", "Torus Regular.otf")
    title_font_path = os.path.join("assets", "fonts", "Torus Semibold.otf")
    groups_font_path = os.path.join("assets", "fonts", "Torus Bold.otf")
    fontawesome_path = os.path.join("assets", "fonts", "fontawesome-regular.ttf")

    def __init__(self, user_details: SimpleNamespace):
        super().__init__(user_details)
        self.profile_card = None

    async def to_embed(self):
        self.profile_card = Image.new('RGBA', self.card_size, self.osu_dark_bg)

        await self.draw_lower_part()
        await self.draw_avatar()
        await self.draw_username()
        await self.draw_pp_rank()
        await self.draw_details(title_font_size=22, value_font_size=36, title_margin=5, value_margin=50)

        embed = super(ImageProfileCard, self).to_embed()
        file = pillow_image_to_discord_file(self.profile_card, "profile.png")

        return embed, file

    async def draw_pp_rank(self):
        global_rank_text = f'#{self.user.statistics.global_rank}'
        global_rank_font_size = 108 - max(len(global_rank_text), 4) * 8
        await self.draw_info_box(self.global_rank_margin, self.global_rank_width, 'Global Ranking',
                                 global_rank_text, self.playtime_separator_color,
                                 title_font_size=28, value_font_size=global_rank_font_size, title_margin=10,
                                 value_margin=75)
        await self.draw_info_box(self.country_rank_margin, self.country_rank_width, 'Country Ranking',
                                 f'#{self.user.statistics.country_rank}', self.playtime_separator_color,
                                 title_font_size=24, value_font_size=62, title_margin=10, value_margin=65)
        pass

    async def draw_info_box(self, position, width, title_text, value_text, color, title_font_size, value_font_size,
                            title_margin, value_margin):
        bold_text_font = ImageFont.truetype(self.title_font_path, title_font_size)
        text_font = ImageFont.truetype(self.text_font_path, value_font_size)
        await self.draw_separator(position=position,
                                  color=color,
                                  width=width)
        d = ImageDraw.Draw(self.profile_card)
        d.text((position[0], position[1] + title_margin), title_text, font=bold_text_font,
               fill=self.osu_text_white)
        d.text((position[0], position[1] + value_margin), value_text, font=text_font,
               fill=self.osu_text_white, anchor='lm')

    async def draw_lower_part(self):
        lower_part = Image.new('RGBA', self.lower_part_size, self.osu_light_bg)
        self.profile_card.paste(lower_part, (0, self.upper_part_size[1]))

    async def draw_details(self, title_font_size, value_font_size, title_margin, value_margin):
        playtime_hours = self.user.statistics.play_time // 3600
        await self.draw_info_box(self.playtime_margin, self.playtime_width, 'Total Play Time',
                                 f'{playtime_hours:,.0f} hours', self.playtime_separator_color,
                                 title_font_size=title_font_size, value_font_size=value_font_size,
                                 title_margin=title_margin, value_margin=value_margin)
        await self.draw_info_box(self.medals_margin, self.medals_width, 'Medals',
                                 f'{len(self.user.user_achievements)}', self.medals_separator_color,
                                 title_font_size=title_font_size, value_font_size=value_font_size,
                                 title_margin=title_margin, value_margin=value_margin)
        await self.draw_info_box(self.pp_margin, self.pp_width, 'pp',
                                 f'{int(self.user.statistics.pp):,}', self.pp_separator_color,
                                 title_font_size=title_font_size, value_font_size=value_font_size,
                                 title_margin=title_margin, value_margin=value_margin)

    async def draw_username(self):
        username_text = self.user.username
        username_font = ImageFont.truetype(self.text_font_path, size=self.username_size)
        username_text_x = self.avatar_margin[0] + self.avatar_size[0] + self.username_margin[0]
        username_text_y = self.username_margin[1]

        # Draw the username text
        d = ImageDraw.Draw(self.profile_card)
        d.text((username_text_x, username_text_y), username_text, font=username_font, fill=self.osu_text_white)

        # Draw user title if it exists
        user_title = self.user.title
        if user_title is not None:
            title_font = ImageFont.truetype(self.title_font_path, size=self.title_size)
            title_color = (255, 255, 255, 255) if len(self.user.groups) == 0 else (
                *tuple(int(v * 255) for v in Color(self.user.groups[0]['colour']).get_rgb()), 255)
            d.text((username_text_x, username_text_y + self.username_size + self.title_margin[1]), user_title,
                   font=title_font, fill=title_color)

        # Draw supporter status + groups
        supporter_bg_x = username_text_x
        supporter_bg_y = username_text_y + self.username_size + self.title_margin[1] + self.title_size + \
                         self.supporter_bg_margin[1]
        if self.user.support_level > 0:
            supporter_bg = Image.new('RGBA', self.supporter_bg_size, (0, 0, 0, 0))
            d = ImageDraw.Draw(supporter_bg)
            d.rounded_rectangle((0, 0, self.supporter_bg_size[0], self.supporter_bg_size[1]),
                                radius=self.supporter_bg_rounded_radius, fill=self.osu_light_pink)
            d.text((self.supporter_bg_size[0] // 2, self.supporter_bg_size[1] // 2), anchor='mm',
                   text=u"\uf004" * self.user.support_level,
                   font=ImageFont.truetype(self.fontawesome_path, size=self.supporter_icon_font_size),
                   fill=self.osu_text_white)

            self.profile_card.paste(supporter_bg, (supporter_bg_x, supporter_bg_y), mask=supporter_bg)

        if len(self.user.groups) > 0:
            if self.user.support_level > 0:
                group_offset = self.supporter_bg_size[0] + self.groups_margin[0]
            else:
                group_offset = self.groups_margin[0]

            group_position_x = supporter_bg_x + group_offset
            group_position_y = supporter_bg_y
            for group in self.user.groups:
                group_color = (255, 255, 255, 255) if len(self.user.groups) == 0 else (
                    *tuple(int(v * 255) for v in Color(group['colour']).get_rgb()), 255)
                d = ImageDraw.Draw(self.profile_card)
                d.rounded_rectangle((group_position_x, group_position_y, group_position_x + self.groups_bg_size[0],
                                     group_position_y + self.groups_bg_size[1]),
                                    radius=self.supporter_bg_rounded_radius, fill=self.groups_bg_color)
                d.text((group_position_x + self.groups_bg_size[0] // 2, group_position_y + self.groups_bg_size[1] // 2),
                       anchor='mm',
                       text=group['short_name'],
                       font=ImageFont.truetype(self.groups_font_path, size=self.supporter_icon_font_size),
                       fill=group_color)
                group_position_x += self.groups_bg_size[0] + self.groups_margin[0]

        # Draw country separator
        country_separator_y = supporter_bg_y + self.supporter_bg_size[1] + self.country_separator_margin[1]
        country_separator_x = supporter_bg_x
        await self.draw_separator((country_separator_x, country_separator_y), self.country_separator_width,
                                  self.country_separator_color)

        # Draw country flag
        country_flag_url = 'https://osu.ppy.sh/assets/images/flags/'
        code_nums = '-'.join([f'1f1{hex(0xA5 + ord(code))[2:]}' for code in self.user.country_code])
        country_flag_url += f'{code_nums}.svg'
        country_flag_path = await download_and_save_asset(country_flag_url)
        country_flag_rlg = svg2rlg(country_flag_path)
        country_flag_rlg.scale(1.5, 1.5)
        country_flag = renderPM.drawToPIL(country_flag_rlg, dpi=72 * 1.5, bg=0x00000)
        country_flag = country_flag.convert('RGBA')
        img_data = country_flag.getdata()
        newData = []
        for item in img_data:
            if item[0] == 0 and item[1] == 0 and item[2] == 0:
                newData.append((0, 0, 0, 0))
            else:
                newData.append(item)

        country_flag.putdata(newData)

        self.profile_card.paste(country_flag, (country_separator_x,
                                               country_separator_y + self.separator_height +
                                               self.country_flag_margin[1]), mask=country_flag)

        # Draw country name
        country_name_x = country_separator_x + self.country_name_margin[0]
        country_name_y = country_separator_y + self.country_name_margin[1]
        d = ImageDraw.Draw(self.profile_card)
        d.text((country_name_x, country_name_y),
               text=self.user.country.name,
               font=ImageFont.truetype(self.text_font_path, size=self.country_name_font_size),
               fill=self.osu_text_pink)

    async def draw_separator(self, position, width, color):
        d = ImageDraw.Draw(self.profile_card)
        d.rounded_rectangle(
            (position[0], position[1], position[0] + width,
             position[1] + self.separator_height), fill=color,
            radius=self.separator_rounded_radius)

    async def draw_avatar(self):
        avatar_path = await download_and_save_asset(self.user.avatar_url)
        avatar = Image.open(avatar_path)
        avatar = avatar.resize(self.avatar_size).convert("RGBA")
        avatar_mask = await self.create_avatar_mask()

        self.profile_card.paste(avatar, self.avatar_margin, avatar_mask)

    async def create_avatar_mask(self):
        avatar_mask = Image.new("RGBA", self.avatar_size, (0, 0, 0, 0))
        d = ImageDraw.Draw(avatar_mask)
        d.rounded_rectangle((0, 0, self.avatar_size[0], self.avatar_size[1]), fill=(255, 255, 255, 255),
                            radius=self.avatar_rounded_rectangle_radius)
        return avatar_mask


class EmbedProfileCard(ProfileCard):
    def __init__(self, user_details):
        super().__init__(user_details)

    async def to_embed(self):
        description_text = f'▸ **Global Rank:** #{self.user.statistics.global_rank} ({self.user.country_code}#{self.user.statistics.country_rank})\n'
        description_text += f'▸ **Level:** {self.user.statistics.level.current} + {self.user.statistics.level.progress}%\n'
        description_text += f'▸ **PP:** {self.user.statistics.pp} **Acc:** ({self.user.statistics.hit_accuracy:.2f}%)\n'
        description_text += f'▸ **Play Count:** {self.user.statistics.play_count:,} \n' \
                            f'▸ **Play Time:** {self.user.statistics.play_time // 3600:,} hrs'

        embed = nextcord.Embed(description=description_text)
        embed.set_thumbnail(url=self.user.avatar_url)
        embed.set_author(name=f'osu! {self.game_mode} profile for {self.user.username}',
                         url=f'https://osu.ppy.sh/users/{self.user.id}',
                         icon_url=f'https://osu.ppy.sh/images/flags/{self.user.country_code}.png')

        return embed, None


class ProfileCardFactory:
    def __init__(self, user_details: SimpleNamespace):
        self.user = user_details

    def get_card(self):
        return ImageProfileCard(self.user)
