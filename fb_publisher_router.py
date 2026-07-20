from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import models
from database import get_db
from facebook_publisher import publish_facebook_post
import asyncio

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
    region = db.query(models.Region).filter(models.Region.name_ar == req.region_name).first()
    
    ads = []
    if region:
        # Use AdSearchIndex to find ads by region_id
        query = db.query(models.AdSearchIndex.ad_id).filter(models.AdSearchIndex.region_id == region.id)
        if req.category_id:
            query = query.filter(models.AdSearchIndex.category_id == req.category_id)
            
        ad_ids_query = query.order_by(models.AdSearchIndex.created_at.desc()).limit(req.count).all()
        
        ad_ids = [r[0] for r in ad_ids_query]
        if ad_ids:
            ads = db.query(models.Ad).filter(models.Ad.id.in_(ad_ids)).all()
            # Sort them back in descending order as returned by AdSearchIndex
            ads.sort(key=lambda x: ad_ids.index(x.id))
    else:
        # Fallback to text matching
        query = db.query(models.Ad).filter(models.Ad.location.ilike(f"%{req.region_name}%"))
        if req.category_id:
            query = query.filter(models.Ad.category_id == req.category_id)
            
        ads = query.order_by(models.Ad.created_at.desc()).limit(req.count).all()
        
    if not ads:
        raise HTTPException(status_code=404, detail="No ads found in this region.")
        
    actual_count = len(ads)
    
    # Build catalog-like text
    msg = req.custom_text if req.custom_text else f"أحدث {actual_count} عقارات في ({req.region_name})! 🏡\n"
    msg += "\n\n"
    
    for i, ad in enumerate(ads, 1):
        price_str = f"{ad.price} دينار" if ad.price else "تواصل لمعرفة السعر"
        # Truncate title if too long
        title = ad.title[:50] + "..." if ad.title and len(ad.title) > 50 else (ad.title or "عقار")
        msg += f"{i}. {title}\n💰 السعر: {price_str}\n🔗 التفاصيل: https://sooq-com.com/ad/{ad.id}\n\n"
        
    msg += "تصفح المزيد على تطبيق وموقع سوقكم! ✨"
    
    # We will use the first ad's link as the main link preview, but only if we don't have images
    main_link = "https://sooq-com.com/"
    
    import json
    
    # Extract images and build child attachments for carousel
    child_attachments = []
    
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
            price_str = f"{ad.price} دينار" if ad.price else "تواصل لمعرفة السعر"
            title = ad.title[:30] + "..." if ad.title and len(ad.title) > 30 else (ad.title or "عقار")
            
            child_attachments.append({
                "link": f"https://sooq-com.com/ad/{ad.id}",
                "name": title,
                "description": price_str,
                "picture": main_image
            })
            
    # Max 10 items for a carousel
    child_attachments = child_attachments[:10]
    
    success = await publish_facebook_post(msg, main_link, child_attachments=child_attachments)
    if success:
        # Mark these ads as posted so auto-publisher doesn't republish them
        for ad in ads:
            ad.is_facebook_posted = True
        db.commit()
        return {"status": "success", "posted_count": actual_count}
    else:
        raise HTTPException(status_code=500, detail="Failed to publish to Facebook.")
