from __future__ import annotations

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)
from live_contentops.scheduled_shadow_production_day_v1 import (
    DISABLED_BY_DEFAULT,
    HUMAN_REQUIRED,
    MISMATCH,
    SHADOW_CONFIRMED,
    UNKNOWN_WRITE,
    run_scheduled_shadow_production_day,
)


def _components():
    packages = [
        {
            "destination": destination,
            "status": "SHADOW_READY",
            "payload_sha256": f"{index + 1:064x}",
            "public_write_performed": False,
        }
        for index, destination in enumerate(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    ]
    return {
        "source_recovery": {
            "status": "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS",
            "http_first": True,
            "shared_request_budget": True,
            "browser_rendered_recovery_attempt_count": 1,
        },
        "browser_preflight": {
            "status": "PASS",
            "lifecycle_state": "HEALTHY_AFTER_RECONNECT",
            "auto_open_requested": True,
            "official_launcher_invoked": True,
            "launcher_attempts": 1,
            "reconnect_attempts": 1,
            "read_only": True,
        },
        "x_ingestion": {
            "status": "INGESTION_ONLY_READY",
            "cdp_port": 9222,
            "ingestion_only": True,
        },
        "grounded_evidence": {
            "status": "GROUNDED_EVIDENCE_READY",
            "evidence_ids": ["source-1", "source-2"],
            "claim_bindings_sha256": "a" * 64,
            "report_truth": "DIRECT_REPUTABLE_REPORT",
        },
        "candidate_decision": {
            "status": "SELECTED",
            "candidate_id": "candidate-1",
            "evidence_ids": ["source-1"],
            "decision_sha256": "b" * 64,
        },
        "canonical_article": {
            "status": "QUALIFIED",
            "article_id": "article-1",
            "payload_sha256": "c" * 64,
            "epistemic_state": "UNCONFIRMED",
            "public_write_performed": False,
        },
        "derivative_packages": packages,
        "destination_readback": {
            "status": "CONFIRMED_SHADOW",
            "platform": "substack",
            "public_write_performed": False,
        },
        "recovery_state": {
            "production_day_id": "2026-10-17",
            "interrupted": False,
        },
    }


def test_complete_scheduled_shadow_cycle_is_reviewable_without_side_effects():
    result = run_scheduled_shadow_production_day(enabled=True, **_components())

    assert result["status"] == SHADOW_CONFIRMED
    assert result["derivative_destination_count"] == 8
    assert result["interruption_recovery"] == "NOT_INTERRUPTED"
    assert result["scheduler_started"] is False
    assert result["durable_store_write_count"] == 0
    assert result["database_mutation"] is False
    assert result["model_call_count"] == 0
    assert result["provider_call_count"] == 0
    assert result["public_write_performed"] is False
    assert len(result["production_day_receipt_sha256"]) == 64
    assert len(result["receipt_sha256"]) == 64


def test_disabled_default_makes_zero_calls_and_returns_immutable_receipt():
    result = run_scheduled_shadow_production_day(enabled=False, **_components())

    assert result["status"] == DISABLED_BY_DEFAULT
    assert result["scheduler_started"] is False
    assert result["durable_store_write_count"] == 0
    assert result["receipt_sha256"]


def test_stale_evidence_and_interrupted_resume_are_fail_closed_or_resumable():
    stale = _components()
    stale["grounded_evidence"]["status"] = "TRUNCATED"
    stale_result = run_scheduled_shadow_production_day(enabled=True, **stale)

    interrupted = _components()
    interrupted["recovery_state"] = {
        "production_day_id": "2026-10-17",
        "interrupted": True,
        "resume_status": "RESUMABLE",
        "semantic_rerun_forbidden": True,
    }
    interrupted_result = run_scheduled_shadow_production_day(enabled=True, **interrupted)

    assert stale_result["status"] == HUMAN_REQUIRED
    assert interrupted_result["status"] == SHADOW_CONFIRMED
    assert interrupted_result["interruption_recovery"] == "RESUMABLE_WITHOUT_SEMANTIC_RERUN"


def test_shadow_invocation_can_use_existing_bounded_preflight_launcher_contract():
    components = _components()
    observed: list[dict] = []
    preflight_result = components["browser_preflight"]

    def preflight_runner(**kwargs):
        observed.append(dict(kwargs))
        return preflight_result

    components.pop("browser_preflight")
    result = run_scheduled_shadow_production_day(
        enabled=True,
        preflight_runner=preflight_runner,
        **components,
    )

    assert result["status"] == SHADOW_CONFIRMED
    assert observed == [{"auto_open": True, "reconnect_once": True}]


def test_unknown_write_stops_before_editorial_or_package_claims():
    unknown = _components()
    unknown["destination_readback"] = {
        "status": UNKNOWN_WRITE,
        "unknown_write": True,
    }
    result = run_scheduled_shadow_production_day(enabled=True, **unknown)

    assert result["status"] == UNKNOWN_WRITE
    assert "stop_retry_readback_reconcile" in result["failure_detail"]
    assert result["public_write_performed"] is False


def test_unknown_write_in_derivative_package_stops_before_reconciliation_claims():
    unknown = _components()
    unknown["derivative_packages"][0] = {
        **unknown["derivative_packages"][0],
        "status": UNKNOWN_WRITE,
        "unknown_write": True,
    }
    result = run_scheduled_shadow_production_day(enabled=True, **unknown)

    assert result["status"] == UNKNOWN_WRITE
    assert "derivative:0" in result["failure_detail"]
    assert "stop_retry_readback_reconcile" in result["failure_detail"]


def test_identity_or_destination_mismatch_never_becomes_shadow_success():
    mismatch = _components()
    mismatch["destination_readback"]["status"] = "MISMATCH"
    result = run_scheduled_shadow_production_day(enabled=True, **mismatch)

    assert result["status"] == MISMATCH
    assert result["production_day_receipt_sha256"] is None
