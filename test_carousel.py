import asyncio
import aiohttp
import json
from facebook_publisher import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID

async def test_carousel():
    url = f"https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/feed"
    
    child_attachments = [
        {
            "link": "https://sooq-com.com/ad/13900",
            "name": "شقة أرضية فاخرة",
            "description": "السعر: 100,000",
            "picture": "https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev/8e79a9df4cc6473bbbd458d02d8c6d39.jpg"
        },
        {
            "link": "https://sooq-com.com/ad/13848",
            "name": "شقة ديلوكس للإيجار",
            "description": "السعر: 500",
            "picture": "https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev/128774ee68704532bf79722c3e30189b.jpg"
        }
    ]
    
    payload = {
        "message": "Testing organic carousel post from API!",
        "link": "https://sooq-com.com",
        "child_attachments": json.dumps(child_attachments),
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    
    async with aiohttp.ClientSession() as s:
        resp = await s.post(url, data=payload)
        print("Status:", resp.status)
        print("Response:", await resp.json())

if __name__ == "__main__":
    asyncio.run(test_carousel())
