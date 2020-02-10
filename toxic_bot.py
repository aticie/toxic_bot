import discord
from utils import *
from discord.ext import commands
import asyncio
import math
import os

TOKEN = os.environ["DISCORD_TOKEN"]
RECENT_CHANNEL_DICT = {}

client = commands.Bot(command_prefix="*", case_insensitive=True)


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
        print(error)
        return


@client.command(name='osulink', aliases=['link'])
async def link(ctx, *args):
    user_discord_id = ctx.message.author.id
    username = " ".join(args)
    ret = link_user_on_file(username, user_discord_id)

    # link_user_on_file returns 1 if username does not match with discord_id
    if ret == 1:
        await ctx.send(f"osu!'daki adını {username} yaptım")
    else:
        await ctx.send(f"Zaten {username} olarak linklisin am k sala")
    pass


@client.command(name='recent', aliases=['rs', 'recnet', 'recenet', 'recnt','rcent','rcnt', 'rec', 'rc', 'r'])
async def recent(ctx, *args):
    global RECENT_CHANNEL_DICT

    if len(args) == 0:
        author_id = ctx.message.author.id
        osu_username = get_osu_username(author_id)
    else:
        osu_username = " ".join(args)

    if osu_username == -1:
        await ctx.send(f"`Önce profilini linkle` <:omar:475326551936729115>\n`Örnek: *link heyronii`")
        return

    recent_play = get_recent(osu_username)
    if recent_play == -1:
        await ctx.send(f"`{osu_username} oyunu bırakmış quit w X:D`")
        return

    user_data = get_osu_user_data(username=osu_username)
    bmap_id = recent_play['beatmap_id']

    channel_id = ctx.message.channel.id # Discord channel id
    RECENT_CHANNEL_DICT[channel_id] = bmap_id # Add recent play bmap id to recent-channel dictionary

    mods = recent_play['enabled_mods']
    _, mods_text = get_mods(mods)
    bmap_data = get_bmap_data(bmap_id, mods)
    bmapset_id = bmap_data["beatmapset_id"]
    cover_img_bytes, cover_from_cache = get_cover_image(bmapset_id)
    recent_image, diff_rating, max_combo = draw_recent_play(osu_username, recent_play, cover_img_bytes, bmap_data,
                                                            cover_from_cache)
    bmap_data["difficultyrating"] = diff_rating
    bmap_data["max_combo"] = max_combo
    title_text, title_text2, bmap_url, _ = get_embed_text_from_beatmap(bmap_data)
    title_text += title_text2 + f" {mods_text}"
    osu_username, player_id, player_playcount, player_rank, player_country_rank, player_pp = get_embed_text_from_profile(
        user_data)

    recent_image.save("recent.png")

    desc_text = parse_recent_play(recent_play)

    embed = discord.Embed(title=title_text, description=desc_text, color=0x00ff00, url=bmap_url)
    embed.set_image(url="attachment://recent.png")
    embed.set_author(name=f"Most recent play of {osu_username}", url=f"https://osu.ppy.sh/users/{player_id}",
                     icon_url=f"https://a.ppy.sh/{player_id}")

    await ctx.send(embed=embed, file=discord.File('recent.png'))

    pass


@client.command(name='country', aliases=['ctr', 'ct', 'c'])
@commands.cooldown(1, 10, commands.BucketType.user)
async def show_country(ctx, *args):
    global RECENT_CHANNEL_DICT
    channel_id = ctx.message.channel.id

    if len(args) == 0:
        if channel_id not in RECENT_CHANNEL_DICT:
            await ctx.send(
                "Son zamanlarda map atılmamış ve sen de map id'si yazmadın LAN ALLAH MIYIM BEN NASIL BİLEBİLİRİM HANGİ MAPİN COUNTRYSİNİ İSTEDİĞİNİ?")
            return
        else:
            bmap_id = RECENT_CHANNEL_DICT[channel_id]
    else:
        if args.startwith("http"):
            bmap_id = args[0].split("/")[-1]
        else:
            bmap_id = args[0]

    bmap_data = get_bmap_data(bmap_id)
    country_data = get_country_rankings(bmap_data)

    title_text, desc_text, bmap_url, cover_url = get_embed_text_from_beatmap(bmap_data)

    embed = discord.Embed(title=title_text, description=desc_text, color=0x00ff00, url=bmap_url)
    embed.set_image(url=cover_url)
    embed.set_author(name="Turkey Country Ranks", icon_url="https://osu.ppy.sh/images/flags/TR.png")
    if len(country_data) > 5:
        embed = add_embed_fields(embed, country_data[:5], 0)
    else:
        embed = add_embed_fields(embed, country_data, 0)

    msg = await ctx.send(embed=embed)

    max_index = len(country_data)
    num = 1
    max_page = math.ceil(max_index / 5) # Show 5 results per page

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
            print('<< Going backward')
            num -= 1
            if num < 1:
                num = max_page

            begin = (num - 1) * 5
            end = min(num * 5, max_index)

            embed2 = discord.Embed(title=title_text, description=desc_text, color=0x00ff00, url=bmap_url)
            embed2.set_image(url=cover_url)
            embed2.set_author(name="Turkey Country Ranks", icon_url="https://osu.ppy.sh/images/flags/TR.png")

            show_data = country_data[begin:end]
            add_embed_fields(embed2, show_data, begin)

            await msg.clear_reactions()
            await msg.edit(embed=embed2)

        elif '➡' in str(res.emoji):
            print('Going forward >>')
            num += 1
            if num > max_page:
                num = 1

            begin = (num - 1) * 5
            end = min(num * 5, max_index)

            embed2 = discord.Embed(title=title_text, description=desc_text, color=0x00ff00, url=bmap_url)
            embed2.set_image(url=cover_url)
            embed2.set_author(name="Turkey Country Ranks", icon_url="https://osu.ppy.sh/images/flags/TR.png")

            show_data = country_data[begin:end]
            add_embed_fields(embed2, show_data, begin)

            await msg.clear_reactions()
            await msg.edit(embed=embed2)


client.run(TOKEN)
