from __future__ import annotations

import json

import pytest

from live_contentops.retention_native_video_critic_v2 import validate_critic_output


def _issue() -> dict[str, object]:
    return {
        "severity": "MINOR",
        "video_id": "eia-hormuz-flows-v2",
        "variant_id": "short_9x16",
        "scene_id": "short-scene-12",
        "start_seconds": 45.3,
        "end_seconds": 49.07,
        "beat_ids": ["short-b12"],
        "category": "visual",
        "observation": "The source microcopy is small in the portrait chart reframe.",
        "structural_fix": "Increase the source-label size within short-b12.",
    }


def _payload(issue: dict[str, object]) -> dict[str, object]:
    return {
        "status": "PASS_WITH_NOTES",
        "summary": "One localized presentation note remains.",
        "scope": {
            "visual_images_reviewed": True,
            "actual_finished_media_sampled": True,
            "audio_listened": False,
            "audio_technical_metrics_reviewed": True,
            "limitations": ["Audio was not auditioned."],
        },
        "issues": [issue],
        "strengths": ["The primary visual evolves clearly."],
        "acceptance_recommendation": "Accept with the localized note.",
    }


def _validate(issue: dict[str, object]) -> tuple[bool, str | None, object, str | None]:
    return validate_critic_output(json.dumps(_payload(issue)))


@pytest.mark.parametrize(
    "field",
    ["video_id", "scene_id", "start_seconds", "end_seconds", "beat_ids"],
)
def test_critic_issue_rejects_missing_localization_fields(field: str) -> None:
    issue = _issue()
    del issue[field]

    accepted, failure_class, value, diagnostic = _validate(issue)

    assert accepted is False
    assert failure_class == "structured_output_schema_invalid"
    assert value is None
    assert diagnostic == "critic_issue_shape_invalid:0"


@pytest.mark.parametrize("field", ["video_id", "scene_id"])
@pytest.mark.parametrize("value", [None, "", "   ", "not exact", "*"])
def test_critic_issue_requires_nonempty_video_and_scene_ids(field: str, value: object) -> None:
    issue = _issue()
    issue[field] = value

    accepted, failure_class, value, diagnostic = _validate(issue)

    assert accepted is False
    assert failure_class == "structured_output_schema_invalid"
    assert value is None
    assert diagnostic == f"critic_issue_{field}_required:0"


@pytest.mark.parametrize(
    ("start_seconds", "end_seconds", "diagnostic"),
    [
        (None, 1.0, "critic_issue_start_seconds_invalid:0"),
        (True, 1.0, "critic_issue_start_seconds_invalid:0"),
        (-0.01, 1.0, "critic_issue_start_seconds_invalid:0"),
        (float("nan"), 1.0, "critic_issue_start_seconds_invalid:0"),
        (0.0, None, "critic_issue_end_seconds_invalid:0"),
        (0.0, False, "critic_issue_end_seconds_invalid:0"),
        (2.0, 1.99, "critic_issue_end_seconds_invalid:0"),
        (0.0, float("inf"), "critic_issue_end_seconds_invalid:0"),
    ],
)
def test_critic_issue_requires_ordered_finite_numeric_timestamps(
    start_seconds: object,
    end_seconds: object,
    diagnostic: str,
) -> None:
    issue = _issue()
    issue["start_seconds"] = start_seconds
    issue["end_seconds"] = end_seconds

    accepted, failure_class, value, actual_diagnostic = _validate(issue)

    assert accepted is False
    assert failure_class == "structured_output_schema_invalid"
    assert value is None
    assert actual_diagnostic == diagnostic


@pytest.mark.parametrize(
    "beat_ids",
    [None, [], [""], ["   "], ["short-b12 "], ["*"], ["short-b12", "short-b12"]],
)
def test_critic_issue_requires_exact_nonempty_unique_beat_ids(beat_ids: object) -> None:
    issue = _issue()
    issue["beat_ids"] = beat_ids

    accepted, failure_class, value, diagnostic = _validate(issue)

    assert accepted is False
    assert failure_class == "structured_output_schema_invalid"
    assert value is None
    assert diagnostic == "critic_issue_beat_ids_required:0"


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("category", "unknown", "critic_issue_category_invalid:0"),
        ("observation", "", "critic_issue_observation_required:0"),
        ("structural_fix", "   ", "critic_issue_structural_fix_required:0"),
    ],
)
def test_critic_issue_retains_content_field_validation(field: str, value: object, diagnostic: str) -> None:
    issue = _issue()
    issue[field] = value

    accepted, failure_class, parsed, actual_diagnostic = _validate(issue)

    assert accepted is False
    assert failure_class == "structured_output_schema_invalid"
    assert parsed is None
    assert actual_diagnostic == diagnostic


def test_critic_issue_accepts_complete_single_scene_localization() -> None:
    accepted, failure_class, value, diagnostic = _validate(_issue())

    assert accepted is True
    assert failure_class is None
    assert value == _payload(_issue())
    assert diagnostic is None


def test_critic_issue_rejects_ambiguous_both_variant_localization() -> None:
    issue = _issue()
    issue["variant_id"] = "both"

    accepted, failure_class, value, diagnostic = _validate(issue)

    assert accepted is False
    assert failure_class == "structured_output_schema_invalid"
    assert value is None
    assert diagnostic == "critic_issue_variant_invalid:0"
