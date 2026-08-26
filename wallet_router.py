import os
import json
import base64
import aiohttp
from google.oauth2 import service_account
from googleapiclient.discovery import build
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/api/wallet", tags=["wallet"])

async def verify_apple_receipt(receipt_data: str) -> dict:
    shared_secret = os.getenv("APPLE_IAP_SHARED_SECRET")
    if not shared_secret:
        raise HTTPException(status_code=500, detail="Apple shared secret not configured on the server")
        
    payload = {
        "receipt-data": receipt_data,
        "password": shared_secret,
        "exclude-old-transactions": True
    }
    
    is_production = os.environ.get("ENV", "development") == "production"
    
    # Try production first
    async with aiohttp.ClientSession() as session:
        async with session.post("https://buy.itunes.apple.com/verifyReceipt", json=payload) as resp:
            data = await resp.json()
            
            # 21007 indicates this receipt is from the Sandbox environment
            # Apple REQUIRES production servers to accept Sandbox receipts during App Review,
            # because Apple reviewers test the live app using sandbox accounts.
            # (The shared_secret protects against spoofing, as it must match your app).
            if data.get("status") == 21007:
                async with session.post("https://sandbox.itunes.apple.com/verifyReceipt", json=payload) as sandbox_resp:
                    data = await sandbox_resp.json()
                    
    status_code = data.get("status")
    if status_code != 0:
        error_messages = {
            21000: "The request to the App Store was not made using the HTTP POST request method.",
            21002: "The data in the receipt-data property was malformed or missing.",
            21003: "The receipt could not be authenticated.",
            21004: "The shared secret you provided does not match the shared secret on file for your account.",
            21005: "The receipt server is currently not available.",
            21006: "This receipt is valid but the subscription has expired.",
            21007: "This receipt is from the test environment, but it was sent to the production environment for verification.",
            21008: "This receipt is from the production environment, but it was sent to the test environment for verification.",
            21010: "This receipt could not be authorized. Treat this the same as if a purchase was never made."
        }
        status_msg = error_messages.get(status_code, "Unknown error")
        print(f"[IAP ERROR - APPLE] Status: {status_code}, Message: {status_msg}, Full Response: {data}")
        raise HTTPException(status_code=400, detail=f"Apple validation failed with status {status_code}: {status_msg}")
        
    # SECURITY: Verify the bundle ID to prevent cross-app receipt spoofing
    receipt_bundle_id = data.get("receipt", {}).get("bundle_id")
    if receipt_bundle_id != "com.sooqcom.app":
        print(f"[IAP ERROR - APPLE] Invalid bundle ID: {receipt_bundle_id}")
        raise HTTPException(status_code=400, detail="Invalid bundle ID in receipt")
        
    return data

async def verify_google_play_receipt(product_id: str, purchase_token: str) -> dict:
    b64_json = os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON_B64")
    if not b64_json:
        raise HTTPException(status_code=500, detail="Google Play service account JSON not configured on the server")
        
    try:
        json_str = base64.b64decode(b64_json).decode("utf-8")
        service_account_info = json.loads(json_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to decode Google Play service account JSON")

    try:
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, 
            scopes=["https://www.googleapis.com/auth/androidpublisher"]
        )
        
        # Build the Android Publisher service
        # In a real async app, this blocking call should be offloaded to a thread pool, but it's acceptable for now
        service = build("androidpublisher", "v3", credentials=credentials)
        
        # Verify the purchase
        package_name = "com.sooqcom.app"
        
        # Calls the API: GET https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{packageName}/purchases/products/{productId}/tokens/{token}
        result = service.purchases().products().get(
            packageName=package_name,
            productId=product_id,
            token=purchase_token
        ).execute()
        
        return result
    except Exception as e:
        print(f"[IAP ERROR - GOOGLE] Validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Google Play validation failed: {str(e)}")

