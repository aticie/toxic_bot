import unittest
from ..src.utils import make_readable_score, time_ago, determine_plural, dominant_color, beatmap_from_cache_or_web, \
    get_acc, get_mods, get_value_from_dbase, sort_plays_by_date, get_recent_best, \
    get_user_best_v2, get_recent, get_osu_user_data, enumerate_mods, get_bmap_data, show_bmap_details, \
    get_user_scores_on_bmap, get_cover_image, draw_chat_lines, get_turkish_chat, get_country_rankings_v2, fix_rank, \
    add_embed_fields_on_country, add_embed_description_on_compare, add_embed_description_on_osutop, draw_map_completion, \
    draw_map_stars, draw_user_play, make_recent_gif, get_and_save_user_assets, draw_user_profile, dayhoursec_time, \
    draw_level_bar, get_osu_user_web_profile, get_embed_text_from_beatmap, get_embed_text_from_profile, \
    parse_recent_play

from datetime import datetime
import numpy as np
from PIL import Image
import asyncio
from oppai import *


class MyTestCase(unittest.TestCase):

    def test_make_readable_score(self):
        # Assert function works correctly
        scores = [1234567890, 123456789, 12345678, 1234567, 123456, 12345, 1234, 123, 12, 1]
        expected_scores = ["1.234.567.890", "123.456.789", "12.345.678", "1.234.567", "123.456", "12.345", "1.234",
                           "123", "12", "1"]
        for score, expected_score in zip(scores, expected_scores):
            test_score = make_readable_score(score)
            self.assertEqual(test_score, expected_score)

    def test_time_ago(self):
        # Assert time ago function works as intended
        time1 = datetime.fromisoformat('2020-12-31T23:59:59-00:00')
        time2 = datetime.fromisoformat('2016-11-03T23:59:59-00:00')
        time3 = datetime.fromisoformat('2020-10-30T23:59:59-00:00')
        time4 = datetime.fromisoformat('2020-12-20T22:59:59-00:00')
        time5 = datetime.fromisoformat('2020-12-31T22:58:59-00:00')
        time6 = datetime.fromisoformat('2020-12-31T23:58:55-00:00')
        time7 = datetime.fromisoformat('2020-12-31T23:59:52-00:00')
        time8 = datetime.fromisoformat('2020-12-31T23:59:59-00:00')

        test_time = time_ago(time1, time2)
        test_time2 = time_ago(time1, time3)
        test_time3 = time_ago(time1, time4)
        test_time4 = time_ago(time1, time5)
        test_time5 = time_ago(time1, time6)
        test_time6 = time_ago(time1, time7)
        test_time7 = time_ago(time1, time8)

        self.assertEqual("4 Years 1 Month ", test_time)
        self.assertEqual("2 Months 1 Day ", test_time2)
        self.assertEqual("11 Days 1 Hour ", test_time3)
        self.assertEqual("1 Hour 1 Minute ", test_time4)
        self.assertEqual("1 Minute 4 Seconds ", test_time5)
        self.assertEqual("7 Seconds ", test_time6)
        self.assertEqual("0 Seconds ", test_time7)

    def test_determine_plural(self):
        # Assure plural checking works for both string and integer inputs
        string_input = [str(i) for i in range(-5, 5)]
        int_input = [i for i in range(-5, 5)]

        for stri, i in zip(string_input, int_input):

            test_result_int = determine_plural(i)
            test_result_str = determine_plural(stri)

            if i != 1:
                self.assertEqual('s', test_result_str)
                self.assertEqual('s', test_result_int)
            else:
                self.assertEqual('', test_result_str)
                self.assertEqual('', test_result_int)

    def test_dominant_color(self):
        # Assure dominant color returns an array, and it works on black image
        black = np.zeros([10, 10, 3], dtype=np.uint8)
        image = Image.fromarray(black)
        result = dominant_color(image)
        comparison = result == np.array([0, 0, 0], dtype=np.float32)
        self.assertTrue(comparison.all())

    def test_get_acc(self):
        # Assure function can take both string and integer inputs and will output float
        string_input = str(100)
        int_input = 100
        out1 = get_acc(string_input, string_input, string_input, string_input)
        out2 = get_acc(int_input, int_input, int_input, int_input)

        self.assertTrue(isinstance(out1, float))
        self.assertTrue(isinstance(out2, float))

    def test_get_mods(self):
        # Assure all mods are returned in order
        all_mods = (1 << 29) - 1

        all_mods_list = ['NF', 'EZ', 'TD', 'HD', 'HR', 'SD', 'RX', 'HT', 'NC', 'FL', 'AT', 'SO', 'AP', 'PF', 'Key4',
                         'Key5', 'Key6', 'Key7', 'Key8', 'FadeIn', 'Random', 'Cinema', 'Target', 'Key9', 'KeyCoop',
                         'Key1', 'Key3', 'Key2']
        all_mods_text = '+NFEZTDHDHRSDRXHTNCFLATSOAPPFKey4Key5Key6Key7Key8FadeInRandomCinemaTargetKey9KeyCoopKey1Key3Key2'

        output_list, output_text = get_mods(all_mods)

        self.assertEqual(all_mods_list, output_list)
        self.assertEqual(all_mods_text, output_text)

    def test_enumerate_mods(self):
        # Enumerate mods must take list only
        mods = ['NF', 'EZ', 'TD', 'HD', 'HR', 'SD', 'RX', 'HT', 'NC', 'FL', 'AT', 'SO', 'AP', 'PF', 'Key4',
                'Key5', 'Key6', 'Key7', 'Key8', 'FadeIn', 'Random', 'Cinema', 'Target', 'Key9', 'KeyCoop',
                'Key1', 'Key3', 'Key2']
        mods_int = enumerate_mods(mods)
        self.assertEqual(mods_int, (1 << 29) - 1)

    def test_get_value_from_dbase(self):
        # 11111111 test id should return test_user and test_recent
        out1 = get_value_from_dbase(11111111, "username")
        out2 = get_value_from_dbase(11111111, "recent")
        self.assertEqual("test_user", out1)
        self.assertEqual("test_recent", out2)

    def test_sort_plays_by_date(self):
        # Assert sorting is in descending order
        date1 = datetime.fromisoformat("2020-12-31T23:59:59-00:00")
        date2 = datetime.fromisoformat("2025-12-31T23:59:59-00:00")
        date3 = datetime.fromisoformat("2015-12-31T23:59:59-00:00")
        dates = [date1, date2, date3]
        indexes_sorted = [1, 0, 2]
        plays_v2 = [{"created_at": d.strftime('%Y-%m-%dT%H:%M:%S+00:00')} for d in dates]
        plays_v1 = [{"date": d.strftime('%Y-%m-%d %H:%M:%S')} for d in dates]

        out1 = sort_plays_by_date(plays_v2, v2=True)
        out2 = sort_plays_by_date(plays_v1, v2=False)
        comparison1 = out1 == indexes_sorted
        comparison2 = out2 == indexes_sorted
        self.assertTrue(comparison1.all())
        self.assertTrue(comparison2.all())

    def test_get_recent_best(self):
        # Assert it works with both string and integer inputs
        user_id = 5642779
        user_id_str = str(user_id)
        response = asyncio.run(get_recent_best(user_id))
        response2 = asyncio.run(get_recent_best(user_id_str))
        self.assertEqual(len(response), 100)
        self.assertTrue(isinstance(response, list))
        self.assertTrue(isinstance(response[0], dict))

    def test_get_user_best_v2(self):
        # Assert it works with both string and integer inputs
        user_id = 5642779
        user_id_str = str(user_id)
        response = asyncio.run(get_user_best_v2(user_id))
        _ = asyncio.run(get_user_best_v2(user_id_str))
        self.assertEqual(len(response), 100)
        self.assertTrue(isinstance(response, list))
        self.assertTrue(isinstance(response[0], dict))

    def test_get_recent(self):
        # Assert it returns valid response
        user_id = 5642779
        response = asyncio.run(get_recent(user_id))

        self.assertEqual(len(response), 1)
        self.assertTrue(isinstance(response, list))
        self.assertTrue(isinstance(response[0], dict))

    def test_get_osu_user_data(self):
        # Assert it returns a dict
        user_id = 5642779
        response = asyncio.run(get_osu_user_data(user_id))

        self.assertTrue(isinstance(response, dict))

    def test_get_bmap_data(self):
        # Assert it returns a dict
        bmap_id = 1018019
        response = get_bmap_data(bmap_id, mods=0, limit=1)
        self.assertTrue(isinstance(response, dict))

    def test_beatmap_from_cache_or_web(self):
        # Assure returned object is of beatmap type
        bmap_id = 1018019
        result = asyncio.run(beatmap_from_cache_or_web(bmap_id))
        empty_map = ezpp_new()
        self.assertTrue(isinstance(result, type(empty_map)))



if __name__ == '__main__':
    unittest.main()
