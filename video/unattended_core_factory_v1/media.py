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

from .creative import hash_file, hash_value
from .transcript import synthesis_text_for_segment, validate_seo_transcript_identity


class MediaExecutionError(RuntimeError):
    pass


WINDOWS_SAFE_EXECUTABLE_PATH_MAX = 259
REMOTION_BROWSER_RELATIVE = Path(
    ".remotion/chrome-headless-shell/win64/"
    "chrome-headless-shell-win64/chrome-headless-shell.exe"
)


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


def resolve_remotion_browser_executable(dependency_root: Path) -> Path:
    """Resolve Chrome from the canonical dependency root, never the job projection."""

    root = dependency_root.resolve()
    expected = (root / REMOTION_BROWSER_RELATIVE).resolve()
    cache_root = root / ".remotion" / "chrome-headless-shell"
    matches = (
        sorted({path.resolve() for path in cache_root.rglob("chrome-headless-shell.exe")})
        if cache_root.is_dir()
        else []
    )
    if len(matches) != 1:
        raise MediaExecutionError(
            f"canonical_remotion_browser_identity_invalid:{len(matches)}:{cache_root}"
        )
    candidate = matches[0]
    if expected.is_file() and candidate != expected:
        raise MediaExecutionError("canonical_remotion_browser_expected_identity_mismatch")
    if root not in candidate.parents:
        raise MediaExecutionError("canonical_remotion_browser_path_escape")
    if os.name == "nt" and len(str(candidate)) > WINDOWS_SAFE_EXECUTABLE_PATH_MAX:
        raise MediaExecutionError(
            f"canonical_remotion_browser_path_too_long:{len(str(candidate))}"
        )
    return candidate


def validate_dependency_root(dependency_root: Path) -> dict[str, Any]:
    """Fail fast unless *dependency_root* is the canonical project node_modules.

    This intentionally validates the exact configured root rather than guessing a nested
    directory.  The returned paths are the same execution surface projected into each generated
    Remotion project by :func:`prepare_project`.
    """

    root = dependency_root.resolve()
    if not root.is_dir():
        raise MediaExecutionError(f"dependency_root_directory_missing:{root}")
    if root.name.casefold() != "node_modules":
        nested = root / "node_modules"
        if nested.is_dir():
            raise MediaExecutionError(
                f"dependency_root_is_project_root:use_node_modules:{nested.resolve()}"
            )
        raise MediaExecutionError(
            f"dependency_root_must_be_node_modules_directory:{root}"
        )

    executable_suffix = ".cmd" if os.name == "nt" else ""
    remotion_cli = (root / ".bin" / f"remotion{executable_suffix}").resolve()
    typescript_cli = (root / ".bin" / f"tsc{executable_suffix}").resolve()
    for label, executable in (
        ("remotion_cli", remotion_cli),
        ("typescript_cli", typescript_cli),
    ):
        if root not in executable.parents:
            raise MediaExecutionError(f"dependency_root_{label}_path_escape")
        if not executable.is_file():
            raise MediaExecutionError(
                f"dependency_root_{label}_missing:{executable}"
            )

    browser = resolve_remotion_browser_executable(root)
    return {
        "result": "PASS_REMOTION_DEPENDENCY_ROOT_PREFLIGHT",
        "dependency_root": str(root),
        "root_contract": "PROJECT_NODE_MODULES",
        "remotion_cli": str(remotion_cli),
        "typescript_cli": str(typescript_cli),
        "canonical_browser_executable": str(browser),
        "canonical_browser_path_length": len(str(browser)),
        "windows_safe_executable_path_max": WINDOWS_SAFE_EXECUTABLE_PATH_MAX,
        "suitable_for_project_node_modules_projection": True,
    }


