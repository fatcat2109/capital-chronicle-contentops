"""Minimal tests for the operator evidence surface contract bridge (0174BU PREP02).

Local-only, deterministic, fail-closed. These tests project the ALREADY-ACCEPTED
0174BT operator evidence summary PASS fixture into the surface contract and assert
evidence-only / no-grant invariants. They grant nothing and touch no network,
credential, env, platform, provider, scheduler, posting, or browser surface.
"""
import copy
import json
from pathlib import Path

from live_contentops.scd_domain_model import PASS, BLOCKED, UNKNOWN
from live_contentops.scd_operator_evidence_surface_contract import (
    build_operator_evidence_surface_contract,
    validate_operator_evidence_surface_contract,
    build_static_js_bridge,
)

ROOT = Path(__file__).resolve().parents[1]
PASS_FIXTURE = (
    ROOT
    / "fixtures"
    / "scd_operator_evidence_summary"
    / "operator_evidence_summary_valid_pass_manual_only.json"
)


def _load_pass_summary():
    with open(PASS_FIXTURE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_build_contract_from_pass_fixture_validates_pass():
    summary = _load_pass_summary()
    packet = build_operator_evidence_surface_contract(summary)

    assert packet["source_evidence_baseline_head"] == "add55ea1c7447770cb9382f86af1794b951ae8f1"
    assert packet["no_grant_label"] == "EVIDENCE ONLY / NO GRANT"

    assert packet["evidence_only"] is True
    assert packet["local_only"] is True
    assert packet["manual_review_required"] is True

    for flag in (
        "public_ready",
        "live_ready",
        "dispatch_ready",
        "platform_api_allowed_now",
        "credential_read_allowed_now",
        "scheduler_enabled_now",
        "posting_enabled_now",
        "readiness_granted",
    ):
        assert packet[flag] is False, flag

    result = validate_operator_evidence_surface_contract(packet)
    assert result["validation_state"] == PASS


def test_build_contract_does_not_mutate_source_summary():
    summary = _load_pass_summary()
    before = copy.deepcopy(summary)
    build_operator_evidence_surface_contract(summary)
    assert summary == before


def test_required_false_flag_true_blocks():
    summary = _load_pass_summary()
    packet = build_operator_evidence_surface_contract(summary)
    packet["credential_read_allowed_now"] = True

    result = validate_operator_evidence_surface_contract(packet)
    assert result["validation_state"] == BLOCKED
    assert any("credential_read_allowed_now" in r for r in result["reasons"])


def test_missing_lineage_id_is_unknown_not_pass():
    summary = _load_pass_summary()
    packet = build_operator_evidence_surface_contract(summary)
    packet["bridge_report_hash"] = ""
    # Reset the declared state so we exercise the missing-lineage -> UNKNOWN
    # computation itself, not the declared-PASS contradiction guard (which would
    # otherwise fail-close a now-inconsistent PASS packet to BLOCKED).
    packet["validation_state"] = UNKNOWN

    result = validate_operator_evidence_surface_contract(packet)
    assert result["validation_state"] == UNKNOWN


def test_static_js_bridge_prefix_and_no_grant():
    summary = _load_pass_summary()
    packet = build_operator_evidence_surface_contract(summary)
    out = build_static_js_bridge(packet)

    assert out.startswith("window.CC_OPERATOR_EVIDENCE_SURFACE =")
    assert "EVIDENCE ONLY / NO GRANT" in out
    assert "http://" not in out
    assert "https://" not in out
    assert "process.env" not in out
    assert ".env" not in out
    assert "fetch(" not in out
