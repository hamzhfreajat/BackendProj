"""
fb_batch_router.py - Facebook Posts Batch Ingestion Endpoint
============================================================
Add this router to main.py:

    from fb_batch_router import router as fb_batch_router
    app.include_router(fb_batch_router)
"""

import os
import json
import logging
import pathlib
import io
import uuid
import requests
import re
import concurrent.futures
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from extraction_constants import REAL_ESTATE_CATEGORIES
from mapper import get_location_map, get_category_map, map_location, map_category

from dotenv import load_dotenv
_this_dir = pathlib.Path(__file__).resolve().parent
load_dotenv(_this_dir / ".env", override=True)

# Fallback: hardcode the key if env var is still missing
_FALLBACK_KEY = "AIzaSyDtwk07CKyqD6dnxcwBhRgf_2GbP8HHmBo"
if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = _FALLBACK_KEY

# Project imports
from database import get_db
import models
from models import SourceType
import schemas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["fb-batch"])

print(f"[fb_batch_router] LOADED — will use source_type = {SourceType.SCRAPER_BOT}")


# -- Pydantic models --------------------------------------------------------

class FbPost(BaseModel):
    index: Optional[int] = None
    author: Optional[str] = None
    timestamp: Optional[str] = None
    postUrl: Optional[str] = None
    text: Optional[str] = None
    images: Optional[List[str]] = []
    reactions: Optional[str] = None
    scrapedAt: Optional[str] = None

class FbBatchRequest(BaseModel):
    posts: List[FbPost]
    category_id: Optional[int] = None
    default_location: Optional[str] = ""

class PostResult(BaseModel):
    index: int
    status: str          # "saved" | "skipped" | "error"
    ad_id: Optional[int] = None
    title: Optional[str] = None
    reason: Optional[str] = None

class FbBatchResponse(BaseModel):
    total: int
    saved: int
    skipped: int
    errors: int
    results: List[PostResult]


# -- Gemini: ONE call for ALL posts ------------------------------------------

_GEMINI_BATCH_PROMPT = """You are an expert data extractor. Extract classified-ad data from the given Facebook posts and respond ONLY with a JSON array.

For EACH post, extract:
- index: (int) the given post number
- title: (string) generate a concise, professional arabic title
- price: (float) numeric price (0.0 if missing)
- location: (string) e.g. 'عمان, عبدون'. IMPORTANT RULE: Numbered zones (المنطقة الثالثة, الخامسة, etc.) belong to العقبة (Aqaba), NOT Amman! Output format: 'العقبة, المنطقة الثالثة'. Empty if missing.
- phone_number: (string or null)
- category_id: (int) Map to the deepest specific sub-category ID from the list below. (Rule: Use 0 if the author is SEEKING/ASKING for an apartment, or if the post is NOT offering real estate).
- rejection_reason: (string) If category_id is 0, provide the exact reason why here. (e.g. 'Seeking apartment', 'Selling furniture')
- suggested_tags: (list[string]) 2-4 important keywords mentioned.
- attributes: (object) Extract basic properties into this object. Also CRITICALLY, create a nested "dynamic_data" object containing these EXACT keys if mentioned:
  {
      "dynamic_data": { 
          "area": (int), "bedrooms": (string), "bathrooms": (string), "furnishing": (string), "rent_duration": (string), "floor": (string), "age": (string), "main_features": (list[string]), "extra_features": (list[string]), "nearby": (list[string]), "facade": (string), "target_tenants": (list[string]), "property_restrictions": (list[string]), "building_fees_status": (list[string]), "water_supply": (list[string]), "cooling_features": (list[string]), "heating_features": (list[string]), "security_deposit_type": (string)
      }
  }

NOTE: Short-term, daily, and weekly furnished rentals perfectly valid! DO NOT reject them.

CATEGORIES:
{categories_block}

POSTS:
{posts_block}
"""

