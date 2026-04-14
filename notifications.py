"""
User-Specific Notification System
- WebSocket Connection Manager: maps user_id -> active WebSocket connections
- send_personal_notification(): saves to DB, sends FCM push, broadcasts via WS
- REST endpoints for device token registration and notification history
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db, SessionLocal
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
        await websocket.accept()
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


# ============================================================
# Reusable Notification Sender (DB + FCM + WebSocket)
# ============================================================

async def send_personal_notification(
    target_user_id: int,
    title: str,
    body: str,
    notification_type: str = None,
    reference_id: int = None
):
    """
    Core function to send a user-specific notification:
    1. Saves to the database
    2. Sends FCM push to the user's registered device tokens
    3. Broadcasts via WebSocket if user is currently connected
    """
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

        # 2. Send FCM Push to the target user's devices ONLY
        user_tokens = db.query(models.UserDeviceToken).filter(
            models.UserDeviceToken.user_id == target_user_id
        ).all()

        if user_tokens:
            try:
                import firebase_admin
                from firebase_admin import messaging

                if not firebase_admin._apps:
                    # Initialize Firebase Admin only once
                    firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
                    if firebase_creds_json:
                        cred_dict = json.loads(firebase_creds_json)
                        cred = firebase_admin.credentials.Certificate(cred_dict)
                        firebase_admin.initialize_app(cred)
                    else:
                        cred_path = "firebase-service-account.json"
                        if os.path.exists(cred_path):
                            cred = firebase_admin.credentials.Certificate(cred_path)
                            firebase_admin.initialize_app(cred)

                if firebase_admin._apps:
                    for device in user_tokens:
                        try:
                            message = messaging.Message(
                                notification=messaging.Notification(title=title, body=body),
                                android=messaging.AndroidConfig(
                                    priority="high",
                                    notification=messaging.AndroidNotification(
                                        channel_id="high_importance_channel"
                                    )
                                ),
                                data={
                                    "type": notification_type or "",
                                    "reference_id": str(reference_id or ""),
                                },
                                token=device.fcm_token,
                            )
                            messaging.send(message)
                        except Exception as e:
                            print(f"[FCM] Failed to send to token {device.fcm_token[:20]}...: {e}")
            except ImportError:
                print("[FCM] firebase-admin not installed. Skipping push notification.")

        # 3. Broadcast via WebSocket to the specific user ONLY
        await manager.send_personal_message(target_user_id, notification_payload)

        print(f"[NOTIFY] Sent to user {target_user_id}: {title}")

    finally:
        db.close()


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


@router.post("/admin/send")
def send_admin_notification(
    data: schemas.AdminNotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Admin endpoint to send notifications to global or specific users."""
    
    if data.target_user_id.lower() == "all":
        # Send to all users
        users = db.query(models.User.id).all()
        for u in users:
            background_tasks.add_task(
                send_personal_notification,
                target_user_id=u[0],
                title=data.title,
                body=data.body,
                notification_type=data.type,
                reference_id=None
            )
        return {"status": "success", "message": f"Global notification initiated for {len(users)} users."}
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
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint mapped strictly to a user_id.
    Client connects with: ws://<host>/api/notifications/ws/<user_id>
    Only receives messages targeted to this specific user_id.
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive; receive pings/messages from client
            data = await websocket.receive_text()
            # Client can send "ping" to keep alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
