from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.treasury_visual_material_repair_v1 import (
    ASSET_SOURCE_FAMILY,
    CHATTERBOX_DIAGNOSTIC_SHA256,
    FROZEN_AUDIO_SHA256,
    NATIVE_GOVERNED_MOTION,
    ROWS,
    STATIC_FULL_CONTEXT,
    STATIC_OBJECT_CLASSES,
    dependency_manifest,
    material_plan,
    validate_audio_freeze,
    validate_creative_source_sandbox,
    validate_evidence_motion_contract,
    validate_material_plan,
)
from scripts.run_v2_short_longform_low_cost_audio_v1 import LONG_SCENES, SHORT_SCENES


REPO = Path(__file__).resolve().parents[1]
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_treasury_owner_visual_integrity_diversity_20260815")
AUDIO_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815")
SOURCE = REPO / "video" / "asset_first_v1" / "src" / "generated" / "treasuryPositioning.tsx"


def durations(variant: str) -> dict[str, float]:
    manifest = json.loads((AUDIO_RUNTIME / "audio" / f"{variant}-manifest.json").read_text(encoding="utf-8"))
    return {row["scene_id"]: float(row["duration_seconds"]) for row in manifest["segments"]}


def selected_hashes() -> dict[str, str]:
    return {name: f"hash-{index}" for index, name in enumerate(sorted(ASSET_SOURCE_FAMILY))}


def plans() -> tuple[dict, dict]:
    return material_plan(SHORT_SCENES, durations("short")), material_plan(LONG_SCENES, durations("longform"))


def test_owner_candidate_uses_explicit_semantic_boundaries_not_duration_recipe_cycling():
    short, longform = plans()
    implementation = (REPO / "live_contentops" / "treasury_visual_material_repair_v1.py").read_text(encoding="utf-8")
    assert "round(duration / 3.4)" not in implementation
    assert "EXPLICIT_NARRATION_INFORMATION_CHANGE" in implementation
    assert all(row["boundary_authority"] == "EXPLICIT_NARRATION_INFORMATION_CHANGE" for beats in longform.values() for row in beats)
    observed = {round(row["duration_seconds"], 1) for beats in longform.values() for row in beats}
    assert len(observed) >= 15
    validation = validate_material_plan(longform, selected_hashes())
    assert validation["status"] == "PASS", validation["errors"]
    assert validation["semantic_beat_duration_seconds"]["maximum"] > 4
    assert validate_material_plan(short, selected_hashes())["status"] == "PASS"


def test_primary_evidence_objects_are_static_full_context_and_native_data_can_animate():
    short, longform = plans()
    combined = {"short:" + key: value for key, value in short.items()} | {"long:" + key: value for key, value in longform.items()}
    contract = validate_evidence_motion_contract(combined)
    assert contract["status"] == "PASS", contract["errors"]
    primary = [row for beats in combined.values() for row in beats if row["evidence_object_class"] in STATIC_OBJECT_CLASSES]
    native = [row for beats in combined.values() for row in beats if row["evidence_object_class"] == "native_cc_data_visual"]
    assert primary and native
    assert all(row["motion_policy"] == STATIC_FULL_CONTEXT for row in primary)
    assert all(row["layout"] in {"document_full", "figure_full"} for row in primary)
    assert all(row["motion_policy"] == NATIVE_GOVERNED_MOTION for row in native)


def test_remotion_source_cannot_zoom_pan_or_crop_primary_charts_tables_and_figures():
    source = SOURCE.read_text(encoding="utf-8")
    document_block = source[source.index("const Document:"):source.index("const PositionChart:")]
    assert "objectFit:'contain'" in document_block
    assert "transform:'none'" in document_block
    assert "objectFit:crop" not in source
    assert "document_crop" not in source and "figure_crop" not in source
    assert "STATIC FULL CONTEXT" in source
    assert "MaturityData" in source and "spring({" in source
    assert "fetch(" not in source and "process.env" not in source


