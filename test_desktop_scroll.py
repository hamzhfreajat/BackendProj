import asyncio
from playwright.async_api import async_playwright
import time

async def test_scrolling():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        url = 'https://www.facebook.com/groups/721423938231423/'
        print(f'Visiting URL on desktop context: {url}')
        await page.goto(url, wait_until='domcontentloaded')
        
        await asyncio.sleep(3)
        
        # Kill the login popup completely
        eval_script = """
        () => {
            const style = document.createElement('style');
            style.innerHTML = 'div[role="dialog"], .x1ja2u2z, #login_popup_cta_container, ._5hn6 { display: none !important; } body { overflow-y: scroll !important; }';
            document.head.appendChild(style);
        }
        """
        await page.evaluate(eval_script)
        
        print('Scrolling 15 times...')
        posts = set()
        
        extract_script = """
        () => {
            const nodes = Array.from(document.querySelectorAll('div[dir="auto"]'));
            const res = [];
            for(let n of nodes) {
                let text = n.innerText ? n.innerText.trim() : '';
                if(text.length > 50 && !text.includes('Like') && !text.includes('Comment')) {
                    res.push(text);
                }
            }
            return res;
        }
        """
        
        for i in range(15):
            await page.keyboard.press('PageDown')
            await asyncio.sleep(1.5)
            
            texts = await page.evaluate(extract_script)
            for t in texts:
                posts.add(''.join(t.split())[:100])
            
            print(f'Scroll {i}: {len(posts)} posts')
            
        print(f'DONE. Found {len(posts)} total unique posts')
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_scrolling())