_GEMMA_SINGLE_PROMPT = """You are an expert real estate data extractor. Perform JSON extraction from the provided Facebook post. 

EXTREMELY IMPORTANT RULE FOR ARABIC: 
If the post contains the word "مطلوب" (Wanted/Seeking) or the author is ASKING to buy or rent an apartment, it is NOT a real estate offering! You MUST set category_id to 0 and provide a rejection_reason.

EXAMPLES OF CORRECT BEHAVIOR:
Example 1 (WANTED POST):
Post: "مطلوب شقة للايجار في الجبيهة بسعر رخيص"
Output: {{"title": "", "price": 0.0, "location": "", "phone_number": null, "category_name": "", "rejection_reason": "Author is seeking an apartment, not offering one", "suggested_tags": [], "attributes": {{}}}}

Example 2 (OFFERING POST - APARTMENT FOR SALE):
Post: "شقة للبيع في طبربور 3 غرف نوم بسعر 40 الف دينار 0791234567"
Output: {{"title": "شقة للبيع في طبربور 3 غرف نوم", "price": 40000.0, "location": "عمان, طبربور", "phone_number": "0791234567", "category_name": "شقق للبيع", "rejection_reason": "", "suggested_tags": ["للبيع", "طبربور", "3 غرف"], "attributes": {{"rooms": 3}}}}

Example 3 (OFFERING POST - APARTMENT FOR RENT):
Post: "شقة فارغة للايجار في دير غبارمكونه من ٣ نوم صالةمطبخ٢ حمام0795634384"
Output: {{"title": "شقة فارغة للإيجار في دير غبار", "price": 0.0, "location": "عمان, دير غبار", "phone_number": "0795634384", "category_name": "شقق للإيجار", "rejection_reason": "", "suggested_tags": ["شقة فارغة", "دير غبار", "إيجار"], "attributes": {{"rooms": 3, "bathrooms": 2, "furnished": "فارغة"}}}}

Now, process the following post. Respond ONLY with a JSON object.

Extract:
- title: (string) generate a concise, professional arabic title (Empty if category_id is 0)
- price: (float) numeric price (0.0 if missing)
- location: (string) Extract the exact city and region found in the post. Format as "City, Region" (e.g. "عمان, عبدون") if known, otherwise just output the region name.
- phone_number: (string or null) Look closely for 10-digit numbers.
- category_name: (string) Extract the exact real estate category (e.g. 'شقق للبيع', 'أراضي للإيجار', 'ستوديوهات'). Use empty string if author is SEEKING or if not offering real estate.
- rejection_reason: (string) If not offering real estate, provide exact reason why here.
- suggested_tags: (list[string]) 2-4 important keywords mentioned.
- attributes: (object) Extract basic properties into this object. Also CRITICALLY, create a nested "dynamic_data" object containing these EXACT keys if mentioned:
  - "dynamic_data": {{ 
      "area": (int), "bedrooms": (string), "bathrooms": (string), "furnishing": (string), "rent_duration": (string), "floor": (string), "age": (string), "main_features": (list[string]), "extra_features": (list[string]), "nearby": (list[string]), "facade": (string), "target_tenants": (list[string]), "property_restrictions": (list[string]), "building_fees_status": (list[string]), "water_supply": (list[string]), "cooling_features": (list[string]), "heating_features": (list[string]), "security_deposit_type": (string)
  }}

POST:
{post_text}

---
CRITICAL INSTRUCTION: Output ONLY valid JSON matching the exact schema requested. Do NOT output conversational text, explanations, or markdown like ```json. Start your response with {{ and end with }}.
"""


def _build_posts_block(posts: List[FbPost]) -> str:
    lines = []
    for i, p in enumerate(posts):
        idx = p.index or (i + 1)
        lines.append(f"--- Post #{idx} ---")
        lines.append(f"Text: {(p.text or '')[:800]}")
        lines.append(f"Images: {len(p.images) if p.images else 0}")
        lines.append("")
    return "\n".join(lines)

import threading
import time
import json
import os
from datetime import datetime

_GEMINI_LOCK = threading.Lock()
_LAST_GEMINI_CALL = 0.0

def _check_and_update_gemini_daily_limit() -> bool:
    """Returns True if under limits, False if 999 daily limit reached."""
    usage_file = "gemini_usage.json"
    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        if os.path.exists(usage_file):
            with open(usage_file, "r") as f:
                usage = json.load(f)
        else:
            usage = {"date": today_str, "count": 0}
            
        if usage.get("date") != today_str:
            usage = {"date": today_str, "count": 0}
            
        if usage["count"] >= 999:
            return False
            
        usage["count"] += 1
        with open(usage_file, "w") as f:
            json.dump(usage, f)
        return True
    except Exception:
        return True # Fail open safely if disk write fails


