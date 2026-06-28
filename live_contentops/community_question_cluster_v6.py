"""V6 Community Question Clustering.

Deterministically classifies snapshots into clusters and enforces safety checks on financial advice.
"""
from __future__ import annotations

import hashlib
from typing import Any

# Classification rules mapping keywords to labels
CLASSIFICATIONS = [
    ("unsafe_financial_advice_request", [
        "buy", "sell", "hold", "target", "exit", "stop loss", "stop-loss", 
        "position size", "position-size", "leverage", "trade setup", "trade-setup", 
        "signal", "guaranteed", "return", "advice", "portfolio", "allocation",
        "invest", "profit", "long term", "short term"
    ]),
    ("source_request", [
        "source", "link", "where", "cite", "citation", "reference", "data from", 
        "url", "evidence", "provenance"
    ]),
    ("methodology_question", [
        "method", "calculation", "calculate", "compute", "formula", "math",
        "model", "data source", "how did you"
    ]),
    ("correction_request", [
        "error", "mistake", "typo", "incorrect", "wrong", "fix", "correct", "bug"
    ]),
    ("disagreement_or_challenge", [
        "disagree", "false", "fake", "nonsense", "bullshit", "oppose", "contrary"
    ]),
    ("product_interest", [
        "product", "subscribe", "service", "premium", "cost", "pricing", "membership"
    ]),
    ("platform_request", [
        "platform", "discord", "telegram", "substack", "channel", "group", "bot"
    ]),
    ("content_topic_request", [
        "suggest", "cover", "write about", "next topic", "future topic", "analyze"
    ]),
    ("clarification_question", [
        "explain", "what does", "mean", "clarify", "confused", "question", "how to"
    ]),
    ("spam_or_low_signal", [
        "spam", "ad", "promo", "lol", "nice", "ok", "great", "hello", "hi", "hey"
    ])
]


def classify_text(text: str) -> str:
    """Classifies a string of text into a category based on keywords."""
    lower_text = text.lower()
    for category, keywords in CLASSIFICATIONS:
        if any(k in lower_text for k in keywords):
            return category
    return "clarification_question"  # Default fallback


def generate_clusters(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Groups snapshots into clusters deterministically based on classification."""
    grouped: dict[str, list[dict[str, Any]]] = {}

    for snap in snapshots:
        raw_text = snap.get("raw_feedback_text_redacted", "")
        # Run classification on redacted text
        category = classify_text(raw_text)
        grouped.setdefault(category, []).append(snap)

    clusters = []
    for label, snaps in grouped.items():
        snap_ids = [s.get("snapshot_id") for s in snaps]
        
        # Build safe summary
        safe_summary = f"Operator-redacted feedback questions challenge related to {label}."
        
        # Set suggested response mode
        if label == "unsafe_financial_advice_request":
            suggested_response_mode = "BLOCKED_NO_RESPONSE"
            backlog_candidate_allowed = False
            blocked_reasons = ["unsafe_financial_advice_request_detected"]
        elif label == "source_request":
            suggested_response_mode = "MANUAL_SOURCE_LINK_ONLY"
            backlog_candidate_allowed = True
            blocked_reasons = []
        elif label == "correction_request":
            suggested_response_mode = "MANUAL_EDITORIAL_CORRECTION"
            backlog_candidate_allowed = True
            blocked_reasons = []
        elif label == "spam_or_low_signal":
            suggested_response_mode = "DISMISS_NO_ACTION"
            backlog_candidate_allowed = False
            blocked_reasons = []
        else:
            suggested_response_mode = "MANUAL_OPERATOR_REVIEW"
            backlog_candidate_allowed = True
            blocked_reasons = []

        # If any snapshot in the cluster is blocked, the cluster inherits blockers
        for s in snaps:
            for b in s.get("blocked_reasons", []):
                if b not in blocked_reasons:
                    blocked_reasons.append(b)
                # If any representative has personal/sensitive data blockers, disable backlog candidate
                if b in ["private_identifier_detected", "secret_or_destination_material_detected"]:
                    backlog_candidate_allowed = False

        # Generate cluster ID
        hasher = hashlib.sha256(label.encode("utf-8"))
        cluster_id = f"cluster_{hasher.hexdigest()[:12]}"

        clusters.append({
            "cluster_id": cluster_id,
            "cluster_label": label,
            "representative_feedback_refs": sorted(snap_ids),
            "safe_summary": safe_summary,
            "suggested_response_mode": suggested_response_mode,
            "backlog_candidate_allowed": backlog_candidate_allowed,
            "blocked_reasons": sorted(blocked_reasons)
        })

    # Sort clusters by label for determinism
    return sorted(clusters, key=lambda c: c["cluster_label"])
