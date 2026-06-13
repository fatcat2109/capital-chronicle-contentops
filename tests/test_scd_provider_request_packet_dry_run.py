import pytest
import json
import os
from live_contentops.scd_provider_request_packet_dry_run import (
    validate_provider_request_packet_dry_run,
    validate_provider_request_payload_redaction,
    validate_provider_request_packet_budget_binding,
    validate_provider_request_packet_audit_manifest,
    build_provider_request_packet_dry_run
)

def _load(f):
    with open(os.path.join("fixtures", "scd_provider_request_packet_dry_run", f)) as file:
        return json.load(file)

def test_pass_dry_run():
    assert validate_provider_request_packet_dry_run(_load("pass_dry_run.json"))["validation_state"] == "PASS"

def test_pass_payload_redaction():
    assert validate_provider_request_payload_redaction(_load("pass_payload_redaction.json"))["validation_state"] == "PASS"

def test_pass_budget_binding():
    assert validate_provider_request_packet_budget_binding(_load("pass_budget_binding.json"))["validation_state"] == "PASS"

def test_pass_audit_manifest():
    assert validate_provider_request_packet_audit_manifest(_load("pass_audit_manifest.json"))["validation_state"] == "PASS"

def test_unknown_missing_prompt_pack_ref():
    assert validate_provider_request_packet_dry_run(_load("unknown_missing_prompt_pack_ref.json"))["validation_state"] == "UNKNOWN"

def test_unknown_missing_canonical_draft_ref():
    assert validate_provider_request_packet_dry_run(_load("unknown_missing_canonical_draft_ref.json"))["validation_state"] == "UNKNOWN"

def test_unknown_missing_credential_envelope_ref():
    assert validate_provider_request_packet_dry_run(_load("unknown_missing_credential_envelope_ref.json"))["validation_state"] == "UNKNOWN"

def test_unknown_missing_audit_manifest_ref():
    assert validate_provider_request_packet_dry_run(_load("unknown_missing_audit_manifest_ref.json"))["validation_state"] == "UNKNOWN"

def test_blocked_provider_api_gate_readiness_state_non_pass():
    assert validate_provider_request_packet_dry_run(_load("blocked_provider_api_gate_readiness_state_non_pass.json"))["validation_state"] == "BLOCKED"

def test_blocked_request_packet_mode_executable():
    assert validate_provider_request_packet_dry_run(_load("blocked_request_packet_mode_executable.json"))["validation_state"] == "BLOCKED"

def test_blocked_executable_true():
    assert validate_provider_request_packet_dry_run(_load("blocked_executable_true.json"))["validation_state"] == "BLOCKED"

def test_blocked_real_url_present():
    assert validate_provider_request_packet_dry_run(_load("blocked_real_url_present.json"))["validation_state"] == "BLOCKED"

def test_blocked_authorization_header():
    assert validate_provider_request_packet_dry_run(_load("blocked_authorization_header.json"))["validation_state"] == "BLOCKED"

def test_blocked_bearer_token():
    assert validate_provider_request_packet_dry_run(_load("blocked_bearer_token.json"))["validation_state"] == "BLOCKED"

def test_blocked_raw_api_key():
    assert validate_provider_request_packet_dry_run(_load("blocked_raw_api_key.json"))["validation_state"] == "BLOCKED"

def test_blocked_wording():
    assert validate_provider_request_packet_dry_run(_load("blocked_wording.json"))["validation_state"] == "BLOCKED"

def test_blocked_network_allowed():
    assert validate_provider_request_packet_dry_run(_load("blocked_network_allowed.json"))["validation_state"] == "BLOCKED"

def test_blocked_provider_client_constructed():
    assert validate_provider_request_packet_dry_run(_load("blocked_provider_client_constructed.json"))["validation_state"] == "BLOCKED"

def test_blocked_env_read_allowed():
    assert validate_provider_request_packet_dry_run(_load("blocked_env_read_allowed.json"))["validation_state"] == "BLOCKED"

def test_blocked_credential_lookup_allowed():
    assert validate_provider_request_packet_dry_run(_load("blocked_credential_lookup_allowed.json"))["validation_state"] == "BLOCKED"

def test_blocked_api_key_present():
    assert validate_provider_request_packet_dry_run(_load("blocked_api_key_present.json"))["validation_state"] == "BLOCKED"

def test_blocked_credential_value_present():
    assert validate_provider_request_packet_dry_run(_load("blocked_credential_value_present.json"))["validation_state"] == "BLOCKED"

def test_blocked_redaction_proof_non_pass():
    assert validate_provider_request_packet_dry_run(_load("blocked_redaction_proof_non_pass.json"))["validation_state"] == "BLOCKED"

def test_blocked_budget_binding_non_pass():
    assert validate_provider_request_packet_dry_run(_load("blocked_budget_binding_non_pass.json"))["validation_state"] == "BLOCKED"

def test_static_scan_no_live_imports():
    with open("live_contentops/scd_provider_request_packet_dry_run.py") as f:
        code = f.read()
    bad_imports = ["import httpx", "import requests", "import urllib", "import socket", "import openai", "import anthropic", "os.environ", "os.getenv", "webbrowser", "subprocess"]
    for bad in bad_imports:
        assert bad not in code

