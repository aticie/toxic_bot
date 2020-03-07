import asyncio
import logging
import math
import subprocess
import sys
import discord
from discord.ext import commands

from utils import *

TOKEN = os.environ["DISCORD_TOKEN"]
prefix_file = os.path.join("Users", "prefixes.json")
prefixes = {}

logger = logging.getLogger('Bot-Main')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('Bot.log')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s]: %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


def get_prefix(client, message):
    with open(prefix_file, "r") as f:
        prefixes = json.load(f)

    return prefixes[str(message.guild.id)]


client = commands.Bot(command_prefix=get_prefix, case_insensitive=True)


def parse_args():
    return


@client.command(name='restart')
@commands.is_owner()
async def _restart_bot(ctx):
    await ctx.send("Restarting...")
    await client.logout()
    subprocess.call([sys.executable, "toxic_bot.py"])


def add_single_page(ctx, show_data, begin, fixed_fields):
    if fixed_fields["callsign"] == "country":
        desc_text = add_embed_fields_on_country(show_data, begin)
        embed2 = discord.Embed(title=fixed_fields["title_text"], description=desc_text,
                               color=ctx.author.color, url=fixed_fields["bmap_url"])
        embed2.set_image(url=fixed_fields["cover_url"])
        embed2.set_author(name=fixed_fields["author_name"], icon_url=fixed_fields["author_icon_url"])
    elif fixed_fields["callsign"] == "compare":
        embed2 = discord.Embed(title=fixed_fields["title_text"], description=fixed_fields["desc_text"],
                               color=ctx.author.color, url=fixed_fields["bmap_url"])
        embed2.set_image(url=fixed_fields["cover_url"])
        embed2.set_author(name=fixed_fields["author_name"], url=fixed_fields["player_url"],
                          icon_url=fixed_fields["avatar_url"])

    return embed2


async def add_pages(ctx, msg, data, fixed_fields):
    max_index = len(data)
    num = 1

    if fixed_fields["callsign"] == "country":
        result_per_page = 5  # Show 5 results per page
    else:
        result_per_page = 3  # Show 3 results per page

    max_page = math.ceil(max_index / result_per_page)
    if max_page <= 1:
        return

    reactmoji = ['⬅', '➡']
    while True:
        for react in reactmoji:
            await msg.add_reaction(react)

        def check_react(reaction, user):
            if reaction.message.id != msg.id:
                return False
            if user != ctx.message.author:
                return False
            if str(reaction.emoji) not in reactmoji:
                return False
            return True

        try:
            res, user = await client.wait_for('reaction_add', timeout=30.0, check=check_react)
        except asyncio.TimeoutError:
            return await msg.clear_reactions()

        if user != ctx.message.author:
            pass
        elif '⬅' in str(res.emoji):
            logger.info(f'<< Going backward on: {fixed_fields["callsign"]} at channel_id: {ctx.channel.id}')
            num -= 1
            if num < 1:
                num = max_page

            begin = (num - 1) * result_per_page
            end = min(num * result_per_page, max_index)
            show_data = data[begin:end]

            embed2 = add_single_page(ctx, show_data, begin, fixed_fields)
            embed2.set_footer(text=f"Page {num} of {max_page}")

            await msg.clear_reactions()
            await msg.edit(embed=embed2)

        elif '➡' in str(res.emoji):
            logger.info(f'>> Going forward on: {fixed_fields["callsign"]} at channel_id: {ctx.channel.id}')
            num += 1
            if num > max_page:
                num = 1

            begin = (num - 1) * result_per_page
            end = min(num * result_per_page, max_index)
            show_data = data[begin:end]

            embed2 = add_single_page(ctx, show_data, begin, fixed_fields)
            embed2.set_footer(text=f"Page {num} of {max_page}")

            await msg.clear_reactions()
            await msg.edit(embed=embed2)


@client.event
async def on_ready():
    global prefix_file, prefixes
    if os.path.exists(prefix_file):
        with open(prefix_file, "r") as f:
            prefixes = json.load(f)
        return
    else:
        with open(prefix_file, "w") as f:
            async for guild in client.fetch_guilds(limit=150):
                prefixes[str(guild.id)] = "*"

            json.dump(prefixes, f, indent=2)
        return


async def get_prefix(ctx):
    global prefix_file, prefixes

    with open(prefix_file, "r") as f:
        prefixes = json.load(f)

    await ctx.send(f"Server prefix is: {prefixes[str(ctx.message.guild.id)]}")


