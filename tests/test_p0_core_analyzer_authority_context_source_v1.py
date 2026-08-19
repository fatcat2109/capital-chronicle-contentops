from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from live_contentops.capital_chronicle_data_catalog_v1 import (
    derive_story_scoped_cc_semantics,
    discover_cc_data_estate,
    query_story_scoped_cc_context,
)
from live_contentops.cc_evidence_bridge_v2 import build_evidence_packet_from_cc_root
from live_contentops.cc_publication_authority_v1 import (
    CONTEXT_ONLY_AVAILABLE,
    NO_RELEVANT_CC_CONTEXT,
    PUBLICATION_PACKET_AVAILABLE,
    PUBLICATION_PACKET_NOT_AVAILABLE,
    PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED,
    PUBLICATION_PACKET_STALE_OR_BLOCKED,
    build_publication_authorized_projection,
    resolve_publication_authority,
    validate_projection_for_consumer,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
)


AS_OF = "2026-08-19T08:00:00Z"


def _bridge_packet() -> dict:
    return {
        "schema_version": "capital_chronicle_content_evidence_packet.v2",
        "packet_id": "bridge-packet-1",
        "status": "PASS_PUBLICATION_AUTHORIZED",
        "generated_at_utc": "2026-08-19T07:05:00Z",
        "as_of_utc": AS_OF,
        "story_window": {"hours": 24},
        "rolling_x_story_binding": {
            "cluster_id": "story-fed",
            "headline_ids": ["h-fed"],
            "request_logical_hash": "r" * 64,
        },
        "events": [{"event_time_utc": "2026-08-19T07:00:00Z"}],
        "official_source_documents": [
            {
                "document_id": "fed-release",
                "publisher": "Federal Reserve",
                "source_id": "federal-reserve",
                "source_url": "https://www.federalreserve.gov/newsevents/pressreleases/test.htm",
                "source_authority_class": "official_public_primary_source",
                "published_at_utc": "2026-08-19T07:00:00Z",
                "raw_sha256": "a" * 64,
                "public_claim_allowed": True,
            }
        ],
        "numeric_claims": [
            {
                "claim_id": "fed-target-upper",
                "metric": "target upper bound",
                "value": "4.50",
                "unit": "percent",
                "observation_time_utc": "2026-08-19T07:00:00Z",
                "known_at_utc": "2026-08-19T07:05:00Z",
                "source_id": "federal-reserve",
                "source_artifact_ref": "packet#numeric_claims/0",
                "public_claim_allowed": True,
                "llm_numeric_authority": False,
                "observed_forecast_scenario_state": "OBSERVED",
            }
        ],
        "market_snapshots": [{"snapshot_id": "fed-snapshot", "claim_ids": ["fed-target-upper"]}],
        "time_series": {"policy_history": [{"date": "2026-08-19", "value": "4.50"}]},
        "time_series_references": ["packet#time_series/policy_history"],
        "candidate_visual_inputs": [
            {
                "visual_input_id": "policy-history-chart",
                "series_id": "policy_history",
                "public_claim_allowed": True,
                "public_display_allowed": True,
            }
        ],
        "citation_map": {"fed-target-upper": ["packet#numeric_claims/0"]},
        "source_state": {"dqr_status": "READY", "source_health_status": "HEALTHY"},
        "provenance": {
            "publication_packet": {
                "sha256": "b" * 64,
                "upstream_packet_id": "upstream-packet-1",
            }
        },
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
            "upstream_packet_id": "upstream-packet-1",
            "upstream_packet_sha256": "b" * 64,
        },
    }


def _binding() -> dict:
    return {
        "cluster_id": "story-fed",
        "headline_ids": ["h-fed"],
        "request_logical_hash": "r" * 64,
    }


