from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path

import pytest

from live_contentops import llm_first_validate_after_v1 as llm_first
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    CONTENTOPS_CODEX_MAX_REASONING_EFFORT,
    COORDINATOR_REASONING_EFFORT,
    EDITORIAL_WORKER_REASONING_EFFORT,
)
from live_contentops.official_codex_provider_v1 import EFFORT
from live_contentops import newsroom_assignment_scheduler_v1 as scheduler


def _article() -> dict:
    claim = "Reuters reported that Acme launched its new service on Tuesday."
    return {
        "title": "Acme launches a new service",
        "canonical_editorial_headline": "Acme launches a new service",
        "subtitle": "The company introduced the service on Tuesday.",
        "dek": "The company introduced the service on Tuesday.",
        "seo_title": "Acme launches new service",
        "search_title": "Acme launches new service",
        "meta_description": "Acme launched a new service on Tuesday.",
        "social_lede": "Acme launches a new service.",
        "social_hook": "Acme launches a new service.",
        "substack_body_markdown": claim + " [[SOURCE:SOURCE_1]]",
    }


def _worker_output(*, declared_time: str = "2026-08-26T11:59:00Z") -> dict:
    return {
        "article": _article(),
        "cited_sources": [
            {
                "source_id": "SOURCE_1",
                "url": "https://www.reuters.com/world/acme-service/",
                "publisher": "Reuters",
                "published_at_utc": declared_time,
            }
        ],
        "material_claim_bindings": [
            {
                "claim_id": "claim-1",
                "claim_text": "Reuters reported that Acme launched its new service on Tuesday.",
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": "Reuters reported that Acme launched its new service on Tuesday.",
                "attribution_required": True,
            }
        ],
    }


def _response(*, published: str | None) -> dict:
    meta = (
        f'<meta property="article:published_time" content="{published}">' if published else ""
    )
    body = (
        "<html><head><title>Acme launches service</title>"
        + meta
        + "</head><body>Reuters reported that Acme launched its new service on Tuesday. "
        "The rollout begins this week.</body></html>"
    ).encode()
    return {
        "status": 200,
        "final_url": "https://www.reuters.com/world/acme-service/",
        "headers": {"content-type": "text/html"},
        "body": body,
        "content_truncated": False,
    }


def test_post_generation_verifier_uses_publisher_timestamp_not_model_timestamp(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        llm_first,
        "_default_public_http_get",
        lambda *_args: _response(published="2026-08-26T00:00:00Z"),
    )
    provider = llm_first.LlmFirstValidateAfterProvider(output_dir=tmp_path)
    result = provider._verify(
        _worker_output(declared_time="2026-08-26T11:59:00Z"),
        candidate={"cluster_id": "cluster-1", "headline_ids": ["headline-1"]},
        cutoff_utc="2026-08-26T12:00:00Z",
    )

    document = result["documents"][0]
    assert document["published_at_utc"] == "2026-08-26T00:00:00Z"
    assert document["published_at_source"] == "PUBLISHER_BYTES_OR_HEADERS"
    assert document["freshness_timestamp_source"] == "PUBLISHER_BYTES_OR_HEADERS"
    assert document["model_declared_published_at_utc"] == "2026-08-26T11:59:00Z"
    assert "freshness_state" not in document
    assert result["verification"]["model_declared_source_timestamp_grants_authority"] is False
    assert result["supported_claims"][0]["evidence_document_ids"] == [
        document["document_id"]
    ]


def test_post_generation_verifier_rejects_model_only_publication_timestamp(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        llm_first,
        "_default_public_http_get",
        lambda *_args: _response(published=None),
    )
    provider = llm_first.LlmFirstValidateAfterProvider(output_dir=tmp_path)
    with pytest.raises(
        llm_first.LlmFirstValidationError,
        match="deterministic_published_timestamp_unavailable",
    ):
        provider._verify(
            _worker_output(declared_time="2026-08-26T11:59:00Z"),
            candidate={"cluster_id": "cluster-1", "headline_ids": ["headline-1"]},
            cutoff_utc="2026-08-26T12:00:00Z",
        )


def test_post_generation_verifier_allows_exact_url_bound_intake_timestamp(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        llm_first,
        "_default_public_http_get",
        lambda *_args: _response(published=None),
    )
    provider = llm_first.LlmFirstValidateAfterProvider(output_dir=tmp_path)
    result = provider._verify(
        _worker_output(declared_time="2020-01-01T00:00:00Z"),
        candidate={
            "cluster_id": "cluster-1",
            "headline_ids": ["headline-1"],
            "headlines": [
                {
                    "headline_id": "headline-1",
                    "source_url": "https://www.reuters.com/world/acme-service/",
                    "source_timestamp_utc": "2026-08-26T01:00:00Z",
                }
            ],
        },
        cutoff_utc="2026-08-26T12:00:00Z",
    )

    document = result["documents"][0]
    assert document["published_at_utc"] == "2026-08-26T01:00:00Z"
    assert document["published_at_source"] == "EXACT_BOUND_HEADLINE_TIMESTAMP"
    assert document["model_declared_published_at_utc"] == "2020-01-01T00:00:00Z"


