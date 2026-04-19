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
from sqlalchemy.orm import Session

# SDK imports - prefer new google.genai, fallback to old google.generativeai
try:
    from google import genai as _genai_new
    _USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    _USE_NEW_SDK = False

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
- description: (string) rewrite professionally for SEO. Do not strictly copy.
- price: (float) numeric price (0.0 if missing)
- location: (string) e.g. 'عمان, عبدون'. IMPORTANT RULE: Numbered zones (المنطقة الثالثة, الخامسة, السادسة, التاسعة, etc.) belong to العقبة (Aqaba), NOT Amman! Output format: 'العقبة, المنطقة الثالثة'. Empty if missing.
- phone_number: (string or null)
- category_id: (int) Map to the deepest specific sub-category ID from the list below. (Rule: Use 0 if the author is SEEKING/ASKING for an apartment, not offering one).
- suggested_tags: (list[string]) 2-4 important keywords mentioned.
- attributes: (object) Extract the following ONLY if explicitly mentioned (OMIT the key entirely if not found to save tokens!):
  area (string/int), rooms (int), bathrooms (int), furnished (string), floor (string), rent_duration (string), key_features (list[string]), room_type (string), target_audience (list[string]), room_capacity (string), rent_includes (list[string]), payment_frequency (string), insurance_required (bool), building_age (string), building_features (list[string]), land_type (string), zoning_classification (string).

CATEGORIES:
{categories_block}

POSTS:
{posts_block}
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


def _build_categories_block(db: Session) -> str:
    # Fetch only categories related to apartments/residential rent and sale
    c_all = db.query(models.Category).all()
    allowed_ids = set()
    category_map = {c.id: c for c in c_all}

    for c in c_all:
        if any(keyword in c.name for keyword in ["شقق", "شقة", "سكن", "ستوديو", "سكني", "فيلات", "عقارات"]):
            allowed_ids.add(c.id)
            # Add parents recursively so AI sees the full path context (e.g. Real estate -> Residential -> Apartment)
            pid = c.parent_id
            while pid:
                allowed_ids.add(pid)
                parent = category_map.get(pid)
                pid = parent.parent_id if parent else None

    # Sort categories to group parents with children visually
    db_categories = sorted([c for c in c_all if c.id in allowed_ids], key=lambda x: x.id)
    
    categories_context_lines = []
    for cat in db_categories:
        linked_tags_str = ",".join([tag.name for tag in getattr(cat, 'linked_tags', [])]) if getattr(cat, 'linked_tags', []) else ""
        keywords = f" | {linked_tags_str}" if linked_tags_str else ""
        categories_context_lines.append(f"ID:{cat.id} Name:{cat.name}{keywords}")
        
    return "\n".join(categories_context_lines)


