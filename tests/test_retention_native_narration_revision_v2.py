from __future__ import annotations

import json

from live_contentops.retention_native_narration_revision_v2 import (
    SCHEMA_VERSION,
    narration_revision_validator,
)


def test_narration_revision_validator_accepts_bounded_exact_rows() -> None:
    source = [
        {"shot_id": "s01", "narration_text": "Supply returns by 2027."},
        {"shot_id": "s02", "narration_text": "Watch demand and inventories."},
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "narration_revisions": [
            {"shot_id": "s01", "narration_text": "Supply returns by 2027."},
            {"shot_id": "s02", "narration_text": "Watch demand and inventories."},
        ],
        "revision_rationale": "Natural pace.",
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    ok, *_ = narration_revision_validator(source)(json.dumps(payload))
    assert ok is True


def test_narration_revision_validator_rejects_new_number_and_wrong_order() -> None:
    source = [
        {"shot_id": "s01", "narration_text": "Supply returns by 2027."},
        {"shot_id": "s02", "narration_text": "Watch demand and inventories."},
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "narration_revisions": [
            {"shot_id": "s02", "narration_text": "Watch demand in 2028."},
            {"shot_id": "s01", "narration_text": "Supply returns by 2027."},
        ],
        "revision_rationale": "Bad scope.",
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    ok, *_ = narration_revision_validator(source)(json.dumps(payload))
    assert ok is False
