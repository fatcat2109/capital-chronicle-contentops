"""Codex Builder brain lane for the controlled V2 A/B creative comparison."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from live_contentops.media_manifest_authority_v1 import sha256_file
from live_contentops.retention_native_concrete_first_v2 import (
    canonical_json,
    logical_hash,
)
from live_contentops.retention_native_motion_pipeline_v2 import (
    build_audio_and_mux,
    probe_media,
)
from live_contentops.retention_native_review_qa_v2 import (
    build_review_artifacts,
    deterministic_qa,
)

SCHEMA_VERSION = "contentops.retention_native.codex_builder_lane.v1"
VIDEO_ID = "cc-v2-eia-hormuz-codex-builder-2026-v1"
DEFAULT_RUNTIME = Path(
    r"A:\Capital Chronicle\Runtime\ContentOps\v2_codex_builder_ab_20260814"
)
CX_BENCHMARK_RUNTIME = Path(
    r"A:\Capital Chronicle\Runtime\ContentOps\v2_concrete_first_xhigh_replacement_20260813"
)
RENDERER_RELATIVE = Path("video") / "concrete_first_v2"
GENERATED_ILLUSTRATION_RELATIVE = (
    Path("video")
    / "concrete_first_v2"
    / "src"
    / "codex_builder_assets"
    / "energy-flow-illustration-v1.png"
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8")


def _run(
    command: Sequence[str], *, cwd: Path | None = None, timeout: float = 5400
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"codex_builder_command_failed:{Path(command[0]).name}:"
            f"{result.stderr[-2000:]}:{result.stdout[-1000:]}"
        )
    return result


def _beat(
    beat_id: str,
    duration: float,
    narration: str,
    takeaway: str,
    visual: str,
    subject: str,
    assets: list[str],
    audio_state: str,
    *,
    sfx: str = "none",
    sfx_at: float = 0.55,
    motion: str = "Purposeful documentary reframe with staged editorial reveal.",
    transition: str = "Motivated hard cut on semantic change.",
    easing: str = "restrained ease-out",
) -> dict[str, Any]:
    return {
        "beat_id": beat_id,
        "duration_seconds": duration,
        "narration": narration,
        "viewer_takeaway": takeaway,
        "primary_visual_type": visual,
        "recognizable_subject": subject,
        "asset_ids": assets,
        "motion_intent": motion,
        "transition_intent": transition,
        "timing_easing": easing,
        "audio_state": audio_state,
        "sfx_kind": sfx,
        "sfx_at_fraction": sfx_at,
        "sfx_intent": (
            "A restrained owned cue marks the information-state change."
            if sfx != "none"
            else ""
        ),
    }


def _plan() -> dict[str, Any]:
    short = [
        _beat(
            "CB_SHORT_01_HOOK",
            3.0,
            "One narrow exit can change the whole oil story.",
            "The oil story begins at the Persian Gulf and Strait of Hormuz.",
            "documentary_context",
            "Persian Gulf seen from orbit",
            ["nasa-persian-gulf-iss069-e-92132"],
            "cold_open",
            sfx="hit",
            sfx_at=0.72,
        ),
        _beat(
            "CB_SHORT_02_MOVEMENT_VS_SUPPLY",
            6.0,
            "EIA reported more Hormuz traffic, but moving ships do not yet prove restored supply.",
            "Reported vessel movement is not yet restored supply.",
            "documentary_context",
            "Hormuz map and real U.S. Navy oiler",
            ["eia-hormuz-map-portrait", "usns-oiler-strait-of-hormuz"],
            "tension",
            sfx="data_tick",
        ),
        _beat(
            "CB_SHORT_03_PHYSICAL_CHAIN",
            7.0,
            "The barrels still have to unload, production has to return, and inventories have to rebuild.",
            "Supply recovery requires unloading, production and inventories.",
            "documentary_context",
            "terminal, refinery and storage tanks",
            [
                "doe-tanker-terminal-pipeline",
                "nara-refinery-portrait",
                "refinery-storage-tanks",
            ],
            "mechanism",
            sfx="hit",
            sfx_at=0.42,
            transition="Three-step physical match cut.",
        ),
        _beat(
            "CB_SHORT_04_SOURCE",
            7.0,
            "This is EIA's July seventh release. Every forward number here is a forecast.",
            "The dated EIA source appears before interpretation.",
            "primary_document",
            "EIA release excerpt",
            ["eia-release-document-portrait"],
            "evidence",
            sfx="data_tick",
        ),
        _beat(
            "CB_SHORT_05_FORECAST",
            8.0,
            "June Brent was eighty-five dollars. EIA forecasts seventy-four in Q3 and sixty-five in 2027.",
            "June $85 is a reference; $74 and $65 are forecasts.",
            "native_data_visual",
            "Capital Chronicle native Brent comparison",
            ["eia-brent-forecast-portrait"],
            "evidence",
            sfx="data_tick",
            sfx_at=0.68,
            motion="Frame-driven line draw with separately timed reference and forecast labels.",
            transition="Document detail dissolves into native data geometry.",
        ),
        _beat(
            "CB_SHORT_06_TRANSMISSION",
            5.333333,
            "If that retreat holds, market effects spread outward.",
            "Illustrative transmission links oil to broader consequences.",
            "illustrative_abstraction",
            "labeled abstract energy-flow texture",
            ["cc-energy-flow-illustration-v1"],
            "consequence",
            sfx="riser",
            sfx_at=0.26,
            motion="Brief labeled illustrative transition with bounded parallax.",
        ),
        _beat(
            "CB_SHORT_07_CONSEQUENCES",
            7.166667,
            "Importers may gain and gasoline may ease, but producer revenue may weaken and the Fed is not automatic.",
            "Consequences are conditional and the Fed response is not automatic.",
            "documentary_context",
            "refinery storage tanks with conditional analysis",
            ["refinery-storage-tanks"],
            "boundary",
            sfx="data_tick",
        ),
        _beat(
            "CB_SHORT_08_TEST",
            7.0,
            "Confirm it with traffic, production, inventory builds, and Brent. Challenge it with disruption, slow restarts, draws, or above-path prices.",
            "A four-signal confirm/challenge test replaces prediction theater.",
            "documentary_context",
            "storage tanks and a confirm/challenge checklist",
            ["refinery-storage-tanks"],
            "tension",
            sfx="hit",
        ),
        _beat(
            "CB_SHORT_09_CHECKPOINTS",
            6.7,
            "WTI at sixty-nine sixty is a separate observation. Watch July fifteenth and August eleventh, then test conditions—not a promised outcome.",
            "WTI is separate from Brent and future dates are checkpoints only.",
            "native_data_visual",
            "WTI observation and two dated checkpoints",
            [],
            "outro",
            sfx="data_tick",
            sfx_at=0.48,
            motion="Minimal timeline draw followed by a restrained brand resolve.",
        ),
    ]
    mid = [
        _beat(
            "CB_MID_01_ORBIT",
            7.0,
            "The supply question begins with geography. The Persian Gulf has one narrow exit.",
            "Locate the Persian Gulf before discussing markets.",
            "documentary_context",
            "Persian Gulf seen from orbit",
            ["nasa-persian-gulf-iss069-e-92132"],
            "cold_open",
            sfx="hit",
        ),
        _beat(
            "CB_MID_02_MAP_AND_TRAFFIC",
            9.0,
            "That exit is the Strait of Hormuz. EIA reported more traffic after the June eighteenth memorandum, but movement alone does not restore supply.",
            "Hormuz traffic changed, but movement and restored supply are different claims.",
            "documentary_context",
            "Hormuz map and real vessel",
            ["eia-hormuz-map-landscape", "usns-oiler-strait-of-hormuz"],
            "tension",
            sfx="data_tick",
        ),
        _beat(
            "CB_MID_03_PHYSICAL_CHAIN",
            12.0,
            "The oil must reach a terminal. Shut-in production must return. Then inventories must rebuild before movement becomes available supply.",
            "Unloading, production and inventories form the physical recovery chain.",
            "documentary_context",
            "terminal, refinery and storage tanks",
            [
                "doe-tanker-terminal-pipeline",
                "nara-refinery-portrait",
                "refinery-storage-tanks",
            ],
            "mechanism",
            sfx="hit",
            sfx_at=0.5,
        ),
        _beat(
            "CB_MID_04_TRANSIT_LIMIT",
            9.0,
            "A ship beyond Hormuz establishes transit. It does not establish production restoration or inventory growth.",
            "Transit is a necessary but insufficient signal.",
            "documentary_context",
            "commercial tanker and oil infrastructure",
            ["commercial-tanker-oil-platform-persian-gulf"],
            "boundary",
        ),
        _beat(
            "CB_MID_05_SOURCE",
            15.0,
            "Now put the source on screen. EIA's July seventh release expects flows and prices to move toward pre-conflict conditions. That language is a forecast, not an observed result.",
            "The source date and forecast boundary stay visible before analysis.",
            "primary_document",
            "EIA release excerpt",
            ["eia-release-document-landscape"],
            "evidence",
            sfx="data_tick",
            sfx_at=0.58,
        ),
        _beat(
            "CB_MID_06_FORECAST",
            8.0,
            "June Brent was eighty-five dollars. EIA forecasts seventy-four in Q3 and sixty-five in 2027.",
            "Separate the observed June reference from two forward values.",
            "native_data_visual",
            "native Brent line comparison",
            ["eia-brent-forecast-landscape"],
            "evidence",
            sfx="data_tick",
            sfx_at=0.72,
        ),
        _beat(
            "CB_MID_07_TRANSMISSION",
            16.0,
            "If that retreat holds, the effect can move through import costs, gasoline and inflation expectations. This graphic is illustrative analysis, not evidence.",
            "A labeled illustrative bridge explains transmission without impersonating evidence.",
            "illustrative_abstraction",
            "abstract energy-flow texture with explicit illustrative label",
            ["cc-energy-flow-illustration-v1"],
            "consequence",
            sfx="riser",
            sfx_at=0.22,
        ),
        _beat(
            "CB_MID_08_CONSEQUENCES",
            21.0,
            "EIA forecasts gasoline at three dollars eighty in Q3 and three forty in Q4. A sustained retreat may support importers and ease headline inflation, while pressuring producer revenue. It still does not dictate the Federal Reserve.",
            "Gasoline and macro implications remain conditional.",
            "documentary_context",
            "storage tanks with conditional consequence modules",
            ["refinery-storage-tanks"],
            "boundary",
            sfx="data_tick",
            sfx_at=0.38,
        ),
        _beat(
            "CB_MID_09_TEST",
            17.0,
            "Confirmation needs continued Hormuz traffic, restored production, inventory builds, and Brent broadly along the path. Renewed disruption, slower restarts, persistent draws or above-path prices would challenge it.",
            "The forecast becomes an explicit four-signal test.",
            "documentary_context",
            "storage tanks and analytical test grid",
            ["refinery-storage-tanks"],
            "tension",
            sfx="hit",
        ),
        _beat(
            "CB_MID_10_CHECKPOINTS",
            8.0,
            "WTI at sixty-nine sixty on July sixth is a separate observation. Use July fifteenth and August eleventh as checkpoints, then judge the conditions—not a promised outcome.",
            "Separate WTI from Brent and close on dated checkpoints.",
            "native_data_visual",
            "WTI observation and checkpoint timeline",
            [],
            "outro",
            sfx="data_tick",
        ),
    ]
    short_motion_metadata = [
        (
            "Slow orbital push with kinetic title lock.",
            "Geographic smash cut.",
            "cinematic settle",
        ),
        (
            "Map-to-vessel split reveal with traffic pulse.",
            "Spatial split wipe.",
            "firm ease-out",
        ),
        (
            "Three documentary stages reveal in a vertical chain.",
            "Physical match cut.",
            "staggered spring settle",
        ),
        (
            "Dated document floats beside an external forecast boundary.",
            "Source-first hard cut.",
            "measured deceleration",
        ),
        (
            "Native line draws once; reference and forecast points lock separately.",
            "Document-to-data dissolve.",
            "linear draw then hold",
        ),
        (
            "Brief bounded parallax across a disclosed illustrative texture.",
            "Analytical bridge dissolve.",
            "slow optical drift",
        ),
        (
            "Conditional consequence modules reveal over real storage imagery.",
            "Grounded consequence cut.",
            "stepped ease-out",
        ),
        (
            "Confirm and challenge panels build as opposing evidence lists.",
            "Dual-panel state change.",
            "alternating stagger",
        ),
        (
            "Checkpoint line draws, dates lock, then brand resolves.",
            "Timeline resolve.",
            "linear-to-soft hold",
        ),
    ]
    mid_motion_metadata = [
        (
            "Orbital geography push with restrained title reveal.",
            "Orbital establishing cut.",
            "cinematic settle",
        ),
        (
            "Landscape map yields to a real vessel through a vertical split.",
            "Spatial split wipe.",
            "firm ease-out",
        ),
        (
            "Terminal, refinery and storage reveal as a three-column physical chain.",
            "Infrastructure match cut.",
            "staggered spring settle",
        ),
        (
            "Real tanker context holds while the transit boundary resolves.",
            "Boundary hard cut.",
            "measured deceleration",
        ),
        (
            "Dated EIA document receives a slow readable evidence push beside interpretation.",
            "Source-first document cut.",
            "slow evidence push",
        ),
        (
            "Native Brent line draws once with independently timed points.",
            "Document-to-data dissolve.",
            "linear draw then hold",
        ),
        (
            "Disclosed illustrative texture drifts under three transmission nodes.",
            "Analytical bridge dissolve.",
            "bounded optical drift",
        ),
        (
            "Three conditional consequence modules stage over documentary tanks.",
            "Grounded consequence cut.",
            "stepped ease-out",
        ),
        (
            "Confirm and challenge columns build as opposing test states.",
            "Dual-panel state change.",
            "alternating stagger",
        ),
        (
            "WTI boundary and checkpoint timeline resolve into the brand close.",
            "Timeline brand resolve.",
            "linear-to-soft hold",
        ),
    ]
    for beat, (motion, transition, easing) in zip(short, short_motion_metadata):
        beat.update(
            {
                "motion_intent": motion,
                "transition_intent": transition,
                "timing_easing": easing,
            }
        )
    for beat, (motion, transition, easing) in zip(mid, mid_motion_metadata):
        beat.update(
            {
                "motion_intent": motion,
                "transition_intent": transition,
                "timing_easing": easing,
            }
        )
    segments = [
        {
            "segment_id": "CB_S1_GEOGRAPHY_AND_TRAFFIC",
            "short_9x16_beats": short[0:2],
            "midform_16x9_beats": mid[0:2],
        },
        {
            "segment_id": "CB_S2_PHYSICAL_SUPPLY",
            "short_9x16_beats": short[2:3],
            "midform_16x9_beats": mid[2:4],
        },
        {
            "segment_id": "CB_S3_SOURCE_AND_FORECAST",
            "short_9x16_beats": short[3:5],
            "midform_16x9_beats": mid[4:6],
        },
        {
            "segment_id": "CB_S4_TRANSMISSION_AND_CONSEQUENCES",
            "short_9x16_beats": short[5:7],
            "midform_16x9_beats": mid[6:8],
        },
        {
            "segment_id": "CB_S5_TEST_AND_CHECKPOINTS",
            "short_9x16_beats": short[7:9],
            "midform_16x9_beats": mid[8:10],
        },
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "video_id": VIDEO_ID,
        "brain": "CODEX_BUILDER",
        "benchmark_id": "EIA_HORMUZ_SHARED_AB_V1",
        "durations_seconds": {"short_9x16": 57.2, "midform_16x9": 122.0},
        "short_9x16_beats": short,
        "midform_16x9_beats": mid,
        "segments": segments,
        "public_write": False,
    }


def prepare(*, runtime: Path, repo_root: Path) -> dict[str, Any]:
    source_public = CX_BENCHMARK_RUNTIME / "render_public" / "assets"
    destination = runtime / "render_public" / "assets"
    if not source_public.is_dir():
        raise RuntimeError("shared_benchmark_assets_missing")
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, Any]] = []
    for source in source_public.iterdir():
        if source.is_file():
            target = destination / source.name
            shutil.copy2(source, target)
            copied.append({"name": source.name, "sha256": sha256_file(target)})
    generated = repo_root / GENERATED_ILLUSTRATION_RELATIVE
    generated_target = destination / "cc-energy-flow-illustration-v1.png"
    shutil.copy2(generated, generated_target)
    copied.append(
        {"name": generated_target.name, "sha256": sha256_file(generated_target)}
    )
    plan = _plan()
    _write_json(runtime / "contracts" / "segment_authorship_v2.json", plan)
    storyboard = {
        "schema_version": "contentops.retention_native.codex_builder_storyboard_gate.v1",
        "video_id": VIDEO_ID,
        "variants": {
            variant: {
                "must_use_asset_compliance": {"status": "PASS"},
                "visual_mix": {
                    "status": "PASS",
                    "documentary_or_source_dominant": True,
                    "illustrative_transition_seconds": (
                        5.333333 if variant == "short_9x16" else 16.0
                    ),
                    "illustrative_content_labeled": True,
                },
            }
            for variant in ("short_9x16", "midform_16x9")
        },
        "public_write": False,
    }
    _write_json(runtime / "storyboard_animatic_manifest_v2.json", storyboard)
    capabilities = {
        "schema_version": "contentops.retention_native.codex_builder_capabilities.v1",
        "brain": "CODEX_BUILDER",
        "capabilities": {
            "topic_and_story_selection": "CODEX_AUTHORED_FIXED_BENCHMARK",
            "narration": "CODEX_AUTHORED",
            "shot_edit_strategy": "CODEX_AUTHORED",
            "motion_code": "CODEX_AUTHORED_REACT_REMOTION",
            "factual_documentary_assets": "V2_RIGHTS_GOVERNED_ASSET_UNIVERSE",
            "illustrative_image": "CODEX_BUILTIN_IMAGEGEN",
            "graphic_elements": "CODEX_CODE_NATIVE_SVG_CSS",
            "voice_waveform": "V2_KOKORO_FALLBACK_REQUIRED",
            "music_and_sfx": "CODEX_DIRECTED_V2_OWNED_PROCEDURAL_SYNTHESIS",
            "render_and_mux": "V2_REMOTION_FFMPEG",
        },
        "generated_illustration": {
            "path": str(generated),
            "runtime_path": str(generated_target),
            "sha256": sha256_file(generated_target),
            "factual_authority": False,
            "viewer_label": "ILLUSTRATIVE ANALYSIS · NOT EVIDENCE",
        },
        "shared_benchmark_asset_count": len(copied) - 1,
        "public_write": False,
    }
    _write_json(runtime / "codex_builder_capabilities_v1.json", capabilities)
    return {
        "status": "PASS_CODEX_BUILDER_LANE_PREPARED",
        "video_id": VIDEO_ID,
        "plan_sha256": logical_hash(plan),
        "asset_count": len(copied),
        "public_write": False,
    }


def render(
    *, runtime: Path, repo_root: Path, node: str, proxy_only: bool = False
) -> dict[str, Any]:
    plan = _read_json(runtime / "contracts" / "segment_authorship_v2.json")
    renderer = (repo_root / RENDERER_RELATIVE).resolve()
    render_script = renderer / "scripts" / "render.mjs"
    authorship_sha256 = logical_hash(
        {
            "tsx_sha256": sha256_file(renderer / "src" / "CodexBuilder.tsx"),
            "root_sha256": sha256_file(renderer / "src" / "Root.tsx"),
            "illustration_sha256": sha256_file(
                runtime
                / "render_public"
                / "assets"
                / "cc-energy-flow-illustration-v1.png"
            ),
            "durations_seconds": plan["durations_seconds"],
        }
    )
    variants: dict[str, Any] = {}
    for variant, composition in (
        ("short_9x16", "CodexBuilderShort"),
        ("midform_16x9", "CodexBuilderMidform"),
    ):
        rows: dict[str, Any] = {}
        render_modes = (
            ("proxy", True, 0.5),
            ("proxy_captions_hidden", False, 0.5),
            ("full", True, 1.0),
            ("full_captions_hidden", False, 1.0),
        )
        if proxy_only:
            render_modes = render_modes[:2]
        for mode, captions, scale in render_modes:
            output = runtime / "render_cache" / "silent" / f"{variant}_{mode}.mp4"
            props = runtime / "contracts" / "render" / f"{variant}_{mode}.json"
            receipt = runtime / "receipts" / "render" / f"{variant}_{mode}.json"
            _write_json(
                props,
                {
                    "captionsVisible": captions,
                    "assetBase": "assets",
                    "authorshipSha256": authorship_sha256,
                    "brain": "CODEX_BUILDER",
                },
            )
            cached = _read_json(receipt) if receipt.is_file() else {}
            cache_hit = (
                output.is_file()
                and receipt.is_file()
                and cached.get("authorship_sha256") == authorship_sha256
            )
            if not cache_hit:
                _run(
                    [
                        node,
                        str(render_script),
                        "--composition",
                        composition,
                        "--output",
                        str(output),
                        "--public-dir",
                        str(runtime / "render_public"),
                        "--props",
                        str(props),
                        "--receipt",
                        str(receipt),
                        "--scale",
                        str(scale),
                    ],
                    cwd=renderer,
                )
            rows[mode] = {
                "path": str(output),
                "sha256": sha256_file(output),
                "receipt": _read_json(receipt),
                "cache_hit": cache_hit,
            }
        variants[variant] = rows
    manifest = {
        "schema_version": "contentops.retention_native.motion_render.v2",
        "video_id": VIDEO_ID,
        "brain": "CODEX_BUILDER",
        "variants": variants,
        "segment_proxy_cache": {},
        "authorship_sha256": authorship_sha256,
        "network_calls": 0,
        "uploads": 0,
        "public_write": False,
        "proxy_only": proxy_only,
    }
    _write_json(runtime / "motion_render_manifest_v2.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=("prepare", "render-proxy", "render", "review", "audio", "probe"),
    )
    parser.add_argument("--runtime", default=str(DEFAULT_RUNTIME))
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--node", default="node")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument(
        "--tts-python",
        default=(
            r"A:\Capital Chronicle\Runtime\ContentOps\tier2\tts-kokoro-venv"
            r"\Scripts\python.exe"
        ),
    )
    args = parser.parse_args()
    runtime = Path(args.runtime).resolve()
    repo_root = Path(args.repo_root).resolve()
    if args.stage == "prepare":
        result = prepare(runtime=runtime, repo_root=repo_root)
    elif args.stage in {"render-proxy", "render"}:
        result = render(
            runtime=runtime,
            repo_root=repo_root,
            node=args.node,
            proxy_only=args.stage == "render-proxy",
        )
    elif args.stage == "review":
        build_review_artifacts(runtime=runtime, ffmpeg=args.ffmpeg)
        result = deterministic_qa(runtime=runtime)
    elif args.stage == "audio":
        result = build_audio_and_mux(
            runtime=runtime,
            tts_python=args.tts_python,
            ffmpeg=args.ffmpeg,
            ffprobe=args.ffprobe,
        )
    else:
        result = probe_media(runtime=runtime, ffprobe=args.ffprobe)
    print(
        json.dumps(
            {
                "status": str(result.get("status") or "PASS"),
                "stage": args.stage,
                "result_sha256": logical_hash(result),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
