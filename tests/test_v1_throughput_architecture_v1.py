from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as implementation
from live_contentops import rolling_x_grounded_article_media_builder_v1 as article_builder
from live_contentops.newsroom_assignment_scheduler_v1 import (
    build_prepared_rolling_x_candidate_state,
    validate_prepared_rolling_x_candidate_state,
)


RECORDED_INTAKE = Path(
    "docs/automation/ROLLING_X_NEWSROOM_LIVE_V1/real_cycle/rolling_x_intake_v1.json"
)
SOURCE_URL = "https://example.com/professional-newsroom-source"


def _large_continuity_input(count: int = 30) -> dict:
    cutoff = datetime(2026, 8, 17, 12, tzinfo=timezone.utc)
    start = cutoff - timedelta(hours=23)
    rows = []
    for index in range(count):
        headline_id = f"frontier-{index:03d}"
        rows.append({
            "headline_id": headline_id,
            "source_timestamp_utc": (start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"),
            "external_content": {
                "headline_text": f"Company {index} reports a current acquisition agreement",
                "author_handle": "controlled",
                "source_platform": "x",
                "url_or_source_ref": "",
                "tags": [],
                "follow_up_data_need_candidates": [],
                "official_source_urls": [f"https://reuters.com/frontier-{index}"],
            },
            "authority_constraints": {
                "discovery_and_ranking_only": True,
                "numeric_truth_authority": False,
                "analysis_or_forecast_authority": False,
                "publication_authority": False,
            },
        })
    return {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "cutoff_time_utc": cutoff.isoformat().replace("+00:00", "Z"),
        "window_start_utc": (cutoff - timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
        "window_hours": 24.0,
        "unique_headline_ids": sorted(row["headline_id"] for row in rows),
        "headlines": rows,
        "counts": {"accepted": len(rows), "duplicates": 0},
        "canonical_input_hash": "controlled-full-input-hash",
        "complete_input_coverage": True,
    }


def test_continuity_frontier_advances_held_identities_without_replaying_unchanged():
    rolling_input = _large_continuity_input()
    first = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc="2026-08-17T12:00:00Z",
        continuity_binding={"last_terminal_cutoff_utc": "2026-08-17T11:00:00Z"},
    )
    first_ids = list(first["prepared_frontier"]["selected_headline_ids"])
    held_ids = set(first["prepared_frontier"]["deferred_headline_ids"])

    second = build_prepared_rolling_x_candidate_state(
        rolling_input={**rolling_input, "cutoff_time_utc": "2026-08-17T12:10:00Z"},
        prepared_at_utc="2026-08-17T12:10:00Z",
        evaluated_headline_ids=first_ids,
        continuity_binding={"last_terminal_cutoff_utc": "2026-08-17T12:00:00Z"},
    )
    second_ids = list(second["prepared_frontier"]["selected_headline_ids"])

    assert len(first_ids) == len(second_ids) == 12
    assert set(first_ids).isdisjoint(second_ids)
    assert set(second_ids).issubset(held_ids)
    assert second["prepared_frontier"]["unchanged_evaluated_excluded_count"] == 12
    assert second["prepared_frontier"]["deferred_identity_count"] == 6
    assert second["prepared_frontier"]["full_universe_semantic_processing_performed"] is False
    assert second["llm_or_provider_calls"] == 0


def test_material_reentry_survives_evaluated_filter_and_empty_unchanged_frontier_is_valid():
    rolling_input = _large_continuity_input(3)
    all_ids = list(rolling_input["unique_headline_ids"])
    material_id = all_ids[1]
    material = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc="2026-08-17T12:00:00Z",
        evaluated_headline_ids=all_ids,
        reentry_headline_ids=[material_id],
    )
    empty = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc="2026-08-17T12:00:00Z",
        evaluated_headline_ids=all_ids,
    )

    assert material["prepared_frontier"]["selected_headline_ids"] == [material_id]
    assert material["prepared_frontier"]["reentry_identity_count"] == 1
    assert empty["prepared_candidate_count"] == 0
    assert empty["assignment"]["decision"] == "NO_PUBLICATION"
    assert empty["assignment"]["reason_code"] == "CONTINUITY_NO_UNSEEN_OR_MATERIAL_UPDATE"
    assert validate_prepared_rolling_x_candidate_state(
        empty, publication_cutoff_utc="2026-08-17T12:01:00Z"
    )["prepared_candidate_count"] == 0


def test_zero_write_prepared_candidate_to_canonical_plan_smoke(monkeypatch, tmp_path):
    """One ordinary path: prepared set -> evidence -> writer -> hard checks -> plan."""
    rolling_input = json.loads(RECORDED_INTAKE.read_text(encoding="utf-8"))
    first_prepared = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc="2026-07-08T13:21:16Z",
    )
    first_ids = list(first_prepared["prepared_frontier"]["selected_headline_ids"])
    prepared = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc="2026-07-08T13:31:16Z",
        evaluated_headline_ids=first_ids,
        continuity_binding={"last_terminal_cutoff_utc": "2026-07-08T13:21:16Z"},
    )
    assert set(prepared["prepared_frontier"]["selected_headline_ids"]).isdisjoint(
        first_ids
    )
    assert prepared["prepared_frontier"]["deferred_identity_count"] > 0
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
            f"[Professional News Source]({SOURCE_URL}) reported that {claim}. The report "
            "establishes the current public position and identifies the development now in "
            "the record, without extending it into unsupported facts or numbers.\n\n"
            "The update matters because readers can distinguish the confirmed development "
            "from speculation surrounding it. The source supports the core proposition, "
            "while motive, scale, and downstream effects remain outside the evidence.\n\n"
            "Important uncertainty remains. Additional first-party detail or independent "
            "reporting would be needed before Capital Chronicle could responsibly add causes, "
            "forecasts, market consequences, or precise quantitative claims."
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

    evidence_ranks: list[int] = []

    def acquire_evidence(request):
        evidence_ranks.append(int(request["rank"]))
        if int(request["rank"]) == 1:
            return {
                "status": "BLOCKED",
                "cluster_id": request["cluster_id"],
                "headline_ids": list(request["headline_ids"]),
                "provided_evidence_capabilities": [],
                "evidence_documents": [],
                "claim_evidence_contract": {
                    "status": "BLOCKED",
                    "supported_claim_count": 0,
                    "fabricated_claim_count": 0,
                },
                "blockers": ["controlled_candidate_local_source_unavailable"],
                "publication_authority": False,
            }
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
    assert evidence_ranks == [1, 2]
    assert result["candidate_walk"]["attempted_candidate_count"] == 2
    assert result["candidate_walk"]["candidate_attempts"][0][
        "evidence_result"
    ] == "BLOCKED"
    assert result["candidate_walk"]["selected_publication_candidate_rank"] == 2
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
    assert result["unknown_write_detected"] is False
