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


def _story_routing(clusters, story_type="regulatory_fiscal_event", **_kwargs):
    return {
        "stories": [
            {
                "cluster_id": row["cluster_id"],
                "story_type": story_type,
                "reason": "Exact focused test routing.",
            }
            for row in clusters
        ],
        "story_type_by_cluster": {
            row["cluster_id"]: story_type for row in clusters
        },
        "router_summary": {"terminal_disposition": "accepted"},
        "semantic_routing_grants_authority": False,
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


def test_bounded_editorial_cycle_exhausts_after_one_revision(monkeypatch):
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
    assert result["revision_rounds_completed"] == 1
    assert len(result["review_history"]) == 2


def test_bounded_editorial_cycle_fails_closed_when_review_router_fails(monkeypatch):
    from live_contentops.nine_router_llm_seam_v2 import RoutedInvocationError

    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )

    def fail_review(_article):
        raise RoutedInvocationError(
            {
                "terminal_disposition": "PROVIDER_EXHAUSTED",
                "models_attempted_in_order": ["model-a"],
                "raw_output": "must-not-persist",
            }
        )

    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=fail_review,
        article_reviser=lambda article, review, round_number: article,
    )

    assert result["status"] == "NO_PUBLICATION"
    assert result["reason_code"] == "EDITORIAL_REVIEW_ROUTER_FAILURE"
    assert result["publication_authority_granted"] is False
    failure = result["review_history"][0]["llm_semantic_review"]["router_failure"]
    assert failure["terminal_disposition"] == "PROVIDER_EXHAUSTED"
    assert "raw_output" not in failure


def test_bounded_editorial_cycle_fails_closed_when_revision_router_fails(monkeypatch):
    from live_contentops.nine_router_llm_seam_v2 import RoutedInvocationError

    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )

    def fail_revision(_article, _review, _round_number):
        raise RoutedInvocationError(
            {
                "terminal_disposition": "BUDGET_EXHAUSTED",
                "budget_exhausted_reason": "llm_cycle_provider_attempt_budget_exhausted",
                "models_attempted_in_order": ["model-a", "model-b"],
                "provider_error": "must-not-persist",
            }
        )

    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic("NEEDS_REVISION"),
        article_reviser=fail_revision,
    )

    assert result["status"] == "NO_PUBLICATION"
    assert result["reason_code"] == "EDITORIAL_REVISION_ROUTER_FAILURE"
    assert result["revision_rounds_completed"] == 0
    assert result["publication_authority_granted"] is False
    failure = result["review_history"][0]["revision"]["router_failure"]
    assert failure["budget_exhausted_reason"] == (
        "llm_cycle_provider_attempt_budget_exhausted"
    )
    assert "provider_error" not in failure


def test_revision_binding_failure_uses_structured_repair_class(monkeypatch):
    from live_contentops import nine_router_llm_seam_v2 as seam

    article = {
        **_article(),
        "cluster_id": "cluster-1",
        "headline_ids": ["headline-1"],
        "evidence_document_ids": ["evidence-1"],
        "x_content_grants_factual_authority": False,
    }
    observed = {}

    def routed(**kwargs):
        observed["prompt"] = kwargs["prompt"]
        invalid = {**article, "cluster_id": "changed-cluster"}
        validation = kwargs["validator"](json.dumps(invalid))
        observed["validation"] = validation
        return {
            "terminal_disposition": "ACCEPTED",
            "output": article,
        }

    monkeypatch.setattr(seam, "routed_llm_invocation", routed)

    revised = implementation._default_rolling_x_article_reviser(
        article,
        {"issues": [{"code": "reader_facing_prose"}]},
        1,
    )

    assert revised == article
    assert observed["validation"] == (
        False,
        "structured_output_malformed",
        None,
        "revision_cluster_id_changed",
    )
    assert "use publisher names rather than raw URLs as link text" in observed["prompt"]
    assert "remove generic financial-advice/informational-purpose boilerplate" in observed["prompt"]
    assert "do not repeat the same claim in adjacent paragraphs" in observed["prompt"]


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
        story_type_classifier=_story_routing,
        publication_enabled=False,
    )
    assert result["classification"] == "NO_PUBLICATION"
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False
    assert result["exact_next_blocker"] == "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED"


def test_assignment_infrastructure_failure_is_blocked_not_editorial_no_publication(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "counts": {"accepted": 1},
        },
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: {
            "status": "BLOCKED",
            "decision": None,
            "reason_code": "ROLLING_X_LEAF_ASSIGNMENT_BLOCKED",
        },
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="assignment-blocked",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        publication_enabled=False,
    )

    assert result["classification"] == "BLOCKED"
    assert result["ranked_viability"]["decision"] is None
    assert result["exact_next_blocker"] == "ROLLING_X_LEAF_ASSIGNMENT_BLOCKED"
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False


