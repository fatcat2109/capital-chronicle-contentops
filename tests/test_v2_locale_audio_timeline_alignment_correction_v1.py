from __future__ import annotations

import copy
from pathlib import Path

import pytest

from video.locale_activation_hardening_v1.factory import (
    LocaleActivationError,
    SynthesizedPhrase,
    align_phrases_to_source_windows,
    validate_timeline_alignment,
)
from video.unattended_core_factory_v1.creative import hash_value


SOURCE_SEGMENTS = [
    {
        "segment_id": "hook",
        "timeline_start_seconds": 0.18,
        "timeline_end_seconds": 3.5,
    },
    {
        "segment_id": "close",
        "timeline_start_seconds": 4.0,
        "timeline_end_seconds": 9.5,
    },
]


def _phrase(cue_id: str, segment_id: str, duration: float) -> SynthesizedPhrase:
    return SynthesizedPhrase(
        cue_id=cue_id,
        source_segment_id=segment_id,
        text=cue_id,
        synthesis_text=cue_id,
        start_seconds=0.0,
        duration_seconds=duration,
        audio_path=str(Path("audio") / f"{cue_id}.wav"),
        audio_sha256=(cue_id * 64)[:64],
    )


def _signed_timing(timing: dict[str, object], *, speech_end: float) -> dict[str, object]:
    result = copy.deepcopy(timing)
    result.pop("timeline_alignment_hash", None)
    result.update(
        {
            "localized_audio_sha256": "a" * 64,
            "meaningful_speech_start_seconds": 0.2,
            "meaningful_speech_end_seconds": speech_end,
            "intentional_ending_silence": False,
        }
    )
    result["timeline_alignment_hash"] = hash_value(result)
    return result


def test_source_window_alignment_records_actual_segment_placements() -> None:
    phrases, timing = align_phrases_to_source_windows(
        locale="vi",
        phrases=[
            _phrase("vi-01", "hook", 1.4),
            _phrase("vi-02", "hook", 1.1),
            _phrase("vi-03", "close", 2.0),
            _phrase("vi-04", "close", 1.5),
        ],
        source_segments=SOURCE_SEGMENTS,
        picture_duration=10.0,
    )
    assert [value.source_segment_id for value in phrases] == ["hook", "hook", "close", "close"]
    assert timing["segments"][0]["actual_segment_start_seconds"] == 0.18
    assert timing["segments"][1]["actual_segment_start_seconds"] == 4.0
    assert timing["segments"][1]["actual_segment_end_seconds"] <= 9.92
    assert all(
        placement["audio_sha256"]
        for segment in timing["segments"]
        for placement in segment["placements"]
    )


def test_original_more_than_fifteen_second_tail_fixture_fails_new_timing_qa() -> None:
    _, timing = align_phrases_to_source_windows(
        locale="vi",
        phrases=[_phrase("vi-01", "hook", 1.0), _phrase("vi-02", "close", 1.0)],
        source_segments=SOURCE_SEGMENTS,
        picture_duration=20.0,
    )
    timing = _signed_timing(timing, speech_end=4.62)
    with pytest.raises(LocaleActivationError, match="unexplained_final_tail_exceeds_limit"):
        validate_timeline_alignment(
            timing,
            source_segments=SOURCE_SEGMENTS,
            picture_duration=20.0,
            strict_inside_windows=True,
        )


def test_corrected_timing_passes_and_hash_binds_actual_audio_and_placements() -> None:
    _, timing = align_phrases_to_source_windows(
        locale="vi",
        phrases=[
            _phrase("vi-01", "hook", 1.0),
            _phrase("vi-02", "close", 2.5),
            _phrase("vi-03", "close", 2.0),
        ],
        source_segments=SOURCE_SEGMENTS,
        picture_duration=10.0,
    )
    timing = _signed_timing(timing, speech_end=9.7)
    result = validate_timeline_alignment(
        timing,
        source_segments=SOURCE_SEGMENTS,
        picture_duration=10.0,
        strict_inside_windows=True,
    )
    assert result["result"] == "PASS_LOCALIZED_TIMELINE_ALIGNMENT"
    assert result["final_tail_seconds"] == pytest.approx(0.3)

    mutated = copy.deepcopy(timing)
    mutated["segments"][1]["placements"][0]["timeline_start_seconds"] += 0.01
    with pytest.raises(LocaleActivationError, match="duration_invalid|hash_mismatch"):
        validate_timeline_alignment(
            mutated,
            source_segments=SOURCE_SEGMENTS,
            picture_duration=10.0,
            strict_inside_windows=True,
        )


def test_segment_that_cannot_fit_requires_bounded_rewrite() -> None:
    with pytest.raises(LocaleActivationError, match="rewrite_required"):
        align_phrases_to_source_windows(
            locale="vi",
            phrases=[_phrase("vi-01", "hook", 4.0), _phrase("vi-02", "close", 1.0)],
            source_segments=SOURCE_SEGMENTS,
            picture_duration=10.0,
        )


def test_correction_surface_has_no_publication_v1_scheduler_or_remotion_authority() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "video"
        / "locale_activation_hardening_v1"
        / "timeline_correction.py"
    ).read_text(encoding="utf-8")
    assert "import live_contentops" not in source
    assert "import remotion" not in source.casefold()
    assert "selenium" not in source.casefold()
    assert "playwright" not in source.casefold()
    assert "-shortest" not in source
