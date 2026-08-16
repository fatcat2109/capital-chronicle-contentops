"""Validate the Frozen Without Breaking multilingual owner-review media.

This task-specific harness is intentionally read-only.  It probes final muxes, validates
native-format and caption contracts, and proves that audio localization did not modify the
accepted longform picture or the shared clean Short picture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

try:
    from .package_factory import validate_caption_set, validate_media_probe
except ImportError:  # direct script execution
    from package_factory import validate_caption_set, validate_media_probe


LOCALES = ("en", "es", "pt-BR", "ja")


def _probe(path: Path, ffprobe: str) -> dict[str, Any]:
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path.resolve()),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def _video_payload_sha256(path: Path, ffmpeg: str) -> str:
    completed = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            str(path.resolve()),
            "-map",
            "0:v:0",
            "-c:v",
            "copy",
            "-bsf:v",
            "h264_mp4toannexb",
            "-f",
            "h264",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    return hashlib.sha256(completed.stdout).hexdigest()


def _caption_validation(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {"path": str(path.resolve()), **validate_caption_set(payload)}


def validate_demo(
    *,
    runtime_root: Path,
    accepted_longform_picture: Path,
    ffmpeg: str,
    ffprobe: str,
) -> dict[str, Any]:
    owner = runtime_root / "renders" / "owner_review"
    media: dict[str, Any] = {}
    errors: list[str] = []

    clean_paths = {
        locale: owner / f"Frozen_Without_Breaking_short_{locale}_clean.mp4"
        for locale in LOCALES
    }
    burned_paths = {
        locale: owner / f"Frozen_Without_Breaking_short_{locale}_burned.mp4"
        for locale in ("es", "pt-BR", "ja")
    }
    longform_es = owner / "Frozen_Without_Breaking_es_1080p_master.mp4"

    for name, path, format_kind in [
        *((f"short_{locale}_clean", path, "SHORT_9_16") for locale, path in clean_paths.items()),
        *((f"short_{locale}_burned", path, "SHORT_9_16") for locale, path in burned_paths.items()),
        ("longform_es", longform_es, "LONGFORM_16_9"),
    ]:
        probe = _probe(path, ffprobe)
        contract = validate_media_probe(format_kind, probe)
        video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
        color = {
            key: video.get(key)
            for key in ("pix_fmt", "color_space", "color_transfer", "color_primaries")
        }
        color_result = (
            "PASS_BT709_MATRIX_YUV420P"
            if video.get("color_space") == "bt709" and video.get("pix_fmt") == "yuv420p"
            else "FAIL_BT709"
        )
        if contract["result"] != "PASS_MEDIA_CONTRACT":
            errors.append(f"{name}:{contract['result']}")
        if not color_result.startswith("PASS_"):
            errors.append(f"{name}:{color_result}")
        media[name] = {
            "path": str(path.resolve()),
            "contract": contract,
            "color": {**color, "result": color_result},
        }

    clean_hashes = {
        locale: _video_payload_sha256(path, ffmpeg) for locale, path in clean_paths.items()
    }
    clean_picture_result = (
        "PASS_UNCHANGED_SHORT_PICTURE"
        if len(set(clean_hashes.values())) == 1
        else "FAIL_SHORT_PICTURE_CHANGED"
    )
    if not clean_picture_result.startswith("PASS_"):
        errors.append(clean_picture_result)

    accepted_hash = _video_payload_sha256(accepted_longform_picture, ffmpeg)
    spanish_hash = _video_payload_sha256(longform_es, ffmpeg)
    longform_picture_result = (
        "PASS_UNCHANGED_ACCEPTED_LONGFORM_PICTURE"
        if accepted_hash == spanish_hash
        else "FAIL_LONGFORM_PICTURE_CHANGED"
    )
    if not longform_picture_result.startswith("PASS_"):
        errors.append(longform_picture_result)

    captions: dict[str, Any] = {}
    for locale in LOCALES:
        for format_name in ("short", "longform"):
            path = (
                runtime_root
                / "audio"
                / locale
                / format_name
                / "captions"
                / f"captions.{locale}.json"
            )
            validation = _caption_validation(path)
            captions[f"{format_name}_{locale}"] = validation
            if validation["result"] != "PASS_CAPTIONS":
                errors.append(f"{format_name}_{locale}:FAIL_CAPTIONS")

    return {
        "schema": "contentops.v2.fwb_multilingual_media_validation.v1",
        "result": "PASS_MULTIFORMAT_MULTILINGUAL_MEDIA" if not errors else "FAIL_MEDIA",
        "media": media,
        "picture_identity": {
            "short_clean": {"result": clean_picture_result, "video_payload_sha256": clean_hashes},
            "longform_spanish": {
                "result": longform_picture_result,
                "accepted_video_payload_sha256": accepted_hash,
                "spanish_video_payload_sha256": spanish_hash,
            },
        },
        "captions": captions,
        "errors": errors,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", required=True, type=Path)
    parser.add_argument("--accepted-longform-picture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = validate_demo(
        runtime_root=args.runtime_root.resolve(),
        accepted_longform_picture=args.accepted_longform_picture.resolve(),
        ffmpeg=args.ffmpeg,
        ffprobe=args.ffprobe,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
