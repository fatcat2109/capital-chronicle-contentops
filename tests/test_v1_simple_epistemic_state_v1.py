from __future__ import annotations

from datetime import datetime, timezone

import pytest
import json

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)
from live_contentops.v1_simple_epistemic_state_v1 import (
    build_epistemic_state,
    candidate_report_provenance,
    trusted_relay_document,
    validate_epistemic_state,
)
from live_contentops.v1_simple_evidence_resolver_v1 import (
    SimpleFirstPartyAwareEvidenceResolver,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    ARTICLE_SCHEMA_VERSION,
    SimpleGeminiNewsroomError,
    _native_preview_bundle,
    _validate_article_against_source_pack,
    run_v1_simple_gemini_newsroom,
)
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_V1_SIMPLE_ARTICLE_WRITING,
    ROLE_V1_SIMPLE_SELECTION,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import SELECTION_SCHEMA_VERSION


CUTOFF = "2026-08-28T01:00:00Z"
NOW = datetime(2026, 8, 28, 1, 1, tzinfo=timezone.utc)
WSJ_URL = "https://www.wsj.com/articles/nvidia-ai-cloud-revenue-sharing-pause"
WSJ_EVENT = "Nvidia has paused parts of its AI cloud revenue-sharing program"
WSJ_BYTES = f"""<html><head><title>{WSJ_EVENT}</title>
<meta property="article:published_time" content="2026-08-27T21:30:00Z"></head>
<body><p>{WSJ_EVENT}, according to people familiar with the matter.</p>
<p>The change affects credit support for smaller cloud providers.</p></body></html>""".encode()
REUTERS_REPORT_URL = "https://www.reuters.com/business/acme-financing-review"
AP_REPORT_URL = "https://apnews.com/article/acme-financing-review"
REUTERS_REPORT_TITLE = "Acme is reviewing its financing strategy"


def _response(url: str, body: bytes):
    return {
        "status": 200,
        "final_url": url,
        "headers": {"content-type": "text/html"},
        "body": body,
    }


def _candidate(*, account: str = "wallstengine") -> dict[str, object]:
    return {
        "candidate_id": "simple-story-nvda-report",
        "story_identity": "simple-story-nvda-report",
        "headline_id": "headline-nvda-report",
        "headline_text": f"{WSJ_EVENT}, per WSJ.",
        "source_timestamp_utc": "2026-08-27T21:51:04Z",
        "source_account": account,
        "source_url": f"https://x.com/{account}/status/1",
        "official_source_urls": [],
        "public_source_urls": [WSJ_URL],
    }


def _request(candidate: dict[str, object], *, source_url: str = WSJ_URL):
    profile = candidate_report_provenance(candidate)
    return {
        "cluster_id": candidate["candidate_id"],
        "headline_ids": [candidate["headline_id"]],
        "request_logical_hash": "report-request-hash",
        "story_evidence_scope_id": candidate["candidate_id"],
        "story_type": "selected_current_news",
        "required_evidence_capabilities": [
            "credible_report_or_event_confirmation",
            "basic_attributed_facts",
        ],
        "story_context": {
            "leaf_summaries": [candidate["headline_text"]],
            "grounded_research_queries": [
                "Nvidia AI cloud revenue sharing program WSJ"
            ],
            "candidate_source_timestamp_utc": candidate["source_timestamp_utc"],
            "report_provenance": profile,
            "public_source_url_bindings": [
                {
                    "headline_id": candidate["headline_id"],
                    "url": source_url,
                    "source_timestamp_utc": candidate["source_timestamp_utc"],
                }
            ],
        },
    }


def _source_pack() -> list[dict[str, object]]:
    text = WSJ_BYTES.decode()
    return [
        {
            "source_id": "SOURCE_1",
            "url": WSJ_URL,
            "publisher": "The Wall Street Journal",
            "published_at_utc": "2026-08-27T21:30:00Z",
            "published_at_source": "PUBLISHER_BYTES_OR_HEADERS",
            "document_id": "wsj-report-doc",
            "source_identity": "wsj.com",
            "source_authority_class": "reputable_secondary_source",
            "canonical_content_sha256": "a" * 64,
            "canonical_content_text": text,
        }
    ]


