"""Create a short vertical video from ContentOps-owned source-backed charts.

No synthetic image is created. The video is a timed sequence of the supplied
FRED/official-source chart files, sized for a native Short or TikTok upload.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


TASK_LABEL = "TASK_CONTENTOPS_HEAVY_EIGHT_PLATFORM_FULL_PIPELINE_RECOVERY_DEBUG_AND_REAL_LIVE_RUN_V1"
DEFAULT_DURATION_PER_CHART_SECONDS = 5


def find_ffmpeg() -> str | None:
    configured = os.environ.get("CONTENTOPS_FFMPEG_BINARY")
    if configured and Path(configured).exists():
        return configured
    return shutil.which("ffmpeg")


def build_chart_sequence_command(
    *,
    ffmpeg_binary: str,
    chart_paths: Sequence[str | Path],
    output_path: str | Path,
    duration_per_chart_seconds: int = DEFAULT_DURATION_PER_CHART_SECONDS,
) -> list[str]:
    paths = [Path(path).resolve() for path in chart_paths]
    if len(paths) < 3:
        raise ValueError("short_video_requires_at_least_three_source_backed_charts")
    if duration_per_chart_seconds < 2:
        raise ValueError("short_video_duration_per_chart_must_be_at_least_two_seconds")
    command: list[str] = [ffmpeg_binary, "-y"]
    for path in paths:
        command.extend(["-loop", "1", "-framerate", "30", "-t", str(duration_per_chart_seconds), "-i", str(path)])
    filters: list[str] = []
    for index in range(len(paths)):
        filters.append(
            f"[{index}:v]scale=1000:1600:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1"
            f"[chart{index}]"
        )
    concat_inputs = "".join(f"[chart{index}]" for index in range(len(paths)))
    filters.append(f"{concat_inputs}concat=n={len(paths)}:v=1:a=0,format=yuv420p[video]")
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[video]",
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(Path(output_path).resolve()),
        ]
    )
    return command


def build_source_chart_short_video(
    *,
    chart_paths: Sequence[str | Path],
    output_path: str | Path,
    duration_per_chart_seconds: int = DEFAULT_DURATION_PER_CHART_SECONDS,
    ffmpeg_binary: str | None = None,
) -> dict[str, object]:
    paths = [Path(path) for path in chart_paths]
    if len(paths) < 3 or any(not path.exists() for path in paths):
        return {"status": "BLOCKED_SOURCE_CHART_MEDIA_MISSING", "source_chart_count": len(paths)}
    binary = ffmpeg_binary or find_ffmpeg()
    if not binary:
        return {"status": "BLOCKED_FFMPEG_NOT_FOUND", "source_chart_count": len(paths)}
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    command = build_chart_sequence_command(
        ffmpeg_binary=binary,
        chart_paths=paths,
        output_path=target,
        duration_per_chart_seconds=duration_per_chart_seconds,
    )
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
        )
    except Exception as exc:
        return {"status": "FAILED_FFMPEG_EXECUTION", "source_chart_count": len(paths), "error_class": type(exc).__name__}
    if completed.returncode != 0 or not target.exists() or target.stat().st_size < 20_000:
        return {"status": "FAILED_FFMPEG_OUTPUT", "source_chart_count": len(paths), "ffmpeg_exit_code": completed.returncode}
    return {
        "status": "SUCCESS",
        "video_path": str(target),
        "source_chart_count": len(paths),
        "duration_seconds": len(paths) * duration_per_chart_seconds,
        "media_kind": "source_backed_chart_sequence_video",
        "ffmpeg_exit_code": completed.returncode,
        "output_bytes": target.stat().st_size,
        "synthetic_image_generated": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a source-chart short video")
    parser.add_argument("--chart", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = build_source_chart_short_video(chart_paths=args.chart, output_path=args.output)
    print(result)
    return 0 if result.get("status") == "SUCCESS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
