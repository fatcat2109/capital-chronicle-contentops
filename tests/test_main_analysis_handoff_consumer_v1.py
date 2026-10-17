from __future__ import annotations

import json
from pathlib import Path

from live_contentops.main_analysis_handoff_consumer_v1 import (
    STATUS_DISABLED_BY_DEFAULT,
    STATUS_FAIL_CLOSED,
    STATUS_REJECTED,
    STATUS_SHADOW_REVIEW_READY,
    consume_main_analysis_handoff_shadow,
)
from live_contentops.universal_governed_registry_v1 import logical_hash


FIXTURE = Path(__file__).parent / "fixtures" / "main_analysis_handoff_bridge_v1.json"


def _bridge() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _run(bridge: dict) -> dict:
    return consume_main_analysis_handoff_shadow(
        bridge,
        enabled=True,
        now_utc="2026-10-17T00:00:00Z",
    )


def test_mixed_main_handoff_round_trip_reaches_review_and_scheduled_shadow():
    bridge = _bridge()
    result = _run(bridge)

    assert result["status"] == STATUS_SHADOW_REVIEW_READY
    assert result["validation_blockers"] == []
    assert result["frozen_v2_projection_preserved"] is True
    assert result["analytical_substance_preserved"] is True
    assert result["proxy_rows_qualitative_only"] is True
    assert result["core_claims_attributable"] is True
    assert result["exact_core_claim_ids"] == ["core-claim-001"]
    assert result["proxy_context_claim_ids"] == [
        "proxy-browseros-001",
        "proxy-x-001",
    ]
    assert result["quarantined_claim_ids"] == [
        "proxy-browseros-001",
        "proxy-x-001",
    ]
    assert result["newsroom_lane"]["outcome"] == "SELECTED"
    assert result["capital_chronicle_lane"]["authorized_claim_ids"] == ["core-claim-001"]
    assert result["editorial_review"]["result"] == "PASS"
    assert result["scheduled_shadow"]["status"] == "SHADOW_CONFIRMED"
    assert result["scheduled_shadow"]["derivative_destination_count"] == 8
    assert result["zero_live_action"] == {
        "scheduler_started": False,
        "durable_store_write_count": 0,
        "database_mutation": False,
        "model_call_count": 0,
        "provider_call_count": 0,
        "browser_action_count": 0,
        "public_write_performed": False,
        "publication_authority": False,
        "v2_activation": False,
    }
    assert len(result["receipt_sha256"]) == 64


def test_consumer_is_disabled_by_default_and_does_not_execute_shadow_owners():
    result = consume_main_analysis_handoff_shadow(_bridge())

    assert result["status"] == STATUS_DISABLED_BY_DEFAULT
    assert result["scheduler_started"] is False
    assert result["durable_store_write_count"] == 0
    assert result["model_call_count"] == 0
    assert result["public_write_performed"] is False
    assert len(result["receipt_sha256"]) == 64


def test_packet_hash_tamper_is_rejected_before_v3_build():
    bridge = _bridge()
    bridge["claims"][0]["statement"] = "Tampered Main claim."

    result = _run(bridge)

    assert result["status"] == STATUS_REJECTED
    assert "main_packet_logical_hash_mismatch" in result["validation_blockers"]
    assert result["v3_packet_logical_hash"] is None


def test_future_pit_and_stale_freshness_are_rejected():
    future = _bridge()
    future["clocks"]["pit_cutoff_utc"] = "2026-10-18T00:00:00Z"
    future["packet_logical_hash"] = logical_hash(
        {key: value for key, value in future.items() if key not in {"packet_logical_hash", "packet_identity_sha256"}}
    )
    future_result = _run(future)

    stale = _bridge()
    stale["freshness"]["status"] = "STALE"
    stale["packet_logical_hash"] = logical_hash(
        {key: value for key, value in stale.items() if key not in {"packet_logical_hash", "packet_identity_sha256"}}
    )
    stale_result = _run(stale)

    assert future_result["status"] == STATUS_REJECTED
    assert "pit_cutoff_in_future" in future_result["validation_blockers"]
    assert stale_result["status"] == STATUS_REJECTED
    assert "freshness_not_fresh" in stale_result["validation_blockers"]


def test_rights_invalid_and_authority_inconsistent_inputs_fail_closed():
    rights = _bridge()
    rights["evidence_documents"][0]["rights_status"] = "RESTRICTED"
    rights["packet_logical_hash"] = logical_hash(
        {key: value for key, value in rights.items() if key not in {"packet_logical_hash", "packet_identity_sha256"}}
    )
    rights_result = _run(rights)

    authority = _bridge()
    authority["authority_boundary"]["contentops_numeric_authority"] = True
    authority["packet_logical_hash"] = logical_hash(
        {key: value for key, value in authority.items() if key not in {"packet_logical_hash", "packet_identity_sha256"}}
    )
    authority_result = _run(authority)

    assert rights_result["status"] == STATUS_REJECTED
    assert any("evidence_document_rights_invalid" in value for value in rights_result["validation_blockers"])
    assert authority_result["status"] == STATUS_REJECTED
    assert "authority_flag_not_false:contentops_numeric_authority" in authority_result["validation_blockers"]


def test_proxy_promotion_and_v2_projection_tamper_are_rejected():
    promoted = _bridge()
    promoted["claims"][1]["permission_state"] = "PUBLIC_CLAIM_ALLOWED"
    promoted["packet_logical_hash"] = logical_hash(
        {key: value for key, value in promoted.items() if key not in {"packet_logical_hash", "packet_identity_sha256"}}
    )
    promoted_result = _run(promoted)

    v2_tampered = _bridge()
    v2_tampered["v2_compatibility_projection"]["packet_id"] = "tampered-packet"
    v2_tampered["packet_logical_hash"] = logical_hash(
        {key: value for key, value in v2_tampered.items() if key not in {"packet_logical_hash", "packet_identity_sha256"}}
    )
    v2_result = _run(v2_tampered)

    assert promoted_result["status"] == STATUS_REJECTED
    assert any("proxy_claim_permission_not_context_only" in value for value in promoted_result["validation_blockers"])
    assert v2_result["status"] == STATUS_REJECTED
    assert "v2_projection_hash_invalid" in v2_result["validation_blockers"]


def test_interrupted_recovery_and_lineage_receipts_are_retained():
    result = _run(_bridge())

    assert result["scheduled_shadow"]["interruption_recovery"] == "RESUMABLE_WITHOUT_SEMANTIC_RERUN"
    assert result["claim_lineage_sha256"]
    assert result["scheduled_shadow"]["destination_readback_sha256"]


def test_scheduled_shadow_failure_remains_fail_closed_when_host_boundary_is_not_pass():
    bridge = _bridge()
    bridge["browser_preflight"]["status"] = "BROWSER_UNAVAILABLE"
    bridge["packet_logical_hash"] = logical_hash(
        {key: value for key, value in bridge.items() if key not in {"packet_logical_hash", "packet_identity_sha256"}}
    )

    result = _run(bridge)

    assert result["status"] == STATUS_FAIL_CLOSED
    assert result["validation_blockers"] == [
        "scheduled_shadow:FAIL_CLOSED:browser_preflight_not_pass"
    ]
