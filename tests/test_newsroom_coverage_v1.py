import json

import pytest

from live_contentops.newsroom_coverage_v1 import weekly_newsroom_coverage, render_coverage_digest
from live_contentops.native_newsroom_volume_v1 import volume_policy, bound_volume_policy
from live_contentops.v1_simple_evidence_resolver_v1 import SimpleFirstPartyAwareEvidenceResolver


def test_expanded_cap_selects_only_new_bindings_and_preserves_issued_ten():
    before = volume_policy("2026-10-30T10:00:00Z")
    after = volume_policy("2026-10-31T10:00:00Z")
    assert before["source_request_limit"] == 10 and after["source_request_limit"] == 20
    assert bound_volume_policy({"cutoff_utc": "2026-10-31T10:00:00Z", "volume_policy": before}) == before
    assert bound_volume_policy({"cutoff_utc": "2026-10-31T10:00:00Z", "volume_policy": after}) == after
    with pytest.raises(ValueError, match="POLICY_BINDING_INVALID"):
        bound_volume_policy({"cutoff_utc": "2026-10-30T10:00:00Z", "volume_policy": after})
    with pytest.raises(ValueError):
        SimpleFirstPartyAwareEvidenceResolver(evaluation_as_of_utc="2026-10-31T10:00:00Z", max_requests=20)
    resolver = SimpleFirstPartyAwareEvidenceResolver(evaluation_as_of_utc="2026-10-31T10:00:00Z",
        max_requests=20, non_chargeable_only=True)
    resolver.resume_request_count(19)
    with pytest.raises(ValueError):
        resolver.resume_request_count(21)


def row(key, value, *, work="run", destination="internal:native-desktop-editorial", clock="2026-10-30T10:00:00Z"):
    return {"message_id": key, "work_item_id": work, "destination": destination,
        "created_at": clock, "payload": json.dumps(value)}


def test_weekly_digest_counts_real_news_all_headlines_and_candidate_walks():
    news = {"classification": "INDEPENDENT_NEWS_DRAFT", "qualified_article_count": 1,
        "simple_result": {"run_id": "news"}}
    main = {"report_id": "main-card", "qualified_article_count": 1, "simple_result": {"run_id": "main"}}
    filtered = {"output": {"schema_version": "contentops.native_headline_filter.v1",
        "decisions": [{"input_sha256": "a"}, {"input_sha256": "b"}]},
        "invocation_observation": {"model": "gpt-6-luna", "reasoning_effort": "max"}}
    outbox = [row("cc-editorial-final-news", news), row("cc-editorial-final-main", main),
        row("native-return", filtered), row("same-input-replay", filtered),
        row("public-news", {}, work="news", destination="substack"),
        row("public-main", {}, work="main", destination="substack")]
    for key, stage, status in [("a-failed", "source:a", "BLOCKED"), ("a-recovery", "source:a:recovery", "PASS"),
                                ("b-failed", "source:b", "BLOCKED")]:
        outbox.append(row(key, {"stage": stage, "result": {"status": status,
            "evidence_documents": [{}] if status == "PASS" else []}},
            destination="internal:cc-report-editorial-stage", clock="2026-10-30T10:01:00Z" if status == "PASS" else "2026-10-30T10:00:00Z"))
    dispatches = [{"dispatch_id": "dispatch_" + x, "message_id": "public-" + x,
        "platform": "substack", "status": "DISPATCH_CONFIRMED", "public_object_id": x,
        "public_object_url": "https://capitalchronicle.substack.com/p/" + x,
        "dispatched_at": "2026-10-30T18:00:00Z"} for x in ("news", "main")]
    reconciliations = [{"reconciliation_id": "reconciliation_" + x, "status": "RECONCILED_CONFIRMED"} for x in ("news", "main")]
    readbacks = [{"dispatch_id": "dispatch_" + x, "readback_data": '{"verified":true}'} for x in ("news", "main")]
    result = weekly_newsroom_coverage(outbox=outbox, dispatches=dispatches, reconciliations=reconciliations,
        readbacks=readbacks, week_ending="2026-10-30")
    last = result["daily"][-1]
    # 01:00 on 31 October belongs to production day 30 October.
    assert last["news_articles"] == last["main_articles"] == 1
    assert last["luna_headlines_filtered"] == 2
    assert last["source_walks"] == 2 and last["source_walks_succeeded"] == 1
    assert result["source_walk_success_rate"] == 0.5
    assert "50.0%" in render_coverage_digest(result)
    assert not result["public_write_performed"] and result["model_calls"] == 0


