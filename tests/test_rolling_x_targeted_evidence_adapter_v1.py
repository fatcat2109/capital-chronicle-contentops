from __future__ import annotations

from copy import deepcopy

from live_contentops.newsroom_assignment_scheduler_v1 import _logical_hash
from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
    RollingXTargetedEvidenceAdapter,
)
from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
)

AS_OF = "2026-08-08T12:00:00Z"


def _request(
    *,
    cluster_id="cluster-1",
    headline_ids=None,
    story_type="market_move",
    required=None,
    families=None,
):
    registry = load_source_capability_registry()
    row = registry["story_types"][story_type]
    request = {
        "schema_version": "capital_chronicle.rolling_x_story_evidence_request.v1",
        "cluster_id": cluster_id,
        "rank": 1,
        "headline_ids": headline_ids or ["headline-1"],
        "story_type": story_type,
        "article_mode": row.get("article_mode") or "straight_news",
        "needed_evidence": ["official record"],
        "required_evidence_capabilities": list(
            required or row["required_evidence_capabilities"]
        ),
        "source_adapter_families": list(
            families or row["source_adapter_families"]
        ),
        "freshness_policy": row["freshness_policy"],
        "market_sensitive": bool(row.get("market_context_required")),
        "market_snapshot_required": bool(row.get("market_context_required")),
        "capital_chronicle_numeric_or_analytical_authority_required": bool(
            row.get("market_context_required")
        ),
        "x_content_is_discovery_and_ranking_only": True,
    }
    request["request_logical_hash"] = _logical_hash(request)
    return request


def _packet(request, *, prior=True):
    claim = {
        "claim_id": "claim-1",
        "metric": "official market metric",
        "value": 100.0,
        "unit": "index",
        "observation_time_utc": "2026-08-08T11:00:00Z",
        "known_at_utc": "2026-08-08T11:05:00Z",
        "source_id": "governed-source",
        "source_artifact_ref": "packet#numeric_claims/0",
        "public_claim_allowed": True,
        "llm_numeric_authority": False,
    }
    if prior:
        claim["prior_value"] = 99.0
    return {
        "schema_version": "capital_chronicle_content_evidence_packet.v2",
        "packet_id": "packet-1",
        "status": "PASS_PUBLICATION_AUTHORIZED",
        "generated_at_utc": "2026-08-08T11:05:00Z",
        "as_of_utc": AS_OF,
        "story_window": {"hours": 24},
        "rolling_x_story_binding": {
            "cluster_id": request["cluster_id"],
            "headline_ids": list(request["headline_ids"]),
            "request_logical_hash": request["request_logical_hash"],
        },
        "provided_evidence_capabilities": list(
            request["required_evidence_capabilities"]
        ),
        "events": [{"event_time_utc": "2026-08-08T10:30:00Z"}],
        "headlines": [{"published_at_utc": "2026-08-08T10:30:00Z"}],
        "official_source_documents": [
            {
                "document_id": "document-1",
                "title": "Official release",
                "publisher": "Official Agency",
                "source_authority_class": "official_public_primary_source",
                "source_url": "https://official.example/release",
                "published_at_utc": "2026-08-08T10:30:00Z",
                "raw_sha256": "a" * 64,
                "public_claim_allowed": True,
            }
        ],
        "numeric_claims": [claim],
        "market_snapshots": [
            {
                "snapshot_id": "snapshot-1",
                "generated_at_utc": "2026-08-08T11:05:00Z",
                "observation_time_utc": "2026-08-08T11:00:00Z",
                "claim_ids": ["claim-1"],
            }
        ],
        "source_state": {"reporting_allowed": True},
        "candidate_visual_inputs": [],
        "citation_map": {"claim-1": ["packet#numeric_claims/0"]},
        "provenance": {
            "retrieved_at_utc": "2026-08-08T11:05:00Z",
            "raw_sha256": "b" * 64,
        },
        "public_claim_permissions": {
            "decision": "ALLOW",
            "reporting_allowed": True,
            "numeric_claims_allowed": True,
            "llm_numeric_authority": False,
        },
        "blockers": [],
        "publication_assignment": {"fresh_material_delta": True},
    }


def _adapter(packet):
    return RollingXTargetedEvidenceAdapter(
        packet_loader=lambda _request: packet,
        evaluation_as_of_utc=AS_OF,
    )


