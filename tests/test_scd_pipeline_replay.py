"""Tests for end-to-end mock pipeline replay orchestrator (SCD, 0174AU).

Local-only, deterministic, fail-closed. Verifies schema shape, per-object
validation states, deterministic stage ordering, allow_* flag blocking, all
live/public/executable/api-gate flag blocking, safety-summary no_* assertions,
evidence-manifest completeness and mutation blocking, final-report fail-closed
precedence (BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS), the deterministic
replay helper reusing existing stage validators without fabrication, and
forbidden financial/signal/Telegram/API language blocking. No network,
providers, credentials, platform APIs, webhooks, OAuth, or live behavior.
"""
import json
import os
from pathlib import Path

from live_contentops import scd_pipeline_replay as pr

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scd_pipeline_replay"


def _load(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Replay input -----------------------------------------------------------------

def test_input_pass():
    res = pr.validate_pipeline_replay_input(_load("input_pass.json"))
    assert res["validation_state"] == pr.PASS, res


def test_input_blocked_allow_network():
    res = pr.validate_pipeline_replay_input(_load("input_blocked_allow_network.json"))
    assert res["validation_state"] == pr.BLOCKED, res


def test_input_unknown_missing_refs():
    res = pr.validate_pipeline_replay_input(_load("input_unknown_missing_refs.json"))
    assert res["validation_state"] == pr.UNKNOWN, res


def test_input_blocks_each_allow_flag():
    for flag in pr.FORBIDDEN_ALLOW_FLAGS:
        packet = _load("input_pass.json")
        packet[flag] = True
        res = pr.validate_pipeline_replay_input(packet)
        assert res["validation_state"] == pr.BLOCKED, f"{flag}: {res}"


def test_input_blocks_non_canonical_stage_order():
    packet = _load("input_pass.json")
    packet["stage_order"] = ["mock_dispatch", "content_intent"]
    res = pr.validate_pipeline_replay_input(packet)
    assert res["validation_state"] == pr.BLOCKED, res


def test_input_blocks_unrecognized_stage():
    packet = _load("input_pass.json")
    packet["stage_order"] = ["content_intent", "not_a_real_stage"]
    res = pr.validate_pipeline_replay_input(packet)
    assert res["validation_state"] == pr.BLOCKED, res


# --- Stage replay result ----------------------------------------------------------

def test_stage_content_intent_pass():
    res = pr.validate_pipeline_stage_replay_result(_load("stage_content_intent_pass.json"))
    assert res["validation_state"] == pr.PASS, res


def test_stage_editorial_workbench_pass():
    res = pr.validate_pipeline_stage_replay_result(_load("stage_editorial_workbench_pass.json"))
    assert res["validation_state"] == pr.PASS, res


def test_stage_platform_payload_compile_pass():
    res = pr.validate_pipeline_stage_replay_result(_load("stage_platform_payload_compile_pass.json"))
    assert res["validation_state"] == pr.PASS, res


def test_stage_one_button_gate_pass():
    res = pr.validate_pipeline_stage_replay_result(_load("stage_one_button_gate_pass.json"))
    assert res["validation_state"] == pr.PASS, res


def test_stage_mock_dispatch_pass():
    res = pr.validate_pipeline_stage_replay_result(_load("stage_mock_dispatch_pass.json"))
    assert res["validation_state"] == pr.PASS, res


def test_stage_blocked_live():
    res = pr.validate_pipeline_stage_replay_result(_load("stage_blocked_live.json"))
    assert res["validation_state"] == pr.BLOCKED, res


def test_stage_blocked_telegram():
    res = pr.validate_pipeline_stage_replay_result(_load("stage_blocked_telegram.json"))
    assert res["validation_state"] == pr.BLOCKED, res


def test_stage_blocked_signal_language():
    res = pr.validate_pipeline_stage_replay_result(_load("stage_blocked_signal.json"))
    assert res["validation_state"] == pr.BLOCKED, res


def test_stage_blocks_api_gate_required():
    stage = _load("stage_content_intent_pass.json")
    stage["api_gate_required"] = True
    res = pr.validate_pipeline_stage_replay_result(stage)
    assert res["validation_state"] == pr.BLOCKED, res


# --- Safety summary ---------------------------------------------------------------

def test_safety_summary_pass():
    res = pr.validate_pipeline_replay_safety_summary(_load("safety_summary_pass.json"))
    assert res["validation_state"] == pr.PASS, res


def test_safety_summary_blocked():
    res = pr.validate_pipeline_replay_safety_summary(_load("safety_summary_blocked.json"))
    assert res["validation_state"] == pr.BLOCKED, res


def test_safety_summary_requires_every_assertion():
    for flag in pr.SAFETY_ASSERTIONS:
        summary = _load("safety_summary_pass.json")
        summary[flag] = False
        res = pr.validate_pipeline_replay_safety_summary(summary)
        assert res["validation_state"] == pr.BLOCKED, f"{flag}: {res}"


# --- Evidence manifest ------------------------------------------------------------

def test_evidence_manifest_pass():
    res = pr.validate_pipeline_replay_evidence_manifest(_load("evidence_manifest_pass.json"))
    assert res["validation_state"] == pr.PASS, res


def test_evidence_manifest_blocked_mutation():
    res = pr.validate_pipeline_replay_evidence_manifest(_load("evidence_manifest_blocked_mutation.json"))
    assert res["validation_state"] == pr.BLOCKED, res


def test_evidence_manifest_incomplete_review():
    manifest = _load("evidence_manifest_pass.json")
    manifest["evidence_complete"] = False
    res = pr.validate_pipeline_replay_evidence_manifest(manifest)
    assert res["validation_state"] == pr.REVIEW_REQUIRED, res


# --- Replay report ----------------------------------------------------------------

def test_report_pass():
    res = pr.validate_pipeline_replay_report(_load("report_pass.json"))
    assert res["validation_state"] == pr.PASS, res


def test_report_blocked_contradiction():
    res = pr.validate_pipeline_replay_report(_load("report_blocked_contradiction.json"))
    assert res["validation_state"] == pr.BLOCKED, res


def test_report_blocked_api_gate():
    res = pr.validate_pipeline_replay_report(_load("report_blocked_api_gate.json"))
    assert res["validation_state"] == pr.BLOCKED, res


def test_report_review_required():
    res = pr.validate_pipeline_replay_report(_load("report_review_required.json"))
    assert res["validation_state"] == pr.REVIEW_REQUIRED, res


def test_report_unknown_stage():
    res = pr.validate_pipeline_replay_report(_load("report_unknown_stage.json"))
    assert res["validation_state"] == pr.UNKNOWN, res


def test_report_fail_closed_precedence_blocked_over_unknown():
    report = _load("report_pass.json")
    report["stage_results"] = [
        {"stage_name": "content_intent", "result": "UNKNOWN"},
        {"stage_name": "editorial_workbench", "result": "BLOCKED"},
    ]
    # Final still PASS -> must be flagged BLOCKED (blocked beats unknown).
    res = pr.validate_pipeline_replay_report(report)
    assert res["validation_state"] == pr.BLOCKED, res


# --- Deterministic replay helper --------------------------------------------------

def test_replay_helper_pass_over_pass_fixtures():
    # Use real PASS packets from prior module fixtures via their validators.
    gate_result = _read_other("scd_dispatch_gate", "gate_result_pass.json")
    record = _read_other("scd_mock_dispatch", "record_pass.json")
    manual_export = _read_other("scd_mock_dispatch", "manual_export_pass.json")
    stage_packets = [
        {"stage_name": "one_button_gate", "packet": gate_result},
        {"stage_name": "mock_dispatch", "packet": record},
        {"stage_name": "manual_export", "packet": manual_export},
    ]
    out = pr.replay_scd_pipeline(stage_packets)
    assert out["final_recommendation"] == pr.PASS, out
    assert all(r["result"] == pr.PASS for r in out["stage_results"]), out


def test_replay_helper_blocks_on_blocked_stage():
    record_blocked = _read_other("scd_mock_dispatch", "record_blocked_network.json")
    stage_packets = [{"stage_name": "mock_dispatch", "packet": record_blocked}]
    out = pr.replay_scd_pipeline(stage_packets)
    assert out["final_recommendation"] == pr.BLOCKED, out


def test_replay_helper_invents_nothing_for_unmapped_stage():
    out = pr.replay_scd_pipeline([{"stage_name": "content_intent", "packet": {}}])
    # content_intent has no reusable mapping here -> UNKNOWN, never fabricated PASS.
    assert out["stage_results"][0]["result"] == pr.UNKNOWN, out
    assert out["final_recommendation"] == pr.UNKNOWN, out


def _read_other(feature, name):
    path = Path(__file__).parent.parent / "fixtures" / feature / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Global flag invariants -------------------------------------------------------

def test_no_pass_fixture_grants_live_or_executable():
    for fname in os.listdir(FIXTURE_DIR):
        # blocked_* fixtures intentionally set live/executable/api true to prove
        # the validator blocks them; their declared label is not authoritative.
        if "blocked" in fname:
            continue
        data = _load(fname)
        if data.get("validation_state") != "PASS":
            continue
        for flag in ("public_ready", "live_ready", "executable_dispatch", "live_eligibility", "api_gate_required"):
            assert data.get(flag) in (False, None), f"{fname}:{flag}"
