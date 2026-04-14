import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False)
        page = await b.new_page()
        await page.goto('https://www.google.com/search?q=شقق+للايجار+في+عمان+فيسبوك', wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(2)
        content = await page.content()
        with open("out.html", "w", encoding="utf-8") as f:
            f.write(content)
        
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll("a")).map(a => a.href).filter(h => h.includes("facebook"));
        }''')
        print(f"Links found: {links}")
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
