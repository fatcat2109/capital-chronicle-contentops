import pytest
import json
from live_contentops.scd_domain_model import PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN
from live_contentops.scd_provider_response_ledger_dry_run import (
    validate_provider_response_receipt_dry_run,
    validate_provider_response_payload_redaction,
    validate_provider_response_ledger_entry,
    validate_provider_response_audit_manifest,
    build_provider_response_ledger_entry,
    build_provider_response_audit_manifest
)

def _load(p):
    with open(f"fixtures/scd_provider_response_ledger_dry_run/{p}", "r") as f:
        return json.load(f)

def test_receipt_pass():
    res = validate_provider_response_receipt_dry_run(_load("pass_response_receipt.json"))
    assert res["validation_state"] == PASS

def test_receipt_missing_request_ref():
    d = _load("pass_response_receipt.json")
    del d["request_packet_ref"]
    res = validate_provider_response_receipt_dry_run(d)
    assert res["validation_state"] != PASS

def test_receipt_missing_response_ref():
    d = _load("pass_response_receipt.json")
    del d["response_artifact_ref"]
    res = validate_provider_response_receipt_dry_run(d)
    assert res["validation_state"] != PASS

def test_receipt_url_blocks():
    res = validate_provider_response_receipt_dry_run(_load("blocked_response_receipt_url.json"))
    assert res["validation_state"] == BLOCKED

def test_receipt_authorization_blocks():
    res = validate_provider_response_receipt_dry_run(_load("blocked_response_receipt_authorization_header.json"))
    assert res["validation_state"] == BLOCKED

def test_receipt_network_flag_blocks():
    res = validate_provider_response_receipt_dry_run(_load("blocked_response_receipt_true_network_flag.json"))
    assert res["validation_state"] == BLOCKED

def test_receipt_authority_blocks():
    d = _load("pass_response_receipt.json")
    d["response_content_authority_state"] = "MARKET_TRUTH"
    res = validate_provider_response_receipt_dry_run(d)
    assert res["validation_state"] == BLOCKED

def test_receipt_generated_content_public_ready_blocks():
    d = _load("pass_response_receipt.json")
    d["generated_content_public_ready"] = True
    res = validate_provider_response_receipt_dry_run(d)
    assert res["validation_state"] == BLOCKED

def test_receipt_unsafe_words_block():
    res = validate_provider_response_receipt_dry_run(_load("blocked_response_receipt_live_call_wording.json"))
    assert res["validation_state"] == BLOCKED

def test_redaction_pass():
    res = validate_provider_response_payload_redaction(_load("pass_response_redaction.json"))
    assert res["validation_state"] == PASS

def test_redaction_redistribution_blocks():
    d = _load("pass_response_redaction.json")
    d["raw_response_redistribution_allowed"] = True
    res = validate_provider_response_payload_redaction(d)
    assert res["validation_state"] == BLOCKED

def test_redaction_raw_payload_present_cannot_pass():
    d = _load("review_response_redaction_raw_payload_present.json")
    d["validation_state"] = PASS
    res = validate_provider_response_payload_redaction(d)
    assert res["validation_state"] != PASS

def test_redaction_missing_ref_cannot_pass():
    d = _load("pass_response_redaction.json")
    del d["response_redaction_ref"]
    res = validate_provider_response_payload_redaction(d)
    assert res["validation_state"] != PASS

def test_redaction_missing_redacted_artifact_cannot_pass():
    res = validate_provider_response_payload_redaction(_load("blocked_response_redaction_missing_redacted_artifact_claimed_pass.json"))
    assert res["validation_state"] != PASS

def test_redaction_secret_blocks():
    res = validate_provider_response_payload_redaction(_load("blocked_response_redaction_secret_detected.json"))
    assert res["validation_state"] == BLOCKED

def test_redaction_public_ready_blocks():
    d = _load("pass_response_redaction.json")
    d["public_ready"] = True
    res = validate_provider_response_payload_redaction(d)
    assert res["validation_state"] == BLOCKED

def test_audit_manifest_pass():
    res = validate_provider_response_audit_manifest(_load("pass_response_audit_manifest.json"))
    assert res["validation_state"] == PASS

def test_audit_manifest_missing_refs_unknown():
    d = _load("pass_response_audit_manifest.json")
    d["request_packet_ref"] = ""
    d["validation_state"] = UNKNOWN
    res = validate_provider_response_audit_manifest(d)
    assert res["validation_state"] == UNKNOWN

