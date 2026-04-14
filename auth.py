import os
from datetime import datetime, timedelta
import random
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fallback_secret_for_development_only_12345")
ALGORITHM = "HS256"

# Set to False in production to re-enable all rate limits and cooldowns
TESTING_MODE = True

def create_access_token(data: dict):
    to_encode = data.copy()
    # No expiration - token lives forever
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def check_rate_limit(db: Session, ip_address: str, mobile_number: str, endpoint: str):
    """
    Enforces IP and Mobile Number based rate limits cleanly.
    """
    now = datetime.utcnow()
    
    # 1. IP Limit: Max 5 requests per minute per IP for this endpoint
    one_min_ago = now - timedelta(minutes=1)
    ip_attempts = db.query(models.RateLimitLog).filter(
        models.RateLimitLog.ip_address == ip_address,
        models.RateLimitLog.endpoint == endpoint,
        models.RateLimitLog.created_at >= one_min_ago
    ).count()
    if ip_attempts >= 5:
        raise HTTPException(status_code=429, detail="Too many requests from this IP. Try again in a minute.")

    # 2. Mobile Limit: Max 10 requests per hour per mobile number for this endpoint
    if mobile_number:
        one_hour_ago = now - timedelta(hours=1)
        mobile_attempts = db.query(models.RateLimitLog).filter(
            models.RateLimitLog.mobile_number == mobile_number,
            models.RateLimitLog.endpoint == endpoint,
            models.RateLimitLog.created_at >= one_hour_ago
        ).count()
        if mobile_attempts >= 10:
            raise HTTPException(status_code=429, detail="Too many requests for this mobile number. Try again in an hour.")

    # Log the attempt
    db.add(models.RateLimitLog(ip_address=ip_address, mobile_number=mobile_number, endpoint=endpoint))
    db.commit()

import re

def normalize_jo_phone(phone_number: str) -> str:
    # 1. Remove all spaces, dashes, and extra characters
    cleaned = re.sub(r'[\s\-a-zA-Z]', '', phone_number)
    
    # 2. Add leading prefix conditionally based on inputs
    if cleaned.startswith('+962'):
        cleaned = '0' + cleaned[4:]
    elif cleaned.startswith('00962'):
        cleaned = '0' + cleaned[5:]
    elif cleaned.startswith('962'):
        cleaned = '0' + cleaned[3:]
    elif cleaned.startswith('7'):
        cleaned = '0' + cleaned
        
    # 3. Check invalid characters (if any symbols remain, reject)
    if not cleaned.isdigit():
        raise HTTPException(status_code=400, detail="Mobile number contains invalid characters.")
        
    # 4. Final strict checks for Jordanian format
    if not cleaned.startswith('07'):
        raise HTTPException(status_code=400, detail="Mobile number must start with 07, 7, or 962.")
        
    allowed_prefixes = ['075', '076', '077', '078', '079']
    if cleaned[:3] not in allowed_prefixes:
        raise HTTPException(status_code=400, detail="Invalid Jordanian network prefix.")
        
    if len(cleaned) != 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number length.")
        
    return cleaned

@router.post("/request-otp")
def request_otp(data: schemas.RequestOTP, request: Request, db: Session = Depends(get_db)):
    ip_address = request.client.host
    mobile_number = normalize_jo_phone(data.mobile_number)

    # 1. Check strict rate limits (skip in testing)
    if not TESTING_MODE:
        check_rate_limit(db, ip_address, mobile_number, "request-otp")

    # 2. Check 5-minute cooldown (skip in testing)
    now = datetime.utcnow()
    if not TESTING_MODE:
        five_mins_ago = now - timedelta(minutes=5)
        last_otp = db.query(models.OtpCode).filter(
            models.OtpCode.mobile_number == mobile_number,
            models.OtpCode.created_at >= five_mins_ago
        ).first()

        if last_otp:
            raise HTTPException(status_code=425, detail="Please wait 5 minutes before requesting another OTP.")

    # 3. Generate new 6-digit OTP
    otp_code = f"{random.randint(100000, 999999)}"
    expires_at = now + timedelta(hours=1)

    db_otp = models.OtpCode(
        mobile_number=mobile_number,
        otp_code=otp_code,
        expires_at=expires_at,
        ip_address=ip_address
    )
    db.add(db_otp)
    db.commit()

    # In production, integrate SMS provider (Twilio, MessageBird, etc.) here.
    # For now, we simulate sending SMS by printing to backend console.
    print(f"\n{'='*40}")
    print(f"📲 SMS TO: {mobile_number}")
    print(f"🔑 OTP CODE: {otp_code}")
    print(f"{'='*40}\n")

    return {"status": "success", "message": "OTP sent successfully"}

@router.post("/verify-otp", response_model=schemas.AuthResponse)
def verify_otp(data: schemas.VerifyOTP, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    ip_address = request.client.host
    mobile_number = normalize_jo_phone(data.mobile_number)
    otp_code = data.otp_code

    if not TESTING_MODE:
        check_rate_limit(db, ip_address, mobile_number, "verify-otp")

    # Get the latest OTP request for this number
    db_otp = db.query(models.OtpCode).filter(models.OtpCode.mobile_number == mobile_number).order_by(models.OtpCode.created_at.desc()).first()

    if not db_otp:
        raise HTTPException(status_code=400, detail="No OTP requested for this number.")

    if datetime.utcnow() > db_otp.expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired.")
        
    if db_otp.attempts >= 10:
        raise HTTPException(status_code=400, detail="Too many invalid attempts. Please request a new OTP.")

    if db_otp.otp_code != otp_code:
        db_otp.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP code.")

    # OTP is valid! Time to log them in.
    # 1. Clear the OTP so it can't be reused
    db.delete(db_otp)
    
    # 2. Get or Create User
    is_new_user = False
    user = db.query(models.User).filter(models.User.mobile_number == mobile_number).first()
    if not user:
        is_new_user = True
        user = models.User(mobile_number=mobile_number)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Auto-create metrics for the new user
        metrics = models.UserMetric(user_id=user.id)
        db.add(metrics)
        db.commit()

    # 3. Mint JWT Token
    access_token = create_access_token(data={"sub": str(user.id), "mobile": user.mobile_number})

    # 4. Send welcome notification for new users
    if is_new_user:
        from notifications import send_personal_notification
        background_tasks.add_task(
            send_personal_notification,
            target_user_id=user.id,
            title="مرحباً بك في السوق المفتوح! 🎉",
            body="حسابك جاهز. ابدأ بتصفح الإعلانات أو أضف إعلانك الأول.",
            notification_type="welcome",
            reference_id=None
        )

    return schemas.AuthResponse(token=access_token, user=user)

# Common dependency for protected routes to easily get current user via JWT
def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

@router.get("/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
