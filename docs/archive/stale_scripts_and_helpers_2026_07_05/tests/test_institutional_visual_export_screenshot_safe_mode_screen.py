import json
import os

from live_contentops import institutional_visual_export_screenshot_safe_mode_screen as vx

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")


def _read(name):
    with open(os.path.join(SHELL_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def test_valid_packet_passes():
    packet = vx.build_packet()
    res = vx.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_shell_files_exist():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        assert os.path.isfile(os.path.join(SHELL_DIR, name)), name


def test_visual_export_screen_exists():
    txt = _read("fixture_data.js")
    assert "visual_export_detail" in txt
    assert "visual_export_studio" in txt


def test_hero_status_band_exists():
    txt = _read("fixture_data.js")
    assert "Capital Chronicle Visual Export + Screenshot-Safe Mode" in txt


def test_safety_ribbon_includes_required():
    txt = _read("fixture_data.js")
    for b in vx.REQUIRED_SAFETY_BANNERS:
        assert b in txt, b


def test_screenshot_safe_mode_panel():
    p = vx.build_packet()["screenshot_safe_mode_panel"]
    assert p["screenshot_taken_by_task"] is False
    assert p["browser_automation"] is False
    assert p["antigravity_run"] is False
    assert p["image_video_pdf_export_created"] is False
    assert p["platform_upload_or_post"] is False


def test_export_safe_card_gallery():
    cards = vx.build_packet()["export_safe_card_gallery"]
    assert len(cards) >= 6
    sources = {c["source_screen"] for c in cards}
    for s in vx.REQUIRED_EXPORT_CARDS:
        assert s in sources, s
    assert any(c["card_id"] == "esc-telegram-gate" for c in cards)


def test_redaction_overlay_fields():
    fields = {r["field"] for r in vx.build_packet()["redaction_overlay_panel"]}
    for f in vx.REQUIRED_REDACTION_FIELDS:
        assert f in fields, f
    for r in vx.build_packet()["redaction_overlay_panel"]:
        assert r["displayed"] is False


def test_watermark_labels():
    labels = vx.build_packet()["watermark_status_label_panel"]
    for w in vx.REQUIRED_WATERMARK_LABELS:
        assert w in labels, w


def test_limitations_freshness_panel():
    p = vx.build_packet()["limitations_freshness_visibility_panel"]
    assert p["limitations_cannot_be_hidden"] is True
    assert p["freshness_visible_for_market_current_claims"] is True


def test_evidence_reference_panel():
    p = vx.build_packet()["evidence_reference_visibility_panel"]
    assert p["evidence_refs_visible"] is True
    assert p["invented_source_artifact_ids_allowed"] is False


def test_export_eligibility_checklist():
    checklist = vx.build_packet()["export_eligibility_checklist"]
    for item in vx.REQUIRED_CHECKLIST_ITEMS:
        assert item in checklist, item


def test_blocked_export_action_matrix():
    actions = {a["action"]: a["state"] for a in vx.build_packet()["blocked_export_action_matrix"]}
    for a in vx.REQUIRED_BLOCKED_ACTIONS:
        assert actions.get(a) == "disabled", a


def test_active_export_or_capture_control_count_zero():
    assert vx.summary()["active_export_or_capture_control_count"] == 0


def test_antigravity_handoff_future_only():
    p = vx.build_packet()["antigravity_handoff_panel"]
    assert p["antigravity_run_yet"] is False
    assert p["future_task_requires_explicit_go"] is True


def test_visual_quality_checklist():
    p = vx.build_packet()["visual_quality_checklist"]
    assert p["color_only_status_communication"] is False
    assert p["green_red_as_market_direction"] is False


def test_preview_states():
    previews = {p["state"]: p for p in vx.build_packet()["screenshot_safe_preview_states"]}
    for ps in vx.REQUIRED_PREVIEW_STATES:
        assert ps in previews, ps
    assert previews["export_ready_with_redaction"]["export_safe"] is True
    for state, p in previews.items():
        if state != "export_ready_with_redaction":
            assert p.get("export_safe") is not True, state
            assert p.get("blocked") is True, state


def test_manual_operator_checklist_present():
    assert vx.build_packet()["manual_operator_checklist"]


def test_evidence_summary_present():
    assert vx.build_packet()["evidence_summary"]["validation_test_scan_evidence_required"] is True


def test_next_allowed_action_requires_audit():
    txt = _read("fixture_data.js")
    assert "AUDIT_OF_0166_EVIDENCE_BEFORE_ANY_NEXT_TASK" in txt


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
    assert vx._count_secret_hits() == 0


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
    assert vx.build_packet()["red_green_market_direction_semantics"] is False


def test_active_frontend_scope_within_shell():
    assert "ui/institutional_shell" in vx.build_packet()["active_frontend_code_changed_scope"]


def test_runtime_authority_true_fails():
    p = vx.build_packet()
    p["runtime_authority"] = True
    res = vx.validate_packet(p)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_screenshot_capture_enabled_fails():
    p = vx.build_packet()
    p["screenshot_capture_enabled_now"] = True
    res = vx.validate_packet(p)
    assert not res["valid"]


def test_file_export_enabled_fails():
    p = vx.build_packet()
    p["file_export_enabled_now"] = True
    res = vx.validate_packet(p)
    assert not res["valid"]


def test_platform_upload_enabled_fails():
    p = vx.build_packet()
    p["platform_upload_enabled_now"] = True
    res = vx.validate_packet(p)
    assert not res["valid"]


def test_antigravity_used_fails():
    p = vx.build_packet()
    p["antigravity_used_now"] = True
    res = vx.validate_packet(p)
    assert not res["valid"]


def test_fewer_than_6_cards_fails():
    p = vx.build_packet()
    p["export_safe_card_gallery"] = p["export_safe_card_gallery"][:5]
    res = vx.validate_packet(p)
    assert not res["valid"]


def test_blocked_action_active_fails():
    p = vx.build_packet()
    for a in p["blocked_export_action_matrix"]:
        if a["action"] == "capture_screenshot":
            a["state"] = "enabled"
    res = vx.validate_packet(p)
    assert not res["valid"]


def test_packet_status_pass_with_errors_fails():
    p = vx.build_packet()
    p["runtime_authority"] = True
    p["packet_status"] = "pass"
    res = vx.validate_packet(p)
    assert not res["valid"]
    assert "packet_status_pass_but_errors_exist" in res["errors"]


def test_cli_summary_validation_valid():
    s = vx.summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"

    assert vx.summary()["active_export_or_capture_control_count"] == 0