async def set_prefix(ctx, arg):
    global prefix_file, prefixes

    with open(prefix_file, "r") as f:
        prefixes = json.load(f)

    prefixes[str(ctx.message.guild.id)] = arg

    with open(prefix_file, "w") as f:
        json.dump(prefixes, f, indent=2)

    await ctx.send(f"Changed prefix to: {prefixes[str(ctx.message.guild.id)]}")


@client.command(name='prefix')
@commands.has_permissions(administrator=True)
async def prefix(ctx, arg1, arg2=None):
    if arg1 == "set":
        if arg2 is not None:
            await set_prefix(ctx, arg2)
        else:
            await ctx.send("Prefix'i ne yapmalıyım yazmamışsın 😔")
    elif arg1 == "get":
        await get_prefix(ctx)
    else:
        await ctx.send("Usage:` *prefix set <new-prefix>`\n`*prefix get`")
    return


@client.event
async def on_command_error(ctx, error):
    if ctx.command is None:
        return
    elif ctx.command.is_on_cooldown(ctx):
        await ctx.send(error)
    else:
        logger.error(error)
        return


async def check_args_for_map(ctx, args):
    channel_id = str(ctx.message.channel.id)
    bmap_id = get_value_from_dbase(channel_id, "recent")

    return_dict = {"bmap": bmap_id, "mods": []}

    if len(args) == 0:
        if bmap_id == -1:
            await ctx.send(f"İstediğin beatmapi bulamadım 😔")
            return None

    elif len(args) > 2:
        await ctx.send(f"Garip bir şey istedin anlamadım 😔 `{ctx.message.content}` ne demek?\n"
                       f"Usage: `*cmd <map_id> <mods>`")
        return None

    elif len(args) == 1:
        if args[0].startswith("http"):
            bmap_id = args[0].split("/")[-1]
            return_dict["bmap"] = bmap_id
        else:
            try:
                bmap_id = int(args[0])
                return_dict["bmap"] = bmap_id
            except:
                requested_mods = check_and_return_mods(args[0])
                return_dict["mods"] = requested_mods

    elif len(args) == 2:
        if args[0].startswith("http"):
            bmap_id = args[0].split("/")[-1]
            mods = check_and_return_mods(args[1])
            return_dict["bmap"] = bmap_id
            return_dict["mods"] = mods
        else:
            bmap_id = int(args[0])
            mods = check_and_return_mods(args[1])
            return_dict["bmap"] = bmap_id
            return_dict["mods"] = mods

    put_recent_on_file(bmap_id, channel_id)
    return return_dict


@client.command(name='map')
async def map(ctx, *args):
    logger.info(
        f"Map called from: {ctx.message.guild.name} - {ctx.message.channel.name} for: {ctx.author.display_name}:")

    args = await check_args_for_map(ctx, args)

    if args is None:
        await ctx.send("Usage: `*map <map_link> <mods>`")
        return

    bmap_id = args["bmap"]
    mods = args["mods"]

    bmap_data = beatmap_from_cache_or_web(bmap_id)
    bmap_metadata = get_bmap_data(bmap_id, mods)
    if bmap_data is None:
        await ctx.send("Böyle bir beatmap yok")
        return

    put_recent_on_file(bmap_id, ctx.message.channel.id)
    embed_fields = show_bmap_details(bmap_metadata, bmap_data, mods)
    embed = discord.Embed(title=embed_fields["title_text"], description=embed_fields["desc_text"],
                          url=embed_fields["title_url"])
    embed.set_author(name=embed_fields["author_text"])
    embed.set_image(url=embed_fields["cover_url"])
    for field in embed_fields["pp_fields"]:
        embed.add_field(name=field["name"], value=field["value"], inline=True)

    await ctx.send(embed=embed)
    return


@client.command(name='osulink', aliases=['link'])
async def link(ctx, *args):
    logger.info(f"Link called from: {ctx.message.guild.name} - {ctx.message.channel.name}")
    user_discord_id = ctx.author.id
    username = " ".join(args)
    ret = link_user_on_file(username, user_discord_id)

    # link_user_on_file returns 1 if username does not match with discord_id
    if ret == 1:
        await ctx.send(f"osu!'daki adını {username} yaptım")
        logger.info(f"Linked discord user: {ctx.author.display_name} with {username}")
    else:
        await ctx.send(f"Zaten {username} olarak linklisin 😔")
    pass


