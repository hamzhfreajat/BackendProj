import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from search_parser import QueryParserService, ParsedQuery

class AutocompleteService:

    @staticmethod
    def _get_price_intent(q: str) -> str:
        if re.search(r'(لقطة|مستعجل|اقل من|أقل من|رخيص|ممتاز)', q):
            return "cheap"
        if re.search(r'(فاخر|فيلا|قصر|ديلوكس)', q):
            return "expensive"
        if re.search(r'(بالتقسيط|تقسيط|بدون دفعة|دفعة اولى)', q):
            return "negotiable"
        if re.search(r'(بسعر|سعر)', q):
            return "exact"
        return "unknown"

    @staticmethod
    def _get_category_info(deal_type: str, property_type: str) -> tuple:
        if deal_type == "RENT":
            mapping = {
                "APARTMENT": (301, "شقق للايجار"),
                "STUDIO": (302, "ستوديوهات للايجار"),
                "VILLA": (3101, "فلل وقصور"),
                "HOUSE": (3102, "بيوت مستقلة"),
                "ROOF": (3103, "روف"),
                "BUILDING": (3104, "عمارة كاملة"),
                "SHOP": (303, "محلات تجارية"),
                "OFFICE": (304, "مكاتب"),
                "LAND": (313, "اراضي"),
                "FARM": (314, "مزارع")
            }
            return mapping.get(property_type, (3, "عقارات للايجار"))
        elif deal_type == "SALE":
            mapping = {
                "APARTMENT": (10301, "شقق للبيع"),
                "STUDIO": (10302, "ستوديوهات للبيع"),
                "VILLA": (10101, "فلل وقصور"),
                "HOUSE": (10102, "بيوت مستقلة"),
                "BUILDING": (10104, "عمارة كاملة"),
                "ROOF": (10105, "ملحق / روف"),
                "SHOP": (10303, "محلات تجارية"),
                "OFFICE": (10304, "مكاتب"),
                "LAND": (10313, "اراضي"),
                "FARM": (10314, "مزارع")
            }
            return mapping.get(property_type, (2, "عقارات للبيع"))
        return None, None

    @staticmethod
    def generate_suggestions(db: Session, query: str) -> Dict[str, Any]:
        if not query or len(query.strip()) < 2:
            return {
                "query": query,
                "normalized_query": query,
                "intent": {
                    "deal_type": "UNKNOWN",
                    "property_type": "UNKNOWN",
                    "location": None,
                    "price_intent": "unknown",
                    "category_id": None,
                    "category_name": None
                },
                "groups": []
            }
            
        parsed = QueryParserService.parse(query)
        price_intent = AutocompleteService._get_price_intent(query)
        
        # Map parsed properties to frontend UI tags
        intent_tags = []
        if parsed.furnished is True:
            intent_tags.append("furnished:مفروشة")
        elif parsed.furnished is False:
            intent_tags.append("furnished:غير مفروشة")
            
        if parsed.floor_number is not None:
            if parsed.floor_number == 0: intent_tags.append("floor:الطابق الأرضي")
            elif parsed.floor_number == -1: intent_tags.append("floor:طابق شبه أرضي")
            elif parsed.floor_number == 99: intent_tags.append("floor:الطابق الأخير")
            elif parsed.floor_number > 0: intent_tags.append(f"floor:{parsed.floor_number}")
            
        if parsed.bedrooms is not None:
            if parsed.bedrooms == 0: intent_tags.append("bedrooms:ستوديو")
            elif parsed.bedrooms >= 6: intent_tags.append("bedrooms:+6")
            else: intent_tags.append(f"bedrooms:{parsed.bedrooms}")

        cat_id, cat_name = AutocompleteService._get_category_info(parsed.deal_type, parsed.property_type)

        # Base intent object
        intent = {
            "deal_type": parsed.deal_type or "UNKNOWN",
            "property_type": parsed.property_type or "UNKNOWN",
            "location": parsed.location,
            "price_intent": price_intent,
            "tags": intent_tags,
            "category_id": cat_id,
            "category_name": cat_name
        }

        # Query completions based on intent
        query_items = []
        location_items = []
        filter_items = []
        
        base_query = query.strip()
        
        # Logic to generate smart suggestions based on parsed intent
        
        # 1. Expand deal type if missing
        if parsed.deal_type is None and parsed.property_type is not None:
            query_items.append({"text": f"{base_query} للبيع", "score": 0.98})
            query_items.append({"text": f"{base_query} للايجار", "score": 0.95})
        
        # 2. Expand locations if location is missing, but we have property + deal type
        if parsed.location is None and parsed.property_type is not None:
            # Look up top 3 cities
            top_cities = ["عمان", "اربد", "الزرقاء"]
            for c in top_cities:
                if c not in base_query:
                    query_items.append({"text": f"{base_query} في {c}", "score": 0.90})
        
        # 3. Add filters if property type is known
        if parsed.property_type == "APARTMENT":
            if "مفروش" not in base_query and "مفروشة" not in base_query:
                filter_items.append({"text": f"{base_query} مفروشة", "score": 0.92})
            if "غرفتين" not in base_query and not parsed.bedrooms:
                filter_items.append({"text": f"{base_query} غرفتين", "score": 0.91})
            if "جديد" not in base_query:
                filter_items.append({"text": f"{base_query} جديدة", "score": 0.89})
                
        # 4. Handle Price Intent Expansions
        if price_intent == "cheap" or "أقل من" in base_query or "اقل من" in base_query:
            if "عمان" not in base_query and parsed.location is None:
                query_items.append({"text": f"{base_query} في عمان", "score": 0.90})
            if "مستعملة" not in base_query:
                query_items.append({"text": f"{base_query} مستعملة", "score": 0.85})
                
        if "تقسيط" in base_query or "بالتقسيط" in base_query:
            if "بدون دفعة" not in base_query:
                query_items.append({"text": f"{base_query} بدون دفعة أولى", "score": 0.95})
            if "عمان" not in base_query and parsed.location is None:
                query_items.append({"text": f"{base_query} في عمان", "score": 0.93})
            if "من المالك" not in base_query:
                query_items.append({"text": f"{base_query} من المالك", "score": 0.90})
                
        # 5. Extract actual DB locations if they typed part of a location
        # This gives real DB feedback
        words = base_query.split()
        last_word = words[-1] if words else ""
        
        if len(last_word) >= 3 and not parsed.location:
            # Check if last word is a known city/region
            locs = db.execute(text("SELECT name_ar FROM regions WHERE name_ar ILIKE :loc LIMIT 3"), {"loc": f"{last_word}%"}).fetchall()
            for row in locs:
                loc_name = row[0]
                new_q = base_query.replace(last_word, loc_name)
                if new_q != base_query:
                    location_items.append({"text": new_q, "score": 0.93})
        
        # Build Groups
        groups = []
        
        from search_service import SearchService
        
        def populate_counts(items, limit):
            valid_items = []
            for item in items:
                count = SearchService.count_properties(db, item["text"])
                if count > 0:
                    item["count"] = count
                    valid_items.append(item)
                if len(valid_items) >= limit:
                    break
            return valid_items
            
        if query_items:
            # Sort by score first
            query_items.sort(key=lambda x: x["score"], reverse=True)
            valid_query_items = populate_counts(query_items, 5)
            if valid_query_items:
                groups.append({
                    "type": "query",
                    "title": "اقتراحات البحث",
                    "items": valid_query_items
                })
            
        if location_items:
            valid_loc_items = populate_counts(location_items, 3)
            if valid_loc_items:
                groups.append({
                    "type": "location",
                    "title": "مواقع مقترحة",
                    "items": valid_loc_items
                })
            
        if filter_items:
            valid_filter_items = populate_counts(filter_items, 3)
            if valid_filter_items:
                groups.append({
                    "type": "filter",
                    "title": "فلاتر إضافية",
                    "items": valid_filter_items
                })
            
        # Fallback if no groups generated at all
        if not groups:
            fallback_items = [
                {"text": f"{base_query} للبيع", "score": 0.8},
                {"text": f"{base_query} للايجار", "score": 0.8}
            ]
            valid_fallback = populate_counts(fallback_items, 2)
            if valid_fallback:
                groups.append({
                    "type": "query",
                    "title": "اقتراحات البحث",
                    "items": valid_fallback
                })

        # Compute remaining text to prevent redundant full-text search
        remaining_text = parsed.normalized_query
        if parsed.location:
            remaining_text = remaining_text.replace(parsed.location, "")
            
        from nlp_dictionaries import DEAL_MAP, PROPERTY_MAP
        for w in parsed.normalized_query.split():
            # Remove mapped real estate words and common stop words
            if w in DEAL_MAP or w in PROPERTY_MAP or w in ['لل', 'في', 'ب', 'من', 'على', 'مع', 'ع', 'و']:
                remaining_text = remaining_text.replace(w, "")
                
        import re
        remaining_text = re.sub(r'\s+', ' ', remaining_text).strip()

        return {
            "query": query,
            "normalized_query": remaining_text,
            "intent": intent,
            "groups": groups
        }
