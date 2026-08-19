"""Run the P0-1 authority/context/source slice with zero external writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops.capital_chronicle_data_catalog_v1 import (
    derive_story_scoped_cc_semantics,
    discover_cc_data_estate,
    query_story_scoped_cc_context,
)
from live_contentops.cc_evidence_bridge_v2 import build_evidence_packet_from_cc_root
from live_contentops.cc_publication_authority_v1 import (
    build_publication_authorized_projection,
    resolve_publication_authority,
    validate_projection_for_consumer,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
)
from live_contentops.official_primary_evidence_loader_v1 import (
    BoundedOfficialPrimaryEvidenceLoader,
)


AS_OF = "2026-08-19T08:00:00Z"
BINDING = {
    "cluster_id": "authorized-policy-story",
    "headline_ids": ["policy-headline"],
    "request_logical_hash": "r" * 64,
}


def _packet() -> dict[str, Any]:
    return {
        "schema_version": "capital_chronicle_content_evidence_packet.v2",
        "packet_id": "demo-cc-packet-1",
        "status": "PASS_PUBLICATION_AUTHORIZED",
        "generated_at_utc": "2026-08-19T07:05:00Z",
        "as_of_utc": AS_OF,
        "story_window": {"hours": 24},
        "rolling_x_story_binding": dict(BINDING),
        "events": [{"event_time_utc": "2026-08-19T07:00:00Z"}],
        "official_source_documents": [{
            "document_id": "official-policy-release",
            "publisher": "Official Policy Authority",
            "source_id": "official-policy-authority",
            "source_url": "https://www.federalreserve.gov/newsevents/pressreleases/test.htm",
            "source_authority_class": "official_public_primary_source",
            "published_at_utc": "2026-08-19T07:00:00Z",
            "raw_sha256": "a" * 64,
            "public_claim_allowed": True,
        }],
        "numeric_claims": [{
            "claim_id": "policy-observation-1",
            "metric": "authorized policy observation",
            "value": "4.50",
            "unit": "percent",
            "observation_time_utc": "2026-08-19T07:00:00Z",
            "known_at_utc": "2026-08-19T07:05:00Z",
            "source_id": "official-policy-authority",
            "source_artifact_ref": "packet#numeric_claims/0",
            "public_claim_allowed": True,
            "llm_numeric_authority": False,
            "observed_forecast_scenario_state": "OBSERVED",
        }],
        "market_snapshots": [{"snapshot_id": "policy-snapshot", "claim_ids": ["policy-observation-1"]}],
        "time_series": {"policy_history": [{"date": "2026-08-19", "value": "4.50"}]},
        "time_series_references": ["packet#time_series/policy_history"],
        "candidate_visual_inputs": [{
            "visual_input_id": "policy-history-chart",
            "series_id": "policy_history",
            "public_claim_allowed": True,
            "public_display_allowed": True,
        }],
        "citation_map": {"policy-observation-1": ["packet#numeric_claims/0"]},
        "source_state": {"dqr_status": "READY", "source_health_status": "HEALTHY"},
        "provenance": {"publication_packet": {"sha256": "b" * 64, "upstream_packet_id": "upstream-demo-1"}},
        "public_claim_permissions": {
            "decision": "ALLOW",
            "reporting_allowed": True,
            "numeric_claims_allowed": True,
            "consumer_class": ["contentops_publication"],
            "llm_numeric_authority": False,
        },
        "blockers": [],
        "governed_contract": {
            "mode": "story_scoped_publication_evidence_v1",
            "upstream_packet_id": "upstream-demo-1",
            "upstream_packet_sha256": "b" * 64,
        },
    }


def _real_read_only_source_smoke() -> dict[str, Any]:
    url = (
        "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
        "TextView?type=daily_treasury_yield_curve"
    )
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-19T23:59:00Z",
        max_requests=1,
        timeout_seconds=12.0,
        max_response_bytes=2_000_000,
    )
    try:
        receipt = loader({
            "cluster_id": "real-read-only-treasury-source-smoke",
            "headline_ids": ["treasury-source-smoke"],
            "source_adapter_families": ["official_macro"],
            "story_context": {
                "official_source_url_bindings": [{
                    "headline_id": "treasury-source-smoke",
                    "url": url,
                    "feed_published_at_utc": "2026-08-19T00:00:00Z",
                }]
            },
        })
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        return {
            "attempted": True,
            "status": "UNAVAILABLE",
            "outcome": "safe_loader_exception:" + type(exc).__name__,
            "source_url": url,
            "public_claim_authority_weakened": False,
        }
    documents = receipt.get("official_source_documents") or []
    document = (documents or [{}])[0]
    return {
        "attempted": True,
        "status": receipt.get("status"),
        "blockers": list(receipt.get("blockers") or []),
        "source_url": document.get("source_url") or url,
        "published_at_utc": document.get("published_at_utc"),
        "published_at_source": document.get("published_at_source"),
        "content_sha256": document.get("canonical_content_sha256") or document.get("raw_sha256"),
        "accepted_document_count": len(documents),
        "request_count": (receipt.get("provenance") or {}).get("request_count"),
        "public_claim_authority_weakened": False,
    }


def run_demo(*, real_source_smoke: bool = False) -> dict[str, Any]:
    packet = _packet()
    authorized = resolve_publication_authority(packet, story_binding=BINDING)
    projection = build_publication_authorized_projection(packet, authorized)
    v1_projection_blockers = validate_projection_for_consumer(
        projection, consumer="v1_article"
    )
    v2_projection_blockers = validate_projection_for_consumer(
        projection, consumer="v2_media"
    )
    media_packet = json.loads(json.dumps(packet))
    media_packet["public_claim_permissions"].update({
        "public_display_allowed": True,
        "allowed_uses": ["public_reporting", "public_media_display"],
    })
    media_resolution = resolve_publication_authority(
        media_packet,
        story_binding=BINDING,
        intended_use="public_media_display",
    )
    media_projection = build_publication_authorized_projection(
        media_packet, media_resolution
    )
    explicit_media_projection_blockers = validate_projection_for_consumer(
        media_projection, consumer="v2_media"
    )

    internal_packet = json.loads(json.dumps(packet))
    internal_packet["status"] = "PASS_CONTRACT_BLOCKED_PUBLICATION"
    internal_packet["governed_contract"]["mode"] = "governed_point_in_time_handoff_v1"
    internal_packet["public_claim_permissions"]["decision"] = "BLOCK"
    internal_packet["public_claim_permissions"]["reporting_allowed"] = False
    internal = resolve_publication_authority(internal_packet, story_binding=BINDING)

    missing = resolve_publication_authority(None, story_binding={
        "cluster_id": "ordinary-web-story",
        "headline_ids": ["web-headline"],
        "request_logical_hash": "w" * 64,
    })
    web_body = (
        "<html><head><title>Accessible current policy report</title></head><body>"
        + "Accessible professional reporting independently establishes the public event. " * 20
        + "</body></html>"
    ).encode("utf-8")
    web_loader = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=4,
        max_requests_per_candidate=2,
        http_get=lambda url, *_args: {
            "status": 200,
            "final_url": url,
            "headers": {"content-type": "text/html"},
            "body": web_body,
        },
        clock=lambda: datetime(2026, 8, 19, 8, tzinfo=timezone.utc),
    )
    web = web_loader({
        "cluster_id": "ordinary-web-story",
        "headline_ids": ["web-headline"],
        "request_logical_hash": "w" * 64,
        "story_context": {
            "leaf_summaries": ["Accessible current policy report"],
            "public_source_url_bindings": [{
                "headline_id": "web-headline",
                "url": "https://reuters.com/world/accessible-current-policy-report",
                "feed_published_at_utc": "2026-08-19T07:30:00Z",
            }],
        },
    })

    with tempfile.TemporaryDirectory(prefix="contentops_p0_1_zero_write_") as temp:
        root = Path(temp)
        db_dir = root / "data/local_db"
        db_dir.mkdir(parents=True)
        db_path = db_dir / "policy_context.duckdb"
        with duckdb.connect(str(db_path)) as connection:
            connection.execute(
                "CREATE TABLE policy_events(title VARCHAR, known_at TIMESTAMP, source_id VARCHAR)"
            )
            connection.execute(
                "INSERT INTO policy_events VALUES "
                "('Federal Reserve policy decision', '2026-08-19 07:00:00', 'fed')"
            )
        before = hashlib.sha256(db_path.read_bytes()).hexdigest()
        catalog = discover_cc_data_estate(cc_root=root, use_cache=False)
        semantic = derive_story_scoped_cc_semantics({
            "leaf_summaries": ["Federal Reserve policy decision changes interest rates"]
        })
        context = query_story_scoped_cc_context(
            catalog, semantic["query_terms"], semantic_activation=semantic
        )
        after = hashlib.sha256(db_path.read_bytes()).hexdigest()
        empty_semantic = derive_story_scoped_cc_semantics({"leaf_summaries": ["brief update"]})
        no_context = query_story_scoped_cc_context(
            catalog, [], semantic_activation=empty_semantic
        )
        incompatible_root = root / "incompatible"
        publication_dir = (
            incompatible_root / "docs/research/publication_evidence/current"
        )
        publication_dir.mkdir(parents=True)
        (publication_dir / "CapitalChroniclePublicationEvidencePacketV9.json").write_text(
            json.dumps({
                "schema_version": "capital_chronicle.publication_evidence_packet.v9",
                "packet_id": "incompatible-demo-9",
                "as_of_utc": AS_OF,
                "status": "PASS_PUBLICATION_AUTHORIZED",
            }),
            encoding="utf-8",
        )
        incompatible_packet = build_evidence_packet_from_cc_root(
            incompatible_root, story_binding=BINDING
        )
        incompatible = resolve_publication_authority(
            incompatible_packet, story_binding=BINDING
        )

    historical_path = (
        REPO_ROOT
        / "docs/automation/CONTENTOPS_FULL_AUTOMATION_LIVE_CANONICAL_BROWSER_RUN_V1"
        / "contentops_full_automation_live_20260807_1/grounded_support_v1.json"
    )
    historical_packet = json.loads(historical_path.read_text(encoding="utf-8"))[
        "official_source_packet"
    ]
    historical_story_id = historical_packet["publication_assignment"]["duplicate_key"]
    historical_reporting = resolve_publication_authority(
        historical_packet,
        story_binding={"story_id": historical_story_id},
        intended_use="public_reporting",
    )
    historical_media = resolve_publication_authority(
        historical_packet,
        story_binding={"story_id": historical_story_id},
        intended_use="public_media_display",
    )
    live_source = _real_read_only_source_smoke() if real_source_smoke else {
        "attempted": False,
        "status": "NOT_REQUESTED",
    }

    stale = resolve_publication_authority(
        packet,
        story_binding=BINDING,
        current_readiness_blockers=["source_health_stale_for_current_story"],
    )
    states = sorted({
        authorized["state"], internal["state"], missing["state"], stale["state"],
        context["state"], no_context["state"],
    })
    expected_states = sorted({
        "PUBLICATION_PACKET_AVAILABLE",
        "PUBLICATION_PACKET_NOT_AVAILABLE",
        "PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED",
        "PUBLICATION_PACKET_STALE_OR_BLOCKED",
        "CONTEXT_ONLY_AVAILABLE",
        "NO_RELEVANT_CC_CONTEXT",
    })
    passed = bool(
        states == expected_states
        and not v1_projection_blockers
        and "cc_projection_use_grant_mismatch" in v2_projection_blockers
        and not explicit_media_projection_blockers
        and historical_reporting["state"] == "PUBLICATION_PACKET_AVAILABLE"
        and historical_media["state"] == "PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED"
        and "CC_GOVERNED_SURFACE_COMPATIBILITY_REQUIRED" in incompatible["reason_codes"]
        and projection["exact_numeric_claims"] == packet["numeric_claims"]
        and projection["exact_time_series"] == packet["time_series"]
        and projection["exact_chart_inputs"] == []
        and media_projection["exact_chart_inputs"] == packet["candidate_visual_inputs"]
        and web["status"] == "PASS"
        and missing["ordinary_latest_web_article_may_continue"] is True
        and context["queried_table_count"] > 0
        and no_context["queried_table_count"] == 0
        and before == after
    )
    return {
        "schema_version": "contentops.p0_1_zero_write_demo.v1",
        "classification": "PASS" if passed else "FAIL",
        "as_of_utc": AS_OF,
        "story_cases": {
            "publication_authorized_consumed": {
                "resolution": authorized,
                "projection_fingerprint": projection["projection_fingerprint"],
                "exact_values_preserved": projection["exact_numeric_claims"] == packet["numeric_claims"],
                "v1_projection_blockers": v1_projection_blockers,
                "v2_projection_blockers": v2_projection_blockers,
            },
            "explicit_media_display_authorized": {
                "resolution": media_resolution,
                "projection_fingerprint": media_projection["projection_fingerprint"],
                "v2_projection_blockers": explicit_media_projection_blockers,
                "exact_values_preserved": (
                    media_projection["exact_numeric_claims"] == packet["numeric_claims"]
                ),
            },
            "accepted_historical_treasury_contract": {
                "reporting_resolution": historical_reporting,
                "media_display_resolution": historical_media,
                "artifact_relative_path": str(historical_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            },
            "internal_analyzer_non_public": {"resolution": internal},
            "incompatible_packet_present": {
                "resolution": incompatible,
                "selection": incompatible_packet["governed_contract"]["publication_selection"],
            },
            "missing_cc_ordinary_latest_web": {
                "resolution": missing,
                "web_status": web["status"],
                "accepted_document_count": len(web["evidence_documents"]),
                "source_url": (web["evidence_documents"] or [{}])[0].get("source_url"),
                "published_at_source": (web["evidence_documents"] or [{}])[0].get("published_at_source"),
                "content_hash_present": bool((web["evidence_documents"] or [{}])[0].get("canonical_content_sha256")),
            },
            "relevant_context": {
                "semantic_activation": semantic,
                "queried_table_count": context["queried_table_count"],
                "matched_table_count": context["matched_table_count"],
                "catalog_fingerprint": context["catalog_fingerprint"],
                "query_budget": context["query_budget"],
                "query_elapsed_ms": context["query_elapsed_ms"],
                "database_sha256_unchanged": before == after,
            },
            "no_relevant_context": {
                "semantic_activation": empty_semantic,
                "queried_table_count": no_context["queried_table_count"],
                "zero_context_reason": no_context["zero_context_reason"],
            },
        },
        "reachable_high_level_states": states,
        "real_read_only_latest_web_source_smoke": live_source,
        "safety": {
            "public_write_performed": False,
            "provider_call_made": False,
            "browser_or_cdp_used": False,
            "external_network_call_made": bool(real_source_smoke),
            "secret_or_session_material_read": False,
            "upstream_mutated": before != after,
            "model_created_numeric_substitution": False,
            "llm_numeric_authority": False,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--real-source-smoke", action="store_true")
    args = parser.parse_args(argv)
    result = run_demo(real_source_smoke=args.real_source_smoke)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(json.dumps({
        "classification": result["classification"],
        "reachable_high_level_states": result["reachable_high_level_states"],
    }, sort_keys=True))
    return 0 if result["classification"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