@client.command(name='recent', aliases=['rs', 'recnet', 'recenet', 'recnt', 'rcent', 'rcnt', 'rec', 'rc', 'r'])
async def recent(ctx, *args):
    logger.info(
        f"Recent called from: {ctx.message.guild.name} - {ctx.message.channel.name} with args: {' '.join(args)} for {ctx.author.display_name}")

    if len(args) == 0:
        author_id = ctx.message.author.id
        osu_username = get_value_from_dbase(author_id, "username")
    else:
        osu_username = " ".join(args)

    if osu_username == -1:
        await ctx.send(f"Kim olduğunu bilmiyorum 😔\nProfilini linklemelisin: `*link heyronii`")
        return

    recent_play = get_recent(osu_username)

    if recent_play == -1:
        await ctx.send(f"`{osu_username}` oyunu bırakmış 😔")
        return

    user_data = get_osu_user_data(username=osu_username)
    osu_username = user_data["username"]
    bmap_id = recent_play['beatmap_id']

    channel_id = str(ctx.message.channel.id)  # Discord channel id

    put_recent_on_file(bmap_id, channel_id)

    mods = recent_play['enabled_mods']
    _, mods_text = get_mods(mods)
    bmap_data = get_bmap_data(bmap_id, mods)
    bmapset_id = bmap_data["beatmapset_id"]
    cover_img_bytes, cover_from_cache = get_cover_image(bmapset_id)
    recent_image, diff_rating, max_combo, is_gif = draw_user_play(osu_username, recent_play, cover_img_bytes, bmap_data,
                                                                  cover_from_cache)
    bmap_data["difficultyrating"] = diff_rating
    bmap_data["max_combo"] = max_combo
    title_text, title_text2, bmap_url, _ = get_embed_text_from_beatmap(bmap_data)
    title_text += title_text2 + f" {mods_text}"
    osu_username, player_id, player_playcount, player_rank, player_country_rank, player_pp = get_embed_text_from_profile(
        user_data)

    footer_text = parse_recent_play(recent_play)

    embed = discord.Embed(title=title_text, color=ctx.message.author.color, url=bmap_url)

    embed.set_author(name=f"Most recent play of {osu_username}", url=f"https://osu.ppy.sh/users/{player_id}",
                     icon_url=f"http://s.ppy.sh/a/{player_id}")
    embed.set_footer(text=footer_text)
    if not is_gif:
        recent_image.save("recent.png")
        embed.set_image(url="attachment://recent.png")
        await ctx.send(embed=embed, file=discord.File('recent.png'))
    else:
        embed.set_image(url="attachment://recent.gif")
        await ctx.send(embed=embed, file=discord.File('recent.gif'))

    pass


@client.command(name='rb', aliases=[f'rb{i + 1}' for i in range(100)])
async def recent_best(ctx, *args):
    logger.info(
        f"Recent Best called from: {ctx.message.guild.name} - {ctx.message.channel.name} with command:"
        f" {ctx.invoked_with}{' '.join(args)} for {ctx.author.display_name}")

    if len(args) == 0:
        author_id = ctx.message.author.id
        osu_username = get_value_from_dbase(author_id, "username")
    else:
        osu_username = " ".join(args)

    if osu_username == -1:
        await ctx.send(f"Kim olduğunu bilmiyorum 😔\nProfilini linklemelisin: `*link heyronii`")
        return

    which_best = ctx.invoked_with[2:]
    if which_best == "":
        which_best = 1
    else:
        which_best = int(which_best)

    recent_play = get_recent_best(osu_username, date_index=which_best)

    user_data = get_osu_user_data(username=osu_username)
    osu_username = user_data["username"]
    bmap_id = recent_play['beatmap_id']

    channel_id = str(ctx.message.channel.id)  # Discord channel id
    put_recent_on_file(bmap_id, channel_id)

    mods = recent_play['enabled_mods']
    _, mods_text = get_mods(mods)
    bmap_data = get_bmap_data(bmap_id, mods)
    bmapset_id = bmap_data["beatmapset_id"]
    cover_img_bytes, cover_from_cache = get_cover_image(bmapset_id)
    recent_image, diff_rating, max_combo, is_gif = draw_user_play(osu_username, recent_play, cover_img_bytes, bmap_data,
                                                                  cover_from_cache)
    bmap_data["difficultyrating"] = diff_rating
    bmap_data["max_combo"] = max_combo
    title_text, title_text2, bmap_url, _ = get_embed_text_from_beatmap(bmap_data)
    title_text += title_text2 + f" {mods_text}"
    osu_username, player_id, player_playcount, player_rank, player_country_rank, player_pp = get_embed_text_from_profile(
        user_data)

    footer_text = parse_recent_play(recent_play)

    embed = discord.Embed(title=title_text, color=ctx.message.author.color, url=bmap_url)

    embed.set_author(name=f"Most recent play of {osu_username}", url=f"https://osu.ppy.sh/users/{player_id}",
                     icon_url=f"http://s.ppy.sh/a/{player_id}")
    embed.set_footer(text=footer_text)
    if not is_gif:
        recent_image.save("recent.png")
        embed.set_image(url="attachment://recent.png")
        await ctx.send(embed=embed, file=discord.File('recent.png'))
    else:
        embed.set_image(url="attachment://recent.gif")
        await ctx.send(embed=embed, file=discord.File('recent.gif'))


