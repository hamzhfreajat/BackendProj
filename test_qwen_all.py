import os, json, sys, io
import re
from openai import OpenAI
from fb_batch_router import _GEMMA_SINGLE_PROMPT

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(os.path.dirname(__file__))

JSON_FILE = r'D:\open\classifieds-app\backend\temp_test_data.json'
OUTPUT_FILE = r'D:\open\classifieds-app\backend\qwen_full_test_results.json'

with open(JSON_FILE, 'r', encoding='utf-8') as f:
    posts = json.load(f)

valid_posts = [p for p in posts if p.get('text', '').strip()]
all_results = []

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

print(f"Starting extraction for {len(valid_posts)} posts using qwen2.5:1.5b...")

for idx, post in enumerate(valid_posts):
    print(f"\n[{idx+1}/{len(valid_posts)}] Processing Post Text -> '{post['text'][:50]}...'", flush=True)
    prompt = _GEMMA_SINGLE_PROMPT.format(post_text=post['text'])
    
    try:
        response = client.chat.completions.create(
            model="qwen2.5:1.5b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1500,
            stream=True
        )
        
        raw, raw_output = "", ""
        print("AI Output: ", end="", flush=True)
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                raw_output += token
                print(token, end="", flush=True)
        print("\n", flush=True)

        raw = raw_output.strip()
        match = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
        if match: raw = match.group(1)
        raw = re.sub(r'[\x00-\x19]', ' ', raw)
        
        # Auto-fix truncated JSON from 1.5b model
        raw = raw.strip()
        open_braces = raw.count('{')
        close_braces = raw.count('}')
        if open_braces > close_braces:
            raw += '}' * (open_braces - close_braces)
            
        try:
            parsed_dict = json.loads(raw)
            print(f" -> SUCCESS (Category: {parsed_dict.get('category_name')})", flush=True)
        except json.JSONDecodeError as e:
            print(f" -> JSON ERROR: {e}\nRAW DATA:\n{raw}\n", flush=True)
            continue
            
        all_results.append({
            "post_index": post.get("index", idx+1),
            "original_text": post['text'],
            "AI_JSON": parsed_dict
        })
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
            json.dump(all_results, out, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f" -> FAILED ({e})", flush=True)

print("\n--- ALL POSTS PROCESSED SUCCESSFULLY ---")
