import json
import os
import subprocess
import sys

from live_contentops import institutional_publish_readiness_tower_screen as prt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")


def _read(name):
    with open(os.path.join(SHELL_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def test_valid_packet_passes():
    packet = prt.build_packet()
    res = prt.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_shell_files_exist():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        assert os.path.isfile(os.path.join(SHELL_DIR, name)), name


def test_tower_screen_exists():
    txt = _read("fixture_data.js")
    assert "publish_readiness_tower_detail" in txt
    assert "publish_readiness_tower" in txt


def test_hero_status_band_exists():
    txt = _read("fixture_data.js")
    assert "Capital Chronicle Publish Readiness Tower" in txt


def test_safety_ribbon_includes_required():
    txt = _read("fixture_data.js")
    for b in prt.REQUIRED_SAFETY_BANNERS:
        assert b in txt, b


def test_platform_telegram():
    txt = _read("fixture_data.js")
    assert "telegram" in txt


def test_platform_x():
    packet = prt.build_packet()
    ids = [p["platform_id"] for p in packet["platform_capability_registry_panel"]]
    assert "x" in ids


def test_platform_linkedin():
    packet = prt.build_packet()
    ids = [p["platform_id"] for p in packet["platform_capability_registry_panel"]]
    assert "linkedin" in ids


def test_platform_threads():
    packet = prt.build_packet()
    ids = [p["platform_id"] for p in packet["platform_capability_registry_panel"]]
    assert "threads" in ids


def test_platform_substack():
    packet = prt.build_packet()
    ids = [p["platform_id"] for p in packet["platform_capability_registry_panel"]]
    assert "substack" in ids


def test_platform_facebook_page():
    packet = prt.build_packet()
    ids = [p["platform_id"] for p in packet["platform_capability_registry_panel"]]
    assert "facebook_page" in ids


def test_platform_instagram():
    packet = prt.build_packet()
    ids = [p["platform_id"] for p in packet["platform_capability_registry_panel"]]
    assert "instagram" in ids


def test_platform_tiktok():
    packet = prt.build_packet()
    ids = [p["platform_id"] for p in packet["platform_capability_registry_panel"]]
    assert "tiktok" in ids


def test_every_platform_dry_run():
    packet = prt.build_packet()
    for p in packet["platform_capability_registry_panel"]:
        assert p["dry_run_render"] == "modeled"


def test_no_platform_live_api():
    packet = prt.build_packet()
    for p in packet["platform_capability_registry_panel"]:
        assert p["live_api"] == "disabled"


def test_no_platform_scheduling():
    packet = prt.build_packet()
    for p in packet["platform_capability_registry_panel"]:
        assert p["scheduling"] == "disabled"


def test_no_platform_public_postable():
    packet = prt.build_packet()
    for p in packet["platform_capability_registry_panel"]:
        assert p["not_public_postable"] is True


def test_manifest_no_real_dispatch():
    packet = prt.build_packet()
    assert packet["dry_run_batch_manifest_panel"]["real_platform_payload_dispatch"] is False


def test_manual_approval_no_auto_approval():
    packet = prt.build_packet()
    assert packet["manual_approval_gate_panel"]["auto_approval"] is False
    assert packet["manual_approval_gate_panel"]["approval_required_before_live_publish"] is True


def test_kill_switch_active_blocking():
    packet = prt.build_packet()
    assert packet["kill_switch_gate_panel"]["kill_switch_active"] is True
    assert packet["kill_switch_gate_panel"]["blocks_publishing"] is True


def test_credential_redaction_no_values():
    packet = prt.build_packet()
    cp = packet["credential_secret_state_panel"]
    assert cp["credential_values_displayed"] is False
    assert cp["env_path_shown"] is False


def test_redacted_audit_blocks_raw():
    packet = prt.build_packet()
    ra = packet["redacted_audit_gate_panel"]
    assert ra["unredacted_secrets_in_audit"] is False
    assert ra["raw_request_urls_in_audit"] is False
    assert ra["raw_platform_responses_in_audit"] is False
    assert ra["raw_env_path_in_audit"] is False


def test_official_docs_does_not_enable_live():
    packet = prt.build_packet()
    assert packet["official_docs_gate_panel"]["docs_verification_enables_live_posting"] is False


def test_telegram_credential_presence_redacted():
    txt = _read("fixture_data.js")
    assert "redacted_presence_only" in txt


def test_telegram_official_docs_implemented():
    packet = prt.build_packet()
    gates = {g["gate"]: g["state"] for g in packet["telegram_pilot_tower_panel"]["sub_gates"]}
    assert gates["official_docs_verification"] == "implemented"


def test_telegram_getme_run_status_separate():
    packet = prt.build_packet()
    gates = {g["gate"]: g["state"] for g in packet["telegram_pilot_tower_panel"]["sub_gates"]}
    assert "separate" in gates["getme_token_validation"]


def test_telegram_channel_permission_unvalidated():
    packet = prt.build_packet()
    gates = {g["gate"]: g["state"] for g in packet["telegram_pilot_tower_panel"]["sub_gates"]}
    assert gates["channel_write_permission"] == "unvalidated"


def test_telegram_send_message_disabled():
    packet = prt.build_packet()
    gates = {g["gate"]: g["state"] for g in packet["telegram_pilot_tower_panel"]["sub_gates"]}
    assert gates["send_message"] == "disabled"


def test_telegram_live_adapter_disabled():
    packet = prt.build_packet()
    gates = {g["gate"]: g["state"] for g in packet["telegram_pilot_tower_panel"]["sub_gates"]}
    assert gates["live_adapter"] == "disabled"


def test_telegram_posting_disabled():
    packet = prt.build_packet()
    gates = {g["gate"]: g["state"] for g in packet["telegram_pilot_tower_panel"]["sub_gates"]}
    assert gates["posting"] == "disabled"


def test_telegram_scheduler_disabled():
    packet = prt.build_packet()
    gates = {g["gate"]: g["state"] for g in packet["telegram_pilot_tower_panel"]["sub_gates"]}
    assert gates["scheduler"] == "disabled"


def test_disabled_controls_publish():
    txt = _read("fixture_data.js")
    assert "publish" in txt


def test_disabled_controls_required_set():
    packet = prt.build_packet()
    controls = {c["control"]: c["state"] for c in packet["publish_disabled_control_surface"]}
    for c in ("publish", "schedule", "connect_api", "oauth", "send_message",
              "getme_live_call", "publish_all", "scrape_metrics"):
        assert controls.get(c) == "disabled", c


def test_zero_active_publish_controls():
    packet = prt.build_packet()
    active = [c for c in packet["publish_disabled_control_surface"] if c["state"] != "disabled"]
    assert len(active) == 0


def test_idempotency_present():
    packet = prt.build_packet()
    assert packet["idempotency_partial_failure_panel"]["idempotency_required_before_live"] is True


def test_partial_failure_present():
    packet = prt.build_packet()
    assert packet["idempotency_partial_failure_panel"]["partial_failure_policy_required"] is True


def test_no_live_retry_loop():
    packet = prt.build_packet()
    assert packet["idempotency_partial_failure_panel"]["current_live_retry_loop"] is False


def test_future_live_handoff_requires_go():
    packet = prt.build_packet()
    assert packet["future_live_handoff_panel"]["one_platform_live_requires_explicit_go"] is True


def test_evidence_summary_present():
    packet = prt.build_packet()
    assert bool(packet["evidence_summary"])


def test_next_allowed_action_requires_audit():
    txt = _read("fixture_data.js")
    assert "AUDIT_OF_0163_EVIDENCE_BEFORE_ANY_NEXT_TASK" in txt



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
    assert prt._count_secret_hits() == 0


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
    packet = prt.build_packet()
    assert packet["red_green_market_direction_semantics"] is False


def test_active_frontend_scope_within_shell():
    packet = prt.build_packet()
    assert "ui/institutional_shell" in packet["active_frontend_code_changed_scope"]


def test_runtime_authority_true_fails():
    packet = prt.build_packet()
    packet["runtime_authority"] = True
    res = prt.validate_packet(packet)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_live_posting_enabled_true_fails():
    packet = prt.build_packet()
    packet["live_posting_enabled_now"] = True
    res = prt.validate_packet(packet)
    assert not res["valid"]
    assert "live_posting_enabled_now_must_be_false" in res["errors"]


def test_platform_live_api_enabled_fails():
    packet = prt.build_packet()
    packet["platform_capability_registry_panel"][0]["live_api"] = "enabled"
    res = prt.validate_packet(packet)
    assert not res["valid"]
    assert any("platform_live_api_must_be_disabled" in e for e in res["errors"])


def test_missing_platform_fails():
    packet = prt.build_packet()
    packet["platform_capability_registry_panel"] = [
        p for p in packet["platform_capability_registry_panel"] if p["platform_id"] != "telegram"
    ]
    res = prt.validate_packet(packet)
    assert not res["valid"]
    assert "platform_missing_telegram" in res["errors"]


def test_active_publish_control_fails():
    packet = prt.build_packet()
    packet["publish_disabled_control_surface"][0]["state"] = "enabled"
    res = prt.validate_packet(packet)
    assert not res["valid"]
    assert any("control_must_be_disabled" in e for e in res["errors"])


def test_telegram_send_message_enabled_fails():
    packet = prt.build_packet()
    for g in packet["telegram_pilot_tower_panel"]["sub_gates"]:
        if g["gate"] == "send_message":
            g["state"] = "enabled"
    res = prt.validate_packet(packet)
    assert not res["valid"]
    assert "telegram_send_message_must_be_disabled" in res["errors"]


def test_packet_status_pass_with_errors_fails():
    packet = prt.build_packet()
    packet["runtime_authority"] = True
    packet["packet_status"] = "pass"
    res = prt.validate_packet(packet)
    assert not res["valid"]
    assert "packet_status_pass_but_errors_exist" in res["errors"]


def test_shell_prototype_tests_module_importable():
    import tests.test_institutional_shell_prototype as shell_tests
    assert hasattr(shell_tests, "test_valid_packet_passes")


def test_command_center_tests_module_importable():
    import tests.test_institutional_command_center_screen as cc_tests
    assert hasattr(cc_tests, "test_valid_packet_passes")


def test_content_studio_tests_module_importable():
    import tests.test_institutional_content_studio_screen as csd_tests
    assert hasattr(csd_tests, "test_valid_packet_passes")


def test_summary_validation_valid_true():
    s = prt.summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"
    assert s["platform_count"] == 8
    assert s["dry_run_platform_count"] == 8
    assert s["live_enabled_platform_count"] == 0
    assert s["scheduler_enabled_platform_count"] == 0
    assert s["public_postable_platform_count"] == 0
    assert s["telegram_pilot_gate_count"] == 11
    assert s["disabled_control_count"] == 11
    assert s["active_publish_control_count"] == 0
    assert s["fetch_call_count"] == 0
    assert s["secret_visible_count"] == 0
    assert s["kill_switch_status"] == "active"


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "pre-alpha-institutional-publish-readiness-tower-screen-summary"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["packet_status"] == "pass"
    assert out["validation_valid"] is True
    assert out["secret_visible_count"] == 0