@client.command(name='osu')
async def show_osu_profile(ctx, *args):
    logger.info(
        f"Osu profile request called from: {ctx.message.guild.name} - {ctx.message.channel.name} with command:"
        f"*{ctx.invoked_with} {' '.join(args)} for {ctx.author.display_name}")

    author_id = ctx.message.author.id
    if len(args) == 0:
        osu_username = get_value_from_dbase(author_id, "username")
        if osu_username == -1:
            await ctx.send("Önce profilini linklemelisin: `*link <osu_username>`")
            return
        args = (osu_username,)

    for osu_username in args:
        real_uname = get_osu_user_data(osu_username)
        if real_uname is None:
            await ctx.send(f"`{osu_username}` bulunamadı... :pensive:")
            return
        real_username = real_uname["username"]
        user_data, achievements_data = get_osu_user_web_profile(real_username)
        osu_username = user_data["username"]
        user_id = user_data["id"]
        image = await draw_user_profile(user_data, achievements_data, ctx)

        img_to_send = io.BytesIO()
        image.save(img_to_send, format='PNG')
        img_to_send.seek(0)
        file = discord.File(img_to_send, "cover.png")
        embed = discord.Embed(color=ctx.message.author.color)
        embed.set_author(name=f"osu! profile for {osu_username}",
                         url=f"https://osu.ppy.sh/users/{user_id}",
                         icon_url=f"https://a.ppy.sh/{user_id}")

        embed.set_image(url="attachment://cover.png")
        await ctx.send(embed=embed, file=file)

    return


