import os
import aiohttp

from helpers.parser import Parser

OSU_API = os.environ["OSU_API_KEY"]

game_mode_enum = {
    0: "Standard",
    1: "Taiko",
    2: "CtB",
    3: "Mania"
}


async def send_multi_play_embed(ctx, parser: Parser, plays: list):
    """
    Send list of plays to context in a paged embed fashion
    :param ctx: Discord context
    :param parser: Parser object from parsed command arguments
    :param plays: List of plays of the user
    :return: None
    """
    pass  # todo - Create and send multi play embed
    max_pages = len(plays) // 5 + 1
    player_country = plays[0]['user']['country_code']
    player_avatar_url = plays[0]['user']['avatar_url']
    player_country_rank = user_data['pp_country_rank']
    player_global_rank = user_data['pp_rank']
    author_icon_url = f"https://osu.ppy.sh/images/flags/{player_country}.png"
    player_url = f"https://osu.ppy.sh/users/{user_data['user_id']}"
    author_name = f"Most recent osu! standard plays for {parser.user}\n" \
                  f" (#{player_global_rank}) - {player_country} #{player_country_rank}"
    embed = discord.Embed(description=desc_text, color=ctx.author.color)
    embed.set_thumbnail(url=avatar_url)
    embed.set_author(
        name=author_name,
        url=player_url,
        icon_url=author_icon_url)
    for play in plays[:5]:
        await ctx.send(f"Requested multiple plays of {user} on beatmap {play['beatmap_id']}.")
    return


async def send_single_play_image(ctx, user, play):
    """
    Sends a single play to context as an image
    :param ctx: Discord context
    :param user: osu! username
    :param play: A single play of user
    :return: None
    """
    pass  # todo - Draw and send single play image
    await ctx.send(f"Requested single play of {user} on beatmap {play['beatmap_id']}.")
    return


async def get_recent_plays(parser):
    """
    Gets the recent plays of a player from osu! api
    :param user: osu! username
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
