import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.exact_operator_approval_signature_verifier_scaffold_v6 import *
import live_contentops.exact_operator_approval_signature_verifier_scaffold_v6 as verifier

SAMPLE_LEDGER = Path("docs/automation/V6_OPERATOR_APPROVAL_LEDGER_GATE_SCAFFOLD_FROM_PAYLOAD_HASH_PREP_HEAVY_BATCH_NO_APPROVAL_NO_SEND/sample_operator_approval_ledger_gate_scaffold_bundle.json")


def _ledger_bundle():
    return json.loads(SAMPLE_LEDGER.read_text(encoding="utf-8"))


def _bundle(source=None):
    return make_exact_operator_approval_signature_verifier_scaffold_bundle(source or _ledger_bundle())


def test_valid_operator_approval_ledger_gate_scaffold_emits_verifier_scaffold():
    b = _bundle()
    assert b.eligible_for_future_exact_operator_approval_task is True
    assert b.eligible_for_future_outbox_preparation_task is False
    assert b.approval_granted_now is False
    assert b.eligible_for_live_send_now is False
    assert b.approval_valid_for_outbox is False
    assert b.approval_valid_for_dispatch is False
    assert b.approval_valid_for_publication is False
    assert b.approval_valid_for_live_send is False
    assert b.provider_call_made is False and b.env_read is False and b.credential_value_read is False
    assert b.network_call_made is False and b.browser_session_used is False
    assert b.executable_request_artifact_created is False and b.public_url_created is False and b.metrics_created is False
    assert b.publication_ready is False and b.dispatch_allowed is False and b.runtime_truth is False
    assert b.human_review_required is True
    assert b.blockers == []
    template = b.future_exact_operator_approval_declaration_template
    assert validate_future_exact_operator_approval_declaration(template) == []
    assert template["approval_mode"] == APPROVAL_MODE
    assert template["approval_scope"] == APPROVAL_SCOPE
    assert template["exact_approval_phrase_required"] == EXACT_PHRASE_REQUIRED_LATER
    assert template["exact_approval_phrase_provided"] == EXACT_PHRASE_PROVIDED_NOW
    assert template["approved_payload_preview_ids"] == []
    assert template["approved_payload_hashes"] == []
    assert template["approved_platforms"] == []


def test_missing_declaration_scaffold_fails_closed():
    data = _ledger_bundle(); data.pop("operator_approval_declaration_scaffold")
    b = _bundle(data)
    assert "upstream_declaration_scaffold_missing" in b.blockers
    assert b.eligible_for_future_exact_operator_approval_task is False


def test_missing_ledger_shell_fails_closed():
    data = _ledger_bundle(); data.pop("approval_ledger_record_shell")
    assert "upstream_ledger_shell_missing" in _bundle(data).blockers


def test_upstream_eligibility_and_hard_false_rules():
    data = _ledger_bundle(); data["eligible_for_future_exact_operator_approval_task"] = False
    assert "upstream_future_exact_operator_approval_eligibility_not_true" in _bundle(data).blockers

    data = _ledger_bundle(); data["eligible_for_future_outbox_preparation_task"] = True
    assert "upstream_eligible_for_future_outbox_preparation_task_not_false" in _bundle(data).blockers

    for flag in UPSTREAM_FALSE_FLAGS:
        data = _ledger_bundle(); data[flag] = True
        assert f"upstream_{flag}_not_false" in _bundle(data).blockers


def test_upstream_declaration_phrase_and_ledger_shell_rules():
    data = _ledger_bundle(); data["operator_approval_declaration_scaffold"]["exact_approval_phrase"] = "JIM_APPROVES_PAYLOAD_HASHES_FOR_FUTURE_OUTBOX_PREP_ONLY"
    assert "upstream_declaration_phrase_not_scaffold_not_approved" in _bundle(data).blockers

    data = _ledger_bundle(); data["approval_ledger_record_shell"]["approval_status"] = "approved"
    assert "upstream_ledger_approval_status_not_not_approved" in _bundle(data).blockers

    for flag in UPSTREAM_LEDGER_FALSE_FLAGS:
        data = _ledger_bundle(); data["approval_ledger_record_shell"][flag] = True
        assert f"upstream_ledger_{flag}_not_false" in _bundle(data).blockers


def test_exact_approval_declaration_template_empty_lists_and_false_flags():
    template = dict(_bundle().future_exact_operator_approval_declaration_template)
    for field in DECLARATION_EMPTY_LISTS:
        mutated = dict(template); mutated[field] = ["not_allowed_in_scaffold"]
        assert f"declaration_{field}_not_empty" in validate_future_exact_operator_approval_declaration(mutated)
    for flag in ("approval_granted_now", "publication_approved_now", "outbox_approved_now", "dispatch_approved_now", "live_send_approved_now"):
        mutated = dict(template); mutated[flag] = True
        assert f"declaration_{flag}_not_false" in validate_future_exact_operator_approval_declaration(mutated)


def test_declaration_extra_field_and_missing_required_fields_fail_closed():
    template = dict(_bundle().future_exact_operator_approval_declaration_template)
    extra = dict(template); extra["unexpected"] = "x"
    assert "declaration_extra_fields" in validate_future_exact_operator_approval_declaration(extra)
    for field in DECLARATION_FIELDS:
        missing = dict(template); missing.pop(field)
        assert f"missing_declaration_{field}" in validate_future_exact_operator_approval_declaration(missing)


def test_forbidden_text_fails_closed_without_echoing_values():
    forbidden = ("endpoint", "webhook", "secret", "channel", "account", "cookie", "session", "browser path", "https://example.invalid/x", "metrics", "trading advice", "financial advice", "signal service", "live-send")
    template = dict(_bundle().future_exact_operator_approval_declaration_template)
    for term in forbidden:
        mutated = dict(template); mutated["notes"] = term
        blockers = validate_future_exact_operator_approval_declaration(mutated)
        assert any(b.startswith("declaration_forbidden_") for b in blockers)
        assert term not in " ".join(blockers)


def test_deterministic_ids_hashes_and_cli(tmp_path):
    assert _bundle().packet_sha256 == _bundle().packet_sha256
    inp = tmp_path / "ledger.json"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"
    inp.write_text(json.dumps(_ledger_bundle()), encoding="utf-8")
    assert main(["--operator-approval-ledger-gate-scaffold-bundle", str(inp), "--output", str(out1)]) == 0
    assert main(["--operator-approval-ledger-gate-scaffold-bundle", str(inp), "--output", str(out2)]) == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--operator-approval-ledger-gate-scaffold-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_exact_operator_approval_task"] is False
    assert data["approval_granted_now"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/exact_operator_approval_signature_verifier_scaffold_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_runbook_sample_hygiene():
    paths = [
        "docs/runbooks/V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_OPERATOR_RUNBOOK_NO_APPROVAL_NO_SEND.md",
        "docs/automation/V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_SCAFFOLD_HEAVY_BATCH_NO_APPROVAL_NO_SEND/implementation_report.md",
        "docs/automation/V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_SCAFFOLD_HEAVY_BATCH_NO_APPROVAL_NO_SEND/exact_operator_approval_signature_verifier_scaffold_contract.md",
        "docs/automation/V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_SCAFFOLD_HEAVY_BATCH_NO_APPROVAL_NO_SEND/sample_exact_operator_approval_signature_verifier_scaffold_bundle.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    txt = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "no provider" in txt and "no live send" in txt and "no approval granted now" in txt
    assert "no outbox/dispatch readiness" in txt and "review-only" in txt