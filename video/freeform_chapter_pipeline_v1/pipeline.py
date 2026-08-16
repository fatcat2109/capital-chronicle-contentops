"""Cheap, resumable execution for free-form chapter-authored Remotion films.

This module deliberately has no high-level creative schema.  It treats viewer-facing
Remotion source as an opaque creative artifact and owns only hard validation, hashing,
selective rendering, cache identity, assembly, audio mixing, muxing, and media probes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


class PipelineError(RuntimeError):
    """A hard deterministic production-boundary failure."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _combined_hash(paths: Iterable[Path], payload: Any) -> str:
    digest = hashlib.sha256(_canonical_json(payload))
    for path in sorted({item.resolve() for item in paths}, key=lambda item: str(item).lower()):
        if not path.is_file():
            raise PipelineError(f"Required dependency is missing: {path}")
        digest.update(str(path).encode("utf-8"))
        digest.update(_sha256(path).encode("ascii"))
    return digest.hexdigest()


def _run(command: Sequence[str], cwd: Path, *, dry_run: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    if dry_run:
        return {"command": list(command), "cwd": str(cwd), "wall_seconds": 0.0, "dry_run": True}
    executable = shutil.which(command[0])
    if executable is None:
        raise PipelineError(f"Required executable is unavailable: {command[0]}")
    resolved_command = [executable, *command[1:]]
    completed = subprocess.run(
        resolved_command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    )
    result = {
        "command": list(command),
        "cwd": str(cwd),
        "wall_seconds": round(time.perf_counter() - started, 3),
        "exit_code": completed.returncode,
        "output": completed.stdout,
    }
    if completed.returncode != 0:
        raise PipelineError(
            f"Command failed with exit code {completed.returncode}: {' '.join(command)}\n{completed.stdout}"
        )
    return result


@dataclass(frozen=True)
class RenderProfile:
    name: str
    width: int
    height: int
    crf: int | None
    hardware_acceleration: str = "disable"


PROFILES = {
    "fast": RenderProfile("fast", 1280, 720, 24),
    "fast-hw": RenderProfile("fast-hw", 1280, 720, None, "required"),
    "frame": RenderProfile("frame", 1920, 1080, 18),
    "lock": RenderProfile("lock", 1920, 1080, 14),
}


class FreeformChapterPipeline:
    def __init__(self, manifest_path: Path, workspace: Path | None = None) -> None:
        self.manifest_path = manifest_path.resolve()
        self.repo_root = self.manifest_path.parents[2]
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.project_root = (self.repo_root / self.manifest["project_root"]).resolve()
        self.workspace = (workspace or self.repo_root / ".task-runtime" / "freeform_chapter_pipeline").resolve()
        self.cache_root = self.workspace / "cache"
        self.render_root = self.workspace / "renders"
        self.telemetry_root = self.workspace / "telemetry"
        self._validate_paths()

    def _validate_paths(self) -> None:
        if not self.project_root.is_relative_to(self.repo_root):
            raise PipelineError("Project root must remain within the repository worktree")
        if not self.manifest_path.is_relative_to(self.repo_root):
            raise PipelineError("Manifest must remain within the repository worktree")

    @property
    def chapters(self) -> list[dict[str, Any]]:
        return list(self.manifest["chapters"])

    def chapter(self, chapter_id: str) -> dict[str, Any]:
        for chapter in self.chapters:
            if chapter["id"] == chapter_id:
                return chapter
        raise PipelineError(f"Unknown chapter: {chapter_id}")

    def validate(self) -> dict[str, Any]:
        contract = self.manifest.get("format_contract", {})
        orchestration = self.manifest.get("model_orchestration", {})
        hard = self.manifest.get("hard_boundaries", {})
        errors: list[str] = []

        if self.manifest.get("schema") != "contentops.v2.freeform_chapter_film.v1":
            errors.append("unsupported schema")
        if contract.get("width") != 1920 or contract.get("height") != 1080:
            errors.append("longform must be 1920x1080")
        if contract.get("fps") != 30:
            errors.append("longform must be 30 fps")
        duration = float(contract.get("duration_seconds", 0))
        if not 300 <= duration <= 2700:
            errors.append("longform duration must be 5:00-45:00")
        if contract.get("color") != "bt709_limited_yuv420p":
            errors.append("final color contract must be BT.709 limited yuv420p")
        if orchestration.get("parent") != "gpt-5.6-sol/high":
            errors.append("parent coordinator must be GPT-5.6 Sol HIGH")
        if orchestration.get("creative_workers") != "gpt-5.6-sol/xhigh":
            errors.append("creative workers must be GPT-5.6 Sol XHIGH")
        forbidden = {str(item).lower() for item in orchestration.get("forbidden_modes", [])}
        if not {"max", "ultra"}.issubset(forbidden):
            errors.append("MAX and ULTRA must both be forbidden")
        if hard.get("video_public_write_authority") is not False:
            errors.append("ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY is required")
        if hard.get("v1_mutation_authority") is not False:
            errors.append("V1 mutation authority must be false")
        if hard.get("allow_4k") is not False:
            errors.append("4K must be disabled")
        if not self.project_root.is_dir():
            errors.append(f"project root is missing: {self.project_root}")
        if not (self.project_root / self.manifest["entry"]).is_file():
            errors.append("Remotion entry is missing")

        chapter_frames = sum(int(chapter["duration_frames"]) for chapter in self.chapters)
        expected_frames = round(duration * int(contract.get("fps", 0)))
        if abs(chapter_frames - expected_frames) > 2:
            errors.append(f"chapter frames {chapter_frames} do not match declared duration {expected_frames}")
        if len({chapter["id"] for chapter in self.chapters}) != len(self.chapters):
            errors.append("chapter IDs must be unique")

        if errors:
            raise PipelineError("; ".join(errors))
        return {
            "result": "PASS_HARD_CONTRACT",
            "chapters": len(self.chapters),
            "frames": chapter_frames,
            "duration_seconds": duration,
            "public_write_authority": False,
            "v1_mutation_authority": False,
            "allow_4k": False,
        }

    def _dependency_paths(self, chapter: dict[str, Any]) -> list[Path]:
        dependencies = list(self.manifest.get("shared_source_files", []))
        dependencies.extend(chapter.get("source_files", []))
        dependencies.extend(chapter.get("asset_files", []))
        dependencies.append("package-lock.json")
        return [(self.project_root / item).resolve() for item in dependencies]

    def chapter_cache_key(self, chapter_id: str, profile: str = "lock", concurrency: int = 2) -> str:
        chapter = self.chapter(chapter_id)
        render_profile = PROFILES[profile]
        payload = {
            "schema": "contentops.v2.chapter_picture_cache.v1",
            "chapter": chapter,
            "profile": render_profile.__dict__,
            "concurrency": concurrency,
            "entry": self.manifest["entry"],
            "picture_only": True,
        }
        return _combined_hash(self._dependency_paths(chapter), payload)

    def bundle_cache_key(self) -> str:
        dependencies: set[Path] = set()
        for chapter in self.chapters:
            dependencies.update(self._dependency_paths(chapter))
        for relative in ("package.json", "tsconfig.json", "remotion.config.ts"):
            candidate = self.project_root / relative
            if candidate.is_file():
                dependencies.add(candidate)
        return _combined_hash(
            dependencies,
            {
                "schema": "contentops.v2.remotion_prepared_bundle.v1",
                "entry": self.manifest["entry"],
            },
        )

    def prepare_bundle(self, *, force: bool = False, dry_run: bool = False) -> dict[str, Any]:
        """Build once and reuse the exact prepared Remotion bundle for a render batch."""
        self.validate()
        key = self.bundle_cache_key()
        output = self.workspace / "bundles" / key[:16]
        ledger_path = self.workspace / "cache" / "prepared_bundle.json"
        ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {}
        if (
            not force
            and ledger.get("key") == key
            and Path(ledger.get("output", "")).joinpath("index.html").is_file()
        ):
            return {"kind": "prepared_bundle", "cache": "HIT", **ledger}
        output.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "npx",
            "--no-install",
            "remotion",
            "bundle",
            self.manifest["entry"],
            "--out-dir",
            str(output),
            "--public-dir",
            "public",
            "--bundle-cache",
        ]
        result = _run(command, self.project_root, dry_run=dry_run)
        if dry_run:
            return {"kind": "prepared_bundle", "cache": "MISS", "key": key, **result}
        record = {
            "key": key,
            "output": str(output),
            "index_sha256": _sha256(output / "index.html"),
            "bundle_wall_seconds": result["wall_seconds"],
        }
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return {"kind": "prepared_bundle", "cache": "MISS", **record}

    def render_command(
        self,
        chapter_id: str,
        output: Path,
        *,
        profile: str,
        concurrency: int,
        frame_range: tuple[int, int] | None = None,
        codec: str = "h264",
        bundle: Path | None = None,
    ) -> list[str]:
        if profile not in PROFILES:
            raise PipelineError(f"Unknown render profile: {profile}")
        if not 1 <= concurrency <= 32:
            raise PipelineError("Concurrency must be within 1-32")
        chapter = self.chapter(chapter_id)
        render_profile = PROFILES[profile]
        command = [
            "npx",
            "--no-install",
            "remotion",
            "render",
            str(bundle.resolve()) if bundle is not None else self.manifest["entry"],
            chapter["composition"],
            str(output),
            "--codec",
            codec,
            "--width",
            str(render_profile.width),
            "--height",
            str(render_profile.height),
            "--pixel-format",
            "yuv420p",
            "--concurrency",
            str(concurrency),
            "--muted",
            "--overwrite",
        ]
        if render_profile.crf is not None:
            command.extend(["--crf", str(render_profile.crf)])
        if render_profile.hardware_acceleration != "disable":
            command.extend(
                ["--hardware-acceleration", render_profile.hardware_acceleration]
            )
        if frame_range is not None:
            start, end = frame_range
            if start < 0 or end < start or end >= int(chapter["duration_frames"]):
                raise PipelineError("Frame range must be within the creative chapter")
            command.extend(["--frames", f"{start}-{end}"])
        return command

    def render_range(
        self,
        chapter_id: str,
        start_frame: int,
        end_frame: int,
        output: Path,
        *,
        profile: str = "fast",
        concurrency: int = 2,
        bundle: Path | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        self.validate()
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        command = self.render_command(
            chapter_id,
            output,
            profile=profile,
            concurrency=concurrency,
            frame_range=(start_frame, end_frame),
            bundle=bundle,
        )
        result = _run(command, self.project_root, dry_run=dry_run)
        result.update({"kind": "dirty_range", "chapter": chapter_id, "frames": [start_frame, end_frame]})
        return result

    def render_chapter(
        self,
        chapter_id: str,
        *,
        profile: str = "lock",
        concurrency: int = 2,
        force: bool = False,
        bundle: Path | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        self.validate()
        key = self.chapter_cache_key(chapter_id, profile, concurrency)
        output = self.render_root / "chapters" / f"{chapter_id}_{key[:12]}.mp4"
        ledger_path = self.cache_root / "chapter_picture_cache.json"
        ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {}
        cached = ledger.get(chapter_id)
        if not force and cached and cached.get("key") == key and Path(cached["output"]).is_file():
            return {"kind": "chapter_lock", "chapter": chapter_id, "cache": "HIT", **cached}

        output.parent.mkdir(parents=True, exist_ok=True)
        command = self.render_command(
            chapter_id, output, profile=profile, concurrency=concurrency, bundle=bundle
        )
        result = _run(command, self.project_root, dry_run=dry_run)
        if dry_run:
            return {"kind": "chapter_lock", "chapter": chapter_id, "cache": "MISS", "key": key, **result}
        probe = self.probe(output)
        record = {
            "key": key,
            "output": str(output),
            "sha256": _sha256(output),
            "probe": probe,
            "render_wall_seconds": result["wall_seconds"],
        }
        ledger[chapter_id] = record
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        return {"kind": "chapter_lock", "chapter": chapter_id, "cache": "MISS", **record}

    def probe(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise PipelineError(f"Media file is missing: {path}")
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=index,codec_name,codec_type,width,height,r_frame_rate,pix_fmt,color_range,color_space,color_transfer,color_primaries,sample_rate,channels,bit_rate",
            "-of",
            "json",
            str(path),
        ]
        completed = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if completed.returncode != 0:
            raise PipelineError(f"ffprobe failed for {path}: {completed.stderr}")
        return json.loads(completed.stdout)

    def assemble(self, chapter_files: Sequence[Path], output: Path, *, dry_run: bool = False) -> dict[str, Any]:
        if len(chapter_files) != len(self.chapters):
            raise PipelineError("Assembly requires exactly one locked picture file per creative chapter")
        probes = [self.probe(path.resolve()) for path in chapter_files]
        stream_locks = []
        for probe in probes:
            video = next((item for item in probe["streams"] if item.get("codec_type") == "video"), None)
            if video is None:
                raise PipelineError("Chapter is missing a video stream")
            stream_locks.append(
                (video.get("codec_name"), video.get("width"), video.get("height"), video.get("r_frame_rate"), video.get("pix_fmt"))
            )
        if len(set(stream_locks)) != 1:
            raise PipelineError(f"Chapter video streams are not concat-compatible: {stream_locks}")
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        concat_file = self.workspace / "assembly" / "chapters.txt"
        concat_file.parent.mkdir(parents=True, exist_ok=True)
        lines = ["file '" + str(path.resolve()).replace("'", "'\\''") + "'" for path in chapter_files]
        concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        command = ["ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output)]
        result = _run(command, self.project_root, dry_run=dry_run)
        if dry_run:
            return {"kind": "picture_assembly", "method": "concat_streamcopy", **result}
        return {
            "kind": "picture_assembly",
            "method": "concat_streamcopy",
            "output": str(output),
            "sha256": _sha256(output),
            "probe": self.probe(output),
            "wall_seconds": result["wall_seconds"],
        }

    def mix_audio(self, plan_path: Path, output: Path, *, dry_run: bool = False) -> dict[str, Any]:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        stems = list(plan.get("stems", []))
        if not stems:
            raise PipelineError("Audio edit plan contains no stems")
        command = ["ffmpeg", "-hide_banner", "-y"]
        filters: list[str] = []
        mix_inputs: list[str] = []
        for index, stem in enumerate(stems):
            source = Path(stem["path"]).resolve()
            if not source.is_file():
                raise PipelineError(f"Audio stem is missing: {source}")
            command.extend(["-i", str(source)])
            chain = [f"[{index}:a]aresample=48000", "aformat=sample_fmts=fltp:channel_layouts=stereo"]
            if stem.get("trim_start_seconds") is not None or stem.get("trim_end_seconds") is not None:
                start = float(stem.get("trim_start_seconds", 0))
                end = stem.get("trim_end_seconds")
                trim = f"atrim=start={start}"
                if end is not None:
                    trim += f":end={float(end)}"
                chain.extend([trim, "asetpts=PTS-STARTPTS"])
            gain_db = float(stem.get("gain_db", 0))
            if gain_db:
                chain.append(f"volume={gain_db}dB")
            if stem.get("fade_in_seconds"):
                chain.append(f"afade=t=in:st=0:d={float(stem['fade_in_seconds'])}")
            if stem.get("fade_out_seconds"):
                duration = float(stem["duration_seconds"])
                fade = float(stem["fade_out_seconds"])
                chain.append(f"afade=t=out:st={max(0, duration - fade)}:d={fade}")
            delay_ms = round(float(stem.get("timeline_start_seconds", 0)) * 1000)
            chain.append(f"adelay={delay_ms}|{delay_ms}")
            label = f"a{index}"
            filters.append(",".join(chain) + f"[{label}]")
            mix_inputs.append(f"[{label}]")
        duration = float(plan["duration_seconds"])
        filters.append(
            "".join(mix_inputs)
            + f"amix=inputs={len(stems)}:duration=longest:normalize=0,atrim=duration={duration},aresample=48000"
            + ",alimiter=limit=0.84:attack=5:release=100[final]"
        )
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        command.extend(["-filter_complex", ";".join(filters), "-map", "[final]", "-c:a", "pcm_s24le", str(output)])
        result = _run(command, self.project_root, dry_run=dry_run)
        if dry_run:
            return {"kind": "audio_only_build", "video_render_invoked": False, **result}
        return {
            "kind": "audio_only_build",
            "video_render_invoked": False,
            "output": str(output),
            "sha256": _sha256(output),
            "probe": self.probe(output),
            "wall_seconds": result["wall_seconds"],
        }

    def mux(self, picture: Path, audio: Path, output: Path, *, dry_run: bool = False) -> dict[str, Any]:
        self.probe(picture.resolve())
        self.probe(audio.resolve())
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            str(picture.resolve()),
            "-i",
            str(audio.resolve()),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output),
        ]
        result = _run(command, self.project_root, dry_run=dry_run)
        if dry_run:
            return {"kind": "final_mux", "video_render_invoked": False, **result}
        return {
            "kind": "final_mux",
            "video_render_invoked": False,
            "output": str(output),
            "sha256": _sha256(output),
            "probe": self.probe(output),
            "wall_seconds": result["wall_seconds"],
        }


def _default_manifest() -> Path:
    return Path(__file__).resolve().with_name("frozen_without_breaking.manifest.json")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=_default_manifest())
    parser.add_argument("--workspace", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    bundle_parser = sub.add_parser("prepare-bundle")
    bundle_parser.add_argument("--force", action="store_true")
    bundle_parser.add_argument("--dry-run", action="store_true")

    range_parser = sub.add_parser("render-range")
    range_parser.add_argument("chapter")
    range_parser.add_argument("start", type=int)
    range_parser.add_argument("end", type=int)
    range_parser.add_argument("output", type=Path)
    range_parser.add_argument("--profile", choices=sorted(PROFILES), default="fast")
    range_parser.add_argument("--concurrency", type=int, default=2)
    range_parser.add_argument("--bundle", type=Path)
    range_parser.add_argument("--dry-run", action="store_true")

    chapter_parser = sub.add_parser("render-chapter")
    chapter_parser.add_argument("chapter")
    chapter_parser.add_argument("--profile", choices=sorted(PROFILES), default="lock")
    chapter_parser.add_argument("--concurrency", type=int, default=2)
    chapter_parser.add_argument("--force", action="store_true")
    chapter_parser.add_argument("--bundle", type=Path)
    chapter_parser.add_argument("--dry-run", action="store_true")

    assemble_parser = sub.add_parser("assemble")
    assemble_parser.add_argument("output", type=Path)
    assemble_parser.add_argument("chapters", nargs="+", type=Path)
    assemble_parser.add_argument("--dry-run", action="store_true")

    mix_parser = sub.add_parser("mix-audio")
    mix_parser.add_argument("plan", type=Path)
    mix_parser.add_argument("output", type=Path)
    mix_parser.add_argument("--dry-run", action="store_true")

    mux_parser = sub.add_parser("mux")
    mux_parser.add_argument("picture", type=Path)
    mux_parser.add_argument("audio", type=Path)
    mux_parser.add_argument("output", type=Path)
    mux_parser.add_argument("--dry-run", action="store_true")

    probe_parser = sub.add_parser("probe")
    probe_parser.add_argument("path", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    pipeline = FreeformChapterPipeline(args.manifest, args.workspace)
    if args.command == "validate":
        result = pipeline.validate()
    elif args.command == "prepare-bundle":
        result = pipeline.prepare_bundle(force=args.force, dry_run=args.dry_run)
    elif args.command == "render-range":
        result = pipeline.render_range(
            args.chapter,
            args.start,
            args.end,
            args.output,
            profile=args.profile,
            concurrency=args.concurrency,
            bundle=args.bundle,
            dry_run=args.dry_run,
        )
    elif args.command == "render-chapter":
        result = pipeline.render_chapter(
            args.chapter,
            profile=args.profile,
            concurrency=args.concurrency,
            force=args.force,
            bundle=args.bundle,
            dry_run=args.dry_run,
        )
    elif args.command == "assemble":
        result = pipeline.assemble(args.chapters, args.output, dry_run=args.dry_run)
    elif args.command == "mix-audio":
        result = pipeline.mix_audio(args.plan, args.output, dry_run=args.dry_run)
    elif args.command == "mux":
        result = pipeline.mux(args.picture, args.audio, args.output, dry_run=args.dry_run)
    else:
        result = pipeline.probe(args.path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
