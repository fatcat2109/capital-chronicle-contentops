"""Complete, compact, read-only catalog of the Capital Chronicle local data estate.

Discovery records every DuckDB store/table schema without scanning table contents. Story
queries then inspect only schema-relevant tables and return bounded match pointers. Arbitrary
database rows remain editorial context, never factual or numeric publication authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

CATALOG_SCHEMA_VERSION = "contentops.capital_chronicle_data_catalog.v2"
DEFAULT_CC_ROOT = Path(r"A:\Capital Chronicle\Main App")
LOCAL_DB_SUBPATH = Path("data") / "local_db"
PUBLICATION_EVIDENCE_SUBPATH = Path("docs/research/publication_evidence/current/CapitalChroniclePublicationEvidencePacketV1.json")
NEWSROOM_POOL_SUBPATH = Path("docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json")
PUBLICATION_EVIDENCE_SCHEMA_VERSION = "capital_chronicle.publication_evidence_packet.v1"
NEWSROOM_POOL_SCHEMA_VERSION = "capital_chronicle.newsroom_candidate_pool.v1"
STORY_QUERY_ENTITY_LIMIT = 6
STORY_QUERY_ROWS_PER_ENTITY = 5
MAX_DEEP_QUERY_TABLES = 8
READ_ONLY_SQL_GUARD = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)
TEXT_TYPE_MARKERS = ("CHAR", "TEXT", "STRING", "VARCHAR", "JSON")
SEARCH_SCHEMA_MARKERS = (
    "entity", "event", "document", "record", "news", "story", "instrument", "security",
    "asset", "issuer", "econom", "macro", "market", "series", "release", "source",
    "analysis", "symbol", "ticker", "title", "headline", "summary", "name", "description",
)

_CATALOG_CACHE: dict[str, tuple[str, dict[str, Any]]] = {}


class CapitalChronicleCatalogError(RuntimeError):
    pass


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _open_readonly(store_path: Path):
    import duckdb

    return duckdb.connect(str(store_path), read_only=True)


def _quote_identifier(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _looks_like_timestamp_column(column: str) -> bool:
    lowered = str(column).lower()
    return any(marker in lowered for marker in ("date", "time", "as_of", "known_at", "recorded", "_at"))


def _estate_file_fingerprint(paths: Sequence[Path]) -> str:
    return _canonical_hash([
        {"path": str(path.resolve()), "size": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns}
        for path in paths
    ])


def _surface_file_metadata(path: Path) -> dict[str, Any]:
    """Return bounded identity metadata for one governed file without granting authority."""
    if not path.is_file():
        return {"path": str(path), "exists": False}
    payload = path.read_bytes()
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": len(payload),
        "mtime_ns": stat.st_mtime_ns,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def discover_cc_data_estate(
    *,
    cc_root: str | Path = DEFAULT_CC_ROOT,
    max_stores: int | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Discover every current DuckDB store/table through metadata-only read-only queries.

    ``max_stores`` remains accepted for callers compiled against v1 but is deliberately ignored:
    completeness is now a correctness invariant, not an optional scan limit.
    """
    root = Path(cc_root).resolve()
    local_db_dir = root / LOCAL_DB_SUBPATH
    store_paths = sorted(local_db_dir.glob("*.duckdb")) if local_db_dir.is_dir() else []
    publication_packet = root / PUBLICATION_EVIDENCE_SUBPATH
    newsroom_pool = root / NEWSROOM_POOL_SUBPATH
    database_file_fingerprint = (
        _estate_file_fingerprint(store_paths) if store_paths else _canonical_hash([])
    )
    governed_surface_files = {
        "publication_evidence_packet": _surface_file_metadata(publication_packet),
        "newsroom_candidate_pool": _surface_file_metadata(newsroom_pool),
    }
    governed_surface_file_fingerprint = _canonical_hash(governed_surface_files)
    file_fingerprint = _canonical_hash({
        "database_file_fingerprint": database_file_fingerprint,
        "governed_surface_file_fingerprint": governed_surface_file_fingerprint,
    })
    cache_key = str(root).casefold()
    cached = _CATALOG_CACHE.get(cache_key)
    if use_cache and cached and cached[0] == file_fingerprint:
        result = copy.deepcopy(cached[1])
        result["cache"] = {
            **dict(result.get("cache") or {}),
            "state": "HIT",
            "file_fingerprint": file_fingerprint,
        }
        return result

    catalog: dict[str, Any] = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "cc_root": str(root),
        "root_exists": root.is_dir(),
        "stores": [],
        "store_count_total": len(store_paths),
        "store_count_discovered": 0,
        "stores_omitted": 0,
        "discovery_complete": True,
        "legacy_max_stores_parameter_ignored": max_stores is not None,
        "governed_surfaces": {
            "publication_evidence_packet": {
                "path": str(publication_packet),
                "exists": publication_packet.is_file(),
                "role": "governed_publication_authority_surface",
                "file_identity": governed_surface_files["publication_evidence_packet"],
            },
            "newsroom_candidate_pool": {
                "path": str(newsroom_pool),
                "exists": newsroom_pool.is_file(),
                "role": "governed_newsroom_pool_surface",
                "file_identity": governed_surface_files["newsroom_candidate_pool"],
            },
        },
        "mutated_upstream": False,
        "connection_mode": "duckdb_read_only",
        "discovery_scope": "ALL_DUCKDB_STORES_AND_ALL_TABLE_SCHEMAS_METADATA_ONLY",
        "cache": {
            "state": "MISS",
            "file_fingerprint": file_fingerprint,
            "database_file_fingerprint": database_file_fingerprint,
            "governed_surface_file_fingerprint": governed_surface_file_fingerprint,
        },
    }
    for store_path in store_paths:
        store_entry: dict[str, Any] = {
            "store_id": store_path.stem,
            "path": str(store_path),
            "type": "duckdb",
            "opened_read_only": False,
            "table_count": 0,
            "tables": [],
            "store_size_bytes": store_path.stat().st_size,
        }
        try:
            connection = _open_readonly(store_path)
        except Exception as exc:  # noqa: BLE001
            store_entry["open_error"] = type(exc).__name__
            catalog["stores"].append(store_entry)
            continue
        try:
            store_entry["opened_read_only"] = True
            rows = connection.execute(
                "SELECT table_name,column_name,data_type,ordinal_position "
                "FROM information_schema.columns WHERE table_schema NOT IN "
                "('information_schema','pg_catalog') ORDER BY table_name,ordinal_position"
            ).fetchall()
            by_table: dict[str, list[tuple[str, str]]] = {}
            for table_name, column_name, data_type, _ in rows:
                by_table.setdefault(str(table_name), []).append(
                    (str(column_name), str(data_type))
                )
            store_entry["table_count"] = len(by_table)
            for table_name, columns in sorted(by_table.items()):
                column_names = [name for name, _ in columns]
                textual = [
                    name for name, data_type in columns
                    if any(marker in data_type.upper() for marker in TEXT_TYPE_MARKERS)
                ]
                preferred_textual = sorted(
                    textual,
                    key=lambda name: (
                        0 if name.lower() in {
                            "canonical_name", "display_name", "name", "title", "headline",
                            "summary", "description", "entity", "entity_name", "symbol",
                            "ticker", "series_name", "document_title",
                        } else 1,
                        len(name),
                        name,
                    ),
                )
                semantic = [
                    name for name in column_names
                    if any(marker in name.lower() for marker in SEARCH_SCHEMA_MARKERS)
                ]
                searchable = bool(preferred_textual and (
                    any(marker in table_name.lower() for marker in SEARCH_SCHEMA_MARKERS)
                    or semantic
                ))
                table_core = {
                    "table": table_name,
                    "column_count": len(columns),
                    "columns": [
                        {"name": name, "data_type": data_type} for name, data_type in columns
                    ],
                    "text_search_columns": preferred_textual[:12],
                    "timestamp_columns": [
                        name for name in column_names if _looks_like_timestamp_column(name)
                    ][:8],
                    "semantic_fields": semantic[:16],
                    "story_search_candidate": searchable,
                    "content_rows_scanned_during_discovery": 0,
                }
                store_entry["tables"].append({
                    **table_core,
                    "schema_fingerprint": _canonical_hash(table_core),
                })
            store_entry["schema_fingerprint"] = _canonical_hash([
                row["schema_fingerprint"] for row in store_entry["tables"]
            ])
        finally:
            connection.close()
        catalog["stores"].append(store_entry)
    catalog["store_count_discovered"] = len(catalog["stores"])
    catalog["catalog_fingerprint"] = _canonical_hash({
        "file_fingerprint": file_fingerprint,
        "stores": [
            {"store_id": row["store_id"], "schema_fingerprint": row.get("schema_fingerprint")}
            for row in catalog["stores"]
        ],
        "governed_surfaces": catalog["governed_surfaces"],
    })
    _CATALOG_CACHE[cache_key] = (file_fingerprint, copy.deepcopy(catalog))
    return catalog


