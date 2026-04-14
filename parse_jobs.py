import re

jobs_tree = """
├── وظائف إدارية
│   ├── إدارة
│   ├── سكرتاريا
│   ├── استقبال
│   ├── إدخال بيانات
│   ├── خدمة عملاء
│   ├── موارد بشرية
│   ├── أخرى
├── وظائف مبيعات وتسويق
│   ├── مبيعات
│   ├── تسويق
│   ├── تسويق إلكتروني
│   ├── ترويج
│   ├── كول سنتر
│   ├── أخرى
├── وظائف محاسبة ومالية
│   ├── محاسبة
│   ├── مالية
│   ├── تدقيق
│   ├── أمين صندوق
│   ├── أخرى
├── وظائف تكنولوجيا المعلومات
│   ├── برمجة
│   ├── دعم فني
│   ├── شبكات
│   ├── قواعد بيانات
│   ├── تحليل نظم
│   ├── تصميم
│   ├── أخرى
├── وظائف تعليم وتدريب
│   ├── تدريس
│   ├── تدريب
│   ├── حضانة
│   ├── تعليم خاص
│   ├── أخرى
├── وظائف طبية وصحية
│   ├── طبيب
│   ├── ممرض
│   ├── صيدلي
│   ├── مختبر
│   ├── علاج طبيعي
│   ├── أشعة
│   ├── أخرى
├── وظائف مطاعم وفنادق
│   ├── طباخ
│   ├── مساعد مطبخ
│   ├── نادل
│   ├── باريستا
│   ├── استقبال فندق
│   ├── تنظيف
│   ├── أخرى
├── وظائف عمال ومهن
│   ├── عامل
│   ├── سائق
│   ├── حارس
│   ├── كهربائي
│   ├── سباك
│   ├── نجار
│   ├── حداد
│   ├── دهان
│   ├── بناء
│   ├── أخرى
├── وظائف هندسة
│   ├── هندسة مدنية
│   ├── هندسة كهربائية
│   ├── هندسة ميكانيكية
│   ├── هندسة معمارية
│   ├── هندسة برمجيات
│   ├── أخرى
├── وظائف توصيل ونقل
│   ├── توصيل طلبات
│   ├── سائق خاص
│   ├── سائق شاحنة
│   ├── سائق تكسي
│   ├── نقل
│   ├── أخرى
├── وظائف تجميل وصالونات
│   ├── حلاقة
│   ├── تصفيف شعر
│   ├── تجميل
│   ├── مكياج
│   ├── عناية بالبشرة
│   ├── أخرى
├── وظائف مصانع
│   ├── إنتاج
│   ├── تعبئة وتغليف
│   ├── تشغيل
│   ├── مراقبة جودة
│   ├── أخرى
├── وظائف زراعة
│   ├── مزارع
│   ├── زراعة
│   ├── تربية حيوانات
│   ├── أخرى
├── وظائف قانونية
│   ├── محامي
│   ├── قانون
│   ├── سكرتاريا قانونية
│   ├── أخرى
├── وظائف إعلام وتصميم
│   ├── تصميم
│   ├── تصوير
│   ├── مونتاج
│   ├── كتابة محتوى
│   ├── أخرى
├── وظائف عن بعد
│   ├── عمل من المنزل
│   ├── عمل جزئي
│   ├── عمل حر
│   ├── أخرى
├── وظائف أخرى
│   ├── أخرى
"""

