from __future__ import annotations

import json
from pathlib import Path

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as implementation


def _article(body="Current official event analysis with reader-facing context."):
    return {
        "title": "Official Event Update",
        "subtitle": "Verified official records establish the event timeline and explain what readers should watch next.",
        "seo_title": "Official Event Update",
        "slug": "official-event-update",
        "meta_description": "An official event update with verified context, limitations, and implications for readers.",
        "editorial_mode": "analysis",
        "substack_body_markdown": body,
        "market_mechanism": "The official timeline clarifies how the event affects the named entities and what remains unresolved.",
        "policy_context": "The governing record defines the current scope and implementation sequence without adding market claims.",
        "cross_asset_implications": "No market or cross-asset reaction is asserted without separate Capital Chronicle evidence.",
    }


def _semantic(decision):
    return {
        "status": "SUCCESS",
        "decision": decision,
        "mode": "analysis",
        "issues": [] if decision == "PASS" else ["clarify why now"],
        "publication_authority": False,
    }


def test_bounded_editorial_cycle_immediate_pass(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    revisions = []
    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic("PASS"),
        article_reviser=lambda article, review, round_number: revisions.append(round_number),
    )
    assert result["status"] == "PASS"
    assert result["revision_rounds_completed"] == 0
    assert revisions == []


def test_bounded_editorial_cycle_revises_once_then_passes(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    decisions = iter(("NEEDS_REVISION", "PASS"))
    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic(next(decisions)),
        article_reviser=lambda article, review, round_number: {
            **article,
            "substack_body_markdown": article["substack_body_markdown"] + " Clarified why now.",
        },
    )
    assert result["status"] == "PASS"
    assert result["revision_rounds_completed"] == 1
    assert len(result["review_history"]) == 2


def test_bounded_editorial_cycle_exhausts_after_two_revisions(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic("NEEDS_REVISION"),
        article_reviser=lambda article, review, round_number: {
            **article,
            "substack_body_markdown": article["substack_body_markdown"] + f" Revision {round_number}.",
        },
    )
    assert result["status"] == "NO_PUBLICATION"
    assert result["reason_code"] == "EDITORIAL_REVISION_ROUNDS_EXHAUSTED"
    assert result["revision_rounds_completed"] == 2
    assert len(result["review_history"]) == 3


def test_canonical_cycle_stops_before_generation_when_ranked_evidence_blocks(monkeypatch, tmp_path: Path):
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "counts": {"accepted": 1},
    }
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": [{"cluster_id": "c1", "rank": 1, "headline_ids": ["h1"]}],
    }
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: intake,
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: assignment,
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: {"status": "NO_PUBLICATION", "reason_code": "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED"},
    )
    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="proof",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        publication_enabled=False,
    )
    assert result["classification"] == "NO_PUBLICATION"
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False
    assert result["exact_next_blocker"] == "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED"


def test_invalid_semantic_decision_fails_closed_and_exhausts(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: {"status": "SUCCESS", "decision": "PUBLISH"},
        article_reviser=lambda article, review, round_number: {
            **article,
            "substack_body_markdown": article["substack_body_markdown"] + f" Revision {round_number}.",
        },
    )
    assert result["status"] == "NO_PUBLICATION"
    assert result["revision_rounds_completed"] == 2
    assert all(
        row["llm_semantic_review"]["decision"] == "NEEDS_REVISION"
        for row in result["review_history"]
    )
    assert all(
        row["llm_semantic_review"]["publication_authority"] is False
        for row in result["review_history"]
    )


def test_dynamic_destination_readiness_uses_only_verified_statuses():
    result = implementation._rolling_x_destination_readiness(
        cdp_port=9223,
        doctor={"status": "READY_TO_ATTACH", "recommended_cdp_port": 9223},
        account_preflight={
            "substack": {"authenticated": True, "destination_identity": "Capital Chronicle"},
            "x": {"authenticated": True, "destination_identity": "@Capitalnicle"},
            "linkedin": {"authenticated": True, "destination_identity": "linkedin:jimcc"},
            "youtube": {"authenticated": True, "destination_identity": "@CapitalChronicleYouTube"},
        },
        capability_presence={
            "telegram": True,
            "discord": True,
            "facebook_page": True,
            "instagram_business": True,
            "threads": True,
        },
    )
    assert result["all_required_destinations_ready"] is True
    assert {row["status"] for row in result["destinations"].values()} == {
        "READY_AUTHENTICATED",
        "READY_NON_BROWSER_BINDING",
    }

    blocked = implementation._rolling_x_destination_readiness(
        cdp_port=9223,
        doctor={"status": "READY_TO_ATTACH", "recommended_cdp_port": 9223},
        account_preflight={
            "substack": {"authenticated": True},
            "x": {"authenticated": True, "destination_identity": "@wrong"},
            "linkedin": {"authenticated": True, "destination_identity": "linkedin:jimcc"},
            "youtube": {"authenticated": True},
        },
        capability_presence={
            "telegram": True,
            "discord": True,
            "facebook_page": True,
            "instagram_business": True,
            "threads": True,
        },
    )
    assert blocked["all_required_destinations_ready"] is False
    assert blocked["destinations"]["x"]["status"] == "BLOCKED"


