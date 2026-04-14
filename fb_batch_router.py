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

_GEMINI_BATCH_PROMPT = """You are an AI assistant that extracts structured classified-ad data from Facebook posts.

Below is a numbered list of Facebook posts representing real classified ads (usually referencing locations in Jordan).
For EACH post, extract the following fields:
- index        (int) -- the post number as given
- title        (string, max 120 chars) -- a concise, clear ad title
- description  (string) -- rewrite and regenerate the description from scratch using the best SEO optimization language and highly engaging Arabic phrasing. Do NOT copy the original text directly. Make it sound like a premium, professional classified ad.
- price        (float) -- Extract the exact numeric price. Support eastern arabic numbers (e.g. ٥٠ دينار is 50.0). Look carefully for implicit rent/sale numbers. Return 0.0 ONLY if strictly missing. Do not return strings!
- location     (string) -- The geographic location. For real estate/apartments, format as 'المدينة, المنطقة' (e.g. عمان, عبدون). For lands (الأراضي), format as 'المحافظة, المديرية, القرية, الحوض' if mentioned (e.g. إربد, لواء بني كنانة, عقربا, حوض البلد). Keep empty if not found.
- phone_number (string or null) -- phone number if mentioned
- category_id  (int) -- Map to the MOST SPECIFIC deepest sub-category ID from the list (never use generic ID 3 if a deeper one like 301 or 3061 fits perfectly!). CRITICAL RULE: Analyze the intent of the author. If the author is SEEKING, ASKING FOR, or REQUESTING an apartment or roommate (meaning they do NOT have a property to offer, but are looking for one), set category_id to 0 to explicitly reject the post. Only accept posts where the author is realistically OFFERING a property or room.
- suggested_tags (list of strings) -- Array of specific feature keywords mentioned in the ad (e.g. "غرفة مفروشة", "طابق ارضي", "اوتوماتيك")
- attributes (object) -- Extract these specific property/shared-room features if mentioned:
    - rooms (int) -- Number of rooms
    - bathrooms (int) -- Number of bathrooms
    - furnished (string) -- Match exactly: مفروشة, غير مفروشة, مفروش جزئياً
    - floor (string) -- Match exactly: طابق التسوية, طابق شبه أرضي, الطابق الأرضي, 1, 2, 3, 4, 5, 6, 7
    - key_features (list[string]) -- Match exactly if possible: تكييف مركزي, تدفئة, شرفة / بلكونة, غرفة خادمة, غرفة غسيل, خزائن حائط, مسبح خاص, سخان شمسي, زجاج شبابيك مزدوج
    - room_type (string) -- غرفة خاصة, غرفة مشتركة, سرير في غرفة, استوديو ملحق بالسكن
    - target_audience (list[string]) -- شباب, طلاب, بنات, عائلات
    - room_capacity (string) -- شخص واحد, شخصين
    - current_occupants (int) -- Number of people currently in apartment
    - rent_duration (string) -- Match exactly: يومي, أسبوعي, شهري, كل 3 أشهر, كل أربع أشهر, كل 5 أشهر, كل 6 أشهر, سنوي
    - rent_includes (list[string]) -- الكهرباء, الماء, الإنترنت, التدفئة
    - payment_frequency (string) -- دفع شهري, دفع كل 3 شهور
    - insurance_required (bool)
    - bathroom_type (string) -- حمام ماستر, حمام مشترك
    - room_contents (list[string]) -- سرير مفرد, خزانة, شاشة
    - room_features (list[string]) -- مكيف مستقل, رديتر, بلكونة
    - shared_spaces (list[string]) -- صالة جلوس واسعة, طاولة طعام
    - kitchen_appliances (list[string]) -- ثلاجة, مايكرويف, غسالة
    - laundry_appliances (list[string]) -- غسالة, نشافة
    - smoking_rules (string) -- التدخين مسموح, يمنع التدخين
    - quietness_rules (string) -- سكن هادئ جداً, سكن مرن
    - guests_rules (string) -- مسموح بالزوار, يمنع الزوار
    - pets_rules (string) -- مسموح, يمنع
    - cleaning_rules (string)
    - building_age (string) -- Match exactly: 0 - 11 شهر, 1 - 5 سنوات, 6 - 9 سنوات, 10 - 19 سنوات, +20 سنة
    - building_features (list[string]) -- Match exactly if possible: يوجد مصعد, حديقة, موقف سيارات, حارس / أمن وحماية, كراج تفك, منطقة شواء, نظام كهرباء احتياطي للطوارئ, بركة سباحة, انتركم
    - land_type (string) -- Match exactly: سكنية, تجارية, زراعية, صناعية, استثمارية, سياحية, مختلطة, أخرى
    - zoning_classification (string) -- Match exactly: سكن أ, سكن ب, سكن ج, سكن د, تجاري, زراعي, صناعي, أخرى
    - facade (string) -- Match exactly: شمالية, جنوبية, شرقية, غربية, شمالية شرقية, شمالية غربية, جنوبية شرقية, جنوبية غربية
    - geometric_shape (string) -- Match exactly: مستطيل, مربع, غير منتظم, زاوية / شارعَين
    - topography (string) -- Match exactly: مستوية, منحدرة, جبلية, واد
    - available_services (list[string]) -- Match exactly: ماء, كهرباء, صرف صحي, إنترنت, شوارع معبدة
    - ownership_type (string) -- Match exactly: ملك, تفويض, أخرى
    - is_mortgaged (string) -- Match exactly: نعم, لا
    - installment_possible (string) -- Match exactly: نعم, لا
    - nearby_places (list[string]) -- جامعة, سوبر ماركت, قريبة من الباص

Return a JSON ARRAY where each element corresponds to one post.
Respond ONLY with valid JSON. No explanation, no markdown fences, no extra text.

=== CATEGORIES LIST ===
{categories_block}
=======================

=== POSTS ===
{posts_block}
"""


