"""Contract validation helpers."""
from typing import Dict, Any, List

SECRET_KEYS = ["api_key", "access_token", "client_secret", "password", "bearer", "refresh_token"]
LIVE_FLAGS = ["network_used", "provider_call_used", "platform_api_used", "publishing_enabled", "scheduler_enabled", "auto_approved"]

class ValidationError(Exception):
    pass

def validate_contract_dict(data: Dict[str, Any]) -> bool:
    """Validates safe contract data."""
    if not isinstance(data, dict):
        raise ValidationError("Contract data must be a dictionary.")
        
    for k, v in data.items():
        if isinstance(k, str) and k.lower() in SECRET_KEYS:
            raise ValidationError(f"Secret-like field detected: {k}")
        
        if k in LIVE_FLAGS and v is True:
            raise ValidationError(f"Live capability flag set to true: {k}")
            
    if "human_approval_required" in data and data["human_approval_required"] is not True:
        raise ValidationError("Human approval requirement cannot be bypassed.")
        
    return True
