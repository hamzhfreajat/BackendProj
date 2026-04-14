import json
import os
import asyncio
from database import SessionLocal
from fb_batch_router import _do_ingest, FbBatchRequest, FbPost

# Force DeepSeek only!
os.environ["GOOGLE_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROK_API_KEY"] = ""

with open("input.json", "r", encoding="utf-8") as f:
    data = json.load(f)

posts = []
for p in data:
    post = FbPost(**p)
    posts.append(post)

req = FbBatchRequest(posts=posts, category_id=3)
db = SessionLocal()

print(f"Ingesting {len(posts)} posts using DeepSeek...")
res = _do_ingest(req, db)
print(f"Saved: {res.saved}, Skipped: {res.skipped}, Errors: {res.errors}")
for r in res.results:
    print(f"[{r.index}] {r.status} - {getattr(r, 'reason', '')} / {getattr(r, 'title', '')}")
