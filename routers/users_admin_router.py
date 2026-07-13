from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from models import User, Ad, SupportMessage, Category
from schemas import UserPublicProfile
import auth
from auth import get_current_admin
import models

router = APIRouter(prefix="/api/admin/users", tags=["admin_users"])

class UserAdminResponse(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    is_active: bool
    is_banned: bool
    created_at: str
    
    class Config:
        from_attributes = True

class UserStatusUpdate(BaseModel):
    is_active: bool

class UserBanUpdate(BaseModel):
    is_banned: bool

class SupportMessageResponse(BaseModel):
    id: int
    sender: str
    message: str
    is_read: bool
    created_at: str

class SupportMessageRequest(BaseModel):
    message: str

class UserAdResponse(BaseModel):
    id: int
    title: Optional[str] = None
    price: Optional[float] = None
    status: str
    created_at: str
    category_name: Optional[str] = None

@router.get("", response_model=List[UserAdminResponse])
def search_users(q: Optional[str] = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    query = db.query(User)
    
    if q:
        query = query.filter(
            or_(
                User.email.ilike(f"%{q}%"),
                User.full_name.ilike(f"%{q}%"),
                User.phone.ilike(f"%{q}%"),
                User.mobile_number.ilike(f"%{q}%"),
                User.username.ilike(f"%{q}%")
            )
        )
        
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    # format created_at
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "full_name": user.full_name or user.username or "Unknown",
            "email": user.email,
            "phone": user.phone,
            "mobile_number": user.mobile_number,
            "is_active": getattr(user, 'is_active', True),
            "is_banned": getattr(user, 'is_banned', False),
            "created_at": user.created_at.isoformat() if user.created_at else ""
        })
    return result

@router.put("/{user_id}/status")
def update_user_status(user_id: int, status: UserStatusUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = status.is_active
    db.commit()
    return {"message": "User status updated successfully"}

@router.put("/{user_id}/ban")
def update_user_ban(user_id: int, ban_status: UserBanUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_banned = ban_status.is_banned
    db.commit()
    return {"message": "User ban status updated successfully"}

@router.get("/{user_id}/ads", response_model=List[UserAdResponse])
def get_user_ads(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    ads = db.query(Ad).filter(Ad.user_id == user_id).order_by(Ad.created_at.desc()).all()
    
    result = []
    for ad in ads:
        category_name = None
        if ad.category_id:
            category = db.query(Category).filter(Category.id == ad.category_id).first()
            if category:
                category_name = category.name
                
        result.append({
            "id": ad.id,
            "title": ad.title or "بدون عنوان",
            "price": float(ad.price) if ad.price else 0.0,
            "status": ad.status if hasattr(ad, 'status') else "active",
            "created_at": ad.created_at.isoformat() if ad.created_at else "",
            "category_name": category_name
        })
    return result

@router.get("/{user_id}/chats", response_model=List[SupportMessageResponse])
def get_user_chats(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    messages = db.query(SupportMessage).filter(SupportMessage.user_id == user_id).order_by(SupportMessage.created_at.asc()).all()
    
    # Mark user messages as read when admin opens chat
    unreads = [m for m in messages if m.sender == 'user' and not m.is_read]
    if unreads:
        for m in unreads:
            m.is_read = True
        db.commit()
        
    result = []
    for m in messages:
        result.append({
            "id": m.id,
            "sender": m.sender,
            "message": m.message,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat() if m.created_at else ""
        })
    return result

@router.post("/{user_id}/chats")
def send_support_message(user_id: int, req: SupportMessageRequest, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    msg = SupportMessage(
        user_id=user_id,
        sender="admin",
        message=req.message,
        is_read=False
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    return {
        "id": msg.id,
        "sender": msg.sender,
        "message": msg.message,
        "is_read": msg.is_read,
        "created_at": msg.created_at.isoformat() if msg.created_at else ""
    }
