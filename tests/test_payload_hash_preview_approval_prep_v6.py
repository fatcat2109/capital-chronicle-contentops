import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.payload_hash_preview_approval_prep_v6 import *
import live_contentops.payload_hash_preview_approval_prep_v6 as prep

SAMPLE_DRAFT_INSPECT = Path("docs/automation/V6_DRAFT_INSPECTOR_FOR_CONTENT_PRODUCTION_REVIEW_BUNDLE_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_draft_inspection_bundle.json")
SAMPLE_REVIEW_CORE = Path("docs/automation/V6_CONTENT_PRODUCTION_CORE_REVIEW_PACKETS_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_content_production_core_review_bundle.json")


def _draft_inspect():
    return json.loads(SAMPLE_DRAFT_INSPECT.read_text(encoding="utf-8"))


def _review_core():
    return json.loads(SAMPLE_REVIEW_CORE.read_text(encoding="utf-8"))


def _bundle(d_inspect=None, r_core=None):
    return make_payload_hash_preview_approval_prep_bundle(d_inspect or _draft_inspect(), r_core or _review_core())


def test_valid_bundle_emits_correct_previews_and_candidate():
    b = _bundle(); data = asdict(b)
    assert b.eligible_for_future_operator_approval_task is True
    assert b.eligible_for_future_outbox_preparation_task is False
    assert b.eligible_for_live_send_now is False
    assert b.provider_call_made is False and b.env_read is False and b.credential_value_read is False
    assert b.network_call_made is False and b.browser_session_used is False
    assert b.executable_request_artifact_created is False
    assert b.public_url_created is False and b.metrics_created is False
    assert b.publication_ready is False and b.dispatch_allowed is False and b.runtime_truth is False
    assert b.human_review_required is True
    
    assert len(b.payload_previews) == len(SUPPORTED_PLATFORMS)
    for p in b.payload_previews:
        assert p["platform"] in SUPPORTED_PLATFORMS
        assert p["preview_mode"] == PREVIEW_MODE
        assert p["preview_publication_ready"] is False
        assert p["preview_dispatch_ready"] is False
        assert p["preview_live_send_ready"] is False
        assert p["human_review_required"] is True
        assert p["payload_hash"]
        
    cand = b.approval_ledger_preparation_candidate
    assert cand["approval_mode"] == APPROVAL_MODE
    assert cand["approval_status"] == "not_approved"
    assert cand["human_approval_required"] is True
    assert cand["approval_granted_now"] is False
    assert cand["valid_for_outbox"] is False
    assert cand["valid_for_dispatch"] is False
    assert cand["publication_ready"] is False
    assert cand["dispatch_allowed"] is False
    assert cand["live_send_allowed"] is False
    assert cand["revocation_supported"] is True
    assert cand["expires_at_required_later"] is True
    assert cand["destination_binding_required_later"] is True
    assert cand["credential_handle_required_later"] is True
    assert cand["payload_hash_revalidation_required_later"] is True
    assert cand["redacted_audit_required_later"] is True
    assert cand["blockers"] == []


def test_missing_report_fails_closed():
    data = _draft_inspect(); data.pop("draft_inspection_report")
    assert "upstream_report_missing" in _bundle(d_inspect=data).blockers


def test_upstream_eligibility_false_fails_closed():
    data = _draft_inspect(); data["eligible_for_payload_hash_preview_task"] = False
    assert "upstream_payload_hash_eligibility_not_true" in _bundle(d_inspect=data).blockers
    
    data = _draft_inspect(); data["eligible_for_approval_ledger_preparation_task"] = False
    assert "upstream_approval_ledger_prep_eligibility_not_true" in _bundle(d_inspect=data).blockers


def test_upstream_flags_and_blocked_targets_rules():
    for flag in HARD_FALSE_FLAGS:
        data = _draft_inspect(); data[flag] = True
        assert f"upstream_{flag}_not_false" in _bundle(d_inspect=data).blockers
        
    data = _draft_inspect(); data["human_review_required"] = False
    assert "upstream_human_review_required_not_true" in _bundle(d_inspect=data).blockers
    
    data = _draft_inspect(); data["draft_inspection_report"]["approval_eligible_targets"] = ["live_send"]
    assert "report_approval_targets_invalid" in _bundle(d_inspect=data).blockers
    
    for target in BLOCKED_TARGETS:
        data = _draft_inspect(); data["draft_inspection_report"]["blocked_targets"].remove(target)
        assert f"report_blocked_target_missing_{target}" in _bundle(d_inspect=data).blockers


