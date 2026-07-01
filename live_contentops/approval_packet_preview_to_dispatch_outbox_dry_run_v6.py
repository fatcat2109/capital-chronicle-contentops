"""V6 Approval Packet Preview to Dispatch Outbox Dry Run Packet Builder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "docs" / "automation" / "V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW" / "platform_variant_final_review_to_approval_packet_preview.json"
OUT_DIR = ROOT / "docs" / "automation" / "V6_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN"
OUT_PATH = OUT_DIR / "approval_packet_preview_to_dispatch_outbox_dry_run_packet.json"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_dry_run_package() -> dict:
    # Read the source final review variant approval preview packet
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        src = json.load(f)

    # Establish exact payload hash and check source credentials
    assert src["platform_variant_final_review_to_approval_packet_preview_packet_id"] == "approval_preview_28f5ef142e404225"
    assert src["exact_payload_hash"] == "b02ec50b38399194d087d12c1e168ceef64fc527ddab1885517ca542f7a72678"

    # Map the approval targets from source to dry-run entries
    targets = src["approval_targets"]

    dry_run_entries = {}

    mappings = [
        ("substack_manual_dry_run_entry", "substack_approval_preview", "POST_MANUAL", "manual_copy_block_only", "Separate final operator approval signature required."),
        ("discord_webhook_dry_run_entry", "discord_approval_preview", "POST_JSON", "webhook_mock_preview_only", "Separate final operator approval signature required."),
        ("telegram_operator_dry_run_entry", "telegram_approval_preview", "POST_JSON", "webhook_mock_preview_only", "Separate final operator approval signature required."),
        ("x_manual_dry_run_entry", "x_approval_preview", "POST_MANUAL", "manual_copy_block_only", "Separate final operator approval signature required."),
        ("linkedin_deferred_dry_run_entry", "linkedin_approval_preview", "DEFERRED", "deferred_future_task", "Deferred until subsequent explicit publication task."),
        ("threads_manual_dry_run_entry", "threads_approval_preview", "POST_MANUAL", "manual_copy_block_only", "Separate final operator approval signature required."),
        ("facebook_manual_dry_run_entry", "facebook_approval_preview", "POST_MANUAL", "manual_copy_block_only", "Separate final operator approval signature required."),
        ("instagram_deferred_dry_run_entry", "instagram_approval_preview", "DEFERRED", "deferred_future_task", "Deferred until subsequent explicit publication task."),
        ("youtube_deferred_dry_run_entry", "youtube_approval_preview", "DEFERRED", "deferred_future_task", "Deferred until subsequent explicit publication task."),
        ("tiktok_deferred_dry_run_entry", "tiktok_approval_preview", "DEFERRED", "deferred_future_task", "Deferred until subsequent explicit publication task."),
    ]

    for entry_key, target_key, method_preview, url_status, block_or_defer_msg in mappings:
        t = targets[target_key]
        text = t["exact_preview_text"]
        
        # Deterministic payload hashes
        payload_hash = sha256_text(text)
        req_body_hash = sha256_text(json.dumps({
            "platform": t["platform_id"],
            "payload": text,
            "adapter": t["adapter_class"],
            "binding": t["destination_binding_status"]
        }, sort_keys=True))

        entry = {
            "platform_id": t["platform_id"],
            "source_approval_target_key": target_key,
            "adapter_class": t["adapter_class"],
            "dry_run_entry_id": f"dry_run_{t['platform_id']}_28f5ef142e404225",
            "dry_run_payload_text": text,
            "dry_run_payload_hash": payload_hash,
            "source_approval_payload_hash": t["payload_hash"],
            "destination_binding_status": t["destination_binding_status"],
            "credential_handle_status": t["credential_handle_status"],
            "request_method_preview": method_preview,
            "request_url_preview_status": url_status,
            "request_body_hash_preview": req_body_hash,
            "executable": False,
            "dispatchable": False,
            "approved": False,
            "approval_required": True,
            "no_public_url_claim": True,
            "no_metrics_claim": True,
            "no_network_request_made": True,
            "no_secret_material_present": True,
        }

        # Handle blocked/deferred reasons dynamically
        if t["destination_binding_status"] == "deferred_future":
            entry["deferred_reason"] = block_or_defer_msg
        else:
            entry["blocked_reason"] = block_or_defer_msg

        dry_run_entries[entry_key] = entry

    # Build top-level dry-run outbox packet
    packet = {
        "packet_kind": "approval_packet_preview_to_dispatch_outbox_dry_run_v0",
        "dispatch_outbox_dry_run_status": "dispatch_outbox_dry_run_created_for_operator_review",
        "dry_run_outbox_package_created": True,
        "dry_run_entries_created": True,
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
        "exact_payload_hashes_preserved": True,
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
        "source_approval_preview_packet_id": "approval_preview_28f5ef142e404225",
        "source_approval_preview_exact_payload_hash": "b02ec50b38399194d087d12c1e168ceef64fc527ddab1885517ca542f7a72678",
        "source_final_review_packet_id": "final_review_preview_11fc52e6e452c4d3",
        "source_final_review_hash": "11fc52e6e452c4d3fedd306ffbf796fae459e061c784eed86cc1e8f65b9d38f2",
        "source_local_draft_preview_packet_id": "local_draft_preview_1f81b17970b6c151",
        "source_draft_review_packet_id": "draft_review_1f81b17970b6c151",
        "source_local_draft_hash": "1f81b17970b6c151d301c63af23e7adcc814e6ddf65bcd4e9a6b2c5def0c8b97",
        "dry_run_entries": dry_run_entries,
        "task_label": "TASK_CONTENTOPS_V6_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN_HEAVY_BATCH_V0"
    }

    return packet


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packet = build_dry_run_package()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2, sort_keys=True)
    print(f"Successfully generated outbox dry-run packet at: {OUT_PATH}")


if __name__ == "__main__":
    main()
