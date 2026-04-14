import requests
import json
import sys

# Ensure stdout uses utf-8
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "e73801bc40msh3ac246033b53206p13b890jsnacb6352e887c"
HOST = "facebook-scraper3.p.rapidapi.com"

def extract_all_images(data):
    """Recursively search for image URLs in the post data."""
    found_images = []
    
    ignore_patterns = [
        'dst-jpg_s', 'dst-jpg_p', '100x100', '80x80', '72x72', '50x50', '32x32', 
        '/cp0/', 'emoji', 'icon'
    ]
    
    def is_valid_ad_image(url):
        if not url or not isinstance(url, str):
            return False
        if not url.startswith('http'):
            return False
        
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in ignore_patterns):
            return False
            
        return True

    def search_dict(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, str) and ('.jpg' in v or '.png' in v or '.webp' in v):
                    clean_v = v.split(' ')[0]
                    if is_valid_ad_image(clean_v) and clean_v not in found_images:
                        found_images.append(clean_v)
                elif isinstance(v, (dict, list)):
                    search_dict(v)
        elif isinstance(d, list):
            for item in d:
                search_dict(item)
                
    # Direct explicit checks first to maintain order
    if isinstance(data, dict):
        if data.get('image') and data.get('image') not in found_images:
            found_images.append(data.get('image'))
        if data.get('video_thumbnail') and data.get('video_thumbnail') not in found_images:
            found_images.append(data.get('video_thumbnail'))
            
        if isinstance(data.get('album_preview'), list):
            for album_item in data['album_preview']:
                if isinstance(album_item, dict):
                    img_uri = album_item.get('image_file_uri') or album_item.get('url')
                    if is_valid_ad_image(img_uri) and img_uri not in found_images:
                        found_images.append(img_uri)
            
    # Then search everything else
    search_dict(data)
    
    # Filter out empty or None
    found_images = [img for img in found_images if img]
    
    # Return max 6 unique images
    return found_images[:6]

def run_test(limit=15):
    group_id = "1419536172244590"
    api_url = f"https://{HOST}/group/posts"
    
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": HOST
    }
    
    processed_count = 0
    cursor = None
    
    # Keep track of skipped
    skipped_no_text = 0
    
    print(f"Starting to fetch up to {limit} posts...")
    
    while processed_count < limit:
        params = {"group_id": group_id}
        if cursor:
            params["cursor"] = cursor
            
        print(f"Fetching page with cursor: {cursor}")
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break
            
        data = response.json()
        posts = data.get('posts', [])
        
        if not posts:
            print("No posts returned in this page.")
            break
            
        print(f"Received {len(posts)} posts in this page.")
        
        for post in posts:
            if processed_count >= limit:
                break
                
            raw_desc = post.get('message', '') or post.get('message_rich', '')
            image_urls = extract_all_images(post)
            
            # The OLD condition in scraper.py was:
            # if not raw_desc or len(raw_desc) < 10: continue
            
            # NEW PROPOSED CONDITION:
            if (not raw_desc or len(raw_desc) < 10) and not image_urls:
                skipped_no_text += 1
                continue
                
            # Simulate processing
            processed_count += 1
            print(f"--- Processed Post {processed_count} ---")
            print(f"Images Extracted: {len(image_urls)}")
            for img in image_urls:
                print(f"  - {img[:80]}...")
            if len(image_urls) == 0:
                print("--- Processed Post 0 IMAGES RAW ---")
                print(json.dumps(post, ensure_ascii=False, indent=2))
                break
        if not cursor:
            print("No more cursor returned.")
            break
            
    print(f"Finished processing {processed_count} posts. Skipped {skipped_no_text} posts due to being empty.")

if __name__ == "__main__":
    run_test(15)
