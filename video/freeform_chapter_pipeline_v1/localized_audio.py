"""Build local multilingual narration, captions, and reusable language audio buses.

Creative/editorial text is an input. This module performs only deterministic local
Kokoro synthesis, measured-duration placement, caption emission, and bus assembly.
It never translates, clones a voice, renders picture, or contacts a platform.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

try:
    from .build_authored_audio import SR, db, duck_envelope, filter_audio
    from .package_factory import build_caption_cues, write_caption_artifacts
except ImportError:  # direct script execution
    from build_authored_audio import SR, db, duck_envelope, filter_audio
    from package_factory import build_caption_cues, write_caption_artifacts


KOKORO_SR = 24_000
SYNTHESIS_REVISION = "kokoro-direct-misaki-ja-with-bounded-clause-fallback-v3"
LATIN_SYNTHESIS_REVISION = "kokoro-direct-with-bounded-clause-fallback-v2"
_JA_G2P: Any = None
FILM_DURATION = 25_451 / 30
SHORT_DURATION = 58.0
SHORT_PREFERRED_STARTS = (0.22, 4.4, 10.333333, 17.833333, 22.733333, 30.666667, 35.266667, 41.6, 48.5, 52.5)
CHAPTER_STARTS = {
    "chapter_01": 0.0,
    "chapter_02": 120.5,
    "chapter_03": 240.966667,
    "chapter_04": 369.833333,
    "chapter_05": 473.933333,
    "chapter_06": 582.066667,
    "chapter_07": 688.433333,
}
PAUSE_RE = re.compile(r"^\[PAUSE\s+([0-9]+(?:\.[0-9]+)?)\]$", re.I)


class LocalizedAudioError(RuntimeError):
    pass


@dataclass(frozen=True)
class MeasuredSegment:
    cue_id: str
    text: str
    caption_text: str
    timeline_start_seconds: float
    actual_audio_duration_seconds: float
    audio_path: str
    speaker: str = "NARRATOR"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def silence(seconds: float, rate: int = KOKORO_SR) -> np.ndarray:
    return np.zeros(max(1, round(seconds * rate)), dtype=np.float32)


def speech_chunks(text: str) -> list[str]:
    return [
        value.strip()
        for value in re.split(r"(?<=[.!?。！？])\s*", text)
        if value.strip()
    ]


def narrative_events(text: str) -> list[tuple[str, str | float]]:
    events: list[tuple[str, str | float]] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            for sentence in speech_chunks(" ".join(paragraph).strip()):
                events.append(("speech", sentence))
            paragraph.clear()

    for raw in text.splitlines():
        line = raw.strip()
        pause = PAUSE_RE.match(line)
        if pause:
            flush()
            events.append(("pause", float(pause.group(1))))
        elif not line:
            flush()
            events.append(("pause", 0.28))
        elif not line.startswith("#"):
            paragraph.append(line)
    flush()
    return events


def synthesize(kokoro: Kokoro, text: str, *, voice: str, speed: float, lang: str) -> np.ndarray:
    def create_part(value: str) -> tuple[np.ndarray, int]:
        global _JA_G2P
        if lang == "ja":
            if _JA_G2P is None:
                from misaki import ja

                _JA_G2P = ja.JAG2P()
            phonemes, _ = _JA_G2P(value)
            return kokoro.create(
                phonemes, voice=voice, speed=speed, lang=lang, is_phonemes=True
            )
        return kokoro.create(value, voice=voice, speed=speed, lang=lang)

    try:
        audio, sample_rate = create_part(text)
        pieces = [np.asarray(audio, dtype=np.float32)]
    except IndexError:
        # The ONNX voice table has a hard token ceiling. Preserve the authored text
        # byte-for-byte while splitting only at bounded punctuation/character edges.
        clauses: list[str] = []
        for sentence in speech_chunks(text):
            remainder = sentence
            while len(remainder) > 100:
                boundary = max(
                    remainder.rfind(mark, 0, 101)
                    for mark in (" ", "、", "，", ",", "；", ";", "：", ":")
                )
                if boundary < 35:
                    boundary = 100
                clauses.append(remainder[:boundary].strip())
                remainder = remainder[boundary:].strip()
            if remainder:
                clauses.append(remainder)
        pieces = []
        sample_rate = KOKORO_SR
        for index, clause in enumerate(clauses):
            part, part_rate = create_part(clause)
            if part_rate != KOKORO_SR:
                raise LocalizedAudioError(f"Unexpected Kokoro sample rate {part_rate}")
            pieces.append(np.asarray(part, dtype=np.float32))
            if index != len(clauses) - 1:
                pieces.append(silence(0.055))
    if sample_rate != KOKORO_SR:
        raise LocalizedAudioError(f"Unexpected Kokoro sample rate {sample_rate}")
    result = np.concatenate(pieces)
    peak = float(np.max(np.abs(result))) or 1.0
    return result * min(1.0, db(-3) / peak)


def to_stereo_48k(audio: np.ndarray) -> np.ndarray:
    # Kokoro's 24 kHz output converts exactly by linear midpoint insertion.  FFmpeg
    # performs the final delivery conversion; this bus representation is adequate
    # for deterministic placement and is subsequently high-pass filtered.
    out = np.empty(len(audio) * 2, dtype=np.float32)
    out[0::2] = audio
    out[1:-1:2] = (audio[:-1] + audio[1:]) * 0.5
    out[-1] = audio[-1]
    return np.column_stack((out, out))


def place(bus: np.ndarray, clip: np.ndarray, at_seconds: float) -> None:
    start = round(at_seconds * SR)
    end = min(len(bus), start + len(clip))
    if start < 0 or start >= len(bus) or end <= start:
        raise LocalizedAudioError(f"Placement outside bus at {at_seconds:.3f}s")
    bus[start:end] += clip[: end - start]


def _write_segment(path: Path, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, audio, KOKORO_SR, subtype="PCM_24")


def synthesize_cached(
    kokoro: Kokoro,
    text: str,
    *,
    voice: str,
    speed: float,
    lang: str,
    path: Path,
) -> np.ndarray:
    synthesis_revision = SYNTHESIS_REVISION if lang == "ja" else LATIN_SYNTHESIS_REVISION
    identity = hashlib.sha256(
        json.dumps(
            {"text": text, "voice": voice, "speed": speed, "lang": lang, "synthesis_revision": synthesis_revision},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    identity_path = path.with_suffix(".identity.json")
    if path.is_file() and identity_path.is_file():
        existing = json.loads(identity_path.read_text(encoding="utf-8"))
        if existing.get("identity") == identity and existing.get("audio_sha256") == sha256(path):
            audio, rate = sf.read(path, dtype="float32")
            if rate == KOKORO_SR:
                return np.asarray(audio, dtype=np.float32)
    audio = synthesize(kokoro, text, voice=voice, speed=speed, lang=lang)
    _write_segment(path, audio)
    identity_path.write_text(
        json.dumps({"identity": identity, "audio_sha256": sha256(path)}, indent=2) + "\n",
        encoding="utf-8",
    )
    return audio


def _write_sample(segments: list[MeasuredSegment], output: Path) -> dict[str, Any]:
    selected: list[np.ndarray] = []
    total = 0.0
    for segment in segments:
        audio, rate = sf.read(segment.audio_path, dtype="float32")
        if rate != KOKORO_SR:
            raise LocalizedAudioError("Voice sample segment rate mismatch")
        if total >= 20:
            break
        selected.extend((audio, silence(0.16)))
        total += len(audio) / rate + 0.16
    sample = np.concatenate(selected)
    if len(sample) / KOKORO_SR > 30:
        sample = sample[: round(30 * KOKORO_SR)]
    sf.write(output, sample, KOKORO_SR, subtype="PCM_24")
    return {"path": str(output.resolve()), "sha256": sha256(output), "duration_seconds": len(sample) / KOKORO_SR}


def build_short(
    *,
    kokoro: Kokoro,
    package: dict[str, Any],
    output_dir: Path,
    voice: str,
    speed: float,
    lang: str,
) -> dict[str, Any]:
    segments_dir = output_dir / "short" / "segments"
    bus = np.zeros((round(SHORT_DURATION * SR), 2), dtype=np.float32)
    measured: list[MeasuredSegment] = []
    cursor = 0.22
    for index, item in enumerate(package["short"]["narration_segments"], start=1):
        cursor = max(cursor, SHORT_PREFERRED_STARTS[index - 1])
        cue_id = str(item.get("id") or f"caption.{index:02d}")
        spoken = str(item["text"]).strip()
        segment_path = segments_dir / f"{index:02d}_{cue_id.replace('.', '_')}.wav"
        clip = synthesize_cached(
            kokoro, spoken, voice=voice, speed=speed, lang=lang, path=segment_path
        )
        duration = len(clip) / KOKORO_SR
        if cursor + duration > SHORT_DURATION - 0.35:
            raise LocalizedAudioError(
                f"Short narration exceeds 58 seconds at speed={speed}; "
                f"{cue_id} ends at {cursor + duration:.3f}s"
            )
        place(bus, to_stereo_48k(clip), cursor)
        measured.append(
            MeasuredSegment(
                cue_id=cue_id,
                text=spoken,
                caption_text=str(item.get("caption_text") or spoken).strip(),
                timeline_start_seconds=round(cursor, 6),
                actual_audio_duration_seconds=round(duration, 6),
                audio_path=str(segment_path.resolve()),
            )
        )
        cursor += duration + 0.14
    bus = filter_audio(bus, high_pass=70)
    narration_path = output_dir / "short" / "narration.wav"
    narration_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(narration_path, bus, SR, subtype="PCM_24")
    caption_set = build_caption_cues(
        language=str(package["locale"]),
        media_duration_seconds=SHORT_DURATION,
        segments=[asdict(item) for item in measured],
    )
    caption_paths = write_caption_artifacts(caption_set, output_dir / "short" / "captions")
    sample = _write_sample(measured, output_dir / "voice_sample.wav")
    return {
        "narration": {"path": str(narration_path.resolve()), "sha256": sha256(narration_path)},
        "segments": [asdict(item) for item in measured],
        "captions": caption_paths,
        "voice_sample": sample,
        "spoken_end_seconds": round(cursor - 0.14, 6),
    }


def build_preflight_sample(
    *,
    kokoro: Kokoro,
    package: dict[str, Any],
    output_dir: Path,
    voice: str,
    speed: float,
    lang: str,
) -> dict[str, Any]:
    measured: list[MeasuredSegment] = []
    cursor = 0.0
    for index, item in enumerate(package["short"]["narration_segments"], start=1):
        if cursor >= 20:
            break
        spoken = str(item["text"]).strip()
        path = output_dir / "preflight_segments" / f"{index:02d}.wav"
        clip = synthesize_cached(
            kokoro, spoken, voice=voice, speed=speed, lang=lang, path=path
        )
        duration = len(clip) / KOKORO_SR
        measured.append(
            MeasuredSegment(
                cue_id=str(item.get("id") or f"caption.{index:02d}"),
                text=spoken,
                caption_text=str(item.get("caption_text") or spoken),
                timeline_start_seconds=cursor,
                actual_audio_duration_seconds=duration,
                audio_path=str(path.resolve()),
            )
        )
        cursor += duration + 0.16
    result = _write_sample(measured, output_dir / "voice_sample_preflight.wav")
    result["status"] = "PENDING_HUMAN_LISTENING_NOT_OWNER_ACCEPTED"
    result["voice"] = voice
    result["language_alias"] = lang
    result["speed"] = speed
    return result


def _load_bus(path: Path, wanted: int) -> np.ndarray:
    audio, rate = sf.read(path, dtype="float32", always_2d=True)
    if rate != SR or audio.shape[1] != 2:
        raise LocalizedAudioError(f"Expected 48 kHz stereo bus: {path}")
    result = np.zeros((wanted, 2), dtype=np.float32)
    result[: min(wanted, len(audio))] = audio[:wanted]
    return result


def build_longform(
    *,
    kokoro: Kokoro,
    package: dict[str, Any],
    output_dir: Path,
    voice: str,
    speed: float,
    lang: str,
    accepted_audio_dir: Path,
) -> dict[str, Any]:
    total = round(FILM_DURATION * SR)
    narration = np.zeros((total, 2), dtype=np.float32)
    measured: list[MeasuredSegment] = []
    chapters = package["longform"]["narration_chapters"]
    chapter_ids = list(CHAPTER_STARTS)
    for chapter_index, chapter_id in enumerate(chapter_ids, start=1):
        cursor = CHAPTER_STARTS[chapter_id]
        window_end = CHAPTER_STARTS.get(
            chapter_ids[chapter_index], FILM_DURATION - 1.0
        ) if chapter_index < len(chapter_ids) else FILM_DURATION - 1.0
        speech_index = 0
        for kind, value in narrative_events(str(chapters[chapter_id])):
            if kind == "pause":
                pause = float(value)
                if pause >= 15 and chapter_id == "chapter_01":
                    cursor = max(cursor, 16.1)
                elif pause >= 15 and chapter_id == "chapter_07":
                    cursor = max(cursor, 737.95)
                else:
                    cursor += pause
                continue
            speech_index += 1
            spoken = str(value)
            segment_path = output_dir / "longform" / "segments" / f"{chapter_id}_{speech_index:02d}.wav"
            clip = synthesize_cached(
                kokoro, spoken, voice=voice, speed=speed, lang=lang, path=segment_path
            )
            duration = len(clip) / KOKORO_SR
            if cursor + duration > window_end:
                raise LocalizedAudioError(
                    f"{chapter_id} exceeds its picture window at speed={speed}: "
                    f"{cursor + duration:.3f}s > {window_end:.3f}s"
                )
            place(narration, to_stereo_48k(clip), cursor)
            measured.append(
                MeasuredSegment(
                    cue_id=f"{chapter_id}.{speech_index:02d}",
                    text=spoken,
                    caption_text=spoken,
                    timeline_start_seconds=round(cursor, 6),
                    actual_audio_duration_seconds=round(duration, 6),
                    audio_path=str(segment_path.resolve()),
                )
            )
            cursor += duration + 0.10
    narration = filter_audio(narration, high_pass=70)
    narration_path = output_dir / "longform" / "narration_bus.wav"
    narration_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(narration_path, narration, SR, subtype="PCM_24")

    authority = _load_bus(accepted_audio_dir / "authority_bus.wav", total)
    music = _load_bus(accepted_audio_dir / "music_bus.wav", total)
    designed = _load_bus(accepted_audio_dir / "designed_bus.wav", total)
    narr_duck = duck_envelope(narration)
    auth_duck = duck_envelope(authority)
    music *= np.power(10, (-3.5 * narr_duck - 5.5 * auth_duck) / 20)[:, None]
    designed *= np.power(10, (-2.0 * narr_duck) / 20)[:, None]
    premaster = narration + authority + music + designed
    premaster[-round(2 * SR):] = 0
    premaster_path = output_dir / "longform" / "premaster.wav"
    sf.write(premaster_path, premaster, SR, subtype="PCM_24")

    caption_segments = [asdict(item) for item in measured]
    # Authentic authority speech stays authentic; localized captions translate it.
    authority_windows = (("AUTH_COLD_OPEN", 0.0, 16.033333), ("AUTH_MID_FILM", 721.666667, 737.8))
    authority_text = {item["id"]: item["text"] for item in package["longform"]["authority_captions"]}
    for authority_id, start, end in authority_windows:
        caption_segments.append(
            {
                "cue_id": authority_id,
                "caption_text": authority_text[authority_id],
                "timeline_start_seconds": start,
                "actual_audio_duration_seconds": end - start,
                "speaker": "AUTHENTIC_AUTHORITY",
            }
        )
    caption_segments.sort(key=lambda value: float(value["timeline_start_seconds"]))
    captions = build_caption_cues(
        language=str(package["locale"]),
        media_duration_seconds=FILM_DURATION,
        segments=caption_segments,
    )
    caption_paths = write_caption_artifacts(captions, output_dir / "longform" / "captions")
    return {
        "narration": {"path": str(narration_path.resolve()), "sha256": sha256(narration_path)},
        "premaster": {"path": str(premaster_path.resolve()), "sha256": sha256(premaster_path)},
        "segments": [asdict(item) for item in measured],
        "captions": caption_paths,
        "authentic_authority_windows": [item[0] for item in authority_windows],
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    package = json.loads(args.editorial.read_text(encoding="utf-8"))
    if package.get("schema") != "contentops.v2.localized_editorial_package.v1":
        raise LocalizedAudioError("Unsupported editorial package schema")
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    kokoro = Kokoro(str(args.model.resolve()), str(args.voices.resolve()))
    if args.sample_only:
        result = {
            "schema": "contentops.v2.local_voice_preflight.v1",
            "locale": package["locale"],
            "backend": "kokoro-onnx",
            "backend_version": "0.4.9",
            "synthesis_revision": SYNTHESIS_REVISION if args.lang == "ja" else LATIN_SYNTHESIS_REVISION,
            "model_sha256": sha256(args.model),
            "voices_sha256": sha256(args.voices),
            "real_person_voice_cloning": False,
            "sample": build_preflight_sample(
                kokoro=kokoro,
                package=package,
                output_dir=output_dir,
                voice=args.voice,
                speed=args.speed,
                lang=args.lang,
            ),
            "runtime_seconds": round(time.perf_counter() - started, 3),
        }
        (output_dir / "voice_preflight_receipt.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return result
    short = build_short(
        kokoro=kokoro,
        package=package,
        output_dir=output_dir,
        voice=args.voice,
        speed=args.speed,
        lang=args.lang,
    )
    longform = None
    if not args.short_only:
        longform = build_longform(
            kokoro=kokoro,
            package=package,
            output_dir=output_dir,
            voice=args.voice,
            speed=args.speed,
            lang=args.lang,
            accepted_audio_dir=args.accepted_audio_dir.resolve(),
        )
    receipt = {
        "schema": "contentops.v2.localized_audio_receipt.v1",
        "locale": package["locale"],
        "backend": "kokoro-onnx",
        "backend_version": "0.4.9",
        "execution": "LOCAL_CPU_ZERO_MARGINAL_COST",
        "voice": args.voice,
        "language_alias": args.lang,
        "speed": args.speed,
        "sample_rate_hz": KOKORO_SR,
        "synthesis_revision": SYNTHESIS_REVISION if args.lang == "ja" else LATIN_SYNTHESIS_REVISION,
        "g2p": "misaki-ja-0.8.4" if args.lang == "ja" else "espeak-ng-via-kokoro-onnx",
        "model": {"path": str(args.model.resolve()), "sha256": sha256(args.model)},
        "voices": {"path": str(args.voices.resolve()), "sha256": sha256(args.voices)},
        "real_person_voice_cloning": False,
        "short": short,
        "longform": longform,
        "runtime_seconds": round(time.perf_counter() - started, 3),
    }
    receipt_path = output_dir / "audio_receipt.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--editorial", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--speed", type=float, required=True)
    parser.add_argument("--accepted-audio-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-only", action="store_true")
    parser.add_argument("--short-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args), ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
