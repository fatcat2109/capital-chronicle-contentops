"""Read-only continuity view for one native Codex Desktop V1 editorial opportunity.

This module is deliberately not a scheduler, newsroom, state store, publisher, model bridge, or
CLI.  It reconstructs the latest terminal editorial cutoff from the existing durable store and
cycle artifacts, filters current intake by durable identities, refreshes the read-only Capital
Chronicle estate, and returns a bounded zero-write briefing for a fresh Desktop task.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence
from urllib.parse import urlsplit

from live_contentops.capital_chronicle_data_catalog_v1 import (
    DEFAULT_CC_ROOT,
    discover_cc_data_estate,
    inspect_governed_cc_surfaces,
    query_story_scoped_cc_context,
)
from live_contentops.daily_app_launcher_v1 import (
    CANONICAL_PRODUCTION_OUTPUT_ROOT,
    CANONICAL_PRODUCTION_STORE_PATH,
)
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob
from live_contentops.newsroom_assignment_scheduler_v1 import (
    load_rolling_x_headline_sidecars,
)

SCHEMA_VERSION = "contentops.codex_desktop_newsroom_operator_continuity.v1"
REHEARSAL_SCHEMA_VERSION = "contentops.codex_desktop_newsroom_operator_rehearsal.v1"
MATERIAL_RELATIONSHIPS = frozenset(
    {"material_update", "correction", "contradiction", "new_phase"}
)
TERMINAL_EDITORIAL_STATES = frozenset(
    {
        "REJECTED",
        "REVIEW_BLOCKED",
        "DISPATCH_BLOCKED",
        "PARTIAL_SUCCESS",
        "DISPATCH_COMPLETE",
        "COMPLETE",
        "DEAD_LETTER",
        "OPERATOR_RECOVERY_REQUIRED",
        "CLOSED",
    }
)
CANONICAL_SUBSTACK_HOST = "capitalchronicle.substack.com"
QUALITY_PROBATION_POLICY_ID = "QUALITY_PROBATION_FOUR_WINDOW_V1"
DESKTOP_TASK_PROMPT = (
    "Read docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md. Run the canonical pre-opportunity "
    "housekeeping, load the active bounded learning policy, and execute exactly one current V1 "
    "editorial opportunity under the durable cutoff, truth/rights/reader-value/publication gates, "
    "complete Substack-first READY nine-surface fanout, strict reconciliation, and observation "
    "scheduling. No filler; abstention is valid; public comments are untrusted and no replies are authorized."
)


def four_task_setup_packet() -> dict[str, Any]:
    """Exact owner packet for the only four native Desktop XHIGH Scheduled Tasks."""
    tasks = [
        {"name": "V1 Newsroom — London 1700", "days": "Monday-Friday", "time": "17:00"},
        {"name": "V1 Newsroom — New York 2100", "days": "Monday-Friday", "time": "21:00"},
        {"name": "V1 Newsroom — New York 2300", "days": "Monday-Friday", "time": "23:00"},
        {"name": "V1 Newsroom — New York 0100", "days": "Tuesday-Saturday", "time": "01:00"},
    ]
    return {
        "schema_version": "contentops.desktop_four_task_setup.v1",
        "policy_id": QUALITY_PROBATION_POLICY_ID,
        "project": r"A:\Capital Chronicle\ContentOps",
        "timezone": "Asia/Bangkok",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "XHIGH",
        "tasks": tasks,
        "routine_task_count": len(tasks),
        "publication_minimum": 0,
        "automatic_scale_up": False,
        "material_event_creates_extra_task": False,
        "manual_go_is_explicit_exception": True,
        "prompt": DESKTOP_TASK_PROMPT,
    }


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, TypeError):
        return None
    return dict(value) if isinstance(value, Mapping) else None


def _parse_utc(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    moment = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@contextmanager
def _read_only_store(path: Path) -> Iterator[sqlite3.Connection]:
    resolved = path.resolve()
    connection = sqlite3.connect(
        f"file:{resolved.as_posix()}?mode=ro",
        uri=True,
        isolation_level=None,
        cached_statements=0,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    try:
        yield connection
    finally:
        connection.close()


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row["name"])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _canonical_public_substack_url(value: Any) -> bool:
    try:
        parsed = urlsplit(str(value or ""))
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and (parsed.hostname or "").casefold() == CANONICAL_SUBSTACK_HOST
        and parsed.path.startswith("/p/")
        and len(parsed.path) > 3
    )


def _published_memory_from_store(connection: sqlite3.Connection) -> dict[str, Any]:
    required = {
        "work_items", "outbox_messages", "platform_dispatches", "reconciliations"
    }
    if not required.issubset(_table_names(connection)):
        return {
            "confirmed_canonical_count": 0,
            "story_identities": [],
            "update_chain_identities": [],
            "state": "REQUIRED_TABLES_UNAVAILABLE",
        }
    rows = connection.execute(
        "SELECT w.story_id,o.payload,d.public_object_url,r.status AS reconciliation_status "
        "FROM work_items w JOIN outbox_messages o ON o.work_item_id=w.work_item_id "
        "JOIN platform_dispatches d ON d.message_id=o.message_id "
        "JOIN reconciliations r ON r.work_item_id=w.work_item_id "
        "WHERE o.destination='substack' AND d.platform='substack' "
        "AND r.status='RECONCILED_CONFIRMED'"
    ).fetchall()
    story_ids: set[str] = set()
    chain_ids: set[str] = set()
    object_urls: set[str] = set()
    for row in rows:
        public_url = str(row["public_object_url"] or "")
        if not _canonical_public_substack_url(public_url):
            continue
        object_urls.add(public_url)
        payload: Mapping[str, Any] = {}
        try:
            parsed_payload = json.loads(str(row["payload"] or "{}"))
            if isinstance(parsed_payload, Mapping):
                payload = parsed_payload
        except (TypeError, ValueError):
            pass
        story_identity = str(payload.get("story_identity") or "").strip()
        update_chain_identity = str(payload.get("update_chain_identity") or "").strip()
        if story_identity:
            story_ids.add(story_identity)
        if update_chain_identity:
            chain_ids.add(update_chain_identity)
    return {
        "confirmed_canonical_count": len(object_urls),
        "story_identities": sorted(story_ids),
        "update_chain_identities": sorted(chain_ids),
        "canonical_url_hashes": sorted(
            hashlib.sha256(value.encode("utf-8")).hexdigest() for value in object_urls
        ),
        "state": "READ_ONLY_DURABLE_RECONCILED_SUBSTACK_MEMORY",
    }


def _active_learning_policy_from_store(connection: sqlite3.Connection) -> dict[str, Any]:
    from live_contentops.daily_app_performance_v1 import (
        BOOTSTRAP_POLICY_VERSION,
        QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
        _bootstrap_policy_payload,
        _normalized_policy_payload,
    )

    if "learning_policy_versions" not in _table_names(connection):
        payload = _bootstrap_policy_payload()
        return {
            "policy_version": BOOTSTRAP_POLICY_VERSION,
            "decision": "CONFIGURED_DEFAULT",
            "sample_count": 0,
            "confidence": 0.0,
            "formula_version": QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
            "timing": payload["timing"],
            "content": payload["content"],
            "seo": payload["seo"],
            "package": payload["package"],
            "grants_factual_or_numeric_authority": False,
            "grants_publication_authority": False,
        }
    row = connection.execute(
        "SELECT * FROM learning_policy_versions WHERE status='ACTIVE' "
        "ORDER BY created_at_utc DESC,policy_version DESC LIMIT 1"
    ).fetchone()
    if row is None:
        payload = _bootstrap_policy_payload()
        return {
            "policy_version": BOOTSTRAP_POLICY_VERSION,
            "decision": "CONFIGURED_DEFAULT",
            "sample_count": 0,
            "confidence": 0.0,
            "formula_version": QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
            "timing": payload["timing"],
            "content": payload["content"],
            "seo": payload["seo"],
            "package": payload["package"],
            "grants_factual_or_numeric_authority": False,
            "grants_publication_authority": False,
        }
    try:
        payload = _normalized_policy_payload(
            dict(json.loads(str(row["policy_payload_json"] or "{}")))
        )
    except (TypeError, ValueError):
        payload = _bootstrap_policy_payload()
    return {
        "policy_version": str(row["policy_version"]),
        "parent_policy_version": row["parent_policy_version"],
        "decision": str(row["decision"]),
        "decision_reason": str(row["decision_reason"]),
        "sample_count": int(row["sample_count"]),
        "confidence": float(row["confidence"]),
        "formula_version": str(row["formula_version"]),
        "timing": dict(payload.get("timing") or {}),
        "content": dict(payload.get("content") or {}),
        "seo": dict(payload.get("seo") or {}),
        "package": dict(payload.get("package") or {}),
        "grants_factual_or_numeric_authority": False,
        "grants_publication_authority": False,
    }


def load_terminal_editorial_continuity(
    *,
    store_path: str | Path = CANONICAL_PRODUCTION_STORE_PATH,
    output_root: str | Path = CANONICAL_PRODUCTION_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Reconstruct cutoff/evaluated/publication memory without modifying the canonical store."""
    store = Path(store_path)
    outputs = Path(output_root)
    base: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "store_path": str(store.resolve()),
        "output_root": str(outputs.resolve()),
        "store_open_mode": "SQLITE_URI_MODE_RO_QUERY_ONLY",
        "database_writes_performed": False,
        "filesystem_writes_performed": False,
        "parallel_state_authority_created": False,
    }
    if not store.is_file():
        from live_contentops.daily_app_performance_v1 import (
            BOOTSTRAP_POLICY_VERSION,
            _bootstrap_policy_payload,
        )
        bootstrap_payload = _bootstrap_policy_payload()
        result = {
            **base,
            "state": "CANONICAL_STORE_MISSING",
            "last_terminal_cutoff_utc": None,
            "terminal_window_id": None,
            "evaluated_headline_ids": [],
            "evaluated_update_chain_identities": [],
            "published_memory": {
                "confirmed_canonical_count": 0,
                "story_identities": [],
                "update_chain_identities": [],
                "state": "CANONICAL_STORE_MISSING",
            },
            "active_learning_policy": {
                "policy_version": BOOTSTRAP_POLICY_VERSION,
                "decision": "CONFIGURED_DEFAULT",
                "sample_count": 0,
                "confidence": 0.0,
                "timing": bootstrap_payload["timing"],
                "content": bootstrap_payload["content"],
                "seo": bootstrap_payload["seo"],
                "package": bootstrap_payload["package"],
                "grants_factual_or_numeric_authority": False,
                "grants_publication_authority": False,
            },
            "prior_cc_catalog_fingerprint": None,
        }
        result["continuity_logical_hash"] = _logical_hash(result)
        return result

    with _read_only_store(store) as connection:
        tables = _table_names(connection)
        if "work_items" not in tables:
            raise ValueError("desktop_continuity_work_items_table_missing")
        placeholders = ",".join("?" for _ in TERMINAL_EDITORIAL_STATES)
        rows = connection.execute(
            "SELECT work_item_id,current_state,updated_at FROM work_items "
            "WHERE target_surface IN "
            "('daily_app_editorial_window','daily_app_material_event_window') "
            f"AND current_state IN ({placeholders}) "
            "ORDER BY updated_at DESC,work_item_id DESC",
            tuple(sorted(TERMINAL_EDITORIAL_STATES)),
        ).fetchall()
        published_memory = _published_memory_from_store(connection)
        active_learning_policy = _active_learning_policy_from_store(connection)

    evaluated_ids: set[str] = set()
    evaluated_chains: set[str] = set()
    terminal_records: list[dict[str, Any]] = []
    published_story_ids = set(published_memory.get("story_identities") or [])
    published_chain_ids = set(published_memory.get("update_chain_identities") or [])
    for row in rows:
        window_id = str(row["work_item_id"])
        output_dir = outputs / window_id
        intake = _read_json_object(output_dir / "rolling_x_intake_v1.json")
        evidence = _read_json_object(
            output_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
        )
        if not intake or not evidence:
            continue
        cutoff = _parse_utc(intake.get("cutoff_time_utc"))
        headline_ids = {
            str(value) for value in (intake.get("unique_headline_ids") or []) if str(value)
        }
        if cutoff is None or not headline_ids:
            continue
        evaluated_ids.update(headline_ids)
        assignment = _read_json_object(output_dir / "rolling_x_assignment_v1.json") or {}
        for cluster in assignment.get("ranked_clusters") or []:
            if not isinstance(cluster, Mapping):
                continue
            chain = str(
                cluster.get("update_chain_identity") or cluster.get("cluster_id") or ""
            ).strip()
            if chain:
                evaluated_chains.add(chain)
        memory_proof = _read_json_object(
            output_dir / "published_memory_cycle_proof_v1.json"
        ) or {}
        observed = memory_proof.get("canonical_article_observed_after_lifecycle") or {}
        if isinstance(observed, Mapping):
            story_identity = str(observed.get("story_identity") or "").strip()
            update_chain_identity = str(
                observed.get("update_chain_identity") or ""
            ).strip()
            if story_identity:
                published_story_ids.add(story_identity)
            if update_chain_identity:
                published_chain_ids.add(update_chain_identity)
        portfolio = _read_json_object(output_dir / "editorial_portfolio_context_v1.json") or {}
        cc_model = portfolio.get("capital_chronicle_read_model") or {}
        terminal_records.append({
            "window_id": window_id,
            "terminal_state": str(row["current_state"]),
            "updated_at_utc": str(row["updated_at"]),
            "cutoff_utc": _iso_utc(cutoff),
            "classification": evidence.get("classification"),
            "evaluated_headline_count": len(headline_ids),
            "cc_catalog_fingerprint": cc_model.get("catalog_fingerprint")
            if isinstance(cc_model, Mapping) else None,
        })
    terminal_records.sort(
        key=lambda value: (
            _parse_utc(value.get("cutoff_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            str(value.get("window_id") or ""),
        ),
        reverse=True,
    )
    latest = terminal_records[0] if terminal_records else None
    published_memory = {
        **published_memory,
        "story_identities": sorted(published_story_ids),
        "update_chain_identities": sorted(published_chain_ids),
    }
    result = {
        **base,
        "state": "READY" if latest else "NO_PRIOR_TERMINAL_EDITORIAL_WINDOW",
        "last_terminal_cutoff_utc": latest.get("cutoff_utc") if latest else None,
        "terminal_window_id": latest.get("window_id") if latest else None,
        "terminal_state": latest.get("terminal_state") if latest else None,
        "terminal_classification": latest.get("classification") if latest else None,
        "terminal_record_count": len(terminal_records),
        "evaluated_headline_ids": sorted(evaluated_ids),
        "evaluated_headline_count": len(evaluated_ids),
        "evaluated_update_chain_identities": sorted(evaluated_chains),
        "published_memory": published_memory,
        "active_learning_policy": active_learning_policy,
        "prior_cc_catalog_fingerprint": latest.get("cc_catalog_fingerprint")
        if latest else None,
    }
    result["continuity_logical_hash"] = _logical_hash(result)
    return result


def _cluster_relationship(cluster: Mapping[str, Any]) -> str:
    for container in (
        cluster.get("update_chain"),
        cluster.get("duplicate_update_chain"),
    ):
        if isinstance(container, Mapping) and container.get("relationship"):
            return str(container["relationship"]).casefold()
    return str(cluster.get("relationship") or "distinct").casefold()


def classify_desktop_candidate_universe(
    *,
    current_headlines: Sequence[Mapping[str, Any]],
    current_clusters: Sequence[Mapping[str, Any]],
    continuity: Mapping[str, Any],
) -> dict[str, Any]:
    """Include unseen identity or governed material delta; hold unchanged/published repeats."""
    rows_by_id: dict[str, dict[str, Any]] = {}
    duplicate_current_ids: set[str] = set()
    for value in current_headlines:
        headline_id = str(value.get("headline_id") or "")
        if not headline_id:
            raise ValueError("desktop_candidate_headline_id_missing")
        if headline_id in rows_by_id:
            duplicate_current_ids.add(headline_id)
            continue
        rows_by_id[headline_id] = dict(value)
    evaluated_ids = {
        str(value) for value in (continuity.get("evaluated_headline_ids") or [])
    }
    published = continuity.get("published_memory") or {}
    published_story_ids = {
        str(value) for value in (published.get("story_identities") or [])
    }
    published_chain_ids = {
        str(value) for value in (published.get("update_chain_identities") or [])
    }
    last_cutoff = _parse_utc(continuity.get("last_terminal_cutoff_utc"))
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    assigned_ids: set[str] = set()
    for position, value in enumerate(current_clusters, start=1):
        cluster = dict(value)
        cluster_id = str(cluster.get("cluster_id") or f"desktop-cluster-{position}")
        headline_ids = [str(item) for item in (cluster.get("headline_ids") or [])]
        if not headline_ids or any(item not in rows_by_id for item in headline_ids):
            raise ValueError("desktop_candidate_cluster_binding_invalid")
        if assigned_ids.intersection(headline_ids):
            raise ValueError("desktop_candidate_headline_assigned_twice")
        assigned_ids.update(headline_ids)
        relationship = _cluster_relationship(cluster)
        material_update = relationship in MATERIAL_RELATIONSHIPS
        unseen_ids = sorted(set(headline_ids) - evaluated_ids)
        chain_identity = str(
            cluster.get("update_chain_identity") or cluster_id
        )
        published_match = (
            cluster_id in published_story_ids or chain_identity in published_chain_ids
        )
        source_times = [
            _parse_utc(rows_by_id[item].get("source_timestamp_utc"))
            for item in headline_ids
        ]
        late_unseen = sorted(
            item for item in unseen_ids
            if last_cutoff is not None
            and (_parse_utc(rows_by_id[item].get("source_timestamp_utc")) or last_cutoff)
            <= last_cutoff
        )
        record = {
            "cluster_id": cluster_id,
            "update_chain_identity": chain_identity,
            "relationship": relationship,
            "headline_ids": headline_ids,
            "unseen_headline_ids": unseen_ids,
            "late_arriving_unseen_headline_ids": late_unseen,
            "published_memory_match": published_match,
            "source_timestamp_max_utc": _iso_utc(max(
                value for value in source_times if value is not None
            )) if any(value is not None for value in source_times) else None,
            "rank": int(cluster.get("rank") or position),
            "entities_topics": list(cluster.get("entities_topics") or []),
        }
        if published_match and not material_update:
            record["decision"] = "EXCLUDE_PUBLISHED_WITHOUT_MATERIAL_DELTA"
            excluded.append(record)
        elif material_update:
            record["decision"] = "INCLUDE_MATERIAL_UPDATE_CHAIN"
            included.append(record)
        elif unseen_ids:
            record["decision"] = "INCLUDE_UNSEEN_HEADLINE_IDENTITY"
            included.append(record)
        else:
            record["decision"] = "EXCLUDE_UNCHANGED_PREVIOUSLY_EVALUATED"
            excluded.append(record)
    included.sort(key=lambda value: (
        0 if value["decision"] == "INCLUDE_MATERIAL_UPDATE_CHAIN" else 1,
        int(value["rank"]),
        str(value["cluster_id"]),
    ))
    result = {
        "schema_version": "contentops.codex_desktop_candidate_universe.v1",
        "current_unique_headline_count": len(rows_by_id),
        "current_duplicate_headline_ids": sorted(duplicate_current_ids),
        "evaluated_headline_count": len(evaluated_ids),
        "included_clusters": included,
        "excluded_clusters": excluded,
        "included_cluster_count": len(included),
        "material_update_cluster_count": sum(
            row["decision"] == "INCLUDE_MATERIAL_UPDATE_CHAIN" for row in included
        ),
        "unseen_headline_ids": sorted({
            item for row in included for item in row["unseen_headline_ids"]
        }),
        "late_arriving_unseen_headline_ids": sorted({
            item for row in included for item in row["late_arriving_unseen_headline_ids"]
        }),
        "unchanged_or_published_excluded_count": len(excluded),
        "timestamp_only_filter_used": False,
        "publication_authority_granted": False,
    }
    result["candidate_universe_logical_hash"] = _logical_hash(result)
    return result


def build_live_zero_write_rehearsal(
    *,
    cutoff_utc: datetime | str | None = None,
    store_path: str | Path = CANONICAL_PRODUCTION_STORE_PATH,
    output_root: str | Path = CANONICAL_PRODUCTION_OUTPUT_ROOT,
    sidecar_glob: str = canonical_headline_sidecar_glob(),
    cc_root: str | Path = DEFAULT_CC_ROOT,
    current_clusters: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one real-state, bounded, read-only opportunity rehearsal; never execute a write."""
    if cutoff_utc is None:
        cutoff = datetime.now(timezone.utc)
    elif isinstance(cutoff_utc, datetime):
        cutoff = cutoff_utc
    else:
        cutoff = _parse_utc(cutoff_utc)
        if cutoff is None:
            raise ValueError("desktop_rehearsal_cutoff_invalid")
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    cutoff = cutoff.astimezone(timezone.utc)
    continuity = load_terminal_editorial_continuity(
        store_path=store_path, output_root=output_root
    )
    current_input = load_rolling_x_headline_sidecars(
        cutoff_utc=cutoff,
        sidecar_glob=sidecar_glob,
        window_hours=24.0,
    )
    headlines = list(current_input.get("headlines") or [])
    if current_clusters is None:
        ordered = sorted(
            headlines,
            key=lambda row: (
                str(row.get("source_timestamp_utc") or ""),
                str(row.get("headline_id") or ""),
            ),
            reverse=True,
        )
        clusters = [
            {
                "cluster_id": "desktop-unclustered-" + str(row["headline_id"]),
                "rank": index,
                "headline_ids": [str(row["headline_id"])],
                "relationship": "distinct",
                "entities_topics": [],
            }
            for index, row in enumerate(ordered, start=1)
        ]
    else:
        clusters = [dict(value) for value in current_clusters]
    universe = classify_desktop_candidate_universe(
        current_headlines=headlines,
        current_clusters=clusters,
        continuity=continuity,
    )
    catalog = discover_cc_data_estate(cc_root=cc_root, use_cache=False)
    governed = inspect_governed_cc_surfaces(catalog)
    selected = next(iter(universe.get("included_clusters") or []), None)
    entities: list[str] = []
    if selected:
        entities = [str(value) for value in (selected.get("entities_topics") or [])]
        if not entities:
            selected_id = next(iter(selected.get("headline_ids") or []), None)
            selected_row = next(
                (row for row in headlines if row.get("headline_id") == selected_id), {}
            )
            headline_text = str(
                (selected_row.get("external_content") or {}).get("headline_text") or ""
            ).strip()
            if headline_text:
                entities = [headline_text]
    cc_context = query_story_scoped_cc_context(catalog, entities) if entities else {
        "schema_version": "contentops.story_scoped_cc_context.v2",
        "queried_entities": [],
        "matches": [],
        "catalog_fingerprint": catalog.get("catalog_fingerprint"),
        "grants_factual_or_numeric_authority": False,
        "mutated_upstream": False,
    }
    prior_fingerprint = continuity.get("prior_cc_catalog_fingerprint")
    current_fingerprint = catalog.get("catalog_fingerprint")
    result = {
        "schema_version": REHEARSAL_SCHEMA_VERSION,
        "cutoff_utc": _iso_utc(cutoff),
        "continuity": continuity,
        "current_intake": {
            "canonical_input_hash": current_input.get("canonical_input_hash"),
            "headline_count": int((current_input.get("counts") or {}).get("accepted") or 0),
            "deduplicated_input_count": int(
                (current_input.get("counts") or {}).get("duplicates") or 0
            ),
        },
        "candidate_universe": universe,
        "active_learning_policy": continuity.get("active_learning_policy"),
        "learning_policy_consumed_by_next_opportunity": True,
        "learning_policy_grants_factual_or_numeric_authority": False,
        "candidate_or_abstention": (
            {
                "decision": "CANDIDATE_FOR_DESKTOP_EDITORIAL_JUDGMENT",
                "cluster_id": selected.get("cluster_id"),
                "headline_ids": selected.get("headline_ids"),
                "relationship": selected.get("relationship"),
            }
            if selected else {"decision": "ABSTAIN_NO_CURRENT_UNSEEN_OR_MATERIAL_UPDATE"}
        ),
        "capital_chronicle": {
            "root": str(Path(cc_root).resolve()),
            "store_count_total": catalog.get("store_count_total"),
            "store_count_discovered": catalog.get("store_count_discovered"),
            "discovery_complete": catalog.get("discovery_complete"),
            "connection_mode": catalog.get("connection_mode"),
            "catalog_fingerprint": current_fingerprint,
            "prior_terminal_catalog_fingerprint": prior_fingerprint,
            "catalog_changed_since_prior_terminal": (
                None if not prior_fingerprint else prior_fingerprint != current_fingerprint
            ),
            "cache_state": (catalog.get("cache") or {}).get("state"),
            "governed_surfaces": governed,
            "story_scoped_context": cc_context,
            "arbitrary_database_context_grants_authority": False,
        },
        "next_terminal_cutoff_constructible": True,
        "next_terminal_cutoff_utc": _iso_utc(cutoff),
        "database_writes_performed": False,
        "filesystem_writes_performed": False,
        "provider_or_model_calls": 0,
        "public_writes": 0,
        "publication_coordinator_sole_public_writer_unchanged": True,
        "v2_mutations": 0,
    }
    result["rehearsal_logical_hash"] = _logical_hash(result)
    return result
