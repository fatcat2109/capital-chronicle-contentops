"""V6 Feedback Summarizer Prompt Contract.

Generates a deterministic LLM-ready prompt contract for offline feedback summary tasks.
"""
from __future__ import annotations

import hashlib
from typing import Any


def generate_prompt_contract(summary_packet: dict[str, Any]) -> dict[str, Any]:
    """Builds a structured prompt contract that specifies rules, safety controls, and schemas for LLM summary."""
    packet_id = summary_packet.get("summary_packet_id", "stub_packet_id")
    refs = summary_packet.get("input_snapshot_refs", [])

    hasher = hashlib.sha256(packet_id.encode("utf-8"))
    contract_id = f"prompt_contract_{hasher.hexdigest()[:12]}"

    allowed_input_fields = [
        "snapshot_id", "source_platform", "source_mode", "collected_at_manual",
        "raw_feedback_text_redacted", "author_handle_redacted"
    ]

    forbidden_input_fields = [
        "email", "phone", "precise_address", "discord_user_id", "telegram_chat_id",
        "webhook_url", "bot_token", "cookie", "session", "localStorage", "sessionStorage",
        "env", "local_path", "access_token"
    ]

    summarizer_instruction = (
        "Analyze the provided redacted feedback snapshots. Identify high-frequency "
        "clarification questions, disagreement themes, and topic requests. Summarize them "
        "synthetically into distinct categories according to the output schema."
    )

    safety_instruction = (
        "CRITICAL: Do not output any buy/sell/hold signal or target pricing. If a user asks "
        "for financial advice, summarize it strictly as an unsafe_financial_advice_request. "
        "Do not write comments or reply drafts. Do not include raw handles."
    )

    output_schema = {
        "type": "object",
        "properties": {
            "themes": {
                "type": "array",
                "items": {"type": "string"}
            },
            "unsafe_topics_detected": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["themes", "unsafe_topics_detected"]
    }

    contract = {
        "prompt_contract_id": contract_id,
        "source_summary_packet_id": packet_id,
        "input_snapshot_refs": sorted(refs),
        "redaction_policy": "NO_SECRET_VALUES_NO_IDS_NO_URLS",
        "allowed_input_fields": allowed_input_fields,
        "forbidden_input_fields": forbidden_input_fields,
        "summarizer_instruction": summarizer_instruction,
        "safety_instruction": safety_instruction,
        "output_schema": output_schema,
        "required_caveats": [
            "Macroeconomic parameters are highly uncertain and model-dependent.",
            "Consult licensed professionals before making any positioning adjustments."
        ],
        "blocked_topic_rules": [
            "No direct investment advice",
            "No signal-service framing"
        ],
        "no_financial_advice_rules": [
            "No target entries or exits",
            "No stop loss or position sizing guidelines"
        ],
        "no_auto_reply_rules": [
            "Do not output executable comments",
            "Do not output platform-native dispatch structures"
        ],
        "provider_call_performed": False,
        "provider_credentials_hydrated": False,
        "human_review_required": True,
        "dispatch_allowed_now": False,
        "public_postable": False
    }

    return contract
