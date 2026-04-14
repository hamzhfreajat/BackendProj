"""
Convert category icon PNGs to small base64 data URIs and store them directly in the DB.
This eliminates network requests for icons entirely, fixing ngrok HTTP/2 stream limits.
"""
import os, sys, codecs, base64
from io import BytesIO

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

from database import SessionLocal
from models import Category

ICON_DIR = os.path.join(os.path.dirname(__file__), "uploads", "icons")

# Map category IDs to icon filenames
ICON_MAP = {
    1: "real_estate.png",
    2: "rental.png",
    3: "vehicles.png",
    4: "services.png",
    5: "electronics.png",
    6: "furniture.png",
    7: "fashion.png",
    8: "kids.png",
    9: "pets.png",
    10: "jobs.png",
    11: "education.png",
    12: "sports.png",
    13: "food.png",
}

def png_to_base64_datauri(filepath, size=48):
    """Resize PNG to small icon and convert to base64 data URI."""
    img = Image.open(filepath)
    img = img.convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    
    buffer = BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    b64 = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f"data:image/png;base64,{b64}"

def main():
    db = SessionLocal()
    updated = 0
    
    for cat_id, icon_file in ICON_MAP.items():
        filepath = os.path.join(ICON_DIR, icon_file)
        if not os.path.exists(filepath):
            print(f"  SKIP: {icon_file} not found")
            continue
            
        data_uri = png_to_base64_datauri(filepath)
        cat = db.query(Category).filter(Category.id == cat_id).first()
        if cat:
            cat.icon_name = data_uri
            updated += 1
            print(f"  OK: {cat.name} -> base64 ({len(data_uri)} chars)")
    
    db.commit()
    print(f"\nUpdated {updated} categories with base64 data URIs.")
    db.close()

if __name__ == "__main__":
    main()
