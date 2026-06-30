import sys
filepath = r"D:\open\classifieds-app\backend\main.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to find "if search:" inside read_ads and get_ads_count
# and insert the ignore_location logic.

# In read_ads:
# def read_ads(...
#     query = db.query(models.Ad)
#     ...
#     ignore_location = False
#     if search:
#         from search_parser import QueryParserService
#         parsed = QueryParserService.parse(search)
#         if parsed.location:
#             ignore_location = True

# Replace     if location: with     if location and not ignore_location:

def patch_func(func_name, code_content):
    idx = code_content.find(f'def {func_name}(')
    if idx == -1: return code_content
    
    # find     if search:
    search_idx = code_content.find('    if search:', idx)
    if search_idx == -1: return code_content
    
    insertion = '''    ignore_location = False
    if search:
        try:
            from search_parser import QueryParserService
            parsed = QueryParserService.parse(search)
            if parsed.location:
                ignore_location = True
        except:
            pass
'''
    code_content = code_content[:search_idx] + insertion + code_content[search_idx:]
    
    # Now find     if location: after this point
    loc_idx = code_content.find('    if location:', search_idx + len(insertion))
    if loc_idx != -1 and loc_idx < code_content.find('def ', search_idx):
        code_content = code_content[:loc_idx] + '    if location and not ignore_location:' + code_content[loc_idx + 16:]
        
    return code_content

content = patch_func('read_ads', content)
content = patch_func('get_ads_count', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched main.py")
