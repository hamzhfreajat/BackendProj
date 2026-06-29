import os
from datetime import datetime, timedelta
import secrets
from typing import List
import jwt
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

import time
import models
import schemas
from database import get_db
from passlib.context import CryptContext

try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_connect_timeout=1)
    redis_client.ping()
    USING_REDIS = True
except Exception:
    USING_REDIS = False
    redis_client = None

# Fallback in-memory stores
IP_RATE_LIMITS = {}
REVOKED_TOKENS = set()

def revoke_token(token: str):
    if USING_REDIS:
        redis_client.setex(f"revoked_token:{token}", 60 * 60 * 24 * 7, "revoked")
    else:
        REVOKED_TOKENS.add(token)

def is_token_revoked(token: str) -> bool:
    if USING_REDIS:
        return redis_client.exists(f"revoked_token:{token}") == 1
    return token in REVOKED_TOKENS


from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from security_events import log_rate_limit_exceeded, log_auth_failure, log_auth_success, log_token_revocation, log_user_logout, log_jwt_forgery_attempt, log_expired_token
import logging


def send_whatsapp_otp(mobile_number: str, otp_code: str):
    token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    if not token:
        print("WARNING: WHATSAPP_ACCESS_TOKEN not set.")
        return

    wa_number = "962" + mobile_number[1:] if mobile_number.startswith("0") else mobile_number

    url = "https://graph.facebook.com/v25.0/1027970960410357/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": wa_number,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US"
            }
        }
    }
    
    # Standard hello_world template expects 0 parameters.
    # To pass OTP, you MUST register an Authentication template with a {{1}} parameter.
    # We are omitting components for 'hello_world' to prevent API 400 Bad Request crash.
    if payload["template"]["name"] != "hello_world":
        payload["template"]["components"] = [
            {
                "type": "body",
                "parameters": [{"type": "text", "text": str(otp_code)}]
            },
            {
                "type": "button",
                "sub_type": "url",
                "index": "0",
                "parameters": [{"type": "text", "text": str(otp_code)}]
            }
        ]

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        print(f"WhatsApp OTP sent to {wa_number}")
    except requests.exceptions.RequestException as e:
        print(f"WhatsApp API Error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("CRITICAL: JWT_SECRET_KEY environment variable is not set. Refusing to start.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 Days

# Disable testing mode in production to re-enable rate limits
TESTING_MODE = os.environ.get("ENV", "development") != "production"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
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

def get_rate_limiter(requests: int, window: int):
    def dependency(request: Request):
        if TESTING_MODE:
            return True
        ip = get_real_ip(request)
        current_time = time.time()
        
        if USING_REDIS:
            key = f"rate_limit:{request.url.path}:{ip}"
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, window)
            elif current > requests:
                log_rate_limit_exceeded(ip, request.url.path)
                raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        else:
            # Memory fallback (not distributed)
            if ip not in IP_RATE_LIMITS:
                IP_RATE_LIMITS[ip] = []
            IP_RATE_LIMITS[ip] = [t for t in IP_RATE_LIMITS[ip] if current_time - t < window]
            if len(IP_RATE_LIMITS[ip]) >= requests:
                log_rate_limit_exceeded(ip, request.url.path)
                raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
            IP_RATE_LIMITS[ip].append(current_time)
        return True
    return dependency

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

def get_real_ip(request: Request) -> str:
    # ProxyHeadersMiddleware sets request.client.host based on X-Forwarded-For if available
    # But we can also manually check CF-Connecting-IP for Cloudflare if needed
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip
    
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
        
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"

@router.post("/request-otp")
def request_otp(data: schemas.RequestOTP, request: Request, db: Session = Depends(get_db)):
    raise HTTPException(status_code=404, detail="OTP authentication is currently disabled.")
