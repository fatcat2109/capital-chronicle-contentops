import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.draft_inspector_for_content_production_v6 import *
import live_contentops.draft_inspector_for_content_production_v6 as inspector

SAMPLE = Path("docs/automation/V6_CONTENT_PRODUCTION_CORE_REVIEW_PACKETS_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_content_production_core_review_bundle.json")


def _bundle():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _inspection(bundle=None):
    return make_draft_inspection_bundle(bundle or _bundle())


def test_valid_bundle_emits_future_only_inspection():
    b = _inspection(); r = b.draft_inspection_report
    assert b.eligible_for_payload_hash_preview_task is True
    assert b.eligible_for_approval_ledger_preparation_task is True
    assert b.eligible_for_live_send_now is False
    assert r["eligible_for_payload_hash_preview_task"] is True
    assert r["eligible_for_approval_ledger_task"] is True
    assert r["eligible_for_live_send_now"] is False
    assert b.provider_call_made is False and b.env_read is False and b.credential_value_read is False
    assert b.network_call_made is False and b.browser_session_used is False
    assert b.public_url_created is False and b.metrics_created is False
    assert b.publication_ready is False and b.dispatch_allowed is False and b.runtime_truth is False
    assert b.human_review_required is True and b.blockers == []


def test_missing_required_packet_section_fails_closed():
    for section in REQUIRED_SECTIONS:
        data = _bundle(); data.pop(section)
        b = _inspection(data)
        assert b.eligible_for_payload_hash_preview_task is False
        assert f"missing_{section}" in b.blockers


def test_upstream_eligibility_and_flags_fail_closed():
    data = _bundle(); data["eligible_for_future_draft_inspection_task"] = False
    assert "upstream_draft_inspection_eligibility_not_true" in _inspection(data).blockers
    for flag in HARD_FALSE_FLAGS:
        data = _bundle(); data[flag] = True
        b = _inspection(data)
        assert b.eligible_for_payload_hash_preview_task is False
        assert f"upstream_{flag}_not_false" in b.blockers
    data = _bundle(); data["human_review_required"] = False
    assert "upstream_human_review_required_not_true" in _inspection(data).blockers


def test_citation_and_missing_evidence_statuses_preserved():
    r = _inspection().draft_inspection_report
    assert r["citation_status"] == "source_review_required"
    assert r["missing_evidence_status"] == "review_required"
    assert r["source_freshness_status"] == "source_review_required"
    assert r["missing_evidence_status"] != "pass"


def test_article_missing_limitations_or_disclosure_fails_closed():
    data = _bundle(); data["canonical_article_review_packet"]["limitations"] = []
    assert "article_limitations_missing" in _inspection(data).blockers
    data = _bundle(); data["canonical_article_review_packet"]["disclosure"] = ""
    assert "article_disclosure_missing" in _inspection(data).blockers


def test_seo_caveats_and_limitations_fail_closed():
    data = _bundle(); data["seo_editorial_packet"]["limitations_preserved"] = False
    assert "seo_limitations_preserved_not_true" in _inspection(data).blockers
    data = _bundle(); data["seo_editorial_packet"]["caveats_preserved"] = False
    assert "seo_caveats_preserved_not_true" in _inspection(data).blockers


def test_discord_drop_safety_fail_closed():
    data = _bundle(); data["discord_drop_candidate_packet"]["discussion_question"] = ""
    assert "discord_discussion_question_missing" in _inspection(data).blockers
    data = _bundle(); data["discord_drop_candidate_packet"]["disclosure"] = ""
    assert "discord_disclosure_missing" in _inspection(data).blockers
    data = _bundle(); data["discord_drop_candidate_packet"]["publication_ready"] = True
    assert "discord_publication_ready_not_false" in _inspection(data).blockers
    data = _bundle(); data["discord_drop_candidate_packet"]["dispatch_allowed"] = True
    assert "discord_dispatch_allowed_not_false" in _inspection(data).blockers


def test_platform_variant_execution_and_preservation():
    r = _inspection().draft_inspection_report
    assert r["variant_execution_status"] == "pass"
    data = _bundle(); v = data["platform_variant_set_candidate_packet"]
    assert v["manual_fallback_by_platform"]["x_manual"] is True
    assert "linkedin_org_deferred" in v["deferred_platforms"] and "tiktok_deferred" in v["deferred_platforms"]
    v["execution_readiness_by_platform"]["discord"] = True
    assert "variant_execution_readiness_not_all_false" in _inspection(data).blockers
    data = _bundle(); data["platform_variant_set_candidate_packet"]["variants"]["discord"]["dispatch_ready"] = True
    assert "variant_dispatch_ready_not_false" in _inspection(data).blockers


def test_approval_and_blocked_targets():
    targets = set(_inspection().draft_inspection_report["approval_eligible_targets"])
    assert targets == set(APPROVAL_TARGETS)
    assert not (targets & PROHIBITED_APPROVAL_TARGETS)
    blocked = set(_inspection().draft_inspection_report["blocked_targets"])
    for target in BLOCKED_TARGETS:
        assert target in blocked


def test_forbidden_content_scan_catches_without_echo():
    bad = ("fake citation", "fake metrics", "financial advice", "signal service", "buy", "sell", "hold", "entries", "exits", "targets", "position sizing", "guaranteed prediction", "model says", "AI guarantees", "publication approved", "dispatch allowed", "live send", "executable request")
    for text in bad:
        data = _bundle(); data["operator_intent_packet"]["notes"] = text
        try:
            _inspection(data)
        except ValueError as exc:
            assert "forbidden_text" in str(exc)
        else:
            raise AssertionError(text)
    data = _bundle(); data["operator_intent_packet"]["notes"] = "https://discord.com/api/webhooks/x/y"
    try:
        _inspection(data)
    except ValueError as exc:
        assert "forbidden_value" in str(exc) and "discord.com" not in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_deterministic_ids_hashes_and_cli(tmp_path):
    assert _inspection().packet_sha256 == _inspection().packet_sha256
    inp = tmp_path / "bundle.json"; out1 = tmp_path / "out1.json"; out2 = tmp_path / "out2.json"
    inp.write_text(json.dumps(_bundle()), encoding="utf-8")
    assert main(["--content-production-review-bundle", str(inp), "--output", str(out1)]) == 0
    assert main(["--content-production-review-bundle", str(inp), "--output", str(out2)]) == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"; out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--content-production-review-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_payload_hash_preview_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/draft_inspector_for_content_production_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_runbook_sample_hygiene():
    paths = [
        "docs/runbooks/V6_DRAFT_INSPECTOR_FOR_CONTENT_PRODUCTION_OPERATOR_RUNBOOK_NO_PROVIDER_NO_SEND.md",
        "docs/automation/V6_DRAFT_INSPECTOR_FOR_CONTENT_PRODUCTION_REVIEW_BUNDLE_HEAVY_BATCH_NO_PROVIDER_NO_SEND/implementation_report.md",
        "docs/automation/V6_DRAFT_INSPECTOR_FOR_CONTENT_PRODUCTION_REVIEW_BUNDLE_HEAVY_BATCH_NO_PROVIDER_NO_SEND/draft_inspector_for_content_production_contract.md",
        "docs/automation/V6_DRAFT_INSPECTOR_FOR_CONTENT_PRODUCTION_REVIEW_BUNDLE_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_draft_inspection_bundle.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    txt = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "no provider" in txt and "no live send" in txt and "no publication readiness" in txt and "review-only" in txt
