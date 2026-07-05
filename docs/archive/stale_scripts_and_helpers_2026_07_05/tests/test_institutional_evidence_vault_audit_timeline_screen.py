import json
import os
import subprocess
import sys

from live_contentops import institutional_evidence_vault_audit_timeline_screen as ev

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")


def _read(name):
    with open(os.path.join(SHELL_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def test_valid_packet_passes():
    packet = ev.build_packet()
    res = ev.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_shell_files_exist():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        assert os.path.isfile(os.path.join(SHELL_DIR, name)), name


def test_evidence_vault_screen_exists():
    txt = _read("fixture_data.js")
    assert "evidence_vault_detail" in txt
    assert "evidence_vault" in txt


def test_hero_status_band_exists():
    txt = _read("fixture_data.js")
    assert "Capital Chronicle Evidence Vault + Audit Timeline" in txt


def test_safety_ribbon_includes_required():
    txt = _read("fixture_data.js")
    for b in ev.REQUIRED_SAFETY_BANNERS:
        assert b in txt, b


def test_task_index_includes_all():
    packet = ev.build_packet()
    ids = [t["task_id"] for t in packet["task_evidence_packet_index"]]
    for tid in ("0157", "0158", "0159", "0160", "0161", "0162", "0163"):
        assert tid in ids, tid


def test_0163_classification():
    packet = ev.build_packet()
    idx = {t["task_id"]: t for t in packet["task_evidence_packet_index"]}
    assert idx["0163"]["classification"] == "PASS_WITH_MINOR_EVIDENCE_GAP"


def test_commit_timeline_includes_baseline():
    packet = ev.build_packet()
    heads = [c["head"] for c in packet["commit_timeline"]]
    assert "a7989ea" in heads


def test_commit_timeline_includes_all_heads():
    txt = _read("fixture_data.js")
    for h in ("260ae89", "1ae6e62", "15b87ff", "1c03ca0", "1b0f34a", "85f7627", "a7989ea"):
        assert h in txt, h


def test_validation_timeline_includes_required():
    txt = _read("fixture_data.js")
    cmds = " ".join(c["command"] for c in ev.build_packet()["validation_command_timeline"]).lower()
    for needle in ("focused", "full suite", "cli summaries", "secret scan", "git diff"):
        assert needle in cmds, needle


def test_test_history_includes_latest():
    packet = ev.build_packet()
    hist = " ".join(h["result"] for h in packet["test_result_history"])
    assert "1561 passed, 28 skipped" in hist


def test_cli_matrix_includes_screens():
    packet = ev.build_packet()
    cli = [r["summary"] for r in packet["cli_summary_snapshot_matrix"]]
    for s in ev.REQUIRED_CLI_SUMMARIES:
        assert s in cli, s


def test_minor_evidence_gap_includes_0163():
    packet = ev.build_packet()
    gaps = [g["task_id"] for g in packet["minor_evidence_gap_registry"]]
    assert "0163" in gaps


def test_secret_scan_summary_zero():
    packet = ev.build_packet()
    ssp = packet["secret_scan_summary_panel"]
    assert ssp["secret_visible_count"] == 0
    assert ssp["raw_env_path_visible"] is False
    assert ssp["raw_request_url_visible"] is False
    assert ssp["raw_platform_response_visible"] is False


def test_forbidden_scope_matrix_complete():
    packet = ev.build_packet()
    fsm = {f["scope"]: f["state"] for f in packet["forbidden_scope_matrix"]}
    for s in ev.REQUIRED_FORBIDDEN_SCOPES:
        assert fsm.get(s) == "disabled", s


def test_residual_drift_local_env():
    packet = ev.build_packet()
    drift = {d["item"]: d["state"] for d in packet["residual_drift_registry"]}
    assert "untouched" in drift["local_env_file"]


def test_residual_drift_strategy_and_bundles():
    packet = ev.build_packet()
    items = [d["item"] for d in packet["residual_drift_registry"]]
    assert "strategy_docs_pdfs" in items
    assert "project_sources_bundle_AFTER_0074" in items


def test_active_blockers_required():
    packet = ev.build_packet()
    blockers = " ".join(packet["active_blockers_panel"]).lower()
    for needle in ("live posting", "scheduler", "platform api", "credential display",
                   "antigravity", "telegram"):
        assert needle in blockers, needle


def test_evidence_packet_standard_present():
    packet = ev.build_packet()
    assert len(packet["evidence_packet_standard_panel"]) >= 10


def test_audit_classification_legend_complete():
    packet = ev.build_packet()
    classes = [c["classification"] for c in packet["audit_classification_legend"]]
    for c in ev.REQUIRED_CLASSIFICATIONS:
        assert c in classes, c


def test_next_task_discipline_requires_audit():
    packet = ev.build_packet()
    ntd = packet["next_task_discipline_panel"]
    assert "0164" in ntd["current_allowed_next_task"]
    assert ntd["cline_must_not_self_select"] is True


def test_audit_timeline_present():
    packet = ev.build_packet()
    assert len(packet["audit_timeline_visualization"]) >= 7


def test_evidence_mutation_controls_zero():
    packet = ev.build_packet()
    assert packet["evidence_mutation_controls_active_count"] == 0
    assert packet["evidence_mutation_enabled_now"] is False


def test_no_mutation_controls_in_assets():
    # app.js is the behavior layer: no mutation control wiring may exist there.
    app = _read("app.js")
    for term in ("delete_evidence", "edit_evidence", "upload_evidence", "refresh_project_sources"):
        assert term not in app, ("app.js", term)
    # In fixture data these terms may appear only as disabled/read-only control labels.
    fx = _read("fixture_data.js")
    for line in fx.splitlines():
        for term in ("delete_evidence", "edit_evidence", "upload_evidence", "refresh_project_sources"):
            if term in line:
                assert "disabled" in line, (term, line.strip())



def test_next_allowed_action_requires_audit():
    txt = _read("fixture_data.js")
    assert "AUDIT_OF_0164_EVIDENCE_BEFORE_ANY_NEXT_TASK" in txt


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
    assert ev._count_secret_hits() == 0


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
    packet = ev.build_packet()
    assert packet["red_green_market_direction_semantics"] is False


def test_active_frontend_scope_within_shell():
    packet = ev.build_packet()
    assert "ui/institutional_shell" in packet["active_frontend_code_changed_scope"]



def test_runtime_authority_true_fails():
    packet = ev.build_packet()
    packet["runtime_authority"] = True
    res = ev.validate_packet(packet)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_evidence_mutation_enabled_true_fails():
    packet = ev.build_packet()
    packet["evidence_mutation_enabled_now"] = True
    res = ev.validate_packet(packet)
    assert not res["valid"]
    assert "evidence_mutation_enabled_now_must_be_false" in res["errors"]


def test_missing_task_fails():
    packet = ev.build_packet()
    packet["task_evidence_packet_index"] = [
        t for t in packet["task_evidence_packet_index"] if t["task_id"] != "0157"
    ]
    res = ev.validate_packet(packet)
    assert not res["valid"]
    assert "task_evidence_missing_0157" in res["errors"]


def test_0163_wrong_classification_fails():
    packet = ev.build_packet()
    for t in packet["task_evidence_packet_index"]:
        if t["task_id"] == "0163":
            t["classification"] = "PASS"
    res = ev.validate_packet(packet)
    assert not res["valid"]
    assert "0163_must_be_pass_with_minor_evidence_gap" in res["errors"]


def test_forbidden_scope_enabled_fails():
    packet = ev.build_packet()
    packet["forbidden_scope_matrix"][0]["state"] = "enabled"
    res = ev.validate_packet(packet)
    assert not res["valid"]
    assert any("forbidden_scope_enabled" in e for e in res["errors"])


def test_evidence_mutation_controls_active_fails():
    packet = ev.build_packet()
    packet["evidence_mutation_controls_active_count"] = 1
    res = ev.validate_packet(packet)
    assert not res["valid"]
    assert "evidence_mutation_controls_must_be_zero" in res["errors"]


def test_packet_status_pass_with_errors_fails():
    packet = ev.build_packet()
    packet["runtime_authority"] = True
    packet["packet_status"] = "pass"
    res = ev.validate_packet(packet)
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


def test_publish_readiness_tests_module_importable():
    import tests.test_institutional_publish_readiness_tower_screen as prt_tests
    assert hasattr(prt_tests, "test_valid_packet_passes")


def test_summary_validation_valid_true():
    s = ev.summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"
    assert s["evidence_packet_count"] == 7
    assert s["commit_timeline_count"] == 12
    assert s["forbidden_scope_count"] == 22
    assert s["forbidden_scope_enabled_count"] == 0
    assert s["audit_classification_count"] == 5
    assert s["minor_evidence_gap_count"] == 1
    assert s["evidence_mutation_control_active_count"] == 0
    assert s["fetch_call_count"] == 0
    assert s["secret_visible_count"] == 0
    assert s["kill_switch_status"] == "active"


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "pre-alpha-institutional-evidence-vault-audit-timeline-screen-summary"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["packet_status"] == "pass"
    assert out["validation_valid"] is True
    assert out["secret_visible_count"] == 0
