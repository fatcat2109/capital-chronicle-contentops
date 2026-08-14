from __future__ import annotations

import copy
import subprocess
from pathlib import Path

import pytest

from live_contentops.lane_b_creative_authority_v1 import (
    ARTICLE_HASH,
    EVIDENCE_HASH,
    CreativeAuthorityLedger,
    CreativeExecutionProvenance,
    logical_hash,
    measure_loudness,
    probe_media,
    validate_audio_eligibility,
    validate_creative_source,
    validate_render_dependencies,
    validate_semantics,
    validate_visual_safety,
    zero_public_write_manifest,
)
from scripts.run_lane_b_creative_authority_v1 import (
    CREATIVE_SOURCE,
    RENDERER,
    dependency_manifest,
    editorial_artifact,
    layout_report,
)


def asset_universe() -> dict:
    files = {
        "nasa-persian-gulf": "nasa-persian-gulf-iss069-e-92132.jpg",
        "eia-hormuz-map-portrait": "eia-hormuz-map-portrait.png",
        "eia-hormuz-map-landscape": "eia-hormuz-map-landscape.png",
        "usns-oiler-hormuz": "usns-oiler-strait-of-hormuz.jpg",
        "doe-tanker-terminal-pipeline": "doe-tanker-terminal-pipeline.jpg",
        "nara-refinery-portrait": "nara-refinery-portrait.jpg",
        "refinery-storage-tanks": "refinery-storage-tanks.jpg",
        "eia-release-document-portrait": "eia-release-document-portrait.png",
        "eia-release-document-landscape": "eia-release-document-landscape.png",
        "commercial-tanker-platform": "commercial-tanker-oil-platform-persian-gulf.jpg",
        "crude-oil-supertanker": "crude-oil-supertanker.jpg",
    }
    return {
        "candidates": [
            {
                "asset_id": asset_id,
                "relative_public_path": f"assets/{filename}",
                "rights_status": "PUBLIC_DOMAIN",
            }
            for asset_id, filename in files.items()
        ],
        "public_write": False,
    }


def test_job_transitions_atomic_claim_and_resume(tmp_path: Path) -> None:
    ledger = CreativeAuthorityLedger(tmp_path / "ledger.sqlite3")
    job = ledger.create_job("i" * 64)
    assert ledger.claim(job["job_id"], "worker-a") is True
    assert ledger.claim(job["job_id"], "worker-b") is False
    ledger.checkpoint(
        job["job_id"],
        "EVIDENCE_LOCKED",
        "i" * 64,
        {"article_hash": ARTICLE_HASH, "evidence_hash": EVIDENCE_HASH},
        model_or_tool="test",
        execution_plane="LOCAL_DETERMINISTIC",
        runtime_seconds=0.1,
    )
    ledger.checkpoint(
        job["job_id"],
        "CREATIVE_SOURCE_READY",
        "i" * 64,
        {"source": "generated/architectureProof.tsx"},
        model_or_tool="gpt-5.6-sol",
        execution_plane="CODEX_TASK_SESSION",
        runtime_seconds=0.2,
    )
    assert ledger.last_valid_stage(job["job_id"]) == "CREATIVE_SOURCE_READY"
    with pytest.raises(ValueError, match="stage_regression"):
        ledger.checkpoint(
            job["job_id"],
            "EDITORIAL_READY",
            "i" * 64,
            {},
            model_or_tool="test",
            execution_plane="LOCAL_DETERMINISTIC",
            runtime_seconds=0,
        )
    ledger.close()


def test_codex_source_provenance_rejects_nine_router() -> None:
    good = CreativeExecutionProvenance(
        execution_plane="CODEX_TASK_SESSION",
        model="gpt-5.6-sol",
        reasoning_effort="not_exposed_to_task_session",
        agent_run_id="architecture-proof",
        prompt_hash="p" * 64,
        artifact_hash="a" * 64,
    )
    assert good.as_dict()["nine_router_route"] is None
    bad = CreativeExecutionProvenance(
        execution_plane="CODEX_TASK_SESSION",
        model="cx/gpt-5.6-sol(xhigh)",
        reasoning_effort="xhigh",
        agent_run_id="architecture-proof",
        prompt_hash="p" * 64,
        artifact_hash="a" * 64,
    )
    with pytest.raises(ValueError, match="nine_router"):
        bad.validate()


def test_generated_source_sandbox_and_viewer_facing_exports(tmp_path: Path) -> None:
    result = validate_creative_source(CREATIVE_SOURCE, RENDERER)
    assert result["status"] == "PASS"
    low_level = (RENDERER / "src" / "lowLevel.tsx").read_text(encoding="utf-8")
    assert "SafeText" in low_level
    assert "SourceAttribution" in low_level
    assert "DocumentaryImage" in low_level
    generated = tmp_path / "project" / "generated"
    generated.mkdir(parents=True)
    unsafe = generated / "unsafe.tsx"
    unsafe.write_text(
        "import React from 'react';\nfetch('https://example.com');\n// CODEX-AUTHORED\n"
        "export const ArchitectureProofShort=()=>null; export const ArchitectureProofMidform=()=>null;",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="forbidden_source:network"):
        validate_creative_source(unsafe, tmp_path / "project")


