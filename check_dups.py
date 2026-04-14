import codecs
import collections

ids = []
with codecs.open("seed_categories.py", "r", "utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith('('):
            try:
                cat_id = int(line.split(',')[0].replace('(','').strip())
                ids.append(cat_id)
            except Exception:
                pass

duplicates = [item for item, count in collections.Counter(ids).items() if count > 1]
print("Found duplicates:", duplicates)
