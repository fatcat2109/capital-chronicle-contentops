"""Tests for operator replay console render-spec / display-binding (SCD, 0174AW).

Local-only, deterministic, fail-closed. Verifies schema shape, per-object
validation states, read-only/display-only invariants, action_enabled blocking,
ui_runtime/browser/screenshot blocking, no_html_css_js/no_api/no_browser/
no_screenshot assertions, live/public/executable/api-gate blocking, recognized
layout regions and deterministic order, display slot source binding / copy-safe /
redaction / mono / semantic color role, status token status/severity/color
consistency, RenderSpecReport fail-closed precedence (BLOCKED > UNKNOWN >
REVIEW_REQUIRED > PASS), current-vs-historical truth binding, the projection
helper inventing nothing, and forbidden financial/signal/Telegram/API/UI-runtime
language blocking. No network, providers, credentials, platform APIs, webhooks,
OAuth, UI runtime, DOM, browser, or live behavior.
"""
import json
import os
from pathlib import Path

from live_contentops import scd_operator_replay_console_render_spec as rs

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scd_render_spec"


def _load(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_other(feature, name):
    path = Path(__file__).parent.parent / "fixtures" / feature / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Render spec ------------------------------------------------------------------

def test_render_spec_pass():
    res = rs.validate_operator_replay_console_render_spec(_load("render_spec_pass.json"))
    assert res["validation_state"] == rs.PASS, res


def test_render_spec_blocked_ui_runtime():
    res = rs.validate_operator_replay_console_render_spec(_load("render_spec_blocked_ui_runtime.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_render_spec_blocked_action():
    res = rs.validate_operator_replay_console_render_spec(_load("render_spec_blocked_action.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_render_spec_unknown():
    res = rs.validate_operator_replay_console_render_spec(_load("render_spec_unknown.json"))
    assert res["validation_state"] == rs.UNKNOWN, res


def test_render_spec_blocks_each_ui_flag():
    for flag in rs.FORBIDDEN_UI_FLAGS:
        packet = _load("render_spec_pass.json")
        packet[flag] = True
        res = rs.validate_operator_replay_console_render_spec(packet)
        assert res["validation_state"] == rs.BLOCKED, f"{flag}: {res}"


def test_render_spec_requires_each_required_region():
    for region in rs.REQUIRED_REGIONS:
        packet = _load("render_spec_pass.json")
        packet["layout_regions"] = [r for r in packet["layout_regions"] if r != region]
        res = rs.validate_operator_replay_console_render_spec(packet)
        assert res["validation_state"] == rs.BLOCKED, f"{region}: {res}"


def test_render_spec_requires_current_truth_separation():
    packet = _load("render_spec_pass.json")
    packet["current_vs_historical_truth_binding"]["stale_or_historical_refs_separated"] = False
    res = rs.validate_operator_replay_console_render_spec(packet)
    assert res["validation_state"] == rs.BLOCKED, res


# --- Layout region ----------------------------------------------------------------

def test_region_command_hero_pass():
    res = rs.validate_replay_console_layout_region_spec(_load("region_command_hero_pass.json"))
    assert res["validation_state"] == rs.PASS, res


def test_region_blocker_banner_pass():
    res = rs.validate_replay_console_layout_region_spec(_load("region_blocker_banner_pass.json"))
    assert res["validation_state"] == rs.PASS, res


def test_region_stage_matrix_pass():
    res = rs.validate_replay_console_layout_region_spec(_load("region_stage_matrix_pass.json"))
    assert res["validation_state"] == rs.PASS, res


def test_region_blocked_unknown_name():
    region = _load("region_base_for_unknown_name.json")
    region["region_name"] = "not_a_region"
    res = rs.validate_replay_console_layout_region_spec(region)
    assert res["validation_state"] == rs.BLOCKED, res


def test_region_blocked_live():
    res = rs.validate_replay_console_layout_region_spec(_load("region_blocked_live.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_region_deterministic_order_from_helper():
    specs = rs.build_layout_region_specs("rs_test")
    indices = [s["region_order_index"] for s in specs]
    assert indices == sorted(indices), indices
    names = [s["region_name"] for s in specs]
    assert names[0] == "command_hero", names


# --- Status token -----------------------------------------------------------------

def test_token_pass():
    res = rs.validate_replay_console_status_token_binding(_load("token_pass.json"))
    assert res["validation_state"] == rs.PASS, res


def test_token_blocked():
    res = rs.validate_replay_console_status_token_binding(_load("token_blocked.json"))
    assert res["validation_state"] == rs.PASS, res


def test_token_review_required():
    res = rs.validate_replay_console_status_token_binding(_load("token_review_required.json"))
    assert res["validation_state"] == rs.PASS, res


def test_token_unknown():
    res = rs.validate_replay_console_status_token_binding(_load("token_unknown.json"))
    assert res["validation_state"] == rs.PASS, res


def test_token_blocked_mismatch():
    res = rs.validate_replay_console_status_token_binding(_load("token_blocked_mismatch.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_token_blocked_ready_flags():
    res = rs.validate_replay_console_status_token_binding(_load("token_blocked_ready.json"))
    assert res["validation_state"] == rs.BLOCKED, res


# --- Display slot binding ---------------------------------------------------------

def test_slot_headline_pass():
    res = rs.validate_replay_console_display_slot_binding(_load("slot_headline_pass.json"))
    assert res["validation_state"] == rs.PASS, res


def test_slot_evidence_pass():
    res = rs.validate_replay_console_display_slot_binding(_load("slot_evidence_pass.json"))
    assert res["validation_state"] == rs.PASS, res


def test_slot_copy_safe_pass():
    res = rs.validate_replay_console_display_slot_binding(_load("slot_copy_safe_pass.json"))
    assert res["validation_state"] == rs.PASS, res


def test_slot_blocked_action():
    res = rs.validate_replay_console_display_slot_binding(_load("slot_blocked_action.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_slot_blocked_endpoint():
    res = rs.validate_replay_console_display_slot_binding(_load("slot_blocked_endpoint.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_slot_blocked_telegram():
    res = rs.validate_replay_console_display_slot_binding(_load("slot_blocked_telegram.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_slot_blocked_signal_language():
    res = rs.validate_replay_console_display_slot_binding(_load("slot_blocked_signal.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_slot_unknown_missing_field():
    res = rs.validate_replay_console_display_slot_binding(_load("slot_unknown_missing_field.json"))
    assert res["validation_state"] == rs.UNKNOWN, res


def test_slot_copy_safe_requires_copy_safe_flag():
    slot = _load("slot_copy_safe_pass.json")
    slot["copy_safe"] = False
    res = rs.validate_replay_console_display_slot_binding(slot)
    assert res["validation_state"] == rs.BLOCKED, res


# --- Render spec report -----------------------------------------------------------

def test_report_pass():
    res = rs.validate_replay_console_render_spec_report(_load("report_pass.json"))
    assert res["validation_state"] == rs.PASS, res


def test_report_blocked_missing():
    res = rs.validate_replay_console_render_spec_report(_load("report_blocked_missing.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_report_blocked_html():
    res = rs.validate_replay_console_render_spec_report(_load("report_blocked_html.json"))
    assert res["validation_state"] == rs.BLOCKED, res


def test_report_review_required():
    res = rs.validate_replay_console_render_spec_report(_load("report_review_required.json"))
    assert res["validation_state"] == rs.REVIEW_REQUIRED, res


def test_report_fail_closed_precedence_blocked_over_unknown():
    report = _load("report_pass.json")
    report["blocked_bindings"] = ["slot_x"]
    report["unknown_bindings"] = ["slot_y"]
    res = rs.validate_replay_console_render_spec_report(report)
    assert res["validation_state"] == rs.BLOCKED, res


def test_report_unknown_when_missing_without_blocked():
    report = _load("report_pass.json")
    report["missing_required_slots"] = ["stage_matrix_slot"]
    report["final_recommendation"] = "UNKNOWN"
    res = rs.validate_replay_console_render_spec_report(report)
    assert res["validation_state"] == rs.UNKNOWN, res


# --- Projection helper ------------------------------------------------------------

def test_projection_helper_pass_over_view_model():
    view_model = _read_other("scd_operator_replay_console", "view_model_pass.json")
    evidence = _read_other("scd_operator_replay_console", "evidence_bundle_pass.json")
    export = _read_other("scd_operator_replay_console", "copy_safe_export_pass.json")
    spec = rs.build_render_spec_from_view_model(view_model, evidence, export)
    res = rs.validate_operator_replay_console_render_spec(spec)
    assert res["validation_state"] == rs.PASS, (spec, res)
    # Helper invents no UI-runtime / browser / screenshot requirement.
    assert spec["ui_runtime_required"] is False
    assert spec["browser_required"] is False
    assert spec["screenshot_required"] is False


def test_projection_helper_invents_no_refs():
    spec = rs.build_render_spec_from_view_model({"view_model_id": "vm_x"}, {}, {})
    # No fabricated evidence/export ids when not supplied.
    assert spec["evidence_bundle_id"] == ""
    assert spec["copy_safe_export_bundle_id"] == ""
    # All region/token skeletons validate individually.
    for region in rs.build_layout_region_specs(spec["render_spec_id"]):
        assert rs.validate_replay_console_layout_region_spec(region)["validation_state"] == rs.PASS
    for token in rs.build_status_token_bindings(spec["render_spec_id"]):
        assert rs.validate_replay_console_status_token_binding(token)["validation_state"] == rs.PASS


# --- Global flag invariants -------------------------------------------------------

def test_no_pass_fixture_grants_live_or_executable():
    for fname in os.listdir(FIXTURE_DIR):
        if "blocked" in fname:
            continue
        data = _load(fname)
        if data.get("validation_state") != "PASS":
            continue
        for flag in ("public_ready", "live_ready", "executable_dispatch", "live_eligibility", "api_gate_required"):
            assert data.get(flag) in (False, None), f"{fname}:{flag}"
        for flag in ("action_enabled", "ui_runtime_required", "browser_required", "screenshot_required"):
            if flag in data:
                assert data[flag] is False, f"{fname}:{flag}"
