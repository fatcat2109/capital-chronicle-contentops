from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from live_contentops.host_readiness_observation_consumer_v1 import (
    STATUS_AMBIGUOUS,
    STATUS_DISABLED_BY_DEFAULT,
    STATUS_FAIL_CLOSED,
    STATUS_HOST_OBSERVED,
    STATUS_NOT_VERIFIED,
    consume_current_host_readiness_observation,
)


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "tests" / "fixtures" / "main_analysis_handoff_bridge_v1.json"
MATRIX = ROOT / "tests" / "fixtures" / "host_readiness_observation_matrix_v1.json"


def _inputs() -> tuple[dict, dict]:
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    return bridge, matrix


def _run(bridge: dict, observation: dict) -> dict:
    return consume_current_host_readiness_observation(
        bridge,
        observation,
        enabled=True,
        now_utc="2026-10-17T00:30:00Z",
    )


def test_healthy_read_only_observation_attaches_to_merged_main_shadow_path():
    bridge, matrix = _inputs()
    result = _run(bridge, matrix["observations"]["healthy"])

    assert result["status"] == STATUS_HOST_OBSERVED
    assert result["readiness_classification"] == STATUS_HOST_OBSERVED
    assert result["host_observed"] is True
    assert result["runtime_proven"] is False
    assert result["publicly_proven"] is False
    assert result["shadow_status"] == "SHADOW_REVIEW_READY"
    assert result["consumer_result"]["scheduled_shadow"]["status"] == "SHADOW_CONFIRMED"
    assert result["consumer_result"]["scheduled_shadow"]["derivative_destination_count"] == 8
    assert result["identity_shadow"]["status"] == "CONFIRMED"
    assert result["destination_shadow"]["status"] == "CONFIRMED_SHADOW"
    assert result["x_ingestion_cdp"]["cdp_port"] == 9222
    assert result["publication_cdp"]["cdp_port"] == 9223
    assert result["scheduler_tasks"]["task_count"] == 3
    assert result["process_filter"]["filter_terms"] == ["ContentOps", "python", "node", "msedge"]
    assert result["packet_hashes"]["main_packet_logical_hash"] == bridge["packet_logical_hash"]
    assert result["packet_hashes"]["shadow_receipt_sha256"] == result["shadow_receipt_sha256"]
    assert result["counters"]["durable_store_write_count"] == 0
    assert result["counters"]["public_write_performed"] is False
    assert result["evidence_taxonomy"]["observation_freshness"] == "FRESH"
    assert len(result["readiness_receipt_sha256"]) == 64


def test_unavailable_matrix_is_explicit_and_fail_closed_without_losing_shadow_evidence():
    bridge, matrix = _inputs()
    result = _run(bridge, matrix["observations"]["unavailable"])

    assert result["status"] == STATUS_FAIL_CLOSED
    assert result["readiness_classification"] == STATUS_NOT_VERIFIED
    assert result["shadow_status"] == "SHADOW_REVIEW_READY"
    assert result["evidence_taxonomy"]["browseros"] == "UNAVAILABLE"
    assert result["evidence_taxonomy"]["x_ingestion_cdp"] == "UNAVAILABLE"
    assert result["evidence_taxonomy"]["publication_cdp"] == "UNAVAILABLE"
    assert result["evidence_taxonomy"]["visible_identity"] == "MISSING"
    assert result["evidence_taxonomy"]["destination_identity"] == "MISSING"
    assert result["public_write_performed"] is False


def test_ambiguous_matrix_never_becomes_host_or_runtime_proof():
    bridge, matrix = _inputs()
    result = _run(bridge, matrix["observations"]["ambiguous"])

    assert result["status"] == STATUS_AMBIGUOUS
    assert result["readiness_classification"] == STATUS_AMBIGUOUS
    assert result["host_observed"] is False
    assert result["runtime_proven"] is False
    assert result["publicly_proven"] is False
    assert result["identity_shadow"]["status"] == "AMBIGUOUS"
    assert result["destination_shadow"]["status"] == "HUMAN_REQUIRED"
    assert result["evidence_taxonomy"]["visible_identity"] == "AMBIGUOUS"
    assert result["evidence_taxonomy"]["destination_identity"] == "HUMAN_REQUIRED"


def test_disabled_default_does_not_invoke_browser_preflight_runner():
    bridge, matrix = _inputs()
    observation = deepcopy(matrix["observations"]["healthy"])
    observation.pop("browseros")
    calls: list[dict] = []

    def runner(**kwargs):
        calls.append(dict(kwargs))
        raise AssertionError("disabled observer must not invoke BrowserOS")

    result = consume_current_host_readiness_observation(
        bridge,
        observation,
        enabled=False,
        preflight_runner=runner,
    )

    assert result["status"] == STATUS_DISABLED_BY_DEFAULT
    assert result["readiness_receipt_sha256"]
    assert calls == []


def test_missing_browser_uses_one_official_bounded_preflight_runner_invocation():
    bridge, matrix = _inputs()
    observation = deepcopy(matrix["observations"]["healthy"])
    observation.pop("browseros")
    calls: list[dict] = []
    browser = deepcopy(matrix["observations"]["healthy"]["browseros"])
    browser["official_launcher_invoked"] = True
    browser["launcher_attempts"] = 1
    browser["reconnect_attempts"] = 1

    def runner(**kwargs):
        calls.append(dict(kwargs))
        return browser

    result = _run_with_runner(bridge, observation, runner)

    assert result["status"] == STATUS_HOST_OBSERVED
    assert result["browser_preflight_runner_invocation_count"] == 1
    assert calls == [{"auto_open": True, "reconnect_once": True}]


def _run_with_runner(bridge: dict, observation: dict, runner) -> dict:
    return consume_current_host_readiness_observation(
        bridge,
        observation,
        enabled=True,
        now_utc="2026-10-17T00:30:00Z",
        preflight_runner=runner,
    )


def test_stale_observation_is_explicitly_rejected():
    bridge, matrix = _inputs()
    observation = deepcopy(matrix["observations"]["healthy"])
    observation["observed_at_utc"] = "2026-10-15T00:00:00Z"

    result = _run(bridge, observation)

    assert result["status"] == STATUS_FAIL_CLOSED
    assert result["evidence_taxonomy"]["observation_freshness"] == "STALE"
    assert "observation_stale" in result["validation_blockers"]


def test_public_proof_or_runtime_proof_claim_is_not_created_by_observer():
    bridge, matrix = _inputs()
    public = deepcopy(matrix["observations"]["healthy"])
    public["publicly_proven"] = True
    public_result = _run(bridge, public)

    runtime = deepcopy(matrix["observations"]["healthy"])
    runtime["runtime_proven"] = True
    runtime_result = _run(bridge, runtime)

    assert public_result["status"] == STATUS_FAIL_CLOSED
    assert "public_proof_or_authority_cannot_be_created_by_observer" in public_result["validation_blockers"]
    assert runtime_result["status"] == STATUS_FAIL_CLOSED
    assert "runtime_proven_flag_without_read_only_runtime_evidence" in runtime_result["validation_blockers"]
    assert public_result["publicly_proven"] is False
    assert runtime_result["publicly_proven"] is False
