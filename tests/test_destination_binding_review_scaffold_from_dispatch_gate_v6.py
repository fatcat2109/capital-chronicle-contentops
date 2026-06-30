import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.dispatch_gate_scaffold_from_prepared_outbox_v6 import make_dispatch_gate_scaffold_bundle
from live_contentops.destination_binding_review_scaffold_from_dispatch_gate_v6 import *
from tests.test_dispatch_gate_scaffold_from_prepared_outbox_v6 import _accepted_outbox

SAMPLE_DISPATCH = Path("docs/automation/V6_DISPATCH_GATE_SCAFFOLD_FROM_PREPARED_OUTBOX_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_dispatch_gate_scaffold_bundle.json")
SAMPLE_DESTINATION = Path("docs/automation/V6_DESTINATION_BINDING_REVIEW_SCAFFOLD_FROM_DISPATCH_GATE_HEAVY_BATCH_NO_ENV_NO_CREDENTIAL_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_destination_binding_review_scaffold_bundle.json")


def _default_dispatch():
    return json.loads(SAMPLE_DISPATCH.read_text(encoding="utf-8"))


def _accepted_dispatch():
    data = asdict(make_dispatch_gate_scaffold_bundle(_accepted_outbox()))
    data["warnings"].append("synthetic_test_fixture_only")
    return data


def _bundle(dispatch=None):
    return make_destination_binding_review_scaffold_bundle(dispatch or _accepted_dispatch())


def test_default_sample_blocked_no_destination_binding_review_records():
    b = make_destination_binding_review_scaffold_bundle(_default_dispatch())
    assert b.destination_binding_review_status == "blocked_no_destination_binding_review_records"
    assert b.destination_binding_review_records == []
    assert b.eligible_for_future_credential_presence_membership_task is False
    assert b.eligible_for_future_dispatch_execution_task is False
    assert b.eligible_for_live_send_now is False
    assert b.destination_binding_present is False
    assert b.credential_handle_present is False
    assert "dispatch_gate_bundle_status_not_ready" in b.blockers


def test_accepted_synthetic_dispatch_gate_creates_symbolic_destination_binding_records():
    b = _bundle()
    assert b.blockers == []
    assert b.destination_binding_review_status == "ready_for_future_credential_presence_membership_only"
    assert b.eligible_for_future_credential_presence_membership_task is True
    assert b.eligible_for_future_dispatch_execution_task is False
    assert b.eligible_for_live_send_now is False
    assert b.destination_binding_present is False
    assert b.credential_handle_present is False
    assert b.env_read is False and b.credential_value_read is False and b.provider_call_made is False
    assert b.network_call_made is False and b.browser_session_used is False and b.executable_request_artifact_created is False
    assert b.endpoint_url_present is False and b.webhook_url_present is False and b.channel_id_present is False
    assert b.account_id_present is False and b.token_present is False and b.payload_body_present is False
    assert b.publication_ready is False and b.dispatch_allowed is False and b.live_send_allowed is False
    assert len(b.destination_binding_review_records) == len(_accepted_dispatch()["dispatch_review_records"])
    for record in b.destination_binding_review_records:
        assert validate_destination_binding_review_record(record) == []
        assert record["destination_binding_mode"] == DESTINATION_BINDING_MODE
        assert record["review_status"] == DESTINATION_REVIEW_STATUS
        assert record["symbolic_destination_binding_id"].startswith("symbolic_destination_binding_required_later_")
        assert record["symbolic_credential_handle_id"].startswith("symbolic_credential_handle_required_later_")


def test_input_dispatch_gate_status_records_and_eligibility_fail_closed():
    data = _accepted_dispatch(); data["dispatch_gate_status"] = "blocked"
    assert "dispatch_gate_bundle_status_not_ready" in _bundle(data).blockers
    data = _accepted_dispatch(); data["dispatch_review_records"] = []
    assert "dispatch_gate_bundle_records_empty" in _bundle(data).blockers
    data = _accepted_dispatch(); data["eligible_for_future_destination_binding_task"] = False
    assert "dispatch_gate_bundle_eligible_for_future_destination_binding_task_not_true" in _bundle(data).blockers
    data = _accepted_dispatch(); data["eligible_for_future_dispatch_execution_task"] = True
    assert "dispatch_gate_bundle_eligible_for_future_dispatch_execution_task_not_false" in _bundle(data).blockers


def test_bundle_hard_false_flags_fail_closed():
    for flag in BUNDLE_FALSE_FLAGS:
        data = _accepted_dispatch(); data[flag] = True
        assert f"dispatch_gate_bundle_{flag}_not_false" in _bundle(data).blockers


def test_bundle_required_later_true_flags_fail_closed():
    for flag in BUNDLE_TRUE_FLAGS:
        data = _accepted_dispatch(); data[flag] = False
        assert f"dispatch_gate_bundle_{flag}_not_true" in _bundle(data).blockers


