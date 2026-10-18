from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.multi_window_newsroom_cycle_consumer_v2 import (
    MAIN_ARTIFACT_BYTES,
    MAIN_ARTIFACT_PATH,
    MAIN_ARTIFACT_SHA256,
    MAIN_BUNDLE_SHA256,
    MAIN_CYCLE_ID,
    RECEIPT_SCHEMA_VERSION,
    consume_multi_window_bundle_v2,
    receipt_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
MAIN_FIXTURE = ROOT / MAIN_ARTIFACT_PATH
CASES = ROOT / "tests" / "fixtures" / "multi_window_newsroom_cycle_v2_cases_v1.json"
RECEIPTS = ROOT / "tests" / "fixtures" / "multi_window_newsroom_cycle_v2_receipts_v1.json"


def _actual() -> dict:
    return json.loads(MAIN_FIXTURE.read_text(encoding="utf-8"))


def _components(unknown_write: bool = False, interrupted: bool = False) -> dict:
    packages = [
        {
            "destination": destination,
            "status": "UNKNOWN_WRITE" if unknown_write and index == 0 else "SHADOW_READY",
            "payload_sha256": f"{index + 1:064x}",
            "public_write_performed": False,
            **({"unknown_write": True} if unknown_write and index == 0 else {}),
        }
        for index, destination in enumerate(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    ]
    return {
        "source_recovery": {"status": "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS", "http_first": True, "shared_request_budget": True, "browser_rendered_recovery_attempt_count": 1},
        "browser_preflight": {"status": "PASS", "read_only": True},
        "x_ingestion": {"status": "INGESTION_ONLY_READY", "cdp_port": 9222, "ingestion_only": True},
        "grounded_evidence": {"status": "GROUNDED_EVIDENCE_READY", "evidence_ids": ["replay-a"], "claim_bindings_sha256": "a" * 64},
        "candidate_decision": {"status": "SELECTED", "candidate_id": "replay-a"},
        "canonical_article": {"status": "QUALIFIED", "article_id": "article-replay-a", "payload_sha256": "b" * 64, "epistemic_state": "UNCONFIRMED", "public_write_performed": False},
        "derivative_packages": packages,
        "destination_readback": {"status": "UNKNOWN_WRITE" if unknown_write else "CONFIRMED_SHADOW", "public_write_performed": False, **({"unknown_write": True} if unknown_write else {})},
        "recovery_state": {"production_day_id": "2026-10-18", "interrupted": interrupted, **({"resume_status": "RESUMABLE", "semantic_rerun_forbidden": True} if interrupted else {})},
    }


def _healthy() -> dict:
    bundle = deepcopy(_actual())
    bundle["cycle_id"] = MAIN_CYCLE_ID
    bundle["parent_reconciliation"]["classification"] = "SHADOW_CONFIRMED"
    bundle["drift_summary"] = {"classification": "NONE", "counts": {"core_admitted": 1, "quarantined": 0}, "exact_blocker": None, "exact_next_action": "RETAIN_SHADOW_RECEIPT", "quality_state": "HEALTHY_SHADOW", "reasons": []}
    bundle["editorial_projection"]["shadow_components"] = _components()
    bundle["editorial_projection"]["projection_sha256"] = hashlib.sha256(json.dumps({k: v for k, v in bundle["editorial_projection"].items() if k != "projection_sha256"}, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    bundle["bundle_sha256"] = None
    bundle["bundle_sha256"] = hashlib.sha256(json.dumps({k: v for k, v in bundle.items() if k != "bundle_sha256"}, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return bundle


def _rehash_projection(bundle: dict, projection: str) -> None:
    value = bundle[projection]
    value["projection_sha256"] = hashlib.sha256(json.dumps({k: v for k, v in value.items() if k != "projection_sha256"}, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _case(name: str) -> dict:
    if name == "current_real":
        return _actual()
    if name == "healthy":
        return _healthy()
    bundle = _healthy()
    if name == "stale":
        bundle["windows"][1]["records"][0]["freshness"]["state"] = "STALE"
        bundle["windows"][1]["window_sha256"] = hashlib.sha256(json.dumps({k: v for k, v in bundle["windows"][1].items() if k != "window_sha256"}, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    elif name == "future":
        bundle["windows"][1]["records"][0]["pit_state"] = "PIT_INVALID_FUTURE_KNOWN_AT"
        bundle["windows"][1]["window_sha256"] = hashlib.sha256(json.dumps({k: v for k, v in bundle["windows"][1].items() if k != "window_sha256"}, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    elif name == "source_head_mismatch":
        bundle["parent_reconciliation"]["source"]["main_input_head"] = "0" * 40
    elif name == "bundle_hash_mismatch":
        bundle["bundle_sha256"] = "0" * 64
        return bundle
    elif name == "tampered":
        bundle["windows"][1]["records"][0]["claim_id"] = "tampered"
    elif name == "authority_flag":
        bundle["authority_flags"]["network_call_performed"] = True
    elif name == "unknown_write":
        bundle["windows"][1]["records"][0]["raw_lineage"]["status"] = "UNKNOWN_WRITE"
    elif name == "interruption_resume":
        bundle["editorial_projection"]["shadow_components"] = _components(interrupted=True)
        _rehash_projection(bundle, "editorial_projection")
    else:
        raise AssertionError(name)
    bundle["bundle_sha256"] = None
    bundle["bundle_sha256"] = hashlib.sha256(json.dumps({k: v for k, v in bundle.items() if k != "bundle_sha256"}, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return bundle


def test_exact_main_artifact_file_and_bundle_hash_are_bound():
    raw = MAIN_FIXTURE.read_bytes()
    assert len(raw) == MAIN_ARTIFACT_BYTES
    assert hashlib.sha256(raw).hexdigest() == MAIN_ARTIFACT_SHA256
    bundle = _actual()
    assert bundle["bundle_sha256"] == MAIN_BUNDLE_SHA256
    result = consume_multi_window_bundle_v2(bundle, artifact_bytes=raw)
    assert result["artifact"]["status"] == "SEALED_MATCH"
    assert result["cycle_id"] == MAIN_CYCLE_ID
    assert result["classification"] == "NOT_VERIFIED"


def test_healthy_bundle_reaches_shadow_confirmed_only():
    calls: list[dict] = []

    def runner(**kwargs):
        calls.append(dict(kwargs))
        from live_contentops.scheduled_shadow_production_day_v1 import run_scheduled_shadow_production_day

        return run_scheduled_shadow_production_day(**kwargs)

    result = consume_multi_window_bundle_v2(_healthy(), shadow_runner=runner)
    assert result["classification"] == "SHADOW_CONFIRMED"
    assert result["status"] == "SHADOW_CONFIRMED"
    assert len(calls) == 1
    assert result["derivative_shadow"]["count"] == 8
    assert result["proof_axes"]["runtime_proven"] is False
    assert result["proof_axes"]["publicly_proven"] is False


def test_current_real_preserves_host_facts_and_abstains():
    result = consume_multi_window_bundle_v2(_actual(), artifact_bytes=MAIN_FIXTURE.read_bytes())
    assert result["classification"] == "NOT_VERIFIED"
    assert result["article_decision"]["status"] == "ABSTAINED"
    assert result["host_facts"]["current_real"]["scheduler_tasks"] == "Disabled"
    assert result["host_facts"]["current_real"]["store"]["integrity_check"] == "ok"
    assert result["host_facts"]["current_real"]["runtime_proven"] is False
    assert result["host_facts"]["current_real"]["publicly_proven"] is False


def test_window_lineage_policy_and_quarantine_are_preserved():
    result = consume_multi_window_bundle_v2(_actual())
    replay = next(row for row in result["windows"] if row["window_id"] == "RECENT_REPLAY")
    proxy = next(row for row in result["windows"] if row["window_id"] == "PROXY_CONTEXT")
    assert replay["dedupe"]["duplicate_group_count"] == 1
    assert replay["contradiction_quarantine"][0]["reason"] == "CONTRADICTORY_CLAIMS"
    assert proxy["records"][0]["exact_proxy_context"]["state"] == "PROXY"
    assert result["policy_matrix"]["PROXY_CONTEXT"]["core"] == "NEVER"
    assert result["contradiction_quarantine"]


def test_fail_closed_matrix():
    expected = {
        "stale": "STALE",
        "future": "STALE",
        "source_head_mismatch": "SOURCE_HEAD_MISMATCH",
        "bundle_hash_mismatch": "PACKET_HASH_MISMATCH",
        "tampered": "PACKET_HASH_MISMATCH",
        "authority_flag": "AUTHORITY_FLAG",
        "unknown_write": "UNKNOWN_WRITE",
    }
    for name, classification in expected.items():
        result = consume_multi_window_bundle_v2(_case(name))
        assert result["classification"] == classification
        assert result["status"] == "BLOCKED"


def test_interruption_resume_and_receipt_hash_are_deterministic():
    result = consume_multi_window_bundle_v2(_case("interruption_resume"))
    assert result["classification"] == "SHADOW_CONFIRMED"
    assert result["interruption_resume"] == "RESUMABLE_WITHOUT_SEMANTIC_RERUN"
    assert result["receipt_sha256"] == receipt_sha256(result)


def test_case_and_receipt_fixtures_round_trip_exactly():
    fixture = json.loads(CASES.read_text(encoding="utf-8"))
    receipts = json.loads(RECEIPTS.read_text(encoding="utf-8"))
    assert receipts["receipt_schema"] == RECEIPT_SCHEMA_VERSION
    for name, bundle in fixture["cases"].items():
        artifact = MAIN_FIXTURE.read_bytes() if name == "current_real" else None
        actual = consume_multi_window_bundle_v2(bundle, artifact_bytes=artifact)
        assert actual == receipts["cases"][name]
        assert actual["receipt_sha256"] == receipt_sha256(actual)


def test_secret_marker_and_rights_fail_closed_without_leaking_value():
    bundle = _healthy()
    bundle["core_projection"]["api_key"] = "Bearer do-not-export-this-value"
    _rehash_projection(bundle, "core_projection")
    bundle["bundle_sha256"] = None
    bundle["bundle_sha256"] = hashlib.sha256(json.dumps({k: v for k, v in bundle.items() if k != "bundle_sha256"}, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result = consume_multi_window_bundle_v2(bundle)
    assert result["classification"] == "NOT_VERIFIED"
    assert "do-not-export-this-value" not in json.dumps(result)