def test_valid_exact_governed_market_packet_satisfies_all_declared_capabilities():
    request = _request()
    receipt = _adapter(_packet(request))(request)

    assert receipt["status"] == "PASS"
    assert receipt["provided_evidence_capabilities"] == [
        "catalyst_evidence",
        "current_market_snapshot",
        "prior_close",
    ]
    assert receipt["capital_chronicle_authority_verified"] is True
    assert receipt["publication_authority"] is False
    document = receipt["evidence_documents"][0]
    assert document["cluster_id"] == request["cluster_id"]
    assert document["headline_ids"] == request["headline_ids"]
    assert document["content_sha256"] == "a" * 64


def test_market_prior_close_is_never_synthesized_by_contentops():
    request = _request()
    receipt = _adapter(_packet(request, prior=False))(request)

    assert receipt["status"] == "BLOCKED"
    assert "governed_prior_close_missing" in receipt["blockers"]
    assert "prior_close" not in receipt["provided_evidence_capabilities"]
    assert receipt["capital_chronicle_authority_verified"] is False


def test_x_or_candidate_context_cannot_satisfy_evidence():
    request = _request()
    packet = _packet(request)
    packet["status"] = "PASS_CONTRACT_BLOCKED_PUBLICATION"
    packet["public_claim_permissions"]["decision"] = "BLOCK"
    packet["public_claim_permissions"]["reporting_allowed"] = False
    packet["official_source_documents"][0]["public_claim_allowed"] = False
    packet["numeric_claims"][0]["public_claim_allowed"] = False

    receipt = _adapter(packet)(request)

    assert receipt["status"] == "BLOCKED"
    assert "governed_packet_not_publication_authorized" in receipt["blockers"]
    assert "governed_reporting_permission_not_granted" in receipt["blockers"]
    assert receipt["capital_chronicle_authority_verified"] is False


def test_stale_governed_packet_fails_current_operator_readiness():
    request = _request()
    packet = _packet(request)
    packet["events"][0]["event_time_utc"] = "2026-07-13T00:00:00Z"
    packet["headlines"][0]["published_at_utc"] = "2026-07-13T00:00:00Z"
    packet["official_source_documents"][0]["published_at_utc"] = (
        "2026-07-13T00:00:00Z"
    )
    packet["numeric_claims"][0]["observation_time_utc"] = (
        "2026-07-13T00:00:00Z"
    )
    packet["market_snapshots"][0]["generated_at_utc"] = (
        "2026-07-13T00:00:00Z"
    )

    receipt = _adapter(packet)(request)

    assert receipt["status"] == "BLOCKED"
    assert "market_sensitive_story_snapshot_stale_or_missing" in receipt["blockers"]
    assert "market_sensitive_story_ingest_stale_or_missing" in receipt["blockers"]


def test_exact_cluster_headline_and_request_hash_binding_is_required():
    request = _request()
    for field, value, expected in (
        ("cluster_id", "other", "governed_evidence_cluster_binding_mismatch"),
        ("headline_ids", ["other"], "governed_evidence_headline_binding_mismatch"),
        ("request_logical_hash", "other", "governed_evidence_request_hash_mismatch"),
    ):
        packet = _packet(request)
        packet["rolling_x_story_binding"][field] = value
        receipt = _adapter(packet)(request)
        assert receipt["status"] == "BLOCKED"
        assert expected in receipt["blockers"]


def test_valid_official_primary_packet_can_satisfy_nonnumeric_capability():
    registry = deepcopy(load_source_capability_registry())
    registry["story_types"]["regulatory_fiscal_event"] = {
        "required_evidence_capabilities": ["official_document"],
        "market_context_required": False,
        "article_mode": "straight_news",
        "freshness_policy": "event_24h",
        "source_adapter_families": ["official_regulatory_fiscal"],
    }
    request = _request(
        story_type="regulatory_fiscal_event",
        required=["official_document"],
        families=["official_regulatory_fiscal"],
    )
    request["market_sensitive"] = False
    request["market_snapshot_required"] = False
    request["capital_chronicle_numeric_or_analytical_authority_required"] = False
    request["request_logical_hash"] = _logical_hash(
        {key: value for key, value in request.items() if key != "request_logical_hash"}
    )
    packet = _packet(request)
    packet["provided_evidence_capabilities"] = ["official_document"]
    adapter = RollingXTargetedEvidenceAdapter(
        packet_loader=lambda _request: packet,
        evaluation_as_of_utc=AS_OF,
        capability_registry=registry,
    )

    receipt = adapter(request)

    assert receipt["status"] == "PASS"
    assert receipt["provided_evidence_capabilities"] == ["official_document"]
    assert receipt["capital_chronicle_authority_verified"] is False
