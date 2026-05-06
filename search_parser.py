import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ParsedQuery(BaseModel):
    original_query: str
    normalized_query: str
    deal_type: Optional[str] = "BOTH"
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    furnished: Optional[bool] = None
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    build_area: Optional[float] = None
    location: Optional[str] = None
    features: List[str] = []
    intents: List[str] = []
    legal: List[str] = []

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
        text = re.sub(r'[()\[\]\{\}\.,!?"\'-]', ' ', text) # Remove punctuation
        return text.lower().strip()

    @classmethod
    def parse(cls, raw_query: str) -> ParsedQuery:
        norm = cls.normalize_arabic(raw_query)
        parsed = ParsedQuery(original_query=raw_query, normalized_query=norm)

        from nlp_dictionaries import DEAL_MAP, PROPERTY_MAP, FEATURES, INTENT, LEGAL
        
        # Normalize dict keys once
        if not hasattr(cls, '_dicts_normalized'):
            cls._DEAL_MAP = {cls.normalize_arabic(k): v for k, v in DEAL_MAP.items()}
            cls._PROPERTY_MAP = {cls.normalize_arabic(k): v for k, v in PROPERTY_MAP.items()}
            cls._FEATURES = {cls.normalize_arabic(k): v for k, v in FEATURES.items()}
            cls._INTENT = {cls.normalize_arabic(k): v for k, v in INTENT.items()}
            cls._LEGAL = {cls.normalize_arabic(k): v for k, v in LEGAL.items()}
            cls._dicts_normalized = True

        # Split tokens
        words = norm.split()
        
        # 1. Extract Deal Type
        deal_types = set()
        for w in words:
            if w in cls._DEAL_MAP:
                deal_types.add(cls._DEAL_MAP[w])
                
        if len(deal_types) == 1:
            parsed.deal_type = list(deal_types)[0]
        else:
            parsed.deal_type = "BOTH"
                
        # 2. Extract Property Type
        for i in range(len(words)):
            # Try 2 words
            if i < len(words) - 1:
                bigram = f"{words[i]} {words[i+1]}"
                if bigram in cls._PROPERTY_MAP:
                    parsed.property_type = cls._PROPERTY_MAP[bigram]
            # Try 1 word
            if words[i] in cls._PROPERTY_MAP and not parsed.property_type:
                parsed.property_type = cls._PROPERTY_MAP[words[i]]

        # 3. Extract Bedrooms
        if re.search(r'\b(غرفه|غرفة واحده|ستوديو|ستديو|استوديو|استديو)\b', norm): parsed.bedrooms = 1
        elif re.search(r'\b(غرفتين)\b', norm): parsed.bedrooms = 2
        else:
            m = re.search(r'(\d+)\s*(غرف|غرفه|نوم)', norm)
            if m: parsed.bedrooms = int(m.group(1))

        # 4. Extract Price
        price_match = re.search(r'(اقل من|تحت|رخيص|بحدود|بسعر لا يتجاوز|سعر لا يتجاوز|سعر)\s*(\d+)\s*(الف|000|دينار)?', norm)
        if price_match:
            amount = int(price_match.group(2))
            unit = price_match.group(3)
            if unit in ["الف", "000"] or amount < 100:
                if unit == "الف" or unit == "000" or amount < 1000:
                    amount *= 1000
            parsed.max_price = float(amount)
        else:
            exact_price = re.search(r'(\d+)\s*(الف)', norm)
            if exact_price:
                parsed.max_price = float(exact_price.group(1)) * 1000

        # 5. Extract Area (build_area)
        area_match = re.search(r'(?:مساحة|مساحتها|بمساحة)?\s*(\d+)\s*(?:متر|م\b|m\b)', norm)
        if area_match:
            parsed.build_area = float(area_match.group(1))

        # 6. Extract Location
        for loc in sorted(cls.LOCATIONS, key=len, reverse=True):
            norm_loc = cls.normalize_arabic(loc)
            if norm_loc in norm:
                parsed.location = loc
                break

        # 7. Extract Features, Intent, Legal
        for i in range(len(words)):
            # Try 2 words
            if i < len(words) - 1:
                bigram = f"{words[i]} {words[i+1]}"
                if bigram in cls._FEATURES and cls._FEATURES[bigram] not in parsed.features:
                    parsed.features.append(cls._FEATURES[bigram])
                if bigram in cls._INTENT and cls._INTENT[bigram] not in parsed.intents:
                    parsed.intents.append(cls._INTENT[bigram])
                if bigram in cls._LEGAL and cls._LEGAL[bigram] not in parsed.legal:
                    parsed.legal.append(cls._LEGAL[bigram])
            # Try 1 word
            w = words[i]
            if w in cls._FEATURES and cls._FEATURES[w] not in parsed.features:
                parsed.features.append(cls._FEATURES[w])
            if w in cls._INTENT and cls._INTENT[w] not in parsed.intents:
                parsed.intents.append(cls._INTENT[w])
            if w in cls._LEGAL and cls._LEGAL[w] not in parsed.legal:
                parsed.legal.append(cls._LEGAL[w])
                
        # Handle furnished explicit mapping
        if "furnished" in parsed.features:
            parsed.furnished = True
        elif "unfurnished" in parsed.features:
            parsed.furnished = False

        return parsed