def test_audit_manifest_missing_refs_claimed_pass_blocked():
    res = validate_provider_response_audit_manifest(_load("blocked_response_audit_manifest_missing_refs_claimed_pass.json"))
    assert res["validation_state"] == BLOCKED

def test_audit_manifest_missing_specific_ref_cannot_pass():
    for r in ["request_packet_ref", "response_artifact_ref", "response_redaction_ref", "response_ledger_ref"]:
        d = _load("pass_response_audit_manifest.json")
        del d[r]
        res = validate_provider_response_audit_manifest(d)
        assert res["validation_state"] != PASS

def test_ledger_entry_pass():
    res = validate_provider_response_ledger_entry(_load("pass_response_ledger_entry.json"))
    assert res["validation_state"] == PASS

def test_ledger_entry_upstream_blocked_rolls_up():
    d = _load("pass_response_ledger_entry.json")
    d["provider_request_packet_state"] = BLOCKED
    res = validate_provider_response_ledger_entry(d)
    assert res["validation_state"] == BLOCKED

def test_ledger_entry_upstream_unknown_rolls_up():
    d = _load("pass_response_ledger_entry.json")
    d["provider_request_packet_state"] = UNKNOWN
    d["validation_state"] = UNKNOWN
    res = validate_provider_response_ledger_entry(d)
    assert res["validation_state"] == UNKNOWN

def test_ledger_entry_receipt_review_rolls_up():
    d = _load("pass_response_ledger_entry.json")
    d["response_receipt_state"] = REVIEW_REQUIRED
    d["validation_state"] = REVIEW_REQUIRED
    res = validate_provider_response_ledger_entry(d)
    assert res["validation_state"] == REVIEW_REQUIRED

def test_ledger_entry_redaction_blocked_rolls_up():
    d = _load("pass_response_ledger_entry.json")
    d["response_redaction_state"] = BLOCKED
    res = validate_provider_response_ledger_entry(d)
    assert res["validation_state"] == BLOCKED

def test_ledger_entry_audit_manifest_unknown_rolls_up():
    d = _load("pass_response_ledger_entry.json")
    d["response_audit_manifest_state"] = UNKNOWN
    d["validation_state"] = UNKNOWN
    res = validate_provider_response_ledger_entry(d)
    assert res["validation_state"] == UNKNOWN

def test_ledger_entry_missing_refs_cannot_pass():
    res = validate_provider_response_ledger_entry(_load("unknown_response_ledger_entry_missing_request_ref.json"))
    assert res["validation_state"] != PASS

def test_ledger_entry_claimed_pass_with_unknown_is_blocked():
    res = validate_provider_response_ledger_entry(_load("blocked_response_ledger_entry_claimed_pass_with_unknown_upstream.json"))
    assert res["validation_state"] == BLOCKED

def test_ledger_entry_unknown_provider_cannot_pass():
    res = validate_provider_response_ledger_entry(_load("blocked_response_ledger_entry_unknown_provider.json"))
    assert res["validation_state"] != PASS

def test_ledger_entry_unknown_endpoint_cannot_pass():
    res = validate_provider_response_ledger_entry(_load("blocked_response_ledger_entry_unknown_endpoint.json"))
    assert res["validation_state"] != PASS

def test_ledger_entry_readiness_true_blocks():
    res = validate_provider_response_ledger_entry(_load("blocked_response_ledger_entry_public_ready_true.json"))
    assert res["validation_state"] == BLOCKED

def test_ledger_entry_false_flags_block():
    for f in ["executable", "network_allowed", "provider_client_constructed", "env_read_allowed", "credential_lookup_allowed"]:
        d = _load("pass_response_ledger_entry.json")
        d[f] = True
        res = validate_provider_response_ledger_entry(d)
        assert res["validation_state"] == BLOCKED

def test_ledger_entry_raw_strings_block():
    d = _load("pass_response_ledger_entry.json")
    d["reasons"] = ["http://example.com"]
    res = validate_provider_response_ledger_entry(d)
    assert res["validation_state"] == BLOCKED

def test_ledger_entry_authority_blocks():
    d = _load("pass_response_ledger_entry.json")
    d["response_content_authority_state"] = "MARKET_TRUTH"
    res = validate_provider_response_ledger_entry(d)
    assert res["validation_state"] == BLOCKED

