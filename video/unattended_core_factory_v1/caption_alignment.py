"""Two-line cues measured from individual natural-speed narration phrases.

Window overflow is held; this does not certify hearing or word-level timing.
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Mapping, Any

import numpy as np
import soundfile as sf

from .creative import hash_file, hash_value
from video.freeform_chapter_pipeline_v1.package_factory import (
    write_caption_artifacts,
    validate_caption_set,
)


def phrase_groups(text: str, *, width: int = 25, max_words: int = 7) -> list[str]:
    words = text.split()
    groups, current = [], []
    for word in words:
        candidate = " ".join([*current, word])
        lines = textwrap.wrap(
            candidate, width=width, break_long_words=False, break_on_hyphens=False
        )
        if current and (len(lines) > 2 or len(current) >= max_words):
            groups.append(" ".join(current))
            current = []
        current.append(word)
        if re.search(r"[.!?;:]$", word) and len(current) >= 3:
            groups.append(" ".join(current))
            current = []
    if current:
        groups.append(" ".join(current))
    if len(groups) > 1 and len(groups[-1].split()) <= 2:
        previous = groups[-2].split()
        trailing = groups[-1].split()
        if len(previous) >= 4:
            move = max(1, len(previous) // 3)
            groups[-2:] = [
                " ".join(previous[:-move]),
                " ".join(previous[-move:] + trailing),
            ]
    return groups


def measured_phrase_narration(
    *,
    timing_lock: Mapping[str, Any],
    editor: Mapping[str, Any],
    model_path: Path,
    voices_path: Path,
    output_dir: Path,
    media_duration_seconds: float,
    caption_width: int = 29,
    max_phrase_words: int = 10,
    phrase_geometry_by_segment: Mapping[str, Mapping[str, int]] | None = None,
) -> dict[str, Any]:
    """Audio-only revision with cues measured from actual short-phrase synthesis.

    Preserve picture windows and natural voice speed. Window overflow is a HOLD,
    never a reason to speed up or trim speech. Original narration is untouched.
    """
    from kokoro_onnx import Kokoro
    from .transcript import synthesis_text_for_segment

    if not 24 <= caption_width <= 48 or not 7 <= max_phrase_words <= 16:
        raise ValueError("Bounded readable phrase geometry required")
    output_dir.mkdir(parents=True, exist_ok=True)
    route = (timing_lock["voice"], float(timing_lock["speed"]), timing_lock["lang"])
    if route != ("af_heart", 1.06, "en-us"):
        raise ValueError("Unapproved source voice route")
    engine = Kokoro(str(model_path), str(voices_path))
    model_identity = {
        "model_sha256": hash_file(model_path),
        "voices_sha256": hash_file(voices_path),
    }
    source_identity = dict(
        timing_lock_sha256=hash_value(timing_lock),
        editor_sha256=hash_value(editor),
        media_duration_seconds=media_duration_seconds,
        **model_identity,
    )
    if (caption_width, max_phrase_words) != (29, 10):
        source_identity["phrase_geometry"] = dict(
            width=caption_width, max_words=max_phrase_words
        )
    if phrase_geometry_by_segment:
        source_identity["phrase_geometry_by_segment"] = dict(phrase_geometry_by_segment)
    source_seal = output_dir / "source_identity.json"
    if (
        source_seal.exists()
        and json.loads(source_seal.read_text(encoding="utf-8")) != source_identity
    ):
        raise ValueError("Changed phrase source requires distinct revision")
    source_seal.write_text(
        json.dumps(source_identity, sort_keys=True) + "\n", encoding="utf-8"
    )
    rate = 24000
    bus = np.zeros(round(media_duration_seconds * rate), dtype=np.float32)
    segments, holds, records = [], [], []
    authored = {s["segment_id"]: s for s in editor["narration_segments"]}
    if set(phrase_geometry_by_segment or {}) - set(authored):
        raise ValueError("Unknown phrase geometry segment")
    transcript = (
        timing_lock.get("canonical_spoken_transcript")
        or timing_lock["source_narrative_transcript"]
    )
    for original in transcript["segments"]:
        geometry = (phrase_geometry_by_segment or {}).get(original["segment_id"], {})
        width, words = (
            geometry.get("width", caption_width),
            geometry.get("max_words", max_phrase_words),
        )
        if not 24 <= width <= 48 or not 7 <= words <= 16:
            raise ValueError("Bounded readable phrase geometry required")
        groups = phrase_groups(original["text"], width=width, max_words=words)
        parts = []
        for index, text in enumerate(groups):
            part = dict(authored[original["segment_id"]], text=text)
            part["pronunciation_notes"] = [
                n for n in part.get("pronunciation_notes", []) if n["surface"] in text
            ]
            spoken = synthesis_text_for_segment(part)
            identity = hash_value(
                {
                    "text": spoken,
                    "route": route,
                    "engine": "kokoro-v1.0",
                    **model_identity,
                }
            )
            path = output_dir / (identity + ".wav")
            seal_path = path.with_suffix(".identity.json")
            if path.exists():
                if not seal_path.is_file() or json.loads(
                    seal_path.read_text(encoding="utf-8")
                ) != {"identity": identity, "audio_sha256": hash_file(path)}:
                    raise ValueError("Phrase cache drift or unsealed audio")
                audio, observed_rate = sf.read(path, dtype="float32")
            else:
                audio, observed_rate = engine.create(
                    spoken, voice=route[0], speed=route[1], lang=route[2]
                )
                peak = float(np.max(np.abs(audio))) or 1
                audio = np.asarray(audio) * min(1, 10 ** (-3 / 20) / peak)
                sf.write(path, audio, rate, subtype="PCM_24")
                seal_path.write_text(
                    json.dumps({"identity": identity, "audio_sha256": hash_file(path)})
                    + "\n",
                    encoding="utf-8",
                )
            if observed_rate != rate:
                raise ValueError("Phrase sample rate mismatch")
            parts.append((text, audio, path))
        total = sum(len(a) / rate for _, a, _ in parts) + 0.045 * max(0, len(parts) - 1)
        available = float(original["actual_audio_duration_seconds"]) + 0.12
        if total > available:
            holds.append(
                {
                    "segment_id": original["segment_id"],
                    "actual_phrase_seconds": total,
                    "available_seconds": available,
                }
            )
            continue
        cursor = float(original["timeline_start_seconds"])
        for index, (text, audio, path) in enumerate(parts):
            start = round(cursor * rate)
            if start < 0 or start + len(audio) > len(bus):
                raise ValueError("Phrase audio exceeds locked picture duration")
            bus[start : start + len(audio)] += audio
            segments.append(
                {
                    "cue_id": f"{original['segment_id']}-{index + 1:02d}",
                    "segment_id": original["segment_id"],
                    "text": text,
                    "caption_text": textwrap.fill(
                        text,
                        width=width,
                        break_long_words=False,
                        break_on_hyphens=False,
                    ),
                    "timeline_start_seconds": cursor,
                    "actual_audio_duration_seconds": len(audio) / rate,
                    "audio_path": str(path.resolve()),
                    "source_audio_sha256": hash_file(path),
                }
            )
            cursor += len(audio) / rate + 0.045
        records.append(
            {
                "segment_id": original["segment_id"],
                "source_segment_audio_sha256": original["audio"]["sha256"],
                "phrase_audio_seconds": total,
                "window_seconds": available,
                "phrases": len(parts),
            }
        )
        # Rebuild one measured segment waveform for the existing transcript owner.
        segment_audio = np.zeros(
            round((cursor - float(original["timeline_start_seconds"]) - 0.045) * rate),
            dtype=np.float32,
        )
        segment_cursor = 0
        for _, audio, _ in parts:
            segment_audio[segment_cursor : segment_cursor + len(audio)] = audio
            segment_cursor += len(audio) + round(0.045 * rate)
        segment_path = output_dir / ("segment_" + original["segment_id"] + ".wav")
        sf.write(segment_path, segment_audio, rate, subtype="PCM_24")
        records[-1]["audio"] = {
            "path": str(segment_path.resolve()),
            "sha256": hash_file(segment_path),
            "size_bytes": segment_path.stat().st_size,
        }
    receipt = {
        "result": "HOLD_PHRASE_AUDIO_WINDOW_OVERFLOW"
        if holds
        else "MEASURED_PHRASE_NARRATION_READY",
        "holds": holds,
        "segments": segments,
        "source_canonical_transcript_hash": transcript.get("canonical_transcript_hash"),
        "source_narrative_transcript_hash": transcript.get(
            "source_narrative_transcript_hash"
        ),
        "route": route,
        "phrase_records": records,
        "picture_render_count": 0,
        "voice_speed_changed": False,
        "alignment_method": "ACTUAL_INDIVIDUAL_PHRASE_WAVEFORM_LENGTHS_PLACED_IN_ORIGINAL_SEGMENT_WINDOWS",
        "hearing": "NOT_VERIFIED",
        "public_write_authority": False,
    }
    if not holds:
        if (
            " ".join(s["text"] for s in segments).split()
            != transcript["plain_text"].split()
        ):
            raise ValueError("Phrase revision changed spoken words")
        wave = output_dir / "phrase_narration.wav"
        sf.write(wave, bus, rate, subtype="PCM_24")
        receipt["audio"] = {"path": str(wave.resolve()), "sha256": hash_file(wave)}
        caption_set = {
            "schema": "contentops.v2.timed_captions.v1",
            "language": "en",
            "media_duration_seconds": media_duration_seconds,
            "timing_basis": receipt["alignment_method"],
            "cues": [
                {
                    "cue_id": s["cue_id"],
                    "start_seconds": s["timeline_start_seconds"],
                    "end_seconds": s["timeline_start_seconds"]
                    + s["actual_audio_duration_seconds"],
                    "text": s["caption_text"],
                    "speaker": "NARRATOR",
                    "source_audio_sha256": s["source_audio_sha256"],
                }
                for s in segments
            ],
        }
        if (
            any(len(c["text"].splitlines()) > 2 for c in caption_set["cues"])
            or validate_caption_set(caption_set)["result"] != "PASS_CAPTIONS"
        ):
            raise ValueError("Invalid measured mobile caption set")
        receipt["artifacts"] = write_caption_artifacts(
            caption_set, output_dir / "captions"
        )
    (output_dir / "phrase_revision_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt
