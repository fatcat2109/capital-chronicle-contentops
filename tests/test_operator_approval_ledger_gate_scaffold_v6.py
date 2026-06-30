import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.operator_approval_ledger_gate_scaffold_v6 import *
import live_contentops.operator_approval_ledger_gate_scaffold_v6 as scaffold

SAMPLE_PREP = Path("docs/automation/V6_PAYLOAD_HASH_PREVIEW_AND_APPROVAL_LEDGER_PREP_FROM_DRAFT_INSPECTION_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_payload_hash_preview_approval_prep_bundle.json")


def _prep_bundle():
    return json.loads(SAMPLE_PREP.read_text(encoding="utf-8"))


def _bundle(prep_bundle=None):
    return make_operator_approval_ledger_gate_scaffold_bundle(prep_bundle or _prep_bundle())


def test_valid_bundle_emits_correct_scaffold():
    b = _bundle(); data = asdict(b)
    assert b.eligible_for_future_exact_operator_approval_task is True
    assert b.eligible_for_future_outbox_preparation_task is False
    assert b.eligible_for_live_send_now is False
    assert b.approval_granted_now is False
    assert b.valid_for_outbox is False
    assert b.valid_for_dispatch is False
    assert b.publication_ready is False
    assert b.dispatch_allowed is False
    assert b.live_send_allowed is False
    
    decl = b.operator_approval_declaration_scaffold
    assert decl["approval_mode"] == APPROVAL_MODE
    assert decl["approval_scope"] == APPROVAL_SCOPE
    assert decl["exact_approval_phrase"] == "NOT_APPROVED_IN_THIS_SCAFFOLD"
    assert decl["approved_payload_preview_ids"] == []
    assert decl["approved_payload_hashes"] == []
    assert decl["approved_platforms"] == []
    assert decl["approval_granted_now"] is False
    assert decl["publication_approved_now"] is False
    assert decl["outbox_approved_now"] is False
    assert decl["dispatch_approved_now"] is False
    assert decl["live_send_approved_now"] is False
    assert decl["provider_call_requested"] is False
    assert decl["env_read_requested"] is False
    assert decl["credential_value_read_requested"] is False
    assert decl["network_call_requested"] is False
    assert decl["browser_session_requested"] is False
    assert decl["executable_request_artifact_requested"] is False
    assert decl["public_url_requested"] is False
    assert decl["metrics_requested"] is False
    assert decl["destination_binding_present"] is False
    assert decl["credential_handle_present"] is False
    assert decl["payload_hash_revalidation_performed"] is False
    assert decl["expires_at"] is None
    assert decl["revocation_supported"] is True
    assert decl["human_review_required"] is True
    assert decl["notes"] == ""
    
    shell = b.approval_ledger_record_shell
    assert shell["approval_record_mode"] == RECORD_MODE
    assert shell["approval_status"] == "not_approved"
    assert shell["approval_granted_now"] is False
    assert shell["approval_valid_for_payload_hash_preview_only"] is False
    assert shell["approval_valid_for_outbox"] is False
    assert shell["approval_valid_for_dispatch"] is False
    assert shell["approval_valid_for_publication"] is False
    assert shell["approval_valid_for_live_send"] is False
    assert shell["approved_payload_preview_ids"] == []
    assert shell["approved_payload_hashes"] == []
    assert shell["approved_platforms"] == []
    for flag in LEDGER_TRUE_FLAGS:
        assert shell[flag] is True
    assert shell["blockers"] == []


def test_missing_previews_fails_closed():
    data = _prep_bundle(); data.pop("payload_previews")
    assert "upstream_previews_missing_or_empty" in _bundle(data).blockers
    
    data = _prep_bundle(); data["payload_previews"] = []
    assert "upstream_previews_missing_or_empty" in _bundle(data).blockers


def test_missing_candidate_fails_closed():
    data = _prep_bundle(); data.pop("approval_ledger_preparation_candidate")
    assert "upstream_approval_candidate_missing" in _bundle(data).blockers


def test_upstream_eligibility_and_flags_rules():
    data = _prep_bundle(); data["eligible_for_future_operator_approval_task"] = False
    assert "upstream_operator_approval_eligibility_not_true" in _bundle(data).blockers
    
    data = _prep_bundle(); data["eligible_for_future_outbox_preparation_task"] = True
    assert "upstream_outbox_prep_eligibility_not_false" in _bundle(data).blockers
    
    for flag in HARD_FALSE_FLAGS:
        data = _prep_bundle(); data[flag] = True
        assert f"upstream_{flag}_not_false" in _bundle(data).blockers
        
    data = _prep_bundle(); data["human_review_required"] = False
    assert "upstream_human_review_required_not_true" in _bundle(data).blockers


