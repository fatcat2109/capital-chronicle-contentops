"""Tests for the approval ledger and one-button dispatch gate (SCD, 0174AS).

Local-only, deterministic, fail-closed. Verifies schema shape, per-object
validation states, operator attestation requirements, append-only/immutable
ledger rules, freeze hash completeness and mutation blocking, one-button gate
preconditions, credential/API/Telegram implication blocking, forbidden
financial/signal language blocking, deterministic canonical hashing, and that
no live/public/executable readiness can be granted. No network, providers,
credentials, platform APIs, webhooks, OAuth, or live behavior.
"""
import json
import os
from pathlib import Path

from live_contentops import scd_dispatch_gate as dg

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scd_dispatch_gate"


def _load(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Operator decision ------------------------------------------------------------

def test_operator_decision_pass():
    res = dg.validate_operator_decision_packet(_load("operator_decision_pass.json"))
    assert res["validation_state"] == dg.PASS, res


def test_operator_decision_blocked_missing_attestation():
    res = dg.validate_operator_decision_packet(_load("operator_decision_blocked_attestation.json"))
    assert res["validation_state"] == dg.BLOCKED, res


def test_operator_decision_blocked_signal_language():
    res = dg.validate_operator_decision_packet(_load("operator_decision_blocked_signal.json"))
    assert res["validation_state"] == dg.BLOCKED, res


def test_operator_decision_requires_full_attestation():
    packet = _load("operator_decision_pass.json")
    packet["operator_attestation"]["reviewed_citations"] = False
    res = dg.validate_operator_decision_packet(packet)
    assert res["validation_state"] == dg.BLOCKED, res


# --- Approval ledger entry --------------------------------------------------------

def test_ledger_entry_pass():
    res = dg.validate_approval_ledger_entry(_load("ledger_entry_pass.json"))
    assert res["validation_state"] == dg.PASS, res


def test_ledger_entry_blocked_executable():
    res = dg.validate_approval_ledger_entry(_load("ledger_entry_blocked_executable.json"))
    assert res["validation_state"] == dg.BLOCKED, res


def test_ledger_entry_blocked_secret():
    res = dg.validate_approval_ledger_entry(_load("ledger_entry_blocked_secret.json"))
    assert res["validation_state"] == dg.BLOCKED, res


def test_ledger_entry_unknown_missing_prev_hash():
    res = dg.validate_approval_ledger_entry(_load("ledger_entry_unknown_prev_hash.json"))
    assert res["validation_state"] == dg.UNKNOWN, res


def test_ledger_entry_requires_append_only():
    entry = _load("ledger_entry_pass.json")
    entry["append_only"] = False
    res = dg.validate_approval_ledger_entry(entry)
    assert res["validation_state"] == dg.BLOCKED, res


def test_ledger_entry_requires_immutable():
    entry = _load("ledger_entry_pass.json")
    entry["immutable_after_write"] = False
    res = dg.validate_approval_ledger_entry(entry)
    assert res["validation_state"] == dg.BLOCKED, res


# --- Freeze manifest --------------------------------------------------------------

def test_freeze_manifest_pass():
    res = dg.validate_dispatch_freeze_manifest(_load("freeze_manifest_pass.json"))
    assert res["validation_state"] == dg.PASS, res


def test_freeze_manifest_blocked_mutation():
    res = dg.validate_dispatch_freeze_manifest(_load("freeze_manifest_blocked_mutation.json"))
    assert res["validation_state"] == dg.BLOCKED, res


def test_freeze_manifest_incomplete_review():
    manifest = _load("freeze_manifest_pass.json")
    manifest["freeze_complete"] = False
    res = dg.validate_dispatch_freeze_manifest(manifest)
    assert res["validation_state"] == dg.REVIEW_REQUIRED, res


# --- Gate request -----------------------------------------------------------------

def test_gate_request_pass():
    res = dg.validate_one_button_dispatch_gate_request(_load("gate_request_pass.json"))
    assert res["validation_state"] == dg.PASS, res


def test_gate_request_blocked_button_while_upstream_blocked():
    res = dg.validate_one_button_dispatch_gate_request(_load("gate_request_blocked_button.json"))
    assert res["validation_state"] == dg.BLOCKED, res


def test_gate_request_blocked_live():
    res = dg.validate_one_button_dispatch_gate_request(_load("gate_request_blocked_live.json"))
    assert res["validation_state"] == dg.BLOCKED, res


def test_gate_request_review_required():
    res = dg.validate_one_button_dispatch_gate_request(_load("gate_request_review_required.json"))
    assert res["validation_state"] == dg.REVIEW_REQUIRED, res


def test_gate_request_unknown_missing_ref():
    res = dg.validate_one_button_dispatch_gate_request(_load("gate_request_unknown_missing_ref.json"))
    assert res["validation_state"] == dg.UNKNOWN, res


def test_gate_request_button_cannot_enable_without_all_preconditions():
    req = _load("gate_request_pass.json")
    req["precondition_summary"]["kill_switch_clear_for_mock"] = False
    res = dg.validate_one_button_dispatch_gate_request(req)
    assert res["validation_state"] == dg.BLOCKED, res


# --- Gate result ------------------------------------------------------------------

def test_gate_result_pass():
    res = dg.validate_one_button_dispatch_gate_result(_load("gate_result_pass.json"))
    assert res["validation_state"] == dg.PASS, res


def test_gate_result_blocked_live():
    res = dg.validate_one_button_dispatch_gate_result(_load("gate_result_blocked_live.json"))
    assert res["validation_state"] == dg.BLOCKED, res


def test_gate_result_blocked_telegram():
    res = dg.validate_one_button_dispatch_gate_result(_load("gate_result_blocked_telegram.json"))
    assert res["validation_state"] == dg.BLOCKED, res


# --- Cross-object binding ---------------------------------------------------------

def test_gate_binding_ready_only_when_both_pass():
    binding = dg.validate_gate_binding(
        _load("gate_request_pass.json"), _load("gate_result_pass.json")
    )
    assert binding["mock_dispatch_ready"] is True, binding
    assert binding["live_ready"] is False, binding
    assert binding["executable_dispatch"] is False, binding


def test_gate_binding_fails_closed_on_blocked_request():
    binding = dg.validate_gate_binding(
        _load("gate_request_blocked_live.json"), _load("gate_result_pass.json")
    )
    assert binding["mock_dispatch_ready"] is False, binding
    assert binding["live_ready"] is False, binding


# --- Canonical hash helper --------------------------------------------------------

def test_canonical_hash_is_deterministic_regardless_of_key_order():
    a = {"x": 1, "y": [2, 3], "z": {"b": 4, "a": 5}}
    b = {"z": {"a": 5, "b": 4}, "y": [2, 3], "x": 1}
    assert dg.canonical_json_sha256(a) == dg.canonical_json_sha256(b)


def test_canonical_hash_changes_on_content_change():
    a = {"x": 1}
    b = {"x": 2}
    assert dg.canonical_json_sha256(a) != dg.canonical_json_sha256(b)


def test_canonical_hash_prefix():
    assert dg.canonical_json_sha256({"x": 1}).startswith("canonical_json_sha256:")


# --- Global flag invariants -------------------------------------------------------

def test_no_fixture_grants_live_or_executable():
    for fname in os.listdir(FIXTURE_DIR):
        data = _load(fname)
        # blocked_live / blocked_executable fixtures intentionally set true to
        # prove blocking; all others must keep these false.
        if "blocked_live" in fname or "blocked_executable" in fname:
            continue
        assert data.get("live_ready") in (False, None), fname
        assert data.get("executable_dispatch") in (False, None), fname
        assert data.get("public_ready") in (False, None), fname
