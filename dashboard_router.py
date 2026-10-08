"""
Endpoints for the admin panel's home page and for handling ad reports.

Everything here is for signed-in admins only.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

import auth
import models
from database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

UNKNOWN_LOCATION = "غير محدد"
REPORT_STATUSES = {"pending", "reviewed", "dismissed"}
TREND_DAYS = 14
TOP_ROWS = 8


def _live(Ad):
    """An ad visitors can see: published and not sold, paused or rejected."""
    return and_(
        Ad.is_published == True,  # noqa: E712
        or_(Ad.is_sold == False, Ad.is_sold.is_(None)),  # noqa: E712
        or_(Ad.is_paused == False, Ad.is_paused.is_(None)),  # noqa: E712
        or_(Ad.is_rejected == False, Ad.is_rejected.is_(None)),  # noqa: E712
    )


@router.get("/overview")
def overview(db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin)):
    """The numbers on the panel's home page: ads, users, what needs attention, and recent trends."""
    Ad, User = models.Ad, models.User
    now = datetime.utcnow()
    day, week, fortnight = now - timedelta(days=1), now - timedelta(days=7), now - timedelta(days=14)
    organic = Ad.source_type == models.SourceType.ORGANIC_USER
    live = _live(Ad)

    def count(*conditions):
        return func.count(Ad.id).filter(and_(*conditions)) if conditions else func.count(Ad.id)

    ads = db.query(
        count(),
        count(live),
        count(Ad.created_at >= day),
        count(Ad.created_at >= week),
        count(Ad.created_at >= fortnight, Ad.created_at < week),
        count(live, organic),
        count(live, Ad.location == UNKNOWN_LOCATION),
        count(live, or_(Ad.price.is_(None), Ad.price <= 0)),
        count(Ad.is_rejected == True),  # noqa: E712
        count(Ad.is_featured == True, live),  # noqa: E712
    ).one()

    users = db.query(
        func.count(User.id),
        func.count(User.id).filter(User.created_at >= day),
        func.count(User.id).filter(User.created_at >= week),
        func.count(User.id).filter(and_(User.created_at >= fortnight, User.created_at < week)),
        func.count(User.id).filter(User.is_banned == True),  # noqa: E712
    ).one()

    pending_reports = db.query(func.count(models.AdReport.id)).filter(models.AdReport.status == "pending").scalar() or 0
    reviews_week = db.query(func.count(models.AdReview.id)).filter(models.AdReview.created_at >= week).scalar() or 0
    low_reviews_week = (
        db.query(func.count(models.AdReview.id))
        .filter(models.AdReview.created_at >= week, models.AdReview.rating <= 2, models.AdReview.is_hidden == False)  # noqa: E712
        .scalar()
        or 0
    )

    # New ads per day, split by where they came from
    since = (now - timedelta(days=TREND_DAYS - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    bucket = func.date(Ad.created_at)
    per_day = dict(
        (str(row[0]), (row[1], row[2]))
        for row in db.query(bucket, func.count(Ad.id).filter(organic), func.count(Ad.id).filter(~organic))
        .filter(Ad.created_at >= since)
        .group_by(bucket)
        .all()
    )
    trend = []
    for offset in range(TREND_DAYS):
        date = (since + timedelta(days=offset)).date()
        organic_count, scraped_count = per_day.get(str(date), (0, 0))
        trend.append({"date": str(date), "organic": organic_count or 0, "scraped": scraped_count or 0})

    # Live ads per city: the part of "المدينة, المنطقة" before the comma
    city = func.split_part(Ad.location, ",", 1)
    cities = (
        db.query(city, func.count(Ad.id))
        .filter(live, Ad.location.isnot(None), Ad.location != "")
        .group_by(city)
        .order_by(func.count(Ad.id).desc())
        .limit(TOP_ROWS)
        .all()
    )

    categories = (
        db.query(models.Category.name, func.count(Ad.id))
        .join(Ad, Ad.category_id == models.Category.id)
        .filter(live)
        .group_by(models.Category.name)
        .order_by(func.count(Ad.id).desc())
        .limit(TOP_ROWS)
        .all()
    )

    new_seekers = db.query(func.count(models.SeekerPost.id)).filter(models.SeekerPost.status == "new").scalar() or 0

    last_scrape = db.query(models.ScrapingLog).order_by(models.ScrapingLog.created_at.desc()).first()
    scraped_day = (
        db.query(func.coalesce(func.sum(models.ScrapingLog.saved_ads), 0), func.coalesce(func.sum(models.ScrapingLog.errors_count), 0))
        .filter(models.ScrapingLog.created_at >= day)
        .one()
    )

    recent = db.query(Ad).order_by(Ad.created_at.desc()).limit(6).all()

    return {
        "ads": {
            "total": ads[0], "live": ads[1], "today": ads[2], "week": ads[3], "previous_week": ads[4],
            "live_organic": ads[5], "live_scraped": ads[1] - ads[5], "unplaced": ads[6], "no_price": ads[7],
            "rejected": ads[8], "featured": ads[9],
        },
        "users": {"total": users[0], "today": users[1], "week": users[2], "previous_week": users[3], "banned": users[4]},
        "attention": {"pending_reports": pending_reports, "low_reviews_week": low_reviews_week, "reviews_week": reviews_week, "new_seekers": new_seekers},
        "trend": trend,
        "cities": [{"name": (name or "").strip() or UNKNOWN_LOCATION, "count": total} for name, total in cities],
        "categories": [{"name": name, "count": total} for name, total in categories],
        "scraping": {
            "last_run": last_scrape.created_at.isoformat() if last_scrape and last_scrape.created_at else None,
            "last_group": last_scrape.group_name if last_scrape else None,
            "saved_today": int(scraped_day[0] or 0),
            "errors_today": int(scraped_day[1] or 0),
        },
        "recent_ads": [
            {
                "id": ad.id, "title": ad.title, "price": float(ad.price) if ad.price is not None else None, "location": ad.location,
                "created_at": ad.created_at.isoformat() if ad.created_at else None,
                "source_type": str(getattr(ad.source_type, "value", ad.source_type)) if ad.source_type is not None else None,
            }
            for ad in recent
        ],
    }


class ReportStatusUpdate(BaseModel):
    status: str


@router.patch("/reports/{report_id}")
def update_report(
    report_id: int,
    body: ReportStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin),
):
    """Marks a report as reviewed or dismissed (or back to pending)."""
    if body.status not in REPORT_STATUSES:
        raise HTTPException(status_code=400, detail="Unknown report status")
    report = db.query(models.AdReport).filter(models.AdReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = body.status
    db.commit()
    return {"id": report.id, "status": report.status}


@router.delete("/reports/{report_id}", status_code=204)
def delete_report(report_id: int, db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin)):
    report = db.query(models.AdReport).filter(models.AdReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()


# ---------------------------------------------------------------------------
# Cities, areas and the other names people use for an area
# ---------------------------------------------------------------------------
import re

from sqlalchemy.exc import IntegrityError

_ARABIC_LETTER = "[ء-ي]"


def _fold(text: str) -> str:
    """One spelling for the variants people type: أ/إ/آ -> ا, ة -> ه, ى -> ي."""
    text = re.sub("[أإآ]", "ا", text or "").replace("ة", "ه").replace("ى", "ي")
    return " ".join(text.split())


def _whole_word(needle: str, haystack: str) -> bool:
    return re.search(f"(?<!{_ARABIC_LETTER}){re.escape(needle)}(?!{_ARABIC_LETTER})", haystack) is not None


@router.get("/locations")
def locations(db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin)):
    """Every city with its areas, each area with its other names and how many ads it holds."""
    Index = models.AdSearchIndex
    ads_per_region = dict(db.query(Index.region_id, func.count(Index.ad_id)).filter(Index.region_id.isnot(None)).group_by(Index.region_id).all())
    ads_per_city = dict(db.query(Index.city_id, func.count(Index.ad_id)).filter(Index.city_id.isnot(None)).group_by(Index.city_id).all())
    aliases = {}
    for alias in db.query(models.RegionAlias).all():
        aliases.setdefault(alias.region_id, []).append({"id": alias.id, "name": alias.alias_name})
    regions = {}
    for region in db.query(models.Region).order_by(models.Region.name_ar).all():
        regions.setdefault(region.city_id, []).append({
            "id": region.id, "name_ar": region.name_ar, "name_en": region.name_en,
            "ads": ads_per_region.get(region.id, 0), "aliases": aliases.get(region.id, []),
        })
    return [
        {"id": city.id, "name_ar": city.name_ar, "name_en": city.name_en, "ads": ads_per_city.get(city.id, 0), "regions": regions.get(city.id, [])}
        for city in db.query(models.City).order_by(models.City.id).all()
    ]


class RegionCreate(BaseModel):
    city_id: int
    name_ar: str
    name_en: str


@router.post("/regions", status_code=201)
def create_region(body: RegionCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin)):
    """Adds an area to a city.

    Refused when the name is already an area of that city in another spelling, or when it sits
    inside another area's name (or the reverse): an area called "أدر" once swallowed every ad
    that said "بادر", so overlapping names are not allowed in.
    """
    name_ar, name_en = " ".join(body.name_ar.split()), " ".join(body.name_en.split())
    if len(name_ar) < 3 or not name_en:
        raise HTTPException(status_code=400, detail="اكتب اسم المنطقة بالعربية (3 أحرف على الأقل) وبالإنجليزية.")
    city = db.query(models.City).filter(models.City.id == body.city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="المدينة غير موجودة.")
    folded = _fold(name_ar)
    if folded == _fold(city.name_ar):
        raise HTTPException(status_code=400, detail="هذا اسم المدينة نفسها.")
    for region in db.query(models.Region).filter(models.Region.city_id == city.id).all():
        other = _fold(region.name_ar)
        if other == folded:
            raise HTTPException(status_code=409, detail=f"المنطقة موجودة مسبقاً باسم «{region.name_ar}».")
        if _whole_word(folded, other) or _whole_word(other, folded):
            raise HTTPException(status_code=409, detail=f"الاسم يتداخل مع المنطقة «{region.name_ar}». اختر اسماً أوضح أو أضفه كاسم بديل لها.")
    region = models.Region(city_id=city.id, name_ar=name_ar, name_en=name_en)
    db.add(region)
    db.commit()
    db.refresh(region)
    return {"id": region.id, "name_ar": region.name_ar, "name_en": region.name_en, "ads": 0, "aliases": []}


