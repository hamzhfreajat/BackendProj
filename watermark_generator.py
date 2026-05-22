import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def create_watermark():
    print("Downloading Tajawal font...")
    font_url = "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Bold.ttf"
    font_path = "Tajawal-Bold.ttf"
    if not os.path.exists(font_path):
        urllib.request.urlretrieve(font_url, font_path)
    
    print("Loading logo...")
    logo_path = "../frontend/assets/images/sooqcom_logo_v2.png"
    if not os.path.exists(logo_path):
        print(f"Error: {logo_path} not found.")
        return
        
    logo = Image.open(logo_path).convert("RGBA")
    
    # Scale logo to a reasonable height, e.g., 100px
    target_height = 100
    aspect_ratio = logo.width / logo.height
    new_width = int(target_height * aspect_ratio)
    logo = logo.resize((new_width, target_height), Image.Resampling.LANCZOS)
    
    text = "سوقكم"
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    
    font = ImageFont.truetype(font_path, 80)
    
    # Measure text size
    # In newer Pillow, textsize is deprecated, use textbbox
    dummy_img = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), bidi_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    padding = 20
    # Final image width: logo_width + text_width + padding
    final_width = logo.width + text_width + padding
    final_height = max(logo.height, text_height)
    
    # Create transparent background
    watermark = Image.new("RGBA", (final_width, final_height), (0, 0, 0, 0))
    
    # Paste logo on the left (RTL text typically goes on the left or right, but let's do Logo then Text)
    # The user said "the same with the word سوقكم same as in the header".
    # Usually in Arabic, text is on the left, logo on the right.
    # Let's put Logo on the Right, Text on the Left.
    logo_x = final_width - logo.width
    logo_y = (final_height - logo.height) // 2
    watermark.paste(logo, (logo_x, logo_y), logo)
    
    # Draw Text
    draw = ImageDraw.Draw(watermark)
    text_x = 0
    text_y = (final_height - text_height) // 2 - bbox[1] # Offset vertical alignment
    draw.text((text_x, text_y), bidi_text, font=font, fill=(255, 255, 255, 255))
    
    # Save the output
    os.makedirs("static", exist_ok=True)
    out_path = "static/watermark.png"
    watermark.save(out_path, "PNG")
    print(f"Saved watermark to {out_path}")

if __name__ == "__main__":
    create_watermark()
