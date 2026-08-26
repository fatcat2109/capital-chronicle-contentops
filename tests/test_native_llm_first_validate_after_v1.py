from __future__ import annotations

from pathlib import Path

import pytest

import live_contentops.llm_first_validate_after_v1 as llm_first
from live_contentops.native_llm_first_validate_after_v1 import (
    INITIAL_HANDOFF_STATUS,
    REVISION_HANDOFF_STATUS,
    WORKER_RETURN_SCHEMA_VERSION,
    NativeDesktopExternalLlmFirstProvider,
    build_external_worker_request,
    build_same_high_revision_contract,
    selection_for_candidate,
    validate_same_high_revision_contract,
)
from live_contentops.newsroom_assignment_scheduler_v1 import (
    _rolling_x_canonical_hash_material,
)
from live_contentops.native_desktop_production_handoff_v1 import logical_hash


def _binding() -> dict:
    headlines = [
        {
            "headline_id": "headline-primary",
            "source_timestamp_utc": "2026-08-11T14:15:00Z",
            "external_content": {
                "headline_text": "Primary policy event",
                "author_handle": "source_primary",
                "url_or_source_ref": "https://www.federalreserve.gov/newsevents/pressreleases/test.htm",
            },
        },
        {
            "headline_id": "headline-fallback",
            "source_timestamp_utc": "2026-08-11T14:20:00Z",
            "external_content": {
                "headline_text": "Fallback policy event",
                "author_handle": "source_fallback",
                "url_or_source_ref": "https://www.federalreserve.gov/newsevents/pressreleases/fallback.htm",
            },
        },
    ]
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "cutoff_time_utc": "2026-08-11T15:00:00Z",
        "window_start_utc": "2026-08-10T15:00:00Z",
        "window_hours": 24.0,
        "unique_headline_ids": ["headline-primary", "headline-fallback"],
        "headlines": headlines,
        "counts": {
            "accepted_in_full_rolling_intake": 1093,
            "accepted": 2,
            "selected_for_native_llm_first": 2,
        },
    }
    intake["canonical_input_hash"] = logical_hash(
        _rolling_x_canonical_hash_material(intake)
    )
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "assignment_method": "NATIVE_LLM_FIRST_HIGH_SELECTION_FROM_ZERO_MODEL_PREPARED_FRONTIER",
        "input_binding": {
            "canonical_input_hash": intake["canonical_input_hash"],
            "input_ids": ["headline-primary", "headline-fallback"],
            "input_count": 2,
            "selected_count": 2,
            "held_count": 0,
        },
        "ranked_clusters": [
            {
                "cluster_id": "cluster-primary",
                "rank": 1,
                "headline_ids": ["headline-primary"],
                "leaf_cluster_ids": ["leaf-primary"],
                "resolved_article_mode": "STANDARD_NEWS_ANALYSIS",
            },
            {
                "cluster_id": "cluster-fallback",
                "rank": 2,
                "headline_ids": ["headline-fallback"],
                "leaf_cluster_ids": ["leaf-fallback"],
                "resolved_article_mode": "BREAKING_BRIEF",
            },
        ],
        "leaf_clusters": [
            {
                "leaf_cluster_id": "leaf-primary",
                "member_headline_ids": ["headline-primary"],
                "canonical_representative_headline_id": "headline-primary",
            },
            {
                "leaf_cluster_id": "leaf-fallback",
                "member_headline_ids": ["headline-fallback"],
                "canonical_representative_headline_id": "headline-fallback",
            },
        ],
        "selected_cluster_id": "cluster-primary",
        "selected_cluster_ids": ["cluster-primary", "cluster-fallback"],
        "selected_headline_ids": ["headline-primary", "headline-fallback"],
    }
    assignment["assignment_logical_hash"] = logical_hash(assignment)
    resume = {
        "schema_version": "contentops.native_llm_first_assignment_resume.v1",
        "assignment_override": assignment,
        "story_type_by_cluster": {
            "cluster-primary": "general_public_event",
            "cluster-fallback": "general_public_event",
        },
        "selected_cluster_ids": ["cluster-primary", "cluster-fallback"],
        "rolling_input_canonical_hash": intake["canonical_input_hash"],
        "selection_request_logical_hash": "a" * 64,
        "selection_return_logical_hash": "b" * 64,
        "factual_or_numeric_authority_granted": False,
        "publication_authority_granted": False,
    }
    resume["resume_binding_logical_hash"] = logical_hash(resume)
    return {
        "rolling_input_override": intake,
        "assignment_override": assignment,
        "story_type_by_cluster": dict(resume["story_type_by_cluster"]),
        "resume_binding": resume,
        "selected_cluster_id": "cluster-primary",
        "selected_cluster_ids": ["cluster-primary", "cluster-fallback"],
        "article_mode": "STANDARD_NEWS_ANALYSIS",
        "selection_request_logical_hash": "a" * 64,
        "selection_return_logical_hash": "b" * 64,
    }


