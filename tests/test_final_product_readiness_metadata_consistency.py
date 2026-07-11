from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "docs/status/current_project_status.json"
PLAN = ROOT / "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN"
RUN = ROOT / "docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_status_records_blocked_final_closure_authority() -> None:
    status = _json(STATUS)
    assert status["latest_accepted_task"] == "TASK_CONTENTOPS_GENERIC_EVIDENCE_FRESHNESS_VISUAL_EDITORIAL_FABRIC_V2"
    assert status["current_task_classification"] == "BLOCKED_FINAL_AUTOMATION_PIPELINE_CLOSURE"
    assert status["upstream_readiness"]["dqr_status"] == "degraded"
    assert status["upstream_readiness"]["reporting_allowed"] is False
    assert status["v1_0_tag_exists"] is False


def test_current_evidence_separates_transport_from_quality() -> None:
    evidence = _json(RUN / "run_evidence_v1.json")
    assert evidence["classification"] == "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1"
    assert evidence["current_quality_classification"] == "PASS_RELIABILITY_HARDENING_WITH_PRESERVED_LEGACY_X_THREADS_OUTPUT_DEFECTS"
    assert evidence["results"]["x"]["quality_status"].startswith("FAIL_LIVE_CHAIN")
    assert evidence["results"]["threads"]["quality_status"].startswith("FAIL_LIVE_ROOT")
    assert evidence["v3_safety"]["new_substack_article_published"] is False
    hardening = _json(RUN / "reliability_hardening_evidence_v3.json")
    assert hardening["editorial_gate"]["classification"] == "PASS"
    assert hardening["editorial_gate"]["deterministic_pass"] is True
    assert hardening["editorial_gate"]["llm_semantic_pass"] is True
    assert hardening["editorial_gate"]["llm_cannot_override_deterministic_blockers"] is True
    assert len(hardening["editorial_gate"]["source_continuity"]["media_sha256"]) == 3


def test_linkedin_pair_and_instagram_semantics_are_unambiguous() -> None:
    pair = _json(RUN / "linkedin_activity_pair_reconciliation_v1.json")
    status = _json(STATUS)
    assert pair["relationship"] == "EARLIER_ACCEPTED_AND_LATEST_CORRECTED_IN_PLACE"
    assert pair["third_post_created"] is False
    assert pair["accepted_activity"]["post_id"] == "7481289145206644736"
    assert pair["latest_activity_after"]["post_id"] == "7481311616265895936"
    instagram = status["platform_matrix"]["instagram_business"]
    assert instagram["quality_status"] == "PASS_FEED_CAPTION_URL_TEXT"
    assert instagram["caption_link_clickable"] is False


def test_semantic_variants_use_three_posts_and_three_visuals() -> None:
    packet = _json(RUN / "planned_semantic_variants_v1.json")
    for platform in ("x", "threads"):
        layout = packet["planned_layouts"][platform]
        metrics = layout["quality_metrics"]
        assert len(layout["posts"]) == 3
        assert metrics["reply_count"] == 2
        assert metrics["sentence_boundary_pass"] is True
        assert metrics["orphan_fragment_count"] == 0
        assert metrics["visual_distribution_pass"] is True
        assert metrics["complete_article_visual_count"] == 3


def test_video_matrix_is_capability_only() -> None:
    packet = _json(RUN / "video_platform_capability_matrix_v1.json")
    assert packet["default_article_youtube_surface"] == "youtube_community"
    assert packet["public_or_private_upload_performed"] is False
    assert packet["rows"]["tiktok_native"]["app_credentials_present"] is True
    assert packet["rows"]["tiktok_native"]["oauth_authorization_status"] == "NOT_AUTHORIZED"


def test_platform_contract_contains_failure_resolution_map() -> None:
    contract = _json(PLAN / "platform_delivery_contract_v1.json")
    failure_map = contract["failure_resolution_map"]
    for platform in ("substack", "telegram", "x", "discord", "linkedin", "facebook_page", "instagram_business", "threads", "youtube_community", "video_capabilities"):
        row = failure_map[platform]
        assert row["adapter"]
        assert row["payload_compiler"]
        assert row["public_readback"]
        assert row["idempotency_ledger"]
        assert row["focused_tests"]
        assert row["common_failures"]
        assert row["allowed_recovery"]
        assert row["forbidden_fallback"]
        assert row["evidence"]
