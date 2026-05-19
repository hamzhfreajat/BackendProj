import requests

url = "https://ocr.sooq-com.com/api/detect"

# Download a sample image (e.g. Google logo)
img_resp = requests.get("https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png")
image_bytes = img_resp.content

print("Sending to OCR service...")
try:
    files = {"file": ("image.png", image_bytes, "image/png")}
    resp = requests.post(url, files=files, timeout=15)
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print("Error:", e)
