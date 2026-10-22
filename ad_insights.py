"""Daily numbers, daily auto-republish and the morning AI report for each ad.

How the pieces fit:
- The API calls record_ad_event() when an ad is shown, opened, called, etc. Counts go to a
  Redis hash per day and the worker moves them into ad_daily_stats every few minutes.
- The worker republishes ads whose owner turned on auto_republish, once every 24 hours.
- Every morning the worker writes one AdDailyReport per live ad: yesterday's numbers, a
  comparison with similar ads, a 0-100 health score and advice written by the AI.

The worker jobs run in the single ARQ process (see worker.py), not in the 4 API processes.
"""
import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, or_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

import models
from database import SessionLocal

try:
    from zoneinfo import ZoneInfo
    AMMAN_TZ = ZoneInfo("Asia/Amman")
except Exception:  # no tz database on this machine; Jordan has stayed on UTC+3 since 2022
    AMMAN_TZ = timezone(timedelta(hours=3))

METRICS = ("impressions", "views", "calls", "whatsapp", "chats", "favorites")
CONTACT_METRICS = ("calls", "whatsapp", "chats")
REDIS_KEY_PREFIX = "ad_daily:"
REPUBLISH_EVERY = timedelta(hours=24)
# One AI call covers all of a user's ads, up to this many (the rest get rule-based advice)
AI_ADS_PER_USER = int(os.getenv("AD_REPORT_AI_ADS_PER_USER", "10"))
# Safety cap on AI calls per morning
AI_MAX_USERS = int(os.getenv("AD_REPORT_AI_MAX_USERS", "500"))


def amman_today() -> date:
    return datetime.now(AMMAN_TZ).date()


def _redis():
    try:
        from auth import redis_client
        return redis_client
    except Exception:
        return None


def _is_live_filter(now: datetime):
    """SQL conditions for an ad the public can see (same idea as _compute_ad_status == "Active")."""
    return (
        models.Ad.is_published == True,
        models.Ad.is_sold == False,
        models.Ad.is_paused == False,
        models.Ad.is_rejected == False,
        or_(models.Ad.expires_at == None, models.Ad.expires_at > now),
    )


def _is_organic_filter():
    """Ads posted by a real user in the app, not imported from Facebook."""
    return (
        models.Ad.user_id != None,
        models.Ad.source_url == None,
        or_(models.Ad.source_type == None, models.Ad.source_type == models.SourceType.ORGANIC_USER),
    )


# ---------------------------------------------------------------------------
# Recording events
# ---------------------------------------------------------------------------

def record_ad_event(ad_ids, metric: str, amount: int = 1, who: str | None = None):
    """Counts something that happened to one or more ads today. Never raises.

    who: the user id or IP. When given, the same person is counted once per ad per day,
    so a buyer who taps "call" five times is one contact.
    """
    try:
        _record(ad_ids, metric, amount, who)
    except Exception as e:
        print(f"[ad_insights] could not record {metric}: {e}")


def _record(ad_ids, metric, amount, who):
    if metric not in METRICS:
        return
    if isinstance(ad_ids, int):
        ad_ids = [ad_ids]
    ad_ids = [int(a) for a in ad_ids if a]
    if not ad_ids:
        return
    today = amman_today().isoformat()
    key = f"{REDIS_KEY_PREFIX}{today}"
    r = _redis()
    if r is not None:
        try:
            if who:
                ad_ids = [a for a in ad_ids if r.set(f"ad_daily_seen:{today}:{a}:{metric}:{who}", 1, nx=True, ex=26 * 3600)]
                if not ad_ids:
                    return
            pipe = r.pipeline()
            for ad_id in ad_ids:
                pipe.hincrby(key, f"{ad_id}:{metric}", amount)
            pipe.expire(key, 3 * 24 * 3600)
            pipe.execute()
            return
        except Exception as e:
            print(f"[ad_insights] Redis unavailable, writing stats directly: {e}")
    _upsert_counts(amman_today(), {(a, metric): amount for a in ad_ids})


