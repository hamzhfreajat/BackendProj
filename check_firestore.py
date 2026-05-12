import os
import sys
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
if not firebase_creds_json:
    print("No FIREBASE_CREDENTIALS in .env")
    sys.exit(1)

cred_dict = json.loads(firebase_creds_json)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)

db = firestore.client()
doc_ref = db.collection("chats").doc("7030_11_21")
doc = doc_ref.get()

if doc.exists:
    print(f"Chat 7030_11_21 exists! Data: {doc.to_dict()}")
else:
    print("Chat 7030_11_21 does NOT exist in Firestore!")

docs = db.collection("chats").where("participants", "array_contains", "11").stream()
print("Chats containing user 11:")
count = 0
for d in docs:
    print(d.id)
    count += 1
if count == 0:
    print("User 11 has no chats!")
