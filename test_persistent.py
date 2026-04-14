import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    
    async with async_playwright() as p:
        print("Launching persistent context...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome", # Use standard Chrome instead of generic Chromium
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1920,1080"
            ],
            viewport={"width": 1920, "height": 1080}
        )
        
        # 'create new tab' and do that
        page = await context.new_page()
        
        print("Loading DDG or Google...")
        await page.goto("https://www.google.com/")
        await asyncio.sleep(1)
        
        search_box = page.locator('textarea[name="q"], input[name="q"]').first
        if await search_box.count() > 0:
            await search_box.click()
            await search_box.type("شقق للايجار في عمان فيسبوك", delay=120)
            await search_box.press("Enter")
            
            print("Waiting for results...")
            try:
                await page.wait_for_selector('div#search', timeout=10000)
                first_fb_link = await page.evaluate('''() => {
                    const links = Array.from(document.querySelectorAll('a'));
                    for(let a of links) {
                        if(a.href && a.href.includes('facebook.com')) {
                            return a.href;
                        }
                    }
                    return null;
                }''')
                print(f"Facebook Link Found: {first_fb_link}")
            except Exception as e:
                print(f"Google Failed: {e}")
        else:
            print("No search box")
            
        await asyncio.sleep(3)
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
