import sys
import os
from sqlalchemy import text

# Add backend path to sys.path if not there
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from notifications import init_firebase_admin
import firebase_admin
from firebase_admin import messaging

if not init_firebase_admin():
    print("Failed to init Firebase")
    sys.exit(1)

db = SessionLocal()
# Get User 41 tokens
result = db.execute(text("SELECT fcm_token, device_type FROM user_device_tokens WHERE user_id = 41")).fetchall()

if not result:
    print("No tokens found for user 41")
    sys.exit(1)

print(f"Found {len(result)} tokens for User 41:")

for row in result:
    token = row[0]
    device_type = row[1]
    print(f"\n--- Testing Token ({device_type}): {token[:20]}...{token[-10:]} ---")
    
    # 4. Construct payload
    title = "Test Notification"
    body = "This is a direct test message."
    
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        apns=messaging.APNSConfig(
            headers={
                "apns-priority": "10",
                "apns-push-type": "alert" # EXPLICIT HEADER
            },
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(title=title, body=body),
                    sound="default",
                    badge=1,
                    mutable_content=True,
                    content_available=True
                )
            )
        ),
        token=token
    )
    
    try:
        response = messaging.send(message, dry_run=False)
        print(f"SUCCESS: Firebase accepted the message. Message ID: {response}")
    except Exception as e:
        print(f"ERROR: Failed to send. {type(e).__name__}: {e}")
