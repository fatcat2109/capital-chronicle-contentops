import json
import os
import subprocess
import sys

from live_contentops import institutional_content_studio_screen as cs

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")


def _read(name):
    with open(os.path.join(SHELL_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def test_valid_packet_passes():
    packet = cs.build_packet()
    res = cs.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_shell_files_exist():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        assert os.path.isfile(os.path.join(SHELL_DIR, name)), name


def test_content_studio_screen_exists():
    txt = _read("fixture_data.js")
    assert "content_studio_detail" in txt
    assert "daily_content_studio" in txt


def test_hero_status_band_exists():
    txt = _read("fixture_data.js")
    assert "Capital Chronicle Content Studio" in txt


def test_safety_ribbon_includes_required():
    txt = _read("fixture_data.js")
    for b in cs.REQUIRED_SAFETY_BANNERS:
        assert b in txt, b


def test_lane_pre_alpha_allowed_review_only():
    txt = _read("fixture_data.js")
    assert "pre_alpha_process" in txt
    assert "allowed_review_only" in txt


def test_lane_grounded_news_with_constraints():
    txt = _read("fixture_data.js")
    assert "grounded_news_context" in txt
    assert "allowed_with_constraints" in txt


def test_lane_future_artifact_blocked():
    packet = cs.build_packet()
    lanes = {l["lane_id"]: l for l in packet["content_lanes"]}
    assert lanes["future_artifact_backed"]["state"] == "blocked"


def test_lane_mixing_blocked():
    packet = cs.build_packet()
    assert packet["lane_rules"]["lane_mixing"] == "blocked"


def test_source_artifact_ids_cannot_be_invented():
    packet = cs.build_packet()
    assert packet["lane_rules"]["source_artifact_ids_invented"] == "blocked"


def test_grounded_news_hook_not_signal():
    packet = cs.build_packet()
    assert packet["grounded_news_rule_panel"]["news_is_hook_not_signal"] is True


def test_repo_news_search_disabled():
    packet = cs.build_packet()
    assert packet["grounded_news_rule_panel"]["repo_searches_or_fetches_news"] is False


def test_provider_llm_generation_disabled():
    packet = cs.build_packet()
    assert packet["draft_review_only_panel"]["repo_calls_provider_llm_api"] is False
    assert packet["provider_llm_api_allowed_now"] is False


def test_source_evidence_requirements():
    txt = _read("fixture_data.js")
    for f in ("source_url", "source_date", "freshness_label", "limitation_label"):
        assert f in txt, f


def test_draft_review_only():
    packet = cs.build_packet()
    assert packet["draft_review_only_panel"]["draft_is_review_only"] is True


def test_final_public_copy_generation_disabled():
    packet = cs.build_packet()
    assert packet["draft_review_only_panel"]["final_public_copy_generation"] == "disabled"


def test_manual_review_required():
    packet = cs.build_packet()
    assert packet["draft_review_only_panel"]["manual_jim_review_required"] is True


def test_claim_risk_classifier_classes():
    txt = _read("fixture_data.js")
    for c in cs.REQUIRED_CLAIM_CLASSES:
        assert c in txt, c


def test_market_sensitive_claim_blocked_or_transformed():
    packet = cs.build_packet()
    for c in packet["claim_risk_classifier"]:
        if c["class"] == "market_sensitive_claim":
            h = c["handling"]


def test_guardrails_buy_sell_hold_forbidden():
    txt = _read("fixture_data.js")
    assert "buy_sell_hold" in txt


def test_guardrails_long_short_forbidden():
    txt = _read("fixture_data.js")
    assert "long_short" in txt


def test_guardrails_position_entry_exit_target_forbidden():
    txt = _read("fixture_data.js")
    for g in ("position_sizing", "entries_exits", "target_prices"):
        assert g in txt, g


def test_guardrails_signal_service_forbidden():
    txt = _read("fixture_data.js")
    assert "signal_service_framing" in txt


def test_guardrails_broker_execution_forbidden():
    txt = _read("fixture_data.js")
    assert "execution_broker_order_routing" in txt


def test_guardrails_fake_alpha_forbidden():
    txt = _read("fixture_data.js")
    assert "fake_alpha" in txt


def test_guardrails_unsupported_numeric_forbidden():
    txt = _read("fixture_data.js")
    assert "unsupported_numeric_market_claims" in txt


def test_limitations_keep_missing_degraded_proxy():
    packet = cs.build_packet()
    lim = packet["limitations_refusal_mode"]
    assert lim["missing_stays_missing"] is True
    assert lim["degraded_stays_degraded"] is True
    assert lim["proxy_only_is_labeled"] is True


def test_platform_fit_dry_run_read_only():
    packet = cs.build_packet()
    for p in packet["platform_fit_preview"]:
        assert p["mode"] == "dry_run_read_only"


def test_platform_fit_no_publish_schedule_api_export():
    packet = cs.build_packet()
    pfc = packet["platform_fit_constraints"]
    for key in ("export_to_platform", "schedule", "publish", "live_api"):
        assert pfc[key] == "disabled"


def test_decision_ledger_requires_operator():
    packet = cs.build_packet()
    assert packet["decision_ledger_handoff"]["operator_decision_required"] is True


def test_decision_ledger_no_auto_approve():
    packet = cs.build_packet()
    assert packet["decision_ledger_handoff"]["approval_is_automatic"] is False


def test_draft_inspector_handoff_exists():
    packet = cs.build_packet()
    assert packet["draft_inspector_handoff"]["next_drilldown_surface"] == "draft_inspector"


def test_blocked_action_final_public_copy():
    txt = _read("fixture_data.js")
    assert "generate_final_public_copy" in txt


def test_blocked_action_provider_api():
    txt = _read("fixture_data.js")
    assert "provider_llm_api" in txt


def test_blocked_action_news_search():
    txt = _read("fixture_data.js")
    assert "news_search_fetch" in txt


def test_blocked_action_platform_api():
    txt = _read("fixture_data.js")
    assert "platform_api" in txt


def test_blocked_action_publish_schedule():
    txt = _read("fixture_data.js")
    assert "publish" in txt
    assert "schedule" in txt


def test_blocked_action_one_button_publish_all():
    txt = _read("fixture_data.js")
    assert "one_button_publish_all" in txt


def test_evidence_summary_present():
    packet = cs.build_packet()
    assert bool(packet["evidence_summary"])


def test_next_allowed_action_requires_audit():
    txt = _read("fixture_data.js")
    assert "AUDIT_OF_0162_EVIDENCE_BEFORE_ANY_NEXT_TASK" in txt



def test_no_active_live_controls():
    app = _read("app.js")
    assert "disabled-control" in app
    assert "aria-disabled" in app


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
    assert cs._count_secret_hits() == 0


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
    packet = cs.build_packet()
    assert packet["red_green_market_direction_semantics"] is False


def test_active_frontend_scope_within_shell():
    packet = cs.build_packet()
    assert "ui/institutional_shell" in packet["active_frontend_code_changed_scope"]


def test_runtime_authority_true_fails():
    packet = cs.build_packet()
    packet["runtime_authority"] = True
    res = cs.validate_packet(packet)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_provider_llm_allowed_true_fails():
    packet = cs.build_packet()
    packet["provider_llm_api_allowed_now"] = True
    res = cs.validate_packet(packet)
    assert not res["valid"]
    assert "provider_llm_api_allowed_now_must_be_false" in res["errors"]


def test_repo_web_search_allowed_true_fails():
    packet = cs.build_packet()
    packet["repo_web_search_allowed_now"] = True
    res = cs.validate_packet(packet)
    assert not res["valid"]
    assert "repo_web_search_allowed_now_must_be_false" in res["errors"]


def test_future_artifact_unblocked_fails():
    packet = cs.build_packet()
    for l in packet["content_lanes"]:
        if l["lane_id"] == "future_artifact_backed":
            l["state"] = "allowed"
    res = cs.validate_packet(packet)
    assert not res["valid"]
    assert "future_artifact_backed_must_be_blocked" in res["errors"]


def test_missing_guardrail_fails():
    packet = cs.build_packet()
    packet["guardrail_results"] = [g for g in packet["guardrail_results"] if g["category"] != "buy_sell_hold"]
    res = cs.validate_packet(packet)
    assert not res["valid"]
    assert "guardrail_missing_buy_sell_hold" in res["errors"]


def test_packet_status_pass_with_errors_fails():
    packet = cs.build_packet()
    packet["runtime_authority"] = True
    packet["packet_status"] = "pass"
    res = cs.validate_packet(packet)
    assert not res["valid"]
    assert "packet_status_pass_but_errors_exist" in res["errors"]


def test_shell_prototype_tests_module_importable():
    import tests.test_institutional_shell_prototype as shell_tests
    assert hasattr(shell_tests, "test_valid_packet_passes")


def test_command_center_tests_module_importable():
    import tests.test_institutional_command_center_screen as cc_tests
    assert hasattr(cc_tests, "test_valid_packet_passes")


def test_summary_validation_valid_true():
    s = cs.summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"
    assert s["content_lane_count"] == 3
    assert s["allowed_lane_count"] == 2
    assert s["blocked_lane_count"] == 1
    assert s["claim_risk_class_count"] == 6
    assert s["guardrail_category_count"] == 12
    assert s["platform_fit_preview_count"] == 5
    assert s["blocked_action_count"] == 12
    assert s["fetch_call_count"] == 0
    assert s["secret_visible_count"] == 0


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "pre-alpha-institutional-content-studio-screen-summary"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["packet_status"] == "pass"
    assert out["validation_valid"] is True
    assert out["secret_visible_count"] == 0
