import os
import io
import glob
import aiohttp

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from database import Database
from helpers.parser import Parser
import discord

OSU_API = os.environ["OSU_API_KEY"]
CACHE_FOLDER = os.environ["CACHE_FOLDER"]
db = Database(os.environ["DB_PATH"])

game_mode_enum = {
    0: "Standard",
    1: "Taiko",
    2: "CtB",
    3: "Mania"
}


async def send_multi_play_embed(ctx, parser: Parser, player: Player, plays: list):
    """
    Send list of plays to context in a paged embed fashion
    :param ctx: Discord context
    :param parser: Parser object from parsed command arguments
    :param plays: List of plays of the user
    :param player: Player object
    :return: None
    """
    pass  # todo - Create and send multi play embed
    for play in plays[:5]:
        await ctx.send(f"Requested multiple plays of {player.username} on beatmap {play['beatmap_id']}.")
    return


async def send_single_play_image(ctx, parser: Parser, player: Player, play: dict):
    """
    Sends a single play to context as an image
    :param ctx: Discord context
    :param parser: Parser object from parsed command arguments
    :param play: A single play of user
    :param player: Player object
    :return: None
    """
    # todo - Draw and send single play image
    beatmap, cover_img = await get_beatmap_and_cover_object(play['beatmap_id'])
    score = OsuScore(play, player, beatmap, parser.game_mode, cover_img)
    image = await draw_single_score(score)

    img_to_send = io.BytesIO()
    image.save(img_to_send, format='PNG')
    img_to_send.seek(0)
    file = discord.File(img_to_send, "recent.png")

    await ctx.send(file=file)
    return


async def get_recent_plays(parser: Parser):
    """
    Gets the recent plays of a player from osu! api
    :param parser: Parsed arguments as a Parser object
    :return: None
    """

    rs_api_url = 'https://osu.ppy.sh/api/get_user_recent'
    params = {'k': OSU_API,  # Api key
              'u': parser.username,
              'limit': 50,
              'm': parser.game_mode}

    async with aiohttp.ClientSession() as session:
        async with session.get(rs_api_url, params=params) as rsp:
            the_response_json = await rsp.json()

    return the_response_json


async def get_player_details(parser: Parser):
    """
    Get player details from osu! api
    :param parser: Parser object
    :return: Returns a Player object
    """
    player = Player()

    player_from_db = db.get_player(parser.username)

    if player_from_db is None:
        user_api_url = 'https://osu.ppy.sh/api/get_user'
        params = {'k': OSU_API,
                  'u': parser.username}
        async with aiohttp.ClientSession() as session:
            async with session.get(user_api_url, params=params) as rsp:
                the_response_json = await rsp.json()

        player.from_dict(the_response_json[0])
        db.set_player(player)
    else:
        player.from_db(player_from_db)

    return player


async def get_player_avatar(player: Player):
    """
    Get player avatar from osu! or cache folder
    :param player: Player object
    :return:
    """
    avatars_folder = os.path.join(CACHE_FOLDER, "Avatars")
    avatar_path = glob.glob(avatars_folder + os.sep + f"{player.id}.*")

    if len(avatar_path) == 0:
        avatar_path = os.path.join(avatars_folder, f"{player.id}.png")
        avatar_url = f"http://s.ppy.sh/a/{player.id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as rsp:
                if rsp.status == 200:
                    avatar = await rsp.read()
                    avatar_img = Image.open(io.BytesIO(avatar))
                    avatar_img.save(avatar_path)
                else:
                    avatar_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    else:
        avatar_img = Image.open(avatar_path[0])

    return avatar_img


async def get_beatmap_and_cover_object(beatmap_id: int):
    """
    Get beatmap and its cover from osu!
    :param beatmap_id: beatmap id
    :return: Returns ezpp beatmap object and cover PIL.Image object
    """
    os.makedirs(CACHE_FOLDER, exist_ok=True)

    beatmap_id = beatmap_id
    map_path = os.path.join(CACHE_FOLDER, "Beatmaps", f"{beatmap_id}.osu")

    ez = ezpp_new()
    ezpp_set_autocalc(ez, 1)

    beatmap_details = db.get_beatmap(beatmap_id)

    if beatmap_details is None:
        beatmap_api_url = f"https://osu.ppy.sh/api/get_beatmaps"
        params = {'k': OSU_API,
                  'b': beatmap_id}
        async with aiohttp.ClientSession() as session:
            async with session.get(beatmap_api_url, params=params) as r:
                beatmap_json = await r.json()

        beatmap = Beatmap()
        beatmap.from_api_json(beatmap_json[0])
        db.set_beatmap(beatmap)
    else:
        beatmap = Beatmap()
        beatmap.from_db_object(beatmap_details)

    if not os.path.exists(map_path):

        try:
            bancho_url = f"https://osu.ppy.sh/osu/{beatmap_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(bancho_url) as r:
                    contents = await r.read()
                    with open(map_path, "w", encoding='utf-8') as f:
                        f.write(contents.decode("utf-8"))
                    print(f"Downloaded {beatmap_id} from osu!")

        except aiohttp.ServerTimeoutError as e:
            print(f"Downloading {beatmap_id} FAILED FROM OSU! {e}")
            print(f"Downloading {beatmap_id} from bloodcat!")

            bloodcat_url = f"https://bloodcat.com/osu/b/{beatmap_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(bloodcat_url) as r:
                    contents = await r.read()
                    if contents.decode('utf-8') == "* File not found or inaccessable!":
                        raise Exception(f"Beatmap {beatmap_id} could not be downloaded...")
                    else:
                        with open(map_path, "w", encoding='utf-8') as f:
                            f.write(contents.decode("utf-8"))

    cover_path = os.path.join(CACHE_FOLDER, "Beatmaps", f"{beatmap.beatmapset_id}.jpg")
    if not os.path.exists(cover_path):
        cover_url = f"https://assets.ppy.sh/beatmaps/{beatmap.beatmapset_id}/covers/cover.jpg"
        async with aiohttp.ClientSession() as session:
            async with session.get(cover_url) as cover_rsp:
                if cover_rsp.status == 200:
                    cover_img_data = await cover_rsp.read()
                    cover_img = Image.open(io.BytesIO(cover_img_data))
                    cover_img.save(cover_path)
                else:
                    cover_img = None
    else:
        cover_img = Image.open(cover_path)

    ezpp_dup(ez, map_path)
    beatmap.set_ezpp_obj(ez)

    return beatmap, cover_img


