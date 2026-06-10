import os
import json
from live_contentops.operator_ui_ux_spec import validate_operator_ui_ux_spec_packet, validate_content_calendar_spec_packet

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "operator_ui_ux")

def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_operator_console_spec():
    res = validate_operator_ui_ux_spec_packet(_load("valid_operator_console_spec.json"))
    assert res["valid"] is True

def test_valid_content_calendar_spec():
    res = validate_content_calendar_spec_packet(_load("valid_content_calendar_spec.json"))
    assert res["valid"] is True

def test_invalid_live_publish_button_enabled():
    res = validate_operator_ui_ux_spec_packet(_load("invalid_live_publish_button_enabled.json"))
    assert res["valid"] is False
    assert any("forbidden_action_enabled:live_publish" in e for e in res["errors"])

def test_invalid_secret_visible_in_ui():
    res = validate_operator_ui_ux_spec_packet(_load("invalid_secret_visible_in_ui.json"))
    assert res["valid"] is False
    assert any("unsafe_secret_detected" in e for e in res["errors"])

def test_invalid_missing_safety_banner():
    res = validate_operator_ui_ux_spec_packet(_load("invalid_missing_safety_banner.json"))
    assert res["valid"] is False
    assert any("missing_safety_banner" in e for e in res["errors"])

def test_invalid_auto_schedule_enabled():
    res = validate_operator_ui_ux_spec_packet(_load("invalid_auto_schedule_enabled.json"))
    assert res["valid"] is False
    assert any("forbidden_action_enabled:schedule_post" in e for e in res["errors"])

def test_invalid_calendar_marks_public_ready():
    res = validate_content_calendar_spec_packet(_load("invalid_calendar_marks_public_ready.json"))
    assert res["valid"] is False
    assert any("forbidden_calendar_state:public_ready" in e for e in res["errors"])