def test_helper_pass_all_evidence_explicit():
    packet = build_provider_request_packet_dry_run(
        _load("pass_api_gate_report.json"),
        _load("pass_credential_envelope_evidence.json"),
        _load("pass_request_budget_evidence.json"),
        _load("pass_provider_allowlist_evidence.json"),
        _load("pass_redaction_proof_evidence.json"),
        _load("pass_budget_binding_evidence.json"),
        _load("pass_provider_symbol_evidence.json"),
        _load("pass_endpoint_family_evidence.json"),
        "r1", "r2", "r3", "r4", "r5"
    )
    assert packet["validation_state"] == "PASS"

def test_helper_missing_credential_envelope_evidence_unknown():
    packet = build_provider_request_packet_dry_run(
        _load("pass_api_gate_report.json"),
        None,
        _load("pass_request_budget_evidence.json"),
        _load("pass_provider_allowlist_evidence.json"),
        _load("pass_redaction_proof_evidence.json"),
        _load("pass_budget_binding_evidence.json"),
        _load("pass_provider_symbol_evidence.json"),
        _load("pass_endpoint_family_evidence.json"),
        "r1", "r2", "r3", "r4", "r5"
    )
    assert packet["validation_state"] == "UNKNOWN"

def test_helper_missing_redaction_proof_evidence_unknown():
    packet = build_provider_request_packet_dry_run(
        _load("pass_api_gate_report.json"),
        _load("pass_credential_envelope_evidence.json"),
        _load("pass_request_budget_evidence.json"),
        _load("pass_provider_allowlist_evidence.json"),
        None,
        _load("pass_budget_binding_evidence.json"),
        _load("pass_provider_symbol_evidence.json"),
        _load("pass_endpoint_family_evidence.json"),
        "r1", "r2", "r3", "r4", "r5"
    )
    assert packet["validation_state"] == "UNKNOWN"

def test_helper_budget_binding_blocked():
    packet = build_provider_request_packet_dry_run(
        _load("pass_api_gate_report.json"),
        _load("pass_credential_envelope_evidence.json"),
        _load("pass_request_budget_evidence.json"),
        _load("pass_provider_allowlist_evidence.json"),
        _load("pass_redaction_proof_evidence.json"),
        _load("blocked_budget_binding.json"),
        _load("pass_provider_symbol_evidence.json"),
        _load("pass_endpoint_family_evidence.json"),
        "r1", "r2", "r3", "r4", "r5"
    )
    assert packet["validation_state"] == "BLOCKED"

def test_helper_provider_allowlist_review_required():
    packet = build_provider_request_packet_dry_run(
        _load("pass_api_gate_report.json"),
        _load("pass_credential_envelope_evidence.json"),
        _load("pass_request_budget_evidence.json"),
        _load("review_provider_allowlist_evidence.json"),
        _load("pass_redaction_proof_evidence.json"),
        _load("pass_budget_binding_evidence.json"),
        _load("pass_provider_symbol_evidence.json"),
        _load("pass_endpoint_family_evidence.json"),
        "r1", "r2", "r3", "r4", "r5"
    )
    assert packet["validation_state"] == "REVIEW_REQUIRED"

def test_helper_missing_provider_symbol_evidence_not_fabricated():
    packet = build_provider_request_packet_dry_run(
        _load("pass_api_gate_report.json"),
        _load("pass_credential_envelope_evidence.json"),
        _load("pass_request_budget_evidence.json"),
        _load("pass_provider_allowlist_evidence.json"),
        _load("pass_redaction_proof_evidence.json"),
        _load("pass_budget_binding_evidence.json"),
        None,
        _load("pass_endpoint_family_evidence.json"),
        "r1", "r2", "r3", "r4", "r5"
    )
    assert packet["symbolic_provider_name"] == "UNKNOWN_PROVIDER"

def test_helper_missing_endpoint_family_evidence_not_fabricated():
    packet = build_provider_request_packet_dry_run(
        _load("pass_api_gate_report.json"),
        _load("pass_credential_envelope_evidence.json"),
        _load("pass_request_budget_evidence.json"),
        _load("pass_provider_allowlist_evidence.json"),
        _load("pass_redaction_proof_evidence.json"),
        _load("pass_budget_binding_evidence.json"),
        _load("pass_provider_symbol_evidence.json"),
        None,
        "r1", "r2", "r3", "r4", "r5"
    )
    assert packet["symbolic_endpoint_family"] == "UNKNOWN_ENDPOINT"

def test_helper_symbolic_provider_url_blocked():
    packet = build_provider_request_packet_dry_run(
        _load("pass_api_gate_report.json"),
        _load("pass_credential_envelope_evidence.json"),
        _load("pass_request_budget_evidence.json"),
        _load("pass_provider_allowlist_evidence.json"),
        _load("pass_redaction_proof_evidence.json"),
        _load("pass_budget_binding_evidence.json"),
        _load("blocked_symbolic_provider_url.json"),
        _load("pass_endpoint_family_evidence.json"),
        "r1", "r2", "r3", "r4", "r5"
    )
    assert packet["validation_state"] == "BLOCKED"

def test_audit_manifest_missing_refs_unknown():
    assert validate_provider_request_packet_audit_manifest(_load("unknown_missing_refs_audit_manifest.json"))["validation_state"] == "UNKNOWN"

def test_audit_manifest_missing_refs_claim_pass_blocked():
    assert validate_provider_request_packet_audit_manifest(_load("blocked_missing_refs_claim_pass_audit_manifest.json"))["validation_state"] == "BLOCKED"

