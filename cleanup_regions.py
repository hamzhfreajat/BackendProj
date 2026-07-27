import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy import func

def get_canonical_name(names):
    # Prefer names with ?, ?, ?
    for n in names:
        if '?' in n or '?' in n or '?' in n:
            return n
    return names[0]

async def main():
    db = SessionLocal()
    with open('region_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Exact Duplicates
    deleted_exact = 0
    for k, v in data['exact_duplicates'].items():
        v.sort(key=lambda x: x['id'])
        canonical_id = v[0]['id']
        to_delete = [r['id'] for r in v[1:]]
        if to_delete:
            deleted_exact += db.query(models.Region).filter(models.Region.id.in_(to_delete)).delete(synchronize_session=False)

    print(f'Deleted {deleted_exact} exact duplicate regions.')

    # 2. Near Duplicates
    updated_ads_count = 0
    deleted_near = 0
    
    modified_ad_ids = set()

    for k, v in data['normalized_duplicates'].items():
        names = list(set([r['name'] for r in v]))
        canonical_name = get_canonical_name(names)
        
        # Determine IDs to delete (any region ID not matching the canonical name)
        # Actually, let's just keep the lowest ID of the canonical name
        canonical_candidates = [r for r in v if r['name'] == canonical_name]
        canonical_candidates.sort(key=lambda x: x['id'])
        if not canonical_candidates:
            canonical_candidates = v
            canonical_candidates.sort(key=lambda x: x['id'])
            canonical_name = canonical_candidates[0]['name']
            
        canonical_id = canonical_candidates[0]['id']
        to_delete = [r['id'] for r in v if r['id'] != canonical_id]
        
        if to_delete:
            deleted_near += db.query(models.Region).filter(models.Region.id.in_(to_delete)).delete(synchronize_session=False)
            
        # Update Ads
        for bad_name in names:
            if bad_name == canonical_name: continue
            
            # Find ads ending with ', bad_name' or exactly 'bad_name'
            ads = db.query(models.Ad).filter(
                (models.Ad.location.endswith(f', {bad_name}')) | 
                (models.Ad.location == bad_name)
            ).all()
            
            for ad in ads:
                if ad.location == bad_name:
                    ad.location = canonical_name
                else:
                    parts = ad.location.split(', ')
                    parts[-1] = canonical_name
                    ad.location = ', '.join(parts)
                modified_ad_ids.add(ad.id)
                updated_ads_count += 1
                
    db.commit()
    print(f'Deleted {deleted_near} near duplicate regions.')
    print(f'Updated {updated_ads_count} Ad locations.')
    
    # 3. Enqueue ARQ jobs for Elasticsearch
    if modified_ad_ids:
        try:
            from arq import create_pool
            from arq.connections import RedisSettings
            
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            if redis_url.startswith('redis://'):
                parts = redis_url.replace('redis://', '').split('/')
                host_port = parts[0].split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                db_num = int(parts[1]) if len(parts) > 1 else 0
                
                pool = await create_pool(RedisSettings(host=host, port=port, database=db_num))
                
                ads_to_sync = db.query(models.Ad).filter(models.Ad.id.in_(list(modified_ad_ids))).all()
                for ad in ads_to_sync:
                    # simplistic serialization
                    ad_dict = {
                        "id": ad.id,
                        "title": ad.title,
                        "description": ad.description,
                        "price": float(ad.price) if ad.price else None,
                        "location": ad.location,
                        "category_id": ad.category_id,
                        "image_url": ad.image_url,
                        "is_hot": ad.is_hot,
                        "created_at": ad.created_at.isoformat() if hasattr(ad, 'created_at') and ad.created_at else None
                    }
                    await pool.enqueue_job('sync_ad_to_elasticsearch', ad_dict)
                print(f'Successfully enqueued {len(ads_to_sync)} ES sync tasks.')
        except Exception as e:
            print(f'Could not enqueue ARQ jobs automatically: {e}')

if __name__ == '__main__':
    asyncio.run(main())