def _ai_process_chunk(chunk_posts: List[FbPost]) -> List[dict]:
    """Send a chunk of posts to an AI model with fallback logic."""
    api_key_gemini = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    api_key_deepseek = os.getenv("DEEPSEEK_API_KEY")
    api_key_grok = os.getenv("GROK_API_KEY")

    if not (api_key_gemini or api_key_deepseek or api_key_grok):
        raise RuntimeError("No API key set for any AI provider.")

    prompt = _GEMINI_BATCH_PROMPT.format(
        categories_block=categories_block,
        posts_block=_build_posts_block(chunk_posts)
    )

    errors = []

    def _parse_json_result(raw: str) -> List[dict]:
        logger.info("Parsing JSON...")
        try:
            # Strip markdown fences if present
            raw = raw.strip()
            # Regex to find the first JSON array or object
            match = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
            if match:
                raw = match.group(1)
            
            # Clean up unescaped control characters (like raw tabs or newlines) which breaks standard json.loads
            raw = re.sub(r'[\x00-\x19]', ' ', raw)
            
            parsed = json.loads(raw)
            
            # Unpack if json_object wrapper is used (common for Deepseek/Grok JSON mode)
            if isinstance(parsed, dict) and len(parsed) == 1 and "posts" in parsed:
                parsed = parsed["posts"]
            elif isinstance(parsed, dict):
                parsed = [parsed]
                
            logger.info("JSON successfully parsed.")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parsing failed: {e}. Raw received: {raw[:200]}...")
            return []

    # 1. Try Local Gemma if enabled
    use_local_gemma = os.getenv("USE_LOCAL_GEMMA", "false").lower() == "true"
    if use_local_gemma:
        from openai import OpenAI
        
        gemma_base_url = os.getenv("GEMMA_BASE_URL", "http://localhost:11434/v1")
        gemma_api_key = os.getenv("GEMMA_API_KEY", "ollama") # Default for ollama
        gemma_model_name = os.getenv("GEMMA_MODEL_NAME", "gemma-classifieds")
        
        client = OpenAI(base_url=gemma_base_url, api_key=gemma_api_key)
        
        all_parsed = []
        for post in chunk_posts:
            single_prompt = _GEMMA_SINGLE_PROMPT.format(
                post_text=post.text
            )
            
            post_parsed = {"ai_chunk_error": "Gemma failed"}
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    logger.info(f"Trying Local Gemma (Attempt {attempt+1}/{max_retries})...")
                    response = client.chat.completions.create(
                        model=gemma_model_name,
                        messages=[{"role": "user", "content": single_prompt}],
                        response_format={"type": "json_object"},
                        temperature=0.1
                    )
                    
                    raw = response.choices[0].message.content
                    parsed_list = _parse_json_result(raw.strip())
                    if parsed_list and len(parsed_list) > 0:
                        post_parsed = parsed_list[0]
                        post_parsed["ai_model"] = gemma_model_name
                        post_parsed["raw_unparsed_chunk_layer"] = raw.strip()
                        break # success, exit retry loop
                        
                except Exception as e:
                    logger.warning(f"Local Gemma failed for post (Attempt {attempt+1}/{max_retries}): {e}")
                    post_parsed["ai_chunk_error"] = str(e)
                    time.sleep(1)
                    
            all_parsed.append(post_parsed)
            
        return all_parsed

    # 2. Try Gemini Exclusively (Infinite Retry with increasing backoff)
    if not api_key_gemini:
        raise RuntimeError("No Gemini API key provided. Fallbacks are disabled by user request.")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            global _LAST_GEMINI_CALL
            sleep_time = 0.0
            with _GEMINI_LOCK:
                if not _check_and_update_gemini_daily_limit():
                    logger.warning("Gemini Daily Limit (999) Reached! Failing.")
                    raise RuntimeError("Gemini Daily Limit Reached")

                # Ensure 5.0 sec gap between requests (max 12 RPM)
                now = time.time()
                elapsed = now - _LAST_GEMINI_CALL
                if elapsed < 5.0:
                    sleep_time = 5.0 - elapsed
                    _LAST_GEMINI_CALL = now + sleep_time
                else:
                    _LAST_GEMINI_CALL = now

            if sleep_time > 0:
                logger.info(f"Rate limiting Gemini: Sleeping {sleep_time:.2f}s outside lock to respect RPM limit")
                time.sleep(sleep_time)

            logger.info(f"Trying Gemini AI (Attempt {attempt+1}/{max_retries})...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent?key={api_key_gemini}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 8192
                }
            }
            
            res = requests.post(url, json=payload, headers=headers, timeout=60)
            res.raise_for_status()

            data = res.json()
            raw = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = _parse_json_result(raw.strip())
            for item in parsed:
                if isinstance(item, dict): 
                    item["ai_model"] = "gemini-1.5-flash-8b"
                    item["raw_unparsed_chunk_layer"] = raw.strip()
            return parsed

        except Exception as e:
            # If the exception is Daily Limit, break out immediately
            if "Gemini Daily Limit Reached" in str(e):
                errors.append(str(e))
                break

            wait_sec = (attempt + 1) * 5
            logger.warning(f"Gemini failed (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait_sec}s...")
            time.sleep(wait_sec)
            
    errors.append("Gemini failed after maximum retries.")

    logger.error("AI processing failed entirely.")
    raise RuntimeError(f"AI processing failed: {errors}")


