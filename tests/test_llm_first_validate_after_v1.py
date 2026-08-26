from __future__ import annotations

import re
from pathlib import Path

import pytest

from live_contentops import llm_first_validate_after_v1 as llm_first
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    CONTENTOPS_CODEX_MAX_REASONING_EFFORT,
    COORDINATOR_REASONING_EFFORT,
    EDITORIAL_WORKER_REASONING_EFFORT,
)
from live_contentops.official_codex_provider_v1 import EFFORT


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


def test_post_generation_verifier_accepts_exact_retrieved_excerpt(monkeypatch, tmp_path):
    body = (
        b"<html><head><title>Acme launches service</title></head><body>"
        b"Reuters reported that Acme launched its new service on Tuesday."
        b" The rollout begins this week.</body></html>"
    )
    monkeypatch.setattr(
        llm_first,
        "_default_public_http_get",
        lambda *_args: {
            "status": 200,
            "final_url": "https://www.reuters.com/world/acme-service/",
            "headers": {"content-type": "text/html"},
            "body": body,
            "content_truncated": False,
        },
    )
    provider = llm_first.LlmFirstValidateAfterProvider(output_dir=tmp_path)
    result = provider._verify(
        {
            "article": _article(),
            "cited_sources": [
                {
                    "source_id": "SOURCE_1",
                    "url": "https://www.reuters.com/world/acme-service/",
                    "publisher": "Reuters",
                    "published_at_utc": "2026-08-26T00:00:00Z",
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
        },
        candidate={"cluster_id": "cluster-1", "headline_ids": ["headline-1"]},
        cutoff_utc="2026-08-26T12:00:00Z",
    )

    assert result["verification"]["ordering"] == "LLM_FIRST_VALIDATE_AFTER"
    assert result["verification"]["deterministic_source_request_count"] == 1
    assert result["documents"][0]["retrieval_method"] == (
        "READ_ONLY_PUBLIC_HTTP_GET_AFTER_GENERATION"
    )
    assert result["supported_claims"][0]["evidence_document_ids"] == [
        result["documents"][0]["document_id"]
    ]


def test_post_generation_verifier_rejects_unverified_claim_excerpt(monkeypatch, tmp_path):
    monkeypatch.setattr(
        llm_first,
        "_default_public_http_get",
        lambda *_args: {
            "status": 200,
            "final_url": "https://www.reuters.com/world/acme-service/",
            "headers": {"content-type": "text/html"},
            "body": b"<html><body>A different public report with enough visible text for validation.</body></html>",
            "content_truncated": False,
        },
    )
    provider = llm_first.LlmFirstValidateAfterProvider(output_dir=tmp_path)
    with pytest.raises(llm_first.LlmFirstValidationError, match="excerpt_not_verified"):
        provider._verify(
            {
                "article": _article(),
                "cited_sources": [
                    {
                        "source_id": "SOURCE_1",
                        "url": "https://www.reuters.com/world/acme-service/",
                        "publisher": "Reuters",
                        "published_at_utc": "2026-08-26T00:00:00Z",
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
            },
            candidate={"cluster_id": "cluster-1", "headline_ids": ["headline-1"]},
            cutoff_utc="2026-08-26T12:00:00Z",
        )


def test_current_contentops_codex_configuration_is_high_only():
    assert CONTENTOPS_CODEX_MAX_REASONING_EFFORT == "HIGH"
    assert COORDINATOR_REASONING_EFFORT == "HIGH"
    assert EDITORIAL_WORKER_REASONING_EFFORT == "HIGH"
    assert EFFORT == "high"

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