async def draw_single_score(score: OsuScore):
    """
    Draws a single score
    :param score: OsuScore object
    :return: Return the created PIL.Image object
    """
    beatmap = score.bmap
    player = score.player

    star_rating = float(ezpp_stars(beatmap.ez))
    player_pp = float(ezpp_pp(beatmap.ez))
    pp_text = f"{player_pp:.2f}pp"
    title_text = f"{beatmap.difficulty} - {beatmap.title}"

    # Left - Top - Right - Bottom
    margin = (25, 15, 15, 5)
    discord_dark = (54, 57, 63)
    cover = Image.new("RGBA", (900, 250), discord_dark) if score.cover is None else score.cover.convert("RGBA")
    cover = cover.filter(ImageFilter.GaussianBlur(5))

    avatar = await get_player_avatar(score.player)
    avatar = avatar.resize((80, 80))

    overlay_black = Image.new('RGBA', cover.size, (0, 0, 0, 180))
    cover = Image.alpha_composite(cover, overlay_black)

    draw = ImageDraw.Draw(cover)

    title_offset = draw_title(draw, title_text, margin)
    draw_details(draw, (beatmap.version, star_rating), title_offset, margin)
    uname_mid_pt = draw_username(draw, score.player.username, margin)
    cover.paste(avatar, (uname_mid_pt - 40, 125))
    draw_score_counts

    return cover


def draw_username(draw, username, margin):
    username_font = ImageFont.truetype(os.path.join(CACHE_FOLDER, "Fonts", "OpenSans-Bold.ttf"), 26)
    username_fill = (255, 255, 255, 255)
    size = draw.im.size
    uname_w, uname_h = get_real_textsize(username, draw, username_font)
    draw.text((margin[0], size[1] - margin[3] - uname_h), username, fill=username_fill, font=username_font)

    mid_point = margin[0] + uname_w//2
    return mid_point


def draw_details(draw, bmap_details, title_offset, margin):
    details_font = ImageFont.truetype(os.path.join(CACHE_FOLDER, "Fonts", "OpenSans-Bold.ttf"), 26)

    desc_fill = (255, 255, 255, 255)

    version = bmap_details[0]
    sr = bmap_details[1]
    details_text = f"[{version}] {sr:.2f}*"
    details_w, details_h = get_real_textsize(details_text, draw, details_font)

    details_changed = False
    while details_w > 660:
        details_changed = True
        version = version[:-1]
        details_w, details_h = get_real_textsize(details_text, draw, details_font)

    if details_changed:
        details_text = f"[{version}..] {bmap_details[1]:.2f}*"

    draw.text((margin[0], margin[1] + title_offset[1]), details_text, fill=desc_fill, font=details_font)

    return details_w, details_h


def draw_title(draw, title_text, margin):
    pp_font = ImageFont.truetype(os.path.join(CACHE_FOLDER, "Fonts", "OpenSans-Bold.ttf"), 36)
    title_font = ImageFont.truetype(os.path.join(CACHE_FOLDER, "Fonts", "OpenSans-Bold.ttf"), 36)

    title_fill = (255, 255, 255, 255)

    title_w, title_h = get_real_textsize(title_text, draw, title_font)

    title_changed = False
    while title_w > 660:
        title_changed = True
        title_text = title_text[:-1]
        title_w, _ = get_real_textsize(title_text, draw, title_font)

    if title_changed:
        title_text = f"{title_text}.."

    draw.text((margin[0], margin[1]), title_text, fill=title_fill, font=title_font)

    return title_w, title_h


def draw_corners(draw):
    discord_dark = (54, 57, 63)
    draw.line([(-0, 0), (5, 5)], fill=discord_dark, width=15)
    draw.line([(draw.im.size[0], 0), (draw.im.size[0] - 5, +5)], fill=discord_dark, width=15)
    draw.line([(0, draw.im.size[1]), (5, draw.im.size[1] - 5)], fill=discord_dark, width=15)
    draw.line([(draw.im.size[0], draw.im.size[1]), (draw.im.size[0] - 5, draw.im.size[1] - 5)], fill=discord_dark,
              width=15)


def get_real_textsize(text, draw, font):
    intext_margin = 5
    offset_x, offset_y = font.getoffset(text)
    width, height = draw.textsize(text, font=font)
    width += offset_x
    height += intext_margin
    return width, height
