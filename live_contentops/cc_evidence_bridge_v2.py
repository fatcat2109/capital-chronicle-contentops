"""Read-only Capital Chronicle evidence bridge for generic ContentOps stories."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "capital_chronicle_content_evidence_packet.v2"
REQUIRED_STATE_FILES = (
    "MarketSnapshot.json",
    "MarketHistory.json",
    "DataQualityReport.json",
    "InputStateManifest.json",
    "SourceHealth.json",
)
GOVERNED_HANDOFF_ROOT = Path(
    "docs/research/database_foundation/final_database_adjudication_and_analyzer_handoff_v1"
)
GOVERNED_FINAL_EVIDENCE = GOVERNED_HANDOFF_ROOT / "DATABASE_FINAL_EVIDENCE_PACKET_V1.json"
GOVERNED_HANDOFF = GOVERNED_HANDOFF_ROOT / "ANALYZER_CLOSED_LOOP_DATA_HANDOFF_V1.json"
GOVERNED_VALIDATION = GOVERNED_HANDOFF_ROOT / "ANALYZER_HANDOFF_VALIDATION_V1.json"
PUBLICATION_EVIDENCE = Path(
    "docs/research/publication_evidence/current/CapitalChroniclePublicationEvidencePacketV1.json"
)
NEWSROOM_POOL_EVIDENCE = Path(
    "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json"
)
PUBLIC_REPORTING_CONSUMERS = {
    "contentops_publication",
    "editorial_publication",
    "public_claim",
    "public_reporting",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path.name}")
    return value


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _utc_text(value: Any) -> str | None:
    parsed = _parse_timestamp(value)
    return parsed.isoformat().replace("+00:00", "Z") if parsed else None


def _load_payload_rows(connection: Any, table: str) -> list[dict[str, Any]]:
    rows = []
    for row_id, payload_json in connection.execute(
        f'SELECT id, payload_json FROM "{table}" ORDER BY id'
    ).fetchall():
        payload = json.loads(payload_json)
        if isinstance(payload, dict):
            rows.append({"governed_row_id": row_id, **payload})
    return rows


def _has_public_reporting_permission(sources: Sequence[Mapping[str, Any]]) -> bool:
    for source in sources:
        consumers = {
            str(value).strip().lower().replace(" ", "_")
            for value in (source.get("allowed_consumers") or [])
        }
        if consumers.intersection(PUBLIC_REPORTING_CONSUMERS):
            return True
    return False


def _build_evidence_packet_from_publication_packet(
    root: Path,
    *,
    as_of_utc: str | None,
    story_window_hours: int,
) -> dict[str, Any]:
    """Translate the story-scoped database product without widening global DQR."""
    source_path = root / PUBLICATION_EVIDENCE
    source = _read_json(source_path)
    if source.get("schema_version") != "capital_chronicle.publication_evidence_packet.v1":
        raise ValueError("unsupported_publication_evidence_packet_schema")
    consumers = {str(value) for value in source.get("consumer_class") or []}
    story_authority = dict(source.get("story_authority") or {})
    permissions = dict(source.get("public_claim_permissions") or {})
    contract_blockers: list[str] = []
    if source.get("status") != "PASS_PUBLICATION_AUTHORIZED":
        contract_blockers.append("publication_evidence_packet_not_authorized")
    if "contentops_publication" not in consumers:
        contract_blockers.append("contentops_publication_consumer_not_granted")
    if story_authority.get("decision") != "ALLOW" or permissions.get("decision") != "ALLOW":
        contract_blockers.append("story_scoped_publication_authority_blocked")
    if story_authority.get("global_dqr_override") is not False:
        contract_blockers.append("publication_packet_attempts_global_dqr_override")
    if (source.get("global_authority") or {}).get("dqr") != "BLOCKED":
        contract_blockers.append("global_dqr_boundary_not_preserved")

    packet_ref = str(PUBLICATION_EVIDENCE).replace("\\", "/")
    numeric_claims = []
    for index, source_claim in enumerate(source.get("numeric_claims") or []):
        claim = dict(source_claim)
        claim.setdefault("release_time_utc", None)
        claim.setdefault("ingestion_time_utc", source.get("generated_at_utc"))
        claim.setdefault("revision_time_utc", None)
        claim.setdefault("freshness_class", "story_scoped_publication_authorized")
        claim.setdefault("source_health", (source.get("source_health") or {}).get("status"))
        claim.setdefault("source_artifact_ref", f"{packet_ref}#numeric_claims/{index}")
        numeric_claims.append(claim)

    source_documents = []
    for index, row in enumerate(source.get("official_source_documents") or []):
        document = dict(row)
        document.setdefault("document_id", f"publication-source-{index + 1}")
        document.setdefault("source_artifact_ref", f"{packet_ref}#official_source_documents/{index}")
        source_documents.append(document)

    source_blockers = list(source.get("blockers") or [])
    blockers = list(dict.fromkeys([*contract_blockers, *source_blockers]))
    as_of = as_of_utc or str(source.get("as_of_utc") or _iso_now())
    as_of_dt = _parse_timestamp(as_of)
    if as_of_dt is None:
        raise ValueError("invalid_as_of_utc")
    packet_core = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _iso_now(),
        "as_of_utc": as_of,
        "story_window": {
            "hours": story_window_hours,
            "start_utc": (as_of_dt - timedelta(hours=story_window_hours)).isoformat().replace("+00:00", "Z"),
            "end_utc": as_of,
        },
        "publication_assignment": dict(source.get("assignment") or {}),
        "events": list(source.get("events") or []),
        "headlines": list(source.get("headlines") or []),
        "official_source_documents": source_documents,
        "numeric_claims": numeric_claims,
        "market_snapshots": [
            {
                **dict(row),
                "generated_at_utc": row.get("generated_at_utc") or row.get("ingestion_time_utc") or source.get("generated_at_utc"),
            }
            for row in (source.get("market_snapshots") or [])
        ],
        "time_series": dict(source.get("time_series") or {}),
        "time_series_references": [f"{packet_ref}#time_series"],
        "cross_asset_context": [],
        "source_state": {
            "dqr_status": (source.get("global_authority") or {}).get("dqr"),
            "global_dqr_reporting_allowed": False,
            "story_scoped_reporting_allowed": bool(permissions.get("reporting_allowed")),
            "source_health_status": (source.get("source_health") or {}).get("status"),
            "global_state_unchanged": (source.get("global_authority") or {}).get("global_state_unchanged"),
        },
        "candidate_visual_inputs": list(source.get("candidate_visual_inputs") or []),
        "citation_map": dict(source.get("citation_map") or {}),
        "provenance": {
            "publication_packet": {
                "relative_path": packet_ref,
                "sha256": _sha256_file(source_path),
                "upstream_packet_id": source.get("packet_id"),
                "upstream_provenance": source.get("provenance") or {},
            }
        },
        "public_claim_permissions": {
            "numeric_claims_allowed": bool(permissions.get("reporting_allowed")) and not blockers,
            "narrative_synthesis_allowed": bool(permissions.get("reporting_allowed")) and not blockers,
            "reporting_allowed": bool(permissions.get("reporting_allowed")) and not blockers,
            "llm_numeric_authority": False,
            "decision": "ALLOW" if not blockers else "BLOCK",
            "consumer_class": sorted(consumers),
        },
        "blockers": blockers,
        "governed_contract": {
            "mode": "story_scoped_publication_evidence_v1",
            "global_dqr_override": False,
            "upstream_packet_id": source.get("packet_id"),
            "upstream_packet_sha256": _sha256_file(source_path),
            "upstream_database_commit": (source.get("provenance") or {}).get("database_commit"),
        },
        "bridge_safety": {
            "source_repo_modified": False,
            "secret_files_read": False,
            "network_call_made": False,
            "database_open_mode": "packet_read_only",
            "legacy_state_fallback_used": False,
        },
    }
    packet_id = "cc-evidence-" + hashlib.sha256(
        json.dumps(packet_core, sort_keys=True).encode()
    ).hexdigest()[:16]
    packet = {"packet_id": packet_id, **packet_core}
    packet["validation_blockers"] = validate_evidence_packet(packet)
    packet["status"] = (
        "PASS_PUBLICATION_AUTHORIZED"
        if not blockers and not packet["validation_blockers"]
        else "FAIL_SCHEMA" if packet["validation_blockers"] else "PASS_CONTRACT_BLOCKED_PUBLICATION"
    )
    return packet


def _build_evidence_packet_from_governed_handoff(
    root: Path,
    *,
    as_of_utc: str | None,
    story_window_hours: int,
) -> dict[str, Any]:
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - runtime dependency guard
        raise RuntimeError("duckdb_required_for_governed_cc_handoff") from exc

    final_path = root / GOVERNED_FINAL_EVIDENCE
    handoff_path = root / GOVERNED_HANDOFF
    validation_path = root / GOVERNED_VALIDATION
    final = _read_json(final_path)
    handoff = _read_json(handoff_path)
    validation = _read_json(validation_path)
    database_binding = handoff.get("point_in_time_database") or {}
    database_path = root / str(database_binding.get("path") or "")
    if not database_path.is_file():
        raise FileNotFoundError(f"missing_governed_point_in_time_database:{database_path}")

    expected_database_sha = str(database_binding.get("physical_sha256") or "")
    actual_database_sha = _sha256_file(database_path)
    hash_matches = bool(expected_database_sha) and actual_database_sha == expected_database_sha
    as_of = as_of_utc or _iso_now()
    as_of_dt = _parse_timestamp(as_of)
    if as_of_dt is None:
        raise ValueError("invalid_as_of_utc")
    story_start = as_of_dt - timedelta(hours=story_window_hours)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        events = _load_payload_rows(connection, "event")
        documents = _load_payload_rows(connection, "document")
        market_rows = _load_payload_rows(connection, "market_observation")
        sources = _load_payload_rows(connection, "source")
        authority_rows = _load_payload_rows(connection, "authority_state_snapshot")
        field_rows = _load_payload_rows(connection, "field_availability_snapshot")
        source_health_rows = _load_payload_rows(connection, "source_health_snapshot")

    reporting_allowed = _has_public_reporting_permission(sources)
    candidate_only = any(
        str(row.get("consumer_eligibility") or "").lower() == "candidate_snapshot_only"
        for row in authority_rows
    )
    dqr_status = str((handoff.get("current_limitations") or {}).get("dqr") or "UNKNOWN")

    normalized_events = []
    for row in events:
        event_time = _utc_text(row.get("published_at") or row.get("provider_updated_at"))
        normalized_events.append({
            "event_id": row.get("record_id") or row["governed_row_id"],
            "event_time_utc": event_time,
            "known_at_utc": None,
            "source_artifact_ref": f"{database_binding.get('path')}#event/{row['governed_row_id']}",
            "content_sha256": row.get("content_sha256"),
            "public_claim_allowed": False,
            "authority_class": "candidate_context",
        })

    normalized_documents = []
    for row in documents:
        published = _utc_text(row.get("published_at") or row.get("provider_updated_at"))
        normalized_documents.append({
            "document_id": row.get("document_id") or row["governed_row_id"],
            "published_at_utc": published,
            "source_id": row.get("target_id"),
            "source_url": None,
            "content_sha256": row.get("content_sha256"),
            "source_artifact_ref": f"{database_binding.get('path')}#document/{row['governed_row_id']}",
            "public_claim_allowed": False,
            "authority_class": "candidate_context",
        })

    numeric_claims = []
    for row in market_rows:
        observation_time = _utc_text(row.get("observation_time"))
        claim_id = f"governed-market:{row.get('observation_id') or row['governed_row_id']}"
        numeric_claims.append({
            "claim_id": claim_id,
            "metric": "unidentified_market_context",
            "value": row.get("value"),
            "unit": "unknown",
            "observation_time_utc": observation_time,
            "release_time_utc": None,
            "ingestion_time_utc": _utc_text(row.get("first_known_time")),
            "revision_time_utc": None,
            "source_id": "governed_point_in_time_market_observation",
            "source_authority": row.get("source_quality") or "context",
            "freshness_class": "governed_as_of_candidate",
            "source_health": "unbound_to_specific_source_health_row",
            "source_artifact_ref": f"{database_binding.get('path')}#market_observation/{row['governed_row_id']}",
            "public_claim_allowed": False,
            "llm_numeric_authority": False,
        })

    event_times = [time for time in (_parse_timestamp(row.get("event_time_utc")) for row in normalized_events) if time]
    market_times = [time for time in (_parse_timestamp(row.get("observation_time_utc")) for row in numeric_claims) if time]
    fresh_event_count = sum(story_start <= time <= as_of_dt for time in event_times)
    fresh_market_count = sum(story_start <= time <= as_of_dt for time in market_times)

    blockers = []
    if not hash_matches:
        blockers.append("governed_point_in_time_database_hash_mismatch")
    if not final.get("analyzer_data_handoff_ready") or validation.get("status") != "PASS":
        blockers.append("governed_analyzer_handoff_not_validated")
    if dqr_status.upper() != "READY":
        blockers.append(f"capital_chronicle_dqr_{dqr_status.lower()}")
    if candidate_only:
        blockers.append("governed_authority_candidate_snapshot_only")
    if not reporting_allowed:
        blockers.append("governed_reporting_permission_not_granted")
    if not normalized_events:
        blockers.append("governed_event_evidence_missing")
    elif not fresh_event_count:
        blockers.append("governed_event_outside_story_window")
    if not normalized_documents:
        blockers.append("governed_official_document_missing")
    elif not any(row.get("source_url") for row in normalized_documents):
        blockers.append("governed_official_document_public_url_missing")
    if not numeric_claims:
        blockers.append("governed_market_state_missing")
    elif not fresh_market_count:
        blockers.append("governed_market_state_stale")
    if any(row.get("unit") == "unknown" for row in numeric_claims):
        blockers.append("governed_market_identity_or_unit_missing")
    if not any(str(row.get("health_state") or "").upper() in {"HEALTHY", "HEALTHY_UNCHANGED"} for row in source_health_rows):
        blockers.append("governed_source_health_not_publication_ready")

    provenance_paths = (final_path, handoff_path, validation_path, database_path)
    packet_core = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _iso_now(),
        "as_of_utc": as_of,
        "story_window": {
            "hours": story_window_hours,
            "start_utc": story_start.isoformat().replace("+00:00", "Z"),
            "end_utc": as_of,
        },
        "events": normalized_events,
        "headlines": [],
        "official_source_documents": normalized_documents,
        "numeric_claims": numeric_claims,
        "market_snapshots": [{
            "snapshot_id": "governed-point-in-time-market-observations",
            "generated_at_utc": max(
                (row.get("ingestion_time_utc") for row in numeric_claims if row.get("ingestion_time_utc")),
                default=None,
            ),
            "market_session_state": "unknown",
            "snapshot_quality": "candidate_context_only",
            "claim_ids": [row["claim_id"] for row in numeric_claims],
        }],
        "time_series_references": [row["source_artifact_ref"] for row in numeric_claims],
        "cross_asset_context": [],
        "source_state": {
            "dqr_status": dqr_status,
            "reporting_allowed": reporting_allowed,
            "candidate_snapshot_only": candidate_only,
            "source_health_rows": len(source_health_rows),
            "healthy_source_rows": sum(
                str(row.get("health_state") or "").upper() in {"HEALTHY", "HEALTHY_UNCHANGED"}
                for row in source_health_rows
            ),
            "authority_semantics": handoff.get("authority_semantics") or [],
            "field_authority_states": sorted({str(row.get("state") or "unknown") for row in field_rows}),
        },
        "candidate_visual_inputs": [],
        "citation_map": {
            row["claim_id"]: [row["source_artifact_ref"]]
            for row in numeric_claims
        },
        "provenance": {
            str(path.relative_to(root)).replace("\\", "/"): {
                "relative_path": str(path.relative_to(root)).replace("\\", "/"),
                "sha256": _sha256_file(path),
                "last_write_time_utc": datetime.fromtimestamp(
                    path.stat().st_mtime, timezone.utc
                ).isoformat().replace("+00:00", "Z"),
            }
            for path in provenance_paths
        },
        "public_claim_permissions": {
            "numeric_claims_allowed": False,
            "narrative_synthesis_allowed": False,
            "reporting_allowed": reporting_allowed,
            "llm_numeric_authority": False,
            "decision": "BLOCK",
            "required_public_consumer_classes": sorted(PUBLIC_REPORTING_CONSUMERS),
            "observed_allowed_consumer_classes": sorted({
                str(value)
                for source in sources
                for value in (source.get("allowed_consumers") or [])
            }),
        },
        "blockers": list(dict.fromkeys(blockers)),
        "governed_contract": {
            "mode": "governed_point_in_time_handoff_v1",
            "database_relative_path": database_binding.get("path"),
            "database_sha256_expected": expected_database_sha,
            "database_sha256_actual": actual_database_sha,
            "database_sha256_matches": hash_matches,
            "query_views": handoff.get("query_view_inventory") or [],
            "fresh_event_count": fresh_event_count,
            "fresh_market_observation_count": fresh_market_count,
            "incremental_refresh_authority": "candidate_metadata_only_numeric_truth_not_promoted",
        },
        "bridge_safety": {
            "source_repo_modified": False,
            "secret_files_read": False,
            "network_call_made": False,
            "database_open_mode": "read_only",
            "legacy_state_fallback_used": False,
        },
    }
    packet_id = "cc-evidence-" + hashlib.sha256(
        json.dumps(packet_core, sort_keys=True).encode()
    ).hexdigest()[:16]
    packet = {"packet_id": packet_id, **packet_core}
    packet["validation_blockers"] = validate_evidence_packet(packet)
    packet["status"] = (
        "FAIL_SCHEMA"
        if packet["validation_blockers"]
        else "PASS_CONTRACT_BLOCKED_PUBLICATION"
    )
    return packet


def validate_evidence_packet(packet: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    required = (
        "schema_version", "packet_id", "generated_at_utc", "as_of_utc", "story_window",
        "events", "official_source_documents", "numeric_claims", "market_snapshots",
        "source_state", "candidate_visual_inputs", "citation_map", "provenance",
        "public_claim_permissions", "blockers",
    )
    blockers.extend(f"missing:{key}" for key in required if key not in packet)
    for claim in packet.get("numeric_claims") or []:
        for key in ("claim_id", "metric", "value", "unit", "observation_time_utc", "source_id", "source_artifact_ref"):
            if claim.get(key) in (None, ""):
                blockers.append(f"numeric_claim:{claim.get('claim_id') or 'unknown'}:missing:{key}")
        if claim.get("llm_numeric_authority") is not False:
            blockers.append(f"numeric_claim:{claim.get('claim_id')}:llm_authority_must_be_false")
    return blockers


def _build_evidence_packet_from_legacy_state(
    capital_chronicle_root: str | Path,
    *,
    as_of_utc: str | None = None,
    story_window_hours: int = 24,
) -> dict[str, Any]:
    root = Path(capital_chronicle_root).resolve()
    state_root = root / "data" / "state" / "current"
    missing = [name for name in REQUIRED_STATE_FILES if not (state_root / name).is_file()]
    if missing:
        raise FileNotFoundError("missing_cc_state_files:" + ",".join(missing))
    artifacts = {name: _read_json(state_root / name) for name in REQUIRED_STATE_FILES}
    snapshot = artifacts["MarketSnapshot.json"]
    dqr = artifacts["DataQualityReport.json"]
    source_health = artifacts["SourceHealth.json"]
    market_history = artifacts["MarketHistory.json"]
    as_of = as_of_utc or _iso_now()
    numeric_claims: list[dict[str, Any]] = []
    visual_inputs: list[dict[str, Any]] = []
    citation_map: dict[str, list[str]] = {}
    for symbol, row in sorted((snapshot.get("metrics") or {}).items()):
        if not isinstance(row, Mapping) or row.get("value") is None or not row.get("timestamp_utc"):
            continue
        claim_id = f"market:{symbol}:{str(row['timestamp_utc']).replace(':', '').replace('-', '')}"
        source_id = str(row.get("source_id") or "unknown")
        source_ref = f"data/state/current/MarketSnapshot.json#metrics.{symbol}"
        history_rows = [item for item in (market_history.get(symbol) or []) if isinstance(item, Mapping) and item.get("value") is not None]
        prior_rows = [item for item in history_rows if str(item.get("timestamp_utc") or "") < str(row.get("timestamp_utc") or "")]
        prior_close = prior_rows[-1].get("value") if prior_rows else None
        move_since_prior = (float(row["value"]) - float(prior_close)) if prior_close is not None else None
        move_percent = (move_since_prior / float(prior_close) * 100.0) if prior_close not in (None, 0) else None
        numeric_claims.append({
            "claim_id": claim_id,
            "metric": symbol,
            "canonical_symbol": symbol,
            "provider_symbol": source_id,
            "value": row.get("value"),
            "bid": row.get("bid"),
            "ask": row.get("ask"),
            "mid": row.get("mid"),
            "last": row.get("last") or row.get("value"),
            "prior_close": prior_close,
            "move_since_prior_close": round(move_since_prior, 6) if move_since_prior is not None else None,
            "move_since_prior_close_percent": round(move_percent, 6) if move_percent is not None else None,
            "interval": "latest_committed_observation",
            "unit": row.get("unit"),
            "observation_time_utc": row.get("timestamp_utc"),
            "release_time_utc": None,
            "ingestion_time_utc": snapshot.get("generated_at_utc"),
            "revision_time_utc": None,
            "source_id": source_id,
            "source_method": row.get("source_method"),
            "source_authority": (row.get("metadata") or {}).get("status", "unverified"),
            "freshness_class": row.get("freshness_status", "unknown"),
            "session_state": snapshot.get("market_session_state", "unknown"),
            "source_health": row.get("freshness_status", "unknown"),
            "source_artifact_ref": source_ref,
            "public_claim_allowed": bool(dqr.get("reporting_allowed")) and row.get("freshness_status") == "fresh",
            "llm_numeric_authority": False,
        })
        citation_map[claim_id] = [source_ref]
        visual_inputs.append({
            "visual_input_id": f"series:{symbol}",
            "role_candidates": ["primary_quantitative_chart", "cross_asset_chart"],
            "evidence_dimension": f"market_series:{symbol}",
            "modality": "time_series",
            "underlying_series_ids": [symbol],
            "source_artifact_ref": source_ref,
            "rights_status": "capital_chronicle_internal_data_visualization_allowed",
            "public_claim_allowed": bool(dqr.get("reporting_allowed")),
        })
    provenance = {
        name: {
            "relative_path": f"data/state/current/{name}",
            "sha256": _sha256_file(state_root / name),
            "last_write_time_utc": datetime.fromtimestamp((state_root / name).stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        for name in REQUIRED_STATE_FILES
    }
    hard_blockers = []
    if not dqr.get("reporting_allowed"):
        hard_blockers.append("capital_chronicle_dqr_reporting_not_allowed")
    if str(dqr.get("overall_status")) != "ready":
        hard_blockers.append(f"capital_chronicle_dqr_{dqr.get('overall_status', 'unknown')}")
    packet_core = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _iso_now(),
        "as_of_utc": as_of,
        "story_window": {"hours": story_window_hours, "start_utc": None, "end_utc": as_of},
        "events": [],
        "headlines": [],
        "official_source_documents": [],
        "numeric_claims": numeric_claims,
        "market_snapshots": [{
            "snapshot_id": snapshot.get("snapshot_id"),
            "generated_at_utc": snapshot.get("generated_at_utc"),
            "market_session_state": snapshot.get("market_session_state"),
            "snapshot_quality": snapshot.get("snapshot_quality"),
            "ttl_policy_seconds": snapshot.get("ttl_policy_seconds"),
            "claim_ids": [row["claim_id"] for row in numeric_claims],
        }],
        "time_series_references": [row["source_artifact_ref"] for row in numeric_claims],
        "cross_asset_context": [row["claim_id"] for row in numeric_claims],
        "source_state": {
            "dqr_report_id": dqr.get("report_id"),
            "dqr_generated_at_utc": dqr.get("generated_at_utc"),
            "dqr_status": dqr.get("overall_status"),
            "reporting_allowed": bool(dqr.get("reporting_allowed")),
            "source_health_status": source_health.get("overall_status"),
            "source_health_generated_at_utc": source_health.get("generated_at_utc"),
            "input_state_manifest_authority": artifacts["InputStateManifest.json"].get("manifest_authority"),
        },
        "candidate_visual_inputs": visual_inputs,
        "citation_map": citation_map,
        "provenance": provenance,
        "public_claim_permissions": {
            "numeric_claims_allowed": bool(dqr.get("reporting_allowed")),
            "narrative_synthesis_allowed": bool(dqr.get("reporting_allowed")),
            "llm_numeric_authority": False,
            "decision": "ALLOW" if dqr.get("reporting_allowed") else "BLOCK",
        },
        "blockers": hard_blockers,
        "bridge_safety": {"source_repo_modified": False, "secret_files_read": False, "network_call_made": False},
    }
    packet_id = "cc-evidence-" + hashlib.sha256(json.dumps(packet_core, sort_keys=True).encode()).hexdigest()[:16]
    packet = {"packet_id": packet_id, **packet_core}
    packet["validation_blockers"] = validate_evidence_packet(packet)
    packet["status"] = "PASS_CONTRACT_BLOCKED_PUBLICATION" if hard_blockers and not packet["validation_blockers"] else ("PASS" if not packet["validation_blockers"] else "FAIL_SCHEMA")
    return packet


def _build_evidence_packet_from_pool_candidate(
    candidate: Mapping[str, Any],
    pool_path: Path,
    pool_hash: str,
    root: Path,
    *,
    as_of_utc: str | None,
    story_window_hours: int,
) -> dict[str, Any]:
    packet = _build_evidence_packet_from_publication_packet(
        root,
        as_of_utc=as_of_utc,
        story_window_hours=story_window_hours,
    )
    packet_ref = str(pool_path.relative_to(pool_path.parents[2])).replace("\\", "/")
    packet["provenance"]["pool_candidate"] = {
        "relative_path": packet_ref,
        "sha256": pool_hash,
        "upstream_candidate_id": candidate.get("candidate_id"),
    }
    packet["governed_contract"]["upstream_candidate_id"] = candidate.get("candidate_id")
    
    if candidate.get("eligible") is not True:
        packet["blockers"] = list(dict.fromkeys(packet["blockers"] + (candidate.get("blockers") or [])))
        packet["status"] = "PASS_CONTRACT_BLOCKED_PUBLICATION"
        
    return packet


def build_evidence_packet_from_cc_root(
    capital_chronicle_root: str | Path,
    *,
    as_of_utc: str | None = None,
    story_window_hours: int = 24,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    root = Path(capital_chronicle_root).resolve()
    if candidate_id:
        pool_path = root / NEWSROOM_POOL_EVIDENCE
        if pool_path.is_file():
            pool = _read_json(pool_path)
            candidate = None
            for c in (pool.get("eligible_candidates") or []) + (pool.get("rejected_candidates") or []):
                if c.get("candidate_id") == candidate_id:
                    candidate = c
                    break
            if candidate:
                return _build_evidence_packet_from_pool_candidate(
                    candidate,
                    pool_path,
                    _sha256_file(pool_path),
                    root,
                    as_of_utc=as_of_utc,
                    story_window_hours=story_window_hours,
                )
            raise ValueError(f"candidate_not_found_in_pool:{candidate_id}")
        raise FileNotFoundError(f"missing_candidate_pool_file:{pool_path}")

    if (root / PUBLICATION_EVIDENCE).is_file():
        return _build_evidence_packet_from_publication_packet(
            root,
            as_of_utc=as_of_utc,
            story_window_hours=story_window_hours,
        )
    if all((root / path).is_file() for path in (GOVERNED_FINAL_EVIDENCE, GOVERNED_HANDOFF, GOVERNED_VALIDATION)):
        return _build_evidence_packet_from_governed_handoff(
            root,
            as_of_utc=as_of_utc,
            story_window_hours=story_window_hours,
        )
    return _build_evidence_packet_from_legacy_state(
        root,
        as_of_utc=as_of_utc,
        story_window_hours=story_window_hours,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capital-chronicle-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--as-of-utc")
    args = parser.parse_args(argv)
    packet = build_evidence_packet_from_cc_root(args.capital_chronicle_root, as_of_utc=args.as_of_utc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": packet["status"], "packet_id": packet["packet_id"]}, sort_keys=True))
    return 0 if packet["status"] != "FAIL_SCHEMA" else 2


if __name__ == "__main__":
    raise SystemExit(main())
