import re
with open('desktop_dump.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Try to find common Facebook class names or just any text
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

print('Finding all text nodes...')
all_texts = list(soup.stripped_strings)

text_chunks = [t for t in all_texts if len(t) > 30]
print(f"Found {len(text_chunks)} text segments longer than 30 chars.")
for t in text_chunks[:10]:
    print("MATCH:", t[:100])