def test_resume_existing_logical_cycle_preserves_frozen_cutoff_and_input_binding(
    monkeypatch, tmp_path: Path
):
    evidence_path = tmp_path / "rolling_x_newsroom_cycle_evidence_v1.json"
    evidence_path.write_text(
        json.dumps({
            "classification": "NO_PUBLICATION",
            "run_id": "same-logical-cycle",
            "intake": {
                "cutoff_time_utc": "2026-08-08T00:00:00Z",
                "canonical_input_hash": "frozen-input-hash",
            },
            "public_write_performed": False,
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("resume must not reload or rebind sidecars")
        ),
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="same-logical-cycle",
        output_dir=tmp_path,
        cutoff_utc="2026-08-09T00:00:00Z",
        publication_enabled=False,
    )

    assert result["intake"]["cutoff_time_utc"] == "2026-08-08T00:00:00Z"
    assert result["intake"]["canonical_input_hash"] == "frozen-input-hash"
    assert result["reentry_guard"] == "existing_cycle_evidence_detected_no_automatic_retry"


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
    assert result["revision_rounds_completed"] == 1
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
    assert result["all_required_destinations_ready"] is False
    assert result["destinations"]["telegram"]["write_eligible"] is False
    assert result["destinations"]["discord"]["write_eligible"] is False

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
    assert blocked["destinations"]["x"]["status"] == "IDENTITY_MISMATCH"


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


def test_release_candidate_isolates_unready_derivative_destination(tmp_path: Path):
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
    assert result["classification"] == "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
    assert "destination_not_ready:x" not in result["blockers"]
    assert result["release_candidate_lock_verification"]["status"] == "PASS_RELEASE_CANDIDATE_LOCK"
    plan = implementation._build_rolling_x_publication_plan(
        run_id="rolling-blocked",
        output_dir=tmp_path,
        viability=viability,
        preparation=result,
        readiness=readiness,
    )
    assert "x" not in {row["destination"] for row in plan["destinations"]}
    skipped_x = next(
        row for row in plan["skipped_derivative_destinations"]
        if row["destination"] == "x"
    )
    assert skipped_x["disposition"] == "SKIPPED_NOT_READY"
    assert skipped_x["canonical_truth_affected"] is False


def test_optional_seo_analysis_and_visual_absence_does_not_block_substack(tmp_path: Path):
    assignment, viability, article, _media, editorial, readiness = _release_inputs(tmp_path)
    for field in (
        "subtitle",
        "seo_title",
        "meta_description",
        "market_mechanism",
        "policy_context",
        "cross_asset_implications",
    ):
        article[field] = ""
    article["substack_body_markdown"] = (
        "The official agency confirmed the public event in its published record."
    )
    result = implementation._prepare_rolling_x_release_candidate(
        run_id="rolling-minimum-useful-article",
        output_dir=tmp_path,
        intake={"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
        assignment=assignment,
        viability=viability,
        article=article,
        media={"assets": []},
        editorial_cycle=editorial,
        destination_readiness=readiness,
    )

    assert result["classification"] == "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
    assert result["blockers"] == []
    assert result["context"]["media"]["media_asset_count"] == 0
    assert all(
        not blocker.startswith("article_field_missing:") for blocker in result["blockers"]
    )


def test_passed_cycle_returns_plan_without_direct_backend_write(monkeypatch, tmp_path: Path):
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
    assert len(calls) == 0
    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert result["public_write_performed"] is False
    assert result["daily_app_newsroom_direct_write"] is False
    assert result["publication_lifecycle_plan"]["destinations"]
    assert result["unknown_write_detected"] is False


def test_router_outage_fallback_has_no_live_publication_authority(monkeypatch, tmp_path: Path):
    _assignment, viability, article, media, _editorial, readiness = _release_inputs(tmp_path)
    article.update(
        {
            "article_generation_method": "DETERMINISTIC_SUPPORTED_CLAIM_BRIEF",
            "article_generation_router_failure": {
                "terminal_disposition": "PROVIDER_EXHAUSTED"
            },
        }
    )
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
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("outage fallback must stop before editorial/release planning")
        ),
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="router-outage-no-publication",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=lambda value: {"article": article, "media": media},
        publication_enabled=True,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == (
        "ARTICLE_GENERATION_ROUTER_FAILURE_NO_PUBLICATION_AUTHORITY"
    )
    assert result["article_generation_publication_eligible"] is False
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False


def test_assignment_router_exception_writes_fail_closed_cycle_evidence(
    monkeypatch, tmp_path: Path
):
    from live_contentops.nine_router_llm_seam_v2 import RoutedInvocationError

    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "counts": {"accepted": 1},
        },
    )

    def fail_assignment(**_kwargs):
        raise RoutedInvocationError(
            {
                "role_task_id": "rolling_x_newsroom_assignment",
                "terminal_disposition": "LLM_TERMINAL_NON_RETRYABLE_FAILURE",
                "models_attempted_in_order": ["model-a"],
                "raw_output": "must-not-persist",
            }
        )

    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        fail_assignment,
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="assignment-router-failure",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        publication_enabled=False,
    )

    assert result["classification"] == "BLOCKED"
    assert result["exact_next_blocker"] == "ROLLING_X_GLOBAL_EDITOR_BLOCKED"
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False
    persisted = json.loads(
        (tmp_path / "rolling_x_newsroom_cycle_evidence_v1.json").read_text(
            encoding="utf-8"
        )
    )
    telemetry = persisted["assignment"]["telemetry"]
    assert telemetry["terminal_disposition"] == "LLM_TERMINAL_NON_RETRYABLE_FAILURE"
    assert telemetry["models_attempted_in_order"] == ["model-a"]
    assert "raw_output" not in telemetry
    assert "publication_lifecycle_plan" not in result


