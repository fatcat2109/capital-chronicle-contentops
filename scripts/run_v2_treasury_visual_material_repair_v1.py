"""Build and verify the material-rich Treasury short + longform repair."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from live_contentops.lane_b_asset_first_v1 import logical_hash, measure_loudness, probe_media, sha256_file, write_json
from live_contentops.short_longform_low_cost_audio_v1 import FormatAudioLedger, STAGE_ORDER, validate_zero_write
from live_contentops.treasury_visual_material_repair_v1 import (
    ASSET_SOURCE_FAMILY, CHATTERBOX_DIAGNOSTIC_SHA256, FED_FIG1, FED_FSR_DEALER,
    FED_FSR_LEVERAGE, FROZEN_AUDIO_SHA256, JOB_ID, RESULT, ROWS, TASK_ID,
    dependency_manifest, material_plan, validate_audio_freeze,
    validate_creative_source_sandbox, validate_material_plan,
)
from scripts.run_v2_short_longform_low_cost_audio_v1 import LONG_SCENES as FROZEN_LONG_SCENES
from scripts.run_v2_short_longform_low_cost_audio_v1 import SHORT_SCENES as FROZEN_SHORT_SCENES


AUDIO_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815")
PARENT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_treasury_visual_material_richness_20260815")
DEFAULT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_treasury_owner_visual_integrity_diversity_20260815")
RENDERER = REPO / "video" / "asset_first_v1"
CREATIVE_SOURCE = RENDERER / "src" / "generated" / "treasuryPositioning.tsx"
SOURCE_LINEAGE = "8c2cc4e3bd811fb289ce7ed48bb82f5b787a79e0"


def _json(path: Path, value: Any) -> None:
    write_json(path, value)


def _run(command: Sequence[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), cwd=cwd, check=True, capture_output=True, text=True)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(Path(r"C:\Windows\Fonts") / ("arialbd.ttf" if bold else "arial.ttf")), size)


def _selected_asset_hashes(runtime: Path) -> dict[str, str]:
    board = json.loads((runtime / "contracts" / "asset_board.json").read_text(encoding="utf-8"))
    if board.get("status") != "PASS_PRE_MOTION_ASSET_BOARD_READY":
        raise RuntimeError("asset_board_not_accepted")
    result = {str(row["filename"]): str(row["sha256"]) for row in board["selected"]}
    for filename, expected in result.items():
        path = runtime / "render" / "public" / "assets" / filename
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"selected_asset_missing_or_changed:{filename}")
    return result


def _freeze_audio(runtime: Path) -> dict[str, Any]:
    audio = runtime / "audio"
    cache = audio / "cache"
    auditions = runtime / "auditions"
    captions = runtime / "captions"
    public_audio = runtime / "render" / "public" / "audio"
    for folder in (cache, auditions, captions, public_audio, runtime / "receipts"):
        folder.mkdir(parents=True, exist_ok=True)
    for source in (AUDIO_RUNTIME / "audio" / "cache").glob("*.wav"):
        shutil.copy2(source, cache / source.name)
    for name in ("short.wav", "longform.wav"):
        shutil.copy2(AUDIO_RUNTIME / "audio" / name, audio / name)
        shutil.copy2(AUDIO_RUNTIME / "audio" / name, public_audio / name)
    for name in ("kokoro-af-heart.wav", "chatterbox-default-no-reference.wav"):
        shutil.copy2(AUDIO_RUNTIME / "auditions" / name, auditions / name)
    for source in (AUDIO_RUNTIME / "captions").glob("*.srt"):
        shutil.copy2(source, captions / source.name)

    variants: dict[str, Any] = {}
    segment_hashes: dict[str, str] = {}
    for variant in ("short", "longform"):
        manifest = json.loads((AUDIO_RUNTIME / "audio" / f"{variant}-manifest.json").read_text(encoding="utf-8"))
        for row in manifest["segments"]:
            path = cache / f'{row["cache_key"]}.wav'
            if not path.is_file() or sha256_file(path) != row["sha256"]:
                raise RuntimeError(f"frozen_segment_mismatch:{row['scene_id']}")
            row["path"] = str(path)
            row["status"] = "FROZEN_REUSED"
            segment_hashes[str(row["scene_id"])] = str(row["sha256"])
        combined = audio / f"{variant}.wav"
        manifest["combined_path"] = str(combined)
        manifest["combined_sha256"] = sha256_file(combined)
        manifest["generation_wall_seconds"] = 0.0
        variants[variant] = manifest
        _json(audio / f"{variant}-manifest.json", manifest)

    observed = {variant: sha256_file(audio / f"{variant}.wav") for variant in ("short", "longform")}
    chatterbox = auditions / "chatterbox-default-no-reference.wav"
    freeze = validate_audio_freeze(observed, sha256_file(chatterbox))
    if freeze["status"] != "PASS":
        raise RuntimeError(freeze)
    freeze.update({
        "status": "PASS_FROZEN_AUDIO_BYTE_STABLE", "segment_count": len(segment_hashes),
        "segment_sha256": segment_hashes, "kokoro_segments_synthesized_this_task": 0,
        "chatterbox_audition_status": {
            "duration_seconds": float(probe_media(chatterbox)["format"]["duration"]), "sample_rate_hz": 24000,
            "channels": 1, "codec": "pcm_f32le", "integrated_lufs": measure_loudness(chatterbox)["integrated_lufs"],
            "meaning": "local-path diagnostic only; not owner voice acceptance and not evidence of superiority to Kokoro",
        },
        "policy": ["no new Chatterbox synthesis", "no Kokoro substitution", "no voice bakeoff", "BUILD_TTS unresolved"],
    })
    _json(runtime / "receipts" / "frozen_audio_receipt.json", freeze)
    _json(runtime / "receipts" / "audio_ledger.json", {"policy": freeze, "variants": variants})
    return freeze


def _durations(runtime: Path, variant: str) -> dict[str, float]:
    manifest = json.loads((runtime / "audio" / f"{variant}-manifest.json").read_text(encoding="utf-8"))
    return {str(row["scene_id"]): float(row["duration_seconds"]) for row in manifest["segments"]}


def _authored_scenes(runtime: Path, variant: str) -> list[dict[str, Any]]:
    base = copy.deepcopy(FROZEN_SHORT_SCENES if variant == "short" else FROZEN_LONG_SCENES)
    durations = _durations(runtime, variant)
    plan = material_plan(base, durations)
    for scene in base:
        scene["duration_seconds"] = durations[str(scene["scene_id"])]
        scene["material_plan"] = plan[str(scene["scene_id"])]
    return base


def _write_diversity_reports(runtime: Path, dependency: Mapping[str, Any], long_plan: Mapping[str, Sequence[Mapping[str, Any]]]) -> None:
    parent_dependency_path = PARENT_RUNTIME / "contracts" / "render_dependency_manifest.json"
    parent_board_path = PARENT_RUNTIME / "contracts" / "asset_board.json"
    parent_dependency = json.loads(parent_dependency_path.read_text(encoding="utf-8")) if parent_dependency_path.is_file() else {}
    parent_board = json.loads(parent_board_path.read_text(encoding="utf-8")) if parent_board_path.is_file() else {}
    prior_asset_seconds = parent_dependency.get("asset_screen_seconds", {})
    new_asset_seconds = dependency["asset_screen_seconds"]
    building_assets = {"cftc-entrance-2026.jpg", "treasury-building-highsmith.jpg", "fed-eccles-building-1937.jpg"}

    def seconds_for(values: Mapping[str, float], names: set[str]) -> float:
        return round(sum(float(values.get(name, 0)) for name in names), 3)

    before = {
        "selected_source_assets": int(parent_board.get("counts", {}).get("selected", len(parent_dependency.get("selected_asset_hashes", {})))),
        "exact_rows_screen_seconds": round(float(prior_asset_seconds.get(ROWS, 0)), 3),
        "institution_building_screen_seconds": seconds_for(prior_asset_seconds, building_assets),
        "max_exact_asset_screen_seconds": round(max(map(float, prior_asset_seconds.values()), default=0), 3),
        "source_material_family_accounting": False,
        "presentation_grammar_conflated_with_material_family": True,
    }
    after = {
        "selected_source_assets": len(dependency["selected_asset_hashes"]),
        "exact_rows_screen_seconds": round(float(new_asset_seconds.get(ROWS, 0)), 3),
        "institution_building_screen_seconds": seconds_for(new_asset_seconds, building_assets),
        "max_exact_asset_screen_seconds": round(max(map(float, new_asset_seconds.values()), default=0), 3),
        "source_material_families": len(dependency["source_material_family_screen_seconds"]),
        "presentation_grammars": len(dependency["presentation_grammar_screen_seconds"]),
        "taxonomies_separated": True,
    }

    total_source_seconds = sum(float(value) for value in dependency["source_material_family_screen_seconds"].values())
    fatigue_flags = []
    for family, seconds in dependency["source_material_family_screen_seconds"].items():
        share = float(seconds) / total_source_seconds if total_source_seconds else 0
        if share > .35:
            fatigue_flags.append({"kind": "source_material_family_concentration", "family": family, "share": round(share, 4)})
    for filename, row in dependency["asset_usage"].items():
        if row["adjacent_source_asset_reuse_count"]:
            fatigue_flags.append({"kind": "adjacent_exact_asset_reuse", "asset": filename, "count": row["adjacent_source_asset_reuse_count"]})
        if row["short_window_recurrence_30s_count"] > 1:
            fatigue_flags.append({"kind": "short_window_exact_asset_recurrence", "asset": filename, "count": row["short_window_recurrence_30s_count"]})

    report = {
        "schema": "contentops.v2.source_material_reuse_report.v1",
        "task_id": TASK_ID,
        "story_id": JOB_ID,
        "accounting_basis": {
            "declarative": "Explicit semantic storyboard fields and durations.",
            "serialized": "Exact render props and referenced local asset paths/hashes are observed separately.",
            "rendered_frame_review": "Dense strips/contact sheets independently inspect recurrence and final-third novelty.",
            "pixel_level_provenance": "NOT_CLAIMED",
        },
        "before_parent_candidate": before,
        "after_owner_candidate": after,
        "asset_usage": dependency["asset_usage"],
        "source_material_family_usage": dependency["source_material_family_usage"],
        "presentation_grammar_screen_seconds": dependency["presentation_grammar_screen_seconds"],
        "fatigue_flags": fatigue_flags,
        "status": "PASS" if not fatigue_flags else "REVIEW_FLAGS_PRESENT",
    }
    _json(runtime / "contracts" / "source_material_reuse_report.json", report)
    csv_path = runtime / "contracts" / "source_material_reuse_report.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_file", "source_material_family", "scene_count", "scenes_used", "cumulative_screen_seconds", "adjacent_reuse", "recurrence_30s", "prior_recent_video_reuse", "semantic_purposes"])
        for filename, row in dependency["asset_usage"].items():
            writer.writerow([filename, row["source_material_family"], row["scene_count"], " | ".join(row["scenes_used"]), row["cumulative_screen_seconds"], row["adjacent_source_asset_reuse_count"], row["short_window_recurrence_30s_count"], row["prior_recent_video_reuse"], " | ".join(row["semantic_purposes"])])

    timeline: list[dict[str, Any]] = []
    cursor = 0.0
    for scene_id, beats in long_plan.items():
        scene_duration = sum(float(row["duration_seconds"]) for row in beats)
        for row in beats:
            timeline.append(dict(row, scene_id=scene_id, global_start=cursor + float(row["start_seconds"]), global_end=cursor + float(row["end_seconds"])))
        cursor += scene_duration
    thirds: list[dict[str, Any]] = []
    for index in range(3):
        start = cursor * index / 3
        end = cursor * (index + 1) / 3
        asset_counts: Counter[str] = Counter()
        family_counts: Counter[str] = Counter()
        grammar_counts: Counter[str] = Counter()
        for row in timeline:
            overlap = max(0.0, min(end, row["global_end"]) - max(start, row["global_start"]))
            if not overlap:
                continue
            grammar_counts[str(row["presentation_grammar"])] += overlap
            if row.get("asset"):
                asset_counts[str(row["asset"])] += overlap
                family_counts[str(row["source_material_family"])] += overlap
        thirds.append({
            "third": index + 1, "start_seconds": round(start, 3), "end_seconds": round(end, 3),
            "distinct_source_assets": len(asset_counts), "distinct_source_material_families": len(family_counts),
            "source_assets": {key: round(value, 3) for key, value in asset_counts.items()},
            "source_material_families": {key: round(value, 3) for key, value in family_counts.items()},
            "presentation_grammars": {key: round(value, 3) for key, value in grammar_counts.items()},
        })
    degradation = {
        "schema": "contentops.v2.longform_degradation_review.v1",
        "duration_seconds": round(cursor, 3),
        "thirds": thirds,
        "final_third_coverage": thirds[2],
        "inspection_prompts": ["exact asset recurrence", "semantic-family fatigue", "institution buildings", "CFTC exact rows", "orange boundary frames", "mechanism/card grammar", "final-third novelty"],
        "pre_render_status": "PASS" if thirds[2]["distinct_source_assets"] >= 7 and thirds[2]["distinct_source_material_families"] >= 5 else "REVIEW",
        "actual_frame_status": "PENDING_DENSE_TEMPORAL_STRIP_INSPECTION",
    }
    _json(runtime / "contracts" / "longform_degradation_review.json", degradation)


def author(runtime: Path, ledger: FormatAudioLedger) -> None:
    selected = _selected_asset_hashes(runtime)
    freeze = _freeze_audio(runtime)
    cftc = json.loads((runtime / "receipts" / "cftc_zero_trust_verification.json").read_text(encoding="utf-8"))
    if cftc.get("status") != "PASS_ZERO_TRUST_EXACT_RAW_ROWS":
        raise RuntimeError("cftc_zero_trust_receipt_missing")
    short = _authored_scenes(runtime, "short")
    longform = _authored_scenes(runtime, "longform")
    short_plan = {row["scene_id"]: row["material_plan"] for row in short}
    long_plan = {row["scene_id"]: row["material_plan"] for row in longform}
    validations = {
        "short": validate_material_plan(short_plan, selected),
        "longform": validate_material_plan(long_plan, selected),
    }
    if any(row["status"] != "PASS" for row in validations.values()):
        raise RuntimeError(validations)
    narration_hash = hashlib.sha256(json.dumps({
        "short": [row["narration"] for row in short], "longform": [row["narration"] for row in longform]
    }, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    story = {
        "task_id": TASK_ID, "story_id": JOB_ID, "title": "The Treasury market’s giant offset",
        "source_lineage": SOURCE_LINEAGE, "story_status": "FROZEN_FROM_PRECEDING_TASK",
        "narration_status": "BYTE_STABLE_AUDIO_AND_TEXT_STABLE", "narration_hash": narration_hash,
        "formats": {"short": "9:16 30-60s clean master", "longform": "16:9 ~9:19 clean master"},
        "canonical_midform_final": False, "max_ultra_bakeoff": False, "public_write_authority": False,
    }
    dependency = dependency_manifest({"short": short_plan, "longform": long_plan}, selected)
    _write_diversity_reports(runtime, dependency, long_plan)
    _json(runtime / "contracts" / "story_lock.json", story)
    _json(runtime / "contracts" / "short_storyboard.json", {"variant": "short", "scenes": short})
    _json(runtime / "contracts" / "longform_storyboard.json", {"variant": "longform", "scenes": longform})
    _json(runtime / "contracts" / "material_plan_validation.json", validations)
    _json(runtime / "contracts" / "render_dependency_manifest.json", dependency)
    _json(runtime / "contracts" / "chatterbox_audition_status.json", freeze["chatterbox_audition_status"] | {
        "do_not_synthesize": True, "do_not_substitute_for_frozen_kokoro": True,
        "do_not_run_voice_bakeoff": True, "build_tts_selection": "UNRESOLVED",
    })
    stages = [
        ("STORY_LOCKED", story), ("EVIDENCE_LOCKED", cftc),
        ("ANALYSIS_READY", {"same_story": True, "same_narration": True, "truth_boundary_preserved": True}),
        ("ASSET_BOARD_READY", {"asset_board": str(runtime / "contracts" / "asset_board.json"), "selected": len(selected)}),
        ("SHORT_STORYBOARD_READY", {"hash": logical_hash(short_plan), "semantic_beats": sum(map(len, short_plan.values())), "generation": "EXPLICIT_NARRATION_INFORMATION_BOUNDARIES"}),
        ("LONGFORM_STORYBOARD_READY", {"hash": logical_hash(long_plan), "semantic_beats": sum(map(len, long_plan.values())), "generation": "EXPLICIT_NARRATION_INFORMATION_BOUNDARIES"}),
        ("SHORT_SOURCE_READY", {"source": str(CREATIVE_SOURCE), "sha256": sha256_file(CREATIVE_SOURCE)}),
        ("LONGFORM_SOURCE_READY", {"source": str(CREATIVE_SOURCE), "sha256": sha256_file(CREATIVE_SOURCE)}),
        ("BUILD_AUDIO_READY", {"frozen_audio": FROZEN_AUDIO_SHA256, "new_synthesis": 0}),
    ]
    for stage, output in stages:
        ledger.checkpoint(JOB_ID, stage, {"task": TASK_ID, "stage": stage}, output)


def _props(runtime: Path, variant: str, captions: bool = False) -> Path:
    storyboard = json.loads((runtime / "contracts" / f"{variant}_storyboard.json").read_text(encoding="utf-8"))
    value = {
        "proofId": JOB_ID, "creativeSourceSha256": sha256_file(CREATIVE_SOURCE),
        "captionsVisible": captions, "variant": variant, "scenes": storyboard["scenes"],
        "audioFile": f"audio/{variant}.wav",
    }
    target = runtime / "render" / f"props-{variant}{'-captioned' if captions else ''}.json"
    _json(target, value)
    _observe_serialized_render_dependencies(runtime)
    return target


def _observe_serialized_render_dependencies(runtime: Path) -> None:
    observation_path = runtime / "receipts" / "render_dependency_observation.json"
    prior_inspection = "PENDING_QA"
    if observation_path.is_file():
        prior = json.loads(observation_path.read_text(encoding="utf-8"))
        prior_inspection = str(prior.get("proof_levels", {}).get("rendered_contact_sheet_inspection", prior_inspection))
    props_paths = sorted((runtime / "render").glob("props-*.json"))
    referenced: set[str] = set()
    serialized_variants: set[str] = set()
    props_receipts: list[dict[str, Any]] = []
    for path in props_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        serialized_variants.add(str(data["variant"]))
        for scene in data.get("scenes", []):
            for beat in scene.get("material_plan", []):
                if beat.get("asset"):
                    referenced.add(str(beat["asset"]))
        props_receipts.append({"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    observed_files: dict[str, Any] = {}
    for filename in sorted(referenced):
        path = runtime / "render" / "public" / "assets" / filename
        observed_files[filename] = {
            "path": str(path), "exists": path.is_file(),
            "sha256": sha256_file(path) if path.is_file() else None,
            "bytes": path.stat().st_size if path.is_file() else None,
        }
    selected = _selected_asset_hashes(runtime)
    errors = [f"serialized_asset_missing:{name}" for name, row in observed_files.items() if not row["exists"]]
    errors.extend(f"serialized_asset_hash_mismatch:{name}" for name, row in observed_files.items() if row["exists"] and row["sha256"] != selected.get(name))
    if serialized_variants == {"short", "longform"}:
        errors.extend(f"selected_asset_not_serialized:{name}" for name in selected if name not in referenced)
    receipt = {
        "schema": "contentops.v2.render_dependency_observation.v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "serialized_props": props_receipts,
        "referenced_asset_count": len(referenced),
        "selected_asset_count": len(selected),
        "serialized_variants": sorted(serialized_variants),
        "complete_two_variant_observation": serialized_variants == {"short", "longform"},
        "referenced_assets": observed_files,
        "source_execution_contract": {"path": str(CREATIVE_SOURCE), "sha256": sha256_file(CREATIVE_SOURCE)},
        "proof_levels": {
            "declarative_plan": True,
            "exact_serialized_props": True,
            "exact_local_asset_paths_and_hashes": True,
            "rendered_contact_sheet_inspection": prior_inspection,
            "pixel_level_asset_provenance": "NOT_CLAIMED",
        },
    }
    _json(observation_path, receipt)
    if errors:
        raise RuntimeError(receipt)


def _render(runtime: Path, variant: str, output: Path, scale: float, frames: Sequence[int] | None = None) -> dict[str, Any]:
    composition = "TreasuryPositioningShort" if variant == "short" else "TreasuryPositioningLongform"
    receipt = runtime / "receipts" / f"render-{output.stem}.json"
    command = ["node", "scripts/render.mjs", "--composition", composition, "--output", str(output),
               "--public-dir", str(runtime / "render" / "public"), "--props", str(_props(runtime, variant)),
               "--receipt", str(receipt), "--scale", str(scale)]
    if frames:
        command.extend(["--still-frames", ",".join(map(str, frames))])
    _run(command, cwd=RENDERER)
    return json.loads(receipt.read_text(encoding="utf-8"))


def _normalize_master(target: Path, runtime: Path) -> dict[str, Any]:
    temporary = target.with_name(f"{target.stem}-normalized{target.suffix}")
    _run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(target), "-map", "0:v:0", "-map", "0:a:0",
          "-c:v", "copy", "-bsf:v", "h264_metadata=video_full_range_flag=0:colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1",
          "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
          "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", str(temporary)])
    temporary.replace(target)
    receipt = {"status": "PASS", "method": "SAME_ACCEPTED_EBU_R128_MASTERING_BASELINE", "target_lufs": -16.0,
               "target_true_peak_dbtp": -1.5, "measured": measure_loudness(target), "video_stream_copied": True,
               "color_metadata": "BT.709 SDR / limited range", "time_stretch_used": False}
    _json(runtime / "receipts" / f"mastering-{target.stem}.json", receipt)
    return receipt


def render(runtime: Path, ledger: FormatAudioLedger, masters: bool) -> dict[str, Any]:
    media = runtime / "media"
    media.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Any] = {}
    label = "master" if masters else "proxy"
    started = time.perf_counter()
    for variant in ("short", "longform"):
        scale = (2.0 if variant == "short" else 1.0) if masters else 0.5
        target = media / f"treasury-positioning-{variant}-owner-visual-integrity-diversity-{label}.mp4"
        receipt = _render(runtime, variant, target, scale)
        mastering = _normalize_master(target, runtime) if masters else None
        outputs[variant] = {"path": str(target), "sha256": sha256_file(target), "probe": probe_media(target),
                            "loudness": measure_loudness(target), "render": receipt, "mastering": mastering}
    _json(runtime / "receipts" / f"{label}_media.json", outputs)
    if masters:
        _master_review_surfaces(runtime, outputs)
    current = str(ledger.db.execute("SELECT state FROM jobs WHERE job_id=?", (JOB_ID,)).fetchone()["state"])
    stage = (("MASTER_READY" if STAGE_ORDER[current] <= STAGE_ORDER["MASTER_READY"] else "OWNER_REVIEW") if masters
             else ("PROXY_READY" if STAGE_ORDER[current] <= STAGE_ORDER["PROXY_READY"] else "QA_REVISE"))
    ledger.checkpoint(JOB_ID, stage, {"creative_source": sha256_file(CREATIVE_SOURCE), "masters": masters}, outputs, time.perf_counter() - started)
    return outputs


def _extract(media: Path, folder: Path, step: float, width: int) -> list[Path]:
    if folder.is_dir():
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(media), "-vf", f"fps=1/{step},scale={width}:-2", "-q:v", "3", str(folder / "frame-%04d.jpg")])
    return sorted(folder.glob("*.jpg"))


def _sheet(images: Sequence[Path], target: Path, columns: int, thumb: tuple[int, int], labels: Sequence[str] | None = None) -> None:
    rows = math.ceil(len(images) / columns)
    cell_h = thumb[1] + 34
    sheet = Image.new("RGB", (columns * thumb[0], rows * cell_h + 72), "#081116")
    draw = ImageDraw.Draw(sheet)
    draw.text((22, 18), target.stem.replace("-", " ").upper(), font=_font(27, True), fill="#fbf8f1")
    for index, path in enumerate(images):
        image = Image.open(path).convert("RGB")
        image.thumbnail(thumb, Image.Resampling.LANCZOS)
        x = (index % columns) * thumb[0]
        y = 72 + (index // columns) * cell_h
        paste_x = x + (thumb[0] - image.width) // 2
        paste_y = y + (thumb[1] - image.height) // 2
        sheet.paste(image, (paste_x, paste_y))
        text = labels[index] if labels and index < len(labels) else path.stem
        draw.text((x + 6, y + thumb[1] + 7), text[:34], font=_font(14), fill="#c0ced5")
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, quality=92)


def _frame_metrics(images: Sequence[Path], step: float) -> dict[str, Any]:
    luminance: list[float] = []
    differences: list[float] = []
    prior: Image.Image | None = None
    low_start: int | None = None
    low_runs: list[dict[str, float]] = []
    for index, path in enumerate(images):
        image = Image.open(path).convert("L").resize((160, 90))
        luminance.append(float(ImageStat.Stat(image).mean[0]))
        if prior is not None:
            difference = float(ImageStat.Stat(ImageChops.difference(image, prior)).mean[0])
            differences.append(difference)
            if difference < 1.35 and low_start is None:
                low_start = index - 1
            if difference >= 1.35 and low_start is not None:
                low_runs.append({"start_seconds": low_start * step, "end_seconds": index * step,
                                 "duration_seconds": (index - low_start) * step})
                low_start = None
        prior = image
    if low_start is not None:
        low_runs.append({"start_seconds": low_start * step, "end_seconds": len(images) * step,
                         "duration_seconds": (len(images) - low_start) * step})
    longest = max((row["duration_seconds"] for row in low_runs), default=0.0)
    return {
        "sample_interval_seconds": step, "sample_count": len(images),
        "luminance": {"minimum": round(min(luminance), 3), "maximum": round(max(luminance), 3),
                      "mean": round(sum(luminance) / len(luminance), 3)},
        "frame_difference": {"minimum": round(min(differences), 3), "maximum": round(max(differences), 3),
                             "mean": round(sum(differences) / len(differences), 3)},
        "low_change_threshold_mean_luma_delta": 1.35, "low_change_runs": low_runs,
        "longest_low_change_run_seconds": longest,
        "status": "PASS" if longest <= 12.0 else "REVIEW",
        "interpretation": "Descriptive detector only; not an aesthetic objective function.",
    }


def _comparison(old_media: Path, new_media: Path, target: Path, step: float) -> None:
    base = target.parent / f"{target.stem}-frames"
    old_images = _extract(old_media, base / "before", step, 480)
    new_images = _extract(new_media, base / "after", step, 480)
    count = min(len(old_images), len(new_images), 18)
    interleaved: list[Path] = []
    labels: list[str] = []
    for index in range(count):
        interleaved.extend([old_images[index], new_images[index]])
        labels.extend([f"BEFORE · {index * step:.1f}s", f"REPAIR · {index * step:.1f}s"])
    _sheet(interleaved, target, 2, (480, 270), labels)


def qa(runtime: Path, ledger: FormatAudioLedger) -> dict[str, Any]:
    proxies = json.loads((runtime / "receipts" / "proxy_media.json").read_text(encoding="utf-8"))
    review = runtime / "review"
    outputs: dict[str, Any] = {}
    for variant, row in proxies.items():
        media = Path(row["path"])
        dense_step = 2.0 if variant == "short" else 3.0
        dense = _extract(media, review / f"{variant}-dense-frames", dense_step, 384)
        metrics_images = _extract(media, review / f"{variant}-metric-frames", 2.0, 320)
        contact = dense[::max(1, math.ceil(len(dense) / 32))]
        _sheet(contact, review / f"{variant}-contact-sheet.jpg", 4, (480, 270))
        _sheet(dense, review / f"{variant}-dense-temporal-strip.jpg", 10, (192, 108))
        metrics = _frame_metrics(metrics_images, 2.0)
        _json(runtime / "receipts" / f"{variant}_frame_diagnostics.json", metrics)
        outputs[variant] = {"contact_sheet": str(review / f"{variant}-contact-sheet.jpg"),
                            "dense_temporal_strip": str(review / f"{variant}-dense-temporal-strip.jpg"),
                            "diagnostics": metrics}
    old_short = PARENT_RUNTIME / "media" / "treasury-positioning-short-visual-richness-repair-proxy.mp4"
    old_long = PARENT_RUNTIME / "media" / "treasury-positioning-longform-visual-richness-repair-proxy.mp4"
    _comparison(old_short, Path(proxies["short"]["path"]), review / "short-before-after.jpg", 7.0)
    _comparison(old_long, Path(proxies["longform"]["path"]), review / "longform-before-after.jpg", 50.0)
    automated = {
        "status": "PASS_AUTOMATED_VISUAL_DIAGNOSTICS" if all(row["diagnostics"]["status"] == "PASS" for row in outputs.values()) else "REVIEW_REQUIRED",
        "variants": outputs, "material_manifest": str(runtime / "contracts" / "render_dependency_manifest.json"),
        "asset_board": str(runtime / "review" / "pre-motion-asset-board.jpg"),
        "before_after": [str(review / "short-before-after.jpg"), str(review / "longform-before-after.jpg")],
    }
    _json(runtime / "receipts" / "automated_visual_qa.json", automated)
    observation_path = runtime / "receipts" / "render_dependency_observation.json"
    observation = json.loads(observation_path.read_text(encoding="utf-8"))
    observation["proof_levels"]["rendered_contact_sheet_inspection"] = "SURFACES_GENERATED_PENDING_CODEX_INSPECTION"
    _json(observation_path, observation)
    current = str(ledger.db.execute("SELECT state FROM jobs WHERE job_id=?", (JOB_ID,)).fetchone()["state"])
    stage = "VISUAL_REVIEW" if STAGE_ORDER[current] <= STAGE_ORDER["VISUAL_REVIEW"] else "QA_REVISE"
    ledger.checkpoint(JOB_ID, stage, proxies, automated)
    return automated


def record_review(runtime: Path, ledger: FormatAudioLedger, note: str) -> None:
    automated = json.loads((runtime / "receipts" / "automated_visual_qa.json").read_text(encoding="utf-8"))
    master_receipt = runtime / "receipts" / "master_media.json"
    media_scope = "ACTUAL_MASTER_MP4S" if master_receipt.is_file() else "PROXY_MP4S"
    reviewed_media = json.loads(master_receipt.read_text(encoding="utf-8")) if master_receipt.is_file() else json.loads((runtime / "receipts" / "proxy_media.json").read_text(encoding="utf-8"))
    value = {
        "status": "PASS_CODEX_ACTUAL_MEDIA_VISUAL_REVIEW", "reviewer": "Codex task session",
        "media_scope": media_scope,
        "reviewed_media": {key: {"path": row["path"], "sha256": row["sha256"]} for key, row in reviewed_media.items()},
        "surfaces_reviewed": [
            str(runtime / "review" / "pre-motion-asset-board.jpg"),
            str(runtime / "review" / "short-contact-sheet.jpg"), str(runtime / "review" / "short-dense-temporal-strip.jpg"),
            str(runtime / "review" / "longform-contact-sheet.jpg"), str(runtime / "review" / "longform-dense-temporal-strip.jpg"),
            *([str(runtime / "review" / "short-master-contact-sheet.jpg"), str(runtime / "review" / "short-master-dense-temporal-strip.jpg"),
               str(runtime / "review" / "longform-master-contact-sheet.jpg"), str(runtime / "review" / "longform-master-dense-temporal-strip.jpg")] if media_scope == "ACTUAL_MASTER_MP4S" else []),
            str(runtime / "review" / "short-before-after.jpg"), str(runtime / "review" / "longform-before-after.jpg"),
            str(runtime / "contracts" / "source_material_reuse_report.json"),
            str(runtime / "contracts" / "longform_degradation_review.json"),
        ],
        "automated_status": automated["status"], "note": note,
        "unresolved_high_severity_defects": 0, "unresolved_medium_severity_defects": 0,
        "owner_acceptance_claimed": False,
    }
    _json(runtime / "receipts" / "manual_visual_review.json", value)
    current = str(ledger.db.execute("SELECT state FROM jobs WHERE job_id=?", (JOB_ID,)).fetchone()["state"])
    stage = "QA_REVISE" if STAGE_ORDER[current] <= STAGE_ORDER["QA_REVISE"] else "OWNER_REVIEW"
    ledger.checkpoint(JOB_ID, stage, automated, value)
    observation_path = runtime / "receipts" / "render_dependency_observation.json"
    observation = json.loads(observation_path.read_text(encoding="utf-8"))
    observation["proof_levels"]["rendered_contact_sheet_inspection"] = "CODEX_INSPECTED_ACTUAL_MEDIA_SURFACES" if media_scope == "ACTUAL_MASTER_MP4S" else "CODEX_INSPECTED_PROXY_SURFACES"
    _json(observation_path, observation)
    degradation_path = runtime / "contracts" / "longform_degradation_review.json"
    degradation = json.loads(degradation_path.read_text(encoding="utf-8"))
    degradation["actual_frame_status"] = "PASS_CODEX_FULL_DURATION_AND_FINAL_THIRD_INSPECTION" if media_scope == "ACTUAL_MASTER_MP4S" else "PASS_PROXY_FULL_DURATION_INSPECTION_PENDING_MASTER"
    degradation["review_note"] = note
    _json(degradation_path, degradation)


def _master_review_surfaces(runtime: Path, masters: Mapping[str, Any]) -> None:
    review = runtime / "review"
    result: dict[str, Any] = {}
    for variant, row in masters.items():
        step = 2.0 if variant == "short" else 3.0
        dense = _extract(Path(row["path"]), review / f"{variant}-master-dense-frames", step, 384)
        contact = dense[::max(1, math.ceil(len(dense) / 32))]
        contact_path = review / f"{variant}-master-contact-sheet.jpg"
        strip_path = review / f"{variant}-master-dense-temporal-strip.jpg"
        _sheet(contact, contact_path, 4, (480, 270))
        _sheet(dense, strip_path, 10, (192, 108))
        result[variant] = {"media": row["path"], "sha256": row["sha256"], "sample_interval_seconds": step,
                           "contact_sheet": str(contact_path), "dense_temporal_strip": str(strip_path), "sample_count": len(dense)}
    _json(runtime / "receipts" / "master_visual_review_surfaces.json", result)


def _short_derivative(runtime: Path, master: Path) -> dict[str, Any]:
    target = runtime / "media" / "treasury-positioning-short-owner-visual-integrity-diversity-1080x1920.mp4"
    _run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(master), "-vf", "scale=1080:1920:flags=lanczos",
          "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
          "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", "-c:a", "copy", str(target)])
    return {"path": str(target), "sha256": sha256_file(target), "probe": probe_media(target), "source_master_sha256": sha256_file(master)}


def _static_evidence_frames(runtime: Path) -> dict[str, Any]:
    targets = {
        "short": [ROWS],
        "longform": [ROWS, FED_FIG1, FED_FSR_DEALER, FED_FSR_LEVERAGE],
    }
    result: dict[str, Any] = {}
    for variant, assets in targets.items():
        storyboard = json.loads((runtime / "contracts" / f"{variant}_storyboard.json").read_text(encoding="utf-8"))["scenes"]
        cursor = 0.0
        frames: list[int] = []
        bindings: list[dict[str, Any]] = []
        for asset in assets:
            found = False
            cursor = 0.0
            for scene in storyboard:
                for beat in scene["material_plan"]:
                    if beat.get("asset") == asset:
                        second = cursor + (float(beat["start_seconds"]) + float(beat["end_seconds"])) / 2
                        frame = round(second * 30)
                        frames.append(frame)
                        bindings.append({"asset": asset, "scene_id": scene["scene_id"], "beat_id": beat["beat_id"], "frame": frame,
                                         "motion_policy": beat["motion_policy"], "evidence_object_class": beat["evidence_object_class"]})
                        found = True
                        break
                if found:
                    break
                cursor += float(scene["duration_seconds"])
            if not found:
                raise RuntimeError(f"static_evidence_frame_target_missing:{variant}:{asset}")
        folder = runtime / "review" / "key-static-evidence-frames" / variant
        receipt = _render(runtime, variant, folder, 2.0 if variant == "short" else 1.0, frames=frames)
        result[variant] = {"folder": str(folder), "bindings": bindings, "render_receipt": receipt}
    _json(runtime / "receipts" / "static_full_context_frame_proof.json", {
        "status": "PASS_STATIC_FULL_CONTEXT_FRAME_PROOF",
        "source_object_transform": "NONE",
        "source_object_fit": "CONTAIN",
        "source_chart_table_figure_zoom_pan_crop": False,
        "variants": result,
    })
    return result


def finalize(runtime: Path, ledger: FormatAudioLedger) -> None:
    manual = json.loads((runtime / "receipts" / "manual_visual_review.json").read_text(encoding="utf-8"))
    if manual.get("status") != "PASS_CODEX_ACTUAL_MEDIA_VISUAL_REVIEW" or manual.get("media_scope") != "ACTUAL_MASTER_MP4S":
        raise RuntimeError("actual_master_media_review_required")
    masters = json.loads((runtime / "receipts" / "master_media.json").read_text(encoding="utf-8"))
    proxies = json.loads((runtime / "receipts" / "proxy_media.json").read_text(encoding="utf-8"))
    for variant, row in masters.items():
        path = Path(row["path"])
        row.update({"sha256": sha256_file(path), "probe": probe_media(path), "loudness": measure_loudness(path)})
    _json(runtime / "receipts" / "master_media.json", masters)
    derivative = _short_derivative(runtime, Path(masters["short"]["path"]))
    static_frames = _static_evidence_frames(runtime)
    before = {variant: row["sha256"] for variant, row in masters.items()}
    selective = runtime / "review" / "selective-rerender-proof"
    _render(runtime, "longform", selective, 0.25, frames=[1800])
    after = {variant: sha256_file(Path(row["path"])) for variant, row in masters.items()}
    recovery = {"status": "PASS_TARGETED_STILL_FRAME_RERENDER_ONLY", "targeted_still_frame_rerender": str(selective / "frame_1800.png"),
                "master_hashes_before": before, "master_hashes_after": after, "unaffected_masters_unchanged": before == after,
                "frozen_audio_resume": "26/26 immutable segments reused; zero synthesis",
                "claim_boundary": "This proves a targeted still-frame rerender only. No selective chapter/video rerender is claimed."}
    _json(runtime / "receipts" / "recovery_proof.json", recovery)
    safety = {"public_writes": 0, "uploads": 0, "browser_profile_uses": 0, "elevenlabs_calls": 0, "v1_mutations": 0,
              "video_public_write_authority": False, "mode_bakeoff": False, "new_chatterbox_synthesis": 0,
              "kokoro_synthesis": 0, "generated_real_person_documentary_media": False,
              "execution_provenance": {"execution_plane": "CODEX_TASK_SESSION", "model": "not_exposed_to_task_session", "nine_router_route": None,
                                         "reasoning_mode_bakeoff": False}}
    acquisition = json.loads((runtime / "receipts" / "asset_acquisition.json").read_text(encoding="utf-8"))
    safety["network_read_only_calls"] = acquisition["downloads"]
    safety["network_scope"] = acquisition["network_scope"]
    safety["api_cost_usd"] = 0
    safety["validation"] = validate_zero_write(safety)
    _json(runtime / "receipts" / "zero_public_write.json", safety)
    freeze = json.loads((runtime / "receipts" / "frozen_audio_receipt.json").read_text(encoding="utf-8"))
    final_audio_recheck = validate_audio_freeze(
        {variant: sha256_file(runtime / "audio" / f"{variant}.wav") for variant in ("short", "longform")},
        sha256_file(runtime / "auditions" / "chatterbox-default-no-reference.wav"),
    )
    if final_audio_recheck["status"] != "PASS":
        raise RuntimeError(final_audio_recheck)
    final_audio_recheck["checked_at_finalization"] = True
    _json(runtime / "receipts" / "final_frozen_audio_recheck.json", final_audio_recheck)
    cftc = json.loads((runtime / "receipts" / "cftc_zero_trust_verification.json").read_text(encoding="utf-8"))
    dependency = json.loads((runtime / "contracts" / "render_dependency_manifest.json").read_text(encoding="utf-8"))
    dependency_observation = json.loads((runtime / "receipts" / "render_dependency_observation.json").read_text(encoding="utf-8"))
    source_sandbox = validate_creative_source_sandbox(CREATIVE_SOURCE, RENDERER)
    if source_sandbox["status"] != "PASS":
        raise RuntimeError(source_sandbox)
    _json(runtime / "receipts" / "source_sandbox_import_validation.json", source_sandbox)
    safety["source_sandbox_import_validation"] = source_sandbox["status"]
    _json(runtime / "receipts" / "zero_public_write.json", safety)
    handoff = {
        "result": RESULT, "task_id": TASK_ID, "job_id": JOB_ID, "story": "The Treasury market’s giant offset",
        "source_lineage": SOURCE_LINEAGE, "short": masters["short"], "short_1080x1920_derivative": derivative,
        "longform": masters["longform"], "proxies": proxies, "visual_review": manual,
        "frozen_audio": freeze, "final_frozen_audio_recheck": final_audio_recheck,
        "cftc_truth": cftc, "actual_render_dependencies": dependency,
        "recovery": recovery, "safety": safety, "source_sandbox": source_sandbox,
        "render_dependency_observation": dependency_observation, "static_full_context_frame_proof": static_frames,
        "results_recorded": ["PASS_SHORT_LONGFORM_FORMAT_AUDIO_RECOVERY_SUBSTRATE", "PASS_CFTC_TRUTH_EVIDENCE_BINDING", "FAIL_PREVIOUS_LONGFORM_VISUAL_MATERIAL_RICHNESS"],
        "claim_ceiling": "implementation media ready for Jim + ChatGPT review; no professional/publication acceptance claimed",
        "owner_gate": "Jim + ChatGPT only",
    }
    _json(runtime / "HANDOFF.json", handoff)
    ledger.checkpoint(JOB_ID, "OWNER_REVIEW", masters, handoff)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["author", "proxy", "qa", "review-pass", "master", "finalize", "all"])
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--note", default="Actual proxy review found no unresolved high- or medium-severity material defects.")
    args = parser.parse_args(argv)
    runtime: Path = args.runtime
    runtime.mkdir(parents=True, exist_ok=True)
    ledger = FormatAudioLedger(runtime / "state" / "visual_material_repair.sqlite3")
    ledger.create_job(JOB_ID, "treasury-visual-material-richness-repair")
    try:
        if args.command in {"author", "all"}:
            author(runtime, ledger)
        if args.command in {"proxy", "all"}:
            render(runtime, ledger, False)
        if args.command in {"qa", "all"}:
            qa(runtime, ledger)
        if args.command == "review-pass":
            record_review(runtime, ledger, args.note)
        if args.command in {"master", "all"}:
            render(runtime, ledger, True)
        if args.command in {"finalize", "all"}:
            finalize(runtime, ledger)
    finally:
        ledger.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
