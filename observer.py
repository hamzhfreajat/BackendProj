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
    # Quick filter for active saved filters that match the same category
    # AND have instant alerts enabled.
    filters = db.query(models.SavedFilter).filter(
        models.SavedFilter.is_active == True,
        models.SavedFilter.alert_frequency.in_(['فوري', 'instant']),
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
                
        # Check tags constraint
        if f.tags and len(f.tags) > 0:
            tag_match = False
            ad_tags = [t.name.lower() for t in ad.linked_tags]
            for tg in f.tags:
                if tg.lower() in ad_tags:
                    tag_match = True
                    break
            if not tag_match:
                continue

        # If it reaches here, all criteria match! Emit a notification.
        alert_title = f"إعلان جديد يطابق اهتمامك!"
        if f.name:
            alert_title = f"بحثك المحفوظ: {f.name}"
            
        alert_body = f"وجدنا: {ad.title[:40]}... بسعر {ad.price} دينار."
        
        # Async invocation (using asyncio.run since background tasks run in a threadpool)
        import asyncio
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
