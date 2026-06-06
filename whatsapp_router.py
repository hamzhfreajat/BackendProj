from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

VERIFY_TOKEN = "sooqcom_secure_token_123"

@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    Required for Meta WhatsApp Cloud API Webhook Verification.
    """
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED successfully!")
        return PlainTextResponse(content=hub_challenge, status_code=200)
    
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Receives incoming messages and status updates from WhatsApp.
    """
    try:
        body = await request.json()
        print("WhatsApp Webhook received:", body)
        return {"status": "success"}
    except Exception as e:
        print(f"Webhook processing error: {e}")
        return {"status": "error"}
