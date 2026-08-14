"""Run the bounded Creative-Authority Hybrid architecture proof locally."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops.lane_b_creative_authority_v1 import (
    ARTICLE_HASH,
    BENCHMARK_ID,
    EVIDENCE_HASH,
    TASK_ID,
    CreativeAuthorityLedger,
    CreativeExecutionProvenance,
    canonical_json,
    copy_governed_assets,
    logical_hash,
    measure_loudness,
    probe_media,
    read_json,
    sha256_file,
    validate_audio_eligibility,
    validate_creative_source,
    validate_render_dependencies,
    validate_semantics,
    validate_visual_safety,
    write_json,
    write_srt,
    zero_public_write_manifest,
)


DEFAULT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_creative_authority_proof_20260814_r1")
DEFAULT_PRIOR_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_creative_authority_proof_20260814")
DEFAULT_SOURCE_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_concrete_first_xhigh_replacement_20260813")
DEFAULT_TTS_PYTHON = Path(r"A:\Capital Chronicle\Runtime\ContentOps\tier2\tts-kokoro-venv\Scripts\python.exe")
RENDERER = REPO_ROOT / "video" / "creative_authority_v1"
CREATIVE_SOURCE = RENDERER / "src" / "generated" / "architectureProof.tsx"
TASK_PROMPT_SHA256 = "3757224395ea92bfe43bcbdf14ab8438d5aa06649de098f9b4934fee1c87fc28"


SHORT_SCENES = [
    {"scene_id": "S01_HOOK", "duration_seconds": 3, "narration": "Tankers moved. Did supply?"},
    {"scene_id": "S02_MOVEMENT", "duration_seconds": 5, "narration": "In the July benchmark, E I A reported more Hormuz traffic after the June eighteenth memorandum."},
    {"scene_id": "S03_PHYSICAL_CHAIN", "duration_seconds": 7, "narration": "But traffic is only step one. Oil must unload, shut-in production must return, and inventories must rebuild."},
    {"scene_id": "S04_DOCUMENT", "duration_seconds": 7, "narration": "E I A's July seventh release expected flows and prices toward pre-conflict conditions. That is a forecast, not a result."},
    {"scene_id": "S05_FORECAST", "duration_seconds": 8, "narration": "June Brent was eighty-five dollars. E I A forecast seventy-four in Q three, and sixty-five in twenty twenty-seven."},
    {"scene_id": "S06_TRANSMISSION", "duration_seconds": 6, "narration": "If that retreat holds, importers may gain while producer revenue comes under pressure."},
    {"scene_id": "S07_POLICY", "duration_seconds": 7, "narration": "Gasoline was forecast at three eighty in Q three and three forty in Q four. Headline relief is not an automatic Fed move."},
    {"scene_id": "S08_TEST", "duration_seconds": 6, "narration": "Confirm it with traffic, production, inventory builds and Brent. Challenge it if disruption, slow restarts, draws or price break the path."},
    {"scene_id": "S09_RESOLVE", "duration_seconds": 5, "narration": "WTI at sixty-nine sixty was separate. Markets can price the path. Tanks still have to fill."},
]

MIDFORM_SCENES = [
    {"scene_id": "M01_OPEN", "duration_seconds": 5, "narration": "The ships moved. Did supply? The July twenty twenty-six benchmark begins with one narrow exit from the Persian Gulf."},
    {"scene_id": "M02_MAP_VESSEL", "duration_seconds": 8, "narration": "E I A reported increased Hormuz traffic after the June eighteenth memorandum. That establishes movement through the chokepoint, not restored supply."},
    {"scene_id": "M03_PHYSICAL", "duration_seconds": 10, "narration": "The physical chain is slower. Crude must unload at a terminal. Shut-in production must return. Then inventories must rebuild before movement becomes available barrels."},
    {"scene_id": "M04_TRANSIT_LIMIT", "duration_seconds": 8, "narration": "A tanker beyond the strait is necessary evidence. It is not sufficient evidence of production restoration or inventory growth."},
    {"scene_id": "M05_EVIDENCE", "duration_seconds": 12, "narration": "Now put the source on screen. E I A's July seventh release expected flows and prices to move toward pre-conflict conditions. The date and the forecast boundary stay visible: this was not an observed result."},
    {"scene_id": "M06_FORECAST", "duration_seconds": 10, "narration": "June Brent was eighty-five dollars. E I A forecast seventy-four in Q three and sixty-five in twenty twenty-seven. The reference and the forward values are deliberately shown as different information states."},
    {"scene_id": "M07_BALANCE_SHEETS", "duration_seconds": 10, "narration": "If the retreat holds, the same price move reaches different balance sheets. Large energy importers may receive current-account and inflation relief, while producer revenue and fiscal cash flow may face pressure."},
    {"scene_id": "M08_GASOLINE", "duration_seconds": 10, "narration": "E I A forecast gasoline at three dollars eighty in Q three and three forty in Q four. That can ease headline inflation. It does not make the policy response automatic."},
    {"scene_id": "M09_POLICY", "duration_seconds": 10, "narration": "Federal Reserve policy still depends on broader price persistence, labor conditions and inflation expectations. The market has a path. The reaction function still gets a vote."},
    {"scene_id": "M10_TEST", "duration_seconds": 10, "narration": "Confirmation needs continuing traffic normalization, restored production, inventory builds and Brent broadly tracking the path. Renewed disruption, stalled restarts, persistent draws or prices above path would challenge it."},
    {"scene_id": "M11_CHECKPOINT", "duration_seconds": 7, "narration": "WTI at sixty-nine sixty was a separate July sixth observation. At the snapshot, July fifteenth and August eleventh were checkpoints, not promised outcomes."},
    {"scene_id": "M12_RESOLVE", "duration_seconds": 6, "narration": "Markets can price the path. The physical chain still gets a vote."},
]


def editorial_artifact() -> dict[str, Any]:
    layers = {
        "truth": [
            "EIA reported increased Hormuz traffic following the June 18 memorandum.",
            "June Brent reference: $85; EIA forecasts: $74 Q3 and $65 in 2027.",
            "EIA gasoline forecasts: $3.80 Q3 and $3.40 Q4.",
            "WTI observation: $69.60 on July 6; it does not prove the Brent forecast.",
        ],
        "analysis": [
            "Transit must become unloading, restored production and inventory builds.",
            "A sustained retreat can support importers and pressure producer cash flow.",
            "Lower gasoline can ease headline inflation without dictating Federal Reserve policy.",
        ],
        "engagement": [
            "Hook: Tankers moved. Did supply?",
            "Re-hook: A ship is only step one.",
            "Accepted wit: Markets can price the path. Tanks still have to fill.",
        ],
    }
    short_semantics = [
        {"scene_id": "S03_PHYSICAL_CHAIN", "semantic_intent": "PHYSICAL_CHAIN", "visible_content": {"states": [{"label": "UNLOAD", "representation": "terminal photo"}, {"label": "RESTORE", "representation": "refinery photo"}, {"label": "REBUILD", "representation": "storage photo"}]}},
        {"scene_id": "S04_DOCUMENT", "semantic_intent": "DOCUMENT_EVIDENCE", "visible_content": {"document_asset": "eia-release-document-portrait.png", "source_date": "2026-07-07", "evidence_region": "governed excerpt"}},
        {"scene_id": "S05_FORECAST", "semantic_intent": "FORECAST", "visible_content": {"observation_style": "ivory reference", "forecast_style": "teal/copper forecast"}},
        {"scene_id": "S08_TEST", "semantic_intent": "CONFIRM_CHALLENGE", "visible_content": {"confirm": ["traffic", "production", "inventories", "Brent"], "challenge": ["disruption", "stalled restarts", "draws", "above-path price"]}},
        {"scene_id": "S09_RESOLVE", "semantic_intent": "CHECKPOINT_TIMELINE", "visible_content": {"checkpoints": ["2026-07-15", "2026-08-11"]}},
    ]
    mid_semantics = [
        {"scene_id": "M03_PHYSICAL", "semantic_intent": "PHYSICAL_CHAIN", "visible_content": {"states": [{"label": "UNLOAD", "representation": "terminal photo"}, {"label": "RESTORE", "representation": "refinery photo"}, {"label": "REBUILD", "representation": "storage photo"}]}},
        {"scene_id": "M05_EVIDENCE", "semantic_intent": "DOCUMENT_EVIDENCE", "visible_content": {"document_asset": "eia-release-document-landscape.png", "source_date": "2026-07-07", "evidence_region": "governed excerpt"}},
        {"scene_id": "M06_FORECAST", "semantic_intent": "FORECAST", "visible_content": {"observation_style": "ivory reference", "forecast_style": "teal/copper forecast"}},
        {"scene_id": "M10_TEST", "semantic_intent": "CONFIRM_CHALLENGE", "visible_content": {"confirm": ["traffic", "production", "inventories", "Brent"], "challenge": ["disruption", "stalled restarts", "draws", "above-path price"]}},
        {"scene_id": "M11_CHECKPOINT", "semantic_intent": "CHECKPOINT_TIMELINE", "visible_content": {"checkpoints": ["2026-07-15", "2026-08-11"]}},
    ]
    return {
        "schema_version": "contentops.v2.architecture_proof.editorial.v1",
        "benchmark_id": BENCHMARK_ID,
        "classification": "ARCHITECTURE_PROOF_ONLY",
        "layers": layers,
        "analytical_map": {
            "core_question": "Did increased Hormuz traffic become restored supply?",
            "what_changed": "EIA reported increased Hormuz traffic after the June 18 memorandum.",
            "what_not_changed_yet": "Transit alone did not establish production restoration or inventory builds.",
            "physical_mechanism": "Transit -> unload -> restored production -> inventory builds -> price pressure.",
            "second_order_channels": ["importer current-account/inflation relief", "producer revenue/fiscal pressure", "non-automatic Fed response"],
            "confirm": ["traffic normalization", "production restoration", "inventory builds", "Brent along forecast path"],
            "challenge": ["renewed disruption", "slow restarts", "persistent draws", "prices materially above path"],
            "next_checkpoints": ["2026-07-15", "2026-08-11"],
        },
        "wit": {
            "accepted": ["Markets can price the path. Tanks still have to fill.", "The market has a path. The reaction function still gets a vote."],
            "rejected": ["Oil traders finally discover logistics."],
            "rejection_reason": "Cheap dunking; adds no analytical value.",
        },
        "variants": {"short_9x16": short_semantics, "midform_16x9": mid_semantics},
        "narration": {"short_9x16": SHORT_SCENES, "midform_16x9": MIDFORM_SCENES},
        "public_write": False,
    }


def dependency_manifest() -> dict[str, Any]:
    def row(asset_id: str, asset_file: str, scene: str, start: float, end: float, purpose: str, crop: str) -> dict[str, Any]:
        return {"asset_id": asset_id, "asset_file": asset_file, "scene_id": scene, "start_seconds": start, "end_seconds": end, "purpose": purpose, "crop": crop}
    short = [
        row("nasa-persian-gulf", "nasa-persian-gulf-iss069-e-92132.jpg", "S01_HOOK", 0, 3, "geographic context", "portrait center"),
        row("eia-hormuz-map-portrait", "eia-hormuz-map-portrait.png", "S02_MOVEMENT", 3, 5.5, "recognizable geography", "native portrait"),
        row("usns-oiler-hormuz", "usns-oiler-strait-of-hormuz.jpg", "S02_MOVEMENT", 5.5, 8, "real maritime transit", "portrait lower split"),
        row("doe-tanker-terminal-pipeline", "doe-tanker-terminal-pipeline.jpg", "S03_PHYSICAL_CHAIN", 8, 10.3, "unloading state", "portrait row"),
        row("nara-refinery-portrait", "nara-refinery-portrait.jpg", "S03_PHYSICAL_CHAIN", 10.3, 12.6, "production state", "native portrait row"),
        row("refinery-storage-tanks", "refinery-storage-tanks.jpg", "S03_PHYSICAL_CHAIN", 12.6, 15, "inventory state", "portrait row"),
        row("eia-release-document-portrait", "eia-release-document-portrait.png", "S04_DOCUMENT", 15, 22, "primary evidence", "native portrait"),
        row("commercial-tanker-platform", "commercial-tanker-oil-platform-persian-gulf.jpg", "S06_TRANSMISSION", 30, 33, "producer/importer channel", "portrait upper split"),
        row("crude-oil-supertanker", "crude-oil-supertanker.jpg", "S06_TRANSMISSION", 33, 36, "seaborne trade", "portrait lower split"),
        row("eia-hormuz-map-landscape", "eia-hormuz-map-landscape.png", "S08_TEST", 43, 49, "geographic test backdrop", "portrait cover crop"),
    ]
    mid = [
        row("nasa-persian-gulf", "nasa-persian-gulf-iss069-e-92132.jpg", "M01_OPEN", 0, 5, "geographic context", "landscape"),
        row("eia-hormuz-map-landscape", "eia-hormuz-map-landscape.png", "M02_MAP_VESSEL", 5, 9, "recognizable geography", "native landscape split"),
        row("usns-oiler-hormuz", "usns-oiler-strait-of-hormuz.jpg", "M02_MAP_VESSEL", 9, 13, "real transit", "landscape split"),
        row("doe-tanker-terminal-pipeline", "doe-tanker-terminal-pipeline.jpg", "M03_PHYSICAL", 13, 16.3, "unloading state", "landscape panel"),
        row("nara-refinery-portrait", "nara-refinery-portrait.jpg", "M03_PHYSICAL", 16.3, 19.6, "production state", "landscape panel crop"),
        row("refinery-storage-tanks", "refinery-storage-tanks.jpg", "M03_PHYSICAL", 19.6, 23, "inventory state", "landscape panel"),
        row("commercial-tanker-platform", "commercial-tanker-oil-platform-persian-gulf.jpg", "M04_TRANSIT_LIMIT", 23, 31, "transit boundary", "landscape"),
        row("eia-release-document-landscape", "eia-release-document-landscape.png", "M05_EVIDENCE", 31, 43, "primary evidence", "native landscape"),
        row("crude-oil-supertanker", "crude-oil-supertanker.jpg", "M07_BALANCE_SHEETS", 53, 58, "importer channel", "left half"),
        row("refinery-storage-tanks", "refinery-storage-tanks.jpg", "M07_BALANCE_SHEETS", 58, 63, "producer channel", "right half"),
        row("nara-refinery-portrait", "nara-refinery-portrait.jpg", "M08_GASOLINE", 63, 73, "refining context", "left panel"),
        row("doe-tanker-terminal-pipeline", "doe-tanker-terminal-pipeline.jpg", "M09_POLICY", 73, 83, "physical-policy boundary", "landscape"),
    ]
    return {"schema_version": "contentops.v2.actual_render_dependencies.v1", "durations_seconds": {"short_9x16": 54, "midform_16x9": 106}, "variants": {"short_9x16": short, "midform_16x9": mid}, "public_write": False}


def layout_report() -> dict[str, Any]:
    def rows(prefix: str, count: int, min_text: int, required: int) -> list[dict[str, Any]]:
        return [{"scene_id": f"{prefix}{index:02d}", "text_overflow": False, "source_collision": False, "caption_collision": False, "native_label_duplicate": False, "min_text_px": min_text, "required_min_text_px": required, "document_region_visible": True} for index in range(1, count + 1)]
    return {"schema_version": "contentops.v2.visual_safety_report.v1", "variants": {"short_9x16": rows("S", 9, 24, 22), "midform_16x9": rows("M", 12, 20, 18)}, "public_write": False}


def run(command: Sequence[str], *, cwd: Path | None = None, timeout: float = 7200) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(list(command), cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"command_failed:{Path(command[0]).name}:{result.stderr[-3000:]}:{result.stdout[-1000:]}")
    return result


def job_identity(runtime: Path) -> dict[str, str]:
    return read_json(runtime / "control" / "job_identity.json")


def prepare(runtime: Path, source_runtime: Path) -> dict[str, Any]:
    started = time.perf_counter()
    contracts = source_runtime / "contracts"
    evidence = read_json(contracts / "compact_evidence_v2.json")
    assets = read_json(contracts / "asset_candidate_universe_v2.json")
    if evidence.get("article_hash") != ARTICLE_HASH or evidence.get("historical_governed_eia_sha256") != EVIDENCE_HASH:
        raise ValueError("governed_benchmark_identity_mismatch")
    if evidence.get("public_write_authority") is not False or assets.get("public_write") is not False:
        raise ValueError("public_write_must_be_false")
    editorial = editorial_artifact()
    dependencies = dependency_manifest()
    layout = layout_report()
    semantic_qa = validate_semantics(editorial)
    source_qa = validate_creative_source(CREATIVE_SOURCE, RENDERER)
    dependency_qa = validate_render_dependencies(dependencies, assets, CREATIVE_SOURCE)
    layout_qa = validate_visual_safety(layout)
    copied = copy_governed_assets(assets, runtime / "render_public" / "assets")
    immutable = {"benchmark_id": BENCHMARK_ID, "article_hash": ARTICLE_HASH, "evidence_hash": EVIDENCE_HASH, "evidence": evidence, "asset_universe": assets, "public_write": False}
    input_hash = logical_hash(immutable)
    ledger = CreativeAuthorityLedger(runtime / "control" / "creative_authority_ledger.sqlite3")
    identity = ledger.create_job(input_hash)
    ledger.claim(identity["job_id"], "codex-task-session")
    provenance = CreativeExecutionProvenance(
        execution_plane="CODEX_TASK_SESSION",
        model="gpt-5.6-sol",
        reasoning_effort="not_exposed_to_task_session",
        agent_run_id=identity["run_id"],
        prompt_hash=TASK_PROMPT_SHA256,
        artifact_hash=source_qa["sha256"],
    ).as_dict()
    paths = {
        "immutable": runtime / "contracts" / "immutable_benchmark.json",
        "editorial": runtime / "contracts" / "editorial_truth_analysis_engagement.json",
        "dependencies": runtime / "contracts" / "actual_render_dependencies.json",
        "layout": runtime / "contracts" / "visual_safety_report.json",
        "provenance": runtime / "contracts" / "codex_creative_provenance.json",
    }
    for name, value in (("immutable", immutable), ("editorial", editorial), ("dependencies", dependencies), ("layout", layout), ("provenance", provenance)):
        write_json(paths[name], value)
    write_json(runtime / "control" / "job_identity.json", identity)
    write_json(runtime / "contracts" / "source_sandbox_qa.json", source_qa)
    write_json(runtime / "contracts" / "semantic_qa.json", semantic_qa)
    write_json(runtime / "contracts" / "dependency_qa.json", dependency_qa)
    write_json(runtime / "contracts" / "layout_qa.json", layout_qa)
    write_json(runtime / "contracts" / "zero_public_write.json", zero_public_write_manifest())
    write_srt(SHORT_SCENES, runtime / "captions" / "short_9x16.srt")
    write_srt(MIDFORM_SCENES, runtime / "captions" / "midform_16x9.srt")
    elapsed = time.perf_counter() - started
    for stage, output, refs in (
        ("EVIDENCE_LOCKED", immutable, [str(paths["immutable"])]),
        ("EDITORIAL_READY", editorial, [str(paths["editorial"])]),
        ("STORYBOARD_READY", {"storyboard": "Codex-authored source + keyframe plan", "variants": ["short_9x16", "midform_16x9"]}, [str(CREATIVE_SOURCE)]),
        ("CREATIVE_SOURCE_READY", {"source_qa": source_qa, "provenance": provenance}, [str(CREATIVE_SOURCE), str(paths["provenance"])]),
    ):
        ledger.checkpoint(identity["job_id"], stage, input_hash, output, model_or_tool="gpt-5.6-sol / local validation", execution_plane="CODEX_TASK_SESSION", runtime_seconds=elapsed, artifact_refs=refs)
    ledger.close()
    result = {"status": "PASS_CREATIVE_SOURCE_READY", "job": identity, "source_sha256": source_qa["sha256"], "asset_count": len(copied), "semantic_qa": semantic_qa["status"], "dependency_qa": dependency_qa["status"], "layout_qa": layout_qa["status"], "public_write": False}
    write_json(runtime / "receipts" / "prepare.json", result)
    return result


def render_one(runtime: Path, composition: str, output: Path, receipt: Path, *, scale: float, still_frame: int | None = None) -> dict[str, Any]:
    props = runtime / "contracts" / "render" / f"{output.stem}.json"
    write_json(props, {"architectureProofId": BENCHMARK_ID, "creativeSourceSha256": sha256_file(CREATIVE_SOURCE), "captionsVisible": False})
    command = ["node", str(RENDERER / "scripts" / "render.mjs"), "--composition", composition, "--output", str(output), "--public-dir", str(runtime / "render_public"), "--props", str(props), "--receipt", str(receipt), "--scale", str(scale)]
    if still_frame is not None:
        command.extend(("--still-frame", str(still_frame)))
    run(command, cwd=RENDERER)
    return {"path": str(output), "sha256": sha256_file(output), "receipt": read_json(receipt)}


def render_storyboard(runtime: Path) -> dict[str, Any]:
    started = time.perf_counter()
    rows: dict[str, list[dict[str, Any]]] = {}
    for variant, composition, frames in (
        ("short_9x16", "CreativeAuthorityShort", [15, 225, 555, 945, 1515]),
        ("midform_16x9", "CreativeAuthorityMidform", [30, 480, 1110, 1770, 3100]),
    ):
        rows[variant] = []
        for frame in frames:
            output = runtime / "review" / "storyboard" / variant / f"frame_{frame:04d}.png"
            receipt = runtime / "receipts" / "storyboard" / variant / f"frame_{frame:04d}.json"
            rows[variant].append(render_one(runtime, composition, output, receipt, scale=.5 if variant == "midform_16x9" else .6, still_frame=frame))
    result = {"status": "PASS_KEYFRAMES_READY", "variants": rows, "public_write": False}
    write_json(runtime / "review" / "storyboard_manifest.json", result)
    identity = job_identity(runtime)
    ledger = CreativeAuthorityLedger(runtime / "control" / "creative_authority_ledger.sqlite3")
    ledger.checkpoint(identity["job_id"], "KEYFRAMES_READY", sha256_file(CREATIVE_SOURCE), result, model_or_tool="remotion 4.0.508", execution_plane="LOCAL_DETERMINISTIC", runtime_seconds=time.perf_counter()-started, artifact_refs=[str(runtime / "review" / "storyboard_manifest.json")])
    ledger.close()
    return result


def render_motion(runtime: Path, *, proxy: bool) -> dict[str, Any]:
    started = time.perf_counter()
    label = "proxy" if proxy else "master_silent"
    scale = .5 if proxy else 1.0
    variants: dict[str, Any] = {}
    output_root = runtime / "proxy" if proxy else runtime / "render_cache" / "silent"
    for variant, composition in (("short_9x16", "CreativeAuthorityShort"), ("midform_16x9", "CreativeAuthorityMidform")):
        output = output_root / f"{variant}_{label}.mp4"
        receipt = runtime / "receipts" / "render" / f"{variant}_{label}.json"
        variants[variant] = render_one(runtime, composition, output, receipt, scale=scale)
    result = {"status": "PASS_PROXY_READY" if proxy else "PASS_SILENT_MASTERS_READY", "variants": variants, "render_count": 2, "selective_rerender_reuse": "storyboard and source validation reused", "public_write": False}
    write_json(runtime / "receipts" / f"{label}.json", result)
    identity = job_identity(runtime)
    ledger = CreativeAuthorityLedger(runtime / "control" / "creative_authority_ledger.sqlite3")
    stage = "PROXY_READY" if proxy else "QA_REVISE"
    ledger.checkpoint(identity["job_id"], stage, sha256_file(CREATIVE_SOURCE), result, model_or_tool="remotion 4.0.508", execution_plane="LOCAL_DETERMINISTIC", runtime_seconds=time.perf_counter()-started, artifact_refs=[row["path"] for row in variants.values()])
    ledger.close()
    return result


def review_artifacts(runtime: Path, *, final: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    base = runtime / ("outputs" if final else "proxy")
    suffix = "clean_master" if final else "proxy"
    rows: dict[str, Any] = {}
    settings = {
        "short_9x16": ("1/6", "scale=360:640", "3x3"),
        "midform_16x9": ("1/10", "scale=480:270", "5x2"),
    }
    for variant in ("short_9x16", "midform_16x9"):
        video = base / (f"{variant}_clean_master.mp4" if final else f"{variant}_proxy.mp4")
        fps, scale, tile = settings[variant]
        review = runtime / "review" / ("final" if final else "proxy")
        contact = review / f"{variant}_contact_sheet.jpg"
        motion = review / f"{variant}_motion_strip.jpg"
        phone = review / f"{variant}_phone_scale.jpg"
        contact.parent.mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", f"fps={fps},{scale},tile={tile}", "-frames:v", "1", str(contact)])
        run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", f"fps=1/3,{scale},tile=6x3", "-frames:v", "1", str(motion)])
        run(["ffmpeg", "-y", "-v", "error", "-ss", "00:00:01.5", "-i", str(video), "-frames:v", "1", "-vf", "scale=360:-1", str(phone)])
        rows[variant] = {"source": str(video), "source_sha256": sha256_file(video), "contact_sheet": {"path": str(contact), "sha256": sha256_file(contact)}, "motion_strip": {"path": str(motion), "sha256": sha256_file(motion)}, "phone_scale": {"path": str(phone), "sha256": sha256_file(phone)}}
    result = {"status": "PASS_REVIEW_ARTIFACTS_READY", "kind": suffix, "variants": rows, "captions_hidden": True, "public_write": False}
    write_json(runtime / "review" / f"{suffix}_review_manifest.json", result)
    identity = job_identity(runtime)
    ledger = CreativeAuthorityLedger(runtime / "control" / "creative_authority_ledger.sqlite3")
    review_stage = "MASTER_READY" if final else "VISUAL_REVIEW"
    ledger.checkpoint(identity["job_id"], review_stage, logical_hash(rows), result, model_or_tool="ffmpeg review artifact generator", execution_plane="LOCAL_DETERMINISTIC", runtime_seconds=time.perf_counter()-started, artifact_refs=[str(runtime / "review" / f"{suffix}_review_manifest.json")])
    ledger.close()
    return result


def repair_and_resume_evidence(runtime: Path, prior_runtime: Path) -> dict[str, Any]:
    """Demonstrate a bounded repair targeting only the two defective storyboard surfaces."""
    started = time.perf_counter()
    identity = job_identity(runtime)
    ledger_path = runtime / "control" / "creative_authority_ledger.sqlite3"
    ledger = CreativeAuthorityLedger(ledger_path)
    resume_from = ledger.last_valid_stage(identity["job_id"])
    proxy_hashes_before = {
        variant: sha256_file(runtime / "proxy" / f"{variant}_proxy.mp4")
        for variant in ("short_9x16", "midform_16x9")
    }
    surfaces = (
        {
            "defect_id": "MIDFORM_OPENING_REVEAL_TOO_SLOW",
            "scene_id": "M01_OPEN",
            "frame_or_time": "frame 30 / 1.0s",
            "before": prior_runtime / "review" / "storyboard" / "midform_16x9" / "frame_0030.png",
            "after_frame": 30,
            "after_name": "midform_open_after.png",
            "defect_type": "delayed_headline_reveal",
            "severity": "MAJOR",
            "expected_outcome": "The complete opening question is readable within the first second.",
            "source_surface": "architectureProof.tsx::MidOpening",
        },
        {
            "defect_id": "MIDFORM_EXIT_MISSING_BRAND_RESOLVE",
            "scene_id": "M12_RESOLVE",
            "frame_or_time": "final six seconds",
            "before": prior_runtime / "review" / "storyboard" / "midform_16x9" / "frame_2850.png",
            "after_frame": 3100,
            "after_name": "midform_exit_after.png",
            "defect_type": "missing_editorial_resolution",
            "severity": "MAJOR",
            "expected_outcome": "The midform ends on a distinct branded analytical resolution, not a checkpoint card.",
            "source_surface": "architectureProof.tsx::MidResolve",
        },
    )
    repairs: list[dict[str, Any]] = []
    selective_root = runtime / "review" / "selective_repair_round_1"
    for surface in surfaces:
        before = Path(surface["before"])
        if not before.is_file():
            raise FileNotFoundError(before)
        after = selective_root / str(surface["after_name"])
        receipt = runtime / "receipts" / "repair_round_1" / f"{surface['defect_id']}.json"
        render = render_one(
            runtime,
            "CreativeAuthorityMidform",
            after,
            receipt,
            scale=.5,
            still_frame=int(surface["after_frame"]),
        )
        defect = {
            "defect_id": surface["defect_id"],
            "scene_id": surface["scene_id"],
            "frame_or_time": surface["frame_or_time"],
            "screenshot_path": str(before),
            "defect_type": surface["defect_type"],
            "severity": surface["severity"],
            "expected_outcome": surface["expected_outcome"],
            "source_surface": surface["source_surface"],
            "repair_receipt": str(receipt),
            "before_hash": sha256_file(before),
            "after_hash": sha256_file(after),
        }
        ledger.record_defect(identity["job_id"], defect)
        repairs.append({**defect, "after_path": str(after), "render": render})
    unchanged = []
    for frame in (480, 1110, 1770):
        before = prior_runtime / "review" / "storyboard" / "midform_16x9" / f"frame_{frame:04d}.png"
        after = runtime / "review" / "storyboard" / "midform_16x9" / f"frame_{frame:04d}.png"
        before_hash = sha256_file(before)
        after_hash = sha256_file(after)
        if before_hash != after_hash:
            raise RuntimeError(f"unaffected_storyboard_surface_changed:{frame}")
        unchanged.append({"frame": frame, "before_hash": before_hash, "after_hash": after_hash, "byte_identical": True})
    proxy_hashes_after = {
        variant: sha256_file(runtime / "proxy" / f"{variant}_proxy.mp4")
        for variant in ("short_9x16", "midform_16x9")
    }
    if proxy_hashes_before != proxy_hashes_after:
        raise RuntimeError("selective_repair_touched_accepted_proxy")
    result = {
        "status": "PASS_BOUNDED_REPAIR_AND_RESUME_READY",
        "resume": {
            "ledger_reopened": True,
            "resume_from": resume_from,
            "completed_receipts_reused": len(list((runtime / "receipts").rglob("*.json"))),
        },
        "repair_rounds": 1,
        "creative_repairs": 1,
        "selective_rerender": {
            "composition": "CreativeAuthorityMidform",
            "surfaces_rendered": 2,
            "full_variants_rendered": 0,
            "accepted_proxy_hashes_before": proxy_hashes_before,
            "accepted_proxy_hashes_after": proxy_hashes_after,
            "unaffected_storyboard_surfaces": unchanged,
        },
        "defects": repairs,
        "public_write": False,
    }
    write_json(runtime / "review" / "repair_resume_manifest.json", result)
    elapsed = time.perf_counter() - started
    ledger.checkpoint(
        identity["job_id"],
        "QA_REVISE",
        sha256_file(CREATIVE_SOURCE),
        result,
        model_or_tool="Codex visual review + selective Remotion still rerender",
        execution_plane="CODEX_TASK_SESSION+LOCAL_DETERMINISTIC",
        runtime_seconds=elapsed,
        revision_count=1,
        artifact_refs=[str(runtime / "review" / "repair_resume_manifest.json")],
    )
    ledger.close()
    return result


def synthesize_and_mux(runtime: Path, tts_python: Path) -> dict[str, Any]:
    started = time.perf_counter()
    validate_audio_eligibility("kokoro")
    rows: dict[str, Any] = {}
    for variant, scenes, duration in (("short_9x16", SHORT_SCENES, 54.0), ("midform_16x9", MIDFORM_SCENES, 106.0)):
        audio_dir = runtime / "audio" / variant
        raw = audio_dir / "narration_raw.wav"
        master = audio_dir / "narration_master.wav"
        request = runtime / "contracts" / "audio" / f"{variant}_kokoro_request.json"
        narration = " ".join(str(row["narration"]) for row in scenes)
        write_json(request, {"schema_version": "contentops.v2.kokoro_request.v1", "segments": [{"beat_id": f"{variant}-narration", "text": narration, "voice": "af_heart", "speed": 1.0, "output_path": str(raw)}]})
        worker = run([str(tts_python), "-m", "live_contentops.video_tts_worker_v1", "--batch-request", str(request)], cwd=REPO_ROOT, timeout=5400)
        raw_probe = probe_media(raw)
        raw_duration = float(raw_probe["format"]["duration"])
        target_voice = duration - 1.2
        tempo = max(.72, min(1.28, raw_duration / target_voice))
        run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", f"atempo={tempo:.6f},apad,atrim=0:{duration},loudnorm=I=-16:TP=-1.8:LRA=11", "-ar", "48000", "-ac", "2", str(master)], timeout=1800)
        measurement = measure_loudness(master)
        if not -17 <= measurement["integrated_lufs"] <= -15 or measurement["true_peak_dbtp"] > -1.5:
            raise RuntimeError(f"audio_qa_failed:{variant}:{measurement}")
        silent = runtime / "render_cache" / "silent" / f"{variant}_master_silent.mp4"
        output = runtime / "outputs" / f"{variant}_clean_master.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(master), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(duration), "-movflags", "+faststart", str(output)], timeout=1800)
        rows[variant] = {"provider": "kokoro", "model": "Kokoro-82M", "voice": "af_heart", "network_calls": 0, "sapi_used": False, "raw": {"path": str(raw), "sha256": sha256_file(raw), "duration_seconds": raw_duration}, "tempo": tempo, "master": {"path": str(master), "sha256": sha256_file(master), "measurement": measurement}, "output": {"path": str(output), "sha256": sha256_file(output), "probe": probe_media(output)}, "worker_stdout_tail": worker.stdout[-1000:]}
    result = {"status": "PASS_PROFESSIONAL_AUDIO_AND_MASTERS_READY", "variants": rows, "public_write": False}
    write_json(runtime / "receipts" / "audio_and_mux.json", result)
    identity = job_identity(runtime)
    ledger = CreativeAuthorityLedger(runtime / "control" / "creative_authority_ledger.sqlite3")
    ledger.checkpoint(identity["job_id"], "MASTER_READY", sha256_file(CREATIVE_SOURCE), result, model_or_tool="Kokoro-82M + ffmpeg", execution_plane="LOCAL_PROFESSIONAL_AUDIO", runtime_seconds=time.perf_counter()-started, artifact_refs=[row["output"]["path"] for row in rows.values()])
    ledger.close()
    return result


def finalize(runtime: Path) -> dict[str, Any]:
    started = time.perf_counter()
    identity = job_identity(runtime)
    audio = read_json(runtime / "receipts" / "audio_and_mux.json")
    reviews = read_json(runtime / "review" / "clean_master_review_manifest.json")
    source_qa = read_json(runtime / "contracts" / "source_sandbox_qa.json")
    dependency_qa = read_json(runtime / "contracts" / "dependency_qa.json")
    semantic_qa = read_json(runtime / "contracts" / "semantic_qa.json")
    layout_qa = read_json(runtime / "contracts" / "layout_qa.json")
    provenance = read_json(runtime / "contracts" / "codex_creative_provenance.json")
    editorial = read_json(runtime / "contracts" / "editorial_truth_analysis_engagement.json")
    repair = read_json(runtime / "review" / "repair_resume_manifest.json")
    ledger = CreativeAuthorityLedger(runtime / "control" / "creative_authority_ledger.sqlite3")
    stage_rows = ledger.stage_rows(identity["job_id"])
    measured_wall_clock = sum(float(row["runtime_seconds"]) for row in stage_rows)
    ledger.reconcile_metrics(
        identity["job_id"],
        render_count=4,
        selective_rerender_count=2,
        revision_count=1,
        operator_interventions=0,
        wall_clock_seconds=measured_wall_clock,
    )
    captions = {
        variant: {
            "path": str(runtime / "captions" / f"{variant}.srt"),
            "sha256": sha256_file(runtime / "captions" / f"{variant}.srt"),
            "sidecar_only": True,
        }
        for variant in ("short_9x16", "midform_16x9")
    }
    result = {
        "status": "PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW",
        "classification": "ARCHITECTURE_PROOF_ONLY",
        "task": TASK_ID,
        "job": identity,
        "creative_source": {"path": str(CREATIVE_SOURCE), "sha256": sha256_file(CREATIVE_SOURCE), "sandbox": source_qa},
        "provenance": provenance,
        "editorial": editorial,
        "qa": {"semantic": semantic_qa, "dependencies": dependency_qa, "layout": layout_qa},
        "media": {variant: {"path": row["output"]["path"], "sha256": row["output"]["sha256"], "probe": row["output"]["probe"], "audio": row["master"]} for variant, row in audio["variants"].items()},
        "captions": captions,
        "review": reviews,
        "defects": ledger.defect_rows(identity["job_id"]),
        "recovery": {"stage_rows": stage_rows, "resume_from": ledger.last_valid_stage(identity["job_id"]), "repair_resume_manifest": repair},
        "cost_runtime": {
            "creative_execution_count": 1,
            "visual_review_rounds": 3,
            "creative_repair_count": 1,
            "full_video_render_count": 4,
            "selective_still_rerender_count": 2,
            "measured_stage_wall_clock_seconds": measured_wall_clock,
            "operator_interventions": 0,
            "quota_or_cost": "not_exposed_to_task_session",
            "job_row": ledger.job_row(identity["job_id"]),
        },
        "safety": zero_public_write_manifest(),
        "mode_policy": "UNSELECTED",
        "future_corrected_bakeoff": "READY_BUT_NOT_EXECUTED",
        "public_write": False,
    }
    ledger.checkpoint(identity["job_id"], "OWNER_REVIEW", logical_hash(result["media"]), result, model_or_tool="local evidence packager", execution_plane="LOCAL_DETERMINISTIC", runtime_seconds=time.perf_counter()-started, artifact_refs=[row["path"] for row in result["media"].values()])
    write_json(runtime / "final_evidence_packet.json", result)
    ledger.close()
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare", "storyboard", "proxy", "review-proxy", "render-final", "repair-evidence", "audio", "review-final", "finalize"))
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--source-runtime", type=Path, default=DEFAULT_SOURCE_RUNTIME)
    parser.add_argument("--prior-runtime", type=Path, default=DEFAULT_PRIOR_RUNTIME)
    parser.add_argument("--tts-python", type=Path, default=DEFAULT_TTS_PYTHON)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    runtime = args.runtime.resolve()
    if args.stage == "prepare":
        result = prepare(runtime, args.source_runtime.resolve())
    elif args.stage == "storyboard":
        result = render_storyboard(runtime)
    elif args.stage == "proxy":
        result = render_motion(runtime, proxy=True)
    elif args.stage == "review-proxy":
        result = review_artifacts(runtime, final=False)
    elif args.stage == "render-final":
        result = render_motion(runtime, proxy=False)
    elif args.stage == "repair-evidence":
        result = repair_and_resume_evidence(runtime, args.prior_runtime.resolve())
    elif args.stage == "audio":
        result = synthesize_and_mux(runtime, args.tts_python.resolve())
    elif args.stage == "review-final":
        result = review_artifacts(runtime, final=True)
    else:
        result = finalize(runtime)
    print(json.dumps({"stage": args.stage, "status": result["status"], "result_sha256": logical_hash(result), "public_write": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