def test_all_publication_and_context_high_level_states_are_reachable():
    missing = resolve_publication_authority(None, story_binding=_binding())
    assert missing["state"] == PUBLICATION_PACKET_NOT_AVAILABLE
    assert missing["ordinary_latest_web_article_may_continue"] is True

    internal = _bridge_packet()
    internal["status"] = "PASS_CONTRACT_BLOCKED_PUBLICATION"
    internal["governed_contract"]["mode"] = "governed_point_in_time_handoff_v1"
    internal["public_claim_permissions"]["decision"] = "BLOCK"
    internal["public_claim_permissions"]["reporting_allowed"] = False
    decision = resolve_publication_authority(internal, story_binding=_binding())
    assert decision["state"] == PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED
    assert "CC_INTERNAL_ANALYZER_HANDOFF_NOT_PUBLICATION_AUTHORITY" in decision["reason_codes"]

    stale = _bridge_packet()
    decision = resolve_publication_authority(
        stale,
        story_binding=_binding(),
        current_readiness_blockers=["market_sensitive_story_snapshot_stale_or_missing"],
    )
    assert decision["state"] == PUBLICATION_PACKET_STALE_OR_BLOCKED

    authorized = resolve_publication_authority(_bridge_packet(), story_binding=_binding())
    assert authorized["state"] == PUBLICATION_PACKET_AVAILABLE

    for key, value, reason in (
        ("candidate_snapshot_only", True, "CC_CANDIDATE_ONLY_NOT_PUBLICATION_AUTHORITY"),
        ("authority_state", "PROXY", "CC_PROXY_STATE_NOT_PUBLICATION_AUTHORITY"),
        ("quality_state", "DEGRADED", "CC_DEGRADED_STATE_NOT_PUBLICATION_AUTHORITY"),
    ):
        nonpublic = _bridge_packet()
        nonpublic["source_state"][key] = value
        decision = resolve_publication_authority(nonpublic, story_binding=_binding())
        assert decision["state"] == PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED
        assert reason in decision["reason_codes"]

    contextual = derive_story_scoped_cc_semantics(
        {"leaf_summaries": ["Federal Reserve policy decision changes interest rates"]}
    )
    assert contextual["state"] == CONTEXT_ONLY_AVAILABLE
    assert contextual["derivation_provenance"]
    none = derive_story_scoped_cc_semantics({"leaf_summaries": ["brief update"]})
    assert none["state"] == NO_RELEVANT_CC_CONTEXT
    assert none["zero_context_reason"] == "MEANINGFUL_STORY_SEMANTICS_ABSENT"


def test_shared_projection_schema_is_lossless_and_exact_use_bound_for_v1_and_v2():
    packet = _bridge_packet()
    resolution = resolve_publication_authority(packet, story_binding=_binding())
    projection = build_publication_authorized_projection(packet, resolution)

    assert projection["exact_numeric_claims"] == packet["numeric_claims"]
    assert projection["exact_time_series"] == packet["time_series"]
    assert projection["exact_chart_inputs"] == []
    assert projection["values_regenerated_or_repaired"] is False
    assert projection["llm_numeric_authority"] is False
    assert validate_projection_for_consumer(projection, consumer="v1_article") == []
    assert "cc_projection_use_grant_mismatch" in validate_projection_for_consumer(
        projection, consumer="v2_media"
    )

    media_resolution = resolve_publication_authority(
        packet,
        story_binding=_binding(),
        intended_use="public_media_display",
    )
    assert media_resolution["state"] == PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED
    assert (
        "CC_PUBLICATION_PACKET_PERMISSION_BLOCKED:intended_use:public_media_display"
        in media_resolution["reason_codes"]
    )

    explicitly_display_authorized = deepcopy(packet)
    explicitly_display_authorized["public_claim_permissions"].update({
        "public_display_allowed": True,
        "allowed_uses": ["public_reporting", "public_media_display"],
    })
    media_resolution = resolve_publication_authority(
        explicitly_display_authorized,
        story_binding=_binding(),
        intended_use="public_media_display",
    )
    assert media_resolution["state"] == PUBLICATION_PACKET_AVAILABLE
    media_projection = build_publication_authorized_projection(
        explicitly_display_authorized, media_resolution
    )
    assert media_projection["exact_numeric_claims"] == packet["numeric_claims"]
    assert media_projection["exact_time_series"] == packet["time_series"]
    assert media_projection["exact_chart_inputs"] == packet["candidate_visual_inputs"]
    assert validate_projection_for_consumer(media_projection, consumer="v2_media") == []

    tampered = deepcopy(projection)
    tampered["exact_numeric_claims"][0]["value"] = "9.99"
    assert "cc_projection_fingerprint_mismatch" in validate_projection_for_consumer(
        tampered, consumer="v1_article"
    )


def test_exact_consumer_and_use_must_be_proven_from_upstream_permissions():
    packet = _bridge_packet()
    mismatch = resolve_publication_authority(
        packet,
        story_binding=_binding(),
        intended_consumer="contentops_video_publication",
    )
    assert mismatch["state"] == PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED
    assert "CC_PUBLICATION_PACKET_PERMISSION_BLOCKED:consumer" in mismatch["reason_codes"]

    absent_use = resolve_publication_authority(
        packet,
        story_binding=_binding(),
        intended_use="public_media_display",
    )
    assert absent_use["resolved_upstream_grant"]["use_granted"] is False
    packet["public_claim_permissions"]["reporting_allowed"] = False
    reporting = resolve_publication_authority(packet, story_binding=_binding())
    assert reporting["state"] == PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED
    assert "CC_PUBLICATION_PACKET_PERMISSION_BLOCKED:intended_use:public_reporting" in reporting["reason_codes"]