def test_semantic_qa_rejects_empty_challenge_and_incomplete_document() -> None:
    editorial = editorial_artifact()
    assert validate_semantics(editorial)["status"] == "PASS"
    broken = copy.deepcopy(editorial)
    test_scene = next(row for row in broken["variants"]["short_9x16"] if row["semantic_intent"] == "CONFIRM_CHALLENGE")
    test_scene["visible_content"]["challenge"] = []
    with pytest.raises(ValueError, match="empty_challenge"):
        validate_semantics(broken)
    broken = copy.deepcopy(editorial)
    document = next(row for row in broken["variants"]["midform_16x9"] if row["semantic_intent"] == "DOCUMENT_EVIDENCE")
    document["visible_content"]["evidence_region"] = ""
    with pytest.raises(ValueError, match="document_evidence_incomplete"):
        validate_semantics(broken)


def test_actual_render_dependencies_match_source_and_enforce_diversity() -> None:
    manifest = dependency_manifest()
    result = validate_render_dependencies(manifest, asset_universe(), CREATIVE_SOURCE)
    assert result["status"] == "PASS"
    assert result["stats"]["short_9x16"]["max_concentration"] <= 0.151
    assert result["stats"]["midform_16x9"]["max_concentration"] <= 0.151
    broken = copy.deepcopy(manifest)
    broken["variants"]["short_9x16"][0]["end_seconds"] = 20
    with pytest.raises(ValueError, match="asset_concentration"):
        validate_render_dependencies(broken, asset_universe(), CREATIVE_SOURCE)


def test_visual_safety_collision_duplicate_and_readability_fail_closed() -> None:
    report = layout_report()
    assert validate_visual_safety(report)["status"] == "PASS"
    for key, expected in (
        ("source_collision", "source_collision"),
        ("native_label_duplicate", "native_label_duplicate"),
        ("text_overflow", "text_overflow"),
    ):
        broken = copy.deepcopy(report)
        broken["variants"]["short_9x16"][0][key] = True
        with pytest.raises(ValueError, match=expected):
            validate_visual_safety(broken)
    broken = copy.deepcopy(report)
    broken["variants"]["short_9x16"][0]["min_text_px"] = 10
    with pytest.raises(ValueError, match="phone_text_too_small"):
        validate_visual_safety(broken)


def test_clean_master_caption_policy_and_professional_audio_boundary() -> None:
    root = (RENDERER / "src" / "root.tsx").read_text(encoding="utf-8")
    assert "captionsVisible: false" in root
    assert validate_audio_eligibility("kokoro")["sapi_used"] is False
    with pytest.raises(ValueError, match="diagnostic_audio_not_professional_media_eligible"):
        validate_audio_eligibility("WINDOWS_SAPI_LOCAL")


def test_zero_public_write_and_v1_isolation() -> None:
    manifest = zero_public_write_manifest()
    assert manifest["public_write"] is False
    assert manifest["platform_actions"] == []
    assert manifest["uploads"] == []
    assert manifest["browser_cdp_actions"] == []
    assert manifest["v1_mutations"] == []
    assert manifest["v2_02_started"] is False
    implementation = Path("live_contentops/lane_b_creative_authority_v1.py").read_text(encoding="utf-8")
    runner = Path("scripts/run_lane_b_creative_authority_v1.py").read_text(encoding="utf-8")
    forbidden_v1_mutation_seams = (
        "durable_operational_store_v1",
        "publication_coordinator_v1",
        "daily_app_supervisor_v1",
    )
    assert not any(name in implementation or name in runner for name in forbidden_v1_mutation_seams)


def test_selective_rerender_identity_is_source_hash_bound() -> None:
    source_hash = logical_hash({"source": CREATIVE_SOURCE.read_text(encoding="utf-8")})
    scene_a = logical_hash({"source_hash": source_hash, "scene": "S04_DOCUMENT"})
    scene_b = logical_hash({"source_hash": source_hash, "scene": "S05_FORECAST"})
    repaired_a = logical_hash({"source_hash": source_hash, "scene": "S04_DOCUMENT", "repair": "source-zone"})
    assert repaired_a != scene_a
    assert scene_b == logical_hash({"source_hash": source_hash, "scene": "S05_FORECAST"})


def test_actual_media_probe_and_audio_qa(tmp_path: Path) -> None:
    media = tmp_path / "probe.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=#07131d:s=360x640:r=30:d=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-shortest",
            str(media),
        ],
        check=True,
    )
    probe = probe_media(media)
    assert round(float(probe["format"]["duration"])) == 1
    assert {stream["codec_type"] for stream in probe["streams"]} == {"video", "audio"}
    loudness = measure_loudness(media)
    assert loudness["integrated_lufs"] < 0
    assert loudness["true_peak_dbtp"] <= 0