@client.command(name='osutop', aliases=['top'])
async def show_top_scores(ctx, *args):
    logger.info(
        f"Osutop called from: {ctx.message.guild.name} - {ctx.message.channel.name} for: {ctx.author.display_name}:")
    channel_id = str(ctx.message.channel.id)

    single_mode = False

    if len(args) == 0:
        author_id = ctx.message.author.id
        osu_username = get_value_from_dbase(author_id, "username")
    else:
        if "-p" in args:
            cutoff = args.index("-p")
            which_best = args[cutoff + 1]
            single_mode = True
            args = args[:cutoff]
            if cutoff != 0:
                osu_username = " ".join(args)
            else:
                author_id = ctx.message.author.id
                osu_username = get_value_from_dbase(author_id, "username")
        else:
            osu_username = " ".join(args)

    if osu_username == -1 or osu_username == "":
        await ctx.send(f"Kim olduğunu bilmiyorum 😔\nProfilini linklemelisin: `*link heyronii`")
        return

    user_data = get_osu_user_data(osu_username)
    if user_data is None:
        ctx.send(f"`{osu_username}` diye birisi yok 😔")
        return

    if not single_mode:
        user_id = user_data["user_id"]
        scores_data = get_user_best_v2(user_id)
        desc_text = add_embed_description_on_osutop(scores_data[:5])
        player_country = scores_data[0]["user"]["country_code"]
        player_country_rank = user_data['pp_country_rank']
        player_global_rank = user_data['pp_rank']
        author_icon_url = f"https://osu.ppy.sh/images/flags/{player_country}.png"
        embed = discord.Embed(description=desc_text, color=ctx.author.color)
        embed.set_thumbnail(url=scores_data[0]['user']['avatar_url'])
        embed.set_author(
            name=f"Top osu! standard plays for {user_data['username']}\n (#{player_global_rank}) - {player_country} #{player_country_rank}",
            url=f"https://osu.ppy.sh/users/{user_data['user_id']}",
            icon_url=author_icon_url)
        await ctx.send(embed=embed)
        return

    if single_mode:
        which_best = int(which_best)
        if not 101 > which_best > 0:
            await ctx.send(f"Olmayan bir skor istiyorsun 😔")
            return

        score_data = get_recent_best(osu_username, best_index=int(which_best) - 1)
        mods = score_data['enabled_mods']
        _, mods_text = get_mods(mods)
        bmap_id = score_data['beatmap_id']
        bmap_data = get_bmap_data(bmap_id)
        bmap_setid = bmap_data["beatmapset_id"]
        put_recent_on_file(bmap_id, channel_id)
        cover_img_bytes, cover_from_cache = get_cover_image(bmap_setid)
        recent_image, diff_rating, max_combo, is_gif = draw_user_play(osu_username, score_data, cover_img_bytes,
                                                                      bmap_data,
                                                                      cover_from_cache)
        bmap_data["difficultyrating"] = diff_rating
        bmap_data["max_combo"] = max_combo
        title_text, title_text2, bmap_url, _ = get_embed_text_from_beatmap(bmap_data)
        title_text += title_text2 + f" {mods_text}"
        osu_username, player_id, player_playcount, player_rank, player_country_rank, player_pp = get_embed_text_from_profile(
            user_data)

        footer_text = parse_recent_play(score_data)

        embed = discord.Embed(title=title_text, color=ctx.message.author.color, url=bmap_url)
        embed.set_author(name=f"Top #{which_best} play of {osu_username}", url=f"https://osu.ppy.sh/users/{player_id}",
                         icon_url=f"http://s.ppy.sh/a/{player_id}")
        embed.set_footer(text=footer_text)
        if not is_gif:
            recent_image.save("top_best.png")
            embed.set_image(url="attachment://top_best.png")
            await ctx.send(embed=embed, file=discord.File('top_best.png'))
        else:
            embed.set_image(url="attachment://recent.gif")
            await ctx.send(embed=embed, file=discord.File('recent.gif'))
        return
    else:
        user_id = user_data["user_id"]
        score_data = get_user_best_v2(user_id=user_id)


