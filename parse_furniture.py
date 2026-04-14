import re

tree_text = """
├── أثاث غرف المعيشة والجلوس
│   ├── طقم كنب
│   ├── كنب كورنر
│   ├── كنبة سرير
│   ├── كرسي بذراعين
│   ├── كرسي ديكور
│   ├── جلسة أرضية
│   ├── مجلس عربي
│   ├── كرسي استرخاء
│   ├── وحدة تلفزيون
│   ├── طاولة قهوة
│   ├── طاولة جانبية
│   ├── كونسول
│   ├── أثاث غرف معيشة أخرى
├── أثاث غرف النوم
│   ├── غرفة نوم كاملة
│   ├── سرير
│   ├── هيكل سرير
│   ├── رأس سرير
│   ├── خزانة ملابس
│   ├── تسريحة
│   ├── طاولة سرير
│   ├── طاولة جانبية للسرير
│   ├── كرسي غرفة نوم
│   ├── خزانة تخزين
│   ├── خزانة حائط
│   ├── أثاث غرف نوم أخرى
├── الفرشات والمنسوجات
│   ├── فرشة مفرد
│   ├── فرشة مزدوج
│   ├── فرشة أطفال
│   ├── فرشات أخرى
│   ├── وسادة
│   ├── مخدة
│   ├── مفارش سرير
│   ├── بطانية
│   ├── شال
│   ├── غطاء فرشة
│   ├── غطاء وسادة
│   ├── كوشن
│   ├── بشكير
│   ├── منشفة
│   ├── مفروشات وأقمشة أخرى
├── أثاث غرف السفرة
│   ├── طاولة طعام
│   ├── كراسي طعام
│   ├── بنش طعام
│   ├── بوفيه
│   ├── وحدة جانبية
│   ├── خزانة عرض
│   ├── أثاث غرفة طعام أخرى
├── أثاث غرف الأطفال
│   ├── سرير أطفال
│   ├── خزانة أطفال
│   ├── تخزين أطفال
│   ├── مكتب دراسة أطفال
│   ├── كرسي أطفال
│   ├── جلسة أطفال
│   ├── طاولة تبديل
│   ├── تسريحة أطفال
│   ├── أثاث أطفال أخرى
├── أثاث المكاتب والدراسة
│   ├── مكتب
│   ├── كرسي مكتب
│   ├── خزانة تخزين
│   ├── خزانة أرشفة
│   ├── مكتبة
│   ├── رف
│   ├── طاولة اجتماعات
│   ├── مكتب استقبال
│   ├── طاولة دراسة
│   ├── أريكة مكتب
│   ├── أثاث مكتب ودراسة أخرى
├── أثاث الحدائق والخارجية
│   ├── جلسة حديقة
│   ├── طاولة خارجية
│   ├── كرسي خارجي
│   ├── أرجوحة
│   ├── مظلة
│   ├── كرسي استرخاء
│   ├── أثاث خارجي أخرى
├── الإضاءة
│   ├── ثريا
│   ├── إضاءة سقف
│   ├── مصباح طاولة
│   ├── مصباح أرضي
│   ├── إضاءة جدارية
│   ├── إضاءة حدائق
│   ├── أخرى
├── الديكور وإكسسوارات المنزل
│   ├── مرآة
│   ├── لوحة
│   ├── إطار صورة
│   ├── سجادة
│   ├── موكيت
│   ├── ستارة
│   ├── إكسسوارات ستائر
│   ├── فازة
│   ├── نبات زينة
│   ├── ساعة حائط
│   ├── شموع
│   ├── فواحة
│   ├── تحف
│   ├── قطع ديكور صغيرة
│   ├── ديكور أخرى
├── أثاث المطبخ والحمام
│   ├── خزائن مطبخ
│   ├── جزيرة مطبخ
│   ├── كرسي بار
│   ├── خزائن حمام
│   ├── مرآة حمام
│   ├── وحدة تخزين حمام
│   ├── أخرى
├── أخرى
"""

def get_icon(name):
    n = name.lower()
    if 'معيشة' in n or 'جلوس' in n or 'كنب' in n or 'تلفزيون' in n or 'طاولة' in n: return 'weekend'
    elif 'نوم' in n or 'سرير' in n or 'خزانة' in n or 'تسريحة' in n: return 'king_bed'
    elif 'فرش' in n or 'نطانية' in n or 'مخد' in n or 'وساد' in n or 'منشفة' in n or 'شال' in n: return 'layers'
    elif 'طعام' in n or 'سفرة' in n or 'بوفيه' in n: return 'dining'
    elif 'أطفال' in n: return 'child_care'
    elif 'مكتب' in n or 'دراسة' in n or 'رف' in n: return 'desk'
    elif 'حدائق' in n or 'أرجوحة' in n or 'خارجي' in n or 'مظلة' in n: return 'deck'
    elif 'إضاءة' in n or 'مصباح' in n or 'ثريا' in n: return 'lightbulb'
    elif 'ديكور' in n or 'مرآة' in n or 'لوحة' in n or 'سجادة' in n or 'ستارة' in n or 'زينة' in n: return 'imagesearch_roller'
    elif 'مطبخ' in n or 'حمام' in n or 'بار' in n: return 'countertops'
    else: return 'chair'

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

gen_list = parse_tree(tree_text, 7, "7")

generated = [
    '    # ═══════════════════════════════════════════════',
    '    # SECOND-LEVEL — أثاث وديكور (parent=7)',
    '    # ═══════════════════════════════════════════════',
] + gen_list + ['']

print(f"Total Furniture generated: {len(gen_list)}")

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
# Blind append at the end ofCATEGORIES
new_content = re.sub(r'\]\n(\s*)\n\s*def seed\(\):', '\n'.join(generated) + r'\n]\n\n\ndef seed():', content, flags=re.MULTILINE)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated seed_categories.py with the Furniture tree!")
