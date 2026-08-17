from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import time
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from video.freeform_chapter_pipeline_v1.package_factory import (
    build_caption_cues,
    build_publication_package,
    validate_caption_set,
    validate_media_probe,
    write_caption_artifacts,
)

from .creative import hash_file


class MediaExecutionError(RuntimeError):
    pass


def artifact(path: str | Path) -> dict[str, Any]:
    item = Path(path).resolve()
    if not item.is_file():
        raise MediaExecutionError(f"artifact_missing:{item}")
    return {
        "path": str(item),
        "sha256": hash_file(item),
        "size_bytes": item.stat().st_size,
    }


def run_command(
    command: Sequence[str], *, cwd: str | Path | None = None, timeout: float = 1800
) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        list(map(str, command)),
        cwd=str(cwd) if cwd else None,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    result = {
        "command": [str(item) for item in command],
        "returncode": completed.returncode,
        "wall_time_seconds": round(time.monotonic() - started, 4),
        "output_tail": completed.stdout[-8000:],
    }
    if completed.returncode != 0:
        raise MediaExecutionError(
            f"command_failed:{Path(str(command[0])).name}:{completed.returncode}\n"
            + completed.stdout[-8000:]
        )
    return result


def _ensure_junction(link: Path, target: Path) -> None:
    link = link.resolve(strict=False)
    target = target.resolve()
    if link.exists():
        if link.resolve() != target:
            raise MediaExecutionError(f"runtime_link_target_mismatch:{link}")
        return
    link.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        run_command(["cmd", "/c", "mklink", "/J", str(link), str(target)])
    else:  # pragma: no cover - production host is Windows, retained for portable tests
        link.symlink_to(target, target_is_directory=True)


def prepare_project(
    *, project_root: Path, scaffold_root: Path, dependency_root: Path, asset_root: Path
) -> dict[str, Any]:
    project_root.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "tsconfig.json"):
        source = scaffold_root / name
        destination = project_root / name
        if not destination.exists():
            shutil.copy2(source, destination)
    _ensure_junction(project_root / "node_modules", dependency_root)
    _ensure_junction(project_root / "public" / "assets", asset_root / "assets")
    return {
        "result": "PASS_PROJECT_SCAFFOLD",
        "project_root": str(project_root.resolve()),
        "dependency_root": str(dependency_root.resolve()),
        "asset_root": str(asset_root.resolve()),
    }


