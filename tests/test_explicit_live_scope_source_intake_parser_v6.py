"""Tests for explicit live scope source intake parser."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.explicit_live_scope_source_intake_parser_v6 import parse_and_normalize, INBOX_DIR

ROOT = Path(__file__).resolve().parents[1]


def test_empty_inbox_blocks() -> None:
    # Ensure inbox is empty
    for f in INBOX_DIR.glob("*"):
        if f.name != ".gitkeep":
            f.unlink()
            
    res = parse_and_normalize()
    assert "blocked_missing_operator_source_artifact" in res["blocked_reasons"]
    assert res["safety_scan"] == "pending"
    assert res["candidate_id"] == ""


def test_placeholder_content_blocks() -> None:
    test_file = INBOX_DIR / "test_draft.md"
    test_file.write_text("TODO: Viết nội dung thật ở đây", encoding="utf-8")
    try:
        res = parse_and_normalize()
        assert res["safety_scan"] == "failed"
        assert any("contains_placeholder_word" in r for r in res["blocked_reasons"])
    finally:
        if test_file.exists():
            test_file.unlink()


def test_financial_advice_blocks() -> None:
    test_file = INBOX_DIR / "test_draft.json"
    test_file.write_text(json.dumps({
        "body": "This is a trade recommendation to buy X at price target Y.",
        "destination_label": "Trades Channel"
    }), encoding="utf-8")
    try:
        res = parse_and_normalize()
        assert res["safety_scan"] == "failed"
        assert any("contains_forbidden_financial_advice" in r for r in res["blocked_reasons"])
    finally:
        if test_file.exists():
            test_file.unlink()


def test_clean_content_passes() -> None:
    test_file = INBOX_DIR / "test_clean.md"
    test_file.write_text("This is clean operator announcement text without trade info.", encoding="utf-8")
    try:
        res = parse_and_normalize()
        assert res["safety_scan"] == "passed"
        assert len(res["blocked_reasons"]) == 0
        assert res["platform_family"] == "discord"
        assert res["content_type"] == "markdown"
        assert res["normalized_body_text"] == "This is clean operator announcement text without trade info."
    finally:
        if test_file.exists():
            test_file.unlink()
        # Restore empty state
        parse_and_normalize()
