import json
import uuid
import datetime
from . import policy_engine
from . import policy_rules
from . import provider_gateway
from . import approval_queue
from .adapters import telegram

def build_sample_source_artifact(safe=True):
    if safe:
        return {
            "artifact_id": "src_" + str(uuid.uuid4())[:8],
            "text": "The central bank kept interest rates unchanged today. [Source: Federal Reserve Release]",
            "source_state": "none"
        }
    else:
        return {
            "artifact_id": "src_" + str(uuid.uuid4())[:8],
            "text": "Buy TSLA immediately! It will definitely go up.",
            "source_state": "none"
        }

def run_telegram_staging_dry_run_flow(safe=True):
    flow_id = "flow_" + str(uuid.uuid4())[:8]
    audit_events = []
    
    source = build_sample_source_artifact(safe=safe)
    audit_events.append({
        "event_id": "evt_" + str(uuid.uuid4())[:8],
        "event_type": "SOURCE_ARTIFACT_PREPARED",
        "target_id": source["artifact_id"],
        "result": "SUCCESS",
        "reason": "Local safe artifact generated",
        "safe_to_log": True,
        "secrets_redacted": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })
    
    policy_res = policy_engine.evaluate_policy(source, target_id=source["artifact_id"])
    audit_events.append({
        "event_id": "evt_" + str(uuid.uuid4())[:8],
        "event_type": "POLICY_EVALUATED",
        "target_id": source["artifact_id"],
        "result": policy_res["status"],
        "reason": str(policy_res["block_reasons"]),
        "safe_to_log": True,
        "secrets_redacted": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })
    
    if policy_res["status"] != policy_rules.PASS_REVIEW_REQUIRED:
        return _build_blocked_flow(flow_id, "BLOCKED_POLICY", source, policy_res, None, None, None, audit_events)
        
    provider_req = {
        "requested_provider": provider_gateway.DRY_RUN_SIMULATOR,
        "dry_run_only": True,
        "policy_status": policy_res["status"],
        "queue_status": "REVIEW_REQUIRED",
        "prompt_text": source["text"]
    }
    try:
        provider_res = provider_gateway.run_provider_dry_run(provider_req)
    except Exception as e:
        return _build_blocked_flow(flow_id, "BLOCKED_PROVIDER_DRY_RUN", source, policy_res, None, None, None, audit_events)

    audit_events.append({
        "event_id": "evt_" + str(uuid.uuid4())[:8],
        "event_type": "PROVIDER_DRY_RUN_SIMULATED",
        "target_id": provider_res.get("result_id", "none"),
        "result": "SUCCESS",
        "reason": "Simulated local payload",
        "safe_to_log": True,
        "secrets_redacted": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })

    queue_item = approval_queue.build_queue_item_from_policy_decision(policy_res)
    audit_events.append({
        "event_id": "evt_" + str(uuid.uuid4())[:8],
        "event_type": "APPROVAL_QUEUE_ITEM_CREATED",
        "target_id": queue_item["queue_item_id"],
        "result": queue_item["queue_status"],
        "reason": "Deterministic mapping",
        "safe_to_log": True,
        "secrets_redacted": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })

    telegram_req = {
        "target_channel_label": "PLACEHOLDER_STAGING_CHANNEL",
        "dry_run_only": True,
        "staging_only": True,
        "policy_status": policy_res["status"],
        "queue_status": queue_item["queue_status"],
        "message_text": provider_res.get("simulated_output_text", ""),
        "human_approval_required": True
    }
    try:
        telegram_res = telegram.run_telegram_dry_run(telegram_req)
    except Exception as e:
        return _build_blocked_flow(flow_id, "BLOCKED_TELEGRAM_DRY_RUN", source, policy_res, provider_res, queue_item, None, audit_events)
    
    audit_events.append({
        "event_id": "evt_" + str(uuid.uuid4())[:8],
        "event_type": "TELEGRAM_DRY_RUN_SIMULATED",
        "target_id": telegram_res.get("result_id", "none"),
        "result": "SUCCESS",
        "reason": "Dry run complete",
        "safe_to_log": True,
        "secrets_redacted": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })
    
    audit_events.append({
        "event_id": "evt_" + str(uuid.uuid4())[:8],
        "event_type": "FLOW_VALIDATED",
        "target_id": flow_id,
        "result": "LOCAL_DRY_RUN_COMPLETE",
        "reason": "All live capabilities remained blocked natively.",
        "safe_to_log": True,
        "secrets_redacted": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })

    return {
        "flow_id": flow_id,
        "task_label": "TASK_CONTENTOPS_0048_TELEGRAM_STAGING_DRY_RUN_ARTIFACT_FLOW_AND_AUDIT_TRAIL",
        "source_artifact_id": source["artifact_id"],
        "policy_decision_id": policy_res["decision_id"],
        "provider_dry_run_result_id": provider_res.get("result_id"),
        "approval_queue_item_id": queue_item["queue_item_id"],
        "telegram_dry_run_result_id": telegram_res.get("result_id"),
        "audit_trail": audit_events,
        "flow_status": "LOCAL_DRY_RUN_COMPLETE",
        "blocker_list": ["Operator GO not provided", "Tokens not configured"],
        "live_credentials_allowed_now": False,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "autonomous_replies_enabled": False,
        "safe_for_publish": False,
        "human_approval_required": True,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }

def _build_blocked_flow(flow_id, flow_status, source, policy_res, provider_res, queue_item, telegram_res, audit_events):
    return {
        "flow_id": flow_id,
        "task_label": "TASK_CONTENTOPS_0048_TELEGRAM_STAGING_DRY_RUN_ARTIFACT_FLOW_AND_AUDIT_TRAIL",
        "source_artifact_id": source["artifact_id"] if source else None,
        "policy_decision_id": policy_res["decision_id"] if policy_res else None,
        "provider_dry_run_result_id": provider_res.get("result_id") if provider_res else None,
        "approval_queue_item_id": queue_item.get("queue_item_id", None) if queue_item else None,
        "telegram_dry_run_result_id": telegram_res.get("result_id") if telegram_res else None,
        "audit_trail": audit_events,
        "flow_status": flow_status,
        "blocker_list": ["Flow blocked early by policy or simulator failure"],
        "live_credentials_allowed_now": False,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "autonomous_replies_enabled": False,
        "safe_for_publish": False,
        "human_approval_required": True,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }

def run_cli_flow():
    return run_telegram_staging_dry_run_flow(safe=True)
