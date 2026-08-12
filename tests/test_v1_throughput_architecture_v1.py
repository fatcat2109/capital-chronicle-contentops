from __future__ import annotations

import json
from pathlib import Path

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as implementation
from live_contentops import rolling_x_grounded_article_media_builder_v1 as article_builder
from live_contentops.newsroom_assignment_scheduler_v1 import (
    build_prepared_rolling_x_candidate_state,
)


RECORDED_INTAKE = Path(
    "docs/automation/ROLLING_X_NEWSROOM_LIVE_V1/real_cycle/rolling_x_intake_v1.json"
)
SOURCE_URL = "https://example.com/professional-newsroom-source"


def test_zero_write_prepared_candidate_to_canonical_plan_smoke(monkeypatch, tmp_path):
    """One ordinary path: prepared set -> evidence -> writer -> hard checks -> plan."""
    rolling_input = json.loads(RECORDED_INTAKE.read_text(encoding="utf-8"))
    prepared = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc="2026-07-08T13:21:16Z",
    )
    monkeypatch.setattr(
        "live_contentops.preselection_intelligence_v1.apply_preselection_intelligence",
        lambda clusters, **_kwargs: {
            "ranked_clusters": list(clusters),
            "preselection_logical_hash": "controlled-zero-write-preselection",
        },
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("full-universe assignment is outside the publication path")
        ),
    )

    writer_calls: list[str] = []

    def quality_writer(prompt: str):
        writer_calls.append(prompt)
        governed = json.loads(prompt.split("GOVERNED_INPUT:\n", 1)[1])
        claim = str(governed["supported_claims"][0]["claim_text"]).rstrip(".")
        markers = "\n\n".join(
            f"[[VISUAL:{asset_id}]]" for asset_id in governed["visual_asset_ids"]
        )
        body = (
            f"[Professional News Source]({SOURCE_URL}) reported that {claim}. "
            "The development is useful to readers because it clarifies the current public "
            "position without extending the report into unsupported claims."
        )
        if markers:
            body += "\n\n" + markers
        return {
            "title": claim[:95],
            "subtitle": "A concise sourced update on the confirmed development.",
            "seo_title": claim[:70],
            "meta_description": (
                f"{claim}. A sourced Capital Chronicle update explaining the confirmed scope."
            )[:165],
            "market_mechanism": "No unsupported market mechanism is asserted.",
            "policy_context": "The report establishes only the current public position.",
            "cross_asset_implications": "No cross-asset implication is asserted.",
            "social_lede": claim,
            "social_mechanism_summary": "The confirmed scope is limited to the report.",
            "social_policy_summary": "The public report defines the current position.",
            "social_cross_asset_summary": "No unsupported market implication is asserted.",
            "substack_body_markdown": body,
        }

    monkeypatch.setattr(article_builder, "_default_article_generator", quality_writer)

    def acquire_evidence(request):
        proposition = " ".join(
            str(request["story_context"]["why_now"] or "").split()
        ).rstrip(".")
        document_id = "controlled-professional-source-1"
        return {
            "status": "PASS",
            "cluster_id": request["cluster_id"],
            "headline_ids": list(request["headline_ids"]),
            "provided_evidence_capabilities": list(
                request["required_evidence_capabilities"]
            ),
            "evidence_review_tier": "ORDINARY_MINIMUM",
            "minimum_trustworthy_evidence_packet": {
                "schema_version": "contentops.minimum_trustworthy_evidence_packet.v1",
                "status": "PASS",
                "risk_tier": "ORDINARY",
                "core_factual_proposition": proposition,
                "source_title": proposition,
                "publisher": "Professional News Source",
                "source_url": SOURCE_URL,
                "published_at_utc": "2026-07-08T13:00:00Z",
                "evidence_document_id": document_id,
                "source_authority_class": "reputable_secondary_source",
                "publication_authority": False,
            },
            "claim_evidence_contract": {
                "status": "PASS",
                "claim_contract_sha256": "c" * 64,
                "supported_claim_count": 1,
                "omitted_claim_count": 0,
                "fabricated_claim_count": 0,
                "supported_claims": [{
                    "claim_id": "claim-1",
                    "claim_text": proposition,
                    "evidence_document_ids": [document_id],
                }],
                "omitted_unsupported_claims": [],
            },
            "evidence_documents": [{
                "document_id": document_id,
                "title": proposition,
                "publisher": "Professional News Source",
                "source_identity": "example.com",
                "source_authority_class": "reputable_secondary_source",
                "source_adapter_family": "reputable_public_secondary",
                "source_url": SOURCE_URL,
                "requested_source_url": SOURCE_URL,
                "published_at_utc": "2026-07-08T13:00:00Z",
                "event_time_utc": "2026-07-08T13:00:00Z",
                "known_at_utc": "2026-07-08T13:10:00Z",
                "canonical_content_text": proposition,
                "public_claim_allowed": True,
                "cluster_id": request["cluster_id"],
                "headline_ids": list(request["headline_ids"]),
                "permission_state": "PUBLIC_CLAIM_ALLOWED",
                "freshness_state": "FRESH_CURRENT_OPERATOR_READINESS",
            }],
            "capital_chronicle_authority_verified": False,
            "numeric_evidence_required": False,
            "blockers": [],
            "publication_authority": False,
        }

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="throughput-architecture-zero-write-smoke",
        output_dir=tmp_path,
        cutoff_utc="2026-07-08T13:51:16Z",
        prepared_candidate_state=prepared,
        evidence_acquirer=acquire_evidence,
        publication_enabled=False,
        published_corpus=[],
        cc_catalog={"stores": [], "root_exists": False},
        destination_readiness_override={
            "all_required_destinations_ready": True,
            "destinations": {
                platform: {"write_eligible": True, "status": "READY_AUTHENTICATED"}
                for platform in ("substack", "x", "linkedin", "youtube")
            } | {
                platform: {"write_eligible": True, "status": "READY_NON_BROWSER_BINDING"}
                for platform in (
                    "telegram", "discord", "facebook_page", "instagram_business", "threads"
                )
            },
            "fixture_bound": True,
            "public_write_authority": False,
        },
    )

    telemetry = result["critical_path_telemetry"]
    assert len(writer_calls) == 1
    assert result["article"]["article_generation_method"] == "ROUTED_LLM_GROUNDED_ARTICLE"
    assert result["editorial_cycle"]["status"] == "PASS"
    assert result["editorial_cycle"]["mandatory_semantic_review_calls"] == 0
    assert result["shadow_publication_plan_ready"] is True
    assert any(
        row["destination"] == "substack"
        for row in result["publication_lifecycle_plan"]["destinations"]
    )
    assert telemetry["full_universe_semantic_assignment_on_critical_path"] is False
    assert telemetry["routine_semantic_calls"] == 1
    assert telemetry["article_writer_semantic_calls"] == 1
    assert telemetry["mandatory_semantic_review_calls"] == 0
    assert telemetry["public_write_performed"] is False
    assert result["public_write_performed"] is False
