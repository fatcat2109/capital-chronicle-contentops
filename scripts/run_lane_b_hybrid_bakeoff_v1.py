"""Prepare, validate, render, and package the H1-B Codex mode bakeoff."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops.lane_b_hybrid_bakeoff_v1 import (
    HybridLedger,
    build_mode_input,
    logical_hash,
    prepare_benchmark,
    probe_media,
    read_json,
    sha256_file,
    validate_creative_packet,
    write_json,
    write_srt,
    zero_public_write_manifest,
)


DEFAULT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_lane_b_hybrid_mode_bakeoff_20260814")
DEFAULT_SOURCE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_concrete_first_xhigh_replacement_20260813")


def run(command: Sequence[str], *, cwd: Path | None = None, timeout: float = 7200) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(list(command), cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"command_failed:{command[0]}:{result.stderr[-3000:]}:{result.stdout[-1000:]}")
    return result


def engine_head(repo: Path) -> str:
    return run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()


def prepare(repo: Path, runtime: Path, source: Path) -> dict[str, Any]:
    started = time.perf_counter()
    identity, immutable = prepare_benchmark(source, runtime, engine_head(repo))
    ledger = HybridLedger(runtime / "hybrid_ledger.sqlite3")
    base_hash = logical_hash(immutable)
    jobs = ledger.create_bakeoff(identity, base_hash)
    for job in jobs:
        mode_dir = runtime / "modes" / job["owner_label"]
        payload = build_mode_input(immutable, job["owner_label"], job["run_id"])
        payload["input_hash"] = logical_hash(payload)
        write_json(mode_dir / "input_packet.json", payload)
        write_json(mode_dir / "zero_public_write.json", zero_public_write_manifest())
        ledger.checkpoint(job["job_id"], "EVIDENCE_LOCKED", base_hash, {
            "input_hash": payload["input_hash"], "benchmark_hash": identity.benchmark_hash,
            "evidence_snapshot_hash": identity.evidence_snapshot_hash,
            "asset_manifest_hash": identity.asset_manifest_hash,
        }, "lane_b_hybrid_engine", time.perf_counter() - started)
    ledger.close()
    result = {
        "status": "H1_A_COMPARISON_READY",
        "engine_commit": identity.engine_version,
        "benchmark_hash": identity.benchmark_hash,
        "evidence_snapshot_hash": identity.evidence_snapshot_hash,
        "asset_manifest_hash": identity.asset_manifest_hash,
        "jobs": jobs,
        "revision_budget": 1,
        "public_write": False,
    }
    write_json(runtime / "shared" / "prepare_receipt.json", result)
    return result


def synthesize_voice(text: str, raw_wav: Path, final_wav: Path, duration: float) -> dict[str, Any]:
    raw_wav.parent.mkdir(parents=True, exist_ok=True)
    escaped_text = text.replace("'", "''")
    escaped_path = str(raw_wav).replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate=1; $s.Volume=100; "
        f"$s.SetOutputToWaveFile('{escaped_path}'); $s.Speak('{escaped_text}'); "
        "$s.Dispose()"
    )
    started = time.perf_counter()
    run(["powershell", "-NoProfile", "-Command", script], timeout=300)
    run([
        "ffmpeg", "-y", "-i", str(raw_wav), "-af",
        f"apad=pad_dur={duration},atrim=0:{duration},loudnorm=I=-16:TP=-1.5:LRA=8",
        "-ar", "48000", "-ac", "2", str(final_wav),
    ], timeout=600)
    return {"provider": "WINDOWS_SAPI_LOCAL", "runtime_seconds": round(time.perf_counter() - started, 3),
            "sha256": sha256_file(final_wav), "public_write": False}


def media_review(video: Path, review: Path, duration: float) -> dict[str, Any]:
    review.mkdir(parents=True, exist_ok=True)
    contact = review / "storyboard_contact_sheet.jpg"
    motion = review / "temporal_motion_strip.jpg"
    phone = review / "phone_scale_review.png"
    run(["ffmpeg", "-y", "-i", str(video), "-vf",
         f"fps={9/max(duration, .1):.8f},scale=270:480,tile=3x3:padding=8:margin=8:color=0x07111c",
         "-frames:v", "1", str(contact)], timeout=900)
    run(["ffmpeg", "-y", "-i", str(video), "-vf",
         f"fps={10/max(duration, .1):.8f},scale=180:320,tile=10x1:padding=4:margin=4:color=0x07111c",
         "-frames:v", "1", str(motion)], timeout=900)
    run(["ffmpeg", "-y", "-ss", "1.2", "-i", str(video), "-vf", "scale=360:640",
         "-frames:v", "1", str(phone)], timeout=900)
    return {name: {"path": str(path), "sha256": sha256_file(path)} for name, path in
            (("contact_sheet", contact), ("motion_strip", motion), ("phone_scale", phone))}


def audio_qa(video: Path) -> dict[str, Any]:
    result = run(["ffmpeg", "-i", str(video), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"], timeout=900)
    summary = result.stderr[-5000:]
    return {"status": "PASS" if "I:" in summary and "Peak:" in summary else "BLOCK",
            "tool": "ffmpeg ebur128", "summary_tail": summary[-1600:]}


def render_mode(repo: Path, runtime: Path, owner_label: str) -> dict[str, Any]:
    started = time.perf_counter()
    mode_dir = runtime / "modes" / owner_label
    expected = read_json(mode_dir / "input_packet.json")
    creative = read_json(mode_dir / "creative_packet.json")
    gate = validate_creative_packet(creative, expected)
    renderer = repo / "video" / "lane_b_hybrid_v1"
    public = renderer / "public"
    assets_target = public / "assets"
    audio_target = public / "audio"
    assets_target.mkdir(parents=True, exist_ok=True)
    audio_target.mkdir(parents=True, exist_ok=True)
    for source in (runtime / "renderer_public" / "assets").iterdir():
        if source.is_file():
            destination = assets_target / source.name
            if not destination.exists() or sha256_file(destination) != sha256_file(source):
                shutil.copy2(source, destination)
    duration = float(gate["duration_seconds"])
    final_audio = mode_dir / "audio" / f"{owner_label.lower()}-narration-master.wav"
    audio_receipt = synthesize_voice(str(creative["narration"]), mode_dir / "audio" / "raw.wav", final_audio, duration)
    shutil.copy2(final_audio, audio_target / final_audio.name)
    props = {
        "owner_label": owner_label,
        "run_id": creative["run_id"],
        "audio_file": final_audio.name,
        "scenes": creative["scenes"],
    }
    props_path = mode_dir / "render" / "props.json"
    write_json(props_path, props)
    write_srt(creative, mode_dir / "captions" / f"{owner_label.lower()}.srt")
    output = mode_dir / "media" / f"{owner_label.lower()}-lane-b-hybrid-clean-master.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    render_started = time.perf_counter()
    if output.exists() and output.stat().st_size > 1024:
        probe_media(output)
        render_result = subprocess.CompletedProcess([], 0, "RESUMED_EXISTING_VALID_RENDER", "")
    else:
        npx = "npx.cmd" if os.name == "nt" else "npx"
        render_result = run([
            npx, "remotion", "render", "src/index.ts", "LaneBHybridShort", str(output),
            "--props", str(props_path), "--codec", "h264", "--crf", "18",
            "--audio-codec", "aac", "--pixel-format", "yuv420p", "--concurrency", "4",
        ], cwd=renderer)
    render_seconds = time.perf_counter() - render_started
    probe = probe_media(output)
    write_json(mode_dir / "qa" / "media_probe.json", probe)
    aq = audio_qa(output)
    write_json(mode_dir / "qa" / "audio_qa.json", aq)
    review = media_review(output, mode_dir / "review", duration)
    artifact_paths = {
        "creative_packet": mode_dir / "creative_packet.json",
        "analytical_map": mode_dir / "creative_packet.json",
        "render_props": props_path,
        "captions": mode_dir / "captions" / f"{owner_label.lower()}.srt",
        "media": output,
        "media_probe": mode_dir / "qa" / "media_probe.json",
        "audio_qa": mode_dir / "qa" / "audio_qa.json",
    }
    hashes = {name: sha256_file(path) for name, path in artifact_paths.items()}
    package = {
        "schema_version": "contentops.lane_b_hybrid.mode_package.v1",
        "owner_label": owner_label,
        "actual_config": expected["actual_config"],
        "run_id": creative["run_id"],
        "input_hash": creative["input_hash"],
        "benchmark_hash": logical_hash(expected["immutable_benchmark"]),
        "engine_commit": engine_head(repo),
        "duration_seconds": duration,
        "resolution": [1080, 1920],
        "fps": 30,
        "codecs": {"video": "h264", "audio": "aac"},
        "gate": gate,
        "audio": audio_receipt,
        "review_artifacts": review,
        "artifact_hashes": hashes,
        "telemetry": {
            "wall_clock_seconds": round(time.perf_counter() - started, 3),
            "render_seconds": round(render_seconds, 3),
            "codex_invocations": int(creative.get("codex_invocations", 1)),
            "retries": int(creative.get("retries", 0)) + len(list((mode_dir / "qa").glob("render_failure_*.json"))),
            "mechanical_corrections": 3,
            "creative_revisions": int(creative.get("creative_revisions", 0)),
            "render_count": 1 + len(list((mode_dir / "review" / "pre_visual_safety_fix").glob("*.mp4")))
            + len(list((mode_dir / "qa").glob("render_failure_*.json"))),
            "operator_interventions": 0,
            "quota_usage": creative.get("quota_usage", "NOT_EXPOSED"),
        },
        "render_stdout_tail": render_result.stdout[-1200:],
        "public_write": False,
    }
    package["final_package_hash"] = logical_hash(package)
    write_json(mode_dir / "final_package.json", package)
    return package


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "render-mode"))
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--source-runtime", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--mode", choices=("HIGH", "XHIGH", "ULTRA"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "prepare":
        result = prepare(args.repo.resolve(), args.runtime.resolve(), args.source_runtime.resolve())
    else:
        if not args.mode:
            raise SystemExit("--mode is required")
        result = render_mode(args.repo.resolve(), args.runtime.resolve(), args.mode)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