def _state() -> dict[str, object]:
    state, blockers = build_epistemic_state(
        request=_request(_candidate()),
        documents=[
            {
                **_source_pack()[0],
                "source_url": WSJ_URL,
                "public_claim_allowed": True,
            }
        ],
        selected_route="REPUTABLE_SECONDARY",
    )
    assert blockers == []
    assert state is not None
    return state


def _article_output(state: dict[str, object]) -> dict[str, object]:
    label = str(state["reader_visible_epistemic_label"])
    title = "The Wall Street Journal reports Nvidia paused part of an AI cloud support program"
    dek = f"{label}: the reported pullback puts smaller GPU-cloud financing under a harsher spotlight."
    search = "Wall Street Journal report on Nvidia AI cloud support pause"
    meta = "The Wall Street Journal reports an Nvidia AI cloud support pause; the event remains unconfirmed."
    social = "The Wall Street Journal report points to a sharper financing test for smaller AI clouds."
    opening = (
        f"{label}: The Wall Street Journal reports that Nvidia paused parts of its AI cloud "
        "revenue-sharing program. [[SOURCE:SOURCE_1]]"
    )
    analysis = (
        "If the report is accurate, smaller providers may face a tougher financing constraint "
        "just as GPU capacity remains expensive. [[SOURCE:SOURCE_1]]"
    )
    article = {
        "title": title,
        "dek": dek,
        "search_title": search,
        "meta_description": meta,
        "social_hook": social,
        "substack_body_markdown": opening + "\n\n" + analysis,
    }
    excerpt = WSJ_EVENT
    claims = [
        {
            "claim_id": f"claim-{field}",
            "claim_text": value,
            "claim_kind": "FACT",
            "source_id": "SOURCE_1",
            "support_excerpt": excerpt,
            "attribution_required": True,
        }
        for field, value in article.items()
        if field != "substack_body_markdown"
    ]
    claims.extend(
        [
            {
                "claim_id": "claim-opening",
                "claim_text": opening.replace(" [[SOURCE:SOURCE_1]]", ""),
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": excerpt,
                "attribution_required": True,
            },
            {
                "claim_id": "claim-analysis",
                "claim_text": analysis.replace(" [[SOURCE:SOURCE_1]]", ""),
                "claim_kind": "CAUSALITY",
                "source_id": "SOURCE_1",
                "support_excerpt": "credit support for smaller cloud providers",
                "attribution_required": True,
            },
        ]
    )
    return {
        "schema_version": ARTICLE_SCHEMA_VERSION,
        "article": article,
        "cited_sources": [
            {
                "source_id": "SOURCE_1",
                "url": WSJ_URL,
                "publisher": "The Wall Street Journal",
                "published_at_utc": "2026-08-27T21:30:00Z",
            }
        ],
        "material_claim_bindings": claims,
        "public_write_attempted": False,
    }


def test_per_wsj_routes_report_first_and_does_not_call_generic_nvidia_official():
    calls: list[str] = []

    def get(url, *_args):
        calls.append(url)
        assert "nvidianews.nvidia.com" not in url
        assert url == WSJ_URL
        return _response(url, WSJ_BYTES)

    result = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )(_request(_candidate()))

    assert result["status"] == "PASS"
    assert calls == [WSJ_URL]
    assert result["provenance"]["selected_route"] == "REPUTABLE_SECONDARY"
    state = result["epistemic_state"]
    assert state["evidence_basis"] == "DIRECT_REPUTABLE_REPORT"
    assert state["event_confirmation_state"] == "UNCONFIRMED"
    assert state["source_multiplicity"] == "SINGLE_SOURCE"
    assert state["origin_character"] == "ANONYMOUS_OR_INTERNAL_SOURCES"
    assert state["event_truth_supported"] is False


