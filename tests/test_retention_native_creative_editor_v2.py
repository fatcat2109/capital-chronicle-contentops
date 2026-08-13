from __future__ import annotations

import json

from live_contentops.retention_native_creative_editor_v2 import (
    BLUEPRINT_SCHEMA_VERSION,
    LEGACY_MIDFORM_BEATS,
    LEGACY_SHORT_BEATS,
    REQUIRED_BEAT_KEYS,
    REQUIRED_HYPOTHESIS_KEYS,
    build_minified_whole_video_prompt,
    compact_blueprint_validator,
    minified_blueprint_validator,
    sanitized_diagnostic,
    validate_legacy_blueprint,
)


def _valid_beat(beat_id: str) -> dict[str, object]:
    row: dict[str, object] = {key: "value" for key in REQUIRED_BEAT_KEYS}
    row.update(
        {
            "beat_id": beat_id,
            "start_seconds": 0,
            "end_seconds": 1,
            "claim_ids": [],
            "evidence_ids": [],
            "asset_ids": [],
        }
    )
    return row


def _valid_payload() -> dict[str, object]:
    return {
        "schema_version": BLUEPRINT_SCHEMA_VERSION,
        "story_id": "story",
        "creative_thesis": "thesis",
        "shared_visual_language": {},
        "variants": {
            "short_9x16": {
                "beats": [_valid_beat(beat_id) for beat_id in LEGACY_SHORT_BEATS]
            },
            "midform_16x9": {
                "beats": [_valid_beat(beat_id) for beat_id in LEGACY_MIDFORM_BEATS]
            },
        },
        "music_direction": "music",
        "sfx_cues": [],
        "rights_and_truth_notes": [],
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }


def test_legacy_validator_reports_exact_parser_and_schema_categories() -> None:
    assert validate_legacy_blueprint("")[3] == "json_empty"
    assert validate_legacy_blueprint("{")[3] == "json_decode_error"
    assert validate_legacy_blueprint("{} trailing")[3] == "json_trailing_content"
    assert validate_legacy_blueprint("{}")[3] == "schema_missing_top_level"
    payload = _valid_payload()
    payload["variants"]["short_9x16"]["beats"][0]["beat_id"] = "wrong"
    assert validate_legacy_blueprint(json.dumps(payload))[3] == "exact_beat_ids_invalid"


def test_legacy_validator_accepts_exact_shape() -> None:
    ok, failure, parsed, diagnostic = validate_legacy_blueprint(json.dumps(_valid_payload()))
    assert ok is True
    assert failure is None
    assert parsed["schema_version"] == BLUEPRINT_SCHEMA_VERSION
    assert diagnostic is None


def test_sanitized_diagnostic_classifies_provider_truncation_without_raw_output() -> None:
    summary = {
        "terminal_disposition": "BLOCKED_EXACT_CREATIVE_MODEL",
        "attempts": [
            {
                "requested_model": "new/gpt-5.6-sol-xhigh",
                "provider_finish_reason": "length",
                "provider_truncation_indicated": True,
                "output_character_length": 64000,
                "output_hash": "abc",
                "failure_class": "structured_output_malformed",
            }
        ],
    }
    result = sanitized_diagnostic(summary, {"story_id": "story"})
    assert result["diagnosis"] == "PROVEN_PROVIDER_OUTPUT_TRUNCATION"
    assert result["raw_rejected_output_persisted"] is False
    assert "output" not in result["attempts"][0]


def test_compact_validator_rejects_ungoverned_asset_binding() -> None:
    hypothesis = {key: "value" for key in REQUIRED_HYPOTHESIS_KEYS}
    hypothesis.update(
        {
            "shot_id": "shot_1",
            "duration_seconds": 10,
            "asset_ids": ["unknown"],
            "claim_ids": [],
            "evidence_ids": [],
        }
    )
    payload = {
        "schema_version": BLUEPRINT_SCHEMA_VERSION,
        "story_id": "story",
        "creative_thesis": "thesis",
        "shared_visual_language": {},
        "variants": {},
        "music_direction": "music",
        "sfx_palette": [],
        "rights_and_truth_notes": [],
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    for variant_id, duration, payoff in (
        ("short_9x16", 60, 10),
        ("midform_16x9", 120, 45),
    ):
        span = duration / 3
        payload["variants"][variant_id] = {
            "duration_seconds": duration,
            "payoff_seconds": payoff,
            "narration_script": "narration",
            "sequences": [
                {
                    "sequence_id": f"{variant_id}_{index}",
                    "start_seconds": index * span,
                    "end_seconds": (index + 1) * span,
                    "visual_hypotheses": [
                        dict(hypothesis, shot_id=f"{variant_id}_shot_{index}")
                    ],
                }
                for index in range(3)
            ],
        }
    validator = compact_blueprint_validator(
        {"story_id": "story", "assets": [], "claims": [], "evidence": []}
    )
    assert validator(json.dumps(payload))[3] == "asset_binding_invalid"


def test_minified_prompt_omits_full_article_and_stays_small() -> None:
    governed = {
        "story_id": "story", "title": "Title", "subtitle": "Subtitle",
        "market_mechanism": "Mechanism", "policy_context": "Policy",
        "cross_asset_implications": "Cross asset", "named_catalysts": [],
        "claims": [], "evidence": [], "assets": [], "article_body": "DO_NOT_INCLUDE",
    }
    prompt = build_minified_whole_video_prompt(governed)
    assert "DO_NOT_INCLUDE" not in prompt
    assert len(prompt) < 7000


def test_minified_validator_accepts_bound_complete_whole_video() -> None:
    governed = {
        "story_id": "story",
        "assets": [{"asset_id": "asset"}],
        "claims": [{"claim_id": "claim"}],
        "evidence": [{"evidence_id": "evidence"}],
    }
    shot = {
        "id": "shot", "t0": 0, "t1": 1, "narration_excerpt": "line",
        "purpose": "purpose", "visual": "visual", "motion": "motion",
        "asset_ids": ["asset"], "claim_ids": ["claim"], "evidence_ids": ["evidence"],
        "transition": "transition", "audio": "audio", "continuity": "continuity",
    }
    payload = {
        "schema_version": BLUEPRINT_SCHEMA_VERSION, "story_id": "story",
        "viewer_promise": "promise", "visual_system": {}, "music": "music",
        "rights_notes": [], "public_write": False, "publication_authority": False,
        "factual_authority": False, "variants": {},
    }
    for variant_id, duration, payoff in (("short_9x16", 45, 10), ("midform_16x9", 90, 45)):
        span = duration / 3
        payload["variants"][variant_id] = {
            "duration_seconds": duration, "hook": "hook", "payoff_seconds": payoff,
            "narration": "complete narration",
            "shots": [dict(shot, id=f"{variant_id}_{i}", t0=i * span, t1=(i + 1) * span) for i in range(3)],
        }
    assert minified_blueprint_validator(governed)(json.dumps(payload))[0] is True
