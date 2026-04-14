import pyautogui
import time

def scroll_for_posts(scroll_amount=-500, scrolls_needed=20, time_between_scrolls=1.5):
    """
    Scrolls down the page to load more posts.
    Adjust `scrolls_needed` or `scroll_amount` as necessary to reach ~50 posts.
    """
    print(f"Scrolling down to load more posts ({scrolls_needed} times)...")
    for i in range(scrolls_needed):
        pyautogui.scroll(scroll_amount)
        time.sleep(time_between_scrolls) # Wait for posts to load after each scroll

def scrape_group(group_name, group_x, group_y):
    print(f"\n--- Starting scrape for {group_name} ---")
    
    # 1. Click Group to open it
    print(f"Clicking {group_name} at ({group_x}, {group_y})...")
    pyautogui.click(x=group_x, y=group_y)
    time.sleep(5) # Wait for the group page to fully load
    
    # 2. Scroll down to load ~50 posts
    scroll_for_posts()
    
    # 3. Click Extension Popup
    print("Clicking Extension...")
    pyautogui.click(x=1255, y=66)
    time.sleep(2) # Wait for extension to respond
    
    # 4. Click Popup Open
    print("Clicking Popup Open...")
    pyautogui.click(x=1042, y=264)
    time.sleep(2) # Wait for popup
    
    # 5. Click Scrap Button
    print("Clicking Scrap Button...")
    pyautogui.click(x=880, y=427)
    
    # Wait for scraping process to finish (adjust if 50 posts takes longer)
    print("Waiting 15 seconds for scraping to finish...")
    time.sleep(15) 
    
    # 6. Click Save
    print("Clicking Save...")
    pyautogui.click(x=1141, y=666)
    print("Waiting 30 seconds for the save process to complete...")
    time.sleep(30) # Wait for file download dialogue/save to complete
    
    # 7. Click Back Button
    print("Clicking Back Button to return to groups...")
    pyautogui.click(x=21, y=66)
    time.sleep(4) # Wait for the previous page to reload

def main():
    print("Starting auto_scrape in 5 seconds...")
    print("Please quickly switch to your browser and make sure the groups page is visible!")
    time.sleep(5)
    
    # The list of groups to click based on your coordinates
    groups = [
        {"name": "Group 1", "x": 715, "y": 335},
        {"name": "Group 2", "x": 302, "y": 335},
        {"name": "Group 3", "x": 715, "y": 516},
        {"name": "Group 4", "x": 302, "y": 516},
    ]
    
    for group in groups:
        scrape_group(group["name"], group["x"], group["y"])
        
    print("\nScraping completed!")

if __name__ == "__main__":
    main()
