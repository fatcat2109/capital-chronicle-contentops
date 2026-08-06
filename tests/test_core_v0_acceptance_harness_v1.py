"""Tests for the canonical CORE V0 acceptance harness (Work Package E, scope item H).

The harness is the launch oracle Work Package G will run, so it must fail loudly on
tampered or incomplete evidence. Half of these tests are deliberately negative: a gate
that cannot fail proves nothing.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from live_contentops.core_v0_acceptance_harness_v1 import (
    FAIL,
    NOT_APPLICABLE,
    PASS,
    REQUIRED_EVIDENCE_FILES,
    REQUIRED_GATES,
    AcceptanceError,
    run_acceptance,
)
from live_contentops.core_v0_shadow_soak_runner_v1 import run_core_v0_shadow_soak

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def evidence(tmp_path_factory):
    root = tmp_path_factory.mktemp("wp_e_acceptance")
    output = root / "out"
    run_core_v0_shadow_soak(
        repo_root=REPO_ROOT,
        store_path=root / "store.sqlite",
        output_dir=output,
        logical_days=2,
    )
    return {"dir": output, "store": root / "store.sqlite"}


def _tamper(evidence, tmp_path, mutate) -> dict:
    """Copy the accepted evidence, mutate it, and re-run acceptance."""
    import shutil

    target = tmp_path / "tampered"
    shutil.copytree(evidence["dir"], target)
    mutate(target)
    return run_acceptance(evidence_dir=target)


def test_accepted_evidence_passes_every_gate(evidence) -> None:
    result = run_acceptance(evidence_dir=evidence["dir"], store_path=evidence["store"])
    assert result["acceptance_status"] == PASS
    assert not result["failed_gates"]
    assert not result["not_applicable_gates"]
    assert {row["gate"] for row in result["gates"]} >= set(REQUIRED_GATES)


def test_harness_is_not_the_noisy_historical_suite(evidence) -> None:
    result = run_acceptance(evidence_dir=evidence["dir"], store_path=evidence["store"])
    assert result["runs_noisy_historical_full_suite_as_launch_oracle"] is False
    assert result["full_suite_pass_claimed"] is False
    assert result["ci_pass_claimed"] is False


def test_durable_gate_reopens_the_real_store(evidence) -> None:
    result = run_acceptance(evidence_dir=evidence["dir"], store_path=evidence["store"])
    gate = next(row for row in result["gates"] if row["gate"] == "durable_replay")
    assert gate["status"] == PASS
    assert gate["detail"]["verified_from"] == "independent_store_reopen"
    assert gate["detail"]["schema_version"] == 4
    assert gate["detail"]["integrity_verified"] is True
    assert gate["detail"]["restart_reconstruction_status"] == "PASS"


def test_durable_gate_degrades_honestly_without_a_store(evidence) -> None:
    result = run_acceptance(evidence_dir=evidence["dir"])
    gate = next(row for row in result["gates"] if row["gate"] == "durable_replay")
    # Still verifiable from the recorded summary, but it must say so rather than imply
    # it re-verified the store.
    assert gate["detail"]["verified_from"] == "run_summary_only_no_store_supplied"


def test_missing_evidence_directory_fails_closed(tmp_path) -> None:
    with pytest.raises(AcceptanceError, match="evidence_dir_not_found"):
        run_acceptance(evidence_dir=tmp_path / "nope")


def test_empty_evidence_directory_never_reports_pass(tmp_path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = run_acceptance(evidence_dir=empty)
    assert result["acceptance_status"] == FAIL
    assert "accepted_evidence_packet_completeness" in result["failed_gates"]
    # Unevaluatable gates must be NOT_APPLICABLE, never silently passed.
    assert set(result["not_applicable_gates"]) >= set(REQUIRED_GATES) - {
        "accepted_evidence_packet_completeness",
        "no_secret_posture",
    }


@pytest.mark.parametrize("filename", REQUIRED_EVIDENCE_FILES)
def test_any_missing_required_file_fails_completeness(evidence, tmp_path, filename) -> None:
    result = _tamper(evidence, tmp_path / filename.replace(".", "_"), lambda d: (d / filename).unlink())
    assert "accepted_evidence_packet_completeness" in result["failed_gates"]
    assert result["acceptance_status"] == FAIL


def test_a_true_live_authority_flag_fails_the_secret_posture_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "soak_run_summary.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["public_write_authority"] = True
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "no_secret_posture" in result["failed_gates"]
    gate = next(row for row in result["gates"] if row["gate"] == "no_secret_posture")
    assert any("public_write_authority" in row for row in gate["detail"]["live_authority_flags_set_true"])


def test_secret_shaped_material_fails_the_secret_posture_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "soak_launch_edge.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["leaked"] = "Bearer abcdefghijklmnopqrstuvwxyz0123456789"
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "no_secret_posture" in result["failed_gates"]


def test_a_missing_release_binding_fails_the_release_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "soak_launch_edge.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["required_bindings"] = data["required_bindings"][:5]
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "release_authorization_integrity" in result["failed_gates"]


def test_boolean_approval_as_authority_fails_the_release_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "soak_launch_edge.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["boolean_approval_accepted_as_authority"] = True
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "release_authorization_integrity" in result["failed_gates"]


def test_an_auto_retried_unknown_write_fails_the_reconciliation_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "soak_launch_edge.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["unknown_writes_auto_retried"] = 1
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "unknown_write_and_reconciliation" in result["failed_gates"]


def test_processing_under_kill_switch_fails_the_mode_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "soak_launch_edge.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["kill_switch_release_queue"]["operations_processed"] = 3
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "mode_and_kill_switch_behaviour" in result["failed_gates"]


def test_a_second_production_runner_fails_the_canonical_path_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "soak_run_summary.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["second_production_runner_created"] = True
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "one_canonical_execution_path" in result["failed_gates"]


def test_a_drifted_policy_hash_fails_the_authority_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "soak_run_summary.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["selection_calibration_policy_logical_hash"] = "0" * 64
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "authority_and_policy_bindings" in result["failed_gates"]


def test_a_blocked_case_reaching_review_ready_fails_the_lineage_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "soak_logical_days.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for case in data["logical_days"][0]["cases"]:
            if case["review_result"] != "PASS":
                case["terminal_state"] = "REVIEW_READY"
                break
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "package_lineage" in result["failed_gates"]


def test_a_disagreeing_v5_snapshot_fails_the_consistency_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "v5_soak_snapshot.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["launch_readiness_disposition"] = "READY_FOR_EXACT_AUTHORIZED_LIVE_COHORT"
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "v5_snapshot_consistency" in result["failed_gates"]


def test_a_hand_authored_v5_snapshot_fails_the_consistency_gate(evidence, tmp_path) -> None:
    def mutate(directory: pathlib.Path) -> None:
        path = directory / "v5_soak_snapshot.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["generated_from_real_run"] = False
        path.write_text(json.dumps(data), encoding="utf-8")

    result = _tamper(evidence, tmp_path, mutate)
    assert "v5_snapshot_consistency" in result["failed_gates"]


def test_every_gate_reports_a_reason(evidence) -> None:
    result = run_acceptance(evidence_dir=evidence["dir"], store_path=evidence["store"])
    for row in result["gates"]:
        assert row["reason"], row["gate"]
        assert row["status"] in (PASS, FAIL, NOT_APPLICABLE)