def test_accepted_historical_treasury_packet_grants_reporting_not_media_display():
    evidence = Path(
        "docs/automation/CONTENTOPS_FULL_AUTOMATION_LIVE_CANONICAL_BROWSER_RUN_V1/"
        "contentops_full_automation_live_20260807_1/grounded_support_v1.json"
    )
    packet = json.loads(evidence.read_text(encoding="utf-8"))["official_source_packet"]
    story_id = packet["publication_assignment"]["duplicate_key"]
    reporting = resolve_publication_authority(
        packet, story_binding={"story_id": story_id}, intended_use="public_reporting"
    )
    media = resolve_publication_authority(
        packet, story_binding={"story_id": story_id}, intended_use="public_media_display"
    )
    assert reporting["state"] == PUBLICATION_PACKET_AVAILABLE
    assert reporting["resolved_upstream_grant"]["upstream_permission_evidence"][
        "permission_field"
    ] == "reporting_allowed"
    assert media["state"] == PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED
    assert media["resolved_upstream_grant"]["upstream_permission_evidence"][
        "public_display_allowed"
    ] is None


def test_explicit_compatible_successor_filename_is_discovered_and_bound(tmp_path: Path):
    current = tmp_path / "docs/research/publication_evidence/current"
    current.mkdir(parents=True)
    source = {
        "schema_version": "capital_chronicle.publication_evidence_packet.v2",
        "contentops_compatibility": {
            "compatible_with": ["capital_chronicle.publication_evidence_packet.v1"],
            "essential_authority_semantics_preserved": True,
        },
        "packet_id": "successor-1",
        "status": "PASS_PUBLICATION_AUTHORIZED",
        "generated_at_utc": "2026-08-19T07:05:00Z",
        "as_of_utc": AS_OF,
        "consumer_class": ["contentops_publication"],
        "story_authority": {
            "decision": "ALLOW",
            "scope": "story-fed",
            "global_dqr_override": False,
        },
        "public_claim_permissions": {
            "decision": "ALLOW",
            "reporting_allowed": True,
            "numeric_claims_allowed": True,
            "narrative_synthesis_allowed": True,
            "public_display_allowed": True,
            "allowed_uses": ["public_reporting", "public_media_display"],
            "llm_numeric_authority": False,
        },
        "source_health": {"status": "HEALTHY"},
        "global_authority": {"dqr": "BLOCKED", "global_state_unchanged": True},
        "rolling_x_story_binding": _binding(),
        "numeric_claims": [_bridge_packet()["numeric_claims"][0]],
        "official_source_documents": _bridge_packet()["official_source_documents"],
        "market_snapshots": _bridge_packet()["market_snapshots"],
        "time_series": _bridge_packet()["time_series"],
        "candidate_visual_inputs": _bridge_packet()["candidate_visual_inputs"],
        "citation_map": _bridge_packet()["citation_map"],
        "provided_evidence_capabilities": ["credible_event_confirmation"],
        "blockers": [],
    }
    path = current / "CapitalChroniclePublicationEvidencePacketV2.json"
    path.write_text(json.dumps(source), encoding="utf-8")

    packet = build_evidence_packet_from_cc_root(tmp_path, story_binding=_binding())
    assert packet["status"] == "PASS_PUBLICATION_AUTHORIZED"
    assert packet["governed_contract"]["schema_compatibility_mode"] == "EXPLICIT_COMPATIBLE_SUCCESSOR"
    assert packet["provenance"]["publication_packet"]["relative_path"].endswith(
        "CapitalChroniclePublicationEvidencePacketV2.json"
    )
    assert packet["public_claim_permissions"]["public_display_allowed"] is True


def test_incompatible_successor_remains_present_and_compatibility_required(tmp_path: Path):
    current = tmp_path / "docs/research/publication_evidence/current"
    current.mkdir(parents=True)
    path = current / "CapitalChroniclePublicationEvidencePacketV9.json"
    path.write_text(json.dumps({
        "schema_version": "capital_chronicle.publication_evidence_packet.v9",
        "packet_id": "incompatible-9",
        "as_of_utc": AS_OF,
        "status": "PASS_PUBLICATION_AUTHORIZED",
        "public_claim_permissions": {
            "decision": "ALLOW", "reporting_allowed": True
        },
    }), encoding="utf-8")

    packet = build_evidence_packet_from_cc_root(tmp_path, story_binding=_binding())
    resolution = resolve_publication_authority(packet, story_binding=_binding())
    assert packet["governed_contract"]["publication_selection"]["state"] == (
        "PRESENT_INCOMPATIBLE"
    )
    assert "CC_GOVERNED_SURFACE_COMPATIBILITY_REQUIRED" in packet["blockers"]
    assert resolution["state"] == PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED
    assert resolution["state"] != PUBLICATION_PACKET_NOT_AVAILABLE
    assert resolution["ordinary_latest_web_article_may_continue"] is True