def _ai_process_chunk(chunk_posts: List[FbPost], categories_block: str) -> List[dict]:
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
        logger.info("Stripping markdown fences...")
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        logger.info("Parsing JSON...")
        parsed = json.loads(raw)
        
        # Unpack if json_object wrapper is used (common for Deepseek/Grok JSON mode)
        if isinstance(parsed, dict) and len(parsed) == 1 and "posts" in parsed:
            parsed = parsed["posts"]
        elif isinstance(parsed, dict):
            parsed = [parsed]
            
        logger.info("JSON successfully parsed.")
        return parsed

    # 1. Try DeepSeek (Priority 1 to minimize token cost)
    if api_key_deepseek:
        try:
            logger.info("Trying DeepSeek AI...")
            headers = {"Authorization": f"Bearer {api_key_deepseek}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=25)
            res.raise_for_status()
            data = res.json()
            raw = data["choices"][0]["message"]["content"]
            return _parse_json_result(raw)
        except Exception as e:
            logger.warning(f"DeepSeek failed/timed-out: {e}")
            errors.append(f"DeepSeek: {e}")

    # 2. Try Gemini
    if api_key_gemini:
        try:
            logger.info("Trying Gemini AI...")
            genai.configure(api_key=api_key_gemini)
            # Use gemini-2.5-flash as an efficient fallback
            model = genai.GenerativeModel("gemini-2.5-flash")
            config = genai.types.GenerationConfig(response_mime_type="application/json")
            # Set explicit timeout to prevent 524 timeout chain
            resp = model.generate_content(prompt, generation_config=config, request_options={"timeout": 25.0})
            return _parse_json_result(resp.text.strip())
        except Exception as e:
            logger.warning(f"Gemini failed/timed-out: {e}")
            errors.append(f"Gemini: {e}")

    # 3. Try Grok (grok-3-mini)
    if api_key_grok:
        try:
            logger.info("Trying Grok AI...")
            headers = {"Authorization": f"Bearer {api_key_grok}", "Content-Type": "application/json"}
            payload = {
                "model": "grok-3-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.x.ai/v1/chat/completions", json=payload, headers=headers, timeout=25)
            res.raise_for_status()
            data = res.json()
            raw = data["choices"][0]["message"]["content"]
            return _parse_json_result(raw)
        except Exception as e:
            logger.warning(f"Grok failed/timed-out: {e}")
            errors.append(f"Grok: {e}")

    raise RuntimeError(f"All AIs failed: {errors}")


def _ai_process_all(posts: List[FbPost], db: Session) -> List[dict]:
    """Process all posts in chunks to avoid token limits, running concurrently."""
    categories_block = _build_categories_block(db)
    
    # Increased chunk size to minimize API requests for large batches natively
    CHUNK_SIZE = 25
    chunks = [posts[i:i + CHUNK_SIZE] for i in range(0, len(posts), CHUNK_SIZE)]
    
    def process_single_chunk(chunk):
        try:
            logger.info(f"Sending chunk of {len(chunk)} posts to AI...")
            res = _ai_process_chunk(chunk, categories_block)
            if len(res) < len(chunk):
                res.extend([{}] * (len(chunk) - len(res)))
            return res[:len(chunk)]
        except Exception as e:
            logger.error(f"AI chunk failed: {e}. Falling back to default data for chunk.")
            return [{}] * len(chunk)

    all_results = []
    # Run all AI chunk processing concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
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


def _is_duplicate(db: Session, source_url: str, raw_description: str) -> bool:
    if source_url:
        import re
        # 1. Check exact match
        if db.query(models.Ad).filter(models.Ad.source_url == source_url).first():
            return True
            
        # 2. Extract FB Post ID and use LIKE matcher (handles tracking parameter changes)
        match = re.search(r'/posts/(\d+)', source_url)
        if match:
            post_id = match.group(1)
            if db.query(models.Ad).filter(models.Ad.source_url.like(f"%/posts/{post_id}%")).first():
                return True
                
        match2 = re.search(r'story_fbid=(\d+)', source_url)
        if match2:
            post_id = match2.group(1)
            if db.query(models.Ad).filter(models.Ad.source_url.like(f"%story_fbid={post_id}%")).first():
                return True

    if raw_description and len(raw_description) > 30:
        # 3. Match by the first 250 characters of the description instead of 100.
        # This prevents completely distinct posts from being marked as duplicates
        # just because they start with the same long generic greeting.
        short_desc = raw_description[:250]
        safe_desc = short_desc.replace('%', '\\%').replace('_', '\\_')
        if db.query(models.Ad).filter(models.Ad.raw_description.like(f"{safe_desc}%")).first():
            return True
            
    return False


def _save_ad_to_db(db, post, ai_data, ai_user_id, fb_request_category_id, default_location):
    # Ensure Gemini's dynamic assignment takes priority over wildcard fb_request mapping
    final_category_id = ai_data.get("category_id") or fb_request_category_id or 3

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
        location=ai_data.get("location") or default_location or "",
        image_url=json.dumps(post.images) if post.images and len(post.images) > 0 else None,
        category_id=final_category_id,
        source_type=SourceType.SCRAPER_BOT,
        source_url=post.postUrl or None,
        raw_description=(post.text or "")[:8000] if post.text else None,
        attributes={
            **ai_attrs, # Spread AI extracted attributes safely
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
            
    db.add(ad)
    db.commit()
    db.refresh(ad)
    
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

def _log_training_data(db: Session, post_text: str, ai_output: dict, status: str, reason: Optional[str] = None):
    try:
        record = models.AITrainingLog(
            post_text=post_text,
            status=status,
            ai_output=ai_output,
            reason=reason
        )
        db.add(record)
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
    seen_in_batch = set()

    for i, post in enumerate(req.posts):
        idx = post.index or (i + 1)

        if not post.text and not post.postUrl:
            skipped += 1
            results.append(PostResult(index=idx, status="skipped", reason="No text or URL"))
            continue

        if _is_duplicate(db, post.postUrl or "", post.text or ""):
            skipped += 1
            results.append(PostResult(index=idx, status="skipped", reason="Duplicate post"))
            continue
            
        # Intra-batch duplicate check (prevents sending 2 identical posts to AI if they were both scraped just now)
        unique_key = None
        if post.postUrl:
            import re
            match = re.search(r'/posts/(\d+)', post.postUrl)
            if match:
                unique_key = f"post_{match.group(1)}"
            else:
                match2 = re.search(r'story_fbid=(\d+)', post.postUrl)
                if match2:
                    unique_key = f"story_{match2.group(1)}"
        
        if not unique_key and post.text and len(post.text) > 30:
            unique_key = f"text_{post.text[:250]}"
            
        if unique_key:
            if unique_key in seen_in_batch:
                skipped += 1
                results.append(PostResult(index=idx, status="skipped", reason="Duplicate post (in batch)"))
                continue
            seen_in_batch.add(unique_key)

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

        # If AI failed to process this post (returned empty or no title), SKIP it!
        if not ai_data or not isinstance(ai_data, dict) or not ai_data.get("title"):
            skipped += 1
            logger.info(f"Post #{idx} skipped: AI processing failed or returned empty data.")
            _log_training_data(db, post.text or "", ai_data, "failed", "AI processing failed or returned empty title")
            results.append(PostResult(index=idx, status="skipped", reason="AI processing failed"))
            continue

        # Skip if AI determined this is a "Looking for" post
        if ai_data.get("category_id") == 0:
            skipped += 1
            logger.info(f"Post #{idx} rejected: AI determined it is seeking an apartment, not offering.")
            _log_training_data(db, post.text or "", ai_data, "rejected", "Seeking apartment (category_id=0)")
            results.append(PostResult(index=idx, status="skipped", reason="Seeking apartment, not offering"))
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
            _log_training_data(db, post.text or "", ai_data, "success", None)
            results.append(PostResult(index=idx, status="saved", ad_id=ad.id, title=ad.title))
            logger.info(f"Post #{idx} -> Ad ID {ad.id}: {ad.title}")
        except Exception as e:
            errors += 1
            logger.error(f"DB save failed for post #{idx}: {e}")
            results.append(PostResult(index=idx, status="error", reason=str(e)))

    return FbBatchResponse(
        total=len(req.posts), saved=saved, skipped=skipped, errors=errors, results=results,
    )
