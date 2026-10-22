import os
import asyncio
from arq.connections import RedisSettings
from arq.cron import cron
from database import SessionLocal
import models
import aiohttp
import os
from datetime import datetime, timedelta, timezone

async def process_telemetry_batch(ctx, batch):
    db = SessionLocal()
    try:
        events_to_insert = []
        for event in batch:
            events_to_insert.append(
                models.TelemetryEvent(
                    event_name=event.get('event_name'),
                    user_id=event.get('user_id'),
                    screen=event.get('screen'),
                    metadata_json=event.get('metadata_json'),
                    timestamp=event.get('timestamp') or datetime.utcnow(),
                    ip_address=event.get('ip_address')
                )
            )
        
        if events_to_insert:
            db.bulk_save_objects(events_to_insert)
            db.commit()
            print(f"Successfully processed {len(events_to_insert)} telemetry events.")
    except Exception as e:
        print(f"Error processing telemetry batch: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

async def sync_ad_to_elasticsearch(ctx, ad_dict):
    try:
        search_service_url = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8000")
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{search_service_url}/api/internal/index", json={"ad": ad_dict}) as response:
                if response.status != 200:
                    text = await response.text()
                    print(f"Error syncing ad {ad_dict.get('id')}: {text}")
    except Exception as e:
        print(f"Error in sync_ad_to_elasticsearch task: {e}")

async def delete_ad_from_elasticsearch(ctx, ad_id):
    try:
        search_service_url = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8000")
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.delete(f"{search_service_url}/api/internal/index/{ad_id}") as response:
                if response.status != 200:
                    text = await response.text()
                    print(f"Error deleting ad {ad_id}: {text}")
    except Exception as e:
        print(f"Error in delete_ad_from_elasticsearch task: {e}")

# --- Ad owner features (ad_insights.py) ---

AMMAN_TZ = timezone(timedelta(hours=3))  # Jordan has no daylight saving since 2022

async def flush_ad_daily_stats(ctx):
    import ad_insights
    await asyncio.to_thread(ad_insights.flush_daily_stats)

async def auto_republish_ads(ctx):
    import ad_insights
    await asyncio.to_thread(ad_insights.run_auto_republish)

async def daily_ad_reports(ctx):
    import ad_insights
    return await ad_insights.generate_daily_reports()

class WorkerSettings:
    functions = [process_telemetry_batch, sync_ad_to_elasticsearch, delete_ad_from_elasticsearch, daily_ad_reports]
    cron_jobs = [
        cron(flush_ad_daily_stats, minute=set(range(0, 60, 5)), run_at_startup=True),
        cron(auto_republish_ads, minute={2, 17, 32, 47}),
        # 06:30 Amman time: yesterday's numbers are final and owners are waking up
        cron(daily_ad_reports, hour={6}, minute={30}, timeout=3600),
    ]
    # Cron hours above are Amman time, whatever the server clock says
    timezone = AMMAN_TZ
    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", None)
    )