@router.post("/topup", response_model=schemas.UserPrivateProfile, dependencies=[Depends(auth.get_rate_limiter(5, 60))])
async def topup_wallet(
    req: schemas.WalletTopupRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifies an In-App Purchase receipt with Apple/Google and adds funds to the user's wallet.
    Prevents replay attacks by checking if the transaction ID was already processed.
    """
    
    product_values = {
        "wallet_topup_10": 10.0,
        "wallet_topup_20": 20.0,
        "wallet_topup_50": 50.0
    }
    
    # Schema validator already checks product_id, but belt-and-suspenders
    if req.product_id not in product_values:
        raise HTTPException(status_code=400, detail="Invalid product ID")
        
    transaction_id = None
    
    if req.platform == "ios":
        receipt_info = await verify_apple_receipt(req.receipt_data)
        
        in_app_list = receipt_info.get("receipt", {}).get("in_app", [])
        
        # Sort by purchase_date_ms desc so we get the latest purchase
        in_app_list.sort(key=lambda x: int(x.get("purchase_date_ms", 0)), reverse=True)
        
        valid_purchase = None
        for p in in_app_list:
            if p.get("product_id") == req.product_id:
                valid_purchase = p
                break
                
        if not valid_purchase:
            raise HTTPException(status_code=400, detail="No matching purchase found in the Apple receipt")
            
        transaction_id = valid_purchase.get("transaction_id")
        
        if not transaction_id:
            print("[IAP ERROR - APPLE] Transaction ID missing from receipt.")
            raise HTTPException(status_code=400, detail="Transaction ID missing from Apple receipt")
            
        # Check for replay attack
        existing_tx = db.query(models.WalletTransaction).filter(
            models.WalletTransaction.reference_id == transaction_id
        ).first()
        
        if existing_tx:
            print(f"[IAP ERROR - APPLE] Transaction {transaction_id} was already processed.")
            raise HTTPException(status_code=400, detail="This receipt has already been processed")
            
    elif req.platform == "android":
        play_result = await verify_google_play_receipt(req.product_id, req.receipt_data)
        
        # Check purchaseState (0 = Purchased, 1 = Canceled, 2 = Pending)
        purchase_state = play_result.get("purchaseState")
        if purchase_state != 0:
            print(f"[IAP ERROR - GOOGLE] Purchase not in 'Purchased' state. Current state: {purchase_state}, Token: {req.receipt_data}")
            raise HTTPException(status_code=400, detail=f"Google Play purchase not in 'Purchased' state (state: {purchase_state})")
            
        # The transaction ID in Google Play is orderId
        transaction_id = play_result.get("orderId")
        if not transaction_id:
            print(f"[IAP ERROR - GOOGLE] Missing orderId in Play response: {play_result}")
            raise HTTPException(status_code=400, detail="Transaction ID missing from Google Play receipt")
            
        # Check for replay attack
        existing_tx = db.query(models.WalletTransaction).filter(
            models.WalletTransaction.reference_id == transaction_id
        ).first()
        
        if existing_tx:
            print(f"[IAP ERROR - GOOGLE] Transaction {transaction_id} was already processed.")
            raise HTTPException(status_code=400, detail="This receipt has already been processed")
    else:
        raise HTTPException(status_code=400, detail="Invalid platform specified")
        
    amount = product_values[req.product_id]
    
    # SECURITY: Lock the user row to prevent concurrent topup race conditions
    user = db.query(models.User).filter(models.User.id == current_user.id).with_for_update().first()
    
    # Update User Balance
    user.wallet_balance = float(user.wallet_balance or 0) + amount
    
    # Log Transaction
    transaction = models.WalletTransaction(
        user_id=user.id,
        amount=amount,
        transaction_type="TOPUP",
        description=f"In-App Purchase Top-up ({req.platform.upper()})",
        reference_id=transaction_id
    )
    db.add(transaction)
    db.commit()
    db.refresh(user)
    
    return user

@router.get("/transactions", response_model=list[schemas.WalletTransaction])
def get_transactions(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    transactions = db.query(models.WalletTransaction).filter(
        models.WalletTransaction.user_id == current_user.id
    ).order_by(models.WalletTransaction.created_at.desc()).all()
    
    return transactions
