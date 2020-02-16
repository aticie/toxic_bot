import discord
from utils import *
from discord.ext import commands
import logging
import asyncio
import math
import os

TOKEN = os.environ["DISCORD_TOKEN"]
RECENT_CHANNEL_DICT = {}

logger = logging.getLogger('Bot-Main')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('Bot.log')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s]: %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

client = commands.Bot(command_prefix="*", case_insensitive=True)


async def add_pages(ctx, msg, data, fixed_fields):
    max_index = len(data)
    num = 1

    called_by = fixed_fields["callsign"]

    if called_by == "country":
        max_page = math.ceil(max_index / 5)  # Show 5 results per page
    else:
        max_page = math.ceil(max_index / 3)  # Show 5 results per page
    if max_page <= 1:
        return
    title_text = fixed_fields["title_text"]
    desc_text = fixed_fields["desc_text"]
    author_name = fixed_fields["author_name"]
    author_icon_url = fixed_fields["author_icon_url"]
    bmap_url = fixed_fields["bmap_url"]
    cover_url = fixed_fields["cover_url"]
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

        embed2 = discord.Embed()
        if user != ctx.message.author:
            pass
        elif '⬅' in str(res.emoji):
            logger.info(f'<< Going backward on: {called_by} at channel_id: {ctx.channel.id}')
            num -= 1
            if num < 1:
                num = max_page

            begin = (num - 1) * 5
            end = min(num * 5, max_index)
            show_data = data[begin:end]

            if called_by == "country":
                embed2 = discord.Embed(title=title_text, description=desc_text, color=ctx.author.color, url=bmap_url)
                embed2.set_image(url=cover_url)
                embed2.set_author(name=author_name, icon_url=author_icon_url)

                add_embed_fields_on_country(embed2, show_data, begin)
            elif called_by == "compare":
                player_url = fixed_fields["player_url"]
                avatar_url = fixed_fields["avatar_url"]

                embed2 = discord.Embed(title=title_text, description=desc_text, url=bmap_url)
                embed2.set_image(url=cover_url)
                embed2.set_author(name=author_name, url=player_url, icon_url=avatar_url)

            embed2.set_footer(text=f"Page {num} of {max_page}")
            await msg.clear_reactions()
            await msg.edit(embed=embed2)

        elif '➡' in str(res.emoji):
            logger.info(f'>> Going forward on: {called_by} at channel_id: {ctx.channel.id}')
            num += 1
            if num > max_page:
                num = 1

            begin = (num - 1) * 5
            end = min(num * 5, max_index)
            show_data = data[begin:end]
            if called_by == "country":
                embed2 = discord.Embed(title=title_text, description=desc_text, color=ctx.author.color, url=bmap_url)
                embed2.set_image(url=cover_url)
                embed2.set_author(name="Turkey Country Ranks", icon_url="https://osu.ppy.sh/images/flags/TR.png")
                add_embed_fields_on_country(embed2, show_data, begin)
            elif called_by == "compare":
                player_url = fixed_fields["player_url"]
                avatar_url = fixed_fields["avatar_url"]

                embed2 = discord.Embed(title=title_text, description=desc_text, url=bmap_url)
                embed2.set_image(url=cover_url)
                embed2.set_author(name=author_name, url=player_url, icon_url=avatar_url)

            embed2.set_footer(text=f"Page {num} of {max_page}")

            await msg.clear_reactions()
            await msg.edit(embed=embed2)


@client.event
async def on_ready():
    print("We are ready to roll!")


