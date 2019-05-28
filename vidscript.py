import numpy as np
import requests
from scipy import stats
import pandas as pd
import urllib.request
from bs4 import BeautifulSoup
import time
import os
import tqdm
import imgkit as pic
from gtts import gTTS
from pygame import mixer
import re
import librosa
from PIL import Image
import sys

begin = time.time()

headers = requests.utils.default_headers()

# Update the headers with your custom ones
# You don't have to worry about case-sensitivity with
# the dictionary keys, because default_headers uses a custom
# CaseInsensitiveDict implementation within requests' source code.
headers.update(
    {
        'User-Agent': 'mac:content aggregation: (by /u/agent_undercover_fbi)'

    }
)

if (len(sys.argv) == 1):
    print('Scrubbing for top post on r/askreddit')

    print ('Waiting 2 seconds to avoid being declared a bot')
    time.sleep(2)

    #Obtaining top post from ask reddit subreddit
    base_url = 'https://old.reddit.com'
    start_url = base_url + '/r/AskReddit/top/'
    response = requests.get(start_url, headers = headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    posts = soup.find(id="siteTable")
    articles = posts.findAll('p', class_="title")
    top_post_title = ''
    top_post_link = ''

    top_post_title = articles[0].a.get_text()
    top_post_link = base_url + articles[0].find('a', href=True)['href'] + '?sort=top'

    print('Top URL obtained')
    print('Accessing the post ' + top_post_title)
    time.sleep(2)
else:
    top_post_link = sys.argv[1] + '?sort=top'

#At this point we have found the link for the top post and must access it and get the data
new_response = requests.get(top_post_link, headers = headers)
new_soup = BeautifulSoup(new_response.text, 'html.parser')
print (top_post_link)

url_split = top_post_link.split('/')
class_id = "siteTable_t3_"+url_split[6]
title = new_soup.find('p', class_="title").find('a').get_text().strip()

body = new_soup.find(id=class_id)

file_title = title.replace(" ", "")[:10]
ft = file_title.replace("'","")
file_title = ft.replace(',','')

#Create the tile page
print('Creating the opening page')
intro_file = open("intro.html", 'w')
intro_file.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><style>html, head, body {margin: 0px;padding: 0px;background: rgb(255, 255, 255) none repeat scroll 0% 0%;border: 1px solid rgb(237, 239, 241);}body {width: 1280px;height: 720px;}body h1 {color: rgb(26, 26, 27);position:absolute;top:30%;transform:translateY(-50%); margin: 0 20px; font-family: \'IBM Plex Sans\', \'Helvetica Neue\', Arial, sans-serif;font-size: 4em;}</style></head><body><h1>' +title+'</h1></body></html>')
intro_file.close()
aud_fil = gTTS(title)
aud_name = "intro.mp3"
aud_fil.save(aud_name)

f_title = os.path.realpath('intro.html')
x_image = 'intro_'+file_title+'.png'
pic.from_file(f_title, x_image)

with Image.open(x_image) as img:
    width, height = img.size
    crop_range = (width-1280, height-720,width, height)
    cropped = img.crop(crop_range)
    cropped.save(x_image)

os.system("ffmpeg -loop 1 -y -i "+ x_image +" -i intro.mp3 -ac 1 -b:a 32k -shortest -f mpeg intro_"+file_title+".mpeg")
os.remove('intro.mp3')
os.remove('intro.html')

print('Extracting parent posts')
parent_comments = body.findChildren("div", recursive=False)

all_user_posts = []
all_comments = []
for p in tqdm.tqdm(parent_comments):
    info = p.find('p', class_ = 'tagline')
    bio = []
    temp_text = p.find('div', class_ = 'md')
    other_text = []
    if temp_text is not None:
        text = temp_text.findAll('p')
        for t in range(len(text)):
            other_text.append(text[t].get_text().strip().split('.'))
            for o in range(len(other_text[t]) - 1):
                other_text[t][o] += '.' 
        bio.append(info.findAll('a')[1].get_text())
        if (info.find('span', class_ = 'score unvoted') is not None):
            bio.append(info.find('span', class_ = 'score unvoted').get_text())
        bio.append(info.time.get_text())
        if (info.find('span', class_ = 'awardings-bar') is not None):
            x = info.find('span', class_ = 'awardings-bar').findAll('a')
            for xi in x:
                bio.append(xi.get_text())
        all_user_posts.append(bio)
        all_comments.append(other_text)
        
print('Extracting first child of all posts')
parent_comments = body.findChildren("div", recursive=False)

all_user_post_replies = []
all_comment_replies = []
for p in tqdm.tqdm(parent_comments):
    bio = []
    text = []
    other_text = []
    if (len(p.findAll('p', class_ = 'tagline')) > 1) and (len(p.findAll('div', class_ = 'md')) > 1):
        info = p.findAll('p', class_ = 'tagline')[1]
        temp_text = p.findAll('div', class_ = 'md')[1]
        if temp_text is not None:
            text = temp_text.findAll('p')
            for t in range(len(text)):
                other_text.append(text[t].get_text().strip().split('.'))
                for o in range(len(other_text[t])-1):
                    other_text[t][o] += '.' 
            
            bio.append(info.findAll('a')[1].get_text())
            if (info.find('span', class_ = 'score unvoted') is not None):
                bio.append(info.find('span', class_ = 'score unvoted').get_text())
            bio.append(info.time.get_text())
            if (info.find('span', class_ = 'awardings-bar') is not None):
                x = info.find('span', class_ = 'awardings-bar').findAll('a')
                for xi in x:
                    bio.append(xi.get_text())
    if (p.find('div', class_ = 'md')):
        all_comment_replies.append(other_text)
        all_user_post_replies.append(bio)

print('Generating audio files and associated html elememnts')


files = []

def write_to_html_main(i, t, a):
    name = str(i) + '_m_Paragraph_' + str(t+1) + '-of-' + str(len(all_comments[i]))+'_Sentance_' + str(a+1)+ '-of-' + str(len(all_comments[i][t])) + ".html"
    
    out_fil = open(name, 'w')
    
#     out_fil.write('<!DOCTYPE html><html><style>html, head, body {margin: 0px;padding: 0px;background: rgb(255, 255, 255) none repeat scroll 0% 0%;border: 1px solid rgb(237, 239, 241);}body {width: 1280px;height: 720px;display:inline-block;}#main-container {margin-left:5px;}#response-container {margin-left:25px;}.name-bar p {display: inline-block;margin-bottom:0px;padding-bottom: 0px;}#everything {position: relative;top: 50%;transform: translateY(-50%);}.name {font-size: 18px;font-weight: 400;line-height: 24px;color: rgb(68, 78, 89);}.time, .points {font-size: 18px;font-weight: 400;line-height: 24px;color: rgb(124, 124, 124);padding-left: 8px;flex: 0 0 auto;}p {-moz-box-align: center;align-items: center;line-height: 24px;display: flex;transition: opacity 0.2s ease 0s;margin-left: 0px;min-height: 27px;color: rgb(26, 26, 27);font-family: "Noto Sans", sans-serif;font-size:21px;}#text p {padding: 2px 0;margin:0px;width: 100%;padding: 0.25em 0px;}</style><head></head><script type="text/javascript">var objDiv = document.getElementById(\'everything\');objDiv.scrollTop = objDiv.scrollHeight-objDiv.clientHeight;</script><body><div id = "everything"><div id="main-container"><div class="name-bar">')
    out_fil.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><style>html, head, body {margin: 0px;padding: 0px;background: rgb(255, 255, 255);}body {width: 1280px;height: 720px;display:inline-block;}#main-container {margin-left:5px;}#response-container {margin-left:25px;}.name-bar p {display: inline-block;margin-bottom:0px;padding-bottom: 0px;}#everything {position: relative; height:inherit; width:inherit; overflow:scroll;}.name {font-size: 18px;font-weight: 400;line-height: 24px;color: rgb(68, 78, 89);}.time, .points {font-size: 18px;font-weight: 400;line-height: 24px;color: rgb(124, 124, 124);padding-left: 8px;flex: 0 0 auto;}p {-moz-box-align: center;align-items: center;line-height: 24px;display: flex;transition: opacity 0.2s ease 0s;margin-left: 0px;min-height: 27px;color: rgb(26, 26, 27);font-family: "Noto Sans", sans-serif;font-size:21px;}#text p {padding: 2px 0;margin:0px;width: 100%;padding: 0.25em 0px;}</style></head><body><div id = "everything"><div id="main-container"><div class="name-bar">')
    out_fil.write('<p class = "name">'+all_user_posts[i][0]+'</p>')
    out_fil.write('<p class = "points">'+all_user_posts[i][1]+'</p>')
    out_fil.write('<p class = "points">  · </p>')
    out_fil.write('<p class = "time">'+all_user_posts[i][2]+'</p></div><div id="text">')
    for t0 in range(len(all_comments[i])):
        if (t0 > t):
            break
        out_fil.write('<p>')
        for a0 in range(len(all_comments[i][t0])):
            if (a0 > a and (t0 >= t)):
                break
            else:
                out_fil.write(all_comments[i][t0][a0])
        out_fil.write('</p>')
    out_fil.write('</div></div></div><script type="text/javascript">var objDiv = document.getElementById(\'everything\');objDiv.scrollTop = objDiv.scrollHeight-objDiv.clientHeight;</script></body></html>')
    files.append(name)
    out_fil.close()
    
def write_to_html_lil_comment(i, t, a):
    name = str(i) + '_s_Paragraph_' + str(t+1) + '-of-' + str(len(all_comment_replies[i]))+'_Sentance_' + str(a+1)+ '-of-' + str(len(all_comment_replies[i][t])) + ".html"
    
    out_fil = open(name, 'w')
    
#     out_fil.write('<!DOCTYPE html><html><style>html, head, body {margin: 0px;padding: 0px;background: rgb(255, 255, 255);border: 1px solid rgb(237, 239, 241);}body {width: 1280px;height: 720px;display:inline-block;}#main-container {margin-left:5px;}#response-container {margin-left:25px;}.name-bar p {display: inline-block;margin-bottom:0px;padding-bottom: 0px;}#everything {position: relative;top: 50%;transform: translateY(-50%); height: inherit; width: inherit; overflow: scroll;}.name {font-size: 18px;font-weight: 400;line-height: 24px;color: rgb(68, 78, 89);}.time, .points {font-size: 18px;font-weight: 400;line-height: 24px;color: rgb(124, 124, 124);padding-left: 8px;flex: 0 0 auto;}p {-moz-box-align: center;align-items: center;line-height: 24px;display: flex;transition: opacity 0.2s ease 0s;margin-left: 0px;min-height: 27px;color: rgb(26, 26, 27);font-family: "Noto Sans", sans-serif;font-size:21px;}#text p {padding: 2px 0;margin:0px;width: 100%;padding: 0.25em 0px;}</style><head></head><script type="text/javascript">var objDiv = document.getElementById(\'everything\');objDiv.scrollTop = objDiv.scrollHeight-objDiv.clientHeight;</script><body><div id = "everything"><div id="main-container"><div class="name-bar">')
    out_fil.write('<!DOCTYPE html><html><head><style>html, head, body {margin: 0px;padding: 0px;background: rgb(255, 255, 255);}body {width: 1280px;height: 720px;display:inline-block;}#main-container {margin-left:5px;}#response-container {margin-left:25px;}.name-bar p {display: inline-block;margin-bottom:0px;padding-bottom: 0px;}#everything {position: relative; height: inherit; width: inherit; overflow: scroll;}.name {font-size: 18px;font-weight: 400;line-height: 24px;color: rgb(68, 78, 89);}.time, .points {font-size: 18px;font-weight: 400;line-height: 24px;color: rgb(124, 124, 124);padding-left: 8px;flex: 0 0 auto;}p {-moz-box-align: center;align-items: center;line-height: 24px;display: flex;transition: opacity 0.2s ease 0s;margin-left: 0px;min-height: 27px;color: rgb(26, 26, 27);font-family: "Noto Sans", sans-serif;font-size:21px;}#text p {padding: 2px 0;margin:0px;width: 100%;padding: 0.25em 0px;}</style><meta charset="UTF-8"></head><body><div id = "everything"><div id="main-container"><div class="name-bar">')
    out_fil.write('<p class = "name">'+all_user_posts[i][0]+'</p>')
    out_fil.write('<p class = "points">'+all_user_posts[i][1]+'</p>')
    out_fil.write('<p class = "points">  · </p>')
    out_fil.write('<p class = "time">'+all_user_posts[i][2]+'</p></div><div id="text">')
    for t0 in range(len(all_comments[i])):
        out_fil.write('<p>')
        for a0 in range(len(all_comments[i][t0])):
            out_fil.write(all_comments[i][t0][a0])
        out_fil.write('</p>')
        
    out_fil.write('</div><div id="response-container"><div class="name-bar">')
    out_fil.write('<p class = "name">'+all_user_post_replies[i][0]+'</p>')
    out_fil.write('<p class = "points">'+all_user_post_replies[i][1]+'</p>')
    out_fil.write('<p class = "points">  · </p>')
    out_fil.write('<p class = "time">'+all_user_post_replies[i][2]+'</p></div><div id="text">')
    for t0 in range(len(all_comment_replies[i])):
        if (t0 > t):
            break
        out_fil.write('<p>')
        for a0 in range(len(all_comment_replies[i][t0])):
            if (a0 > a and (t0 >= t)):
                break
            else:
                out_fil.write(all_comment_replies[i][t0][a0])
        out_fil.write('</p>')
    out_fil.write('</div></div></div></div></div><script type="text/javascript">var objDiv = document.getElementById(\'everything\');objDiv.scrollTop = objDiv.scrollHeight-objDiv.clientHeight;</script></body></html>')
    files.append(name)
    out_fil.close()

def get_duration(filename):
    return librosa.core.get_duration(filename=filename)

total_audio_length = 0
max_audio_length = 600

for i in tqdm.tqdm(range(len(all_user_posts))):
    for t in range(len(all_comments[i])):
        for a in range(len(all_comments[i][t])):
            if  len(all_user_posts[i]) >= 3:
                write_to_html_main(i,t,a)
                if all_comments[i][t][a]:
                    if re.search('[a-zA-Z]', all_comments[i][t][a]):
                        aud_fil = gTTS(all_comments[i][t][a])
                        aud_name = str(i) + '_m_Paragraph_' + str(t + 1) + '-of-' + str(len(all_comments[i]))+'_Sentance_' + str(a+1)+ '-of-' + str(len(all_comments[i][t])) + ".mp3"
                        aud_fil.save(aud_name)
                        total_audio_length += get_duration(aud_name)
    if len(all_user_post_replies[i]) > 0:
        for t in range(len(all_comment_replies[i])):
            for a in range(len(all_comment_replies[i][t])):
                if len(all_user_post_replies[i]) >= 3 and len(all_user_posts[i]) >= 3:
                    write_to_html_lil_comment(i,t,a)
                    if all_comment_replies[i][t][a]:
                        if re.search('[a-zA-Z]', all_comment_replies[i][t][a]):
                            aud_fil = gTTS(all_comment_replies[i][t][a])
                            aud_name = str(i) + '_s_Paragraph_' + str(t + 1) + '-of-' + str(len(all_comment_replies[i]))+'_Sentance_' + str(a+1)+ '-of-' + str(len(all_comment_replies[i][t])) + ".mp3"
                            aud_fil.save(aud_name)
                            total_audio_length += get_duration(aud_name)
    if (total_audio_length > max_audio_length):
        break

print('Quit with ' + str(total_audio_length) + 's of audio')

print('Creating visual elemenst from the html pages')
for file in tqdm.tqdm(files):
    f = os.path.realpath(file)
    x = file.replace('html', 'png')
    pic.from_file(f, x)

print('Cropping images')

for file in tqdm.tqdm(files):
    f = os.path.realpath(file)
    x = file.replace('html', 'png')
    x0 = file.replace('html', 'png')
    with Image.open(x) as img:
        width, height = img.size
        crop_range = (width-1280, height-720,width, height)
        cropped = img.crop(crop_range)
        cropped.save(x0)

print('Combining audio with pngs to create each individual clip')

vids = []
for file in tqdm.tqdm(range(len(files))):
    f = os.path.realpath(files[file])
    x = files[file].replace('html', 'mp3')
    y = files[file].replace('html', 'png')
    z = files[file].replace('html', 'mpeg')
    os.remove(f)
    if (os.path.isfile(x)):
#         os.system("ffmpeg -loop 1 -y -i "+ y +" -i " + x +" -r 60 -b:v 1M -ar 44100 -ac 1 -b:a 32k -acodec copy -shortest -maxrate 8M -bufsize 4M " + z)
        os.system("ffmpeg -loop 1 -y -i "+ y +" -i " + x +" -b:a 32k -shortest -f mpeg " + z)
        os.remove(y)
        os.remove(x)
        vids.append(z)


print('Combining all clips')

fileObject = open("list.txt", "w")

start = '0'

fileObject.write('file \'intro_'+file_title+'.mpeg\' \n')
fileObject.write('file \'transition.mpeg\' \n')
for i in vids:
    transition_check = i.split('_')
    if (transition_check[0] != start):
        fileObject.write('file \'transition.mpeg\'')
        fileObject.write('\n')
        start = transition_check[0]
    if (os.path.isfile(i)):
        fileObject.write('file \'' + i +'\'')
        fileObject.write('\n')

fileObject.write('file \'endslate.mpeg\'')
fileObject.write('\n')
fileObject.close()

os.system('ffmpeg -y -f concat -i list.txt -codec copy '+file_title+'.mp4')
metadata = open("desc_elements.txt", "w")

metadata.write(title + '\n')
metadata.write(top_post_link)

metadata.close()

# os.system('ffmpeg -y -i '+file_title+'.mpeg -map 0 -vn -acodec copy audio.mp3')

# os.system('ffmpeg -y -i audio.mp3 -i background.mp3 -filter_complex amerge -ac 2 -c:a mp3 -shortest -ac 1 -vbr 4 Merged_Audio_track.mp3')

# os.system('ffmpeg -y -i '+file_title+'.mpeg -i Merged_Audio_Track.mp3 -c copy -map 0:0 -map 1:0 '+file_title+'.mp4')


for part_vid in vids:
    os.remove(part_vid)

end = time.time()

minutes = (end - begin)//60

seconds = ((end - begin)) - minutes*60

print('Total time elapsed ' + str(int(minutes))+':'+str(seconds))