def _upsert_counts(day: date, counts: dict):
    """counts: {(ad_id, metric): n}. Adds to the existing row for that ad and day."""
    rows = {}
    for (ad_id, metric), n in counts.items():
        rows.setdefault(ad_id, {m: 0 for m in METRICS})[metric] += n
    if not rows:
        return
    db = SessionLocal()
    try:
        existing = {i for (i,) in db.query(models.Ad.id).filter(models.Ad.id.in_(list(rows))).all()}
        values = [{"ad_id": a, "day": day, **m} for a, m in rows.items() if a in existing]
        if values:
            stmt = pg_insert(models.AdDailyStat).values(values)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_ad_daily_stats_ad_day",
                set_={m: getattr(models.AdDailyStat, m) + getattr(stmt.excluded, m) for m in METRICS},
            )
            db.execute(stmt)
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def flush_daily_stats() -> int:
    """Moves the Redis counters into ad_daily_stats. Returns how many counters were saved."""
    r = _redis()
    if r is None:
        return 0
    saved = 0
    for key in r.scan_iter(match=f"{REDIS_KEY_PREFIX}????-??-??"):
        day = date.fromisoformat(key[len(REDIS_KEY_PREFIX):])
        # Rename first so new events go to a fresh hash while we read this one
        work_key = f"{key}:flushing:{uuid.uuid4().hex}"
        try:
            r.rename(key, work_key)
        except Exception:
            continue  # key vanished between scan and rename
        data = r.hgetall(work_key)
        counts = {}
        for field, n in data.items():
            try:
                ad_id, metric = field.split(":", 1)
                counts[(int(ad_id), metric)] = int(n)
            except ValueError:
                continue
        try:
            _upsert_counts(day, counts)
            r.delete(work_key)
            saved += len(counts)
        except Exception as e:
            print(f"[ad_insights] could not save daily stats for {day}, keeping them in Redis: {e}")
            pipe = r.pipeline()
            for field, n in data.items():
                pipe.hincrby(key, field, int(n))
            pipe.delete(work_key)
            pipe.execute()
    return saved


# ---------------------------------------------------------------------------
# Daily auto-republish
# ---------------------------------------------------------------------------

def run_auto_republish() -> int:
    """Moves auto-republish ads back to the top, at most once every 24 hours. Returns the count."""
    from search_service import SearchService

    now = datetime.utcnow()
    due = now - REPUBLISH_EVERY
    db = SessionLocal()
    try:
        # One UPDATE claims the ads, so two runs can never republish the same ad twice
        stmt = (
            update(models.Ad)
            .where(
                models.Ad.auto_republish == True,
                *_is_live_filter(now),
                *_is_organic_filter(),
                func.coalesce(models.Ad.last_republished_at, models.Ad.created_at) <= due,
            )
            .values(
                last_republished_at=now,
                created_at=now,  # listings are ordered by this date
                updated_at=now,
                # The owner does not need the "you can republish now" reminder
                republish_notification_sent=True,
            )
            .returning(models.Ad.id)
            .execution_options(synchronize_session=False)
        )
        ids = [row[0] for row in db.execute(stmt).fetchall()]
        db.commit()
        for ad in db.query(models.Ad).filter(models.Ad.id.in_(ids)).all() if ids else []:
            try:
                SearchService.sync_ad_to_search_index(db, ad)
            except Exception as e:
                db.rollback()
                print(f"[auto-republish] search index not refreshed for ad {ad.id}: {e}")
        if ids:
            print(f"[auto-republish] moved {len(ids)} ads to the top")
        return len(ids)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Morning report
# ---------------------------------------------------------------------------

def _sum_stats(db, ad_ids, start: date, end: date) -> dict:
    """{ad_id: {metric: total}} for days start..end inclusive."""
    if not ad_ids:
        return {}
    cols = [func.coalesce(func.sum(getattr(models.AdDailyStat, m)), 0) for m in METRICS]
    rows = (
        db.query(models.AdDailyStat.ad_id, *cols)
        .filter(models.AdDailyStat.ad_id.in_(ad_ids), models.AdDailyStat.day >= start, models.AdDailyStat.day <= end)
        .group_by(models.AdDailyStat.ad_id)
        .all()
    )
    return {r[0]: dict(zip(METRICS, (int(v) for v in r[1:]))) for r in rows}


def _empty():
    return {m: 0 for m in METRICS}


def _contacts(s: dict) -> int:
    return sum(s.get(m, 0) for m in CONTACT_METRICS)


def _rate(part, whole):
    return round(part / whole, 4) if whole else None


def _category_benchmarks(ads, week: dict) -> dict:
    """Average weekly numbers per live ad in each category (only categories with 3+ ads)."""
    groups = {}
    for ad in ads:
        groups.setdefault(ad.category_id, []).append(week.get(ad.id, _empty()))
    out = {}
    for cat_id, stats in groups.items():
        if len(stats) < 3:
            continue
        n = len(stats)
        imp = sum(s["impressions"] for s in stats)
        views = sum(s["views"] for s in stats)
        contacts = sum(_contacts(s) for s in stats)
        out[cat_id] = {
            "ads": n,
            "avg_views_7d": round(views / n, 1),
            "avg_contacts_7d": round(contacts / n, 2),
            "avg_open_rate": _rate(views, imp),
            "avg_contact_rate": _rate(contacts, views),
        }
    return out


