"""Test V6 Real Source Pack Operator Approval Gate Validator."""
from __future__ import annotations

from live_contentops import real_source_pack_operator_approval_gate_v6 as gate_mod
from live_contentops import real_source_pack_operator_approval_template_v6 as template_builder
from live_contentops import real_source_pack_operator_approval_validator_v6 as validator


def test_validator_passes_on_clean_gate_state():
    gate_packet = {
        "approval_gate_status": "OPERATOR_APPROVAL_REQUIRED",
        "runtime_truth": False,
        "operator_approval_created": False,
        "operator_signature_present": False,
        "source_pack_hash_present": False
    }
    template = template_builder.make_operator_approval_template()
    matrix = gate_mod.make_approval_readiness_matrix()

    report, blockers = validator.validate_operator_approval_gate(gate_packet, template, matrix)

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "operator_approval_missing" in blockers
    assert "approval_signature_missing" in blockers
    assert "source_pack_hash_approval_missing" in blockers
    assert "draft_generation_blocked" in blockers
    assert "publication_blocked_until_operator_approval" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_fails_on_active_approval_leak():
    gate_packet = {
        "approval_gate_status": "OPERATOR_APPROVAL_REQUIRED",
        "runtime_truth": False,
        "operator_approval_created": True,  # Leak
        "operator_signature_present": False,
        "source_pack_hash_present": False
    }
    template = template_builder.make_operator_approval_template()
    matrix = gate_mod.make_approval_readiness_matrix()

    report, blockers = validator.validate_operator_approval_gate(gate_packet, template, matrix)

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_approval_creation_detected" in blockers


def test_validator_fails_on_raw_secret_leak():
    gate_packet = {
        "approval_gate_status": "OPERATOR_APPROVAL_REQUIRED",
        "runtime_truth": False,
        "operator_approval_created": False,
        "operator_signature_present": False,
        "source_pack_hash_present": False,
        "notes": "Here is operator_jim_sig leaked"  # Leak keyword
    }
    template = template_builder.make_operator_approval_template()
    matrix = gate_mod.make_approval_readiness_matrix()

    report, blockers = validator.validate_operator_approval_gate(gate_packet, template, matrix)

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.real_source_pack_operator_approval_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs
