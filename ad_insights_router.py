"""Owner endpoints for daily auto-republish and the morning ad report (see ad_insights.py)."""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

import ad_insights
import auth
import models
from database import get_db

router = APIRouter(tags=["Ad insights"])

HISTORY_DAYS = 14


class EnabledRequest(BaseModel):
    enabled: bool


def _own_ad(db: Session, ad_id: int, user: models.User) -> models.Ad:
    ad = db.query(models.Ad).filter(models.Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    if ad.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your ad")
    return ad


def _report_out(r: Optional[models.AdDailyReport]):
    if not r:
        return None
    return {
        "report_date": r.report_date.isoformat(),
        "health_score": r.health_score,
        "summary": r.summary,
        "tips": r.tips or [],
        "stats": r.stats or {},
        "by_ai": bool(r.ai_model),
    }


def _today_pending(ad_id: int) -> dict:
    """Counts from today that are still in Redis (the worker saves them every 5 minutes)."""
    r = ad_insights._redis()
    out = {m: 0 for m in ad_insights.METRICS}
    if r is None:
        return out
    try:
        key = f"{ad_insights.REDIS_KEY_PREFIX}{ad_insights.amman_today().isoformat()}"
        fields = [f"{ad_id}:{m}" for m in ad_insights.METRICS]
        for m, v in zip(ad_insights.METRICS, r.hmget(key, fields)):
            out[m] = int(v or 0)
    except Exception:
        pass
    return out


@router.post("/api/my-ads/{ad_id}/auto-republish")
def set_auto_republish(ad_id: int, req: EnabledRequest,
                       current_user: models.User = Depends(auth.get_current_user),
                       db: Session = Depends(get_db)):
    """Turns daily auto-republish on or off for one ad."""
    ad = _own_ad(db, ad_id, current_user)
    ad.auto_republish = req.enabled
    db.commit()
    return {"status": "success", "auto_republish": ad.auto_republish}


@router.post("/api/my-ads/auto-republish-all", dependencies=[Depends(auth.get_rate_limiter(10, 60))])
def set_auto_republish_all(req: EnabledRequest,
                           current_user: models.User = Depends(auth.get_current_user),
                           db: Session = Depends(get_db)):
    """Turns daily auto-republish on or off for every ad of the user."""
    count = (
        db.query(models.Ad)
        .filter(models.Ad.user_id == current_user.id)
        .update({"auto_republish": req.enabled}, synchronize_session=False)
    )
    db.commit()
    return {"status": "success", "updated": count, "auto_republish": req.enabled}


@router.get("/api/my-ads/{ad_id}/insights")
def get_ad_insights(ad_id: int,
                    current_user: models.User = Depends(auth.get_current_user),
                    db: Session = Depends(get_db)):
    """The latest morning report of one ad plus its numbers for the last 14 days."""
    ad = _own_ad(db, ad_id, current_user)
    today = ad_insights.amman_today()
    start = today - timedelta(days=HISTORY_DAYS - 1)

    rows = {
        s.day: s for s in db.query(models.AdDailyStat)
        .filter(models.AdDailyStat.ad_id == ad.id, models.AdDailyStat.day >= start).all()
    }
    pending = _today_pending(ad.id)
    history = []
    for i in range(HISTORY_DAYS):
        d = start + timedelta(days=i)
        s = rows.get(d)
        day = {m: (getattr(s, m) if s else 0) for m in ad_insights.METRICS}
        if d == today:
            day = {m: day[m] + pending[m] for m in ad_insights.METRICS}
        day["contacts"] = sum(day[m] for m in ad_insights.CONTACT_METRICS)
        history.append({"day": d.isoformat(), **day})

    report = (
        db.query(models.AdDailyReport)
        .filter(models.AdDailyReport.ad_id == ad.id)
        .order_by(models.AdDailyReport.report_date.desc())
        .first()
    )
    last_top = ad.last_republished_at or ad.created_at
    return {
        "ad_id": ad.id,
        "auto_republish": bool(ad.auto_republish),
        "next_republish_at": (last_top + ad_insights.REPUBLISH_EVERY).isoformat() if ad.auto_republish and last_top else None,
        "report": _report_out(report),
        "history": history,
    }


@router.get("/api/my-ads/reports/daily")
def get_my_daily_reports(current_user: models.User = Depends(auth.get_current_user),
                         db: Session = Depends(get_db)):
    """The newest morning report for each of the user's ads, weakest ads first."""
    latest = (
        db.query(func.max(models.AdDailyReport.report_date))
        .filter(models.AdDailyReport.user_id == current_user.id)
        .scalar()
    )
    if not latest:
        return {"report_date": None, "totals": None, "ads": []}
    reports = (
        db.query(models.AdDailyReport, models.Ad)
        .join(models.Ad, models.Ad.id == models.AdDailyReport.ad_id)
        .filter(models.AdDailyReport.user_id == current_user.id, models.AdDailyReport.report_date == latest)
        .order_by(models.AdDailyReport.health_score.asc())
        .all()
    )
    totals = {k: 0 for k in ("impressions", "views", "contacts", "favorites")}
    ads = []
    for r, ad in reports:
        y = (r.stats or {}).get("yesterday", {})
        for k in totals:
            totals[k] += int(y.get(k, 0) or 0)
        ads.append({
            "ad_id": ad.id,
            "title": ad.title,
            "image_url": (ad.image_urls or [None])[0] or ad.image_url,
            "auto_republish": bool(ad.auto_republish),
            **_report_out(r),
        })
    return {"report_date": latest.isoformat(), "totals": totals, "ads": ads}


@router.put("/api/users/me/daily-report")
def set_daily_report_notifications(req: EnabledRequest,
                                   current_user: models.User = Depends(auth.get_current_user),
                                   db: Session = Depends(get_db)):
    """Turns the morning report push notification on or off. Reports are still written."""
    current_user.daily_report_enabled = req.enabled
    db.commit()
    return {"status": "success", "daily_report_enabled": req.enabled}


@router.post("/api/admin/ad-reports/run")
async def run_daily_reports_now(request: Request, current_admin: models.User = Depends(auth.get_current_admin)):
    """Admin: queue the morning report job now (it skips ads that already have today's report)."""
    pool = getattr(request.app.state, "arq_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Worker queue is not available")
    job = await pool.enqueue_job("daily_ad_reports")
    return {"status": "queued", "job_id": job.job_id if job else None}
