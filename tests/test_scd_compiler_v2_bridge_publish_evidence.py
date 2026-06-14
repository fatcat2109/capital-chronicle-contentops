"""Tests for the compiler v2 bridge -> publish-evidence alignment layer (SCD, 0174BR).

Local-only, deterministic. Verifies that the NEW parallel evidence-alignment
module binds the ACCEPTED compiler v2 approval-dispatch bridge report (0174BP) to
publish-readiness and redacted-audit concerns as *evidence only*, fails closed
(BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS), and never grants readiness,
approval, dispatch, posting, platform API, credential access, scheduler, public
status, or creates/registers an audit event.
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
from live_contentops.scd_compiler_v2_bridge_publish_evidence import (
    EVIDENCE_SCHEMA_VERSION,
    READINESS_ALIGNMENT_MODE,
    AUDIT_ALIGNMENT_MODE,
    AUDIT_EVENT_TYPE_REQUESTED,
    COMPILER_V2_BRIDGE_PUBLISH_EVIDENCE_VALIDATORS,
    derive_bridge_report_hash,
    build_compiler_v2_bridge_publish_readiness_alignment,
    validate_compiler_v2_bridge_publish_readiness_alignment,
    build_compiler_v2_bridge_redacted_audit_alignment,
    validate_compiler_v2_bridge_redacted_audit_alignment,
)

EVIDENCE_FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "scd_compiler_v2_bridge_publish_evidence",
)
BRIDGE_FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "scd_compiler_v2_dispatch_bridge",
)

# Flags that must never be asserted true on any valid evidence-alignment object.
_NEVER_TRUE_FLAGS = (
    "readiness_granted",
    "publish_ready",
    "public_ready",
    "live_ready",
    "dispatch_ready",
    "executable_dispatch",
    "platform_api_allowed_now",
    "credential_read_allowed_now",
    "credentials_requested_now",
    "scheduler_enabled_now",
    "posting_enabled_now",
    "autonomous_replies_enabled_now",
    "dms_enabled_now",
    "scraping_enabled_now",
    "audit_event_created",
    "audit_allowlist_modified",
    "audit_event_type_registered_now",
    "credential_values_present",
    "token_values_present",
    "raw_vendor_payload_present",
)


def _load(directory, name):
    with open(os.path.join(directory, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _evidence(name):
    return _load(EVIDENCE_FIXTURE_DIR, name)


def _bridge(name):
    return _load(BRIDGE_FIXTURE_DIR, name)


def _iter_bool_flags(obj):
    for key, val in obj.items():
        if isinstance(val, bool):
            yield key, val


# --- Deterministic bridge-report hashing ---------------------------------------------

def test_bridge_report_hash_is_deterministic_and_canonical():
    report = _bridge("approval_dispatch_bridge_report_valid_pass_manual_only.json")
    first = derive_bridge_report_hash(report)
    second = derive_bridge_report_hash(report)
    assert first == second
    assert first == canonical_json_sha256(report)
    assert first.startswith("canonical_json_sha256:")


def test_bridge_report_hash_key_order_independent():
    report = _bridge("approval_dispatch_bridge_report_valid_pass_manual_only.json")
    reordered = {k: report[k] for k in reversed(list(report.keys()))}
    assert derive_bridge_report_hash(reordered) == derive_bridge_report_hash(report)


def test_bridge_report_hash_changes_on_mutation():
    report = _bridge("approval_dispatch_bridge_report_valid_pass_manual_only.json")
    baseline = derive_bridge_report_hash(report)
    mutated = dict(report)
    mutated["bridge_report_id"] = report["bridge_report_id"] + "_x"
    assert derive_bridge_report_hash(mutated) != baseline


# --- Builders bind lineage and never grant -------------------------------------------

def test_readiness_alignment_pass_path_binds_and_grants_nothing():
    report = _bridge("approval_dispatch_bridge_report_valid_pass_manual_only.json")
    packet = build_compiler_v2_bridge_publish_readiness_alignment(report)
    assert validate_compiler_v2_bridge_publish_readiness_alignment(packet)["validation_state"] == PASS
    # lineage bound
    assert packet["bridge_report_id"] == report["bridge_report_id"]
    assert packet["compiler_output_id"] == report["compiler_output_id"]
    assert packet["bridge_report_hash"] == derive_bridge_report_hash(report)
    assert packet["readiness_alignment_mode"] == READINESS_ALIGNMENT_MODE
    # PASS but still grants nothing
    for flag in _NEVER_TRUE_FLAGS:
        assert packet.get(flag) is not True


def test_readiness_alignment_review_required_propagates():
    report = _bridge("approval_dispatch_bridge_report_valid_review_required.json")
    packet = build_compiler_v2_bridge_publish_readiness_alignment(report)
    assert validate_compiler_v2_bridge_publish_readiness_alignment(packet)["validation_state"] == REVIEW_REQUIRED


def test_redacted_audit_alignment_pass_path_creates_no_event():
    report = _bridge("approval_dispatch_bridge_report_valid_pass_manual_only.json")
    packet = build_compiler_v2_bridge_redacted_audit_alignment(report)
    assert validate_compiler_v2_bridge_redacted_audit_alignment(packet)["validation_state"] == PASS
    assert packet["audit_alignment_mode"] == AUDIT_ALIGNMENT_MODE
    assert packet["audit_event_type_requested"] == AUDIT_EVENT_TYPE_REQUESTED
    assert packet["audit_event_created"] is False
    assert packet["audit_allowlist_modified"] is False
    assert packet["audit_event_type_registered_now"] is False
    assert packet["secrets_redacted"] is True
    for flag in _NEVER_TRUE_FLAGS:
        assert packet.get(flag) is not True


def test_redacted_audit_alignment_review_required_propagates():
    report = _bridge("approval_dispatch_bridge_report_valid_review_required.json")
    packet = build_compiler_v2_bridge_redacted_audit_alignment(report)
    assert validate_compiler_v2_bridge_redacted_audit_alignment(packet)["validation_state"] == REVIEW_REQUIRED


# --- Bound bridge state propagation (fail-closed) ------------------------------------

def test_readiness_alignment_blocked_bridge_blocks():
    report = _bridge("approval_dispatch_bridge_report_valid_review_required.json")
    blocked_report = dict(report)
    blocked_report["validation_state"] = BLOCKED
    blocked_report["final_recommendation"] = BLOCKED
    blocked_report["payload_hash_manifest_state"] = BLOCKED
    packet = build_compiler_v2_bridge_publish_readiness_alignment(blocked_report)
    assert validate_compiler_v2_bridge_publish_readiness_alignment(packet)["validation_state"] == BLOCKED


def test_builders_do_not_mutate_input_report():
    report = _bridge("approval_dispatch_bridge_report_valid_pass_manual_only.json")
    before = json.dumps(report, sort_keys=True)
    build_compiler_v2_bridge_publish_readiness_alignment(report)
    build_compiler_v2_bridge_redacted_audit_alignment(report)
    assert json.dumps(report, sort_keys=True) == before


# --- Valid fixtures never imply readiness/approval/dispatch/event creation -----------

def test_valid_fixtures_never_imply_grant():
    for name in (
        "publish_readiness_alignment_valid_pass_manual_only.json",
        "publish_readiness_alignment_valid_review_required.json",
        "redacted_audit_alignment_valid_pass_manual_only.json",
        "redacted_audit_alignment_valid_review_required.json",
    ):
        data = _evidence(name)
        assert data["schema_version"] == EVIDENCE_SCHEMA_VERSION
        for key, val in _iter_bool_flags(data):
            if key in _NEVER_TRUE_FLAGS:
                assert val is not True, f"{name}:{key} must not be true in a valid path"
        # required-true evidence invariants
        for flag in ("bridge_report_bound", "local_only", "evidence_only",
                     "non_executable", "manual_review_required", "redacted_safe"):
            assert data[flag] is True, f"{name}:{flag} must be true"


def test_valid_fixtures_revalidate():
    pass_cases = {
        "publish_readiness_alignment_valid_pass_manual_only.json": (
            validate_compiler_v2_bridge_publish_readiness_alignment, PASS),
        "publish_readiness_alignment_valid_review_required.json": (
            validate_compiler_v2_bridge_publish_readiness_alignment, REVIEW_REQUIRED),
        "redacted_audit_alignment_valid_pass_manual_only.json": (
            validate_compiler_v2_bridge_redacted_audit_alignment, PASS),
        "redacted_audit_alignment_valid_review_required.json": (
            validate_compiler_v2_bridge_redacted_audit_alignment, REVIEW_REQUIRED),
    }
    for name, (validator, expected) in pass_cases.items():
        data = _evidence(name)
        assert validator(data)["validation_state"] == expected, name


# --- Data-driven hostile / degraded harness ------------------------------------------

def test_hostile_cases_fail_closed():
    cases = _evidence("hostile_degraded_cases.json")["cases"]
    assert cases
    for case in cases:
        validator = COMPILER_V2_BRIDGE_PUBLISH_EVIDENCE_VALIDATORS[case["kind"]]
        result = validator(case["packet"])
        assert result["validation_state"] == case["expected_state"], (
            f"{case['case_id']}: expected {case['expected_state']}, "
            f"got {result['validation_state']} ({result['reasons']})"
        )
        assert result["validation_state"] != PASS