def test_post_generation_verifier_rejects_unverified_claim_excerpt(monkeypatch, tmp_path):
    monkeypatch.setattr(
        llm_first,
        "_default_public_http_get",
        lambda *_args: {
            "status": 200,
            "final_url": "https://www.reuters.com/world/acme-service/",
            "headers": {"content-type": "text/html"},
            "body": (
                b'<html><head><meta property="article:published_time" '
                b'content="2026-08-26T00:00:00Z"></head><body>'
                b"A different public report with enough visible text for validation.</body></html>"
            ),
            "content_truncated": False,
        },
    )
    provider = llm_first.LlmFirstValidateAfterProvider(output_dir=tmp_path)
    with pytest.raises(llm_first.LlmFirstValidationError, match="excerpt_not_verified"):
        provider._verify(
            _worker_output(),
            candidate={"cluster_id": "cluster-1", "headline_ids": ["headline-1"]},
            cutoff_utc="2026-08-26T12:00:00Z",
        )


def test_exact_bound_coordinator_checkpoint_is_reused_without_new_model_turn(
    monkeypatch, tmp_path
):
    candidates = [
        {
            "cluster_id": "cluster-1",
            "rank": 1,
            "headline_ids": ["headline-1"],
            "headlines": [],
        }
    ]
    published = [{"story_identity": "old-story"}]
    governed = llm_first.LlmFirstValidateAfterProvider._selection_governed_input(
        candidates=candidates,
        cutoff_utc="2026-08-26T12:00:00Z",
        published_corpus=published,
        excluded_cluster_ids=[],
    )
    governed_hash = llm_first._hash(governed)
    selection = {
        "selected_cluster_id": "cluster-1",
        "article_mode": "BREAKING_BRIEF",
        "selection_rationale": "Current and useful.",
    }
    receipt = {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "HIGH",
        "provider_input_identity": {
            "role": "V1_LLM_FIRST_COORDINATOR_SELECTION",
            "governed_input_hash": governed_hash,
        },
    }
    (tmp_path / "llm_first_coordinator_selection_v1.json").write_text(
        json.dumps(
            {
                "schema_version": llm_first.COORDINATOR_CHECKPOINT_SCHEMA_VERSION,
                # Deliberately omit the new top-level hash to prove compatibility with the
                # already-persisted pre-Phase-A checkpoint, whose receipt owns the exact hash.
                "selection": selection,
                "coordinator_receipt": receipt,
                "maximum_reasoning_effort": "HIGH",
                "public_write_performed": False,
            }
        ),
        encoding="utf-8",
    )

    class ForbiddenSession:
        def __init__(self, *args, **kwargs):
            raise AssertionError("coordinator model turn must not be recreated")

    monkeypatch.setattr(llm_first, "OfficialCodexEditorialSession", ForbiddenSession)
    provider = llm_first.LlmFirstValidateAfterProvider(output_dir=tmp_path)
    actual_selection, actual_receipt = provider._select(
        candidates=candidates,
        cutoff_utc="2026-08-26T12:00:00Z",
        published_corpus=published,
        excluded_cluster_ids=[],
    )

    assert actual_selection == selection
    assert actual_receipt == receipt
    assert provider._coordinator_checkpoint_reused is True


