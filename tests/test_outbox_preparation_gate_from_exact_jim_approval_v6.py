import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.outbox_preparation_gate_from_exact_jim_approval_v6 import *
from live_contentops.exact_jim_approval_declaration_intake_gate_v6 import (
    APPROVAL_MODE as INTAKE_APPROVAL_MODE,
    APPROVAL_SCOPE as INTAKE_APPROVAL_SCOPE,
    EXACT_APPROVAL_PHRASE,
    make_exact_jim_approval_declaration_intake_gate_bundle,
)

SAMPLE_VERIFIER = Path("docs/automation/V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_SCAFFOLD_HEAVY_BATCH_NO_APPROVAL_NO_SEND/sample_exact_operator_approval_signature_verifier_scaffold_bundle.json")
SAMPLE_INTAKE = Path("docs/automation/V6_EXACT_JIM_APPROVAL_DECLARATION_INTAKE_GATE_HEAVY_BATCH_NO_PROVIDER_NO_LIVE_SEND/sample_exact_jim_approval_declaration_intake_gate_bundle.json")


def _verifier_bundle():
    return json.loads(SAMPLE_VERIFIER.read_text(encoding="utf-8"))


def _default_intake():
    return json.loads(SAMPLE_INTAKE.read_text(encoding="utf-8"))


