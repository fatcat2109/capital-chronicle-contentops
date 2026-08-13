"""Post-comprehension motion authorship, render, audio, and media QA for V2-01."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.media_manifest_authority_v1 import sha256_file
from live_contentops.nine_router_llm_seam_v2 import ROLE_V2_MOTION_CODE_AUTHOR
from live_contentops.retention_native_audio_score_v2 import render_owned_score
from live_contentops.retention_native_concrete_first_v2 import canonical_json, logical_hash
from live_contentops.retention_native_creative_brain_v2 import (
    NineRouterGPT56Brain,
    validate_motion_output,
)
from live_contentops.retention_native_motion_sandbox_v2 import (
    persist_authored_files,
    validate_generated_motion_files,
)
from live_contentops.retention_native_replacement_runner_v2 import DEFAULT_RUNTIME, VIDEO_ID

SCHEMA_VERSION = "contentops.retention_native.motion_pipeline.v2"
RENDERER_RELATIVE = Path("video") / "concrete_first_v2"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8")


def _run(command: Sequence[str], *, cwd: Path | None = None, timeout: float = 3600) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command), cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )
    if result.returncode:
        raise RuntimeError(
            f"command_failed:{Path(command[0]).name}:{result.stderr[-2000:]}:{result.stdout[-1000:]}"
        )
    return result


def _safe(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")
    if not cleaned:
        raise ValueError("generated_identifier_empty")
    return cleaned


MOTION_INSTRUCTION = """You are the exact XHIGH Motion Code Author. The storyboard and visual-grounding decisions are already accepted; implement them faithfully as deterministic React/Remotion code. Author only the supplied segment/variant, small enough for one bounded response. Return ONLY JSON: {batch_id,beat_ids,files:[{path,source}]}. Produce exactly one TSX file at the required_path and export the required_component_name React.FC<VariantProps>. Import VariantProps from '../types'. Use only React and approved Remotion APIs (AbsoluteFill, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig). No network, env, filesystem, shell, dynamic dependencies, randomness, CSS transitions, or publication actions. Every exact beat_id must appear literally in source. Use the exact asset relative_public_path bindings; required real assets may not be replaced with geometry. Use frame-driven cuts, reframes, document punch-ins, map progression, native data comparisons, annotations, and purposeful holds exactly as storyboard intent warrants. Captions render only when captionsVisible is true; source labels and editorial labels remain. Keep source labels readable, prevent overflow, preserve safe zones. Avoid generic cards, unexplained symbols, universal zoom/parallax, repeated easing/direction, chart crawl, and unrelated simultaneous motion. The component starts at its own local frame zero and lasts exact duration_frames."""


def author_motion(*, runtime: Path, repo_root: Path) -> dict[str, Any]:
    premotion = _read_json(runtime / "premotion_comprehension_report_v2.json")
    if premotion["deterministic_gate"]["motion_code_authorized"] is not True:
        raise RuntimeError("motion_author_called_before_comprehension_pass")
    director = _read_json(runtime / "contracts" / "creative_director_v2.json")
    segments = _read_json(runtime / "contracts" / "segment_authorship_v2.json")
    storyboard = _read_json(runtime / "storyboard_animatic_manifest_v2.json")
    assets = _read_json(runtime / "contracts" / "asset_candidate_universe_v2.json")
    renderer_root = (repo_root / RENDERER_RELATIVE).resolve()
    asset_bindings = {
        row["asset_id"]: {
            "relative_public_path": row["relative_public_path"],
            "rights_status": row["rights_status"],
            "attribution": row["attribution"],
            "recognizable_focal_object": row["recognizable_focal_object"],
        }
        for row in assets["candidates"]
    }
    authored: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for variant in ("short_9x16", "midform_16x9"):
        variant_beats = segments[f"{variant}_beats"]
        frame_rows = {
            row["beat_id"]: row for row in storyboard["variants"][variant]["frames"]
        }
        for segment in segments["segments"]:
            key = f"{variant}_beats"
            beats = list(segment[key])
            segment_id = str(segment["segment_id"])
            safe_variant = _safe(variant)
            safe_segment = _safe(segment_id)
            component_name = f"Motion_{safe_variant}_{safe_segment}"
            required_path = f"src/generated/{safe_variant}_{safe_segment}.tsx"
            duration_frames = int(round(sum(float(beat["duration_seconds"]) for beat in beats) * 30))
            selected_asset_ids = {str(asset_id) for beat in beats for asset_id in beat["asset_ids"]}
            prompt = {
                "instruction": MOTION_INSTRUCTION,
                "video_id": VIDEO_ID,
                "variant_id": variant,
                "dimensions": {"width": 1080 if variant == "short_9x16" else 1920, "height": 1920 if variant == "short_9x16" else 1080, "fps": 30},
                "required_path": required_path,
                "required_component_name": component_name,
                "duration_frames": duration_frames,
                "immutable_creative_bible": director["creative_bible"],
                "segment_contract": next(row for row in director["segment_graph"] if row["segment_id"] == segment_id),
                "accepted_segment_artifact": segment,
                "accepted_beats": beats,
                "accepted_storyboard_frames": [frame_rows[beat["beat_id"]] for beat in beats],
                "resolved_assets": {asset_id: asset_bindings[asset_id] for asset_id in selected_asset_ids},
                "neighboring_context": {
                    "previous_beat_id": variant_beats[max(0, variant_beats.index(beats[0]) - 1)]["beat_id"] if variant_beats.index(beats[0]) > 0 else None,
                    "next_beat_id": variant_beats[variant_beats.index(beats[-1]) + 1]["beat_id"] if variant_beats.index(beats[-1]) + 1 < len(variant_beats) else None,
                },
                "technical_baseline": {
                    "remotion": "4.0.507",
                    "frame_driven": True,
                    "caption_safe_zone_bottom": 0.16 if variant == "short_9x16" else 0.11,
                    "render_time_network": False,
                },
                "public_write_authority": False,
            }
            image_paths = tuple(frame_rows[beat["beat_id"]]["path"] for beat in beats)
            output, receipt = NineRouterGPT56Brain().author(
                role=ROLE_V2_MOTION_CODE_AUTHOR,
                prompt_payload=prompt,
                validator=validate_motion_output,
                logical_invocation_id=f"inv_v2_motion_{safe_variant}_{safe_segment}_{logical_hash(prompt)[:14]}",
                prompt_template="concrete_first_xhigh_motion_segment",
                prompt_version="v2_minimal_raw_no_generation_config",
                image_paths=image_paths,
                wire_mode="minimal_raw",
                evidence_dir=(
                    runtime / "provider_evidence" / "motion" / safe_variant / safe_segment
                ),
            )
            if str(output.get("batch_id") or "") != f"{variant}:{segment_id}":
                raise RuntimeError(f"motion_batch_identity_mismatch:{variant}:{segment_id}")
            if output.get("beat_ids") != [beat["beat_id"] for beat in beats]:
                raise RuntimeError(f"motion_beat_identity_mismatch:{variant}:{segment_id}")
            files = list(output["files"])
            if len(files) != 1 or files[0].get("path") != required_path:
                raise RuntimeError(f"motion_file_contract_mismatch:{variant}:{segment_id}")
            sandbox = validate_generated_motion_files(
                files, expected_beat_ids=[beat["beat_id"] for beat in beats]
            )
            if sandbox["status"] != "PASS":
                raise RuntimeError(f"motion_sandbox_block:{variant}:{segment_id}:{sandbox['violations']}")
            provenance = persist_authored_files(files, renderer_root=renderer_root)
            receipt_row = receipt.to_dict()
            if receipt_row["degraded_creative_model"]:
                raise RuntimeError("professional_motion_candidate_degraded_creative_model")
            row = {
                "variant_id": variant,
                "segment_id": segment_id,
                "component_name": component_name,
                "required_path": required_path,
                "duration_frames": duration_frames,
                "composition_id": f"Seg{safe_variant}{safe_segment}",
                "beat_ids": output["beat_ids"],
                "sandbox": sandbox,
                "provenance": provenance,
                "model_output_sha256": logical_hash(output),
                "receipt_sha256": logical_hash(receipt_row),
            }
            authored.append(row)
            receipts.append(receipt_row)
            _write_json(runtime / "receipts" / "motion" / f"{safe_variant}_{safe_segment}.json", receipt_row)
    index = _mechanical_index(authored)
    index_path = renderer_root / "src" / "generated" / "index.tsx"
    before_placeholder = index_path.read_text(encoding="utf-8")
    index_path.write_text(index, encoding="utf-8", newline="\n")
    index_provenance = {
        "path": str(index_path),
        "before_sha256": logical_hash(before_placeholder),
        "after_sha256": logical_hash(index),
        "kind": "MECHANICAL_IMPORT_SEQUENCE_ASSEMBLY",
        "creative_inputs": [row["model_output_sha256"] for row in authored],
        "viewer_visible_creative_decisions_added_by_codex": False,
    }
    typecheck = _run(["npm", "run", "typecheck"], cwd=renderer_root, timeout=600)
    manifest = {
        "schema_version": "contentops.retention_native.motion_authorship.v2",
        "video_id": VIDEO_ID,
        "authored_batches": authored,
        "receipts": receipts,
        "index_provenance": index_provenance,
        "typecheck": {"status": "PASS", "stdout": typecheck.stdout[-2000:]},
        "degraded_creative_model": False,
        "provenance_broken": False,
        "public_write": False,
    }
    _write_json(runtime / "motion_authorship_manifest_v2.json", manifest)
    return manifest


def _mechanical_index(rows: Sequence[Mapping[str, Any]]) -> str:
    imports = ["import React from 'react';", "import {AbsoluteFill, Sequence} from 'remotion';", "import type {VariantProps} from '../types';"]
    for row in rows:
        module = "./" + Path(str(row["required_path"])).stem
        imports.append(f"import {{{row['component_name']}}} from '{module}';")
    body: list[str] = [*imports, ""]
    totals: dict[str, int] = {}
    for variant, export_name in (("short_9x16", "ShortVideo"), ("midform_16x9", "MidformVideo")):
        selected = [row for row in rows if row["variant_id"] == variant]
        offset = 0
        body.append(f"export const {export_name}: React.FC<VariantProps> = (props) => (")
        body.append("  <AbsoluteFill style={{backgroundColor: '#081018'}}>")
        for row in selected:
            duration = int(row["duration_frames"])
            body.append(f"    <Sequence from={{{offset}}} durationInFrames={{{duration}}} name=\"{row['segment_id']}\">")
            body.append(f"      <{row['component_name']} {{...props}} />")
            body.append("    </Sequence>")
            offset += duration
        body.extend(("  </AbsoluteFill>", ");", ""))
        totals[variant] = offset
    body.append(f"export const shortDurationFrames = {totals['short_9x16']};")
    body.append(f"export const midformDurationFrames = {totals['midform_16x9']};")
    body.append("export const authoredSegments: Array<{id: string; component: React.FC<VariantProps>; durationInFrames: number; width: number; height: number}> = [")
    for row in rows:
        width = 1080 if row["variant_id"] == "short_9x16" else 1920
        height = 1920 if row["variant_id"] == "short_9x16" else 1080
        body.append(
            f"  {{id: '{row['composition_id']}', component: {row['component_name']}, "
            f"durationInFrames: {int(row['duration_frames'])}, width: {width}, height: {height}}},"
        )
    body.append("];")
    return "\n".join(body) + "\n"


def render_motion(*, runtime: Path, repo_root: Path, node: str = "node") -> dict[str, Any]:
    motion = _read_json(runtime / "motion_authorship_manifest_v2.json")
    if motion.get("provenance_broken") or motion.get("degraded_creative_model"):
        raise RuntimeError("motion_manifest_not_renderable")
    renderer = (repo_root / RENDERER_RELATIVE).resolve()
    public_dir = runtime / "render_public"
    render_script = renderer / "scripts" / "render.mjs"
    results: dict[str, Any] = {}
    segment_cache: dict[str, Any] = {}
    # Render one proxy per authored segment first. These are the selective-rerender cache
    # units and the direct input to temporal motion strips/localized revision evidence.
    for row in motion["authored_batches"]:
        key = logical_hash(
            {
                "composition_id": row["composition_id"],
                "model_output_sha256": row["model_output_sha256"],
                "duration_frames": row["duration_frames"],
                "captions_visible": False,
                "scale": 0.5,
            }
        )
        output = runtime / "render_cache" / "segments" / row["variant_id"] / f"{row['segment_id']}-{key[:18]}.mp4"
        receipt = output.with_suffix(".receipt.json")
        props = output.with_suffix(".props.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        _write_json(props, {"captionsVisible": False, "assetBase": "assets"})
        cache_hit = output.is_file() and receipt.is_file()
        if not cache_hit:
            _run(
                [node, str(render_script), "--composition", row["composition_id"], "--output", str(output), "--public-dir", str(public_dir), "--props", str(props), "--receipt", str(receipt), "--scale", "0.5"],
                cwd=renderer,
                timeout=3600,
            )
        segment_cache[f"{row['variant_id']}:{row['segment_id']}"] = {
            "cache_key": key,
            "cache_hit": cache_hit,
            "path": str(output),
            "sha256": sha256_file(output),
            "receipt_path": str(receipt),
            "beat_ids": row["beat_ids"],
        }
    for variant, composition in (
        ("short_9x16", "ConcreteFirstShort"),
        ("midform_16x9", "ConcreteFirstMidform"),
    ):
        variant_rows: dict[str, Any] = {}
        for mode, captions, scale in (
            ("proxy", True, 0.5),
            ("proxy_captions_hidden", False, 0.5),
            ("full", True, 1.0),
            ("full_captions_hidden", False, 1.0),
        ):
            props = runtime / "contracts" / "render" / f"{variant}_{mode}_props.json"
            receipt = runtime / "receipts" / "render" / f"{variant}_{mode}.json"
            output = runtime / "render_cache" / "silent" / f"{variant}_{mode}.mp4"
            _write_json(props, {"captionsVisible": captions, "assetBase": "assets"})
            _run(
                [node, str(render_script), "--composition", composition, "--output", str(output), "--public-dir", str(public_dir), "--props", str(props), "--receipt", str(receipt), "--scale", str(scale)],
                cwd=renderer,
                timeout=5400,
            )
            variant_rows[mode] = {
                "path": str(output),
                "sha256": sha256_file(output),
                "receipt": _read_json(receipt),
            }
        results[variant] = variant_rows
    manifest = {
        "schema_version": "contentops.retention_native.motion_render.v2",
        "video_id": VIDEO_ID,
        "variants": results,
        "segment_proxy_cache": segment_cache,
        "selective_rerender_unit": "variant_segment_component",
        "network_calls": 0,
        "uploads": 0,
        "public_write": False,
    }
    _write_json(runtime / "motion_render_manifest_v2.json", manifest)
    return manifest


def _parse_loudnorm(stderr: str) -> dict[str, Any]:
    matches = list(re.finditer(r"\{\s*\"input_i\".*?\}", stderr, flags=re.DOTALL))
    if not matches:
        raise RuntimeError("ffmpeg_loudnorm_json_missing")
    return json.loads(matches[-1].group(0))


def _measure_loudness(path: Path, ffmpeg: str) -> dict[str, float]:
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", str(path), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "NUL"],
        capture_output=True, text=True, timeout=1200, check=False,
    )
    value = _parse_loudnorm(result.stderr)
    return {"integrated_lufs": float(value["input_i"]), "true_peak_dbtp": float(value["input_tp"])}


def build_audio_and_mux(
    *, runtime: Path, tts_python: str, ffmpeg: str, ffprobe: str
) -> dict[str, Any]:
    segments = _read_json(runtime / "contracts" / "segment_authorship_v2.json")
    renders = _read_json(runtime / "motion_render_manifest_v2.json")
    results: dict[str, Any] = {}
    for variant in ("short_9x16", "midform_16x9"):
        beats = segments[f"{variant}_beats"]
        duration = float(segments["durations_seconds"][variant])
        narration_text = " ".join(str(beat["narration"]) for beat in beats)
        narration = runtime / "audio" / variant / "narration.wav"
        narration.parent.mkdir(parents=True, exist_ok=True)
        request = runtime / "contracts" / "audio" / f"{variant}_kokoro_request.json"
        _write_json(request, {
            "schema_version": "contentops.retention_native.kokoro_batch_request.v2",
            "segments": [{
                "beat_id": f"{variant}-narration",
                "text": narration_text.replace("EIA", "E I A"),
                "voice": "af_heart",
                "speed": 1.13 if variant == "short_9x16" else 1.0,
                "output_path": str(narration),
            }],
        })
        worker = _run(
            [tts_python, "-m", "live_contentops.video_tts_worker_v1", "--batch-request", str(request)],
            cwd=Path.cwd(),
            timeout=5400,
        )
        state_timeline: list[dict[str, Any]] = []
        sfx: list[dict[str, Any]] = []
        at = 0.0
        for beat in beats:
            beat_duration = float(beat["duration_seconds"])
            state_timeline.append({"start_seconds": at, "end_seconds": at + beat_duration, "state": beat["audio_state"]})
            if beat["sfx_kind"] != "none":
                sfx.append({
                    "cue_id": f"{variant}-{beat['beat_id']}",
                    "kind": beat["sfx_kind"],
                    "at_seconds": at + beat_duration * float(beat["sfx_at_fraction"]),
                    "authored_intent": beat.get("sfx_intent"),
                })
            at += beat_duration
        score = render_owned_score(
            duration_seconds=duration,
            state_timeline=state_timeline,
            sfx_cues=sfx,
            output_dir=runtime / "audio" / variant / "score",
        )
        premaster = runtime / "audio" / variant / "premaster.wav"
        master = runtime / "audio" / variant / "master.wav"
        _run([
            ffmpeg, "-y", "-v", "error",
            "-i", str(narration), "-i", str(score["music"]["path"]), "-i", str(score["sfx"]["path"]),
            "-filter_complex",
            f"[0:a]apad,atrim=0:{duration},volume=1.0[n];[1:a]atrim=0:{duration},volume=0.17[m];[2:a]atrim=0:{duration},volume=0.62[s];[n][m][s]amix=inputs=3:duration=longest:normalize=0,atrim=0:{duration}[a]",
            "-map", "[a]", "-ar", "48000", "-ac", "2", str(premaster),
        ], timeout=1800)
        _run([
            ffmpeg, "-y", "-v", "error", "-i", str(premaster),
            "-af", "loudnorm=I=-16:TP=-1.8:LRA=11", "-ar", "48000", "-ac", "2", str(master),
        ], timeout=1800)
        measurement = _measure_loudness(master, ffmpeg)
        if not -17 <= measurement["integrated_lufs"] <= -15:
            raise RuntimeError(f"audio_loudness_outside_contract:{variant}:{measurement}")
        if measurement["true_peak_dbtp"] > -1.5:
            raise RuntimeError(f"audio_true_peak_outside_contract:{variant}:{measurement}")
        output_rows: dict[str, Any] = {}
        for mode, silent_key, suffix in (
            ("final", "full", ""),
            ("captions_hidden", "full_captions_hidden", "_captions_hidden"),
        ):
            output = runtime / "outputs" / f"{variant}{suffix}.mp4"
            output.parent.mkdir(parents=True, exist_ok=True)
            _run([
                ffmpeg, "-y", "-v", "error", "-i", renders["variants"][variant][silent_key]["path"],
                "-i", str(master), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(output),
            ], timeout=1800)
            output_rows[mode] = {"path": str(output), "sha256": sha256_file(output)}
        results[variant] = {
            "duration_seconds": duration,
            "narration": {"path": str(narration), "sha256": sha256_file(narration), "provider": "kokoro", "model": "Kokoro-82M", "voice": "af_heart", "network_calls": 0},
            "worker_stdout_tail": worker.stdout[-1000:],
            "score": score,
            "master": {"path": str(master), "sha256": sha256_file(master), "measurement": measurement},
            "outputs": output_rows,
        }
    manifest = {
        "schema_version": "contentops.retention_native.audio_mux.v2",
        "video_id": VIDEO_ID,
        "variants": results,
        "target_integrated_lufs": -16.0,
        "true_peak_dbtp_max": -1.5,
        "network_calls": 0,
        "uploads": 0,
        "public_write": False,
    }
    _write_json(runtime / "audio_mux_manifest_v2.json", manifest)
    return manifest


def probe_media(*, runtime: Path, ffprobe: str) -> dict[str, Any]:
    audio = _read_json(runtime / "audio_mux_manifest_v2.json")
    expected = {
        "short_9x16": (1080, 1920, 45.0, 60.0),
        "midform_16x9": (1920, 1080, 90.0, 150.0),
    }
    rows: dict[str, Any] = {}
    for variant, (width, height, minimum, maximum) in expected.items():
        variants: dict[str, Any] = {}
        for mode in ("final", "captions_hidden"):
            path = Path(audio["variants"][variant]["outputs"][mode]["path"])
            raw = _run([
                ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
            ], timeout=300)
            probe = json.loads(raw.stdout)
            video = next(row for row in probe["streams"] if row["codec_type"] == "video")
            sound = next(row for row in probe["streams"] if row["codec_type"] == "audio")
            duration = float(probe["format"]["duration"])
            blockers: list[str] = []
            if (int(video["width"]), int(video["height"])) != (width, height):
                blockers.append("dimensions")
            if video["codec_name"] != "h264" or sound["codec_name"] != "aac":
                blockers.append("codecs")
            if not minimum <= duration <= maximum + 0.5:
                blockers.append("duration")
            variants[mode] = {
                "path": str(path), "sha256": sha256_file(path), "duration_seconds": duration,
                "width": int(video["width"]), "height": int(video["height"]),
                "video_codec": video["codec_name"], "audio_codec": sound["codec_name"],
                "fps": video.get("avg_frame_rate"), "size_bytes": path.stat().st_size,
                "status": "PASS" if not blockers else "BLOCK", "blockers": blockers,
            }
            if blockers:
                raise RuntimeError(f"final_media_probe_block:{variant}:{mode}:{blockers}")
        rows[variant] = variants
    report = {
        "schema_version": "contentops.retention_native.final_media_probe.v2",
        "video_id": VIDEO_ID,
        "variants": rows,
        "status": "PASS",
        "public_write": False,
    }
    _write_json(runtime / "final_media_probe_v2.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("author", "render", "audio", "probe"))
    parser.add_argument("--runtime", default=str(DEFAULT_RUNTIME))
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--node", default="node")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--tts-python", default=r"A:\Capital Chronicle\Runtime\ContentOps\tier2\tts-kokoro-venv\Scripts\python.exe")
    args = parser.parse_args()
    runtime = Path(args.runtime).resolve()
    repo_root = Path(args.repo_root).resolve()
    if args.stage == "author":
        result = author_motion(runtime=runtime, repo_root=repo_root)
    elif args.stage == "render":
        result = render_motion(runtime=runtime, repo_root=repo_root, node=args.node)
    elif args.stage == "audio":
        result = build_audio_and_mux(runtime=runtime, tts_python=args.tts_python, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
    else:
        result = probe_media(runtime=runtime, ffprobe=args.ffprobe)
    print(json.dumps({"status": "PASS", "stage": args.stage, "result_sha256": logical_hash(result)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
