import json
import os
import subprocess
import sys

from live_contentops import institutional_content_calendar_workflow_board_screen as cw

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")


def _read(name):
    with open(os.path.join(SHELL_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def test_valid_packet_passes():
    packet = cw.build_packet()
    res = cw.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_shell_files_exist():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        assert os.path.isfile(os.path.join(SHELL_DIR, name)), name


def test_calendar_screen_exists():
    txt = _read("fixture_data.js")
    assert "content_calendar_workflow_detail" in txt
    assert "content_calendar" in txt


def test_hero_status_band_exists():
    txt = _read("fixture_data.js")
    assert "Capital Chronicle Content Calendar + Workflow Board" in txt


def test_safety_ribbon_includes_required():
    txt = _read("fixture_data.js")
    for b in cw.REQUIRED_SAFETY_BANNERS:
        assert b in txt, b


def test_workflow_states_present():
    packet = cw.build_packet()
    for s in cw.ALLOWED_WORKFLOW_STATES:
        assert s in packet["workflow_states"], s


def test_forbidden_states_not_active():
    packet = cw.build_packet()
    active = {it["lifecycle_state"] for it in packet["content_items"]}
    for fs in cw.FORBIDDEN_STATES:
        assert fs not in active, fs
        assert fs not in packet["workflow_states"], fs


def test_at_least_8_items():
    packet = cw.build_packet()
    assert len(packet["content_items"]) >= 8


def test_required_content_types():
    packet = cw.build_packet()
    for ct in cw.REQUIRED_CONTENT_TYPES:
        assert ct in packet["content_type_coverage"], ct


def test_market_note_constraints():
    packet = cw.build_packet()
    market = [it for it in packet["content_items"] if it["content_type"] == "market_note"]
    assert market
    for it in market:
        assert it.get("educational_general_only") is True
        assert it.get("no_signal_language") is True
        assert it.get("no_buy_sell_hold") is True
        assert it.get("freshness_status")


def test_lane_model():
    packet = cw.build_packet()
    lanes = {l["lane"]: l["state"] for l in packet["lane_model"]}
    assert "pre_alpha_process" in lanes
    assert "grounded_news_context" in lanes
    assert lanes["future_artifact_backed"] == "blocked"


def test_evidence_source_panel():
    packet = cw.build_packet()
    esp = packet["evidence_source_panel"]
    assert esp["source_evidence_required"] is True
    assert esp["invented_source_artifact_ids_allowed"] is False


def test_approval_manual_publish_panel():
    packet = cw.build_packet()
    amp = packet["approval_manual_publish_panel"]
    assert amp["operator_approval_required"] is True
    assert amp["approval_implies_platform_posting"] is False
    assert amp["manual_post_url_recorded_later_not_fetched"] is True
    assert amp["api_sync"] is False


def test_metrics_manual_only():
    packet = cw.build_packet()
    mpp = packet["metrics_placeholder_panel"]
    assert mpp["scraping"] is False
    assert mpp["platform_api_metrics"] is False
    assert mpp["automatic_sync"] is False


def test_freshness_limitations_visible():
    packet = cw.build_packet()
    flp = packet["freshness_limitations_panel"]
    assert flp["missing_degraded_proxy_labels_visible"] is True
    assert flp["forecast_readiness_blocked_is_valid_state"] is True


def test_blocked_reasons_present():
    packet = cw.build_packet()
    for r in ("missing_source", "missing_artifact_id", "future_artifact_not_available",
              "market_note_missing_freshness", "scheduler_disabled"):
        assert r in packet["blocked_reasons_panel"], r


def test_calendar_view_no_scheduled_semantics():
    packet = cw.build_packet()
    cal = packet["calendar_view"]
    assert cal["implies_scheduled_posts"] is False
    text = json.dumps(cal).lower()
    for bad in ("scheduled post", "auto publish", "dispatch time"):
        assert bad not in text, bad


def test_workflow_board_columns_allowed_only():
    packet = cw.build_packet()
    cols = packet["workflow_board_view"]["columns"]
    for c in cols:
        assert c in cw.ALLOWED_WORKFLOW_STATES, c


def test_decision_ledger_no_auto_approval():
    packet = cw.build_packet()
    assert packet["decision_ledger_handoff"]["auto_approval"] is False


def test_evidence_vault_handoff_no_mutation():
    packet = cw.build_packet()
    assert packet["evidence_vault_handoff"]["evidence_mutation_from_this_screen"] is False


def test_visual_export_handoff_no_platform_export():
    packet = cw.build_packet()
    assert packet["visual_export_handoff"]["export_to_platform"] is False


def test_disabled_controls_present_and_disabled():
    packet = cw.build_packet()
    controls = {c["control"]: c["state"] for c in packet["disabled_controls_surface"]}
    for c in cw.REQUIRED_DISABLED_CONTROLS:
        assert controls.get(c) == "disabled", c


def test_evidence_summary_present():
    packet = cw.build_packet()
    assert packet["evidence_summary"]["validation_test_scan_evidence_required"] is True


def test_next_allowed_action_requires_audit():
    txt = _read("fixture_data.js")
    assert "AUDIT_OF_0165_EVIDENCE_BEFORE_ANY_NEXT_TASK" in txt


def test_no_external_cdn_or_remote_url():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        txt = _read(name)
        assert "http://" not in txt, name
        assert "https://" not in txt, name


def test_no_network_calls():
    for name in ("app.js", "fixture_data.js", "index.html"):
        txt = _read(name)
        assert "fetch(" not in txt, name
        assert "new XMLHttpRequest" not in txt, name
        assert "new WebSocket" not in txt, name
        assert "new EventSource" not in txt, name


def test_no_token_like_secret_visible():
    assert cw._count_secret_hits() == 0


def test_no_raw_env_path_visible():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        txt = _read(name)
        assert ".env" not in txt, name


def test_no_actionable_signal_text():
    banned = ["buy now", "sell now", "go long", "go short", "bullish", "bearish",
              "buy/sell", "alpha signal"]
    for name in ("app.js", "fixture_data.js", "styles.css", "index.html"):
        txt = _read(name).lower()
        for term in banned:
            assert term not in txt, (name, term)


def test_no_red_green_market_direction_semantics():
    packet = cw.build_packet()
    assert packet["red_green_market_direction_semantics"] is False


def test_active_frontend_scope_within_shell():
    packet = cw.build_packet()
    assert "ui/institutional_shell" in packet["active_frontend_code_changed_scope"]
