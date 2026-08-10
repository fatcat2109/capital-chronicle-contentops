"""Isolated local TTS worker for the Tier-2 local video lane.

The worker is deliberately provider-shaped: the caller supplies text and an output
path, while the selected local model remains replaceable. It performs no network,
credential, or platform work.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence


# Runtime generation is offline. Model acquisition is an explicit setup action.
os.environ.setdefault("HF_HUB_OFFLINE", "1")


def _resource_snapshot() -> dict[str, object]:
    peak_ram_gib = None
    try:
        import psutil  # type: ignore

        peak_ram_gib = round(psutil.Process().memory_info().rss / (1024 ** 3), 4)
    except Exception:
        pass
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            succeeded = ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
            if succeeded:
                peak_ram_gib = round(counters.PeakWorkingSetSize / (1024 ** 3), 4)
        except Exception:
            pass
    try:
        import torch  # type: ignore

        cuda_available = bool(torch.cuda.is_available())
        peak_vram_gib = round(torch.cuda.max_memory_allocated() / (1024 ** 3), 4) if cuda_available else 0.0
    except Exception:
        cuda_available = False
        peak_vram_gib = None
    return {"peak_ram_gib": peak_ram_gib, "cuda_available": cuda_available, "peak_vram_gib": peak_vram_gib}


def generate_kokoro(text: str, output_path: str | Path, *, voice: str = "af_heart", speed: float = 1.0) -> dict[str, object]:
    try:
        from kokoro import KPipeline  # type: ignore
        import soundfile as sf  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised by environment preflight
        raise RuntimeError(f"kokoro_dependencies_unavailable:{type(exc).__name__}") from exc

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="a")
    chunks = []
    for _graphemes, _phonemes, audio in pipeline(text, voice=voice, speed=speed, split_pattern=r"\n+"):
        chunks.append(audio)
    if not chunks:
        raise RuntimeError("kokoro_returned_no_audio")
    try:
        import numpy as np  # type: ignore

        audio = np.concatenate(chunks)
    except Exception as exc:
        raise RuntimeError(f"kokoro_audio_join_failed:{type(exc).__name__}") from exc
    sf.write(str(target), audio, 24000)
    return {
        "provider": "kokoro",
        "model": "Kokoro-82M",
        "voice": voice,
        "language": "en-US",
        "sample_rate": 24000,
        "output_path": str(target),
        "output_bytes": target.stat().st_size,
        **_resource_snapshot(),
        "network_call_performed": False,
        "public_write_performed": False,
    }


def generate_kokoro_batch(request_path: str | Path) -> dict[str, object]:
    request = json.loads(Path(request_path).read_text(encoding="utf-8"))
    if not isinstance(request, dict) or not isinstance(request.get("segments"), list):
        raise ValueError("kokoro_batch_segments_required")
    try:
        from kokoro import KPipeline  # type: ignore
        import numpy as np  # type: ignore
        import soundfile as sf  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised by environment preflight
        raise RuntimeError(f"kokoro_dependencies_unavailable:{type(exc).__name__}") from exc
    pipeline = KPipeline(lang_code="a")
    rows = []
    for segment in request["segments"]:
        target = Path(str(segment["output_path"]))
        target.parent.mkdir(parents=True, exist_ok=True)
        chunks = [audio for _graphemes, _phonemes, audio in pipeline(
            str(segment["text"]),
            voice=str(segment.get("voice") or "af_heart"),
            speed=float(segment.get("speed") or 1.0),
            split_pattern=r"\n+",
        )]
        if not chunks:
            raise RuntimeError("kokoro_returned_no_audio")
        sf.write(str(target), np.concatenate(chunks), 24000)
        rows.append({"output_path": str(target), "output_bytes": target.stat().st_size})
    return {"provider": "kokoro", "model": "Kokoro-82M", "segment_count": len(rows), "segments": rows, **_resource_snapshot(), "network_call_performed": False, "public_write_performed": False}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate one local Kokoro narration segment.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text-file", type=Path)
    source.add_argument("--batch-request", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--voice", default="af_heart")
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args(argv)
    if args.batch_request:
        result = generate_kokoro_batch(args.batch_request)
    else:
        if args.output is None:
            parser.error("--output is required with --text-file")
        result = generate_kokoro(args.text_file.read_text(encoding="utf-8"), args.output, voice=args.voice, speed=args.speed)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