seekers_tree = """
├── باحث عن عمل إداري
│   ├── إدارة
│   ├── سكرتاريا
│   ├── استقبال
│   ├── إدخال بيانات
│   ├── خدمة عملاء
│   ├── موارد بشرية
│   ├── أخرى
├── باحث عن عمل مبيعات وتسويق
│   ├── مبيعات
│   ├── تسويق
│   ├── تسويق إلكتروني
│   ├── ترويج
│   ├── كول سنتر
│   ├── أخرى
├── باحث عن عمل محاسبة ومالية
│   ├── محاسبة
│   ├── مالية
│   ├── تدقيق
│   ├── أمين صندوق
│   ├── أخرى
├── باحث عن عمل تكنولوجيا المعلومات
│   ├── برمجة
│   ├── دعم فني
│   ├── شبكات
│   ├── قواعد بيانات
│   ├── تحليل نظم
│   ├── تصميم
│   ├── أخرى
├── باحث عن عمل تعليم وتدريب
│   ├── تدريس
│   ├── تدريب
│   ├── حضانة
│   ├── تعليم خاص
│   ├── أخرى
├── باحث عن عمل طبي وصحي
│   ├── طبيب
│   ├── ممرض
│   ├── صيدلي
│   ├── مختبر
│   ├── علاج طبيعي
│   ├── أشعة
│   ├── أخرى
├── باحث عن عمل مطاعم وفنادق
│   ├── طباخ
│   ├── مساعد مطبخ
│   ├── نادل
│   ├── باريستا
│   ├── استقبال فندق
│   ├── تنظيف
│   ├── أخرى
├── باحث عن عمل عمال ومهن
│   ├── عامل
│   ├── سائق
│   ├── حارس
│   ├── كهربائي
│   ├── سباك
│   ├── نجار
│   ├── حداد
│   ├── دهان
│   ├── بناء
│   ├── أخرى
├── باحث عن عمل هندسة
│   ├── هندسة مدنية
│   ├── هندسة كهربائية
│   ├── هندسة ميكانيكية
│   ├── هندسة معمارية
│   ├── هندسة برمجيات
│   ├── أخرى
├── باحث عن عمل توصيل ونقل
│   ├── توصيل طلبات
│   ├── سائق خاص
│   ├── سائق شاحنة
│   ├── سائق تكسي
│   ├── نقل
│   ├── أخرى
├── باحث عن عمل تجميل وصالونات
│   ├── حلاقة
│   ├── تصفيف شعر
│   ├── تجميل
│   ├── مكياج
│   ├── عناية بالبشرة
│   ├── أخرى
├── باحث عن عمل مصانع
│   ├── إنتاج
│   ├── تعبئة وتغليف
│   ├── تشغيل
│   ├── مراقبة جودة
│   ├── أخرى
├── باحث عن عمل زراعة
│   ├── مزارع
│   ├── زراعة
│   ├── تربية حيوانات
│   ├── أخرى
├── باحث عن عمل قانوني
│   ├── محامي
│   ├── قانون
│   ├── سكرتاريا قانونية
│   ├── أخرى
├── باحث عن عمل إعلام وتصميم
│   ├── تصميم
│   ├── تصوير
│   ├── مونتاج
│   ├── كتابة محتوى
│   ├── أخرى
├── باحث عن عمل عن بعد
│   ├── عمل من المنزل
│   ├── عمل جزئي
│   ├── عمل حر
│   ├── أخرى
├── باحث عن أي عمل
│   ├── أي عمل
│   ├── عمل بدوام كامل
│   ├── عمل بدوام جزئي
│   ├── أخرى
├── أخرى
│   ├── أخرى
"""

