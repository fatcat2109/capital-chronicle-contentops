from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.host_readiness_observation_consumer_v1 import portable_receipt_sha256
from live_contentops.scheduled_shadow_production_day_v1 import (
    POST_MERGE_ARTIFACT_BYTES,
    POST_MERGE_ARTIFACT_COMMIT,
    POST_MERGE_ARTIFACT_PATH,
    POST_MERGE_ARTIFACT_SHA256_PREFIX,
    POST_MERGE_INPUT_SHA256_PREFIX,
    _cross_plane_observed_facts,
    cross_plane_input_sha256,
    cross_plane_receipt_sha256,
    reconcile_post_merge_cross_plane_shadow_cycle_replay,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / POST_MERGE_ARTIFACT_PATH
CASES = ROOT / "tests" / "fixtures" / "cross_plane_shadow_cycle_post_merge_replay_cases_v1.json"
RECEIPTS = ROOT / "tests" / "fixtures" / "cross_plane_shadow_cycle_replay_receipts_v1.json"


def _current() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _components(unknown_write: bool = False) -> dict:
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
        "source_recovery": {
            "status": "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS",
            "http_first": True,
            "shared_request_budget": True,
            "browser_rendered_recovery_attempt_count": 1,
        },
        "browser_preflight": {"status": "PASS", "read_only": True},
        "x_ingestion": {"status": "INGESTION_ONLY_READY", "cdp_port": 9222},
        "grounded_evidence": {
            "status": "GROUNDED_EVIDENCE_READY",
            "evidence_ids": ["source-1"],
            "claim_bindings_sha256": "a" * 64,
        },
        "candidate_decision": {"status": "SELECTED", "candidate_id": "candidate-1"},
        "canonical_article": {
            "status": "QUALIFIED",
            "article_id": "article-1",
            "payload_sha256": "b" * 64,
            "epistemic_state": "UNCONFIRMED",
            "public_write_performed": False,
        },
        "derivative_packages": packages,
        "destination_readback": {
            "status": "UNKNOWN_WRITE" if unknown_write else "CONFIRMED_SHADOW",
            "public_write_performed": False,
            **({"unknown_write": True} if unknown_write else {}),
        },
        "recovery_state": {"production_day_id": "2026-10-17", "interrupted": False},
    }


def _rehash(value: dict) -> dict:
    value["portable_receipt"]["portable_receipt_sha256"] = portable_receipt_sha256(
        value["portable_receipt"]
    )
    value["post_merge_provenance"]["portable_receipt_sha256"] = value["portable_receipt"][
        "portable_receipt_sha256"
    ]
    value["input_sha256"] = None
    value["input_sha256"] = cross_plane_input_sha256(value)
    return value


def _synthetic(name: str) -> dict:
    value = deepcopy(_current())
    portable = value["portable_receipt"]
    source = portable["observation"]["source"]
    if name == "healthy":
        portable["classification"] = "HOST_OBSERVED"
        portable["proof_layers"]["HOST_OBSERVED"] = "HOST_OBSERVED"
        source["host_observed"] = True
        source["identity_shadow"] = {"status": "CONFIRMED"}
        source["destination_shadow"] = {"status": "CONFIRMED_SHADOW"}
        value["shadow_components"] = _components()
    elif name == "stale":
        portable["freshness"].update(
            {
                "as_of_utc": "2026-10-18T14:00:00Z",
                "age_seconds": 90000,
                "status": "STALE",
            }
        )
        value["clock_state"].update(
            {"as_of_utc": "2026-10-18T14:00:00Z", "freshness_status": "STALE"}
        )
    elif name == "mismatch":
        value["post_merge_provenance"]["contentops_merged_head"] = "0" * 40
    elif name == "tampered":
        portable["classification"] = "HOST_OBSERVED"
    elif name == "unknown_write":
        portable["zero_effect"]["public_write_performed"] = True
        value["zero_effect_flags"]["public_write_performed"] = True
    else:
        raise AssertionError(name)
    value.pop("shadow_components", None) if name != "healthy" else None
    if name == "unknown_write":
        value["shadow_components"] = _components(unknown_write=True)
    if name == "tampered":
        value["input_sha256"] = cross_plane_input_sha256(value)
    else:
        value["current_facts"] = _cross_plane_observed_facts(portable)
        value["bindings"]["proof_layers"] = deepcopy(portable["proof_layers"])
        _rehash(value)
    return value


