import cv2
import numpy as np
import colorsys
from datetime import datetime, timedelta
import os
from oppai import *
import json
import requests
from PIL import Image, ImageFilter, ImageFont, ImageDraw
import io

USER_LINK_FILE = os.path.join("Users", "link_list.json")
OSU_API = os.environ["OSU_API_KEY"]

with open("mods.txt", "r") as mods_file:
    all_mods = mods_file.readlines()


def strike(text):
    result = ''
    for c in text:
        result = result + c + '\u0336'
    return result


def make_readable_score(score):
    if isinstance(score, int):
        score = str(score)

    readable_score = ""
    score = score[::-1]
    for i in range((len(score) - 1) // 3 + 1):
        start = 0 + i * 3
        end = (i + 1) * 3
        readable_score += score[start:end] + "."
    readable_score = readable_score[:-1][::-1]
    return readable_score


def time_ago(time1, time2):
    time_diff = time1 - time2
    timeago = datetime(1, 1, 1) + time_diff
    time_limit = 0
    time_ago = ""
    if timeago.year - 1 != 0:
        time_ago += "{} Year{} ".format(timeago.year - 1, determine_plural(timeago.year - 1))
        time_limit = time_limit + 1
    if timeago.month - 1 != 0:
        time_ago += "{} Month{} ".format(timeago.month - 1, determine_plural(timeago.month - 1))
        time_limit = time_limit + 1
    if timeago.day - 1 != 0 and not time_limit == 2:
        time_ago += "{} Day{} ".format(timeago.day - 1, determine_plural(timeago.day - 1))
        time_limit = time_limit + 1
    if timeago.hour != 0 and not time_limit == 2:
        time_ago += "{} Hour{} ".format(timeago.hour, determine_plural(timeago.hour))
        time_limit = time_limit + 1
    if timeago.minute != 0 and not time_limit == 2:
        time_ago += "{} Minute{} ".format(timeago.minute, determine_plural(timeago.minute))
        time_limit = time_limit + 1
    if not time_limit == 2:
        time_ago += "{} Second{} ".format(timeago.second, determine_plural(timeago.second))
    return time_ago


def determine_plural(number):
    if int(number) != 1:
        return 's'
    else:
        return ''


def rounded_rectangle(img, topLeft, bottomRight, lineColor, thickness, lineType, cornerRadius):
    '''corners:
     * p1 - p2
     * |     |
     * p4 - p3
     '''
    img2 = img.copy()

    p1 = topLeft
    p2 = (bottomRight[0], topLeft[1])
    p3 = bottomRight
    p4 = (topLeft[0], bottomRight[1])

    # // draw straight lines
    cv2.line(img2, (p1[0] + cornerRadius, p1[1]), (p2[0] - cornerRadius, p2[1]), lineColor, thickness)
    cv2.line(img2, (p2[0], p2[1] + cornerRadius), (p3[0], p3[1] - cornerRadius), lineColor, thickness)
    cv2.line(img2, (p4[0] + cornerRadius, p4[1]), (p3[0] - cornerRadius, p3[1]), lineColor, thickness)
    cv2.line(img2, (p1[0], p1[1] + cornerRadius), (p4[0], p4[1] - cornerRadius), lineColor, thickness)

    # // draw arcs
    cv2.ellipse(img2, (p1[0] + cornerRadius, p1[1] + cornerRadius), (cornerRadius, cornerRadius), 180.0, 0, 90,
                lineColor, thickness, lineType)
    cv2.ellipse(img2, (p2[0] - cornerRadius, p2[1] + cornerRadius), (cornerRadius, cornerRadius), 270.0, 0, 90,
                lineColor, thickness, lineType)
    cv2.ellipse(img2, (p3[0] - cornerRadius, p3[1] - cornerRadius), (cornerRadius, cornerRadius), 0.0, 0, 90, lineColor,
                thickness, lineType)
    cv2.ellipse(img2, (p4[0] + cornerRadius, p4[1] - cornerRadius), (cornerRadius, cornerRadius), 90.0, 0, 90,
                lineColor, thickness, lineType)

    cv2.rectangle(img2, (p1[0] + cornerRadius // 5, p1[1] + cornerRadius // 5),
                  (p3[0] - cornerRadius // 5, p3[1] - cornerRadius // 5), lineColor, -1)

    return img2


def add_images(im1, im2, pos, alpha):
    im3 = np.copy(im1)
    im4 = np.copy(im2)
    h, w, c = im2.shape
    im3[pos[0]:pos[0] + h, pos[1]:pos[1] + w] = im4
    return cv2.addWeighted(im3, alpha, im1, 1 - alpha, 0)


def add_avatar_by_mask(im1, im2, mask, pos):
    im3 = mask.copy()
    h, w, c = im2.shape
    im3[(pos[1] - h // 2):(pos[1] + h // 2), (pos[0] - h // 2):(pos[0] + h // 2), :] = im2
    final_im = np.where(mask < 255, im1, im3)
    return final_im


def add_images_by_mask(im1, im2, mask):
    new_img = np.where(mask < 255, im1, im2)
    return new_img


def add_image_by_alpha(im1, im2, pos):
    im3 = im1.copy()
    h, w, c = im2.shape
    x = pos[0]
    y = pos[1]
    for i, height in enumerate(im2):
        for j, width in enumerate(height):
            alpha = width[3] / 255
            im3[x + i, y + j, :] = alpha * width[:3] + (1 - alpha) * im3[x + i, y + j, :]
    return im3


def dominant_color(img):
    data = np.reshape(img, (-1, 3))
    data = np.float32(data)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    flags = cv2.KMEANS_RANDOM_CENTERS
    compactness, labels, centers = cv2.kmeans(data, 1, None, criteria, 10, flags)

    return centers[0]


def convert_hsv_to_rgb(hsv):
    h, s, v = hsv
    h = h / 360
    s = s / 255
    v = v / 255

    r, g, b = colorsys.hsv_to_rgb(h, s, v)

    r = r * 255
    g = g * 255
    b = b * 255
    rgb = (int(r), int(g), int(b))
    return rgb


def convert_bgr_to_hsv(bgr):
    b, g, r = bgr
    r = r / 255
    g = g / 255
    b = b / 255

    h, s, v = colorsys.rgb_to_hsv(b, g, r)

    h = h * 360
    s = s * 255
    v = v * 255
    hsv = (int(h), int(s), int(v))
    return hsv


def add_avatar_rim(avatar_im, avatar_pos, avatar_size, hue):
    h, s, v = hue
    s = 200
    v = 200
    rgb = convert_hsv_to_rgb((h, s, v))
    return cv2.circle(avatar_im, avatar_pos, avatar_size // 2, rgb, 6, cv2.LINE_AA)


def image_from_cache_or_web(thing_id, url, folder):
    path = os.path.join(folder, thing_id + ".jpg")
    if not os.path.exists(folder):
        os.mkdir(folder)
    if os.path.exists(path):
        image = cv2.imread(path)
    else:
        r = requests.get(url)
        nparr = np.fromstring(r.content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imwrite(path, image)

    return image


def beatmap_from_cache_or_web(beatmap_id):
    if not os.path.exists("Beatmaps"):
        os.mkdir("Beatmaps")
    beatmap_id = str(beatmap_id)
    url = "https://osu.ppy.sh/osu/" + beatmap_id
    path = os.path.join("Beatmaps", beatmap_id + ".osu")
    ez = ezpp_new()
    ezpp_set_autocalc(ez, 1)
    if os.path.exists(path):
        ezpp_dup(ez, 'Beatmaps/{}.osu'.format(beatmap_id))
    else:
        print("Requesting: " + url)
        r = requests.get(url)
        with open(path, "w", encoding='utf-8') as f:
            f.write(r.content.decode("utf-8"))

        ezpp_dup(ez, 'Beatmaps/{}.osu'.format(beatmap_id))

    return ez


def bmap_info_from_oppai(ez, mods):
    mods = int(mods)
    ezpp_set_mods(ez, mods)
    return ezpp_stars(ez), ezpp_max_combo(ez)


def calculate_pp(ez, count100, count50, countmiss, mods, combo):
    count100 = int(count100)
    count50 = int(count50)
    countmiss = int(countmiss)
    mods = int(mods)
    combo = int(combo)
    ezpp_set_mods(ez, mods)
    ezpp_set_accuracy(ez, count100, count50)
    ezpp_set_combo(ez, combo)
    ezpp_set_nmiss(ez, countmiss)
    pp_raw = ezpp_pp(ez)
    ezpp_set_combo(ez, ezpp_max_combo(ez))
    ezpp_set_nmiss(ez, 0)
    pp_fc = ezpp_pp(ez)
    ezpp_set_accuracy_percent(ez, 95)
    pp_95 = ezpp_pp(ez)
    ezpp_set_accuracy_percent(ez, 100)
    pp_ss = ezpp_pp(ez)

    return pp_raw, pp_fc, pp_95, pp_ss


def get_acc(count300, count100, count50, countmiss):
    count300 = int(count300)
    count100 = int(count100)
    count50 = int(count50)
    countmiss = int(countmiss)

    note_count = count300 + count100 + count50 + countmiss
    acc = (count300 + count100 / 3 + count50 / 6) / note_count * 100

    return acc


def get_mods(mods):
    global all_mods

    mod_list = []
    mods = int(mods)

    i = 1
    for mod in all_mods:
        if i & mods == i:
            mod_list.append(mod.rstrip())
        i = i << 1

    if "NC" in mod_list:
        mod_list.remove("DT")

    mod_text = "+"+"".join(mod_list) if len(mod_list)>0 else ""
    return mod_list, mod_text


def link_user_on_file(user_osu_nickname, user_discord_id):
    user_discord_id = str(user_discord_id)

    users_dict = {}
    if not os.path.exists(USER_LINK_FILE):
        os.makedirs("Users", exist_ok=True)
        with open(USER_LINK_FILE, "w") as f:
            json.dump(users_dict, f)

    with open(USER_LINK_FILE, "r") as link_list:
        users_dict = json.load(link_list)

    if user_discord_id in users_dict:
        if user_osu_nickname == users_dict[user_discord_id]:
            return -1

    users_dict[user_discord_id] = user_osu_nickname
    with open(USER_LINK_FILE, "w") as link_list:
        json.dump(users_dict, link_list)
    return 1


def get_osu_username(discord_id):
    discord_id = str(discord_id)

    users_dict = {}
    if not os.path.exists(USER_LINK_FILE):
        os.makedirs("Users", exist_ok=True)
        with open(USER_LINK_FILE, "w") as f:
            json.dump(users_dict, f)
    with open(USER_LINK_FILE, "r") as f:
        users_dict = json.load(f)

    if discord_id in users_dict:
        return users_dict[discord_id]
    else:
        return -1


def get_recent(user_id, limit=1):
    rs_api_url = 'https://osu.ppy.sh/api/get_user_recent'
    PARAMS = {'k': OSU_API,  # Api key
              'u': user_id,
              'limit': limit}

    req = requests.get(url=rs_api_url, params=PARAMS)
    if len(req.json()) == 0:
        return -1
    recent_data = req.json()[0]

    return recent_data


def get_osu_user_data(username):
    user_api_url = "https://osu.ppy.sh/api/get_user"
    USER_PARAMS = {'k': OSU_API,  # Api key
                   'u': username
                   }
    user_req = requests.get(url=user_api_url, params=USER_PARAMS)
    user_data = user_req.json()[0]
    return user_data


def get_bmap_data(bmap_id, mods=0, limit=1):
    bmap_api_url = "https://osu.ppy.sh/api/get_beatmaps"
    mods = int(mods)
    bmap_id = int(bmap_id)
    BMAP_PARAMS = {'k': OSU_API,  # Api key
                   'b': bmap_id,
                   'mods': mods,
                   'limit': limit}

    bmap_req = requests.get(url=bmap_api_url, params=BMAP_PARAMS)
    bmap_data = bmap_req.json()[0]

    return bmap_data


def get_cover_image(bmap_setid):
    covers_folder = "Covers"
    covers_local = os.listdir(covers_folder)
    cover_image_name = f"{bmap_setid}.jpg"
    cover_save_name = os.path.join(covers_folder, cover_image_name)

    if cover_image_name in covers_local:
        print(f"DEBUG: Acquired image from local cache: {cover_save_name}")
        with open(cover_save_name, "rb") as f:
            cover_img_data = f.read()

        return cover_img_data, True

    cover_url = f"https://assets.ppy.sh/beatmaps/{bmap_setid}/covers/cover.jpg"
    print(f"DEBUG: Acquired image from {cover_url}")
    cover_req = requests.get(url=cover_url)
    cover_img_data = cover_req.content

    return cover_img_data, False


def get_country_rankings(bmap_data):
    country_url = f"https://osu.ppy.sh/web/osu-osz2-getscores.php"
    headers = {
        "User-Agent": "osu!",
        "Host": "osu.ppy.sh",
        "Accept-Encoding": "gzip, deflate"

    }
    bmap_md5 = bmap_data["file_md5"]
    bmap_artist = bmap_data["artist"]
    bmap_title = bmap_data["title"]
    bmap_creator = bmap_data["creator"]
    bmap_version = bmap_data["version"]
    bmap_setid = bmap_data["beatmapset_id"]

    f = f"{bmap_artist} - {bmap_title} ({bmap_creator}) [{bmap_version}].osu"
    PARAMS = {
        's': 0,
        'vv': 4,
        'v': 4,
        'c': bmap_md5,
        'f': f,
        'i': bmap_setid,
        'm': 0,
        'a': 0,
        'us': "heyronii",
        'ha': os.environ["ha"],
        'mods': 0
    }

    print(f)
    r = requests.get(country_url, headers=headers, params=PARAMS)

    country_data = parse_country_data(r.text)

    return country_data


def parse_country_data(text):
    scores_array = text.split("\n")[5:-1]

    country_data = []

    for score in scores_array:
        player_data = {}
        fields = score.split("|")
        player_data["name"] = fields[1]
        player_data["score"] = fields[2]
        player_data["combo"] = fields[3]
        player_data["count50"] = fields[4]
        player_data["count100"] = fields[5]
        player_data["count300"] = fields[6]
        player_data["countmiss"] = fields[7]
        player_data["count100g"] = fields[8]
        player_data["count300g"] = fields[9]
        player_data["perfect"] = fields[10]
        player_data["enabled_mods"] = fields[11]
        country_data.append(player_data)

    return country_data


def add_embed_fields(embed, country_data, offset):
    for player_rank, score in enumerate(country_data):
        player_name = score["name"]
        player_score = score["score"]
        player_combo = score["combo"]
        mods_list, _ = get_mods(score["enabled_mods"])
        player_mods = "".join(mods_list) if len(mods_list) > 0 else "NoMod"
        player_acc = get_acc(score["count300"], score["count100"], score["count50"], score["countmiss"])
        player_score = make_readable_score(player_score)
        value_text = f"{player_score} ({player_combo}x) - {player_acc:.2f}% {player_mods}"
        player_text = f"**#{player_rank + offset + 1} {player_name}**"
        embed.add_field(name=player_text, value=value_text, inline=False)

    return embed


def draw_recent_play(player_name, play_data, background_image, bmap_data, from_cache=True):
    badge_width = 400
    badge_height = 125
    badge_size = (badge_width, badge_height)

    bmapset_id = bmap_data["beatmapset_id"]
    bmap_id = play_data["beatmap_id"]
    bmp = beatmap_from_cache_or_web(bmap_id)

    cover = Image.open(io.BytesIO(background_image))
    if not from_cache:
        cover_save_name = os.path.join("Covers", f"{bmapset_id}.png")
        cover.save(cover_save_name)

    cover = cover.convert("RGBA")
    w, h = cover.size
    crop_box = (50, 0, w - 50, h)
    cover = cover.crop(crop_box)

    print(cover.size)  # DEBUG
    cover = cover.resize(badge_size, Image.BICUBIC)
    cover = cover.filter(ImageFilter.GaussianBlur(5))

    overlay_black = Image.new('RGBA', cover.size, (0, 0, 0, 180))
    cover = Image.alpha_composite(cover, overlay_black)

    txt = Image.new('RGBA', cover.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(txt)

    font_50 = ImageFont.truetype(os.path.join("Fonts", "Exo2-MediumItalic.otf"), 50 * 2)
    font_48 = ImageFont.truetype(os.path.join("Fonts", "Exo2-MediumItalic.otf"), 48 * 2)
    font_36 = ImageFont.truetype(os.path.join("Fonts", "Exo2-BlackItalic.otf"), 36)
    font_20 = ImageFont.truetype(os.path.join("Fonts", "Exo2-ExtraBold.otf"), 22)
    font_16 = ImageFont.truetype(os.path.join("Fonts", "Exo2-Black.otf"), 16)
    font_11 = ImageFont.truetype(os.path.join("Fonts", "Exo2-ExtraBold.otf"), 13)

    diff_rating = float(bmap_data["difficultyrating"])
    mods = play_data["enabled_mods"]
    max_combo = bmap_data["max_combo"]
    if diff_rating == 0:
        diff_rating, max_combo = bmap_info_from_oppai(bmp, mods)

    text_fill = (255, 255, 255, 200)
    bmap_name = bmap_data["title"]
    bmap_diff = bmap_data["version"]
    bmap_creator = bmap_data["creator"]
    bmap_misc = f"[{bmap_diff}] by {bmap_creator} | {diff_rating:.2f}*"

    name_w, _ = d.textsize(bmap_name, font_20)
    if name_w > 325:
        bmap_name = f"{bmap_name[:25]}~"
    d.text((8, 0), bmap_name, fill=text_fill, font=font_20)
    d.text((8, 26), bmap_misc, fill=text_fill, font=font_11)

    count300 = play_data["count300"]
    count100 = play_data["count100"]
    count50 = play_data["count50"]
    count_miss = play_data["countmiss"]
    play_combo = play_data["maxcombo"]

    mods_list, _ = get_mods(mods)
    mods_string = "NoMod" if len(mods_list) == 0 else "".join(mods_list)
    pp_raw, pp_fc, pp_95, pp_ss = calculate_pp(bmp, count100, count50, count_miss, mods, play_combo)

    acc = get_acc(count300, count100, count50, count_miss)

    d.text((8, 42), f"{count100}x100 | {count50}x50 | {count_miss}xMiss | Mods:{mods_string}",
           fill=text_fill, font=font_11)
    d.text((8, 58), f"{play_combo}x/{max_combo} | %{acc:.2f} | played by {player_name}",
           fill=text_fill, font=font_11)

    rank_color_dict = {"F": (250, 22, 63, 30),
                       "C": (139, 47, 151, 30),
                       "B": (70, 179, 230, 30),
                       "A": (148, 252, 19, 30),
                       "S": (253, 212, 22, 30),
                       "X": (253, 212, 22, 30),
                       "SH": (239, 239, 239, 30),
                       "XH": (239, 239, 239, 30)}

    rank = play_data["rank"]
    rank_color = rank_color_dict[rank]
    rank_text_color = (rank_color[0], rank_color[1], rank_color[2], 180)
    pp_text_fill = (163, 163, 163, 200) if rank == "F" else (255, 255, 255, 200)
    pp_text = f"{pp_raw:.2f}PP"
    pp_text_w, pp_text_h = d.textsize(pp_text, font_36)

    d.text((badge_width - 5 - pp_text_w, badge_height - 5 - pp_text_h), pp_text, fill=pp_text_fill, font=font_36)

    circle = Image.new('RGBA', (cover.size[0] * 2, cover.size[1] * 2), (255, 255, 255, 0))
    dc = ImageDraw.Draw(circle)

    dc.ellipse([((badge_width - 75) * 2, 5 * 2), ((badge_width - 5) * 2, 75 * 2)], fill=rank_color)
    if rank == "SH" or rank == "XH":
        dc.text(((badge_width - 55 - 15) * 2, 8 * 2), rank, fill=rank_text_color, font=font_48)
    else:
        dc.text(((badge_width - 55) * 2, 8 * 2), rank, fill=rank_text_color, font=font_50)

    circle = circle.resize(cover.size, resample=Image.BICUBIC)

    halfway_img = Image.alpha_composite(cover, txt)
    final_cover = Image.alpha_composite(halfway_img, circle)

    return final_cover, diff_rating, max_combo


def get_embed_text_from_beatmap(bmap_data):
    bmap_title = bmap_data["title"]
    bmap_artist = bmap_data["artist"]
    bmap_version = bmap_data["version"]
    bmap_creator = bmap_data["creator"]
    bmap_stars = float(bmap_data["difficultyrating"])
    bmap_setid = bmap_data["beatmapset_id"]
    bmap_id = bmap_data["beatmap_id"]
    title_text = f"{bmap_artist} - {bmap_title}"
    desc_text = f"**({bmap_creator}) [{bmap_version}] {bmap_stars:.2f} ⭐**"
    bmap_url = f"https://osu.ppy.sh/beatmapsets/{bmap_setid}#osu/{bmap_id}"
    cover_url = f"https://assets.ppy.sh/beatmaps/{bmap_setid}/covers/cover.jpg"
    return title_text, desc_text, bmap_url, cover_url


def get_embed_text_from_profile(user_data):
    osu_username = user_data["username"]
    player_playcount = user_data["playcount"]
    player_rank = user_data["pp_rank"]
    player_country_rank = user_data["pp_country_rank"]
    player_pp = user_data["pp_raw"]
    player_id = user_data["user_id"]

    return osu_username, player_id, player_playcount, player_rank, player_country_rank, player_pp


def parse_recent_play(score_data):
    score = score_data["score"]
    combo = score_data["maxcombo"]
    count50 = score_data["count50"]
    count100 = score_data["count100"]
    count300 = score_data["count300"]
    countmiss = score_data["countmiss"]
    _, mods_text = get_mods(score_data["enabled_mods"])
    rank = score_data["rank"]
    date = score_data["date"]
    timeago = time_ago(datetime.utcnow(), datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))

    return f'▸ Score Set {timeago}Ago\n'


if __name__ == "__main__":
    bmap_data = get_bmap_data(978026)
    get_country_rankings(bmap_data)
