import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv()

class ExtractedAdAttributes(BaseModel):
    rooms: Optional[int] = Field(description="Number of rooms, if mentioned")
    bathrooms: Optional[int] = Field(description="Number of bathrooms")
    furnished: Optional[str] = Field(description="Furnished state. Match with: مفروش کامل, فرش فندقي, شبه مفروش, فارغ, جديد لم يسكن")
    floor: Optional[str] = Field(description="Floor level. Match with: تسوية, طابق أرضي, طوابق علوية, رووف")
    key_features: List[str] = Field(description="Array of features like: تدفئة, تكييف إنفيرتر, مصعد, كراج خاص, مطبخ راكب, شحن سيارة كهربائية, etc.")
    target_audience: List[str] = Field(description="Who is this for? e.g. عائلات, عرسان, طالبات, سكن موظفين")
    payment_method: List[str] = Field(description="How payment works? e.g. من المالك, مكتب عقاري, دفع شهري, سنوي, إيجار يومي, تقسيط")
    phone_number: Optional[str] = Field(description="Any extracted Jordanian phone number")

class ExtractedAd(BaseModel):
    post_index: int = Field(description="The index of the post in the prompt array (0 to 9)")
    category_id: int = Field(description="The ID of the category that best matches this post (e.g., 301 for apartments, 101 for cars, etc.)")
    title: str = Field(description="A clean, concise title for the ad (max 80 chars)")
    description: str = Field(description="The full ad text cleaned up")
    price: float = Field(description="The extracted price in JOD. Return 0 if not found")
    attributes: ExtractedAdAttributes = Field(description="Detailed property / vehicle attributes")

gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

posts = []
with open("debug_fb_posts.txt", "r", encoding="utf-8") as f:
    text = f.read()
    parts = text.split("--- POST ")
    for p in parts[1:]:
        t = p.split("TEXT:\n")[-1].split("IMAGES:")[0].strip()
        posts.append(t)

print("Found", len(posts), "posts in dump.")
for idx, p in enumerate(posts[:5]):
    pass

system_instruction = (
    "You are an expert AI data extraction assistant specialized in Jordanian classifieds ( العقارات, السيارات, الوظائف ).\n"
    "You will receive an array of raw text posts from Facebook groups or classifieds sites.\n"
    "1. Read EACH post individually.\n"
    "2. If it is a generic post without a clear ad ('Good morning', 'Please like my page'), SKIP it. Do NOT return it in the JSON array.\n"
    "3. For valid ads, extract the fields exactly as required by the schema.\n"
    f"4. If you can confidently determine the Category ID from this list, use it:\nID: 301 | Name: Apartments\n"
    "If you CANNOT determine the ID, you may leave `category_id` as 0.\n"
    "5. Ensure prices are purely numeric (JOD). Extract any Jordanian phone numbers precisely."
)

model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)

prompts_array = []
for idx, post in enumerate(posts[:5]):
    prompts_array.append(f"POST {idx}:\n{post}")

prompt_text = "Extract the following posts into the JSON Schema array:\n" + "\n---\n".join(prompts_array)

print("Sending to Gemini...")
result = model.generate_content(
    prompt_text,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=list[ExtractedAd],
    ),
)
with open("debug_gemini_output.json", "w", encoding="utf-8") as out_f:
    out_f.write(result.text)
print("Saved to debug_gemini_output.json")
