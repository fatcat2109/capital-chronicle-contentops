from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from video.locale_activation_hardening_v1.factory import (
    MANDATORY_LOCALES,
    LocaleActivationError,
    _caption_lines,
    inspect_picture,
    media_metadata_verdict,
    mux_picture_identical_locale,
    validate_translation_packet,
)
from video.unattended_core_factory_v1.creative import hash_value
from video.unattended_core_factory_v1.transcript import normalize_english_spoken_numbers


REPO = Path(__file__).resolve().parents[1]
TRANSLATIONS = (
    REPO / "video" / "locale_activation_hardening_v1" / "us_retail_locales_v1.json"
)
SOURCE_TEXT = {
    "hook": "Start with the July retail headline. Then look underneath it.",
    "topline": "U.S. retail and food services sales were $763.6 billion in July 2026, down 0.6 percent from June and up 5.0 percent from July 2025.",
    "pivot": "So where did the monthly change actually appear?",
    "core_measure": "Sales excluding motor vehicles and gasoline were down 0.2 percent from June and up 4.8 percent from July 2025.",
    "vehicles": "Motor vehicle and parts dealer sales fell 1.8 percent from June.",
    "nonstore": "Nonstore retailer sales fell 2.2 percent from June.",
    "food_service": "Food services and drinking place sales rose 0.5 percent from June.",
    "caveat_setup": "Before turning that mix into a consumer verdict, keep the measurement limit in view.",
    "measurement": "The Census sales estimates are adjusted for seasonal, holiday, and trading-day differences but not for price changes.",
    "close": "One release, several directions, and a headline that needs its footnote.",
}


def _packet() -> dict[str, object]:
    return json.loads(TRANSLATIONS.read_text(encoding="utf-8"))


def _source_transcript(packet: dict[str, object]) -> dict[str, object]:
    first_locale = packet["locales"]["zh-Hans"]  # type: ignore[index]
    segments = []
    for item in first_locale["segments"]:  # type: ignore[index]
        text = SOURCE_TEXT[item["segment_id"]]
        segments.append(
            {
                "segment_id": item["segment_id"],
                "text": text,
                "segment_text_sha256": hash_value(text),
            }
        )
    return {
        "canonical_transcript_hash": packet["source_canonical_transcript_hash"],
        "segments": segments,
    }


def test_decimal_verbalization_preserves_sign_fraction_currency_units_and_trailing_zero() -> None:
    spoken = normalize_english_spoken_numbers(
        "0.1%, 0.3 percent, 272.5 kg, 264.0, -0.2 pp, $763.6 billion, and "
        + chr(0x20AC)
        + "12.0 million."
    )
    assert "zero point one percent" in spoken
    assert "zero point three percent" in spoken
    assert "two hundred seventy two point five kilograms" in spoken
    assert "two hundred sixty four point zero" in spoken
    assert "negative zero point two percentage points" in spoken
    assert "seven hundred sixty three point six billion dollars" in spoken
    assert "twelve point zero million euros" in spoken


def test_all_mandatory_translations_bind_source_numeric_entity_direction_and_negation() -> None:
    packet = _packet()
    result = validate_translation_packet(packet, _source_transcript(packet))
    assert result["result"] == "PASS_GOVERNED_TRANSLATION_PACKET"
    assert tuple(result["locales"]) == MANDATORY_LOCALES
    assert all(
        value["result"] == "PASS_TRANSLATION_TRUTH_INVARIANTS"
        for value in result["locales"].values()
    )


@pytest.mark.parametrize("locale", MANDATORY_LOCALES)
def test_translation_fails_closed_if_decimal_or_negation_spoken_surface_is_lost(locale: str) -> None:
    packet = _packet()
    broken = copy.deepcopy(packet)
    topline = broken["locales"][locale]["segments"][1]
    anchor = next(value for value in topline["truth_anchors"] if value["id"] == "DOWN_0_6_PERCENT")
    topline["synthesis_text"] = topline["synthesis_text"].replace(anchor["spoken_surface"], "")
    with pytest.raises(LocaleActivationError, match="anchor_surface_missing"):
        validate_translation_packet(broken, _source_transcript(packet))

    broken = copy.deepcopy(packet)
    measurement = broken["locales"][locale]["segments"][8]
    anchor = next(value for value in measurement["truth_anchors"] if value["id"] == "NEGATION_PRICE")
    measurement["text"] = measurement["text"].replace(anchor["display_surface"], "")
    with pytest.raises(LocaleActivationError, match="anchor_surface_missing"):
        validate_translation_packet(broken, _source_transcript(packet))


def test_locale_a_cannot_satisfy_locale_b_identity() -> None:
    packet = _packet()
    broken = copy.deepcopy(packet)
    broken["locales"]["ko"] = copy.deepcopy(packet["locales"]["vi"])
    with pytest.raises(LocaleActivationError, match="localized_locale_identity_mismatch:ko"):
        validate_translation_packet(broken, _source_transcript(packet))


def test_caption_wrapping_is_at_most_two_mobile_lines_for_cjk_and_latin() -> None:
    for locale, text in (
        ("zh-Hans", "美国零售和餐饮服务销售额较上月下降百分之零点六。"),
        ("ko", "미국 소매 외식 서비스 매출은 전월보다 감소했습니다."),
        ("vi", "Doanh số bán lẻ và dịch vụ ăn uống của Mỹ giảm so với tháng trước."),
        ("hi", "अमेरिकी खुदरा और खाद्य सेवा बिक्री पिछले महीने से कम रही।"),
    ):
        wrapped = _caption_lines(text, locale=locale)
        assert len(wrapped.splitlines()) <= 2


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg required")
def test_stream_copy_mux_preserves_picture_frames_when_audio_is_shorter(tmp_path: Path) -> None:
    picture = tmp_path / "picture.mp4"
    audio = tmp_path / "short.wav"
    output = tmp_path / "localized.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x102030:s=320x568:r=30:d=2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            picture,
        ],
        check=True,
    )
    sf.write(audio, np.zeros(24_000, dtype=np.float32), 24_000)
    source = inspect_picture(picture)
    proof = mux_picture_identical_locale(
        picture=picture, audio=audio, output=output, source_picture=source
    )
    assert proof["result"] == "PASS_PICTURE_STREAM_AND_FRAME_IDENTITY"
    assert proof["ffmpeg_shortest_used"] is False
    assert proof["localized_mux"]["frame_count"] == 60
    assert proof["localized_mux"]["video_stream_sha256"] == source["video_stream_sha256"]


def test_full_range_observation_does_not_trigger_speculative_picture_transcode() -> None:
    verdict = media_metadata_verdict({"pixel_format": "yuvj420p", "color_range": "pc"})
    assert verdict["objectively_required_correction"] is False
    assert verdict["shared_normalized_base_picture"] is None


def test_locale_module_has_zero_publication_v1_scheduler_or_remotion_surface() -> None:
    source = (
        REPO / "video" / "locale_activation_hardening_v1" / "factory.py"
    ).read_text(encoding="utf-8")
    assert "import live_contentops" not in source
    assert "import remotion" not in source.casefold()
    assert "selenium" not in source.casefold()
    assert "playwright" not in source.casefold()
    assert "-shortest" not in source
