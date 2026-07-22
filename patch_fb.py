with open('fb_publisher_router.py', 'a', encoding='utf-8') as f:
    f.write('''

@router.post("/generate-text")
async def generate_text(req: ManualPublishRequest, db: Session = Depends(get_db)):
    # Try to resolve region_id from the given region_name
    region = db.query(models.Region).filter(models.Region.name_ar == req.region_name).first()
    
    ads = []
    if region:
        query = db.query(models.AdSearchIndex.ad_id).filter(models.AdSearchIndex.region_id == region.id)
        if req.category_id:
            query = query.filter(models.AdSearchIndex.category_id == req.category_id)
            
        ad_ids_query = query.order_by(models.AdSearchIndex.created_at.desc()).limit(req.count).all()
        
        ad_ids = [r[0] for r in ad_ids_query]
        if ad_ids:
            ads = db.query(models.Ad).filter(models.Ad.id.in_(ad_ids)).all()
            ads.sort(key=lambda x: ad_ids.index(x.id))
    else:
        query = db.query(models.Ad).filter(models.Ad.location.ilike(f"%{req.region_name}%"))
        if req.category_id:
            query = query.filter(models.Ad.category_id == req.category_id)
            
        ads = query.order_by(models.Ad.created_at.desc()).limit(req.count).all()
        
    if not ads:
        raise HTTPException(status_code=404, detail="No ads found in this region.")
        
    actual_count = len(ads)
    
    msg = req.custom_text if req.custom_text else f"???? {actual_count} ?????? ?? ({req.region_name})! ??\\n"
    msg += "\\n\\n"
    
    for i, ad in enumerate(ads, 1):
        price_str = f"{ad.price} ?????" if ad.price else "????? ?????? ?????"
        title = ad.title[:50] + "..." if ad.title and len(ad.title) > 50 else (ad.title or "????")
        
        # We explicitly WANT individual links here since the user wants to copy/paste it
        msg += f"{i}. {title}\\n?? ?????: {price_str}\\n?? ????????: https://share.sooq-com.com/ad/{ad.id}\\n\\n"
        
    msg += "???? ?????? ??? ????? ????? ?????! ?"
    
    if ads and len(ads) > 0:
        main_link = f"https://share.sooq-com.com/ad/{ads[0].id}"
    else:
        main_link = "https://share.sooq-com.com/"

    return {"text": msg, "main_link": main_link, "count": actual_count}
''')