def test_exact_verified_worker_checkpoint_reenters_without_another_model_call(
    monkeypatch, tmp_path
):
    ranked = [
        {
            "cluster_id": "cluster-1",
            "rank": 1,
            "headline_ids": ["headline-1"],
            "why_now": "Current event",
        }
    ]
    intake = {
        "headlines": [
            {
                "headline_id": "headline-1",
                "headline_text": "Acme reports earnings Wednesday",
                "source_timestamp_utc": "2026-08-26T01:00:00Z",
            }
        ]
    }
    provider = llm_first.LlmFirstValidateAfterProvider(output_dir=tmp_path)
    candidates = provider._candidate_packet(ranked, intake)
    selection = {
        "selected_cluster_id": "cluster-1",
        "article_mode": "WEEK_AHEAD_OR_WATCH",
        "selection_rationale": "A useful current catalyst watch.",
    }
    cutoff = "2026-08-26T12:00:00Z"
    coordinator_hash = llm_first._hash(
        provider._selection_governed_input(
            candidates=candidates,
            cutoff_utc=cutoff,
            published_corpus=[],
            excluded_cluster_ids=[],
        )
    )
    worker_hash = llm_first._hash(
        provider._worker_governed_input(
            candidate=candidates[0], selection=selection, cutoff_utc=cutoff
        )
    )
    content = "Acme reports earnings Wednesday with enough exact source text."
    coordinator_receipt = {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "HIGH",
        "model_turn_completed": True,
        "public_write_attempted": False,
        "provider_input_identity": {
            "role": "V1_LLM_FIRST_COORDINATOR_SELECTION",
            "governed_input_hash": coordinator_hash,
        },
    }
    worker_receipt = {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "HIGH",
        "model_turn_completed": True,
        "public_write_attempted": False,
        "provider_input_identity": {"role": "V1_LLM_FIRST_EDITORIAL_WRITER"},
    }
    (tmp_path / "llm_first_validate_after_receipt_v1.json").write_text(
        json.dumps(
            {
                "article": _article(),
                "selection": selection,
                "coordinator_receipt": coordinator_receipt,
                "coordinator_checkpoint_reused": False,
                "worker_receipts": [worker_receipt],
                "candidate_attempts": [{"cluster_id": "cluster-1", "status": "PASS"}],
                "governed_input_hash": worker_hash,
                "documents": [
                    {
                        "document_id": "doc-1",
                        "canonical_content_text": content,
                        "canonical_content_sha256": hashlib.sha256(
                            content.encode("utf-8")
                        ).hexdigest(),
                    }
                ],
                "supported_claims": [{"claim_id": "claim-1"}],
                "cited_sources": [],
                "material_claim_bindings": [],
                "verification": {
                    "status": "PASS",
                    "deterministic_source_request_count": 1,
                },
            }
        ),
        encoding="utf-8",
    )

    class ForbiddenSession:
        def __init__(self, **_kwargs):
            raise AssertionError("verified checkpoint must avoid a new model session")

    monkeypatch.setattr(llm_first, "OfficialCodexEditorialSession", ForbiddenSession)

    summary = provider.prepare(
        ranked_clusters=ranked,
        intake=intake,
        cutoff_utc=cutoff,
        published_corpus=[],
    )

    assert summary["verified_checkpoint_reused"] is True
    assert summary["coordinator_checkpoint_reused"] is True
    assert summary["model_calls_executed_this_prepare"] == []


def test_duplicate_title_h1_is_removed_without_changing_body_prose():
    article = {
        "title": "Acme reports earnings",
        "canonical_editorial_headline": "Acme reports earnings",
        "substack_body_markdown": (
            "# Acme reports earnings\n\n"
            "Acme reports earnings Wednesday. [[SOURCE:SOURCE_1]]"
        ),
    }

    normalized = llm_first._without_duplicate_leading_h1(article)

    assert normalized["title"] == article["title"]
    assert normalized["substack_body_markdown"] == (
        "Acme reports earnings Wednesday. [[SOURCE:SOURCE_1]]"
    )
    assert article["substack_body_markdown"].startswith("# ")


def test_checkpoint_is_not_reused_when_governed_input_drifted(monkeypatch, tmp_path):
    checkpoint = {
        "schema_version": llm_first.COORDINATOR_CHECKPOINT_SCHEMA_VERSION,
        "governed_input_hash": "0" * 64,
        "selection": {
            "selected_cluster_id": "cluster-1",
            "article_mode": "BREAKING_BRIEF",
            "selection_rationale": "Old selection.",
        },
        "coordinator_receipt": {
            "model": "gpt-5.6-sol",
            "reasoning_effort": "HIGH",
            "provider_input_identity": {
                "role": "V1_LLM_FIRST_COORDINATOR_SELECTION",
                "governed_input_hash": "0" * 64,
            },
        },
        "maximum_reasoning_effort": "HIGH",
        "public_write_performed": False,
    }
    (tmp_path / "llm_first_coordinator_selection_v1.json").write_text(
        json.dumps(checkpoint), encoding="utf-8"
    )

    class ExpectedFreshSelection(Exception):
        pass

    class FreshSession:
        def __init__(self, *args, **kwargs):
            raise ExpectedFreshSelection

    monkeypatch.setattr(llm_first, "OfficialCodexEditorialSession", FreshSession)
    provider = llm_first.LlmFirstValidateAfterProvider(output_dir=tmp_path)
    with pytest.raises(ExpectedFreshSelection):
        provider._select(
            candidates=[{"cluster_id": "cluster-1", "headline_ids": ["headline-1"]}],
            cutoff_utc="2026-08-26T12:00:00Z",
            published_corpus=[],
            excluded_cluster_ids=[],
        )
    assert provider._coordinator_checkpoint_reused is False


