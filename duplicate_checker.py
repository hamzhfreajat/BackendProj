import os
import requests
import json
import logging

logger = logging.getLogger(__name__)

_DEEPSEEK_PROMPT = """You are an AI moderator for a classifieds platform.
Your job is to determine if a user is trying to post a duplicate ad.
Users sometimes try to bypass duplicate filters by slightly changing the title or description, but the underlying item/service being sold is exactly the same.

You will be given:
1. "New Ad": The ad the user is trying to post right now.
2. "Recent Ads": A list of ads the user has recently posted in the exact same category.

Task:
Compare the "New Ad" against the "Recent Ads".
Is the New Ad representing the exact same physical item, property, or service as any of the Recent Ads?
Look at the specifications, description, and title. If they are highly similar (e.g., same car model and year, same apartment location and price), it is a duplicate.

Output:
You MUST output ONLY a raw JSON object. Do not wrap it in markdown block quotes like ```json.
The JSON object must have exactly two fields:
- "is_duplicate": true or false
- "reason": A short explanation of why it is or isn't a duplicate.

Example Output:
{"is_duplicate": true, "reason": "The description and specifications match an apartment posted recently."}
"""

def check_duplicate_with_deepseek(new_ad_data: dict, recent_ads: list) -> bool:
    """
    Calls DeepSeek to verify if new_ad_data is a duplicate of any ad in recent_ads.
    Returns True if it is a duplicate, False otherwise.
    """
    if not recent_ads:
        return False
        
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.warning("DEEPSEEK_API_KEY is not set. Skipping AI duplicate check.")
        return False
        
    try:
        # Prepare the payload for AI
        simplified_recent = []
        for ad in recent_ads:
            simplified_recent.append({
                "id": ad.id,
                "title": ad.title,
                "description": ad.description,
                "price": float(ad.price) if ad.price else None,
                "location": ad.location,
                "attributes": ad.attributes
            })
            
        payload_content = {
            "New Ad": {
                "title": new_ad_data.get("title"),
                "description": new_ad_data.get("description"),
                "price": new_ad_data.get("price"),
                "location": new_ad_data.get("location"),
                "attributes": new_ad_data.get("attributes")
            },
            "Recent Ads": simplified_recent
        }

        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": _DEEPSEEK_PROMPT},
                {"role": "user", "content": json.dumps(payload_content, ensure_ascii=False)}
            ],
            "response_format": {"type": "json_object"}
        }
        
        logger.info("Calling DeepSeek for duplicate detection...")
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        res.raise_for_status()
        
        data = res.json()
        content = data["choices"][0]["message"]["content"]
        
        # Parse JSON
        result = json.loads(content)
        is_duplicate = result.get("is_duplicate", False)
        reason = result.get("reason", "")
        
        if is_duplicate:
            logger.info(f"AI flagged ad as DUPLICATE: {reason}")
        else:
            logger.info(f"AI passed ad. Not a duplicate: {reason}")
            
        return is_duplicate
        
    except Exception as e:
        logger.error(f"Error during DeepSeek duplicate check: {e}")
        # Fail open: if AI fails, allow the ad to avoid blocking real users
        return False
