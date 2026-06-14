"""Tests for the operator evidence summary roll-up layer (SCD, 0174BT).

Local-only, deterministic. Verifies that the NEW parallel operator-evidence-summary
module rolls the ACCEPTED chain (compiler v2 -> approval/dispatch bridge report
(0174BP) -> publish-readiness alignment + redacted-audit alignment (0174BR)) into
ONE compact operator-facing summary as *evidence only*, fails closed
(BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS), and never grants readiness, approval,
dispatch, posting, platform/provider API, credential access, scheduler, public
status, audit-event creation, or audit allow-list modification.
"""
import json
import os

from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
)
from live_contentops.scd_dispatch_gate import canonical_json_sha256
from live_contentops.scd_operator_evidence_summary import (
    SUMMARY_SCHEMA_VERSION,
    OPERATOR_SUMMARY_MODE,
    ALLOWED_OPERATOR_ACTION,
    OPERATOR_EVIDENCE_SUMMARY_VALIDATORS,
    derive_operator_evidence_summary_id,
    build_operator_evidence_summary,
    validate_operator_evidence_summary,
)

SUMMARY_FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "scd_operator_evidence_summary",
)
BRIDGE_FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "scd_compiler_v2_dispatch_bridge",
)
EVIDENCE_FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "scd_compiler_v2_bridge_publish_evidence",
)

# Flags that must never be asserted true on any valid summary object.
_NEVER_TRUE_FLAGS = (
    "readiness_granted",
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
)

# Flags that must be asserted true on any valid summary object.
_REQUIRED_TRUE_FLAGS = (
    "evidence_only",
    "non_executable",
    "manual_review_required",
    "local_only",
    "operator_visible",
    "ui_ready_packet",
    "bridge_report_bound",
    "bridge_hash_matches",
    "lineage_ids_consistent",
)


