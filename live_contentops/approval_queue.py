"""Deterministic local approval queue."""
import datetime
import uuid
from typing import Dict, Any, List
from . import policy_rules
from . import audit_log

ALLOWED_QUEUE_STATUSES = [
    "REVIEW_REQUIRED", "SOURCE_REQUIRED", "BLOCKED", "REVISION_REQUESTED",
    "REJECTED", "APPROVED_FOR_FUTURE_DRY_RUN_ONLY"
]

ALLOWED_OPERATOR_ACTIONS = [
    "request_sources_first", "request_revision", "reject", "quarantine", "approve_for_future_dry_run_only"
]

FORBIDDEN_OPERATOR_ACTIONS = [
    "publish_now", "schedule_now", "send_now", "auto_approve", "auto_publish", "autonomous_reply", "dm_user"
]

def build_queue_item_from_policy_decision(policy_decision: Dict[str, Any], payload: Dict[str, Any] = None) -> Dict[str, Any]:
    if not isinstance(policy_decision, dict) or "status" not in policy_decision:
        raise ValueError("Invalid policy decision")

    policy_status = policy_decision["status"]

    if policy_status == policy_rules.BLOCKED_SOURCE_REQUIRED:
        queue_status = "SOURCE_REQUIRED"
    elif policy_status == policy_rules.PASS_REVIEW_REQUIRED:
        queue_status = "REVIEW_REQUIRED"
    elif policy_status.startswith("BLOCKED"):
        queue_status = "BLOCKED"
    else:
        queue_status = "REVIEW_REQUIRED"

    item_id = "queue_" + str(uuid.uuid4()).replace("-", "")

    return {
        "queue_item_id": item_id,
        "source_payload_id": payload.get("id", "unknown") if payload else "unknown",
        "source_policy_decision_id": policy_decision.get("decision_id", ""),
        "policy_status": policy_status,
        "risk_flags": policy_decision.get("risk_flags", []),
        "block_reasons": policy_decision.get("block_reasons", []),
        "review_reasons": policy_decision.get("review_reasons", []),
        "required_human_actions": ["Review"] if queue_status in ["REVIEW_REQUIRED", "SOURCE_REQUIRED"] else [],
        "content_type": "unknown",
        "target_platform": "unknown",
        "source_state": policy_decision.get("source_requirements", "none"),
        "risk_tier": "high" if queue_status == "BLOCKED" else "medium",
        "review_priority": "normal",
        "queue_status": queue_status,
        "allowed_operator_actions": ALLOWED_OPERATOR_ACTIONS,
        "forbidden_operator_actions": FORBIDDEN_OPERATOR_ACTIONS,
        "human_approval_required": True,
        "safe_for_publish": False,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "created_at": datetime.datetime.now().isoformat()
    }

def apply_human_decision(queue_item: Dict[str, Any], action: str, actor_id: str, reason: str) -> Dict[str, Any]:
    if not actor_id:
        raise ValueError("Actor ID is required for human decision")
    if action in FORBIDDEN_OPERATOR_ACTIONS:
        raise ValueError(f"Action '{action}' is strictly forbidden by policy")
    if action not in ALLOWED_OPERATOR_ACTIONS:
        raise ValueError(f"Action '{action}' is not a recognized operator action")

    if queue_item["queue_status"] in ["BLOCKED", "SOURCE_REQUIRED"] and action == "approve_for_future_dry_run_only":
        raise ValueError("Cannot approve an item that is BLOCKED or SOURCE_REQUIRED")

    new_status = queue_item["queue_status"]
    if action == "approve_for_future_dry_run_only":
        new_status = "APPROVED_FOR_FUTURE_DRY_RUN_ONLY"
    elif action == "reject":
        new_status = "REJECTED"
    elif action == "request_revision":
        new_status = "REVISION_REQUESTED"
    elif action == "request_sources_first":
        new_status = "SOURCE_REQUIRED"

    queue_item["queue_status"] = new_status

    # Audit log creation is a side effect. Usually we would persist it, here we just return it alongside.
    audit_event = audit_log.create_audit_event(
        event_type="APPROVED_FOR_FUTURE_DRY_RUN_ONLY" if new_status == "APPROVED_FOR_FUTURE_DRY_RUN_ONLY" else "ITEM_REJECTED",
        actor_id=actor_id,
        target_id=queue_item["queue_item_id"],
        action=action,
        result=new_status,
        reason=reason
    )

    return {
        "updated_item": queue_item,
        "audit_event": audit_event
    }

def summarize_queue(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = {s: 0 for s in ALLOWED_QUEUE_STATUSES}
    for item in items:
        st = item.get("queue_status")
        if st in counts:
            counts[st] += 1
    return {
        "total": len(items),
        "status_counts": counts
    }