def _accepted_declaration():
    verifier = _verifier_bundle()
    template = verifier["future_exact_operator_approval_declaration_template"]
    return {
        "schema_version": SCHEMA_VERSION,
        "jim_approval_declaration_id": "synthetic_test_fixture_only_outbox_prep_jim_approval_001",
        "source_exact_operator_approval_signature_verifier_scaffold_bundle_id": verifier["exact_operator_approval_signature_verifier_scaffold_bundle_id"],
        "source_payload_hash_preview_approval_prep_bundle_id": template["source_payload_hash_preview_approval_prep_bundle_id"],
        "operator_id": "jim",
        "created_at_manual": "synthetic_test_fixture_only_manual_timestamp",
        "approval_mode": INTAKE_APPROVAL_MODE,
        "approval_scope": INTAKE_APPROVAL_SCOPE,
        "exact_approval_phrase_required": EXACT_APPROVAL_PHRASE,
        "exact_approval_phrase_provided": EXACT_APPROVAL_PHRASE,
        "approved_payload_preview_ids": ["synthetic_test_fixture_only_preview_001", "synthetic_test_fixture_only_preview_002"],
        "approved_payload_hashes": ["1" * 64, "2" * 64],
        "approved_platforms": ["discord", "telegram"],
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


def _accepted_intake():
    return asdict(make_exact_jim_approval_declaration_intake_gate_bundle(_verifier_bundle(), _accepted_declaration()))


def _bundle(intake=None):
    return make_outbox_preparation_gate_bundle(intake or _accepted_intake())


def test_accepted_synthetic_intake_creates_non_executable_outbox_records():
    b = _bundle()
    assert b.blockers == []
    assert b.outbox_preparation_status == "prepared_for_future_dispatch_gate_only"
    assert b.eligible_for_future_dispatch_gate_task is True
    assert b.eligible_for_live_send_now is False
    assert b.publication_ready is False
    assert b.dispatch_allowed is False
    assert b.live_send_allowed is False
    assert b.provider_call_made is False and b.env_read is False and b.credential_value_read is False
    assert b.network_call_made is False and b.browser_session_used is False
    assert b.executable_request_artifact_created is False and b.public_url_created is False and b.metrics_created is False
    assert len(b.outbox_records) == 2
    for record in b.outbox_records:
        assert validate_outbox_record(record) == []
        assert record["outbox_mode"] == OUTBOX_MODE
        assert record["record_status"] == RECORD_STATUS
        assert record["payload_body_included"] is False
        assert record["payload_body_non_executable"] is True
        assert record["payload_hash_bound"] is True
        assert record["destination_binding_present"] is False
        assert record["credential_handle_present"] is False
        assert record["dispatch_allowed"] is False
        assert record["publication_ready"] is False
        assert record["live_send_allowed"] is False


def test_default_sample_not_approved_does_not_prepare_outbox():
    b = make_outbox_preparation_gate_bundle(_default_intake())
    assert b.outbox_preparation_status == "blocked_not_prepared"
    assert b.eligible_for_future_dispatch_gate_task is False
    assert b.outbox_records == []
    assert "intake_status_not_accepted" in b.blockers
    assert b.eligible_for_live_send_now is False
    assert b.publication_ready is False
    assert b.dispatch_allowed is False
    assert b.live_send_allowed is False


def test_intake_approval_and_outbox_eligibility_flags_fail_closed():
    data = _accepted_intake(); data["approval_granted_now"] = False
    assert "intake_approval_granted_now_not_true" in _bundle(data).blockers
    data = _accepted_intake(); data["eligible_for_future_outbox_preparation_task"] = False
    assert "intake_future_outbox_preparation_eligibility_not_true" in _bundle(data).blockers
    data = _accepted_intake(); data["approval_valid_for_payload_hashes_only"] = False
    assert "intake_approval_valid_for_payload_hashes_only_not_true" in _bundle(data).blockers
    data = _accepted_intake(); data["blockers"] = ["synthetic_blocker"]
    assert "intake_blockers_not_empty" in _bundle(data).blockers


def test_empty_approved_ids_hashes_platforms_fail_closed():
    for key in ("approved_payload_preview_ids", "approved_payload_hashes", "approved_platforms"):
        data = _accepted_intake(); data[key] = []
        assert f"intake_{key}_empty" in _bundle(data).blockers


def test_intake_hard_false_flags_fail_closed():
    for flag in INTAKE_FALSE_FLAGS:
        data = _accepted_intake(); data[flag] = True
        assert f"intake_{flag}_not_false" in _bundle(data).blockers


def test_outbox_records_never_include_forbidden_values():
    forbidden = ("endpoint", "webhook", "token", "channel", "account", "cookie", "session", "browser profile", "ENV_VALUE", "https://example.invalid/x", "metrics")
    for term in forbidden:
        record = dict(_bundle().outbox_records[0]); record["approved_payload_preview_id"] = term
        blockers = validate_outbox_record(record)
        assert any(b.startswith("outbox_record_forbidden_") for b in blockers)
        assert term not in " ".join(blockers)


def test_outbox_record_binding_body_and_readiness_flags_fail_closed():
    for flag in ("destination_binding_present", "credential_handle_present", "payload_body_included", "dispatch_allowed", "publication_ready", "live_send_allowed"):
        record = dict(_bundle().outbox_records[0]); record[flag] = True
        assert f"outbox_record_{flag}_not_false" in validate_outbox_record(record)


def test_forbidden_advice_fake_claims_and_live_send_text_fail_closed_without_echoing():
    forbidden = ("financial advice", "signal service", "fake metrics", "fake citations", "live-send", "buy", "sell", "hold", "entries", "exits", "targets")
    for term in forbidden:
        record = dict(_bundle().outbox_records[0]); record["approved_payload_preview_id"] = term
        blockers = validate_outbox_record(record)
        assert any(b.startswith("outbox_record_forbidden_") for b in blockers)
        assert term not in " ".join(blockers)


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--exact-jim-approval-intake-gate-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_dispatch_gate_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_cli_deterministic_output(tmp_path):
    inp = tmp_path / "intake.json"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"
    inp.write_text(json.dumps(_accepted_intake()), encoding="utf-8")
    assert main(["--exact-jim-approval-intake-gate-bundle", str(inp), "--output", str(out1)]) == 0
    assert main(["--exact-jim-approval-intake-gate-bundle", str(inp), "--output", str(out2)]) == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/outbox_preparation_gate_from_exact_jim_approval_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_runbook_sample_hygiene():
    paths = [
        "docs/runbooks/V6_OUTBOX_PREPARATION_GATE_OPERATOR_RUNBOOK_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md",
        "docs/automation/V6_OUTBOX_PREPARATION_GATE_FROM_EXACT_JIM_APPROVAL_INTAKE_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/implementation_report.md",
        "docs/automation/V6_OUTBOX_PREPARATION_GATE_FROM_EXACT_JIM_APPROVAL_INTAKE_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/outbox_preparation_gate_contract.md",
        "docs/automation/V6_OUTBOX_PREPARATION_GATE_FROM_EXACT_JIM_APPROVAL_INTAKE_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_outbox_preparation_gate_bundle.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    txt = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "outbox preparation only" in txt
    assert "no provider" in txt and "no dispatch" in txt and "no live send" in txt
    assert "no executable request" in txt and "no public url" in txt and "metrics" in txt
    assert "future dispatch gate required" in txt