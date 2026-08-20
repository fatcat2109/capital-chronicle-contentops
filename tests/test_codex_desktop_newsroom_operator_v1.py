import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_data_catalog_v1 import (
    _CATALOG_CACHE,
    discover_cc_data_estate,
    inspect_governed_cc_surfaces,
    query_story_scoped_cc_context,
)
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    COORDINATOR_MODEL,
    COORDINATOR_REASONING_EFFORT,
    DESKTOP_TASK_PROMPT,
    EDITORIAL_WORKER_MODEL,
    EDITORIAL_WORKER_REASONING_EFFORT,
    MANUAL_GO_PROMPT,
    build_editorial_worker_routing_packet,
    build_live_zero_write_rehearsal,
    classify_desktop_candidate_universe,
    four_task_setup_packet,
    load_terminal_editorial_continuity,
    validate_editorial_worker_return,
)
from live_contentops.newsroom_assignment_scheduler_v1 import (
    build_prepared_rolling_x_candidate_state,
    load_rolling_x_headline_sidecars,
)
from live_contentops.daily_app_supervisor_v1 import ContentOpsDailyAppSupervisor


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _create_store(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE work_items (
            work_item_id TEXT PRIMARY KEY, story_id TEXT NOT NULL, current_state TEXT NOT NULL,
            target_surface TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE outbox_messages (
            message_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL,
            destination TEXT NOT NULL, payload TEXT NOT NULL
        );
        CREATE TABLE platform_dispatches (
            dispatch_id TEXT PRIMARY KEY, message_id TEXT NOT NULL, platform TEXT NOT NULL,
            public_object_url TEXT
        );
        CREATE TABLE reconciliations (
            reconciliation_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, status TEXT NOT NULL
        );
        CREATE TABLE learning_policy_versions (
            policy_version TEXT PRIMARY KEY, parent_policy_version TEXT, created_at_utc TEXT,
            status TEXT, decision TEXT, sample_count INTEGER, confidence REAL,
            formula_version TEXT, observation_ids_json TEXT, evaluation_window TEXT,
            accepted_changes_json TEXT, bounded_delta_json TEXT, rollback_reference TEXT,
            decision_reason TEXT, policy_payload_json TEXT, policy_hash TEXT
        );
        """
    )
    connection.commit()
    connection.close()


def _terminal_cycle(
    store_path: Path,
    output_root: Path,
    *,
    window_id: str,
    cutoff: str,
    headline_ids: list[str],
    updated_at: str,
    catalog_fingerprint: str,
) -> None:
    connection = sqlite3.connect(store_path)
    connection.execute(
        "INSERT INTO work_items VALUES (?,?,?,?,?)",
        (
            window_id,
            window_id,
            "REJECTED",
            "daily_app_editorial_window",
            updated_at,
        ),
    )
    connection.commit()
    connection.close()
    cycle_dir = output_root / window_id
    _write_json(cycle_dir / "rolling_x_intake_v1.json", {
        "cutoff_time_utc": cutoff,
        "unique_headline_ids": headline_ids,
    })
    _write_json(cycle_dir / "rolling_x_newsroom_cycle_evidence_v1.json", {
        "classification": "NO_PUBLICATION",
        "public_write_performed": False,
    })
    _write_json(cycle_dir / "rolling_x_assignment_v1.json", {
        "ranked_clusters": [{
            "cluster_id": f"chain-{window_id}",
            "headline_ids": headline_ids,
        }],
    })
    _write_json(cycle_dir / "editorial_portfolio_context_v1.json", {
        "capital_chronicle_read_model": {
            "catalog_fingerprint": catalog_fingerprint,
        }
    })


def _publication_packet(*, schema_version: str = "capital_chronicle.publication_evidence_packet.v1", source_health: str = "HEALTHY") -> dict:
    return {
        "schema_version": schema_version,
        "status": "PASS_PUBLICATION_AUTHORIZED",
        "packet_id": "packet-1",
        "generated_at_utc": "2026-08-16T04:00:00Z",
        "as_of_utc": "2026-08-16T03:00:00Z",
        "story_authority": {"decision": "ALLOW", "scope": "story-1"},
        "public_claim_permissions": {
            "decision": "ALLOW",
            "numeric_claims_allowed": True,
            "llm_numeric_authority": False,
        },
        "source_health": {"status": source_health, "freshness_age_hours": 1.0},
        "provenance": {"retrieved_at_utc": "2026-08-16T03:00:00Z"},
        "blockers": [],
        "numeric_claims": [{"claim_id": "n1"}],
        "time_series": [{"series_id": "s1"}],
    }


def _newsroom_pool() -> dict:
    return {
        "schema_version": "capital_chronicle.newsroom_candidate_pool.v1",
        "status": "PASS_CANDIDATE_POOL_READY",
        "pool_id": "pool-1",
        "cutoff_time_utc": "2026-08-16T04:00:00Z",
        "candidate_only": True,
        "counts": {"eligible": 2},
    }


def _create_cc_root(root: Path) -> Path:
    duckdb = pytest.importorskip("duckdb")
    db_dir = root / "data" / "local_db"
    db_dir.mkdir(parents=True)
    connection = duckdb.connect(str(db_dir / "entities.duckdb"))
    connection.execute(
        "CREATE TABLE entity_history (display_name VARCHAR, known_at TIMESTAMP, dqr VARCHAR)"
    )
    connection.execute(
        "INSERT INTO entity_history VALUES ('Federal Reserve','2026-08-16 03:00:00','PASS')"
    )
    connection.close()
    _write_json(
        root / "docs/research/publication_evidence/current/CapitalChroniclePublicationEvidencePacketV1.json",
        _publication_packet(),
    )
    _write_json(
        root / "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json",
        _newsroom_pool(),
    )
    return db_dir / "entities.duckdb"


def test_terminal_cutoff_uses_latest_terminal_artifact_and_read_only_store(tmp_path):
    store = tmp_path / "store.sqlite3"
    outputs = tmp_path / "outputs"
    _create_store(store)
    _terminal_cycle(
        store,
        outputs,
        window_id="window-old",
        cutoff="2026-08-16T02:00:00Z",
        headline_ids=["h-old"],
        updated_at="2026-08-16T02:10:00Z",
        catalog_fingerprint="catalog-old",
    )
    _terminal_cycle(
        store,
        outputs,
        window_id="window-new",
        cutoff="2026-08-16T04:00:00Z",
        headline_ids=["h-seen"],
        updated_at="2026-08-16T04:10:00Z",
        catalog_fingerprint="catalog-new",
    )
    before = hashlib.sha256(store.read_bytes()).hexdigest()

    continuity = load_terminal_editorial_continuity(
        store_path=store, output_root=outputs
    )

    assert continuity["last_terminal_cutoff_utc"] == "2026-08-16T04:00:00Z"
    assert continuity["terminal_window_id"] == "window-new"
    assert continuity["evaluated_headline_ids"] == ["h-old", "h-seen"]
    assert continuity["prior_cc_catalog_fingerprint"] == "catalog-new"
    assert continuity["store_open_mode"] == "SQLITE_URI_MODE_RO_QUERY_ONLY"
    assert continuity["database_writes_performed"] is False
    assert hashlib.sha256(store.read_bytes()).hexdigest() == before


def test_terminal_continuity_uses_attempted_frontier_not_full_intake_universe(tmp_path):
    store = tmp_path / "store.sqlite3"
    outputs = tmp_path / "outputs"
    _create_store(store)
    full_ids = [f"headline-{index:02d}" for index in range(20)]
    _terminal_cycle(
        store,
        outputs,
        window_id="window-frontier",
        cutoff="2026-08-16T04:00:00Z",
        headline_ids=full_ids,
        updated_at="2026-08-16T04:10:00Z",
        catalog_fingerprint="catalog-frontier",
    )
    cycle_dir = outputs / "window-frontier"
    _write_json(cycle_dir / "rolling_x_assignment_v1.json", {
        "ranked_clusters": [
            {"cluster_id": "attempted", "rank": 1, "headline_ids": full_ids[:2]},
            {"cluster_id": "held", "rank": 2, "headline_ids": full_ids[2:4]},
        ],
    })
    _write_json(cycle_dir / "rolling_x_newsroom_cycle_evidence_v1.json", {
        "classification": "NO_PUBLICATION",
        "candidate_walk": {
            "candidate_attempts": [{"rank": 1, "cluster_id": "attempted"}],
        },
        "public_write_performed": False,
    })

    continuity = load_terminal_editorial_continuity(
        store_path=store, output_root=outputs
    )

    assert continuity["evaluated_headline_ids"] == full_ids[:2]
    assert continuity["terminal_records"][0]["evaluated_identity_source"] == (
        "CANDIDATE_WALK_ATTEMPTS"
    )
    assert continuity["last_terminal_cutoff_utc"] == "2026-08-16T04:00:00Z"


def test_frontier_only_non_promotion_is_not_editorially_evaluated(tmp_path):
    store = tmp_path / "store.sqlite3"
    outputs = tmp_path / "outputs"
    _create_store(store)
    _terminal_cycle(
        store,
        outputs,
        window_id="window-frontier-disposition",
        cutoff="2026-08-16T04:00:00Z",
        headline_ids=["selected", "cheap-only"],
        updated_at="2026-08-16T04:10:00Z",
        catalog_fingerprint="catalog-frontier-disposition",
    )
    cycle_dir = outputs / "window-frontier-disposition"
    _write_json(cycle_dir / "rolling_x_assignment_v1.json", {
        "ranked_clusters": [
            {"cluster_id": "selected-cluster", "rank": 1, "headline_ids": ["selected"]},
            {"cluster_id": "cheap-cluster", "rank": 2, "headline_ids": ["cheap-only"]},
        ],
    })
    _write_json(cycle_dir / "rolling_x_prepared_candidate_state_v1.json", {
        "prepared_frontier": {
            "selected_headline_ids": ["selected"],
            "not_promoted_headline_ids": ["cheap-only"],
            "identity_dispositions": [{
                "headline_id": "cheap-only",
                "disposition": "NOT_PROMOTED_BEFORE_EXPIRY",
                "accounting_level": "CHEAP_FRONTIER_DISPOSITION",
                "evidence_walk_evaluated": False,
            }],
        },
    })

    continuity = load_terminal_editorial_continuity(
        store_path=store, output_root=outputs
    )

    assert continuity["evaluated_headline_ids"] == ["selected"]
    assert "cheap-only" not in continuity["evaluated_headline_ids"]
    assert continuity["terminal_records"][0]["evaluated_identity_source"] == (
        "PREPARED_FRONTIER"
    )


def test_candidate_universe_dedupes_includes_material_and_late_unseen_excludes_published(tmp_path):
    store = tmp_path / "store.sqlite3"
    outputs = tmp_path / "outputs"
    _create_store(store)
    _terminal_cycle(
        store,
        outputs,
        window_id="window-last",
        cutoff="2026-08-16T04:00:00Z",
        headline_ids=["h-seen", "h-material"],
        updated_at="2026-08-16T04:10:00Z",
        catalog_fingerprint="catalog-last",
    )
    connection = sqlite3.connect(store)
    connection.execute(
        "INSERT INTO work_items VALUES (?,?,?,?,?)",
        ("published-work", "published-story", "COMPLETE", "article", "2026-08-16T03:00:00Z"),
    )
    connection.execute(
        "INSERT INTO outbox_messages VALUES (?,?,?,?)",
        (
            "message-1",
            "published-work",
            "substack",
            json.dumps({
                "story_identity": "published-story",
                "update_chain_identity": "published-chain",
            }),
        ),
    )
    connection.execute(
        "INSERT INTO platform_dispatches VALUES (?,?,?,?)",
        (
            "dispatch-1", "message-1", "substack",
            "https://capitalchronicle.substack.com/p/published-story",
        ),
    )
    connection.execute(
        "INSERT INTO reconciliations VALUES (?,?,?)",
        ("recon-1", "published-work", "RECONCILED_CONFIRMED"),
    )
    connection.commit()
    connection.close()
    continuity = load_terminal_editorial_continuity(
        store_path=store, output_root=outputs
    )
    headlines = [
        {"headline_id": "h-seen", "source_timestamp_utc": "2026-08-16T03:00:00Z"},
        {"headline_id": "h-seen", "source_timestamp_utc": "2026-08-16T03:00:00Z"},
        {"headline_id": "h-material", "source_timestamp_utc": "2026-08-16T03:30:00Z"},
        {"headline_id": "h-late", "source_timestamp_utc": "2026-08-16T03:45:00Z"},
        {"headline_id": "h-published", "source_timestamp_utc": "2026-08-16T05:00:00Z"},
    ]
    clusters = [
        {"cluster_id": "unchanged", "rank": 1, "headline_ids": ["h-seen"]},
        {
            "cluster_id": "material",
            "rank": 2,
            "headline_ids": ["h-material"],
            "update_chain_identity": "material-chain",
            "update_chain": {"relationship": "material_update"},
        },
        {"cluster_id": "late", "rank": 3, "headline_ids": ["h-late"]},
        {
            "cluster_id": "published-story",
            "rank": 4,
            "headline_ids": ["h-published"],
            "update_chain_identity": "published-chain",
        },
    ]

    universe = classify_desktop_candidate_universe(
        current_headlines=headlines,
        current_clusters=clusters,
        continuity=continuity,
    )

    assert universe["current_duplicate_headline_ids"] == ["h-seen"]
    assert [row["cluster_id"] for row in universe["included_clusters"]] == [
        "material", "late"
    ]
    assert universe["material_update_cluster_count"] == 1
    assert universe["late_arriving_unseen_headline_ids"] == ["h-late"]
    excluded = {row["cluster_id"]: row["decision"] for row in universe["excluded_clusters"]}
    assert excluded == {
        "unchanged": "EXCLUDE_UNCHANGED_PREVIOUSLY_EVALUATED",
        "published-story": "EXCLUDE_PUBLISHED_WITHOUT_MATERIAL_DELTA",
    }
    assert universe["timestamp_only_filter_used"] is False


@pytest.mark.parametrize(
    "relationship", ["material_update", "correction", "contradiction", "new_phase"]
)
def test_governed_material_relationship_reenters_even_when_identity_was_evaluated(
    relationship,
):
    universe = classify_desktop_candidate_universe(
        current_headlines=[{
            "headline_id": "evaluated-update",
            "source_timestamp_utc": "2026-08-16T05:00:00Z",
        }],
        current_clusters=[{
            "cluster_id": "update-cluster",
            "rank": 1,
            "headline_ids": ["evaluated-update"],
            "update_chain_identity": "durable-chain",
            "update_chain": {"relationship": relationship},
        }],
        continuity={
            "evaluated_headline_ids": ["evaluated-update"],
            "last_terminal_cutoff_utc": "2026-08-16T04:00:00Z",
            "published_memory": {
                "story_identities": [], "update_chain_identities": [],
            },
            "material_event_priority": {},
        },
    )

    assert universe["included_cluster_count"] == 1
    assert universe["included_clusters"][0]["decision"] == (
        "INCLUDE_MATERIAL_UPDATE_CHAIN"
    )
    assert universe["included_clusters"][0]["relationship"] == relationship
    rows = [
        {"headline_id": "evaluated-update", "source_timestamp_utc": "2026-08-16T05:00:00Z"},
        {"headline_id": "ordinary", "source_timestamp_utc": "2026-08-16T04:00:00Z"},
    ]
    prepared = build_prepared_rolling_x_candidate_state(
        rolling_input={
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "cutoff_time_utc": "2026-08-16T06:00:00Z",
            "window_start_utc": "2026-08-15T06:00:00Z",
            "window_hours": 24.0,
            "unique_headline_ids": ["evaluated-update", "ordinary"],
            "headlines": rows,
            "counts": {"accepted": 2, "duplicates": 0},
            "canonical_input_hash": "controlled",
            "complete_input_coverage": True,
        },
        prepared_at_utc="2026-08-16T06:00:00Z",
        max_candidates=1,
        evaluated_headline_ids=["evaluated-update"],
        reentry_headline_ids=["evaluated-update"],
    )
    assert prepared["prepared_frontier"]["selected_headline_ids"] == [
        "evaluated-update"
    ]
    assert prepared["prepared_frontier"]["identity_dispositions"][0][
        "material_reentry"
    ] is True


def test_cc_catalog_refreshes_on_estate_or_governed_surface_change_and_remains_read_only(tmp_path):
    root = tmp_path / "Main App"
    database_path = _create_cc_root(root)
    _CATALOG_CACHE.clear()
    database_before = hashlib.sha256(database_path.read_bytes()).hexdigest()

    first = discover_cc_data_estate(cc_root=root)
    cached = discover_cc_data_estate(cc_root=root)
    context = query_story_scoped_cc_context(first, ["Federal Reserve"])
    packet_path = root / "docs/research/publication_evidence/current/CapitalChroniclePublicationEvidencePacketV1.json"
    packet = _publication_packet()
    packet["packet_id"] = "packet-2"
    _write_json(packet_path, packet)
    refreshed = discover_cc_data_estate(cc_root=root)
    assert hashlib.sha256(database_path.read_bytes()).hexdigest() == database_before
    duckdb = pytest.importorskip("duckdb")
    connection = duckdb.connect(str(database_path))
    connection.execute(
        "CREATE TABLE newly_added_schema_surface (entity_name VARCHAR, as_of TIMESTAMP)"
    )
    connection.close()
    schema_refreshed = discover_cc_data_estate(cc_root=root)

    assert first["cache"]["state"] == "MISS"
    assert cached["cache"]["state"] == "HIT"
    assert refreshed["cache"]["state"] == "MISS"
    assert first["catalog_fingerprint"] != refreshed["catalog_fingerprint"]
    assert schema_refreshed["cache"]["state"] == "MISS"
    assert schema_refreshed["catalog_fingerprint"] != refreshed["catalog_fingerprint"]
    discovered_tables = {
        table["table"]
        for store in schema_refreshed["stores"]
        for table in store["tables"]
    }
    assert "newly_added_schema_surface" in discovered_tables
    assert first["store_count_discovered"] == first["store_count_total"] == 1
    assert context["grants_factual_or_numeric_authority"] is False
    assert context["mutated_upstream"] is False
    assert hashlib.sha256(database_path.read_bytes()).hexdigest() != database_before


def test_governed_surface_authority_is_distinct_from_context_and_schema_failure_is_bounded(tmp_path):
    root = tmp_path / "Main App"
    _create_cc_root(root)
    catalog = discover_cc_data_estate(cc_root=root, use_cache=False)
    inspected = inspect_governed_cc_surfaces(catalog)

    publication = inspected["surfaces"]["publication_evidence_packet"]
    pool = inspected["surfaces"]["newsroom_candidate_pool"]
    assert publication["authority_class"] == "GOVERNED_CC_AUTHORITY_PACKET"
    assert publication["packet_contract_authorized_for_exact_scope"] is True
    assert publication["publication_authority_granted"] is False
    assert publication["llm_numeric_authority"] is False
    assert pool["authority_class"] == "GOVERNED_NEWSROOM_DISCOVERY_ONLY"
    assert pool["publication_authority_granted"] is False
    assert inspected["compatible_governed_publication_packet_available"] is True
    assert inspected["governed_publication_authority_available"] is False
    assert inspected["context_or_discovery_grants_publication_authority"] is False

    packet_path = root / "docs/research/publication_evidence/current/CapitalChroniclePublicationEvidencePacketV1.json"
    _write_json(packet_path, _publication_packet(schema_version="future.unknown.v99"))
    future_catalog = discover_cc_data_estate(cc_root=root, use_cache=False)
    future = inspect_governed_cc_surfaces(future_catalog)
    assert future["compatibility_state"] == "CC_GOVERNED_SURFACE_COMPATIBILITY_REQUIRED"
    assert future["governed_publication_authority_available"] is False
    assert future["surfaces"]["newsroom_candidate_pool"]["state"] == "READY_CONTEXT_ONLY"


def test_stale_or_missing_governed_context_never_fabricates_authority(tmp_path):
    root = tmp_path / "Main App"
    _create_cc_root(root)
    packet_path = root / "docs/research/publication_evidence/current/CapitalChroniclePublicationEvidencePacketV1.json"
    pool_path = root / "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json"
    _write_json(packet_path, _publication_packet(source_health="STALE"))
    pool_path.unlink()

    inspected = inspect_governed_cc_surfaces(
        discover_cc_data_estate(cc_root=root, use_cache=False)
    )

    assert inspected["governed_publication_authority_available"] is False
    assert inspected["surfaces"]["publication_evidence_packet"]["state"] == (
        "CONTEXT_ONLY_NOT_AUTHORIZED"
    )
    assert inspected["surfaces"]["newsroom_candidate_pool"]["state"] == "MISSING"
    assert inspected["compatibility_state"] == "COMPATIBLE"
    packet_path.unlink()
    missing = inspect_governed_cc_surfaces(
        discover_cc_data_estate(cc_root=root, use_cache=False)
    )
    assert missing["governed_publication_authority_available"] is False
    assert missing["compatible_governed_publication_packet_available"] is False
    assert missing["surfaces"]["publication_evidence_packet"]["state"] == "MISSING"


def test_real_shape_zero_write_rehearsal_constructs_next_cutoff_without_parallel_authority(tmp_path):
    store = tmp_path / "store.sqlite3"
    outputs = tmp_path / "outputs"
    sidecars = tmp_path / "sidecars"
    sidecars.mkdir()
    _create_store(store)
    _terminal_cycle(
        store,
        outputs,
        window_id="window-last",
        cutoff="2026-08-17T12:00:00Z",
        headline_ids=["h-unrelated-prior"],
        updated_at="2026-08-17T12:10:00Z",
        catalog_fingerprint="catalog-prior",
    )
    (sidecars / "step1_headline_sidecar_2026_08_17.jsonl").write_text(
        json.dumps({
            "tweet_id": "live-1",
            "timestamp": "2026-08-17T13:00:00Z",
            "text": "Federal Reserve publishes a current official update",
            "linked_urls": ["https://federalreserve.gov/example"],
        }) + "\n",
        encoding="utf-8",
    )
    cc_root = tmp_path / "Main App"
    _create_cc_root(cc_root)
    store_before = hashlib.sha256(store.read_bytes()).hexdigest()
    output_files_before = sorted(path.relative_to(outputs) for path in outputs.rglob("*"))

    rehearsal = build_live_zero_write_rehearsal(
        cutoff_utc="2026-08-17T14:00:00Z",
        store_path=store,
        output_root=outputs,
        sidecar_glob=str(sidecars / "*.jsonl"),
        cc_root=cc_root,
    )

    assert rehearsal["continuity"]["last_terminal_cutoff_utc"] == "2026-08-17T12:00:00Z"
    assert rehearsal["current_intake"]["headline_count"] == 1
    assert rehearsal["candidate_or_abstention"]["decision"] == (
        "CANDIDATE_FOR_DESKTOP_EDITORIAL_JUDGMENT"
    )
    assert rehearsal["prepared_frontier_is_continuity_bound"] is True
    assert rehearsal["prepared_candidate_count"] == 1
    assert rehearsal["deferred_candidate_count"] == 0
    assert rehearsal["capital_chronicle"]["discovery_complete"] is True
    assert rehearsal["capital_chronicle"]["story_scoped_context"][
        "grants_factual_or_numeric_authority"
    ] is False
    assert rehearsal["next_terminal_cutoff_constructible"] is True
    assert rehearsal["public_writes"] == 0
    assert rehearsal["publication_coordinator_sole_public_writer_unchanged"] is True
    assert rehearsal["continuity"]["parallel_state_authority_created"] is False
    assert hashlib.sha256(store.read_bytes()).hexdigest() == store_before
    assert sorted(path.relative_to(outputs) for path in outputs.rglob("*")) == output_files_before


def test_desktop_rehearsal_reuses_canonical_reserved_frontier_and_never_promotes_raw_rank_one(
    tmp_path, monkeypatch,
):
    from live_contentops import codex_desktop_newsroom_operator_v1 as desktop_operator

    store = tmp_path / "store.sqlite3"
    outputs = tmp_path / "outputs"
    sidecars = tmp_path / "sidecars"
    sidecars.mkdir()
    sidecar = sidecars / "step1_headline_sidecar_2026_08_17.jsonl"
    original_ids = [f"reserved-seam-{index:02d}" for index in range(25)]
    urgent_tweet_id = "raw-rank-one-new-urgent"
    rows = [
        {
            "tweet_id": headline_id,
            "timestamp": "2026-08-17T13:00:00Z",
            "text": f"Controlled current development {headline_id}",
            "linked_urls": [f"https://reuters.com/{headline_id}"],
        }
        for headline_id in original_ids
    ] + [{
        "tweet_id": urgent_tweet_id,
        "timestamp": "2026-08-17T15:59:00Z",
        "text": "Controlled newly arrived urgent development",
        "linked_urls": ["https://reuters.com/new-urgent"],
    }]
    sidecar.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    cc_root = tmp_path / "Main App"
    _create_cc_root(cc_root)
    continuity = {
        "terminal_window_id": "terminal-before-target",
        "last_terminal_cutoff_utc": "2026-08-17T13:59:00Z",
        "evaluated_headline_ids": [],
        "published_memory": {"story_identities": [], "update_chain_identities": []},
        "material_event_priority": {"headline_ids": [], "priority_count": 0},
        "active_learning_policy": {},
        "continuity_logical_hash": "continuity-before-target",
        "prior_cc_catalog_fingerprint": None,
    }
    monkeypatch.setattr(
        desktop_operator,
        "load_terminal_editorial_continuity",
        lambda **_kwargs: dict(continuity),
    )
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=store,
        output_root=outputs,
        operating_mode="SHADOW_ONLY",
        clock=lambda: datetime(2026, 8, 17, 14, tzinfo=timezone.utc),
        newsroom_cycle=lambda **_kwargs: {"classification": "NO_PUBLICATION"},
        sidecar_glob=str(sidecar),
    )
    first_refresh = supervisor._refresh_prepared_candidate_checkpoint(
        datetime(2026, 8, 17, 14, tzinfo=timezone.utc)
    )
    assert first_refresh["status"] == "READY"
    checkpoint_path = supervisor._prepared_candidate_checkpoint_path
    earlier = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    earlier_frontier = earlier["prepared_frontier"]
    first_selected = list(earlier_frontier["selected_headline_ids"])
    reserved_for_target = {
        row["headline_id"]
        for row in earlier_frontier["identity_dispositions"]
        if row["disposition"] == "FUTURE_OPPORTUNITY_PROVEN"
        and row["opportunity"]["start_utc"] == "2026-08-17T16:00:00Z"
    }
    assert len(first_selected) == len(reserved_for_target) == 12

    continuity["evaluated_headline_ids"] = first_selected
    continuity["continuity_logical_hash"] = "continuity-at-reserved-target"
    target_cutoff = datetime(2026, 8, 17, 16, 1, tzinfo=timezone.utc)
    target_input = load_rolling_x_headline_sidecars(
        cutoff_utc=target_cutoff,
        sidecar_glob=str(sidecar),
        window_hours=24.0,
    )
    current_ids = list(target_input["unique_headline_ids"])
    urgent_id = next(
        row["headline_id"]
        for row in target_input["headlines"]
        if (row.get("external_content") or {}).get("headline_text")
        == "Controlled newly arrived urgent development"
    )
    current_clusters = [{
        "cluster_id": "raw-urgent-rank-one",
        "rank": 1,
        "headline_ids": [urgent_id],
        "relationship": "distinct",
        "entities_topics": ["urgent"],
    }] + [
        {
            "cluster_id": f"cluster-{headline_id}",
            "rank": index + 2,
            "headline_ids": [headline_id],
            "relationship": "distinct",
            "entities_topics": [headline_id],
        }
        for index, headline_id in enumerate(
            value for value in current_ids if value != urgent_id
        )
    ]
    stale_checkpoint_before = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    rebuilt_rehearsal = build_live_zero_write_rehearsal(
        cutoff_utc=target_cutoff,
        store_path=store,
        output_root=outputs,
        sidecar_glob=str(sidecar),
        cc_root=cc_root,
        current_clusters=current_clusters,
    )
    rebuilt_frontier = rebuilt_rehearsal["prepared_candidate_state_preview"][
        "prepared_frontier"
    ]
    assert rebuilt_rehearsal["prepared_candidate_state_source"] == (
        "REBUILT_FROM_CANONICAL_FRONTIER_INPUTS"
    )
    assert set(rebuilt_frontier["selected_headline_ids"]) == reserved_for_target
    assert urgent_id not in rebuilt_frontier["selected_headline_ids"]
    assert hashlib.sha256(checkpoint_path.read_bytes()).hexdigest() == stale_checkpoint_before

    target_refresh = supervisor._refresh_prepared_candidate_checkpoint(target_cutoff)
    assert target_refresh["status"] == "READY"
    canonical = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    canonical_frontier = canonical["prepared_frontier"]
    assert set(canonical_frontier["selected_headline_ids"]) == reserved_for_target
    assert urgent_id not in canonical_frontier["selected_headline_ids"]
    store_before = hashlib.sha256(store.read_bytes()).hexdigest()
    output_before = {
        path.relative_to(outputs): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in outputs.rglob("*")
        if path.is_file()
    }
    rehearsal = build_live_zero_write_rehearsal(
        cutoff_utc=target_cutoff,
        store_path=store,
        output_root=outputs,
        sidecar_glob=str(sidecar),
        cc_root=cc_root,
        current_clusters=current_clusters,
    )
    rehearsal_frontier = rehearsal["prepared_candidate_state_preview"][
        "prepared_frontier"
    ]

    assert len(current_ids) > 12
    assert rehearsal["prepared_candidate_state_source"] == (
        "REUSED_VALID_CONTINUOUS_CHECKPOINT"
    )
    for key in (
        "selected_headline_ids",
        "deferred_headline_ids",
        "not_promoted_headline_ids",
        "identity_dispositions",
    ):
        assert rehearsal_frontier[key] == canonical_frontier[key]
    assert set(rehearsal_frontier["selected_headline_ids"]) == reserved_for_target
    candidate_ids = set(rehearsal["candidate_or_abstention"]["headline_ids"])
    assert rehearsal["candidate_or_abstention"]["decision"] == (
        "CANDIDATE_FOR_DESKTOP_EDITORIAL_JUDGMENT"
    )
    assert candidate_ids.issubset(rehearsal_frontier["selected_headline_ids"])
    assert urgent_id not in candidate_ids
    assert rehearsal["candidate_universe"]["included_clusters"][0]["cluster_id"] == (
        "raw-urgent-rank-one"
    )
    assert rehearsal["prepared_candidate_count"] == 12
    assert all(
        row["evidence_walk_evaluated"] is False
        for row in rehearsal_frontier["identity_dispositions"]
    )
    assert rehearsal["model_calls"] == rehearsal["provider_calls"] == 0
    assert rehearsal["public_requests"] == rehearsal["public_writes"] == 0
    assert rehearsal["unknown_write_detected"] is False
    assert hashlib.sha256(store.read_bytes()).hexdigest() == store_before
    assert {
        path.relative_to(outputs): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in outputs.rglob("*")
        if path.is_file()
    } == output_before


def test_exact_four_task_packet_has_no_hidden_minimum_or_scale_up():
    packet = four_task_setup_packet()
    assert packet["model"] == COORDINATOR_MODEL == "gpt-5.6-sol"
    assert packet["reasoning_effort"] == COORDINATOR_REASONING_EFFORT == "HIGH"
    assert packet["editorial_worker_model"] == EDITORIAL_WORKER_MODEL == "gpt-5.6-sol"
    assert packet["editorial_worker_reasoning_effort"] == (
        EDITORIAL_WORKER_REASONING_EFFORT
    ) == "XHIGH"
    assert packet["editorial_worker_is_fresh_and_isolated"] is True
    assert packet["editorial_worker_only_when_article_warranted"] is True
    assert packet["routine_task_count"] == 4
    assert packet["publication_minimum"] == 0
    assert packet["automatic_scale_up"] is False
    assert packet["material_event_creates_extra_task"] is False
    assert packet["manual_go_is_explicit_exception"] is True
    assert packet["prompt"] == DESKTOP_TASK_PROMPT
    assert [(row["name"], row["days"], row["time"]) for row in packet["tasks"]] == [
        ("V1 Newsroom — London 1700", "Monday-Friday", "17:00"),
        ("V1 Newsroom — New York 2100", "Monday-Friday", "21:00"),
        ("V1 Newsroom — New York 2300", "Monday-Friday", "23:00"),
        ("V1 Newsroom — New York 0100", "Tuesday-Saturday", "01:00"),
    ]
    assert "fresh V1 Desktop coordinator on exact gpt-5.6-sol / HIGH" in DESKTOP_TASK_PROMPT
    assert "Only when one real candidate has enough governed evidence" in DESKTOP_TASK_PROMPT
    assert "Start one fresh V1 Desktop coordinator on exact gpt-5.6-sol / HIGH" in MANUAL_GO_PROMPT


@pytest.mark.parametrize(
    "opportunity_state",
    [
        "NO_NEW_HEADLINE",
        "DUPLICATE_ONLY",
        "NO_QUALIFIED_CANDIDATE",
        "EVIDENCE_BLOCKED",
        "FULL_DISTRIBUTION_READINESS_BLOCKED",
        "RECOVERY_ONLY",
        "HOUSEKEEPING_ONLY",
        "METRICS_LEARNING_HOUSEKEEPING_ONLY",
    ],
)
def test_no_article_paths_use_high_and_request_zero_xhigh_workers(opportunity_state):
    route = build_editorial_worker_routing_packet(
        opportunity_state=opportunity_state,
    )

    assert route["coordinator"] == {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "HIGH",
        "owns_deterministic_validation_after_return": True,
        "owns_publication_coordination": True,
    }
    assert route["decision"] == "HIGH_ONLY_NO_EDITORIAL_WORKER"
    assert route["xhigh_worker_count_requested"] == 0
    assert route["worker_request"] is None
    assert route["public_write_performed"] is False
    assert route["desktop_bridge_created"] is False
    assert route["scheduler_or_queue_created"] is False


def test_distribution_hold_before_editorial_requests_no_xhigh_worker():
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": {"packet_id": "evidence-1"},
            "exact_source_handles": ["source-1"],
        },
        readiness_checked_before_editorial=True,
        readiness_state="HOLD",
    )

    assert route["opportunity_state"] == "FULL_DISTRIBUTION_READINESS_BLOCKED"
    assert route["decision"] == "HIGH_ONLY_NO_EDITORIAL_WORKER"
    assert route["xhigh_worker_count_requested"] == 0


def test_article_qualified_route_requests_one_fresh_hash_bound_xhigh_worker_and_high_resumes():
    governed_context = {
        "accepted_evidence_packet": {"packet_id": "evidence-1", "status": "ACCEPTED"},
        "exact_source_handles": ["source-1", "source-2"],
        "governed_capital_chronicle_context": {"authority": "READ_ONLY"},
        "active_bounded_learning_policy": {"policy_version": "policy-1"},
        "material_update_context": {"relationship": "material_update"},
        "rights_cleared_media_candidates": [{"asset_id": "asset-1"}],
        "governed_chart_inputs": [{"series_id": "series-1"}],
        "destination_package_constraints": {"substack": {"canonical": True}},
    }
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context=governed_context,
        readiness_checked_before_editorial=True,
        readiness_state="READY",
    )

    worker = route["worker_request"]
    assert route["xhigh_worker_count_requested"] == 1
    assert route["decision"] == "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER"
    assert worker["model"] == "gpt-5.6-sol"
    assert worker["reasoning_effort"] == "XHIGH"
    assert worker["fresh"] is True
    assert worker["isolated"] is True
    assert worker["resume_existing"] is False
    assert worker["governed_input_hash"] == route["governed_input_hash"]
    assert {
        key: value
        for key, value in worker["bounded_governed_context"].items()
        if key != "institutional_edge_editorial_packet"
    } == governed_context
    editorial_packet = worker["bounded_governed_context"][
        "institutional_edge_editorial_packet"
    ]
    assert editorial_packet["voice_id"] == "CAPITAL_CHRONICLE_INSTITUTIONAL_EDGE_V1"
    assert editorial_packet["editorial_packet_sha256"]
    assert editorial_packet["grants_public_write_authority"] is False
    assert worker["max_bounded_editorial_revisions"] == 1
    assert worker["grants_factual_authority"] is False
    assert worker["grants_numeric_authority"] is False
    assert worker["grants_capital_chronicle_authority"] is False
    assert worker["grants_permission_authority"] is False
    assert worker["grants_public_write_authority"] is False
    source_contract = worker["exact_source_marker_contract"]
    assert source_contract["required_for_source_bound_factual_copy"] is True
    assert source_contract["copy_exact_supplied_markers_only"] is True
    assert source_contract["exact_supplied_markers"] == [
        "[[SOURCE:SOURCE_1]]",
        "[[SOURCE:SOURCE_2]]",
    ]
    assert source_contract["source_identity_order"] == ["source-1", "source-2"]
    assert source_contract["marker_format"] == "[[SOURCE:SOURCE_N]]"
    assert source_contract["deterministic_marker_injection_after_authorship"] is False
    assert source_contract["invent_urls_handles_source_ids_evidence_ids_or_facts"] is False
    assert "exact supplied [[SOURCE:SOURCE_N]] markers" in DESKTOP_TASK_PROMPT
    assert "exact supplied [[SOURCE:SOURCE_N]]" in MANUAL_GO_PROMPT

    validated = validate_editorial_worker_return(
        worker_return={
            "governed_input_hash": route["governed_input_hash"],
            "model": "gpt-5.6-sol",
            "reasoning_effort": "XHIGH",
            "fresh": True,
            "isolated": True,
            "bounded_revision_count": 1,
            "public_write_attempted": False,
            "article": {"title": "A publication-quality result"},
        },
        expected_governed_input_hash=route["governed_input_hash"],
    )
    assert validated["coordinator_resumes"] is True
    assert validated["coordinator_reasoning_effort"] == "HIGH"
    assert validated["deterministic_validation_required"] is True
    assert validated["xhigh_publication_authority"] is False
    assert validated["publication_coordinator_remains_sole_public_writer"] is True


def test_xhigh_return_rejects_wrong_hash_second_revision_and_public_write():
    expected_hash = "a" * 64
    with pytest.raises(ValueError, match="input_hash_mismatch"):
        validate_editorial_worker_return(
            worker_return={"governed_input_hash": "b" * 64},
            expected_governed_input_hash=expected_hash,
        )
    with pytest.raises(ValueError, match="revision_limit_exceeded"):
        validate_editorial_worker_return(
            worker_return={
                "governed_input_hash": expected_hash,
                "model": "gpt-5.6-sol", "reasoning_effort": "XHIGH",
                "fresh": True, "isolated": True,
                "bounded_revision_count": 2,
            },
            expected_governed_input_hash=expected_hash,
        )
    with pytest.raises(ValueError, match="public_write_forbidden"):
        validate_editorial_worker_return(
            worker_return={
                "governed_input_hash": expected_hash,
                "model": "gpt-5.6-sol", "reasoning_effort": "XHIGH",
                "fresh": True, "isolated": True,
                "bounded_revision_count": 0,
                "public_write_attempted": True,
            },
            expected_governed_input_hash=expected_hash,
        )


def test_breaking_brief_is_article_qualified_and_requests_exactly_one_xhigh_worker():
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": {
                "packet_id": "breaking-brief-evidence",
                "effective_article_mode": "BREAKING_BRIEF",
            },
            "exact_source_handles": ["source-breaking-1"],
        },
        readiness_checked_before_editorial=True,
        readiness_state="READY",
    )
    assert route["xhigh_worker_count_requested"] == 1
    assert route["worker_request"]["reasoning_effort"] == "XHIGH"


@pytest.mark.parametrize(
    ("product_mode", "projected_mode"),
    [
        ("BREAKING_BRIEF", "BREAKING_BRIEF"),
        ("FOLLOW_UP_UPDATE", "FOLLOW_UP_UPDATE"),
        ("STANDARD_NEWS_ANALYSIS", "STANDARD_ANALYSIS"),
        ("CAPITAL_CHRONICLE_VIEW", "HOUSE_VIEW"),
        ("WHAT_THE_MARKET_IS_MISSING", "HOUSE_VIEW"),
        ("EVERGREEN_EXPLAINER", "EXPLAINER"),
        ("DATA_OR_DOCUMENT_LENS", "DOCUMENT_LENS"),
        ("WEEK_AHEAD_OR_WATCH", "WEEK_AHEAD_WATCH"),
    ],
)
def test_routing_packet_preserves_canonical_product_mode_semantics(
    product_mode, projected_mode
):
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": {"packet_id": "mode-contract-evidence"},
            "exact_source_handles": ["source-mode-1"],
        },
        readiness_checked_before_editorial=True,
        readiness_state="READY",
        article_mode=product_mode,
    )

    worker = route["worker_request"]
    editorial_packet = worker["bounded_governed_context"][
        "institutional_edge_editorial_packet"
    ]
    assert editorial_packet["article_mode"] == projected_mode
    assert editorial_packet["mode_expectations"]
    assert worker["grants_factual_authority"] is False
    assert worker["grants_numeric_authority"] is False
    assert worker["grants_capital_chronicle_authority"] is False
    assert worker["grants_permission_authority"] is False
    assert worker["grants_public_write_authority"] is False


def test_active_policy_sections_reach_next_desktop_briefing(tmp_path):
    store = tmp_path / "store.sqlite3"
    _create_store(store)
    payload = {
        "timing": {"applied_offset_minutes": 0, "recommended_offset_minutes": 15,
                   "owner_locked": True},
        "content": {"recommendations": [{"field": "story_type", "value": "FOLLOW_UP"}]},
        "seo": {"recommendations": [{"field": "primary_search_intent", "value": "EXPLAIN"}]},
        "package": {"by_destination": {"x": {"copy_form": "THREAD"}}},
    }
    connection = sqlite3.connect(store)
    connection.execute(
        "INSERT INTO learning_policy_versions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "policy.learned.test", "policy.bootstrap.v1", "2026-08-16T05:00:00Z", "ACTIVE",
            "ACCEPT_BOUNDED_UPDATE", 8, 0.8, "qualified_engagement.formula.v1", "[]", "w",
            "{}", "{}", None, "bounded_improvement", json.dumps(payload), "hash",
        ),
    )
    connection.commit()
    connection.close()

    continuity = load_terminal_editorial_continuity(store_path=store, output_root=tmp_path / "out")
    active = continuity["active_learning_policy"]

    assert active["policy_version"] == "policy.learned.test"
    assert active["sample_count"] == 8
    assert active["confidence"] == 0.8
    assert active["timing"]["owner_locked"] is True
    assert active["content"] == payload["content"]
    assert active["seo"] == payload["seo"]
    assert active["package"] == payload["package"]
    assert active["grants_factual_or_numeric_authority"] is False
    assert active["grants_publication_authority"] is False