def _release_inputs(tmp_path: Path):
    assets = []
    for index, asset_id in enumerate(("event_record", "timeline", "geography"), start=1):
        path = tmp_path / f"{asset_id}.png"
        path.write_bytes(f"image-{index}".encode())
        assets.append(
            {
                "asset_id": asset_id,
                "path": str(path),
                "sha256": implementation._sha256_file(path),
                "caption": f"Verified {asset_id} source visual.",
                "alt_text": f"Verified {asset_id} visual",
                "source_label": "Official Agency",
                "source_page_url": f"https://official.example/{asset_id}",
                "provenance_status": "VERIFIED",
            }
        )
    evidence_documents = [
        {"evidence_id": "ev-1", "source_url": "https://official.example/record"}
    ]
    viability = {
        "status": "SUCCESS",
        "selected_cluster_id": "c1",
        "selected_rank": 1,
        "selected_headline_ids": ["h1"],
        "selected_cluster": {"cluster_id": "c1", "rank": 1, "headline_ids": ["h1"]},
        "selected_evidence": {"evidence_documents": evidence_documents},
    }
    body = "\n\n".join(
        [
            "Official event record released today explains the latest change and what matters now.",
            "[[VISUAL:event_record]]",
            "## What changed\nThe official event record establishes the current facts and affected entities.",
            "[[VISUAL:timeline]]",
            "## Why it matters\nThe timeline clarifies implementation and what would confirm the next phase.",
            "[[VISUAL:geography]]",
            "## Limits\nA conflicting official update would challenge the current account.",
            "## What comes next\nThe named agency update and implementation notice are the next catalysts.",
        ]
    )
    article = {
        **_article(body),
        "cluster_id": "c1",
        "headline_ids": ["h1"],
        "evidence_document_ids": ["ev-1"],
        "x_content_grants_factual_authority": False,
        "canonical_url": "https://capitalchronicle.substack.com/p/pending-publication",
        "social_lede": "The official event record establishes the latest verified update.",
        "social_mechanism_summary": "The implementation timeline explains why the event matters now.",
        "social_policy_summary": "The governing record defines the current scope and sequence.",
        "social_cross_asset_summary": "No unsupported market reaction is asserted.",
    }
    assignment = {"assignment_logical_hash": "assignment-hash"}
    media = {"assets": assets}
    editorial = {"status": "PASS", "article": article, "review_history": []}
    readiness = {
        "all_required_destinations_ready": True,
        "destinations": {
            platform: {"write_eligible": True, "status": "READY_AUTHENTICATED"}
            for platform in ("substack", "x", "linkedin", "youtube")
        } | {
            platform: {"write_eligible": True, "status": "READY_NON_BROWSER_BINDING"}
            for platform in ("telegram", "discord", "facebook_page", "instagram_business", "threads")
        },
    }
    return assignment, viability, article, media, editorial, readiness


