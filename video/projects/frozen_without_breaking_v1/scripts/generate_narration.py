"""Generate chapter narration locally with the accepted Kokoro ONNX voice.

Input files are plain UTF-8 text under ``narration/chapter_XX.txt``.  A line
containing ``[PAUSE N]`` inserts N seconds of silence.  Blank-line paragraph
breaks receive a short natural pause.  Output is 24 kHz mono WAV plus a small
duration manifest used by the Remotion edit.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "narration"
OUTPUT_DIR = ROOT / "public" / "assets" / "audio" / "narration"
SAMPLE_RATE = 24_000
PAUSE_RE = re.compile(r"^\[PAUSE\s+([0-9]+(?:\.[0-9]+)?)\]$", re.I)


def silence(seconds: float) -> np.ndarray:
    return np.zeros(max(1, round(seconds * SAMPLE_RATE)), dtype=np.float32)


def parse_blocks(text: str) -> list[tuple[str, str | float]]:
    blocks: list[tuple[str, str | float]] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            blocks.append(("speech", " ".join(paragraph).strip()))
            paragraph.clear()

    for raw in text.splitlines():
        line = raw.strip()
        match = PAUSE_RE.match(line)
        if match:
            flush()
            blocks.append(("pause", float(match.group(1))))
        elif not line:
            flush()
            blocks.append(("pause", 0.34))
        elif not line.startswith("#"):
            paragraph.append(line)
    flush()
    return blocks


def speech_chunks(text: str) -> list[str]:
    """Keep ONNX inputs short while preserving the governed narration bytes."""
    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", text)
        if part.strip()
    ]


def synthesize_file(
    kokoro: Kokoro, path: Path, voice: str, speed: float, lang: str
) -> tuple[np.ndarray, int]:
    pieces: list[np.ndarray] = [silence(0.12)]
    word_count = 0
    for kind, value in parse_blocks(path.read_text(encoding="utf-8")):
        if kind == "pause":
            pieces.append(silence(float(value)))
            continue

        text = str(value)
        word_count += len(re.findall(r"\b[\w'-]+\b", text))
        chunks = []
        for chunk_text in speech_chunks(text):
            audio, sample_rate = kokoro.create(
                chunk_text, voice=voice, speed=speed, lang=lang
            )
            if sample_rate != SAMPLE_RATE:
                raise RuntimeError(
                    f"Unexpected Kokoro sample rate {sample_rate}; expected {SAMPLE_RATE}"
                )
            chunks.append(np.asarray(audio, dtype=np.float32))
        for index, chunk in enumerate(chunks):
            pieces.append(chunk)
            if index != len(chunks) - 1:
                pieces.append(silence(0.10))

    pieces.append(silence(0.25))
    audio = np.concatenate(pieces).astype(np.float32)
    peak = float(np.max(np.abs(audio))) or 1.0
    audio *= min(1.0, 10 ** (-3 / 20) / peak)
    return audio, word_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--voice", default="af_heart")
    parser.add_argument("--speed", type=float, default=1.06)
    parser.add_argument("--lang", default="en-us")
    parser.add_argument("--pattern", default="chapter_*.txt")
    args = parser.parse_args()

    files = sorted(INPUT_DIR.glob(args.pattern))
    if not files:
        raise SystemExit(f"No narration inputs matched {INPUT_DIR / args.pattern}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    kokoro = Kokoro(str(args.model.resolve()), str(args.voices.resolve()))
    manifest: dict[str, object] = {
        "engine": "kokoro-onnx 0.4.9 / local CPU",
        "voice": args.voice,
        "speed": args.speed,
        "lang": args.lang,
        "sample_rate_hz": SAMPLE_RATE,
        "chapters": [],
    }

    for path in files:
        audio, word_count = synthesize_file(
            kokoro, path, args.voice, args.speed, args.lang
        )
        out = OUTPUT_DIR / f"{path.stem}.wav"
        sf.write(out, audio, SAMPLE_RATE, subtype="PCM_24")
        seconds = len(audio) / SAMPLE_RATE
        manifest["chapters"].append(
            {
                "id": path.stem,
                "input": str(path.relative_to(ROOT)).replace("\\", "/"),
                "output": str(out.relative_to(ROOT)).replace("\\", "/"),
                "words": word_count,
                "duration_seconds": round(seconds, 3),
                "frames_30fps": round(seconds * 30),
            }
        )
        print(f"{path.name}: {word_count} words, {seconds:.2f}s -> {out}")

    manifest_path = OUTPUT_DIR / "narration_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(manifest_path)


if __name__ == "__main__":
    main()
