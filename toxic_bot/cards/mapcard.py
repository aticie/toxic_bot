from abc import ABC
from types import SimpleNamespace

import nextcord
import rosu_pp_py as rosu
from ossapi import Mod

from toxic_bot.helpers.http_downloader import download_and_save_beatmap


class MapCard:
    def __init__(self, beatmap: SimpleNamespace, mods: Mod = Mod.NM):
        self.beatmap = beatmap
        self.beatmapset = beatmap.beatmapset
        self.mods = mods

    async def to_embed(self):
        """
        Generates an embed object for the beatmap information.

        Implemented in subclasses.
        """
        raise NotImplementedError()


class EmbedMapCard(MapCard, ABC):
    async def to_embed(self):
        """
        Generates an embed object for the beatmap information.
        """
        beatmap_path = await download_and_save_beatmap(self.beatmap.id)
        beatmap_calculator = rosu.Calculator(beatmap_path)
        params = [rosu.ScoreParams(mods=self.mods.value,
                                   combo=self.beatmap.max_combo),
                  rosu.ScoreParams(mods=self.mods.value,
                                   combo=self.beatmap.max_combo,
                                   acc=100),
                  rosu.ScoreParams(mods=self.mods.value,
                                   combo=self.beatmap.max_combo,
                                   acc=99),
                  rosu.ScoreParams(mods=self.mods.value,
                                   combo=self.beatmap.max_combo,
                                   acc=97),
                  rosu.ScoreParams(mods=self.mods.value,
                                   combo=self.beatmap.max_combo,
                                   acc=95)
                  ]

        rosu_pp_results = beatmap_calculator.calculate(params)
        rosu_pp_result = rosu_pp_results[0]
        beatconnect_link = f"https://beatconnect.io/b/{self.beatmapset.id}/"
        bancho_link = f"https://osu.ppy.sh/beatmapsets/{self.beatmapset.id}/download"
        bloodcat_link = f"https://bloodcat.com/osu/s/{self.beatmapset.id}"
        download_disabled = self.beatmapset.availability.download_disabled

        no_vid_text_beatconnect = ""
        no_vid_text_bancho = ""
        if self.beatmapset.video:
            no_vid_text_bancho = f"([No-vid]({bancho_link}?novideo=1))"
            no_vid_text_beatconnect = f"([No-vid]({beatconnect_link}?novideo=1))"
        if download_disabled:
            download_text = f"**Download:** ~~Bancho~~ | [Bloodcat]({bloodcat_link}) | [BeatConnect]({beatconnect_link})"
        else:
            download_text = f"**Download:** [Bancho]({bancho_link}) {no_vid_text_bancho} | [Bloodcat]({bloodcat_link}) " \
                            f"| [BeatConnect]({beatconnect_link}) {no_vid_text_beatconnect}"

        bmap_mins = self.beatmap.total_length // 60
        bmap_secs = self.beatmap.total_length % 60

        diff_details_text = f"**▸CS:** {rosu_pp_result.cs:.1f} **▸AR:** {rosu_pp_result.ar:.1f} **▸OD:**" \
                            f" {rosu_pp_result.od:.1f} **▸HP:** {rosu_pp_result.hp:.1f}"
        desc_text = f"<:total_length:680709852988833802> **{bmap_mins}:{bmap_secs:02d}**" \
                    f" <:bpm:680709843060916292> **{rosu_pp_result.bpm:.0f} bpm**" \
                    f"  <:count_circles:680712754273058817> **{rosu_pp_result.nCircles}** " \
                    f" <:count_sliders:680712747012325409> **{rosu_pp_result.nSliders}**\n" \
                    f"{diff_details_text} \n" \
                    f"{download_text}\n"

        pp_values = [result.pp for result in rosu_pp_results[-2::-1]]
        pp_values_text = f'```Acc |{"95%":^8}|{"97%":^8}|{"99%":^8}|{"100%":^8}|\n' \
                         f'----|' + '-' * 8 + '|' + '-' * 8 + '|' + '-' * 8 + '|' + '-' * 8 + '|' + '\n' \
                                                                                                    f' PP |{pp_values[0]:^8.2f}|{pp_values[1]:^8.2f}|{pp_values[2]:^8.2f}|{pp_values[3]:^8.2f}|```'

        embed = nextcord.Embed()
        embed.set_author(name=f"{self.beatmapset.artist} - {self.beatmapset.title} by {self.beatmapset.creator}",
                         url=self.beatmap.url)
        embed.add_field(name=f"**[{self.beatmap.version}]** {rosu_pp_result.stars:.2f}★", value=desc_text, inline=False)
        embed.add_field(name="PP values", value=pp_values_text, inline=False)
        embed.set_image(url=self.beatmapset.covers.cover)

        return embed


class MapCardFactory:
    def __init__(self, beatmap_details: SimpleNamespace):
        self.beatmap_details = beatmap_details
        pass

    def get_card(self):
        return EmbedMapCard(self.beatmap_details)
