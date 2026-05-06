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
    def generate_suggestions(db: Session, query: str) -> Dict[str, Any]:
        if not query or len(query.strip()) < 2:
            return {
                "query": query,
                "normalized_query": query,
                "intent": {
                    "deal_type": "UNKNOWN",
                    "property_type": "UNKNOWN",
                    "location": None,
                    "price_intent": "unknown"
                },
                "groups": []
            }
            
        parsed = QueryParserService.parse(query)
        price_intent = AutocompleteService._get_price_intent(query)
        
        # Base intent object
        intent = {
            "deal_type": parsed.deal_type or "UNKNOWN",
            "property_type": parsed.property_type or "UNKNOWN",
            "location": parsed.location,
            "price_intent": price_intent
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
            if "عمان" not in base_query:
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

        return {
            "query": query,
            "normalized_query": parsed.normalized_query,
            "intent": intent,
            "groups": groups
        }
