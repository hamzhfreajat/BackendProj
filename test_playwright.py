import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://www.facebook.com/groups/637038403908513/?locale=ar_AR"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ar-AR"
        )
        page = await context.new_page()
        print("Navigating...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        eval_script = """
        () => {
            const style = document.createElement('style');
            style.innerHTML = 'div[role="dialog"], .x1ja2u2z, #login_popup_cta_container, ._5hn6 { display: none !important; } body { overflow-y: scroll !important; }';
            document.head.appendChild(style);
        }
        """
        await page.evaluate(eval_script)
        await asyncio.sleep(3)
        
        # Scroll logic to load more
        for i in range(5):
            await page.keyboard.press('PageDown')
            await page.keyboard.press('PageDown')
            await asyncio.sleep(1.5)
            
        # Try to click all "عرض المزيد" or "See more" buttons
        see_more_script = """
        () => {
            const buttons = Array.from(document.querySelectorAll('div[role="button"]'));
            let clicked = 0;
            for (let b of buttons) {
                if (b.innerText && (b.innerText.includes("عرض المزيد") || b.innerText.includes("See more"))) {
                    b.click();
                    clicked++;
                }
            }
            return clicked;
        }
        """
        clicked = await page.evaluate(see_more_script)
        print(f"Clicked 'See more' {clicked} times.")
        await asyncio.sleep(2)
        
        # Now try to identify actual posts!
        # A Facebook post in a group is typically inside a role="feed" or has specific structure.
        # Often, posts are inside elements with role="article"
        extract_script = """
        () => {
            const articles = Array.from(document.querySelectorAll('*[role="article"]'));
            const res = [];
            for(let article of articles) {
                // Find message body. Usually the largest text block, or under data-ad-preview
                // We'll just grab the innerText of the article, but filter out the comments part
                // comments usually come after a generic label like "Like Comment Share"
                let text = article.innerText || "";
                
                // Hacky way: Just grab the whole text of the article
                res.push(text);
            }
            // fallback if no role="article"
            if (res.length === 0) {
                 const nodes = Array.from(document.querySelectorAll('div[dir="auto"]'));
                 for(let n of nodes) {
                     let text = n.innerText ? n.innerText.trim() : '';
                     if(text.length > 50 && !text.includes('Like') && !text.includes('Comment') && !text.includes('Share')) {
                         res.push(text);
                     }
                 }
                 return res;
            }
            return res;
        }
        """
        texts = await page.evaluate(extract_script)
        
        print(f"Extracted {len(texts)} possible posts.")
        with open("debug_playwright_out.txt", "w", encoding="utf-8") as f:
            for idx, t in enumerate(texts):
                f.write(f"--- POST {idx} ---\n{t[:300]}...\n\n")
                
        await browser.close()

asyncio.run(main())