def test_unrelated_aws_nvidia_release_neither_confirms_nor_disproves_report():
    unrelated = {
        "document_id": "nvidia-aws-release",
        "publisher": "NVIDIA",
        "source_identity": "nvidianews.nvidia.com",
        "source_authority_class": "official_public_primary_source",
        "source_url": "https://nvidianews.nvidia.com/news/aws-expansion",
        "canonical_content_text": "AWS and NVIDIA announced an expansion of GPU infrastructure.",
        "public_claim_allowed": True,
    }
    state, blockers = build_epistemic_state(
        request=_request(_candidate()),
        documents=[unrelated],
        selected_route="OFFICIAL_PRIMARY",
    )
    assert state is None
    assert "epistemic_selected_event_not_supported_by_route" in blockers


def test_one_secondary_ordinary_report_passes_but_high_harm_allegation_does_not():
    assert validate_epistemic_state(_state()) == []
    candidate = _candidate()
    candidate["headline_text"] = (
        "Example Company allegedly concealed fatal product defects, per WSJ."
    )
    state, blockers = build_epistemic_state(
        request=_request(candidate),
        documents=[
            {
                "document_id": "wsj-high-harm",
                "publisher": "The Wall Street Journal",
                "source_identity": "wsj.com",
                "source_authority_class": "reputable_secondary_source",
                "source_url": WSJ_URL,
                "canonical_content_text": candidate["headline_text"],
                "public_claim_allowed": True,
            }
        ],
        selected_route="REPUTABLE_SECONDARY",
    )
    assert state is None
    assert blockers == ["epistemic_high_harm_single_source_insufficient"]


def test_unconfirmed_copy_cannot_inflate_certainty_or_invent_origin_labels():
    state = _state()
    output = _article_output(state)
    output["article"]["title"] = "Nvidia paused part of its AI cloud support program"
    with pytest.raises(SimpleGeminiNewsroomError) as exc_info:
        _validate_article_against_source_pack(
            output,
            _source_pack(),
            selected_candidate=_candidate(),
            article_mode="STANDARD_NEWS_ANALYSIS",
            epistemic_state=state,
        )
    assert any(
        blocker.startswith("epistemic_title_attribution_or_uncertainty_missing")
        or blocker.startswith("epistemic_certainty_inflation:title")
        for blocker in exc_info.value.details
    )

    output = _article_output(state)
    output["article"]["substack_body_markdown"] += (
        "\n\nThe leaked plan would alter financing incentives. [[SOURCE:SOURCE_1]]"
    )
    with pytest.raises(SimpleGeminiNewsroomError) as origin_exc:
        _validate_article_against_source_pack(
            output,
            _source_pack(),
            selected_candidate=_candidate(),
            article_mode="STANDARD_NEWS_ANALYSIS",
            epistemic_state={**state, "origin_character": "UNSPECIFIED"},
        )
    assert "epistemic_unsupported_leak_label" in origin_exc.value.details


def test_exact_eight_previews_preserve_machine_and_reader_visible_epistemic_state():
    state = _state()
    article, validation = _validate_article_against_source_pack(
        _article_output(state),
        _source_pack(),
        selected_candidate=_candidate(),
        article_mode="STANDARD_NEWS_ANALYSIS",
        epistemic_state=state,
    )
    assert validation["status"] == "PASS"
    bundle, intents = _native_preview_bundle(
        article=article,
        article_mode="STANDARD_NEWS_ANALYSIS",
        article_identity="b" * 64,
        epistemic_state=state,
    )
    assert set(bundle["packages"]) == set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert bundle["package_count"] == 8
    assert bundle["every_preview_preserves_epistemic_state"] is True
    label = str(state["reader_visible_epistemic_label"])
    assert all(label in str(payload) for payload in bundle["packages"].values())
    assert all(row["epistemic_state"] == state for row in intents)
    assert all(row["dispatch_state"] == "UNDISPATCHED" for row in intents)


