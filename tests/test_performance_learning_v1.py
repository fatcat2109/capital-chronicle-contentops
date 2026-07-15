from dataclasses import replace
from pathlib import Path
import pytest
from live_contentops import manual_publish_record_metrics_ledger_contract as ledger
from live_contentops import performance_learning_v1 as learning


def _source():
    packet = ledger.build_contract_packet()
    return packet.manual_publish_records[0], packet.manual_metrics_records[0]


def _identity(platform_id=None, suffix="a"):
    publish, _ = _source()
    return learning.build_content_identity(
        evidence_packet_id=f"packet-{suffix}", story_cluster_id=f"cluster-{suffix}",
        candidate_id=f"candidate-{suffix}", assignment_decision_id=f"assignment-{suffix}",
        content_item_id=f"content-{suffix}", article_version_id=f"article-{suffix}",
        headline_variant_id=f"headline-{suffix}", visual_bundle_id=f"visual-{suffix}",
        platform_variant_id=f"variant-{suffix}", platform_id=platform_id or publish.platform_id,
        publication_window_id=f"window-{suffix}", experiment_id=f"experiment-{suffix}",
        canonical_url_reference=f"https://example.invalid/canonical/{suffix}",
        platform_post_reference=f"post-{suffix}", platform_url_reference=f"https://example.invalid/post/{suffix}",
    )


def _snapshot(identity=None, **metric_changes):
    publish, metrics = _source()
    if metric_changes:
        metrics = replace(metrics, **metric_changes)
    return learning.build_performance_snapshot(
        identity=identity or _identity(), publish_record=publish, metrics_record=metrics,
        metric_name="impressions", metric_definition="Manual displayed impression count.",
        metric_scope="single operator-attested post observation",
    )


def test_contract_packet_is_deterministic_and_terminates_with_real_evidence_no_idea():
    first, second = learning.build_contract_packet(), learning.build_contract_packet()
    assert first == second
    assert first.packet_hash == second.packet_hash
    assert first.all_records_manual_only and first.all_learning_review_only
    assert first.no_collection_performed and first.no_api_verification and first.no_scraping
    assert first.no_automatic_editorial_mutation and first.no_auto_publish and first.no_dispatch
    assert first.terminal_classification == learning.TERMINAL_NO_IDEA
    assert first.source_bindings["candidate_id"] == "cc-candidate-120438cc800db7f941be"
    assert first.source_bindings["cluster_id"] == "cc-cluster-7aa53a08e0a4b35873af"
    assert len(first.identities) == len(first.snapshots) == 9
    assert {snapshot.platform_id for snapshot in first.snapshots} == {
        "discord", "facebook_page", "instagram_business", "linkedin", "substack",
        "telegram", "threads", "x", "youtube",
    }
    assert all(snapshot.metric_value is None for snapshot in first.snapshots)
    assert all(snapshot.collection_status == learning.COLLECTION_UNAVAILABLE for snapshot in first.snapshots)
    retrospective, idea = first.retrospectives[0], first.idea_candidates[0]
    assert retrospective.retrospective_status == learning.RETROSPECTIVE_UNAVAILABLE
    assert retrospective.available_metric_count == 0
    assert idea.candidate_type == learning.IDEA_NO_IDEA
    assert "already represented" in idea.hypothesis
    assert "raw-secret" not in learning._json(first)


def test_identity_binds_required_references_without_public_authority():
    identity = _identity()
    assert identity.identity_status == "VALID"
    assert identity.evidence_packet_schema_version == "capital_chronicle_content_evidence_packet.v2"
    assert len(identity.canonical_url_hash) == len(identity.platform_post_id_hash) == 64
    assert identity.safety_flags["publication_authority_granted"] is False
    blocked = _identity(suffix="missing")
    blocked = replace(blocked, content_item_id="")
    assert blocked.content_item_id == ""