def _ai_process_all(posts: List[FbPost], db: Session) -> List[dict]:
    """Process all posts in chunks to avoid token limits, running concurrently."""
    categories_block = _build_categories_block(db)
    
    # Send ALL non-duplicate posts to AI safely in chunks
    # Keep chunk size explicitly huge (50) to divide the heavy System Prompt token cost to absolute zero per post.
    CHUNK_SIZE = 50
    chunks = [posts[i:i + CHUNK_SIZE] for i in range(0, len(posts), CHUNK_SIZE)]
    
    def process_single_chunk(chunk):
        try:
            logger.info(f"Sending chunk of {len(chunk)} posts to AI...")
            res = _ai_process_chunk(chunk)
            if len(res) < len(chunk):
                # If AI returned fewer results, pad with an explicit error to avoid silent blanks
                res.extend([{"ai_chunk_error": "AI returned fewer items than requested (possible truncation)"}] * (len(chunk) - len(res)))
            return res[:len(chunk)]
        except Exception as e:
            logger.error(f"AI chunk failed: {e}. Falling back to default data for chunk.")
            return [{"ai_chunk_error": str(e)}] * len(chunk)

    all_results = []
    # Run all AI chunk processing concurrently (max 3 workers to prevent overwhelming free tier lock)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results_from_threads = executor.map(process_single_chunk, chunks)
        for chunk_res in results_from_threads:
            all_results.extend(chunk_res)

    return all_results


# -- DB helpers --------------------------------------------------------------

def _upload_imgs_to_r2(image_urls: List[str]) -> List[str]:
    if not image_urls:
        return []
    
    from media_router import get_r2_client
    r2_client = get_r2_client()
    if not r2_client:
        return image_urls
    
    bucket_name = os.getenv("R2_BUCKET_NAME", "joapp-ads")
    public_url = os.getenv("R2_PUBLIC_URL", "https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev")
    public_url_base = public_url.rstrip('/')
    
    def process_url(url):
        if not url: return None
        if "r2.dev" in url or "cloudflare" in url:
            return url
            
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', 'image/jpeg')
                file_ext = ".png" if "png" in content_type else ".jpg"
                unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                file_obj = io.BytesIO(resp.content)
                
                r2_client.upload_fileobj(
                    file_obj, 
                    bucket_name, 
                    unique_filename,
                    ExtraArgs={'ContentType': content_type}
                )
                return f"{public_url_base}/{unique_filename}"
            else:
                return url
        except Exception as e:
            logger.error(f"Failed to upload FB image to R2 {url}: {e}")
            return url

    # Use ThreadPoolExecutor to upload all images concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_url, image_urls))
        
    return [r for r in results if r is not None]

def _get_or_create_ai_user(db: Session) -> models.User:
    ai_user = db.query(models.User).filter(models.User.username == "ai_scraper").first()
    if not ai_user:
        ai_user = models.User(
            username="ai_scraper",
            email="ai_scraper@system.local",
        )
        if hasattr(models.User, "hashed_password"):
            ai_user.hashed_password = "SYSTEM_NO_LOGIN"
        db.add(ai_user)
        db.commit()
        db.refresh(ai_user)
    return ai_user