def test_revision_router_failure_writes_no_publication_evidence(monkeypatch, tmp_path: Path):
    from live_contentops.nine_router_llm_seam_v2 import RoutedInvocationError

    _assignment, viability, article, media, _editorial, readiness = _release_inputs(tmp_path)
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

    def fail_revision(_article, _review, _round_number):
        raise RoutedInvocationError(
            {
                "terminal_disposition": "BUDGET_EXHAUSTED",
                "budget_exhausted_reason": "llm_cycle_provider_attempt_budget_exhausted",
            }
        )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="revision-router-failure",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=lambda value: {"article": article, "media": media},
        editorial_reviewer=lambda value: _semantic("NEEDS_REVISION"),
        article_reviser=fail_revision,
        publication_enabled=True,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "EDITORIAL_REVISION_ROUTER_FAILURE"
    assert result["editorial_cycle"]["publication_authority_granted"] is False
    assert "publication_lifecycle_plan" not in result
    persisted = json.loads(
        (tmp_path / "rolling_x_newsroom_cycle_evidence_v1.json").read_text(encoding="utf-8")
    )
    assert persisted["exact_next_blocker"] == "EDITORIAL_REVISION_ROUTER_FAILURE"
    assert persisted["editorial_cycle"]["review_history"][0]["revision"]["status"] == (
        "FAILED_ROUTER"
    )


def test_old_backend_unknown_write_fixture_cannot_bypass_plan_coordinator(
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
    assert result["unknown_write_detected"] is False
    assert result["public_write_performed"] is False
    assert result["daily_app_newsroom_direct_write"] is False
    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"


def test_default_cycle_uses_real_targeted_evidence_adapter(monkeypatch, tmp_path: Path):
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "counts": {"accepted": 1},
    }
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": [
            {
                "cluster_id": "c1",
                "rank": 1,
                "headline_ids": ["h1"],
                "market_sensitive": True,
                "article_mode": "breaking",
            }
        ],
    }
    seen = []

    class FakeAdapter:
        def __init__(self, **kwargs):
            seen.append(("init", kwargs))

        def __call__(self, request):
            seen.append(("call", request))
            return {
                "status": "BLOCKED",
                "cluster_id": request["cluster_id"],
                "headline_ids": request["headline_ids"],
                "provided_evidence_capabilities": [],
                "evidence_documents": [],
                "capital_chronicle_authority_verified": False,
                "numeric_evidence_required": True,
                "blockers": ["exact_governed_story_evidence_missing"],
                "publication_authority": False,
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
        "live_contentops.rolling_x_targeted_evidence_adapter_v1.RollingXTargetedEvidenceAdapter",
        FakeAdapter,
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="default-adapter",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        capital_chronicle_root=Path("read-only-cc-root"),
        story_type_classifier=_story_routing,
        publication_enabled=False,
    )

    assert [kind for kind, _ in seen] == ["init", "call"]
    assert seen[0][1]["capital_chronicle_root"] == Path("read-only-cc-root")
    assert result["classification"] == "NO_PUBLICATION"
    assert result["ranked_viability"]["rank_attempts"][0]["blockers"]