@client.command(name='compare', aliases=['cmp', 'c', 'cp'])
async def compare(ctx, *args):
    logger.info(
        f"Compare called from: {ctx.message.guild.name} - {ctx.message.channel.name} for: {ctx.author.display_name}:")
    channel_id = str(ctx.message.channel.id)
    bmap_id = get_value_from_dbase(channel_id, "recent")

    if bmap_id == -1:
        await ctx.send(
            "Hangi map ile karşılaştırmam gerektiğini bilmiyorum 😔")
        return

    if len(args) == 0:
        author_id = ctx.message.author.id
        osu_username = get_value_from_dbase(author_id, "username")
    else:
        osu_username = " ".join(args)

    if osu_username == -1:
        await ctx.send(f"Kim olduğunu bilmiyorum 😔\nProfilini linklemelisin: `*link heyronii`")
        return
    scores_data = get_user_scores_on_bmap(osu_username, bmap_id)
    if len(scores_data) == 0:
        await ctx.send(f"`{osu_username}` mapi oynamamış 😔")
        return
    user_data = get_osu_user_data(username=osu_username)
    bmap_data = get_bmap_data(bmap_id)
    osu_username = user_data["username"]
    player_id = user_data["user_id"]
    bmap_title = bmap_data["title"]
    bmap_artist = bmap_data["artist"]
    bmap_setid = bmap_data["beatmapset_id"]
    bmap_version = bmap_data["version"]
    author_name = f"Top osu! standard plays for {osu_username}"
    bmap_url = f"https://osu.ppy.sh/beatmapsets/{bmap_setid}#osu/{bmap_id}"
    player_url = f"https://osu.ppy.sh/users/{player_id}"
    avatar_url = f"http://s.ppy.sh/a/{player_id}"
    cover_url = f"https://assets.ppy.sh/beatmaps/{bmap_setid}/covers/cover.jpg"
    title_text = f"{bmap_artist} - {bmap_title} [{bmap_version}]"
    bmp = beatmap_from_cache_or_web(bmap_id)

    if len(scores_data) == 0:
        await ctx.send(f"`{osu_username}` oynamamış 😔")
        return

    if len(scores_data) == 1:
        cover_img_bytes, cover_from_cache = get_cover_image(bmap_setid)
        recent_image, diff_rating, max_combo, is_gif = draw_user_play(osu_username, scores_data[0], cover_img_bytes,
                                                                      bmap_data,
                                                                      cover_from_cache)
        mods = scores_data[0]["enabled_mods"]
        bmap_data["difficultyrating"] = diff_rating
        bmap_data["max_combo"] = max_combo
        _, mods_text = get_mods(mods)
        title_text, title_text2, bmap_url, _ = get_embed_text_from_beatmap(bmap_data)
        title_text += title_text2 + f" {mods_text}"
        osu_username, player_id, player_playcount, player_rank, player_country_rank, player_pp = get_embed_text_from_profile(
            user_data)

        footer_text = parse_recent_play(scores_data[0])

        embed = discord.Embed(title=title_text, color=ctx.message.author.color, url=bmap_url)
        embed.set_author(name=f"Most recent play of {osu_username}", url=f"https://osu.ppy.sh/users/{player_id}",
                         icon_url=f"http://s.ppy.sh/a/{player_id}")
        embed.set_footer(text=footer_text)
        if not is_gif:
            recent_image.save("recent.png")
            embed.set_image(url="attachment://recent.png")
            await ctx.send(embed=embed, file=discord.File('recent.png'))
        else:
            embed.set_image(url="attachment://recent.gif")
            await ctx.send(embed=embed, file=discord.File('recent.gif'))
        return

    if len(scores_data) > 3:
        desc_text = add_embed_description_on_compare(scores_data[:3], 0, bmp)
    else:
        desc_text = add_embed_description_on_compare(scores_data, 0, bmp)

    max_pages = len(scores_data) // 3 + 1
    embed = discord.Embed(title=title_text, description=desc_text, url=bmap_url)
    embed.set_image(url=cover_url)
    embed.set_author(name=author_name, url=player_url, icon_url=avatar_url)
    if max_pages != 1:
        embed.set_footer(text=f"Page 1 of {max_pages}")

    fixed_fields = {"callsign": "compare",
                    "title_text": title_text,
                    "desc_text": desc_text,
                    "author_name": author_name,
                    "author_icon_url": "https://osu.ppy.sh/images/flags/TR.png",
                    "player_url": player_url,
                    "avatar_url": avatar_url,
                    "cover_url": cover_url,
                    "bmap_url": bmap_url}

    msg = await ctx.send(embed=embed)

    await add_pages(ctx, msg, scores_data, fixed_fields)


@client.command(name='scores', aliases=['score', 'sc', 's'])
async def show_map_score(ctx, *args):
    logger.info(
        f"Scores called from: {ctx.message.guild.name} - {ctx.message.channel.name} for: {ctx.author.display_name}:")

    if len(args) == 0:
        await compare(ctx)
        return

    map_link = args[0]
    if map_link.startswith("http"):
        bmap_id = map_link.split("/")[-1]
        try:
            bmap_id = int(bmap_id)
        except:
            await ctx.send(f"`Beatmap linkiyle ilgili bi sıkıntı var: {map_link}`")
            return
    else:
        try:
            bmap_id = int(map_link)
        except:
            await ctx.send(f"`Beatmap id'siyle ilgili bi sıkıntı var: {map_link}`")
            return

    author_id = ctx.author.id
    try:
        player_name = args[1]
    except:
        player_name = get_value_from_dbase(author_id, "username")

    if player_name == -1:
        await ctx.send(f"`Kim olduğunu bilmiyorum 😔\nProfilini linklemelisin: `*link heyronii`")
        return

    channel_id = str(ctx.message.channel.id)
    put_recent_on_file(bmap_id, channel_id)

    scores_data = get_user_scores_on_bmap(player_name, bmap_id)
    user_data = get_osu_user_data(username=player_name)
    bmap_data = get_bmap_data(bmap_id)
    osu_username = user_data["username"]
    player_id = user_data["user_id"]
    bmap_title = bmap_data["title"]
    bmap_artist = bmap_data["artist"]
    bmap_setid = bmap_data["beatmapset_id"]
    bmap_version = bmap_data["version"]
    author_name = f"Top osu! standard plays for {osu_username}"
    bmap_url = f"https://osu.ppy.sh/beatmapsets/{bmap_setid}#osu/{bmap_id}"
    player_url = f"https://osu.ppy.sh/users/{player_id}"
    avatar_url = f"http://s.ppy.sh/a/{player_id}"
    cover_url = f"https://assets.ppy.sh/beatmaps/{bmap_setid}/covers/cover.jpg"
    title_text = f"{bmap_artist} - {bmap_title} [{bmap_version}]"
    bmp = beatmap_from_cache_or_web(bmap_id)

    if len(scores_data) > 3:
        desc_text = add_embed_description_on_compare(scores_data[:3], 0, bmp)
    else:
        desc_text = add_embed_description_on_compare(scores_data, 0, bmp)

    max_pages = len(scores_data) // 3 + 1
    embed = discord.Embed(title=title_text, description=desc_text, url=bmap_url)
    embed.set_image(url=cover_url)
    embed.set_author(name=author_name, url=player_url, icon_url=avatar_url)
    if max_pages != 1:
        embed.set_footer(text=f"Page 1 of {max_pages}")

    fixed_fields = {"callsign": "compare",
                    "title_text": title_text,
                    "desc_text": desc_text,
                    "author_name": author_name,
                    "author_icon_url": "https://osu.ppy.sh/images/flags/TR.png",
                    "player_url": player_url,
                    "avatar_url": avatar_url,
                    "cover_url": cover_url,
                    "bmap_url": bmap_url}

    msg = await ctx.send(embed=embed)

    await add_pages(ctx, msg, scores_data, fixed_fields)