def test_no_current_x_relay_has_report_truth_authority():
    # ``financialjuice`` is an existing freshness-only professional-feed donor. Current code
    # explicitly leaves its text discovery-only, so it cannot be promoted into report truth.
    for account in ("financialjuice", "FirstSquawk", "DeItaone", "wallstengine"):
        candidate = _candidate(account=account)
        request = _request(candidate, source_url=candidate["source_url"])
        assert request["story_context"]["report_provenance"][
            "trusted_relay_identity_approved"
        ] is False
        assert trusted_relay_document(request) is None


@pytest.mark.parametrize(
    ("headline", "publisher"),
    [
        ("Reuters reports that a bank is reviewing its strategy", "Reuters"),
        ("A bank is reviewing its strategy, according to Bloomberg", "Bloomberg"),
        ("A bank is reviewing its strategy, per WSJ", "The Wall Street Journal"),
        (
            "Gulf states are investing in ports and pipelines, Reuters reported Friday.",
            "Reuters",
        ),
    ],
)
def test_existing_attribution_taxonomy_recognizes_explicit_report_forms(
    headline, publisher
):
    profile = candidate_report_provenance(
        {**_candidate(), "headline_text": headline}
    )
    assert profile["explicit_reputable_attribution"] is True
    assert profile["primary_reporting_publisher"] == publisher
    assert profile["report_or_event_authority_granted"] is False
    assert not str(profile["event_proposition"]).casefold().endswith(
        "reported friday"
    )


def test_unsupported_epistemic_enum_fails_closed():
    state = _state()
    assert validate_epistemic_state(
        {**state, "evidence_basis": "MODEL_CONFIDENCE"}
    ) == ["epistemic_evidence_basis_invalid"]


def test_candidate_local_provenance_failure_continues_to_admitted_fallback_same_ledger(
    tmp_path,
):
    first = _candidate()
    second = {
        **_candidate(),
        "candidate_id": "simple-story-fallback",
        "story_identity": "simple-story-fallback",
        "headline_id": "headline-fallback",
        "headline_text": "Nvidia AI cloud revenue-sharing support has a separate current update",
        "source_timestamp_utc": "2026-08-27T21:50:00Z",
    }
    rolling = {"schema_version": "test.v1", "headlines": [first, second]}
    selected_ids: list[str] = []

    state = _state()

    def llm_invoke(**kwargs):
        role = kwargs["role_task_id"]
        if role == ROLE_V1_SIMPLE_SELECTION:
            candidates = kwargs["governed_input"]["candidates"]
            ids = [row["candidate_id"] for row in candidates]
            selected_ids.extend(ids[:2])
            return (
                {
                    "schema_version": SELECTION_SCHEMA_VERSION,
                    "status": "SELECT_CANDIDATE_PLAN",
                    "ordered_candidate_plan": [
                        {
                            "candidate_id": ids[0],
                            "article_mode": "STANDARD_NEWS_ANALYSIS",
                            "selection_rationale": "Useful current attributed report.",
                            "research_queries": ["current attributed report"],
                        },
                        {
                            "candidate_id": ids[1],
                            "article_mode": "STANDARD_NEWS_ANALYSIS",
                            "selection_rationale": "Useful independent fallback story.",
                            "research_queries": ["current fallback story"],
                        },
                    ],
                    "selection_summary": "Two independently useful candidates.",
                    "public_write_attempted": False,
                },
                {
                    "selected_model": "vx/gemini-3.5-flash(high)",
                    "total_attempts": 1,
                    "public_write_attempted": False,
                },
            )
        assert role == ROLE_V1_SIMPLE_ARTICLE_WRITING
        return (
            _article_output(state),
            {
                "selected_model": "vx/gemini-3.5-flash(high)",
                "total_attempts": 1,
                "public_write_attempted": False,
            },
        )

    calls = 0

    def evidence_loader(_request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return {
                "status": "BLOCKED",
                "blockers": ["epistemic_report_provenance_not_governed"],
                "evidence_documents": [],
                "provenance": {"request_count_for_call": 1},
            }
        return {
            "status": "PASS",
            "blockers": [],
            "evidence_documents": [
                {
                    **_source_pack()[0],
                    "source_url": WSJ_URL,
                    "reader_source_url": WSJ_URL,
                    "public_claim_allowed": True,
                }
            ],
            "epistemic_state": state,
            "provenance": {"request_count_for_call": 1},
        }

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input=rolling,
        llm_invoke=llm_invoke,
        evidence_loader=evidence_loader,
        run_id="provenance-fallback",
    )
    assert result["classification"] == "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE"
    assert calls == 2
    assert result["source_request_count"] == 2
    assert [row["status"] for row in result["candidate_attempt_history"]] == [
        "SOURCE_BLOCKED",
        "SOURCE_QUALIFIED",
    ]
    assert result["logical_model_invocation_count"] == 2
    assert result["derivative_intent_count"] == 8
    assert result["codex_runtime_model_call_count"] == 0
    assert result["public_write_performed"] is False
    assert result["unknown_write_count"] == 0
    record = json.loads((tmp_path / "qualified_article_record_v1.json").read_text())
    assert record["epistemic_state"] == state