def test_dependency_accounting_separates_source_material_from_presentation_grammar():
    short, longform = plans()
    manifest = dependency_manifest({"short": short, "longform": longform}, selected_hashes())
    assert manifest["taxonomy_separation"]
    assert "source_material_family_screen_seconds" in manifest
    assert "presentation_grammar_screen_seconds" in manifest
    assert "editorial_boundary" not in manifest["source_material_family_screen_seconds"]
    assert "boundary" in manifest["presentation_grammar_screen_seconds"]
    assert set(ASSET_SOURCE_FAMILY).issubset(manifest["asset_usage"])
    assert manifest["asset_usage"][ROWS]["scene_count"] <= 3
    assert manifest["asset_usage"][ROWS]["adjacent_source_asset_reuse_count"] == 0
    assert all(row["adjacent_source_asset_reuse_count"] == 0 for row in manifest["asset_usage"].values())
    assert len(manifest["source_material_family_usage"]) >= 9


def test_story_specific_source_passes_sandbox_and_import_boundary():
    result = validate_creative_source_sandbox(SOURCE, REPO / "video" / "asset_first_v1")
    assert result["status"] == "PASS", result["errors"]
    assert result["imports"] == ["react", "remotion"]


def test_frozen_audio_and_chatterbox_diagnostic_are_not_provider_selection():
    assert validate_audio_freeze(FROZEN_AUDIO_SHA256, CHATTERBOX_DIAGNOSTIC_SHA256)["status"] == "PASS"
    runner = (REPO / "scripts" / "run_v2_treasury_visual_material_repair_v1.py").read_text(encoding="utf-8")
    assert "video_tts_worker" not in runner
    assert '"public_writes": 0' in runner
    assert '"v1_mutations": 0' in runner
    assert '"mode_bakeoff": False' in runner


def test_runtime_asset_board_truth_audio_and_dependency_observation_if_present():
    board_path = RUNTIME / "contracts" / "asset_board.json"
    if not board_path.is_file():
        pytest.skip("runtime owner candidate not present")
    board = json.loads(board_path.read_text(encoding="utf-8"))
    assert board["status"] == "PASS_PRE_MOTION_ASSET_BOARD_READY"
    assert board["counts"]["selected"] >= 20
    assert board["counts"]["selected_source_material_families"] >= 9
    assert all(row.get("rights") and row.get("sha256") and row.get("story_use") and row.get("source_material_family") for row in board["selected"])
    cftc = json.loads((RUNTIME / "receipts" / "cftc_zero_trust_verification.json").read_text(encoding="utf-8"))
    assert cftc["status"] == "PASS_ZERO_TRUST_EXACT_RAW_ROWS"
    assert cftc["source_sha256"] == "e3e4bff2592777fbd9a125e723bdb087b5110b47b95c16e1b376dcb029b44f96"
    assert {row["row_sha256"] for row in cftc["rows"]} == {
        "c70fb895f4fa8c3df8f38d3cf3aa0a41a39d52388d8f15289cc02fe7e1303da8",
        "ec1e9bc0dd9a4c68764c19f95b02bdd4ad8c7f5176cebaa6337ef953b63b76da",
        "4beffa46b41271563ccb4cd48bc5ef903184e793356a2fc9c3a967a1b7d6bf6e",
    }
    audio = json.loads((RUNTIME / "receipts" / "frozen_audio_receipt.json").read_text(encoding="utf-8"))
    assert audio["status"] == "PASS_FROZEN_AUDIO_BYTE_STABLE"
    assert audio["segment_count"] == 26 and audio["kokoro_segments_synthesized_this_task"] == 0
    observation_path = RUNTIME / "receipts" / "render_dependency_observation.json"
    if observation_path.is_file():
        observation = json.loads(observation_path.read_text(encoding="utf-8"))
        assert observation["status"] == "PASS"
        assert observation["referenced_asset_count"] == board["counts"]["selected"]
        assert observation["proof_levels"]["pixel_level_asset_provenance"] == "NOT_CLAIMED"
