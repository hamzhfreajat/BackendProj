PROPERTY_MAP = {
    "شقة": "APARTMENT", "شقه": "APARTMENT", "شقق": "APARTMENT", "شقق سكنية": "APARTMENT", 
    "تسوية": "APARTMENT", "بيت": "HOUSE", "منزل": "HOUSE", "بيوت": "HOUSE", "منازل": "HOUSE", 
    "بيت مستقل": "HOUSE", "فيلا": "VILLA", "فلل": "VILLA", "قصر": "VILLA", "قصور": "VILLA", 
    "اراضي": "LAND", "أراضي": "LAND", "ارض": "LAND", "أرض": "LAND", "ارض زراعية": "LAND", 
    "ارض سكنية": "LAND", "ارض تجارية": "LAND", "نمرة": "LAND", "قطعة ارض": "LAND", 
    "محل": "SHOP", "محلات": "SHOP", "معرض": "SHOP", "معارض": "SHOP", "مخفر": "SHOP", 
    "مخزن": "WAREHOUSE", "مستودع": "WAREHOUSE", "مستودعات": "WAREHOUSE", "هنجر": "WAREHOUSE", 
    "هناجر": "WAREHOUSE", "مكتب": "OFFICE", "مكاتب": "OFFICE", "عيادة": "OFFICE", 
    "عيادات": "OFFICE", "مساحة مكتبية": "OFFICE", "استوديو": "STUDIO", "استديو": "STUDIO", 
    "ستوديو": "STUDIO", "ستديو": "STUDIO", "رووف": "ROOF", "روف": "ROOF", "روفات": "ROOF", 
    "عمارة": "BUILDING", "بناية": "BUILDING", "مبنى": "BUILDING", "مجمع": "BUILDING", 
    "مجمع تجاري": "BUILDING", "شاليه": "FARM", "شاليهات": "FARM", "مزرعة": "FARM", "مزارع": "FARM"
}

DEAL_MAP = {
    "للبيع": "SALE", "بيع": "SALE", "برسم البيع": "SALE", "للايجار": "RENT", "للإيجار": "RENT", 
    "ايجار": "RENT", "إيجار": "RENT", "يومي": "RENT", 
    "شهري": "RENT", "سنوي": "RENT", "للاستثمار": "SALE", "للإستثمار": "SALE", "ضمان": "RENT", 
    "خلو": "SALE", "بدل خلو": "SALE"
}

FEATURES = {
    "مفروش": "furnished", "مفروشة": "furnished", "مفروشه": "furnished", "فرش فندقي": "furnished", 
    "مؤثث": "furnished", "عفش": "furnished", "اثاث": "furnished", "غير مفروش": "unfurnished", 
    "فارغ": "unfurnished", "فارغة": "unfurnished", "فارغه": "unfurnished", "بدون عفش": "unfurnished", 
    "مصعد": "elevator", "اسانسير": "elevator", "مصاعد": "elevator", "كراج": "parking", 
    "مصف": "parking", "موقف": "parking", "كراجات": "parking", "باركنج": "parking", 
    "مواقف": "parking", "بلكونة": "balcony", "بلكونه": "balcony", "برندا": "balcony", 
    "فرندا": "balcony", "شرفة": "balcony", "تراس": "terrace", "ترس": "terrace", "تراسات": "terrace", 
    "حديقة": "garden", "حديقه": "garden", "ساحة": "garden", "حوش": "garden", "مساحة خضراء": "garden", 
    "تدفئة": "heating", "تدفئه": "heating", "بويلر": "heating", "تدفئة مركزية": "heating", 
    "تدفئة غاز": "heating", "رديترات": "heating", "تكييف": "ac", "مكيف": "ac", "مكيفات": "ac", 
    "سنترال": "ac", "تبريد": "ac", "طاقة شمسية": "solar", "طاقه شمسيه": "solar", "سخان شمسي": "solar", 
    "مسبح": "pool", "بركة": "pool", "بركة سباحة": "pool", "اطلالة": "view", "إطلالة": "view", 
    "مطلة": "view", "فيو": "view", "بانوراما": "view", "كاشفة": "view", "حارس": "security", 
    "بواب": "security", "سكيورتي": "security", "امن": "security", "ماستر": "master_bedroom", 
    "نوم ماستر": "master_bedroom", "حمام ماستر": "master_bedroom", "خزانة بالحيط": "built_in_wardrobes", 
    "خزائن حائط": "built_in_wardrobes", "خزاين": "built_in_wardrobes", "ديكورات": "decorations", 
    "جبس": "decorations", "جبسن بورد": "decorations", "انارة مخفية": "decorations", 
    "سبوتات": "decorations", "تشطيبات سوبر ديلوكس": "premium_finish", "تشطيب فاخر": "premium_finish", 
    "تشطيبات حديثة": "premium_finish", "نخب اول": "premium_finish", "تشطيب نخب": "premium_finish", 
    "مطبخ راكب": "kitchen_installed", "مطبخ خشب": "kitchen_installed", "مطبخ امريكي": "kitchen_installed", 
    "مطبخ بلوط": "kitchen_installed", "مطبخ المنيوم": "kitchen_installed", "بئر ماء": "water_well", 
    "بير ماء": "water_well", "خزان ماء": "water_well", "مستودع": "storage_room", "خزين": "storage_room", 
    "غرفة خزين": "storage_room", "مدخل مستقل": "private_entrance", "باب مستقل": "private_entrance", 
    "كاميرات": "cctv", "كاميرات مراقبة": "cctv", "نظام حماية": "cctv", "اباجورات كهرباء": "electric_shutters", 
    "اباجورات": "electric_shutters", "زجاج دبل": "double_glazed", "دبل جلاس": "double_glazed", 
    "مقطع خاص": "double_glazed"
}

