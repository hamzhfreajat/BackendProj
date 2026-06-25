import asyncio
import aiohttp
from facebook_publisher import upload_unpublished_photo

async def main():
    async with aiohttp.ClientSession() as session:
        res = await upload_unpublished_photo(session, 'https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev/8e79a9df4cc6473bbbd458d02d8c6d39.jpg')
        print('Media ID:', res)

if __name__ == "__main__":
    asyncio.run(main())