#     ip_address = get_real_ip(request)
#     mobile_number = normalize_jo_phone(data.mobile_number)
# 
#     # 1. Check strict rate limits (skip in testing)
#     if not TESTING_MODE:
#         check_rate_limit(db, ip_address, mobile_number, "request-otp")
# 
#     # 2. Check max 3 requests per 10 minutes (skip in testing)
#     now = datetime.utcnow()
#     if not TESTING_MODE:
#         ten_mins_ago = now - timedelta(minutes=10)
#         recent_otps_count = db.query(models.OtpCode).filter(
#             models.OtpCode.mobile_number == mobile_number,
#             models.OtpCode.created_at >= ten_mins_ago
#         ).count()
# 
#         if recent_otps_count >= 3:
#             raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait 10 minutes.")
# 
#     # 3. Generate new 6-digit OTP securely
#     otp_code = str(secrets.randbelow(900000) + 100000)
#     # Security Gap Fix: Hash OTP before storing
#     hashed_otp = get_password_hash(otp_code)
#     # Expire OTP after 5 minutes
#     expires_at = now + timedelta(minutes=5)
# 
#     db_otp = models.OtpCode(
#         mobile_number=mobile_number,
#         otp_code=hashed_otp,
#         expires_at=expires_at,
#         ip_address=ip_address
#     )
#     db.add(db_otp)
#     db.commit()
# 
#     # Send via WhatsApp or SMS
#     if data.method == "sms":
#         print(f"*** PLACEHOLDER SMS SENT TO {mobile_number}: YOUR OTP IS {otp_code} ***")
#     else:
#         # Default to whatsapp
#         send_whatsapp_otp(mobile_number, otp_code)
# 
#     return {"status": "success", "message": f"OTP sent successfully via {data.method or 'whatsapp'}"}

@router.post("/admin-login", response_model=schemas.AuthResponse, dependencies=[Depends(get_rate_limiter(5, 60))])
def admin_login(data: schemas.AdminLogin, request: Request, db: Session = Depends(get_db)):
    """
    Standard Username & Password login specifically designed for strictly Admin Dashboard access.
    """
    ip_address = get_real_ip(request)

    user = db.query(models.User).filter(
        models.User.username == data.username,
        models.User.user_type == "admin"
    ).first()
    
    if not user:
        log_auth_failure(ip_address, "/admin-login", "User not found")
        raise HTTPException(status_code=401, detail="Invalid username or password.")
        
    if not user.hashed_password:
        log_auth_failure(ip_address, "/admin-login", "Invalid credentials configuration")
        raise HTTPException(status_code=401, detail="Invalid credentials configuration. Contact system admin.")
        
    if not verify_password(data.password, user.hashed_password):
        log_auth_failure(ip_address, "/admin-login", "Invalid password", user_id=str(user.id))
        raise HTTPException(status_code=401, detail="Invalid username or password.")
        
    # Valid login credentials verified! Mint a new Dashboard JWT token.
    log_auth_success(ip_address, "/admin-login", user.username, str(user.id))
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "type": "admin"})

    return schemas.AuthResponse(token=access_token, user=user)

