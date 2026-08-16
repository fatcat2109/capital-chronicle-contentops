import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_data_catalog_v1 import (
    _CATALOG_CACHE,
    discover_cc_data_estate,
    inspect_governed_cc_surfaces,
    query_story_scoped_cc_context,
)
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    DESKTOP_TASK_PROMPT,
    build_live_zero_write_rehearsal,
    classify_desktop_candidate_universe,
    four_task_setup_packet,
    load_terminal_editorial_continuity,
)


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
        cutoff="2026-08-16T04:00:00Z",
        headline_ids=["h-unrelated-prior"],
        updated_at="2026-08-16T04:10:00Z",
        catalog_fingerprint="catalog-prior",
    )
    (sidecars / "step1_headline_sidecar_2026_08_16.jsonl").write_text(
        json.dumps({
            "tweet_id": "live-1",
            "timestamp": "2026-08-16T05:00:00Z",
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
        cutoff_utc="2026-08-16T06:00:00Z",
        store_path=store,
        output_root=outputs,
        sidecar_glob=str(sidecars / "*.jsonl"),
        cc_root=cc_root,
    )

    assert rehearsal["continuity"]["last_terminal_cutoff_utc"] == "2026-08-16T04:00:00Z"
    assert rehearsal["current_intake"]["headline_count"] == 1
    assert rehearsal["candidate_or_abstention"]["decision"] == (
        "CANDIDATE_FOR_DESKTOP_EDITORIAL_JUDGMENT"
    )
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


def test_exact_four_task_packet_has_no_hidden_minimum_or_scale_up():
    packet = four_task_setup_packet()
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
