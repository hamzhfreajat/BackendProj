import asyncio
import aiohttp
import json
from facebook_publisher import upload_unpublished_photo, FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID

async def test():
    async with aiohttp.ClientSession() as s:
        res1 = await upload_unpublished_photo(s, 'https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev/8e79a9df4cc6473bbbd458d02d8c6d39.jpg')
        print('Media 1:', res1)
        payload = {
            'message': 'Test post with attached_media', 
            'access_token': FACEBOOK_ACCESS_TOKEN, 
            'attached_media': json.dumps([{"media_fbid": str(res1)}])
        }
        resp = await s.post(f'https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/feed', data=payload)
        print('Post Response:', await resp.json())

if __name__ == "__main__":
    asyncio.run(test())