def validate_assets(packet: Mapping[str, Any], asset_root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for item in packet.get("rights_assets", []):
        relative = Path(str(item["relative_path"]))
        path = (asset_root / relative).resolve()
        if asset_root.resolve() not in path.parents:
            raise MediaExecutionError(f"asset_path_escape:{item.get('asset_id')}")
        observed = artifact(path)
        if observed["sha256"] != str(item["sha256"]):
            raise MediaExecutionError(f"asset_hash_mismatch:{item.get('asset_id')}")
        records.append({"asset_id": item["asset_id"], **observed})
    return {"result": "PASS_ASSET_HASHES_AND_RIGHTS_BINDING", "assets": records}


def typecheck_project(project_root: Path) -> dict[str, Any]:
    executable = project_root / "node_modules" / ".bin" / (
        "tsc.cmd" if os.name == "nt" else "tsc"
    )
    result = run_command([str(executable), "--noEmit"], cwd=project_root, timeout=300)
    return {"result": "PASS_GENERATED_SOURCE_TYPECHECK", **result}


def render_project(
    *, project_root: Path, output: Path, crf: int, concurrency: int = 2
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    executable = project_root / "node_modules" / ".bin" / (
        "remotion.cmd" if os.name == "nt" else "remotion"
    )
    result = run_command(
        [
            str(executable),
            "render",
            "src/index.tsx",
            "FWBUnattendedShort",
            str(output),
            "--codec=h264",
            f"--crf={int(crf)}",
            "--pixel-format=yuv420p",
            f"--concurrency={max(1, int(concurrency))}",
            "--log=verbose",
        ],
        cwd=project_root,
        timeout=3600,
    )
    return {
        "result": "PASS_RENDER",
        "artifact": artifact(output),
        **result,
    }


def probe_media(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if completed.returncode != 0:
        raise MediaExecutionError(f"ffprobe_failed:{completed.stderr[-4000:]}")
    return json.loads(completed.stdout)


def contact_sheet(video: Path, output: Path, *, count: int = 9) -> dict[str, Any]:
    probe = probe_media(video)
    duration = float(probe["format"]["duration"])
    interval = max(0.5, duration / (count + 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video),
        "-vf",
        f"fps=1/{interval:.6f},scale=360:-1,tile=3x3:padding=6:margin=6",
        "-frames:v",
        "1",
        "-q:v",
        "4",
        str(output),
    ]
    result = run_command(command, timeout=300)
    return {
        "result": "PASS_CONTACT_SHEET",
        "artifact": artifact(output),
        "sample_count": count,
        **result,
    }


def image_data_url(path: Path) -> str:
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _silence(seconds: float, sample_rate: int) -> Any:
    import numpy as np

    return np.zeros(max(1, round(seconds * sample_rate)), dtype=np.float32)


def synthesize_narration(
    *,
    editor: Mapping[str, Any],
    model_path: Path,
    voices_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro

    output_dir.mkdir(parents=True, exist_ok=True)
    intent = dict(editor.get("audio_intent", {}))
    voice = str(intent.get("narration_voice") or "af_heart")
    speed = float(intent.get("speed") or 1.06)
    lang = str(intent.get("lang") or "en-us")
    if (voice, round(speed, 2), lang) != ("af_heart", 1.06, "en-us"):
        raise MediaExecutionError("audio_intent_changed_owner_accepted_voice_route")
    kokoro = Kokoro(str(model_path.resolve()), str(voices_path.resolve()))
    sample_rate = 24_000
    pieces: list[np.ndarray] = [_silence(0.18, sample_rate)]
    placements: list[dict[str, Any]] = []
    cursor = len(pieces[0]) / sample_rate
    for index, segment in enumerate(editor["narration_segments"], start=1):
        text = str(segment["text"])
        generated, returned_rate = kokoro.create(text, voice=voice, speed=speed, lang=lang)
        if int(returned_rate) != sample_rate:
            raise MediaExecutionError(f"kokoro_sample_rate_unexpected:{returned_rate}")
        audio = np.asarray(generated, dtype=np.float32)
        peak = float(np.max(np.abs(audio))) or 1.0
        audio *= min(1.0, 10 ** (-3 / 20) / peak)
        segment_path = output_dir / f"segment_{index:02d}.wav"
        sf.write(segment_path, audio, sample_rate, subtype="PCM_24")
        duration = len(audio) / sample_rate
        placements.append(
            {
                "cue_id": str(segment["segment_id"]),
                "timeline_start_seconds": round(cursor, 6),
                "actual_audio_duration_seconds": round(duration, 6),
                "caption_text": text,
                "audio_path": str(segment_path),
            }
        )
        pieces.append(audio)
        pieces.append(_silence(0.16 if index < len(editor["narration_segments"]) else 0.35, sample_rate))
        cursor += duration + (0.16 if index < len(editor["narration_segments"]) else 0.35)
    narration = np.concatenate(pieces)
    output = output_dir / "narration.wav"
    sf.write(output, narration, sample_rate, subtype="PCM_24")
    return {
        "schema": "contentops.v2.narration_build_receipt.v1",
        "provider": "kokoro-onnx",
        "model": "kokoro-v1.0",
        "voice": voice,
        "speed": speed,
        "lang": lang,
        "sample_rate_hz": sample_rate,
        "duration_seconds": round(len(narration) / sample_rate, 6),
        "placements": placements,
        "artifact": artifact(output),
        "external_cost_usd": 0.0,
    }


def build_audio_mix(
    *,
    picture: Path,
    narration_receipt: Mapping[str, Any],
    bed_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    picture_probe = probe_media(picture)
    picture_duration = float(picture_probe["format"]["duration"])
    narration_duration = float(narration_receipt["duration_seconds"])
    if narration_duration > picture_duration - 0.15:
        raise MediaExecutionError(
            f"narration_exceeds_picture:{narration_duration:.3f}>{picture_duration:.3f}"
        )
    mix = output_dir / "final_mix.wav"
    bed_gain = 0.045
    fade_out_start = max(0.0, picture_duration - 1.5)
    filter_graph = (
        f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0[n];"
        f"[1:a]atrim=0:{picture_duration:.6f},volume={bed_gain},"
        f"afade=t=in:st=0:d=0.7,afade=t=out:st={fade_out_start:.6f}:d=1.5[b];"
        f"[n][b]amix=inputs=2:duration=longest:normalize=0,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[m]"
    )
    mix_result = run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(narration_receipt["artifact"]["path"]),
            "-stream_loop",
            "-1",
            "-i",
            str(bed_path),
            "-filter_complex",
            filter_graph,
            "-map",
            "[m]",
            "-t",
            f"{picture_duration:.6f}",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            str(mix),
        ],
        timeout=600,
    )
    return {
        "result": "PASS_AUDIO_MIX",
        "mix": artifact(mix),
        "mix_execution": mix_result,
    }


def mux_final_media(*, picture: Path, mix: Path, output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    mux_result = run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(picture),
            "-i",
            str(mix),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output),
        ],
        timeout=600,
    )
    return {
        "result": "PASS_FINAL_MUX",
        "final_media": artifact(output),
        "mux_execution": mux_result,
    }


def loudness_report(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-filter_complex",
            "ebur128=peak=true",
            "-f",
            "null",
            "NUL" if os.name == "nt" else "/dev/null",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    text = completed.stdout
    integrated = re.findall(r"I:\s*(-?[0-9.]+)\s+LUFS", text)
    peaks = re.findall(r"Peak:\s*(-?[0-9.]+)\s+dBFS", text)
    if not integrated:
        raise MediaExecutionError("loudness_measurement_missing")
    return {
        "result": "PASS_AUDIO_MEASURED",
        "integrated_lufs": float(integrated[-1]),
        "true_peak_dbfs": float(peaks[-1]) if peaks else None,
    }


def build_captions(
    *, editor: Mapping[str, Any], narration_receipt: Mapping[str, Any], output_dir: Path
) -> dict[str, Any]:
    caption_set = build_caption_cues(
        language="en",
        media_duration_seconds=float(editor["duration_seconds"]),
        segments=narration_receipt["placements"],
    )
    validation = validate_caption_set(caption_set)
    if validation["result"] != "PASS_CAPTIONS":
        raise MediaExecutionError(f"caption_validation_failed:{validation['errors']}")
    return {
        "result": "PASS_CAPTIONS",
        "validation": validation,
        "artifacts": write_caption_artifacts(caption_set, output_dir),
    }


def technical_media_report(path: Path, output: Path) -> dict[str, Any]:
    probe = probe_media(path)
    media_validation = validate_media_probe("SHORT_9_16", probe)
    loudness = loudness_report(path)
    report = {
        "schema": "contentops.v2.unattended_technical_media_report.v1",
        "artifact": artifact(path),
        "probe": probe,
        "media_validation": media_validation,
        "loudness": loudness,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_artifact"] = artifact(output)
    if media_validation["result"] != "PASS_MEDIA_CONTRACT":
        raise MediaExecutionError(f"technical_media_invalid:{media_validation['errors']}")
    return report


def build_neutral_package(
    *,
    story_id: str,
    run_id: str,
    final_media: Path,
    audio: Path,
    captions: Mapping[str, Any],
    rights_refs: Sequence[str],
    evidence_refs: Sequence[str],
    title: str,
    input_hash: str,
    output: Path,
) -> dict[str, Any]:
    artifacts = captions["artifacts"]
    package = build_publication_package(
        {
            "source_story_id": story_id,
            "source_film_id": run_id,
            "format": "SHORT_9_16",
            "language": "en",
            "canonical_picture": str(final_media),
            "burned_caption_video": None,
            "audio": str(audio),
            "caption_json": artifacts["json"]["path"],
            "caption_srt": artifacts["srt"]["path"],
            "caption_vtt": artifacts["vtt"]["path"],
            "metadata": {
                "title": title,
                "description": "Shadow owner-review package. No platform delivery authorized.",
            },
            "chapters": [{"start_seconds": 0, "title": title}],
            "rights_provenance_refs": list(rights_refs),
            "factual_evidence_refs": [input_hash, *evidence_refs],
            "intended_future_surfaces": [],
            "generation_version": "v1",
            "delivery_policy": {
                "picture_render_scope": "ONCE_PER_EDITORIAL_FORMAT",
                "locale_picture_render_default": False,
                "burned_captions": "OPTIONAL_ONLY_EXACT_AUTHORITY_REQUIRED",
                "recurring_locale_creative_xhigh": False,
            },
            "hard_boundaries": {
                "video_public_write_authority": False,
                "v1_mutation_authority": False,
                "scheduler_mutation_authority": False,
                "allow_4k": False,
            },
        }
    )
    package["governed_input_hash"] = input_hash
    package["final_mux"] = artifact(final_media)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    package["manifest_artifact"] = artifact(output)
    return package
