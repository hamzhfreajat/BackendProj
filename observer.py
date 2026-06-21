import models
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from notifications import send_personal_notification
import json

def trigger_saved_filter_notifications(db: Session, ad: models.Ad):
    """
    Checks all active Saved Filters against the newly inserted ad.
    If conditions match, sends a notification to the User.
    """
    # Do not send notifications for ads with no price or zero price (to avoid spamming users with incomplete scraped ads)
    if not ad.price or ad.price <= 0:
        return

    # Quick filter for active saved filters that match the same category
    # AND have instant alerts enabled.
    filters = db.query(models.SavedFilter).filter(
        models.SavedFilter.is_active == True,
        models.SavedFilter.alert_frequency.in_(['فوري', 'instant', 'batch_100']),
        (models.SavedFilter.category_id == ad.category_id) | (models.SavedFilter.category_id == None)
    ).all()

    for f in filters:
        # Check price constraints
        if f.min_price is not None and ad.price < f.min_price:
            continue
        if f.max_price is not None and ad.price > f.max_price:
            continue
            
        # Check location constraint 
        # (Assuming location is a substring match of ad.location for now)
        if f.locations and len(f.locations) > 0:
            location_match = False
            ad_location = ad.location.lower() if ad.location else ""
            for loc in f.locations:
                if loc.lower() in ad_location:
                    location_match = True
                    break
            if not location_match:
                continue
                
        # Check tags and attributes constraint
        if f.tags and len(f.tags) > 0:
            normal_tags = []
            kv_tags = {}
            for tg in f.tags:
                if ":" in tg:
                    k, v = tg.split(":", 1)
                    if k not in kv_tags:
                        kv_tags[k] = []
                    kv_tags[k].append(v)
                else:
                    normal_tags.append(tg.lower())

            ad_tags = [t.name.lower() for t in ad.linked_tags]
            
            # 1. Normal tags (require AT LEAST ONE match if any exist)
            if normal_tags:
                has_normal_match = any(nt in ad_tags for nt in normal_tags)
                if not has_normal_match:
                    continue

            # 2. Key-Value Attributes (must match ALL keys, but ANY value within the key)
            if kv_tags:
                if not ad.attributes:
                    continue # Ad has no attributes but filter requires them
                
                dyn_data = ad.attributes.get("dynamic_data", {})
                failed_kv = False
                for k, allowed_vals in kv_tags.items():
                    # Map 'bedrooms' to 'rooms' for scraper data compatibility
                    db_k = "rooms" if k == "bedrooms" else k
                    
                    if k == "min_area":
                        area = ad.attributes.get("area") or dyn_data.get("area")
                        if not area or int(area) < int(allowed_vals[0]):
                            failed_kv = True; break
                    elif k == "max_area":
                        area = ad.attributes.get("area") or dyn_data.get("area")
                        if not area or int(area) > int(allowed_vals[0]):
                            failed_kv = True; break
                    else:
                        raw_val = ad.attributes.get(db_k)
                        if raw_val is None:
                            raw_val = dyn_data.get(db_k)
                            
                        # Treat None or empty string as an automatic failure if the filter requires a value
                        if raw_val is None or raw_val == "":
                            failed_kv = True; break
                            
                        ad_val = str(raw_val)
                        if ad_val not in allowed_vals:
                            failed_kv = True; break
                
                if failed_kv:
                    continue

        # If it reaches here, all criteria match!
        import asyncio
        if f.alert_frequency in ['فوري', 'instant']:
            alert_title = f"إعلان جديد يطابق اهتمامك!"
            if f.name:
                alert_title = f"بحثك المحفوظ: {f.name}"
                
            alert_body = f"وجدنا: {ad.title[:40]}... بسعر {ad.price} دينار."
            
            try:
                asyncio.run(send_personal_notification(
                    target_user_id=f.user_id,
                    title=alert_title,
                    body=alert_body,
                    notification_type="saved_filter_alert",
                    reference_id=ad.id
                ))
            except Exception as e:
                print(f"Error sending filter notification: {e}")
        elif f.alert_frequency == 'batch_100':
            f.match_count = (f.match_count or 0) + 1
            if f.match_count >= 100:
                alert_title = "100 إعلان جديد يطابق بحثك"
                alert_body = "تصفح أحدث الإعلانات التي تم إضافتها بناءً على بحثك المحفوظ"
                if f.name:
                    alert_title = f"100 إعلان لـ {f.name}"
                try:
                    asyncio.run(send_personal_notification(
                        target_user_id=f.user_id,
                        title=alert_title,
                        body=alert_body,
                        notification_type="saved_search_batch",
                        reference_id=f.id # Passing filter_id as reference_id for navigation
                    ))
                except Exception as e:
                    print(f"Error sending batch notification: {e}")
                f.match_count = 0
            
    db.commit()