def test_forbidden_preview_text_interception():
    bad = ("fake citation", "fake metrics", "financial advice", "signal service", "buy", "sell", "hold", "entries", "exits", "targets", "position sizing", "guaranteed prediction", "model says", "ai guarantees", "publication approved", "dispatch allowed", "live send", "executable request", "webhook", "endpoint", "secret", "public url")
    for term in bad:
        data = _review_core()
        data["platform_variant_set_candidate_packet"]["variants"]["x_manual"]["review_only_text"] = term
        try:
            _bundle(r_core=data)
        except ValueError as exc:
            assert "forbidden_text" in str(exc)
        else:
            raise AssertionError(term)
            
    data = _review_core()
    data["platform_variant_set_candidate_packet"]["variants"]["x_manual"]["review_only_text"] = "https://discord.com/api/webhooks/x/y"
    try:
        _bundle(r_core=data)
    except ValueError as exc:
        assert "forbidden_value" in str(exc) and "discord.com" not in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_payload_hash_dependency_and_exclusion():
    p1 = _bundle().payload_previews[0]
    
    # Change review text
    data = _review_core()
    data["platform_variant_set_candidate_packet"]["variants"]["substack"]["review_only_text"] = "New substack variant text review"
    p2 = _bundle(r_core=data).payload_previews[0]
    
    assert p1["payload_hash"] != p2["payload_hash"]
    
    # Check change platform
    p3 = _bundle().payload_previews[1]
    assert p1["payload_hash"] != p3["payload_hash"]
    
    # Exclude secret check
    raw_hash_input = {
        "platform": "substack",
        "payload_class": "review_only_draft_candidate",
        "adapter_class": "future_webhook_adapter",
        "preview_text": p1["preview_text"],
        "source_draft_inspection_report_id": p1["source_draft_inspection_report_id"]
    }
    # Direct hash computation without secrets should equal the payload_hash
    computed = compute_payload_hash("substack", "review_only_draft_candidate", "future_webhook_adapter", p1["preview_text"], p1["source_draft_inspection_report_id"])
    assert p1["payload_hash"] == computed
    # Webhook or secret not present in input dump
    serialized = json.dumps(raw_hash_input)
    assert "discord.com" not in serialized
    assert "https://" not in serialized
    assert "cookie" not in serialized
    assert "secret" not in serialized
    assert "cookie" not in serialized


def test_approval_prep_cannot_grant_readiness():
    b = _bundle()
    cand = b.approval_ledger_preparation_candidate
    assert cand["approval_granted_now"] is False
    assert cand["valid_for_outbox"] is False
    assert cand["valid_for_dispatch"] is False
    assert cand["publication_ready"] is False
    assert cand["dispatch_allowed"] is False
    assert cand["live_send_allowed"] is False


def test_deterministic_ids_hashes_and_cli(tmp_path):
    assert _bundle().packet_sha256 == _bundle().packet_sha256
    d_inp = tmp_path / "draft.json"
    r_inp = tmp_path / "review.json"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"
    
    d_inp.write_text(json.dumps(_draft_inspect()), encoding="utf-8")
    r_inp.write_text(json.dumps(_review_core()), encoding="utf-8")
    
    assert main(["--draft-inspection-bundle", str(d_inp), "--content-production-review-bundle", str(r_inp), "--output", str(out1)]) == 0
    assert main(["--draft-inspection-bundle", str(d_inp), "--content-production-review-bundle", str(r_inp), "--output", str(out2)]) == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    d_inp = tmp_path / "bad_draft.json"
    r_inp = tmp_path / "review.json"
    out = tmp_path / "out.json"
    d_inp.write_text("[]", encoding="utf-8")
    r_inp.write_text(json.dumps(_review_core()), encoding="utf-8")
    
    assert main(["--draft-inspection-bundle", str(d_inp), "--content-production-review-bundle", str(r_inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_operator_approval_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/payload_hash_preview_approval_prep_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_runbook_sample_hygiene():
    paths = [
        "docs/runbooks/V6_PAYLOAD_HASH_PREVIEW_APPROVAL_PREP_OPERATOR_RUNBOOK_NO_PROVIDER_NO_SEND.md",
        "docs/automation/V6_PAYLOAD_HASH_PREVIEW_AND_APPROVAL_LEDGER_PREP_FROM_DRAFT_INSPECTION_HEAVY_BATCH_NO_PROVIDER_NO_SEND/implementation_report.md",
        "docs/automation/V6_PAYLOAD_HASH_PREVIEW_AND_APPROVAL_LEDGER_PREP_FROM_DRAFT_INSPECTION_HEAVY_BATCH_NO_PROVIDER_NO_SEND/payload_hash_preview_approval_prep_contract.md",
        "docs/automation/V6_PAYLOAD_HASH_PREVIEW_AND_APPROVAL_LEDGER_PREP_FROM_DRAFT_INSPECTION_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_payload_hash_preview_approval_prep_bundle.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    txt = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "no provider" in txt and "no live send" in txt and "no outbox/dispatch readiness" in txt and "review-only" in txt