def test_canonical_cycle_classifies_accepted_shortlist_once_without_external_mapping(
    monkeypatch, tmp_path: Path
):
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "counts": {"accepted": 2},
        "headlines": [],
    }
    clusters = [
        {"cluster_id": "c1", "rank": 1, "headline_ids": ["h1"], "article_mode": "breaking"},
        {"cluster_id": "c2", "rank": 2, "headline_ids": ["h2"], "article_mode": "breaking"},
    ]
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": clusters,
    }
    classifier_calls = []
    viability_calls = []
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: assignment,
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: viability_calls.append(kwargs) or {
            "status": "NO_PUBLICATION",
            "reason_code": "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED",
        },
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="automatic-story-routing",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        rolling_input=intake,
        story_type_classifier=lambda **kwargs: classifier_calls.append(kwargs)
        or _story_routing(kwargs["clusters"]),
        evidence_acquirer=lambda request: (_ for _ in ()).throw(
            AssertionError("patched viability owns this focused seam")
        ),
        publication_enabled=False,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert len(classifier_calls) == 1
    assert [row["cluster_id"] for row in classifier_calls[0]["clusters"]] == ["c1", "c2"]
    assert viability_calls[0]["story_type_by_cluster"] == {
        "c1": "regulatory_fiscal_event",
        "c2": "regulatory_fiscal_event",
    }
    assert result["story_routing"]["semantic_routing_grants_authority"] is False
    assert (tmp_path / "rolling_x_story_routing_v1.json").is_file()


def test_canonical_cycle_fails_closed_on_unknown_or_duplicate_classifier_ids(
    monkeypatch, tmp_path: Path
):
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": [
            {"cluster_id": "c1", "rank": 1, "headline_ids": ["h1"], "article_mode": "breaking"},
            {"cluster_id": "c2", "rank": 2, "headline_ids": ["h2"], "article_mode": "breaking"},
        ],
    }
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: assignment,
    )
    for label, stories, mapping in (
        (
            "unknown",
            [
                {"cluster_id": "c1", "story_type": "regulatory_fiscal_event"},
                {"cluster_id": "unknown", "story_type": "regulatory_fiscal_event"},
            ],
            {"c1": "regulatory_fiscal_event", "unknown": "regulatory_fiscal_event"},
        ),
        (
            "duplicate",
            [
                {"cluster_id": "c1", "story_type": "regulatory_fiscal_event"},
                {"cluster_id": "c1", "story_type": "regulatory_fiscal_event"},
            ],
            {"c1": "regulatory_fiscal_event", "c2": "regulatory_fiscal_event"},
        ),
    ):
        output = tmp_path / label
        result = implementation._run_rolling_x_newsroom_cycle(
            run_id=f"classifier-{label}",
            output_dir=output,
            cutoff_utc="2026-08-08T00:00:00Z",
            rolling_input={"schema_version": "capital_chronicle.rolling_x_headline_input.v1", "headlines": []},
            story_type_classifier=lambda **_kwargs: {
                "stories": stories,
                "story_type_by_cluster": mapping,
                "semantic_routing_grants_authority": False,
            },
            evidence_acquirer=lambda request: (_ for _ in ()).throw(
                AssertionError("invalid classifier output must stop before evidence")
            ),
            publication_enabled=False,
        )
        assert result["classification"] == "BLOCKED"
        assert result["exact_next_blocker"] == "STORY_TYPE_CLASSIFICATION_BLOCKED"
        assert result["ranked_viability"]["rank_attempts"] == []


def test_canonical_cycle_forwards_frozen_input_and_exact_checkpoints(
    monkeypatch, tmp_path: Path
):
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "canonical_input_hash": "frozen-input-hash",
        "cutoff_time_utc": "2026-08-08T09:18:54Z",
        "counts": {"accepted": 1},
    }
    leaf_checkpoints = {"leaf-1": {"checkpoint": "exact"}}
    global_checkpoint = {"checkpoint": "exact-global"}
    calls = []
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("frozen resume must not reload X sidecars")
        ),
    )

    def assign(**kwargs):
        calls.append(kwargs)
        return {
            "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
            "status": "SUCCESS",
            "decision": "NO_PUBLICATION",
            "ranked_clusters": [],
        }

    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        assign,
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="frozen-resume",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T09:18:54Z",
        rolling_input=intake,
        leaf_checkpoints=leaf_checkpoints,
        global_checkpoint=global_checkpoint,
        assignment_provider_call=lambda *_args: (_ for _ in ()).throw(
            AssertionError("assignment provider call forbidden")
        ),
        publication_enabled=False,
    )

    assert len(calls) == 1
    assert calls[0]["rolling_input"] == intake
    assert calls[0]["leaf_checkpoints"] is leaf_checkpoints
    assert calls[0]["global_checkpoint"] is global_checkpoint
    assert result["intake"]["canonical_input_hash"] == "frozen-input-hash"
    assert result["classification"] == "NO_PUBLICATION"
