import cv2
import numpy as np
import colorsys
import time
from datetime import datetime
import os
import random
from PIL import ImageFont
from oppai import *
import requests

with open("mods.txt", "r") as f:
    all_mods = f.readlines()

def strike(text):
    result = ''
    for c in text:
        result = result + c + '\u0336'
    return result

def make_readable_score(score):
    
    if type(score) == type(0):
        score = str(score)
    
    readable_score = ""
    score = score[::-1]
    for i in range((len(score)-1)//3+1):
        start = 0+i*3
        end = (i+1)*3
        readable_score += score[start:end]+"."
    readable_score = readable_score[:-1][::-1]
    return readable_score

def time_ago(time1, time2):
    time_diff = time1 - time2
    timeago = datetime(1,1,1) + time_diff
    time_limit = 0
    time_ago = ""
    if timeago.year-1 != 0:
        time_ago += "{} Year{} ".format(timeago.year-1, determine_plural(timeago.year-1))
        time_limit = time_limit + 1
    if timeago.month-1 !=0:
        time_ago += "{} Month{} ".format(timeago.month-1, determine_plural(timeago.month-1))
        time_limit = time_limit + 1
    if timeago.day-1 !=0 and not time_limit == 2:
        time_ago += "{} Day{} ".format(timeago.day-1, determine_plural(timeago.day-1))
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

def rounded_rectangle(img, topLeft, bottomRight, lineColor, thickness, lineType , cornerRadius):

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

    #// draw straight lines
    cv2.line(img2, (p1[0]+cornerRadius,p1[1]), (p2[0]-cornerRadius,p2[1]), lineColor, thickness)
    cv2.line(img2, (p2[0],p2[1]+cornerRadius), (p3[0],p3[1]-cornerRadius), lineColor, thickness)
    cv2.line(img2, (p4[0]+cornerRadius,p4[1]), (p3[0]-cornerRadius,p3[1]), lineColor, thickness)
    cv2.line(img2, (p1[0],p1[1]+cornerRadius), (p4[0],p4[1]-cornerRadius), lineColor, thickness)

    #// draw arcs
    cv2.ellipse(img2, (p1[0]+cornerRadius, p1[1]+cornerRadius),  ( cornerRadius, cornerRadius ), 180.0, 0, 90, lineColor, thickness, lineType )
    cv2.ellipse(img2, (p2[0]-cornerRadius, p2[1]+cornerRadius),  ( cornerRadius, cornerRadius ), 270.0, 0, 90, lineColor, thickness, lineType )
    cv2.ellipse(img2, (p3[0]-cornerRadius, p3[1]-cornerRadius),  ( cornerRadius, cornerRadius ), 0.0, 0, 90, lineColor, thickness, lineType )
    cv2.ellipse(img2, (p4[0]+cornerRadius, p4[1]-cornerRadius),  ( cornerRadius, cornerRadius ), 90.0, 0, 90, lineColor, thickness, lineType )

    cv2.rectangle(img2, (p1[0]+cornerRadius//5,p1[1]+cornerRadius//5), (p3[0]-cornerRadius//5,p3[1]-cornerRadius//5), lineColor, -1)

    return img2


def add_images(im1, im2, pos, alpha):

    im3 = np.copy(im1)
    im4 = np.copy(im2)
    h,w,c = im2.shape
    im3[pos[0]:pos[0]+h,pos[1]:pos[1]+w] = im4
    return cv2.addWeighted(im3, alpha, im1, 1 - alpha, 0)
    
    
def add_avatar_by_mask(im1, im2, mask, pos):
    
    im3 = mask.copy()
    h,w,c = im2.shape
    im3[(pos[1]-h//2):(pos[1]+h//2),(pos[0]-h//2):(pos[0]+h//2), :] = im2
    final_im = np.where(mask<255, im1, im3)
    return final_im


def add_images_by_mask(im1, im2, mask):
    new_img = np.where(mask<255, im1, im2)
    return new_img

def add_image_by_alpha(im1, im2, pos):
    im3 = im1.copy()
    h,w,c = im2.shape
    x = pos[0]
    y = pos[1]
    for i, height in enumerate(im2):
        for j, width in enumerate(height):
            alpha = width[3]/255
            im3[x+i,y+j,:] = alpha*width[:3]+(1-alpha)*im3[x+i,y+j,:]
    return im3

def dominant_color(img):
    data = np.reshape(img, (-1,3))
    data = np.float32(data)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    flags = cv2.KMEANS_RANDOM_CENTERS
    compactness,labels,centers = cv2.kmeans(data,1,None,criteria,10,flags)

    return centers[0]

def convert_hsv_to_rgb(hsv):
    h,s,v = hsv
    h = h/360
    s = s/255
    v = v/255
    
    r,g,b = colorsys.hsv_to_rgb(h,s,v)

    r = r*255
    g = g*255
    b = b*255
    rgb = (int(r),int(g),int(b))
    return rgb

def convert_bgr_to_hsv(bgr):
    b,g,r = bgr
    r = r/255
    g = g/255
    b = b/255
    
    h,s,v = colorsys.rgb_to_hsv(b,g,r)

    h = h*360
    s = s*255
    v = v*255
    hsv = (int(h),int(s),int(v))
    return hsv

def add_avatar_rim(avatar_im, avatar_pos, avatar_size, hue):

    h,s,v = hue
    s= 200
    v = 200
    rgb = convert_hsv_to_rgb((h,s,v))
    return cv2.circle(avatar_im, avatar_pos, avatar_size//2, rgb, 6, cv2.LINE_AA)


def image_from_cache_or_web(thing_id, url, folder):

    path = os.path.join(folder, thing_id+".jpg")
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
    url = "https://osu.ppy.sh/osu/"+beatmap_id
    path = os.path.join("Beatmaps", beatmap_id+".osu")
    ez = ezpp_new()
    ezpp_set_autocalc(ez, 1)
    if os.path.exists(path):
        ezpp_dup(ez, 'Beatmaps/{}.osu'.format(beatmap_id))
    else:
        print("Requesting: "+url)
        r = requests.get(url)
        with open(path, "w", encoding='utf-8') as f:
            f.write(r.content.decode("utf-8"))
        
        ezpp_dup(ez, 'Beatmaps/{}.osu'.format(beatmap_id))
        
    return ez


def calculate_pp(ez, count300, count100, count50, countmiss, mods, combo):
    
    count300 = int(count300)
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

    note_count = count300+count100+count50+countmiss
    acc = (count300+count100/3+count50/6)/note_count*100

    return acc
    
    

def get_mods(mods):
    
    global all_mods
    
    mod_list = []
    mods = int(mods)
    
    i = 1
    for mod in all_mods:
        if i&mods == i:
            mod_list.append(mod.rstrip())
        i=i<<1
    
    return mod_list