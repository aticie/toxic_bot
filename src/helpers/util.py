import os
import io
import aiohttp

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from database import Database
from helpers.parser import Parser
from data.player import Player
from data.beatmap import Beatmap
from data.osu_score import OsuScore
from oppai import *
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
              'u': parser.user,
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

    player_from_db = db.get_player(parser.user)

    if player_from_db is None:
        user_api_url = 'https://osu.ppy.sh/api/get_user'
        params = {'k': OSU_API,
                  'u': parser.user}
        async with aiohttp.ClientSession() as session:
            async with session.get(user_api_url, params=params) as rsp:
                the_response_json = await rsp.json()

        player.from_dict(the_response_json[0])
        db.set_player(player)
    else:
        player.from_db(player_from_db)

    return player


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
        cover_url = f"https://osu.ppy.sh/osu/{beatmap.beatmapset_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(cover_url) as cover_rsp:
                if cover_rsp.status == "200":
                    cover_img_data = await cover_rsp.read()
                    cover_img = Image.open(io.BytesIO(cover_img_data))
                    cover_img.save(cover_path)
                else:
                    cover_img = None

    ezpp_dup(ez, 'Beatmaps/{}.osu'.format(beatmap_id))
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

    title_text = beatmap.title
    pp_text = f"{ezpp_pp(beatmap.ez)}pp"
    details_text = f"[{beatmap.version}] {ezpp_stars(beatmap.ez):.2f}*"

    # Left - Top - Right - Bottom
    margin = (15, 15, 15, 15)

    cover = Image.new("RGBA", (900, 250), (128, 128, 128, 255)) if score.cover is None else score.cover
    cover = cover.filter(ImageFilter.GaussianBlur(5))

    overlay_black = Image.new('RGBA', cover.size, (0, 0, 0, 180))
    cover = Image.alpha_composite(cover, overlay_black)

    draw = ImageDraw.Draw(cover)

    draw_corners(draw)
    title_offset = draw_title(draw, title_text, margin)
    details_offset = draw_details(draw, details_text, title_offset, margin)

    return cover


def draw_details(draw, details_text, title_offset, margin):
    details_font = ImageFont.truetype(os.path.join(CACHE_FOLDER, "Fonts", "OpenSans-Bold.ttf"), 42)

    desc_fill = (255, 255, 255, 255)

    details_w, details_h = get_real_textsize(details_text, draw, details_font)
    draw.text((margin[0], title_offset[1]), details_text, fill=desc_fill, font=details_font)

    return details_w, details_h


def draw_title(draw, title_text, margin):
    pp_font = ImageFont.truetype(os.path.join(CACHE_FOLDER, "Fonts", "OpenSans-Bold.ttf"), 72)
    title_font = ImageFont.truetype(os.path.join(CACHE_FOLDER, "Fonts", "OpenSans-Bold.ttf"), 56)

    title_fill = (255, 255, 255, 255)

    title_w, title_h = get_real_textsize(title_text, draw, title_font)
    if title_w > 600:
        bmap_name = f"{title_text[:28]}.."

    draw.text((margin[0], 0), title_text, fill=title_fill, font=title_font)

    return title_w, title_h


def draw_corners(draw):
    draw.line([(-5, 5), (5, -5)], fill=(0, 0, 0), width=15)
    draw.line([(draw.im.size[0] - 5, 5), (draw.im.size[0] + 5, -5)], fill=(0, 0, 0), width=15)
    draw.line([(-5, draw.im.size[1] + 5), (5, draw.im.size[1] - 5)], fill=(0, 0, 0), width=15)
    draw.line([(draw.im.size[0] - 5, draw.im.size[1] + 5), (draw.im.size[0] + 5, draw.im.size[1] - 5)], fill=(0, 0, 0),
              width=15)


def get_real_textsize(text, draw, font):
    offset_x, offset_y = font.getoffset(text)
    width, height = draw.textsize(text, font=font)
    width += offset_x
    height += offset_y
    return width, height