def test_empty_epistemic_state_does_not_add_noisy_schema_blockers(tmp_path):
    rolling = {
        "schema_version": "test.v1",
        "headlines": [_candidate()],
    }

    def llm_invoke(**kwargs):
        candidate_id = kwargs["governed_input"]["candidates"][0]["candidate_id"]
        return (
            {
                "schema_version": SELECTION_SCHEMA_VERSION,
                "status": "SELECT_CANDIDATE_PLAN",
                "ordered_candidate_plan": [
                    {
                        "candidate_id": candidate_id,
                        "article_mode": "BREAKING_BRIEF",
                        "selection_rationale": "Useful current attributed report.",
                        "research_queries": ["current attributed report"],
                    }
                ],
                "selection_summary": "One useful candidate.",
                "public_write_attempted": False,
            },
            {
                "selected_model": "vx/gemini-3.5-flash(high)",
                "total_attempts": 1,
                "public_write_attempted": False,
            },
        )

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input=rolling,
        llm_invoke=llm_invoke,
        evidence_loader=lambda _request: {
            "status": "BLOCKED",
            "blockers": ["epistemic_report_provenance_not_governed"],
            "evidence_documents": [],
            "epistemic_state": {},
            "provenance": {"request_count_for_call": 1},
        },
        run_id="empty-epistemic-blocked",
    )
    assert result["classification"] == "NO_PUBLICATION"
    blockers = result["candidate_attempt_history"][0]["blockers"]
    assert blockers == ["epistemic_report_provenance_not_governed"]


def _mixed_publisher_rss() -> bytes:
    return f"""<rss><channel>
    <item><title>Acme reviews financing strategy and capital plans - Associated Press</title>
    <link>https://news.google.com/rss/articles/ap-acme</link>
    <pubDate>Fri, 28 Aug 2026 00:50:00 GMT</pubDate>
    <source url="https://apnews.com">Associated Press</source></item>
    <item><title>{REUTERS_REPORT_TITLE} - Reuters</title>
    <link>https://news.google.com/rss/articles/reuters-acme</link>
    <pubDate>Fri, 28 Aug 2026 00:45:00 GMT</pubDate>
    <source url="https://www.reuters.com">Reuters</source></item>
    </channel></rss>""".encode()


def _sitemap(url: str, title: str) -> bytes:
    return f"""<urlset><url><loc>{url}</loc>
    <publication_date>2026-08-28T00:45:00Z</publication_date>
    <title>{title}</title></url></urlset>""".encode()


def _publisher_article(title: str) -> bytes:
    return f"""<html><head><title>{title}</title>
    <meta property="article:published_time" content="2026-08-28T00:45:00Z"></head>
    <body><article><p>{title}.</p>
    <p>The review covers funding terms for future projects.</p></article></body></html>""".encode()


def _rss_request(headline: str) -> dict[str, object]:
    candidate = {
        **_candidate(),
        "headline_text": headline,
        "source_timestamp_utc": "2026-08-28T00:55:00Z",
        "public_source_urls": [],
    }
    request = _request(candidate)
    request["story_context"]["public_source_url_bindings"] = []
    request["story_context"]["grounded_research_queries"] = [
        "Acme reviewing financing strategy"
    ]
    return request


