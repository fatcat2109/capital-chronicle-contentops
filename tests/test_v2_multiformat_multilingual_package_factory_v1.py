from __future__ import annotations

import json
from pathlib import Path

import pytest

from video.freeform_chapter_pipeline_v1.package_factory import (
    PackageFactoryError,
    build_caption_cues,
    build_publication_package,
    caption_text,
    load_locale_registry,
    validate_anchor_preservation,
    validate_caption_set,
    validate_media_probe,
)


REPO = Path(__file__).resolve().parents[1]
LOCALES = REPO / "video" / "freeform_chapter_pipeline_v1" / "locale_profiles.json"


def _artifact(tmp_path: Path, name: str, payload: bytes) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _package_spec(tmp_path: Path, *, language: str = "es") -> dict[str, object]:
    picture = _artifact(tmp_path, "picture.mp4", b"same accepted picture")
    audio = _artifact(tmp_path, f"audio-{language}.wav", language.encode("utf-8"))
    captions = _artifact(tmp_path, f"captions-{language}.json", b"{}")
    srt = _artifact(tmp_path, f"captions-{language}.srt", b"1\n")
    vtt = _artifact(tmp_path, f"captions-{language}.vtt", b"WEBVTT\n")
    return {
        "source_story_id": "frozen_without_breaking",
        "source_film_id": "frozen_without_breaking_owner_polish_v1",
        "format": "LONGFORM_16_9",
        "language": language,
        "canonical_picture": str(picture),
        "burned_caption_video": None,
        "audio": str(audio),
        "caption_json": str(captions),
        "caption_srt": str(srt),
        "caption_vtt": str(vtt),
        "metadata": {
            "title": f"Title {language}",
            "description": f"Description {language}",
        },
        "chapters": [{"start_seconds": 0, "title": "Opening"}],
        "rights_provenance_refs": ["rights-sha256"],
        "factual_evidence_refs": ["facts-sha256"],
        "intended_future_surfaces": ["YOUTUBE_NORMAL_VIDEO"],
        "generation_version": "v1",
        "generation_timestamp_utc": "2026-08-16T00:00:00Z",
        "delivery_policy": {
            "picture_render_scope": "ONCE_PER_EDITORIAL_FORMAT",
            "locale_picture_render_default": False,
            "burned_captions": "OPTIONAL_ONLY_EXACT_AUTHORITY_REQUIRED",
            "recurring_locale_creative_xhigh": False,
        },
        "hard_boundaries": {
            "video_public_write_authority": False,
            "v1_mutation_authority": False,
            "scheduler_mutation_authority": False,
            "allow_4k": False,
        },
    }


def test_locale_registry_is_configurable_and_does_not_claim_unproven_support() -> None:
    registry = load_locale_registry(LOCALES)

    assert set(registry["profiles"]["CORE_ALWAYS_ON"]) == {
        "en", "es", "pt-BR", "zh-Hans", "hi", "id", "ar", "vi", "ja", "ko", "fr", "de"
    }
    assert set(registry["profiles"]["EXPANSION_CONFIGURED"]) == {
        "zh-Hant", "bn", "ta", "te", "mr", "ur", "fil", "tr", "ru", "th", "it"
    }
    assert registry["locales"]["en"]["support_status"] == "CANONICAL_EXISTING"
    assert all(
        registry["locales"][tag]["support_status"]
        == "PROOF_COMPLETE_OWNER_VOICE_REVIEW_REQUIRED"
        for tag in ("es", "pt-BR", "ja")
    )
    assert "configuration_rule" in registry


def test_factual_anchor_guard_checks_actual_localized_surfaces() -> None:
    contract = {
        "source_story_id": "frozen_without_breaking",
        "anchors": [
            {
                "id": "EMP002_VALUE",
                "kind": "NUMBER_PERCENT_UNIT",
                "accepted_forms": {"es": ["4,1 %", "4,1%"]},
            },
            {
                "id": "EMP011_DIRECTION",
                "kind": "DIRECTION",
                "accepted_forms": {"es": ["cayó en 87.000", "descendió en 87.000"]},
            },
            {
                "id": "UNCERTAINTY",
                "kind": "UNCERTAINTY",
                "accepted_forms": {"es": ["preliminar"]},
            },
        ],
    }
    payload = {
        "language": "es",
        "localized_fields": {
            "narration": "El empleo de hogares cayó en 87.000 y la tasa fue 4,1 %.",
            "description": "Lectura preliminar, no una predicción.",
        },
    }

    result = validate_anchor_preservation(contract, payload)
    assert result["result"] == "PASS_FACTUAL_ANCHORS"
    assert all(item["result"] == "PRESERVED" for item in result["anchors"])

    payload["localized_fields"]["description"] = "Una predicción definitiva."
    failed = validate_anchor_preservation(contract, payload)
    assert failed["result"] == "FAIL_FACTUAL_ANCHORS"
    assert failed["failures"] == ["UNCERTAINTY"]


def test_caption_timing_comes_from_actual_segment_duration_and_supports_cjk() -> None:
    caption_set = build_caption_cues(
        language="ja",
        media_duration_seconds=8.0,
        segments=[
            {
                "cue_id": "ja-1",
                "timeline_start_seconds": 0.5,
                "actual_audio_duration_seconds": 2.25,
                "caption_text": "失業率は4.1％に低下しました。",
            },
            {
                "cue_id": "ja-2",
                "timeline_start_seconds": 3.0,
                "actual_audio_duration_seconds": 4.5,
                "caption_text": "しかし、家計調査の就業者数も減少しました。",
            },
        ],
    )

    assert caption_set["timing_basis"] == "ACTUAL_PLACED_AUDIO_SEGMENT_DURATIONS"
    assert caption_set["cues"][0]["end_seconds"] == 2.75
    assert validate_caption_set(caption_set)["result"] == "PASS_CAPTIONS"
    assert "00:00:00,500 --> 00:00:02,750" in caption_text(caption_set, kind="srt")
    assert caption_text(caption_set, kind="vtt").startswith("WEBVTT\n")


