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
    
    for file in files:
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
                file.file.seek(0)
                r2_client.upload_fileobj(
                    file.file, 
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
                content = await file.read()
                buffer.write(content)
                
            file_url = f"/uploads/{unique_filename}"
            uploaded_urls.append(file_url)
        
    return {"urls": uploaded_urls}
