from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from live_contentops.multi_window_newsroom_cycle_consumer_v1 import (
    RECEIPT_SCHEMA_VERSION,
    SCHEMA_VERSION,
    bundle_sha256,
    consume_multi_window_newsroom_cycle,
    receipt_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
BUNDLES = ROOT / "tests" / "fixtures" / "multi_window_newsroom_cycle_bundles_v1.json"
RECEIPTS = ROOT / "tests" / "fixtures" / "multi_window_newsroom_cycle_receipts_v1.json"


def _bundles() -> dict:
    return json.loads(BUNDLES.read_text(encoding="utf-8"))


def _case(name: str) -> dict:
    return deepcopy(_bundles()["cases"][name])


def _rehash(bundle: dict) -> dict:
    bundle["bundle_sha256"] = None
    bundle["bundle_sha256"] = bundle_sha256(bundle)
    return bundle


def test_bundle_contract_has_exact_three_windows_and_deterministic_hashes():
    fixture = _bundles()

    assert fixture["contract"] == SCHEMA_VERSION
    for name, bundle in fixture["cases"].items():
        assert set(bundle) == {
            "schema",
            "version",
            "cycle_id",
            "generated_at_utc",
            "as_of_utc",
            "parent_reconciliation",
            "windows",
            "core_projection",
            "editorial_projection",
            "drift_summary",
            "authority_flags",
            "bundle_sha256",
        }
        assert bundle["schema"] == SCHEMA_VERSION
        assert tuple(row["window_id"] for row in bundle["windows"]) == (
            "CURRENT_REAL",
            "RECENT_REPLAY",
            "PROXY_CONTEXT",
        )
        if name != "tampered":
            assert bundle["bundle_sha256"] == bundle_sha256(bundle)


def test_current_real_preserves_host_facts_and_stays_not_verified():
    result = consume_multi_window_newsroom_cycle(_case("current_real"))

    assert result["classification"] == "NOT_VERIFIED"
    assert result["status"] == "BLOCKED"
    assert result["current_host_facts"]["browseros"]["status"] == "PASS"
    assert result["current_host_facts"]["x_ingestion_cdp"]["status"] == "UNAVAILABLE"
    assert result["current_host_facts"]["publication_cdp"]["status"] == "UNAVAILABLE"
    assert all(row["state_text"] == "Disabled" for row in result["current_host_facts"]["scheduler_tasks"]["tasks"])
    assert result["current_host_facts"]["identity"]["status"] == "MISSING"
    assert result["current_host_facts"]["destination"]["status"] == "MISSING"
    assert result["current_host_facts"]["store"]["integrity_check"] == "ok"
    assert result["runtime_proven"] is False
    assert result["publicly_proven"] is False


def test_healthy_synthetic_reuses_existing_shadow_owner_and_never_promotes():
    calls: list[dict] = []

    def runner(**kwargs):
        calls.append(dict(kwargs))
        from live_contentops.scheduled_shadow_production_day_v1 import run_scheduled_shadow_production_day

        return run_scheduled_shadow_production_day(**kwargs)

    result = consume_multi_window_newsroom_cycle(_case("healthy"), shadow_runner=runner)

    assert result["classification"] == "SHADOW_CONFIRMED"
    assert result["status"] == "SHADOW_CONFIRMED"
    assert len(calls) == 1
    assert calls[0]["enabled"] is True
    assert result["derivative_hashes"]["count"] == 8
    assert result["runtime_proven"] is False
    assert result["publicly_proven"] is False
    assert result["candidate_selection"]["selected_candidate_id"] == "replay-1"


def test_duplicate_collapse_and_context_are_preserved():
    result = consume_multi_window_newsroom_cycle(_case("duplicate_collapse"))

    assert result["classification"] == "SHADOW_CONFIRMED"
    assert "replay-1-duplicate" in result["abstained_claim_ids"]
    assert "proxy-1" in result["qualitative_context_claim_ids"]
    assert result["window_bindings"][1]["dedupe"][0]["decision"] == "COLLAPSED"


def test_contradiction_and_proxy_only_never_promote_claims():
    contradiction = consume_multi_window_newsroom_cycle(_case("contradiction_quarantine"))
    assert contradiction["classification"] == "NOT_VERIFIED"
    assert contradiction["contradiction_quarantine"][0]["reason"] == "CONTRADICTION_QUARANTINE"
    assert set(contradiction["abstained_claim_ids"]) >= {"replay-1", "replay-2"}

    proxy = consume_multi_window_newsroom_cycle(_case("proxy_only"))
    assert proxy["classification"] == "NOT_VERIFIED"
    assert "proxy-1" in proxy["qualitative_context_claim_ids"]
    assert proxy["article_package"] is None


def test_stale_and_future_windows_fail_closed():
    for name in ("stale", "future"):
        result = consume_multi_window_newsroom_cycle(_case(name))
        assert result["classification"] == "STALE"
        assert result["status"] == "BLOCKED"


def test_tamper_authority_and_unknown_write_are_distinct():
    tampered = consume_multi_window_newsroom_cycle(_case("tampered"))
    assert tampered["classification"] == "PACKET_HASH_MISMATCH"

    authority = consume_multi_window_newsroom_cycle(_case("authority_flag"))
    assert authority["classification"] == "AUTHORITY_FLAG"

    unknown = consume_multi_window_newsroom_cycle(_case("unknown_write"))
    assert unknown["classification"] == "UNKNOWN_WRITE"
    assert unknown["status"] == "BLOCKED"


def test_source_head_and_rights_drift_fail_closed():
    source = _case("healthy")
    source["core_projection"]["source"]["contentops_head"] = "0" * 40
    _rehash(source)
    result = consume_multi_window_newsroom_cycle(source)
    assert result["classification"] == "SOURCE_HEAD_MISMATCH"

    rights = _case("healthy")
    rights["core_projection"]["rights"]["status"] = "PUBLIC_WRITE"
    _rehash(rights)
    result = consume_multi_window_newsroom_cycle(rights)
    assert result["classification"] == "NOT_VERIFIED"
    assert "core_rights_invalid" in result["blockers"]


def test_interruption_resume_is_carried_from_existing_shadow_receipt():
    result = consume_multi_window_newsroom_cycle(_case("interruption_resume"))

    assert result["classification"] == "SHADOW_CONFIRMED"
    assert result["interruption_resume"] == "RESUMABLE_WITHOUT_SEMANTIC_RERUN"


def test_receipt_fixture_round_trip_and_hashes_are_deterministic():
    fixture = _bundles()
    receipts = json.loads(RECEIPTS.read_text(encoding="utf-8"))

    assert receipts["receipt_schema"] == RECEIPT_SCHEMA_VERSION
    for name, bundle in fixture["cases"].items():
        actual = consume_multi_window_newsroom_cycle(bundle)
        expected = receipts["cases"][name]
        assert actual == expected
        assert actual["receipt_sha256"] == receipt_sha256(actual)


def test_secret_marker_blocks_without_exporting_value():
    bundle = _case("healthy")
    bundle["core_projection"]["api_key"] = "Bearer do-not-export-this-value"
    _rehash(bundle)

    result = consume_multi_window_newsroom_cycle(bundle)

    assert result["classification"] == "NOT_VERIFIED"
    assert any("secret_material" in blocker for blocker in result["blockers"])
    assert "do-not-export-this-value" not in json.dumps(result)
