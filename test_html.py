import requests
from bs4 import BeautifulSoup

url = "https://jo.opensooq.com/ar/سيارات-ومركبات/سيارات-للبيع"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(response.text, 'html.parser')

print(f"Total HTML length: {len(response.text)}")
# Try to find common link patterns that point to ads
links = soup.find_all('a')
ad_links = [l for l in links if l.get('href') and '/ar/search/' in l.get('href')]
if ad_links:
    sample_container = ad_links[0].parent.parent
    print(f"Sample Container classes: {sample_container.get('class')}")
    print(f"Tag: {sample_container.name}")
else:
    print("No ad links found.")
    
# Let's just find the first 5 images and see their parents
imgs = soup.find_all('img')
print(f"Found {len(imgs)} imgs")
for img in imgs[:5]:
    print(img.get('src') or img.get('data-src'), getattr(img.parent, 'name', ''))
