from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import models
from database import get_db
from facebook_publisher import publish_facebook_post
import asyncio

def _norm_str(s):
    if not s: return s
    for a, b in [('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ة', 'ه'), ('ى', 'ي')]:
        s = s.replace(a, b)
    return s

def _norm_col(col):
    from sqlalchemy.sql import func
    c = func.replace(col, 'أ', 'ا')
    c = func.replace(c, 'إ', 'ا')
    c = func.replace(c, 'آ', 'ا')
    c = func.replace(c, 'ة', 'ه')
    c = func.replace(c, 'ى', 'ي')
    return c

router = APIRouter(prefix="/api/facebook", tags=["facebook"])

class RuleCreate(BaseModel):
    region_name: str
    threshold: int

class RuleResponse(BaseModel):
    id: int
    region_name: str
    threshold: int
    
    class Config:
        orm_mode = True

class ManualPublishRequest(BaseModel):
    region_name: str
    count: int
    custom_text: Optional[str] = None
    category_id: Optional[int] = None
    format: Optional[str] = "catalog"

@router.get("-rules", response_model=List[RuleResponse])
def get_rules(db: Session = Depends(get_db)):
    return db.query(models.FacebookAutoPostRule).all()

@router.post("-rules", response_model=RuleResponse)
def add_or_update_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    existing = db.query(models.FacebookAutoPostRule).filter(models.FacebookAutoPostRule.region_name == rule.region_name).first()
    if existing:
        existing.threshold = rule.threshold
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_rule = models.FacebookAutoPostRule(region_name=rule.region_name, threshold=rule.threshold)
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        return new_rule

@router.delete("-rules/{region_name}")
def delete_rule(region_name: str, db: Session = Depends(get_db)):
    rule = db.query(models.FacebookAutoPostRule).filter(models.FacebookAutoPostRule.region_name == region_name).first()
    if rule:
        db.delete(rule)
        db.commit()
    return {"status": "ok"}

@router.post("/manual-publish")
async def manual_publish(req: ManualPublishRequest, db: Session = Depends(get_db)):
    # Try to resolve region_id from the given region_name
    region = db.query(models.Region).filter(_norm_col(models.Region.name_ar) == _norm_str(req.region_name)).first()
    
    query = db.query(models.Ad).filter(_norm_col(models.Ad.location).ilike(f"%{_norm_str(req.region_name)}%"))
    if req.category_id:
        query = query.filter(models.Ad.category_id == req.category_id)
        
    ads = query.order_by(models.Ad.created_at.desc()).limit(req.count).all()
        
    if not ads:
        raise HTTPException(status_code=404, detail="No ads found in this region.")
        
    actual_count = len(ads)
    
    # Format handling
    fmt = req.format if hasattr(req, 'format') and req.format else "catalog"
    
    # Build catalog-like text
    msg = req.custom_text if req.custom_text else f"أحدث {actual_count} عقارات في ({req.region_name})! 🏡\n"
    msg += "\n\n"
    
    emojis = ["🏡", "🌟", "✨", "💎"]
    for i, ad in enumerate(ads, 1):
        price_str = f"{ad.price} دينار" if ad.price else "تواصل لمعرفة السعر"
        # Truncate title if too long
        title = ad.title[:50] + "..." if ad.title and len(ad.title) > 50 else (ad.title or "عقار")
        emoji = emojis[(i-1) % len(emojis)]
        
        msg += f"{i}. {emoji} {title}\n💰 السعر: {price_str}\n\n"
        
    msg += "تصفح المزيد على تطبيق وموقع سوقكم! ✨\n"
    
    import urllib.parse
    
    # The user requested the main link (which is used for the final 'See more' card) 
    # to be the same as the link for the latest ad in the list.
    if ads and len(ads) > 0:
        main_link = f"https://share.sooq-com.com/ad/{ads[0].id}"
    else:
        main_link = "https://share.sooq-com.com/"
    
    import json
    
    # Extract images and build child attachments for carousel
    child_attachments = []
    all_images = []
    
    for ad in ads:
        # Determine main image for the ad
        main_image = None
        if hasattr(ad, 'image_urls') and ad.image_urls:
            main_image = ad.image_urls[0] if ad.image_urls else None
        elif hasattr(ad, 'image_url') and ad.image_url:
            try:
                parsed = json.loads(ad.image_url)
                if isinstance(parsed, list) and parsed:
                    main_image = parsed[0]
                else:
                    main_image = ad.image_url
            except:
                main_image = ad.image_url
                
        if main_image and isinstance(main_image, str):
            all_images.append(main_image)
            price_str = f"{ad.price} دينار" if ad.price else "تواصل لمعرفة السعر"
            title = ad.title[:30] + "..." if ad.title and len(ad.title) > 30 else (ad.title or "عقار")
            
            child_attachments.append({
                "link": f"https://share.sooq-com.com/ad/{ad.id}",
                "name": title,
                "description": price_str,
                "picture": main_image
            })
            
    # Max 10 items for a carousel or album
    child_attachments = child_attachments[:10]
    all_images = all_images[:10]
    
    # Format handling
    fmt = req.format if hasattr(req, 'format') and req.format else "catalog"
    final_msg = msg
    final_link = None
    final_images = None
    final_child = None
    
    # Append link to text if requested
    if fmt in ["link", "text_link_catalog", "text_link_images"]:
        final_msg += f"\nالرابط الأساسي: {main_link}"
        
    if fmt in ["catalog", "text_link_catalog"]:
        final_link = main_link
        final_child = child_attachments
    elif fmt in ["images", "text_link_images"]:
        final_images = all_images
    elif fmt == "link":
        final_link = main_link
    elif fmt == "text_only":
        pass
    else:
        # fallback
        final_link = main_link
        final_child = child_attachments
    
    success = await publish_facebook_post(
        final_msg, 
        link=final_link, 
        image_urls=final_images, 
        child_attachments=final_child
    )
    if success:
        # Mark these ads as posted so auto-publisher doesn't republish them
        for ad in ads:
            ad.is_facebook_posted = True
        db.commit()
        return {"status": "success", "posted_count": actual_count}
    else:
        raise HTTPException(status_code=500, detail="Failed to publish to Facebook.")

