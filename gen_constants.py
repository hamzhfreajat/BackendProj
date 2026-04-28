def generate_constants():
    with open("real_estate_mappings.txt", "r", encoding="utf-8") as f:
        content = f.read()
        
    parts = content.split("=== CITIES & REGIONS ===")
    cats = parts[0].replace("=== CATEGORIES ===", "").strip()
    locs = parts[1].strip()
    
    with open("extraction_constants.py", "w", encoding="utf-8") as f:
        f.write("# Auto-generated constants for AI Prompting\n\n")
        f.write("REAL_ESTATE_CATEGORIES = \"\"\"\\\n")
        f.write(cats)
        f.write("\n\"\"\"\n\n")
        
        f.write("LOCATIONS = \"\"\"\\\n")
        f.write(locs)
        f.write("\n\"\"\"\n")

if __name__ == "__main__":
    generate_constants()
