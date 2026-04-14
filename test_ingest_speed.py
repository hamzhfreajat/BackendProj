import sys
import json
import time

from database import get_db, SessionLocal
from fb_batch_router import _do_ingest, FbBatchRequest, FbPost

def main():
    print("Loading JSON...")
    try:
        # We can pass the hardcoded path or arguments
        json_path = r"test_payload_mod.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    # Create request object
    posts = [FbPost(**p) for p in data]
    req = FbBatchRequest(posts=posts, category_id=3, default_location="Amman")

    print(f"Loaded {len(req.posts)} posts.")
    db = SessionLocal()
    start_time = time.time()

    try:
        print("Starting ingestion...")
        res = _do_ingest(req, db)
        print(f"Finished in {time.time() - start_time:.2f} seconds.")
        print(f"Results: Saved: {res.saved}, Skipped: {res.skipped}, Errors: {res.errors}")
        for r in res.results:
            if r.status == "saved":
                print(f"Saved -> {r.title}")
    except Exception as e:
        print(f"Ingestion failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
