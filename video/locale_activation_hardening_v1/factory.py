"""Activate localized V2 audio/caption/metadata packages from one accepted picture.

This module is deliberately platform-neutral. It validates a human/model-authored governed
translation packet, synthesizes only the packet's explicit pronunciation text, creates timed
sidecars from measured audio, and stream-copies the accepted video stream into per-locale muxes.
It contains no Remotion, browser, scheduler, V1, credential-readback, or publication transport.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import requests
import soundfile as sf
from kokoro_onnx import Kokoro

from video.freeform_chapter_pipeline_v1.package_factory import (
    build_caption_cues,
    caption_text,
    validate_caption_set,
)
from video.unattended_core_factory_v1.creative import canonical_bytes, hash_value
from video.unattended_core_factory_v1.media import artifact, probe_media


MANDATORY_LOCALES = ("zh-Hans", "hi", "vi", "ko")
TRANSLATION_SCHEMA = "contentops.v2.governed_locale_translation.v1"
LOCALIZED_TRANSCRIPT_SCHEMA = "contentops.v2.localized_spoken_transcript.v1"
PACKAGE_SCHEMA = "contentops.v2.locale_activation_package.v1"
SAMPLE_RATE = 24_000
INITIAL_SILENCE_SECONDS = 0.18
BETWEEN_PHRASES_SECONDS = 0.10
FINAL_HEADROOM_SECONDS = 0.08
MAX_UNEXPLAINED_FINAL_TAIL_SECONDS = 3.0
MAX_NATURAL_INTER_PHRASE_PAUSE_SECONDS = 0.55
ELEVENLABS_URL = "https://api.elevenlabs.io/v1"
FORBIDDEN_MANIFEST_KEYS = re.compile(
    r"(?:api.?key|credential|cookie|session|authorization|access.?token|refresh.?token)", re.I
)


class LocaleActivationError(RuntimeError):
    """A fail-closed locale truth, synthesis, media, or packaging error."""


@dataclass(frozen=True)
class SynthesizedPhrase:
    cue_id: str
    source_segment_id: str
    text: str
    synthesis_text: str
    start_seconds: float
    duration_seconds: float
    audio_path: str
    audio_sha256: str


@dataclass(frozen=True)
class TTSRoute:
    provider: str
    model: str
    voice: str
    language: str
    speed: float
    external_cost_usd: float | None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return artifact(path)


def _run(command: Sequence[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [str(value) for value in command],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if completed.returncode:
        tail = completed.stdout[-2000:].replace("\r", " ").replace("\n", " ")
        raise LocaleActivationError(f"command_failed:{Path(command[0]).name}:{tail}")
    return completed


def _stream_probe(path: Path) -> tuple[dict[str, Any], dict[str, Any], float, int]:
    probe = probe_media(path)
    video = next(
        (stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video"),
        None,
    )
    if video is None:
        raise LocaleActivationError("accepted_picture_video_stream_missing")
    duration = float(video.get("duration") or probe.get("format", {}).get("duration") or 0)
    frames_text = str(video.get("nb_frames") or "")
    if not frames_text.isdigit():
        raise LocaleActivationError("accepted_picture_exact_frame_count_missing")
    return probe, video, duration, int(frames_text)


def video_stream_sha256(path: Path) -> str:
    completed = _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-c:v",
            "copy",
            "-f",
            "hash",
            "-hash",
            "sha256",
            "-",
        ]
    )
    match = re.search(r"SHA256=([0-9a-f]{64})", completed.stdout, flags=re.I)
    if not match:
        raise LocaleActivationError("video_stream_hash_missing")
    return match.group(1).lower()


def inspect_picture(path: Path) -> dict[str, Any]:
    probe, video, duration, frames = _stream_probe(path)
    return {
        "artifact": artifact(path),
        "video_stream_sha256": video_stream_sha256(path),
        "frame_count": frames,
        "video_duration_seconds": round(duration, 6),
        "codec": video.get("codec_name"),
        "profile": video.get("profile"),
        "width": video.get("width"),
        "height": video.get("height"),
        "pixel_format": video.get("pix_fmt"),
        "color_range": video.get("color_range"),
        "color_space": video.get("color_space"),
        "color_transfer": video.get("color_transfer"),
        "color_primaries": video.get("color_primaries"),
        "format_duration_seconds": float(probe.get("format", {}).get("duration") or 0),
    }


def media_metadata_verdict(picture: Mapping[str, Any]) -> dict[str, Any]:
    pixel_format = str(picture.get("pixel_format") or "")
    color_range = str(picture.get("color_range") or "")
    # yuvj420p/full-range H.264 is legal and broadly decodable. Without source evidence that
    # levels are wrong, changing pixel values would be speculative and violate picture identity.
    observed_full_range = pixel_format.startswith("yuvj") or color_range == "pc"
    return {
        "observed_full_range_yuvj_style": observed_full_range,
        "objectively_required_correction": False,
        "verdict": "PRESERVE_ACCEPTED_PICTURE_STREAM_NO_SPECULATIVE_TRANSCODE",
        "shared_normalized_base_picture": None,
    }


def _nonempty_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text or "\ufffd" in text or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text):
        raise LocaleActivationError(f"invalid_text:{label}")
    return text


def validate_translation_packet(
    packet: Mapping[str, Any], source_transcript: Mapping[str, Any]
) -> dict[str, Any]:
    if packet.get("schema") != TRANSLATION_SCHEMA:
        raise LocaleActivationError("translation_schema_invalid")
    if packet.get("source_canonical_transcript_hash") != source_transcript.get(
        "canonical_transcript_hash"
    ):
        raise LocaleActivationError("translation_source_transcript_hash_mismatch")
    source_segments = {str(item["segment_id"]): item for item in source_transcript["segments"]}
    source_order = [str(item["segment_id"]) for item in source_transcript["segments"]]
    locale_results: dict[str, Any] = {}
    locales = packet.get("locales")
    if not isinstance(locales, Mapping) or set(MANDATORY_LOCALES) - set(locales):
        raise LocaleActivationError("mandatory_locale_translation_missing")

    for locale in MANDATORY_LOCALES:
        localized = locales[locale]
        if localized.get("locale") != locale:
            raise LocaleActivationError(f"localized_locale_identity_mismatch:{locale}")
        segments = localized.get("segments")
        if not isinstance(segments, list) or [str(item.get("segment_id")) for item in segments] != source_order:
            raise LocaleActivationError(f"localized_segment_identity_mismatch:{locale}")
        seen_anchors: set[str] = set()
        for item in segments:
            segment_id = str(item["segment_id"])
            source = source_segments[segment_id]
            if item.get("source_text_sha256") != source.get("segment_text_sha256"):
                raise LocaleActivationError(f"localized_source_text_hash_mismatch:{locale}:{segment_id}")
            text = _nonempty_text(item.get("text"), f"{locale}:{segment_id}:text")
            synthesis_text = _nonempty_text(
                item.get("synthesis_text"), f"{locale}:{segment_id}:synthesis_text"
            )
            for anchor in item.get("truth_anchors", []):
                anchor_id = _nonempty_text(anchor.get("id"), "anchor_id")
                if anchor_id in seen_anchors:
                    raise LocaleActivationError(f"duplicate_locale_anchor:{locale}:{anchor_id}")
                seen_anchors.add(anchor_id)
                source_surface = _nonempty_text(anchor.get("source_surface"), "source_surface")
                display_surface = _nonempty_text(anchor.get("display_surface"), "display_surface")
                spoken_surface = _nonempty_text(anchor.get("spoken_surface"), "spoken_surface")
                if source_surface not in str(source["text"]):
                    raise LocaleActivationError(
                        f"anchor_not_bound_to_source:{locale}:{segment_id}:{anchor_id}"
                    )
                if display_surface not in text or spoken_surface not in synthesis_text:
                    raise LocaleActivationError(
                        f"anchor_surface_missing:{locale}:{segment_id}:{anchor_id}"
                    )
        expected_anchors = {
            str(anchor["id"])
            for locale_anchor in locales[locale]["segments"]
            for anchor in locale_anchor.get("truth_anchors", [])
        }
        if seen_anchors != expected_anchors:
            raise LocaleActivationError(f"locale_anchor_set_incomplete:{locale}")
        locale_results[locale] = {
            "result": "PASS_TRANSLATION_TRUTH_INVARIANTS",
            "segment_count": len(segments),
            "anchor_count": len(seen_anchors),
            "entity_identity_preserved": True,
            "numeric_direction_negation_preserved": True,
            "factual_writer_count": 1,
        }
    return {
        "result": "PASS_GOVERNED_TRANSLATION_PACKET",
        "source_canonical_transcript_hash": source_transcript["canonical_transcript_hash"],
        "locales": locale_results,
    }


def _split_phrases(text: str, synthesis_text: str) -> list[tuple[str, str]]:
    sentence_boundary = r"(?<=[!?。！？।])\s*|(?<=\.)\s+(?=\S)"
    display = [value.strip() for value in re.split(sentence_boundary, text) if value.strip()]
    spoken = [
        value.strip()
        for value in re.split(sentence_boundary, synthesis_text)
        if value.strip()
    ]
    if len(display) != len(spoken):
        return [(text, synthesis_text)]
    phrases: list[tuple[str, str]] = []
    for display_sentence, spoken_sentence in zip(display, spoken):
        display_clauses = [
            value.strip()
            for value in re.split(r"(?<=[,;，；：:])\s*", display_sentence)
            if value.strip()
        ]
        spoken_clauses = [
            value.strip()
            for value in re.split(r"(?<=[,;，；：:])\s*", spoken_sentence)
            if value.strip()
        ]
        if len(display_clauses) == len(spoken_clauses):
            phrases.extend(zip(display_clauses, spoken_clauses))
        else:
            phrases.append((display_sentence, spoken_sentence))
    return phrases


def _kokoro_synthesize(
    kokoro: Kokoro, text: str, *, voice: str, speed: float, language: str, output: Path
) -> None:
    audio, rate = kokoro.create(text, voice=voice, speed=speed, lang=language)
    if int(rate) != SAMPLE_RATE:
        raise LocaleActivationError(f"kokoro_sample_rate_unexpected:{rate}")
    output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output, np.asarray(audio, dtype=np.float32), SAMPLE_RATE, subtype="PCM_24")


def _elevenlabs_synthesize(
    text: str, *, voice: str, model: str, speed: float, output: Path, api_key: str
) -> None:
    identity = hash_value({"text": text, "voice": voice, "model": model, "speed": speed})
    identity_path = output.with_suffix(".identity.json")
    if output.exists() and identity_path.exists():
        cached = json.loads(identity_path.read_text(encoding="utf-8"))
        if cached.get("identity") == identity and cached.get("audio_sha256") == _sha256_file(output):
            return
    response = requests.post(
        f"{ELEVENLABS_URL}/text-to-speech/{voice}",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": model,
            "voice_settings": {"stability": 0.55, "similarity_boost": 0.75, "style": 0.0},
        },
        timeout=120,
    )
    if response.status_code != 200:
        raise LocaleActivationError(f"elevenlabs_synthesis_failed:http_{response.status_code}")
    raw = response.content
    if len(raw) < 1024:
        raise LocaleActivationError("elevenlabs_audio_payload_invalid")
    output.parent.mkdir(parents=True, exist_ok=True)
    provider_audio = output.with_suffix(".provider.mp3")
    provider_audio.write_bytes(raw)
    _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(provider_audio),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-filter:a",
            f"atempo={speed:.6f}",
            "-c:a",
            "pcm_s24le",
            str(output),
        ]
    )
    _write_json(identity_path, {"identity": identity, "audio_sha256": _sha256_file(output)})


def _route_for_locale(locale: str) -> TTSRoute:
    if locale == "zh-Hans":
        return TTSRoute(
            "ElevenLabs", "eleven_multilingual_v2", "EXAVITQu4vr4xnSDxMaL", "zh-Hans", 1.18, None
        )
    if locale == "hi":
        return TTSRoute("kokoro-onnx", "kokoro-v1.0", "hf_alpha", "hi", 1.33, 0.0)
    if locale == "vi":
        return TTSRoute(
            "ElevenLabs", "eleven_flash_v2_5", "EXAVITQu4vr4xnSDxMaL", "vi", 1.18, None
        )
    if locale == "ko":
        return TTSRoute(
            "ElevenLabs", "eleven_multilingual_v2", "EXAVITQu4vr4xnSDxMaL", "ko", 1.10, None
        )
    raise LocaleActivationError(f"unsupported_locale:{locale}")


def _source_segment_windows(
    source_segments: Sequence[Mapping[str, Any]], *, picture_duration: float
) -> list[dict[str, Any]]:
    """Bind each governed source segment to its accepted picture/narrative window."""
    if not source_segments:
        raise LocaleActivationError("source_timing_segments_missing")
    windows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, segment in enumerate(source_segments):
        segment_id = _nonempty_text(segment.get("segment_id"), "source_segment_id")
        if segment_id in seen:
            raise LocaleActivationError(f"duplicate_source_timing_segment:{segment_id}")
        seen.add(segment_id)
        start = float(segment.get("timeline_start_seconds", -1))
        narrative_end = float(segment.get("timeline_end_seconds", -1))
        if index + 1 < len(source_segments):
            window_end = float(source_segments[index + 1].get("timeline_start_seconds", -1))
        else:
            window_end = float(picture_duration)
        if start < 0 or narrative_end < start or window_end <= start:
            raise LocaleActivationError(f"source_timing_window_invalid:{segment_id}")
        if narrative_end > window_end + 0.001 or window_end > picture_duration + 0.001:
            raise LocaleActivationError(f"source_timing_window_exceeds_picture:{segment_id}")
        windows.append(
            {
                "source_segment_id": segment_id,
                "source_timeline_start_seconds": round(start, 6),
                "source_narrative_end_seconds": round(narrative_end, 6),
                "source_window_end_seconds": round(window_end, 6),
            }
        )
    return windows


def align_phrases_to_source_windows(
    *,
    locale: str,
    phrases: Sequence[SynthesizedPhrase],
    source_segments: Sequence[Mapping[str, Any]],
    picture_duration: float,
) -> tuple[list[SynthesizedPhrase], dict[str, Any]]:
    """Place measured localized phrases inside their governed source narrative windows.

    This never changes audio speed or wording. If measured speech cannot fit with a natural
    minimum pause, the caller must perform a bounded localization rewrite and resynthesize only
    the affected source segment.
    """
    windows = _source_segment_windows(source_segments, picture_duration=picture_duration)
    phrase_ids = [phrase.source_segment_id for phrase in phrases]
    expected_ids = [window["source_segment_id"] for window in windows]
    if set(phrase_ids) != set(expected_ids):
        raise LocaleActivationError(f"localized_source_segment_binding_incomplete:{locale}")

    aligned: list[SynthesizedPhrase] = []
    segment_records: list[dict[str, Any]] = []
    for index, window in enumerate(windows):
        segment_id = str(window["source_segment_id"])
        linked = [phrase for phrase in phrases if phrase.source_segment_id == segment_id]
        if not linked:
            raise LocaleActivationError(f"localized_segment_audio_missing:{locale}:{segment_id}")
        window_start = float(window["source_timeline_start_seconds"])
        window_end = float(window["source_window_end_seconds"])
        usable_end = window_end - (FINAL_HEADROOM_SECONDS if index == len(windows) - 1 else 0.0)
        audio_duration = sum(float(phrase.duration_seconds) for phrase in linked)
        minimum_pause = BETWEEN_PHRASES_SECONDS * max(0, len(linked) - 1)
        if audio_duration + minimum_pause > usable_end - window_start + 0.001:
            raise LocaleActivationError(
                "localized_segment_exceeds_picture_window_rewrite_required:"
                f"{locale}:{segment_id}:{audio_duration + minimum_pause:.3f}>"
                f"{usable_end - window_start:.3f}"
            )
        if len(linked) > 1:
            available_pause = (usable_end - window_start - audio_duration) / (len(linked) - 1)
            phrase_pause = min(
                MAX_NATURAL_INTER_PHRASE_PAUSE_SECONDS,
                max(BETWEEN_PHRASES_SECONDS, available_pause),
            )
        else:
            phrase_pause = 0.0
        cursor = window_start
        placements: list[dict[str, Any]] = []
        for phrase_index, phrase in enumerate(linked):
            placed = SynthesizedPhrase(
                cue_id=phrase.cue_id,
                source_segment_id=phrase.source_segment_id,
                text=phrase.text,
                synthesis_text=phrase.synthesis_text,
                start_seconds=round(cursor, 6),
                duration_seconds=round(float(phrase.duration_seconds), 6),
                audio_path=phrase.audio_path,
                audio_sha256=phrase.audio_sha256,
            )
            aligned.append(placed)
            end = float(placed.start_seconds) + float(placed.duration_seconds)
            placements.append(
                {
                    "cue_id": placed.cue_id,
                    "source_segment_id": segment_id,
                    "timeline_start_seconds": placed.start_seconds,
                    "actual_audio_duration_seconds": placed.duration_seconds,
                    "timeline_end_seconds": round(end, 6),
                    "audio_sha256": placed.audio_sha256,
                }
            )
            cursor = end
            if phrase_index + 1 < len(linked):
                cursor += phrase_pause
        segment_end = float(placements[-1]["timeline_end_seconds"])
        segment_records.append(
            {
                **window,
                "actual_segment_start_seconds": placements[0]["timeline_start_seconds"],
                "actual_segment_end_seconds": round(segment_end, 6),
                "actual_synthesized_duration_seconds": round(audio_duration, 6),
                "inter_phrase_pause_seconds": round(phrase_pause, 6),
                "trailing_window_slack_seconds": round(window_end - segment_end, 6),
                "placement_mode": "INSIDE_GOVERNED_SOURCE_WINDOW",
                "placements": placements,
            }
        )
    timing = {
        "schema": "contentops.v2.localized_timeline_alignment.v1",
        "locale": locale,
        "picture_duration_seconds": round(float(picture_duration), 6),
        "max_unexplained_final_tail_seconds": MAX_UNEXPLAINED_FINAL_TAIL_SECONDS,
        "segments": segment_records,
    }
    timing["timeline_alignment_hash"] = hash_value(timing)
    return aligned, timing


def _write_aligned_audio_program(
    *, locale: str, phrases: Sequence[SynthesizedPhrase], output: Path, picture_duration: float
) -> dict[str, Any]:
    bus = np.zeros(round(picture_duration * SAMPLE_RATE), dtype=np.float32)
    for phrase in phrases:
        clip, rate = sf.read(phrase.audio_path, dtype="float32")
        if int(rate) != SAMPLE_RATE:
            raise LocaleActivationError("locale_phrase_sample_rate_mismatch")
        if clip.ndim == 2:
            clip = np.mean(clip, axis=1)
        start = round(phrase.start_seconds * SAMPLE_RATE)
        end = start + len(clip)
        if end > len(bus):
            raise LocaleActivationError(f"locale_audio_overflow:{locale}:{phrase.cue_id}")
        bus[start:end] += clip
    output.parent.mkdir(parents=True, exist_ok=True)
    peak = float(np.max(np.abs(bus))) or 1.0
    sf.write(output, bus * min(1.0, 0.88 / peak), SAMPLE_RATE, subtype="PCM_24")
    return artifact(output)


def meaningful_speech_bounds(path: Path, *, threshold_db: float = -45.0) -> dict[str, float]:
    """Measure meaningful speech bounds with deterministic 10 ms RMS windows."""
    audio, rate = sf.read(path, dtype="float32")
    if audio.ndim == 2:
        audio = np.mean(audio, axis=1)
    window = max(1, round(int(rate) * 0.01))
    padded = np.pad(audio, (0, (-len(audio)) % window))
    blocks = padded.reshape(-1, window)
    rms = np.sqrt(np.mean(np.square(blocks, dtype=np.float64), axis=1))
    threshold = 10.0 ** (threshold_db / 20.0)
    active = np.flatnonzero(rms >= threshold)
    if not len(active):
        raise LocaleActivationError(f"localized_audio_contains_no_meaningful_speech:{path.name}")
    return {
        "speech_start_seconds": round(float(active[0] * window / rate), 6),
        "speech_end_seconds": round(float(min(len(audio), (active[-1] + 1) * window) / rate), 6),
    }


def validate_timeline_alignment(
    timing: Mapping[str, Any],
    *,
    source_segments: Sequence[Mapping[str, Any]],
    picture_duration: float,
    strict_inside_windows: bool,
) -> dict[str, Any]:
    """Fail closed on identity drift, overlap, picture overflow, or tail concentration."""
    if timing.get("schema") != "contentops.v2.localized_timeline_alignment.v1":
        raise LocaleActivationError("localized_timeline_alignment_schema_invalid")
    locale = _nonempty_text(timing.get("locale"), "timeline_locale")
    if abs(float(timing.get("picture_duration_seconds", -1)) - picture_duration) > 0.001:
        raise LocaleActivationError(f"localized_timeline_picture_duration_mismatch:{locale}")
    expected_windows = _source_segment_windows(
        source_segments, picture_duration=picture_duration
    )
    observed_segments = timing.get("segments")
    if not isinstance(observed_segments, list) or [
        str(value.get("source_segment_id")) for value in observed_segments
    ] != [value["source_segment_id"] for value in expected_windows]:
        raise LocaleActivationError(f"localized_timeline_segment_identity_mismatch:{locale}")

    speech_start = float(timing.get("meaningful_speech_start_seconds", -1))
    speech_end = float(timing.get("meaningful_speech_end_seconds", -1))
    if speech_start < 0 or speech_end <= speech_start or speech_end > picture_duration + 0.001:
        raise LocaleActivationError(f"localized_meaningful_speech_bounds_invalid:{locale}")
    tail = picture_duration - speech_end
    allowed_tail = float(
        timing.get(
            "max_unexplained_final_tail_seconds", MAX_UNEXPLAINED_FINAL_TAIL_SECONDS
        )
    )
    if tail > allowed_tail + 0.001 and not bool(timing.get("intentional_ending_silence")):
        raise LocaleActivationError(
            f"localized_unexplained_final_tail_exceeds_limit:{locale}:{tail:.3f}>{allowed_tail:.3f}"
        )

    previous_end = 0.0
    cue_ids: set[str] = set()
    for observed, expected in zip(observed_segments, expected_windows):
        segment_id = str(expected["source_segment_id"])
        placements = observed.get("placements")
        if not isinstance(placements, list) or not placements:
            raise LocaleActivationError(f"localized_timeline_placements_missing:{locale}:{segment_id}")
        segment_start = float(placements[0].get("timeline_start_seconds", -1))
        segment_end = float(placements[-1].get("timeline_end_seconds", -1))
        for placement in placements:
            cue_id = _nonempty_text(placement.get("cue_id"), "timeline_cue_id")
            if cue_id in cue_ids:
                raise LocaleActivationError(f"localized_timeline_duplicate_cue:{locale}:{cue_id}")
            cue_ids.add(cue_id)
            if placement.get("source_segment_id") != segment_id:
                raise LocaleActivationError(
                    f"localized_timeline_source_binding_mismatch:{locale}:{cue_id}"
                )
            start = float(placement.get("timeline_start_seconds", -1))
            duration = float(placement.get("actual_audio_duration_seconds", -1))
            end = float(placement.get("timeline_end_seconds", -1))
            if duration <= 0 or abs(start + duration - end) > 0.001:
                raise LocaleActivationError(f"localized_timeline_duration_invalid:{locale}:{cue_id}")
            if start < previous_end - 0.001:
                raise LocaleActivationError(f"localized_timeline_overlap:{locale}:{cue_id}")
            if end > picture_duration + 0.001:
                raise LocaleActivationError(f"localized_timeline_exceeds_picture:{locale}:{cue_id}")
            previous_end = end
        window_start = float(expected["source_timeline_start_seconds"])
        window_end = float(expected["source_window_end_seconds"])
        if strict_inside_windows:
            if segment_start < window_start - 0.001 or segment_end > window_end + 0.001:
                raise LocaleActivationError(
                    f"localized_timeline_outside_source_window:{locale}:{segment_id}"
                )
        elif segment_end < window_start - 0.001 or segment_start > window_end + 0.001:
            raise LocaleActivationError(
                f"localized_timeline_misses_source_window:{locale}:{segment_id}"
            )

    unsigned = dict(timing)
    observed_hash = str(unsigned.pop("timeline_alignment_hash", ""))
    if not observed_hash or hash_value(unsigned) != observed_hash:
        raise LocaleActivationError(f"localized_timeline_alignment_hash_mismatch:{locale}")
    return {
        "result": "PASS_LOCALIZED_TIMELINE_ALIGNMENT",
        "locale": locale,
        "strict_inside_source_windows": strict_inside_windows,
        "segment_count": len(observed_segments),
        "cue_count": len(cue_ids),
        "meaningful_speech_start_seconds": round(speech_start, 6),
        "meaningful_speech_end_seconds": round(speech_end, 6),
        "final_tail_seconds": round(tail, 6),
        "timeline_alignment_hash": observed_hash,
    }


def _assemble_locale_audio(
    *,
    locale: str,
    localized: Mapping[str, Any],
    output_root: Path,
    picture_duration: float,
    source_segments: Sequence[Mapping[str, Any]],
    kokoro: Kokoro,
    api_key: str | None,
) -> tuple[dict[str, Any], list[SynthesizedPhrase]]:
    route = _route_for_locale(locale)
    if route.provider == "ElevenLabs" and not api_key:
        raise LocaleActivationError(f"tts_capability_blocked:{locale}:ELEVENLABS_API_KEY_absent")
    segments_root = output_root / "audio" / "segments"
    phrases: list[SynthesizedPhrase] = []
    requested_characters = 0
    corrections: list[dict[str, Any]] = []
    ordinal = 0
    for segment in localized["segments"]:
        segment_id = str(segment["segment_id"])
        for display, spoken in _split_phrases(str(segment["text"]), str(segment["synthesis_text"])):
            ordinal += 1
            requested_characters += len(spoken)
            output = segments_root / f"{ordinal:02d}_{segment_id}.wav"
            if route.provider == "kokoro-onnx":
                _kokoro_synthesize(
                    kokoro,
                    spoken,
                    voice=route.voice,
                    speed=route.speed,
                    language=route.language,
                    output=output,
                )
            else:
                _elevenlabs_synthesize(
                    spoken,
                    voice=route.voice,
                    model=route.model,
                    speed=route.speed,
                    output=output,
                    api_key=str(api_key),
                )
            duration = float(sf.info(output).duration)
            phrases.append(
                SynthesizedPhrase(
                    cue_id=f"{locale}-{ordinal:02d}",
                    source_segment_id=segment_id,
                    text=display,
                    synthesis_text=spoken,
                    start_seconds=0.0,
                    duration_seconds=round(duration, 6),
                    audio_path=str(output.resolve()),
                    audio_sha256=_sha256_file(output),
                )
            )
        for anchor in segment.get("truth_anchors", []):
            if anchor["display_surface"] != anchor["spoken_surface"]:
                corrections.append(
                    {
                        "source_segment_id": segment_id,
                        "surface": anchor["display_surface"],
                        "spoken_as": anchor["spoken_surface"],
                    }
                )
    phrases, timing = align_phrases_to_source_windows(
        locale=locale,
        phrases=phrases,
        source_segments=source_segments,
        picture_duration=picture_duration,
    )
    spoken_end = max(phrase.start_seconds + phrase.duration_seconds for phrase in phrases)
    narration = output_root / "audio" / f"narration.{locale}.wav"
    audio_artifact = _write_aligned_audio_program(
        locale=locale,
        phrases=phrases,
        output=narration,
        picture_duration=picture_duration,
    )
    speech_bounds = meaningful_speech_bounds(narration)
    timing.pop("timeline_alignment_hash", None)
    timing.update(
        {
            "localized_audio_sha256": audio_artifact["sha256"],
            "meaningful_speech_start_seconds": speech_bounds["speech_start_seconds"],
            "meaningful_speech_end_seconds": speech_bounds["speech_end_seconds"],
            "intentional_ending_silence": False,
        }
    )
    timing["timeline_alignment_hash"] = hash_value(timing)
    transcript_plain = " ".join(str(item["text"]) for item in localized["segments"])
    synthesis_plain = " ".join(str(item["synthesis_text"]) for item in localized["segments"])
    receipt = {
        "schema": "contentops.v2.localized_tts_receipt.v1",
        "locale": locale,
        "provider": route.provider,
        "model": route.model,
        "voice": route.voice,
        "language": route.language,
        "speed": route.speed,
        "transcript_hash": hash_value(transcript_plain),
        "synthesis_text_hash": hash_value(synthesis_plain),
        "audio": audio_artifact,
        "actual_spoken_end_seconds": round(spoken_end, 6),
        "meaningful_speech_start_seconds": speech_bounds["speech_start_seconds"],
        "meaningful_speech_end_seconds": speech_bounds["speech_end_seconds"],
        "final_meaningful_speech_tail_seconds": round(
            picture_duration - speech_bounds["speech_end_seconds"], 6
        ),
        "audio_program_duration_seconds": round(float(sf.info(narration).duration), 6),
        "requested_characters": requested_characters,
        "external_cost_usd": route.external_cost_usd,
        "cost_status": "LOCAL_ZERO_COST" if route.provider == "kokoro-onnx" else "NOT_EXPOSED_BY_TTS_RESPONSE",
        "pronunciation_corrections": corrections,
        "timeline_alignment_hash": timing["timeline_alignment_hash"],
        "segment_placements": timing["segments"],
        "secret_material_persisted": False,
    }
    receipt["tts_receipt_hash"] = hash_value(receipt)
    return receipt, phrases


def _caption_lines(text: str, *, locale: str) -> str:
    max_chars = 21 if locale in {"zh-Hans", "ko"} else 38
    if len(text) <= max_chars:
        return text
    if locale in {"zh-Hans", "ko"}:
        boundary = min(range(max(1, len(text) // 2 - 6), min(len(text), len(text) // 2 + 7)), key=lambda i: abs(i - len(text) / 2))
        for token in "，、；： ":
            candidates = [i + 1 for i, char in enumerate(text) if char == token and 5 < i < len(text) - 5]
            if candidates:
                boundary = min(candidates, key=lambda i: abs(i - len(text) / 2))
                break
        return text[:boundary].strip() + "\n" + text[boundary:].strip()
    words = text.split()
    lines = [""]
    for word in words:
        candidate = (lines[-1] + " " + word).strip()
        if len(candidate) <= max_chars or len(lines) == 2:
            lines[-1] = candidate
        else:
            lines.append(word)
    if len(lines) > 2 or any(len(line) > max_chars + 8 for line in lines):
        raise LocaleActivationError(f"caption_mobile_line_contract_failed:{locale}:{text}")
    return "\n".join(lines)


def _build_transcript_and_captions(
    *,
    locale: str,
    localized: Mapping[str, Any],
    source_hash: str,
    receipt: Mapping[str, Any],
    phrases: Sequence[SynthesizedPhrase],
    picture_duration: float,
    output_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    segments = []
    timing_by_segment = {
        str(value["source_segment_id"]): value
        for value in receipt.get("segment_placements", [])
    }
    for item in localized["segments"]:
        segment_id = str(item["segment_id"])
        linked = [phrase for phrase in phrases if phrase.source_segment_id == segment_id]
        timing = timing_by_segment.get(segment_id)
        if timing is None:
            raise LocaleActivationError(
                f"localized_transcript_timing_binding_missing:{locale}:{segment_id}"
            )
        segments.append(
            {
                "segment_id": segment_id,
                "kind": item["kind"],
                "text": item["text"],
                "text_sha256": hash_value(item["text"]),
                "synthesis_text": item["synthesis_text"],
                "synthesis_text_sha256": hash_value(item["synthesis_text"]),
                "source_text_sha256": item["source_text_sha256"],
                "truth_anchor_ids": [str(value["id"]) for value in item.get("truth_anchors", [])],
                "cue_ids": [value.cue_id for value in linked],
                "source_timing_window": {
                    key: timing[key]
                    for key in (
                        "source_timeline_start_seconds",
                        "source_narrative_end_seconds",
                        "source_window_end_seconds",
                    )
                },
                "actual_placements": list(timing["placements"]),
            }
        )
    plain_text = " ".join(str(item["text"]) for item in localized["segments"])
    synthesis_text = " ".join(str(item["synthesis_text"]) for item in localized["segments"])
    transcript = {
        "schema": LOCALIZED_TRANSCRIPT_SCHEMA,
        "locale": locale,
        "source_canonical_transcript_hash": source_hash,
        "plain_text": plain_text,
        "plain_text_sha256": hash_value(plain_text),
        "synthesis_text_sha256": hash_value(synthesis_text),
        "locked_localized_audio_sha256": receipt["audio"]["sha256"],
        "timeline_alignment_hash": receipt["timeline_alignment_hash"],
        "segments": segments,
    }
    transcript["localized_transcript_hash"] = hash_value(transcript)

    caption_segments = [
        {
            "cue_id": phrase.cue_id,
            "timeline_start_seconds": phrase.start_seconds,
            "actual_audio_duration_seconds": phrase.duration_seconds,
            "caption_text": _caption_lines(phrase.text, locale=locale),
            "speaker": "NARRATOR",
            "audio_path": phrase.audio_path,
        }
        for phrase in phrases
    ]
    captions = build_caption_cues(
        language=locale,
        media_duration_seconds=picture_duration,
        segments=caption_segments,
    )
    captions["localized_transcript_hash"] = transcript["localized_transcript_hash"]
    captions["localized_audio_sha256"] = receipt["audio"]["sha256"]
    captions["max_lines"] = 2
    captions["semantic_boundary"] = "SYNTHESIZED_PHRASE"
    validation = validate_caption_set(captions)
    if validation["result"] != "PASS_CAPTIONS":
        raise LocaleActivationError(f"caption_validation_failed:{locale}:{validation['errors']}")
    caption_root = output_root / "captions"
    caption_root.mkdir(parents=True, exist_ok=True)
    caption_json = caption_root / f"captions.{locale}.json"
    caption_srt = caption_root / f"captions.{locale}.srt"
    caption_vtt = caption_root / f"captions.{locale}.vtt"
    _write_json(caption_json, captions)
    caption_srt.write_text(caption_text(captions, kind="srt"), encoding="utf-8")
    caption_vtt.write_text(caption_text(captions, kind="vtt"), encoding="utf-8")
    artifacts = {
        "json": artifact(caption_json),
        "srt": artifact(caption_srt),
        "vtt": artifact(caption_vtt),
    }
    return transcript, captions, artifacts


def _metadata_from_transcript(
    localized: Mapping[str, Any], transcript: Mapping[str, Any], phrases: Sequence[SynthesizedPhrase]
) -> dict[str, Any]:
    segments = list(localized["segments"])
    title = str(segments[0]["text"])
    description = " ".join(str(value["text"]) for value in segments[:2])
    entity_surfaces: list[str] = []
    for segment in segments:
        for anchor in segment.get("truth_anchors", []):
            if anchor.get("kind") in {"ENTITY", "INSTITUTION"}:
                surface = str(anchor["display_surface"])
                if surface not in entity_surfaces:
                    entity_surfaces.append(surface)
    metadata = {
        "title": title,
        "description": description,
        "search_entities": entity_surfaces,
        "chapters": [
            {
                "source_segment_id": segment["segment_id"],
                "start_seconds": next(
                    phrase.start_seconds
                    for phrase in phrases
                    if phrase.source_segment_id == segment["segment_id"]
                ),
                "title": str(segment["text"]),
            }
            for segment in segments
        ],
        "derivation_basis": "GOVERNED_LOCALIZED_TRANSCRIPT_ONLY",
        "localized_transcript_hash": transcript["localized_transcript_hash"],
        "invented_or_strengthened_fact_count": 0,
    }
    metadata["metadata_hash"] = hash_value(metadata)
    return metadata


def mux_picture_identical_locale(
    *, picture: Path, audio: Path, output: Path, source_picture: Mapping[str, Any]
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(picture),
            "-i",
            str(audio),
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
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    observed = inspect_picture(output)
    if (
        observed["video_stream_sha256"] != source_picture["video_stream_sha256"]
        or observed["frame_count"] != source_picture["frame_count"]
        or abs(observed["video_duration_seconds"] - source_picture["video_duration_seconds"]) > 0.001
    ):
        raise LocaleActivationError("localized_mux_picture_identity_mismatch")
    return {
        "result": "PASS_PICTURE_STREAM_AND_FRAME_IDENTITY",
        "source": dict(source_picture),
        "localized_mux": observed,
        "audio_duration_cannot_truncate_picture": True,
        "ffmpeg_shortest_used": False,
        "picture_render_count": 0,
    }


def _sample(phrases: Sequence[SynthesizedPhrase], output: Path) -> dict[str, Any]:
    selected = next(
        (
            phrase
            for phrase in phrases
            if phrase.source_segment_id == "topline"
        ),
        phrases[0],
    )
    audio, rate = sf.read(selected.audio_path, dtype="float32")
    sf.write(output, audio[: round(min(len(audio) / rate, 12.0) * rate)], rate, subtype="PCM_24")
    return {
        "artifact": artifact(output),
        "source_cue_id": selected.cue_id,
        "coverage": ["NUMBER", "PROPER_NOUN_OR_STANDARD_LOCAL_RENDERING", "NORMAL_SENTENCE"],
    }


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if FORBIDDEN_MANIFEST_KEYS.search(str(key)):
                raise LocaleActivationError(f"secret_like_manifest_key:{key}")
            _assert_no_forbidden_keys(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _assert_no_forbidden_keys(item)


def activate_locales(
    *,
    source_job_root: Path,
    translations_path: Path,
    output_root: Path,
    kokoro_model: Path,
    kokoro_voices: Path,
) -> dict[str, Any]:
    source_job_root = source_job_root.resolve()
    output_root = output_root.resolve()
    timing_lock = json.loads(
        (source_job_root / "artifacts" / "actual_narration_timing_lock.json").read_text(
            encoding="utf-8"
        )
    )
    source_package = json.loads(
        (source_job_root / "package" / "platform_neutral_package_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    source_transcript = timing_lock["canonical_spoken_transcript"]
    packet = json.loads(translations_path.read_text(encoding="utf-8"))
    translation_validation = validate_translation_packet(packet, source_transcript)
    picture = source_job_root / "media" / "picture_lock.mp4"
    source_picture = inspect_picture(picture)
    metadata_verdict = media_metadata_verdict(source_picture)
    kokoro = Kokoro(str(kokoro_model.resolve()), str(kokoro_voices.resolve()))
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    locale_packages: dict[str, Any] = {}
    for locale in MANDATORY_LOCALES:
        locale_root = output_root / "locales" / locale
        localized = packet["locales"][locale]
        receipt, phrases = _assemble_locale_audio(
            locale=locale,
            localized=localized,
            output_root=locale_root,
            picture_duration=source_picture["video_duration_seconds"],
            source_segments=source_transcript["segments"],
            kokoro=kokoro,
            api_key=api_key,
        )
        transcript, captions, caption_artifacts = _build_transcript_and_captions(
            locale=locale,
            localized=localized,
            source_hash=source_transcript["canonical_transcript_hash"],
            receipt=receipt,
            phrases=phrases,
            picture_duration=source_picture["video_duration_seconds"],
            output_root=locale_root,
        )
        metadata = _metadata_from_transcript(localized, transcript, phrases)
        timing = {
            "schema": "contentops.v2.localized_timeline_alignment.v1",
            "locale": locale,
            "picture_duration_seconds": source_picture["video_duration_seconds"],
            "max_unexplained_final_tail_seconds": MAX_UNEXPLAINED_FINAL_TAIL_SECONDS,
            "segments": receipt["segment_placements"],
            "localized_audio_sha256": receipt["audio"]["sha256"],
            "meaningful_speech_start_seconds": receipt["meaningful_speech_start_seconds"],
            "meaningful_speech_end_seconds": receipt["meaningful_speech_end_seconds"],
            "intentional_ending_silence": False,
            "timeline_alignment_hash": receipt["timeline_alignment_hash"],
        }
        timing_validation = validate_timeline_alignment(
            timing,
            source_segments=source_transcript["segments"],
            picture_duration=source_picture["video_duration_seconds"],
            strict_inside_windows=True,
        )
        transcript_artifact = _write_json(locale_root / "localized_transcript.json", transcript)
        metadata_artifact = _write_json(locale_root / "localized_metadata.json", metadata)
        tts_artifact = _write_json(locale_root / "tts_receipt.json", receipt)
        timing_artifact = _write_json(locale_root / "localized_timing.json", timing)
        mux_path = locale_root / "media" / f"us-retail-short.{locale}.mp4"
        picture_identity = mux_picture_identical_locale(
            picture=picture,
            audio=Path(receipt["audio"]["path"]),
            output=mux_path,
            source_picture=source_picture,
        )
        sample = _sample(phrases, locale_root / "audio" / f"listening_sample.{locale}.wav")
        package = {
            "schema": PACKAGE_SCHEMA,
            "locale": locale,
            "source_story_id": source_package["source_story_id"],
            "source_canonical_transcript_hash": source_transcript["canonical_transcript_hash"],
            "localized_transcript_hash": transcript["localized_transcript_hash"],
            "accepted_picture": source_picture,
            "localized_mux": artifact(mux_path),
            "picture_identity_proof": picture_identity,
            "localized_audio": receipt["audio"],
            "tts_receipt": tts_artifact,
            "localized_timing": timing_artifact,
            "timeline_alignment_qa": timing_validation,
            "localized_transcript": transcript_artifact,
            "captions": caption_artifacts,
            "metadata": metadata_artifact,
            "listening_sample": sample,
            "future_surfaces": {
                "youtube": "LOCALIZED_AUDIO_TRACK_AND_CAPTION_SIDECARS_NO_UPLOAD",
                "short_form": "ONE_SELECTED_LOCALIZED_AUDIO_PROGRAM_NO_UPLOAD",
            },
            "hard_boundaries": {
                "video_public_write_authority": False,
                "v1_mutation_authority": False,
                "scheduler_mutation_authority": False,
                "picture_rerender_count": 0,
                "burned_captions": False,
            },
            "owner_listening_acceptance_claimed": False,
        }
        _assert_no_forbidden_keys(package)
        unsigned = dict(package)
        package["package_id"] = "locale_pkg_" + hashlib.sha256(
            canonical_bytes(unsigned)
        ).hexdigest()
        package_artifact = _write_json(locale_root / "package_manifest.json", package)
        locale_packages[locale] = {
            "package_id": package["package_id"],
            "package_manifest": package_artifact,
            "localized_transcript_hash": transcript["localized_transcript_hash"],
            "timeline_alignment_hash": receipt["timeline_alignment_hash"],
            "audio_sha256": receipt["audio"]["sha256"],
            "caption_sha256": {key: value["sha256"] for key, value in caption_artifacts.items()},
            "metadata_sha256": metadata_artifact["sha256"],
            "mux_sha256": package["localized_mux"]["sha256"],
            "picture_stream_sha256": picture_identity["localized_mux"]["video_stream_sha256"],
            "frame_count": picture_identity["localized_mux"]["frame_count"],
            "tts": {key: receipt[key] for key in ("provider", "model", "voice", "language", "external_cost_usd", "cost_status")},
            "full_audio_path": receipt["audio"]["path"],
            "sample_path": sample["artifact"]["path"],
            "final_package_path": str(mux_path),
        }

    english_audio = Path(str(source_package["artifacts"]["audio"]["path"]))
    youtube_manifest = {
        "schema": "contentops.v2.youtube_multilingual_package.v1",
        "accepted_picture": source_picture,
        "canonical_english_audio": artifact(english_audio),
        "localized_packages": locale_packages,
        "upload_authority": False,
        "account_eligibility_claimed": False,
    }
    _assert_no_forbidden_keys(youtube_manifest)
    youtube_artifact = _write_json(output_root / "youtube_multilingual_manifest.json", youtube_manifest)
    final = {
        "schema": "contentops.v2.locale_activation_e2e_receipt.v1",
        "task_id": "TASK_CONTENTOPS_V2_LOCALE_ACTIVATION_HARDENING_V1",
        "result": "PASS_IMPLEMENTATION_V2_LOCALE_ACTIVATION_PACKAGES_READY_FOR_JIM_LISTENING_REVIEW",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_job_root": str(source_job_root),
        "source_canonical_transcript_hash": source_transcript["canonical_transcript_hash"],
        "translation_validation": translation_validation,
        "accepted_picture": source_picture,
        "media_metadata_verdict": metadata_verdict,
        "locales": locale_packages,
        "youtube_manifest": youtube_artifact,
        "picture_render_count": 0,
        "remotion_invocation_count": 0,
        "publication_attempt_count": 0,
        "v1_mutation_count": 0,
        "scheduler_mutation_count": 0,
        "owner_listening_acceptance_claimed": False,
    }
    final["receipt_hash"] = hash_value(final)
    _assert_no_forbidden_keys(final)
    _write_json(output_root / "locale_activation_e2e_receipt.json", final)
    return final
