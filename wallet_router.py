from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/api/wallet", tags=["wallet"])

@router.post("/topup", response_model=schemas.UserPrivateProfile)
def topup_wallet(
    req: schemas.WalletTopupRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifies an In-App Purchase receipt and adds funds to the user's wallet.
    In a production app, you MUST verify the `receipt_data` with Google/Apple servers 
    using their respective APIs before granting the balance.
    """
    
    # Mapping of product IDs to real JOD values
    product_values = {
        "wallet_topup_10": 10.0,
        "wallet_topup_20": 20.0,
        "wallet_topup_50": 50.0
    }
    
    if req.product_id not in product_values:
        raise HTTPException(status_code=400, detail="Invalid product ID")
        
    amount = product_values[req.product_id]
    
    # Update User Balance
    current_user.wallet_balance = float(current_user.wallet_balance or 0) + amount
    
    # Log Transaction
    transaction = models.WalletTransaction(
        user_id=current_user.id,
        amount=amount,
        transaction_type="TOPUP",
        description=f"In-App Purchase Top-up ({req.platform})",
        reference_id=req.receipt_data[:50] # Just storing prefix for logs
    )
    db.add(transaction)
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("/transactions", response_model=list[schemas.WalletTransaction])
def get_transactions(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    transactions = db.query(models.WalletTransaction).filter(
        models.WalletTransaction.user_id == current_user.id
    ).order_by(models.WalletTransaction.created_at.desc()).all()
    
    return transactions
