"""Tests for the bounded LLM editorial workbench contract (SCD, 0174AQ).

Local-only, deterministic, fail-closed. Verifies schema shape, per-object
validation states, provider/public/approval flag blocking, limitation and
citation integrity, hallucination / invented-authority blocking, forbidden
financial/signal language blocking, and that critique never becomes approval.
No network, providers, credentials, or live behavior.
"""
import json
from pathlib import Path

from live_contentops import scd_editorial_workbench as ew

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scd_editorial_workbench"


def _load(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Voice profile ----------------------------------------------------------------

def test_voice_profile_pass():
    res = ew.validate_editorial_voice_profile(_load("voice_profile_pass.json"))
    assert res["validation_state"] == ew.PASS, res


def test_voice_profile_requires_no_market_advice_flag():
    profile = _load("voice_profile_pass.json")
    profile["no_market_advice_required"] = False
    res = ew.validate_editorial_voice_profile(profile)
    assert res["validation_state"] == ew.BLOCKED, res


# --- Hook taxonomy ----------------------------------------------------------------

def test_hook_taxonomy_pass():
    res = ew.validate_hook_taxonomy_entry(_load("hook_taxonomy_pass.json"))
    assert res["validation_state"] == ew.PASS, res


def test_hook_taxonomy_artifact_future_cannot_target_lane_ab():
    hook = _load("hook_taxonomy_pass.json")
    hook["hook_type"] = "artifact_backed_future"
    res = ew.validate_hook_taxonomy_entry(hook)
    assert res["validation_state"] == ew.BLOCKED, res


# --- Request ----------------------------------------------------------------------

def test_request_lane_a_pass():
    res = ew.validate_editorial_workbench_request(_load("request_lane_a_pass.json"))
    assert res["validation_state"] == ew.PASS, res


def test_request_lane_b_pass():
    res = ew.validate_editorial_workbench_request(_load("request_lane_b_pass.json"))
    assert res["validation_state"] == ew.PASS, res


def test_request_blocked_provider_call():
    res = ew.validate_editorial_workbench_request(_load("request_blocked_provider.json"))
    assert res["validation_state"] == ew.BLOCKED, res


def test_request_unknown_missing_lineage():
    res = ew.validate_editorial_workbench_request(_load("request_unknown.json"))
    assert res["validation_state"] == ew.UNKNOWN, res


def test_request_lane_c_requires_real_artifact_authority():
    req = _load("request_lane_a_pass.json")
    req["content_lane"] = "C"
    req["artifact_authority_state"] = "none"
    res = ew.validate_editorial_workbench_request(req)
    assert res["validation_state"] == ew.BLOCKED, res


# --- Output -----------------------------------------------------------------------

def test_output_pass():
    res = ew.validate_editorial_workbench_output(_load("output_pass.json"))
    assert res["validation_state"] == ew.PASS, res


def test_output_blocked_removes_limitation():
    res = ew.validate_editorial_workbench_output(_load("output_blocked_removes_limitation.json"))
    assert res["validation_state"] == ew.BLOCKED, res


def test_output_blocked_invents_citation():
    res = ew.validate_editorial_workbench_output(_load("output_blocked_invents_citation.json"))
    assert res["validation_state"] == ew.BLOCKED, res


def test_output_blocked_signal_language():
    res = ew.validate_editorial_workbench_output(_load("output_blocked_signal.json"))
    assert res["validation_state"] == ew.BLOCKED, res


def test_output_blocked_fake_authority():
    res = ew.validate_editorial_workbench_output(_load("output_blocked_fake_authority.json"))
    assert res["validation_state"] == ew.BLOCKED, res


def test_output_blocked_invented_metric():
    res = ew.validate_editorial_workbench_output(_load("output_blocked_invented_metric.json"))
    assert res["validation_state"] == ew.BLOCKED, res


def test_output_review_required_citation_ambiguous():
    res = ew.validate_editorial_workbench_output(_load("output_review_required.json"))
    assert res["validation_state"] == ew.REVIEW_REQUIRED, res


def test_output_cannot_be_system_approved():
    out = _load("output_pass.json")
    out["approved_by_system"] = True
    res = ew.validate_editorial_workbench_output(out)
    assert res["validation_state"] == ew.BLOCKED, res


def test_output_cannot_be_public_ready():
    out = _load("output_pass.json")
    out["public_ready"] = True
    res = ew.validate_editorial_workbench_output(out)
    assert res["validation_state"] == ew.BLOCKED, res


def test_output_cannot_add_claims():
    out = _load("output_pass.json")
    out["claims_added"] = ["an unsupported new claim"]
    res = ew.validate_editorial_workbench_output(out)
    assert res["validation_state"] == ew.BLOCKED, res


# --- Critique ---------------------------------------------------------------------

def test_critique_pass_still_requires_operator_review():
    fixture = _load("critique_pass.json")
    assert fixture["operator_review_required"] is True
    res = ew.validate_editorial_critique_packet(fixture)
    assert res["validation_state"] == ew.PASS, res


def test_critique_blocked_when_it_tries_to_approve():
    res = ew.validate_editorial_critique_packet(_load("critique_blocked_approval.json"))
    assert res["validation_state"] == ew.BLOCKED, res


def test_critique_cannot_pass_with_blocked_subresult():
    crit = _load("critique_pass.json")
    crit["forbidden_language_result"] = "BLOCKED"
    res = ew.validate_editorial_critique_packet(crit)
    assert res["validation_state"] == ew.BLOCKED, res


def test_critique_never_sets_approval_flag():
    # Even a fully-PASS critique fixture must keep approved_by_system false.
    fixture = _load("critique_pass.json")
    assert fixture.get("approved_by_system") is False


# --- Global flag invariants -------------------------------------------------------

def test_no_request_fixture_allows_provider_calls():
    for name in ("request_lane_a_pass.json", "request_lane_b_pass.json", "request_unknown.json"):
        assert _load(name)["provider_call_allowed"] is False, name


def test_no_output_fixture_is_public_or_approved():
    import os
    for fname in os.listdir(FIXTURE_DIR):
        if fname.startswith("output_"):
            data = _load(fname)
            assert data.get("public_ready") is False, fname
            assert data.get("approved_by_system") is False, fname
