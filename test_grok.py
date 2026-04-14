import json
import os
import requests
import asyncio
from fb_batch_router import _ai_process_chunk, FbPost, _build_categories_block
from database import SessionLocal

# Force Grok only
os.environ["GOOGLE_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["DEEPSEEK_API_KEY"] = ""

db = SessionLocal()
categories_block = _build_categories_block(db)

posts = [
    FbPost(
        index=1,
        author="Ahmed",
        text="شقه مفروشه للايجار قرب مجمع جبر والماكدونلد شارع عبدالله غوشه 3نوم ماستر حمامين وصاله ومطبخ وتراس قريبه من الخدمات 0781675116",
        postUrl="http://fb.com/1"
    ),
    FbPost(
        index=2,
        author="Sami",
        text="مطلوب شريك سكن شبه مفروش استوديو مجمع سكني المقابلين شركة إسكان الأجرة ٥٠ دينار٠٧٩٠٦٦٦٣٢٣",
        postUrl="http://fb.com/2"
    ),
    FbPost(
        index=3,
        author="Ali",
        text="متوفر غرفه شيرنغ او برايفت بخلدا إم السماق مي وكهرباء ونت وحارس ومي لشرب وغاز مبطخ لشخصين 250 شخص200 0796305555 اتصال",
        postUrl="http://fb.com/3"
    ),
]

print("Sending 3 posts directly to Grok-3-mini...")
result = _ai_process_chunk(posts, categories_block)
print("\n--- GROK JSON RESULT ---")
print(json.dumps(result, ensure_ascii=False, indent=2))
