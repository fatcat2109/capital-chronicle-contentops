"""Deterministic, locally synthesized music and restrained SFX for V2 proofs.

The score contains no samples, model output, or third-party musical material.  It
is generated from oscillators and seeded noise, making the rendered WAVs
Capital Chronicle-owned proof assets with reproducible provenance.
"""
from __future__ import annotations

import hashlib
import json
import math
import wave
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


SCORE_GENERATOR_VERSION = "contentops.retention_native.score.v2.2"
SAMPLE_RATE = 24_000
CHANNELS = 2


_STATE_CHORDS = {
    "cold_open": (55.0, (220.00, 261.63, 329.63)),
    "tension": (73.42, (220.00, 261.63, 329.63)),
    "evidence": (65.41, (196.00, 246.94, 293.66)),
    "mechanism": (55.0, (220.00, 261.63, 329.63)),
    "consequence": (65.41, (196.00, 246.94, 329.63)),
    "boundary": (49.00, (196.00, 233.08, 293.66)),
    "resolution": (65.41, (196.00, 261.63, 329.63)),
    "outro": (65.41, (196.00, 261.63, 329.63)),
}


def render_owned_score(
    *,
    duration_seconds: float,
    state_timeline: Sequence[Mapping[str, Any]],
    sfx_cues: Sequence[Mapping[str, Any]],
    output_dir: str | Path,
) -> dict[str, Any]:
    if duration_seconds <= 0:
        raise ValueError("score_duration_must_be_positive")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    music_path = root / "owned_music_bed.wav"
    sfx_path = root / "owned_sfx.wav"
    _render_music(duration_seconds, state_timeline, music_path)
    sfx_result = _render_sfx(duration_seconds, sfx_cues, sfx_path)
    result = {
        "schema_version": SCORE_GENERATOR_VERSION,
        "status": "PASS",
        "generator": "deterministic_numpy_oscillators_and_seeded_noise",
        "source_samples": [],
        "model_calls": 0,
        "network_calls": 0,
        "rights_status": "CAPITAL_CHRONICLE_OWNED",
        "license_or_terms": "Original local procedural score; no third-party samples or model output.",
        "duration_seconds": round(duration_seconds, 3),
        "sample_rate": SAMPLE_RATE,
        "channels": CHANNELS,
        "music": _media_row(music_path),
        "sfx": _media_row(sfx_path),
        "state_timeline": [dict(row) for row in state_timeline],
        "requested_sfx_cues": [dict(row) for row in sfx_cues],
        # Compatibility field: unlike the historical receipt, this contains only
        # cues that were actually mixed into the written stem.
        "sfx_cues": sfx_result["executed_cues"],
        "sfx_execution_receipts": sfx_result["execution_receipts"],
        "skipped_sfx_cues": sfx_result["skipped_cues"],
        "requested_sfx_cue_count": len(sfx_cues),
        "executed_sfx_cue_count": len(sfx_result["executed_cues"]),
    }
    (root / "audio_score_provenance.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _state_at(second: float, timeline: Sequence[Mapping[str, Any]]) -> str:
    for row in timeline:
        if float(row.get("start_seconds", 0)) <= second < float(row.get("end_seconds", 0)):
            return str(row.get("state") or "evidence")
    return "outro"


def _render_music(duration: float, timeline: Sequence[Mapping[str, Any]], output: Path) -> None:
    frames_total = int(math.ceil(duration * SAMPLE_RATE))
    tempo = 86.0
    beat_seconds = 60.0 / tempo
    chunk_frames = SAMPLE_RATE * 2
    with wave.open(str(output), "wb") as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        for start in range(0, frames_total, chunk_frames):
            count = min(chunk_frames, frames_total - start)
            t = (np.arange(count, dtype=np.float64) + start) / SAMPLE_RATE
            center = (start + count / 2) / SAMPLE_RATE
            state = _state_at(center, timeline)
            root, chord = _STATE_CHORDS.get(state, _STATE_CHORDS["evidence"])
            intensity = {
                "cold_open": 0.54,
                "tension": 0.95,
                "evidence": 0.66,
                "mechanism": 0.78,
                "consequence": 0.83,
                "boundary": 0.48,
                "resolution": 0.68,
                "outro": 0.42,
            }.get(state, 0.62)
            slow = 0.72 + 0.28 * np.sin(2 * np.pi * 0.065 * t)
            left = np.zeros(count, dtype=np.float64)
            right = np.zeros(count, dtype=np.float64)
            for index, frequency in enumerate(chord):
                phase = index * 0.71
                left += np.sin(2 * np.pi * frequency * t + phase)
                left += 0.18 * np.sin(2 * np.pi * frequency * 2 * t + phase / 2)
                right += np.sin(2 * np.pi * frequency * t + phase + 0.08 * (index + 1))
                right += 0.18 * np.sin(2 * np.pi * frequency * 2 * t + phase / 2 + 0.04)
            left *= 0.017 * intensity * slow
            right *= 0.017 * intensity * slow
            left += 0.036 * intensity * np.sin(2 * np.pi * root * t)
            right += 0.036 * intensity * np.sin(2 * np.pi * root * t + 0.035)

            beat_position = np.mod(t, beat_seconds)
            beat_number = np.floor(t / beat_seconds).astype(np.int64)
            arp_index = np.mod(beat_number, len(chord))
            arp_frequency = np.take(np.asarray(chord), arp_index)
            pluck = np.exp(-beat_position * 8.5) * np.sin(2 * np.pi * arp_frequency * 2 * t)
            left += 0.026 * intensity * pluck
            right += 0.023 * intensity * np.exp(-beat_position * 8.0) * np.sin(2 * np.pi * arp_frequency * 2 * t + 0.1)

            kick_position = np.mod(t, beat_seconds * 2)
            kick_env = np.exp(-kick_position * 18.0)
            kick = np.sin(2 * np.pi * (48.0 + 32.0 * np.exp(-kick_position * 20.0)) * t) * kick_env
            left += 0.024 * intensity * kick
            right += 0.024 * intensity * kick

            fade = np.ones(count, dtype=np.float64)
            fade_in = np.clip(t / 1.2, 0, 1)
            fade_out = np.clip((duration - t) / 1.8, 0, 1)
            fade *= np.minimum(fade_in, fade_out)
            stereo = np.column_stack((left * fade, right * fade))
            pcm = np.clip(stereo, -0.92, 0.92)
            handle.writeframes((pcm * 32767).astype("<i2").tobytes())


def _render_sfx(
    duration: float,
    cues: Sequence[Mapping[str, Any]],
    output: Path,
) -> dict[str, list[dict[str, Any]]]:
    frames_total = int(math.ceil(duration * SAMPLE_RATE))
    stereo = np.zeros((frames_total, 2), dtype=np.float32)
    executed_cues: list[dict[str, Any]] = []
    execution_plan: list[dict[str, Any]] = []
    skipped_cues: list[dict[str, Any]] = []
    for index, cue in enumerate(cues):
        start_seconds = float(cue.get("at_seconds", 0))
        cue_id = str(cue.get("cue_id") or f"sfx-cue-{index + 1:04d}")
        kind = str(cue.get("kind") or "tick")
        if not 0 <= start_seconds < duration:
            skipped_cues.append({
                "cue_id": cue_id,
                "kind": kind,
                "start_seconds": round(start_seconds, 6),
                "reason": "start_outside_score_duration",
            })
            continue
        cue_duration = {"whoosh": 0.52, "riser": 0.82, "hit": 0.32, "data_tick": 0.18}.get(kind, 0.22)
        start_frame = int(start_seconds * SAMPLE_RATE)
        count = min(int(cue_duration * SAMPLE_RATE), frames_total - start_frame)
        if count <= 0:
            skipped_cues.append({
                "cue_id": cue_id,
                "kind": kind,
                "start_seconds": round(start_seconds, 6),
                "reason": "no_frames_inside_score_duration",
            })
            continue
        local = np.arange(count, dtype=np.float64) / SAMPLE_RATE
        if kind == "whoosh":
            rng = np.random.default_rng(3100 + index)
            noise = rng.standard_normal(count)
            envelope = np.sin(np.pi * np.clip(local / cue_duration, 0, 1)) ** 2
            signal = 0.07 * envelope * noise + 0.025 * envelope * np.sin(2 * np.pi * (180 + 900 * local / cue_duration) * local)
        elif kind == "riser":
            envelope = np.sin(np.pi * np.clip(local / cue_duration, 0, 1)) ** 1.4
            signal = 0.085 * envelope * np.sin(2 * np.pi * (110 + 520 * (local / cue_duration) ** 2) * local)
        elif kind == "hit":
            envelope = np.exp(-local * 13)
            signal = 0.16 * envelope * (np.sin(2 * np.pi * 62 * local) + 0.34 * np.sin(2 * np.pi * 124 * local))
        else:
            envelope = np.exp(-local * 22)
            signal = 0.08 * envelope * np.sin(2 * np.pi * 1040 * local)
        pan = -0.18 if index % 2 == 0 else 0.18
        stereo[start_frame:start_frame + count, 0] += signal * (1 - pan) * 0.5
        stereo[start_frame:start_frame + count, 1] += signal * (1 + pan) * 0.5
        executed_cues.append(dict(cue))
        execution_plan.append({
            "cue_id": cue_id,
            "kind": kind,
            "start_seconds": round(start_seconds, 6),
            "start_frame": start_frame,
            "frame_count": count,
        })
    with wave.open(str(output), "wb") as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes((np.clip(stereo, -0.92, 0.92) * 32767).astype("<i2").tobytes())
    return {
        "executed_cues": executed_cues,
        "execution_receipts": _measure_written_sfx_windows(output, execution_plan),
        "skipped_cues": skipped_cues,
    }


def _measure_written_sfx_windows(
    output: Path,
    execution_plan: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Measure cue energy from the PCM bytes that were actually written."""

    with wave.open(str(output), "rb") as handle:
        if handle.getnchannels() != CHANNELS:
            raise ValueError("sfx_stem_channel_count_mismatch")
        if handle.getsampwidth() != 2:
            raise ValueError("sfx_stem_sample_width_mismatch")
        if handle.getframerate() != SAMPLE_RATE:
            raise ValueError("sfx_stem_sample_rate_mismatch")
        frame_count = handle.getnframes()
        pcm_bytes = handle.readframes(frame_count)
    pcm = np.frombuffer(pcm_bytes, dtype="<i2")
    if pcm.size != frame_count * CHANNELS:
        raise ValueError("sfx_stem_frame_count_mismatch")
    pcm = pcm.reshape(frame_count, CHANNELS)

    receipts: list[dict[str, Any]] = []
    for planned in execution_plan:
        start_frame = int(planned["start_frame"])
        planned_frames = int(planned["frame_count"])
        window = pcm[start_frame:start_frame + planned_frames]
        normalized = window.astype(np.float64) / 32768.0
        nonzero_sample_count = int(np.count_nonzero(window))
        mean_square_energy = float(np.mean(np.square(normalized))) if normalized.size else 0.0
        peak = float(np.max(np.abs(normalized))) if normalized.size else 0.0
        receipts.append({
            "cue_id": str(planned["cue_id"]),
            "kind": str(planned["kind"]),
            "start_seconds": float(planned["start_seconds"]),
            "start_frame": start_frame,
            "frame_count": int(window.shape[0]),
            "nonzero_sample_count": nonzero_sample_count,
            "measured_mean_square_energy": round(mean_square_energy, 12),
            "measured_peak": round(peak, 9),
            "energy_verified": bool(
                window.shape[0] == planned_frames
                and nonzero_sample_count > 0
                and mean_square_energy > 0.0
                and peak > 0.0
            ),
        })
    return receipts


def _media_row(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path), "sha256": digest, "size_bytes": path.stat().st_size}
