from __future__ import annotations

import wave

import numpy as np

from live_contentops.retention_native_audio_score_v2 import CHANNELS, render_owned_score


def _written_pcm(path: str) -> np.ndarray:
    with wave.open(path, "rb") as handle:
        frames = handle.getnframes()
        payload = handle.readframes(frames)
    return np.frombuffer(payload, dtype="<i2").reshape(frames, CHANNELS)


def test_in_range_sfx_cue_has_written_energy_execution_receipt(tmp_path) -> None:
    cue = {
        "cue_id": "cue-hit",
        "beat_id": "beat-1",
        "kind": "hit",
        "at_seconds": 0.1,
    }
    score = render_owned_score(
        duration_seconds=0.6,
        state_timeline=(),
        sfx_cues=(cue,),
        output_dir=tmp_path / "first",
    )

    assert score["requested_sfx_cues"] == [cue]
    assert score["sfx_cues"] == [cue]
    assert score["requested_sfx_cue_count"] == 1
    assert score["executed_sfx_cue_count"] == 1
    assert score["skipped_sfx_cues"] == []

    receipt = score["sfx_execution_receipts"][0]
    assert receipt["cue_id"] == "cue-hit"
    assert receipt["kind"] == "hit"
    assert receipt["start_seconds"] == 0.1
    assert receipt["start_frame"] == 2_400
    assert receipt["frame_count"] == 7_680
    assert receipt["nonzero_sample_count"] > 0
    assert receipt["measured_mean_square_energy"] > 0
    assert receipt["measured_peak"] > 0
    assert receipt["energy_verified"] is True

    pcm = _written_pcm(score["sfx"]["path"])
    window = pcm[receipt["start_frame"]:receipt["start_frame"] + receipt["frame_count"]]
    normalized = window.astype(np.float64) / 32768.0
    assert receipt["nonzero_sample_count"] == int(np.count_nonzero(window))
    assert receipt["measured_mean_square_energy"] == round(float(np.mean(np.square(normalized))), 12)
    assert receipt["measured_peak"] == round(float(np.max(np.abs(normalized))), 9)

    repeated = render_owned_score(
        duration_seconds=0.6,
        state_timeline=(),
        sfx_cues=(cue,),
        output_dir=tmp_path / "repeat",
    )
    assert repeated["sfx"]["sha256"] == score["sfx"]["sha256"]
    assert repeated["sfx_execution_receipts"] == score["sfx_execution_receipts"]


def test_out_of_range_sfx_cue_is_requested_but_not_executed(tmp_path) -> None:
    cue = {
        "cue_id": "cue-too-late",
        "beat_id": "beat-2",
        "kind": "riser",
        "at_seconds": 0.5,
    }
    score = render_owned_score(
        duration_seconds=0.5,
        state_timeline=(),
        sfx_cues=(cue,),
        output_dir=tmp_path,
    )

    assert score["requested_sfx_cues"] == [cue]
    assert score["sfx_cues"] == []
    assert score["sfx_execution_receipts"] == []
    assert score["requested_sfx_cue_count"] == 1
    assert score["executed_sfx_cue_count"] == 0
    assert score["skipped_sfx_cues"] == [{
        "cue_id": "cue-too-late",
        "kind": "riser",
        "start_seconds": 0.5,
        "reason": "start_outside_score_duration",
    }]
    assert not np.any(_written_pcm(score["sfx"]["path"]))