def test_remote_fixture_is_exactly_read_back_and_sealed_mismatch_is_fail_closed():
    raw = FIXTURE.read_bytes()
    assert len(raw) == POST_MERGE_ARTIFACT_BYTES
    assert hashlib.sha256(raw).hexdigest().startswith("4b208104")
    assert not hashlib.sha256(raw).hexdigest().startswith(POST_MERGE_ARTIFACT_SHA256_PREFIX)
    packet = json.loads(raw)
    assert packet["input_sha256"].startswith(POST_MERGE_INPUT_SHA256_PREFIX)
    result = reconcile_post_merge_cross_plane_shadow_cycle_replay(raw)
    assert result["classification"] == "NOT_VERIFIED"
    assert result["status"] == "BLOCKED"
    assert "main_fixture_sha256_prefix_mismatch" in result["blockers"]
    assert result["artifact"]["commit"] == POST_MERGE_ARTIFACT_COMMIT
    assert result["artifact"]["path"] == POST_MERGE_ARTIFACT_PATH
    assert result["current_facts"]["identity_status"] == "MISSING"
    assert result["current_facts"]["destination_status"] == "MISSING"


def test_healthy_synthetic_fixture_reconciles_shadow_only():
    result = reconcile_post_merge_cross_plane_shadow_cycle_replay(
        _synthetic("healthy"), artifact_kind="SYNTHETIC"
    )

    assert result["classification"] == "NONE"
    assert result["status"] == "RECONCILED"
    assert result["production_day_receipt_sha256"]
    assert result["runtime_proven"] is False
    assert result["publicly_proven"] is False
    assert result["next"] == "HAND_REPLAY_RECEIPT_HASH_TO_MAIN_FOR_NEXT_RECONCILIATION"


def test_stale_mismatch_tampered_and_unknown_write_cases_fail_closed():
    expected = {
        "stale": "RECEIPT_STALE",
        "mismatch": "SOURCE_HEAD_MISMATCH",
        "tampered": "PACKET_HASH_MISMATCH",
        "unknown_write": "UNKNOWN_WRITE",
    }
    for name, classification in expected.items():
        result = reconcile_post_merge_cross_plane_shadow_cycle_replay(
            _synthetic(name), artifact_kind="SYNTHETIC"
        )
        assert result["classification"] == classification
        assert result["status"] == "BLOCKED"
        assert result["production_day_receipt_sha256"] is None


def test_future_clock_and_authority_flag_are_rejected():
    future = _synthetic("healthy")
    future["clock_state"]["as_of_utc"] = "2026-10-16T00:00:00Z"
    _rehash(future)
    result = reconcile_post_merge_cross_plane_shadow_cycle_replay(
        future, artifact_kind="SYNTHETIC"
    )
    assert result["classification"] == "RECEIPT_STALE"

    authority = _synthetic("healthy")
    authority["authority_flags"]["network_call"] = True
    _rehash(authority)
    result = reconcile_post_merge_cross_plane_shadow_cycle_replay(
        authority, artifact_kind="SYNTHETIC"
    )
    assert result["classification"] == "AUTHORITY_FLAG"


def test_replay_receipt_hash_is_deterministic_and_fixture_cases_are_round_trippable():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    receipts = json.loads(RECEIPTS.read_text(encoding="utf-8"))
    for name, descriptor in cases["cases"].items():
        result = reconcile_post_merge_cross_plane_shadow_cycle_replay(
            _synthetic(name) if descriptor["kind"] == "SYNTHETIC" else FIXTURE,
            artifact_kind=descriptor["kind"],
        )
        expected = receipts["cases"][name]
        assert result == expected
        assert result["receipt_sha256"] == cross_plane_receipt_sha256(result)
