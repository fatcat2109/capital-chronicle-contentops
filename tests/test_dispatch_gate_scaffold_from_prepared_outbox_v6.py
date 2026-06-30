import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.dispatch_gate_scaffold_from_prepared_outbox_v6 import *
from live_contentops.outbox_preparation_gate_from_exact_jim_approval_v6 import make_outbox_preparation_gate_bundle
from tests.test_outbox_preparation_gate_from_exact_jim_approval_v6 import _accepted_intake

SAMPLE_OUTBOX = Path("docs/automation/V6_OUTBOX_PREPARATION_GATE_FROM_EXACT_JIM_APPROVAL_INTAKE_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_outbox_preparation_gate_bundle.json")


def _default_outbox():
    return json.loads(SAMPLE_OUTBOX.read_text(encoding="utf-8"))


def _accepted_outbox():
    data = asdict(make_outbox_preparation_gate_bundle(_accepted_intake()))
    data["warnings"].append("synthetic_test_fixture_only")
    return data


def _bundle(outbox=None):
    return make_dispatch_gate_scaffold_bundle(outbox or _accepted_outbox())


def test_default_sample_blocked_no_dispatch_review_records():
    b = make_dispatch_gate_scaffold_bundle(_default_outbox())
    assert b.dispatch_gate_status == "blocked_no_dispatch_review_records"
    assert b.dispatch_review_records == []
    assert b.eligible_for_future_destination_binding_task is False
    assert b.eligible_for_future_dispatch_execution_task is False
    assert b.eligible_for_live_send_now is False
    assert b.publication_ready is False
    assert b.dispatch_allowed is False
    assert b.live_send_allowed is False
    assert "outbox_bundle_status_not_prepared" in b.blockers


def test_accepted_synthetic_prepared_outbox_creates_dispatch_review_records():
    b = _bundle()
    assert b.blockers == []
    assert b.dispatch_gate_status == "ready_for_future_destination_binding_review_only"
    assert b.eligible_for_future_destination_binding_task is True
    assert b.eligible_for_future_dispatch_execution_task is False
    assert b.eligible_for_live_send_now is False
    assert b.publication_ready is False
    assert b.dispatch_allowed is False
    assert b.live_send_allowed is False
    assert b.provider_call_made is False and b.env_read is False and b.credential_value_read is False
    assert b.network_call_made is False and b.browser_session_used is False
    assert b.executable_request_artifact_created is False and b.public_url_created is False and b.metrics_created is False
    assert len(b.dispatch_review_records) == len(_accepted_outbox()["outbox_records"])
    for record in b.dispatch_review_records:
        assert validate_dispatch_review_record(record) == []
        assert record["dispatch_gate_mode"] == DISPATCH_GATE_MODE
        assert record["review_status"] == REVIEW_STATUS
        assert record["destination_binding_present"] is False
        assert record["credential_handle_present"] is False
        assert record["destination_binding_required_later"] is True
        assert record["credential_handle_required_later"] is True
        assert record["payload_hash_revalidation_required_later"] is True
        assert record["exact_operator_dispatch_go_required_later"] is True
        assert record["dispatch_allowed"] is False
        assert record["publication_ready"] is False
        assert record["live_send_allowed"] is False


def test_input_outbox_status_records_and_eligibility_fail_closed():
    data = _accepted_outbox(); data["outbox_preparation_status"] = "blocked_not_prepared"
    assert "outbox_bundle_status_not_prepared" in _bundle(data).blockers
    data = _accepted_outbox(); data["outbox_records"] = []
    assert "outbox_bundle_records_empty" in _bundle(data).blockers
    data = _accepted_outbox(); data["eligible_for_future_dispatch_gate_task"] = False
    assert "outbox_bundle_future_dispatch_gate_eligibility_not_true" in _bundle(data).blockers


def test_outbox_bundle_hard_false_flags_fail_closed():
    for flag in UPSTREAM_FALSE_FLAGS:
        data = _accepted_outbox(); data[flag] = True
        assert f"outbox_bundle_{flag}_not_false" in _bundle(data).blockers


def test_outbox_record_body_binding_readiness_and_blockers_fail_closed():
    for flag in ("payload_body_included", "destination_binding_present", "credential_handle_present", "dispatch_allowed", "publication_ready", "live_send_allowed"):
        data = _accepted_outbox(); data["outbox_records"][0][flag] = True
        assert f"record_0_outbox_record_{flag}_not_false" in _bundle(data).blockers
    data = _accepted_outbox(); data["outbox_records"][0]["blockers"] = ["synthetic_blocker"]
    assert "record_0_outbox_record_blockers_not_empty" in _bundle(data).blockers


def test_missing_approved_preview_hash_platform_fail_closed():
    for key in ("approved_payload_preview_id", "approved_payload_hash", "platform"):
        data = _accepted_outbox(); data["outbox_records"][0][key] = ""
        assert f"record_0_outbox_record_{key}_empty" in _bundle(data).blockers


def test_forbidden_outbox_record_text_fails_closed_without_echoing():
    forbidden = ("endpoint", "webhook", "token", "channel", "account", "cookie", "session", "localStorage", "browser profile", "env value", "credential value", "https://example.invalid/x", "metrics", "financial advice", "signal service", "fake metrics", "fake citations", "live-send")
    for term in forbidden:
        data = _accepted_outbox(); data["outbox_records"][0]["approved_payload_preview_id"] = term
        blockers = _bundle(data).blockers
        assert any("forbidden_" in b for b in blockers)
        assert term not in " ".join(blockers)


def test_dispatch_review_records_never_include_forbidden_text():
    forbidden = ("endpoint", "webhook", "token", "channel", "account", "cookie", "session", "browser profile", "env value", "credential value", "public URL", "metrics", "payload body", "curl")
    base = _bundle().dispatch_review_records[0]
    for term in forbidden:
        record = dict(base); record["approved_payload_preview_id"] = term
        blockers = validate_dispatch_review_record(record)
        assert any(b.startswith("dispatch_review_record_forbidden_") for b in blockers)
        assert term not in " ".join(blockers)


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--outbox-preparation-gate-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_destination_binding_task"] is False
    assert data["eligible_for_future_dispatch_execution_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_cli_deterministic_output(tmp_path):
    inp = tmp_path / "outbox.json"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"
    inp.write_text(json.dumps(_accepted_outbox()), encoding="utf-8")
    assert main(["--outbox-preparation-gate-bundle", str(inp), "--output", str(out1)]) == 0
    assert main(["--outbox-preparation-gate-bundle", str(inp), "--output", str(out2)]) == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/dispatch_gate_scaffold_from_prepared_outbox_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_runbook_sample_hygiene():
    paths = [
        "docs/runbooks/V6_DISPATCH_GATE_SCAFFOLD_OPERATOR_RUNBOOK_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md",
        "docs/automation/V6_DISPATCH_GATE_SCAFFOLD_FROM_PREPARED_OUTBOX_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/implementation_report.md",
        "docs/automation/V6_DISPATCH_GATE_SCAFFOLD_FROM_PREPARED_OUTBOX_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/dispatch_gate_scaffold_contract.md",
        "docs/automation/V6_DISPATCH_GATE_SCAFFOLD_FROM_PREPARED_OUTBOX_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_dispatch_gate_scaffold_bundle.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    txt = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "dispatch gate scaffold only" in txt
    assert "no provider" in txt and "no dispatch" in txt and "no live send" in txt
    assert "no executable request" in txt and "no public url" in txt and "metrics" in txt
    assert "destination binding later" in txt and "credential handle later" in txt
    assert "future dispatch execution task separate" in txt