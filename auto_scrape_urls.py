import pyautogui
import time
import os

def scroll_for_posts(scroll_amount=-500, scrolls_needed=20, time_between_scrolls=1.5):
    """
    Scrolls down the page to load more posts.
    """
    print(f"Scrolling down to load more posts ({scrolls_needed} times)...")
    for i in range(scrolls_needed):
        pyautogui.scroll(scroll_amount)
        time.sleep(time_between_scrolls)

def scrape_group(group_url):
    print(f"\n--- Starting scrape for {group_url} ---")
    
    # 1. Navigate to the Group URL
    print("Focusing address bar and typing URL...")
    # This presses Ctrl+L to focus the browser's address bar
    pyautogui.hotkey('ctrl', 'l') 
    time.sleep(0.5)
    pyautogui.write(group_url)
    pyautogui.press('enter')
    
    # Wait for the group page to fully load
    time.sleep(8) 
    
    # 2. Scroll down to load ~50 posts
    scroll_for_posts()
    
    # 3. Click Extension Icon
    # IMPORTANT: Update these coordinates for your new device!
    print("Clicking Extension...")
    pyautogui.click(x=1255, y=66) 
    time.sleep(2) 
    
    # 4. Click Popup Open inside Extension
    print("Clicking Popup Open...")
    pyautogui.click(x=1042, y=264)
    time.sleep(2) 
    
    # 5. Click Scrap Button
    print("Clicking Scrap Button...")
    pyautogui.click(x=880, y=427)
    
    print("Waiting 15 seconds for scraping to finish...")
    time.sleep(15) 
    
    # 6. Click Save
    print("Clicking Save...")
    pyautogui.click(x=1141, y=666)
    
    print("Waiting 20 seconds for the save process to complete...")
    time.sleep(20) 

def main():
    if not os.path.exists("groups.txt"):
        print("Please create a 'groups.txt' file with one Facebook group URL per line.")
        with open("groups.txt", "w", encoding="utf-8") as f:
            f.write("https://www.facebook.com/groups/example1\n")
            f.write("https://www.facebook.com/groups/example2\n")
        return
        
    with open("groups.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]
        
    if not urls:
        print("groups.txt is empty. Please add some URLs.")
        return

    print(f"Loaded {len(urls)} groups from groups.txt")
    print("Starting auto_scrape in 5 seconds...")
    print("Please quickly switch to your Chrome browser and make sure it is fullscreen!")
    time.sleep(5)
    
    for url in urls:
        scrape_group(url)
        
    print("\nAll groups scraped successfully!")

if __name__ == "__main__":
    main()
