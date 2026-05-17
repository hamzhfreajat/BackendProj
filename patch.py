import sys

def patch():
    file_path = "d:/open/classifieds-app/backend/main.py"
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    original = "".join(lines[938:1049])
    replacement = "".join(lines[1193:1325])
    
    if "def read_ads" not in "".join(lines[839:845]):
        print("read_ads is not where expected!")
        return
        
    text = "".join(lines)
    if original not in text:
        print("Original text not found! Lines might have shifted.")
        return
        
    new_text = text.replace(original, replacement)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_text)
        
    print("Patched successfully!")

if __name__ == "__main__":
    patch()