def test_dispatch_review_record_binding_and_readiness_flags_fail_closed():
    for flag in ("destination_binding_present", "credential_handle_present"):
        data = _accepted_dispatch(); data["dispatch_review_records"][0][flag] = True
        assert f"record_0_dispatch_review_record_{flag}_not_false" in _bundle(data).blockers
    for flag in ("dispatch_allowed", "publication_ready", "live_send_allowed"):
        data = _accepted_dispatch(); data["dispatch_review_records"][0][flag] = True
        assert f"record_0_dispatch_review_record_{flag}_not_false" in _bundle(data).blockers
    data = _accepted_dispatch(); data["dispatch_review_records"][0]["blockers"] = ["synthetic_blocker"]
    assert "record_0_dispatch_review_record_blockers_not_empty" in _bundle(data).blockers


def test_missing_source_platform_preview_hash_fail_closed():
    for key in ("source_outbox_record_id", "platform", "approved_payload_preview_id", "approved_payload_hash"):
        data = _accepted_dispatch(); data["dispatch_review_records"][0][key] = ""
        assert f"record_0_dispatch_review_record_{key}_empty" in _bundle(data).blockers


def test_destination_binding_review_record_hard_flags_fail_closed():
    base = _bundle().destination_binding_review_records[0]
    for flag in DESTINATION_REVIEW_FALSE_FLAGS:
        record = dict(base); record[flag] = True
        assert f"destination_binding_review_record_{flag}_not_false" in validate_destination_binding_review_record(record)


def test_symbolic_id_prefix_required():
    base = _bundle().destination_binding_review_records[0]
    record = dict(base); record["symbolic_destination_binding_id"] = "bad"
    assert "destination_binding_review_record_symbolic_destination_binding_id_prefix_invalid" in validate_destination_binding_review_record(record)
    record = dict(base); record["symbolic_credential_handle_id"] = "bad"
    assert "destination_binding_review_record_symbolic_credential_handle_id_prefix_invalid" in validate_destination_binding_review_record(record)


def test_forbidden_text_fails_closed_without_echoing_raw_value():
    forbidden = ("endpoint", "webhook", "token", "channel", "account", "cookie", "session", "localStorage", "browser profile", "env value", "credential value", "https://example.invalid/x", "metrics", "financial advice", "signal service", "fake metrics", "fake citations", "live-send", "payload body", "curl", "fetch", "requests")
    for term in forbidden:
        data = _accepted_dispatch(); data["dispatch_review_records"][0]["approved_payload_preview_id"] = term
        blockers = _bundle(data).blockers
        assert any("forbidden_" in b for b in blockers)
        assert term not in " ".join(blockers)


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"; out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--dispatch-gate-scaffold-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_credential_presence_membership_task"] is False
    assert data["eligible_for_future_dispatch_execution_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_cli_deterministic_output(tmp_path):
    inp = tmp_path / "dispatch.json"; out1 = tmp_path / "out1.json"; out2 = tmp_path / "out2.json"
    inp.write_text(json.dumps(_accepted_dispatch()), encoding="utf-8")
    assert main(["--dispatch-gate-scaffold-bundle", str(inp), "--output", str(out1)]) == 0
    assert main(["--dispatch-gate-scaffold-bundle", str(inp), "--output", str(out2)]) == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/destination_binding_review_scaffold_from_dispatch_gate_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_static_no_hardcoded_endpoint_or_executable_pattern():
    src = Path("live_contentops/destination_binding_review_scaffold_from_dispatch_gate_v6.py").read_text(encoding="utf-8")
    for pat in [r"discord(?:app)?\.com/api/webhooks", r"https?://", r"\bPOST\b", r"headers\s*=", r"body\s*=", r"curl\s", r"fetch\(", r"requests\."]:
        assert re.search(pat, src, re.I) is None, pat


def test_docs_runbook_sample_hygiene():
    paths = [
        "docs/runbooks/V6_DESTINATION_BINDING_REVIEW_SCAFFOLD_OPERATOR_RUNBOOK_NO_ENV_NO_CREDENTIAL_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md",
        "docs/automation/V6_DESTINATION_BINDING_REVIEW_SCAFFOLD_FROM_DISPATCH_GATE_HEAVY_BATCH_NO_ENV_NO_CREDENTIAL_NO_PROVIDER_NO_DISPATCH_NO_LIVE/implementation_report.md",
        "docs/automation/V6_DESTINATION_BINDING_REVIEW_SCAFFOLD_FROM_DISPATCH_GATE_HEAVY_BATCH_NO_ENV_NO_CREDENTIAL_NO_PROVIDER_NO_DISPATCH_NO_LIVE/destination_binding_review_scaffold_contract.md",
        "docs/automation/V6_DESTINATION_BINDING_REVIEW_SCAFFOLD_FROM_DISPATCH_GATE_HEAVY_BATCH_NO_ENV_NO_CREDENTIAL_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_destination_binding_review_scaffold_bundle.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    txt = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "destination binding review scaffold only" in txt
    assert "no env read" in txt and "no credential value read" in txt and "no provider" in txt
    assert "no dispatch" in txt and "no live send" in txt and "no executable request" in txt
    assert "no endpoint" in txt and "webhook" in txt and "channel" in txt and "account" in txt and "token" in txt
    assert "credential presence membership task later" in txt and "dispatch execution task separate" in txt
    sample = json.loads(SAMPLE_DESTINATION.read_text(encoding="utf-8"))
    assert sample["destination_binding_review_records"] == []
    assert sample["eligible_for_future_credential_presence_membership_task"] is False
