"""Single Authoritative ContentOps SQLite WAL Operational Store & Canonical State Machine v1.

Wave 02 Execution Mode: LOCAL_DURABLE_STATE_FINAL_CORRECTION_NO_LIVE_ACTION
"""
from __future__ import annotations

import hashlib
import inspect
import json
import pathlib
import re
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple, Union

from live_contentops.historical_schema_compatibility_v1 import (
    CANONICAL_SCHEMA_VERSION,
    CURRENT_MIGRATION_CHECKSUMS,
    CURRENT_MIGRATION_SQL,
    DEPENDENCY_MANIFEST_HASH,
    DEPENDENCY_MANIFEST_JSON,
    DEPENDENCY_MANIFEST_V2,
    DEPENDENCY_MANIFEST_V2_HASH,
    DEPENDENCY_MANIFEST_V2_JSON,
    DEPENDENCY_MANIFEST_V3_HASH,
    DEPENDENCY_MANIFEST_V3_JSON,
    DEPENDENCY_MANIFEST_V4_HASH,
    DEPENDENCY_MANIFEST_V4_JSON,
    DEPENDENCY_MANIFEST_V5_HASH,
    DEPENDENCY_MANIFEST_V5_JSON,
    DEPENDENCY_MANIFEST_V6_HASH,
    DEPENDENCY_MANIFEST_V6_JSON,
    DEPENDENCY_MANIFEST_V7_HASH,
    DEPENDENCY_MANIFEST_V7_JSON,
    LEGACY_QUARANTINE_SCOPE,
    MIGRATION_V5_CHECKSUM,
    MIGRATION_V5_SQL,
    MIGRATION_V6_SQL,
    MIGRATION_V7_SQL,
    MIGRATION_V8_SQL,
    MIGRATION_V9_SQL,
    canonical_json,
    recognize_lineage,
    schema_fingerprint,
    upgrade_historical_database,
)

SCHEMA_VERSION = CANONICAL_SCHEMA_VERSION
BUSY_TIMEOUT_MS = 5000
EVENT_SCHEMA_VERSION = "contentops.event_payload.v1"
LEGACY_EVENT_SCHEMA_VERSION = "contentops.event_payload.legacy_v1"
HISTORICAL_EVENT_SCHEMA_VERSION = "contentops.event_payload.historical_v1"
LEGACY_BASELINE_EVENT_SCHEMA_VERSION = "contentops.event_payload.legacy_projection_baseline.v1"
ACCEPTED_EVENT_SCHEMA_VERSIONS = frozenset({
    EVENT_SCHEMA_VERSION,
    LEGACY_EVENT_SCHEMA_VERSION,
    HISTORICAL_EVENT_SCHEMA_VERSION,
    LEGACY_BASELINE_EVENT_SCHEMA_VERSION,
})
GENESIS_EVENT_KIND = "WORK_ITEM_CREATED"
GENESIS_PREVIOUS_HASH = "GENESIS_" + "0" * 64
ARTIFACT_SCOPES = frozenset({"WORK_ITEM_EXACT", "STORY_EXACT", "GLOBAL_REUSABLE", LEGACY_QUARANTINE_SCOPE})
ACTIVE_ARTIFACT_SCOPES = frozenset({"WORK_ITEM_EXACT", "STORY_EXACT", "GLOBAL_REUSABLE"})
DESTINATION_READINESS_STATES = frozenset({
    "READY_AUTHENTICATED", "READY_NON_BROWSER_BINDING", "REAUTH_REQUIRED",
    "AUTH_INVALID", "IDENTITY_MISMATCH", "PERMISSION_MISSING", "SESSION_UNAVAILABLE",
    "TRANSPORT_UNAVAILABLE", "TRANSIENT_DEGRADED", "CAPABILITY_UNSUPPORTED",
    "LAST_VERIFIED_READY", "STALE_NEEDS_JIT_VERIFICATION",
})
PROTECTED_INSERT_TABLES = frozenset({"transition_events", "artifact_references"})
RUNTIME_INSERT_GUARD_SQL = (
    "CREATE TRIGGER IF NOT EXISTS trg_transition_events_append_authorized BEFORE INSERT ON transition_events BEGIN SELECT CASE WHEN contentops_append_authorized() != 1 THEN RAISE(ABORT,'transition_events INSERT requires canonical append authorization') END; END",
    "CREATE TRIGGER IF NOT EXISTS trg_artifact_references_insert_authorized BEFORE INSERT ON artifact_references BEGIN SELECT CASE WHEN contentops_artifact_insert_authorized() != 1 THEN RAISE(ABORT,'artifact_references INSERT requires canonical registration authorization') END; END",
)

CANONICAL_STATES = frozenset({
    "DISCOVERED", "EVIDENCE_PENDING", "EVIDENCE_READY", "EVIDENCE_BLOCKED",
    "ASSIGNMENT_CANDIDATE", "ASSIGNED", "DEFERRED", "DUPLICATE", "REJECTED",
    "PRODUCTION_IN_PROGRESS", "REVIEW_BLOCKED", "REVIEW_READY", "OPERATOR_PENDING",
    "APPROVED_EXACT", "HELD", "EXPIRED", "OUTBOX_READY", "DISPATCHING",
    "PARTIAL_SUCCESS", "UNKNOWN_WRITE", "DISPATCH_BLOCKED", "DISPATCH_COMPLETE",
    "RECONCILING", "COMPLETE", "DEAD_LETTER", "OPERATOR_RECOVERY_REQUIRED",
    "OBSERVATION_PENDING", "LEARNING_REVIEW_READY", "CLOSED",
})
WAVE02_PROTECTED_STATES = frozenset({
    "APPROVED_EXACT", "OUTBOX_READY", "DISPATCHING", "PARTIAL_SUCCESS",
    "UNKNOWN_WRITE", "DISPATCH_BLOCKED", "DISPATCH_COMPLETE", "RECONCILING", "COMPLETE",
})
STATE_TRANSITION_GRAPH: Dict[str, set[str]] = {
    "DISCOVERED": {"EVIDENCE_PENDING"},
    "EVIDENCE_PENDING": {"EVIDENCE_READY", "EVIDENCE_BLOCKED"},
    "EVIDENCE_READY": {"ASSIGNMENT_CANDIDATE"},
    "EVIDENCE_BLOCKED": {"DEFERRED", "REJECTED"},
    "ASSIGNMENT_CANDIDATE": {"ASSIGNED", "DEFERRED", "DUPLICATE", "REJECTED"},
    "ASSIGNED": {"PRODUCTION_IN_PROGRESS"},
    "PRODUCTION_IN_PROGRESS": {"REVIEW_BLOCKED", "REVIEW_READY"},
    "REVIEW_BLOCKED": {"HELD", "REJECTED"},
    "REVIEW_READY": {"OPERATOR_PENDING"},
    "OPERATOR_PENDING": {"APPROVED_EXACT", "HELD", "REJECTED", "EXPIRED"},
    "APPROVED_EXACT": {"OUTBOX_READY"}, "HELD": {"DEFERRED", "REJECTED"},
    "EXPIRED": {"CLOSED"}, "OUTBOX_READY": {"DISPATCHING"},
    "DISPATCHING": {"PARTIAL_SUCCESS", "UNKNOWN_WRITE", "DISPATCH_BLOCKED", "DISPATCH_COMPLETE"},
    "PARTIAL_SUCCESS": {"RECONCILING", "OPERATOR_RECOVERY_REQUIRED"},
    "UNKNOWN_WRITE": {"RECONCILING", "OPERATOR_RECOVERY_REQUIRED"},
    "DISPATCH_BLOCKED": {"HELD", "DEAD_LETTER"}, "DISPATCH_COMPLETE": {"RECONCILING"},
    "RECONCILING": {"COMPLETE", "DEAD_LETTER", "OPERATOR_RECOVERY_REQUIRED"},
    "COMPLETE": {"OBSERVATION_PENDING"}, "DEAD_LETTER": {"OPERATOR_RECOVERY_REQUIRED", "CLOSED"},
    "OPERATOR_RECOVERY_REQUIRED": {"ASSIGNMENT_CANDIDATE", "CLOSED"},
    "OBSERVATION_PENDING": {"LEARNING_REVIEW_READY"}, "LEARNING_REVIEW_READY": {"CLOSED"},
    "CLOSED": set(), "DEFERRED": {"ASSIGNMENT_CANDIDATE"}, "DUPLICATE": {"CLOSED"},
    "REJECTED": {"CLOSED"},
}
HISTORICAL_MIGRATION_STATE_EDGES = frozenset({
    ("EVIDENCE_READY", "ASSIGNED"),
})

class DurableStoreError(Exception): pass
class MigrationError(DurableStoreError): pass
class InvalidStateTransitionError(DurableStoreError): pass
class CASStateConflictError(DurableStoreError): pass
class TransitionValidationError(DurableStoreError): pass
class WorkItemNotFoundError(DurableStoreError): pass
class StaleFencingTokenError(DurableStoreError): pass
class LeaseConflictError(DurableStoreError): pass
class DurableStateCorruptionError(DurableStoreError): pass
class Wave02AuthorityViolationError(DurableStoreError): pass
class ArtifactNotFoundError(DurableStoreError): pass
class ArtifactValidationError(DurableStoreError): pass
class DispatchIdentityConflictError(DurableStoreError):
    """A re-registration attempted to replace an already-persisted exact public-object identity.

    External public-object identity is write-once durable truth. The same dispatch with the same
    identity is idempotent; a conflicting identity fails closed and is never silently overwritten.
    """


class PerformanceObservationConflictError(DurableStoreError):
    """A repeated observation identity carried different content.

    Re-collecting the SAME exact observation identity is idempotent, but a conflicting content
    hash for the same identity must never silently overwrite historical numbers.
    """


class LearningPolicyConflictError(DurableStoreError):
    """A learning-policy version is immutable; a conflicting re-registration fails closed."""


class OperatingModeConflictError(DurableStoreError):
    """The expected durable mode-control version did not match current state."""


class OperatorTriggerAlreadyPendingError(DurableStoreError):
    """At most one PENDING operator-requested cycle trigger may exist at a time.

    The partial unique index enforces this durably; repeated HTTP retries/double clicks are
    idempotent and never create duplicate editorial executions. The existing pending trigger
    identity is returned instead of a second row.
    """


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def compute_sha256(data: Union[str, bytes]) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()

def is_valid_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", value or ""))

# ``canonical_json`` is deliberately NOT redefined here. It is imported from
# live_contentops.historical_schema_compatibility_v1 so that the migration writer and
# the replay verifier share one byte-identical encoder. Re-defining it locally caused a
# silent event-payload hash mismatch on any non-ASCII content.

def split_sql_statements(sql_script: str) -> List[str]:
    """Split a migration script only at SQLite-complete statement boundaries."""
    statements: List[str] = []
    current: List[str] = []
    for character in sql_script:
        current.append(character)
        if character != ";":
            continue
        candidate = "".join(current).strip()
        if candidate and sqlite3.complete_statement(candidate):
            statements.append(candidate)
            current = []
    remainder = "".join(current).strip()
    if remainder:
        if not sqlite3.complete_statement(remainder):
            raise MigrationError("Migration SQL ended with an incomplete statement")
        statements.append(remainder)
    return statements

