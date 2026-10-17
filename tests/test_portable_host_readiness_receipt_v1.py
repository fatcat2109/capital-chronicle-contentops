from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from live_contentops.host_readiness_observation_consumer_v1 import (
    PORTABLE_PROOF_LAYERS,
    PORTABLE_SCHEMA_VERSION,
    export_portable_host_readiness_receipt,
    portable_receipt_sha256,
    validate_portable_host_readiness_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "portable_host_readiness_receipts_v1.json"


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_round_trip_is_portable_without_contentops_imports():
    fixture = _fixture()
    cases = fixture["cases"]

    assert fixture["schema_version"] == "contentops.portable_host_readiness_receipt_fixture_set.v1"
    for name in ("current_real", "healthy", "unavailable", "ambiguous", "stale"):
        receipt = cases[name]
        assert receipt["schema_version"] == PORTABLE_SCHEMA_VERSION
        assert validate_portable_host_readiness_receipt(receipt) == []
        assert receipt["source"]["repository"] == "fatcat2109/capital-chronicle-contentops"
        assert receipt["source"]["head"] == fixture["source_head"]
        assert receipt["rights"]["raw_payload_included"] is False
        assert set(receipt["proof_layers"]) == set(PORTABLE_PROOF_LAYERS)

    assert cases["healthy"]["classification"] == "HOST_OBSERVED"
    assert cases["unavailable"]["classification"] == "NOT_VERIFIED"
    assert cases["ambiguous"]["classification"] == "AMBIGUOUS"
    assert cases["stale"]["classification"] == "STALE"


def test_current_real_receipt_preserves_the_goal4_observation_without_synthesizing_health():
    receipt = _fixture()["cases"]["current_real"]
    source = receipt["observation"]["source"]

    assert receipt["classification"] == "NOT_VERIFIED"
    assert source["browseros"]["status"] == "PASS"
    assert source["browseros"]["endpoint"] == "http://127.0.0.1:9010/mcp"
    assert source["browseros"]["server_name"] == "browseros-neo"
    assert source["browseros"]["mcp_protocol_version"] == "2025-06-18"
    assert source["browseros"]["allowed_tools"] == ["name_session", "read", "tabs"]
    assert source["x_ingestion_cdp"]["status"] == "UNAVAILABLE"
    assert source["publication_cdp"]["status"] == "UNAVAILABLE"
    assert all(row["state_text"] == "Disabled" for row in source["scheduler_tasks"]["tasks"])
    assert source["identity_shadow"]["status"] == "MISSING"
    assert source["destination_shadow"]["status"] == "MISSING"
    assert source["store"]["integrity_check"] == "ok"
    assert source["store"]["foreign_key_violation_count"] == 0
    assert source["counters"]["durable_store_write_count"] == 0
    assert source["public_write_performed"] is False
    assert source["runtime_proven"] is False
    assert source["publicly_proven"] is False


def test_portable_hash_is_deterministic_and_self_verifying():
    receipt = _fixture()["cases"]["healthy"]
    first = portable_receipt_sha256(receipt)
    second = portable_receipt_sha256(json.loads(json.dumps(receipt)))

    assert first == second == receipt["portable_receipt_sha256"]
    assert validate_portable_host_readiness_receipt(receipt) == []


def test_stdlib_foreign_consumer_can_validate_without_contentops_imports():
    receipt = _fixture()["cases"]["current_real"]
    body = {key: value for key, value in receipt.items() if key != "portable_receipt_sha256"}
    canonical = json.dumps(
        body,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

    assert sha256(canonical).hexdigest() == receipt["portable_receipt_sha256"]
    assert receipt["schema_version"] == "contentops.portable_host_readiness_receipt.v1"
    assert receipt["source"]["source_receipt_hash_verified"] is True
    assert receipt["rights"]["raw_payload_included"] is False


def test_tampered_wire_receipt_is_rejected_by_foreign_validator():
    tampered = _fixture()["cases"]["tampered"]

    blockers = validate_portable_host_readiness_receipt(tampered)

    assert "portable_receipt_hash_invalid" in blockers


def test_source_receipt_tamper_exports_blocked_without_copying_untrusted_payload():
    source = deepcopy(_fixture()["cases"]["healthy"]["observation"]["source"])
    source["status"] = "TAMPERED"
    source["readiness_receipt_sha256"] = "f" * 64
    result = export_portable_host_readiness_receipt(
        source,
        source_repository="fatcat2109/capital-chronicle-contentops",
        source_branch="master",
        source_head=_fixture()["source_head"],
        known_at_utc="2026-10-17T00:00:00Z",
        as_of_utc="2026-10-17T00:00:00Z",
    )

    assert result["export_status"] == "BLOCKED"
    assert "source_readiness_receipt_hash_invalid" in result["validation_blockers"]
    assert result["observation"].get("source") is None
    assert "TAMPERED" not in json.dumps(result)


def test_secret_material_is_rejected_and_never_exported():
    source = deepcopy(_fixture()["cases"]["healthy"]["observation"]["source"])
    source["readiness_receipt_sha256"] = "0" * 64
    source["browseros"]["authorization"] = "Bearer do-not-export-this-value"
    result = export_portable_host_readiness_receipt(
        source,
        source_repository="fatcat2109/capital-chronicle-contentops",
        source_branch="master",
        source_head=_fixture()["source_head"],
        known_at_utc="2026-10-17T00:00:00Z",
        as_of_utc="2026-10-17T00:00:00Z",
    )

    assert result["export_status"] == "BLOCKED"
    assert "secret_material_rejected_from_portable_export" in result["validation_blockers"]
    assert result["redaction"]["secret_material_detected"] is True
    assert "do-not-export-this-value" not in json.dumps(result)


def test_proof_layer_values_are_explicit_and_do_not_promote_public_readiness():
    for name, expected in (
        ("healthy", "HOST_OBSERVED"),
        ("unavailable", "NOT_VERIFIED"),
        ("ambiguous", "AMBIGUOUS"),
        ("stale", "STALE"),
    ):
        receipt = _fixture()["cases"][name]
        assert receipt["classification"] == expected
        assert receipt["proof_layers"]["PUBLICLY_PROVEN"] == "NOT_VERIFIED"

