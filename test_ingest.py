import sys, json
sys.path.append('d:/open/classifieds-app/backend')
from database import SessionLocal
from fb_batch_router import _do_ingest, FbBatchRequest, FbPost
db = SessionLocal()
with open(r'c:\Users\hfraijat\Downloads\fb_posts_2026-04-19T17-42-03-286Z.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
req = FbBatchRequest(posts=[FbPost(**p) for p in data])
response = _do_ingest(req, db)
for r in response.results:
    print(f'Post {r.index}: {r.status} - {r.reason}')