def test_current_contentops_codex_configuration_is_high_only():
    assert CONTENTOPS_CODEX_MAX_REASONING_EFFORT == "HIGH"
    assert COORDINATOR_REASONING_EFFORT == "HIGH"
    assert EDITORIAL_WORKER_REASONING_EFFORT == "HIGH"
    assert EFFORT == "high"


def test_llm_first_selected_mode_reaches_exact_post_generation_evidence():
    cluster_id = "cluster-earnings"
    headline_ids = ["headline-1"]

    def acquire(request):
        document = {
            "document_id": "doc-1",
            "source_url": "https://www.reuters.com/world/acme-service/",
            "public_claim_allowed": True,
        }
        return {
            "status": "PASS",
            "blockers": [],
            "cluster_id": request["cluster_id"],
            "headline_ids": list(request["headline_ids"]),
            "provided_evidence_capabilities": list(
                request["required_evidence_capabilities"]
            ),
            "evidence_documents": [document],
            "minimum_trustworthy_evidence_packet": {
                "status": "PASS",
                "risk_tier": "ORDINARY",
                "core_factual_proposition": "Acme reports earnings Wednesday.",
                "evidence_document_id": "doc-1",
                "source_url": document["source_url"],
            },
            "claim_evidence_contract": {
                "status": "PASS",
                "supported_claim_count": 1,
                "fabricated_claim_count": 0,
            },
            "capital_chronicle_authority_verified": False,
            "publication_authority": False,
        }

    result = scheduler.select_first_viable_rolling_x_cluster(
        assignment={
            "schema_version": scheduler.ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
            "decision": "SELECT_STORY",
            "ranked_clusters": [
                {
                    "cluster_id": cluster_id,
                    "headline_ids": headline_ids,
                    "rank": 1,
                    "article_mode": "WEEK_AHEAD_OR_WATCH",
                    "resolved_article_mode": "WEEK_AHEAD_OR_WATCH",
                    "llm_first_validate_after_selected": True,
                }
            ],
        },
        acquire_evidence=acquire,
        story_type_by_cluster={cluster_id: "company_sector_event"},
    )

    assert result["status"] == "SUCCESS"
    assert result["selected_cluster_id"] == cluster_id
    assert result["rank_attempts"][0]["capability_resolution"]["blockers"] == []
    assert result["rank_attempts"][0]["effective_article_mode"] == (
        "WEEK_AHEAD_OR_WATCH"
    )

    root = Path(__file__).resolve().parents[1]
    runtime_paths = [
        root / "live_contentops" / "codex_desktop_newsroom_operator_v1.py",
        root / "live_contentops" / "official_codex_provider_v1.py",
        root / "live_contentops" / "llm_first_validate_after_v1.py",
        root / "live_contentops" / "native_desktop_production_handoff_v1.py",
        root / "live_contentops" / "newsroom_production_day_v1.py",
    ]
    forbidden_assignment = re.compile(
        r"(?:EFFORT|REASONING_EFFORT)\s*=\s*[\"'](?:XHIGH|ULTRA_HIGH|MAX|ULTRA)[\"']",
        re.IGNORECASE,
    )
    for path in runtime_paths:
        text = path.read_text(encoding="utf-8")
        assert forbidden_assignment.search(text) is None, path
        assert "gpt-5.6-sol / XHIGH" not in text, path
        assert "gpt-5.6-sol / ULTRA" not in text, path


def test_workflow_policy_locks_github_first_and_conversation_decision():
    root = Path(__file__).resolve().parents[1]
    policy = (
        root
        / "docs"
        / "automation"
        / "CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md"
    ).read_text(encoding="utf-8")
    assert "GitHub Connector / `WEB_STATIC` first" in policy
    assert "Codex Desktop / `CODEX_EXECUTION` is the second-last choice" in policy
    assert "CODEX DESKTOP CONVERSATION: CURRENT" in policy
    assert "CODEX DESKTOP CONVERSATION: FRESH" in policy
    assert "If uncertain between CURRENT and FRESH, choose FRESH" in policy
    assert "REASONING CEILING: HIGH" in policy


def test_canonical_cycle_exposes_llm_first_adapter_before_evidence_selection():
    root = Path(__file__).resolve().parents[1]
    implementation = (
        root / "live_contentops" / "_eight_platform_substack_first_pipeline_impl_v1.py"
    ).read_text(encoding="utf-8")
    prepare_index = implementation.index("prepare(\n                ranked_clusters=llm_candidates")
    evidence_index = implementation.index("select_with_quota_efficient_discovery()")
    readiness_index = implementation.index("verify_full_v1_transaction_preflight")
    assert prepare_index < evidence_index < readiness_index
    assert "llm_first_validate_after_requires_zero_public_write" in implementation
    assert '"llm_first_validate_after_binding"' in implementation
    assert "checkpoint_llm_binding_valid" in implementation