MIGRATION_V1_SQL = r"""
CREATE TABLE IF NOT EXISTS schema_migrations (
 version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL, description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS operational_windows (window_id TEXT PRIMARY KEY, window_key TEXT NOT NULL UNIQUE, started_at TEXT NOT NULL, closed_at TEXT, status TEXT NOT NULL CHECK(status IN ('ACTIVE','CLOSED','HALTED')));
CREATE TABLE IF NOT EXISTS scheduler_ticks (tick_id TEXT PRIMARY KEY, window_id TEXT NOT NULL, tick_number INTEGER NOT NULL, evaluated_at TEXT NOT NULL, work_items_evaluated INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(window_id) REFERENCES operational_windows(window_id));
CREATE TABLE IF NOT EXISTS work_items (work_item_id TEXT PRIMARY KEY, story_id TEXT NOT NULL, title TEXT NOT NULL, current_state TEXT NOT NULL, state_version INTEGER NOT NULL DEFAULT 1, target_surface TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS story_versions (story_version_id TEXT PRIMARY KEY, story_id TEXT NOT NULL, version_num INTEGER NOT NULL, headline TEXT NOT NULL, body_text TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assignments (assignment_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, assignee_ref TEXT NOT NULL, assigned_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ACTIVE','RELEASED','COMPLETED')), FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS artifact_references (artifact_id TEXT PRIMARY KEY, artifact_type TEXT NOT NULL, story_id TEXT, work_item_id TEXT, storage_class TEXT NOT NULL, byte_length INTEGER NOT NULL, sha256_hash TEXT NOT NULL, schema_version TEXT NOT NULL, created_at TEXT NOT NULL, producer_ref TEXT NOT NULL, sensitivity_class TEXT NOT NULL DEFAULT 'PUBLIC', FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS transition_events (event_id TEXT PRIMARY KEY, transition_key TEXT NOT NULL UNIQUE, work_item_id TEXT NOT NULL, from_state TEXT NOT NULL, to_state TEXT NOT NULL, state_version INTEGER NOT NULL, actor_class TEXT NOT NULL, actor_ref TEXT NOT NULL, reason_code TEXT NOT NULL, explanation TEXT NOT NULL, artifact_hash_set TEXT NOT NULL, correlation_id TEXT NOT NULL, timestamp_utc TEXT NOT NULL, authority_granted INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS model_invocations (invocation_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, model_id TEXT NOT NULL, prompt_tokens INTEGER NOT NULL DEFAULT 0, completion_tokens INTEGER NOT NULL DEFAULT 0, invoked_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS review_records (review_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, reviewer_ref TEXT NOT NULL, decision TEXT NOT NULL, notes TEXT NOT NULL, reviewed_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS operator_decisions (decision_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, operator_ref TEXT NOT NULL, action TEXT NOT NULL, notes TEXT NOT NULL, decided_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS leases (lease_id TEXT PRIMARY KEY, lease_key TEXT NOT NULL UNIQUE, work_item_id TEXT, owner_ref TEXT NOT NULL, fencing_token INTEGER NOT NULL, acquired_at TEXT NOT NULL, renewed_at TEXT NOT NULL, expires_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ACTIVE','EXPIRED','RELEASED')), FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS heartbeats (heartbeat_id TEXT PRIMARY KEY, worker_id TEXT NOT NULL UNIQUE, lease_id TEXT, last_seen_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ALIVE','DEAD')), FOREIGN KEY(lease_id) REFERENCES leases(lease_id));
CREATE TABLE IF NOT EXISTS approval_envelopes (envelope_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, approved_by TEXT NOT NULL, expires_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'HELD', FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS outbox_messages (message_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, destination TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', created_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS platform_dispatches (dispatch_id TEXT PRIMARY KEY, message_id TEXT NOT NULL, platform TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', dispatched_at TEXT NOT NULL, FOREIGN KEY(message_id) REFERENCES outbox_messages(message_id));
CREATE TABLE IF NOT EXISTS readbacks (readback_id TEXT PRIMARY KEY, dispatch_id TEXT NOT NULL, readback_data TEXT NOT NULL, read_at TEXT NOT NULL, FOREIGN KEY(dispatch_id) REFERENCES platform_dispatches(dispatch_id));
CREATE TABLE IF NOT EXISTS reconciliations (reconciliation_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', reconciled_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));
CREATE TABLE IF NOT EXISTS incidents (incident_id TEXT PRIMARY KEY, work_item_id TEXT, severity TEXT NOT NULL, description TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS metrics (metric_id TEXT PRIMARY KEY, metric_name TEXT NOT NULL, metric_value REAL NOT NULL, recorded_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS feedback_records (feedback_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, source TEXT NOT NULL, rating REAL, recorded_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS learning_reviews (review_id TEXT PRIMARY KEY, summary TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS trg_transition_events_no_update BEFORE UPDATE ON transition_events BEGIN SELECT RAISE(ABORT,'transition_events are append-only: UPDATE forbidden'); END;
CREATE TRIGGER IF NOT EXISTS trg_transition_events_no_delete BEFORE DELETE ON transition_events BEGIN SELECT RAISE(ABORT,'transition_events are append-only: DELETE forbidden'); END;
"""

MIGRATION_V2_SQL = r"""
ALTER TABLE transition_events ADD COLUMN event_seq INTEGER;
ALTER TABLE transition_events ADD COLUMN previous_event_hash TEXT;
ALTER TABLE transition_events ADD COLUMN event_hash TEXT;
ALTER TABLE transition_events ADD COLUMN policy_version TEXT NOT NULL DEFAULT 'contentops.policy.v1';
ALTER TABLE transition_events ADD COLUMN model_version TEXT NOT NULL DEFAULT 'NOT_APPLICABLE';
ALTER TABLE transition_events ADD COLUMN authority_type TEXT NOT NULL DEFAULT 'NONE';
ALTER TABLE transition_events ADD COLUMN authority_ref TEXT;
ALTER TABLE transition_events ADD COLUMN authority_effect TEXT NOT NULL DEFAULT 'NO_AUTHORITY_GRANTED';
ALTER TABLE transition_events ADD COLUMN input_artifact_ids TEXT NOT NULL DEFAULT '[]';
ALTER TABLE transition_events ADD COLUMN output_artifact_ids TEXT NOT NULL DEFAULT '[]';
"""

MIGRATION_V3_SQL = r"""
CREATE TABLE transition_events_v3 (
 event_id TEXT PRIMARY KEY, transition_key TEXT NOT NULL UNIQUE, work_item_id TEXT NOT NULL,
 event_kind TEXT NOT NULL, event_seq INTEGER NOT NULL, from_state TEXT NOT NULL, to_state TEXT NOT NULL,
 state_version INTEGER NOT NULL, actor_class TEXT NOT NULL, actor_ref TEXT NOT NULL,
 reason_code TEXT NOT NULL, explanation TEXT NOT NULL, explanation_hash TEXT NOT NULL,
 correlation_id TEXT NOT NULL, policy_version TEXT NOT NULL, model_version TEXT NOT NULL,
 authority_type TEXT NOT NULL, authority_ref TEXT, authority_effect TEXT NOT NULL,
 lease_id TEXT, lease_key TEXT, fencing_token INTEGER NOT NULL, input_artifact_ids TEXT NOT NULL,
 output_artifact_ids TEXT NOT NULL, artifact_snapshot_json TEXT NOT NULL, previous_event_hash TEXT NOT NULL,
 event_payload_json TEXT NOT NULL, event_hash TEXT NOT NULL, timestamp_utc TEXT NOT NULL,
 FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);
ALTER TABLE artifact_references ADD COLUMN artifact_scope TEXT NOT NULL DEFAULT 'STORY_EXACT';
ALTER TABLE artifact_references ADD COLUMN receipt_id TEXT;
ALTER TABLE artifact_references ADD COLUMN receipt_schema TEXT;
ALTER TABLE artifact_references ADD COLUMN receipt_source_identity TEXT;
ALTER TABLE artifact_references ADD COLUMN receipt_object_identity TEXT;
ALTER TABLE artifact_references ADD COLUMN receipt_verifier_identity TEXT;
ALTER TABLE artifact_references ADD COLUMN canonical_receipt_hash TEXT;
"""


