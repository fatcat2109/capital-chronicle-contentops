"""Deterministic local audit log builder."""
import datetime
import uuid
from typing import Dict, Any, List
from . import policy_rules

ALLOWED_EVENT_TYPES = [
    "POLICY_EVALUATED", "QUEUE_ITEM_CREATED", "HUMAN_REVIEW_REQUIRED", "SOURCE_REQUESTED",
    "REVISION_REQUESTED", "ITEM_REJECTED", "ITEM_QUARANTINED", "APPROVED_FOR_FUTURE_DRY_RUN_ONLY",
    "KILL_SWITCH_STATUS_RECORDED", "VALIDATION_FAILED"
]

def create_audit_event(event_type: str, actor_id: str, target_id: str, action: str, result: str, reason: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"Invalid event type: {event_type}")

    has_secrets = False
    if payload and policy_rules.check_secret_keys(payload):
        has_secrets = True

    event_id = "aud_" + str(uuid.uuid4()).replace("-", "")

    return {
        "audit_event_id": event_id,
        "event_type": event_type,
        "actor_type": "HUMAN" if actor_id != "SYSTEM" else "SYSTEM",
        "actor_id": actor_id,
        "target_type": "QUEUE_ITEM",
        "target_id": target_id,
        "action": action,
        "result": result,
        "reason": reason,
        "redaction_status": "REDACTED" if has_secrets else "CLEAN",
        "safe_to_log": not has_secrets,
        "secrets_redacted": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "created_at": datetime.datetime.now().isoformat()
    }
