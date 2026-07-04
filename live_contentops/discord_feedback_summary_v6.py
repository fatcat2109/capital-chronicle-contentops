"""V6 deterministic Discord/community feedback summary builder."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from live_contentops.community_signal_intake_v6 import (
    SAFETY_FLAGS as SIGNAL_SAFETY_FLAGS,
    sample_community_signal_packets,
    stable_hash,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "automation" / "V6_COMMUNITY_SIGNAL"
SUMMARY_PATH = OUT_DIR / "sample_discord_feedback_summary.json"
REPORT_PATH = OUT_DIR / "implementation_report.md"
TASK_LABEL = "TASK_CONTENTOPS_V6_COMMUNITY_SIGNAL_INTAKE_AND_FEEDBACK_SUMMARY_V0"
SAFETY_FLAGS = {
    **SIGNAL_SAFETY_FLAGS,
    "summary_generated_by_llm": False,
    "next_content_approved_by_llm": False,
    "next_content_approved_by_system": False,
}


def _ready_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [signal for signal in signals if signal.get("status") == "READY_FOR_FEEDBACK_SUMMARY_REVIEW" and not signal.get("blockers")]


def _cluster_by_theme(signals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for signal in signals:
        clusters[str(signal.get("theme", "uncategorized"))].append(signal)
    return dict(sorted(clusters.items()))


def _content_backlog_from_clusters(clusters: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    backlog = []
    for theme, signals in clusters.items():
        required_sources = sorted({source for signal in signals for source in signal.get("required_sources", [])})
        signal_ids = [signal["signal_packet_id"] for signal in signals]
        backlog.append({
            "backlog_candidate": signals[0].get("backlog_candidate", theme),
            "theme": theme,
            "source_signal_packet_ids": signal_ids,
            "source_signal_hashes": [signal["signal_hash"] for signal in signals],
            "question_count": len(signals),
            "required_sources": required_sources,
            "recommended_next_action": signals[0].get("recommended_next_action", "operator_review"),
            "research_grounding_required_before_claim_use": True,
            "operator_review_required_before_next_content": True,
            "ready_for_article_claim_use": False,
            "readiness_status": "ready_for_operator_backlog_review_only",
        })
    backlog.sort(key=lambda item: (-item["question_count"], item["theme"]))
    return backlog


def build_discord_feedback_summary(signals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    source_signals = signals if signals is not None else sample_community_signal_packets()
    ready = _ready_signals(source_signals)
    blocked = [signal for signal in source_signals if signal not in ready]
    clusters = _cluster_by_theme(ready)
    theme_counts = Counter(signal.get("theme", "uncategorized") for signal in ready)
    source_channels = sorted({signal.get("source_channel_id", "") for signal in ready if signal.get("source_channel_id")})
    summary = {
        "schema_version": "6.0.0",
        "packet_kind": "discord_feedback_summary_v0",
        "task_label": TASK_LABEL,
        "summary_method": "deterministic_theme_grouping_no_llm",
        "date_range": "operator_selected_sample_no_clock_dependency",
        "source_channels": source_channels,
        "source_signal_packet_ids": [signal["signal_packet_id"] for signal in ready],
        "source_signal_hashes": [signal["signal_hash"] for signal in ready],
        "blocked_signal_packet_ids": [signal.get("signal_packet_id", "unknown") for signal in blocked],
        "recurring_questions": [
            {"theme": theme, "count": count, "question_texts": [s["question_text"] for s in clusters[theme]]}
            for theme, count in sorted(theme_counts.items())
        ],
        "objections": [],
        "confusing_terms": sorted({"real yields" if signal.get("theme") == "real_yields_education" else signal.get("theme", "") for signal in ready}),
        "requested_topics": sorted(theme_counts),
        "product_feedback": [],
        "moderation_flags": ["blocked_signals_present"] if blocked else [],
        "recommended_content_backlog": _content_backlog_from_clusters(clusters),
        "llm_summary_allowed_later": True,
        "llm_provider_call_made": False,
        "llm_cannot_approve_next_content": True,
        "community_input_cannot_be_factual_claim_without_research_grounding": True,
        "summary_status": "READY_FOR_OPERATOR_BACKLOG_REVIEW_ONLY",
        "blocked_controls": ["approve_next_content", "dispatch", "publish", "schedule", "scrape", "bot_collect", "private_message_ingest"],
        "non_readiness_claims": {
            "bot_ready_claimed": False,
            "api_ready_claimed": False,
            "llm_approved_claimed": False,
            "claim_grounding_complete": False,
            "dispatch_readiness_claimed": False,
        },
        "safety_flags": SAFETY_FLAGS,
    }
    summary["summary_hash"] = stable_hash({k: v for k, v in summary.items() if k not in {"summary_hash", "exact_payload_hash", "summary_id"}})
    summary["summary_id"] = f"discord_feedback_summary_{summary['summary_hash'][:16]}"
    summary["exact_payload_hash"] = stable_hash(summary)
    validate_discord_feedback_summary(summary)
    return summary


def validate_discord_feedback_summary(summary: dict[str, Any]) -> None:
    for key, expected in SAFETY_FLAGS.items():
        if summary.get("safety_flags", {}).get(key) is not expected:
            raise ValueError(f"{key}_must_be_false")
    if summary.get("llm_provider_call_made") is not False:
        raise ValueError("llm_provider_call_must_be_false")
    if summary.get("llm_cannot_approve_next_content") is not True:
        raise ValueError("llm_cannot_approve_next_content_required")
    for candidate in summary.get("recommended_content_backlog", []):
        if candidate.get("research_grounding_required_before_claim_use") is not True:
            raise ValueError("research_grounding_required")
        if candidate.get("ready_for_article_claim_use") is not False:
            raise ValueError("community_signal_cannot_be_claim_ready")


def write_sample_discord_feedback_summary() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = build_discord_feedback_summary()
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(f"""# V6 Community Signal Implementation Report

## Status

`{summary['summary_status']}`

## Purpose

This local-only community layer turns manually selected public Discord/community
questions into structured signal packets and a deterministic feedback backlog.

## Safety Boundary

No bot collection, scraping, private-message ingestion, network, API, webhook,
provider, LLM provider, browser, CDP, env, credential, cookie, storage, session,
token, header, live write, retry, schedule, comment, DM, or reaction action is
performed.

## Packet

- `summary_id`: `{summary['summary_id']}`
- `source_signals`: {len(summary['source_signal_packet_ids'])}
- `backlog_candidates`: {len(summary['recommended_content_backlog'])}
- `summary_hash`: `{summary['summary_hash']}`
- `exact_payload_hash`: `{summary['exact_payload_hash']}`

## Next Task

```text
TASK_CONTENTOPS_V6_METRICS_FINAL_UI_COMMAND_CENTER_RED_TEAM_RELEASE_EVIDENCE_V0
```
""", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(write_sample_discord_feedback_summary(), indent=2, sort_keys=True))