def inspect_governed_cc_surfaces(catalog: Mapping[str, Any]) -> dict[str, Any]:
    """Inspect exact governed packets while keeping arbitrary database context non-authoritative.

    Unknown governed schemas fail only the affected capability. Missing, malformed, or stale-
    flagged packets never become publication authority, and ordinary journalism remains free to
    proceed on separately acquired public evidence.
    """
    surfaces = catalog.get("governed_surfaces") or {}
    result: dict[str, Any] = {
        "schema_version": "contentops.capital_chronicle_governed_surface_inspection.v1",
        "catalog_fingerprint": catalog.get("catalog_fingerprint"),
        "surfaces": {},
        "governed_publication_authority_available": False,
        "compatible_governed_publication_packet_available": False,
        "context_or_discovery_grants_publication_authority": False,
        "mutated_upstream": False,
    }
    compatibility_required: list[str] = []
    for surface_name in ("publication_evidence_packet", "newsroom_candidate_pool"):
        descriptor = surfaces.get(surface_name) or {}
        path = Path(str(descriptor.get("path") or ""))
        row: dict[str, Any] = {
            "surface": surface_name,
            "path": str(path),
            "exists": path.is_file(),
            "role": descriptor.get("role"),
            "authority_class": "CONTEXT_OR_DISCOVERY_ONLY",
            "publication_authority_granted": False,
        }
        if not path.is_file():
            row["state"] = "MISSING"
            result["surfaces"][surface_name] = row
            continue
        try:
            payload = path.read_bytes()
            value = json.loads(payload.decode("utf-8"))
            if not isinstance(value, Mapping):
                raise ValueError("governed_surface_root_not_object")
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            row.update({
                "state": "MALFORMED",
                "error_class": type(exc).__name__,
            })
            result["surfaces"][surface_name] = row
            continue
        row.update({
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "schema_version": value.get("schema_version"),
            "status": value.get("status"),
            "generated_at_utc": value.get("generated_at_utc"),
        })
        if surface_name == "publication_evidence_packet":
            if value.get("schema_version") != PUBLICATION_EVIDENCE_SCHEMA_VERSION:
                row["state"] = "CC_GOVERNED_SURFACE_COMPATIBILITY_REQUIRED"
                compatibility_required.append(surface_name)
                result["surfaces"][surface_name] = row
                continue
            story_authority = value.get("story_authority") or {}
            permissions = value.get("public_claim_permissions") or {}
            source_health = value.get("source_health") or {}
            blockers = [str(item) for item in (value.get("blockers") or [])]
            source_health_status = str(source_health.get("status") or "").upper()
            packet_authorized = bool(
                value.get("status") == "PASS_PUBLICATION_AUTHORIZED"
                and str(value.get("packet_id") or "").strip()
                and str(value.get("as_of_utc") or "").strip()
                and isinstance(story_authority, Mapping)
                and story_authority.get("decision") == "ALLOW"
                and str(story_authority.get("scope") or "").strip()
                and isinstance(permissions, Mapping)
                and permissions.get("decision") == "ALLOW"
                and source_health_status in {"HEALTHY", "PASS", "READY", "FRESH"}
                and not blockers
            )
            row.update({
                "state": "READY" if packet_authorized else "CONTEXT_ONLY_NOT_AUTHORIZED",
                "packet_id": value.get("packet_id"),
                "as_of_utc": value.get("as_of_utc"),
                "source_retrieved_at_utc": (value.get("provenance") or {}).get(
                    "retrieved_at_utc"
                ) if isinstance(value.get("provenance"), Mapping) else None,
                "source_health_status": source_health.get("status")
                if isinstance(source_health, Mapping) else None,
                "source_freshness_age_hours_at_packet_generation": source_health.get(
                    "freshness_age_hours"
                ) if isinstance(source_health, Mapping) else None,
                "story_authority_decision": story_authority.get("decision")
                if isinstance(story_authority, Mapping) else None,
                "story_authority_scope": story_authority.get("scope")
                if isinstance(story_authority, Mapping) else None,
                "public_claim_permission_decision": permissions.get("decision")
                if isinstance(permissions, Mapping) else None,
                "numeric_claims_allowed": bool(permissions.get("numeric_claims_allowed"))
                if isinstance(permissions, Mapping) else False,
                "llm_numeric_authority": bool(permissions.get("llm_numeric_authority"))
                if isinstance(permissions, Mapping) else False,
                "numeric_claim_count": len(value.get("numeric_claims") or []),
                "time_series_count": len(value.get("time_series") or []),
                "blockers": blockers,
                "packet_contract_authorized_for_exact_scope": packet_authorized,
                "freshness_must_be_reassessed_for_current_story": True,
                "exact_story_scope_binding_required": True,
            })
            if packet_authorized:
                row["authority_class"] = "GOVERNED_CC_AUTHORITY_PACKET"
                result["compatible_governed_publication_packet_available"] = True
        else:
            if value.get("schema_version") != NEWSROOM_POOL_SCHEMA_VERSION:
                row["state"] = "CC_GOVERNED_SURFACE_COMPATIBILITY_REQUIRED"
                compatibility_required.append(surface_name)
                result["surfaces"][surface_name] = row
                continue
            row.update({
                "state": "READY_CONTEXT_ONLY",
                "pool_id": value.get("pool_id"),
                "cutoff_time_utc": value.get("cutoff_time_utc"),
                "candidate_only": value.get("candidate_only") is True,
                "eligible_candidate_count": int(
                    (value.get("counts") or {}).get("eligible") or 0
                ) if isinstance(value.get("counts"), Mapping) else 0,
                "authority_class": "GOVERNED_NEWSROOM_DISCOVERY_ONLY",
            })
        result["surfaces"][surface_name] = row
    result["compatibility_required_surfaces"] = compatibility_required
    result["compatibility_state"] = (
        "CC_GOVERNED_SURFACE_COMPATIBILITY_REQUIRED"
        if compatibility_required else "COMPATIBLE"
    )
    return result