def test_builder_all_pass():
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "E", "batch_id": "b1"}
    rec = {"validation_state": PASS}
    red = {"validation_state": PASS}
    aud = {"validation_state": PASS}
    res = build_provider_response_ledger_entry(
        req, rec, red, aud, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["validation_state"] == PASS

def test_builder_missing_request_packet_unknown():
    rec = {"validation_state": PASS}
    res = build_provider_response_ledger_entry(
        None, rec, rec, rec, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["validation_state"] != PASS

def test_builder_missing_receipt_unknown():
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "E", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, None, req, req, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["validation_state"] != PASS

def test_builder_missing_redaction_unknown():
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "E", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, req, None, req, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["validation_state"] != PASS

def test_builder_missing_audit_unknown():
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "E", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, req, req, None, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["validation_state"] != PASS

def test_builder_missing_request_packet_ref_unknown():
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "E", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, req, req, req, "", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["validation_state"] == UNKNOWN
    valid = validate_provider_response_ledger_entry(res)
    assert valid["validation_state"] == UNKNOWN

@pytest.mark.parametrize("missing_val", ["", None])
@pytest.mark.parametrize("missing_ref", [
    "prompt_pack_ref",
    "canonical_draft_ref",
    "budget_ref",
    "credential_envelope_ref",
    "request_audit_manifest_ref",
    "response_artifact_ref",
    "response_redaction_ref",
    "response_audit_manifest_ref"
])
def test_builder_missing_ref_unknown(missing_ref, missing_val):
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "E", "batch_id": "b1"}
    kwargs = {
        "request_packet": req,
        "response_receipt": req,
        "response_redaction": req,
        "response_audit_manifest": req,
        "request_packet_ref": "r_req",
        "prompt_pack_ref": "r_pro",
        "canonical_draft_ref": "r_can",
        "budget_ref": "r_bud",
        "credential_envelope_ref": "r_cred",
        "request_audit_manifest_ref": "r_raud",
        "response_artifact_ref": "r_art",
        "response_redaction_ref": "r_rred",
        "response_audit_manifest_ref": "r_raudm"
    }
    kwargs[missing_ref] = missing_val
    res = build_provider_response_ledger_entry(**kwargs)
    assert res["validation_state"] == UNKNOWN
    assert res[missing_ref] == ""
    assert any(missing_ref in r for r in res["reasons"])
    valid = validate_provider_response_ledger_entry(res)
    assert valid["validation_state"] == UNKNOWN

def test_builder_inherits_symbolic_provider():
    req = {"validation_state": PASS, "symbolic_provider_name": "MY_PROV", "symbolic_endpoint_family": "MY_END", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, req, req, req, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["symbolic_provider_name"] == "MY_PROV"
    assert res["symbolic_endpoint_family"] == "MY_END"

def test_builder_unknown_provider_cannot_pass():
    req = {"validation_state": PASS, "symbolic_provider_name": "UNKNOWN_PROVIDER", "symbolic_endpoint_family": "MY_END", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, req, req, req, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["validation_state"] != PASS

def test_builder_unknown_endpoint_cannot_pass():
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "UNKNOWN_ENDPOINT", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, req, req, req, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["validation_state"] != PASS

def test_builder_validates_through_validator():
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "E", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, req, req, req, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    valid = validate_provider_response_ledger_entry(res)
    assert valid["validation_state"] == PASS

def test_builder_preserves_safety_flags_false():
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "E", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, req, req, req, "r_req", "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["executable"] is False
    assert res["network_allowed"] is False

def test_builder_itemizes_reasons():
    req = {"validation_state": PASS, "symbolic_provider_name": "P", "symbolic_endpoint_family": "E", "batch_id": "b1"}
    res = build_provider_response_ledger_entry(
        req, req, req, req, None, "r_pro", "r_can", "r_bud", "r_cred", "r_raud", "r_art", "r_rred", "r_raudm"
    )
    assert res["validation_state"] == UNKNOWN
    assert any("request_packet_ref" in r for r in res["reasons"])
    valid = validate_provider_response_ledger_entry(res)
    assert valid["validation_state"] == UNKNOWN

def test_build_response_audit_manifest_pass():
    res = build_provider_response_audit_manifest(
        "b1", ["ref1"], "req_ref", "art_ref", "red_ref", "led_ref"
    )
    assert res["validation_state"] == PASS
    valid = validate_provider_response_audit_manifest(res)
    assert valid["validation_state"] == PASS

def test_build_response_audit_manifest_missing_upstream_refs_unknown():
    res1 = build_provider_response_audit_manifest(
        "b1", None, "req_ref", "art_ref", "red_ref", "led_ref"
    )
    assert res1["validation_state"] == UNKNOWN
    assert res1["upstream_lineage_refs"] == []
    assert any("upstream_lineage_refs missing" in r for r in res1["reasons"])
    
    res2 = build_provider_response_audit_manifest(
        "b1", [], "req_ref", "art_ref", "red_ref", "led_ref"
    )
    assert res2["validation_state"] == UNKNOWN
    assert res2["upstream_lineage_refs"] == []
    
    valid1 = validate_provider_response_audit_manifest(res1)
    assert valid1["validation_state"] == UNKNOWN

@pytest.mark.parametrize("missing_val", ["", None])
@pytest.mark.parametrize("missing_ref", [
    "request_packet_ref",
    "response_artifact_ref",
    "response_redaction_ref",
    "response_ledger_ref"
])
def test_build_response_audit_manifest_missing_ref_unknown(missing_ref, missing_val):
    kwargs = {
        "batch_id": "b1",
        "upstream_lineage_refs": ["u1"],
        "request_packet_ref": "r_req",
        "response_artifact_ref": "r_art",
        "response_redaction_ref": "r_red",
        "response_ledger_ref": "r_led"
    }
    kwargs[missing_ref] = missing_val
    res = build_provider_response_audit_manifest(**kwargs)
    assert res["validation_state"] == UNKNOWN
    assert res[missing_ref] == ""
    assert any(missing_ref in r for r in res["reasons"])
    valid = validate_provider_response_audit_manifest(res)
    assert valid["validation_state"] == UNKNOWN

@pytest.mark.parametrize("missing_val", ["", None])
def test_build_response_audit_manifest_missing_batch_id_unknown_or_not_pass(missing_val):
    res = build_provider_response_audit_manifest(
        missing_val, ["ref1"], "req_ref", "art_ref", "red_ref", "led_ref"
    )
    assert res["batch_id"] == "unknown"
    assert res["validation_state"] != PASS
    assert any("batch_id missing" in r for r in res["reasons"])
    valid = validate_provider_response_audit_manifest(res)
    assert valid["validation_state"] != BLOCKED or "schema" not in str(valid["reasons"])

@pytest.mark.parametrize("hostile_str", [
    "http://example.com",
    "https://example.com",
    "authorization",
    "bearer abc",
    "sk-test",
    "token=abc",
    "webhook",
    "dispatch",
    "publish",
    "live call",
    "call provider now"
])
@pytest.mark.parametrize("field_to_poison", [
    "request_packet_ref",
    "response_artifact_ref",
    "response_redaction_ref",
    "response_ledger_ref",
    "upstream_lineage_refs"
])
def test_build_response_audit_manifest_hostile_strings_block(hostile_str, field_to_poison):
    kwargs = {
        "batch_id": "b1",
        "upstream_lineage_refs": ["u1"],
        "request_packet_ref": "r_req",
        "response_artifact_ref": "r_art",
        "response_redaction_ref": "r_red",
        "response_ledger_ref": "r_led"
    }
    if field_to_poison == "upstream_lineage_refs":
        kwargs[field_to_poison] = [hostile_str]
    else:
        kwargs[field_to_poison] = hostile_str
        
    res = build_provider_response_audit_manifest(**kwargs)
    assert res["validation_state"] == BLOCKED
    valid = validate_provider_response_audit_manifest(res)
    assert valid["validation_state"] == BLOCKED

def test_build_response_audit_manifest_no_schema_mismatch_for_none_inputs():
    res = build_provider_response_audit_manifest(None, None, None, None, None, None)
    assert isinstance(res["request_packet_ref"], str)
    assert isinstance(res["upstream_lineage_refs"], list)
    valid = validate_provider_response_audit_manifest(res)
    assert valid["validation_state"] == UNKNOWN
    assert not any("schema:" in r for r in valid["reasons"])

def test_static_source_safety():
    with open("live_contentops/scd_provider_response_ledger_dry_run.py", "r") as f:
        src = f.read()
    forbidden = ["requests", "httpx", "urllib", "socket", "subprocess", "webbrowser", "openai", "anthropic", "os.environ", "os.getenv"]
    for word in forbidden:
        assert word not in src, f"Forbidden word found: {word}"
