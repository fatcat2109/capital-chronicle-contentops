"""V6 local-only community signal intake packet builder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "automation" / "V6_COMMUNITY_SIGNAL"
SIGNALS_PATH = OUT_DIR / "sample_signal_packets.json"
TASK_LABEL = "TASK_CONTENTOPS_V6_COMMUNITY_SIGNAL_INTAKE_AND_FEEDBACK_SUMMARY_V0"
INPUT_MODES = {"manual_paste", "operator_note", "future_slash_command", "future_bot_export"}
DEFERRED_INPUT_MODES = {"future_slash_command", "future_bot_export"}
SECRET_KEY_PARTS = ("secret", "token", "cookie", "session", "password", "credential", "authorization", "api_key", "header", "env")
FORBIDDEN_WORDING = (
    "financial advice", "trade signal", "buy signal", "sell signal", "price target",
    "guaranteed return", "private message", "dm from", "direct message",
)
CLAIM_WORDS = ("is true", "proved", "confirmed", "fact:", "will happen", "guaranteed")
SAFETY_FLAGS = {
    "bot_required": False,
    "bot_collection_performed": False,
    "message_scraping_performed": False,
    "private_message_ingested": False,
    "network_call_made": False,
    "provider_call_made": False,
    "llm_provider_call_made": False,
    "platform_api_used": False,
    "browser_or_cdp_action_performed": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "live_write_performed": False,
    "public_url_fetch_made": False,
}


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def has_secret_like_key(value: Any) -> bool:
    allowed = set(SAFETY_FLAGS) | {"safety_flags"}
    return any(key.lower() not in allowed and any(part in key.lower() for part in SECRET_KEY_PARTS) for key, _ in _walk(value))


def _contains_forbidden_text(*values: str) -> bool:
    haystack = " ".join(values).lower()
    return any(term in haystack for term in FORBIDDEN_WORDING)


def _unsupported_claim_without_grounding(question_text: str, required_sources: list[str]) -> bool:
    text = question_text.lower()
    return any(term in text for term in CLAIM_WORDS) and not required_sources


def build_community_signal_packet(
    *,
    source_channel_id: str,
    input_mode: str,
    question_text: str,
    theme: str,
    content_potential: str,
    required_sources: list[str],
    safe_angle: str,
    unsafe_angle: str,
    recommended_next_action: str,
    backlog_candidate: str,
    source_visibility: str = "public_channel_operator_selected",
) -> dict[str, Any]:
    blockers: list[str] = []
    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "community_signal_packet_v0",
        "task_label": TASK_LABEL,
        "source_channel_id": source_channel_id,
        "source_channel_id_operator_supplied_unverified": True,
        "input_mode": input_mode,
        "input_mode_deferred": input_mode in DEFERRED_INPUT_MODES,
        "source_visibility": source_visibility,
        "question_text": question_text,
        "theme": theme,
        "content_potential": content_potential,
        "required_sources": required_sources,
        "safe_angle": safe_angle,
        "unsafe_angle": unsafe_angle,
        "recommended_next_action": recommended_next_action,
        "backlog_candidate": backlog_candidate,
        "community_input_is_factual_claim": False,
        "research_grounding_required_before_claim_use": True,
        "operator_review_required_before_next_content": True,
        "safety_flags": SAFETY_FLAGS,
    }
    if input_mode not in INPUT_MODES:
        blockers.append("unsupported_input_mode")
    if source_visibility != "public_channel_operator_selected":
        blockers.append("private_message_ingestion_blocked")
    if not question_text.strip():
        blockers.append("question_text_required")
    if not safe_angle.strip():
        blockers.append("safe_angle_required")
    if _contains_forbidden_text(question_text, safe_angle, unsafe_angle, recommended_next_action):
        blockers.append("forbidden_financial_or_private_message_wording_blocked")
    if _unsupported_claim_without_grounding(question_text, required_sources):
        blockers.append("unsupported_claim_requires_research_grounding")
    if has_secret_like_key(packet):
        blockers.append("secret_like_key_blocked")
    packet["blockers"] = blockers
    packet["status"] = "BLOCKED_COMMUNITY_SIGNAL_REVIEW_REQUIRED" if blockers else "READY_FOR_FEEDBACK_SUMMARY_REVIEW"
    packet["signal_hash"] = stable_hash({k: v for k, v in packet.items() if k != "signal_hash"})
    packet["signal_packet_id"] = f"community_signal_{packet['signal_hash'][:16]}"
    return packet


def validate_community_signal_packet(packet: dict[str, Any]) -> None:
    if packet.get("blockers"):
        raise ValueError("blocked_signal_packet")
    for key, expected in SAFETY_FLAGS.items():
        if packet.get("safety_flags", {}).get(key) is not expected:
            raise ValueError(f"{key}_must_be_false")
    if packet.get("community_input_is_factual_claim") is not False:
        raise ValueError("community_input_cannot_be_factual_claim")
    if packet.get("research_grounding_required_before_claim_use") is not True:
        raise ValueError("research_grounding_required")
    if packet.get("source_visibility") != "public_channel_operator_selected":
        raise ValueError("private_message_ingestion_blocked")
    if has_secret_like_key(packet):
        raise ValueError("secret_like_key_blocked")


def sample_community_signal_packets() -> list[dict[str, Any]]:
    return [
        build_community_signal_packet(
            source_channel_id="discord_channel_macro_discussion_operator_supplied",
            input_mode="manual_paste",
            question_text="How should readers think about inflation data when Fed messaging changes tone?",
            theme="fed_inflation_context",
            content_potential="high",
            required_sources=["fomc_statement", "cpi_release", "treasury_yield_context"],
            safe_angle="Explain what changes in Fed language can and cannot tell us.",
            unsafe_angle="Predict the next rate move as certain.",
            recommended_next_action="add_to_research_backlog",
            backlog_candidate="fed_language_vs_inflation_data_explainer",
        ),
        build_community_signal_packet(
            source_channel_id="discord_channel_reader_questions_operator_supplied",
            input_mode="operator_note",
            question_text="Several readers were confused by real yields versus nominal yields.",
            theme="real_yields_education",
            content_potential="medium",
            required_sources=["treasury_yield_data", "inflation_expectations_source"],
            safe_angle="Create a plain-English explainer with definitions and caveats.",
            unsafe_angle="Use the question as proof of market direction.",
            recommended_next_action="prepare_source_pack_candidate",
            backlog_candidate="real_yields_plain_english_explainer",
        ),
    ]


def write_sample_signal_packets() -> list[dict[str, Any]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packets = sample_community_signal_packets()
    SIGNALS_PATH.write_text(json.dumps(packets, indent=2, sort_keys=True), encoding="utf-8")
    return packets


if __name__ == "__main__":
    print(json.dumps(write_sample_signal_packets(), indent=2, sort_keys=True))
