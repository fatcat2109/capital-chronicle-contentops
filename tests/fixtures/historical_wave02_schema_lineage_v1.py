"""Exact historical Wave 02 SQLite schema fixtures.

The schema objects are loaded from a checked-in frozen extraction generated from each
originating commit's own migration registry. This module never imports or reuses the
current durable-store migration SQL.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
from typing import Any, Dict, Mapping, Sequence


_FROZEN_EXTRACTION = pathlib.Path(__file__).with_name("historical_wave02_schema_objects_v1.json")
_GENESIS_PREVIOUS_HASH = "GENESIS_" + ("0" * 64)
_T0 = "2026-07-15T12:00:00+00:00"
_T1 = "2026-07-15T12:01:00+00:00"
_T2 = "2026-07-15T12:02:00+00:00"


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _columns(connection: sqlite3.Connection, table: str) -> Sequence[str]:
    return tuple(str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall())


def _insert(connection: sqlite3.Connection, table: str, values: Mapping[str, Any]) -> None:
    columns = [column for column in _columns(connection, table) if column in values]
    placeholders = ",".join("?" for _ in columns)
    connection.execute(
        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
        tuple(values[column] for column in columns),
    )


def load_historical_schema_extraction() -> Mapping[str, Mapping[str, Any]]:
    """Return frozen lineage records keyed by their full originating commit."""
    payload = json.loads(_FROZEN_EXTRACTION.read_text(encoding="utf-8-sig"))
    return {str(lineage["commit"]): lineage for lineage in payload["lineages"]}


def _work_item_values(
    work_item_id: str,
    story_id: str,
    title: str,
    current_state: str,
    state_version: int,
) -> Dict[str, Any]:
    return {
        "work_item_id": work_item_id,
        "work_item_key": f"{story_id}:substack",
        "story_id": story_id,
        "title": title,
        "target_surface": "substack",
        "current_state": current_state,
        "state_version": state_version,
        "lock_version": state_version,
        "created_at": _T0,
        "updated_at": _T2 if state_version > 2 else _T1,
    }


def _populate_operational_rows(connection: sqlite3.Connection) -> Dict[str, Any]:
    event_columns = set(_columns(connection, "transition_events"))
    artifact_columns = set(_columns(connection, "artifact_references"))
    has_envelope = "event_payload_json" in event_columns
    has_event_kind = "event_kind" in event_columns
    no_genesis = not has_envelope

    projections = (
        _work_item_values(
            "wi_historical_alpha",
            "story_historical_alpha",
            "Historical Alpha",
            "EVIDENCE_READY" if no_genesis else "EVIDENCE_PENDING",
            3 if no_genesis else 2,
        ),
        _work_item_values(
            "wi_historical_beta",
            "story_historical_beta",
            "Historical Beta",
            "EVIDENCE_PENDING" if no_genesis else "DISCOVERED",
            2 if no_genesis else 1,
        ),
    )
    for projection in projections:
        _insert(connection, "work_items", projection)

    artifact_bytes = b"historical-alpha-source-evidence"
    artifact_hash = _sha256(artifact_bytes)
    artifact = {
        "artifact_id": "art_historical_alpha",
        "artifact_key": "historical-alpha-source-evidence",
        "artifact_type": "source_evidence",
        "story_id": "story_historical_alpha",
        "work_item_id": "wi_historical_alpha",
        "storage_path": "legacy://historical-alpha-source-evidence",
        "storage_class": "LOCAL_FIXTURE",
        "content_hash": artifact_hash,
        "sha256_hash": artifact_hash,
        "byte_length": len(artifact_bytes),
        "metadata_json": "{}",
        "schema_version": "contentops.historical_fixture_artifact.v1",
        "created_at": _T0,
        "producer_ref": "historical_fixture",
        "sensitivity_class": "PUBLIC",
        "artifact_scope": "WORK_ITEM_EXACT",
    }
    if "canonical_receipt_hash" in artifact_columns:
        artifact.update(
            {
                "receipt_id": "receipt_historical_alpha",
                "receipt_schema": "contentops.historical_fixture_receipt.v1",
                "receipt_source_identity": "historical_fixture",
                "receipt_object_identity": "art_historical_alpha",
                "receipt_verifier_identity": "historical_fixture",
                "canonical_receipt_hash": _sha256("historical-alpha-receipt"),
            }
        )
    _insert(connection, "artifact_references", artifact)

    _insert(
        connection,
        "assignments",
        {
            "assignment_id": "assignment_historical_alpha",
            "work_item_id": "wi_historical_alpha",
            "assignee": "historical_worker",
            "assignee_ref": "historical_worker",
            "assigned_at": _T0,
            "status": "ACTIVE",
            "unassigned_at": None,
            "metadata_json": "{}",
        },
    )
    _insert(
        connection,
        "leases",
        {
            "lease_id": "lease_historical_alpha",
            "lease_key": "lease-key-historical-alpha",
            "work_item_id": "wi_historical_alpha",
            "owner_ref": "historical_worker",
            "fencing_token": 1,
            "acquired_at": _T0,
            "renewed_at": _T1,
            "expires_at": "2099-01-01T00:00:00+00:00",
            "status": "ACTIVE",
        },
    )
    _insert(
        connection,
        "heartbeats",
        {
            "heartbeat_id": "heartbeat_historical_alpha",
            "worker_id": "historical_worker",
            "lease_id": "lease_historical_alpha",
            "last_heartbeat_at": _T1,
            "last_seen_at": _T1,
            "status": "ALIVE",
            "metadata_json": "{}",
        },
    )

    event_ids = []
    if no_genesis:
        source_events = (
            {
                "event_id": "evt_historical_alpha_v2",
                "transition_key": "tr_historical_alpha_v2",
                "work_item_id": "wi_historical_alpha",
                "event_seq": 1,
                "from_state": "DISCOVERED",
                "to_state": "EVIDENCE_PENDING",
                "state_version": 2,
                "timestamp_utc": _T1,
                "artifact_hash_set": json.dumps([artifact_hash]),
                "input_artifact_ids": json.dumps(["art_historical_alpha"]),
            },
            {
                "event_id": "evt_historical_alpha_v3",
                "transition_key": "tr_historical_alpha_v3",
                "work_item_id": "wi_historical_alpha",
                "event_seq": 2,
                "from_state": "EVIDENCE_PENDING",
                "to_state": "EVIDENCE_READY",
                "state_version": 3,
                "timestamp_utc": _T2,
                "artifact_hash_set": "[]",
                "input_artifact_ids": "[]",
            },
            {
                "event_id": "evt_historical_beta_v2",
                "transition_key": "tr_historical_beta_v2",
                "work_item_id": "wi_historical_beta",
                "event_seq": 1,
                "from_state": "DISCOVERED",
                "to_state": "EVIDENCE_PENDING",
                "state_version": 2,
                "timestamp_utc": _T1,
                "artifact_hash_set": "[]",
                "input_artifact_ids": "[]",
            },
        )
        previous_hashes: Dict[str, str] = {}
        for source in source_events:
            previous_hash = previous_hashes.get(source["work_item_id"], _GENESIS_PREVIOUS_HASH)
            source_hash_material = (
                f"{source['work_item_id']}:{source['event_seq']}:{previous_hash}:"
                f"{source['from_state']}:{source['to_state']}:{source['state_version']}:"
                f"HistoricalFixture:historical_worker:HISTORICAL_FIXTURE_TRANSITION:"
                f"{source['input_artifact_ids']}:{source['timestamp_utc']}"
            )
            event_hash = _sha256(source_hash_material)
            event = {
                **source,
                "actor_class": "HistoricalFixture",
                "actor_ref": "historical_worker",
                "reason_code": "HISTORICAL_FIXTURE_TRANSITION",
                "explanation": f"Historical transition to {source['to_state']}",
                "correlation_id": f"corr_{source['event_id']}",
                "authority_granted": 0,
                "previous_event_hash": previous_hash,
                "event_hash": event_hash,
                "policy_version": "contentops.policy.v1",
                "model_version": "NOT_APPLICABLE",
                "authority_type": "NONE",
                "authority_ref": None,
                "authority_effect": "NO_AUTHORITY_GRANTED",
                "output_artifact_ids": "[]",
            }
            _insert(connection, "transition_events", event)
            previous_hashes[source["work_item_id"]] = event_hash
            event_ids.append(source["event_id"])
    else:
        for projection in projections:
            work_item_id = str(projection["work_item_id"])
            story_id = str(projection["story_id"])
            explanation = f"Genesis event for work item {work_item_id} story {story_id}"
            payload = {
                "event_schema_version": "contentops.event_payload.v1",
                "event_seq": 1,
                "work_item_id": work_item_id,
                "story_id": story_id,
                "title": projection["title"],
                "target_surface": projection["target_surface"],
                "state_version": 1,
                "from_state": "DISCOVERED",
                "to_state": "DISCOVERED",
                "previous_event_hash": _GENESIS_PREVIOUS_HASH,
                "actor_class": "ContentOpsDurableStore",
                "actor_ref": "historical_worker",
                "reason_code": "WORK_ITEM_INITIALIZATION",
                "explanation_hash": _sha256(explanation),
                "correlation_id": f"corr_init_{work_item_id}",
                "policy_version": "contentops.policy.v1",
                "model_version": "NOT_APPLICABLE",
                "authority_type": "NONE",
                "authority_ref": None,
                "authority_effect": "NO_AUTHORITY_GRANTED",
                "lease_id": None,
                "lease_key": None,
                "fencing_token": 0,
                "input_artifact_ids": [],
                "output_artifact_ids": [],
                "artifact_snapshots": [],
                "timestamp_utc": _T0,
            }
            if has_event_kind:
                payload["event_kind"] = "WORK_ITEM_CREATED"
            payload_json = json.dumps(payload, sort_keys=True)
            event_hash = _sha256(payload_json)
            event_id = f"evt_{_sha256(event_hash)[:16]}"
            event = {
                "event_id": event_id,
                "transition_key": f"tr_{work_item_id}_v1_genesis",
                "work_item_id": work_item_id,
                "event_kind": "WORK_ITEM_CREATED",
                "event_seq": 1,
                "from_state": "DISCOVERED",
                "to_state": "DISCOVERED",
                "state_version": 1,
                "actor_class": "ContentOpsDurableStore",
                "actor_ref": "historical_worker",
                "reason_code": "WORK_ITEM_INITIALIZATION",
                "explanation": explanation,
                "explanation_hash": _sha256(explanation),
                "correlation_id": f"corr_init_{work_item_id}",
                "policy_version": "contentops.policy.v1",
                "model_version": "NOT_APPLICABLE",
                "authority_type": "NONE",
                "authority_ref": None,
                "authority_effect": "NO_AUTHORITY_GRANTED",
                "lease_id": None,
                "lease_key": None,
                "fencing_token": 0,
                "input_artifact_ids": "[]",
                "output_artifact_ids": "[]",
                "artifact_snapshot_json": "[]",
                "previous_event_hash": _GENESIS_PREVIOUS_HASH,
                "event_payload_json": payload_json,
                "event_hash": event_hash,
                "timestamp_utc": _T0,
            }
            _insert(connection, "transition_events", event)
            event_ids.append(event_id)

        alpha_genesis = connection.execute(
            "SELECT event_hash FROM transition_events WHERE work_item_id='wi_historical_alpha' AND event_seq=1"
        ).fetchone()[0]
        explanation = "Historical transition to EVIDENCE_PENDING"
        transition_payload = {
            "event_schema_version": "contentops.event_payload.v1",
            "event_seq": 2,
            "work_item_id": "wi_historical_alpha",
            "story_id": "story_historical_alpha",
            "state_version": 2,
            "from_state": "DISCOVERED",
            "to_state": "EVIDENCE_PENDING",
            "previous_event_hash": alpha_genesis,
            "actor_class": "HistoricalFixture",
            "actor_ref": "historical_worker",
            "reason_code": "HISTORICAL_FIXTURE_TRANSITION",
            "explanation_hash": _sha256(explanation),
            "correlation_id": "corr_historical_alpha_v2",
            "policy_version": "contentops.policy.v1",
            "model_version": "NOT_APPLICABLE",
            "authority_type": "NONE",
            "authority_ref": None,
            "authority_effect": "NO_AUTHORITY_GRANTED",
            "lease_id": "lease_historical_alpha",
            "lease_key": "lease-key-historical-alpha",
            "fencing_token": 1,
            "input_artifact_ids": [],
            "output_artifact_ids": [],
            "artifact_snapshots": [],
            "timestamp_utc": _T1,
        }
        if has_event_kind:
            transition_payload.update(
                {
                    "event_kind": "STATE_TRANSITION",
                    "title": "Historical Alpha",
                    "target_surface": "substack",
                }
            )
        payload_json = json.dumps(transition_payload, sort_keys=True)
        event_hash = _sha256(payload_json)
        transition_event = {
            "event_id": "evt_historical_alpha_v2",
            "transition_key": "tr_historical_alpha_v2",
            "work_item_id": "wi_historical_alpha",
            "event_kind": "STATE_TRANSITION",
            "event_seq": 2,
            "from_state": "DISCOVERED",
            "to_state": "EVIDENCE_PENDING",
            "state_version": 2,
            "actor_class": "HistoricalFixture",
            "actor_ref": "historical_worker",
            "reason_code": "HISTORICAL_FIXTURE_TRANSITION",
            "explanation": explanation,
            "explanation_hash": _sha256(explanation),
            "correlation_id": "corr_historical_alpha_v2",
            "policy_version": "contentops.policy.v1",
            "model_version": "NOT_APPLICABLE",
            "authority_type": "NONE",
            "authority_ref": None,
            "authority_effect": "NO_AUTHORITY_GRANTED",
            "lease_id": "lease_historical_alpha",
            "lease_key": "lease-key-historical-alpha",
            "fencing_token": 1,
            "input_artifact_ids": "[]",
            "output_artifact_ids": "[]",
            "artifact_snapshot_json": "[]",
            "previous_event_hash": alpha_genesis,
            "event_payload_json": payload_json,
            "event_hash": event_hash,
            "timestamp_utc": _T1,
        }
        _insert(connection, "transition_events", transition_event)
        event_ids.append(transition_event["event_id"])

    return {
        "source_event_ids": tuple(event_ids),
        "work_item_projections": tuple(
            {
                key: projection[key]
                for key in (
                    "work_item_id",
                    "story_id",
                    "title",
                    "target_surface",
                    "current_state",
                    "state_version",
                    "created_at",
                    "updated_at",
                )
            }
            for projection in projections
        ),
        "expected_baseline_count": 2 if no_genesis else 0,
        "expected_genesis_count": 0 if no_genesis else 2,
        "artifact_id": "art_historical_alpha",
    }


def create_exact_historical_database(db_path: pathlib.Path, *, originating_commit: str) -> Dict[str, Any]:
    """Materialize one exact extracted schema, migration history, and operational rows."""
    lineages = load_historical_schema_extraction()
    try:
        lineage = lineages[originating_commit]
    except KeyError as exc:
        raise ValueError(f"unknown historical fixture commit: {originating_commit}") from exc

    connection = sqlite3.connect(str(db_path))
    connection.create_function("contentops_append_authorized", 0, lambda: 1)
    try:
        schema_type_order = {"table": 0, "index": 1, "trigger": 2, "view": 3}
        schema_objects = sorted(
            enumerate(lineage["schema"]),
            key=lambda item: (
                schema_type_order.get(str(item[1].get("type")), 99),
                item[0],
            ),
        )
        for _, schema_object in schema_objects:
            sql = schema_object.get("sql")
            if sql:
                connection.execute(str(sql))
        for migration_row in lineage["migration_rows"]:
            connection.execute(
                "INSERT INTO schema_migrations(version,checksum,applied_at,description) VALUES (?,?,?,?)",
                (
                    int(migration_row["version"]),
                    str(migration_row["checksum"]),
                    str(migration_row["applied_at"]),
                    str(migration_row["description"]),
                ),
            )
        fixture_evidence = _populate_operational_rows(connection)
        connection.commit()
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("exact historical fixture integrity check failed")
    finally:
        connection.close()

    return {
        "originating_commit": str(lineage["commit"]),
        "schema_fingerprint": str(lineage["fingerprint"]),
        "migration_rows": tuple(dict(row) for row in lineage["migration_rows"]),
        **fixture_evidence,
    }