def test_snapshot_rejects_invalid_or_non_manual_metric_provenance():
    baseline = _snapshot()
    assert not baseline.blocked_reasons
    publish, metrics = _source()
    cases = (
        (replace(metrics, metric_values_are_api_verified=True), "api_verified_metric_rejected"),
        (replace(metrics, metric_values_are_scraped=True), "scraped_metric_rejected"),
        (replace(metrics, metric_values_are_operator_attested=False), "manual_metric_not_operator_attested"),
        (replace(metrics, source_payload_hash="wrong"), "manual_metrics_payload_hash_mismatch"),
        (replace(metrics, platform_id="wrong"), "manual_metrics_platform_mismatch"),
        (replace(metrics, metrics={**metrics.metrics, "impressions": -1}), "metric_value_invalid"),
        (replace(metrics, metric_observed_at_epoch=1), "metric_observed_before_publication"),
        (replace(metrics, metric_recorded_at_epoch=1), "metric_recorded_before_observation"),
    )
    for invalid, expected in cases:
        snapshot = learning.build_performance_snapshot(
            identity=_identity(), publish_record=publish, metrics_record=invalid,
            metric_name="impressions", metric_definition="manual", metric_scope="manual",
        )
        assert snapshot.collection_status == "BLOCKED"
        assert expected in snapshot.blocked_reasons


def test_snapshot_append_only_rejects_material_collision():
    snapshot = _snapshot()
    assert learning.append_snapshot((), snapshot) == (snapshot,)
    assert learning.append_snapshot((snapshot,), snapshot) == (snapshot,)
    collision = replace(snapshot, metric_value=snapshot.metric_value + 1)
    with pytest.raises(ValueError, match="append_only_snapshot_collision"):
        learning.append_snapshot((snapshot,), collision)


def test_retrospective_blocks_mixed_or_invalid_cohorts_and_never_declares_winner():
    first = _snapshot(_identity(suffix="first"))
    second = _snapshot(_identity(platform_id="another-platform", suffix="second"))
    mixed = learning.build_content_retrospective((first, second), cohort_definition="same-post comparisons")
    assert "mixed_platform_cohort_rejected" in mixed.blocked_reasons
    assert mixed.retrospective_status == "BLOCKED"
    assert mixed.can_update_scheduler is False
    one = learning.build_content_retrospective((first,), cohort_definition="manual cohort")
    assert one.retrospective_status == learning.RETROSPECTIVE_INCONCLUSIVE
    assert "winner" not in one.summary.lower()
    assert all(effect in one.forbidden_effects_checked for effect in learning.FORBIDDEN_LEARNING_EFFECTS)


def test_idea_candidates_are_human_review_only_and_cannot_mutate_editorial_work():
    idea = learning.build_idea_candidate(learning.build_content_retrospective((_snapshot(),), cohort_definition="manual cohort"))
    assert idea.required_human_review is True
    assert idea.operator_status == learning.OPERATOR_REVIEW_REQUIRED
    assert not any((idea.can_create_editorial_brief, idea.can_auto_generate_content, idea.can_update_scheduler, idea.can_update_writer_guidance, idea.can_update_platform_defaults, idea.can_auto_publish, idea.can_dispatch, idea.public_postable))
    assert all(value is False for key, value in idea.safety_flags.items() if key.startswith("can_") or key in {"network_performed", "browser_session_used", "automatic_editorial_mutation"})


