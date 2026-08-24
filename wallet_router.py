import os
import aiohttp
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
            # SECURITY: Only allow sandbox fallback in non-production environments
            if data.get("status") == 21007:
                if is_production:
                    raise HTTPException(status_code=400, detail="Sandbox receipts are not accepted in production")
                async with session.post("https://sandbox.itunes.apple.com/verifyReceipt", json=payload) as sandbox_resp:
                    data = await sandbox_resp.json()
                    
    if data.get("status") != 0:
        raise HTTPException(status_code=400, detail=f"Apple validation failed with status {data.get('status')}")
        
    return data

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
            raise HTTPException(status_code=400, detail="Transaction ID missing from Apple receipt")
            
        # Check for replay attack
        existing_tx = db.query(models.WalletTransaction).filter(
            models.WalletTransaction.reference_id == transaction_id
        ).first()
        
        if existing_tx:
            raise HTTPException(status_code=400, detail="This receipt has already been processed")
            
    elif req.platform == "android":
        # Google Play validation requires a Service Account JSON and the Google Play Developer API.
        # Until implemented, we block Android purchases to prevent fraud.
        raise HTTPException(status_code=501, detail="Android validation is not yet implemented on the server")
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
