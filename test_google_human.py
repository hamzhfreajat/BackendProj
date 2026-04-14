import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False)
        page = await b.new_page()
        await page.goto("https://www.google.com/")
        print("Loaded Google")
        await asyncio.sleep(1)
        
        search_box = page.locator('textarea[name="q"], input[name="q"]').first
        await search_box.click()
        await search_box.type("شقق للايجار في عمان فيسبوك", delay=100)
        await search_box.press("Enter")
        
        print("Pressed enter, waiting for results...")
        try:
            await page.wait_for_selector('div#search', timeout=10000)
            print("Search results loaded.")
            
            # Find the first Facebook link
            first_fb_link = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                for(let a of links) {
                    if(a.href && a.href.includes('facebook.com')) {
                        return a.href;
                    }
                }
                return null;
            }''')
            print(f"Link found: {first_fb_link}")
        except Exception as e:
            print(f"Error: {e}")
            content = await page.content()
            with open("test_out.html", "w", encoding="utf-8") as f:
                f.write(content)
            
        await asyncio.sleep(2)
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
