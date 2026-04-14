-- ============================================================
-- Migration: Copy عقارات للإيجار structure to عقارات للبيع
-- 1. Insert new hierarchical categories under parent=2
-- 2. Remap ads from old categories to new ones
-- 3. Delete old flat categories (201-210 and children)
-- ============================================================

BEGIN;

-- ════════════════════════════════════════════════
-- STEP 1: INSERT NEW CATEGORIES
-- ════════════════════════════════════════════════

-- Second-level under عقارات للبيع (id=2)
INSERT INTO categories (id, parent_id, name, description, icon_name, color_hex, slugs) VALUES
(10310, 2, 'سكني', 'شقق، فلل، منازل واستديوهات', 'home', '#4CAF50', '{"en": ["Residential"]}'),
(10311, 2, 'تجاري', 'مكاتب، معارض ومخازن', 'store', '#FF9800', '{"en": ["Commercial"]}'),
(10313, 2, 'أراضي', 'جميع أنواع الأراضي', 'landscape', '#8BC34A', '{"en": ["Lands"]}'),
(10314, 2, 'مزارع', 'مزارع للبيع والاستثمار', 'agriculture', '#4CAF50', '{"en": ["Farms"]}'),
(10315, 2, 'شاليهات / منتجعات / بيوت ريفية', 'شاليهات، منتجعات، وبيوت ريفية للبيع والاستثمار', 'pool', '#00BCD4', '{"en": ["Chalets / Resorts / Rural Houses"]}')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id, description = EXCLUDED.description, icon_name = EXCLUDED.icon_name, color_hex = EXCLUDED.color_hex, slugs = EXCLUDED.slugs;