def test_no_observation_is_unavailable_and_unverified_model_is_named():
    unknown = {"output": {"schema_version": "contentops.native_headline_filter.v1", "decisions": []},
        "invocation_observation": {"model": None, "reasoning_effort": None}}
    result = weekly_newsroom_coverage(outbox=[row("unknown", unknown)], dispatches=[], reconciliations=[],
        readbacks=[], week_ending="2026-10-30")
    assert result["source_walk_success_rate"] is None
    assert result["gaps"][0]["cause"] == "LUNA_ACTUAL_MODEL_OR_EFFORT_UNVERIFIED"
    assert "UNAVAILABLE" in render_coverage_digest(result)


def test_a_reused_earlier_decision_is_not_new_weekly_filter_work():
    value = {"output": {"schema_version": "contentops.native_headline_filter.v1",
        "decisions": [{"input_sha256": "unchanged"}]},
        "invocation_observation": {"model": "gpt-6-luna", "reasoning_effort": "max"}}
    result = weekly_newsroom_coverage(outbox=[row("later", value), row("earlier", value, clock="2026-10-23T10:00:00Z")],
        dispatches=[], reconciliations=[], readbacks=[], week_ending="2026-10-30")
    assert sum(r["luna_headlines_filtered"] for r in result["daily"]) == 0


@pytest.mark.parametrize("host,path", [
    ("www.federalreserve.gov", "/newsevents/pressreleases/bcreg20261030a.htm"),
    ("www.cftc.gov", "/PressRoom/PressReleases/controlled"),
    ("www.bls.gov", "/opub/ted/2026/controlled.htm"),
    ("www.eia.gov", "/outlooks/steo/report/controlled.php"),
])
def test_expanded_agency_routes_keep_exact_policy_and_authorship_gate(tmp_path, host, path):
    from hashlib import sha256
    from live_contentops.contentops_source_research_v1 import POLICIES, RetainedSourceResearch
    from live_contentops.official_primary_evidence_loader_v1 import _html_canonical_visible_text
    # Synthetic source and permission text exercise routing, not real rights proof.
    raw = b"<html><body>Controlled agency release fixture.</body></html>"
    text = _html_canonical_visible_text(raw.decode())
    policy = ("CONTROLLED TEST ONLY: " + "; ".join(POLICIES[host][1])).encode()
    (tmp_path / "capture.html").write_bytes(raw)
    (tmp_path / "policy.html").write_bytes(policy)
    family = {"www.federalreserve.gov": "official_policy", "www.cftc.gov": "official_regulatory_fiscal"}.get(host, "official_macro")
    doc = {"source_url": "https://" + host + path, "raw_sha256": sha256(raw).hexdigest(),
        "canonical_content_text": text, "source_adapter_family": family,
        "publisher": "Controlled agency fixture", "source_authority_class": "official_public_primary_source",
        "published_at_utc": "2026-10-30T00:00:00Z"}
    (tmp_path / "loader.json").write_text(json.dumps({"status": "PASS", "official_source_documents": [doc],
        "provenance": {"retrieved_at_utc": "2026-10-30T01:00:00Z"}}))
    spec = {"headline_id": "controlled", "headline_text": text, "capture_path": "capture.html",
        "policy_capture_path": "policy.html", "loader_result_path": "loader.json", "policy_url": POLICIES[host][0],
        "policy_capture_sha256": sha256(policy).hexdigest(), "source_capture_sha256": sha256(raw).hexdigest(),
        "proposition_span": [0, len(text)], "policy_retrieved_at_utc": "2026-10-30T01:00:00Z"}
    index = {"schema_version": "contentops.retained_source_research.v1", "records": [spec]}
    (tmp_path / "index.json").write_text(json.dumps(index))
    accepted = RetainedSourceResearch(tmp_path)
    assert len(accepted.records) == 1 and not accepted.gaps
    assert next(iter(accepted.records.values()))["source_permissions"]["scope"] == "AGENCY_AUTHORED_TEXT_ONLY_EXCLUDES_LOGOS_PHOTOS_THIRD_PARTY"
    (tmp_path / "policy.html").write_bytes(b"Missing rights evidence")
    rejected = RetainedSourceResearch(tmp_path)
    assert not rejected.records and rejected.gaps