@client.event
async def on_command_error(ctx, error):
    if ctx.command == None:
        return
    elif ctx.command.is_on_cooldown(ctx):
        await ctx.send(error)
    else:
        logger.error(error)
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

    channel_id = ctx.message.channel.id  # Discord channel id

    put_recent_on_file(bmap_id, channel_id)

    mods = recent_play['enabled_mods']
    _, mods_text = get_mods(mods)
    bmap_data = get_bmap_data(bmap_id, mods)
    bmapset_id = bmap_data["beatmapset_id"]
    cover_img_bytes, cover_from_cache = get_cover_image(bmapset_id)
    recent_image, diff_rating, max_combo = draw_user_play(osu_username, recent_play, cover_img_bytes, bmap_data,
                                                          cover_from_cache)
    bmap_data["difficultyrating"] = diff_rating
    bmap_data["max_combo"] = max_combo
    title_text, title_text2, bmap_url, _ = get_embed_text_from_beatmap(bmap_data)
    title_text += title_text2 + f" {mods_text}"
    osu_username, player_id, player_playcount, player_rank, player_country_rank, player_pp = get_embed_text_from_profile(
        user_data)

    recent_image.save("recent.png")

    footer_text = parse_recent_play(recent_play)

    embed = discord.Embed(title=title_text, color=ctx.message.author.color, url=bmap_url)
    embed.set_image(url="attachment://recent.png")
    embed.set_author(name=f"Most recent play of {osu_username}", url=f"https://osu.ppy.sh/users/{player_id}",
                     icon_url=f"http://s.ppy.sh/a/{player_id}")
    embed.set_footer(text=footer_text)
    await ctx.send(embed=embed, file=discord.File('recent.png'))

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

    channel_id = ctx.message.channel.id  # Discord channel id
    put_recent_on_file(bmap_id, channel_id)

    mods = recent_play['enabled_mods']
    _, mods_text = get_mods(mods)
    bmap_data = get_bmap_data(bmap_id, mods)
    bmapset_id = bmap_data["beatmapset_id"]
    cover_img_bytes, cover_from_cache = get_cover_image(bmapset_id)
    recent_image, diff_rating, max_combo = draw_user_play(osu_username, recent_play, cover_img_bytes, bmap_data,
                                                          cover_from_cache)
    bmap_data["difficultyrating"] = diff_rating
    bmap_data["max_combo"] = max_combo
    title_text, title_text2, bmap_url, _ = get_embed_text_from_beatmap(bmap_data)
    title_text += title_text2 + f" {mods_text}"
    osu_username, player_id, player_playcount, player_rank, player_country_rank, player_pp = get_embed_text_from_profile(
        user_data)

    recent_image.save("recent.png")

    footer_text = parse_recent_play(recent_play)

    embed = discord.Embed(title=title_text, color=ctx.message.author.color, url=bmap_url)
    embed.set_image(url="attachment://recent.png")
    embed.set_author(name=f"Most recent play of {osu_username}", url=f"https://osu.ppy.sh/users/{player_id}",
                     icon_url=f"http://s.ppy.sh/a/{player_id}")
    embed.set_footer(text=footer_text)
    await ctx.send(embed=embed, file=discord.File('recent.png'))


@client.command(name='compare', aliases=['cmp', 'c', 'cp'])
async def compare(ctx, *args):
    logger.info(
        f"Compare called from: {ctx.message.guild.name} - {ctx.message.channel.name} for: {ctx.author.display_name}:")
    channel_id = ctx.message.channel.id
    recent_channel_dict = get_value_from_dbase(channel_id, "recent")

    if channel_id not in recent_channel_dict:
        await ctx.send(
            "Hangi map ile karşılaştırmam gerektiğini bilmiyorum 😔")
        return
    else:
        bmap_id = recent_channel_dict[channel_id]

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
        recent_image, diff_rating, max_combo = draw_user_play(osu_username, scores_data[0], cover_img_bytes, bmap_data,
                                                              cover_from_cache)
        mods = scores_data[0]["enabled_mods"]
        bmap_data["difficultyrating"] = diff_rating
        bmap_data["max_combo"] = max_combo
        _, mods_text = get_mods(mods)
        title_text, title_text2, bmap_url, _ = get_embed_text_from_beatmap(bmap_data)
        title_text += title_text2 + f" {mods_text}"
        osu_username, player_id, player_playcount, player_rank, player_country_rank, player_pp = get_embed_text_from_profile(
            user_data)

        recent_image.save("recent.png")

        footer_text = parse_recent_play(scores_data[0])

        embed = discord.Embed(title=title_text, color=ctx.message.author.color, url=bmap_url)
        embed.set_image(url="attachment://recent.png")
        embed.set_author(name=f"Most recent play of {osu_username}", url=f"https://osu.ppy.sh/users/{player_id}",
                         icon_url=f"http://s.ppy.sh/a/{player_id}")
        embed.set_footer(text=footer_text)
        await ctx.send(embed=embed, file=discord.File('recent.png'))
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

    channel_id = ctx.message.channel.id
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
    channel_id = ctx.message.channel.id

    recent_channel_dict = get_value_from_dbase(channel_id, "recent")
    if len(args) == 0:
        if channel_id not in recent_channel_dict:
            await ctx.send(
                "Hangi mapi istediğini bilmiyorum 😔")
            return
        else:
            bmap_id = recent_channel_dict[channel_id]
    else:
        if args[0].startswith("http"):
            bmap_id = args[0].split("/")[-1]
            try:
                bmap_id = int(bmap_id)
            except:
                await ctx.send(f"Beatmap linkiyle ilgili bi sıkıntı var: {args[0]}\n\
                    Usage: `*country https://osu.ppy.sh/beatmapsets/1090677#osu/2284572`")
                return
        else:
            bmap_id = args[0]

    put_recent_on_file(bmap_id, channel_id)
    country_data = get_country_rankings_v2(bmap_id)
    bmap_data = get_bmap_data(bmap_id)
    if len(country_data) == 0:
        await ctx.send("Ülke sıralamasında kimsenin skoru yok 😔")
        return

    title_text, desc_text, bmap_url, cover_url = get_embed_text_from_beatmap(bmap_data)

    embed = discord.Embed(title=title_text, description=desc_text, color=ctx.author.color, url=bmap_url)
    embed.set_image(url=cover_url)
    embed.set_author(name="Turkey Country Ranks", icon_url="https://osu.ppy.sh/images/flags/TR.png")
    if len(country_data) > 5:
        embed = add_embed_fields_on_country(embed, country_data[:5], 0)
    else:
        embed = add_embed_fields_on_country(embed, country_data, 0)

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
