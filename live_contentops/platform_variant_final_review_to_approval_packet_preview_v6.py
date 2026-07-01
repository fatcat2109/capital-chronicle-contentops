"""Platform Variant Final Review to Approval Packet Preview Packet Builder."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "docs" / "automation" / "V6_CANONICAL_DRAFT_FINAL_REVIEW_TO_PLATFORM_VARIANT_PREVIEW" / "canonical_draft_final_review_to_platform_variant_preview_packet.json"
DEST_DIR = ROOT / "docs" / "automation" / "V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW"
DEST_PATH = DEST_DIR / "platform_variant_final_review_to_approval_packet_preview.json"


def build_packet() -> dict:
    if not SOURCE_PATH.exists():
        print(f"Error: Source packet not found at {SOURCE_PATH}")
        sys.exit(1)

    source_data = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    source_variants = source_data.get("preview_variants", {})
    source_payload_hash = source_data.get("exact_payload_hash", "11fc52e6e452c4d3fedd306ffbf796fae459e061c784eed86cc1e8f65b9d38f2")

    # Target configurations
    targets_config = [
        {
            "platform_id": "substack",
            "adapter_class": "manual_fallback_adapter",
            "source_variant_key": "substack_canonical_preview",
            "destination_binding_status": "preview_bound_manual",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Separate final operator approval signature required."
        },
        {
            "platform_id": "discord",
            "adapter_class": "webhook_adapter_preview_only",
            "source_variant_key": "discord_drop_preview",
            "destination_binding_status": "webhook_mock_bound",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Separate final operator approval signature required."
        },
        {
            "platform_id": "telegram",
            "adapter_class": "webhook_adapter_preview_only",
            "source_variant_key": "telegram_operator_preview",
            "destination_binding_status": "webhook_mock_bound",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Separate final operator approval signature required."
        },
        {
            "platform_id": "x",
            "adapter_class": "manual_fallback_adapter",
            "source_variant_key": "x_manual_preview",
            "destination_binding_status": "preview_bound_manual",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Separate final operator approval signature required."
        },
        {
            "platform_id": "linkedin",
            "adapter_class": "deferred_adapter",
            "source_variant_key": "linkedin_personal_deferred_preview",
            "destination_binding_status": "deferred_future",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Deferred until subsequent explicit publication task."
        },
        {
            "platform_id": "threads",
            "adapter_class": "manual_fallback_adapter",
            "source_variant_key": "threads_preview",
            "destination_binding_status": "preview_bound_manual",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Separate final operator approval signature required."
        },
        {
            "platform_id": "facebook",
            "adapter_class": "manual_fallback_adapter",
            "source_variant_key": "facebook_page_preview",
            "destination_binding_status": "preview_bound_manual",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Separate final operator approval signature required."
        },
        {
            "platform_id": "instagram",
            "adapter_class": "deferred_adapter",
            "source_variant_key": "instagram_caption_preview",
            "destination_binding_status": "deferred_future",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Deferred until subsequent explicit publication task."
        },
        {
            "platform_id": "youtube",
            "adapter_class": "deferred_adapter",
            "source_variant_key": "youtube_metadata_future_preview",
            "destination_binding_status": "deferred_future",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Deferred until subsequent explicit publication task."
        },
        {
            "platform_id": "tiktok",
            "adapter_class": "deferred_adapter",
            "source_variant_key": "tiktok_metadata_deferred_preview",
            "destination_binding_status": "deferred_future",
            "credential_handle_status": "fixture_only",
            "blocked_reason": "Deferred until subsequent explicit publication task."
        }
    ]

    approval_targets = {}
    for target in targets_config:
        platform_id = target["platform_id"]
        source_key = target["source_variant_key"]
        variant = source_variants.get(source_key, {})
        body = variant.get("body", "")

        payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        # Build key
        target_key = f"{platform_id}_approval_preview"
        approval_targets[target_key] = {
            "platform_id": platform_id,
            "adapter_class": target["adapter_class"],
            "source_variant_key": source_key,
            "exact_preview_text": body,
            "payload_hash": payload_hash,
            "destination_binding_status": target["destination_binding_status"],
            "credential_handle_status": target["credential_handle_status"],
            "approval_required": True,
            "approved": False,
            "dispatchable": False,
            "blocked_reason": target["blocked_reason"],
            "no_public_url_claim": True,
            "no_metrics_claim": True
        }

    packet_id_seed = f"approval_packet_preview_{source_payload_hash}"
    packet_id = "approval_preview_" + hashlib.sha256(packet_id_seed.encode("utf-8")).hexdigest()[:16]

    # Preflight scan for advisory terms
    forbidden_terms = [
        "buy", "sell", "hold", "price target", "position sizing",
        "entry point", "exit point", "trading recommendation",
        "guaranteed prediction", "signal service", "implied trading instruction"
    ]
    forbidden_present = False
    for target in approval_targets.values():
        txt = target["exact_preview_text"].lower()
        if any(term in txt for term in forbidden_terms):
            forbidden_present = True
            break

    packet = {
        "packet_kind": "platform_variant_final_review_to_approval_packet_preview_v0",
        "platform_variant_final_review_to_approval_packet_preview_packet_id": packet_id,
        "platform_variant_final_review_status": "ready_for_operator_approval_packet_review",
        "approval_packet_preview_status": "approval_packet_preview_created_for_operator_review",
        "exact_platform_payload_previews_created": True,
        "exact_payload_hashes_created": True,
        "approval_packet_preview_created": True,
        "actual_operator_approval_recorded": False,
        "approval_ledger_entry_created": False,
        "approval_record_created": False,
        "approval_signature_present": False,
        "approval_signature_required": True,
        "outbox_entry_created": False,
        "dispatch_outbox_ready": False,
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
        "forbidden_financial_advice_or_signal_wording_present": forbidden_present,

        # Source context binding
        "source_final_review_packet_id": source_data.get("canonical_draft_final_review_to_platform_variant_preview_packet_id"),
        "source_final_review_hash": source_payload_hash,
        "source_local_draft_preview_packet_id": source_data.get("source_local_draft_preview_packet_id"),
        "source_draft_review_packet_id": source_data.get("source_draft_review_packet_id"),
        "source_exact_payload_hash": source_data.get("source_exact_payload_hash"),
        "source_draft_authorization_packet_hash": source_data.get("source_draft_authorization_packet_hash"),
        "source_pack_intake_packet_hash": source_data.get("source_pack_intake_packet_hash"),
        "source_next_article_brief_packet_hash": source_data.get("source_next_article_brief_packet_hash"),
        "task_label": "TASK_CONTENTOPS_V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_HEAVY_BATCH_V0",

        "approval_targets": approval_targets
    }

    # Calculate exact preview packet hash of the serialized json values
    serialized = json.dumps(packet, sort_keys=True, indent=2)
    packet_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    packet["exact_payload_hash"] = packet_hash

    return packet


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    packet = build_packet()
    DEST_PATH.write_text(json.dumps(packet, sort_keys=True, indent=2), encoding="utf-8")
    print(f"Successfully generated approval preview packet: {DEST_PATH}")
    print(f"Packet Hash: {packet['exact_payload_hash']}")


if __name__ == "__main__":
    main()
