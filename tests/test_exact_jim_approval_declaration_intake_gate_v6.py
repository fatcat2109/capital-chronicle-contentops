import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.exact_jim_approval_declaration_intake_gate_v6 import *

SAMPLE_VERIFIER = Path("docs/automation/V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_SCAFFOLD_HEAVY_BATCH_NO_APPROVAL_NO_SEND/sample_exact_operator_approval_signature_verifier_scaffold_bundle.json")


def _verifier_bundle():
    return json.loads(SAMPLE_VERIFIER.read_text(encoding="utf-8"))


def _accepted_declaration():
    verifier = _verifier_bundle()
    template = verifier["future_exact_operator_approval_declaration_template"]
    return {
        "schema_version": SCHEMA_VERSION,
        "jim_approval_declaration_id": "synthetic_test_fixture_only_jim_approval_declaration_001",
        "source_exact_operator_approval_signature_verifier_scaffold_bundle_id": verifier["exact_operator_approval_signature_verifier_scaffold_bundle_id"],
        "source_payload_hash_preview_approval_prep_bundle_id": template["source_payload_hash_preview_approval_prep_bundle_id"],
        "operator_id": "jim",
        "created_at_manual": "synthetic_test_fixture_only_manual_timestamp",
        "approval_mode": APPROVAL_MODE,
        "approval_scope": APPROVAL_SCOPE,
        "exact_approval_phrase_required": EXACT_APPROVAL_PHRASE,
        "exact_approval_phrase_provided": EXACT_APPROVAL_PHRASE,
        "approved_payload_preview_ids": ["synthetic_test_fixture_only_preview_001"],
        "approved_payload_hashes": ["0" * 64],
        "approved_platforms": ["discord"],
        "approval_hash_binding_present": True,
        "payload_hashes_revalidated_now": True,
        "payload_hash_revalidation_report_id": "synthetic_test_fixture_only_revalidation_report_001",
        "destination_binding_present": False,
        "destination_binding_id": None,
        "credential_handle_present": False,
        "credential_handle_id": None,
        "approval_granted_now": True,
        "publication_approved_now": False,
        "outbox_approved_now": False,
        "dispatch_approved_now": False,
        "live_send_approved_now": False,
        "provider_call_requested": False,
        "env_read_requested": False,
        "credential_value_read_requested": False,
        "network_call_requested": False,
        "browser_session_requested": False,
        "executable_request_artifact_requested": False,
        "public_url_requested": False,
        "metrics_requested": False,
        "revocation_supported": True,
        "expires_at": "2099-01-01T00:00:00Z",
        "human_review_required": True,
        "notes": "synthetic_test_fixture_only",
    }


def _bundle(verifier=None, declaration=None):
    return make_exact_jim_approval_declaration_intake_gate_bundle(verifier or _verifier_bundle(), declaration)


def test_default_sample_no_declaration_not_approved():
    b = _bundle()
    assert b.approval_declaration_status == "not_approved_or_rejected"
    assert b.approval_granted_now is False
    assert b.eligible_for_future_outbox_preparation_task is False
    assert b.eligible_for_live_send_now is False
    assert b.publication_ready is False
    assert b.dispatch_allowed is False
    assert b.live_send_allowed is False
    assert b.provider_call_made is False and b.env_read is False and b.credential_value_read is False
    assert b.network_call_made is False and b.browser_session_used is False
    assert b.executable_request_artifact_created is False and b.public_url_created is False and b.metrics_created is False
    assert "approval_declaration_missing" in b.blockers


def test_valid_synthetic_exact_jim_approval_only_future_outbox_preparation():
    b = _bundle(declaration=_accepted_declaration())
    assert b.blockers == []
    assert b.approval_declaration_status == "accepted_for_future_outbox_preparation_only"
    assert b.approval_granted_now is True
    assert b.eligible_for_future_outbox_preparation_task is True
    assert b.approval_valid_for_payload_hashes_only is True
    assert b.eligible_for_live_send_now is False
    assert b.publication_ready is False
    assert b.dispatch_allowed is False
    assert b.live_send_allowed is False
    assert b.provider_call_made is False and b.env_read is False and b.credential_value_read is False
    assert b.network_call_made is False and b.browser_session_used is False
    assert b.executable_request_artifact_created is False and b.public_url_created is False and b.metrics_created is False


def test_exact_phrase_mismatch_and_operator_not_jim_fail_closed():
    d = _accepted_declaration(); d["exact_approval_phrase_provided"] = "NOT_PROVIDED_IN_THIS_INTAKE_SAMPLE"
    assert "declaration_exact_phrase_provided_mismatch" in _bundle(declaration=d).blockers
    d = _accepted_declaration(); d["operator_id"] = "not_jim"
    assert "declaration_operator_id_not_jim" in _bundle(declaration=d).blockers


def test_empty_approved_lists_fail_closed():
    for key in DECLARATION_REQUIRED_NON_EMPTY_LISTS:
        d = _accepted_declaration(); d[key] = []
        assert f"declaration_{key}_empty" in _bundle(declaration=d).blockers


def test_hash_binding_revalidation_and_report_required():
    d = _accepted_declaration(); d["approval_hash_binding_present"] = False
    assert "declaration_approval_hash_binding_present_not_true" in _bundle(declaration=d).blockers
    d = _accepted_declaration(); d["payload_hashes_revalidated_now"] = False
    assert "declaration_payload_hashes_revalidated_now_not_true" in _bundle(declaration=d).blockers
    d = _accepted_declaration(); d["payload_hash_revalidation_report_id"] = ""
    assert "declaration_payload_hash_revalidation_report_id_empty" in _bundle(declaration=d).blockers