INTENT = {
    "مستعجل": "urgent", "مستعجلة": "urgent", "بداعي السفر": "urgent_sale", "لظروف خاصة": "urgent_sale", 
    "بداعي الهجرة": "urgent_sale", "طارئ": "urgent", "لقطة": "hot_deal", "فرصة": "hot_deal", 
    "صيدة": "hot_deal", "فرصة لا تعوض": "hot_deal", "سعر مغري": "hot_deal", "فرصة ذهبية": "hot_deal", 
    "سعر محروق": "cheap", "رخيص": "cheap", "ارخص": "cheap", "تصفية": "cheap", "فرصة العمر": "cheap", 
    "باقل من سعر السوق": "cheap", "اقل من التخمين": "cheap", "أقل من سعر السوق": "cheap", "أقل من": "cheap", 
    "سعر مناسب": "affordable", "سعر معقول": "affordable", "بسعر الكلفة": "affordable", 
    "قابل للتفاوض": "negotiable", "في مجال": "negotiable", "قابل للبدل": "negotiable", 
    "تفاوض": "negotiable", "مع امكانية التفاوض": "negotiable", "مرونة بالسعر": "negotiable", 
    "نهائي": "non_negotiable", "غير قابل للتفاوض": "non_negotiable", "كاش فقط": "non_negotiable", 
    "سعر نهائي": "non_negotiable", "من الاخر": "non_negotiable", "بدون عمولة": "no_commission", 
    "من المالك مباشرة": "no_commission", "من المالك": "no_commission", "المالك": "no_commission", 
    "بدون وسطاء": "no_commission", "لا للوسطاء": "no_commission", "تقسيط": "installments", 
    "بالتقسيط": "installments", "دفعة اولى": "installments", "دفعه اولى": "installments", 
    "أقساط": "installments", "اقساط": "installments", "بدون دفعة": "installments", 
    "بدون بنوك": "installments", "اقساط مباشرة": "installments", "دفعات": "installments", 
    "استثمار": "investment", "عائد استثماري": "investment", "دخل ممتاز": "investment", 
    "مؤجرة": "investment", "تصلح للاستثمار": "investment"
}

LEGAL = {
    "طابو": "title_deed", "كوشان": "title_deed", "قوشان": "title_deed", "سند تسجيل": "title_deed", 
    "سند ملكية": "title_deed", "سند مستقل": "independent_deed", "قوشان مستقل": "independent_deed", 
    "طابو مستقل": "independent_deed", "مفروز": "subdivided", "مفرز": "subdivided", "مشاع": "shared_deed", 
    "حصص مشاع": "shared_deed", "سند مشاع": "shared_deed", "غير مفروز": "shared_deed", 
    "رهن": "mortgage", "مرهون": "mortgage", "مطلوب للبنك": "mortgage", "فك الرهن": "mortgage_release", 
    "حر": "mortgage_release", "غير مرهون": "mortgage_release", "بدون رهن": "mortgage_release", 
    "تنازل": "transfer_ready", "تنازل فوري": "transfer_ready", "جاهز للتنازل": "transfer_ready", 
    "فراغ": "transfer_ready", "الفراغ": "transfer_ready", "ورثة": "inheritance", "حصر ارث": "inheritance", 
    "تقسيم ورثة": "inheritance", "تجاري": "commercial_zoning", "سكن": "residential_zoning", 
    "صناعي": "industrial_zoning", "سكن ج": "zoning_c", "سكن ب": "zoning_b", "سكن ا": "zoning_a", 
    "سكن أ": "zoning_a", "سكن خاص": "zoning_special", "تنظيم": "zoning"
}