class AliasCreate(BaseModel):
    name: str


@router.post("/regions/{region_id}/aliases", status_code=201)
def create_alias(region_id: int, body: AliasCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin)):
    """Adds another name people use for an area ("خريبة السوق" for "خربة السوق")."""
    name = " ".join(body.name.split())
    if len(name) < 3:
        raise HTTPException(status_code=400, detail="الاسم البديل قصير جداً.")
    region = db.query(models.Region).filter(models.Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="المنطقة غير موجودة.")
    folded = _fold(name)
    if any(_fold(other.name_ar) == folded for other in db.query(models.Region).all()):
        raise HTTPException(status_code=409, detail="هذا الاسم هو اسم منطقة موجودة.")
    if any(_fold(city.name_ar) == folded for city in db.query(models.City).all()):
        raise HTTPException(status_code=409, detail="هذا الاسم هو اسم مدينة.")
    alias = models.RegionAlias(region_id=region.id, alias_name=name)
    db.add(alias)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="هذا الاسم البديل مستخدم من قبل.")
    db.refresh(alias)
    return {"id": alias.id, "name": alias.alias_name}


@router.delete("/aliases/{alias_id}", status_code=204)
def delete_alias(alias_id: int, db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin)):
    alias = db.query(models.RegionAlias).filter(models.RegionAlias.id == alias_id).first()
    if not alias:
        raise HTTPException(status_code=404, detail="الاسم البديل غير موجود.")
    db.delete(alias)
    db.commit()


