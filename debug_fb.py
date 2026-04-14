import asyncio
from playwright.async_api import async_playwright

async def dump_html():
    url = "https://web.facebook.com/groups/476046146252156/?locale=ar_AR&_rdc=1&_rdr#"
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Navigating...")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        
        print("Scrolling...")
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
        content = await page.content()
        with open("fb_dump.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Dumped to fb_dump.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_html())
