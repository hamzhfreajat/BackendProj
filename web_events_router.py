"""
What visitors of the public website do with an ad: see it in a list, open its page,
show the phone number, open WhatsApp or the chat. The same counters the app keeps (`Ad.views`,
`Ad.chats_count`), so an advertiser sees website and app visitors together.

Website visitors are not signed in, so the app's /interaction endpoints do not fit.
The website sends these with navigator.sendBeacon: a plain POST with no body or a
plain-text one, which needs no CORS preflight. The response is never read, so it is always 204.

The browser counts each ad once a day per visitor (it remembers what it sent), and
crawlers are ignored here. Like the app's bulk-views endpoint, nothing stops a
determined script from inflating a counter; the rate limit keeps that small.
"""
import logging
import re
from typing import List

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

import auth
import models
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web/ads", tags=["web-events"])

CONTACT_KINDS = {"phone", "whatsapp", "chat"}
# Ads seen in lists arrive in batches, like the app's bulk views
MAX_SHOWN_BATCH = 60
_CRAWLER = re.compile(r"bot|crawl|spider|slurp|facebookexternalhit|preview|headless|lighthouse", re.IGNORECASE)


def _is_crawler(request: Request) -> bool:
    return bool(_CRAWLER.search(request.headers.get("user-agent", "")))


def _add_views(db: Session, ad_ids: List[int]):
    """Through the same buffer as the app's views, flushed to the database in batches."""
    from auth import redis_client
    if redis_client:
        try:
            pipe = redis_client.pipeline()
            for ad_id in ad_ids:
                pipe.hincrby("ad_views_buffer", str(ad_id), 1)
            pipe.execute()
            return
        except Exception as error:
            logger.error(f"Website views not buffered, writing them directly: {error}")
    db.query(models.Ad).filter(models.Ad.id.in_(ad_ids)).update(
        {models.Ad.views: func.coalesce(models.Ad.views, 0) + 1}, synchronize_session=False
    )
    db.commit()


@router.post("/{ad_id}/seen", status_code=204, dependencies=[Depends(auth.get_rate_limiter(120, 60))])
def ad_seen(ad_id: int, request: Request, db: Session = Depends(get_db)):
    """A visitor opened the ad's page."""
    if not _is_crawler(request):
        _add_views(db, [ad_id])
    return Response(status_code=204)


@router.post("/shown", status_code=204, dependencies=[Depends(auth.get_rate_limiter(30, 60))])
async def ads_shown(request: Request, db: Session = Depends(get_db)):
    """Ads a visitor saw in a list: at least half the card on screen for a second.
    The body is the ids as plain text, "61000,61001", so the beacon needs no preflight."""
    if _is_crawler(request):
        return Response(status_code=204)
    raw = await request.body()
    parts = raw[:2000].decode("utf-8", "ignore").split(",")
    if len(raw) > 2000:
        parts = parts[:-1]  # cut in the middle of an id
    ad_ids = list(dict.fromkeys(int(part) for part in parts if part.strip().isdigit()))[:MAX_SHOWN_BATCH]
    if ad_ids:
        _add_views(db, ad_ids)
    return Response(status_code=204)


@router.post("/{ad_id}/contact/{kind}", status_code=204, dependencies=[Depends(auth.get_rate_limiter(60, 60))])
def ad_contacted(ad_id: int, kind: str, request: Request, db: Session = Depends(get_db)):
    """A visitor showed the phone number, opened WhatsApp or the chat."""
    if kind not in CONTACT_KINDS or _is_crawler(request):
        return Response(status_code=204)
    db.query(models.Ad).filter(models.Ad.id == ad_id).update(
        {models.Ad.chats_count: func.coalesce(models.Ad.chats_count, 0) + 1}, synchronize_session=False
    )
    db.commit()
    return Response(status_code=204)