-- سكني للبيع (parent=10310)
INSERT INTO categories (id, parent_id, name, slugs) VALUES
(10301, 10310, 'شقق للبيع', '{"ar": ["مفروش کامل", "فرش فندقي", "شبه مفروش", "فارغ", "جديد لم يسكن", "عائلات", "عرسان", "مصعد", "كراج خاص", "حارس عمارة", "مطبخ راكب", "بلكونة", "ترس", "حديقة", "تدفئة", "تكييف إنفيرتر", "كاميرات مراقبة", "زجاج دبل", "سخان شمسي", "غرفة خادمة", "تسوية", "طابق أرضي", "طوابق علوية", "رووف", "من المالك", "مكتب عقاري", "تقسيط", "قابل للتفاوض"], "en": ["Furnished", "Unfurnished", "Families", "Singles", "New", "Heating", "Inverter AC"]}'),
(10302, 10310, 'ستوديوهات للبيع', '{"ar": ["مفروش کامل", "فرش فندقي", "شبه مفروش", "فارغ", "جديد لم يسكن", "قريب من الجامعة"], "en": ["Near University", "Furnished", "Semi-Furnished"]}'),
(10101, 10310, 'فلل وقصور', NULL),
(10102, 10310, 'بيوت مستقلة للبيع', NULL),
(10103, 10310, 'دوبلكس / بنتهاوس', NULL),
(10104, 10310, 'طابق كامل للبيع', NULL),
(10105, 10310, 'ملحق / روف', NULL),
(10999, 10310, 'أخرى', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id, slugs = EXCLUDED.slugs;

-- Sub of شقق للبيع
INSERT INTO categories (id, parent_id, name, slugs) VALUES
(10015, 10301, 'شقق فندقية / مخدومة', '{"ar": ["شقق فندقية", "شقة مفروشة"], "en": ["Hotel / Serviced Apartments"]}')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id, slugs = EXCLUDED.slugs;

-- Sub of ستوديوهات للبيع
INSERT INTO categories (id, parent_id, name, slugs) VALUES
(10023, 10302, 'ستوديو فندقي / مخدوم', '{"ar": ["ستوديو فندقي", "خدمات فندقية"], "en": ["Hotel / Serviced Studio"]}')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id, slugs = EXCLUDED.slugs;

-- تجاري للبيع (parent=10311)
INSERT INTO categories (id, parent_id, name, slugs) VALUES
(10303, 10311, 'محلات ومعارض للبيع', '{"ar": ["مع خلو", "بدون خلو", "موقع حيوي", "بابين"], "en": ["With Key Money", "No Key Money"]}'),
(10304, 10311, 'مكاتب للبيع', '{"ar": ["مجهز بالكامل", "مساحة مفتوحة", "مجمع تجاري"], "en": ["Fully Equipped", "Open Space"]}')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id, slugs = EXCLUDED.slugs;

-- محلات ومعارض للبيع subs
INSERT INTO categories (id, parent_id, name) VALUES
(10853, 10303, 'محلات تجارية عامة'),
(10872, 10303, 'كشك / بسطة / مساحة مفتوحة'),
(10874, 10303, 'محل مغلق'),
(10875, 10303, 'بسطة / مساحة مفتوحة')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- معارض تجارية متخصصة
INSERT INTO categories (id, parent_id, name) VALUES
(10876, 10311, 'معارض تجارية متخصصة'),
(10877, 10876, 'معارض سيارات'),
(10878, 10876, 'معرض مستقل'),
(10883, 10876, 'معارض أجهزة كهربائية وإلكترونيات'),
(10886, 10876, 'معارض ملابس وأحذية')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- صالونات ومراكز تجميل
INSERT INTO categories (id, parent_id, name) VALUES
(10889, 10311, 'صالونات ومراكز تجميل'),
(10890, 10889, 'صالون حلاقة رجالي'),
(10893, 10889, 'صالون تجميل نسائي / سبا')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- مطاعم ومقاهي
INSERT INTO categories (id, parent_id, name) VALUES
(10896, 10311, 'مطاعم ومقاهي'),
(18001, 10896, 'مطعم'),
(18002, 10896, 'كافيه / مقهى'),
(18003, 10896, 'مطعم وكافيه')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- مكاتب للبيع subs
INSERT INTO categories (id, parent_id, name) VALUES
(16945, 10304, 'مقر مستقل'),
(18004, 10304, 'مكتب'),
(18005, 10304, 'مقر شركة'),
(18006, 10304, 'مبنى إداري')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- مخازن ومستودعات
INSERT INTO categories (id, parent_id, name) VALUES
(10912, 10311, 'مخازن ومستودعات'),
(10913, 10912, 'مخزن متصل بمحل'),
(10915, 10912, 'مخزن خلفي'),
(10919, 10912, 'مستودع مستقل'),
(18007, 10912, 'مخزن')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- عيادات ومراكز طبية
INSERT INTO categories (id, parent_id, name) VALUES
(18008, 10311, 'عيادات ومراكز طبية'),
(18009, 18008, 'عيادة'),
(18010, 18008, 'مركز طبي'),
(18011, 18008, 'مختبر'),
(18012, 18008, 'صيدلية')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- مراكز تعليمية
INSERT INTO categories (id, parent_id, name) VALUES
(18013, 10311, 'مراكز تعليمية'),
(18014, 18013, 'مدرسة'),
(18015, 18013, 'روضة'),
(18016, 18013, 'مركز تدريب'),
(18017, 18013, 'معهد')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- صالات ومرافق
INSERT INTO categories (id, parent_id, name) VALUES
(18018, 10311, 'صالات ومرافق'),
(18019, 18018, 'صالة رياضية'),
(18020, 18018, 'صالة أفراح'),
(18021, 18018, 'صالة عرض'),
(18022, 18018, 'نادي')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- فنادق وسياحة
INSERT INTO categories (id, parent_id, name) VALUES
(18023, 10311, 'فنادق وسياحة'),
(18024, 18023, 'فندق'),
(18025, 18023, 'شقق فندقية'),
(18026, 18023, 'بيت ضيافة'),
(18027, 18023, 'نزل')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- أراضي تجارية
INSERT INTO categories (id, parent_id, name) VALUES
(18028, 10311, 'أراضي تجارية'),
(18029, 18028, 'أرض تجارية'),
(18030, 18028, 'أرض صناعية'),
(18031, 18028, 'أرض استثمارية')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- مباني تجارية كاملة
INSERT INTO categories (id, parent_id, name) VALUES
(18032, 10311, 'مباني تجارية كاملة'),
(18033, 18032, 'عمارة تجارية'),
(18034, 18032, 'مجمع تجاري'),
(18035, 18032, 'مول'),
(18036, 18032, 'مبنى متعدد الاستخدام')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- أخرى تجاري
INSERT INTO categories (id, parent_id, name) VALUES
(18037, 10311, 'أخرى')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- ════════════════════════════════════════════════
-- أراضي للبيع (parent=10313)
-- ════════════════════════════════════════════════
INSERT INTO categories (id, parent_id, name) VALUES
(19000, 10313, 'أراضي سكنية'),
(19001, 19000, 'أرض سكنية'),
(19002, 19000, 'أرض فيلا'),
(19003, 19000, 'أرض عمارات'),
(19004, 19000, 'أرض إسكان'),
(19010, 10313, 'أراضي تجارية'),
(19011, 19010, 'أرض تجارية'),
(19012, 19010, 'أرض مول / مجمع تجاري'),
(19013, 19010, 'أرض مكاتب'),
(19014, 19010, 'أرض استثمارية تجارية'),
(19020, 10313, 'أراضي صناعية'),
(19021, 19020, 'أرض صناعية'),
(19022, 19020, 'أرض مصانع'),
(19023, 19020, 'أرض مستودعات'),
(19024, 19020, 'أرض ورش'),
(19030, 10313, 'أراضي زراعية'),
(19031, 19030, 'أرض زراعية'),
(19032, 19030, 'مزرعة'),
(19033, 19030, 'أرض بئر / ري'),
(19034, 19030, 'أرض مشجرة'),
(19040, 10313, 'أراضي سياحية'),
(19041, 19040, 'أرض منتجع'),
(19042, 19040, 'أرض فندق'),
(19043, 19040, 'أرض شاليهات'),
(19044, 19040, 'أرض سياحية استثمارية'),
(19050, 10313, 'أراضي متعددة الاستخدام'),
(19051, 19050, 'أرض تنظيم خاص'),
(19052, 19050, 'أرض استثمار'),
(19053, 19050, 'أرض استعمال مختلط'),
(19054, 19050, 'أرض مشروع'),
(19060, 10313, 'أراضي حكومية / تنظيم خاص'),
(19061, 19060, 'أرض أملاك دولة'),
(19062, 19060, 'أرض وقف'),
(19063, 19060, 'أرض تنظيم حكومي'),
(19070, 10313, 'أراضي بدون تنظيم'),
(19071, 19070, 'أرض خارج التنظيم'),
(19072, 19070, 'أرض بادية'),
(19073, 19070, 'أرض فضاء'),
(19074, 19070, 'أرض غير مصنفة')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- ════════════════════════════════════════════════
-- مزارع للبيع (parent=10314)
-- ════════════════════════════════════════════════
INSERT INTO categories (id, parent_id, name) VALUES
(19200, 10314, 'مزارع زراعية'),
(19201, 19200, 'مزرعة خضار'),
(19202, 19200, 'مزرعة فواكه'),
(19203, 19200, 'مزرعة زيتون'),
(19204, 19200, 'مزرعة حمضيات'),
(19205, 19200, 'مزرعة محاصيل'),
(19206, 19200, 'مزرعة أشجار'),
(19210, 10314, 'مزارع تربية حيوانات'),
(19211, 19210, 'مزرعة أغنام'),
(19212, 19210, 'مزرعة أبقار'),
(19213, 19210, 'مزرعة دواجن'),
(19214, 19210, 'مزرعة خيول'),
(19215, 19210, 'مزرعة أسماك'),
(19216, 19210, 'مزرعة نحل'),
(19220, 10314, 'مزارع استثمارية'),
(19221, 19220, 'مزرعة استثمارية'),
(19222, 19220, 'مزرعة منتجة'),
(19223, 19220, 'مزرعة مشروع'),
(19224, 19220, 'مزرعة تجارية'),
(19230, 10314, 'مزارع مع سكن'),
(19231, 19230, 'مزرعة مع بيت'),
(19232, 19230, 'مزرعة مع فيلا'),
(19233, 19230, 'مزرعة مع استراحة'),
(19234, 19230, 'مزرعة مع شاليه'),
(19240, 10314, 'مزارع سياحية / ترفيهية'),
(19241, 19240, 'مزرعة سياحية'),
(19242, 19240, 'مزرعة رحلات'),
(19243, 19240, 'مزرعة منتجع'),
(19244, 19240, 'مزرعة فعاليات'),
(19250, 10314, 'مزارع مجهزة بالبنية التحتية'),
(19251, 19250, 'مزرعة مع بئر'),
(19252, 19250, 'مزرعة مع كهرباء'),
(19253, 19250, 'مزرعة مع بيت بلاستيك'),
(19254, 19250, 'مزرعة مع مستودعات'),
(19260, 10314, 'مزارع صناعية / إنتاجية'),
(19261, 19260, 'مزرعة أعلاف'),
(19262, 19260, 'مزرعة ألبان'),
(19263, 19260, 'مزرعة دواجن تجارية'),
(19264, 19260, 'مزرعة إنتاج غذائي'),
(19270, 10314, 'مزارع غير مستغلة'),
(19271, 19270, 'مزرعة غير مزروعة'),
(19272, 19270, 'مزرعة أرض فقط'),
(19273, 19270, 'مزرعة بحاجة تأهيل'),
(19274, 19270, 'مزرعة غير مستثمرة'),
(19280, 10314, 'أخرى')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- ════════════════════════════════════════════════
-- شاليهات / منتجعات / بيوت ريفية للبيع (parent=10315)
-- ════════════════════════════════════════════════
INSERT INTO categories (id, parent_id, name) VALUES
(19300, 10315, 'شاليهات'),
(19301, 19300, 'شاليه مستقل'),
(19302, 19300, 'شاليه ضمن مجمع'),
(19303, 19300, 'شاليه مع مسبح'),
(19304, 19300, 'شاليه مع حديقة'),
(19305, 19300, 'شاليه مع إطلالة'),
(19310, 10315, 'منتجعات'),
(19311, 19310, 'منتجع سياحي'),
(19312, 19310, 'منتجع عائلي'),
(19313, 19310, 'منتجع علاجي'),
(19314, 19310, 'منتجع جبلي'),
(19315, 19310, 'منتجع بحري'),
(19320, 10315, 'استراحات ومزارع ترفيهية'),
(19321, 19320, 'استراحة'),
(19322, 19320, 'استراحة عائلية'),
(19323, 19320, 'مزرعة ترفيهية'),
(19324, 19320, 'مزرعة مع مسبح'),
(19330, 10315, 'شقق فندقية'),
(19331, 19330, 'شقة فندقية'),
(19332, 19330, 'جناح فندقي'),
(19333, 19330, 'فيلا فندقية'),
(19340, 10315, 'فلل سياحية'),
(19341, 19340, 'فيلا سياحية'),
(19342, 19340, 'فيلا ضمن منتجع'),
(19343, 19340, 'فيلا عطلات'),
(19350, 10315, 'مواقع تخييم ورحلات'),
(19351, 19350, 'موقع تخييم'),
(19352, 19350, 'مخيم سياحي'),
(19353, 19350, 'مخيم صحراوي'),
(19354, 19350, 'موقع كرفانات'),
(19360, 10315, 'بيوت ضيافة'),
(19361, 19360, 'بيت ضيافة'),
(19362, 19360, 'نُزل'),
(19363, 19360, 'نُزل ريفي'),
(19364, 19360, 'بيت تراثي سياحي'),
(19370, 10315, 'مشاريع سياحية'),
(19371, 19370, 'مشروع منتجع'),
(19372, 19370, 'مشروع شاليهات'),
(19373, 19370, 'أرض مشروع سياحي'),
(19374, 19370, 'مجمع سياحي'),
(19380, 10315, 'بيوت ريفية'),
(19381, 19380, 'بيت ريفي'),
(19382, 19380, 'بيت ريفي سياحي'),
(19383, 19380, 'بيت تراثي'),
(19384, 19380, 'بيت طيني'),
(19390, 10315, 'أخرى')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, parent_id = EXCLUDED.parent_id;

-- ════════════════════════════════════════════════
-- STEP 2: REMAP ADS from old categories to new ones
-- ════════════════════════════════════════════════
UPDATE ads SET category_id = 10301 WHERE category_id = 201;  -- شقق للبيع
UPDATE ads SET category_id = 19001 WHERE category_id = 202;  -- أراضي للبيع → أرض سكنية
UPDATE ads SET category_id = 10101 WHERE category_id = 203;  -- فلل وقصور
UPDATE ads SET category_id = 10853 WHERE category_id = 204;  -- عقارات تجارية → محلات تجارية عامة
UPDATE ads SET category_id = 19200 WHERE category_id = 205;  -- مزارع وشاليهات → مزارع زراعية
UPDATE ads SET category_id = 10102 WHERE category_id = 206;  -- بيوت ومنازل → بيوت مستقلة
UPDATE ads SET category_id = 18032 WHERE category_id = 207;  -- عمارات ومجمعات → مباني تجارية
UPDATE ads SET category_id = 10301 WHERE category_id = 208;  -- قيد الإنشاء → شقق للبيع
UPDATE ads SET category_id = 10999 WHERE category_id = 209;  -- عقارات أجنبية → أخرى
UPDATE ads SET category_id = 10999 WHERE category_id = 210;  -- أخرى سكنية → أخرى
UPDATE ads SET category_id = 10015 WHERE category_id = 2015; -- شقق فندقية
UPDATE ads SET category_id = 10302 WHERE category_id = 2016; -- استديوهات
UPDATE ads SET category_id = 10101 WHERE category_id IN (2031, 2032, 2033); -- فلل
UPDATE ads SET category_id = 19232 WHERE category_id = 2051; -- مزارع مع فيلا
UPDATE ads SET category_id = 19301 WHERE category_id = 2052; -- شاليهات خاصة → شاليه مستقل
UPDATE ads SET category_id = 10102 WHERE category_id IN (2061, 2062); -- بيوت مستقلة
UPDATE ads SET category_id = 18033 WHERE category_id = 2071; -- عمارات سكنية → عمارة تجارية
UPDATE ads SET category_id = 18034 WHERE category_id = 2072; -- مجمعات → مجمع تجاري
UPDATE ads SET category_id = 10999 WHERE category_id = 2073; -- سكن طلاب → أخرى
UPDATE ads SET category_id = 10301 WHERE category_id = 2081; -- شقق قيد الإنشاء → شقق للبيع
UPDATE ads SET category_id = 10101 WHERE category_id = 2082; -- فلل عظم → فلل وقصور
UPDATE ads SET category_id = 10999 WHERE category_id = 2101; -- حصص مشاع → أخرى
UPDATE ads SET category_id = 10105 WHERE category_id = 2102; -- أسطح → ملحق / روف

-- ════════════════════════════════════════════════
-- STEP 3: DELETE OLD CATEGORIES (children first)
-- ════════════════════════════════════════════════
DELETE FROM categories WHERE id IN (2015, 2016, 2031, 2032, 2033, 2051, 2052, 2061, 2062, 2071, 2072, 2073, 2081, 2082, 2101, 2102);
DELETE FROM categories WHERE id IN (201, 202, 203, 204, 205, 206, 207, 208, 209, 210);

-- Fix sequence
SELECT setval(pg_get_serial_sequence('categories', 'id'), (SELECT MAX(id) FROM categories), true);

COMMIT;
