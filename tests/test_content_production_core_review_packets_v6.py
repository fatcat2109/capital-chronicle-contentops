import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.content_production_core_review_packets_v6 import *
import live_contentops.content_production_core_review_packets_v6 as core


def _intent():
    return {
        "schema_version": "6.0.0",
        "operator_intent_id": "intent_001",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T08:45:00+07:00",
        "intent_class": "create_canonical_article",
        "raw_operator_topic": "How to evaluate forecast readiness before publishing educational macro commentary",
        "content_lane": "forecast_readiness_explainer",
        "intended_platforms": ["substack", "discord", "x_manual", "linkedin_org_deferred", "tiktok_deferred"],
        "live_write_requested": False,
        "provider_call_requested": False,
        "browser_requested": False,
        "publication_requested": False,
        "dispatch_requested": False,
        "financial_advice_requested": False,
        "signal_service_requested": False,
        "notes": "",
    }


def _bundle(intent=None):
    return make_content_production_review_bundle(intent or _intent())


def test_valid_intent_creates_full_review_bundle_future_only():
    b = _bundle(); data = asdict(b)
    assert b.eligible_for_future_draft_inspection_task is True
    assert b.eligible_for_payload_hash_approval_task is True
    assert b.eligible_for_live_send_now is False
    assert b.provider_call_made is False
    assert b.env_read is False and b.credential_value_read is False
    assert b.network_call_made is False and b.browser_session_used is False
    assert b.public_url_created is False and b.metrics_created is False
    assert b.publication_ready is False and b.dispatch_allowed is False
    assert b.runtime_truth is False and b.human_review_required is True
    for key in ("operator_intent_packet", "research_grounding_packet", "canonical_article_review_packet", "seo_editorial_packet", "discord_drop_candidate_packet", "platform_variant_set_candidate_packet"):
        assert data[key]


def test_request_flags_and_financial_signal_requests_fail_closed():
    for flag in REQUEST_FALSE_FLAGS:
        intent = _intent(); intent[flag] = True
        b = _bundle(intent)
        assert b.eligible_for_future_draft_inspection_task is False
        assert f"operator_intent_{flag}_not_false" in b.blockers


def test_unsafe_topic_text_fails_without_echoing_secret_like_values():
    bad = ("buy", "sell", "hold", "entries", "exits", "targets", "position sizing", "guaranteed prediction", "fake metrics", "fake public URL", "webhook", "endpoint", "signal service")
    for text in bad:
        intent = _intent(); intent["raw_operator_topic"] = text
        try:
            _bundle(intent)
        except ValueError as exc:
            assert "forbidden_text" in str(exc)
        else:
            raise AssertionError(text)
    intent = _intent(); intent["raw_operator_topic"] = "https://discord.com/api/webhooks/x/y"
    try:
        _bundle(intent)
    except ValueError as exc:
        assert "forbidden_value" in str(exc) and "discord.com" not in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_research_preserves_missing_evidence_and_publication_false():
    b = _bundle(); r = b.research_grounding_packet
    assert r["missing_evidence"]
    assert r["allowed_for_drafting"] is True
    assert r["allowed_for_publication"] is False
    assert r["human_review_required"] is True
    r["allowed_for_publication"] = True
    assert "research_allowed_for_publication_not_false" in core._research_blockers(r)


def test_article_rules_fail_closed():
    a = _bundle().canonical_article_review_packet
    a["limitations"] = []
    assert "article_limitations_missing" in core._article_blockers(a)
    a = _bundle().canonical_article_review_packet; a["disclosure"] = ""
    assert "article_disclosure_missing" in core._article_blockers(a)
    for field, text in (("body_markdown", "buy"), ("title", "fake citation"), ("lede", "https://example.test")):
        a = _bundle().canonical_article_review_packet; a[field] = text
        try:
            core._assert_safe(a, "article")
        except ValueError:
            pass
        else:
            raise AssertionError(field)


def test_seo_rules_fail_closed():
    seo = _bundle().seo_editorial_packet
    seo["limitations_preserved"] = False
    assert "seo_limitations_preserved_not_true" in core._seo_blockers(seo)
    seo = _bundle().seo_editorial_packet; seo["caveats_preserved"] = False
    assert "seo_caveats_preserved_not_true" in core._seo_blockers(seo)
    seo = _bundle().seo_editorial_packet; seo["rejected_clickbait"] = ""
    assert "seo_rejected_clickbait_missing" in core._seo_blockers(seo)


def test_discord_drop_rules_fail_closed():
    d = _bundle().discord_drop_candidate_packet
    d["discussion_question"] = ""
    assert "discord_discussion_question_missing" in core._discord_blockers(d)
    d = _bundle().discord_drop_candidate_packet; d["disclosure"] = ""
    assert "discord_disclosure_missing" in core._discord_blockers(d)
    d = _bundle().discord_drop_candidate_packet; d["publication_ready"] = True
    assert "discord_publication_ready_not_false" in core._discord_blockers(d)
    d = _bundle().discord_drop_candidate_packet; d["dispatch_allowed"] = True
    assert "discord_dispatch_allowed_not_false" in core._discord_blockers(d)


def test_platform_variants_manual_deferred_and_not_ready():
    v = _bundle().platform_variant_set_candidate_packet
    assert all(x is False for x in v["execution_readiness_by_platform"].values())
    assert v["manual_fallback_by_platform"]["x_manual"] is True
    assert "linkedin_org_deferred" in v["deferred_platforms"]
    assert "tiktok_deferred" in v["deferred_platforms"]
    v["execution_readiness_by_platform"]["discord"] = True
    assert "variant_execution_readiness_not_all_false" in core._variant_blockers(v)


def test_deterministic_ids_hashes_and_cli(tmp_path):
    assert _bundle().packet_sha256 == _bundle().packet_sha256
    intent = tmp_path / "intent.json"; out1 = tmp_path / "out1.json"; out2 = tmp_path / "out2.json"
    intent.write_text(json.dumps(_intent()), encoding="utf-8")
    assert main(["--operator-intent", str(intent), "--output", str(out1)]) == 0
    assert main(["--operator-intent", str(intent), "--output", str(out2)]) == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"; out = tmp_path / "out.json"
    bad.write_text("[]", encoding="utf-8")
    assert main(["--operator-intent", str(bad), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_draft_inspection_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/content_production_core_review_packets_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_runbook_sample_hygiene():
    paths = [
        "docs/runbooks/V6_CONTENT_PRODUCTION_CORE_OPERATOR_RUNBOOK_NO_PROVIDER_NO_SEND.md",
        "docs/automation/V6_CONTENT_PRODUCTION_CORE_REVIEW_PACKETS_HEAVY_BATCH_NO_PROVIDER_NO_SEND/implementation_report.md",
        "docs/automation/V6_CONTENT_PRODUCTION_CORE_REVIEW_PACKETS_HEAVY_BATCH_NO_PROVIDER_NO_SEND/content_production_core_review_packets_contract.md",
        "docs/automation/V6_CONTENT_PRODUCTION_CORE_REVIEW_PACKETS_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_content_production_core_review_bundle.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    txt = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "no provider" in txt and "no live send" in txt and "no publication readiness" in txt and "review-only" in txt
