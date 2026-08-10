"""Read-only Capital Chronicle data catalog / read model for ContentOps editorial intelligence.

Owner decision 2026-08-10 (V1 realignment): ContentOps uses the actual current Capital
Chronicle data estate through a direct READ-ONLY catalog/query boundary. Capital Chronicle
remains analytical/numeric authority where exact article contracts require it; this module is an
adapter into existing authority, NOT a new analytical engine, and it NEVER mutates upstream.

Two distinct editorial uses:

A. EDITORIAL INTELLIGENCE - context richness, related datasets/analysis, novelty, ranking;
B. FACTUAL/ANALYTICAL AUTHORITY - only via the existing governed Capital Chronicle authority
   surfaces (cc_evidence_bridge_v2 packet contracts), never by promoting arbitrary DB rows.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

CATALOG_SCHEMA_VERSION = "contentops.capital_chronicle_data_catalog.v1"
DEFAULT_CC_ROOT = Path(r"A:\Capital Chronicle\Main App")
LOCAL_DB_SUBPATH = Path("data") / "local_db"
PUBLICATION_EVIDENCE_SUBPATH = Path("docs/research/publication_evidence/current/CapitalChroniclePublicationEvidencePacketV1.json")
NEWSROOM_POOL_SUBPATH = Path("docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json")
MAX_STORES = 12
MAX_TABLES_PER_STORE = 60
MAX_PROBED_TABLES = 10
STORY_QUERY_ENTITY_LIMIT = 4
STORY_QUERY_ROWS_PER_ENTITY = 5
READ_ONLY_SQL_GUARD = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)


class CapitalChronicleCatalogError(RuntimeError):
    pass


def _open_readonly(store_path: Path):
    import duckdb

    return duckdb.connect(str(store_path), read_only=True)


def _looks_like_timestamp_column(column: str) -> bool:
    lowered = str(column).lower()
    return any(marker in lowered for marker in ("date", "time", "as_of", "known_at", "recorded", "_at"))


def discover_cc_data_estate(
    *,
    cc_root: str | Path = DEFAULT_CC_ROOT,
    max_stores: int = MAX_STORES,
) -> dict[str, Any]:
    """Compact read-only discovery of the current Capital Chronicle data estate. No raw dumps."""
    root = Path(cc_root)
    catalog: dict[str, Any] = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "cc_root": str(root),
        "root_exists": root.is_dir(),
        "stores": [],
        "governed_surfaces": {},
        "mutated_upstream": False,
        "connection_mode": "duckdb_read_only",
    }
    if not root.is_dir():
        return catalog
    publication_packet = root / PUBLICATION_EVIDENCE_SUBPATH
    newsroom_pool = root / NEWSROOM_POOL_SUBPATH
    catalog["governed_surfaces"] = {
        "publication_evidence_packet": {
            "path": str(publication_packet),
            "exists": publication_packet.is_file(),
            "role": "governed_publication_authority_surface",
        },
        "newsroom_candidate_pool": {
            "path": str(newsroom_pool),
            "exists": newsroom_pool.is_file(),
            "role": "governed_newsroom_pool_surface",
        },
    }
    local_db_dir = root / LOCAL_DB_SUBPATH
    if not local_db_dir.is_dir():
        return catalog
    store_paths = sorted(local_db_dir.glob("*.duckdb"))[:max_stores]
    for store_path in store_paths:
        store_entry: dict[str, Any] = {
            "store_id": store_path.stem,
            "path": str(store_path),
            "type": "duckdb",
            "opened_read_only": False,
            "table_count": 0,
            "tables": [],
        }
        try:
            connection = _open_readonly(store_path)
        except Exception as exc:  # noqa: BLE001
            store_entry["open_error"] = type(exc).__name__
            catalog["stores"].append(store_entry)
            continue
        try:
            store_entry["opened_read_only"] = True
            table_names = [
                str(row[0])
                for row in connection.execute(
                    "SELECT table_name FROM information_schema.tables ORDER BY table_name"
                ).fetchall()
            ][:MAX_TABLES_PER_STORE]
            store_entry["table_count"] = len(table_names)
            for table_name in table_names[:MAX_PROBED_TABLES]:
                table_entry: dict[str, Any] = {"table": table_name}
                try:
                    columns = [
                        str(row[0])
                        for row in connection.execute(
                            "SELECT column_name FROM information_schema.columns WHERE table_name=?",
                            [table_name],
                        ).fetchall()
                    ]
                    table_entry["column_count"] = len(columns)
                    table_entry["row_count"] = int(
                        connection.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
                    )
                    timestamp_columns = [column for column in columns if _looks_like_timestamp_column(column)]
                    table_entry["timestamp_columns"] = timestamp_columns[:4]
                    if timestamp_columns:
                        try:
                            latest = connection.execute(
                                f'SELECT MAX("{timestamp_columns[0]}") FROM "{table_name}"'
                            ).fetchone()[0]
                            table_entry["latest_observation"] = str(latest) if latest is not None else None
                        except Exception:  # noqa: BLE001
                            table_entry["latest_observation"] = None
                    table_entry["semantic_fields"] = [
                        column
                        for column in columns
                        if any(
                            marker in column.lower()
                            for marker in ("entity", "instrument", "topic", "dqr", "authority", "lineage", "source", "status", "quality")
                        )
                    ][:8]
                except Exception as exc:  # noqa: BLE001
                    table_entry["probe_error"] = type(exc).__name__
                store_entry["tables"].append(table_entry)
        finally:
            connection.close()
        catalog["stores"].append(store_entry)
    return catalog


def _candidate_search_tables(store_entry: Mapping[str, Any]) -> list[str]:
    tables = []
    for table in store_entry.get("tables") or []:
        name = str(table.get("table") or "")
        if any(marker in name for marker in ("entity", "event", "document", "record")):
            tables.append(name)
    return tables[:3]


def query_story_scoped_cc_context(
    catalog: Mapping[str, Any],
    entities: Sequence[str],
    *,
    max_rows_per_entity: int = STORY_QUERY_ROWS_PER_ENTITY,
) -> dict[str, Any]:
    """Bounded story-scoped read: which Capital Chronicle surfaces hold relevant context.

    Returns compact identity/freshness pointers only - never full table dumps. Read-only."""
    import duckdb

    normalized_entities: list[str] = []
    for entity in entities:
        text = str(entity or "").strip()
        if text and text not in normalized_entities:
            normalized_entities.append(text)
    normalized_entities = normalized_entities[:STORY_QUERY_ENTITY_LIMIT]
    matches: list[dict[str, Any]] = []
    richness_total = 0.0
    for store_entry in catalog.get("stores") or []:
        if not store_entry.get("opened_read_only"):
            continue
        search_tables = _candidate_search_tables(store_entry)
        if not search_tables:
            continue
        try:
            connection = duckdb.connect(str(store_entry["path"]), read_only=True)
        except Exception:  # noqa: BLE001
            continue
        try:
            for table_name in search_tables:
                try:
                    columns = [
                        str(row[0])
                        for row in connection.execute(
                            "SELECT column_name FROM information_schema.columns WHERE table_name=?",
                            [table_name],
                        ).fetchall()
                    ]
                except Exception:  # noqa: BLE001
                    continue
                text_column = next(
                    (column for column in columns if column.lower() in {"display_name", "name", "canonical_name", "title", "text", "headline", "summary"}),
                    None,
                )
                if text_column is None:
                    continue
                for entity in normalized_entities:
                    safe_entity = entity.replace("'", "''")
                    sql = (
                        f'SELECT COUNT(*) FROM "{table_name}" '
                        f"WHERE LOWER(CAST(\"{text_column}\" AS VARCHAR)) LIKE LOWER(?) LIMIT 1"
                    )
                    if not READ_ONLY_SQL_GUARD.match(sql):
                        raise CapitalChronicleCatalogError("read_only_sql_guard")
                    try:
                        count = int(connection.execute(sql, [f"%{safe_entity}%"]).fetchone()[0])
                    except Exception:  # noqa: BLE001
                        continue
                    if count <= 0:
                        continue
                    richness_total += min(float(count), 50.0)
                    matches.append({
                        "store_id": store_entry.get("store_id"),
                        "table": table_name,
                        "matched_entity": entity,
                        "relevant_row_count": count,
                        "bounded": True,
                    })
        finally:
            connection.close()
    matches = matches[:20]
    richness = 0.0
    if matches:
        richness = min(1.0, richness_total / 200.0)
    return {
        "schema_version": "contentops.story_scoped_cc_context.v1",
        "queried_entities": normalized_entities,
        "matches": matches,
        "cc_context_richness": round(richness, 4),
        "matched_store_ids": sorted({str(row["store_id"]) for row in matches}),
        "grants_factual_or_numeric_authority": False,
        "mutated_upstream": False,
    }
