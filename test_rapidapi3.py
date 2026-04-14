import requests
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "e73801bc40msh3ac246033b53206p13b890jsnacb6352e887c"
HOST = "facebook-scraper3.p.rapidapi.com"

url = f"https://{HOST}/group/posts"
querystring = {"group_id": "476046146252156"}

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": HOST
}

print(f"Testing {HOST} /group/posts...")
response = requests.get(url, headers=headers, params=querystring)
try:
    data = response.json()
    posts = data.get('posts', [])
    for idx, post in enumerate(posts):
        print(f"\n--- Post {idx} ---")
        img = post.get('image')
        vid = post.get('video_thumbnail')
        album = post.get('album_preview')
        attached = post.get('attached_post')
        print(f"Image: {img}")
        print(f"Video: {vid}")
        print(f"Album: {album}")
        # print attached keys
        if attached:
            print("Attached post keys:", attached.keys())
        
        # print all keys that have 'img' or 'pic' or 'url' in them
        for k, v in post.items():
            if v and isinstance(v, str) and ('jpg' in v or 'png' in v):
                print(f"Found image URL in key '{k}': {v[:50]}...")
            if v and isinstance(v, list) and len(v) > 0 and isinstance(v[0], str) and ('jpg' in v[0] or 'png' in v[0]):
                print(f"Found image list in key '{k}'")
except Exception as e:
    print(e)
    print(response.text[:500])
