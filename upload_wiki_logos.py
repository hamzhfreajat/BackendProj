import requests
import json
import boto3
from urllib.parse import quote
from database import SessionLocal
from models import Category

# Cloudflare R2 Config
R2_ACCESS_KEY_ID = "0e100733aeb20a80893ab9f24fcfb268"
R2_SECRET_ACCESS_KEY = "195b95b9e8fa268e7e03a38bcd1b19ef3f7e14ceeb90221f62e38821dd937090"
R2_BUCKET_NAME = "joapp-ads"
R2_ENDPOINT_URL = "https://eca032391478b97d195a13ea5a7adc1e.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev"

s3_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto"
)

brands = {
    'اس دبليو ام': 'SWM_motors',
    'جاي ام اي في': 'JMEV',
    'جايكو': 'Jaecoo',
    'دي اف اس كي': 'DFSK',
    'سيريس': 'Seres_(automobiles)',
    'زد إكس اوتو': 'ZX_Auto',
    'ساوايست  ': 'Soueast',
    'آيتو': 'AITO_Auto',
    'افاتار': 'Avatr_Technology',
    'آي إم': 'IM_Motors',
    'تانك': 'Tank_(marque)',
    'بايك': 'BAIC_Group',
    'نيتا': 'Hozon_Auto',
    'ربدان': 'Nio_Inc.',
    'روكس': 'Rox_Motor',
    'سكاي ويل': 'Skyworth_Auto',
    'فورثينج': 'Forthing',
    'لينك اند كو': 'Lynk_%26_Co'
}

def upload_to_r2(content, file_name):
    s3_client.put_object(Bucket=R2_BUCKET_NAME, Key=file_name, Body=content, ContentType="image/png")
    return f"{R2_PUBLIC_URL}/{file_name}"

db = SessionLocal()
categories = db.query(Category).filter(Category.parent_id.in_([101, 102]), Category.icon_name == None).all()

for cat in categories:
    if cat.name in brands:
        wiki_title = brands[cat.name]
        url = f'https://en.wikipedia.org/wiki/{wiki_title}'
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            if r.status_code == 200:
                text = r.text
                idx = text.find('class="infobox')
                if idx != -1:
                    img_idx = text.find('<img ', idx)
                    if img_idx != -1:
                        src_idx = text.find('src="', img_idx) + 5
                        src_end = text.find('"', src_idx)
                        src = text[src_idx:src_end]
                        if src.startswith('//'):
                            src = 'https:' + src
                        
                        # Fix size to 120px to get better resolution
                        src = src.replace('100px-', '120px-').replace('150px-', '120px-')
                        if '220px-' in src:
                            src = src.replace('220px-', '120px-')
                            
                        # print successfully without using arabic chars
                        print(f"Found image: {src}")
                        
                        img_r = requests.get(src, timeout=5)
                        if img_r.status_code == 200:
                            slug = wiki_title.replace('_', '').lower()
                            file_name = f"logos/{slug}_wiki.png"
                            public_url = upload_to_r2(img_r.content, file_name)
                            cat.icon_name = public_url
                            db.commit()
                            print(f"Success uploaded {slug}")
        except Exception as e:
            pass

db.close()
