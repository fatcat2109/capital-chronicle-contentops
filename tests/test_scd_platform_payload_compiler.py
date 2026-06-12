"""Tests for the platform payload compiler contract (SCD, 0174AR).

Local-only, deterministic, fail-closed. Verifies schema shape, per-object
validation states, character-limit enforcement, limitation/citation
preservation, unsupported-feature/unknown-platform handling, Telegram bot/API
blocking, forbidden financial/signal language blocking, and that no live/public/
dispatch readiness can be granted. The compiler helper invents nothing.
No network, providers, credentials, platform APIs, or live behavior.
"""
import json
import os
from pathlib import Path

from live_contentops import scd_platform_payload_compiler as cc

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scd_platform_payload_compiler"


def _load(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Constraint profiles ----------------------------------------------------------

def test_profile_x_twitter_pass():
    res = cc.validate_platform_constraint_profile(_load("profile_x_twitter_pass.json"))
    assert res["validation_state"] == cc.PASS, res


def test_profile_linkedin_pass():
    res = cc.validate_platform_constraint_profile(_load("profile_linkedin_pass.json"))
    assert res["validation_state"] == cc.PASS, res


def test_profile_telegram_pass_no_bot_api():
    res = cc.validate_platform_constraint_profile(_load("profile_telegram_pass.json"))
    assert res["validation_state"] == cc.PASS, res


def test_profile_must_be_manual_publish_only():
    profile = _load("profile_x_twitter_pass.json")
    profile["manual_publish_only"] = False
    res = cc.validate_platform_constraint_profile(profile)
    assert res["validation_state"] == cc.BLOCKED, res


def test_profile_live_api_future_blocks():
    profile = _load("profile_telegram_pass.json")
    profile["live_api_supported_future"] = True
    res = cc.validate_platform_constraint_profile(profile)
    assert res["validation_state"] == cc.BLOCKED, res


# --- Compiler input ---------------------------------------------------------------

def test_input_pass():
    res = cc.validate_platform_payload_compiler_input(_load("input_pass.json"))
    assert res["validation_state"] == cc.PASS, res


def test_input_unknown_missing_lineage():
    res = cc.validate_platform_payload_compiler_input(_load("input_unknown.json"))
    assert res["validation_state"] == cc.UNKNOWN, res


def test_input_blocks_public_ready():
    packet = _load("input_pass.json")
    packet["public_ready"] = True
    res = cc.validate_platform_payload_compiler_input(packet)
    assert res["validation_state"] == cc.BLOCKED, res


def test_input_blocks_live_eligibility():
    packet = _load("input_pass.json")
    packet["live_eligibility"] = True
    res = cc.validate_platform_payload_compiler_input(packet)
    assert res["validation_state"] == cc.BLOCKED, res


# --- Compiler output --------------------------------------------------------------

def test_output_pass():
    res = cc.validate_platform_payload_compiler_output(_load("output_pass.json"))
    assert res["validation_state"] == cc.PASS, res


def test_output_blocked_overflow():
    res = cc.validate_platform_payload_compiler_output(_load("output_blocked_overflow.json"))
    assert res["validation_state"] == cc.BLOCKED, res


def test_output_blocked_removes_limitation():
    res = cc.validate_platform_payload_compiler_output(_load("output_blocked_removes_limitation.json"))
    assert res["validation_state"] == cc.BLOCKED, res


def test_output_blocked_citation():
    res = cc.validate_platform_payload_compiler_output(_load("output_blocked_citation.json"))
    assert res["validation_state"] == cc.BLOCKED, res


def test_output_blocked_signal_language():
    res = cc.validate_platform_payload_compiler_output(_load("output_blocked_signal.json"))
    assert res["validation_state"] == cc.BLOCKED, res


def test_output_blocked_telegram_api():
    res = cc.validate_platform_payload_compiler_output(_load("output_blocked_telegram_api.json"))
    assert res["validation_state"] == cc.BLOCKED, res


def test_output_blocked_public_or_live():
    res = cc.validate_platform_payload_compiler_output(_load("output_blocked_public.json"))
    assert res["validation_state"] == cc.BLOCKED, res


def test_output_review_required():
    res = cc.validate_platform_payload_compiler_output(_load("output_review_required.json"))
    assert res["validation_state"] == cc.REVIEW_REQUIRED, res


def test_output_unknown_platform():
    res = cc.validate_platform_payload_compiler_output(_load("output_unknown_platform.json"))
    assert res["validation_state"] == cc.UNKNOWN, res


def test_output_overflow_blocks_even_if_subresults_pass():
    out = _load("output_pass.json")
    out["platform_payloads"][0]["character_count"] = 9999
    res = cc.validate_platform_payload_compiler_output(out)
    assert res["validation_state"] == cc.BLOCKED, res


# --- Compile report ---------------------------------------------------------------

def test_report_pass():
    res = cc.validate_platform_payload_compile_report(_load("report_pass.json"))
    assert res["validation_state"] == cc.PASS, res


def test_report_blocked_contradiction():
    res = cc.validate_platform_payload_compile_report(_load("report_blocked_contradiction.json"))
    assert res["validation_state"] == cc.BLOCKED, res


def test_report_blocked_live_ready():
    res = cc.validate_platform_payload_compile_report(_load("report_blocked_live_ready.json"))
    assert res["validation_state"] == cc.BLOCKED, res


def test_report_cannot_pass_with_any_non_pass_platform():
    report = _load("report_pass.json")
    report["per_platform_results"].append({"platform_id": "telegram", "result": "REVIEW_REQUIRED"})
    res = cc.validate_platform_payload_compile_report(report)
    assert res["validation_state"] == cc.BLOCKED, res


# --- Compiler helper --------------------------------------------------------------

def test_compile_helper_invents_nothing():
    input_packet = _load("input_pass.json")
    profiles = [
        _load("profile_x_twitter_pass.json"),
        _load("profile_linkedin_pass.json"),
        _load("profile_telegram_pass.json"),
    ]
    candidates = cc.compile_platform_payloads(input_packet, profiles)
    assert len(candidates) == len(input_packet["requested_platforms"])
    for cand in candidates:
        # No invented links / hashtags.
        assert cand["hashtags"] == []
        assert cand["links"] == []
        # Mode is always dry_run.
        assert cand["mode"] == "dry_run"
        # Text is exactly the supplied source text (no invention).
        assert cand["text"] == input_packet["source_text"]
        # Citations/limitations carried forward verbatim.
        assert cand["citations"] == input_packet["source_citations"]
        assert cand["limitations"] == input_packet["source_limitations"]


def test_compile_helper_output_validates_pass():
    input_packet = _load("input_pass.json")
    profiles = [
        _load("profile_x_twitter_pass.json"),
        _load("profile_linkedin_pass.json"),
        _load("profile_telegram_pass.json"),
    ]
    candidates = cc.compile_platform_payloads(input_packet, profiles)
    # Build a minimal output object around the candidates and validate it.
    output = {
        "schema_version": "1.0",
        "compiler_output_id": "cout_helper_001",
        "compiler_input_id": input_packet["compiler_input_id"],
        "platform_payloads": candidates,
        "unsupported_feature_flags": [],
        "operator_review_required": True,
        "public_ready": False,
        "live_eligibility": False,
        "validation_state": "PASS",
        "blocked_reasons": [],
    }
    res = cc.validate_platform_payload_compiler_output(output)
    assert res["validation_state"] == cc.PASS, res


# --- Global flag invariants -------------------------------------------------------

def test_no_output_fixture_is_public_or_live():
    for fname in os.listdir(FIXTURE_DIR):
        if fname.startswith("output_") and "blocked_public" not in fname:
            data = _load(fname)
            assert data.get("public_ready") is False, fname
            assert data.get("live_eligibility") is False, fname


def test_no_report_fixture_is_live_or_dispatch_ready():
    for fname in os.listdir(FIXTURE_DIR):
        if fname.startswith("report_") and "blocked_live" not in fname:
            data = _load(fname)
            assert data.get("live_ready") is False, fname
            assert data.get("dispatch_ready") is False, fname
