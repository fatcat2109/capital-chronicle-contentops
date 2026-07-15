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


def test_contract_packet_is_deterministic_redacted_and_inconclusive():
    first, second = learning.build_contract_packet(), learning.build_contract_packet()
    assert first == second
    assert first.packet_hash == second.packet_hash
    assert first.all_records_manual_only and first.all_learning_review_only
    assert first.no_collection_performed and first.no_api_verification and first.no_scraping
    assert first.no_automatic_editorial_mutation and first.no_auto_publish and first.no_dispatch
    snapshot = first.snapshots[0]
    retrospective, idea = first.retrospectives[0], first.idea_candidates[0]
    assert snapshot.authority_class == learning.AUTHORITY_MANUAL_OPERATOR_ENTRY
    assert snapshot.collection_status == learning.COLLECTION_RECORDED_REVIEW_ONLY
    assert retrospective.retrospective_status == learning.RETROSPECTIVE_INCONCLUSIVE
    assert retrospective.sample_size == 1 and retrospective.distinct_content_identity_count == 1
    assert idea.candidate_type == "observation_plan"
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
