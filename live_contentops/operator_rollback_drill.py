"""Deterministic local operator rollback and quarantine drill simulator."""
import uuid
import datetime
from typing import Dict, Any
from . import telegram_staging_flow
from . import approval_queue
from . import policy_engine
from . import policy_rules
from . import provider_gateway
from .adapters import telegram

def run_operator_rollback_drill(operator_id: str = "operator_jim_local") -> Dict[str, Any]:
    """
    Simulates a full Telegram dry-run pipeline, where the operator explicitly reviews the packet
    and issues a 'reject' (quarantine) command due to a simulated issue.
    """
    drill_id = "drill_" + str(uuid.uuid4())[:8]
    audit_events = []
    
    # 1. Source Artifact (Safe)
    source = telegram_staging_flow.build_sample_source_artifact(safe=True)
    audit_events.append({
        "event_id": "evt_" + str(uuid.uuid4())[:8],
        "event_type": "SOURCE_ARTIFACT_PREPARED",
        "target_id": source["artifact_id"],
        "result": "SUCCESS",
        "reason": "Local safe artifact generated for drill",
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
    
    # 2. Policy Engine
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
        raise RuntimeError("Rollback drill requires an artifact that passes policy for human review.")

    # 3. Provider Dry Run Simulator
    provider_req = {
        "requested_provider": provider_gateway.DRY_RUN_SIMULATOR,
        "dry_run_only": True,
        "policy_status": policy_res["status"],
        "queue_status": "REVIEW_REQUIRED",
        "prompt_text": source["text"]
    }
    provider_res = provider_gateway.run_provider_dry_run(provider_req)

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

    # 4. Approval Queue Creation
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

    # 5. Telegram Adapter
    telegram_req = {
        "target_channel_label": "PLACEHOLDER_STAGING_CHANNEL",
        "dry_run_only": True,
        "staging_only": True,
        "policy_status": policy_res["status"],
        "queue_status": queue_item["queue_status"],
        "message_text": provider_res.get("simulated_output_text", ""),
        "human_approval_required": True
    }
    telegram_res = telegram.run_telegram_dry_run(telegram_req)
    
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

    # 6. Operator Simulation: Reject/Quarantine
    operator_decision = approval_queue.apply_human_decision(
        queue_item=queue_item,
        action="reject",
        actor_id=operator_id,
        reason="DRILL: Operator detected hallucinated fact in provider dry run output."
    )
    
    # Extract the audit event returned by apply_human_decision
    human_audit = operator_decision["audit_event"]
    
    audit_events.append({
        "event_id": human_audit["event_id"],
        "event_type": human_audit["event_type"],
        "target_id": queue_item["queue_item_id"],
        "result": "REJECTED_AND_QUARANTINED",
        "reason": f"Action reject by {operator_id}: DRILL: Operator detected hallucinated fact in provider dry run output.",
        "safe_to_log": True,
        "secrets_redacted": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "created_at": human_audit["timestamp"]
    })

    return {
        "drill_id": drill_id,
        "task_label": "TASK_CONTENTOPS_0049_TELEGRAM_STAGING_OPERATOR_SIMULATION_REVIEW_AND_ROLLBACK_DRILL",
        "source_artifact_id": source["artifact_id"],
        "policy_decision_id": policy_res["decision_id"],
        "provider_dry_run_result_id": provider_res.get("result_id"),
        "approval_queue_item_id": queue_item["queue_item_id"],
        "telegram_dry_run_result_id": telegram_res.get("result_id"),
        "operator_action": "reject",
        "operator_actor_id": operator_id,
        "final_queue_status": queue_item["queue_status"],
        "audit_trail": audit_events,
        "drill_status": "SUCCESSFUL_ROLLBACK",
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

def run_cli_drill():
    return run_operator_rollback_drill()
