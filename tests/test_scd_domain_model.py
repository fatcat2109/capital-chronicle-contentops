"""Tests for the unified Supervised Content Distribution (SCD) domain model.

Local-only, deterministic, fail-closed. Validates schema shape, per-object
validation states (PASS / BLOCKED / REVIEW_REQUIRED / UNKNOWN), and cross-object
dispatch-readiness invariants. No network, credentials, or live behavior.
"""
import json
from pathlib import Path

import pytest

from live_contentops import scd_domain_model as scd

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scd_domain_model"


def _load(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


# --- ContentIntentPacket ----------------------------------------------------------

def test_intent_lane_a_pass():
    res = scd.validate_content_intent_packet(_load("intent_lane_a_pass.json"))
    assert res["validation_state"] == scd.PASS, res


def test_intent_lane_b_pass():
    res = scd.validate_content_intent_packet(_load("intent_lane_b_pass.json"))
    assert res["validation_state"] == scd.PASS, res


def test_intent_blocked_financial():
    res = scd.validate_content_intent_packet(_load("intent_blocked_financial.json"))
    assert res["validation_state"] == scd.BLOCKED, res


def test_intent_blocked_fake_artifact():
    res = scd.validate_content_intent_packet(_load("intent_blocked_fake_artifact.json"))
    assert res["validation_state"] == scd.BLOCKED, res


def test_intent_unknown():
    res = scd.validate_content_intent_packet(_load("intent_unknown.json"))
    assert res["validation_state"] == scd.UNKNOWN, res


# --- CanonicalSocialPost ----------------------------------------------------------

def test_post_pass():
    res = scd.validate_canonical_social_post(_load("post_pass.json"))
    assert res["validation_state"] == scd.PASS, res


# --- PlatformPayload --------------------------------------------------------------

def test_payload_pass():
    res = scd.validate_platform_payload(_load("payload_pass.json"))
    assert res["validation_state"] == scd.PASS, res


def test_payload_live_eligibility_blocked():
    payload = _load("payload_pass.json")
    payload["live_eligibility"] = True
    res = scd.validate_platform_payload(payload)
    assert res["validation_state"] == scd.BLOCKED, res


# --- ApprovalPacket ---------------------------------------------------------------

def test_approval_pass():
    res = scd.validate_approval_packet(_load("approval_pass.json"))
    assert res["validation_state"] == scd.PASS, res


def test_approval_review_required():
    res = scd.validate_approval_packet(_load("approval_review_required.json"))
    assert res["validation_state"] == scd.REVIEW_REQUIRED, res


def test_approval_auto_approved_blocked():
    packet = _load("approval_pass.json")
    packet["auto_approved"] = True
    res = scd.validate_approval_packet(packet)
    assert res["validation_state"] == scd.BLOCKED, res


# --- DispatchPacket ---------------------------------------------------------------

def test_dispatch_pass():
    res = scd.validate_dispatch_packet(_load("dispatch_pass.json"))
    assert res["validation_state"] == scd.PASS, res


def test_dispatch_blocked_upstream():
    res = scd.validate_dispatch_packet(_load("dispatch_blocked_upstream.json"))
    assert res["validation_state"] == scd.BLOCKED, res


def test_dispatch_live_ready_blocked():
    packet = _load("dispatch_pass.json")
    packet["live_ready"] = True
    res = scd.validate_dispatch_packet(packet)
    assert res["validation_state"] == scd.BLOCKED, res


def test_dispatch_executable_blocked():
    packet = _load("dispatch_pass.json")
    packet["executable_dispatch"] = True
    res = scd.validate_dispatch_packet(packet)
    assert res["validation_state"] == scd.BLOCKED, res


# --- RedactedAuditEvent -----------------------------------------------------------

def test_audit_pass():
    res = scd.validate_redacted_audit_event(_load("audit_pass.json"))
    assert res["validation_state"] == scd.PASS, res


def test_audit_blocked_secret():
    res = scd.validate_redacted_audit_event(_load("audit_blocked_secret.json"))
    assert res["validation_state"] == scd.BLOCKED, res


def test_audit_rejects_token_even_if_redaction_claimed():
    event = _load("audit_pass.json")
    event["redacted_request_placeholder"] = "bearer sk-ABCDEFGH12345678"
    res = scd.validate_redacted_audit_event(event)
    assert res["validation_state"] == scd.BLOCKED, res


# --- MetricsRecord ----------------------------------------------------------------

def test_metrics_pass():
    res = scd.validate_metrics_record(_load("metrics_pass.json"))
    assert res["validation_state"] == scd.PASS, res


def test_metrics_blocked_scrape():
    res = scd.validate_metrics_record(_load("metrics_blocked_scrape.json"))
    assert res["validation_state"] == scd.BLOCKED, res


def test_metrics_blocked_live_api():
    rec = _load("metrics_pass.json")
    rec["live_api_import_used"] = True
    res = scd.validate_metrics_record(rec)
    assert res["validation_state"] == scd.BLOCKED, res


# --- Cross-object invariants ------------------------------------------------------

def test_dispatch_readiness_all_pass():
    objects = {
        "content_intent_packet": _load("intent_lane_a_pass.json"),
        "canonical_social_post": _load("post_pass.json"),
        "platform_payload": _load("payload_pass.json"),
        "approval_packet": _load("approval_pass.json"),
        "dispatch_packet": _load("dispatch_pass.json"),
        "redacted_audit_event": _load("audit_pass.json"),
        "metrics_record": _load("metrics_pass.json"),
    }
    res = scd.validate_dispatch_readiness(objects)
    assert res["dispatch_ready"] is True, res
    # Live readiness is NEVER granted by this task.
    assert res["live_ready"] is False, res


def test_dispatch_readiness_fails_closed_on_bad_upstream():
    objects = {
        "content_intent_packet": _load("intent_blocked_financial.json"),
        "dispatch_packet": _load("dispatch_pass.json"),
    }
    res = scd.validate_dispatch_readiness(objects)
    assert res["dispatch_ready"] is False, res
    assert res["live_ready"] is False, res


def test_dispatch_readiness_fails_closed_on_unknown_upstream():
    objects = {
        "content_intent_packet": _load("intent_unknown.json"),
        "dispatch_packet": _load("dispatch_pass.json"),
    }
    res = scd.validate_dispatch_readiness(objects)
    assert res["dispatch_ready"] is False, res


def test_no_object_grants_live_readiness():
    # Defensive: even a fully-PASS pipeline cannot flip live_ready true.
    objects = {
        "dispatch_packet": _load("dispatch_pass.json"),
    }
    res = scd.validate_dispatch_readiness(objects)
    assert res["live_ready"] is False, res