def test_upstream_candidate_eligibility_rules():
    data = _prep_bundle(); data["approval_ledger_preparation_candidate"]["approval_status"] = "approved"
    assert "upstream_candidate_status_not_not_approved" in _bundle(data).blockers
    
    for flag in ("approval_granted_now", "valid_for_outbox", "valid_for_dispatch", "publication_ready", "dispatch_allowed", "live_send_allowed"):
        data = _prep_bundle(); data["approval_ledger_preparation_candidate"][flag] = True
        assert f"upstream_candidate_{flag}_not_false" in _bundle(data).blockers


def test_scaffold_declaration_constraints():
    b = _bundle()
    decl = b.operator_approval_declaration_scaffold
    assert decl["approved_payload_preview_ids"] == []
    assert decl["approved_payload_hashes"] == []
    assert decl["approved_platforms"] == []
    assert decl["approval_granted_now"] is False
    assert decl["publication_approved_now"] is False
    assert decl["outbox_approved_now"] is False
    assert decl["dispatch_approved_now"] is False
    assert decl["live_send_approved_now"] is False


def test_extra_fields_fail_closed():
    decl = dict(_bundle().operator_approval_declaration_scaffold)
    assert validate_operator_approval_declaration(decl) == []

    with_extra = dict(decl)
    with_extra["unexpected_field"] = "unexpected"
    assert "declaration_extra_fields" in validate_operator_approval_declaration(with_extra)

    for field in DECLARATION_FIELDS:
        missing = dict(decl)
        missing.pop(field)
        assert f"missing_declaration_{field}" in validate_operator_approval_declaration(missing)

    from live_contentops.exact_operator_approval_signature_verifier_scaffold_v6 import (
        DECLARATION_FALSE_FLAGS as EXACT_DECLARATION_FALSE_FLAGS,
        make_future_exact_operator_approval_declaration_template,
        validate_future_exact_operator_approval_declaration,
    )

    future_decl = make_future_exact_operator_approval_declaration_template(asdict(_bundle()))
    for flag in EXACT_DECLARATION_FALSE_FLAGS:
        flagged = dict(future_decl)
        flagged[flag] = True
        assert f"declaration_{flag}_not_false" in validate_future_exact_operator_approval_declaration(flagged)


def test_forbidden_notes_interception():
    bad = ("fake citation", "fake metrics", "financial advice", "signal service", "buy", "sell", "hold", "entries", "exits", "targets", "position sizing", "guaranteed prediction", "model says", "ai guarantees", "publication approved", "dispatch allowed", "live send", "executable request", "webhook", "endpoint", "secret", "public url")
    for term in bad:
        data = _prep_bundle()
        # Insert a forbidden string into the notes of the prep bundle or some text
        data["warnings"].append(term)
        try:
            _bundle(data)
        except ValueError as exc:
            assert "forbidden_text" in str(exc)
        else:
            raise AssertionError(term)
            
    data = _prep_bundle()
    data["warnings"].append("https://discord.com/api/webhooks/x/y")
    try:
        _bundle(data)
    except ValueError as exc:
        assert "forbidden_value" in str(exc) and "discord.com" not in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_deterministic_ids_hashes_and_cli(tmp_path):
    assert _bundle().packet_sha256 == _bundle().packet_sha256
    inp = tmp_path / "prep.json"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"
    
    inp.write_text(json.dumps(_prep_bundle()), encoding="utf-8")
    
    assert main(["--payload-hash-prep-bundle", str(inp), "--output", str(out1)]) == 0
    assert main(["--payload-hash-prep-bundle", str(inp), "--output", str(out2)]) == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    
    assert main(["--payload-hash-prep-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_exact_operator_approval_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/operator_approval_ledger_gate_scaffold_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_runbook_sample_hygiene():
    paths = [
        "docs/runbooks/V6_OPERATOR_APPROVAL_LEDGER_GATE_SCAFFOLD_OPERATOR_RUNBOOK_NO_APPROVAL_NO_SEND.md",
        "docs/automation/V6_OPERATOR_APPROVAL_LEDGER_GATE_SCAFFOLD_FROM_PAYLOAD_HASH_PREP_HEAVY_BATCH_NO_APPROVAL_NO_SEND/implementation_report.md",
        "docs/automation/V6_OPERATOR_APPROVAL_LEDGER_GATE_SCAFFOLD_FROM_PAYLOAD_HASH_PREP_HEAVY_BATCH_NO_APPROVAL_NO_SEND/operator_approval_ledger_gate_scaffold_contract.md",
        "docs/automation/V6_OPERATOR_APPROVAL_LEDGER_GATE_SCAFFOLD_FROM_PAYLOAD_HASH_PREP_HEAVY_BATCH_NO_APPROVAL_NO_SEND/sample_operator_approval_ledger_gate_scaffold_bundle.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    txt = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "no provider" in txt and "no live send" in txt and "no approval granted now" in txt and "review-only" in txt
