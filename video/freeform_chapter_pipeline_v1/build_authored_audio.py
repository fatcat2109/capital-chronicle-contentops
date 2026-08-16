"""Execute an XHIGH-authored whole-film audio plan without rendering picture.

The plan owns cue selection and editorial timing.  This module is deliberately a
deterministic stem builder: it decodes rights-locked sources, synthesizes only the
declared non-documentary palette, places stems, applies conservative side-chain
ducking, and writes 48 kHz stereo buses plus a premaster WAV.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy import ndimage, signal


SR = 48_000


class AudioBuildError(RuntimeError):
    pass


def db(value: float) -> float:
    return 10 ** (value / 20)


def seed_for(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:8], "big")


def run(command: list[str]) -> None:
    executable = shutil.which(command[0])
    if executable is None:
        raise AudioBuildError(f"Missing executable: {command[0]}")
    completed = subprocess.run(
        [executable, *command[1:]],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise AudioBuildError(completed.stdout)


def read_audio(path: Path, temp: Path) -> np.ndarray:
    source = path
    if path.suffix.lower() not in {".wav", ".flac", ".aif", ".aiff"}:
        source = temp / f"{hashlib.sha256(str(path).encode()).hexdigest()[:16]}.wav"
        if not source.is_file():
            run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(path),
                    "-vn",
                    "-ar",
                    str(SR),
                    "-ac",
                    "2",
                    "-c:a",
                    "pcm_f32le",
                    str(source),
                ]
            )
    audio, sample_rate = sf.read(source, dtype="float32", always_2d=True)
    if audio.shape[1] == 1:
        audio = np.repeat(audio, 2, axis=1)
    elif audio.shape[1] > 2:
        audio = audio[:, :2]
    if sample_rate != SR:
        divisor = math.gcd(sample_rate, SR)
        audio = signal.resample_poly(audio, SR // divisor, sample_rate // divisor, axis=0)
    return np.asarray(audio, dtype=np.float32)


def filter_audio(
    audio: np.ndarray, *, high_pass: float | None = None, low_pass: float | None = None
) -> np.ndarray:
    result = audio
    if high_pass:
        sos = signal.butter(3, high_pass, btype="highpass", fs=SR, output="sos")
        result = signal.sosfilt(sos, result, axis=0).astype(np.float32)
    if low_pass:
        sos = signal.butter(3, low_pass, btype="lowpass", fs=SR, output="sos")
        result = signal.sosfilt(sos, result, axis=0).astype(np.float32)
    return result


def fade(audio: np.ndarray, fade_in: float = 0, fade_out: float = 0) -> np.ndarray:
    result = audio.copy()
    in_count = min(len(result), round(fade_in * SR))
    out_count = min(len(result), round(fade_out * SR))
    if in_count:
        result[:in_count] *= np.sin(np.linspace(0, math.pi / 2, in_count, dtype=np.float32))[:, None]
    if out_count:
        result[-out_count:] *= np.cos(np.linspace(0, math.pi / 2, out_count, dtype=np.float32))[:, None]
    return result


def stereo_width(audio: np.ndarray, percent: float) -> np.ndarray:
    mid = (audio[:, 0] + audio[:, 1]) * 0.5
    side = (audio[:, 0] - audio[:, 1]) * 0.5 * (percent / 100)
    return np.column_stack((mid + side, mid - side)).astype(np.float32)


def place(bus: np.ndarray, clip: np.ndarray, at_seconds: float) -> None:
    start = max(0, round(at_seconds * SR))
    if start >= len(bus):
        return
    end = min(len(bus), start + len(clip))
    bus[start:end] += clip[: end - start]


def pink_noise(count: int, rng: np.random.Generator) -> np.ndarray:
    white = rng.standard_normal(count).astype(np.float32)
    spectrum = np.fft.rfft(white)
    frequencies = np.fft.rfftfreq(count, 1 / SR)
    spectrum[1:] /= np.sqrt(frequencies[1:])
    spectrum[0] = 0
    noise = np.fft.irfft(spectrum, n=count).astype(np.float32)
    peak = float(np.max(np.abs(noise))) or 1
    return noise / peak


def noise_region(
    asset: str,
    duration: float,
    seed: str,
    *,
    omit_partial: float | None = None,
    low_pass_override: float | None = None,
) -> np.ndarray:
    count = max(1, round(duration * SR))
    rng = np.random.default_rng(seed_for(seed))
    if asset == "FLUORESCENT_AIR":
        t = np.arange(count, dtype=np.float32) / SR
        mono = rng.standard_normal(count).astype(np.float32) * db(-48)
        mono = filter_audio(mono[:, None], low_pass=1800)[:, 0]
        for frequency, level in ((60, -34), (120, -38), (240, -46)):
            if omit_partial == frequency:
                continue
            mono += np.sin(2 * np.pi * frequency * t).astype(np.float32) * db(level)
        mono *= 0.93 + 0.07 * np.sin(2 * np.pi * 0.11 * t)
        return np.column_stack((mono, mono))
    mono = pink_noise(count, rng)
    if asset == "DISTANT_TRANSIT_AIR":
        mono = filter_audio(mono[:, None], high_pass=85, low_pass=720)[:, 0]
        t = np.arange(count, dtype=np.float32) / SR
        mono += np.sin(2 * np.pi * 126 * t).astype(np.float32) * db(-18)
        left = mono * (0.88 + 0.12 * np.sin(2 * np.pi * 0.045 * t))
        right = mono * (0.88 - 0.12 * np.sin(2 * np.pi * 0.045 * t))
        return np.column_stack((left, right)).astype(np.float32)
    cutoff = low_pass_override or 1600
    mono = filter_audio(mono[:, None], high_pass=55, low_pass=cutoff)[:, 0]
    delay = min(round(0.012 * SR), count - 1)
    right = np.roll(mono, delay)
    right[:delay] = 0
    return np.column_stack((mono, right)).astype(np.float32)


def envelope(count: int, attack: float, release: float) -> np.ndarray:
    attack_count = min(count, max(1, round(attack * SR)))
    release_count = min(count - attack_count, max(1, round(release * SR)))
    result = np.ones(count, dtype=np.float32)
    result[:attack_count] = np.linspace(0, 1, attack_count, dtype=np.float32)
    if release_count:
        result[-release_count:] = np.linspace(1, 0, release_count, dtype=np.float32)
    return result


def effect(asset: str, seed: str, peak_dbfs: float, **options: Any) -> np.ndarray:
    rng = np.random.default_rng(seed_for(seed))
    if asset in {"PAPER_RELAY", "PAPER_FRICTION"}:
        duration = 0.23 if asset == "PAPER_RELAY" else 0.68
        count = round(duration * SR)
        mono = pink_noise(count, rng)
        low, high = (620, 4600) if asset == "PAPER_RELAY" else (420, 3200)
        sos = signal.butter(3, [low, high], btype="bandpass", fs=SR, output="sos")
        mono = signal.sosfilt(sos, mono).astype(np.float32)
        mono *= envelope(count, 0.002 if asset == "PAPER_RELAY" else 0.04, duration * 0.82)
        if asset == "PAPER_RELAY":
            t = np.arange(count, dtype=np.float32) / SR
            mono += np.sin(2 * np.pi * 118 * t).astype(np.float32) * envelope(count, 0.002, 0.055) * db(-20)
    elif asset == "RAIL_TICK":
        count = round(0.14 * SR)
        mono = rng.standard_normal(count).astype(np.float32)
        sos = signal.butter(3, [1200, 4800], btype="bandpass", fs=SR, output="sos")
        mono = signal.sosfilt(sos, mono).astype(np.float32)
        mono *= envelope(count, 0.001, 0.12)
        t = np.arange(count, dtype=np.float32) / SR
        mono += np.sin(2 * np.pi * 920 * t).astype(np.float32) * np.exp(-t / 0.035)
    elif asset in {"CC_TONAL_MOTIF", "STATE_AIR_APERTURE"}:
        if asset == "STATE_AIR_APERTURE":
            count = round(0.35 * SR)
            mono = pink_noise(count, rng)
            sos = signal.butter(3, [180, 1200], btype="bandpass", fs=SR, output="sos")
            mono = signal.sosfilt(sos, mono).astype(np.float32)
            mono *= envelope(count, 0.09, 0.21)
        else:
            count = round(1.9 * SR)
            t = np.arange(count, dtype=np.float32) / SR
            mono = (2 / np.pi * np.arcsin(np.sin(2 * np.pi * 73.42 * t))).astype(np.float32)
            if not options.get("omit_partial_hz"):
                mono += np.sin(2 * np.pi * 110 * t).astype(np.float32) * 0.35
            mono *= envelope(count, 0.07, 1.8)
    elif asset == "MECHANICAL_128":
        count = round(0.12 * SR)
        t = np.arange(count, dtype=np.float32) / SR
        mono = np.sin(2 * np.pi * 66 * t).astype(np.float32) * envelope(count, 0.003, 0.09)
        mono += rng.standard_normal(count).astype(np.float32) * envelope(count, 0.001, 0.045) * 0.25
    else:
        raise AudioBuildError(f"Unsupported effect asset: {asset}")
    peak = float(np.max(np.abs(mono))) or 1
    mono = mono / peak * db(peak_dbfs)
    pan = float(options.get("pan_percent", 0)) / 100
    return np.column_stack((mono * (1 - max(0, pan)), mono * (1 + min(0, pan)))).astype(np.float32)


def add_flow_pulse(bus: np.ndarray, region: dict[str, Any]) -> None:
    start = region["film_in_seconds"]
    end = region["film_out_seconds"]
    level = db(region["gain_db"])
    layer_specs = {item["layer_id"]: item for item in region["layers"]}
    intervals = {"A": 60 / 80 / 2, "B": 60 / 80, "C": 60 / 80 * 2}
    frequencies = {"A": 920.0, "B": 146.0, "C": 73.42}
    durations = {"A": 0.08, "B": 0.15, "C": 0.26}
    for layer in ("A", "B", "C"):
        cursor = start + (intervals[layer] if layer == "A" else 0)
        while cursor < min(end, layer_specs[layer]["remove_at_seconds"]):
            count = round(durations[layer] * SR)
            t = np.arange(count, dtype=np.float32) / SR
            if layer == "A":
                mono = np.sin(2 * np.pi * frequencies[layer] * t) * np.exp(-t / 0.025)
            elif layer == "B":
                mono = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * frequencies[layer] * t))
            else:
                mono = np.sin(2 * np.pi * frequencies[layer] * t)
            mono = mono.astype(np.float32) * envelope(count, 0.005, durations[layer] * 0.9) * level
            place(bus, np.column_stack((mono, mono)), cursor)
            cursor += intervals[layer]


def add_mechanical_region(bus: np.ndarray, region: dict[str, Any]) -> None:
    beat = 60 / 128
    start = float(region["film_in_seconds"])
    end = float(region["film_out_seconds"])
    cursor = start
    bar = 0
    while cursor < end:
        hit_offsets = (0, 1.5 * beat, 3 * beat) if region["id"].endswith("A") else (0, 2 * beat, 1.5 * beat, 3.5 * beat)
        for index, offset in enumerate(hit_offsets):
            when = cursor + offset
            if when >= end:
                continue
            if region["id"].endswith("A") and bar % 4 == 3 and index == 0:
                continue
            clip = effect("MECHANICAL_128", f"{region['id']}_{bar}_{index}", region["gain_db"])
            place(bus, clip, when)
        cursor += beat * 4
        bar += 1


def duck_envelope(bus: np.ndarray) -> np.ndarray:
    active = (np.max(np.abs(bus), axis=1) > 0.006).astype(np.float32)
    held = ndimage.maximum_filter1d(active, size=round(0.22 * SR), mode="constant")
    return ndimage.uniform_filter1d(held, size=round(0.09 * SR), mode="nearest")


def build(plan_path: Path, output_dir: Path) -> dict[str, Any]:
    plan_path = plan_path.resolve()
    root = plan_path.parent
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    total_frames = int(plan["timebase"]["total_frames"])
    count = round(total_frames / float(plan["timebase"]["fps"]) * SR)
    output_dir.mkdir(parents=True, exist_ok=True)

    narration = np.zeros((count, 2), dtype=np.float32)
    authority = np.zeros_like(narration)
    music = np.zeros_like(narration)
    designed = np.zeros_like(narration)

    with tempfile.TemporaryDirectory(prefix="fwb-audio-") as temp_name:
        temp = Path(temp_name)
        for stem in plan["narration"]["stems"]:
            clip = read_audio(root / stem["path"], temp) * db(float(stem.get("gain_db", 0)))
            clip = filter_audio(clip, high_pass=70)
            place(narration, clip, float(stem["film_start_seconds"]))

        for edit in plan["authority_edits"]:
            source = read_audio(root / edit["path"], temp)
            source_start = round(float(edit["source_in_seconds"]) * SR)
            source_end = round(float(edit["source_out_seconds"]) * SR)
            clip = source[source_start:source_end] * db(float(edit["gain_db"]))
            local_fade_out_start = float(edit["fade_out_start_seconds"]) - float(edit["film_in_seconds"])
            clip = fade(
                clip,
                float(edit.get("fade_in_seconds", 0)),
                max(0, len(clip) / SR - local_fade_out_start),
            )
            clip = filter_audio(clip, high_pass=55)
            place(authority, clip, float(edit["film_in_seconds"]))

        music_sources = {
            item["id"]: read_audio(root / item["path"], temp)
            for item in plan["music_sources"]
        }
        for cue in plan["music_cues"]:
            source = music_sources[cue["source_id"]]
            start = round(float(cue["source_in_seconds"]) * SR)
            end = round(float(cue["source_out_seconds"]) * SR)
            clip = source[start:end]
            wanted = round((float(cue["film_out_seconds"]) - float(cue["film_in_seconds"])) * SR)
            clip = clip[:wanted]
            clip = filter_audio(
                clip,
                high_pass=cue.get("high_pass_hz"),
                low_pass=cue.get("low_pass_hz"),
            )
            clip = stereo_width(clip, float(cue.get("stereo_width_percent", 100)))
            clip = fade(clip, float(cue["fade_in_seconds"]), float(cue["fade_out_seconds"]))
            clip *= db(float(cue["gain_db"]))
            place(music, clip, float(cue["film_in_seconds"]))

    for region in plan["ambience_regions"]:
        duration = float(region["film_out_seconds"]) - float(region["film_in_seconds"])
        clip = noise_region(
            region["asset_id"],
            duration,
            region["id"],
            omit_partial=region.get("omit_partial_hz"),
            low_pass_override=region.get("low_pass_hz_override"),
        )
        if region.get("stereo_width_percent") is not None:
            clip = stereo_width(clip, float(region["stereo_width_percent"]))
        if region.get("linear_gain_change_db"):
            ramp = np.linspace(0, float(region["linear_gain_change_db"]), len(clip), dtype=np.float32)
            clip *= np.power(10, ramp / 20)[:, None]
        clip = fade(clip, float(region.get("fade_in_seconds", 0)), float(region.get("fade_out_seconds", 0)))
        clip *= db(float(region["gain_db"]))
        place(designed, clip, float(region["film_in_seconds"]))

    for region in plan["continuous_tonal_regions"]:
        duration = float(region["film_out_seconds"]) - float(region["film_in_seconds"])
        tone_count = round(duration * SR)
        t = np.arange(tone_count, dtype=np.float32) / SR
        mono = (2 / np.pi * np.arcsin(np.sin(2 * np.pi * 73.42 * t))).astype(np.float32)
        mono += np.sin(2 * np.pi * 146.84 * t).astype(np.float32) * db(-18)
        clip = np.column_stack((mono, mono)) * db(float(region["gain_db"]))
        clip = fade(clip, float(region["fade_in_seconds"]), float(region["fade_out_seconds"]))
        place(designed, clip, float(region["film_in_seconds"]))

    for region in plan["pulse_regions"]:
        if region["asset_id"] == "FLOW_PULSE":
            add_flow_pulse(designed, region)
        else:
            add_mechanical_region(designed, region)

    for event in plan["effects_events"]:
        event_options = {
            key: value
            for key, value in event.items()
            if key not in {"asset_id", "peak_dbfs"}
        }
        clip = effect(
            event["asset_id"],
            f"FWB_AUDIO_EDIT_XHIGH_V1_{event.get('seed_suffix', event['id'])}",
            float(event["peak_dbfs"]),
            **event_options,
        )
        place(designed, clip, float(event["film_seconds"]))

    narr_duck = duck_envelope(narration)
    auth_duck = duck_envelope(authority)
    music *= np.power(10, (-3.5 * narr_duck - 5.5 * auth_duck) / 20)[:, None]
    designed *= np.power(10, (-2.0 * narr_duck) / 20)[:, None]
    premaster = narration + authority + music + designed
    premaster[-round(2 * SR) :] = 0

    outputs = {
        "narration_bus": output_dir / "narration_bus.wav",
        "authority_bus": output_dir / "authority_bus.wav",
        "music_bus": output_dir / "music_bus.wav",
        "designed_bus": output_dir / "designed_bus.wav",
        "premaster": output_dir / "premaster.wav",
    }
    for key, path in outputs.items():
        data = premaster if key == "premaster" else locals()[key.removesuffix("_bus")]
        sf.write(path, data, SR, subtype="PCM_24")

    result = {
        "schema": "contentops.v2.authored_audio_build_receipt.v1",
        "plan": str(plan_path),
        "sample_rate_hz": SR,
        "channels": 2,
        "duration_seconds": count / SR,
        "final_silence_seconds": 2,
        "outputs": {
            key: {
                "path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
            }
            for key, path in outputs.items()
        },
    }
    receipt = output_dir / "audio_build_receipt.json"
    receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.plan, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
