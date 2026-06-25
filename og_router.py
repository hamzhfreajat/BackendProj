from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
import re
import io
import json
import requests
from PIL import Image

import models
from database import get_db

router = APIRouter(prefix="/api/v1/og", tags=["Open Graph"])

def download_image(url: str):
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        return img
    except Exception as e:
        print(f"Failed to download image {url}: {e}")
        return None

@router.get("/html")
async def get_og_html(request: Request, path: str = Query("")):
    """
    Returns an HTML stub containing Open Graph meta tags, pointing to the dynamic image generator.
    """
    # Determine the public host dynamically based on the request headers (or hardcode your domain)
    host = request.headers.get("host", "sooq-com.com")
    scheme = request.headers.get("x-forwarded-proto", "https")
    base_url = f"{scheme}://{host}"
    
    # URL to the dynamic image endpoint
    image_url = f"{base_url}/api/v1/og/image?path={path}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="utf-8">
        <title>Sookcom - سوقكم</title>
        <meta property="og:title" content="سوقكم - إعلانات مبوبة">
        <meta property="og:description" content="أفضل منصة إعلانات في الأردن">
        <meta property="og:image" content="{image_url}">
        <meta property="og:image:width" content="1200">
        <meta property="og:image:height" content="630">
        <meta property="og:url" content="{base_url}{path}">
        <meta property="og:type" content="website">
    </head>
    <body>
        <h1>Sookcom Open Graph Preview</h1>
        <p>This page is intended for social media crawlers.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/image")
async def get_og_image(path: str = Query(""), db: Session = Depends(get_db)):
    """
    Generates a 2x2 collage of ads matching the category in the path.
    """
    cat_id = None
    # Parse /category/123 from the path
    match = re.search(r'/category/(\d+)', path)
    if match:
        cat_id = int(match.group(1))

    # Build query
    query = db.query(models.Ad).filter(models.Ad.is_published == True)
    if cat_id:
        query = query.filter(models.Ad.category_id == cat_id)
        
    # Fetch top 4 ads
    ads = query.order_by(models.Ad.id.desc()).limit(4).all()

    # Extract image URLs
    img_urls = []
    for ad in ads:
        if ad.image_url:
            try:
                # Some image_urls are stored as JSON arrays, some as flat strings
                if ad.image_url.startswith('['):
                    urls = json.loads(ad.image_url)
                    if urls and len(urls) > 0:
                        img_urls.append(urls[0])
                else:
                    img_urls.append(ad.image_url)
            except:
                pass

    if not img_urls:
        # Return a simple blank image or default logo
        img = Image.new('RGB', (1200, 630), color = (240, 240, 240))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        return Response(content=img_byte_arr.getvalue(), media_type="image/jpeg")

    # Download images
    downloaded_images = []
    for u in img_urls[:4]:
        img = download_image(u)
        if img:
            downloaded_images.append(img)

    # Make a 1200x630 collage
    collage = Image.new('RGB', (1200, 630), color=(255, 255, 255))
    
    if len(downloaded_images) == 0:
        pass
    elif len(downloaded_images) == 1:
        # Just resize to fit
        img = downloaded_images[0]
        # crop to 1200x630
        img = img.resize((1200, int(img.height * (1200 / img.width))))
        collage.paste(img, (0, 0))
    elif len(downloaded_images) == 2:
        img1 = downloaded_images[0].resize((600, 630))
        img2 = downloaded_images[1].resize((600, 630))
        collage.paste(img1, (0, 0))
        collage.paste(img2, (600, 0))
    elif len(downloaded_images) == 3:
        img1 = downloaded_images[0].resize((600, 630))
        img2 = downloaded_images[1].resize((600, 315))
        img3 = downloaded_images[2].resize((600, 315))
        collage.paste(img1, (0, 0))
        collage.paste(img2, (600, 0))
        collage.paste(img3, (600, 315))
    else: # 4 images
        img1 = downloaded_images[0].resize((600, 315))
        img2 = downloaded_images[1].resize((600, 315))
        img3 = downloaded_images[2].resize((600, 315))
        img4 = downloaded_images[3].resize((600, 315))
        collage.paste(img1, (0, 0))
        collage.paste(img2, (600, 0))
        collage.paste(img3, (0, 315))
        collage.paste(img4, (600, 315))

    img_byte_arr = io.BytesIO()
    collage.save(img_byte_arr, format='JPEG', quality=85)
    return Response(content=img_byte_arr.getvalue(), media_type="image/jpeg")