def test_semantic_activation_executes_only_bounded_read_only_queries(tmp_path: Path):
    db_dir = tmp_path / "data/local_db"
    db_dir.mkdir(parents=True)
    db_path = db_dir / "events.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        connection.execute(
            "CREATE TABLE policy_events(title VARCHAR, known_at TIMESTAMP, source_id VARCHAR)"
        )
        connection.execute(
            "INSERT INTO policy_events VALUES "
            "('Federal Reserve policy decision', '2026-08-19 07:00:00', 'fed')"
        )
    before = db_path.read_bytes()
    catalog = discover_cc_data_estate(cc_root=tmp_path, use_cache=False)
    semantic = derive_story_scoped_cc_semantics(
        {"leaf_summaries": ["Federal Reserve announces a policy decision"]}
    )
    context = query_story_scoped_cc_context(
        catalog, semantic["query_terms"], semantic_activation=semantic
    )

    assert context["state"] == CONTEXT_ONLY_AVAILABLE
    assert 0 < context["queried_table_count"] <= context["deep_query_table_limit"]
    assert context["matches"]
    assert context["connection_mode"] == "duckdb_read_only"
    assert context["mutated_upstream"] is False
    assert db_path.read_bytes() == before

    zero = query_story_scoped_cc_context(
        catalog,
        [],
        semantic_activation=derive_story_scoped_cc_semantics({"leaf_summaries": ["brief update"]}),
    )
    assert zero["state"] == NO_RELEVANT_CC_CONTEXT
    assert zero["queried_table_count"] == 0


def test_bound_timestamp_recovers_accessible_source_without_snippet_promotion():
    article = (
        "<html><head><title>Federal Reserve policy report</title></head><body>"
        + "The Federal Reserve published a policy report with current evidence. " * 20
        + "</body></html>"
    ).encode()
    calls: list[str] = []

    def get(url, *_args):
        calls.append(url)
        return {
            "status": 200,
            "final_url": url,
            "headers": {"content-type": "text/html"},
            "body": article,
        }

    loader = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=8,
        max_requests_per_candidate=2,
        http_get=get,
        clock=lambda: datetime(2026, 8, 19, 8, tzinfo=timezone.utc),
    )
    request = {
        "cluster_id": "web-story",
        "headline_ids": ["web-headline"],
        "request_logical_hash": "w" * 64,
        "story_context": {
            "leaf_summaries": ["Federal Reserve policy report"],
            "public_source_url_bindings": [
                {
                    "headline_id": "web-headline",
                    "url": "https://reuters.com/world/test",
                    "feed_published_at_utc": "2026-08-19T07:30:00Z",
                }
            ],
        },
    }
    receipt = loader(request)
    assert receipt["status"] == "PASS"
    assert receipt["evidence_documents"][0]["published_at_source"] == "EXACT_BOUND_DISCOVERY_TIMESTAMP"
    assert receipt["evidence_documents"][0]["canonical_content_sha256"]
    assert receipt["provenance"]["request_count_for_candidate"] == 1
    assert receipt["provenance"]["request_limit_per_candidate"] == 2
    assert receipt["publication_authority"] is False


def test_unresolved_news_listing_remains_locator_only_not_factual_authority():
    rss = b"""<?xml version='1.0'?><rss><channel><item>
    <title>Policy authority issues a new statement - Reuters</title>
    <link>https://news.google.com/unresolved</link>
    <pubDate>Wed, 19 Aug 2026 07:30:00 GMT</pubDate>
    <source url='https://reuters.com'>Reuters</source>
    </item></channel></rss>"""
    loader = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda url, *_args: {
            "status": 200,
            "final_url": url,
            "headers": {"content-type": "application/rss+xml"},
            "body": rss,
        },
        clock=lambda: datetime(2026, 8, 19, 8, tzinfo=timezone.utc),
    )
    receipt = loader({
        "cluster_id": "locator-only",
        "headline_ids": ["locator-headline"],
        "request_logical_hash": "l" * 64,
        "story_context": {"leaf_summaries": ["Policy authority issues a new statement"]},
    })
    assert receipt["status"] == "BLOCKED"
    assert receipt["evidence_documents"] == []
    assert receipt["locator_only_records"]
    assert all(
        row["public_claim_allowed"] is False
        and row["locator_or_attribution_only"] is True
        for row in receipt["locator_only_records"]
    )
