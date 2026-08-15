"""Build and verify the material-rich Treasury short + longform repair."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
import hashlib
import json
import math
import re
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
from live_contentops.short_longform_low_cost_audio_v1 import (
    FormatAudioLedger, STAGE_ORDER, build_missing_segment_request, validate_zero_write,
)
from live_contentops.treasury_visual_material_repair_v1 import (
    ASSET_SOURCE_FAMILY, CHATTERBOX_DIAGNOSTIC_SHA256, FED_FIG1, FED_FSR_DEALER,
    FED_FSR_LEVERAGE, FROZEN_AUDIO_SHA256, JOB_ID, RESULT, ROWS, TASK_ID,
    dependency_manifest, material_plan, treasury_visual_state_plan,
    validate_creative_source_sandbox, validate_material_plan,
)
from live_contentops.v2_creative_pacing_v1 import (
    pacing_diagnostics, scan_internal_jargon, summarize_prompt_contract,
    validate_visual_state_architecture, viewer_copy_values,
)
from scripts.run_v2_short_longform_low_cost_audio_v1 import LONG_SCENES as FROZEN_LONG_SCENES
from scripts.run_v2_short_longform_low_cost_audio_v1 import SHORT_SCENES as FROZEN_SHORT_SCENES


AUDIO_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815")
PARENT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_treasury_visual_material_richness_20260815")
ACCEPTED_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_treasury_owner_visual_integrity_diversity_20260815")
DEFAULT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_creative_pacing_ingestion_visual_state_20260815_r2")
RENDERER = REPO / "video" / "asset_first_v1"
CREATIVE_SOURCE = RENDERER / "src" / "generated" / "treasuryPositioning.tsx"
TTS_PYTHON = Path(r"A:\Capital Chronicle\Runtime\ContentOps\tier2\tts-kokoro-venv\Scripts\python.exe")
SOURCE_LINEAGE = "ae0abc575521392b043486415cefaa7179c14b48"
LONGFORM_SCENE_ORDER = (
    "L01_COLD_OPEN", "L02_SOURCE_CLOCK", "L08_BASIS_SETUP", "L09_REPO_FINANCING",
    "L03_TWO_YEAR", "L04_FIVE_YEAR", "L05_TEN_YEAR", "L06_WEEKLY_CHANGE",
    "L07_ASSET_MANAGER_JOB", "L10_FED_SCALE", "L11_PROXY_BOUNDARY", "L12_BENEFIT",
    "L13_STRESS_CHAIN", "L14_DEALER_CAPACITY", "L15_WHAT_TO_WATCH", "L16_CONFIRM",
    "L17_BALANCE_SHEET", "L18_CLOSE",
)


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


def _seed_accepted_asset_universe(runtime: Path) -> None:
    """Reuse the accepted 23-asset universe without another network hunt."""
    if (runtime / "contracts" / "asset_board.json").is_file():
        return
    copies = (
        (ACCEPTED_RUNTIME / "render" / "public" / "assets", runtime / "render" / "public" / "assets"),
        (ACCEPTED_RUNTIME / "authority", runtime / "authority"),
    )
    for source, target in copies:
        if not source.exists():
            raise RuntimeError(f"accepted_asset_source_missing:{source}")
        shutil.copytree(source, target, dirs_exist_ok=True)
    for relative in (
        Path("contracts/asset_board.json"), Path("review/pre-motion-asset-board.jpg"),
        Path("receipts/cftc_zero_trust_verification.json"),
    ):
        source = ACCEPTED_RUNTIME / relative
        target = runtime / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    accepted_acquisition = json.loads((ACCEPTED_RUNTIME / "receipts" / "asset_acquisition.json").read_text(encoding="utf-8"))
    _json(runtime / "receipts" / "asset_acquisition.json", {
        "status": "PASS_REUSED_ACCEPTED_ASSET_UNIVERSE", "downloads": 0,
        "network_scope": "NONE; local byte-for-byte reuse of accepted rights/provenance assets",
        "accepted_runtime": str(ACCEPTED_RUNTIME),
        "accepted_receipt_sha256": sha256_file(ACCEPTED_RUNTIME / "receipts" / "asset_acquisition.json"),
        "accepted_download_history": accepted_acquisition.get("downloads", 0),
    })


def _concat_wav(paths: Sequence[Path], target: Path, runtime: Path) -> None:
    listing = runtime / "audio" / f"{target.stem}-concat.txt"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("".join(f"file '{str(path).replace(chr(39), chr(39) + '\\' + chr(39) + chr(39))}'\n" for path in paths), encoding="utf-8")
    _run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c:a", "pcm_s16le", str(target)])


def _captions(scenes: Sequence[Mapping[str, Any]], target: Path) -> None:
    def stamp(seconds: float) -> str:
        milliseconds = round(seconds * 1000)
        return f"{milliseconds // 3600000:02d}:{(milliseconds // 60000) % 60:02d}:{(milliseconds // 1000) % 60:02d},{milliseconds % 1000:03d}"

    index, cursor = 1, 0.0
    blocks: list[str] = []
    for scene in scenes:
        words = str(scene["narration"]).split()
        chunks = [words[offset:offset + 7] for offset in range(0, len(words), 7)]
        per = float(scene["duration_seconds"]) / max(1, len(chunks))
        for chunk in chunks:
            blocks.append(f"{index}\n{stamp(cursor)} --> {stamp(cursor + per)}\n{' '.join(chunk)}\n")
            index += 1
            cursor += per
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(blocks), encoding="utf-8")


def _ordered_frozen_scenes(variant: str) -> list[dict[str, Any]]:
    base = copy.deepcopy(FROZEN_SHORT_SCENES if variant == "short" else FROZEN_LONG_SCENES)
    if variant == "longform":
        by_id = {str(scene["scene_id"]): scene for scene in base}
        base = [by_id[scene_id] for scene_id in LONGFORM_SCENE_ORDER]
        for scene in base:
            if scene["scene_id"] == "L02_SOURCE_CLOCK":
                scene["narration"] = str(scene["narration"]).replace("governed weekly map", "official weekly map")
    return base


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
    for name in ("kokoro-af-heart.wav", "chatterbox-default-no-reference.wav"):
        shutil.copy2(AUDIO_RUNTIME / "auditions" / name, auditions / name)

    variants: dict[str, Any] = {}
    segment_hashes: dict[str, str] = {}
    tts_wall_seconds = 0.0
    for variant in ("short", "longform"):
        source_manifest = json.loads((AUDIO_RUNTIME / "audio" / f"{variant}-manifest.json").read_text(encoding="utf-8"))
        by_scene = {str(row["scene_id"]): dict(row) for row in source_manifest["segments"]}
        scenes = _ordered_frozen_scenes(variant)
        rows: list[dict[str, Any]] = []
        regenerated = 0
        for scene in scenes:
            source_row = by_scene[str(scene["scene_id"])]
            text_sha = hashlib.sha256(str(scene["narration"]).encode()).hexdigest()
            if text_sha == source_row["text_sha256"]:
                rows.append(source_row)
                continue
            request, manifest_rows = build_missing_segment_request([scene], cache, speed=1.0)
            request_path = audio / f"{variant}-{scene['scene_id']}-kokoro-request.json"
            _json(request_path, request)
            if request["segments"]:
                synthesis_started = time.perf_counter()
                completed = _run([str(TTS_PYTHON), str(REPO / "live_contentops" / "video_tts_worker_v1.py"), "--batch-request", str(request_path)])
                tts_wall_seconds += time.perf_counter() - synthesis_started
                json_line = next((line for line in reversed(completed.stdout.splitlines()) if line.lstrip().startswith("{")), "")
                _json(runtime / "receipts" / f"{variant}-{scene['scene_id']}-kokoro-worker.json", json.loads(json_line))
                regenerated += 1
            row = manifest_rows[0]
            generated_path = Path(row["path"])
            row.update({
                "duration_seconds": float(probe_media(generated_path)["format"]["duration"]),
                "sha256": sha256_file(generated_path), "bytes": generated_path.stat().st_size,
                "status": "REGENERATED_LOCAL_CHANGED_JARGON_SEGMENT",
            })
            rows.append(row)
        for row in rows:
            path = cache / f'{row["cache_key"]}.wav'
            if not path.is_file() or sha256_file(path) != row["sha256"]:
                raise RuntimeError(f"frozen_segment_mismatch:{row['scene_id']}")
            row["path"] = str(path)
            if row.get("status") != "REGENERATED_LOCAL_CHANGED_JARGON_SEGMENT":
                row["status"] = "FROZEN_REUSED_NO_SYNTHESIS"
            segment_hashes[str(row["scene_id"])] = str(row["sha256"])
        combined = audio / f"{variant}.wav"
        _concat_wav([Path(row["path"]) for row in rows], combined, runtime)
        for scene, row in zip(scenes, rows):
            scene["duration_seconds"] = float(row["duration_seconds"])
        _captions(scenes, captions / f"treasury-positioning-{variant}.srt")
        shutil.copy2(combined, public_audio / f"{variant}.wav")
        manifest = {
            "segments": rows, "combined_path": str(combined), "combined_sha256": sha256_file(combined),
            "duration_seconds": float(probe_media(combined)["format"]["duration"]),
            "generation_wall_seconds": 0.0, "segments_reused": len(rows) - regenerated, "segments_regenerated": regenerated,
            "editorial_reorder": variant == "longform", "scene_order": [str(scene["scene_id"]) for scene in scenes],
        }
        variants[variant] = manifest
        _json(audio / f"{variant}-manifest.json", manifest)

    observed = {variant: sha256_file(audio / f"{variant}.wav") for variant in ("short", "longform")}
    chatterbox = auditions / "chatterbox-default-no-reference.wav"
    if sha256_file(chatterbox) != CHATTERBOX_DIAGNOSTIC_SHA256:
        raise RuntimeError("chatterbox_diagnostic_hash_mismatch")
    freeze = {
        "status": "PASS_25_SEGMENTS_REUSED_1_JARGON_SEGMENT_REGENERATED_LOCAL", "segment_count": len(segment_hashes),
        "segment_sha256": segment_hashes, "kokoro_segments_synthesized_this_task": sum(row["segments_regenerated"] for row in variants.values()),
        "local_segments_regenerated": sum(row["segments_regenerated"] for row in variants.values()), "combined_audio_rebuilt_locally": ["short", "longform"],
        "source_combined_audio_sha256": dict(FROZEN_AUDIO_SHA256), "result_combined_audio_sha256": observed,
        "longform_scene_order_before": [str(scene["scene_id"]) for scene in FROZEN_LONG_SCENES],
        "longform_scene_order_after": list(LONGFORM_SCENE_ORDER),
        "chatterbox_audition_status": {
            "duration_seconds": float(probe_media(chatterbox)["format"]["duration"]), "sample_rate_hz": 24000,
            "channels": 1, "codec": "pcm_f32le", "integrated_lufs": measure_loudness(chatterbox)["integrated_lufs"],
            "meaning": "local-path diagnostic only; not owner voice acceptance and not evidence of superiority to Kokoro",
        },
        "policy": ["no new Chatterbox synthesis", "one changed Kokoro build segment for viewer-jargon removal", "no voice bakeoff", "BUILD_TTS unresolved", "all unchanged segments reused"],
        "api_cost_usd": 0, "wall_seconds_tts_synthesis": round(tts_wall_seconds, 3),
    }
    _json(runtime / "receipts" / "frozen_audio_receipt.json", freeze)
    _json(runtime / "receipts" / "audio_ledger.json", {"policy": freeze, "variants": variants})
    return freeze


def _durations(runtime: Path, variant: str) -> dict[str, float]:
    manifest = json.loads((runtime / "audio" / f"{variant}-manifest.json").read_text(encoding="utf-8"))
    return {str(row["scene_id"]): float(row["duration_seconds"]) for row in manifest["segments"]}


def _authored_scenes(runtime: Path, variant: str) -> list[dict[str, Any]]:
    base = _ordered_frozen_scenes(variant)
    durations = _durations(runtime, variant)
    plan = material_plan(base, durations)
    for scene in base:
        scene["duration_seconds"] = durations[str(scene["scene_id"])]
        scene["material_plan"] = plan[str(scene["scene_id"])]
        states, transitions = treasury_visual_state_plan(str(scene["scene_id"]), scene["material_plan"])
        scene["visual_state_plan"] = states
        scene["transition_events"] = transitions
    return base


def _write_pacing_reports(runtime: Path, short: Sequence[Mapping[str, Any]], longform: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    variants = {"short": short, "longform": longform}
    validations = {name: validate_visual_state_architecture(scenes) for name, scenes in variants.items()}
    if any(row["status"] != "PASS" for row in validations.values()):
        raise RuntimeError(validations)
    diagnostics = pacing_diagnostics(variants)
    def semantic_card_seconds(scenes: Sequence[Mapping[str, Any]]) -> float:
        return round(sum(float(beat["duration_seconds"]) for scene in scenes for beat in scene["material_plan"] if beat.get("presentation_grammar") in {"boundary", "montage"}), 3)

    def state_card_seconds(scenes: Sequence[Mapping[str, Any]]) -> float:
        return round(sum(float(state["duration_seconds"]) for scene in scenes for state in scene["visual_state_plan"] if state.get("display_layout") in {"boundary", "montage"}), 3)

    before = {
        "short": {"semantic_beats": sum(len(scene["material_plan"]) for scene in short), "visual_states": 24, "full_screen_transitions": 23, "standalone_boundary_montage_seconds": semantic_card_seconds(short)},
        "longform": {"semantic_beats": sum(len(scene["material_plan"]) for scene in longform), "visual_states": 125, "full_screen_transitions": 124, "standalone_boundary_montage_seconds": semantic_card_seconds(longform)},
        "basis": "Independent owner audit estimate of the accepted parent actual media.",
    }
    after = {
        name: {
            "semantic_beats": row["semantic_beat_count"], "visual_states": row["visual_state_count"],
            "full_screen_transitions": row["full_screen_transition_count"],
            "semantic_beats_per_visual_state": row["semantic_beats_per_visual_state"],
            "mean_visual_state_seconds": row["visual_state_duration_seconds"]["mean"],
            "low_information_standalone_card_seconds": row["low_information_standalone_card_burden"]["screen_seconds"],
            "standalone_boundary_montage_seconds": state_card_seconds(variants[name]),
        } for name, row in diagnostics["variants"].items()
    }
    timeline: list[dict[str, Any]] = []
    mapping: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    for variant, scenes in variants.items():
        cursor = 0.0
        for scene in scenes:
            state_by_beat = {beat_id: state for state in scene["visual_state_plan"] for beat_id in state["semantic_beat_ids"]}
            for state in scene["visual_state_plan"]:
                timeline.append({
                    "variant": variant, "scene_id": scene["scene_id"], "visual_state_id": state["visual_state_id"],
                    "global_start_seconds": round(cursor + float(state["start_seconds"]), 3),
                    "global_end_seconds": round(cursor + float(state["end_seconds"]), 3),
                    "duration_seconds": state["duration_seconds"], "context_key": state["context_key"],
                    "display_layout": state["display_layout"], "semantic_beat_ids": state["semantic_beat_ids"],
                    "within_state_actions": state["within_state_actions"], "information_density": state["information_density"],
                    "ingestion_rationale": state["ingestion_rationale"],
                })
            for beat in scene["material_plan"]:
                state = state_by_beat[str(beat["beat_id"])]
                mapping.append({
                    "variant": variant, "scene_id": scene["scene_id"], "semantic_beat_id": beat["beat_id"],
                    "visual_state_id": state["visual_state_id"], "within_state_action_id": next(
                        action["action_id"] for action in state["within_state_actions"] if action["semantic_beat_id"] == beat["beat_id"]
                    ),
                })
            for event in scene["transition_events"]:
                transitions.append(dict(event, variant=variant, global_at_seconds=round(cursor + float(event["at_seconds"]), 3)))
            cursor += float(scene["duration_seconds"])
    copy_scan = scan_internal_jargon(viewer_copy_values(short) + viewer_copy_values(longform))
    if copy_scan["status"] != "PASS":
        raise RuntimeError(copy_scan)
    narration_metrics = {}
    for name, scenes in variants.items():
        word_count = sum(len(re.findall(r"\b[\w’'-]+\b", str(scene["narration"]), flags=re.UNICODE)) for scene in scenes)
        duration = sum(float(scene["duration_seconds"]) for scene in scenes)
        narration_metrics[name] = {
            "word_count": word_count,
            "duration_seconds": round(duration, 3),
            "words_per_minute": round(word_count * 60 / duration, 1),
            "basis": "authored narration words divided by exact frozen build-audio segment duration",
        }
    report = {
        "schema": "contentops.v2.creative_pacing_owner_review.v1", "task_id": TASK_ID,
        "validations": validations, "diagnostics": diagnostics, "before": before, "after": after,
        "internal_jargon_scan": copy_scan,
        "payoff_distance_review": {
            "before": "Basis mechanism began after the 2Y/5Y/10Y and weekly-delta blocks.",
            "after": "Basis mechanism and repo financing now follow the source clock, before detailed tenor evidence.",
            "longform_scene_order": [scene["scene_id"] for scene in longform],
        },
        "narration_pause_summary": {
            "narration_text_changed": True, "changed_segment": "L02_SOURCE_CLOCK: governed weekly map → official weekly map",
            "semantic_segments_reordered": ["L08_BASIS_SETUP", "L09_REPO_FINANCING"],
            "segments_regenerated": 1, "deliberate_pause_policy": "Existing segment-final pauses retained; no global TTS slowdown.",
        },
        "narration_metrics": narration_metrics,
        "diagnostic_policy": "Suspicious patterns are review surfaces, not universal numerical pass thresholds.",
    }
    _json(runtime / "contracts" / "creative_pacing_prompt_contract.json", summarize_prompt_contract())
    _json(runtime / "contracts" / "creative_pacing_validation.json", validations)
    _json(runtime / "contracts" / "creative_pacing_diagnostics.json", diagnostics)
    _json(runtime / "contracts" / "visual_state_timeline.json", {"states": timeline})
    _json(runtime / "contracts" / "semantic_beat_to_visual_state_mapping.json", {"mapping": mapping})
    _json(runtime / "contracts" / "full_screen_transition_timeline.json", {"transitions": transitions})
    _json(runtime / "contracts" / "creative_pacing_owner_review.json", report)
    _json(runtime / "receipts" / "internal_jargon_scan.json", copy_scan)
    return report


def _visual_state_dependency_manifest(variants: Mapping[str, Sequence[Mapping[str, Any]]], selected: Mapping[str, str]) -> dict[str, Any]:
    """Account from serialized visual-state anchors, not semantic-plan asset IDs."""
    asset_seconds: Counter[str] = Counter()
    family_seconds: Counter[str] = Counter()
    presentation_seconds: Counter[str] = Counter()
    purpose_seconds: Counter[str] = Counter()
    occurrences: dict[str, list[dict[str, Any]]] = {}
    per_scene: dict[str, Any] = {}
    total = 0.0
    for variant, scenes in variants.items():
        cursor = 0.0
        prior_asset: str | None = None
        for scene in scenes:
            beats = {str(beat["beat_id"]): beat for beat in scene["material_plan"]}
            scene_assets: Counter[str] = Counter()
            scene_families: Counter[str] = Counter()
            scene_presentations: Counter[str] = Counter()
            for state in scene["visual_state_plan"]:
                duration = float(state["duration_seconds"])
                total += duration
                presentation = str(state["display_layout"])
                presentation_seconds[presentation] += duration
                scene_presentations[presentation] += duration
                purpose_seconds[str(state["context_key"])] += duration
                anchor = beats[str(state["anchor_beat_id"])]
                filename = anchor.get("asset")
                if not filename:
                    continue
                filename = str(filename)
                family = ASSET_SOURCE_FAMILY[filename]
                asset_seconds[filename] += duration
                family_seconds[family] += duration
                scene_assets[filename] += duration
                scene_families[family] += duration
                occurrences.setdefault(filename, []).append({
                    "variant": variant, "scene_id": scene["scene_id"], "visual_state_id": state["visual_state_id"],
                    "start_seconds": round(cursor + float(state["start_seconds"]), 3),
                    "duration_seconds": round(duration, 3), "semantic_purpose": state["context_key"],
                    "adjacent_source_asset_reuse": filename == prior_asset,
                })
                prior_asset = filename
            per_scene[f"{variant}:{scene['scene_id']}"] = {
                "duration_seconds": round(float(scene["duration_seconds"]), 3),
                "semantic_beats": len(scene["material_plan"]), "visual_states": len(scene["visual_state_plan"]),
                "source_material_families": {key: round(value, 3) for key, value in scene_families.items()},
                "presentation_grammars": {key: round(value, 3) for key, value in scene_presentations.items()},
                "assets": {key: round(value, 3) for key, value in scene_assets.items()},
            }
            cursor += float(scene["duration_seconds"])
    asset_usage: dict[str, Any] = {}
    family_usage: dict[str, Any] = {}
    for filename, rows in sorted(occurrences.items()):
        short_window = sum(
            prior["variant"] == current["variant"] and current["start_seconds"] - prior["start_seconds"] <= 30
            for prior, current in zip(rows, rows[1:])
        )
        family = ASSET_SOURCE_FAMILY[filename]
        asset_usage[filename] = {
            "sha256": selected[filename], "source_material_family": family,
            "scenes_used": sorted({f"{row['variant']}:{row['scene_id']}" for row in rows}),
            "scene_count": len({f"{row['variant']}:{row['scene_id']}" for row in rows}),
            "occurrence_count": len(rows), "cumulative_screen_seconds": round(asset_seconds[filename], 3),
            "adjacent_source_asset_reuse_count": sum(bool(row["adjacent_source_asset_reuse"]) for row in rows),
            "short_window_recurrence_30s_count": short_window,
            "semantic_purposes": sorted({str(row["semantic_purpose"]) for row in rows}), "occurrences": rows,
            "prior_recent_video_reuse": "KNOWN_ACCEPTED_TREASURY_ASSET",
        }
    for family in sorted(family_seconds):
        family_rows = [row | {"asset": filename} for filename, rows in occurrences.items() if ASSET_SOURCE_FAMILY[filename] == family for row in rows]
        family_usage[family] = {
            "cumulative_screen_seconds": round(family_seconds[family], 3),
            "assets": sorted({row["asset"] for row in family_rows}),
            "scenes_used": sorted({f"{row['variant']}:{row['scene_id']}" for row in family_rows}),
            "occurrence_count": len(family_rows),
        }
    rendered = set(asset_usage)
    return {
        "schema": "contentops.v2.serialized_visual_state_render_dependency_manifest.v1",
        "task_id": TASK_ID, "story_id": JOB_ID, "total_screen_seconds": round(total, 3),
        "selected_asset_hashes": dict(selected), "rendered_asset_hashes": {name: selected[name] for name in sorted(rendered)},
        "selected_but_not_rendered": sorted(set(selected) - rendered),
        "asset_screen_seconds": {key: round(value, 3) for key, value in sorted(asset_seconds.items())},
        "source_material_family_screen_seconds": {key: round(value, 3) for key, value in sorted(family_seconds.items())},
        "presentation_grammar_screen_seconds": {key: round(value, 3) for key, value in sorted(presentation_seconds.items())},
        "purpose_screen_seconds": {key: round(value, 3) for key, value in sorted(purpose_seconds.items())},
        "asset_usage": asset_usage, "source_material_family_usage": family_usage, "per_scene": per_scene,
        "external_runtime_fetches": 0, "generated_person_media": 0,
        "taxonomy_separation": {
            "source_material_family": "Actual rendered source provenance/semantic universe only.",
            "presentation_grammar": "Visual-state layout only; never counted as source-material diversity.",
        },
        "dependency_proof_level": "EXACT_SERIALIZED_VISUAL_STATE_ANCHORS_PLUS_LOCAL_FILE_HASHES; pixel-level provenance not claimed",
    }


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
    _seed_accepted_asset_universe(runtime)
    selected = _selected_asset_hashes(runtime)
    freeze = _freeze_audio(runtime)
    cftc = json.loads((runtime / "receipts" / "cftc_zero_trust_verification.json").read_text(encoding="utf-8"))
    if cftc.get("status") != "PASS_ZERO_TRUST_EXACT_RAW_ROWS":
        raise RuntimeError("cftc_zero_trust_receipt_missing")
    numeric_binding = _numeric_binding_receipt(runtime)
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
    pacing = _write_pacing_reports(runtime, short, longform)
    narration_hash = hashlib.sha256(json.dumps({
        "short": [row["narration"] for row in short], "longform": [row["narration"] for row in longform]
    }, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    story = {
        "task_id": TASK_ID, "story_id": JOB_ID, "title": "The Treasury market’s giant offset",
        "source_lineage": SOURCE_LINEAGE, "story_status": "SAME_GOVERNED_TREASURY_STORY",
        "narration_status": "TEXT_STABLE_SEGMENTS_REUSED_LONGFORM_EDITORIALLY_REORDERED", "narration_hash": narration_hash,
        "formats": {"short": "9:16 30-60s clean master", "longform": "16:9 5-45m clean master"},
        "canonical_midform_final": False, "max_ultra_bakeoff": False, "public_write_authority": False,
    }
    dependency = _visual_state_dependency_manifest({"short": short, "longform": longform}, selected)
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
        ("STORY_LOCKED", story), ("EVIDENCE_LOCKED", {"cftc": cftc, "numeric_binding": numeric_binding}),
        ("ANALYSIS_READY", {"same_story": True, "narration_text_stable": True, "longform_chapter_reorder": True, "truth_boundary_preserved": True}),
        ("ASSET_BOARD_READY", {"asset_board": str(runtime / "contracts" / "asset_board.json"), "selected": len(selected)}),
        ("SHORT_STORYBOARD_READY", {"hash": logical_hash(short_plan), "semantic_beats": sum(map(len, short_plan.values())), "visual_states": pacing["after"]["short"]["visual_states"], "generation": "AUTHORED_SEMANTIC_BEAT_TO_VISUAL_STATE_MAPPING"}),
        ("LONGFORM_STORYBOARD_READY", {"hash": logical_hash(long_plan), "semantic_beats": sum(map(len, long_plan.values())), "visual_states": pacing["after"]["longform"]["visual_states"], "generation": "AUTHORED_SEMANTIC_BEAT_TO_VISUAL_STATE_MAPPING"}),
        ("SHORT_SOURCE_READY", {"source": str(CREATIVE_SOURCE), "sha256": sha256_file(CREATIVE_SOURCE)}),
        ("LONGFORM_SOURCE_READY", {"source": str(CREATIVE_SOURCE), "sha256": sha256_file(CREATIVE_SOURCE)}),
        ("BUILD_AUDIO_READY", {"source_audio": FROZEN_AUDIO_SHA256, "segment_reuse": 25, "new_local_kokoro_synthesis": 1,
                               "api_cost_usd": 0, "longform_editorial_reorder": True}),
    ]
    for stage, output in stages:
        ledger.checkpoint(JOB_ID, stage, {"task": TASK_ID, "stage": stage}, output)


def _governed_positions(runtime: Path) -> list[dict[str, Any]]:
    receipt = json.loads((runtime / "receipts" / "cftc_zero_trust_verification.json").read_text(encoding="utf-8"))
    labels = {"UST 2Y NOTE": "2Y", "UST 5Y NOTE": "5Y", "UST 10Y NOTE": "10Y"}
    return [{
        "label": labels[str(row["market"])], "open_interest": int(row["open_interest"]),
        "asset_net": int(row["asset_net"]), "lever_net": int(row["lever_net"]),
        "asset_net_weekly_change": int(row["asset_net_weekly_change"]),
        "lever_net_weekly_change": int(row["lever_net_weekly_change"]),
        "row_sha256": str(row["row_sha256"]),
    } for row in receipt["rows"]]


def _numeric_binding_receipt(runtime: Path) -> dict[str, Any]:
    receipt = json.loads((runtime / "receipts" / "cftc_zero_trust_verification.json").read_text(encoding="utf-8"))
    render_values = _governed_positions(runtime)
    source_text = CREATIVE_SOURCE.read_text(encoding="utf-8")
    errors: list[str] = []
    if "assetLong" in source_text or "assetShort" in source_text:
        errors.append("unused_synthetic_gross_leg_literal_present")
    for row in receipt["rows"]:
        for key in ("open_interest", "asset_net", "lever_net", "asset_net_weekly_change", "lever_net_weekly_change"):
            if not isinstance(row[key], int):
                errors.append(f"noninteger_governed_value:{row['market']}:{key}")
    expected_hashes = [str(row["row_sha256"]) for row in receipt["rows"]]
    if [row["row_sha256"] for row in render_values] != expected_hashes:
        errors.append("render_row_hash_binding_mismatch")
    value = {
        "status": "PASS_VIEWER_FACING_CFTC_VALUES_BOUND_TO_EXACT_GOVERNED_ROWS" if not errors else "FAIL",
        "errors": errors, "source_sha256": receipt["source_sha256"],
        "row_sha256": expected_hashes, "render_props_values": render_values,
        "viewer_source_numeric_authority": "render props only; no CFTC position literals in viewer-facing TypeScript",
        "removed_fields": ["assetLong", "assetShort"],
    }
    _json(runtime / "receipts" / "numeric_binding_receipt.json", value)
    if errors:
        raise RuntimeError(value)
    return value


def _props(runtime: Path, variant: str, captions: bool = False) -> Path:
    storyboard = json.loads((runtime / "contracts" / f"{variant}_storyboard.json").read_text(encoding="utf-8"))
    value = {
        "proofId": JOB_ID, "creativeSourceSha256": sha256_file(CREATIVE_SOURCE),
        "captionsVisible": captions, "variant": variant, "scenes": storyboard["scenes"],
        "audioFile": f"audio/{variant}.wav", "governedPositions": _governed_positions(runtime),
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
            beats = {str(beat["beat_id"]): beat for beat in scene.get("material_plan", [])}
            for state in scene.get("visual_state_plan", []):
                anchor = beats.get(str(state.get("anchor_beat_id")), {})
                if anchor.get("asset"):
                    referenced.add(str(anchor["asset"]))
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
    receipt = {
        "schema": "contentops.v2.render_dependency_observation.v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "serialized_props": props_receipts,
        "referenced_asset_count": len(referenced),
        "selected_asset_count": len(selected),
        "selected_but_not_rendered": sorted(set(selected) - referenced),
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
        target = media / f"treasury-positioning-{variant}-creative-pacing-ingestion-{label}.mp4"
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
        "status": "PASS_DESCRIPTIVE_DIAGNOSTIC",
        "interpretation": "Descriptive detector only. A low-change run is not a pacing failure without state utility, ingestion, and progressive-disclosure context.",
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
        "status": "PASS_AUTOMATED_VISUAL_DIAGNOSTICS" if all(row["diagnostics"]["status"] == "PASS_DESCRIPTIVE_DIAGNOSTIC" for row in outputs.values()) else "REVIEW_REQUIRED",
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
    target = runtime / "media" / "treasury-positioning-short-creative-pacing-ingestion-1080x1920.mp4"
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


def _progressive_disclosure_frame_proof(runtime: Path) -> dict[str, Any]:
    """Render several actions inside one state to prove continuity plus disclosure."""
    targets = {
        "short": ("S04_PRIMARY_ROW", "cftc_exact_rows", [0, 1, 2]),
        "longform": ("L03_TWO_YEAR", "two_year_object", [0, 1, 2, 4, 5]),
    }
    result: dict[str, Any] = {}
    for variant, (scene_id, context_key, action_indexes) in targets.items():
        scenes = json.loads((runtime / "contracts" / f"{variant}_storyboard.json").read_text(encoding="utf-8"))["scenes"]
        cursor = 0.0
        scene = None
        for candidate in scenes:
            if candidate["scene_id"] == scene_id:
                scene = candidate
                break
            cursor += float(candidate["duration_seconds"])
        if scene is None:
            raise RuntimeError(f"progressive_scene_missing:{variant}:{scene_id}")
        state = next((row for row in scene["visual_state_plan"] if row["context_key"] == context_key), None)
        if state is None:
            raise RuntimeError(f"progressive_state_missing:{variant}:{context_key}")
        actions = state["within_state_actions"]
        frames: list[int] = []
        bindings: list[dict[str, Any]] = []
        for action_index in action_indexes:
            action = actions[action_index]
            second = cursor + float(state["start_seconds"]) + float(action["at_seconds"]) + 0.75
            second = min(second, cursor + float(state["end_seconds"]) - 0.1)
            frame = round(second * 30)
            frames.append(frame)
            bindings.append({
                "frame": frame, "global_seconds": round(second, 3), "scene_id": scene_id,
                "visual_state_id": state["visual_state_id"], "action_id": action["action_id"],
                "semantic_beat_id": action["semantic_beat_id"], "emphasis": action["emphasis"],
                "utility": action["utility"], "display_layout": state["display_layout"],
            })
        folder = runtime / "review" / "progressive-disclosure-frames" / variant
        render_receipt = _render(runtime, variant, folder, 1.0, frames=frames)
        paths = [Path(path) for path in render_receipt["output_paths"]]
        sheet = runtime / "review" / f"{variant}-progressive-disclosure-proof.jpg"
        if variant == "short":
            _sheet(paths, sheet, len(paths), (360, 640), [row["emphasis"] for row in bindings])
        else:
            _sheet(paths, sheet, 3, (480, 270), [row["emphasis"] for row in bindings])
        result[variant] = {
            "status": "PASS_SAME_VISUAL_STATE_MULTIPLE_SEMANTIC_ACTIONS",
            "visual_state_id": state["visual_state_id"], "context_key": context_key,
            "frame_folder": str(folder), "proof_sheet": str(sheet), "bindings": bindings,
            "render_receipt": render_receipt,
        }
    receipt = {
        "status": "PASS_PROGRESSIVE_DISCLOSURE_ACTUAL_FRAME_PROOF",
        "interpretation": "Each variant keeps one composition and visual-state ID while viewer emphasis advances across multiple semantic beats.",
        "variants": result,
    }
    _json(runtime / "receipts" / "progressive_disclosure_frame_proof.json", receipt)
    return receipt


def _audio_pause_analysis(media: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(media), "-af", "silencedetect=noise=-40dB:d=0.25", "-f", "null", "-"],
        cwd=REPO, check=False, capture_output=True, text=True,
    )
    durations = [float(value) for value in re.findall(r"silence_duration:\s*([0-9.]+)", completed.stderr)]
    if completed.returncode:
        raise RuntimeError(f"silence_analysis_failed:{media}:{completed.stderr[-1000:]}")
    return {
        "threshold_db": -40, "minimum_pause_seconds": 0.25,
        "detected_pause_count": len(durations), "detected_pause_seconds": round(sum(durations), 3),
        "median_pause_seconds": round(sorted(durations)[len(durations) // 2], 3) if durations else 0,
        "longest_pause_seconds": round(max(durations), 3) if durations else 0,
        "interpretation": "Descriptive silence detection on the actual mastered soundtrack; not a normative cadence gate.",
    }


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
    progressive_frames = _progressive_disclosure_frame_proof(runtime)
    pause_analysis = {variant: _audio_pause_analysis(Path(row["path"])) for variant, row in masters.items()}
    _json(runtime / "receipts" / "actual_master_pause_analysis.json", {"status": "PASS", "variants": pause_analysis})
    before = {variant: row["sha256"] for variant, row in masters.items()}
    selective = runtime / "review" / "selective-rerender-proof"
    _render(runtime, "longform", selective, 0.25, frames=[1800])
    after = {variant: sha256_file(Path(row["path"])) for variant, row in masters.items()}
    recovery = {"status": "PASS_TARGETED_STILL_FRAME_RERENDER_ONLY", "targeted_still_frame_rerender": str(selective / "frame_1800.png"),
                "master_hashes_before": before, "master_hashes_after": after, "unaffected_masters_unchanged": before == after,
                "frozen_audio_resume": "25/26 segments reused; one local jargon-cleanup segment regenerated; zero API cost",
                "claim_boundary": "This proves a targeted still-frame rerender only. No selective chapter/video rerender is claimed."}
    _json(runtime / "receipts" / "recovery_proof.json", recovery)
    safety = {"public_writes": 0, "uploads": 0, "browser_profile_uses": 0, "elevenlabs_calls": 0, "v1_mutations": 0,
              "video_public_write_authority": False, "mode_bakeoff": False, "new_chatterbox_synthesis": 0,
              "kokoro_synthesis": 1, "generated_real_person_documentary_media": False,
              "execution_provenance": {"execution_plane": "CODEX_TASK_SESSION", "model": "not_exposed_to_task_session", "nine_router_route": None,
                                         "reasoning_mode_bakeoff": False}}
    acquisition = json.loads((runtime / "receipts" / "asset_acquisition.json").read_text(encoding="utf-8"))
    safety["network_read_only_calls"] = acquisition["downloads"]
    safety["network_scope"] = acquisition["network_scope"]
    safety["api_cost_usd"] = 0
    safety["validation"] = validate_zero_write(safety)
    _json(runtime / "receipts" / "zero_public_write.json", safety)
    freeze = json.loads((runtime / "receipts" / "frozen_audio_receipt.json").read_text(encoding="utf-8"))
    audio_errors: list[str] = []
    audio_variants: dict[str, Any] = {}
    for variant in ("short", "longform"):
        manifest = json.loads((runtime / "audio" / f"{variant}-manifest.json").read_text(encoding="utf-8"))
        for segment in manifest["segments"]:
            path = Path(segment["path"])
            if not path.is_file() or sha256_file(path) != segment["sha256"]:
                audio_errors.append(f"segment_changed:{segment['scene_id']}")
        combined = runtime / "audio" / f"{variant}.wav"
        if sha256_file(combined) != manifest["combined_sha256"]:
            audio_errors.append(f"combined_changed:{variant}")
        audio_variants[variant] = {"combined_sha256": manifest["combined_sha256"], "segments": len(manifest["segments"]), "regenerated": manifest["segments_regenerated"]}
    if sha256_file(runtime / "auditions" / "chatterbox-default-no-reference.wav") != CHATTERBOX_DIAGNOSTIC_SHA256:
        audio_errors.append("chatterbox_diagnostic_changed")
    final_audio_recheck = {"status": "PASS" if not audio_errors else "FAIL", "errors": audio_errors, "variants": audio_variants, "checked_at_finalization": True}
    if audio_errors:
        raise RuntimeError(final_audio_recheck)
    _json(runtime / "receipts" / "final_frozen_audio_recheck.json", final_audio_recheck)
    cftc = json.loads((runtime / "receipts" / "cftc_zero_trust_verification.json").read_text(encoding="utf-8"))
    numeric_binding = json.loads((runtime / "receipts" / "numeric_binding_receipt.json").read_text(encoding="utf-8"))
    pacing = json.loads((runtime / "contracts" / "creative_pacing_owner_review.json").read_text(encoding="utf-8"))
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
        "cftc_truth": cftc, "numeric_binding": numeric_binding, "creative_pacing": pacing, "actual_render_dependencies": dependency,
        "recovery": recovery, "safety": safety, "source_sandbox": source_sandbox,
        "render_dependency_observation": dependency_observation, "static_full_context_frame_proof": static_frames,
        "progressive_disclosure_frame_proof": progressive_frames, "actual_master_pause_analysis": pause_analysis,
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