def browser_launch_layout(project_root: Path, dependency_root: Path) -> dict[str, Any]:
    canonical = resolve_remotion_browser_executable(dependency_root)
    relative = canonical.relative_to(dependency_root.resolve())
    projected = project_root.resolve() / "node_modules" / relative
    return {
        "result": "PASS_WINDOWS_SAFE_REMOTION_BROWSER_LAYOUT",
        "canonical_browser_executable": str(canonical),
        "canonical_browser_path_length": len(str(canonical)),
        "canonical_browser_exists": canonical.is_file(),
        "projected_browser_executable": str(projected),
        "projected_browser_path_length": len(str(projected)),
        "projected_browser_exists": projected.is_file(),
        "same_file_identity": projected.is_file() and os.path.samefile(projected, canonical),
        "render_uses_canonical_browser_executable": True,
        "windows_safe_executable_path_max": WINDOWS_SAFE_EXECUTABLE_PATH_MAX,
    }


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
    return {
        "result": "PASS_PROJECT_SCAFFOLD",
        "project_root": str(project_root.resolve()),
        "dependency_root": str(dependency_root.resolve()),
        "asset_root": str(asset_root.resolve()),
        "render_uses_canonical_public_root": True,
        "browser_launch_layout": browser_launch_layout(project_root, dependency_root),
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
    *,
    project_root: Path,
    output: Path,
    crf: int,
    browser_executable: Path,
    public_root: Path,
    composition_id: str = "ContentOpsV2Short",
    entry_point: str = "src/index.tsx",
    concurrency: int = 2,
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    browser = browser_executable.resolve()
    if not browser.is_file():
        raise MediaExecutionError(f"canonical_remotion_browser_missing:{browser}")
    if os.name == "nt" and len(str(browser)) > WINDOWS_SAFE_EXECUTABLE_PATH_MAX:
        raise MediaExecutionError(f"canonical_remotion_browser_path_too_long:{len(str(browser))}")
    public = public_root.resolve()
    if not public.is_dir() or not (public / "assets").is_dir():
        raise MediaExecutionError(f"canonical_public_asset_root_invalid:{public}")
    executable = project_root / "node_modules" / ".bin" / (
        "remotion.cmd" if os.name == "nt" else "remotion"
    )
    result = run_command(
        [
            str(executable),
            "render",
            entry_point,
            composition_id,
            str(output),
            "--codec=h264",
            f"--crf={int(crf)}",
            "--pixel-format=yuv420p",
            f"--concurrency={max(1, int(concurrency))}",
            f"--browser-executable={browser}",
            f"--public-dir={public}",
            "--log=verbose",
        ],
        cwd=project_root,
        timeout=3600,
    )
    return {
        "result": "PASS_RENDER",
        "artifact": artifact(output),
        "browser_executable": str(browser),
        "browser_executable_path_length": len(str(browser)),
        "canonical_public_root": str(public),
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
    initial_silence = 0.18
    pieces: list[np.ndarray] = [_silence(initial_silence, sample_rate)]
    placements: list[dict[str, Any]] = []
    cursor = len(pieces[0]) / sample_rate
    for index, segment in enumerate(editor["narration_segments"], start=1):
        text = str(segment["text"])
        synthesis_text = synthesis_text_for_segment(segment)
        segment_id = str(segment["segment_id"])
        identity = hash_value(
            {
                "provider": "kokoro-onnx",
                "model": "kokoro-v1.0",
                "voice": voice,
                "speed": speed,
                "lang": lang,
                "sample_rate_hz": sample_rate,
                "segment_id": segment_id,
                "text": synthesis_text,
            }
        )
        segment_path = output_dir / f"segment_{index:02d}_{segment_id}.wav"
        identity_path = segment_path.with_suffix(".identity.json")
        audio = None
        if segment_path.is_file() and identity_path.is_file():
            cached = json.loads(identity_path.read_text(encoding="utf-8"))
            if (
                cached.get("identity") == identity
                and cached.get("audio_sha256") == hash_file(segment_path)
            ):
                cached_audio, cached_rate = sf.read(segment_path, dtype="float32")
                if int(cached_rate) == sample_rate:
                    audio = np.asarray(cached_audio, dtype=np.float32)
        synthesis_action = "REUSED_CACHE"
        if audio is None:
            generated, returned_rate = kokoro.create(
                synthesis_text, voice=voice, speed=speed, lang=lang
            )
            if int(returned_rate) != sample_rate:
                raise MediaExecutionError(f"kokoro_sample_rate_unexpected:{returned_rate}")
            audio = np.asarray(generated, dtype=np.float32)
            peak = float(np.max(np.abs(audio))) or 1.0
            audio *= min(1.0, 10 ** (-3 / 20) / peak)
            sf.write(segment_path, audio, sample_rate, subtype="PCM_24")
            identity_path.write_text(
                json.dumps(
                    {
                        "identity": identity,
                        "audio_sha256": hash_file(segment_path),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            synthesis_action = "SYNTHESIZED"
        duration = len(audio) / sample_rate
        pause_after = 0.16 if index < len(editor["narration_segments"]) else 0.35
        audio_record = artifact(segment_path)
        placements.append(
            {
                "cue_id": segment_id,
                "segment_id": segment_id,
                "segment_text_sha256": hash_value(text),
                "synthesis_text_sha256": hash_value(synthesis_text),
                "timeline_start_seconds": round(cursor, 6),
                "actual_audio_duration_seconds": round(duration, 6),
                "timeline_end_seconds": round(cursor + duration, 6),
                "pause_after_seconds": pause_after,
                "caption_text": text,
                "audio_path": str(segment_path.resolve()),
                "audio": audio_record,
                "synthesis_action": synthesis_action,
            }
        )
        pieces.append(audio)
        pieces.append(_silence(pause_after, sample_rate))
        cursor += duration + pause_after
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
        "initial_silence_seconds": initial_silence,
        "placements": placements,
        "artifact": artifact(output),
        "external_cost_usd": 0.0,
    }


def build_audio_mix(
    *,
    picture: Path,
    timing_lock: Mapping[str, Any],
    bed_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    picture_probe = probe_media(picture)
    picture_duration = float(picture_probe["format"]["duration"])
    narration_duration = float(timing_lock["actual_total_narration_duration_seconds"])
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
            str(timing_lock["locked_narration_audio"]["path"]),
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
    *, timing_lock: Mapping[str, Any], media_duration_seconds: float, output_dir: Path
) -> dict[str, Any]:
    transcript = timing_lock.get("canonical_spoken_transcript")
    if not isinstance(transcript, Mapping):
        raise MediaExecutionError("canonical_spoken_transcript_missing_for_captions")
    if transcript.get("locked_narration_audio_sha256") != timing_lock.get(
        "locked_narration_audio", {}
    ).get("sha256"):
        raise MediaExecutionError("caption_transcript_audio_identity_mismatch")
    caption_set = build_caption_cues(
        language="en",
        media_duration_seconds=media_duration_seconds,
        segments=transcript["segments"],
    )
    caption_set["canonical_transcript_hash"] = transcript[
        "canonical_transcript_hash"
    ]
    caption_set["locked_narration_audio_sha256"] = transcript[
        "locked_narration_audio_sha256"
    ]
    validation = validate_caption_set(caption_set)
    if validation["result"] != "PASS_CAPTIONS":
        raise MediaExecutionError(f"caption_validation_failed:{validation['errors']}")
    return {
        "result": "PASS_CAPTIONS",
        "validation": validation,
        "canonical_transcript_hash": transcript["canonical_transcript_hash"],
        "locked_narration_audio_sha256": transcript[
            "locked_narration_audio_sha256"
        ],
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
    input_hash: str,
    timing_lock: Mapping[str, Any],
    seo_package: Mapping[str, Any],
    output: Path,
) -> dict[str, Any]:
    artifacts = captions["artifacts"]
    transcript = dict(timing_lock["canonical_spoken_transcript"])
    validate_seo_transcript_identity(seo_package, transcript=transcript)
    final_audio = artifact(audio)
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
                "title": seo_package["title"],
                "description": seo_package["description"],
                "search_entities": list(seo_package["search_entities"]),
            },
            "chapters": list(seo_package["chapters"]),
            "rights_provenance_refs": list(rights_refs),
            "factual_evidence_refs": [input_hash, *evidence_refs],
            "intended_future_surfaces": [],
            "generation_version": "v1",
            "canonical_transcript_identity": {
                "canonical_transcript_hash": transcript[
                    "canonical_transcript_hash"
                ],
                "plain_text_sha256": transcript["plain_text_sha256"],
                "locked_narration_audio_sha256": transcript[
                    "locked_narration_audio_sha256"
                ],
                "final_audio_sha256": final_audio["sha256"],
                "voiceover_qa_hash": timing_lock["voiceover_qa"][
                    "voiceover_qa_hash"
                ],
            },
            "seo_derivation": {
                "schema": seo_package["schema"],
                "seo_package_hash": seo_package["seo_package_hash"],
                "canonical_transcript_hash": seo_package[
                    "canonical_transcript_hash"
                ],
                "invented_or_strengthened_fact_count": seo_package[
                    "invented_or_strengthened_fact_count"
                ],
            },
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
    package["narration_timing_lock_hash"] = timing_lock["timing_lock_hash"]
    package["canonical_transcript_hash"] = transcript["canonical_transcript_hash"]
    package["voiceover_qa_hash"] = timing_lock["voiceover_qa"]["voiceover_qa_hash"]
    package["seo_package_hash"] = seo_package["seo_package_hash"]
    package["final_mux"] = artifact(final_media)
    package["final_audio"] = final_audio
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    package["manifest_artifact"] = artifact(output)
    return package
