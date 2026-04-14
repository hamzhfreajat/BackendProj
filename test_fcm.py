import os
import json
import firebase_admin
from firebase_admin import credentials, messaging

cred_path = r"d:\open\classifieds-app\backend\firebase-service-account.json"
fcm_token = "fSQDp2YNRAe_xdZNM4Daz6:APA91bE44Tn0bJOoR8ZLiqCXtXrbHwz3yKiSRyDBJFeASoSFAXXyYDqxx__uWVGNYW0J_gUmswU8hTLW76IWfvCCq5W6R5ST_9iS0s4w5egGzrlXB-obS30"

print("Initializing Firebase...")
try:
    firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
    if firebase_creds_json:
        cred_dict = json.loads(firebase_creds_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized from environment variable!")
    else:
        if not os.path.exists(cred_path):
            print(f"File not found: {cred_path}")
        else:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized!")
        
        message = messaging.Message(
            notification=messaging.Notification(title="Test Alert", body="This is a background notification test"),
            data={"type": "admin_alert"},
            token=fcm_token,
        )
        response = messaging.send(message)
        print("Successfully sent message:", response)
except Exception as e:
    print("Error:", str(e))
