from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)
from live_contentops.newsroom_production_day_v1 import (
    load_qualified_article_records,
    newsroom_production_day_id,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    ARTICLE_SCHEMA_VERSION,
    SELECTION_SCHEMA_VERSION,
    MAX_SOURCE_REQUESTS,
    SimpleGeminiNewsroomError,
    run_v1_simple_gemini_newsroom,
)

CUTOFF = "2026-08-26T14:00:00Z"
SOURCE_URL = "https://www.reuters.com/technology/nvidia-financing-plan"
TITLE = "Nvidia financing plan leaves commitment details undisclosed"
DEK = "Nvidia described a large financing plan but did not disclose individual commitments or a deployment timetable."
SOURCE_TEXT = (
    "Nvidia financing plan leaves commitment details undisclosed. "
    "Nvidia described a large financing plan but did not disclose individual commitments or a deployment timetable. "
    "The company said the financing framework would support data centres, chip factories and power infrastructure. "
    "The disclosed aggregate scale did not include project-by-project funding schedules."
)


def _rolling_input():
    return {
        "schema_version": "test.rolling_input.v1",
        "headlines": [
            {
                "headline_id": "headline-selected",
                "headline_text": "Nvidia outlines financing framework for AI infrastructure",
                "source_timestamp_utc": "2026-08-26T13:40:00Z",
                "source_account": "wire",
                "source_url": SOURCE_URL,
            },
            {
                "headline_id": "headline-other",
                "headline_text": "Taiwan sets a new defence budget proposal",
                "source_timestamp_utc": "2026-08-26T13:35:00Z",
                "source_account": "wire",
                "source_url": "https://www.reuters.com/world/asia-pacific/taiwan-budget",
            },
            {
                "headline_id": "headline-published",
                "headline_text": "Already published exact title",
                "source_timestamp_utc": "2026-08-26T13:30:00Z",
                "source_account": "wire",
                "source_url": "https://www.reuters.com/world/published",
            },
        ],
    }


def _selection(candidate_id: str):
    return {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "status": "SELECT_STORY",
        "selected_candidate_id": candidate_id,
        "article_mode": "STANDARD_NEWS_ANALYSIS",
        "selection_rationale": "The financing terms are useful and current.",
        "research_queries": ["Nvidia financing plan commitments infrastructure"],
        "public_write_attempted": False,
    }


def _article_output(*, bad_excerpt: bool = False):
    paragraph_one = (
        "Nvidia described a large financing plan but did not disclose individual commitments or a deployment timetable. "
        "[[SOURCE:SOURCE_1]]"
    )
    paragraph_two = (
        "The company said the financing framework would support data centres, chip factories and power infrastructure. "
        "[[SOURCE:SOURCE_1]]"
    )
    return {
        "schema_version": ARTICLE_SCHEMA_VERSION,
        "article": {
            "title": TITLE,
            "dek": DEK,
            "search_title": "Nvidia financing plan: what remains undisclosed",
            "meta_description": "The disclosed financing framework still leaves individual commitments and deployment timing unclear.",
            "social_hook": "The headline number is large; the missing commitment detail is more important.",
            "substack_body_markdown": "## What was announced\n\n" + paragraph_one + "\n\n## What remains unclear\n\n" + paragraph_two,
        },
        "cited_sources": [
            {
                "source_id": "SOURCE_1",
                "url": SOURCE_URL,
                "publisher": "Reuters",
                "published_at_utc": "2026-08-26T13:20:00Z",
            }
        ],
        "material_claim_bindings": [
            {
                "claim_id": "claim-title",
                "claim_text": TITLE,
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": TITLE,
                "attribution_required": True,
            },
            {
                "claim_id": "claim-dek",
                "claim_text": DEK,
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": "not in source" if bad_excerpt else DEK,
                "attribution_required": True,
            },
            {
                "claim_id": "claim-infra",
                "claim_text": "The company said the financing framework would support data centres, chip factories and power infrastructure.",
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": "The company said the financing framework would support data centres, chip factories and power infrastructure.",
                "attribution_required": True,
            },
        ],
        "public_write_attempted": False,
    }


def _evidence_result(request_count: int = 1):
    return {
        "status": "PASS",
        "blockers": [],
        "evidence_documents": [
            {
                "document_id": "doc-reuters-nvidia",
                "publisher": "Reuters",
                "source_identity": "reuters.com",
                "source_url": SOURCE_URL,
                "reader_source_url": SOURCE_URL,
                "published_at_utc": "2026-08-26T13:20:00Z",
                "published_at_source": "PUBLISHER_BYTES_OR_HEADERS",
                "canonical_content_sha256": "a" * 64,
                "canonical_content_text": SOURCE_TEXT,
                "public_claim_allowed": True,
            }
        ],
        "provenance": {
            "request_count_for_call": request_count,
            "request_limit": MAX_SOURCE_REQUESTS,
            "network_reads_avoided_for_call": 0,
        },
    }


def _receipt(role: str):
    return {
        "schema_version": "contentops.nine_router_ordered_model_router.v2",
        "logical_invocation_id": role,
        "role_task_id": role,
        "terminal_disposition": "ACCEPTED",
        "selected_model": "vx/gemini-3.1-pro-preview(high)",
        "models_attempted_in_order": ["vx/gemini-3.1-pro-preview(high)"],
        "total_attempts": 1,
        "total_fallback_transitions": 0,
        "total_usage": {"total_tokens": 100},
        "total_cost": {},
        "model_identity_provider_verifiable": True,
        "public_write_attempted": False,
    }