def _migration_v2_transform(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT rowid AS legacy_rowid,* FROM transition_events").fetchall()
    grouped: Dict[str, List[sqlite3.Row]] = {}
    for row in rows:
        grouped.setdefault(row["work_item_id"], []).append(row)
    for work_item_id, events in grouped.items():
        state_versions = [int(row["state_version"]) for row in events]
        if sorted(state_versions) != list(range(1, len(events) + 1)):
            raise MigrationError(f"Ambiguous legacy event ordering for work item {work_item_id}: state versions are not unique and contiguous")
        ordered = sorted(events, key=lambda row: int(row["state_version"]))
        timestamps = [str(row["timestamp_utc"]) for row in ordered]
        if len(timestamps) != len(set(timestamps)) or timestamps != sorted(timestamps):
            raise MigrationError(f"Ambiguous legacy event ordering for work item {work_item_id}: timestamps are duplicate or conflict with state versions")
    conn.execute("DROP TRIGGER IF EXISTS trg_transition_events_no_update")
    conn.execute("DROP TRIGGER IF EXISTS trg_transition_events_no_delete")
    for events in grouped.values():
        for seq, row in enumerate(sorted(events, key=lambda value: int(value["state_version"])), 1):
            conn.execute("UPDATE transition_events SET event_seq=? WHERE rowid=?", (seq, row["legacy_rowid"]))
    conn.execute("CREATE UNIQUE INDEX idx_transition_events_work_item_seq ON transition_events(work_item_id,event_seq)")
    conn.execute("CREATE TRIGGER trg_transition_events_no_update BEFORE UPDATE ON transition_events BEGIN SELECT RAISE(ABORT,'transition_events are append-only: UPDATE forbidden'); END")
    conn.execute("CREATE TRIGGER trg_transition_events_no_delete BEFORE DELETE ON transition_events BEGIN SELECT RAISE(ABORT,'transition_events are append-only: DELETE forbidden'); END")


def _legacy_artifact_ids(raw: str) -> List[str]:
    try:
        value = json.loads(raw or "[]")
        return sorted(str(v) for v in value) if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def _migration_v3_transform(conn: sqlite3.Connection) -> None:
    legacy_fields = (
        "event_id", "transition_key", "work_item_id", "from_state", "to_state", "state_version",
        "actor_class", "actor_ref", "reason_code", "explanation", "artifact_hash_set",
        "correlation_id", "timestamp_utc", "authority_granted",
    )
    conn.execute("""UPDATE artifact_references
                    SET artifact_scope=CASE
                        WHEN work_item_id IS NOT NULL THEN 'WORK_ITEM_EXACT'
                        WHEN story_id IS NOT NULL THEN 'STORY_EXACT'
                        ELSE 'GLOBAL_REUSABLE' END""")
    rows = conn.execute("SELECT t.*,w.story_id,w.title,w.target_surface FROM transition_events t JOIN work_items w USING(work_item_id) ORDER BY t.work_item_id,t.event_seq").fetchall()
    prior: Dict[str, str] = {}
    for row in rows:
        kind = GENESIS_EVENT_KIND if row["event_seq"] == 1 and row["state_version"] == 1 and row["to_state"] == "DISCOVERED" else "STATE_TRANSITION"
        previous_hash = prior.get(row["work_item_id"], GENESIS_PREVIOUS_HASH)
        explanation_hash = compute_sha256(row["explanation"])
        raw_artifact_values = _legacy_artifact_ids(row["artifact_hash_set"])
        resolved_ids: List[str] = []
        snapshots: List[Dict[str, Any]] = []
        for artifact_id in raw_artifact_values:
            artifact = conn.execute("SELECT * FROM artifact_references WHERE artifact_id=?", (artifact_id,)).fetchone()
            if artifact is None:
                continue
            if artifact["artifact_scope"] == "WORK_ITEM_EXACT" and (
                artifact["story_id"] != row["story_id"] or artifact["work_item_id"] != row["work_item_id"]
            ):
                raise MigrationError(f"Legacy artifact {artifact_id} violates exact work-item scope")
            if artifact["artifact_scope"] == "STORY_EXACT" and artifact["story_id"] != row["story_id"]:
                raise MigrationError(f"Legacy artifact {artifact_id} violates exact story scope")
            resolved_ids.append(artifact_id)
            snapshots.append({key: artifact[key] for key in (
                "artifact_id", "artifact_type", "story_id", "work_item_id", "artifact_scope", "storage_class",
                "byte_length", "sha256_hash", "schema_version", "producer_ref", "receipt_id", "receipt_schema",
                "receipt_source_identity", "receipt_object_identity", "receipt_verifier_identity", "canonical_receipt_hash",
            )})
        source_record = {field: row[field] for field in legacy_fields}
        payload = build_event_envelope(
            event_schema_version=LEGACY_EVENT_SCHEMA_VERSION, event_kind=kind,
            event_seq=row["event_seq"], work_item_id=row["work_item_id"], story_id=row["story_id"],
            title=row["title"], target_surface=row["target_surface"], state_version=row["state_version"],
            from_state=row["from_state"], to_state=row["to_state"], previous_event_hash=previous_hash,
            actor_class=row["actor_class"], actor_ref=row["actor_ref"], reason_code=row["reason_code"],
            explanation_hash=explanation_hash, correlation_id=row["correlation_id"],
            policy_version="LEGACY_UNKNOWN", model_version="LEGACY_UNKNOWN",
            authority_type="LEGACY_UNKNOWN" if row["authority_granted"] else "NONE",
            authority_ref=None,
            authority_effect="LEGACY_FLAG_NOT_ACCEPTED_AS_AUTHORITY" if row["authority_granted"] else "NO_AUTHORITY_GRANTED",
            lease_id=None, lease_key=None, fencing_token=0, input_artifact_ids=resolved_ids,
            output_artifact_ids=[], artifact_snapshots=snapshots, timestamp_utc=row["timestamp_utc"],
        )
        payload["legacy_migration"] = {
            "source_record": source_record,
            "unresolved_artifact_values": sorted(set(raw_artifact_values) - set(resolved_ids)),
            "unknown_fields": [
                "event_kind", "previous_event_hash", "event_hash", "policy_version", "model_version",
                "authority_type", "authority_ref", "authority_effect", "lease_id", "lease_key",
                "fencing_token", "input_output_artifact_roles",
            ],
        }
        payload_json = canonical_json(payload)
        event_hash = compute_sha256(payload_json)
        conn.execute("""INSERT INTO transition_events_v3 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            row["event_id"], row["transition_key"], row["work_item_id"], kind, row["event_seq"],
            row["from_state"], row["to_state"], row["state_version"], row["actor_class"], row["actor_ref"],
            row["reason_code"], row["explanation"], explanation_hash, row["correlation_id"], payload["policy_version"],
            payload["model_version"], payload["authority_type"], None, payload["authority_effect"], None, None, 0,
            canonical_json(resolved_ids), "[]", canonical_json(snapshots), previous_hash, payload_json, event_hash,
            row["timestamp_utc"],
        ))
        prior[row["work_item_id"]] = event_hash
    conn.execute("DROP TRIGGER IF EXISTS trg_transition_events_no_update")
    conn.execute("DROP TRIGGER IF EXISTS trg_transition_events_no_delete")
    conn.execute("DROP TABLE transition_events")
    conn.execute("ALTER TABLE transition_events_v3 RENAME TO transition_events")
    conn.execute("CREATE UNIQUE INDEX idx_transition_events_work_item_seq ON transition_events(work_item_id,event_seq)")
    conn.execute("CREATE UNIQUE INDEX idx_assignments_one_active_per_work_item ON assignments(work_item_id) WHERE status='ACTIVE'")
    conn.execute("CREATE TRIGGER trg_transition_events_append_authorized BEFORE INSERT ON transition_events BEGIN SELECT CASE WHEN contentops_append_authorized() != 1 THEN RAISE(ABORT,'transition_events INSERT requires canonical append authorization') END; END")
    conn.execute("CREATE TRIGGER trg_transition_events_no_update BEFORE UPDATE ON transition_events BEGIN SELECT RAISE(ABORT,'transition_events are append-only: UPDATE forbidden'); END")
    conn.execute("CREATE TRIGGER trg_transition_events_no_delete BEFORE DELETE ON transition_events BEGIN SELECT RAISE(ABORT,'transition_events are append-only: DELETE forbidden'); END")
    conn.execute("CREATE TRIGGER trg_artifact_references_no_update BEFORE UPDATE ON artifact_references BEGIN SELECT RAISE(ABORT,'artifact_references are immutable: UPDATE forbidden'); END")
    conn.execute("CREATE TRIGGER trg_artifact_references_no_delete BEFORE DELETE ON artifact_references BEGIN SELECT RAISE(ABORT,'artifact_references are immutable: DELETE forbidden'); END")

@dataclass(frozen=True)
class Migration:
    version: int
    description: str
    sql: str
    transform_version: str
    transform: Optional[Callable[[sqlite3.Connection], None]] = None

    @property
    def transform_source_hash(self) -> str:
        return compute_sha256(inspect.getsource(self.transform) if self.transform else "NO_TRANSFORM")

    @property
    def checksum(self) -> str:
        frozen = CURRENT_MIGRATION_CHECKSUMS.get(self.version)
        if frozen is not None:
            return frozen
        return compute_sha256(canonical_json({"sql": self.sql, "transform_version": self.transform_version, "transform_source_hash": self.transform_source_hash}))

    def __iter__(self):
        return iter((self.version, self.description, self.sql))

MIGRATIONS: List[Migration] = [
    Migration(1, "Initial Wave 02 Durable Operational Store Schema", MIGRATION_V1_SQL, "sql_only.v1"),
    Migration(2, "Deterministic legacy sequence assignment", MIGRATION_V2_SQL, "legacy_sequence.v2", _migration_v2_transform),
    Migration(3, "Canonical event envelopes, receipt scope, and append guards", MIGRATION_V3_SQL, "legacy_envelope.v3", _migration_v3_transform),
    Migration(4, "Wave 02 Schema v4: Historical Lineage Compatibility and Dependency Manifest", CURRENT_MIGRATION_SQL[4], "historical_lineage_compatibility.v4"),
    Migration(5, "Schema v5: platform_dispatches public-object identity persistence", MIGRATION_V5_SQL, "sql_only.v5"),
    Migration(6, "Schema v6: performance_observations and learning_policy_versions", MIGRATION_V6_SQL, "sql_only.v6"),
    Migration(7, "Schema v7: canonical operating-mode control", MIGRATION_V7_SQL, "sql_only.v7"),
    Migration(8, "Schema v8: current destination readiness", MIGRATION_V8_SQL, "sql_only.v8"),
    Migration(9, "Schema v9: append-only operator-requested cycle triggers", MIGRATION_V9_SQL, "sql_only.v9"),
]


def build_event_envelope(**fields: Any) -> Dict[str, Any]:
    required = (
        "event_schema_version", "event_kind", "event_seq", "work_item_id", "story_id", "title",
        "target_surface", "state_version", "from_state", "to_state", "previous_event_hash",
        "actor_class", "actor_ref", "reason_code", "explanation_hash", "correlation_id",
        "policy_version", "model_version", "authority_type", "authority_ref", "authority_effect",
        "lease_id", "lease_key", "fencing_token", "input_artifact_ids", "output_artifact_ids",
        "artifact_snapshots", "timestamp_utc",
    )
    missing = [key for key in required if key not in fields]
    if missing:
        raise TransitionValidationError(f"Missing event envelope fields: {missing}")
    envelope = {key: fields[key] for key in required}
    envelope["input_artifact_ids"] = sorted(set(envelope["input_artifact_ids"]))
    envelope["output_artifact_ids"] = sorted(set(envelope["output_artifact_ids"]))
    envelope["artifact_snapshots"] = sorted(envelope["artifact_snapshots"], key=lambda s: s["artifact_id"])
    return envelope


class ContentOpsDurableStore:
    def __init__(self, db_path: pathlib.Path, busy_timeout_ms: int = BUSY_TIMEOUT_MS, auto_migrate: bool = True,
                 now_fn: Optional[Callable[[], datetime]] = None,
                 receipt_resolvers: Optional[Mapping[str, Callable[[Mapping[str, Any]], Any]]] = None) -> None:
        self.db_path = pathlib.Path(db_path).resolve(); self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.busy_timeout_ms = busy_timeout_ms; self._now_fn = now_fn
        self._write_local = threading.local(); self._receipt_resolvers = dict(receipt_resolvers or {})
        self.migration_proofs: List[Dict[str, Any]] = []
        if auto_migrate: self.run_migrations()

    def _get_now(self) -> datetime:
        now = self._now_fn() if self._now_fn else datetime.now(timezone.utc)
        return now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now.astimezone(timezone.utc)
    def _get_now_iso(self) -> str: return self._get_now().isoformat()
    def _append_authorized(self) -> int: return int(bool(getattr(self._write_local, "append_enabled", False)))
    def _artifact_insert_authorized(self) -> int: return int(bool(getattr(self._write_local, "artifact_insert_enabled", False)))
    def _connection_authorizer(self, action: int, argument_1: Optional[str], _argument_2: Optional[str],
                               _database: Optional[str], _trigger: Optional[str]) -> int:
        if action == sqlite3.SQLITE_INSERT and argument_1 == "transition_events" and not self._append_authorized():
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_INSERT and argument_1 == "artifact_references" and not self._artifact_insert_authorized():
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    @contextmanager
    def _canonical_append(self) -> Iterator[None]:
        previous = bool(getattr(self._write_local, "append_enabled", False)); self._write_local.append_enabled = True
        try: yield
        finally: self._write_local.append_enabled = previous
    @contextmanager
    def _canonical_artifact_insert(self) -> Iterator[None]:
        previous = bool(getattr(self._write_local, "artifact_insert_enabled", False)); self._write_local.artifact_insert_enabled = True
        try: yield
        finally: self._write_local.artifact_insert_enabled = previous

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.db_path), timeout=self.busy_timeout_ms / 1000.0, isolation_level=None,
            cached_statements=0,
        )
        conn.row_factory = sqlite3.Row
        conn.create_function("contentops_append_authorized", 0, self._append_authorized)
        conn.create_function("contentops_artifact_insert_authorized", 0, self._artifact_insert_authorized)
        conn.set_authorizer(self._connection_authorizer)
        conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA foreign_keys=ON"); conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
        return conn
    def get_read_only_connection(self) -> sqlite3.Connection:
        """Open the configured canonical store in SQLite read-only/query-only mode."""
        conn = sqlite3.connect(
            f"file:{self.db_path.as_posix()}?mode=ro", uri=True,
            timeout=self.busy_timeout_ms / 1000.0, isolation_level=None, cached_statements=0,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
        return conn
    def _ensure_runtime_write_guards(self) -> None:
        with self.get_connection() as conn:
            for statement in RUNTIME_INSERT_GUARD_SQL:
                conn.execute(statement)
    def query_pragmas(self) -> Dict[str, Any]:
        with self.get_connection() as c: return {"journal_mode": str(c.execute("PRAGMA journal_mode").fetchone()[0]).upper(), "foreign_keys": int(c.execute("PRAGMA foreign_keys").fetchone()[0]), "busy_timeout_ms": int(c.execute("PRAGMA busy_timeout").fetchone()[0])}
    def verify_schema_integrity(self) -> bool:
        with self.get_connection() as c:
            result = c.execute("PRAGMA integrity_check").fetchone()[0]
            if str(result).lower() != "ok": raise DurableStateCorruptionError(str(result))
            current_row = c.execute(
                "SELECT MAX(version) FROM schema_migrations"
            ).fetchone() if c.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
            ).fetchone()[0] else None
            if current_row and int(current_row[0] or 0) >= CANONICAL_SCHEMA_VERSION:
                metadata_table = c.execute(
                    "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_lineage_metadata'"
                ).fetchone()[0]
                if metadata_table != 1:
                    raise DurableStateCorruptionError("Schema lineage metadata missing")
                rows = c.execute("SELECT * FROM schema_lineage_metadata").fetchall()
                if (
                    len(rows) != 1
                    or int(rows[0]["singleton_id"]) != 1
                    or int(rows[0]["compatibility_version"]) != CANONICAL_SCHEMA_VERSION
                    or rows[0]["dependency_manifest_json"] not in (DEPENDENCY_MANIFEST_JSON, DEPENDENCY_MANIFEST_V2_JSON, DEPENDENCY_MANIFEST_V3_JSON, DEPENDENCY_MANIFEST_V4_JSON, DEPENDENCY_MANIFEST_V5_JSON, DEPENDENCY_MANIFEST_V6_JSON, DEPENDENCY_MANIFEST_V7_JSON)
                    or rows[0]["dependency_manifest_hash"] not in (DEPENDENCY_MANIFEST_HASH, DEPENDENCY_MANIFEST_V2_HASH, DEPENDENCY_MANIFEST_V3_HASH, DEPENDENCY_MANIFEST_V4_HASH, DEPENDENCY_MANIFEST_V5_HASH, DEPENDENCY_MANIFEST_V6_HASH, DEPENDENCY_MANIFEST_V7_HASH)
                ):
                    raise DurableStateCorruptionError("Dependency manifest binding mismatch")
                guard_rows = {
                    row["name"]: str(row["sql"] or "")
                    for row in c.execute(
                        "SELECT name,sql FROM sqlite_master WHERE type='trigger' AND name IN (?,?)",
                        ("trg_transition_events_append_authorized", "trg_artifact_references_insert_authorized"),
                    ).fetchall()
                }
                required_guards = {
                    "trg_transition_events_append_authorized": "contentops_append_authorized",
                    "trg_artifact_references_insert_authorized": "contentops_artifact_insert_authorized",
                }
                for trigger_name, function_name in required_guards.items():
                    sql = guard_rows.get(trigger_name, "").lower()
                    if "before insert" not in sql or function_name not in sql:
                        raise DurableStateCorruptionError(f"Runtime insert guard missing or invalid: {trigger_name}")
        return True
    def get_current_schema_version(self) -> int:
        c=self.get_connection()
        try:
            if not c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()[0]: return 0
            row = c.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]; return int(row or 0)
        finally: c.close()
    def verify_applied_migrations(self) -> bool:
        with self.get_connection() as c:
            if not c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()[0]: return True
            rows = c.execute("SELECT * FROM schema_migrations ORDER BY version").fetchall(); registry = {m.version: m for m in MIGRATIONS}
            versions = [r["version"] for r in rows]
            if versions != list(range(1, len(versions) + 1)): raise MigrationError("Non-contiguous or missing applied migration history")
            if versions and max(versions) > max(registry): raise MigrationError("Database schema is ahead of embedded registry")
            for row in rows:
                if row["version"] not in registry: raise MigrationError(f"Unknown migration version {row['version']}")
                if row["checksum"] != registry[row["version"]].checksum: raise MigrationError(f"Checksum drift for migration v{row['version']}")
        return True
    def create_wal_safe_backup(self) -> pathlib.Path:
        path = self.db_path.parent / f"{self.db_path.name}.bak.{self._get_now().strftime('%Y%m%d_%H%M%S_%f')}"
        with self.get_connection() as source:
            source.execute("PRAGMA wal_checkpoint(TRUNCATE)"); dest = sqlite3.connect(str(path))
            try: source.backup(dest)
            finally: dest.close()
        return path
    def restore_from_backup(self, backup_path: pathlib.Path) -> None:
        if not backup_path.exists(): raise MigrationError(f"Backup path {backup_path} does not exist")
        source = sqlite3.connect(str(backup_path)); destination = sqlite3.connect(str(self.db_path))
        try:
            source.backup(destination)
        finally:
            destination.close(); source.close()
    def run_migrations(self, target_version: Optional[int] = None) -> int:
        current = self.get_current_schema_version()
        if current and current < CANONICAL_SCHEMA_VERSION and self.db_path.exists():
            conn = self.get_connection()
            try:
                recorded = tuple((int(row[0]), str(row[1])) for row in conn.execute(
                    "SELECT version,checksum FROM schema_migrations ORDER BY version"
                ).fetchall())
                expected_checksums = {m.version: m.checksum for m in MIGRATIONS}
                current_prefix = tuple((version, expected_checksums[version]) for version in range(1, current + 1))
                if recorded != current_prefix:
                    recognize_lineage(conn)
                    if target_version is not None and target_version < CANONICAL_SCHEMA_VERSION:
                        return 0
                    conn.close()
                    proof = upgrade_historical_database(self.db_path, now_iso=self._get_now_iso())
                    self.migration_proofs.append(proof)
                    self._ensure_runtime_write_guards()
                    self.verify_schema_integrity()
                    return 1
            finally:
                try: conn.close()
                except Exception: pass
        self.verify_applied_migrations(); applied = 0
        ordered = sorted(MIGRATIONS, key=lambda m: m.version)
        if [m.version for m in ordered] != list(range(1, len(ordered) + 1)): raise MigrationError("Non-contiguous migration registry")
        maximum = ordered[-1].version if target_version is None else target_version
        if maximum < current or maximum > ordered[-1].version:
            raise MigrationError(f"Invalid target migration version {maximum}")
        for migration in ordered:
            if migration.version <= current or migration.version > maximum: continue
            backup = self.create_wal_safe_backup()
            conn = self.get_connection()
            try:
                conn.execute("BEGIN IMMEDIATE")
                before = self._capture_migration_snapshot(conn)
                for statement in split_sql_statements(migration.sql): conn.execute(statement)
                if migration.transform: migration.transform(conn)
                if migration.version == 4:
                    source_fingerprint = schema_fingerprint(conn)
                    conn.execute(
                        "INSERT OR REPLACE INTO schema_lineage_metadata VALUES (1,?,?,?,?,?,?)",
                        ("wave02.03337e8.schema_v3.canonical_pre_v4", source_fingerprint, 4,
                         DEPENDENCY_MANIFEST_V2_JSON, DEPENDENCY_MANIFEST_V2_HASH, self._get_now_iso()),
                    )
                if migration.version == 5:
                    updated = conn.execute(
                        "UPDATE schema_lineage_metadata SET compatibility_version=?, dependency_manifest_json=?,"
                        " dependency_manifest_hash=?, upgraded_at=? WHERE singleton_id=1",
                        (5, DEPENDENCY_MANIFEST_V3_JSON, DEPENDENCY_MANIFEST_V3_HASH, self._get_now_iso()),
                    ).rowcount
                    if updated != 1:
                        raise MigrationError(
                            "Migration v5 requires an existing canonical schema_lineage_metadata row"
                        )
                if migration.version == 6:
                    updated = conn.execute(
                        "UPDATE schema_lineage_metadata SET compatibility_version=?, dependency_manifest_json=?,"
                        " dependency_manifest_hash=?, upgraded_at=? WHERE singleton_id=1",
                        (6, DEPENDENCY_MANIFEST_V4_JSON, DEPENDENCY_MANIFEST_V4_HASH, self._get_now_iso()),
                    ).rowcount
                    if updated != 1:
                        raise MigrationError(
                            "Migration v6 requires an existing canonical schema_lineage_metadata row"
                        )
                if migration.version == 7:
                    updated = conn.execute(
                        "UPDATE schema_lineage_metadata SET compatibility_version=?, dependency_manifest_json=?,"
                        " dependency_manifest_hash=?, upgraded_at=? WHERE singleton_id=1",
                        (7, DEPENDENCY_MANIFEST_V5_JSON, DEPENDENCY_MANIFEST_V5_HASH, self._get_now_iso()),
                    ).rowcount
                    if updated != 1:
                        raise MigrationError(
                            "Migration v7 requires an existing canonical schema_lineage_metadata row"
                        )
                if migration.version == 8:
                    updated = conn.execute(
                        "UPDATE schema_lineage_metadata SET compatibility_version=?, dependency_manifest_json=?,"
                        " dependency_manifest_hash=?, upgraded_at=? WHERE singleton_id=1",
                        (8, DEPENDENCY_MANIFEST_V6_JSON, DEPENDENCY_MANIFEST_V6_HASH, self._get_now_iso()),
                    ).rowcount
                    if updated != 1:
                        raise MigrationError(
                            "Migration v8 requires an existing canonical schema_lineage_metadata row"
                        )
                if migration.version == 9:
                    updated = conn.execute(
                        "UPDATE schema_lineage_metadata SET compatibility_version=?, dependency_manifest_json=?,"
                        " dependency_manifest_hash=?, upgraded_at=? WHERE singleton_id=1",
                        (9, DEPENDENCY_MANIFEST_V7_JSON, DEPENDENCY_MANIFEST_V7_HASH, self._get_now_iso()),
                    ).rowcount
                    if updated != 1:
                        raise MigrationError(
                            "Migration v9 requires an existing canonical schema_lineage_metadata row"
                        )
                proof = self._verify_migration_preservation(conn, before, migration.version)
                conn.execute("INSERT INTO schema_migrations VALUES (?,?,?,?)", (migration.version, migration.checksum, self._get_now_iso(), migration.description))
                conn.execute("COMMIT")
                conn.close()
                conn = None

                self.verify_applied_migrations()
                if migration.version == SCHEMA_VERSION:
                    self._ensure_runtime_write_guards()
                self.verify_schema_integrity()

                with self.get_connection() as verify_conn:
                    fk_check = verify_conn.execute("PRAGMA foreign_key_check").fetchall()
                    if fk_check:
                        raise DurableStateCorruptionError(f"Foreign key violations after migration v{migration.version}: {fk_check}")
                    integrity = verify_conn.execute("PRAGMA integrity_check").fetchone()[0]
                    if str(integrity).lower() != "ok":
                        raise DurableStateCorruptionError(f"Integrity check failed after migration v{migration.version}: {integrity}")

                self.migration_proofs.append(proof)
                applied += 1
                if backup.exists():
                    backup.unlink()
            except Exception as exc:
                if conn is not None:
                    try:
                        if conn.in_transaction: conn.execute("ROLLBACK")
                    except Exception: pass
                    try: conn.close()
                    except Exception: pass
                try:
                    self.restore_from_backup(backup)
                    self.verify_schema_integrity()
                except Exception as restore_exc:
                    raise MigrationError(f"Failed migration version {migration.version}: {exc}; backup restore failed: {restore_exc}") from restore_exc
                raise MigrationError(f"Failed migration version {migration.version}: {exc}") from exc
        self.verify_applied_migrations()
        if maximum == SCHEMA_VERSION:
            self._ensure_runtime_write_guards()
        self.verify_schema_integrity()
        return applied
    def _table_counts(self, conn: sqlite3.Connection) -> Dict[str, int]:
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {n: conn.execute(f'SELECT count(*) FROM "{n}"').fetchone()[0] for n in names}
    def _canonical_legacy_records(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='transition_events'").fetchone()
        if not exists:
            return []
        columns = {row[1] for row in conn.execute("PRAGMA table_info(transition_events)").fetchall()}
        records: List[Dict[str, Any]] = []
        if "event_payload_json" in columns:
            rows = conn.execute("SELECT event_payload_json FROM transition_events ORDER BY work_item_id,event_seq").fetchall()
            for row in rows:
                migrated = json.loads(row["event_payload_json"]).get("legacy_migration")
                if migrated is not None:
                    records.append(migrated["source_record"])
            return records
        fields = (
            "event_id", "transition_key", "work_item_id", "from_state", "to_state", "state_version",
            "actor_class", "actor_ref", "reason_code", "explanation", "artifact_hash_set",
            "correlation_id", "timestamp_utc", "authority_granted",
        )
        order_by = "work_item_id,state_version,transition_key,event_id"
        for row in conn.execute(f"SELECT {','.join(fields)} FROM transition_events ORDER BY {order_by}").fetchall():
            records.append({field: row[field] for field in fields})
        return records
    def _capture_migration_snapshot(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        records = self._canonical_legacy_records(conn)
        return {
            "counts": self._table_counts(conn),
            "legacy_event_count": len(records),
            "canonical_legacy_event_hash": compute_sha256(canonical_json(records)),
        }
    def _verify_migration_preservation(self, conn: sqlite3.Connection, before: Dict[str, Any], version: int) -> Dict[str, Any]:
        after_counts = self._table_counts(conn)
        for table, count in before["counts"].items():
            if table == "schema_migrations": continue
            after = after_counts.get(table)
            if after != count: raise MigrationError(f"Migration v{version} row loss in {table}: {count}->{after}")
        records = self._canonical_legacy_records(conn)
        post_hash = compute_sha256(canonical_json(records))
        if len(records) != before["legacy_event_count"]:
            raise MigrationError(f"Migration v{version} legacy event count changed")
        if post_hash != before["canonical_legacy_event_hash"]:
            raise MigrationError(f"Migration v{version} canonical legacy-record hash changed")
        if version == 2 and conn.execute("SELECT count(*) FROM transition_events WHERE event_seq IS NULL").fetchone()[0]: raise MigrationError("Unsequenced legacy events")
        return {
            "migration_version": version,
            "pre_counts": before["counts"],
            "post_counts": after_counts,
            "legacy_event_count": len(records),
            "canonical_legacy_event_hash": post_hash,
            "status": "PASS_LOSSLESS_MIGRATION",
        }

    def register_receipt_resolver(self, verifier_identity: str, resolver: Callable[[Mapping[str, Any]], Any]) -> None:
        if not verifier_identity or not callable(resolver): raise ArtifactValidationError("Invalid receipt resolver")
        self._receipt_resolvers[verifier_identity] = resolver
    def register_artifact(self, *, artifact_id: str, artifact_type: str, storage_class: str, schema_version: str,
                          producer_ref: str, content_bytes: Optional[bytes] = None,
                          verified_receipt: Optional[Dict[str, Any]] = None, story_id: Optional[str] = None,
                          work_item_id: Optional[str] = None, sensitivity_class: str = "PUBLIC",
                          artifact_scope: Optional[str] = None) -> Dict[str, Any]:
        if not all((artifact_id, artifact_type, storage_class, schema_version, producer_ref)): raise ArtifactValidationError("Missing required artifact registration parameter")
        scope = artifact_scope or ("WORK_ITEM_EXACT" if work_item_id else "STORY_EXACT" if story_id else "GLOBAL_REUSABLE")
        if scope not in ARTIFACT_SCOPES: raise ArtifactValidationError("Invalid artifact_scope")
        if scope == "WORK_ITEM_EXACT" and (not story_id or not work_item_id): raise ArtifactValidationError("WORK_ITEM_EXACT requires story_id and work_item_id")
        if scope == "STORY_EXACT" and not story_id: raise ArtifactValidationError("STORY_EXACT requires story_id")
        receipt_meta = {key: None for key in ("receipt_id", "receipt_schema", "receipt_source_identity", "receipt_object_identity", "receipt_verifier_identity", "canonical_receipt_hash")}
        if content_bytes is not None and verified_receipt is not None: raise ArtifactValidationError("Provide bytes or receipt, not both")
        if content_bytes is not None:
            exact = bytes(content_bytes)
        elif verified_receipt is not None:
            receipt = dict(verified_receipt); verifier = receipt.get("verifier_identity") or receipt.get("verifier_ref")
            source = receipt.get("source_identity") or receipt.get("repository_identity"); obj = receipt.get("object_identity") or receipt.get("path_identity")
            receipt_id = receipt.get("receipt_id"); receipt_schema = receipt.get("schema_version")
            if not all((receipt_id, receipt_schema, source, obj, verifier)): raise ArtifactValidationError("verified_receipt missing required contract identity or provenance fields")
            resolver = self._receipt_resolvers.get(str(verifier))
            if resolver is None: raise ArtifactValidationError("verified_receipt requires registered verifier/resolver")
            resolved = resolver(receipt)
            if not isinstance(resolved, Mapping) or not isinstance(resolved.get("content_bytes"), (bytes, bytearray)):
                raise ArtifactValidationError("receipt resolver must return exact bytes and independently resolved immutable identity")
            exact = bytes(resolved["content_bytes"])
            if resolved.get("source_identity") != source or resolved.get("object_identity") != obj:
                raise ArtifactValidationError("verified_receipt resolver identity mismatch")
            object_hash = receipt.get("blob_hash") or receipt.get("object_hash")
            if not object_hash or resolved.get("object_hash") != object_hash:
                raise ArtifactValidationError("verified_receipt immutable object hash mismatch")
            if resolved.get("immutable") is not True:
                raise ArtifactValidationError("verified_receipt resolver did not attest immutable object resolution")
            if receipt.get("sha256_hash") != compute_sha256(exact) or receipt.get("byte_length") != len(exact): raise ArtifactValidationError("verified_receipt byte hash/length mismatch")
            receipt_meta = {"receipt_id": receipt_id, "receipt_schema": receipt_schema, "receipt_source_identity": source,
                            "receipt_object_identity": obj, "receipt_verifier_identity": verifier,
                            "canonical_receipt_hash": compute_sha256(canonical_json(receipt))}
        else: raise ArtifactValidationError("register_artifact requires either content_bytes or verified_receipt")
        digest = compute_sha256(exact); now = self._get_now_iso(); conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute("SELECT * FROM artifact_references WHERE artifact_id=?", (artifact_id,)).fetchone()
            if existing:
                expected_existing = {
                    "artifact_type": artifact_type, "story_id": story_id, "work_item_id": work_item_id,
                    "storage_class": storage_class, "byte_length": len(exact), "sha256_hash": digest,
                    "schema_version": schema_version, "producer_ref": producer_ref,
                    "sensitivity_class": sensitivity_class, "artifact_scope": scope, **receipt_meta,
                }
                mismatches = [key for key, value in expected_existing.items() if existing[key] != value]
                if mismatches: raise ArtifactValidationError(f"Conflicting artifact registration fields: {mismatches}")
                conn.execute("COMMIT"); return dict(existing)
            with self._canonical_artifact_insert():
                conn.execute("""INSERT INTO artifact_references (artifact_id,artifact_type,story_id,work_item_id,storage_class,byte_length,sha256_hash,schema_version,created_at,producer_ref,sensitivity_class,artifact_scope,receipt_id,receipt_schema,receipt_source_identity,receipt_object_identity,receipt_verifier_identity,canonical_receipt_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                             (artifact_id, artifact_type, story_id, work_item_id, storage_class, len(exact), digest, schema_version, now, producer_ref, sensitivity_class, scope, *receipt_meta.values()))
            conn.execute("COMMIT"); return dict(conn.execute("SELECT * FROM artifact_references WHERE artifact_id=?", (artifact_id,)).fetchone())
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        finally: conn.close()
    def get_artifact(self, artifact_id: str) -> Dict[str, Any]:
        with self.get_connection() as c:
            row = c.execute("SELECT * FROM artifact_references WHERE artifact_id=?", (artifact_id,)).fetchone()
            if not row: raise ArtifactNotFoundError(f"Artifact {artifact_id} not registered")
            return dict(row)
    def _validate_artifact_scope(self, art: sqlite3.Row, story_id: str, work_item_id: str) -> None:
        scope = art["artifact_scope"]
        if scope == LEGACY_QUARANTINE_SCOPE:
            raise ArtifactValidationError(f"Artifact {art['artifact_id']} is quarantined from active use")
        if scope == "WORK_ITEM_EXACT" and (art["story_id"] != story_id or art["work_item_id"] != work_item_id): raise ArtifactValidationError(f"Artifact {art['artifact_id']} is outside exact work-item scope")
        if scope == "STORY_EXACT" and art["story_id"] != story_id: raise ArtifactValidationError(f"Artifact {art['artifact_id']} is outside exact story scope")
        if scope not in ACTIVE_ARTIFACT_SCOPES: raise ArtifactValidationError(f"Artifact {art['artifact_id']} has invalid scope")
    def _artifact_snapshots(self, conn: sqlite3.Connection, ids: Sequence[str], story_id: str, work_item_id: str) -> List[Dict[str, Any]]:
        snapshots = []
        for artifact_id in sorted(set(ids)):
            row = conn.execute("SELECT * FROM artifact_references WHERE artifact_id=?", (artifact_id,)).fetchone()
            if not row: raise ArtifactNotFoundError(f"Referenced artifact {artifact_id} is not registered")
            self._validate_artifact_scope(row, story_id, work_item_id)
            snapshots.append({key: row[key] for key in ("artifact_id", "artifact_type", "story_id", "work_item_id", "artifact_scope", "storage_class", "byte_length", "sha256_hash", "schema_version", "producer_ref", "receipt_id", "receipt_schema", "receipt_source_identity", "receipt_object_identity", "receipt_verifier_identity", "canonical_receipt_hash")})
        return snapshots

    def _append_event(self, conn: sqlite3.Connection, *, event_id: str, transition_key: str, envelope: Dict[str, Any], explanation: str) -> None:
        payload = canonical_json(envelope); event_hash = compute_sha256(payload)
        values = (event_id, transition_key, envelope["work_item_id"], envelope["event_kind"], envelope["event_seq"], envelope["from_state"], envelope["to_state"], envelope["state_version"], envelope["actor_class"], envelope["actor_ref"], envelope["reason_code"], explanation, envelope["explanation_hash"], envelope["correlation_id"], envelope["policy_version"], envelope["model_version"], envelope["authority_type"], envelope["authority_ref"], envelope["authority_effect"], envelope["lease_id"], envelope["lease_key"], envelope["fencing_token"], canonical_json(envelope["input_artifact_ids"]), canonical_json(envelope["output_artifact_ids"]), canonical_json(envelope["artifact_snapshots"]), envelope["previous_event_hash"], payload, event_hash, envelope["timestamp_utc"])
        with self._canonical_append(): conn.execute("INSERT INTO transition_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    def create_work_item(self, *, story_id: str, title: str, target_surface: str, work_item_id: Optional[str] = None,
                         actor_ref: str = "producer_ref", correlation_id: Optional[str] = None,
                         input_artifact_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        now = self._get_now_iso(); item_id = work_item_id or f"wi_{compute_sha256(story_id+title+now)[:16]}"; ids = input_artifact_ids or []
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute("SELECT * FROM work_items WHERE work_item_id=?", (item_id,)).fetchone()
            if existing:
                if (existing["story_id"], existing["title"], existing["target_surface"]) != (story_id, title, target_surface): raise ValueError("Conflicting recreation")
                conn.execute("COMMIT"); return dict(existing)
            snaps = self._artifact_snapshots(conn, ids, story_id, item_id)
            conn.execute("INSERT INTO work_items VALUES (?,?,?,?,?,?,?,?)", (item_id, story_id, title, "DISCOVERED", 1, target_surface, now, now))
            explanation = f"Genesis event for work item {item_id} story {story_id}"
            env = build_event_envelope(event_schema_version=EVENT_SCHEMA_VERSION, event_kind=GENESIS_EVENT_KIND, event_seq=1,
                work_item_id=item_id, story_id=story_id, title=title, target_surface=target_surface, state_version=1,
                from_state="DISCOVERED", to_state="DISCOVERED", previous_event_hash=GENESIS_PREVIOUS_HASH,
                actor_class="ContentOpsDurableStore", actor_ref=actor_ref, reason_code="WORK_ITEM_INITIALIZATION",
                explanation_hash=compute_sha256(explanation), correlation_id=correlation_id or f"corr_init_{item_id}",
                policy_version="contentops.policy.v1", model_version="NOT_APPLICABLE", authority_type="NONE", authority_ref=None,
                authority_effect="NO_AUTHORITY_GRANTED", lease_id=None, lease_key=None, fencing_token=0,
                input_artifact_ids=ids, output_artifact_ids=[], artifact_snapshots=snaps, timestamp_utc=now)
            event_hash = compute_sha256(canonical_json(env)); event_id = f"evt_{event_hash[:16]}"
            self._append_event(conn, event_id=event_id, transition_key=f"tr_{item_id}_v1_genesis", envelope=env, explanation=explanation)
            conn.execute("COMMIT"); result = dict(conn.execute("SELECT * FROM work_items WHERE work_item_id=?", (item_id,)).fetchone()); result.update(genesis_event_id=event_id, genesis_event_hash=event_hash); return result
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        finally: conn.close()
    def get_work_item(self, work_item_id: str) -> Dict[str, Any]:
        with self.get_connection() as c:
            row = c.execute("SELECT * FROM work_items WHERE work_item_id=?", (work_item_id,)).fetchone()
            if not row: raise WorkItemNotFoundError(f"Work item {work_item_id} not found")
            return dict(row)

    def _expire_assignments(self, conn: sqlite3.Connection, work_item_id: Optional[str], lease_id: Optional[str] = None) -> None:
        if work_item_id: conn.execute("UPDATE assignments SET status='RELEASED' WHERE work_item_id=? AND status='ACTIVE'", (work_item_id,))
        if lease_id: conn.execute("UPDATE heartbeats SET status='DEAD' WHERE lease_id=? AND status='ALIVE'", (lease_id,))
    def acquire_lease(self, lease_key: str, owner_ref: str, ttl_seconds: int = 30, work_item_id: Optional[str] = None) -> Dict[str, Any]:
        now = self._get_now(); now_iso = now.isoformat(); expires = (now + timedelta(seconds=ttl_seconds)).isoformat(); conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE"); existing = conn.execute("SELECT * FROM leases WHERE lease_key=?", (lease_key,)).fetchone()
            if existing and existing["status"] == "ACTIVE" and existing["expires_at"] > now_iso and existing["owner_ref"] != owner_ref: raise LeaseConflictError(f"Lease {lease_key} is active")
            if existing:
                self._expire_assignments(conn, existing["work_item_id"], existing["lease_id"]); token = existing["fencing_token"] + 1; lease_id = existing["lease_id"]
                conn.execute("UPDATE leases SET work_item_id=?,owner_ref=?,fencing_token=?,acquired_at=?,renewed_at=?,expires_at=?,status='ACTIVE' WHERE lease_key=?", (work_item_id, owner_ref, token, now_iso, now_iso, expires, lease_key))
            else:
                token = 1; lease_id = f"lease_{compute_sha256(lease_key+owner_ref+now_iso)[:16]}"; conn.execute("INSERT INTO leases VALUES (?,?,?,?,?,?,?,?,?)", (lease_id, lease_key, work_item_id, owner_ref, token, now_iso, now_iso, expires, "ACTIVE"))
            conn.execute("COMMIT"); return dict(conn.execute("SELECT * FROM leases WHERE lease_id=?", (lease_id,)).fetchone())
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        finally: conn.close()
    def renew_lease(self, lease_id: str, owner_ref: str, fencing_token: int, ttl_seconds: int = 30) -> Dict[str, Any]:
        now = self._get_now(); conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE"); lease = conn.execute("SELECT * FROM leases WHERE lease_id=?", (lease_id,)).fetchone()
            if not lease or lease["fencing_token"] != fencing_token: raise StaleFencingTokenError("Stale fencing token")
            if lease["owner_ref"] != owner_ref or lease["status"] != "ACTIVE" or lease["expires_at"] <= now.isoformat(): raise LeaseConflictError("Lease is not renewable")
            conn.execute("UPDATE leases SET renewed_at=?,expires_at=? WHERE lease_id=?", (now.isoformat(), (now+timedelta(seconds=ttl_seconds)).isoformat(), lease_id)); conn.execute("COMMIT"); return dict(conn.execute("SELECT * FROM leases WHERE lease_id=?", (lease_id,)).fetchone())
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        finally: conn.close()
    def release_lease(self, lease_id: str, owner_ref: str, fencing_token: int) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE"); lease = conn.execute("SELECT * FROM leases WHERE lease_id=?", (lease_id,)).fetchone()
            if not lease or lease["fencing_token"] != fencing_token: raise StaleFencingTokenError("Stale fencing token")
            if lease["owner_ref"] != owner_ref: raise LeaseConflictError("Lease owner mismatch")
            self._expire_assignments(conn, lease["work_item_id"], lease_id); conn.execute("UPDATE leases SET status='RELEASED' WHERE lease_id=?", (lease_id,)); conn.execute("COMMIT"); result = dict(lease); result["status"] = "RELEASED"; return result
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        finally: conn.close()
    def recover_stale_leases(self) -> List[str]:
        now = self._get_now_iso(); conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE"); rows = conn.execute("SELECT * FROM leases WHERE status='ACTIVE' AND expires_at<=?", (now,)).fetchall()
            for row in rows: self._expire_assignments(conn, row["work_item_id"], row["lease_id"]); conn.execute("UPDATE leases SET status='EXPIRED' WHERE lease_id=?", (row["lease_id"],))
            conn.execute("COMMIT"); return [r["lease_id"] for r in rows]
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        finally: conn.close()
    def claim_work_item(self, *, lease_key: str, work_item_id: str, owner_ref: str, ttl_seconds: int = 30) -> Dict[str, Any]:
        now = self._get_now(); now_iso = now.isoformat(); expires = (now+timedelta(seconds=ttl_seconds)).isoformat(); conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            if not conn.execute("SELECT 1 FROM work_items WHERE work_item_id=?", (work_item_id,)).fetchone(): raise WorkItemNotFoundError(work_item_id)
            lease = conn.execute("SELECT * FROM leases WHERE lease_key=?", (lease_key,)).fetchone()
            active = conn.execute("SELECT * FROM assignments WHERE work_item_id=? AND status='ACTIVE'", (work_item_id,)).fetchone()
            if active and lease and lease["status"] == "ACTIVE" and lease["expires_at"] > now_iso and lease["owner_ref"] != owner_ref: raise LeaseConflictError(f"Work item {work_item_id} actively assigned")
            if lease and lease["status"] == "ACTIVE" and lease["expires_at"] > now_iso and lease["owner_ref"] != owner_ref: raise LeaseConflictError(f"Lease {lease_key} is held")
            if lease:
                self._expire_assignments(conn, lease["work_item_id"], lease["lease_id"]); token = lease["fencing_token"]+1; lease_id=lease["lease_id"]
                conn.execute("UPDATE leases SET work_item_id=?,owner_ref=?,fencing_token=?,acquired_at=?,renewed_at=?,expires_at=?,status='ACTIVE' WHERE lease_key=?", (work_item_id,owner_ref,token,now_iso,now_iso,expires,lease_key))
            else:
                token=1; lease_id=f"lease_{compute_sha256(lease_key+owner_ref+now_iso)[:16]}"; conn.execute("INSERT INTO leases VALUES (?,?,?,?,?,?,?,?,?)", (lease_id,lease_key,work_item_id,owner_ref,token,now_iso,now_iso,expires,"ACTIVE"))
            assignment_id=f"asgn_{compute_sha256(work_item_id+owner_ref+str(token))[:16]}"; conn.execute("INSERT INTO assignments VALUES (?,?,?,?,?)", (assignment_id,work_item_id,owner_ref,now_iso,"ACTIVE")); conn.execute("COMMIT")
            result=dict(conn.execute("SELECT * FROM leases WHERE lease_id=?",(lease_id,)).fetchone()); result["assignment_id"]=assignment_id; return result
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        finally: conn.close()
    def upsert_heartbeat(self, worker_id: str, lease_id: Optional[str] = None) -> Dict[str, Any]:
        now=self._get_now_iso(); hb=f"hb_{compute_sha256(worker_id)[:16]}"; conn=self.get_connection()
        try:
            conn.execute("INSERT INTO heartbeats VALUES (?,?,?,?,?) ON CONFLICT(worker_id) DO UPDATE SET lease_id=excluded.lease_id,last_seen_at=excluded.last_seen_at,status='ALIVE'",(hb,worker_id,lease_id,now,"ALIVE")); return dict(conn.execute("SELECT * FROM heartbeats WHERE worker_id=?",(worker_id,)).fetchone())
        finally: conn.close()
    def query_fresh_heartbeats(self, ttl_seconds: int=60) -> List[Dict[str,Any]]:
        cutoff=(self._get_now()-timedelta(seconds=ttl_seconds)).isoformat()
        with self.get_connection() as c: return [dict(r) for r in c.execute("SELECT * FROM heartbeats WHERE last_seen_at>=? AND status='ALIVE'",(cutoff,)).fetchall()]
    def dispose_stale_heartbeats(self, ttl_seconds:int=60)->List[str]:
        cutoff=(self._get_now()-timedelta(seconds=ttl_seconds)).isoformat(); conn=self.get_connection()
        try:
            rows=conn.execute("SELECT worker_id FROM heartbeats WHERE last_seen_at<? AND status='ALIVE'",(cutoff,)).fetchall(); ids=[r[0] for r in rows]
            if ids: conn.execute(f"UPDATE heartbeats SET status='DEAD' WHERE worker_id IN ({','.join('?'*len(ids))})",ids)
            return ids
        finally: conn.close()

    def transition_state(self, *, work_item_id:str, expected_from_state:str, to_state:str, expected_state_version:int,
                         actor_class:str, actor_ref:str, reason_code:str, explanation:str, lease_key:str, fencing_token:int,
                         input_artifact_ids:List[str], output_artifact_ids:List[str], correlation_id:str,
                         policy_version:str="contentops.policy.v1", model_version:str="NOT_APPLICABLE") -> Dict[str,Any]:
        if expected_from_state not in CANONICAL_STATES or to_state not in CANONICAL_STATES: raise InvalidStateTransitionError("Unknown state")
        if to_state not in STATE_TRANSITION_GRAPH.get(expected_from_state,set()): raise InvalidStateTransitionError(f"Illegal state transition from {expected_from_state} to {to_state}")
        if to_state in WAVE02_PROTECTED_STATES: raise Wave02AuthorityViolationError(f"Wave 02 protected authority state {to_state}")
        if not all((actor_class,actor_ref,reason_code,explanation,correlation_id,lease_key)): raise TransitionValidationError("Missing required transition parameter")
        now=self._get_now_iso(); conn=self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE"); item=conn.execute("SELECT * FROM work_items WHERE work_item_id=?",(work_item_id,)).fetchone()
            if not item: raise WorkItemNotFoundError(work_item_id)
            if item["current_state"]!=expected_from_state or item["state_version"]!=expected_state_version: raise CASStateConflictError("CAS state conflict")
            lease=conn.execute("SELECT * FROM leases WHERE lease_key=?",(lease_key,)).fetchone()
            if not lease or lease["status"]!="ACTIVE" or lease["expires_at"]<=now or lease["fencing_token"]!=fencing_token or lease["owner_ref"]!=actor_ref or (lease["work_item_id"] and lease["work_item_id"]!=work_item_id): raise StaleFencingTokenError("Lease/fencing validation failed")
            inputs=sorted(set(input_artifact_ids)); outputs=sorted(set(output_artifact_ids)); snaps=self._artifact_snapshots(conn,inputs+outputs,item["story_id"],work_item_id)
            prev=conn.execute("SELECT * FROM transition_events WHERE work_item_id=? ORDER BY event_seq DESC LIMIT 1",(work_item_id,)).fetchone()
            if not prev: raise DurableStateCorruptionError("Missing genesis event")
            seq=prev["event_seq"]+1; version=expected_state_version+1
            env=build_event_envelope(event_schema_version=EVENT_SCHEMA_VERSION,event_kind="STATE_TRANSITION",event_seq=seq,work_item_id=work_item_id,story_id=item["story_id"],title=item["title"],target_surface=item["target_surface"],state_version=version,from_state=expected_from_state,to_state=to_state,previous_event_hash=prev["event_hash"],actor_class=actor_class,actor_ref=actor_ref,reason_code=reason_code,explanation_hash=compute_sha256(explanation),correlation_id=correlation_id,policy_version=policy_version,model_version=model_version,authority_type="NONE",authority_ref=None,authority_effect="NO_AUTHORITY_GRANTED",lease_id=lease["lease_id"],lease_key=lease_key,fencing_token=fencing_token,input_artifact_ids=inputs,output_artifact_ids=outputs,artifact_snapshots=snaps,timestamp_utc=now)
            payload=canonical_json(env); event_hash=compute_sha256(payload); event_id=f"evt_{event_hash[:16]}"; self._append_event(conn,event_id=event_id,transition_key=f"tr_{work_item_id}_v{version}_{event_hash[:8]}",envelope=env,explanation=explanation)
            conn.execute("UPDATE work_items SET current_state=?,state_version=?,updated_at=? WHERE work_item_id=?",(to_state,version,now,work_item_id)); conn.execute("COMMIT")
            return {"work_item_id":work_item_id,"previous_state":expected_from_state,"current_state":to_state,"state_version":version,"event_id":event_id,"event_seq":seq,"event_hash":event_hash,"previous_event_hash":prev["event_hash"],"updated_at":now}
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        finally: conn.close()

    def _verify_event(self, conn:sqlite3.Connection, item:sqlite3.Row, evt:sqlite3.Row, expected_seq:int, current_state:str, previous_hash:str)->str:
        try: payload=json.loads(evt["event_payload_json"])
        except Exception as exc: raise DurableStateCorruptionError("Invalid event payload JSON") from exc
        schema_version=payload.get("event_schema_version")
        if schema_version not in ACCEPTED_EVENT_SCHEMA_VERSIONS: raise DurableStateCorruptionError("Unaccepted event schema version")
        if evt["event_kind"] != payload.get("event_kind"): raise DurableStateCorruptionError("Event kind mismatch")
        baseline=schema_version==LEGACY_BASELINE_EVENT_SCHEMA_VERSION
        genesis=expected_seq==1
        if genesis and baseline:
            if evt["event_kind"]!="LEGACY_PROJECTION_BASELINE" or evt["reason_code"]!="LEGACY_PROJECTION_BASELINE" or evt["from_state"]!="DISCOVERED" or evt["to_state"]!="DISCOVERED": raise DurableStateCorruptionError("Invalid legacy projection baseline")
            baseline_row=conn.execute("SELECT * FROM legacy_projection_baselines WHERE work_item_id=?",(item["work_item_id"],)).fetchone()
            if not baseline_row or baseline_row["baseline_event_json"]!=evt["event_payload_json"] or baseline_row["baseline_event_hash"]!=evt["event_hash"] or baseline_row["original_projection_hash"]!=payload.get("original_projection_hash"): raise DurableStateCorruptionError("Legacy projection baseline binding mismatch")
            if payload.get("migration_generated") is not True or payload.get("source_lineage_id")!=baseline_row["lineage_id"]: raise DurableStateCorruptionError("Legacy projection baseline provenance mismatch")
        elif genesis:
            if evt["event_kind"]!=GENESIS_EVENT_KIND or evt["reason_code"]!="WORK_ITEM_INITIALIZATION" or evt["from_state"]!="DISCOVERED" or evt["to_state"]!="DISCOVERED": raise DurableStateCorruptionError("Missing valid genesis event")
        else:
            if evt["event_kind"]!="STATE_TRANSITION": raise DurableStateCorruptionError("Invalid transition event kind")
            edge=(evt["from_state"],evt["to_state"])
            valid_runtime_edge=evt["from_state"]==current_state and evt["to_state"] in STATE_TRANSITION_GRAPH.get(current_state,set())
            valid_historical_edge=(
                schema_version==HISTORICAL_EVENT_SCHEMA_VERSION
                and evt["from_state"]==current_state
                and edge in HISTORICAL_MIGRATION_STATE_EDGES
                and payload.get("legacy_migration",{}).get("source_record_hash")
            )
            if not valid_runtime_edge and not valid_historical_edge: raise DurableStateCorruptionError("Illegal event state edge")
            if evt["to_state"] in WAVE02_PROTECTED_STATES: raise DurableStateCorruptionError("Protected authority state event")
        if evt["previous_event_hash"]!=previous_hash: raise DurableStateCorruptionError("Previous event hash mismatch")
        if compute_sha256(evt["explanation"])!=evt["explanation_hash"]: raise DurableStateCorruptionError("Explanation hash mismatch")
        if canonical_json(payload)!=evt["event_payload_json"] or compute_sha256(evt["event_payload_json"])!=evt["event_hash"]: raise DurableStateCorruptionError("Event payload hash mismatch")
        column_map={"event_kind":evt["event_kind"],"event_seq":evt["event_seq"],"work_item_id":evt["work_item_id"],"story_id":item["story_id"],"title":item["title"],"target_surface":item["target_surface"],"state_version":evt["state_version"],"from_state":evt["from_state"],"to_state":evt["to_state"],"previous_event_hash":evt["previous_event_hash"],"actor_class":evt["actor_class"],"actor_ref":evt["actor_ref"],"reason_code":evt["reason_code"],"explanation_hash":evt["explanation_hash"],"correlation_id":evt["correlation_id"],"policy_version":evt["policy_version"],"model_version":evt["model_version"],"authority_type":evt["authority_type"],"authority_ref":evt["authority_ref"],"authority_effect":evt["authority_effect"],"lease_id":evt["lease_id"],"lease_key":evt["lease_key"],"fencing_token":evt["fencing_token"],"timestamp_utc":evt["timestamp_utc"]}
        for field,value in column_map.items():
            if payload.get(field)!=value: raise DurableStateCorruptionError(f"Event payload column mismatch for field '{field}'")
        if evt["event_seq"]!=expected_seq: raise DurableStateCorruptionError("Event sequence mismatch")
        if schema_version in {EVENT_SCHEMA_VERSION,LEGACY_EVENT_SCHEMA_VERSION} and evt["state_version"]!=expected_seq: raise DurableStateCorruptionError("Event sequence/state-version mismatch")
        inputs=json.loads(evt["input_artifact_ids"]); outputs=json.loads(evt["output_artifact_ids"]); snapshots=json.loads(evt["artifact_snapshot_json"])
        if inputs!=sorted(set(inputs)) or outputs!=sorted(set(outputs)) or payload.get("input_artifact_ids")!=inputs or payload.get("output_artifact_ids")!=outputs or payload.get("artifact_snapshots")!=snapshots: raise DurableStateCorruptionError("Artifact ID/snapshot envelope mismatch")
        if sorted(s["artifact_id"] for s in snapshots)!=sorted(set(inputs+outputs)): raise DurableStateCorruptionError("Artifact snapshot set mismatch")
        for snap in snapshots:
            row=conn.execute("SELECT * FROM artifact_references WHERE artifact_id=?",(snap["artifact_id"],)).fetchone()
            if not row or row["sha256_hash"]!=snap["sha256_hash"] or row["byte_length"]!=snap["byte_length"] or row["canonical_receipt_hash"]!=snap.get("canonical_receipt_hash"): raise DurableStateCorruptionError("Replay artifact snapshot corruption")
        return evt["to_state"]
    def replay_work_item_events(self,work_item_id:str)->Dict[str,Any]:
        conn=self.get_connection()
        try:
            item=conn.execute("SELECT * FROM work_items WHERE work_item_id=?",(work_item_id,)).fetchone()
            if not item: raise WorkItemNotFoundError(work_item_id)
            events=conn.execute("SELECT * FROM transition_events WHERE work_item_id=? ORDER BY event_seq",(work_item_id,)).fetchall()
            if not events: raise DurableStateCorruptionError("has no transition events")
            state="DISCOVERED"; previous=GENESIS_PREVIOUS_HASH
            for seq,evt in enumerate(events,1): state=self._verify_event(conn,item,evt,seq,state,previous); previous=evt["event_hash"]
            expected_projection_version=events[-1]["state_version"]
            if item["current_state"]!=state or item["state_version"]!=expected_projection_version: raise DurableStateCorruptionError("Materialized projection mismatch")
            return {"work_item_id":work_item_id,"replayed_state":state,"replayed_version":expected_projection_version,"event_count":len(events),"last_event_hash":previous,"verification_status":"PASS"}
        finally: conn.close()
    def reconstruct_in_flight_state(self)->Dict[str,Any]:
        recovered=self.recover_stale_leases(); dead=self.dispose_stale_heartbeats()
        with self.get_connection() as c: ids=[r[0] for r in c.execute("SELECT work_item_id FROM work_items")]
        for work_item_id in ids: self.replay_work_item_events(work_item_id)
        return {"restart_reconstruction_status":"PASS","recovered_leases_count":len(recovered),"dead_heartbeats_count":len(dead),"verified_work_items_count":len(ids)}
    def export_redacted_store_evidence(self)->Dict[str,Any]:
        with self.get_connection() as c:
            migrations=[dict(r) for r in c.execute("SELECT * FROM schema_migrations ORDER BY version")]; items=[dict(r) for r in c.execute("SELECT * FROM work_items ORDER BY work_item_id")]; events=[dict(r) for r in c.execute("SELECT * FROM transition_events ORDER BY work_item_id,event_seq")]
            leases=c.execute("SELECT count(*) FROM leases").fetchone()[0]; artifacts=c.execute("SELECT count(*) FROM artifact_references").fetchone()[0]
        red_items=[{"work_item_id":i["work_item_id"],"story_id":compute_sha256(i["story_id"])[:16],"title":"[REDACTED_TITLE]","current_state":i["current_state"],"state_version":i["state_version"],"target_surface":i["target_surface"],"created_at":i["created_at"],"updated_at":i["updated_at"]} for i in items]
        red_events=[{"event_id":e["event_id"],"work_item_id":e["work_item_id"],"event_seq":e["event_seq"],"from_state":e["from_state"],"to_state":e["to_state"],"state_version":e["state_version"],"actor_class":e["actor_class"],"actor_ref":"[REDACTED_ACTOR_REF]","reason_code":e["reason_code"],"explanation":"[REDACTED_EXPLANATION]","explanation_hash":e["explanation_hash"],"correlation_id":e["correlation_id"],"previous_event_hash":e["previous_event_hash"],"event_hash":e["event_hash"],"authority_type":e["authority_type"],"authority_effect":e["authority_effect"],"timestamp_utc":e["timestamp_utc"]} for e in events]
        return {"schema_version":"contentops.durable_store_export.v1","database_pragmas":self.query_pragmas(),"current_schema_version":self.get_current_schema_version(),"redaction_guarantee":"PASS_NO_SECRETS_CREDENTIALS_OR_PRIVATE_MATERIAL","counts":{"migrations":len(migrations),"work_items":len(items),"transition_events":len(events),"leases":leases,"artifacts":artifacts},"migrations":migrations,"work_items":red_items,"transition_events":red_events}

    # ------------------------------------------------------------------
    # Canonical publication lifecycle persistence.
    #
    # These methods reuse the EXISTING canonical operational-store tables
    # (outbox_messages, platform_dispatches, readbacks, reconciliations,
    # incidents). They do not create a new store, table, or schema, and they
    # never call a network publisher. Writes are idempotent on the exact
    # durable identity (restart/redispatch never creates duplicate rows),
    # which is the restart-safe foundation for the autonomous dispatch chain
    # outbox -> dispatch -> readback -> reconciliation.
    # ------------------------------------------------------------------

    def _idempotent_insert(self, table: str, primary_key: str, key_value: str,
                           columns: Sequence[str], values: Sequence[Any]) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                f"SELECT * FROM {table} WHERE {primary_key}=?", (key_value,)
            ).fetchone()
            if existing:
                conn.execute("COMMIT")
                return dict(existing)
            placeholders = ",".join("?" for _ in columns)
            conn.execute(
                f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})", tuple(values)
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                f"SELECT * FROM {table} WHERE {primary_key}=?", (key_value,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def register_outbox_message(self, *, message_id: str, work_item_id: str,
                                destination: str, payload: str,
                                status: str = "PENDING") -> Dict[str, Any]:
        return self._idempotent_insert(
            "outbox_messages", "message_id", message_id,
            ("message_id", "work_item_id", "destination", "payload", "status", "created_at"),
            (message_id, work_item_id, destination, payload, status, self._get_now_iso()),
        )

    def set_outbox_status(self, message_id: str, status: str) -> Dict[str, Any]:
        """Update only lifecycle status; exact outbox payload bytes remain immutable."""
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM outbox_messages WHERE message_id=?", (message_id,)
            ).fetchone()
            if row is None:
                raise WorkItemNotFoundError(f"outbox message {message_id} not found")
            conn.execute(
                "UPDATE outbox_messages SET status=? WHERE message_id=?", (status, message_id)
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM outbox_messages WHERE message_id=?", (message_id,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def finalize_outbox_payload_before_dispatch(
        self, *, message_id: str, payload: str, status: str = "READY"
    ) -> Dict[str, Any]:
        """Finalize dependency-bound bytes only while no dispatch marker exists.

        This is used for Substack-first derivative packages: the canonical URL is unknowable
        when the master plan is registered, but exact final payload bytes must be durable before
        the adapter boundary.  Once any dispatch row exists the payload is immutable.
        """
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM outbox_messages WHERE message_id=?", (message_id,)
            ).fetchone()
            if row is None:
                raise WorkItemNotFoundError(f"outbox message {message_id} not found")
            marker = conn.execute(
                "SELECT dispatch_id FROM platform_dispatches WHERE message_id=?", (message_id,)
            ).fetchone()
            if marker is not None:
                raise DispatchIdentityConflictError(
                    f"outbox_payload_immutable_after_dispatch_marker:{message_id}"
                )
            conn.execute(
                "UPDATE outbox_messages SET payload=?, status=? WHERE message_id=?",
                (payload, status, message_id),
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM outbox_messages WHERE message_id=?", (message_id,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def list_outbox_messages(self, *, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if status is None:
                rows = conn.execute(
                    "SELECT * FROM outbox_messages ORDER BY created_at, message_id"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM outbox_messages WHERE status=? ORDER BY created_at, message_id",
                    (status,),
                ).fetchall()
            return [dict(row) for row in rows]

    def get_platform_dispatch(self, dispatch_id: str) -> Optional[Dict[str, Any]]:
        """Read one canonical dispatch row including its persisted external public-object identity."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM platform_dispatches WHERE dispatch_id=?", (dispatch_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_platform_dispatches(self) -> List[Dict[str, Any]]:
        """List all canonical dispatch rows (read-only; used for observation eligibility)."""
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM platform_dispatches ORDER BY dispatched_at, dispatch_id"
            ).fetchall()]

    def register_platform_dispatch(
        self,
        *,
        dispatch_id: str,
        message_id: str,
        platform: str,
        status: str = "PENDING",
        public_object_id: Optional[str] = None,
        public_object_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a canonical dispatch with the exact external public-object identity.

        The publisher-supplied public-object identity is WRITE-ONCE durable truth:
          * same dispatch + same identity   -> idempotent PASS (returns the existing row);
          * same dispatch + different identity -> ``DispatchIdentityConflictError`` (never rewritten).
        Missing URL does not invalidate a valid exact public_object_id; the URL hash is
        deterministic over the exact URL when a URL is present.
        """
        public_object_id = str(public_object_id) if public_object_id else None
        public_object_url = str(public_object_url) if public_object_url else None
        public_object_url_hash = (
            compute_sha256(public_object_url) if public_object_url else None
        )
        columns = (
            "dispatch_id", "message_id", "platform", "status", "dispatched_at",
            "public_object_id", "public_object_url", "public_object_url_hash",
        )
        values = (
            dispatch_id, message_id, platform, status, self._get_now_iso(),
            public_object_id, public_object_url, public_object_url_hash,
        )
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT * FROM platform_dispatches WHERE dispatch_id=?", (dispatch_id,)
            ).fetchone()
            if existing:
                # Write-once identity: a conflicting different identity fails closed; identical
                # identity is idempotent; supplying an identity where none is persisted is a
                # safe one-time completion; a registration without identity never erases one.
                stored_id = existing["public_object_id"]
                stored_url = existing["public_object_url"]
                if public_object_id is not None and stored_id is not None and public_object_id != stored_id:
                    raise DispatchIdentityConflictError(
                        f"platform_dispatch_identity_conflict:{dispatch_id}:public_object_id"
                    )
                if public_object_url is not None and stored_url is not None and public_object_url != stored_url:
                    raise DispatchIdentityConflictError(
                        f"platform_dispatch_identity_conflict:{dispatch_id}:public_object_url"
                    )
                if public_object_id is not None and public_object_id == stored_id and (
                    public_object_url is not None and stored_url is not None and public_object_url != stored_url
                ):
                    raise DispatchIdentityConflictError(
                        f"platform_dispatch_identity_conflict:{dispatch_id}:public_object_url_for_same_object"
                    )
                completed = (
                    (public_object_id is not None and stored_id is None)
                    or (public_object_url is not None and stored_url is None)
                )
                if completed:
                    conn.execute(
                        "UPDATE platform_dispatches SET public_object_id=COALESCE(public_object_id, ?),"
                        " public_object_url=COALESCE(public_object_url, ?),"
                        " public_object_url_hash=COALESCE(public_object_url_hash, ?)"
                        " WHERE dispatch_id=?",
                        (public_object_id, public_object_url, public_object_url_hash, dispatch_id),
                    )
                conn.execute("COMMIT")
                return dict(conn.execute(
                    "SELECT * FROM platform_dispatches WHERE dispatch_id=?", (dispatch_id,)
                ).fetchone())
            placeholders = ",".join("?" for _ in columns)
            conn.execute(
                f"INSERT INTO platform_dispatches ({','.join(columns)}) VALUES ({placeholders})",
                values,
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM platform_dispatches WHERE dispatch_id=?", (dispatch_id,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def register_readback(self, *, readback_id: str, dispatch_id: str,
                          readback_data: str) -> Dict[str, Any]:
        return self._idempotent_insert(
            "readbacks", "readback_id", readback_id,
            ("readback_id", "dispatch_id", "readback_data", "read_at"),
            (readback_id, dispatch_id, readback_data, self._get_now_iso()),
        )

    def list_readbacks_for_dispatch(self, dispatch_id: str) -> List[Dict[str, Any]]:
        """List append-only readback observations for one exact dispatch."""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM readbacks WHERE dispatch_id=? ORDER BY read_at, readback_id",
                (dispatch_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def register_reconciliation(self, *, reconciliation_id: str, work_item_id: str,
                                status: str = "PENDING") -> Dict[str, Any]:
        return self._idempotent_insert(
            "reconciliations", "reconciliation_id", reconciliation_id,
            ("reconciliation_id", "work_item_id", "status", "reconciled_at"),
            (reconciliation_id, work_item_id, status, self._get_now_iso()),
        )

    def register_incident(self, *, incident_id: str, work_item_id: Optional[str],
                          severity: str, description: str) -> Dict[str, Any]:
        return self._idempotent_insert(
            "incidents", "incident_id", incident_id,
            ("incident_id", "work_item_id", "severity", "description", "created_at"),
            (incident_id, work_item_id, severity, description, self._get_now_iso()),
        )

    def set_dispatch_status(self, dispatch_id: str, status: str) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM platform_dispatches WHERE dispatch_id=?", (dispatch_id,)
            ).fetchone()
            if row is None:
                raise WorkItemNotFoundError(f"dispatch {dispatch_id} not found")
            conn.execute(
                "UPDATE platform_dispatches SET status=? WHERE dispatch_id=?",
                (status, dispatch_id),
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM platform_dispatches WHERE dispatch_id=?", (dispatch_id,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def set_reconciliation_status(self, reconciliation_id: str, status: str) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM reconciliations WHERE reconciliation_id=?", (reconciliation_id,)
            ).fetchone()
            if row is None:
                raise WorkItemNotFoundError(f"reconciliation {reconciliation_id} not found")
            conn.execute(
                "UPDATE reconciliations SET status=? WHERE reconciliation_id=?",
                (status, reconciliation_id),
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM reconciliations WHERE reconciliation_id=?", (reconciliation_id,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def get_outbox_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM outbox_messages WHERE message_id=?", (message_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_dispatches_for_work_item(self, work_item_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT d.* FROM platform_dispatches d"
                " JOIN outbox_messages m ON m.message_id = d.message_id"
                " WHERE m.work_item_id=? ORDER BY d.dispatch_id", (work_item_id,)
            ).fetchall()]

    def get_reconciliations_for_work_item(self, work_item_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM reconciliations WHERE work_item_id=? ORDER BY reconciliation_id",
                (work_item_id,)
            ).fetchall()]

    # ------------------------------------------------------------------
    # Current sanitized destination readiness (schema v8).
    # ------------------------------------------------------------------

    def upsert_destination_readiness(self, *, row: Mapping[str, Any]) -> Dict[str, Any]:
        required = {
            "surface", "platform", "transport_registry_version", "transport_type",
            "readiness_state", "identity_match", "probe_kind", "probed_at_utc",
        }
        missing = sorted(required - set(row))
        if missing:
            raise ValueError(f"destination_readiness_missing_fields:{','.join(missing)}")
        state = str(row["readiness_state"])
        if state not in DESTINATION_READINESS_STATES:
            raise ValueError(f"destination_readiness_state_invalid:{state}")
        detail = row.get("sanitized_detail") or {}
        if not isinstance(detail, Mapping):
            raise ValueError("destination_readiness_detail_must_be_mapping")
        # Reject common secret-bearing field names before persistence. Probe implementations
        # additionally whitelist their emitted details; this is the durable backstop.
        forbidden = re.compile(
            r"(^|_)(token|secret|cookie|authorization|webhook_url|session|password)(_|$)",
            re.IGNORECASE,
        )
        if any(forbidden.search(str(key)) for key in detail):
            raise ValueError("destination_readiness_detail_contains_forbidden_field")
        values = (
            str(row["surface"]), str(row["platform"]),
            str(row["transport_registry_version"]), str(row["transport_type"]), state,
            str(row.get("destination_identity") or "") or None,
            int(bool(row["identity_match"])), str(row["probe_kind"]),
            str(row["probed_at_utc"]), canonical_json(dict(detail)),
        )
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO destination_readiness "
                "(surface,platform,transport_registry_version,transport_type,readiness_state,"
                "destination_identity,identity_match,probe_kind,probed_at_utc,sanitized_detail_json) "
                "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(surface) DO UPDATE SET "
                "platform=excluded.platform,transport_registry_version=excluded.transport_registry_version,"
                "transport_type=excluded.transport_type,readiness_state=excluded.readiness_state,"
                "destination_identity=excluded.destination_identity,identity_match=excluded.identity_match,"
                "probe_kind=excluded.probe_kind,probed_at_utc=excluded.probed_at_utc,"
                "sanitized_detail_json=excluded.sanitized_detail_json",
                values,
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM destination_readiness WHERE surface=?", (values[0],)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def list_destination_readiness(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM destination_readiness ORDER BY platform, surface"
            ).fetchall()]

    # ------------------------------------------------------------------
    # Performance observations + learning policy versions (schema v6).
    #
    # Observations are append-only and idempotent by exact observation identity.
    # Learning-policy versions are immutable, parent-retained history; rollback adds
    # a NEW version rather than rewriting existing rows.
    # ------------------------------------------------------------------

    def register_performance_observation(self, *, observation: Mapping[str, Any]) -> Dict[str, Any]:
        """Persist one performance observation (idempotent by observation_id).

        Re-registering the SAME exact observation identity (same ``observation_hash``) is an
        idempotent PASS. A conflicting content hash for the same identity raises
        ``PerformanceObservationConflictError`` and never silently overwrites history.
        """
        observation_id = str(observation["observation_id"])
        observation_hash = str(observation["observation_hash"])
        columns = (
            "observation_id", "schema_version", "dispatch_id", "work_item_id", "platform",
            "public_object_id", "public_object_url_hash", "observation_window", "scheduled_for_utc",
            "collected_at_utc", "collector_capability_version", "collection_status",
            "metrics_native_json", "metric_availability_json", "source_identity",
            "observation_hash", "learning_eligible",
        )
        values = tuple(observation.get(col) for col in columns)
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT * FROM performance_observations WHERE observation_id=?", (observation_id,)
            ).fetchone()
            if existing:
                if existing["observation_hash"] != observation_hash:
                    raise PerformanceObservationConflictError(
                        f"performance_observation_conflict:{observation_id}"
                    )
                conn.execute("COMMIT")
                return dict(conn.execute(
                    "SELECT * FROM performance_observations WHERE observation_id=?", (observation_id,)
                ).fetchone())
            placeholders = ",".join("?" for _ in columns)
            conn.execute(
                f"INSERT INTO performance_observations ({','.join(columns)}) VALUES ({placeholders})",
                values,
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM performance_observations WHERE observation_id=?", (observation_id,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def mark_performance_observation_collected(
        self, *, observation_id: str, collection_status: str, collected_at_utc: str,
        metrics_native_json: str, metric_availability_json: str,
        source_identity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record the collection outcome for a scheduled observation (read-only collection)."""
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM performance_observations WHERE observation_id=?", (observation_id,)
            ).fetchone()
            if row is None:
                raise WorkItemNotFoundError(f"performance_observation {observation_id} not found")
            resolved_source = str(source_identity or row["source_identity"])
            conn.execute(
                "UPDATE performance_observations SET collection_status=?, collected_at_utc=?,"
                " metrics_native_json=?, metric_availability_json=?, source_identity=?"
                " WHERE observation_id=?",
                (collection_status, collected_at_utc, metrics_native_json,
                 metric_availability_json, resolved_source, observation_id),
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM performance_observations WHERE observation_id=?", (observation_id,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def get_performance_observation(self, observation_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM performance_observations WHERE observation_id=?", (observation_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_performance_observations(
        self, *, dispatch_id: Optional[str] = None,
        collection_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM performance_observations"
        clauses: List[str] = []
        params: List[Any] = []
        if dispatch_id is not None:
            clauses.append("dispatch_id=?")
            params.append(dispatch_id)
        if collection_status is not None:
            clauses.append("collection_status=?")
            params.append(collection_status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY scheduled_for_utc, observation_id"
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def register_learning_policy(self, *, policy: Mapping[str, Any]) -> Dict[str, Any]:
        """Persist one immutable learning-policy version (idempotent by policy_version).

        Re-registering the same policy_version with an identical ``policy_hash`` is idempotent.
        A conflicting hash for the same version raises ``LearningPolicyConflictError``.
        """
        policy_version = str(policy["policy_version"])
        policy_hash = str(policy["policy_hash"])
        columns = (
            "policy_version", "parent_policy_version", "created_at_utc", "status", "decision",
            "sample_count", "confidence", "formula_version", "observation_ids_json",
            "evaluation_window", "accepted_changes_json", "bounded_delta_json",
            "rollback_reference", "decision_reason", "policy_payload_json", "policy_hash",
        )
        values = tuple(policy.get(col) for col in columns)
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT * FROM learning_policy_versions WHERE policy_version=?", (policy_version,)
            ).fetchone()
            if existing:
                if existing["policy_hash"] != policy_hash:
                    raise LearningPolicyConflictError(f"learning_policy_conflict:{policy_version}")
                conn.execute("COMMIT")
                return dict(conn.execute(
                    "SELECT * FROM learning_policy_versions WHERE policy_version=?", (policy_version,)
                ).fetchone())
            placeholders = ",".join("?" for _ in columns)
            conn.execute(
                f"INSERT INTO learning_policy_versions ({','.join(columns)}) VALUES ({placeholders})",
                values,
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM learning_policy_versions WHERE policy_version=?", (policy_version,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def set_learning_policy_status(self, *, policy_version: str, status: str) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM learning_policy_versions WHERE policy_version=?", (policy_version,)
            ).fetchone()
            if row is None:
                raise WorkItemNotFoundError(f"learning_policy {policy_version} not found")
            conn.execute(
                "UPDATE learning_policy_versions SET status=? WHERE policy_version=?",
                (status, policy_version),
            )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM learning_policy_versions WHERE policy_version=?", (policy_version,)
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def get_learning_policy(self, policy_version: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM learning_policy_versions WHERE policy_version=?", (policy_version,)
            ).fetchone()
            return dict(row) if row else None

    def list_learning_policies(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM learning_policy_versions ORDER BY created_at_utc, policy_version"
            ).fetchall()]

    def get_active_learning_policy(self) -> Optional[Dict[str, Any]]:
        """Return the most recently created ACTIVE learning-policy version, if any."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM learning_policy_versions WHERE status='ACTIVE'"
                " ORDER BY created_at_utc DESC, policy_version DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # Canonical operating-mode control (schema v7).
    # ------------------------------------------------------------------

    def get_operating_control(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM operating_controls WHERE singleton_id=1"
            ).fetchone()
            if row is None:
                raise DurableStateCorruptionError("canonical operating control missing")
            return dict(row)

    def update_operating_control(
        self, *, expected_state_version: int, operating_mode: str,
        control_source: str,
    ) -> Dict[str, Any]:
        """CAS-update operating policy only; never launch a cycle or publisher."""
        allowed = {
            "AUTONOMOUS_DEFAULT", "SUPERVISED_OPERATOR_GATE", "SHADOW_ONLY", "KILL_SWITCH"
        }
        if operating_mode not in allowed:
            raise ValueError(f"daily_app_operating_mode_invalid:{operating_mode}")
        if not re.fullmatch(r"[A-Z0-9_.:-]{1,64}", str(control_source or "")):
            raise ValueError("daily_app_control_source_invalid")
        expected = int(expected_state_version)
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            updated = conn.execute(
                "UPDATE operating_controls SET operating_mode=?, state_version=state_version+1,"
                " updated_at_utc=?, control_source=?"
                " WHERE singleton_id=1 AND state_version=?",
                (operating_mode, self._get_now_iso(), control_source, expected),
            ).rowcount
            if updated != 1:
                actual = conn.execute(
                    "SELECT state_version FROM operating_controls WHERE singleton_id=1"
                ).fetchone()
                raise OperatingModeConflictError(
                    f"operating_mode_cas_conflict:expected={expected}:actual="
                    f"{actual['state_version'] if actual else 'missing'}"
                )
            conn.execute("COMMIT")
            return dict(conn.execute(
                "SELECT * FROM operating_controls WHERE singleton_id=1"
            ).fetchone())
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Operator-requested cycle triggers (schema v9, append-only).
    # ------------------------------------------------------------------

    def record_operator_cycle_trigger(
        self,
        *,
        trigger_id: str,
        trigger_kind: str = "OPERATOR_REQUESTED",
        requested_mode: str,
        control_state_version: int,
        requested_at_utc: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Persist exactly one durable operator trigger request (idempotent single PENDING)."""
        if trigger_kind != "OPERATOR_REQUESTED":
            raise ValueError(f"operator_trigger_kind_invalid:{trigger_kind}")
        if requested_mode not in {
            "AUTONOMOUS_DEFAULT", "SUPERVISED_OPERATOR_GATE", "SHADOW_ONLY", "KILL_SWITCH",
        }:
            raise ValueError(f"operator_trigger_mode_invalid:{requested_mode}")
        if not re.fullmatch(r"[a-z0-9_.:-]{8,128}", str(trigger_id or "")):
            raise ValueError("operator_trigger_id_invalid")
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    "INSERT INTO operator_cycle_triggers VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        str(trigger_id),
                        trigger_kind,
                        requested_at_utc or self._get_now_iso(),
                        requested_mode,
                        int(control_state_version),
                        "PENDING",
                        None,
                        None,
                        None,
                    ),
                )
            except Exception as exc:
                existing = conn.execute(
                    "SELECT * FROM operator_cycle_triggers WHERE state='PENDING' LIMIT 1"
                ).fetchone()
                if existing is not None:
                    conn.execute("ROLLBACK")
                    raise OperatorTriggerAlreadyPendingError(
                        f"operator_trigger_already_pending:{existing['trigger_id']}"
                    ) from exc
                raise
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()
        pending = self.fetch_pending_operator_trigger()
        if pending is None:
            raise DurableStateCorruptionError("operator trigger insert lost")
        return pending

    def fetch_pending_operator_trigger(self) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM operator_cycle_triggers WHERE state='PENDING'"
                " ORDER BY requested_at_utc ASC, trigger_id ASC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def latest_operator_cycle_trigger(self) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM operator_cycle_triggers"
                " ORDER BY requested_at_utc DESC, trigger_id DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def consume_operator_cycle_trigger(
        self,
        trigger_id: str,
        *,
        window_id: Optional[str],
        detail: str,
        consumed_at_utc: Optional[str] = None,
    ) -> bool:
        """CAS-transition one PENDING trigger to CONSUMED exactly once (restart-safe)."""
        if not re.fullmatch(r"[A-Za-z0-9_.:@-]{1,192}", str(detail or "")):
            raise ValueError("operator_trigger_consumption_detail_invalid")
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            updated = conn.execute(
                "UPDATE operator_cycle_triggers SET state='CONSUMED', consumed_at_utc=?,"
                " consumed_window_id=?, consumption_detail=?"
                " WHERE trigger_id=? AND state='PENDING'",
                (
                    consumed_at_utc or self._get_now_iso(),
                    window_id,
                    detail,
                    str(trigger_id),
                ),
            ).rowcount
            conn.execute("COMMIT")
            return updated == 1
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def active_editorial_cycle_window_ids(self) -> List[str]:
        """Work items in EVIDENCE_PENDING with a live ACTIVE lease (one canonical cycle running)."""
        with self.get_connection() as conn:
            now = self._get_now_iso()
            rows = conn.execute(
                "SELECT DISTINCT w.work_item_id FROM work_items w"
                " JOIN leases l ON l.work_item_id = w.work_item_id"
                " WHERE w.current_state='EVIDENCE_PENDING' AND l.status='ACTIVE'"
                " AND l.expires_at > ? ORDER BY w.work_item_id",
                (now,),
            ).fetchall()
            return [str(row["work_item_id"]) for row in rows]

    def stale_editorial_cycle_window_ids(self) -> List[str]:
        """Pending canonical cycles whose original owner no longer has a live lease.

        A host stop can occur after the work item enters ``EVIDENCE_PENDING`` but before the
        newsroom returns.  Scheduled windows are not necessarily evaluated again after their
        wall-clock interval ends, so startup housekeeping must be able to find and terminalize
        those abandoned claims without re-running them.
        """
        with self.get_connection() as conn:
            now = self._get_now_iso()
            rows = conn.execute(
                "SELECT w.work_item_id FROM work_items w"
                " WHERE w.current_state='EVIDENCE_PENDING'"
                " AND w.target_surface IN"
                " ('daily_app_editorial_window','daily_app_material_event_window')"
                " AND NOT EXISTS ("
                "   SELECT 1 FROM leases l WHERE l.work_item_id=w.work_item_id"
                "   AND l.status='ACTIVE' AND l.expires_at > ?"
                " ) ORDER BY w.work_item_id",
                (now,),
            ).fetchall()
            return [str(row["work_item_id"]) for row in rows]