def test_artifact_writer_is_scoped_and_source_has_no_live_integrations(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    result = learning.write_artifacts(repo_root=repo)
    assert Path(result["packet_path"]).relative_to(repo) == learning.DOC_REL_DIR / learning.PACKET_FILENAME
    assert Path(result["runbook_path"]).relative_to(repo) == learning.DOC_REL_DIR / learning.RUNBOOK_FILENAME
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_contentops_performance_learning_v1"):
        learning.write_artifacts(repo_root=repo, output_dir=tmp_path / "other")
    text = Path(learning.__file__).read_text(encoding="utf-8-sig")
    forbidden = ("import requests", "from requests", "import urllib", "from urllib", "import socket", "from socket", "os.environ", "dotenv", "playwright", "selenium", "BeautifulSoup", "subprocess", "webbrowser", "schedule.every")
    for needle in forbidden:
        assert needle not in text
    for needle in ("network_performed", "browser_session_used", "automatic_editorial_mutation", "llm_provider_called"):
        assert needle in text


def test_real_content_loop_reads_bodies_and_examines_three_governed_mechanisms():
    first = learning.build_real_content_idea_loop()
    second = learning.build_real_content_idea_loop()
    assert first == second
    retrospective = first["retrospective"]
    assert retrospective["article_word_count_read"] >= 500
    assert all(retrospective["article_coverage"].values())
    assert retrospective["native_derivative_count_examined"] == 8
    assert retrospective["metric_status"] == learning.COLLECTION_UNAVAILABLE
    assert retrospective["performance_conclusion"] is None
    assert first["backlog"]["examined_idea_count"] == 3
    assert len(first["generated_ideas"]["records"]) == 1
    assert len(first["rejected_ideas"]["records"]) == 2


def test_real_content_loop_assigns_evidence_refresh_not_article_or_public_write():
    result = learning.build_real_content_idea_loop()
    idea = result["generated_ideas"]["records"][0]
    assert idea["status"] == "ASSIGNABLE_FOR_EVIDENCE_REFRESH_ONLY"
    assert idea["duplicate_published_cluster_suppressed"] is True
    assert idea["new_article_authorized"] is False
    brief = result["briefs"]["records"][0]
    assert len(brief["required_existing_claim_ids"]) == 4
    assert not brief["can_draft_article"]
    assert not brief["can_publish"]
    assert not brief["can_dispatch"]
    assignment = result["assignment"]
    assert assignment["assignment_status"] == "INTERNAL_RESEARCH_ASSIGNMENT_CREATED"
    assert assignment["public_write_performed"] is False
    assert assignment["publication_authority_granted"] is False


def test_blocked_pool_mechanisms_preserve_real_ids_and_blockers():
    result = learning.build_real_content_idea_loop()
    records = {record["source_candidate_id"]: record for record in result["rejected_ideas"]["records"]}
    catalyst = records["cc-candidate-d68a10790ca2d7f74c38"]
    macro = records["cc-candidate-3f705fbf747b1838ca10"]
    assert catalyst["status"] == "REJECT_NOT_REPORTABLE"
    assert "story_scoped_reporting_authority_required" in catalyst["blockers"]
    assert macro["status"] == "HOLD_AUTHORITY_GAP"
    assert "real_regime_undetermined" in macro["blockers"]
    assert not catalyst["reporting_allowed"] and not macro["reporting_allowed"]
    assert catalyst["numeric_claims"] == macro["numeric_claims"] == []


def test_derivative_comparison_is_content_only_and_not_performance_ranking():
    comparison = learning.build_real_content_idea_loop()["derivative_comparison"]
    assert comparison["metric_status"] == learning.COLLECTION_UNAVAILABLE
    assert comparison["comparison_basis"] == "literal content coverage only; not performance"
    assert len(comparison["rows"]) == 8
    assert all(row["public_destination_status"] == "SUCCESS" for row in comparison["rows"])
    assert all(len(row["payload_text_sha256"]) == 64 for row in comparison["rows"])


def test_real_loop_manifest_and_writer_are_deterministic_and_scoped(tmp_path):
    manifest = learning.build_real_content_idea_loop()["manifest"]
    assert manifest["terminal_classification"] == learning.REAL_LOOP_TERMINAL
    assert manifest["pinned_upstream"]["commit_sha"] == learning.PINNED_UPSTREAM_COMMIT
    assert manifest["pinned_upstream"]["pool_artifact_sha256"].startswith("e4f60146")
    assert manifest["real_article_body_read"] and manifest["real_native_payloads_read"]
    assert manifest["public_write_performed"] is False
    assert manifest["task_4_started"] is False
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_real_content_idea_loop"):
        learning.write_real_content_idea_loop_artifacts(repo, tmp_path / "other")


def test_adaptive_treasury_authority_uses_only_final_public_body():
    authority = learning.normalize_treasury_learning_authority()
    assert authority["canonical_slug"] == "treasury-yield-curve-edges-wider"
    assert authority["canonical_url"].endswith("/p/treasury-yield-curve-edges-wider")
    assert authority["learning_body_sha256"] == learning.TREASURY_FINAL_ACCEPTED_BODY_SHA256
    assert authority["final_public_body"]["accepted_for_learning"] is True
    assert authority["stale_article_export"]["accepted_for_learning"] is False
    assert authority["historical_embedded_manifest_body"]["accepted_for_learning"] is False
    assert authority["pre_final_repair_public_body"]["accepted_for_learning"] is False
    assert authority["stale_body_fallback_allowed"] is False
    for stale_hash in (
        learning.TREASURY_STALE_ARTICLE_EXPORT_SHA256,
        learning.TREASURY_STALE_DECLARED_EXPORT_SHA256,
        learning.TREASURY_HISTORICAL_MANIFEST_BODY_SHA256,
        learning.TREASURY_PRE_FINAL_REPAIR_BODY_SHA256,
    ):
        with pytest.raises(ValueError, match="stale_treasury_body_rejected_for_learning"):
            learning.normalize_treasury_learning_authority(observed_body_sha256=stale_hash)


def test_adaptive_pool_binding_is_exact_and_fails_closed():
    artifacts = learning.build_adaptive_newsroom_learning_loop()
    binding = artifacts["replay"]["upstream_candidate_pool_binding"]
    assert binding == artifacts["manifest"]["upstream_candidate_pool_binding"]
    assert binding["repository"] == "fatcat2109/Headline-Raw-data-json"
    assert binding["branch"] == "main"
    assert binding["commit_sha"] == "9bff5453a118486740ccc8957fcabd3c139fb3d2"
    assert binding["artifact_path"] == learning.UPSTREAM_POOL_ARTIFACT_PATH
    assert binding["git_blob_sha1"] == learning.UPSTREAM_POOL_BLOB_SHA1
    assert binding["file_sha256"] == learning.UPSTREAM_POOL_FILE_SHA256
    assert binding["pool_logical_hash"] == learning.UPSTREAM_POOL_LOGICAL_HASH
    assert binding["read_only"] is True
    root = Path(learning.__file__).resolve().parents[1]
    pool = learning._read_json(root, learning.POOL_REL_PATH)
    tampered = {**pool, "logical_hash": "0" * 64}
    with pytest.raises(ValueError, match="latest_upstream_pool_logical_hash_mismatch"):
        learning.build_adaptive_newsroom_learning_loop(candidate_pool=tampered)


def _adaptive_candidate(relationship="new_phase", *, authorized=True, candidate_id="candidate", cluster_id="cluster"):
    return {
        "candidate_id": candidate_id,
        "cluster_id": cluster_id,
        "relationship": relationship,
        "eligible": authorized,
        "claim_permissions": {"reporting_allowed": authorized},
        "blockers": [] if authorized else ["story_scoped_reporting_authority_required"],
    }


@pytest.mark.parametrize("relationship", ["material_update", "confirmation", "contradiction", "correction"])
def test_adaptive_outcome_classifier_detects_governed_update_types(relationship):
    outcomes = learning.classify_adaptive_outcomes(
        _adaptive_candidate(relationship),
        published_candidate_ids=set(),
        published_cluster_ids=set(),
        packaging_gap_present=False,
    )
    assert outcomes[relationship] is True
    assert outcomes["duplicate"] is False
    assert outcomes["insufficient_authority"] is False


def test_adaptive_outcome_classifier_covers_new_phase_refresh_gap_duplicate_filler_and_authority():
    published_candidate_ids, published_cluster_ids = {"published"}, {"published-cluster"}
    refresh = learning.classify_adaptive_outcomes(
        _adaptive_candidate(candidate_id="published", cluster_id="published-cluster"),
        published_candidate_ids=published_candidate_ids,
        published_cluster_ids=published_cluster_ids,
        packaging_gap_present=True,
    )
    assert refresh["new_phase"] and refresh["evergreen_refresh"]
    assert refresh["packaging_gap"] and refresh["duplicate"]
    assert not refresh["filler"]
    filler = learning.classify_adaptive_outcomes(
        _adaptive_candidate(candidate_id="published", cluster_id="published-cluster"),
        published_candidate_ids=published_candidate_ids,
        published_cluster_ids=published_cluster_ids,
        packaging_gap_present=False,
    )
    assert filler["duplicate"] and filler["filler"]
    assert not filler["evergreen_refresh"] and not filler["packaging_gap"]
    insufficient = learning.classify_adaptive_outcomes(
        _adaptive_candidate(authorized=False),
        published_candidate_ids=set(),
        published_cluster_ids=set(),
        packaging_gap_present=False,
    )
    assert insufficient["new_phase"] and insufficient["insufficient_authority"]


def test_adaptive_shadow_replay_is_deterministic_inspectable_and_no_publication():
    first = learning.build_adaptive_newsroom_learning_loop()
    second = learning.build_adaptive_newsroom_learning_loop()
    assert first == second
    decision, replay, manifest = first["decision"], first["replay"], first["manifest"]
    assert decision["schema_version"] == "contentops.learning_decision.v1"
    assert decision["learning_decision_id"].endswith(decision["logical_hash"][:24])
    assert decision["sample_size"] == 9
    assert decision["distinct_content_count"] == 1
    assert len(decision["input_snapshot_ids"]) == 9
    assert len(decision["input_gap_ids"]) == 2
    assert len(decision["input_idea_ids"]) == 1
    assert decision["feature_availability"]["performance_metric_values"] is False
    assert decision["confidence"] == "BOUNDED_CONTENT_AND_AUTHORITY_ONLY_NO_PERFORMANCE_METRICS"
    assert decision["operator_state"] == "OPERATOR_REVIEW_REQUIRED_SHADOW_ONLY"
    assert set(decision["detected_outcomes"]) == {
        "new_phase", "evergreen_refresh", "packaging_gap", "duplicate", "insufficient_authority"
    }
    assert len(replay["candidate_records"]) == 3
    assert [record["shadow_rank"] for record in replay["candidate_records"]] == [1, 2, 3]
    assert all("feature_values" in record and "penalties" in record for record in replay["candidate_records"])
    assert all(record["ranking_reasons"] for record in replay["candidate_records"])
    assert all(record["publication_selected"] is False for record in replay["candidate_records"])
    assert len(decision["no_publication_decisions"]) == 3
    assert all(row["decision"] == "NO_PUBLICATION" for row in decision["no_publication_decisions"])
    assert manifest["publication_count"] == manifest["policy_mutation_count"] == 0
    assert manifest["terminal_classification"] == learning.ADAPTIVE_TERMINAL
    assert manifest["next_action"] == learning.ADAPTIVE_NEXT_ACTION


def test_adaptive_learning_firewall_is_complete_and_proposals_remain_review_only():
    decision = learning.build_adaptive_newsroom_learning_loop()["decision"]
    assert tuple(decision["forbidden_effects_checked"]) == learning.ADAPTIVE_FORBIDDEN_EFFECTS
    flags = decision["safety_flags"]
    assert flags["shadow_mode"] and flags["operator_review_required"]
    assert flags["learning_firewall_enforced"] and flags["final_public_body_authority_enforced"]
    for key, value in flags.items():
        if key.endswith("_mutated") or key.endswith("_performed") or key in {
            "network_performed", "browser_session_used", "credential_accessed",
            "automatic_assignment_created",
        }:
            assert value is False, key
    assert all(proposal["numeric_prior_delta"] is None for proposal in decision["proposed_ranking_prior_changes"])
    assert all(proposal["numeric_prior_delta"] is None for proposal in decision["proposed_publication_window_changes"])
    for key in ("proposed_headline_changes", "proposed_visual_changes", "proposed_format_changes"):
        assert all(proposal["automatic_change"] is False for proposal in decision[key])


def test_adaptive_writer_is_scoped_and_artifacts_match_rebuild(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    source_root = Path(learning.__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_adaptive_newsroom_learning_loop"):
        learning.write_adaptive_newsroom_learning_artifacts(source_root, tmp_path / "other")
    result = learning.write_adaptive_newsroom_learning_artifacts(source_root)
    rebuilt = learning.build_adaptive_newsroom_learning_loop(source_root)
    assert result["artifacts"] == rebuilt
    for key, path in result["paths"].items():
        assert Path(path).is_file(), key
    assert learning._digest(rebuilt["decision"]) == rebuilt["manifest"]["artifact_hashes"]["decision"]
    assert learning._digest(rebuilt["replay"]) == rebuilt["manifest"]["artifact_hashes"]["replay"]
