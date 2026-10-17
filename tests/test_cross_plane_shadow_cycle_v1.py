from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from live_contentops.scheduled_shadow_production_day_v1 import (
    CROSS_PLANE_CANONICALIZATION,
    CROSS_PLANE_INPUT_SCHEMA,
    cross_plane_input_sha256,
    reconcile_cross_plane_shadow_cycle,
    run_scheduled_shadow_production_day,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "cross_plane_shadow_cycle_inputs_v1.json"
RECEIPT_FIXTURE = ROOT / "tests" / "fixtures" / "cross_plane_shadow_cycle_receipts_v1.json"


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _case(name: str) -> dict:
    return deepcopy(_fixture()["cases"][name])


def _rehash(value: dict) -> dict:
    value["input_sha256"] = None
    value["input_sha256"] = cross_plane_input_sha256(value)
    return value


def test_main_contract_fixture_is_byte_stable_and_self_verifying():
    fixture = _fixture()

    assert fixture["producer_contract"] == CROSS_PLANE_INPUT_SCHEMA
    assert fixture["canonicalization"] == CROSS_PLANE_CANONICALIZATION
    for value in fixture["cases"].values():
        assert value["schema_version"] == CROSS_PLANE_INPUT_SCHEMA
        assert value["canonicalization"] == CROSS_PLANE_CANONICALIZATION
        assert value["input_sha256"] == cross_plane_input_sha256(value)


def test_receipt_fixture_is_byte_stable_and_reproducible_from_each_input():
    fixture = _fixture()
    receipts = json.loads(RECEIPT_FIXTURE.read_text(encoding="utf-8"))

    for name, value in fixture["cases"].items():
        actual = reconcile_cross_plane_shadow_cycle(value)
        expected = receipts["cases"][name]
        assert actual == expected
        assert actual["receipt_sha256"]
        assert actual["schema_version"] == "contentops.cross_plane_shadow_cycle_receipt.v1"


def test_healthy_input_reconciles_one_shadow_cycle_through_injected_existing_owner():
    calls: list[dict] = []

    def runner(**kwargs):
        calls.append(dict(kwargs))
        return run_scheduled_shadow_production_day(**kwargs)

    result = reconcile_cross_plane_shadow_cycle(_case("healthy"), shadow_runner=runner)

    assert result["classification"] == "NONE"
    assert result["status"] == "RECONCILED"
    assert len(calls) == 1
    assert calls[0]["enabled"] is True
    assert result["production_day_receipt_sha256"]
    assert result["runtime_proven"] is False
    assert result["publicly_proven"] is False
    assert result["zero_effect"]["database_mutation"] is False
    assert result["zero_effect"]["public_write_performed"] is False
    assert result["next"] == "RECONCILED_SHADOW_ONLY_NO_RUNTIME_OR_PUBLIC_PROMOTION"


def test_current_real_preserves_read_only_host_facts_and_does_not_admit_cycle():
    calls: list[dict] = []

    result = reconcile_cross_plane_shadow_cycle(
        _case("current_real"),
        shadow_runner=lambda **kwargs: calls.append(kwargs),
    )

    assert result["classification"] == "NOT_VERIFIED"
    assert result["status"] == "BLOCKED"
    assert calls == []
    assert result["current_facts"]["identity_status"] == "MISSING"
    assert result["current_facts"]["destination_status"] == "MISSING"
    assert result["current_facts"]["store"]["integrity_check"] == "ok"
    assert result["current_facts"]["zero_effect"]["public_write_performed"] is False


def test_finite_blocker_classifications_fail_closed():
    expected = {
        "stale": "RECEIPT_STALE",
        "mismatch": "SOURCE_HEAD_MISMATCH",
        "ambiguous": "AMBIGUOUS",
        "tampered": "NOT_VERIFIED",
        "unknown_write": "UNKNOWN_WRITE",
    }

    for name, classification in expected.items():
        result = reconcile_cross_plane_shadow_cycle(_case(name))
        assert result["classification"] == classification
        assert result["status"] == "BLOCKED"
        assert result["production_day_receipt_sha256"] is None


def test_input_hash_tamper_is_not_verified_before_shadow_call():
    value = _case("healthy")
    value["authority_flags"]["main_authority"] = True
    result = reconcile_cross_plane_shadow_cycle(value)

    assert result["classification"] == "NOT_VERIFIED"
    assert "cross_plane_input_hash_invalid" in result["blocker"]
    assert result["production_day_receipt_sha256"] is None


def test_packet_proof_task_and_authority_mismatches_are_distinct():
    packet = _case("healthy")
    packet["main_packet"]["logical_hash"] = "f" * 64
    packet = _rehash(packet)
    assert reconcile_cross_plane_shadow_cycle(packet)["classification"] == "PACKET_HASH_MISMATCH"

    proof = _case("healthy")
    proof["bindings"]["proof_layers"]["HOST_OBSERVED"] = "NOT_VERIFIED"
    proof = _rehash(proof)
    assert reconcile_cross_plane_shadow_cycle(proof)["classification"] == "PROOF_LAYER_MISMATCH"

    tasks = _case("healthy")
    tasks["current_facts"]["task_states"][0]["state_text"] = "Enabled"
    tasks = _rehash(tasks)
    assert reconcile_cross_plane_shadow_cycle(tasks)["classification"] == "TASK_STATE_MISMATCH"

    authority = _case("healthy")
    authority["authority_flags"]["provider_call"] = True
    authority = _rehash(authority)
    assert reconcile_cross_plane_shadow_cycle(authority)["classification"] == "AUTHORITY_FLAG"

    missing_flag = _case("healthy")
    del missing_flag["authority_flags"]["external_effect"]
    missing_flag = _rehash(missing_flag)
    assert reconcile_cross_plane_shadow_cycle(missing_flag)["classification"] == "AUTHORITY_FLAG"


def test_tampered_embedded_portable_receipt_is_not_copied_into_output():
    value = _case("healthy")
    value["portable_receipt"]["classification"] = "NOT_VERIFIED"
    value = _rehash(value)

    result = reconcile_cross_plane_shadow_cycle(value)

    assert result["classification"] == "NOT_VERIFIED"
    assert "portable:portable_receipt_hash_invalid" in result["blocker"]
    assert result["source"]["contentops_head"] is None
    assert result["current_facts"]["task_states"] == []


def test_unknown_write_stops_before_existing_shadow_owner():
    calls: list[dict] = []
    result = reconcile_cross_plane_shadow_cycle(
        _case("unknown_write"),
        shadow_runner=lambda **kwargs: calls.append(kwargs),
    )

    assert result["classification"] == "UNKNOWN_WRITE"
    assert "unknown_write_stop_retry_readback_reconcile" in result["blocker"]
    assert calls == []
