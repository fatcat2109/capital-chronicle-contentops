"""Tests for TASK_CONTENTOPS_0172 institutional shell view-model source of truth + drift guard."""

import copy
import json
from pathlib import Path

from live_contentops import institutional_shell_view_model_source_of_truth as m

_ROOT = Path(__file__).resolve().parent.parent
_SHELL = _ROOT / "ui" / "institutional_shell"
_FIXTURE = _SHELL / "fixture_data.js"
_APP = _SHELL / "app.js"

REQUIRED_SCREENS = [
    "command_center", "content_lane_control", "daily_content_studio",
    "draft_inspector", "grounded_news_angle_lab", "publish_readiness_tower",
    "telegram_pilot_gate", "approval_queue", "content_calendar",
    "evidence_vault", "visual_export_studio", "settings_safety_policy",
]


def _p():
    return m.build_packet()


def test_packet_validates():
    assert m.validate_packet(_p())["valid"]


def test_summary_valid():
    assert m.build_summary()["validation_valid"] is True


def test_task_label():
    assert _p()["task_label"] == m.TASK_LABEL


def test_required_starting_baseline():
    assert _p()["required_starting_baseline"] == "667f0ad"


def test_prior_accepted_pass():
    assert _p()["prior_task_classification"] == "PASS"


def test_source_of_truth_model_present():
    assert _p()["source_of_truth_model_present"] is True


def test_global_metadata_source_of_truth_present():
    assert _p()["global_metadata_source_of_truth_present"] is True


def test_fixture_drift_guard_present():
    assert _p()["fixture_drift_guard_present"] is True


def test_drift_findings_empty():
    assert _p()["drift_findings"] == []



def test_twelve_screens_present():
    assert _p()["screen_count"] == 12
    inv = _p()["screen_inventory"]
    for s in REQUIRED_SCREENS:
        assert s in inv


def test_current_vs_historical_separated():
    assert _p()["current_vs_historical_metadata_separated"] is True


def test_browser_qa_provenance_present():
    p = _p()
    assert p["browser_qa_evidence_provenance_present"] is True
    assert p["browser_qa_evidence_provenance"]["task"] == "0169"
    assert p["browser_qa_evidence_provenance"]["classification"] == "PASS_WITH_MINOR_EVIDENCE_GAP"


def test_no_stale_regression():
    assert _p()["stale_global_header_regression_count"] == 0


def test_historical_policy_present():
    assert _p()["historical_metadata_policy_present"] is True


def test_forbidden_controls_zero():
    assert _p()["forbidden_controls_active_count"] == 0


def test_kill_switch_active():
    assert _p()["kill_switch_status"] == "active"


def test_secret_visible_zero():
    assert _p()["secret_visible_count"] == 0


def test_baseline_semantics_no_future_head_claim():
    p = _p()
    assert "post-task HEAD" in p["baseline_semantics"]


# --- negative cases ---

def test_forbidden_flag_true_fails():
    p = copy.deepcopy(_p())
    p["live_posting_enabled_now"] = True
    assert not m.validate_packet(p)["valid"]


def test_stale_regression_fails():
    p = copy.deepcopy(_p())
    p["stale_global_header_regression_count"] = 1
    assert not m.validate_packet(p)["valid"]


def test_historical_policy_missing_fails():
    p = copy.deepcopy(_p())
    p["historical_metadata_policy_present"] = False
    assert not m.validate_packet(p)["valid"]


def test_current_vs_historical_false_fails():
    p = copy.deepcopy(_p())
    p["current_vs_historical_metadata_separated"] = False
    assert not m.validate_packet(p)["valid"]


def test_screen_count_mismatch_fails():
    p = copy.deepcopy(_p())
    p["screen_count"] = 11
    assert not m.validate_packet(p)["valid"]


def test_secret_visible_fails():
    p = copy.deepcopy(_p())
    p["secret_visible_count"] = 1
    assert not m.validate_packet(p)["valid"]


def test_drift_findings_present_fails():
    p = copy.deepcopy(_p())
    p["drift_findings"] = ["stale_head_presented_as_current"]
    assert not m.validate_packet(p)["valid"]


def test_kill_switch_inactive_fails():
    p = copy.deepcopy(_p())
    p["kill_switch_status"] = "inactive"
    assert not m.validate_packet(p)["valid"]


# --- live shell asset drift checks ---

def test_fixture_no_stale_head_as_current():
    fx = _FIXTURE.read_text(encoding="utf-8")
    assert 'accepted_head_short: "15b87ff"' not in fx


def test_fixture_no_stale_gate_as_current():
    fx = _FIXTURE.read_text(encoding="utf-8")
    assert 'current_gate: "telegram_official_docs' not in fx


def test_app_historical_labels_present():
    app = _APP.read_text(encoding="utf-8")
    assert "Screen Baseline (historical)" in app
    assert "Screen Gate (historical)" in app


def test_drift_checks_clean_on_live_assets():
    findings, metrics = m.run_drift_checks()
    assert findings == []
    assert metrics["screen_count"] == 12


def test_schema_required_fields_match():
    schema = json.loads(
        (_ROOT / "schemas"
         / "institutional_shell_view_model_source_of_truth_packet.schema.json")
        .read_text(encoding="utf-8")
    )
    p = _p()
    for field in schema["required"]:
        assert field in p

    assert p["current_global_state"]["last_accepted_baseline_entering_task"] == "667f0ad"
