import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ParsedQuery(BaseModel):
    original_query: str
    normalized_query: str
    deal_type: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    furnished: Optional[bool] = None
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    build_area: Optional[float] = None
    location: Optional[str] = None
    features: List[str] = []

class QueryParserService:
    # Jordanian specific locations mapped to unified names
    LOCATIONS = [
        "عمان", "الزرقاء", "اربد", "العقبة", "دابوق", "عبدون", "تلاع العلي", 
        "ضاحية الرشيد", "مرج الحمام", "جبل اللويبدة", "الجامعة الاردنية", 
        "خلدا", "جامعة اليرموك", "الزرقاء الجديدة", "الجبيهة"
    ]
    
    FEATURES_MAP = {
        "مسبح": ["مسبح", "بركة سباحة"],
        "تراس": ["تراس", "ترس"],
        "حديقة": ["حديقه", "حديقة"],
        "بالتقسيط": ["بالتقسيط", "تقسيط", "اقساط"],
        "من المالك": ["من المالك"],
        "طابو": ["طابو", "سند مستقل", "قوشان"],
        "مدخل مستقل": ["مدخل مستقل"],
        "إطلالة": ["اطلاله", "إطلالة", "مطلة"],
        "سوبر ديلوكس": ["سوبر ديلوكس", "تشطيبات سوبر ديلوكس"],
        "تحت الإنشاء": ["تحت الانشاء", "قيد الانشاء", "عظم"],
        "استثمار": ["استثمار", "تصلح للاستثمار"],
        "لقطة": ["لقطه", "سعر حرق", "بداعي السفر", "مستعجل"]
    }

    @staticmethod
    def normalize_arabic(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'[أإآ]', 'ا', text)
        text = re.sub(r'ة', 'ه', text)
        text = re.sub(r'ى', 'ي', text)
        text = re.sub(r'[ًٌٍَُِّْ]', '', text)  # Remove diacritics
        return text.lower().strip()

    @classmethod
    def parse(cls, raw_query: str) -> ParsedQuery:
        norm = cls.normalize_arabic(raw_query)
        parsed = ParsedQuery(original_query=raw_query, normalized_query=norm)

        # 1. Extract Deal Type
        if re.search(r'\b(بيع|للبيع)\b', norm):
            parsed.deal_type = "SALE"
        elif re.search(r'\b(ايجار|للايجار|اجار)\b', norm):
            parsed.deal_type = "RENT"

        # 2. Extract Property Type
        if re.search(r'\b(شقه|شقق)\b', norm): parsed.property_type = "APARTMENT"
        elif re.search(r'\b(فيلا|فلل|فيلات)\b', norm): parsed.property_type = "VILLA"
        elif re.search(r'\b(ارض|اراضي)\b', norm): parsed.property_type = "LAND"
        elif re.search(r'\b(بيت|منزل|بيوت)\b', norm): parsed.property_type = "HOUSE"
        elif re.search(r'\b(محل|تجاري|مكتب|معرض|مخزن)\b', norm): parsed.property_type = "SHOP"
        elif re.search(r'\b(استوديو|ستوديو)\b', norm): parsed.property_type = "STUDIO"
        elif re.search(r'\b(رووف|روف)\b', norm): parsed.property_type = "ROOF"
        elif re.search(r'\b(دوبلكس)\b', norm): parsed.property_type = "DUPLEX"
        elif re.search(r'\b(عماره|عمارة|مبنى)\b', norm): parsed.property_type = "BUILDING"

        # 3. Extract Bedrooms
        if re.search(r'\b(غرفه|غرفة واحده)\b', norm): parsed.bedrooms = 1
        elif re.search(r'\b(غرفتين)\b', norm): parsed.bedrooms = 2
        else:
            m = re.search(r'(\d+)\s*(غرف|غرفه|نوم)', norm)
            if m: parsed.bedrooms = int(m.group(1))

        # 4. Extract Price
        price_match = re.search(r'(اقل من|تحت|رخيص|بحدود|بسعر لا يتجاوز|سعر لا يتجاوز|سعر)\s*(\d+)\s*(الف|000|دينار)?', norm)
        if price_match:
            amount = int(price_match.group(2))
            unit = price_match.group(3)
            if unit in ["الف", "000"] or amount < 100:  # e.g. 50 meaning 50k
                if unit == "الف" or unit == "000" or amount < 1000:
                    amount *= 1000
            parsed.max_price = float(amount)
        else:
            # Fallback for just exact numbers with ألف
            exact_price = re.search(r'(\d+)\s*(الف)', norm)
            if exact_price:
                parsed.max_price = float(exact_price.group(1)) * 1000

        # 5. Extract Area (build_area)
        area_match = re.search(r'(?:مساحة|مساحتها|بمساحة)?\s*(\d+)\s*(?:متر|م\b|m\b)', norm)
        if area_match:
            parsed.build_area = float(area_match.group(1))

        # 6. Extract Furnished
        if re.search(r'\b(مفروش|مفروشه)\b', norm):
            parsed.furnished = True

        # 7. Extract Location
        # Check against our known locations list
        for loc in sorted(cls.LOCATIONS, key=len, reverse=True):
            norm_loc = cls.normalize_arabic(loc)
            if norm_loc in norm:
                parsed.location = loc
                break

        # 8. Extract Features and Legal/Intent Terms
        for feature_name, keywords in cls.FEATURES_MAP.items():
            for kw in keywords:
                norm_kw = cls.normalize_arabic(kw)
                if norm_kw in norm:
                    if feature_name not in parsed.features:
                        parsed.features.append(feature_name)

        return parsed