@router.post("/generate-text")
async def generate_text(req: ManualPublishRequest, db: Session = Depends(get_db)):
    query = db.query(models.Ad).filter(_norm_col(models.Ad.location).ilike(f"%{_norm_str(req.region_name)}%"))
    if req.category_id:
        query = query.filter(models.Ad.category_id == req.category_id)
        
    ads = query.order_by(models.Ad.created_at.desc()).limit(req.count).all()
        
    if not ads:
        raise HTTPException(status_code=404, detail="No ads found in this region.")
        
    actual_count = len(ads)
    
    msg = req.custom_text if req.custom_text else f"أحدث {actual_count} عقارات في ({req.region_name})! 🏡\n"
    msg += "\n\n"
    
    fmt = req.format if hasattr(req, 'format') and req.format else "catalog"

    emojis = ["🏡", "🌟", "✨", "💎"]

    for i, ad in enumerate(ads, 1):
        price_str = f"{ad.price} دينار" if ad.price else "تواصل لمعرفة السعر"
        title = ad.title[:50] + "..." if ad.title and len(ad.title) > 50 else (ad.title or "عقار")
        emoji = emojis[(i-1) % len(emojis)]
        
        if fmt in ["images", "text_only", "link"]:
            # no individual links
            msg += f"{i}. {emoji} {title}\n💰 السعر: {price_str}\n\n"
        else:
            # We explicitly WANT individual links here since the user wants to copy/paste it
            msg += f"{i}. {emoji} {title}\n💰 السعر: {price_str}\n🔗 التفاصيل:\nhttps://share.sooq-com.com/ad/{ad.id}\n\n"
        
    msg += "تصفح المزيد على تطبيق وموقع سوقكم! ✨\n"
    
    if ads and len(ads) > 0:
        main_link = f"https://share.sooq-com.com/ad/{ads[0].id}"
    else:
        main_link = "https://share.sooq-com.com/"
        
    if fmt in ["link", "text_link_catalog", "text_link_images"]:
        msg += f"\nالرابط الأساسي: {main_link}"

    return {"text": msg, "main_link": main_link, "count": actual_count}

@router.get("/ready-combinations")
def get_ready_combinations(db: Session = Depends(get_db)):
    from sqlalchemy import func
    import datetime
    
    # Find leaf categories
    parent_ids = db.query(models.Category.parent_id).filter(models.Category.parent_id.isnot(None)).distinct()
    leaf_categories = db.query(models.Category).filter(~models.Category.id.in_(parent_ids)).all()
    leaf_cat_ids = [c.id for c in leaf_categories]
    leaf_cat_map = {c.id: c.name for c in leaf_categories}
    
    now = datetime.datetime.utcnow()
    
    # Group ads in Ad by region_name ILIKE and category_id
    results = db.query(
        models.Region.id.label('region_id'),
        models.Region.name_ar.label('region_name'),
        models.Ad.category_id,
        func.count(models.Ad.id).label('post_count')
    ).join(
        models.Ad, _norm_col(models.Ad.location).ilike(func.concat('%', _norm_col(models.Region.name_ar), '%'))
    ).filter(
        models.Ad.category_id.in_(leaf_cat_ids),
        models.Ad.is_published == True,
        models.Ad.is_paused == False,
        models.Ad.is_sold == False,
        models.Ad.is_rejected == False,
        (models.Ad.expires_at == None) | (models.Ad.expires_at > now)
    ).group_by(
        models.Region.id,
        models.Region.name_ar,
        models.Ad.category_id
    ).having(
        func.count(models.Ad.id) >= 50
    ).all()
    
    output = []
    for r in results:
        cat_name = leaf_cat_map.get(r.category_id, "قسم غير معروف")
        
        output.append({
            "region_name": r.region_name,
            "category_id": r.category_id,
            "category_name": cat_name,
            "count": min(r.post_count, 20),
            "actual_count": r.post_count
        })
        
    return output
