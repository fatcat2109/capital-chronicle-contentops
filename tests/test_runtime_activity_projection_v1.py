from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from live_contentops.runtime_activity_projection_v1 import (
    ACTIVITY_FILE_NAME,
    RuntimeActivityRecorderV1,
    load_runtime_activity,
)


NOW = datetime(2026, 8, 14, 4, 0, tzinfo=timezone.utc)


def test_runtime_activity_is_bounded_presentation_telemetry(tmp_path):
    recorder = RuntimeActivityRecorderV1(
        output_dir=tmp_path, work_item_id="cycle-1", now_fn=lambda: NOW,
    )
    recorder.record(
        "CANDIDATE_SELECTION", candidate_rank=2, candidate_count=7,
        story_label="Safe story https://example.invalid/?token=never-expose",
        grounding="source-bound evidence", destination="substack",
    )
    current = recorder.record("GROUNDED_RESEARCH")
    assert current["current_stage"] == "GROUNDED_RESEARCH"
    assert current["completed_stages"] == ["CANDIDATE_SELECTION"]
    assert current["candidate_rank"] == 2
    assert current["candidate_count"] == 7
    assert current["safe_story_label"] == "Safe story [link]"
    assert current["presentation_only"] is True
    assert current["authority_granted"] is False
    assert current["contains_hidden_reasoning"] is False
    encoded = json.dumps(load_runtime_activity(tmp_path / ACTIVITY_FILE_NAME))
    assert "token=never-expose" not in encoded
    assert "https://" not in encoded


def test_runtime_activity_identity_and_stage_fail_closed(tmp_path):
    RuntimeActivityRecorderV1(
        output_dir=tmp_path, work_item_id="cycle-1", now_fn=lambda: NOW,
    ).record("HEADLINE_INGESTION")
    with pytest.raises(ValueError, match="identity_conflict"):
        RuntimeActivityRecorderV1(
            output_dir=tmp_path, work_item_id="cycle-2", now_fn=lambda: NOW,
        ).record("CANDIDATE_SELECTION")
    with pytest.raises(ValueError, match="stage_invalid"):
        RuntimeActivityRecorderV1(
            output_dir=tmp_path / "other", work_item_id="cycle-3", now_fn=lambda: NOW,
        ).record("INVENTED_ACTIVITY")


def test_runtime_activity_finish_never_advances_lifecycle(tmp_path):
    recorder = RuntimeActivityRecorderV1(
        output_dir=tmp_path, work_item_id="cycle-1", now_fn=lambda: NOW,
    )
    recorder.record("PACKAGE_BUILD")
    finished = recorder.finish(
        terminal_result="REJECTED", exact_reason="NO_PUBLICATION",
    )
    assert finished["active"] is False
    assert finished["terminal_result"] == "REJECTED"
    assert finished["exact_reason"] == "NO_PUBLICATION"
    assert finished["authority_granted"] is False
