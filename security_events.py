import logging
import json
import datetime
import traceback
import contextvars
from typing import Optional

# Global context variable for request ID tracking
request_id_ctx = contextvars.ContextVar("request_id", default="system")

class JSONSecurityFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "request_id": request_id_ctx.get(),
            "service_name": "classifieds_backend",
            "level": record.levelname,
            "category": getattr(record, "category", "SYSTEM ERROR"),
            "event_type": getattr(record, "event_type", "unknown_event"),
            "message": record.getMessage(),
            "ip_address": getattr(record, "ip_address", "unknown"),
            "user_id": getattr(record, "user_id", "unknown"),
            "endpoint": getattr(record, "endpoint", "unknown"),
        }
        
        # Override request_id if explicitly passed (e.g. for BackgroundTasks)
        override_request_id = getattr(record, "override_request_id", None)
        if override_request_id:
            log_entry["request_id"] = override_request_id
            
        if record.exc_info:
            log_entry["exception"] = "".join(traceback.format_exception(*record.exc_info))
            
        return json.dumps(log_entry)

# Setup Logger
logger = logging.getLogger("security_events")
logger.setLevel(logging.INFO)
logger.propagate = False

console_handler = logging.StreamHandler()
console_handler.setFormatter(JSONSecurityFormatter())
if not logger.handlers:
    logger.addHandler(console_handler)

def _emit_event(level: int, category: str, event_type: str, message: str, ip_address: str, endpoint: str, user_id: str = "unknown", override_request_id: Optional[str] = None):
    extra = {
        "category": category,
        "event_type": event_type,
        "ip_address": ip_address,
        "user_id": str(user_id) if user_id else "unknown",
        "endpoint": endpoint,
        "override_request_id": override_request_id
    }
    logger.log(level, message, extra=extra)

# --- STRICTLY TYPED SECURITY EVENT FUNCTIONS ---

def log_auth_failure(ip_address: str, endpoint: str, reason: str, user_id: str = "unknown", override_request_id: Optional[str] = None):
    _emit_event(logging.WARNING, "AUTH ATTEMPT", "failed_login", f"Failed authentication: {reason}", ip_address, endpoint, user_id, override_request_id)

def log_auth_success(ip_address: str, endpoint: str, username: str, user_id: str, override_request_id: Optional[str] = None):
    _emit_event(logging.INFO, "AUTH ATTEMPT", "successful_login", f"Successful login: {username}", ip_address, endpoint, user_id, override_request_id)

def log_token_revocation(ip_address: str, endpoint: str, override_request_id: Optional[str] = None):
    _emit_event(logging.WARNING, "AUTH ATTEMPT", "revoked_token_access", "Attempted access with revoked token", ip_address, endpoint, override_request_id=override_request_id)

def log_rate_limit_exceeded(ip_address: str, endpoint: str, override_request_id: Optional[str] = None):
    _emit_event(logging.WARNING, "ABUSE ATTEMPT", "rate_limit_exceeded", f"Rate limit exceeded for endpoint: {endpoint}", ip_address, endpoint, override_request_id=override_request_id)

def log_bola_attempt(user_id: str, ip_address: str, endpoint: str, target_object_id: str, override_request_id: Optional[str] = None):
    _emit_event(logging.WARNING, "ABUSE ATTEMPT", "bola_attempt", f"BOLA attempt: User tried to access/modify object {target_object_id} without ownership", ip_address, endpoint, user_id, override_request_id)

def log_unauthorized_access(ip_address: str, endpoint: str, reason: str, user_id: str = "unknown", override_request_id: Optional[str] = None):
    _emit_event(logging.WARNING, "AUTH ATTEMPT", "unauthorized_access", f"Unauthorized access: {reason}", ip_address, endpoint, user_id, override_request_id)

def log_file_upload_blocked(ip_address: str, endpoint: str, reason: str, user_id: str = "unknown", override_request_id: Optional[str] = None):
    _emit_event(logging.WARNING, "ABUSE ATTEMPT", "file_upload_blocked", f"File upload rejected: {reason}", ip_address, endpoint, user_id, override_request_id)

def log_system_error(ip_address: str, endpoint: str, message: str, override_request_id: Optional[str] = None):
    _emit_event(logging.ERROR, "SYSTEM ERROR", "unhandled_exception", message, ip_address, endpoint, override_request_id=override_request_id)

def log_schema_validation_failure(ip_address: str, endpoint: str, reason: str, override_request_id: Optional[str] = None):
    _emit_event(logging.WARNING, "POSSIBLE DOS PATTERN", "schema_validation_failure", f"Schema validation failed: {reason}", ip_address, endpoint, override_request_id=override_request_id)

def log_jwt_forgery_attempt(ip_address: str, endpoint: str, override_request_id: Optional[str] = None):
    _emit_event(logging.WARNING, "ABUSE ATTEMPT", "forged_token_signature", "Invalid JWT signature or forgery attempt", ip_address, endpoint, override_request_id=override_request_id)

def log_expired_token(ip_address: str, endpoint: str, override_request_id: Optional[str] = None):
    _emit_event(logging.INFO, "AUTH ATTEMPT", "expired_token", "Attempted access with expired token", ip_address, endpoint, override_request_id=override_request_id)

def log_user_logout(user_id: str, ip_address: str, endpoint: str, override_request_id: Optional[str] = None):
    _emit_event(logging.INFO, "AUTH ATTEMPT", "user_logout", "User logged out securely", ip_address, endpoint, user_id, override_request_id)