def test_attributed_publisher_pins_mixed_rss_resolution_to_reuters_only():
    calls: list[str] = []

    def get(url, *_args):
        calls.append(url)
        if url.startswith("https://news.google.com/rss/search"):
            return _response(url, _mixed_publisher_rss())
        if url == "https://www.reuters.com/news-sitemap.xml":
            return _response(url, _sitemap(REUTERS_REPORT_URL, REUTERS_REPORT_TITLE))
        if url == REUTERS_REPORT_URL:
            return _response(url, _publisher_article(REUTERS_REPORT_TITLE))
        raise AssertionError(f"unexpected publisher resolution attempt:{url}")

    result = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )(
        _rss_request(
            "Acme is reviewing its financing strategy, REUTERS REPORTED FRIDAY."
        )
    )
    assert result["status"] == "PASS"
    assert len(calls) == 3
    assert not any("apnews.com" in value for value in calls)
    route = result["provenance"]["route_history"][0]
    assert route["attributed_publisher_identity"] == "reuters.com"
    assert route["rss_candidate_publisher_identities_observed"] == [
        "apnews.com",
        "reuters.com",
    ]
    assert route["publisher_identities_eligible_for_resolution"] == [
        "reuters.com"
    ]
    assert route["publisher_resolution_attempted_identities"] == ["reuters.com"]
    assert result["provided_evidence_capabilities"] == [
        "attributed_report_provenance",
        "basic_attributed_facts",
    ]
    assert "credible_event_confirmation" not in result[
        "provided_evidence_capabilities"
    ]
    state = result["epistemic_state"]
    assert state["evidence_basis"] == "DIRECT_REPUTABLE_REPORT"
    assert state["event_confirmation_state"] == "UNCONFIRMED"
    assert state["source_multiplicity"] == "SINGLE_SOURCE"


def test_attributed_reuters_unresolved_does_not_spend_attempt_on_ap():
    calls: list[str] = []

    def get(url, *_args):
        calls.append(url)
        if url.startswith("https://news.google.com/rss/search"):
            return _response(url, _mixed_publisher_rss())
        if url == "https://www.reuters.com/news-sitemap.xml":
            return {"status": 404, "final_url": url, "headers": {}, "body": b""}
        if url == "https://www.reuters.com/robots.txt":
            return _response(url, b"User-agent: *\n")
        raise AssertionError(f"unexpected publisher resolution attempt:{url}")

    result = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )(
        _rss_request(
            "Acme is reviewing its financing strategy, REUTERS REPORTED FRIDAY."
        )
    )
    assert result["status"] == "BLOCKED"
    assert len(calls) == 3
    assert not any("apnews.com" in value for value in calls)
    route = result["provenance"]["route_history"][0]
    assert route["publisher_resolution_attempted_identities"] == ["reuters.com"]


def test_non_attributed_mixed_rss_preserves_generic_relevance_ranking():
    calls: list[str] = []

    def get(url, *_args):
        calls.append(url)
        if url.startswith("https://news.google.com/rss/search"):
            return _response(url, _mixed_publisher_rss())
        if url == "https://apnews.com/news-sitemap.xml":
            return _response(
                url,
                _sitemap(
                    AP_REPORT_URL,
                    "Acme reviews financing strategy and capital plans",
                ),
            )
        if url == AP_REPORT_URL:
            return _response(
                url,
                _publisher_article(
                    "Acme reviews financing strategy and capital plans"
                ),
            )
        raise AssertionError(f"unexpected publisher resolution attempt:{url}")

    result = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )(_rss_request("Acme reviews financing strategy and capital plans"))
    assert result["status"] == "PASS"
    assert any("apnews.com" in value for value in calls)
    route = result["provenance"]["route_history"][0]
    assert route["attributed_publisher_identity"] is None
    assert route["publisher_identities_eligible_for_resolution"] == [
        "apnews.com",
        "reuters.com",
    ]
    assert route["publisher_resolution_attempted_identities"][0] == "apnews.com"
