import os
import re

target_dir = r'd:/open/classifieds-app/frontend/lib/screens'
files = [
    'home_page.dart',
    'categories_page.dart',
    'category_details_page.dart',
    'add_ad_wizard.dart',
    'add_ad_subcategories.dart'
]

new_func = """  IconData _getIconData(String? iconName) {
    if (iconName == null || iconName.isEmpty) return Icons.category;
    switch (iconName) {
      case 'local_fire_department': return Icons.local_fire_department;
      case 'apartment': return Icons.apartment;
      case 'business': return Icons.business;
      case 'directions_car': return Icons.directions_car;
      case 'storefront': return Icons.storefront;
      case 'work': return Icons.work;
      case 'devices': return Icons.devices;
      case 'chair': return Icons.chair;
      case 'checkroom': return Icons.checkroom;
      case 'child_friendly': return Icons.child_friendly;
      case 'pets': return Icons.pets;
      case 'cleaning_services': return Icons.cleaning_services;
      case 'menu_book': return Icons.menu_book;
      case 'health_and_safety': return Icons.health_and_safety;
      case 'grass': return Icons.grass;
      case 'precision_manufacturing': return Icons.precision_manufacturing;
      case 'sports_esports': return Icons.sports_esports;
      case 'vpn_key': return Icons.vpn_key;
      case 'fitness_center': return Icons.fitness_center;
      case 'restaurant': return Icons.restaurant;
      case 'home': return Icons.home;
      case 'landscape': return Icons.landscape;
      case 'miscellaneous_services': return Icons.miscellaneous_services;
      case 'face_retouching_natural': return Icons.face_retouching_natural;
      case 'motorcycle': return Icons.motorcycle;
      case 'holiday_village': return Icons.holiday_village;
      case 'key': return Icons.key;
      case 'sell': return Icons.sell;
      case 'phone_iphone': return Icons.phone_iphone;
      case 'house': return Icons.house;
      default: return Icons.category;
    }
  }"""

for fname in files:
    path = os.path.join(target_dir, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to match the existing _getIconData
    pattern = re.compile(r'\s*IconData\s+_getIconData\s*\(\s*String\?\s*iconName\s*\)\s*\{.*?(?=\s*(?:Color\s+_getColor|IconData\s+_getIconForSubcategory|Widget\s+_build))', re.MULTILINE | re.DOTALL)
    
    match = pattern.search(content)
    if match:
        replaced = content[:match.start()] + '\n' + new_func + '\n' + content[match.end():]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(replaced)
        print(f'Patched {fname}')
    else:
        print(f'Regex failed for {fname}')
