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
│   ├── عربة ضيافة
│   ├── ديكور مدفأة
│   ├── أثاث غرف معيشة أخرى
├── أثاث غرف النوم
│   ├── غرفة نوم كاملة
│   ├── سرير
│   ├── هيكل سرير
│   ├── رأس سرير
│   ├── خزانة ملابس
│   ├── تسريحة
│   ├── طاولة سرير
│   ├── طاولة جانبية
│   ├── كرسي غرفة نوم
│   ├── خزانة أدراج
│   ├── خزانة حائط
│   ├── حامل ملابس
│   ├── أثاث غرف نوم أخرى
├── الفرشات والمنسوجات
│   ├── فرشة
│   ├── لباد فرشة
│   ├── غطاء فرشة
│   ├── وسادة
│   ├── لحاف
│   ├── غطاء لحاف
│   ├── مفارش سرير
│   ├── بطانية
│   ├── شال
│   ├── كوشن
│   ├── بشكير
│   ├── منشفة
│   ├── روب حمام
│   ├── مفروشات أخرى
├── أثاث غرف السفرة
│   ├── طاولة طعام
│   ├── كراسي طعام
│   ├── بنش طعام
│   ├── بوفيه
│   ├── وحدة جانبية
│   ├── خزانة عرض
│   ├── خزانة مشروبات
│   ├── أثاث غرفة طعام أخرى
├── أثاث المداخل والتنظيم
│   ├── رف أحذية
│   ├── علاقة ملابس
│   ├── علاقة معاطف
│   ├── صندوق تخزين
│   ├── ترنك
│   ├── فاصل غرف
│   ├── أخرى
├── أثاث غرف الأطفال
│   ├── سرير أطفال
│   ├── سرير طابقين
│   ├── خزانة أطفال
│   ├── تخزين ألعاب
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
│   ├── رفوف
│   ├── طاولة اجتماعات
│   ├── مكتب استقبال
│   ├── طاولة دراسة
│   ├── أريكة مكتب
│   ├── واقي أرضية كرسي
│   ├── أثاث مكتب أخرى
├── أثاث الحدائق والخارجية
│   ├── جلسة حديقة
│   ├── طاولة خارجية
│   ├── كرسي خارجي
│   ├── أرجوحة
│   ├── هاموك
│   ├── مظلة
│   ├── كرسي استرخاء
│   ├── دفاية خارجية
│   ├── أثاث خارجي أخرى
├── الإضاءة
│   ├── ثريا
│   ├── إضاءة سقف
│   ├── سبوت لايت
│   ├── مصباح طاولة
│   ├── مصباح أرضي
│   ├── إضاءة جدارية
│   ├── إضاءة حدائق
│   ├── إضاءة طاقة شمسية
│   ├── إضاءة ديكور
│   ├── أخرى
├── الديكور وإكسسوارات المنزل
│   ├── مرآة
│   ├── لوحة
│   ├── إطار صورة
│   ├── سجادة
│   ├── موكيت
│   ├── دعاسة
│   ├── ستارة
│   ├── إكسسوارات ستائر
│   ├── فازة
│   ├── نبات زينة
│   ├── ساعة حائط
│   ├── شموع
│   ├── فواحة
│   ├── مبخرة
│   ├── تحف
│   ├── ورق جدران
│   ├── ملصقات جدران
│   ├── نافورة ديكور
│   ├── ديكور أخرى
├── أثاث المطبخ والحمام والغسيل
│   ├── خزائن مطبخ
│   ├── جزيرة مطبخ
│   ├── كرسي بار
│   ├── خزائن حمام
│   ├── مرآة حمام
│   ├── طاولة كوي
│   ├── منشر غسيل
│   ├── أخرى
├── أخرى
"""

def get_icon(name):
    n = name.lower()
    if 'معيشة' in n or 'جلوس' in n or 'كنب' in n or 'تلفزيون' in n or 'طاولة' in n or 'مدفأة' in n: return 'weekend'
    elif 'نوم' in n or 'سرير' in n or 'خزانة' in n or 'تسريحة' in n: return 'king_bed'
    elif 'فرش' in n or 'بطانية' in n or 'مخد' in n or 'وساد' in n or 'منشفة' in n or 'شال' in n or 'لحاف' in n or 'روب حمام' in n: return 'layers'
    elif 'طعام' in n or 'سفرة' in n or 'بوفيه' in n or 'مشروبات' in n: return 'dining'
    elif 'أطفال' in n or 'ألعاب' in n: return 'child_care'
    elif 'مكتب' in n or 'دراسة' in n or 'رف' in n: return 'desk'
    elif 'حدائق' in n or 'أرجوحة' in n or 'خارجي' in n or 'مظلة' in n or 'دفاية' in n or 'هاموك' in n: return 'deck'
    elif 'إضاءة' in n or 'مصباح' in n or 'ثريا' in n or 'سبوت' in n: return 'lightbulb'
    elif 'ديكور' in n or 'مرآة' in n or 'لوحة' in n or 'سجادة' in n or 'ستارة' in n or 'زينة' in n or 'ورق جدران' in n or 'نافورة' in n: return 'imagesearch_roller'
    elif 'مطبخ' in n or 'حمام' in n or 'بار' in n or 'كوي' in n or 'غسيل' in n: return 'countertops'
    elif 'مداخل' in n or 'أحذية' in n or 'علاقة' in n or 'صندوق' in n or 'ترنك' in n or 'فاصل' in n: return 'door_front'
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
] + gen_list

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
skip = False
for line in lines:
    if line.strip() == ']':
        # we reached what should be the end of the CATEGORIES list, stop.
        break
    
    # Let's deal with the corrupted line if it has literals.
    # Actually wait, we just skip from the first time we see:  # SECOND-LEVEL — أثاث وديكور (parent=7)
    # Even if it's corrupted, we will catch the literal string `# SECOND-LEVEL`
    if '# SECOND-LEVEL' in line and '(parent=7)' in line and not '\\n' in line:
        skip = True
    
    if skip:
        continue
        
    out_lines.append(line)

# Now out_lines contains everything up to the first injection.
# We append the new generated lines to out_lines
for gl in generated:
    out_lines.append(gl + '\n')

# Then we close the list and the function
out_lines.append(']\n\n\ndef seed():\n')

# And now we get the rest of the file (from def seed(): to end) from the original file
in_seed_func = False
for line in lines:
    if line.startswith('def seed():'):
        in_seed_func = True
        continue
    
    if in_seed_func:
        out_lines.append(line)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(''.join(out_lines))

print(f"Total Expanded Furniture inserted: {len(generated)}")
