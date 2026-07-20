import aiohttp
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Read Facebook credentials from environment variables
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
FACEBOOK_ACCESS_TOKEN = os.environ.get("FACEBOOK_ACCESS_TOKEN")

if not FACEBOOK_PAGE_ID or not FACEBOOK_ACCESS_TOKEN:
    logger.warning("FACEBOOK_PAGE_ID or FACEBOOK_ACCESS_TOKEN not set. Facebook publishing will be unavailable.")
    FACEBOOK_PAGE_ID = FACEBOOK_PAGE_ID or ""
    FACEBOOK_ACCESS_TOKEN = FACEBOOK_ACCESS_TOKEN or ""
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

async def publish_facebook_post(message: str, link: str = None, image_urls: list = None, child_attachments: list = None) -> bool:
    """
    Publishes a post to the configured Facebook Page.
    Returns True if successful, False otherwise.
    """
    url = f"https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/feed"
    
    payload = {
        "message": message,
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    import json
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # If child_attachments is provided, it creates a true link carousel!
            if child_attachments and len(child_attachments) > 0:
                payload["link"] = link if link else "https://share.sooq-com.com"
                payload["child_attachments"] = json.dumps(child_attachments[:10])
            # Otherwise fallback to basic photo attachments if we have image_urls
            elif image_urls and len(image_urls) > 0:
                media_ids = []
                for img_url in image_urls[:10]: # Max 10 images for a post usually
                    if img_url:
                        media_id = await upload_unpublished_photo(session, img_url)
                        if media_id:
                            media_ids.append(media_id)
                
                if media_ids:
                    # Construct attached_media array
                    attached_media = [{"media_fbid": str(mid)} for mid in media_ids]
                    payload["attached_media"] = json.dumps(attached_media)
            else:
                # Can only use link if no attached_media and no child_attachments
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