@router.post("/verify-otp", response_model=schemas.AuthResponse)
def verify_otp(data: schemas.VerifyOTP, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    raise HTTPException(status_code=404, detail="OTP authentication is currently disabled.")
#     ip_address = get_real_ip(request)
#     mobile_number = normalize_jo_phone(data.mobile_number)
#         # Send in-app notification
#         background_tasks.add_task(
#             send_personal_notification,
#             target_user_id=user.id,
#             title="مرحباً بك في سوقكم! 🎉",
#             body="حسابك جاهز. ابدأ بتصفح الإعلانات أو أضف إعلانك الأول.",
#             notification_type="welcome",
#             reference_id=None
#         )
#         
#         # Send chat message from admin
#         background_tasks.add_task(
#             send_welcome_chat_message,
#             user_id=user.id,
#             user_name=user.username or user.mobile_number,
#             user_phone=user.mobile_number
#         )
# 
#     return schemas.AuthResponse(token=access_token, user=user)

@router.post("/google", response_model=schemas.AuthResponse, dependencies=[Depends(get_rate_limiter(5, 60))])
def google_auth(data: schemas.GoogleAuthRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        google_client_id_web = os.environ.get("GOOGLE_CLIENT_ID_WEB")
        google_client_id_ios = os.environ.get("GOOGLE_CLIENT_ID_IOS")
        audiences = [aud for aud in [google_client_id, google_client_id_web, google_client_id_ios] if aud]
        
        idinfo = id_token.verify_oauth2_token(
            data.id_token,
            google_requests.Request(),
            audience=audiences  # Validates token is issued for either Mobile, Web, or iOS app
        )
        
        email = idinfo.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Google token does not contain an email address.")
            
        is_new_user = False
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            is_new_user = True
            user = models.User(
                email=email,
                full_name=idinfo.get('name'),
                avatar_url=idinfo.get('picture'),
                is_email_verified=True,
                username=email.split('@')[0]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Auto-create metrics for the new user
            metrics = models.UserMetric(user_id=user.id)
            db.add(metrics)
            db.commit()
            
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        if is_new_user:
            from notifications import send_personal_notification, send_welcome_chat_message
            background_tasks.add_task(
                send_personal_notification,
                target_user_id=user.id,
                title="مرحباً بك في سوقكم! 🎉",
                body="حسابك جاهز. ابدأ بتصفح الإعلانات أو أضف إعلانك الأول.",
                notification_type="welcome",
                reference_id=None
            )
            background_tasks.add_task(
                send_welcome_chat_message,
                user_id=user.id,
                user_name=user.username or user.email,
                user_phone=user.email
            )
            
        return schemas.AuthResponse(token=access_token, user=user)
        
    except ValueError as e:
        print(f"Google Token Verification Failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Google authentication token.")

@router.post("/facebook", response_model=schemas.AuthResponse)
def facebook_auth(data: schemas.FacebookAuthRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # Verify Facebook token via Graph API
        fb_url = f"https://graph.facebook.com/me?fields=id,name,email,picture.width(400).height(400)&access_token={data.access_token}"
        response = requests.get(fb_url, timeout=10)
        
        if response.status_code != 200:
            raise ValueError("Invalid Facebook token")
            
        fb_data = response.json()
        
        email = fb_data.get('email')
        
        if not email:
            raise HTTPException(status_code=400, detail="Facebook account must have an email address linked.")
            
        is_new_user = False
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            is_new_user = True
            
            # Extract picture if available
            avatar_url = None
            if 'picture' in fb_data and 'data' in fb_data['picture']:
                avatar_url = fb_data['picture']['data'].get('url')
                
            user = models.User(
                email=email,
                full_name=fb_data.get('name'),
                avatar_url=avatar_url,
                is_email_verified=True,
                username=email.split('@')[0]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Auto-create metrics for the new user
            metrics = models.UserMetric(user_id=user.id)
            db.add(metrics)
            db.commit()
            
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        if is_new_user:
            from notifications import send_personal_notification, send_welcome_chat_message
            background_tasks.add_task(
                send_personal_notification,
                target_user_id=user.id,
                title="مرحباً بك في سوقكم! 🎉",
                body="حسابك جاهز. ابدأ بتصفح الإعلانات أو أضف إعلانك الأول.",
                notification_type="welcome",
                reference_id=None
            )
            background_tasks.add_task(
                send_welcome_chat_message,
                user_id=user.id,
                user_name=user.username or user.email,
                user_phone=user.email
            )
            
        return schemas.AuthResponse(token=access_token, user=user)
        
    except ValueError as e:
        print(f"Facebook Token Verification Failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Facebook authentication token.")

from fastapi import Form
from fastapi.responses import RedirectResponse

@router.post("/apple/callback")
def apple_callback(
    code: str = Form(None),
    id_token: str = Form(None),
    state: str = Form(None),
    user: str = Form(None),
    error: str = Form(None)
):
    """
    Callback endpoint used by the Android Apple Sign-In flow.
    Apple redirects here after successful login, and we redirect back to the app via an Intent.
    """
    if error:
        return f"Apple Sign-In Error: {error}"
        
    # Construct the query parameters
    import urllib.parse
    params = {}
    if code: params["code"] = code
    if id_token: params["id_token"] = id_token
    if state: params["state"] = state
    if user: params["user"] = user
    
    query_string = urllib.parse.urlencode(params)
    
    # We must redirect to the custom intent scheme expected by sign_in_with_apple
    intent_url = f"intent://callback?{query_string}#Intent;package=com.sooqcom.app;scheme=signinwithapple;end"
    
    return RedirectResponse(url=intent_url, status_code=307)

@router.post("/apple", response_model=schemas.AuthResponse)
def apple_auth(data: schemas.AppleAuthRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # Fetch Apple's public keys
        jwks_client = jwt.PyJWKClient("https://appleid.apple.com/auth/keys")
        signing_key = jwks_client.get_signing_key_from_jwt(data.id_token)
        
        # Decode and verify the token
        # Accept both iOS (Bundle ID) and Android (Service ID) tokens
        payload = jwt.decode(
            data.id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=["com.sooqcom.app", "com.sooqcom.app.service"]
        )
        
        apple_sub = payload.get("sub")
        email = payload.get("email") or data.email
        
        if not email and not apple_sub:
            raise HTTPException(status_code=400, detail="Invalid Apple token")
            
        is_new_user = False
        # Try to find by email first, or by a unique apple_id (sub) if we added it to the schema.
        # Since we use email as the primary key for OAuth users in our current schema:
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            is_new_user = True
            
            # Combine first and last name if provided (Apple only sends this on the FIRST login)
            full_name = None
            if data.first_name or data.last_name:
                full_name = f"{data.first_name or ''} {data.last_name or ''}".strip()
                
            user = models.User(
                email=email,
                full_name=full_name,
                is_email_verified=True,
                username=email.split('@')[0] if email else f"apple_user_{apple_sub[:8]}"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            metrics = models.UserMetric(user_id=user.id)
            db.add(metrics)
            db.commit()
            
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        if is_new_user:
            from notifications import send_personal_notification, send_welcome_chat_message
            background_tasks.add_task(
                send_personal_notification,
                target_user_id=user.id,
                title="مرحباً بك في سوقكم! 🎉",
                body="حسابك جاهز. ابدأ بتصفح الإعلانات أو أضف إعلانك الأول.",
                notification_type="welcome",
                reference_id=None
            )
            background_tasks.add_task(
                send_welcome_chat_message,
                user_id=user.id,
                user_name=user.username or user.email,
                user_phone=user.email or ""
            )
            
        return schemas.AuthResponse(token=access_token, user=user)
        
    except Exception as e:
        log_auth_failure(get_real_ip(request), "/google", f"OAuth verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid Apple authentication token.")


# Common dependency for protected routes to easily get current user via JWT
def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    if is_token_revoked(token):
        log_token_revocation(get_real_ip(request), request.url.path)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
        return user
    except jwt.ExpiredSignatureError:
        log_expired_token(get_real_ip(request), request.url.path)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.PyJWTError:
        log_jwt_forgery_attempt(get_real_ip(request), request.url.path)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

@router.get("/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
def logout(request: Request, current_user: models.User = Depends(get_current_user)):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        revoke_token(token)
        log_user_logout(str(current_user.id), get_real_ip(request), "/logout")
    return {"status": "success", "message": "Logged out successfully"}

@router.delete("/account")
def delete_account(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Safely log the user out
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        revoke_token(token)
        log_user_logout(str(current_user.id), get_real_ip(request), "/delete_account")
        
    # Delete the user from the database
    # This will cascade delete their ads, messages, saved filters, etc. based on models.py foreign keys
    db.delete(current_user)
    db.commit()
    
    return {"status": "success", "message": "Account and all associated data have been permanently deleted"}

# Admin Dependency
def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.user_type != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    return current_user

@router.get("/admin/otps", response_model=List[schemas.OtpCodeOut])
def get_all_otps(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    otps = db.query(models.OtpCode).order_by(models.OtpCode.created_at.desc()).limit(100).all()
    return otps
