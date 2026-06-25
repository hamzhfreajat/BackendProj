import aiohttp
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Hardcoded for now based on the user's setup
FACEBOOK_PAGE_ID = "100516965181114" # Sooqcom Page ID
FACEBOOK_ACCESS_TOKEN = "EAAiDF1hlti8BR1oJkqUyhE6ttOE2XY3uapArobbgQoxeu156oqbkjLPbp4C99pNczbkXe99KpY2DEkHEZAw6vypJelGurZC6jSnskNOLA6Kk58qeRRNyJeLD1NE32XG5tHZCecK2wcWZBYHXGFiY3Vq1mmgCvYnZCU9shBRC2K295HKbRAZAxhs9WVLFNnc2z7qOpOwBcZD"

async def publish_facebook_post(message: str, link: str = None) -> bool:
    """
    Publishes a post to the configured Facebook Page.
    Returns True if successful, False otherwise.
    """
    url = f"https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/feed"
    
    payload = {
        "message": message,
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    
    if link:
        payload["link"] = link
        
    try:
        async with aiohttp.ClientSession() as session:
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
