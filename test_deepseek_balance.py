import requests
import os
from dotenv import load_dotenv

load_dotenv('.env')
key = os.getenv('DEEPSEEK_API_KEY')
print("Key:", key[:5])

payload = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "respond in json format"}],
    "response_format": {"type": "json_object"}
}
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

res = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers)
print(res.status_code)
print(res.text[:200])
