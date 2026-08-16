from __future__ import annotations

import json
from pathlib import Path

import pytest

from video.freeform_chapter_pipeline_v1.governed_translation import (
    GovernedTranslationError,
    Qwen3LocalTranslator,
    build_translation_messages,
    validate_governed_translation,
)


REPO = Path(__file__).resolve().parents[1]
PIPELINE = REPO / "video" / "freeform_chapter_pipeline_v1"


def _segment() -> dict[str, object]:
    return {
        "segment_id": "labor-001",
        "source_text": "On July 7, payrolls fell 23,000; the estimate is preliminary.",
        "governed_facts": [
            {"id": "date", "kind": "DATE", "accepted_forms": {"vi": ["ngày 7 tháng 7"]}},
            {"id": "number", "kind": "NUMBER", "accepted_forms": {"vi": ["23.000"]}},
            {"id": "direction", "kind": "SIGN_DIRECTION", "accepted_forms": {"vi": ["giảm"]}},
            {"id": "entity", "kind": "NAMED_ENTITY", "accepted_forms": {"vi": ["biên chế"]}},
            {"id": "uncertainty", "kind": "UNCERTAINTY", "accepted_forms": {"vi": ["sơ bộ"]}},
        ],
    }


def test_qwen3_backend_is_local_apache_and_not_factual_authority(tmp_path: Path) -> None:
    registry = json.loads((PIPELINE / "translation_backends.json").read_text(encoding="utf-8"))
    backend = registry["backends"]["qwen3_4b_local"]
    assert backend["official_model_id"] == "Qwen/Qwen3-4B"
    assert backend["license"] == "Apache-2.0"
    assert backend["network_allowed_during_translation"] is False
    assert "NOT_FACTUAL_AUTHORITY" in backend["role"]
    assert "nllb_200_distilled" in registry["forbidden_canonical_backends"]

    messages = build_translation_messages(_segment(), "vi")
    assert "not factual authority" in messages[0]["content"]
    with pytest.raises(GovernedTranslationError, match="not materialized"):
        Qwen3LocalTranslator(tmp_path / "missing", registry)


def test_governed_translation_passes_all_actual_target_forms() -> None:
    result = validate_governed_translation(
        _segment(),
        "Ngày 7 tháng 7, biên chế giảm 23.000; đây là ước tính sơ bộ.",
        "vi",
    )
    assert result["result"] == "PASS_GOVERNED_TRANSLATION"
    assert result["silent_repair_performed"] is False


def test_governed_translation_fails_closed_without_silent_number_repair() -> None:
    result = validate_governed_translation(
        _segment(),
        "Ngày 7 tháng 7, biên chế tăng 32.000; đây là con số chính thức.",
        "vi",
    )
    assert result["result"] == "FAIL_GOVERNED_TRANSLATION_CLOSED"
    assert {item["id"] for item in result["failures"]} == {
        "number", "direction", "uncertainty"
    }
    assert result["silent_repair_performed"] is False


def test_tts_and_voice_registries_cover_all_declared_locales_and_lock_english_owner_baseline() -> None:
    locale_registry = json.loads((PIPELINE / "locale_profiles.json").read_text(encoding="utf-8"))
    routes = json.loads((PIPELINE / "tts_routes.json").read_text(encoding="utf-8"))
    voices = json.loads((PIPELINE / "voice_registry.json").read_text(encoding="utf-8"))
    declared = set(locale_registry["locales"])
    assert set(routes["routes"]) == declared
    assert set(voices["entries"]) == declared
    english = voices["entries"]["en"]
    assert english["provider"] == "kokoro-onnx"
    assert english["voice_identity"] == "af_heart"
    assert english["settings"] == {"speed": 1.06, "lang": "en-us"}
    assert english["acceptance_status"] == "OWNER_PREFERRED_ACCEPTED_BASELINE"
    assert english["sample_path"] is None
    assert english["sample_sha256"] is None
    assert "am_michael" not in json.dumps(english)
    assert routes["routes"]["vi"][0] == "eleven_flash_v2_5"
    assert routes["routes"]["bn"] == ["eleven_v3"]
    assert voices["entries"]["vi"]["sample_path"] is None
    assert "PENDING" in voices["entries"]["vi"]["acceptance_status"]
    assert routes["voice_safety"]["real_person_voice_cloning"] is False


def test_production_builder_has_no_locale_picture_or_remotion_path() -> None:
    source = (PIPELINE / "build_demo_packages.py").read_text(encoding="utf-8")
    assert "canonical_short_picture" in source
    assert "canonical_longform_picture" in source
    assert "short_{locale}" not in source
    assert "remotion" not in source.lower()
    assert 'burned = None' in source


def test_sidecar_proof_uses_stream_copy_and_declares_zero_render_operations() -> None:
    source = (PIPELINE / "zero_rerender_sidecar_proof.py").read_text(encoding="utf-8")
    assert '"-c:v", "copy"' in source
    assert '"remotion_video_renders": 0' in source
    assert '"localized_picture_renders": 0' in source
    assert '"picture_render_required": False' in source
    assert "remotion render" not in source.lower()
