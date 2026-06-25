import asyncio
from facebook_publisher import publish_facebook_post

async def main():
    image_urls = [
        'https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev/8e79a9df4cc6473bbbd458d02d8c6d39.jpg',
        'https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev/128774ee68704532bf79722c3e30189b.jpg'
    ]
    res = await publish_facebook_post("Test carousel from CLI with images", "https://sooq-com.com", image_urls)
    print("Success:", res)

if __name__ == "__main__":
    asyncio.run(main())
