from sqlalchemy.orm import Session
from sqlalchemy import text
from search_parser import QueryParserService
import json

# Global cache for location lookups to avoid N+1 queries during backfill
LOCATIONS_CACHE = {
    "regions": None,
    "cities": None
}

class SearchService:
    @staticmethod
    def search_properties(db: Session, raw_query: str, limit: int = 100):
        parsed = QueryParserService.parse(raw_query)
        
        # Base query combining TSVECTOR and Trigram fuzzy match
        base_sql = """
            SELECT ad_id, category_id, price, deal_type, property_type,
                   ts_rank_cd(search_vector, websearch_to_tsquery('simple', :query)) as rank,
                   similarity(search_text, :query) as sim_score
            FROM ad_search_index
            WHERE 1=1
              AND (search_vector @@ websearch_to_tsquery('simple', :query) 
                   OR search_text % :query)
        """
        
        params = {"query": parsed.normalized_query}

        # Apply Structured Filters
        if parsed.deal_type:
            base_sql += " AND deal_type = :deal_type"
            params["deal_type"] = parsed.deal_type
            
        if parsed.property_type:
            base_sql += " AND property_type = :property_type"
            params["property_type"] = parsed.property_type
            
        if parsed.bedrooms:
            base_sql += " AND bedrooms >= :bedrooms"
            params["bedrooms"] = parsed.bedrooms
            
        if parsed.max_price:
            base_sql += " AND price <= :max_price"
            params["max_price"] = parsed.max_price
            
        if parsed.min_price:
            base_sql += " AND price >= :min_price"
            params["min_price"] = parsed.min_price
            
        if parsed.build_area:
            base_sql += " AND build_area >= :build_area"
            params["build_area"] = parsed.build_area
            
        if parsed.furnished is not None:
            base_sql += " AND furnished = :furnished"
            params["furnished"] = parsed.furnished
            
        if parsed.location:
            base_sql += " AND search_text ILIKE :location"
            params["location"] = f"%{parsed.location}%"
            
        for idx, feat in enumerate(parsed.features):
            base_sql += f" AND search_text ILIKE :feature_{idx}"
            params[f"feature_{idx}"] = f"%{feat}%"


        # Ranking Logic
        base_sql += """
            ORDER BY 
                is_boosted DESC,
                is_hot DESC,
                ts_rank_cd(search_vector, websearch_to_tsquery('simple', :query)) DESC,
                similarity(search_text, :query) DESC,
                created_at DESC
            LIMIT :limit
        """
        params["limit"] = limit

        # Ensure Trigram similarity threshold is optimized for Arabic
        db.execute(text("SET pg_trgm.similarity_threshold = 0.25"))
        
        result = db.execute(text(base_sql), params)
        return [row.ad_id for row in result]
        
    @staticmethod
    def sync_ad_to_search_index(db: Session, ad, commit: bool = True):
        """Syncs an Ad to the ad_search_index table."""
        try:
            # Gather text components
            title = ad.title or ""
            desc = ad.description or ""
            loc = ad.location or ""
            cat_name = ad.category.name if ad.category else ""
            
            search_text = f"{title} {desc} {loc} {cat_name}"
            
            # Extract real estate details if available
            deal_type = None
            property_type = None
            bedrooms = None
            bathrooms = None
            furnished = None
            build_area = None
            floor_number = None
            attributes_jsonb = {}
            
            if ad.category:
                if 'بيع' in ad.category.name:
                    deal_type = "SALE"
                elif 'ايجار' in ad.category.name or 'إيجار' in ad.category.name:
                    deal_type = "RENT"
                    
            if ad.real_estate_detail:
                bathrooms = ad.real_estate_detail.bathrooms
                furnished = True if ad.real_estate_detail.furnished in ['مفروشة', 'مفروش', 'مفروش جزئياً', 'yes', 'true'] else False
                build_area = ad.real_estate_detail.build_area
                floor_number = None
                try:
                    if ad.real_estate_detail.floor and ad.real_estate_detail.floor.isdigit():
                        floor_number = int(ad.real_estate_detail.floor)
                except:
                    pass
                if ad.real_estate_detail.additional_features:
                    attributes_jsonb['features'] = ad.real_estate_detail.additional_features
            
            # Get linked tags and extract bedrooms
            if getattr(ad, 'linked_tags', None):
                tag_names = [t.name_ar for t in ad.linked_tags if hasattr(t, 'name_ar')] + [t.name for t in ad.linked_tags if hasattr(t, 'name')]
                tag_names = list(set(tag_names))
                search_text += " " + " ".join(tag_names)
                attributes_jsonb['tags'] = tag_names
                
                # Extract bedrooms from tags (e.g. "bedrooms:3")
                for tag in tag_names:
                    if tag.startswith("bedrooms:"):
                        try:
                            val = tag.split(":")[1]
                            if val == 'ستوديو':
                                bedrooms = 1
                            elif val.startswith('+'):
                                bedrooms = int(val[1:])
                            else:
                                bedrooms = int(val)
                        except:
                            pass
            
            # NLP Parsing for missing fields
            parsed = QueryParserService.parse(f"{title} {desc} {loc}")
            
            if not deal_type:
                deal_type = parsed.deal_type
                
            property_type = parsed.property_type
            
            if not bedrooms:
                # try ad.attributes directly before parsed
                ad_rooms = None
                if ad.attributes and isinstance(ad.attributes, dict):
                    ad_rooms = ad.attributes.get("rooms")
                bedrooms = ad_rooms or parsed.bedrooms
                
            if not build_area:
                build_area = parsed.build_area

            city_id = getattr(ad, 'city_id', None)
            region_id = getattr(ad, 'region_id', None)
            
            if not region_id and parsed.location:
                # Build cache if empty
                if LOCATIONS_CACHE["regions"] is None:
                    LOCATIONS_CACHE["regions"] = db.execute(text("SELECT id, city_id, name_ar FROM regions")).fetchall()
                    LOCATIONS_CACHE["cities"] = db.execute(text("SELECT id, name_ar FROM cities")).fetchall()
                
                # Fast in-memory lookup
                loc_lower = parsed.location.lower()
                for r_id, r_cid, r_name in LOCATIONS_CACHE["regions"]:
                    if r_name and loc_lower in r_name.lower():
                        region_id = r_id
                        city_id = r_cid
                        break
                
                if not region_id:
                    for c_id, c_name in LOCATIONS_CACHE["cities"]:
                        if c_name and loc_lower in c_name.lower():
                            city_id = c_id
                            break
            
            upsert_sql = """
                INSERT INTO ad_search_index (
                    ad_id, category_id, city_id, region_id, deal_type, property_type, price,
                    bedrooms, bathrooms, furnished, build_area, floor_number, 
                    is_hot, is_boosted, attributes_jsonb, search_text, search_vector, updated_at
                )
                VALUES (
                    :ad_id, :category_id, :city_id, :region_id, :deal_type, :property_type, :price,
                    :bedrooms, :bathrooms, :furnished, :build_area, :floor_number,
                    :is_hot, :is_boosted, :attributes_jsonb, :search_text,
                    to_tsvector('simple', :search_text), CURRENT_TIMESTAMP
                )
                ON CONFLICT (ad_id) DO UPDATE SET
                    category_id = EXCLUDED.category_id,
                    city_id = EXCLUDED.city_id,
                    region_id = EXCLUDED.region_id,
                    deal_type = EXCLUDED.deal_type,
                    property_type = EXCLUDED.property_type,
                    price = EXCLUDED.price,
                    bedrooms = EXCLUDED.bedrooms,
                    bathrooms = EXCLUDED.bathrooms,
                    furnished = EXCLUDED.furnished,
                    build_area = EXCLUDED.build_area,
                    floor_number = EXCLUDED.floor_number,
                    is_hot = EXCLUDED.is_hot,
                    is_boosted = EXCLUDED.is_boosted,
                    attributes_jsonb = EXCLUDED.attributes_jsonb,
                    search_text = EXCLUDED.search_text,
                    search_vector = EXCLUDED.search_vector,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            params = {
                "ad_id": ad.id,
                "category_id": ad.category_id,
                "city_id": city_id,
                "region_id": region_id,
                "deal_type": deal_type,
                "property_type": property_type,
                "price": ad.price,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "furnished": furnished,
                "build_area": build_area,
                "floor_number": floor_number,
                "is_hot": ad.is_hot,
                "is_boosted": ad.is_boosted,
                "attributes_jsonb": json.dumps(attributes_jsonb) if attributes_jsonb else None,
                "search_text": search_text
            }
            
            db.execute(text(upsert_sql), params)
            if commit:
                db.commit()
        except Exception as e:
            print(f"Failed to sync ad {ad.id} to search index: {e}")
            if commit:
                db.rollback()
