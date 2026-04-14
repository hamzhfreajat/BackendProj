import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False)
        page = await b.new_page()
        print("Loading DDG...")
        await page.goto("https://duckduckgo.com/")
        await asyncio.sleep(1)
        
        print("Typing...")
        search_box = page.locator('input[name="q"]').first
        await search_box.click()
        await search_box.type("site:facebook.com شقق للايجار في عمان", delay=100)
        await search_box.press("Enter")
        
        print("Waiting for results...")
        try:
            await page.wait_for_selector('a[data-testid="result-title-a"]', timeout=10000)
            
            # Find the first Facebook link
            first_fb_link = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a[data-testid="result-title-a"]'));
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
            
        await asyncio.sleep(2)
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
