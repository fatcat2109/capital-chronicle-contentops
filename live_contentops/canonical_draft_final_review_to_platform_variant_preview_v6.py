"""Backend packet builder for V6 Canonical Draft Final Review and Platform Variant Preview."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "automation" / "V6_CANONICAL_DRAFT_FINAL_REVIEW_TO_PLATFORM_VARIANT_PREVIEW"
OUT_FILE = OUT_DIR / "canonical_draft_final_review_to_platform_variant_preview_packet.json"


def build_packet() -> dict:
    # 1. Source packet info and hashes
    source_local_draft_preview_packet_id = "local_draft_preview_1f81b17970b6c151"
    source_draft_review_packet_id = "draft_review_1f81b17970b6c151"
    source_exact_payload_hash = "1f81b17970b6c151d301c63af23e7adcc814e6ddf65bcd4e9a6b2c5def0c8b97"
    source_draft_authorization_packet_hash = "80882c581b07e355e7be27ceef62fcc86edfd297db9766c4328de4adedda0486"
    source_pack_intake_packet_hash = "410e6b646cfe2f4b2307885826fa416b8aac95bc10c0a06cb89aeafef587a685"
    source_next_article_brief_packet_hash = "63c639189791ee71dd6ac33365c34b890b2d91558212e538467d5735c30251c6"

    # Define preview variants
    preview_variants = {
        "substack_canonical_preview": {
            "title": "Educational Explainer: Cash-Flow Quality and Key Accounting Formulas",
            "body": "Financial reporting lists profits, but cash quality shows underlying strength. This educational explainer focuses on understanding standard accounting principles.",
            "status": "preview_only"
        },
        "discord_drop_preview": {
            "title": "Cash-Flow Quality Discussion Starter",
            "body": "How do we evaluate the quality of a firm's reported cash flows without reliance on advisory predictions? Let's discuss Days Sales Outstanding and Cash Conversion Cycle metrics.",
            "status": "preview_only"
        },
        "telegram_operator_preview": {
            "title": "V6 Operator Notification",
            "body": "Local canonical draft preview is ready for operator final review. No LLM or provider API was called.",
            "status": "preview_only"
        },
        "x_manual_preview": {
            "title": "X Thread Draft",
            "body": "Profits are fine, but cash is king. Let's learn standard cash conversion cycle components qualitatively: DIO + DSO - DPO. Educational only, no financial advice.",
            "status": "preview_only"
        },
        "linkedin_personal_deferred_preview": {
            "title": "LinkedIn Article Draft",
            "body": "A qualitative overview of Earnings Quality, cash conversion speed, and dividend safety cushions based on historical SEC filing structures. Strictly educational.",
            "status": "preview_only"
        },
        "threads_preview": {
            "title": "Threads Update Draft",
            "body": "Understanding standard accounting metrics like Days Inventory Outstanding (DIO) without guaranteed market predictions. What indicators do you prioritize?",
            "status": "preview_only"
        },
        "facebook_page_preview": {
            "title": "Facebook Article Outline",
            "body": "Earnings Quality analysis: comparing net income to operating cash flows to identify qualitative discrepancies. Standard financial literacy.",
            "status": "preview_only"
        },
        "instagram_caption_preview": {
            "title": "Instagram Photo Caption Draft",
            "body": "Profits vs Cash: A look at cash conversion cycle mechanics. Details and formulas inside. #finance #education #accounting",
            "status": "preview_only"
        },
        "youtube_metadata_future_preview": {
            "title": "YouTube Video Metadata Preview",
            "body": "Educational video script outline: How to qualitatively verify earnings quality and cash cycles from historical SEC documents.",
            "status": "preview_only"
        },
        "tiktok_metadata_deferred_preview": {
            "title": "TikTok Video Captions Preview",
            "body": "Why cash conversion matter. Educational outline on DSO and DPO formulas.",
            "status": "preview_only"
        }
    }

    # Forbidden term check scan
    forbidden_terms = [
        r"\bbuy\b", r"\bsell\b", r"\bhold\b", r"price target",
        r"position sizing", r"guaranteed prediction", r"signal-service",
        r"trading instruction"
    ]
    has_forbidden = False
    for variant in preview_variants.values():
        combined_text = (variant["title"] + " " + variant["body"]).lower()
        for term in forbidden_terms:
            if re.search(term, combined_text):
                has_forbidden = True
                break

    # Construct draft final review & platform preview packet
    packet = {
        "packet_kind": "canonical_draft_final_review_to_platform_variant_preview_v0",
        "canonical_draft_final_review_status": "ready_for_operator_final_review",
        "final_article_approved": False,
        "operator_final_approval_required": True,
        "platform_variant_preview_status": "platform_variant_preview_created_for_operator_review",
        "platform_variants_created": True,
        "platform_variants_are_preview_only": True,
        "platform_payloads_approved": False,
        "approval_record_created": False,
        "outbox_entry_created": False,
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
        "forbidden_financial_advice_or_signal_wording_present": has_forbidden,
        "source_local_draft_preview_packet_id": source_local_draft_preview_packet_id,
        "source_draft_review_packet_id": source_draft_review_packet_id,
        "source_exact_payload_hash": source_exact_payload_hash,
        "source_draft_authorization_packet_hash": source_draft_authorization_packet_hash,
        "source_pack_intake_packet_hash": source_pack_intake_packet_hash,
        "source_next_article_brief_packet_hash": source_next_article_brief_packet_hash,
        "preview_variants": preview_variants,
        "task_label": "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_FINAL_REVIEW_TO_PLATFORM_VARIANT_PREVIEW_HEAVY_BATCH_V0"
    }

    # Generate a unique stable packet ID based on the contents to ensure deterministic generation
    content_bytes = json.dumps(packet, sort_keys=True).encode("utf-8")
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    packet_id = f"final_review_preview_{content_hash[:16]}"
    packet["canonical_draft_final_review_to_platform_variant_preview_packet_id"] = packet_id
    packet["exact_payload_hash"] = content_hash

    # Save to file
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2, sort_keys=True)

    print(f"Packet successfully written to: {OUT_FILE}")
    print(f"Packet ID: {packet_id}")
    print(f"Payload Hash: {content_hash}")
    return packet


if __name__ == "__main__":
    build_packet()
