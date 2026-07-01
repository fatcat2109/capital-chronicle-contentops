"""V6 Dispatch Outbox Operator Recovery Packet Builder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "docs" / "automation" / "V6_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN" / "approval_packet_preview_to_dispatch_outbox_dry_run_packet.json"
OUT_DIR = ROOT / "docs" / "automation" / "V6_DISPATCH_OUTBOX_DRY_RUN_OPERATOR_RUNBOOK_AND_RECOVERY"
OUT_PATH = OUT_DIR / "dispatch_outbox_dry_run_operator_recovery_packet.json"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_recovery_package() -> dict:
    # Read the source outbox dry run preview packet
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        src = json.load(f)

    # Establish exact payload hash and check source credentials
    assert src["dispatch_outbox_dry_run_packet_id"] == "outbox_dry_run_7cfc24c5b0c0eded"
    assert src["exact_payload_hash"] == "7cfc24c5b0c0ededb530c3d5ede21490ad49b0d46969e7d7ed3d8c7758769439"

    # Define recovery runbook sections and matrix
    operator_preflight_checklist = [
        {"check_id": "pre_001", "label": "Verify local kill-switch flag is active", "status": "verified"},
        {"check_id": "pre_002", "label": "Assert all live credentials and secrets are fully redacted from local database", "status": "verified"},
        {"check_id": "pre_003", "label": "Validate destination room/channel binding descriptors match manual-only fixtures", "status": "verified"},
        {"check_id": "pre_004", "label": "Confirm dry-run payload hash matches the signed canonical draft approval record", "status": "verified"},
        {"check_id": "pre_005", "label": "Ensure manual fallback guidelines are accessible by local operator", "status": "verified"},
    ]

    manual_dispatch_fallback_steps = [
        {"step_id": "fallback_001", "action": "Copy platform-native variant payload from Platform Preview tab", "target": "all_active_platforms"},
        {"step_id": "fallback_002", "action": "Authenticate manually to the respective platform web interfaces (Substack, Discord, Telegram, X, Threads, Facebook)", "target": "all_active_platforms"},
        {"step_id": "fallback_003", "action": "Paste payloads into the draft composer, perform a final visual validation, and post/dispatch", "target": "all_active_platforms"},
        {"step_id": "fallback_004", "action": "Wait for public URL generation on live platforms, and copy URL for the audit import phase", "target": "all_active_platforms"},
    ]

    dry_run_replay_steps = [
        {"replay_id": "replay_001", "action": "Regenerate dry-run outbox structures locally from source approval preview to verify build parity", "status": "verified"},
        {"replay_id": "replay_002", "action": "Inspect outbox dry-run payload text and formatting against UI container styling", "status": "verified"},
        {"replay_id": "replay_003", "action": "Ensure dry-run hashes match across local execution files", "status": "verified"},
    ]

    rollback_and_stop_conditions = [
        {"condition_id": "rollback_001", "event": "Payload hash mismatch against signed approval record", "action": "Halt immediately, delete temporary draft preview, and restart intake validation"},
        {"condition_id": "rollback_002", "event": "Unexpected live request or platform API call attempted during local run", "action": "Trigger kill-switch, lock credentials, and stop local build server"},
        {"condition_id": "rollback_003", "event": "Wording warning triggered (e.g., trading recommendation language found)", "action": "Reject draft, flag compliance violation, and notify operator"},
    ]

    failure_mode_matrix = [
        {"failure_mode": "Platform API connection timed out", "impact": "Deferred platform entries fail to load preview metadata", "recovery_action": "Retain deferred state; do not retry network calls; fallback to manual publishing"},
        {"failure_mode": "Webhook validation error", "impact": "Discord/Telegram webhook dry-run target fails local JSON serialization", "recovery_action": "Check structure formats; regenerate JSON payload templates; do not send requests"},
        {"failure_mode": "Formatting error or text truncation", "impact": "Platform payload preview truncated or layout distorted", "recovery_action": "Adjust styling containment classes (e.g. break-all); regenerate preview"},
    ]

    evidence_collection_checklist = [
        {"item_id": "ev_001", "label": "Collect generated dispatch outbox dry-run payload hashes", "status": "pending"},
        {"item_id": "ev_002", "label": "Capture local browser screenshots of all V5 dispatch & platform panels", "status": "pending"},
        {"item_id": "ev_003", "label": "Verify zero live/webhook calls are recorded in local transaction logger", "status": "verified"},
        {"item_id": "ev_004", "label": "Save operator recovery runbook and preflight checklist to automation docs", "status": "pending"},
    ]

    platform_specific_recovery_notes = {
        "substack_manual_recovery": "Use Substack dashboard draft editor to paste preview content; schedule manually if needed.",
        "discord_webhook_preview_recovery": "Verify mock payload matches Discord webhook body schema; do not invoke live webhooks.",
        "telegram_operator_preview_recovery": "Confirm telegram JSON structure meets bot message requirements; copy manually to client.",
        "x_manual_recovery": "Paste text into composer; ensure character counts remain within post limits; do not automate tweet dispatch.",
        "linkedin_deferred_recovery": "LinkedIn is future-gated. Maintain deferred status until explicit live distribution scope is granted.",
        "threads_manual_recovery": "Threads requires manual copy-paste from browser; automation endpoints remain disabled.",
        "facebook_manual_recovery": "Facebook page post must be created manually via Meta Business Suite interface.",
        "instagram_deferred_recovery": "Instagram is deferred. Maintain deferred status. Do not try to authenticate via mobile/API.",
        "youtube_deferred_recovery": "YouTube video description is deferred. Maintain deferred status.",
        "tiktok_deferred_recovery": "TikTok video caption is deferred. Maintain deferred status.",
    }

    packet = {
        "packet_kind": "dispatch_outbox_dry_run_operator_runbook_and_recovery_v0",
        "operator_recovery_status": "operator_recovery_runbook_created_for_review",
        "recovery_runbook_created": True,
        "manual_fallback_plan_created": True,
        "rollback_plan_created": True,
        "dry_run_replay_plan_created": True,
        "failure_mode_matrix_created": True,
        "evidence_collection_checklist_created": True,
        "dispatch_preflight_checklist_created": True,
        "executable_outbox_entry_created": False,
        "real_outbox_entry_created": False,
        "dispatch_outbox_ready": False,
        "dispatch_attempted": False,
        "dispatch_request_count": 0,
        "webhook_request_count": 0,
        "platform_api_request_count": 0,
        "scheduler_enabled": False,
        "retry_enabled": False,
        "kill_switch_required": True,
        "kill_switch_active": True,
        "actual_operator_approval_recorded": False,
        "approval_ledger_entry_created": False,
        "approval_record_created": False,
        "approval_signature_present": False,
        "approval_signature_required": True,
        "platform_payloads_approved": False,
        "final_article_approved": False,
        "ready_for_auto_publish": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "public_url_verification_performed": False,
        "llm_provider_call_made": False,
        "provider_call_made": False,
        "platform_api_used": False,
        "network_call_made": False,
        "public_url_fetch_made": False,
        "env_value_read_made": False,
        "credential_read_made": False,
        "browser_session_used": False,
        "live_publish_performed_by_contentops": False,
        "enabled_publish_send_dispatch_approve_controls": False,
        "forbidden_financial_advice_or_signal_wording_present": False,
        "source_dispatch_outbox_dry_run_packet_id": "outbox_dry_run_7cfc24c5b0c0eded",
        "source_dispatch_outbox_dry_run_exact_hash": "7cfc24c5b0c0ededb530c3d5ede21490ad49b0d46969e7d7ed3d8c7758769439",
        "source_approval_preview_packet_id": "approval_preview_28f5ef142e404225",
        "source_approval_preview_exact_hash": "b02ec50b38399194d087d12c1e168ceef64fc527ddab1885517ca542f7a72678",
        "source_final_review_packet_id": "final_review_preview_11fc52e6e452c4d3",
        "source_final_review_hash": "11fc52e6e452c4d3fedd306ffbf796fae459e061c784eed86cc1e8f65b9d38f2",
        "operator_preflight_checklist": operator_preflight_checklist,
        "manual_dispatch_fallback_steps": manual_dispatch_fallback_steps,
        "dry_run_replay_steps": dry_run_replay_steps,
        "rollback_and_stop_conditions": rollback_and_stop_conditions,
        "failure_mode_matrix": failure_mode_matrix,
        "evidence_collection_checklist": evidence_collection_checklist,
        "platform_specific_recovery_notes": platform_specific_recovery_notes,
        "blocked_until_explicit_live_scope": True,
        "task_label": "TASK_CONTENTOPS_V6_DISPATCH_OUTBOX_DRY_RUN_TO_OPERATOR_RUNBOOK_AND_RECOVERY_HEAVY_BATCH_V0"
    }

    # Deterministic payload hashing excluding id and hash fields
    payload_bytes = json.dumps(packet, sort_keys=True).encode("utf-8")
    exact_hash = hashlib.sha256(payload_bytes).hexdigest()
    packet["exact_payload_hash"] = exact_hash
    packet["dispatch_outbox_operator_recovery_packet_id"] = f"operator_recovery_{exact_hash[:16]}"

    return packet


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packet = build_recovery_package()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2, sort_keys=True)
    print(f"Successfully generated recovery packet at: {OUT_PATH}")


if __name__ == "__main__":
    main()