def test_one_selected_story_reaches_two_gemini_calls_then_exact_eight_zero_write_intents(tmp_path: Path):
    events: list[str] = []
    selected_candidate_id: list[str] = []

    def llm_invoke(**kwargs):
        role = kwargs["role_task_id"]
        events.append("llm:" + role)
        governed = kwargs["governed_input"]
        if role == "rolling_x_newsroom_assignment":
            candidates = governed["candidates"]
            assert len(candidates) == 2
            assert all(row["headline_id"] != "headline-published" for row in candidates)
            candidate_id = next(
                row["candidate_id"]
                for row in candidates
                if row["headline_id"] == "headline-selected"
            )
            selected_candidate_id.append(candidate_id)
            return _selection(candidate_id), _receipt(role)
        assert role == "article_writing"
        assert events == ["llm:rolling_x_newsroom_assignment", "evidence", "llm:article_writing"]
        assert governed["selected_candidate"]["candidate_id"] == selected_candidate_id[0]
        assert len(governed["source_pack"]) == 1
        return _article_output(), _receipt(role)

    def evidence_loader(request):
        events.append("evidence")
        assert events == ["llm:rolling_x_newsroom_assignment", "evidence"]
        assert request["cluster_id"] == selected_candidate_id[0]
        assert request["headline_ids"] == ["headline-selected"]
        return _evidence_result()

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input=_rolling_input(),
        published_memory=[{"title": "Already published exact title"}],
        llm_invoke=llm_invoke,
        evidence_loader=evidence_loader,
        run_id="window-test",
    )

    assert result["classification"] == "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE"
    assert result["logical_model_invocation_count"] == 2
    assert result["codex_runtime_model_call_count"] == 0
    assert result["source_request_count"] == 1
    assert result["qualified_article_count"] == 1
    assert result["derivative_intent_count"] == 8
    assert result["public_write_performed"] is False
    assert result["unknown_write_count"] == 0
    intents = json.loads((tmp_path / "derivative_intents_v1.json").read_text())
    assert {row["destination"] for row in intents["intents"]} == set(
        V1_REQUIRED_DERIVATIVE_DESTINATIONS
    )
    assert all(row["dispatch_state"] == "UNDISPATCHED" for row in intents["intents"])
    records = load_qualified_article_records(
        tmp_path,
        production_day_id=newsroom_production_day_id(CUTOFF),
    )
    assert len(records) == 1
    assert records[0]["editorial_worker"]["provider"] == "9router"
    assert records[0]["editorial_worker"]["model"] == "vx/gemini-3.1-pro-preview(high)"


def test_one_validation_failure_allows_exactly_one_gemini_revision(tmp_path: Path):
    roles: list[str] = []

    def llm_invoke(**kwargs):
        role = kwargs["role_task_id"]
        roles.append(role)
        if role == "rolling_x_newsroom_assignment":
            candidate_id = kwargs["governed_input"]["candidates"][0]["candidate_id"]
            return _selection(candidate_id), _receipt(role)
        if role == "article_writing":
            return _article_output(bad_excerpt=True), _receipt(role)
        assert role == "rolling_x_editorial_revision"
        assert "material_claim_excerpt_not_verified:claim-dek" in kwargs["prompt"]
        return _article_output(), _receipt(role)

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input={"headlines": [_rolling_input()["headlines"][0]]},
        llm_invoke=llm_invoke,
        evidence_loader=lambda _request: _evidence_result(),
        run_id="window-revision",
    )

    assert result["classification"] == "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE"
    assert result["revision_performed"] is True
    assert result["logical_model_invocation_count"] == 3
    assert roles == [
        "rolling_x_newsroom_assignment",
        "article_writing",
        "rolling_x_editorial_revision",
    ]


def test_second_validation_failure_abstains_without_fourth_model_call(tmp_path: Path):
    roles: list[str] = []

    def llm_invoke(**kwargs):
        role = kwargs["role_task_id"]
        roles.append(role)
        if role == "rolling_x_newsroom_assignment":
            candidate_id = kwargs["governed_input"]["candidates"][0]["candidate_id"]
            return _selection(candidate_id), _receipt(role)
        return _article_output(bad_excerpt=True), _receipt(role)

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input={"headlines": [_rolling_input()["headlines"][0]]},
        llm_invoke=llm_invoke,
        evidence_loader=lambda _request: _evidence_result(),
        run_id="window-revision-fail",
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "SINGLE_GEMINI_REVISION_EXHAUSTED"
    assert result["logical_model_invocation_count"] == 3
    assert result["qualified_article_count"] == 0
    assert roles.count("rolling_x_editorial_revision") == 1


def test_source_budget_blocks_before_writer_and_never_spawns_codex(tmp_path: Path):
    roles: list[str] = []

    def llm_invoke(**kwargs):
        role = kwargs["role_task_id"]
        roles.append(role)
        candidate_id = kwargs["governed_input"]["candidates"][0]["candidate_id"]
        return _selection(candidate_id), _receipt(role)

    with pytest.raises(SimpleGeminiNewsroomError) as exc_info:
        run_v1_simple_gemini_newsroom(
            output_dir=tmp_path,
            cutoff_utc=CUTOFF,
            rolling_input={"headlines": [_rolling_input()["headlines"][0]]},
            llm_invoke=llm_invoke,
            evidence_loader=lambda _request: _evidence_result(MAX_SOURCE_REQUESTS + 1),
            run_id="window-budget",
        )

    assert exc_info.value.code == "selected_story_source_request_budget_exceeded"
    assert roles == ["rolling_x_newsroom_assignment"]


def test_module_has_no_codex_runtime_dependency():
    path = Path(__file__).parents[1] / "live_contentops" / "v1_simple_gemini_newsroom_v1.py"
    text = path.read_text(encoding="utf-8").casefold()
    assert "official_codex" not in text
    assert "codex_desktop" not in text
    assert "officialcodexeditorialsession" not in text