def _selection() -> dict:
    return {
        "schema_version": "contentops.native_llm_first_selection_return.v1",
        "canonical_opportunity_id": "window-1",
        "selection_request_logical_hash": "a" * 64,
        "selection_return_logical_hash": "b" * 64,
        "selected_cluster_id": "cluster-primary",
        "article_mode": "STANDARD_NEWS_ANALYSIS",
        "selection_rationale": "Primary is the most useful story.",
        "fallback_candidates": [
            {
                "cluster_id": "cluster-fallback",
                "article_mode": "BREAKING_BRIEF",
                "selection_rationale": "Fallback remains independently useful.",
            }
        ],
        "model": "gpt-5.6-sol",
        "reasoning_effort": "HIGH",
        "public_write_attempted": False,
    }


def _article_output() -> dict:
    claim = "The Federal Reserve said the test policy remains unchanged."
    return {
        "article": {
            "title": "Test policy remains unchanged",
            "canonical_editorial_headline": "Test policy remains unchanged",
            "dek": "A bounded test article.",
            "substack_body_markdown": claim + " [[SOURCE:SOURCE_1]]",
        },
        "cited_sources": [
            {
                "source_id": "SOURCE_1",
                "url": "https://www.federalreserve.gov/newsevents/pressreleases/test.htm",
                "publisher": "Federal Reserve",
                "published_at_utc": "2026-08-11T14:15:00Z",
            }
        ],
        "material_claim_bindings": [
            {
                "claim_id": "claim-1",
                "claim_text": claim,
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": claim,
                "attribution_required": True,
            }
        ],
    }


def test_worker_request_preserves_high_primary_then_fallback_plan():
    binding = _binding()
    selection = _selection()
    primary_request, primary, primary_selection = build_external_worker_request(
        binding=binding,
        selection=selection,
        cutoff_utc="2026-08-11T15:00:00Z",
        candidate_index=0,
    )
    fallback_request, fallback, fallback_selection = build_external_worker_request(
        binding=binding,
        selection=selection,
        cutoff_utc="2026-08-11T15:00:00Z",
        candidate_index=1,
    )

    assert primary["cluster_id"] == "cluster-primary"
    assert primary_selection["selected_cluster_id"] == "cluster-primary"
    assert primary_request["candidate_plan_index"] == 0
    assert primary_request["fresh"] is True
    assert fallback["cluster_id"] == "cluster-fallback"
    assert fallback_selection["selected_cluster_id"] == "cluster-fallback"
    assert fallback_request["candidate_plan_index"] == 1
    assert selection_for_candidate(selection, candidate_index=0)["fallback_candidates"][0][
        "cluster_id"
    ] == "cluster-fallback"


def test_same_high_revision_contract_is_one_round_and_hash_bound():
    binding = _binding()
    selection = _selection()
    initial_request, _candidate, _current = build_external_worker_request(
        binding=binding,
        selection=selection,
        cutoff_utc="2026-08-11T15:00:00Z",
        candidate_index=0,
    )
    worker_return = {
        "schema_version": WORKER_RETURN_SCHEMA_VERSION,
        "governed_input_hash": initial_request["governed_input_hash"],
        "model": "gpt-5.6-sol",
        "reasoning_effort": "HIGH",
        "fresh": True,
        "isolated": True,
        "resume_existing": False,
        "public_write_attempted": False,
        "output": _article_output(),
    }
    contract = build_same_high_revision_contract(
        governed_input_hash=initial_request["governed_input_hash"],
        worker_return=worker_return,
        blockers=["deterministic_source_retrieval_failed:SOURCE_1"],
        prior_bounded_revision_count=0,
    )
    assert validate_same_high_revision_contract(contract) == contract
    revision_request, _candidate, _selection_row = build_external_worker_request(
        binding=binding,
        selection=selection,
        cutoff_utc="2026-08-11T15:00:00Z",
        candidate_index=0,
        revision_contract=contract,
    )
    assert revision_request["resume_same_isolated_worker"] is True
    assert revision_request["fresh_worker_creation"] is False
    assert revision_request["governed_input_hash"] == initial_request["governed_input_hash"]
    with pytest.raises(ValueError, match="revision_budget_exhausted"):
        build_same_high_revision_contract(
            governed_input_hash=initial_request["governed_input_hash"],
            worker_return=worker_return,
            blockers=["still blocked"],
            prior_bounded_revision_count=1,
        )


