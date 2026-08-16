"""Produce sidecars and a stream-copy localized mux without invoking a renderer."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

try:
    from .package_factory import caption_text, validate_caption_set
except ImportError:  # direct script execution
    from package_factory import caption_text, validate_caption_set


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _video_payload_sha256(path: Path, ffmpeg: str) -> str:
    result = subprocess.run(
        [
            ffmpeg, "-v", "error", "-i", str(path.resolve()), "-map", "0:v:0",
            "-c:v", "copy", "-bsf:v", "h264_mp4toannexb", "-f", "h264", "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    return hashlib.sha256(result.stdout).hexdigest()


def run_proof(
    *,
    picture: Path,
    audio: Path,
    caption_json: Path,
    metadata_source: Path,
    output_root: Path,
    ffmpeg: str = "ffmpeg",
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    captions = json.loads(caption_json.read_text(encoding="utf-8"))
    caption_validation = validate_caption_set(captions)
    if caption_validation["result"] != "PASS_CAPTIONS":
        raise RuntimeError(f"Caption input failed: {caption_validation['errors']}")

    locale = str(captions["language"])
    generated_json = output_root / f"captions.{locale}.json"
    generated_srt = output_root / f"captions.{locale}.srt"
    generated_vtt = output_root / f"captions.{locale}.vtt"
    generated_json.write_text(json.dumps(captions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    generated_srt.write_text(caption_text(captions, kind="srt"), encoding="utf-8")
    generated_vtt.write_text(caption_text(captions, kind="vtt"), encoding="utf-8")

    editorial = json.loads(metadata_source.read_text(encoding="utf-8"))
    format_name = "short" if float(captions["media_duration_seconds"]) <= 60.5 else "longform"
    metadata = {
        key: editorial[format_name][key]
        for key in ("title", "description", "social_copy")
    }
    metadata_path = output_root / f"metadata.{format_name}.{locale}.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    muxed = output_root / f"stream_copy_mux.{format_name}.{locale}.mp4"
    command = [
        ffmpeg, "-hide_banner", "-y", "-i", str(picture.resolve()), "-i", str(audio.resolve()),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
        "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", str(muxed.resolve()),
    ]
    subprocess.run(command, check=True, capture_output=True)
    picture_payload = _video_payload_sha256(picture, ffmpeg)
    mux_payload = _video_payload_sha256(muxed, ffmpeg)
    result = "PASS_ZERO_RERENDER_SIDECARS" if picture_payload == mux_payload else "FAIL_VIDEO_PAYLOAD_CHANGED"
    return {
        "schema": "contentops.v2.zero_rerender_sidecar_proof.v1",
        "result": result,
        "operations": {
            "remotion_video_renders": 0,
            "4k_renders": 0,
            "localized_picture_renders": 0,
            "ffmpeg_stream_copy_muxes": 1,
            "caption_sidecar_writes": 3,
            "metadata_sidecar_writes": 1,
            "public_writes": 0,
            "v1_mutations": 0,
            "scheduler_changes": 0,
            "max_calls": 0,
            "ultra_calls": 0,
        },
        "mux": {
            "command_contract": "-c:v copy",
            "picture_path": str(picture.resolve()),
            "picture_sha256": _sha256(picture),
            "picture_video_payload_sha256": picture_payload,
            "output_path": str(muxed.resolve()),
            "output_sha256": _sha256(muxed),
            "output_video_payload_sha256": mux_payload,
        },
        "captions": {
            "timing_basis": captions.get("timing_basis"),
            "validation": caption_validation,
            "json": str(generated_json.resolve()),
            "srt": str(generated_srt.resolve()),
            "vtt": str(generated_vtt.resolve()),
            "picture_render_required": False,
        },
        "metadata": {
            "path": str(metadata_path.resolve()),
            "picture_render_required": False,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--picture", required=True, type=Path)
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--caption-json", required=True, type=Path)
    parser.add_argument("--metadata-source", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = run_proof(
        picture=args.picture.resolve(),
        audio=args.audio.resolve(),
        caption_json=args.caption_json.resolve(),
        metadata_source=args.metadata_source.resolve(),
        output_root=args.output_root.resolve(),
        ffmpeg=args.ffmpeg,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "PASS_ZERO_RERENDER_SIDECARS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
