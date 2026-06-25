import aiohttp
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Hardcoded for now based on the user's setup
FACEBOOK_PAGE_ID = "100516965181114" # Sooqcom Page ID
FACEBOOK_ACCESS_TOKEN = "EAAiDF1hlti8BR1oJkqUyhE6ttOE2XY3uapArobbgQoxeu156oqbkjLPbp4C99pNczbkXe99KpY2DEkHEZAw6vypJelGurZC6jSnskNOLA6Kk58qeRRNyJeLD1NE32XG5tHZCecK2wcWZBYHXGFiY3Vq1mmgCvYnZCU9shBRC2K295HKbRAZAxhs9WVLFNnc2z7qOpOwBcZD"

async def upload_unpublished_photo(session: aiohttp.ClientSession, image_url: str) -> str:
    """Uploads a photo without publishing it to get its media ID for a carousel post."""
    url = f"https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/photos"
    payload = {
        "url": image_url,
        "published": "false",
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    async with session.post(url, data=payload) as response:
        if response.status == 200:
            result = await response.json()
            return result.get("id")
        return None

async def publish_facebook_post(message: str, link: str = None, image_urls: list = None) -> bool:
    """
    Publishes a post to the configured Facebook Page.
    Returns True if successful, False otherwise.
    """
    url = f"https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/feed"
    
    payload = {
        "message": message,
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # If we have images, upload them first
            if image_urls and len(image_urls) > 0:
                media_ids = []
                for img_url in image_urls[:10]: # Max 10 images for a post usually
                    if img_url:
                        media_id = await upload_unpublished_photo(session, img_url)
                        if media_id:
                            media_ids.append(media_id)
                
                if media_ids:
                    # Construct attached_media array
                    import json
                    attached_media = [{"media_fbid": str(mid)} for mid in media_ids]
                    payload["attached_media"] = json.dumps(attached_media)
            else:
                # Can only use link if no attached_media
                if link:
                    payload["link"] = link
                    
            async with session.post(url, data=payload) as response:
                result = await response.json()
                if response.status == 200:
                    logger.info(f"Successfully published to Facebook: {result}")
                    return True
                else:
                    logger.error(f"Failed to publish to Facebook. Status: {response.status}, Error: {result}")
                    return False
    except Exception as e:
        logger.error(f"Exception while publishing to Facebook: {e}")
        return False