def test_destination_and_credential_binding_fail_closed_in_this_task():
    d = _accepted_declaration(); d["destination_binding_present"] = True
    assert "declaration_destination_binding_present_not_false" in _bundle(declaration=d).blockers
    d = _accepted_declaration(); d["destination_binding_id"] = "destination_binding_not_allowed"
    assert "declaration_destination_binding_id_not_null" in _bundle(declaration=d).blockers
    d = _accepted_declaration(); d["credential_handle_present"] = True
    assert "declaration_credential_handle_present_not_false" in _bundle(declaration=d).blockers
    d = _accepted_declaration(); d["credential_handle_id"] = "credential_handle_not_allowed"
    assert "declaration_credential_handle_id_not_null" in _bundle(declaration=d).blockers


def test_publication_outbox_dispatch_live_flags_fail_closed():
    for flag in ("publication_approved_now", "outbox_approved_now", "dispatch_approved_now", "live_send_approved_now"):
        d = _accepted_declaration(); d[flag] = True
        assert f"declaration_{flag}_not_false" in _bundle(declaration=d).blockers


def test_provider_env_credential_network_browser_executable_public_metrics_requested_fail_closed():
    for flag in ("provider_call_requested", "env_read_requested", "credential_value_read_requested", "network_call_requested", "browser_session_requested", "executable_request_artifact_requested", "public_url_requested", "metrics_requested"):
        d = _accepted_declaration(); d[flag] = True
        assert f"declaration_{flag}_not_false" in _bundle(declaration=d).blockers


def test_expires_at_missing_extra_field_and_missing_required_fields_fail_closed():
    d = _accepted_declaration(); d["expires_at"] = ""
    assert "declaration_expires_at_missing" in _bundle(declaration=d).blockers
    d = _accepted_declaration(); d["unexpected"] = "x"
    assert "declaration_extra_fields" in _bundle(declaration=d).blockers
    for field in DECLARATION_FIELDS:
        d = _accepted_declaration(); d.pop(field)
        assert f"missing_declaration_{field}" in _bundle(declaration=d).blockers


def test_forbidden_text_fails_closed_without_echoing_values():
    forbidden = ("endpoint", "webhook", "secret", "channel", "account", "cookie", "session", "browser path", "https://example.invalid/x", "metrics", "trading advice", "financial advice", "signal service", "live-send")
    for term in forbidden:
        d = _accepted_declaration(); d["notes"] = term
        blockers = _bundle(declaration=d).blockers
        assert any(b.startswith("declaration_forbidden_") for b in blockers)
        assert term not in " ".join(blockers)


def test_invalid_upstream_verifier_scaffold_fails_closed():
    upstream = _verifier_bundle(); upstream.pop("task_label")
    assert "upstream_task_label_invalid" in _bundle(upstream, _accepted_declaration()).blockers
    upstream = _verifier_bundle(); upstream["eligible_for_future_exact_operator_approval_task"] = False
    assert "upstream_future_exact_operator_approval_eligibility_not_true" in _bundle(upstream, _accepted_declaration()).blockers
    upstream = _verifier_bundle(); upstream["approval_granted_now"] = True
    assert "upstream_approval_granted_now_not_false" in _bundle(upstream, _accepted_declaration()).blockers


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--exact-operator-approval-signature-verifier-scaffold-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["approval_granted_now"] is False
    assert data["eligible_for_live_send_now"] is False


def test_cli_deterministic_output(tmp_path):
    verifier_path = tmp_path / "verifier.json"
    declaration_path = tmp_path / "declaration.json"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"
    verifier_path.write_text(json.dumps(_verifier_bundle()), encoding="utf-8")
    declaration_path.write_text(json.dumps(_accepted_declaration()), encoding="utf-8")
    args = ["--exact-operator-approval-signature-verifier-scaffold-bundle", str(verifier_path), "--jim-approval-declaration", str(declaration_path)]
    assert main(args + ["--output", str(out1)]) == 0
    assert main(args + ["--output", str(out2)]) == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/exact_jim_approval_declaration_intake_gate_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_runbook_sample_hygiene():
    paths = [
        "docs/runbooks/V6_EXACT_JIM_APPROVAL_DECLARATION_INTAKE_GATE_OPERATOR_RUNBOOK_NO_PROVIDER_NO_LIVE_SEND.md",
        "docs/automation/V6_EXACT_JIM_APPROVAL_DECLARATION_INTAKE_GATE_HEAVY_BATCH_NO_PROVIDER_NO_LIVE_SEND/implementation_report.md",
        "docs/automation/V6_EXACT_JIM_APPROVAL_DECLARATION_INTAKE_GATE_HEAVY_BATCH_NO_PROVIDER_NO_LIVE_SEND/exact_jim_approval_declaration_intake_gate_contract.md",
        "docs/automation/V6_EXACT_JIM_APPROVAL_DECLARATION_INTAKE_GATE_HEAVY_BATCH_NO_PROVIDER_NO_LIVE_SEND/sample_exact_jim_approval_declaration_intake_gate_bundle.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    txt = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "approval intake only" in txt
    assert "no provider" in txt and "no live send" in txt and "no outbox execution" in txt
    assert "no dispatch readiness" in txt
    assert "accepted approval is only for future outbox preparation" in txt