from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.treasury_visual_material_repair_v1 import (
    CHATTERBOX_DIAGNOSTIC_SHA256, FED_FIG1, FED_FIG3, FED_FIG4, FED_FSR, FED_NOTE,
    FROZEN_AUDIO_SHA256, PHOTO_CFTC, PHOTO_FED, PHOTO_TREASURY, ROWS, SCHEDULE,
    TREASURY_REMARKS, dependency_manifest, material_plan, validate_audio_freeze,
    validate_creative_source_sandbox, validate_material_plan,
)
from scripts.run_v2_short_longform_low_cost_audio_v1 import LONG_SCENES, SHORT_SCENES


REPO = Path(__file__).resolve().parents[1]
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_treasury_visual_material_richness_20260815")
OLD_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815")
ASSETS = {PHOTO_CFTC, PHOTO_TREASURY, PHOTO_FED, ROWS, SCHEDULE, FED_NOTE, TREASURY_REMARKS, FED_FIG1, FED_FIG3, FED_FIG4, FED_FSR}


def durations(variant: str) -> dict[str, float]:
    manifest = json.loads((OLD_RUNTIME / "audio" / f"{variant}-manifest.json").read_text(encoding="utf-8"))
    return {row["scene_id"]: float(row["duration_seconds"]) for row in manifest["segments"]}


def selected_hashes() -> dict[str, str]:
    return {name: f"hash-{index}" for index, name in enumerate(sorted(ASSETS))}


def test_material_plan_uses_real_source_assets_and_two_to_four_second_microbeats():
    short = material_plan(SHORT_SCENES, durations("short"))
    longform = material_plan(LONG_SCENES, durations("longform"))
    assert validate_material_plan(short, selected_hashes())["status"] == "PASS"
    validation = validate_material_plan(longform, selected_hashes())
    assert validation["status"] == "PASS"
    assert validation["real_source_share"] >= 0.5
    assert len(validation["family_seconds"]) >= 9
    assert validation["longest_abstract_run_seconds"] <= 10.5
    assert all(2 <= row["duration_seconds"] <= 4 for rows in longform.values() for row in rows)


def test_render_dependency_manifest_is_derived_from_exact_screen_time_not_family_labels():
    plans = {"short": material_plan(SHORT_SCENES, durations("short")), "longform": material_plan(LONG_SCENES, durations("longform"))}
    manifest = dependency_manifest(plans, selected_hashes())
    assert manifest["external_runtime_fetches"] == 0
    assert manifest["generated_person_media"] == 0
    assert set(ASSETS).issubset(manifest["selected_asset_hashes"])
    assert sum(manifest["asset_screen_seconds"].values()) > 300
    assert len(manifest["per_scene"]) == 26
    assert all(row["microbeats"] >= 2 for row in manifest["per_scene"].values())


def test_story_specific_source_renders_actual_material_and_rejects_the_old_grid_deck():
    source = (REPO / "video" / "asset_first_v1" / "src" / "generated" / "treasuryPositioning.tsx").read_text(encoding="utf-8")
    for token in ("PhotoFull", "Document", "PositionChart", "WeeklyDelta", "Mechanism", "Boundary", "SourceClock", "StressChain", "Monitoring", "Montage"):
        assert token in source
    assert "<Img" in source and "assets/${name}" in source
    assert "<Grid" not in source
    assert "material_plan" in source
    assert "fetch(" not in source and "process.env" not in source


def test_story_specific_source_passes_sandbox_and_import_boundary():
    source = REPO / "video" / "asset_first_v1" / "src" / "generated" / "treasuryPositioning.tsx"
    result = validate_creative_source_sandbox(source, REPO / "video" / "asset_first_v1")
    assert result["status"] == "PASS", result["errors"]
    assert result["imports"] == ["react", "remotion"]


def test_frozen_audio_and_chatterbox_diagnostic_are_not_provider_selection():
    assert validate_audio_freeze(FROZEN_AUDIO_SHA256, CHATTERBOX_DIAGNOSTIC_SHA256)["status"] == "PASS"
    source = (REPO / "scripts" / "run_v2_treasury_visual_material_repair_v1.py").read_text(encoding="utf-8")
    assert "video_tts_worker" not in source
    assert "new_tts_synthesis" not in source or "new_tts_synthesis" in (REPO / "live_contentops" / "treasury_visual_material_repair_v1.py").read_text(encoding="utf-8")
    assert "review-pass" in source


def test_runtime_asset_board_and_zero_trust_cftc_rows_if_present():
    if not (RUNTIME / "contracts" / "asset_board.json").is_file():
        pytest.skip("runtime material proof not present")
    board = json.loads((RUNTIME / "contracts" / "asset_board.json").read_text(encoding="utf-8"))
    assert board["status"] == "PASS_PRE_MOTION_ASSET_BOARD_READY"
    assert board["counts"]["selected"] >= 10
    assert all(row.get("rights") and row.get("sha256") and row.get("story_use") for row in board["selected"])
    cftc = json.loads((RUNTIME / "receipts" / "cftc_zero_trust_verification.json").read_text(encoding="utf-8"))
    assert cftc["status"] == "PASS_ZERO_TRUST_EXACT_RAW_ROWS"
    assert cftc["source_sha256"] == "e3e4bff2592777fbd9a125e723bdb087b5110b47b95c16e1b376dcb029b44f96"
    assert {row["asset_net"] for row in cftc["rows"]} == {1_680_389, 2_883_977, 2_554_411}
    assert {row["lever_net"] for row in cftc["rows"]} == {-1_359_521, -2_147_744, -2_163_714}


def test_runtime_frozen_audio_receipt_if_present():
    receipt = RUNTIME / "receipts" / "frozen_audio_receipt.json"
    if not receipt.is_file():
        pytest.skip("runtime frozen-audio proof not present")
    data = json.loads(receipt.read_text(encoding="utf-8"))
    assert data["status"] == "PASS_FROZEN_AUDIO_BYTE_STABLE"
    assert data["segment_count"] == 26
    assert data["kokoro_segments_synthesized_this_task"] == 0
    assert data["voice_bakeoff"] is False
    assert data["build_tts_selection"] == "UNRESOLVED_AFTER_FROZEN_KOKORO_AB"