# ---------------------------------------------------------------------------
# Requests: Facebook posts from people looking for a property
# ---------------------------------------------------------------------------
SEEKER_STATUSES = {"new", "commented", "ignored"}


def _group_names(db: Session) -> dict:
    """Facebook group id -> the name it was saved under."""
    names = {}
    for group in db.query(models.SavedGroup).all():
        match = re.search(r"groups/([^/?#]+)", group.url or "")
        if match:
            names[match.group(1)] = group.name
    return names


@router.get("/seekers")
def seekers(
    status: str = "new",
    deal: str = "",
    q: str = "",
    page: int = 1,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin),
):
    """Posts from people looking for a property, newest first, with the link to each post."""
    Post = models.SeekerPost
    limit = max(1, min(limit, 100))
    query = db.query(Post)
    if status in SEEKER_STATUSES:
        query = query.filter(Post.status == status)
    if deal in ("rent", "sale"):
        query = query.filter(Post.deal == deal)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(Post.text.ilike(like), Post.location.ilike(like), Post.author.ilike(like)))
    total = query.count()
    rows = query.order_by(Post.created_at.desc()).offset((max(page, 1) - 1) * limit).limit(limit).all()
    counts = dict(db.query(Post.status, func.count(Post.id)).group_by(Post.status).all())
    groups = _group_names(db)

    def group_of(url):
        match = re.search(r"groups/([^/?#]+)", url or "")
        return groups.get(match.group(1)) if match else None

    return {
        "total": total,
        "counts": {name: counts.get(name, 0) for name in SEEKER_STATUSES},
        "items": [
            {
                "id": row.id, "post_url": row.post_url, "author": row.author, "text": row.text, "kind": row.kind, "deal": row.deal,
                "location": row.location, "posted_at": row.posted_at, "status": row.status, "group": group_of(row.post_url),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }


class SeekerStatusUpdate(BaseModel):
    status: str


@router.patch("/seekers/{post_id}")
def update_seeker(post_id: int, body: SeekerStatusUpdate, db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin)):
    """Marks a request as answered ("commented"), ignored, or new again."""
    if body.status not in SEEKER_STATUSES:
        raise HTTPException(status_code=400, detail="Unknown status")
    post = db.query(models.SeekerPost).filter(models.SeekerPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Request not found")
    post.status = body.status
    db.commit()
    return {"id": post.id, "status": post.status}