def _candidate_search_tables(store_entry: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return every schema-relevant table; no first-N truncation is permitted."""
    return [
        table for table in (store_entry.get("tables") or [])
        if isinstance(table, Mapping) and table.get("story_search_candidate") is True
    ]


def _deep_query_score(
    store_entry: Mapping[str, Any], table: Mapping[str, Any], entities: Sequence[str]
) -> float:
    """Schema-only relevance score used to select the bounded deep-query set."""
    table_name = str(table.get("table") or "").lower()
    fields = [str(value).lower() for value in (table.get("semantic_fields") or [])]
    text_fields = [str(value).lower() for value in (table.get("text_search_columns") or [])]
    score = 0.0
    score += 6.0 * int("entity" in table_name)
    score += 4.0 * int(any(marker in table_name for marker in ("event", "document", "record")))
    score += 5.0 * int(any(value in {
        "canonical_name", "display_name", "entity_name", "title", "headline", "symbol", "ticker"
    } for value in text_fields))
    score += min(4.0, len(fields) * 0.4)
    entity_tokens = {
        token for entity in entities for token in re.findall(r"[a-z0-9]{3,}", entity.lower())
    }
    score += 8.0 * int(any(token in table_name for token in entity_tokens))
    size_bytes = max(1, int(store_entry.get("store_size_bytes") or 1))
    score -= min(5.0, max(0.0, (len(str(size_bytes)) - 7) * 0.75))
    return round(score, 4)


def _parse_time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def query_story_scoped_cc_context(
    catalog: Mapping[str, Any],
    entities: Sequence[str],
    *,
    max_rows_per_entity: int = STORY_QUERY_ROWS_PER_ENTITY,
) -> dict[str, Any]:
    """Selectively query actual matching rows and return compact auditable pointers."""
    normalized_entities: list[str] = []
    for entity in entities:
        text = " ".join(str(entity or "").split())
        if text and text.casefold() not in {item.casefold() for item in normalized_entities}:
            normalized_entities.append(text)
    normalized_entities = normalized_entities[:STORY_QUERY_ENTITY_LIMIT]
    row_limit = max(1, min(int(max_rows_per_entity), 20))
    matches: list[dict[str, Any]] = []
    scored_candidates: list[tuple[float, str, str]] = []
    for store_entry in catalog.get("stores") or []:
        if not store_entry.get("opened_read_only"):
            continue
        for table in _candidate_search_tables(store_entry):
            scored_candidates.append((
                _deep_query_score(store_entry, table, normalized_entities),
                str(store_entry.get("store_id") or ""),
                str(table.get("table") or ""),
            ))
    scored_candidates.sort(key=lambda value: (-value[0], value[1], value[2]))
    selected_candidates = {
        (store_id, table_name)
        for _, store_id, table_name in scored_candidates[:MAX_DEEP_QUERY_TABLES]
    }
    tables_considered = len(scored_candidates)
    tables_queried = 0
    for store_entry in catalog.get("stores") or []:
        if not store_entry.get("opened_read_only"):
            continue
        candidates = [
            table for table in _candidate_search_tables(store_entry)
            if (str(store_entry.get("store_id") or ""), str(table.get("table") or ""))
            in selected_candidates
        ]
        if not candidates or not normalized_entities:
            continue
        try:
            connection = _open_readonly(Path(str(store_entry["path"])))
        except Exception:  # noqa: BLE001
            continue
        try:
            for table in candidates:
                text_columns = [str(value) for value in (table.get("text_search_columns") or [])]
                if not text_columns:
                    continue
                timestamp_columns = [
                    str(value) for value in (table.get("timestamp_columns") or [])
                ]
                selected_columns = text_columns[:8] + timestamp_columns[:2]
                select_sql = ",".join(_quote_identifier(value) for value in selected_columns)
                predicate = " OR ".join(
                    f"LOWER(CAST({_quote_identifier(value)} AS VARCHAR)) LIKE LOWER(?)"
                    for value in text_columns[:8]
                )
                table_name = str(table.get("table") or "")
                sql = (
                    f"SELECT {select_sql} FROM {_quote_identifier(table_name)} "
                    f"WHERE {predicate} LIMIT {row_limit + 1}"
                )
                if not READ_ONLY_SQL_GUARD.match(sql):
                    raise CapitalChronicleCatalogError("read_only_sql_guard")
                tables_queried += 1
                for entity in normalized_entities:
                    try:
                        rows = connection.execute(
                            sql, [f"%{entity}%"] * min(len(text_columns), 8)
                        ).fetchall()
                    except Exception:  # noqa: BLE001
                        continue
                    if not rows:
                        continue
                    bounded_rows = rows[:row_limit]
                    latest = None
                    row_refs: list[str] = []
                    for row in bounded_rows:
                        row_values = [None if value is None else str(value) for value in row]
                        row_refs.append(_canonical_hash({
                            "store": store_entry.get("store_id"),
                            "table": table_name,
                            "values": row_values,
                        })[:24])
                        for value in row_values[len(text_columns[:8]):]:
                            parsed = _parse_time(value)
                            latest = parsed if parsed and (latest is None or parsed > latest) else latest
                    semantic_fields = [
                        str(value).lower() for value in (table.get("semantic_fields") or [])
                    ]
                    matches.append({
                        "store_id": store_entry.get("store_id"),
                        "table": table_name,
                        "matched_entity": entity,
                        "relevant_row_count_bounded": len(bounded_rows),
                        "more_rows_possible": len(rows) > row_limit,
                        "latest_matched_observation_utc": (
                            latest.isoformat().replace("+00:00", "Z") if latest else None
                        ),
                        "row_reference_hashes": row_refs,
                        "schema_fingerprint": table.get("schema_fingerprint"),
                        "quality_or_lineage_fields_present": sorted({
                            field for field in semantic_fields
                            if any(marker in field for marker in (
                                "dqr", "quality", "lineage", "authority", "source", "known_at"
                            ))
                        }),
                        "bounded": True,
                    })
        finally:
            connection.close()

    matched_entities = {str(row["matched_entity"]).casefold() for row in matches}
    matched_stores = {str(row["store_id"]) for row in matches}
    matched_rows = sum(int(row["relevant_row_count_bounded"]) for row in matches)
    coverage = (
        len(matched_entities) / float(len(normalized_entities)) if normalized_entities else 0.0
    )
    row_density = min(1.0, matched_rows / float(max(1, len(normalized_entities) * row_limit)))
    store_diversity = min(1.0, len(matched_stores) / 3.0)
    quality_lineage = (
        sum(bool(row["quality_or_lineage_fields_present"]) for row in matches) / float(len(matches))
        if matches else 0.0
    )
    freshness = (
        sum(bool(row["latest_matched_observation_utc"]) for row in matches) / float(len(matches))
        if matches else 0.0
    )
    richness = min(
        1.0,
        (0.35 * coverage)
        + (0.20 * row_density)
        + (0.15 * store_diversity)
        + (0.15 * quality_lineage)
        + (0.15 * freshness),
    ) if matches else 0.0
    return {
        "schema_version": "contentops.story_scoped_cc_context.v2",
        "queried_entities": normalized_entities,
        "matches": matches,
        "cc_context_richness": round(richness, 4),
        "richness_components": {
            "entity_coverage": round(coverage, 4),
            "bounded_row_density": round(row_density, 4),
            "matched_store_diversity": round(store_diversity, 4),
            "quality_lineage_surface_coverage": round(quality_lineage, 4),
            "matched_freshness_metadata_coverage": round(freshness, 4),
        },
        "matched_store_ids": sorted(matched_stores),
        "matched_store_count": len(matched_stores),
        "matched_table_count": len({(row["store_id"], row["table"]) for row in matches}),
        "candidate_table_count": tables_considered,
        "deep_query_table_limit": MAX_DEEP_QUERY_TABLES,
        "deep_query_selection_method": "DETERMINISTIC_SCHEMA_RELEVANCE_SCORE",
        "deep_query_selected_tables": [
            {"score": score, "store_id": store_id, "table": table_name}
            for score, store_id, table_name in scored_candidates[:MAX_DEEP_QUERY_TABLES]
        ],
        "queried_table_count": tables_queried,
        "catalog_fingerprint": catalog.get("catalog_fingerprint"),
        "all_discovered_stores_considered": True,
        "grants_factual_or_numeric_authority": False,
        "mutated_upstream": False,
    }