@client.command(name='country', aliases=['ctr', 'ct'])
@commands.cooldown(1, 10, commands.BucketType.user)
async def show_country(ctx, *args):
    logger.info(
        f"Country called from: {ctx.message.guild.name} - {ctx.message.channel.name} for: {ctx.author.display_name}:")
    channel_id = str(ctx.message.channel.id)

    bmap_id = get_value_from_dbase(channel_id, "recent")
    if len(args) == 0:
        requested_mods = ""
        if bmap_id == -1:
            await ctx.send(
                "Hangi mapi istediğini bilmiyorum 😔")
            return
    elif len(args) < 3:
        if args[0].startswith("http"):
            bmap_id = args[0].split("/")[-1]
            try:
                bmap_id = int(bmap_id)
                requested_mods = ""
            except:
                await ctx.send(f"Beatmap linkiyle ilgili bi sıkıntı var: {args[0]}\n\
                    Usage: `*country https://osu.ppy.sh/beatmapsets/1090677#osu/2284572`")
                return
        elif len(args) == 1:
            try:
                bmap_id = int(args[0])
                requested_mods = ""
            except:
                requested_mods = args[0]
        if len(args) == 2:
            requested_mods = args[1]
    else:
        await ctx.send(
            "Ne yapmak istediğini anlamadım 😔\n Kullanım: `*ctr <map_link> <mods>`")
        return

    put_recent_on_file(bmap_id, channel_id)
    country_data = get_country_rankings_v2(bmap_id, requested_mods)
    bmap_data = get_bmap_data(bmap_id)
    if len(country_data) == 0:
        await ctx.send("Ülke sıralamasında kimsenin skoru yok 😔")
        return

    if len(country_data) > 5:
        desc_text = add_embed_fields_on_country(country_data[:5], 0)
    else:
        desc_text = add_embed_fields_on_country(country_data, 0)

    title_text, title_text2, bmap_url, cover_url = get_embed_text_from_beatmap(bmap_data)
    title_text = title_text + " " + title_text2
    embed = discord.Embed(title=title_text, description=desc_text, color=ctx.author.color, url=bmap_url)
    embed.set_image(url=cover_url)
    embed.set_author(name="Turkey Country Ranks", icon_url="https://osu.ppy.sh/images/flags/TR.png")

    msg = await ctx.send(embed=embed)

    fixed_fields = {"callsign": "country",
                    "title_text": title_text,
                    "desc_text": desc_text,
                    "author_name": "Turkey Country Ranks",
                    "author_icon_url": "https://osu.ppy.sh/images/flags/TR.png",
                    "cover_url": cover_url,
                    "bmap_url": bmap_url}
    await add_pages(ctx, msg, country_data, fixed_fields)


client.run(TOKEN)
