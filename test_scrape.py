import requests
from bs4 import BeautifulSoup

url = "https://jo.opensooq.com/ar/سيارات-ومركبات/سيارات-للبيع"
headers = {"User-Agent": "Mozilla/5.0"}
try:
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    containers = soup.find_all(lambda tag: tag.name in ['div', 'li'] and any(c in tag.get('class', []) for c in ['post', 'listing', 'sc-12kyuvi-0', 'mb-32']))
    
    if not containers:
        containers = soup.find_all('li', class_=lambda c: c and 'post' in c.lower())
        
    print(f"Found {len(containers)} containers")
    for i, container in enumerate(containers[:5]):
        title_tag = container.find(['h2', 'h3'])
        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        imgs = container.find_all('img')
        img_srcs = [img.get('src') or img.get('data-src') for img in imgs]
        print(f"{i+1}. Title: {title} | Images: {len(img_srcs)} -> {img_srcs[0] if img_srcs else 'None'}")
except Exception as e:
    print(e)