def _is_duplicate(db: Session, source_url: str, raw_description: str) -> Optional[int]:
    if source_url:
        import re
        # 1. Check exact match
        ad = db.query(models.Ad).filter(models.Ad.source_url == source_url).first()
        if ad: return ad.id
            
        # 2. Extract FB Post ID and use LIKE matcher (handles tracking parameter changes)
        match = re.search(r'/posts/(\d+)', source_url)
        if match:
            post_id = match.group(1)
            ad = db.query(models.Ad).filter(models.Ad.source_url.like(f"%/posts/{post_id}%")).first()
            if ad: return ad.id
                
        match2 = re.search(r'story_fbid=(\d+)', source_url)
        if match2:
            post_id = match2.group(1)
            ad = db.query(models.Ad).filter(models.Ad.source_url.like(f"%story_fbid={post_id}%")).first()
            if ad: return ad.id

    return None
            
    return None
def _save_ad_to_db(db, post, ai_data, ai_user_id, fb_request_category_id, default_location):
    # Dynamically extract Category from AI category_name strings
    categories_map = get_category_map()
    ai_cat_name = ai_data.get("category_name", "")
    mapped_cat_id = 0
    if ai_cat_name:
        mapped_cat_id = map_category(ai_cat_name, categories_map)
        
    final_category_id = mapped_cat_id or ai_data.get("category_id") or fb_request_category_id or 3
    if ai_data.get("rejection_reason"):
        final_category_id = 0 # Enforce rejected 
    
    # Map explicit Region Locs
    location_map = get_location_map()
    ai_loc_str = ai_data.get("location", "")
    mapped_location = map_location(ai_loc_str, location_map) or default_location or ""

    # Generate smarter fallback title if AI extraction failed
    ad_title = ai_data.get("title")
    if not ad_title:
        if post.text:
            words = post.text.strip().split()
            ad_title = " ".join(words[:8]) + ("..." if len(words) > 8 else "")
        else:
            ad_title = f"إعلان من {post.author or 'مستخدم'}"

    # Handle AI nested attribute extraction safely
    ai_attrs = ai_data.get("attributes", {})
    if isinstance(ai_attrs, str):
        try:
            ai_attrs = json.loads(ai_attrs)
        except:
            ai_attrs = {}
    elif not isinstance(ai_attrs, dict):
        ai_attrs = {}

    # Handle AI price extraction safely
    raw_price = ai_data.get("price", 0.0)
    try:
        final_price = float(raw_price)
    except (ValueError, TypeError):
        final_price = 0.0

    from datetime import datetime, timedelta
    ad_created_at = None
    if post.timestamp:
        try:
            # Handle standard ISO formats from the JS scraper
            dt_str = post.timestamp.replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str)
            
            # The database stores naive standard time in Jordan Local Time (UTC+3)
            # Since the scraper sends UTC (Z) or offset-aware dates, we shift to +3 first
            dt = dt + timedelta(hours=3)
            
            ad_created_at = dt.replace(tzinfo=None) # Use naive datetime for SQLAlchemy TIMESTAMP
        except ValueError:
            pass

    ad = models.Ad(
        user_id=ai_user_id,
        title=ad_title,
        description=ai_data.get("description") or post.text or "",
        price=final_price,
        location=mapped_location,
        image_url=json.dumps(post.images) if post.images and len(post.images) > 0 else None,
        category_id=final_category_id,
        source_type=SourceType.SCRAPER_BOT,
        source_url=post.postUrl or None,
        raw_description=(post.text or "")[:8000] if post.text else None,
        attributes={
            **ai_attrs, # Spread AI extracted attributes safely
            "dynamic_data": ai_attrs.get("dynamic_data", {}), # Ensure it explicitly exists
            "author": post.author,
            "timestamp": post.timestamp,
            "reactions": post.reactions,
            "scraped_at": post.scrapedAt,
            "phone_number": ai_data.get("phone_number"),
            "images": post.images or [],
        },
        is_published=True,
    )
    
    if ad_created_at:
        ad.created_at = ad_created_at
    
    # Map AI extracted Tags
    suggested_tags = ai_data.get("suggested_tags", [])
    if isinstance(suggested_tags, list) and len(suggested_tags) > 0:
        dest_category = None
        if final_category_id:
            dest_category = db.query(models.Category).filter(models.Category.id == final_category_id).first()
            
        for tag_name in suggested_tags:
            if not isinstance(tag_name, str):
                continue
            clean_tag = tag_name.strip()
            if not clean_tag:
                continue
            tag = db.query(models.Tag).filter(models.Tag.name == clean_tag).first()
            if not tag:
                tag = models.Tag(name=clean_tag)
                db.add(tag)
            ad.linked_tags.append(tag)
            
            # Propagate the tag to the global category so Flutter renders it as a filter chip!
            if dest_category and tag not in dest_category.linked_tags:
                dest_category.linked_tags.append(tag)
            
    db.add(ad)
    db.commit()
    db.refresh(ad)
    
    # Extract dynamic properties for normalized Real Estate Details table
    dyn = ai_attrs.get("dynamic_data", {})
    try:
        re_detail = models.AdRealEstateDetail(
            ad_id=ad.id,
            bathrooms=int(dyn.get("bathrooms", 0)) if str(dyn.get("bathrooms", "")).isdigit() else ai_attrs.get("bathrooms"),
            furnished=str(dyn.get("furnishing")) if dyn.get("furnishing") else str(ai_attrs.get("furnished", "")),
            build_area=dyn.get("area") or ai_attrs.get("area"),
            floor=str(dyn.get("floor")) if dyn.get("floor") else str(ai_attrs.get("floor", "")),
            rent_duration=str(dyn.get("rent_duration")) if dyn.get("rent_duration") else str(ai_attrs.get("rent_duration", "")),
            view_orientation=str(dyn.get("facade")) if dyn.get("facade") else None,
            building_age=str(dyn.get("age")) if dyn.get("age") else None,
            key_features=dyn.get("main_features", []) + ai_attrs.get("key_features", []),
            additional_features=dyn.get("extra_features", []) + dyn.get("target_tenants", []) + dyn.get("property_restrictions", []),
            nearby_locations=dyn.get("nearby", [])
        )
        db.add(re_detail)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create Real Estate Details for bot ad: {e}")
    
    # TRIGGER NOTIFICATION ENGINE 
    from observer import trigger_saved_filter_notifications
    try:
        trigger_saved_filter_notifications(db, ad)
    except Exception as e:
        logger.error(f"Failed to trigger notifications: {e}")
        
    return ad


