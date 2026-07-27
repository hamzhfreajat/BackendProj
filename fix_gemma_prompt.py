import sys

filepath = 'fb_batch_router.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('single_prompt = _GEMMA_SINGLE_PROMPT.format(\n                post_text=post.text\n            )', 'single_prompt = _GEMMA_SINGLE_PROMPT.format(\n                post_text=post.text,\n                dynamic_location_rules=dynamic_rules_str\n            )')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed Gemma format call")
