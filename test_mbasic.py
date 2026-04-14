import asyncio
from playwright.async_api import async_playwright
import sys
sys.stdout.reconfigure(encoding='utf-8')

async def test_mbasic():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a mobile user agent
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
            viewport={'width': 375, 'height': 812}
        )
        page = await context.new_page()
        
        urls = [
            'https://mbasic.facebook.com/groups/177020175996812',
            'https://mbasic.facebook.com/groups/637038403908513',
            'https://mbasic.facebook.com/groups/721423938231423'
        ]
        
        for url in urls:
            print(f"\\n--- Testing {url} ---")
            await page.goto(url, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # Simple check to see if we hit a login page
            title = await page.title()
            print(f"Page Title: {title}")
            
            # Find all message container sections
            eval_script = """
            () => {
                const els = document.querySelectorAll('div[data-ft]');
                const posts = [];
                for(let el of els) {
                    let text = el.innerText || '';
                    if (text.length > 20 && !text.includes('Log In') && !text.includes('تسجيل الدخول')) {
                        posts.push(text.trim());
                    }
                }
                return posts;
            }
            """
            posts = await page.evaluate(eval_script)
            print(f"Found {len(posts)} posts from initial load:")
            for p in posts[:2]:
                print(f"  > {p[:50]}...")
            
            # Try to find 'See more posts' link
            try:
                # Look for a link containing 'Show more' or 'عرض المزيد' or just targeting /groups/
                more_link = await page.evaluate('''() => {
                    const links = document.querySelectorAll('a');
                    for (let a of links) {
                        if (a.href && a.href.includes('cursor=')) {
                            return a.href;
                        }
                    }
                    return null;
                }''')
                
                if more_link:
                    print(f"Found pagination link: {more_link[:80]}...")
                    await page.goto(more_link, wait_until='domcontentloaded')
                    await asyncio.sleep(2)
                    posts_2 = await page.evaluate(eval_script)
                    print(f"Found {len(posts_2)} MORE posts from page 2.")
                else:
                    print("No pagination link found.")
            except Exception as e:
                print("Error paginating:", e)
                
        await browser.close()

asyncio.run(test_mbasic())
