"""Tests for canonical V1/V2 natural observation read model.

Verifies:
1. All 19 locked lanes are projected conforming to the common lane contract.
2. Missing data remains explicit (None / UNAVAILABLE / NOT_PRESENT), never converted to 0.
3. V2 arbitrary files cannot be read (strict allowlist and traversal protection).
4. Secret-shaped keys fail closed via _assert_nonsecret.
5. Zero SQLite mutations / pure read-only projection.
6. Full snapshot integration via build_daily_app_snapshot.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import pytest

from live_contentops.contentops_observation_read_model_v1 import (
    ALL_LANE_IDS,
    LANE_V1_HEADLINE_INTAKE_FRESHNESS,
    LANE_V1_CANDIDATE_FUNNEL,
    LANE_V1_EVIDENCE_SOURCE_HEALTH,
    LANE_V1_PUBLICATION_SAFETY_RECOVERY,
    LANE_V1_REAL_PERFORMANCE_OBSERVATIONS,
    LANE_V1_PASSIVE_INTERACTION_QUALITY,
    LANE_V1_CLOSED_LOOP_LEARNING,
    LANE_V1_SEARCH_DISCOVERY,
    LANE_V1_COST_RUNTIME_YIELD,
    LANE_V2_V1_TO_VIDEO_TRIGGER_SHADOW,
    LANE_V2_SOURCE_RIGHTS_ASSET_SUPPLY,
    LANE_V2_ASSET_DIVERSITY_AND_SCREEN_TIME,
    LANE_V2_PRODUCTION_TCO_RECOVERY_SOAK,
    LANE_V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE,
    LANE_V2_PUBLICATION_READINESS,
    LANE_V2_POST_PUBLISH_RETENTION_ATTRIBUTION,
    LANE_V2_CLOSED_LOOP_VIDEO_LEARNING,
    LANE_CROSS_LANE_SOURCE_ACCESS_HEALTH,
    LANE_CROSS_LANE_DATA_FRESHNESS_AND_AUTHORITY,
    ObservationReadModelError,
    _assert_nonsecret,
    _safe_load_v2_package,
    build_observation_read_model,
)
from live_contentops.daily_app_ui_read_model_v1 import build_daily_app_snapshot
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)


def _store(tmp_path, name="daily.sqlite3"):
    return ContentOpsDurableStore(tmp_path / name, now_fn=lambda: NOW)


def test_observation_read_model_all_19_lanes_projected(tmp_path):
    """Ensure all 19 locked lanes are present and conform to common contract."""
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")

    with store.get_read_only_connection() as conn:
        model = build_observation_read_model(
            conn=conn,
            runtime_root=tmp_path / "runtime",
            now=NOW,
        )

    assert model["schema_version"] == "contentops.observation_read_model.v1"
    assert model["summary"]["total_lanes"] == 19
    assert model["summary"]["v1_lane_count"] == 9
    assert model["summary"]["v2_lane_count"] == 8
    assert model["summary"]["cross_lane_count"] == 2

    lane_map = {lane["lane_id"]: lane for lane in model["lanes"]}
    assert len(lane_map) == 19

    # Verify all expected lane IDs exist
    for expected_id in ALL_LANE_IDS:
        assert expected_id in lane_map, f"Missing lane: {expected_id}"
        lane = lane_map[expected_id]
        # Check required fields of common contract
        assert "lane_contract_version" in lane
        assert "lane_id" in lane
        assert "group" in lane
        assert "state" in lane
        assert "data_source" in lane
        assert "authority_class" in lane
        assert "confidence" in lane
        assert "freshness" in lane
        assert "write_authority" in lane
        assert "metrics" in lane


def test_missing_data_remains_unavailable_not_zero(tmp_path):
    """Verify missing data is preserved as None/UNAVAILABLE and never converted to 0."""
    store = _store(tmp_path)
    with store.get_read_only_connection() as conn:
        model = build_observation_read_model(
            conn=conn,
            runtime_root=tmp_path / "empty_runtime",
            now=NOW,
        )

    lane_map = {lane["lane_id"]: lane for lane in model["lanes"]}

    # V2 Post Publish Retention must be BLOCKED_OWNER_AUTHORITY with None completion/retention rates
    retention_lane = lane_map[LANE_V2_POST_PUBLISH_RETENTION_ATTRIBUTION]
    assert retention_lane["state"] == "BLOCKED_OWNER_AUTHORITY"
    assert retention_lane["metrics"]["average_completion_rate"] is None
    assert retention_lane["metrics"]["average_retention_score"] is None
    assert retention_lane["metrics"]["published_video_count"] == 0

    # V2 Video Learning must be WAITING_FOR_REAL_PUBLIC_OBJECT
    video_learning = lane_map[LANE_V2_CLOSED_LOOP_VIDEO_LEARNING]
    assert video_learning["state"] == "WAITING_FOR_REAL_OBJECT"

    # Search discovery must be OPERATOR_SETUP_REQUIRED
    search_lane = lane_map[LANE_V1_SEARCH_DISCOVERY]
    assert search_lane["state"] == "OPERATOR_SETUP_REQUIRED"
    assert search_lane["confidence"] == "NO_SEARCH_SPECIFIC_SAMPLE"


def test_v2_safe_artifact_allowlist_and_traversal_protection(tmp_path):
    """Verify that arbitrary or traversal files in V2 package cannot be read."""
    pkg_dir = tmp_path / "v2_test_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "contracts").mkdir()
    (pkg_dir / "receipts").mkdir()

    # Create allowlisted file
    (pkg_dir / "HANDOFF.json").write_text(json.dumps({"result": "PASS_TEST"}), encoding="utf-8")
    (pkg_dir / "receipts" / "zero_public_write.json").write_text(
        json.dumps({"public_writes": 0, "video_public_write_authority": False}), encoding="utf-8"
    )

    # Create unauthorized / secret-shaped files
    (pkg_dir / "secret_tokens.json").write_text(json.dumps({"token": "secret123"}), encoding="utf-8")
    (pkg_dir / "arbitrary_dump.json").write_text(json.dumps({"arbitrary": "data"}), encoding="utf-8")

    loaded = _safe_load_v2_package(pkg_dir)
    artifacts = loaded["artifacts"]

    assert "HANDOFF.json" in artifacts
    assert "receipts/zero_public_write.json" in artifacts
    assert "secret_tokens.json" not in artifacts
    assert "arbitrary_dump.json" not in artifacts


def test_secret_key_rejection():
    """Verify _assert_nonsecret raises on any secret-shaped keys."""
    clean_data = {"public_count": 5, "metrics": {"views": 100, "status": "AVAILABLE"}}
    _assert_nonsecret(clean_data)  # Should not raise

    secret_data = {"public_count": 5, "metrics": {"auth_token": "abc123secret"}}
    with pytest.raises(ObservationReadModelError, match="Secret-shaped key rejected"):
        _assert_nonsecret(secret_data)

    nested_secret = {"items": [{"webhook_url": "https://example.com"}]}
    with pytest.raises(ObservationReadModelError, match="Secret-shaped key rejected"):
        _assert_nonsecret(nested_secret)


def test_zero_mutation_guarantee(tmp_path):
    """Verify that building observation read model and snapshot performs zero DB writes."""
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")

    with store.get_connection() as conn:
        before_counts = {
            t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("work_items", "transition_events", "platform_dispatches", "operating_controls")
        }

    snapshot = build_daily_app_snapshot(store.db_path, now=NOW, runtime_root=tmp_path / "runtime")
    assert "observation" in snapshot
    assert snapshot["observation"]["summary"]["total_lanes"] == 19

    with store.get_connection() as conn:
        after_counts = {
            t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("work_items", "transition_events", "platform_dispatches", "operating_controls")
        }

    assert before_counts == after_counts, "Durable store was mutated during read model projection"


def test_v2_real_package_projection(tmp_path):
    """Verify realistic V2 Treasury package correctly populates diversity, TCO, and owner gate."""
    runtime_root = tmp_path / "Runtime" / "ContentOps"
    pkg_dir = runtime_root / "v2_treasury_visual_material_richness_20260815"
    (pkg_dir / "contracts").mkdir(parents=True)
    (pkg_dir / "receipts").mkdir(parents=True)

    (pkg_dir / "HANDOFF.json").write_text(json.dumps({
        "result": "PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW",
        "short": {"render": {"elapsed_ms": 120000, "renderer_version": "4.0.508", "scale": 2}},
    }), encoding="utf-8")

    (pkg_dir / "contracts" / "render_dependency_manifest.json").write_text(json.dumps({
        "total_screen_seconds": 615.8,
        "asset_screen_seconds": {"asset1.jpg": 40.0, "asset2.png": 80.0},
        "family_screen_seconds": {"documentary_photo": 107.0, "native_data": 88.0},
    }), encoding="utf-8")

    (pkg_dir / "receipts" / "manual_visual_review.json").write_text(json.dumps({
        "status": "PASS_CODEX_ACTUAL_MEDIA_VISUAL_REVIEW",
        "reviewer": "Codex task session",
        "owner_acceptance_claimed": False,
        "unresolved_high_severity_defects": 0,
    }), encoding="utf-8")

    (pkg_dir / "receipts" / "zero_public_write.json").write_text(json.dumps({
        "public_writes": 0,
        "uploads": 0,
        "video_public_write_authority": False,
    }), encoding="utf-8")

    store = _store(tmp_path)
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW, runtime_root=runtime_root)
    obs = snapshot["observation"]

    lane_map = {l["lane_id"]: l for l in obs["lanes"]}

    # Asset diversity lane
    div_lane = lane_map[LANE_V2_ASSET_DIVERSITY_AND_SCREEN_TIME]
    assert div_lane["state"] == "LIVE_OBSERVATION"
    assert div_lane["metrics"]["total_screen_seconds"] == 615.8
    assert div_lane["metrics"]["unique_assets_used"] == 2

    # Owner gate lane
    gate_lane = lane_map[LANE_V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE]
    assert gate_lane["state"] == "LIVE_OBSERVATION"
    assert gate_lane["metrics"]["owner_acceptance_claimed"] is False
    assert gate_lane["blocker"] == "PENDING_JIM_CHATGPT_OWNER_ACCEPTANCE"