# -- Main endpoint -----------------------------------------------------------

@router.post("/fb-posts/batch", response_model=FbBatchResponse)
def ingest_fb_posts_batch(
    req: FbBatchRequest,
    db: Session = Depends(get_db),
):
    """
    Accept a batch of scraped Facebook posts, process ALL through
    Gemini AI in ONE request, then save each result to the database.
    """
    try:
        return _do_ingest(req, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled error in batch endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def _log_training_data(db: Session, post_text: str, ai_output: dict, status: str, reason: str, raw_response: str = None, ai_model: str = None):
    try:
        log_entry = models.AITrainingLog(
            post_text=post_text,
            status=status,
            ai_model=ai_model,
            ai_output=ai_output,
            reason=reason,
            raw_response=raw_response
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Training logger failed: {e}")

def _do_ingest(req: FbBatchRequest, db: Session):
    if not req.posts:
        raise HTTPException(status_code=400, detail="No posts provided.")

    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("GROK_API_KEY")):
        raise HTTPException(status_code=500, detail="Missing AI API keys.")

    ai_user = _get_or_create_ai_user(db)
    results: List[PostResult] = []
    saved = skipped = errors = 0

    # Step 1: Filter duplicates and empty posts BEFORE calling AI
    posts_to_process: List[FbPost] = []
    post_index_map: dict = {}
    # Separate sets for URL and Text intra-batch deduplication
    seen_in_batch_urls = set()
    seen_in_batch_texts = set()

    for i, post in enumerate(req.posts):
        idx = post.index or (i + 1)

        if not post.text and not post.postUrl:
            skipped += 1
            results.append(PostResult(index=idx, status="skipped", reason="No text or URL"))
            continue

        dup_ad_id = _is_duplicate(db, post.postUrl or "", post.text or "")
        if dup_ad_id:
            skipped += 1
            reason = f"Duplicate post (Matches Ad ID {dup_ad_id})"
            _log_training_data(db, post.text or "", {"dup_ad_id": dup_ad_id}, "skipped", reason)
            results.append(PostResult(index=idx, status="skipped", reason=reason))
            continue
            
        # Intra-batch duplicate check (prevents sending identical posts to AI if they were both scraped just now)
        unique_key_url = None
        if post.postUrl:
            match = re.search(r'/posts/(\d+)', post.postUrl)
            if match:
                unique_key_url = f"post_{match.group(1)}"
            else:
                match2 = re.search(r'story_fbid=(\d+)', post.postUrl)
                if match2:
                    unique_key_url = f"story_{match2.group(1)}"
        
        unique_key_text = None
        is_intra_dup = False
        if unique_key_url and unique_key_url in seen_in_batch_urls:
            is_intra_dup = True
            
        if is_intra_dup:
            skipped += 1
            results.append(PostResult(index=idx, status="skipped", reason="Duplicate post (in batch)"))
            continue
            
        if unique_key_url: seen_in_batch_urls.add(unique_key_url)

        raw_text = post.text or ""
        clean_text = re.sub(r'[\s-]', '', raw_text)
        if not re.search(r'\d{9,}', clean_text):
            skipped += 1
            results.append(PostResult(index=idx, status="skipped", reason="No phone number found"))
            continue

        post_index_map[len(posts_to_process)] = idx
        posts_to_process.append(post)

    if not posts_to_process:
        return FbBatchResponse(
            total=len(req.posts), saved=0, skipped=skipped, errors=0, results=results,
        )

    # Step 2: Send ALL non-duplicate posts to AI safely in chunks
    try:
        logger.info(f"Sending {len(posts_to_process)} posts to AI...")
        ai_results = _ai_process_all(posts_to_process, db)
        logger.info(f"AI returned {len(ai_results)} results")
    except Exception as e:
        logger.error(f"AI failed: {e}. Falling back to default data.")
        ai_results = [{}] * len(posts_to_process)

    # Step 3: Save each AI result to the database
    for j, post in enumerate(posts_to_process):
        idx = post_index_map[j]
        ai_data = ai_results[j] if j < len(ai_results) else {}

        raw_res = None
        used_ai_model = None
        if isinstance(ai_data, dict):
            if "raw_unparsed_chunk_layer" in ai_data:
                raw_res = ai_data.pop("raw_unparsed_chunk_layer")
            if "ai_model" in ai_data:
                used_ai_model = ai_data.pop("ai_model")

        # 1. Output explicit AI Exceptions
        if isinstance(ai_data, dict) and "ai_chunk_error" in ai_data:
            skipped += 1
            reason = f"AI Error: {ai_data['ai_chunk_error']}"
            logger.error(f"Post #{idx} skipped: {reason}")
            _log_training_data(db, post.text or "", ai_data, "failed", reason, raw_res, used_ai_model)
            results.append(PostResult(index=idx, status="skipped", reason=reason))
            continue

        # 2. Skip if AI determined this is a "Looking for" post or rejected it explicitly
        if isinstance(ai_data, dict) and ai_data.get("category_id") == 0:
            skipped += 1
            reason = ai_data.get("rejection_reason", "AI determined post is not offering real estate (category_id=0)")
            logger.info(f"Post #{idx} rejected: {reason}")
            _log_training_data(db, post.text or "", ai_data, "rejected", reason, raw_res, used_ai_model)
            results.append(PostResult(index=idx, status="skipped", reason=reason))
            continue

        # 3. Finally, if AI just returned empty properties (like no title), complain
        if not ai_data or not ai_data.get("title"):
            skipped += 1
            reason = "AI returned missing or incomplete JSON (no title)"
            logger.info(f"Post #{idx} skipped: {reason}")
            _log_training_data(db, post.text or "", ai_data, "failed", reason, raw_res, used_ai_model)
            results.append(PostResult(index=idx, status="skipped", reason=reason))
            continue

        try:
            post.images = _upload_imgs_to_r2(post.images)
            ad = _save_ad_to_db(
                db=db, post=post, ai_data=ai_data,
                ai_user_id=ai_user.id,
                fb_request_category_id=req.category_id,
                default_location=req.default_location or "",
            )
            saved += 1
            _log_training_data(db, post.text or "", ai_data, "success", None, raw_res, used_ai_model)
            results.append(PostResult(index=idx, status="saved", ad_id=ad.id, title=ad.title))
            logger.info(f"Post #{idx} -> Ad ID {ad.id}: {ad.title}")
        except Exception as e:
            errors += 1
            logger.error(f"DB save failed for post #{idx}: {e}")
            results.append(PostResult(index=idx, status="error", reason=str(e)))

    return FbBatchResponse(
        total=len(req.posts), saved=saved, skipped=skipped, errors=errors, results=results,
    )
