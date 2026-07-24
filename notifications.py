"""
User-Specific Notification System
- WebSocket Connection Manager: maps user_id -> active WebSocket connections
- send_personal_notification(): saves to DB, sends FCM push, broadcasts via WS
- REST endpoints for device token registration and notification history
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db, SessionLocal
import auth
from auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# ============================================================
# WebSocket Connection Manager (Per-User Mapping)
# ============================================================

class ConnectionManager:
    """
    Manages WebSocket connections mapped strictly by user_id.
    Each user can have multiple active connections (e.g. phone + tablet).
    Messages are ONLY delivered to the target user's connections.
    """

    def __init__(self):
        # Dict[user_id -> List[WebSocket]]
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"[WS] User {user_id} connected. Active connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"[WS] User {user_id} disconnected.")

    async def send_personal_message(self, user_id: int, data: dict):
        """Send a JSON payload ONLY to a specific user's active WebSocket connections."""
        if user_id in self.active_connections:
            dead_sockets = []
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead_sockets.append(ws)
            # Clean up dead connections
            for ws in dead_sockets:
                self.active_connections[user_id].remove(ws)


manager = ConnectionManager()

def init_firebase_admin():
    try:
        import firebase_admin
        from firebase_admin import credentials
        if not firebase_admin._apps:
            firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
            if firebase_creds_json:
                cred_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                cred_path = "firebase-service-account.json"
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
        return True
    except ImportError:
        print("[FCM] firebase-admin not installed.")
        return False

