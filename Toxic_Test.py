from PIL import ImageFont, ImageDraw, Image
import requests
import cv2
import numpy as np
import random
from datetime import datetime
import json
import os
import colorsys
from math import sqrt
import textwrap
import time
from utils import *

def create_recent_image(bmp_data, user_data, score_data, pp):
    
    text_spill = 36
    fill = (255, 255, 255, 255)
    
    # Score data
    # "score_id"         : "7654321",
    # "score"            : "1234567",
    # "username"         : "User name",
    # "count300"         : "300",
    # "count100"         : "50",
    # "count50"          : "10",
    # "countmiss"        : "1",
    # "maxcombo"         : "421",
    # "countkatu"        : "10",
    # "countgeki"        : "50",
    # "perfect"          : "0",          // 1 = maximum combo of map reached, 0 otherwise
    # "enabled_mods"     : "76",         // bitwise flag representation of mods used. see reference
    # "user_id"          : "1",
    # "date"             : "2013-06-22 9:11:16", // in UTC
    # "rank"             : "SH",
    # "pp"               : "1.3019",        //Float value , 4 decimals
    # "replay_available" : "1"              // 1 = osu! official servers store the replay, 0 - does not
    
    score = score_data["score"]
    rank = score_data["rank"]
    date = score_data["date"]   
    count300 = score_data["count300"]
    count100 = score_data["count100"]
    count50 = score_data["count50"]
    countmiss = score_data["countmiss"]
    mods = score_data["enabled_mods"]
    combo = score_data["maxcombo"]
    
    rank = "F"    
    rank_im = cv2.imread("Ranks/ranking-{}.png".format(rank.lower()), cv2.IMREAD_UNCHANGED)
    
    acc = get_acc(count300,count100,count50,countmiss)
    mod_list = get_mods(mods)
    
    # Beatmap data
    # "approved"             : "1",                   // 4 = loved, 3 = qualified, 2 = approved, 1 = ranked, 0 = pending, -1 = WIP, -2 = graveyard
    # "submit_date"          : "2013-05-15 11:32:26", // date submitted, in UTC
    # "approved_date"        : "2013-07-06 08:54:46", // date ranked, in UTC
    # "last_update"          : "2013-07-06 08:51:22", // last update date, in UTC. May be after approved_date if map was unranked and reranked.
    # "artist"               : "Luxion",
    # "beatmap_id"           : "252002",              // beatmap_id is per difficulty
    # "beatmapset_id"        : "93398",               // beatmapset_id groups difficulties into a set
    # "bpm"                  : "196",
    # "creator"              : "RikiH_",
    # "creator_id"           : "686209",
    # "difficultyrating"     : "5.744717597961426",   // The amount of stars the map would have ingame and on the website
    # "diff_aim"             : "2.7706098556518555",
    # "diff_speed"           : "2.9062750339508057",
    # "diff_size"            : "4",                   // Circle size value (CS)
    # "diff_overall"         : "8",                   // Overall difficulty (OD)
    # "diff_approach"        : "9",                   // Approach Rate (AR)
    # "diff_drain"           : "7",                   // Health drain (HP)
    # "hit_length"           : "114",                 // seconds from first note to last note not including breaks
    # "source"               : "BMS",
    # "genre_id"             : "2",                   // 0 = any, 1 = unspecified, 2 = video game, 3 = anime, 4 = rock, 5 = pop, 6 = other, 7 = novelty, 9 = hip hop, 10 = electronic (note that there's no 8)
    # "language_id"          : "5",                   // 0 = any, 1 = other, 2 = english, 3 = japanese, 4 = chinese, 5 = instrumental, 6 = korean, 7 = french, 8 = german, 9 = swedish, 10 = spanish, 11 = italian
    # "title"                : "High-Priestess",      // song name
    # "total_length"         : "146",                 // seconds from first note to last note including breaks
    # "version"              : "Overkill",            // difficulty name
    # "file_md5"             : "c8f08438204abfcdd1a748ebfae67421", # // md5 hash of the beatmap
    # "mode"                 : "0",                   // game mode,
    # "tags"                 : "kloyd flower roxas",  // Beatmap tags separated by spaces.
    # "favourite_count"      : "140",                 // Number of times the beatmap was favourited. (americans: notice the ou!)
    # "rating"               : "9.44779",
    # "playcount"            : "94637",               // Number of times the beatmap was played
    # "passcount"            : "10599",               // Number of times the beatmap was passed, completed (the user didn't fail or retry)
    # "count_normal"         : "388",
    # "count_slider"         : "222",
    # "count_spinner"        : "3",
    # "max_combo"            : "899",                 // The maximum combo a user can reach playing this beatmap.
    # "download_unavailable" : "0",                   // If the download for this beatmap is unavailable (old map, etc.)
    # "audio_unavailable"    : "0"                    // If the audio for this beatmap is unavailable (DMCA takedown, etc.)
    
    bmp_set_id = bmp_data["beatmapset_id"]
    bmp_id = bmp_data["beatmap_id"]
    bmp_artist = bmp_data["artist"]
    bmp_title = bmp_data["title"]
    bmp_creator = bmp_data["creator"]
    bmp_diff = float(bmp_data["difficultyrating"])
    bmp_cs = bmp_data["diff_size"]
    bmp_od = bmp_data["diff_overall"]
    bmp_ar = bmp_data["diff_approach"]
    bmp_hp = bmp_data["diff_drain"]
    bmp_bpm = bmp_data["bpm"]
    bmp_diff_name = bmp_data["version"]
    bmp_length = int(bmp_data["total_length"])
    bmp_length = "{0:d}:{1:d}".format(bmp_length//60, bmp_length%60)
    bmp_max_combo = bmp_data["max_combo"]
    
    
        
    # User Data
    # "user_id"              : "1",
    # "username"             : "User name",
    # "join_date"            : "2014-07-13 06:26:30", // In UTC
    # "count300"             : "1337",      // Total amount for all ranked, approved, and loved beatmaps played
    # "count100"             : "123",       // Total amount for all ranked, approved, and loved beatmaps played
    # "count50"              : "69",        // Total amount for all ranked, approved, and loved beatmaps played
    # "playcount"            : "42",        // Only counts ranked, approved, and loved beatmaps
    # "ranked_score"         : "666666",    // Counts the best individual score on each ranked, approved, and loved beatmaps
    # "total_score"          : "999999998", // Counts every score on ranked, approved, and loved beatmaps
    # "pp_rank"              : "2442",
    # "level"                : "50.5050",
    # "pp_raw"               : "3113",      // For inactive players this will be 0 to purge them from leaderboards
    # "accuracy"             : "98.1234",
    # "count_rank_ss"        : "54",
    # "count_rank_ssh"       : "54",
    # "count_rank_s"         : "81",        // Counts for SS/SSH/S/SH/A ranks on maps
    # "count_rank_sh"        : "81",
    # "count_rank_a"         : "862",    
    # "country"              : "DE",        // Uses the ISO3166-1 alpha-2 country code naming. See this for more information: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
    # "total_seconds_played" : "1823790",
    # "pp_country_rank"      :"1337",       // The user's rank in the country.
    # "events"               : [{           // Contains events for this user
    # "display_html"    : "<img src='\/images\/A_small.png'\/>...",
    # "beatmap_id"    : "222342",
    # "beatmapset_id"    : "54851",
    # "date"        : "2013-07-07 22:34:04", // In UTC
    # "epicfactor"    : "1"      // How "epic" this event is (between 1 and 32)
    
    user_id = user_data["user_id"]
    player_name = user_data["username"]
    country = user_data["country"]
    player_total_pp = user_data["pp_raw"]
    
    
    #bmp_detail_text = "{} - CS:{} AR:{} OD:{} HP:{} BPM:{} {:.2f}*".format(bmp_length, bmp_cs, bmp_ar, bmp_od, bmp_hp, bmp_bpm, bmp_diff)
    #if len(bmp_detail_text)>text_spill:
        #bmp_detail_text = "\n".join(textwrap.wrap(bmp_detail_text, width=text_spill))
    
    cover_url = 'https://assets.ppy.sh/beatmaps/{}/covers/cover.jpg'.format(bmp_set_id)
    avatar_url = 'https://a.ppy.sh/{}'.format(user_id)
    flag_url = 'https://osu.ppy.sh/images/flags/{}.png'.format(country)

    cover_folder = os.path.join(os.getcwd(),"Covers")
    if not os.path.exists(cover_folder):
        os.mkdir(cover_folder)

    avatar_folder = os.path.join(os.getcwd(),"Avatars")
    if not os.path.exists(avatar_folder):
        os.mkdir(avatar_folder)

    flag_folder = os.path.join(os.getcwd(),"Flags")
    if not os.path.exists(flag_folder):
        os.mkdir(flag_folder)
        
    rank_folder = os.path.join(os.getcwd(),"Ranks")
    if not os.path.exists(rank_folder):
        os.mkdir(rank_folder)
    
    cache_time = time.time()
    cover = image_from_cache_or_web(bmp_set_id, cover_url, cover_folder)
    avatar = image_from_cache_or_web(user_id, avatar_url, avatar_folder)
    flag = image_from_cache_or_web(country, flag_url, flag_folder)
    print("Cache takes {:.2f} sec".format(time.time()-cache_time))
    
    img_mod_time = time.time()
    size = 84
    avatar_resize = (size, size)
    avatar = cv2.resize(avatar, avatar_resize)
    avatar_mask = np.zeros(avatar.shape[0:2], dtype=np.uint8)
    avatar_mask = cv2.circle(avatar_mask, (size//2,size//2), size//2, 255, -1)
    avatar = cv2.copyTo(avatar,avatar_mask)
    
    # Resize and crop beatmap cover
    cover = cv2.resize(cover, (0,0), fx=1.2,fy=1.2)
    height, width, channel = cover.shape
    cropped_cover = cover[:, (width-height)//2-50:(width+height)//2+50, :]
    cropped_cover = cv2.GaussianBlur(cropped_cover, (5,5), cv2.BORDER_DEFAULT)
    
    overlay_margin = (15,15)
    top_left = (overlay_margin[0], overlay_margin[1])
    bottom_right = (cropped_cover.shape[1]-overlay_margin[0], cropped_cover.shape[0]-overlay_margin[1])
    
    # Find dominant color of the map background
    color = dominant_color(cropped_cover)
    hue, sat , val =  convert_bgr_to_hsv(color)
    val = max(40,val-100)
    rgb = convert_hsv_to_rgb((hue,sat,val))
    
    # Create transparent overlay
    rounded = rounded_rectangle(cropped_cover, top_left, bottom_right, rgb, 3, cv2.LINE_AA , 15)
    rounded = add_images(cropped_cover, rounded , (0,0), 0.7)
    
    # Avatar is aligned from top left
    avatar_pos = (65, 65)
    # Create mask for avatar and avatar rim (for blurring it)
    cover_mask = cv2.circle(np.zeros(rounded.shape, dtype=np.uint8), avatar_pos, size//2, (255,255,255), -1)
    cover_mask_for_blur = cv2.circle(np.zeros(rounded.shape, dtype=np.uint8), avatar_pos, size//2, (255,255,255), 8)
    

    # Flag is aligned from top right
    flag_size = (70,47)
    flag_pos = (cropped_cover.shape[1]-flag_size[0]-35,35)

    margin = (5,5)
    flag_mask_top_left = (flag_pos[0]+margin[0], flag_pos[1]+margin[1])
    flag_mask_btm_right = (flag_pos[0]+flag_size[0]-margin[0], flag_pos[1]+flag_size[1]-margin[0])    
    
    # Add avatar to the template
    avatar_im = add_avatar_by_mask(rounded, avatar, cover_mask, avatar_pos)
    rimmed = add_avatar_rim(avatar_im, avatar_pos, size, (hue,sat,val))
    rimmed_blurry = cv2.GaussianBlur(rimmed, (3,3), cv2.BORDER_DEFAULT)
    
    # Add flag to the template
    template = add_images_by_mask(rimmed, rimmed_blurry, cover_mask_for_blur)
    flag_mask = rounded_rectangle(np.zeros(template.shape), flag_mask_top_left, flag_mask_btm_right, (255,255,255), 6, cv2.LINE_AA , 8)
    flag_blur_mask = rounded_rectangle(np.zeros(template.shape), flag_mask_top_left, flag_mask_btm_right, (255,255,255), 6, cv2.LINE_AA , 8)
    flag_blur_mask = cv2.rectangle(flag_blur_mask, (flag_mask_top_left[0]+2,flag_mask_top_left[1]+2),(flag_mask_btm_right[0]-2,flag_mask_btm_right[1]-2), (0,0,0),-1)
    flagged_im = add_images(template, flag, (flag_pos[1],flag_pos[0]), 1)
    
    
    if rank != "F":
        rank_size = (80,97)
        rank_im = cv2.resize(rank_im,rank_size)
        # Rank position is anchored from bottom right
        rank_pos = (cropped_cover.shape[0] - rank_size[0] - 50, cropped_cover.shape[1] - rank_size[1])
    else:
        rank_size = rank_im.shape[0:2]
        rank_pos = (cropped_cover.shape[0] - rank_size[0] - 70, cropped_cover.shape[1] -  rank_size[1] - 50)
    # Add rank and mods to the image
    added_images = add_images_by_mask(template, flagged_im, flag_mask)
    flag_blurred = cv2.GaussianBlur(added_images, (5,5), cv2.BORDER_DEFAULT)
    added_images = add_images_by_mask(added_images, flag_blurred, flag_blur_mask)
    added_images = add_image_by_alpha(added_images, rank_im, rank_pos)
    mod_pos_mid = (rank_pos[0]-60, rank_pos[1]+20)
    mod_img_shift = 25
    shift = [i-len(mod_list)//2 for i in range(len(mod_list))]
    print(mod_list)
    for i,mod in enumerate(mod_list):
        mod_pos = (mod_pos_mid[0], mod_pos_mid[1]+shift[i]*mod_img_shift)
        mod_im = cv2.imread("Mods/selection-mod-{}.png".format(mod.lower()),cv2.IMREAD_UNCHANGED)
        mod_im = cv2.resize(mod_im, (45,45))
        added_images = add_image_by_alpha(added_images, mod_im, mod_pos)
    
    light_font_name = "Fonts/OpenSans-Light.ttf" 
    bold_font_name = "Fonts/OpenSans-Bold.ttf"
    reg_font_name = "Fonts/OpenSans-Regular.ttf"
    display_font_name = "Fonts/Aaargh.ttf"
    
    img_pil = Image.fromarray(added_images)
    draw = ImageDraw.Draw(img_pil)
    
    player_text = "{}".format(player_name)
    player_text_font = ImageFont.truetype(bold_font_name, 22)
    player_name_pos = (avatar_pos[0]+60, avatar_pos[1]-30)
    draw.text(player_name_pos, player_text, font = player_text_font, fill = fill)

    pp_text = "{}pp".format(player_total_pp)
    pp_text_font = ImageFont.truetype(reg_font_name, 26)
    pp_pos = (player_name_pos[0], player_name_pos[1]+30)
    draw.text(pp_pos, pp_text, font = pp_text_font, fill = fill)
    
    map_text = "{} - {} [{}]".format(bmp_artist, bmp_title,bmp_diff_name)
    if len(map_text)>text_spill:
        map_text_lines = textwrap.wrap(map_text, width=text_spill)
        map_text_row = len(map_text_lines)
        map_text = "\n".join(map_text_lines)
    map_text_font =ImageFont.truetype(reg_font_name, 30 - map_text_row*6)
    map_name_pos = (avatar_pos[0]-40, avatar_pos[1]+50)
    draw.multiline_text(map_name_pos, map_text, font = map_text_font, fill = fill, spacing=10)
    '''
    score_pos = (avatar_pos[0]-40, map_name_pos[1]+(map_text_row)*20)
    score_readable = make_readable_score(score)
    score_text = "{} - {:.2f}% - x{}/{}".format(score_readable, acc, combo, bmp_max_combo)
    score_text_font = ImageFont.truetype(reg_font_name, 18)
    draw.text(score_pos, score_text, font=score_text_font, fill = fill)
    '''
    bmp = beatmap_from_cache_or_web(bmp_id)
    pp_raw, pp_fc, pp_95, pp_ss = calculate_pp(bmp, count300, count100, count50, countmiss, mods, combo)
    font_s = 20+int((pp_ss/100)*4)
    score_detail_pos = (avatar_pos[0]-40, map_name_pos[1]+(map_text_row)*20+30)
    score_detail_text = "{:.0f}pp".format(pp_raw)
    score_detail_text_font = ImageFont.truetype(bold_font_name, font_s)
    draw.text(score_detail_pos, score_detail_text, font=score_detail_text_font, fill = fill)
    if rank=="F":
        line1 = (score_detail_pos[0],score_detail_pos[1]+int(round(font_s*2/3)))+(score_detail_pos[0]+len(score_detail_text)*font_s*2/3,score_detail_pos[1]+int(round(font_s*2/3)))
        draw.line(line1, fill=(0,0,0), width=3)

    
    timeago = time_ago(datetime.utcnow(), datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
    date_text = "Played {}ago".format(timeago) 
    date_text_font = ImageFont.truetype(light_font_name, 16)
    date_pos = (avatar_pos[0]-40, cropped_cover.shape[0]-35)
    draw.text(date_pos, date_text, font=date_text_font, fill = fill)

    #draw.multiline_text(bmp_detail_pos, bmp_detail_text, font=font, fill = fill)

    b, g, r = img_pil.split()
    img_pil = Image.merge("RGB", (r, g, b))
    img_pil.save('test_recent.jpg', format="JPEG", subsampling=0, quality=100)
    img_pil.show()
    
    print("Img modification takes {:.2f} sec".format(time.time()-img_mod_time))
    
    return None


with open("ex_bmp_data.json","r") as f:
    bmp_data = json.load(f)
with open("ex_score_data.json","r") as f:
    score_data = json.load(f)
with open("ex_user_data.json","r") as f:
    user_data = json.load(f)

pp = None
create_recent_image(bmp_data, user_data, score_data, pp)