def build_ad_facts(ad, yesterday: dict, week: dict, prev_week: dict, bench: dict | None, now: datetime) -> dict:
    """Everything the report says about one ad, as plain numbers."""
    photos = len(ad.image_urls or [])
    desc_len = len((ad.description or "").strip())
    live_since = ad.original_created_at or ad.created_at
    last_top = ad.last_republished_at or ad.created_at
    return {
        "yesterday": {**yesterday, "contacts": _contacts(yesterday)},
        "last_7_days": {**week, "contacts": _contacts(week)},
        "previous_7_days": {**prev_week, "contacts": _contacts(prev_week)},
        "open_rate_7d": _rate(week["views"], week["impressions"]),      # opened / shown
        "contact_rate_7d": _rate(_contacts(week), week["views"]),       # contacted / opened
        "category_average": bench,
        "listing": {
            "photos": photos,
            "has_video": bool(ad.video_url),
            "title_length": len((ad.title or "").strip()),
            "description_length": desc_len,
            "price": float(ad.price) if ad.price is not None else None,
            "price_vs_market": ad.market_price_status,
            "market_average_price": float(ad.market_average_price) if ad.market_average_price else None,
            "price_deviation_pct": float(ad.deviation_pct) * 100 if ad.deviation_pct is not None else None,
            "days_live": (now - live_since).days if live_since else None,
            "hours_since_top": int((now - last_top).total_seconds() // 3600) if last_top else None,
            "auto_republish": bool(ad.auto_republish),
            "is_boosted": bool(ad.is_boosted),
            "rating": float(ad.rating_avg) if ad.rating_avg is not None else None,
            "reviews": ad.reviews_count or 0,
        },
    }


def health_score(facts: dict) -> int:
    """0-100. Half for how complete the listing is, half for how it does against similar ads."""
    l = facts["listing"]
    q = 0
    q += 15 if l["photos"] >= 5 else 10 if l["photos"] >= 3 else 5 if l["photos"] >= 1 else 0
    q += 10 if l["description_length"] >= 200 else 6 if l["description_length"] >= 80 else 2
    q += 10 if l["price"] else 0
    q += {"BELOW_MARKET": 10, "NOT_BELOW_MARKET": 6}.get(l["price_vs_market"], 6)
    q += 5 if l["has_video"] else 0

    bench = facts["category_average"]
    week = facts["last_7_days"]
    if bench and bench["avg_views_7d"] > 0:
        p = min(week["views"] / bench["avg_views_7d"], 1.5) / 1.5 * 25
    else:
        p = 12.5
    if bench and bench["avg_contact_rate"] and facts["contact_rate_7d"] is not None:
        p += min(facts["contact_rate_7d"] / bench["avg_contact_rate"], 1.5) / 1.5 * 25
    elif week["contacts"] > 0:
        p += 20
    else:
        p += 10
    return int(round(min(100, q + p)))


def rule_tips(facts: dict) -> list:
    """Advice that does not need the AI. Also the fallback when the AI is down."""
    l = facts["listing"]
    week = facts["last_7_days"]
    bench = facts["category_average"] or {}
    tips = []
    if l["photos"] < 5:
        tips.append({"text": f"إعلانك فيه {l['photos']} صور فقط. الإعلانات التي فيها 5 صور أو أكثر تحصل على اهتمام أكبر.", "action": "add_photos"})
    if l["description_length"] < 80:
        tips.append({"text": "الوصف قصير. أضف المساحة والمميزات والموقع بالتفصيل ليثق بك المشتري.", "action": "edit_description"})
    if not l["price"]:
        tips.append({"text": "أضف السعر. كثير من المشترين يتجاهلون الإعلانات بدون سعر.", "action": "edit_price"})
    elif l["price_vs_market"] == "NOT_BELOW_MARKET" and (l["price_deviation_pct"] or 0) > 10:
        tips.append({"text": f"سعرك أعلى من متوسط السوق بحوالي {round(l['price_deviation_pct'])}%. جرّب تخفيضاً بسيطاً.", "action": "edit_price"})
    if week["views"] >= 20 and facts["contact_rate_7d"] is not None and facts["contact_rate_7d"] < 0.02:
        tips.append({"text": "الناس تفتح إعلانك لكن قليل منهم يتواصل. راجع السعر وأضف صوراً أوضح.", "action": "edit_price"})
    if week["impressions"] >= 100 and facts["open_rate_7d"] is not None and bench.get("avg_open_rate") and facts["open_rate_7d"] < bench["avg_open_rate"] * 0.6:
        tips.append({"text": "إعلانك يظهر كثيراً لكن نادراً ما يُفتح. غيّر الصورة الأولى واجعل العنوان أوضح.", "action": "edit_title"})
    if not l["auto_republish"] and (l["hours_since_top"] or 0) >= 48:
        tips.append({"text": "مرّ أكثر من يومين على آخر ظهور لإعلانك في الأعلى. فعّل إعادة النشر التلقائية.", "action": "enable_auto_republish"})
    if not l["has_video"]:
        tips.append({"text": "أضف فيديو قصير للعقار، فهو يزيد ثقة المشتري.", "action": "add_video"})
    return tips[:3]


def _summary_fallback(facts: dict) -> str:
    y = facts["yesterday"]
    return f"أمس ظهر إعلانك {y['impressions']} مرة، وفتحه {y['views']} شخص، وتواصل معك {y['contacts']}."


def _ask_ai_json(prompt: str):
    """Gemini first, DeepSeek as the fallback (same as ai_router). Returns (data, model) or (None, None)."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            try:
                from google import genai as genai_new
                client = genai_new.Client(api_key=api_key)
                raw = client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text
            except ImportError:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                raw = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt).text
            return _parse_json(raw), "gemini-2.5-flash"
        except Exception as e:
            print(f"[ad-report] Gemini failed, trying DeepSeek: {e}")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        try:
            import openai
            client = openai.OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com", timeout=30.0)
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return _parse_json(resp.choices[0].message.content), "deepseek-chat"
        except Exception as e:
            print(f"[ad-report] DeepSeek failed: {e}")
    return None, None


def _parse_json(raw: str):
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


ALLOWED_ACTIONS = {
    "add_photos", "edit_description", "edit_title", "edit_price", "add_video",
    "enable_auto_republish", "republish", "boost", "none",
}


def _ai_advice(ads_with_facts: list):
    """One AI call for all of a user's ads. Returns ({ad_id: {"summary", "tips"}}, model)."""
    payload = []
    for ad, facts in ads_with_facts:
        payload.append({
            "ad_id": ad.id,
            "title": (ad.title or "")[:120],
            "description": (ad.description or "")[:400],
            "category": ad.category.name if ad.category else None,
            "location": ad.location,
            "facts": facts,
        })
    prompt = f"""
أنت مستشار مبيعات لسوق إعلانات مبوبة في الأردن. لكل إعلان أدناه أرقام أمس وآخر 7 أيام والـ 7 أيام التي قبلها،
ومتوسط الإعلانات المشابهة في نفس الفئة (category_average)، وتفاصيل الإعلان نفسه.

معاني الأرقام: impressions = ظهر في القائمة، views = فُتح الإعلان، contacts = اتصال أو واتساب أو محادثة أو إظهار الرقم،
favorites = أُضيف للمفضلة، open_rate_7d = views/impressions، contact_rate_7d = contacts/views.

اكتب لكل إعلان:
- "summary": جملتان بالعربية البسيطة تشرحان سلوك الزوار أمس مقارنة بالأسبوع الماضي وبالإعلانات المشابهة. استخدم الأرقام. لا تخترع أرقاماً غير موجودة.
- "tips": من 1 إلى 3 نصائح عملية ومحددة لهذا الإعلان بالذات، مرتبة حسب الأهمية. كل نصيحة {{"text": "...", "action": "..."}}
  حيث action واحد من: {sorted(ALLOWED_ACTIONS)}.
إذا كان الإعلان يعمل جيداً قل ذلك بوضوح ولا تختلق مشاكل.

الإعلانات:
{json.dumps(payload, ensure_ascii=False, default=str)}

أرجع JSON فقط بهذا الشكل:
{{"ads": [{{"ad_id": 1, "summary": "...", "tips": [{{"text": "...", "action": "edit_price"}}]}}]}}
"""
    data, model = _ask_ai_json(prompt)
    out = {}
    if not isinstance(data, dict):
        return out, None
    for item in data.get("ads", []):
        try:
            ad_id = int(item.get("ad_id"))
        except (TypeError, ValueError):
            continue
        tips = []
        for t in (item.get("tips") or [])[:3]:
            if isinstance(t, dict) and t.get("text"):
                action = t.get("action") if t.get("action") in ALLOWED_ACTIONS else "none"
                tips.append({"text": str(t["text"])[:300], "action": action})
        summary = str(item.get("summary") or "")[:600]
        if summary or tips:
            out[ad_id] = {"summary": summary, "tips": tips}
    return out, model


def build_daily_reports(report_date: date | None = None):
    """Writes the report for report_date (default: yesterday, Amman time).

    Slow (database + one AI call per user), so the worker runs it in a thread.
    Returns (summary, notifications to send).
    """
    flush_daily_stats()
    day = report_date or (amman_today() - timedelta(days=1))
    week_start = day - timedelta(days=6)
    prev_start, prev_end = day - timedelta(days=13), day - timedelta(days=7)
    now = datetime.utcnow()

    db = SessionLocal()
    written, ai_users, to_notify = 0, 0, []
    try:
        already = {i for (i,) in db.query(models.AdDailyReport.ad_id).filter(models.AdDailyReport.report_date == day).all()}
        ads = db.query(models.Ad).filter(*_is_live_filter(now), *_is_organic_filter()).all()
        ids = [a.id for a in ads]
        y_stats = _sum_stats(db, ids, day, day)
        w_stats = _sum_stats(db, ids, week_start, day)
        p_stats = _sum_stats(db, ids, prev_start, prev_end)
        benches = _category_benchmarks(ads, w_stats)

        by_user = {}
        for ad in ads:
            if ad.id in already:
                continue  # the job already ran today (restart): do not write it twice
            facts = build_ad_facts(ad, y_stats.get(ad.id, _empty()), w_stats.get(ad.id, _empty()),
                                   p_stats.get(ad.id, _empty()), benches.get(ad.category_id), now)
            by_user.setdefault(ad.user_id, []).append((ad, facts))

        for user_id, items in by_user.items():
            # Ask the AI about the ads people looked at most; the rest get rule-based advice
            items.sort(key=lambda x: x[1]["last_7_days"]["views"], reverse=True)
            advice, model = {}, None
            if ai_users < AI_MAX_USERS:
                try:
                    advice, model = _ai_advice(items[:AI_ADS_PER_USER])
                    ai_users += 1
                except Exception as e:
                    print(f"[ad-report] AI advice failed for user {user_id}: {e}")

            for ad, facts in items:
                a = advice.get(ad.id)
                db.add(models.AdDailyReport(
                    ad_id=ad.id,
                    user_id=user_id,
                    report_date=day,
                    health_score=health_score(facts),
                    stats=facts,
                    summary=(a or {}).get("summary") or _summary_fallback(facts),
                    tips=(a or {}).get("tips") or rule_tips(facts),
                    ai_model=model if a else None,
                ))
            try:
                db.commit()
                written += len(items)
            except Exception as e:  # another run wrote this user's reports first
                db.rollback()
                print(f"[ad-report] reports for user {user_id} not saved: {e}")
                continue

            owner = db.query(models.User).filter(models.User.id == user_id).first()
            if not owner or not owner.daily_report_enabled:
                continue
            views = sum(f["yesterday"]["views"] for _, f in items)
            contacts = sum(f["yesterday"]["contacts"] for _, f in items)
            if views == 0 and contacts == 0:
                continue  # nothing happened: the report is in the app, but no push
            to_notify.append({
                "target_user_id": user_id,
                "title": "تقرير إعلاناتك اليومي 📊",
                "body": f"أمس فتح {views} شخص إعلاناتك وتواصل معك {contacts}. اطّلع على النصائح لتحسين نتائجك.",
                "notification_type": "daily_ad_report",
                "reference_id": items[0][0].id if len(items) == 1 else None,
            })
    finally:
        db.close()
    summary = {"date": day.isoformat(), "reports": written, "ai_users": ai_users, "notified": len(to_notify)}
    return summary, to_notify


async def generate_daily_reports(report_date: date | None = None) -> dict:
    """Builds the morning reports and sends one push per owner."""
    import asyncio
    from notifications import send_personal_notification

    summary, to_notify = await asyncio.to_thread(build_daily_reports, report_date)
    for n in to_notify:
        try:
            await send_personal_notification(**n)
        except Exception as e:
            print(f"[ad-report] notification failed for user {n['target_user_id']}: {e}")
    print(f"[ad-report] {summary}")
    return summary
