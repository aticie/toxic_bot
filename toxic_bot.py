import discord
from utils import *
from discord.ext import commands
import asyncio
import math
import os

TOKEN = os.environ["DISCORD_TOKEN"]

client = commands.Bot(command_prefix="*", case_insensitive=True)

@client.event
async def on_ready():
    print("We are ready to roll!")

@client.event
async def on_command_error(ctx, error):
    if ctx.command == None:
        pass
    elif ctx.command.is_on_cooldown:
        await ctx.send(error)

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


@client.command(name='recent', aliases=['rs', 'recnet', 'recenet', 'recnt', 'rec', 'rc', 'r'])
async def recent(ctx, *args):

    if len(args) == 0:
        author_id = ctx.message.author.id
        osu_username = get_osu_username(author_id)
    else:
        osu_username = " ".join(args)

    if osu_username == -1:
        await ctx.send(f"`Önce profilini linkle MAL` <:omar:475326551936729115>")
        return

    recent_play = get_recent(osu_username)
    if recent_play == -1:
        await ctx.send(f"`{osu_username} oyunu bırakmış quit w X:D`")
        return

    bmap_id = recent_play['beatmap_id']
    mods = recent_play['enabled_mods']
    bmap_data = get_bmap_data(bmap_id, mods)
    bmapset_id = bmap_data["beatmapset_id"]
    cover_img_bytes, cover_from_cache = get_cover_image(bmapset_id)


    recent_image = draw_recent_play(osu_username, recent_play, cover_img_bytes, bmap_data, cover_from_cache)
    recent_image.save("recent.png")

    await ctx.send(file=discord.File('recent.png'))

    pass


@client.command(name='country', aliases=['ctr', 'ct'])
@commands.cooldown(1, 10, commands.BucketType.user)
async def show_country(ctx, arg):

    bmap_id = arg
    bmap_data = get_bmap_data(bmap_id)
    country_data = get_country_rankings(bmap_data)

    bmap_title = bmap_data["title"]
    bmap_artist = bmap_data["artist"]
    bmap_version = bmap_data["version"]
    bmap_creator = bmap_data["creator"]
    bmap_stars = float(bmap_data["difficultyrating"])
    bmap_setid = bmap_data["beatmapset_id"]
    title_text = f"{bmap_artist} - {bmap_title}"
    desc_text = f"**({bmap_creator}) [{bmap_version}] {bmap_stars:.2f} ⭐**"
    bmap_url = f"https://osu.ppy.sh/beatmapsets/{bmap_setid}#osu/{bmap_id}"

    embed = discord.Embed(title=title_text, description=desc_text, color=0x00ff00, url=bmap_url)
    cover_url = f"https://assets.ppy.sh/beatmaps/{bmap_setid}/covers/cover.jpg"
    embed.set_image(url=cover_url)
    embed.set_author(name="Turkey Country Ranks", icon_url="https://osu.ppy.sh/images/flags/TR.png")
    if len(country_data) > 5:
        embed = add_embed_fields(embed, country_data[:5], 0)
    else:
        embed = add_embed_fields(embed, country_data, 0)

    msg = await ctx.send(embed=embed)

    max_index = len(country_data)
    num = 1
    max_page = math.ceil(max_index/5)

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

            begin = (num-1)*5
            end = min(num*5, max_index)

            embed2 = discord.Embed(title=title_text, description=desc_text, color=0x00ff00, url=bmap_url)
            cover_url = f"https://assets.ppy.sh/beatmaps/{bmap_setid}/covers/cover.jpg"
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

            begin = (num-1)*5
            end = min(num*5, max_index)

            embed2 = discord.Embed(title=title_text, description=desc_text, color=0x00ff00, url=bmap_url)
            cover_url = f"https://assets.ppy.sh/beatmaps/{bmap_setid}/covers/cover.jpg"
            embed2.set_image(url=cover_url)
            embed2.set_author(name="Turkey Country Ranks", icon_url="https://osu.ppy.sh/images/flags/TR.png")

            show_data = country_data[begin:end]
            add_embed_fields(embed2, show_data, begin)

            await msg.clear_reactions()
            await msg.edit(embed=embed2)


client.run(TOKEN)
