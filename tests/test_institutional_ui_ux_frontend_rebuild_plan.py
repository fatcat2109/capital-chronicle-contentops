import json
import os
import subprocess
import sys

from live_contentops import institutional_ui_ux_frontend_rebuild_plan as plan

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def test_packet_validates_clean():
    packet = plan.build_packet()
    res = plan.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_planning_only_mode():
    packet = plan.build_packet()
    assert packet["ui_rebuild_mode"] == "planning_only"
    assert packet["runtime_authority"] is False


def test_all_forbidden_flags_false():
    packet = plan.build_packet()
    for k in plan.FORBIDDEN_TRUE:
        assert packet[k] is False, k


def test_all_required_flags_true():
    packet = plan.build_packet()
    for k in plan.REQUIRED_TRUE:
        assert packet[k] is True, k


def test_secret_visible_count_zero():
    packet = plan.build_packet()
    assert packet["secret_visible_count"] == 0


def test_status_token_vocabulary_complete():
    packet = plan.build_packet()
    for tok in plan.STATUS_TOKEN_VOCABULARY:
        assert tok in packet["status_token_vocabulary"]
    assert len(packet["status_token_vocabulary"]) == 10


def test_phase_coverage_through_0168():
    packet = plan.build_packet()
    labels = packet["phase_task_labels"]
    for needed in ("0158", "0159", "0160", "0161", "0162", "0163",
                   "0164", "0165", "0166", "0167", "0168"):
        assert any(needed in lbl for lbl in labels), needed


def test_referenced_docs_exist():
    packet = plan.build_packet()
    for key in ("master_plan_doc", "backlog_doc", "quality_matrix_doc",
                "antigravity_strategy_doc"):
        rel = packet[key]
        assert plan._doc_exists(rel), rel


def test_negative_active_frontend_changed_fails():
    packet = plan.build_packet()
    packet["active_frontend_code_changed"] = True
    res = plan.validate_packet(packet)
    assert not res["valid"]
    assert "active_frontend_code_changed_must_be_false" in res["errors"]


def test_negative_antigravity_used_now_fails():
    packet = plan.build_packet()
    packet["antigravity_used_now"] = True
    res = plan.validate_packet(packet)
    assert not res["valid"]
    assert "antigravity_used_now_must_be_false" in res["errors"]


def test_negative_live_posting_enabled_fails():
    packet = plan.build_packet()
    packet["live_posting_enabled_now"] = True
    res = plan.validate_packet(packet)
    assert not res["valid"]
    assert "live_posting_enabled_now_must_be_false" in res["errors"]


def test_negative_credential_read_allowed_fails():
    packet = plan.build_packet()
    packet["credential_read_allowed_now"] = True
    res = plan.validate_packet(packet)
    assert not res["valid"]
    assert "credential_read_allowed_now_must_be_false" in res["errors"]


def test_negative_signal_language_allowed_fails():
    packet = plan.build_packet()
    packet["signal_language_allowed"] = True
    res = plan.validate_packet(packet)
    assert not res["valid"]
    assert "signal_language_allowed_must_be_false" in res["errors"]


def test_negative_public_ready_copy_fails():
    packet = plan.build_packet()
    packet["public_ready_final_copy_generated"] = True
    res = plan.validate_packet(packet)
    assert not res["valid"]
    assert "public_ready_final_copy_generated_must_be_false" in res["errors"]


def test_negative_secret_visible_count_nonzero_fails():
    packet = plan.build_packet()
    packet["secret_visible_count"] = 1
    res = plan.validate_packet(packet)
    assert not res["valid"]


def test_negative_manual_review_required_false_fails():
    packet = plan.build_packet()
    packet["manual_review_required"] = False
    res = plan.validate_packet(packet)
    assert not res["valid"]
    assert "manual_review_required_must_be_true" in res["errors"]


def test_negative_missing_phase_task_fails():
    packet = plan.build_packet()
    packet["phase_task_labels"] = [
        lbl for lbl in packet["phase_task_labels"] if "0168" not in lbl
    ]
    res = plan.validate_packet(packet)
    assert not res["valid"]
    assert "phase_task_0168_missing" in res["errors"]


def test_summary_keys_and_values():
    s = plan.summary()
    assert s["packet_status"] == "pass"
    assert s["validation_valid"] is True
    assert s["ui_rebuild_mode"] == "planning_only"
    assert s["phase_task_count"] == 11
    assert s["status_token_count"] == 10
    assert s["secret_visible_count"] == 0
    assert s["antigravity_used_now"] is False
    assert s["live_posting_enabled_now"] is False
    assert s["kill_switch_status"] == "active"


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "pre-alpha-institutional-ui-ux-rebuild-plan-summary"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["packet_status"] == "pass"
    assert out["validation_valid"] is True
    assert out["secret_visible_count"] == 0