def _build_posts_block(posts: List[FbPost]) -> str:
    lines = []
    for i, p in enumerate(posts):
        idx = p.index or (i + 1)
        lines.append(f"--- Post #{idx} ---")
        lines.append(f"Author: {p.author or 'Unknown'}")
        lines.append(f"Text: {(p.text or '')[:2000]}")
        lines.append(f"URL: {p.postUrl or 'N/A'}")
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
        parent_name = ""
        if cat.parent_id:
            parent = category_map.get(cat.parent_id)
            if parent:
                parent_name = f" (Child of {parent.name})"
        
        linked_tags_str = ", ".join([tag.name for tag in getattr(cat, 'linked_tags', [])]) if getattr(cat, 'linked_tags', []) else ""
        tags = f" | Tag: {cat.tag}" if getattr(cat, 'tag', None) else ""
        keywords = f" | Keywords: {linked_tags_str}" if linked_tags_str else ""
        categories_context_lines.append(f"ID: {cat.id} | Name: {cat.name}{parent_name}{tags}{keywords}")
        
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

    # 1. Try Gemini
    if api_key_gemini:
        try:
            logger.info("Trying Gemini AI...")
            genai.configure(api_key=api_key_gemini)
            model = genai.GenerativeModel("gemini-2.5-flash")
            config = genai.types.GenerationConfig(response_mime_type="application/json")
            resp = model.generate_content(prompt, generation_config=config)
            return _parse_json_result(resp.text.strip())
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
            errors.append(f"Gemini: {e}")

    # 2. Try Grok (grok-3-mini)
    if api_key_grok:
        try:
            logger.info("Trying Grok AI...")
            headers = {"Authorization": f"Bearer {api_key_grok}", "Content-Type": "application/json"}
            payload = {
                "model": "grok-3-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.x.ai/v1/chat/completions", json=payload, headers=headers, timeout=60)
            res.raise_for_status()
            data = res.json()
            raw = data["choices"][0]["message"]["content"]
            return _parse_json_result(raw)
        except Exception as e:
            logger.warning(f"Grok failed: {e}")
            errors.append(f"Grok: {e}")

    # 3. Try DeepSeek
    if api_key_deepseek:
        try:
            logger.info("Trying DeepSeek AI...")
            headers = {"Authorization": f"Bearer {api_key_deepseek}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=60)
            res.raise_for_status()
            data = res.json()
            raw = data["choices"][0]["message"]["content"]
            return _parse_json_result(raw)
        except Exception as e:
            logger.warning(f"DeepSeek failed: {e}")
            errors.append(f"DeepSeek: {e}")

    raise RuntimeError(f"All AIs failed: {errors}")


def _ai_process_all(posts: List[FbPost], db: Session) -> List[dict]:
    """Process all posts in chunks to avoid token limits, running concurrently."""
    categories_block = _build_categories_block(db)
    
    CHUNK_SIZE = 4
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
        if db.query(models.Ad).filter(models.Ad.source_url == source_url).first():
            return True
    if raw_description:
        if db.query(models.Ad).filter(models.Ad.raw_description == raw_description[:500]).first():
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
        raw_description=(post.text or "")[:2000] if post.text else None,
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

        # Skip if AI determined this is a "Looking for" post
        if ai_data.get("category_id") == 0:
            skipped += 1
            logger.info(f"Post #{idx} rejected: AI determined it is seeking an apartment, not offering.")
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
            results.append(PostResult(index=idx, status="saved", ad_id=ad.id, title=ad.title))
            logger.info(f"Post #{idx} -> Ad ID {ad.id}: {ad.title}")
        except Exception as e:
            errors += 1
            logger.error(f"DB save failed for post #{idx}: {e}")
            results.append(PostResult(index=idx, status="error", reason=str(e)))

    return FbBatchResponse(
        total=len(req.posts), saved=saved, skipped=skipped, errors=errors, results=results,
    )