def test_rolling_x_release_candidate_builds_and_verifies_canonical_lock(tmp_path: Path):
    assignment, viability, article, media, editorial, readiness = _release_inputs(tmp_path)
    result = implementation._prepare_rolling_x_release_candidate(
        run_id="rolling-release",
        output_dir=tmp_path,
        intake={"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
        assignment=assignment,
        viability=viability,
        article=article,
        media=media,
        editorial_cycle=editorial,
        destination_readiness=readiness,
    )
    assert result["classification"] == "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
    assert result["release_candidate_lock_verification"]["status"] == "PASS_RELEASE_CANDIDATE_LOCK"
    assert set(implementation._RELEASE_PREPARATION_ARTIFACTS).issubset(
        {path.name for path in tmp_path.iterdir()}
    )
    context = json.loads((tmp_path / "run_context_v1.json").read_text(encoding="utf-8"))
    assert context["rolling_x_live_path_used"] is True
    assert context["generic_live_path_used"] is False
    payloads = json.loads((tmp_path / "native_payloads_rehearsal_v1.json").read_text(encoding="utf-8"))
    assert payloads["x"]["quality_metrics"]["complete_article_visual_count"] == 3
    assert payloads["threads"]["quality_metrics"]["reply_count"] == 2


def test_release_candidate_blocks_when_any_destination_is_not_ready(tmp_path: Path):
    assignment, viability, article, media, editorial, readiness = _release_inputs(tmp_path)
    readiness["all_required_destinations_ready"] = False
    readiness["destinations"]["x"] = {"write_eligible": False, "status": "BLOCKED"}
    result = implementation._prepare_rolling_x_release_candidate(
        run_id="rolling-blocked",
        output_dir=tmp_path,
        intake={"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
        assignment=assignment,
        viability=viability,
        article=article,
        media=media,
        editorial_cycle=editorial,
        destination_readiness=readiness,
    )
    assert result["classification"] == "BLOCKED_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
    assert "destination_not_ready:x" in result["blockers"]
    assert result["release_candidate_lock_verification"]["status"] == "BLOCKED_RELEASE_CANDIDATE_LOCK"


def test_passed_cycle_delegates_once_to_canonical_backend(monkeypatch, tmp_path: Path):
    assignment, viability, article, media, editorial, readiness = _release_inputs(tmp_path)
    calls = []
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: {"status": "SUCCESS", "assignment_logical_hash": "assignment-hash"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: viability,
    )
    monkeypatch.setattr(implementation, "_rolling_x_destination_readiness", lambda **kwargs: readiness)
    monkeypatch.setattr(
        implementation,
        "_run_bounded_rolling_x_editorial_cycle",
        lambda **kwargs: editorial,
    )
    monkeypatch.setattr(
        implementation,
        "_run_eight_platform_substack_first_pipeline",
        lambda **kwargs: calls.append(kwargs) or {
            "classification": "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1",
            "results": {
                "substack": {
                    "status": "SUCCESS",
                    "public_url": "https://capitalchronicle.substack.com/p/official-event-update",
                    "provider_readback_verified": True,
                    "readback": {"status": "SUCCESS"},
                }
            },
        },
    )
    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="rolling-dispatch",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=lambda value: {"article": article, "media": media},
        editorial_reviewer=lambda value: _semantic("PASS"),
        article_reviser=lambda value, review, round_number: value,
        publication_enabled=True,
    )
    assert len(calls) == 1
    assert result["classification"] == "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1"
    assert result["public_write_performed"] is True
    assert result["strict_readback_performed"] is True
    assert result["unknown_write_detected"] is False


def test_unknown_write_from_canonical_backend_stops_retry_and_requires_reconciliation(
    monkeypatch, tmp_path: Path
):
    assignment, viability, article, media, editorial, readiness = _release_inputs(tmp_path)
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: {"status": "SUCCESS", "assignment_logical_hash": "assignment-hash"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: viability,
    )
    monkeypatch.setattr(implementation, "_rolling_x_destination_readiness", lambda **kwargs: readiness)
    monkeypatch.setattr(
        implementation,
        "_run_bounded_rolling_x_editorial_cycle",
        lambda **kwargs: editorial,
    )
    monkeypatch.setattr(
        implementation,
        "_run_eight_platform_substack_first_pipeline",
        lambda **kwargs: {
            "classification": "FAILED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1",
            "results": {
                "substack": {"status": "SUCCESS", "provider_readback_verified": True},
                "x": {
                    "status": "FAILED_X_PERMALINK_READBACK",
                    "write_outcome_certainty": "unknown",
                    "automatic_retry_blocked": True,
                },
            },
        },
    )
    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="rolling-unknown",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=lambda value: {"article": article, "media": media},
        editorial_reviewer=lambda value: _semantic("PASS"),
        article_reviser=lambda value, review, round_number: value,
        publication_enabled=True,
    )
    assert result["unknown_write_detected"] is True
    assert result["automatic_retry_blocked"] is True
    assert result["exact_next_blocker"] == "STOP_RETRY_READ_BACK_RECONCILE"
