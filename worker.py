import os
import asyncio
from arq.connections import RedisSettings
from database import SessionLocal
import models
from datetime import datetime

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
                    timestamp=event.get('timestamp') or datetime.utcnow()
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

class WorkerSettings:
    functions = [process_telemetry_batch]
    redis_settings = RedisSettings(host=os.getenv("REDIS_HOST", "redis"), port=6379)