def test_caption_guard_rejects_overlap_and_out_of_bounds() -> None:
    with pytest.raises(PackageFactoryError, match="overlaps"):
        build_caption_cues(
            language="pt-BR",
            media_duration_seconds=5,
            segments=[
                {
                    "timeline_start_seconds": 0,
                    "actual_audio_duration_seconds": 3,
                    "caption_text": "Primeira fala.",
                },
                {
                    "timeline_start_seconds": 2.9,
                    "actual_audio_duration_seconds": 1,
                    "caption_text": "Segunda fala.",
                },
            ],
        )


def test_package_id_is_content_addressed_and_language_specific(tmp_path: Path) -> None:
    spanish_spec = _package_spec(tmp_path / "es", language="es")
    spanish = build_publication_package(spanish_spec)
    repeated = build_publication_package(spanish_spec)
    portuguese = build_publication_package(_package_spec(tmp_path / "pt", language="pt-BR"))

    assert spanish["package_id"] == repeated["package_id"]
    assert spanish["package_id"].startswith("pkg_")
    assert spanish["package_id"] != portuguese["package_id"]
    assert spanish["transport"] is None
    assert spanish["publication_state"] == "AUDIO_SIDECAR_FIRST_PACKAGE_ONLY_ZERO_PUBLIC_WRITE"


def test_language_audio_reuses_unchanged_picture_identity(tmp_path: Path) -> None:
    root = tmp_path / "shared"
    es_spec = _package_spec(root, language="es")
    es_audio = _artifact(root, "audio-es.wav", b"spanish")
    es_spec["audio"] = str(es_audio)
    pt_spec = dict(es_spec)
    pt_audio = _artifact(root, "audio-pt.wav", b"portuguese")
    pt_spec.update(
        {
            "language": "pt-BR",
            "audio": str(pt_audio),
            "metadata": {"title": "Título", "description": "Descrição"},
        }
    )

    es = build_publication_package(es_spec)
    pt = build_publication_package(pt_spec)

    assert es["artifacts"]["canonical_picture"]["sha256"] == pt["artifacts"]["canonical_picture"]["sha256"]
    assert es["artifacts"]["audio"]["sha256"] != pt["artifacts"]["audio"]["sha256"]


def test_burned_short_is_optional_only_and_requires_exact_authority(tmp_path: Path) -> None:
    spec = _package_spec(tmp_path, language="ja")
    spec["format"] = "SHORT_9_16"
    spec["intended_future_surfaces"] = ["YOUTUBE_SHORTS", "TIKTOK", "INSTAGRAM_REELS"]
    spec["burned_caption_video"] = str(
        _artifact(tmp_path, "burned.mp4", b"viewer-facing captions")
    )
    with pytest.raises(PackageFactoryError, match="OPTIONAL_ONLY"):
        build_publication_package(spec)

    spec["burned_caption_exact_authority"] = "future-exact-task-id"
    package = build_publication_package(spec)
    assert package["artifacts"]["canonical_picture"]["sha256"] != package["artifacts"]["burned_caption_video"]["sha256"]


def test_native_media_contracts_and_no_4k() -> None:
    short_probe = {
        "streams": [
            {
                "codec_type": "video",
                "width": 1080,
                "height": 1920,
                "r_frame_rate": "30/1",
            },
            {"codec_type": "audio", "sample_rate": "48000"},
        ],
        "format": {"duration": "55.25"},
    }
    assert validate_media_probe("SHORT_9_16", short_probe)["result"] == "PASS_MEDIA_CONTRACT"

    short_probe["streams"][0]["width"] = 2160
    short_probe["streams"][0]["height"] = 3840
    result = validate_media_probe("SHORT_9_16", short_probe)
    assert result["result"] == "FAIL_MEDIA_CONTRACT"
    assert "4k_forbidden" in result["errors"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"hard_boundaries": {"video_public_write_authority": True}}, "ZERO_VIDEO_PUBLIC_WRITE"),
        ({"hard_boundaries": {"v1_mutation_authority": True}}, "V1 mutation"),
        ({"hard_boundaries": {"scheduler_mutation_authority": True}}, "Scheduler mutation"),
        ({"api_token": "forbidden"}, "credential/account-like"),
    ],
)
def test_package_has_no_public_write_v1_scheduler_or_credentials(
    tmp_path: Path, mutation: dict[str, object], message: str
) -> None:
    spec = _package_spec(tmp_path)
    if "hard_boundaries" in mutation:
        spec["hard_boundaries"].update(mutation["hard_boundaries"])
    else:
        spec.update(mutation)

    with pytest.raises(PackageFactoryError, match=message):
        build_publication_package(spec)


def test_package_module_does_not_import_v1_or_platform_transports() -> None:
    source = (
        REPO / "video" / "freeform_chapter_pipeline_v1" / "package_factory.py"
    ).read_text(encoding="utf-8")

    assert "live_contentops" not in source
    assert "youtube" not in source.lower()
    assert "tiktok" not in source.lower()
    assert "requests" not in source
    assert "selenium" not in source
