"""Tests for the compiler v2 -> approval/dispatch boundary bridge (SCD, 0174BP).

Local-only, deterministic. Verifies fail-closed reconciliation of a compiler v2
compile report against BOTH an approval-ledger candidate and a
dispatch-gate/freeze candidate, deterministic hash re-derivation, the
compile-pass trust-gap closure, global no-live invariants, and a data-driven
hostile/degraded harness.
"""
import json
import os

import pytest

from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
)
from live_contentops.scd_dispatch_gate import canonical_json_sha256
from live_contentops.scd_compiler_v2_dispatch_bridge import (
    ALLOWED_BRIDGE_MODE,
    REQUIRED_FALSE_FLAGS_BRIDGE,
    COMPILER_V2_DISPATCH_BRIDGE_VALIDATORS,
    derive_platform_payload_hashes_v2,
    reconcile_report_with_approval_ledger_v2,
    reconcile_report_with_dispatch_gate_v2,
    build_compiler_v2_dispatch_bridge_result,
    validate_compiler_v2_dispatch_bridge_result,
)

BRIDGE_FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "scd_compiler_v2_dispatch_bridge",
)
COMPILER_FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "scd_platform_payload_compiler_v2",
)


def _load(directory, name):
    with open(os.path.join(directory, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _bridge(name):
    return _load(BRIDGE_FIXTURE_DIR, name)


def _compiler(name):
    return _load(COMPILER_FIXTURE_DIR, name)


# --- Deterministic hash re-derivation -------------------------------------------------

def test_derive_hashes_is_deterministic_and_canonical():
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    first = derive_platform_payload_hashes_v2(output)
    second = derive_platform_payload_hashes_v2(output)
    assert first == second
    assert len(first) == len(output["platform_payloads"])
    # each derived hash is the shared canonical helper over the payload object
    for payload, derived in zip(output["platform_payloads"], first):
        assert derived == canonical_json_sha256(payload)
        assert derived.startswith("canonical_json_sha256:")


def test_derive_hashes_key_order_independent():
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    baseline = derive_platform_payload_hashes_v2(output)
    reordered = {
        "platform_payloads": [
            {k: payload[k] for k in reversed(list(payload.keys()))}
            for payload in output["platform_payloads"]
        ]
    }
    assert derive_platform_payload_hashes_v2(reordered) == baseline


def test_derive_hashes_empty_output():
    assert derive_platform_payload_hashes_v2({}) == []


# --- Valid combined bridge result -----------------------------------------------------

def test_valid_bridge_result_review_required_not_blocked():
    packet = _bridge("bridge_result_valid_review_required.json")
    result = validate_compiler_v2_dispatch_bridge_result(packet)
    # tiktok high-friction report is REVIEW_REQUIRED; bridge degrades, never blocks
    assert result["validation_state"] == REVIEW_REQUIRED


def test_valid_bridge_result_mode_and_flags():
    packet = _bridge("bridge_result_valid_review_required.json")
    assert packet["bridge_mode"] == ALLOWED_BRIDGE_MODE
    assert packet["operator_review_required"] is True
    for flag in REQUIRED_FALSE_FLAGS_BRIDGE:
        assert packet[flag] is False


def test_valid_bridge_result_subresults_present():
    packet = _bridge("bridge_result_valid_review_required.json")
    assert packet["approval_reconciliation"]
    assert packet["dispatch_reconciliation"]
    assert packet["approval_reconciliation"]["hash_match"] is True
    assert packet["dispatch_reconciliation"]["hash_match"] is True


# --- Approval-ledger reconciliation ---------------------------------------------------

def test_approval_ledger_matching_hashes_not_blocked():
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    ledger = _bridge("approval_ledger_entry_valid.json")
    result = reconcile_report_with_approval_ledger_v2(report, ledger, output)
    assert result["result"] != BLOCKED
    assert result["hash_match"] is True
    assert result["lineage_matches_report"] is True


def test_approval_ledger_hash_mismatch_blocks():
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    ledger = _bridge("approval_ledger_entry_valid.json")
    tampered = json.loads(json.dumps(ledger))
    tampered["platform_payload_hash_refs"] = ["canonical_json_sha256:deadbeef"]
    result = reconcile_report_with_approval_ledger_v2(report, tampered, output)
    assert result["result"] == BLOCKED
    assert any("payload_hash_mismatch" in r for r in result["reasons"])


def test_approval_ledger_lineage_mismatch_blocks():
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    ledger = _bridge("approval_ledger_entry_valid.json")
    tampered = json.loads(json.dumps(ledger))
    tampered["compiler_output_id"] = "cout_some_other_output"
    result = reconcile_report_with_approval_ledger_v2(report, tampered, output)
    assert result["result"] == BLOCKED
    assert any("compiler_output_id_mismatch" in r for r in result["reasons"])


def test_approval_ledger_missing_refs_unknown():
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    ledger = _bridge("approval_ledger_entry_valid.json")
    no_refs = json.loads(json.dumps(ledger))
    no_refs["platform_payload_hash_refs"] = []
    result = reconcile_report_with_approval_ledger_v2(report, no_refs, output)
    assert result["result"] == UNKNOWN


# --- Dispatch-gate / freeze reconciliation --------------------------------------------

def test_dispatch_gate_consistent_claim_not_blocked():
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    gate = _bridge("dispatch_gate_request_valid.json")
    freeze = _bridge("dispatch_freeze_manifest_valid.json")
    result = reconcile_report_with_dispatch_gate_v2(report, gate, freeze, output)
    assert result["result"] != BLOCKED
    assert result["claim_consistent"] is True
    assert result["hash_match"] is True


def test_dispatch_gate_false_compile_pass_claim_blocks():
    # Core trust-gap closure: gate self-asserts platform_compile_pass while the
    # report's final_recommendation is REVIEW_REQUIRED.
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    gate = _bridge("dispatch_gate_request_valid.json")
    freeze = _bridge("dispatch_freeze_manifest_valid.json")
    lying = json.loads(json.dumps(gate))
    lying["precondition_summary"]["platform_compile_pass"] = True
    result = reconcile_report_with_dispatch_gate_v2(report, lying, freeze, output)
    assert result["result"] == BLOCKED
    assert result["claim_consistent"] is False
    assert any("gate_claims_compile_pass_but_report_is" in r for r in result["reasons"])


def test_dispatch_freeze_hash_mismatch_blocks():
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    gate = _bridge("dispatch_gate_request_valid.json")
    freeze = _bridge("dispatch_freeze_manifest_valid.json")
    tampered = json.loads(json.dumps(freeze))
    tampered["platform_payload_hashes"] = ["canonical_json_sha256:tampered"]
    result = reconcile_report_with_dispatch_gate_v2(report, gate, tampered, output)
    assert result["result"] == BLOCKED
    assert any("payload_hash_mismatch" in r for r in result["reasons"])


def test_dispatch_mutation_after_freeze_blocks():
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    gate = _bridge("dispatch_gate_request_valid.json")
    freeze = _bridge("dispatch_freeze_manifest_valid.json")
    mutated = json.loads(json.dumps(freeze))
    mutated["mutation_after_freeze_detected"] = True
    result = reconcile_report_with_dispatch_gate_v2(report, gate, mutated, output)
    assert result["result"] == BLOCKED
    assert any("mutation_after_freeze_detected" in r for r in result["reasons"])


# --- Combined builder never grants readiness ------------------------------------------

def test_builder_forces_all_readiness_false():
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    ledger = _bridge("approval_ledger_entry_valid.json")
    gate = _bridge("dispatch_gate_request_valid.json")
    freeze = _bridge("dispatch_freeze_manifest_valid.json")
    built = build_compiler_v2_dispatch_bridge_result(report, output, ledger, gate, freeze)
    assert built["bridge_mode"] == ALLOWED_BRIDGE_MODE
    assert built["operator_review_required"] is True
    for flag in REQUIRED_FALSE_FLAGS_BRIDGE:
        assert built[flag] is False
    assert built["validation_state"] != PASS


def test_builder_does_not_mutate_inputs():
    report = _compiler("compiler_v2_report_valid_review_required.json")
    output = _compiler("compiler_v2_output_valid_all_platforms.json")
    ledger = _bridge("approval_ledger_entry_valid.json")
    gate = _bridge("dispatch_gate_request_valid.json")
    freeze = _bridge("dispatch_freeze_manifest_valid.json")
    before = json.dumps([report, output, ledger, gate, freeze], sort_keys=True)
    build_compiler_v2_dispatch_bridge_result(report, output, ledger, gate, freeze)
    after = json.dumps([report, output, ledger, gate, freeze], sort_keys=True)
    assert before == after


# --- Global no-live invariant across all valid fixtures -------------------------------

def _iter_bool_flags(node):
    if isinstance(node, dict):
        for key, val in node.items():
            yield key, val
            yield from _iter_bool_flags(val)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_bool_flags(item)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "approval_ledger_entry_valid.json",
        "dispatch_freeze_manifest_valid.json",
        "dispatch_gate_request_valid.json",
        "bridge_result_valid_review_required.json",
    ],
)
def test_valid_fixtures_never_enable_live(fixture_name):
    data = _bridge(fixture_name)
    forbidden_true = {
        "public_ready",
        "live_eligibility",
        "live_ready",
        "dispatch_ready",
        "mock_dispatch_ready",
        "executable_dispatch",
        "live_api_enabled_now",
        "platform_api_allowed_now",
        "credential_read_allowed_now",
        "credentials_requested_now",
        "posting_enabled_now",
        "scheduler_enabled_now",
        "autonomous_replies_enabled_now",
        "dms_enabled_now",
        "scraping_enabled_now",
    }
    for key, val in _iter_bool_flags(data):
        if key in forbidden_true:
            assert val is not True, f"{fixture_name}:{key} must not be true"


# --- Data-driven hostile / degraded harness ------------------------------------------

def test_hostile_cases_fail_closed():
    cases = _bridge("hostile_degraded_cases.json")["cases"]
    assert cases
    for case in cases:
        validator = COMPILER_V2_DISPATCH_BRIDGE_VALIDATORS[case["kind"]]
        result = validator(case["packet"])
        assert result["validation_state"] == case["expected_state"], (
            f"{case['case_id']}: expected {case['expected_state']}, "
            f"got {result['validation_state']} ({result['reasons']})"
        )
        # a hostile case may never resolve to PASS
        assert result["validation_state"] != PASS
