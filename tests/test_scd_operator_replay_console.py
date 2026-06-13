"""Tests for operator replay console read-only view model (SCD, 0174AV).

Local-only, deterministic, fail-closed. Verifies schema shape, per-object
validation states, read-only/display-only invariants, action_enabled blocking,
allow_* flag blocking, live/public/executable/api-gate flag blocking, stage
chip severity/status mapping, ViewModel headline fail-closed precedence
(BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS), evidence-bundle completeness /
redaction proof / protected path statement, copy-safe export redaction and
no-public-ready / no-live-instruction rules, current-vs-historical truth
separation, the projection helper inventing nothing, and forbidden
financial/signal/Telegram/API language blocking. No network, providers,
credentials, platform APIs, webhooks, OAuth, UI runtime, or live behavior.
"""
import json
import os
from pathlib import Path

from live_contentops import scd_operator_replay_console as rc

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scd_operator_replay_console"


def _load(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Console input ----------------------------------------------------------------

def test_input_pass():
    res = rc.validate_operator_replay_console_input(_load("input_pass.json"))
    assert res["validation_state"] == rc.PASS, res


def test_input_blocked_allow_network():
    res = rc.validate_operator_replay_console_input(_load("input_blocked_allow_network.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_input_blocks_each_allow_flag():
    for flag in rc.FORBIDDEN_ALLOW_FLAGS:
        packet = _load("input_pass.json")
        packet[flag] = True
        res = rc.validate_operator_replay_console_input(packet)
        assert res["validation_state"] == rc.BLOCKED, f"{flag}: {res}"


# --- Stage status chip ------------------------------------------------------------

def test_chip_pass():
    res = rc.validate_replay_stage_status_chip(_load("chip_pass.json"))
    assert res["validation_state"] == rc.PASS, res


def test_chip_blocked_status_is_blocking():
    res = rc.validate_replay_stage_status_chip(_load("chip_blocked_status.json"))
    assert res["validation_state"] == rc.PASS, res


def test_chip_review_required():
    res = rc.validate_replay_stage_status_chip(_load("chip_review_required.json"))
    assert res["validation_state"] == rc.PASS, res


def test_chip_unknown():
    res = rc.validate_replay_stage_status_chip(_load("chip_unknown.json"))
    assert res["validation_state"] == rc.PASS, res


def test_chip_blocked_action_enabled():
    res = rc.validate_replay_stage_status_chip(_load("chip_blocked_action_enabled.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_chip_blocked_live():
    res = rc.validate_replay_stage_status_chip(_load("chip_blocked_live.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_chip_blocked_signal_language():
    res = rc.validate_replay_stage_status_chip(_load("chip_blocked_signal.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_chip_blocked_telegram():
    res = rc.validate_replay_stage_status_chip(_load("chip_blocked_telegram.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_chip_blocked_severity_mismatch():
    chip = _load("chip_pass.json")
    chip["severity"] = "blocked"
    res = rc.validate_replay_stage_status_chip(chip)
    assert res["validation_state"] == rc.BLOCKED, res


def test_chip_blocked_status_requires_is_blocking():
    chip = _load("chip_blocked_status.json")
    chip["is_blocking_stage"] = False
    res = rc.validate_replay_stage_status_chip(chip)
    assert res["validation_state"] == rc.BLOCKED, res


# --- View model -------------------------------------------------------------------

def test_view_model_pass():
    res = rc.validate_operator_replay_console_view_model(_load("view_model_pass.json"))
    assert res["validation_state"] == rc.PASS, res


def test_view_model_blocked_contradiction():
    res = rc.validate_operator_replay_console_view_model(_load("view_model_blocked_contradiction.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_view_model_blocked_display():
    res = rc.validate_operator_replay_console_view_model(_load("view_model_blocked_display.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_view_model_review_required():
    res = rc.validate_operator_replay_console_view_model(_load("view_model_review_required.json"))
    assert res["validation_state"] == rc.REVIEW_REQUIRED, res


def test_view_model_unknown_stage():
    res = rc.validate_operator_replay_console_view_model(_load("view_model_unknown_stage.json"))
    assert res["validation_state"] == rc.UNKNOWN, res


def test_view_model_fail_closed_precedence_blocked_over_unknown():
    vm = _load("view_model_pass.json")
    vm["stage_status_chips"] = [
        {"stage_name": "content_intent", "status": "UNKNOWN"},
        {"stage_name": "editorial_workbench", "status": "BLOCKED"},
    ]
    res = rc.validate_operator_replay_console_view_model(vm)
    assert res["validation_state"] == rc.BLOCKED, res


def test_view_model_pass_requires_export_refs():
    vm = _load("view_model_pass.json")
    vm["copy_safe_export_bundle_ref"] = ""
    res = rc.validate_operator_replay_console_view_model(vm)
    assert res["validation_state"] == rc.BLOCKED, res


def test_view_model_requires_current_truth_separation():
    vm = _load("view_model_pass.json")
    vm["current_vs_historical_truth"]["stale_or_historical_refs_separated"] = False
    res = rc.validate_operator_replay_console_view_model(vm)
    assert res["validation_state"] == rc.BLOCKED, res


# --- Evidence bundle --------------------------------------------------------------

def test_evidence_bundle_pass():
    res = rc.validate_replay_evidence_bundle(_load("evidence_bundle_pass.json"))
    assert res["validation_state"] == rc.PASS, res


def test_evidence_bundle_blocked_redaction():
    res = rc.validate_replay_evidence_bundle(_load("evidence_bundle_blocked_redaction.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_evidence_bundle_blocked_endpoint():
    res = rc.validate_replay_evidence_bundle(_load("evidence_bundle_blocked_endpoint.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_evidence_bundle_unknown():
    res = rc.validate_replay_evidence_bundle(_load("evidence_bundle_unknown.json"))
    assert res["validation_state"] == rc.UNKNOWN, res


def test_evidence_bundle_requires_protected_path_statement():
    bundle = _load("evidence_bundle_pass.json")
    bundle["protected_path_statement"] = ""
    res = rc.validate_replay_evidence_bundle(bundle)
    assert res["validation_state"] == rc.BLOCKED, res


# --- Copy-safe export bundle ------------------------------------------------------

def test_copy_safe_export_pass():
    res = rc.validate_copy_safe_export_bundle(_load("copy_safe_export_pass.json"))
    assert res["validation_state"] == rc.PASS, res


def test_copy_safe_export_blocked_live():
    res = rc.validate_copy_safe_export_bundle(_load("copy_safe_export_blocked_live.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_copy_safe_export_blocked_public():
    res = rc.validate_copy_safe_export_bundle(_load("copy_safe_export_blocked_public.json"))
    assert res["validation_state"] == rc.BLOCKED, res


def test_copy_safe_export_requires_manual_notice_and_evidence():
    bundle = _load("copy_safe_export_pass.json")
    bundle["manual_publish_only_notice_included"] = False
    res = rc.validate_copy_safe_export_bundle(bundle)
    assert res["validation_state"] == rc.BLOCKED, res


# --- Projection helpers -----------------------------------------------------------

def test_projection_helper_pass_over_pass_report():
    console_input = _load("input_pass.json")
    replay_report = _read_other("scd_pipeline_replay", "report_pass.json")
    safety = _read_other("scd_pipeline_replay", "safety_summary_pass.json")
    manifest = _read_other("scd_pipeline_replay", "evidence_manifest_pass.json")
    out = rc.project_replay_console_view_model(console_input, replay_report, safety, manifest)
    assert out["headline_status"] == rc.PASS, out
    assert out["safety_counters"]["blocked_count"] == 0, out
    # Each projected chip must pass its own validator.
    for chip in out["stage_status_chips"]:
        res = rc.validate_replay_stage_status_chip(chip)
        assert res["validation_state"] == rc.PASS, (chip, res)


def test_projection_helper_blocks_on_blocked_stage():
    console_input = _load("input_pass.json")
    replay_report = _read_other("scd_pipeline_replay", "report_blocked_contradiction.json")
    out = rc.project_replay_console_view_model(console_input, replay_report, {}, {})
    assert out["headline_status"] == rc.BLOCKED, out
    blocking = [c for c in out["stage_status_chips"] if c["is_blocking_stage"]]
    assert blocking, out


def test_projection_helper_invents_nothing():
    # Empty report -> no chips fabricated, headline UNKNOWN, no invented refs.
    out = rc.project_replay_console_view_model({"console_input_id": "cin_x"}, {"stage_results": []}, {}, {})
    assert out["stage_status_chips"] == [], out
    assert out["headline_status"] == rc.UNKNOWN, out


def _read_other(feature, name):
    path = Path(__file__).parent.parent / "fixtures" / feature / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Global flag invariants -------------------------------------------------------

def test_no_pass_fixture_grants_live_or_executable():
    for fname in os.listdir(FIXTURE_DIR):
        # blocked_* fixtures intentionally set live/action/etc true to prove the
        # validator blocks them; their declared label is not authoritative.
        if "blocked" in fname:
            continue
        data = _load(fname)
        if data.get("validation_state") != "PASS":
            continue
        for flag in ("public_ready", "live_ready", "executable_dispatch", "live_eligibility", "api_gate_required"):
            assert data.get(flag) in (False, None), f"{fname}:{flag}"
        if "action_enabled" in data:
            assert data["action_enabled"] is False, f"{fname}:action_enabled"