def send_welcome_chat_message(user_id: int, user_name: str, user_phone: str):
    if not init_firebase_admin():
        return
    try:
        import firebase_admin
        from firebase_admin import firestore
        db_fs = firestore.client()
        user_id_str = str(user_id)
        chat_id = f"welcome_admin_{user_id_str}"
        
        # Don't send if chat already exists
        chat_doc = db_fs.collection("chats").document(chat_id).get()
        if chat_doc.exists:
            return

        message_ref = db_fs.collection("chats").document(chat_id).collection("messages").document()
        welcome_text = "مرحباً بك! 👋 نحن هنا لمساعدتك في أي وقت، جاهزون للرد على استفساراتك."
        
        message_ref.set({
            "senderId": "admin",
            "text": welcome_text,
            "type": "text",
            "mediaUrl": None,
            "status": "sent",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        db_fs.collection("chats").document(chat_id).set({
            "adId": "welcome",
            "adTitle": "خدمة العملاء",
            "adPrice": "",
            "adImageUrl": "",
            "participants": [user_id_str, "admin"],
            "users": {
                user_id_str: {
                    "name": user_name or user_phone,
                    "avatar": "https://cdn-icons-png.freepik.com/512/3135/3135715.png",
                    "phone": user_phone,
                    "unreadCount": 1
                },
                "admin": {
                    "name": "خدمة العملاء",
                    "avatar": "https://cdn-icons-png.freepik.com/512/3135/3135715.png",
                    "unreadCount": 0
                }
            },
            "lastMessage": welcome_text,
            "lastMessageTime": firestore.SERVER_TIMESTAMP,
            "lastSenderId": "admin"
        }, merge=True)
        print(f"[CHAT] Welcome message sent to {user_id}")
    except Exception as e:
        print(f"[CHAT] Failed to send welcome message: {e}")


# ============================================================
# Reusable Notification Sender (DB + FCM + WebSocket)
# ============================================================

def _send_personal_notification_sync(
    target_user_id: int,
    title: str,
    body: str,
    notification_type: str = None,
    reference_id: int = None,
    extra_data: dict = None
):
    db = SessionLocal()
    try:
        # 1. Save notification to the database
        db_notification = models.Notification(
            target_user_id=target_user_id,
            title=title,
            body=body,
            type=notification_type,
            reference_id=reference_id
        )
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)

        notification_payload = {
            "id": db_notification.id,
            "title": title,
            "body": body,
            "type": notification_type,
            "reference_id": reference_id,
            "is_read": False,
            "created_at": db_notification.created_at.isoformat()
        }
        if extra_data:
            notification_payload.update(extra_data)

        # 2. Send FCM Push to the target user's devices ONLY
        user_tokens = db.query(models.UserDeviceToken).filter(
            models.UserDeviceToken.user_id == target_user_id
        ).all()

        if user_tokens:
            try:
                import firebase_admin
                from firebase_admin import messaging

                if not init_firebase_admin():
                    print("[FCM] Failed to initialize firebase.", flush=True)

                if firebase_admin._apps:
                    for device in user_tokens:
                        try:
                            data_payload = {
                                "type": notification_type or "",
                                "reference_id": str(reference_id or ""),
                            }
                            if extra_data:
                                for k, v in extra_data.items():
                                    data_payload[k] = str(v)

                            # Ensure we have title and body in data payload for data-only messages
                            data_payload["title"] = title
                            data_payload["body"] = body

                            message = messaging.Message(
                                notification=messaging.Notification(title=title, body=body),
                                android=messaging.AndroidConfig(
                                    priority="high",
                                    notification=messaging.AndroidNotification(
                                        channel_id="high_importance_channel",
                                        sound="default"
                                    )
                                ),
                                apns=messaging.APNSConfig(
                                    headers={
                                        "apns-priority": "10",
                                        "apns-push-type": "alert"
                                    },
                                    payload=messaging.APNSPayload(
                                        aps=messaging.Aps(
                                            alert=messaging.ApsAlert(
                                                title=title,
                                                body=body
                                            ),
                                            sound="default",
                                            badge=1,
                                            mutable_content=True,
                                            content_available=True
                                        )
                                    )
                                ),
                                data=data_payload,
                                token=device.fcm_token,
                            )
                            messaging.send(message)
                        except messaging.UnregisteredError:
                            print(f"[FCM] Token {device.fcm_token[:20]} is unregistered. Removing from DB.", flush=True)
                            db.delete(device)
                            db.commit()
                        except Exception as e:
                            print(f"[FCM] Failed to send to token {device.fcm_token[:20]}...: {e}", flush=True)
            except ImportError:
                print("[FCM] firebase-admin not installed. Skipping push notification.", flush=True)

        return notification_payload

    finally:
        db.close()


async def send_personal_notification(
    target_user_id: int,
    title: str,
    body: str,
    notification_type: str = None,
    reference_id: int = None,
    extra_data: dict = None
):
    """
    Core function to send a user-specific notification:
    1. Saves to the database (sync in thread)
    2. Sends FCM push to the user's registered device tokens (sync in thread)
    3. Broadcasts via WebSocket if user is currently connected (async)
    """
    # Run synchronous DB writes and blocking FCM network calls in a background thread
    notification_payload = await asyncio.to_thread(
        _send_personal_notification_sync,
        target_user_id,
        title,
        body,
        notification_type,
        reference_id,
        extra_data
    )

    # 3. Broadcast via WebSocket to the specific user ONLY
    await manager.send_personal_message(target_user_id, notification_payload)

    print(f"[NOTIFY] Sent to user {target_user_id}: {title}", flush=True)


# ============================================================
# REST API Endpoints
# ============================================================

@router.post("/device-token")
def register_device_token(
    data: schemas.DeviceTokenCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register or update FCM token for the authenticated user."""
    # Check if this token already exists
    existing = db.query(models.UserDeviceToken).filter(
        models.UserDeviceToken.fcm_token == data.fcm_token
    ).first()

    if existing:
        # Update ownership if token moved to a different user (device changed accounts)
        existing.user_id = current_user.id
        existing.device_type = data.device_type
    else:
        new_token = models.UserDeviceToken(
            user_id=current_user.id,
            fcm_token=data.fcm_token,
            device_type=data.device_type
        )
        db.add(new_token)

    db.commit()
    return {"status": "success", "message": "Device token registered."}


@router.get("/", response_model=List[schemas.NotificationOut])
def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch notification history strictly for the authenticated user."""
    query = db.query(models.Notification).filter(
        models.Notification.target_user_id == current_user.id
    )

    if unread_only:
        query = query.filter(models.Notification.is_read == False)

    notifications = query.order_by(
        models.Notification.created_at.desc()
    ).offset(skip).limit(limit).all()

    return notifications


@router.get("/unread-count")
def get_unread_count(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications for the authenticated user."""
    count = db.query(models.Notification).filter(
        models.Notification.target_user_id == current_user.id,
        models.Notification.is_read == False
    ).count()
    return {"unread_count": count}


@router.put("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific notification as read (only if it belongs to the authenticated user)."""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.target_user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    return {"status": "success"}


@router.put("/read-all")
def mark_all_as_read(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for the authenticated user."""
    db.query(models.Notification).filter(
        models.Notification.target_user_id == current_user.id,
        models.Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "success"}


@router.post("/chat-alert")
def send_chat_alert(
    data: schemas.ChatAlertCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger a push notification for a chat message."""
    target_user = db.query(models.User).filter(models.User.id == data.target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    title = f"رسالة جديدة من {data.sender_name}"
    
    background_tasks.add_task(
        send_personal_notification,
        target_user_id=data.target_user_id,
        title=title,
        body=data.message_preview,
        notification_type="chat_message",
        reference_id=int(data.ad_id) if data.ad_id.isdigit() else None,
        extra_data={
            "sender_name": data.sender_name, 
            "ad_title": getattr(data, 'ad_title', ''),
            "chat_id": getattr(data, 'chat_id', ''),
            "message_id": getattr(data, 'message_id', ''),
            "ad_id": data.ad_id,
        }
    )
    
    return {"status": "success", "message": "Chat alert queued."}


@router.post("/admin/send")
def send_admin_notification(
    data: schemas.AdminNotificationCreate,
    background_tasks: BackgroundTasks,
    current_admin: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to send notifications to global or specific users."""
    if current_admin.user_type != "admin":
        from fastapi import status as http_status
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    if data.target_user_id.lower() == "all":
        # Send a single broadcast to the global 'all_users' FCM topic
        def _send_global_fcm():
            try:
                import firebase_admin
                from firebase_admin import messaging
                if not init_firebase_admin(): return
                if not firebase_admin._apps: return
                
                message = messaging.Message(
                    notification=messaging.Notification(title=data.title, body=data.body),
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            channel_id="high_importance_channel",
                            sound="default"
                        )
                    ),
                    data={"type": data.type or ""},
                    topic="all_users",
                )
                messaging.send(message)
                print(f"[FCM] Global push sent to topic 'all_users'", flush=True)
            except Exception as e:
                print(f"[FCM] Global push failed: {e}", flush=True)

        background_tasks.add_task(_send_global_fcm)
        return {"status": "success", "message": "Global push notification initiated via FCM topics."}
    else:
        # Send to specific user by ID
        try:
            target_id = int(data.target_user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target user ID. Must be an integer or 'all'.")
            
        target_user = db.query(models.User).filter(models.User.id == target_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
            
        background_tasks.add_task(
            send_personal_notification,
            target_user_id=target_id,
            title=data.title,
            body=data.body,
            notification_type=data.type,
            reference_id=None
        )
        return {"status": "success", "message": f"Notification sent to user {target_id}."}


# ============================================================
# WebSocket Endpoint (User-Specific)
# ============================================================

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, token: str = None):
    """
    WebSocket endpoint mapped strictly to a user_id.
    Client connects with: ws://<host>/api/notifications/ws/<user_id>?token=<jwt>
    Verifies the JWT token before accepting the connection.
    """
    # Authenticate before accepting the WebSocket connection
    await websocket.accept()
    
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return
    
    try:
        import jwt as pyjwt
        from auth import SECRET_KEY, ALGORITHM
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_user_id = int(payload.get("sub", 0))
        if token_user_id != user_id:
            await websocket.close(code=4003, reason="Token user does not match connection user")
            return
    except Exception:
        await websocket.close(code=4001, reason="Invalid authentication token")
        return
    
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
