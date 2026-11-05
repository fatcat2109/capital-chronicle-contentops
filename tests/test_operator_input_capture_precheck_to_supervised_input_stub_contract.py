"""Tests for Operator Input Capture Precheck to Supervised Input Stub Contract.

Part of TASK_CONTENTOPS_0175BP_OPERATOR_INPUT_CAPTURE_PRECHECK_TO_SUPERVISED_INPUT_STUB_CONTRACT_V0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.operator_input_capture_precheck_to_supervised_input_stub_contract import (
    ALLOWED_FUTURE_CAPTURE_MODES,
    FORBIDDEN_CURRENT_ACTIONS,
    NEXT_RECOMMENDED_TASK,
    REQUIRED_INPUT_FIELDS,
    create_supervised_input_stub_contract,
    write_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175BN" / "review_only_intent_to_operator_input_capture_precheck_packet.json"
FORBIDDEN_OUTPUT_KEYS = {
    "operator_prose",
    "operator_notes_text",
    "draft",
    "draft_text",
    "draft_paragraph",
    "headline",
    "hook",
    "caption",
    "platform_copy",
    "generated_copy",
    "editorial_thesis",
    "thesis",
}


@pytest.fixture
def source_packet() -> dict:
    with open(SOURCE_PACKET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_blocked_source_items_remain_blocked():
    sample = {
        "task_label": "TASK_CONTENTOPS_0175BN_REVIEW_ONLY_INTENT_TO_OPERATOR_INPUT_CAPTURE_PRECHECK_V0",
        "global_operator_input_capture_status": "BLOCKED_OPERATOR_INPUT_CAPTURE_NOT_ENABLED",
        "field_policy": {field: {"required": True} for field in REQUIRED_INPUT_FIELDS},
        "input_capture_precheck_items": [
            {
                "intent_item_id": "intent_item_blocked",
                "source_candidate_id": "blocked_candidate",
                "relative_path": "docs/example.json",
                "evidence_role": "contract",
                "source_family": "Example",
                "records_count": 0,
                "contract_name": "EXAMPLE_CONTRACT",
                "intent_scope_label": "example_review",
                "operator_input_capture_precheck_status": "BLOCKED_BY_REVIEW_ONLY_INTENT_PACKET",
                "blocked_reasons": ["example_block"],
                "missing_requirements": ["example_requirement"],
            }
        ],
    }

    packet = create_supervised_input_stub_contract(sample)
    assert packet["supervised_input_stub_items"][0]["supervised_input_stub_status"] == "BLOCKED_BY_OPERATOR_INPUT_CAPTURE_PRECHECK"


