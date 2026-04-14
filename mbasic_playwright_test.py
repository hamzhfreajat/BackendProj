import asyncio
import time
import random
from playwright.async_api import async_playwright

async def run_mbasic_scraper(url: str, limit: int = 50):
    # Requirement 1: MUST use the mbasic.facebook.com version of the group URL
    if "www.facebook.com" in url:
        url = url.replace("www.facebook.com", "mbasic.facebook.com")
    elif "facebook.com" in url and "mbasic.facebook.com" not in url:
        url = url.replace("facebook.com", "mbasic.facebook.com")
        
    posts = []
    seen_texts = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Requirement 2: MUST set a mobile User-Agent (e.g., Android/Chrome)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
            viewport={"width": 360, "height": 800},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            locale="ar-AE"
        )
        page = await context.new_page()
        
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Requirement 4: Implement a While loop that strictly stops when exactly 50 unique posts are collected.
        while len(posts) < limit:
            # Requirement 5: Add random time.sleep() between requests to prevent IP blocking.
            sleep_time = random.uniform(2.5, 4.5)
            print(f"Sleeping for {sleep_time:.2f} seconds...")
            await asyncio.sleep(sleep_time)
            
            # The script should scrape the text of the posts
            post_elements = await page.evaluate('''
                () => {
                    const allDivs = Array.from(document.querySelectorAll('div, p, span'));
                    const result = [];
                    for(let el of allDivs) {
                        let t = el.innerText ? el.innerText.trim() : "";
                        if(t.length > 30 && !t.includes("See more posts") && !t.includes("عرض المزيد") && !t.includes("Like")) {
                            result.push(t);
                        }
                    }
                    return result;
                }
            ''')
            
            for text in post_elements:
                if not text or len(text) < 20:
                    continue
                # Use a fingerprint to guarantee unique posts as requested
                fingerprint = "".join(text.split())[:100]
                if fingerprint not in seen_texts:
                    seen_texts.add(fingerprint)
                    posts.append(text)
                    print(f"Collected Post {len(posts)}: {text[:40]}...")
                    if len(posts) >= limit:
                        break
            
            if len(posts) >= limit:
                print(f"Strictly stopping at {limit} unique posts.")
                break
                
            # Requirement 3: look for the pagination link (usually an <a> tag with text like 'See more posts' or 'عرض المزيد') and navigate to it.
            print("Looking for pagination link...")
            try:
                # Find by text or common mbasic cursor attributes
                pagination_link = page.locator("a:has-text('See more posts'), a:has-text('عرض المزيد'), a:has-text('عرض المزيد من المنشورات'), a[href*='?cursor='], a[href*='&cursor=']").first
                
                if await pagination_link.count() > 0:
                    # mbasic sometimes obscures the clickable area, grab the href and goto to be perfectly safe
                    href = await pagination_link.get_attribute("href")
                    if href:
                        print("Navigating to next page...")
                        # If it's a relative path, resolve it
                        if href.startswith("/"):
                            href = "https://mbasic.facebook.com" + href
                        await page.goto(href, wait_until="domcontentloaded", timeout=60000)
                    else:
                        await pagination_link.click(wait_until="domcontentloaded", timeout=60000)
                else:
                    # Mbasic fallback: sometimes it uses `#m_more_item a`
                    more_item = page.locator("#m_more_item a").first
                    if await more_item.count() > 0:
                        href = await more_item.get_attribute("href")
                        print("Navigating to #m_more_item href...")
                        if href and href.startswith("/"):
                            href = "https://mbasic.facebook.com" + href
                        await page.goto(href, wait_until="domcontentloaded", timeout=60000)
                    else:
                        print("No pagination link found. Reached end or blocked by Facebook.")
                        break
            except Exception as e:
                print(f"Pagination error: {e}")
                break
                
        await browser.close()
        # Requirement 6: Return the scraped data as a list of strings
        return posts

if __name__ == "__main__":
    result = asyncio.run(run_mbasic_scraper("https://www.facebook.com/groups/637038403908513/", 50))
    print(f"\\n--- FINAL RESULT ---")
    print(f"Total Unique Posts Scraped: {len(result)}")