def _load(directory, name):
    with open(os.path.join(directory, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _summary(name):
    return _load(SUMMARY_FIXTURE_DIR, name)


def _bridge(name):
    return _load(BRIDGE_FIXTURE_DIR, name)


def _evidence(name):
    return _load(EVIDENCE_FIXTURE_DIR, name)


def _iter_bool_flags(obj):
    for key, val in obj.items():
        if isinstance(val, bool):
            yield key, val


# --- Builder binds lineage, rolls up, and grants nothing -----------------------------

def test_build_pass_path_binds_chain_and_grants_nothing():
    bridge = _bridge("approval_dispatch_bridge_report_valid_pass_manual_only.json")
    rdy = _evidence("publish_readiness_alignment_valid_pass_manual_only.json")
    aud = _evidence("redacted_audit_alignment_valid_pass_manual_only.json")

    packet = build_operator_evidence_summary(bridge, rdy, aud)
    assert validate_operator_evidence_summary(packet)["validation_state"] == PASS

    # lineage bound from the authoritative bridge report
    assert packet["bridge_report_id"] == bridge["bridge_report_id"]
    assert packet["compiler_output_id"] == bridge["compiler_output_id"]
    assert packet["compile_report_id"] == bridge["compile_report_id"]
    assert packet["payload_hash_manifest_id"] == bridge["payload_hash_manifest_id"]
    assert packet["bridge_report_hash"] == canonical_json_sha256(bridge)
    assert packet["readiness_alignment_id"] == rdy["readiness_alignment_id"]
    assert packet["audit_alignment_id"] == aud["audit_alignment_id"]
    assert packet["operator_evidence_summary_id"] == derive_operator_evidence_summary_id(
        bridge["bridge_report_id"])

    # rollup + counts
    assert packet["rollup_state"] == PASS
    assert packet["blocker_count"] == 0
    assert packet["review_required_count"] == 0
    assert packet["unknown_count"] == 0
    assert packet["operator_summary_mode"] == OPERATOR_SUMMARY_MODE
    assert packet["allowed_operator_action"] == ALLOWED_OPERATOR_ACTION

    # PASS but still grants nothing
    for flag in _NEVER_TRUE_FLAGS:
        assert packet.get(flag) is not True
    for flag in _REQUIRED_TRUE_FLAGS:
        assert packet[flag] is True


def test_build_review_required_path_propagates():
    bridge = _bridge("approval_dispatch_bridge_report_valid_review_required.json")
    rdy = _evidence("publish_readiness_alignment_valid_review_required.json")
    aud = _evidence("redacted_audit_alignment_valid_review_required.json")

    packet = build_operator_evidence_summary(bridge, rdy, aud)
    assert validate_operator_evidence_summary(packet)["validation_state"] == REVIEW_REQUIRED
    assert packet["rollup_state"] == REVIEW_REQUIRED
    assert packet["review_required_count"] == 3
    for flag in _NEVER_TRUE_FLAGS:
        assert packet.get(flag) is not True


def test_builder_does_not_mutate_inputs():
    bridge = _bridge("approval_dispatch_bridge_report_valid_pass_manual_only.json")
    rdy = _evidence("publish_readiness_alignment_valid_pass_manual_only.json")
    aud = _evidence("redacted_audit_alignment_valid_pass_manual_only.json")
    before = (
        json.dumps(bridge, sort_keys=True),
        json.dumps(rdy, sort_keys=True),
        json.dumps(aud, sort_keys=True),
    )
    build_operator_evidence_summary(bridge, rdy, aud)
    after = (
        json.dumps(bridge, sort_keys=True),
        json.dumps(rdy, sort_keys=True),
        json.dumps(aud, sort_keys=True),
    )
    assert before == after


def test_bridge_hash_is_canonical_over_supplied_report():
    bridge = _bridge("approval_dispatch_bridge_report_valid_pass_manual_only.json")
    rdy = _evidence("publish_readiness_alignment_valid_pass_manual_only.json")
    aud = _evidence("redacted_audit_alignment_valid_pass_manual_only.json")
    packet = build_operator_evidence_summary(bridge, rdy, aud)
    # key-order independence of the bound canonical hash
    reordered = {k: bridge[k] for k in reversed(list(bridge.keys()))}
    packet2 = build_operator_evidence_summary(reordered, rdy, aud)
    assert packet["bridge_report_hash"] == packet2["bridge_report_hash"]


# --- Valid fixtures never imply any grant --------------------------------------------

def test_valid_fixtures_revalidate_and_never_grant():
    cases = {
        "operator_evidence_summary_valid_pass_manual_only.json": PASS,
        "operator_evidence_summary_valid_review_required.json": REVIEW_REQUIRED,
    }
    for name, expected in cases.items():
        data = _summary(name)
        assert data["schema_version"] == SUMMARY_SCHEMA_VERSION
        assert validate_operator_evidence_summary(data)["validation_state"] == expected, name
        for key, val in _iter_bool_flags(data):
            if key in _NEVER_TRUE_FLAGS:
                assert val is not True, f"{name}:{key} must not be true in a valid path"
        for flag in _REQUIRED_TRUE_FLAGS:
            assert data[flag] is True, f"{name}:{flag} must be true"


# --- Data-driven hostile / degraded harness ------------------------------------------

def test_hostile_cases_fail_closed():
    cases = _summary("hostile_degraded_cases.json")["cases"]
    assert cases
    for case in cases:
        validator = OPERATOR_EVIDENCE_SUMMARY_VALIDATORS[case["kind"]]
        result = validator(case["packet"])
        assert result["validation_state"] == case["expected_state"], (
            f"{case['case_id']}: expected {case['expected_state']}, "
            f"got {result['validation_state']} ({result['reasons']})"
        )
        assert result["validation_state"] != PASS, case["case_id"]


def test_hostile_matrix_covers_required_dimensions():
    case_ids = {c["case_id"] for c in _summary("hostile_degraded_cases.json")["cases"]}
    # spot-check that the key adversarial dimensions are present
    for required in (
        "public_ready_true_blocks",
        "live_ready_true_blocks",
        "dispatch_ready_true_blocks",
        "executable_dispatch_true_blocks",
        "platform_api_allowed_now_true_blocks",
        "credential_read_allowed_now_true_blocks",
        "credentials_requested_now_true_blocks",
        "scheduler_enabled_now_true_blocks",
        "posting_enabled_now_true_blocks",
        "autonomous_replies_enabled_now_true_blocks",
        "dms_enabled_now_true_blocks",
        "scraping_enabled_now_true_blocks",
        "audit_event_created_true_blocks",
        "audit_allowlist_modified_true_blocks",
        "readiness_granted_true_blocks",
        "evidence_only_false_blocks",
        "non_executable_false_blocks",
        "manual_review_required_false_blocks",
        "bridge_report_hash_mismatch_blocks",
        "compiler_output_id_mismatch_blocks",
        "compile_report_id_mismatch_blocks",
        "payload_hash_manifest_id_mismatch_blocks",
        "readiness_alignment_id_missing_unknown",
        "audit_alignment_id_missing_unknown",
        "declared_pass_over_review_blocks",
        "inconsistent_blocker_count_blocks",
        "bound_bridge_blocked_blocks",
        "bound_bridge_unknown_unknown",
        "bound_bridge_review_review",
        "bound_readiness_blocked_blocks",
        "bound_audit_blocked_blocks",
        "secret_like_string_blocks",
    ):
        assert required in case_ids, f"missing hostile dimension: {required}"
