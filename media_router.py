import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List
import uuid

import boto3
from botocore.client import Config

# Define a simple media router
router = APIRouter(prefix="/api/media", tags=["media"])

def get_r2_client():
    from dotenv import load_dotenv
    load_dotenv('.env') # Force reload in case
    
    ak = os.getenv("R2_ACCESS_KEY_ID")
    sk = os.getenv("R2_SECRET_ACCESS_KEY")
    eu = os.getenv("R2_ENDPOINT_URL")
    
    print(f"DEBUG R2 Setup -> AK: {bool(ak)}, EU: {bool(eu)}")
    
    if not ak or not eu:
        return None
    return boto3.client(
        's3',
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        endpoint_url=eu,
        region_name="auto",
        config=Config(signature_version='s3v4')
    )

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_media(files: List[UploadFile] = File(...)):
    """
    Receives multiple files, saves them to Cloudflare R2 (or locally if missing config),
    and returns a list of URLs pointing to the saved files.
    """
    uploaded_urls = []
    
    r2_client = get_r2_client()
    
    from fb_batch_router import check_image_bytes_for_watermark
    
    for file in files:
        # Check for watermarks on image uploads
        file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        is_image = file.content_type and file.content_type.startswith('image/')
        if not is_image and file_ext in ['.jpg', '.jpeg', '.png', '.webp', '.heic']:
            is_image = True
            
        if is_image:
            content = await file.read()
            if check_image_bytes_for_watermark(content):
                raise HTTPException(
                    status_code=400, 
                    detail="عذراً، الصورة المرفقة تحتوي على شعارات لمواقع أخرى أو نصوص إضافية تمنع نشرها. يرجى اختيار صورة اخرى."
                )
            
            # --- APPLY WATERMARK ---
            try:
                from PIL import Image
                import io
                
                uploaded_img = Image.open(io.BytesIO(content)).convert("RGBA")
                watermark_path = "static/watermark.png"
                if os.path.exists(watermark_path):
                    watermark = Image.open(watermark_path).convert("RGBA")
                    
                    target_width = int(uploaded_img.width * 0.25)
                    target_width = max(100, min(target_width, 800))
                    
                    aspect_ratio = watermark.width / watermark.height
                    target_height = int(target_width / aspect_ratio)
                    watermark = watermark.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    
                    padding = int(uploaded_img.width * 0.03)
                    position = (padding, uploaded_img.height - watermark.height - padding)
                    
                    composite = Image.new("RGBA", uploaded_img.size)
                    composite.paste(uploaded_img, (0,0))
                    composite.paste(watermark, position, mask=watermark)
                    
                    if file_ext in ['.jpg', '.jpeg']:
                        final_img = composite.convert("RGB")
                        save_format = "JPEG"
                    else:
                        final_img = composite
                        save_format = "PNG"
                        
                    out_buffer = io.BytesIO()
                    final_img.save(out_buffer, format=save_format, quality=90)
                    content = out_buffer.getvalue()
            except Exception as e:
                print(f"Failed to apply watermark: {e}")
            # -----------------------
            
            file_obj_to_upload = io.BytesIO(content)
        else:
            file_obj_to_upload = file.file
            file_obj_to_upload.seek(0)

        # Generate a unique filename to prevent collisions
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        r2_client = get_r2_client()
        bucket_name = os.getenv("R2_BUCKET_NAME", "joapp-ads")
        public_url = os.getenv("R2_PUBLIC_URL", "https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev")

        if r2_client:
            # Upload to Cloudflare R2
            try:
                print(f"Uploading {unique_filename} to Cloudflare R2 bucket: {bucket_name}...")
                file_obj_to_upload.seek(0)
                r2_client.upload_fileobj(
                    file_obj_to_upload, 
                    bucket_name, 
                    unique_filename,
                    ExtraArgs={'ContentType': file.content_type or 'application/octet-stream'}
                )
                
                # Construct public URL
                public_url_base = public_url.rstrip('/')
                file_url = f"{public_url_base}/{unique_filename}"
                uploaded_urls.append(file_url)
                print(f"R2 Upload SUCCESS! -> {file_url}")
                
            except Exception as e:
                print(f"R2 Upload Exception: {e}")
                raise HTTPException(status_code=500, detail="Failed to upload image to Cloudflare R2")
        else:
            # Fallback to Local Upload
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            with open(file_path, "wb") as buffer:
                file_obj_to_upload.seek(0)
                buffer.write(file_obj_to_upload.read())
                
            file_url = f"/uploads/{unique_filename}"
            uploaded_urls.append(file_url)
        
    return {"urls": uploaded_urls}

@router.post("/check-watermarks")
async def check_watermarks(files: List[UploadFile] = File(...)):
    """
    Receives multiple files and ONLY checks them for watermarks.
    Returns 200 OK if clean, 400 Bad Request if a watermark is found.
    """
    from fb_batch_router import check_image_bytes_for_watermark
    
    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        is_image = file.content_type and file.content_type.startswith('image/')
        if not is_image and file_ext in ['.jpg', '.jpeg', '.png', '.webp', '.heic']:
            is_image = True
            
        if is_image:
            content = await file.read()
            if check_image_bytes_for_watermark(content):
                raise HTTPException(
                    status_code=400, 
                    detail="عذراً، الصورة المرفقة تحتوي على شعارات لمواقع أخرى أو نصوص إضافية تمنع نشرها. يرجى اختيار صورة طبيعية."
                )
    return {"status": "clean"}