def get_icon(name):
    n = name.lower()
    if 'إدار' in n or 'سكرتاريا' in n or 'إدخال بيانات' in n or 'عملاء' in n or 'بشرية' in n: return 'manage_accounts'
    elif 'مبيعات' in n or 'تسويق' in n or 'ترويج' in n or 'كول سنتر' in n: return 'campaign'
    elif 'محاسبة' in n or 'مالية' in n or 'تدقيق' in n or 'صندوق' in n: return 'account_balance'
    elif 'تكنولوجيا' in n or 'برمجة' in n or 'شبكات' in n or 'دعم فني' in n or 'قواعد بيانات' in n: return 'computer'
    elif 'تعليم' in n or 'تدريب' in n or 'تدريس' in n or 'حضانة' in n: return 'school'
    elif 'طبي' in n or 'صحي' in n or 'ممرض' in n or 'صيدلي' in n or 'مختبر' in n or 'علاج' in n or 'أشعة' in n: return 'local_hospital'
    elif 'مطاعم' in n or 'فنادق' in n or 'طباخ' in n or 'نادل' in n or 'باريستا' in n or 'مطبخ' in n: return 'restaurant'
    elif 'عمال' in n or 'مهن' in n or 'نجار' in n or 'حداد' in n or 'كهربائي' in n or 'سباك' in n or 'بناء' in n or 'دهان' in n: return 'handyman'
    elif 'هندسة' in n: return 'architecture'
    elif 'توصيل' in n or 'نقل' in n or 'سائق' in n or 'تكسي' in n or 'شاحنة' in n: return 'local_shipping'
    elif 'تجميل' in n or 'صالونات' in n or 'حلاقة' in n or 'شعر' in n or 'مكياج' in n or 'بشرة' in n: return 'content_cut'
    elif 'مصانع' in n or 'إنتاج' in n or 'تعبئة' in n or 'تشغيل' in n or 'جودة' in n: return 'factory'
    elif 'زراعة' in n or 'مزارع' in n or 'حيوانات' in n: return 'agriculture'
    elif 'قانون' in n or 'محامي' in n: return 'gavel'
    elif 'إعلام' in n or 'تصميم' in n or 'تصوير' in n or 'مونتاج' in n or 'محتوى' in n: return 'camera_alt'
    elif 'عن بعد' in n or 'منزل' in n or 'جزئي' in n or 'حر' in n: return 'laptop_mac'
    elif 'أي عمل' in n or 'دوام' in n: return 'work_outline'
    else: return 'work'

def parse_tree(lines_text, parent_id, prefix):
    lines = lines_text.strip().split('\n')
    gen = []
    l1_idx = 0
    l2_idx = 0
    current_l1_id = None
    for line in lines:
        if line.startswith('├──'):
            l1_idx += 1
            name = line.replace('├──', '').strip()
            icon = get_icon(name)
            current_l1_id = int(f"{prefix}{l1_idx:02d}")
            gen.append(f'    ({current_l1_id}, {parent_id}, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
            l2_idx = 0
        elif line.startswith('│   ├──'):
            l2_idx += 1
            name = line.replace('│   ├──', '').strip()
            icon = get_icon(name)
            l2_id = int(f"{current_l1_id}{l2_idx:02d}")
            gen.append(f'    ({l2_id}, {current_l1_id}, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
    return gen

jobs_gen = parse_tree(jobs_tree, 6, "6")
seekers_gen = parse_tree(seekers_tree, 14, "14")

generated = [
    '    # ═══════════════════════════════════════════════',
    '    # SECOND-LEVEL — وظائف شاغرة (parent=6)',
    '    # ═══════════════════════════════════════════════',
] + jobs_gen + [
    '',
    '    (14, None, "باحثين عن عمل", "سير ذاتية، وباحثين عن وظائف", "person_search", "#00BCD4", None, {"en": ["Job Seekers"]}),',
    '    # ═══════════════════════════════════════════════',
    '    # SECOND-LEVEL — باحثين عن عمل (parent=14)',
    '    # ═══════════════════════════════════════════════'
] + seekers_gen + ['']

print(f"Total JOBS generated: {len(jobs_gen)}")
print(f"Total SEEKERS generated: {len(seekers_gen)}")

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I will find the block of old 6xx definitions and erase them.
# The old 6xx block started around `# SECOND-LEVEL — وظائف شاغرة (parent=6)`
# But to be completely safe, I am going to erase them from DB via a separate script anyway.
# Here I will just blindly append the new blocks at the end.
import re
new_content = re.sub(r'\]\n(\s*)\n\s*def seed\(\):', '\n'.join(generated) + r'\n]\n\n\ndef seed():', content, flags=re.MULTILINE)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated seed_categories.py with both trees!")