def test_external_worker_is_verified_after_generation_and_cached_for_canonical_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    binding = _binding()
    selection = _selection()
    request, _candidate, current_selection = build_external_worker_request(
        binding=binding,
        selection=selection,
        cutoff_utc="2026-08-11T15:00:00Z",
        candidate_index=0,
    )
    body = (
        b"<html><head><title>Federal Reserve test</title></head><body>"
        b"The Federal Reserve said the test policy remains unchanged. "
        b"This additional public text makes the deterministic page sufficiently substantive."
        b"</body></html>"
    )
    requests = []

    def fake_get(url: str, timeout: float, max_bytes: int):
        requests.append((url, timeout, max_bytes))
        return {
            "status": 200,
            "body": body,
            "headers": {"content-type": "text/html"},
            "final_url": url,
            "content_truncated": False,
        }

    monkeypatch.setattr(llm_first, "_default_public_http_get", fake_get)
    worker_return = {
        "schema_version": WORKER_RETURN_SCHEMA_VERSION,
        "governed_input_hash": request["governed_input_hash"],
        "model": "gpt-5.6-sol",
        "reasoning_effort": "HIGH",
        "fresh": True,
        "isolated": True,
        "resume_existing": False,
        "public_write_attempted": False,
        "usage": {"input_tokens": 123, "output_tokens": 45},
        "output": _article_output(),
    }
    provider = NativeDesktopExternalLlmFirstProvider(
        output_dir=tmp_path,
        selected_selection=current_selection,
        expected_worker_request=request,
        worker_return=worker_return,
        candidate_index=0,
    )
    first = provider.prepare(
        ranked_clusters=binding["assignment_override"]["ranked_clusters"],
        intake=binding["rolling_input_override"],
        cutoff_utc="2026-08-11T15:00:00Z",
        published_corpus=[],
    )
    second = provider.prepare(
        ranked_clusters=binding["assignment_override"]["ranked_clusters"],
        intake=binding["rolling_input_override"],
        cutoff_utc="2026-08-11T15:00:00Z",
        published_corpus=[],
    )

    assert first["status"] == "PASS"
    assert first["ordering"] == "LLM_FIRST_VALIDATE_AFTER"
    assert first["worker_precedes_deterministic_source_retrieval"] is True
    assert first["network_requests"] == 1
    assert second == first
    assert len(requests) == 1
    evidence = provider.evidence_acquirer(
        {"cluster_id": "cluster-primary", "headline_ids": ["headline-primary"]}
    )
    assert evidence["status"] == "PASS"
    assert evidence["evidence_review_tier"] == "POST_GENERATION_DETERMINISTIC_SOURCE_BYTES"
    assert evidence["publication_authority"] is False


def test_external_worker_failure_is_post_generation_not_prewriter_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    binding = _binding()
    selection = _selection()
    request, _candidate, current_selection = build_external_worker_request(
        binding=binding,
        selection=selection,
        cutoff_utc="2026-08-11T15:00:00Z",
        candidate_index=0,
    )
    monkeypatch.setattr(
        llm_first,
        "_default_public_http_get",
        lambda *_args, **_kwargs: {
            "status": 403,
            "body": b"forbidden",
            "headers": {"content-type": "text/plain"},
            "final_url": "https://www.federalreserve.gov/newsevents/pressreleases/test.htm",
            "content_truncated": False,
        },
    )
    worker_return = {
        "schema_version": WORKER_RETURN_SCHEMA_VERSION,
        "governed_input_hash": request["governed_input_hash"],
        "model": "gpt-5.6-sol",
        "reasoning_effort": "HIGH",
        "fresh": True,
        "isolated": True,
        "resume_existing": False,
        "public_write_attempted": False,
        "output": _article_output(),
    }
    provider = NativeDesktopExternalLlmFirstProvider(
        output_dir=tmp_path,
        selected_selection=current_selection,
        expected_worker_request=request,
        worker_return=worker_return,
        candidate_index=0,
    )
    with pytest.raises(llm_first.LlmFirstValidationError) as exc_info:
        provider.prepare(
            ranked_clusters=binding["assignment_override"]["ranked_clusters"],
            intake=binding["rolling_input_override"],
            cutoff_utc="2026-08-11T15:00:00Z",
            published_corpus=[],
        )
    assert "deterministic_source_retrieval_failed:SOURCE_1" in exc_info.value.blockers


def test_status_names_are_high_only_not_runtime_xhigh():
    assert "HIGH" in INITIAL_HANDOFF_STATUS
    assert "HIGH" in REVISION_HANDOFF_STATUS
    assert "XHIGH" not in INITIAL_HANDOFF_STATUS
    assert "XHIGH" not in REVISION_HANDOFF_STATUS
