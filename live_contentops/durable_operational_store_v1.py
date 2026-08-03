"""Single Authoritative ContentOps SQLite WAL Operational Store & Canonical State Machine v1.

Wave 02 Execution Mode: LOCAL_DURABLE_STATE_FINAL_CORRECTION_NO_LIVE_ACTION

Key Features:
1. SQLite WAL mode (PRAGMA journal_mode=WAL;), foreign keys (PRAGMA foreign_keys=ON;), busy timeout.
2. Explicit transactions (BEGIN IMMEDIATE) with atomic versioned migrations (v1 -> v2 -> v3) and checksum validation.
3. Cryptographically bound genesis events (WORK_ITEM_CREATED) for work item initialization.
4. Schema-versioned canonical event payload JSON and SHA-256 envelope hashing across all semantic fields.
5. Genuinely immutable registered artifact references with byte/receipt verification and DB-level UPDATE/DELETE triggers.
6. Monotonic lease fencing tokens required on every work-item state mutation.
7. Fail-closed Wave 02 authority guard rejecting protected authority-bearing state transitions.
8. Deterministic event replay and state corruption detection.
9. PRAGMA-verified deterministic export with adversarial redaction.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

SCHEMA_VERSION = 3
BUSY_TIMEOUT_MS = 5000

# Canonical 29 States
CANONICAL_STATES = frozenset({
    "DISCOVERED",
    "EVIDENCE_PENDING",
    "EVIDENCE_READY",
    "EVIDENCE_BLOCKED",
    "ASSIGNMENT_CANDIDATE",
    "ASSIGNED",
    "DEFERRED",
    "DUPLICATE",
    "REJECTED",
    "PRODUCTION_IN_PROGRESS",
    "REVIEW_BLOCKED",
    "REVIEW_READY",
    "OPERATOR_PENDING",
    "APPROVED_EXACT",
    "HELD",
    "EXPIRED",
    "OUTBOX_READY",
    "DISPATCHING",
    "PARTIAL_SUCCESS",
    "UNKNOWN_WRITE",
    "DISPATCH_BLOCKED",
    "DISPATCH_COMPLETE",
    "RECONCILING",
    "COMPLETE",
    "DEAD_LETTER",
    "OPERATOR_RECOVERY_REQUIRED",
    "OBSERVATION_PENDING",
    "LEARNING_REVIEW_READY",
    "CLOSED",
})

# Wave 02 Protected Authority-Bearing States (Fail-Closed Guard)
WAVE02_PROTECTED_STATES = frozenset({
    "APPROVED_EXACT",
    "OUTBOX_READY",
    "DISPATCHING",
    "PARTIAL_SUCCESS",
    "UNKNOWN_WRITE",
    "DISPATCH_BLOCKED",
    "DISPATCH_COMPLETE",
    "RECONCILING",
    "COMPLETE",
})

# Valid State Transition Graph
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
    "APPROVED_EXACT": {"OUTBOX_READY"},
    "HELD": {"DEFERRED", "REJECTED"},
    "EXPIRED": {"CLOSED"},
    "OUTBOX_READY": {"DISPATCHING"},
    "DISPATCHING": {"PARTIAL_SUCCESS", "UNKNOWN_WRITE", "DISPATCH_BLOCKED", "DISPATCH_COMPLETE"},
    "PARTIAL_SUCCESS": {"RECONCILING", "OPERATOR_RECOVERY_REQUIRED"},
    "UNKNOWN_WRITE": {"RECONCILING", "OPERATOR_RECOVERY_REQUIRED"},
    "DISPATCH_BLOCKED": {"HELD", "DEAD_LETTER"},
    "DISPATCH_COMPLETE": {"RECONCILING"},
    "RECONCILING": {"COMPLETE", "DEAD_LETTER", "OPERATOR_RECOVERY_REQUIRED"},
    "COMPLETE": {"OBSERVATION_PENDING"},
    "DEAD_LETTER": {"OPERATOR_RECOVERY_REQUIRED", "CLOSED"},
    "OPERATOR_RECOVERY_REQUIRED": {"ASSIGNMENT_CANDIDATE", "CLOSED"},
    "OBSERVATION_PENDING": {"LEARNING_REVIEW_READY"},
    "LEARNING_REVIEW_READY": {"CLOSED"},
    "CLOSED": set(),
    "DEFERRED": {"ASSIGNMENT_CANDIDATE"},
    "DUPLICATE": {"CLOSED"},
    "REJECTED": {"CLOSED"},
}

GENESIS_PREVIOUS_HASH = "GENESIS_" + "0" * 64


# --- Exceptions ---

class DurableStoreError(Exception):
    """Base exception for durable store operations."""


class MigrationError(DurableStoreError):
    """Raised when schema migration or backup fails."""


class InvalidStateTransitionError(DurableStoreError):
    """Raised when a state transition is not allowed by the transition graph."""


class CASStateConflictError(DurableStoreError):
    """Raised when Compare-And-Set state version or current state mismatches."""


class TransitionValidationError(DurableStoreError):
    """Raised when transition parameters or artifact hashes are invalid."""


class WorkItemNotFoundError(DurableStoreError):
    """Raised when a requested work item does not exist."""


class StaleFencingTokenError(DurableStoreError):
    """Raised when a mutation attempt uses a stale or invalid lease fencing token."""


class LeaseConflictError(DurableStoreError):
    """Raised when acquiring an active lease conflicts with an existing unexpired lock."""


class DurableStateCorruptionError(DurableStoreError):
    """Raised when deterministic replay detects event sequence or projection corruption."""


class Wave02AuthorityViolationError(DurableStoreError):
    """Raised when an operation attempts to enter an authority-bearing state in Wave 02."""


class ArtifactNotFoundError(DurableStoreError):
    """Raised when a referenced artifact ID is not registered."""


class ArtifactValidationError(DurableStoreError):
    """Raised when artifact metadata or hash is invalid."""


# --- Utility Functions ---

def utc_now_iso() -> str:
    """Return ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def compute_sha256(data: Union[str, bytes]) -> str:
    """Compute hex SHA-256 digest."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def is_valid_sha256(hash_str: str) -> bool:
    """Check if string is a valid 64-character hex SHA-256."""
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", hash_str))


def split_sql_statements(sql_script: str) -> List[str]:
    """Split SQL script into individual executable statements, preserving BEGIN...END trigger blocks."""
    statements = []
    current_stmt = []
    in_trigger = False

    for line in sql_script.splitlines():
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("--"):
            continue

        current_stmt.append(line)

        upper = line_clean.upper()
        if "CREATE TRIGGER" in upper:
            in_trigger = True
        if in_trigger and upper == "END;":
            in_trigger = False
            statements.append("\n".join(current_stmt).strip())
            current_stmt = []
            continue

        if not in_trigger and line_clean.endswith(";"):
            statements.append("\n".join(current_stmt).strip())
            current_stmt = []

    if current_stmt:
        remaining = "\n".join(current_stmt).strip()
        if remaining:
            statements.append(remaining)

    return statements


# --- Migration Scripts ---

MIGRATION_V1_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operational_windows (
    window_id TEXT PRIMARY KEY,
    window_key TEXT NOT NULL UNIQUE,
    started_at TEXT NOT NULL,
    closed_at TEXT,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'CLOSED', 'HALTED'))
);

CREATE TABLE IF NOT EXISTS scheduler_ticks (
    tick_id TEXT PRIMARY KEY,
    window_id TEXT NOT NULL,
    tick_number INTEGER NOT NULL,
    evaluated_at TEXT NOT NULL,
    work_items_evaluated INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(window_id) REFERENCES operational_windows(window_id)
);

CREATE TABLE IF NOT EXISTS work_items (
    work_item_id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    title TEXT NOT NULL,
    current_state TEXT NOT NULL,
    state_version INTEGER NOT NULL DEFAULT 1,
    target_surface TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS story_versions (
    story_version_id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    version_num INTEGER NOT NULL,
    headline TEXT NOT NULL,
    body_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL,
    assignee_ref TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'RELEASED', 'COMPLETED')),
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS artifact_references (
    artifact_id TEXT PRIMARY KEY,
    artifact_type TEXT NOT NULL,
    story_id TEXT,
    work_item_id TEXT,
    storage_class TEXT NOT NULL,
    byte_length INTEGER NOT NULL,
    sha256_hash TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    producer_ref TEXT NOT NULL,
    sensitivity_class TEXT NOT NULL DEFAULT 'PUBLIC',
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS transition_events (
    event_id TEXT PRIMARY KEY,
    transition_key TEXT NOT NULL UNIQUE,
    work_item_id TEXT NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    state_version INTEGER NOT NULL,
    actor_class TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    explanation TEXT NOT NULL,
    artifact_hash_set TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    authority_granted INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS model_invocations (
    invocation_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    invoked_at TEXT NOT NULL,
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS review_records (
    review_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL,
    reviewer_ref TEXT NOT NULL,
    decision TEXT NOT NULL,
    notes TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS operator_decisions (
    decision_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL,
    operator_ref TEXT NOT NULL,
    action TEXT NOT NULL,
    notes TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS leases (
    lease_id TEXT PRIMARY KEY,
    lease_key TEXT NOT NULL UNIQUE,
    work_item_id TEXT,
    owner_ref TEXT NOT NULL,
    fencing_token INTEGER NOT NULL,
    acquired_at TEXT NOT NULL,
    renewed_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'EXPIRED', 'RELEASED')),
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS heartbeats (
    heartbeat_id TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL UNIQUE,
    lease_id TEXT,
    last_seen_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ALIVE', 'DEAD')),
    FOREIGN KEY(lease_id) REFERENCES leases(lease_id)
);

CREATE TABLE IF NOT EXISTS approval_envelopes (
    envelope_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'HELD',
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS outbox_messages (
    message_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL,
    destination TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TEXT NOT NULL,
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS platform_dispatches (
    dispatch_id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    dispatched_at TEXT NOT NULL,
    FOREIGN KEY(message_id) REFERENCES outbox_messages(message_id)
);

CREATE TABLE IF NOT EXISTS readbacks (
    readback_id TEXT PRIMARY KEY,
    dispatch_id TEXT NOT NULL,
    readback_data TEXT NOT NULL,
    read_at TEXT NOT NULL,
    FOREIGN KEY(dispatch_id) REFERENCES platform_dispatches(dispatch_id)
);

CREATE TABLE IF NOT EXISTS reconciliations (
    reconciliation_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    reconciled_at TEXT NOT NULL,
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    work_item_id TEXT,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics (
    metric_id TEXT PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback_records (
    feedback_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL,
    source TEXT NOT NULL,
    rating REAL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_reviews (
    review_id TEXT PRIMARY KEY,
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS trg_transition_events_no_update
BEFORE UPDATE ON transition_events
BEGIN
    SELECT RAISE(ABORT, 'transition_events are append-only: UPDATE forbidden');
END;

CREATE TRIGGER IF NOT EXISTS trg_transition_events_no_delete
BEFORE DELETE ON transition_events
BEGIN
    SELECT RAISE(ABORT, 'transition_events are append-only: DELETE forbidden');
END;
"""

MIGRATION_V2_SQL = """
ALTER TABLE transition_events ADD COLUMN event_seq INTEGER NOT NULL DEFAULT 1;
ALTER TABLE transition_events ADD COLUMN previous_event_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE transition_events ADD COLUMN event_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE transition_events ADD COLUMN policy_version TEXT NOT NULL DEFAULT 'contentops.policy.v1';
ALTER TABLE transition_events ADD COLUMN model_version TEXT NOT NULL DEFAULT 'NOT_APPLICABLE';
ALTER TABLE transition_events ADD COLUMN authority_type TEXT NOT NULL DEFAULT 'NONE';
ALTER TABLE transition_events ADD COLUMN authority_ref TEXT;
ALTER TABLE transition_events ADD COLUMN authority_effect TEXT NOT NULL DEFAULT 'NO_AUTHORITY_GRANTED';
ALTER TABLE transition_events ADD COLUMN input_artifact_ids TEXT NOT NULL DEFAULT '[]';
ALTER TABLE transition_events ADD COLUMN output_artifact_ids TEXT NOT NULL DEFAULT '[]';

CREATE UNIQUE INDEX IF NOT EXISTS idx_transition_events_work_item_seq
ON transition_events(work_item_id, event_seq);
"""

MIGRATION_V3_SQL = """
-- Drop old triggers
DROP TRIGGER IF EXISTS trg_transition_events_no_update;
DROP TRIGGER IF EXISTS trg_transition_events_no_delete;

-- Create new transition_events_v3 table
CREATE TABLE transition_events_v3 (
    event_id TEXT PRIMARY KEY,
    transition_key TEXT NOT NULL UNIQUE,
    work_item_id TEXT NOT NULL,
    event_seq INTEGER NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    state_version INTEGER NOT NULL,
    actor_class TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    explanation TEXT NOT NULL,
    explanation_hash TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    policy_version TEXT NOT NULL DEFAULT 'contentops.policy.v1',
    model_version TEXT NOT NULL DEFAULT 'NOT_APPLICABLE',
    authority_type TEXT NOT NULL DEFAULT 'NONE',
    authority_ref TEXT,
    authority_effect TEXT NOT NULL DEFAULT 'NO_AUTHORITY_GRANTED',
    lease_id TEXT,
    lease_key TEXT,
    fencing_token INTEGER NOT NULL DEFAULT 0,
    input_artifact_ids TEXT NOT NULL DEFAULT '[]',
    output_artifact_ids TEXT NOT NULL DEFAULT '[]',
    artifact_snapshot_json TEXT NOT NULL DEFAULT '[]',
    previous_event_hash TEXT NOT NULL,
    event_payload_json TEXT NOT NULL DEFAULT '',
    event_hash TEXT NOT NULL DEFAULT '',
    timestamp_utc TEXT NOT NULL,
    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)
);

-- Copy all existing rows from transition_events cleanly into transition_events_v3
INSERT INTO transition_events_v3 (
    event_id, transition_key, work_item_id, event_seq, from_state, to_state, state_version,
    actor_class, actor_ref, reason_code, explanation, explanation_hash, correlation_id,
    policy_version, model_version, authority_type, authority_ref, authority_effect,
    lease_id, lease_key, fencing_token, input_artifact_ids, output_artifact_ids,
    artifact_snapshot_json, previous_event_hash, event_payload_json, event_hash, timestamp_utc
)
SELECT
    event_id,
    transition_key,
    work_item_id,
    COALESCE(event_seq, 1),
    from_state,
    to_state,
    state_version,
    actor_class,
    actor_ref,
    reason_code,
    explanation,
    '',
    correlation_id,
    COALESCE(policy_version, 'contentops.policy.v1'),
    COALESCE(model_version, 'NOT_APPLICABLE'),
    COALESCE(authority_type, 'NONE'),
    authority_ref,
    COALESCE(authority_effect, 'NO_AUTHORITY_GRANTED'),
    NULL,
    NULL,
    0,
    COALESCE(input_artifact_ids, '[]'),
    COALESCE(output_artifact_ids, '[]'),
    '[]',
    COALESCE(NULLIF(previous_event_hash, ''), 'GENESIS_0000000000000000000000000000000000000000000000000000000000000000'),
    '',
    '',
    timestamp_utc
FROM transition_events;

-- Drop original transition_events table and rename transition_events_v3
DROP TABLE transition_events;
ALTER TABLE transition_events_v3 RENAME TO transition_events;

CREATE UNIQUE INDEX IF NOT EXISTS idx_transition_events_work_item_seq
ON transition_events(work_item_id, event_seq);

-- Attach artifact_references immutability triggers
CREATE TRIGGER IF NOT EXISTS trg_artifact_references_no_update
BEFORE UPDATE ON artifact_references
BEGIN
    SELECT RAISE(ABORT, 'artifact_references are immutable: UPDATE forbidden');
END;

CREATE TRIGGER IF NOT EXISTS trg_artifact_references_no_delete
BEFORE DELETE ON artifact_references
BEGIN
    SELECT RAISE(ABORT, 'artifact_references are immutable: DELETE forbidden');
END;
"""

MIGRATIONS: List[Tuple[int, str, str]] = [
    (1, "Initial Wave 02 Durable Operational Store Schema", MIGRATION_V1_SQL),
    (2, "Wave 02 Fencing, Artifact Integrity, and Structured Event Chain Upgrade", MIGRATION_V2_SQL),
    (3, "Wave 02 Schema v3: Cryptographic Event Payload Envelope and Immutable Artifact Triggers", MIGRATION_V3_SQL),
]


class ContentOpsDurableStore:
    """Single authoritative SQLite WAL operational store and canonical state machine."""

    def __init__(
        self,
        db_path: pathlib.Path,
        busy_timeout_ms: int = BUSY_TIMEOUT_MS,
        auto_migrate: bool = True,
        now_fn: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.db_path = pathlib.Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.busy_timeout_ms = busy_timeout_ms
        self._now_fn = now_fn

        if auto_migrate:
            self.run_migrations()

    def _get_now(self) -> datetime:
        if self._now_fn is not None:
            now = self._now_fn()
            if now.tzinfo is None:
                return now.replace(tzinfo=timezone.utc)
            return now
        return datetime.now(timezone.utc)

    def _get_now_iso(self) -> str:
        return self._get_now().isoformat()

    def get_connection(self) -> sqlite3.Connection:
        """Create a new connection configured for WAL mode, foreign keys, and busy timeout."""
        conn = sqlite3.connect(str(self.db_path), timeout=self.busy_timeout_ms / 1000.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms};")
        return conn

    def query_pragmas(self) -> Dict[str, Any]:
        """Query actual SQLite PRAGMA settings on a live connection."""
        conn = self.get_connection()
        try:
            journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            foreign_keys = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
            busy_timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
            return {
                "journal_mode": str(journal_mode).upper(),
                "foreign_keys": int(foreign_keys),
                "busy_timeout_ms": int(busy_timeout),
            }
        finally:
            conn.close()

    def verify_schema_integrity(self) -> bool:
        """Run SQLite B-tree integrity check."""
        conn = self.get_connection()
        try:
            res = conn.execute("PRAGMA integrity_check;").fetchone()[0]
            if str(res).lower() != "ok":
                raise DurableStateCorruptionError(f"Database B-tree corruption detected: {res}")
            return True
        finally:
            conn.close()

    def get_current_schema_version(self) -> int:
        """Get highest applied schema version."""
        conn = self.get_connection()
        try:
            tbl_check = conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations';"
            ).fetchone()[0]
            if not tbl_check:
                return 0
            row = conn.execute("SELECT MAX(version) AS max_ver FROM schema_migrations;").fetchone()
            return row["max_ver"] if row and row["max_ver"] is not None else 0
        finally:
            conn.close()

    def verify_applied_migrations(self) -> bool:
        """Verify checksum immutability, contiguity, and registry matching across all applied migrations."""
        conn = self.get_connection()
        try:
            tbl_check = conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations';"
            ).fetchone()[0]
            if not tbl_check:
                return True

            applied = conn.execute("SELECT * FROM schema_migrations ORDER BY version ASC;").fetchall()
            if not applied:
                return True

            sorted_migrations = {m[0]: m for m in MIGRATIONS}
            max_registry_ver = max(sorted_migrations.keys())
            applied_versions = [row["version"] for row in applied]

            if len(applied_versions) != len(set(applied_versions)):
                raise MigrationError("Duplicate migration versions found in schema_migrations")

            max_applied_ver = max(applied_versions)
            if max_applied_ver > max_registry_ver:
                raise MigrationError(f"Database schema version {max_applied_ver} is ahead of embedded registry max {max_registry_ver}")

            for idx, ver in enumerate(applied_versions):
                expected_ver = idx + 1
                if ver != expected_ver:
                    raise MigrationError(f"Non-contiguous or missing applied migration history: expected version {expected_ver}, got {ver}")

            for row in applied:
                ver = row["version"]
                if ver not in sorted_migrations:
                    raise MigrationError(f"Applied migration version {ver} not found in embedded registry")
                expected_sql = sorted_migrations[ver][2]
                expected_checksum = compute_sha256(expected_sql)
                if row["checksum"] != expected_checksum:
                    raise MigrationError(f"Checksum drift for migration v{ver}: expected {expected_checksum}, recorded {row['checksum']}")

            return True
        finally:
            conn.close()

    def create_wal_safe_backup(self) -> pathlib.Path:
        """Create a WAL-safe online backup using SQLite's backup API."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_path = self.db_path.parent / f"{self.db_path.name}.bak.{timestamp}"

        conn = self.get_connection()
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            bck_conn = sqlite3.connect(str(backup_path))
            try:
                conn.backup(bck_conn)
            finally:
                bck_conn.close()
            return backup_path
        finally:
            conn.close()

    def restore_from_backup(self, backup_path: pathlib.Path) -> None:
        """Restore database from a WAL-safe backup, ensuring lingering WAL/SHM artifacts are removed."""
        if not backup_path.exists():
            raise MigrationError(f"Backup path {backup_path} does not exist")

        wal_file = pathlib.Path(f"{self.db_path}-wal")
        shm_file = pathlib.Path(f"{self.db_path}-shm")

        if wal_file.exists():
            wal_file.unlink()
        if shm_file.exists():
            shm_file.unlink()

        shutil.copy2(backup_path, self.db_path)

    def run_migrations(self) -> int:
        """Run pending versioned migrations in contiguous order with atomic transaction boundaries."""
        self.verify_applied_migrations()
        current_version = self.get_current_schema_version()
        applied_count = 0

        sorted_migrations = sorted(MIGRATIONS, key=lambda m: m[0])

        for idx, (ver, desc, sql) in enumerate(sorted_migrations):
            expected_ver = idx + 1
            if ver != expected_ver:
                raise MigrationError(f"Non-contiguous migration version: got {ver}, expected {expected_ver}")

        for version, description, sql_script in sorted_migrations:
            if version <= current_version:
                continue

            checksum = compute_sha256(sql_script)
            backup_file = self.create_wal_safe_backup()

            conn = self.get_connection()
            try:
                conn.execute("BEGIN IMMEDIATE;")

                for stmt in split_sql_statements(sql_script):
                    conn.execute(stmt)

                if version == 3:
                    rows_to_backfill = conn.execute(
                        "SELECT t.*, w.story_id FROM transition_events t "
                        "LEFT JOIN work_items w ON t.work_item_id = w.work_item_id "
                        "WHERE t.event_payload_json IS NULL OR t.event_payload_json = '';"
                    ).fetchall()

                    for row in rows_to_backfill:
                        exp_hash = row["explanation_hash"] if row["explanation_hash"] else compute_sha256(row["explanation"] or "")
                        story_id = row["story_id"] or f"story_{row['work_item_id']}"
                        p_dict = {
                            "event_schema_version": "contentops.event_payload.legacy_v1",
                            "event_seq": row["event_seq"],
                            "work_item_id": row["work_item_id"],
                            "story_id": story_id,
                            "state_version": row["state_version"],
                            "from_state": row["from_state"],
                            "to_state": row["to_state"],
                            "previous_event_hash": row["previous_event_hash"] or GENESIS_PREVIOUS_HASH,
                            "actor_class": row["actor_class"],
                            "actor_ref": row["actor_ref"],
                            "reason_code": row["reason_code"],
                            "explanation_hash": exp_hash,
                            "correlation_id": row["correlation_id"],
                            "policy_version": row["policy_version"] or "contentops.policy.v1",
                            "model_version": row["model_version"] or "NOT_APPLICABLE",
                            "authority_type": row["authority_type"] or "NONE",
                            "authority_ref": row["authority_ref"],
                            "authority_effect": row["authority_effect"] or "NO_AUTHORITY_GRANTED",
                            "lease_id": row["lease_id"],
                            "lease_key": row["lease_key"],
                            "fencing_token": row["fencing_token"] or 0,
                            "input_artifact_ids": json.loads(row["input_artifact_ids"]) if row["input_artifact_ids"] else [],
                            "output_artifact_ids": json.loads(row["output_artifact_ids"]) if row["output_artifact_ids"] else [],
                            "artifact_snapshots": json.loads(row["artifact_snapshot_json"]) if row["artifact_snapshot_json"] else [],
                            "timestamp_utc": row["timestamp_utc"],
                        }
                        p_json = json.dumps(p_dict, sort_keys=True)
                        e_hash = compute_sha256(p_json)
                        conn.execute(
                            "UPDATE transition_events SET explanation_hash = ?, event_payload_json = ?, event_hash = ? WHERE event_id = ?;",
                            (exp_hash, p_json, e_hash, row["event_id"]),
                        )

                    conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_transition_events_no_update
                    BEFORE UPDATE ON transition_events
                    BEGIN
                        SELECT RAISE(ABORT, 'transition_events are append-only: UPDATE forbidden');
                    END;
                    """)
                    conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_transition_events_no_delete
                    BEFORE DELETE ON transition_events
                    BEGIN
                        SELECT RAISE(ABORT, 'transition_events are append-only: DELETE forbidden');
                    END;
                    """)

                conn.execute(
                    "INSERT INTO schema_migrations (version, checksum, applied_at, description) VALUES (?, ?, ?, ?);",
                    (version, checksum, utc_now_iso(), description),
                )
                conn.execute("COMMIT;")
                applied_count += 1
            except Exception as exc:
                try:
                    conn.execute("ROLLBACK;")
                except Exception:
                    pass
                conn.close()
                self.restore_from_backup(backup_file)
                raise MigrationError(f"Failed migration version {version}: {exc}") from exc
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
                if backup_file.exists():
                    try:
                        backup_file.unlink()
                    except Exception:
                        pass

        self.verify_applied_migrations()
        self.verify_schema_integrity()
        return applied_count

    # --- Immutable Artifact Registration ---

    def register_artifact(
        self,
        *,
        artifact_id: str,
        artifact_type: str,
        storage_class: str,
        schema_version: str,
        producer_ref: str,
        content_bytes: Optional[bytes] = None,
        verified_receipt: Optional[Dict[str, Any]] = None,
        story_id: Optional[str] = None,
        work_item_id: Optional[str] = None,
        sensitivity_class: str = "PUBLIC",
    ) -> Dict[str, Any]:
        """Register an immutable artifact reference deriving length and SHA-256 from exact bytes or verified receipt."""
        if not artifact_id or not artifact_type or not storage_class or not schema_version or not producer_ref:
            raise ArtifactValidationError("Missing required artifact registration parameter")

        if content_bytes is not None:
            byte_length = len(content_bytes)
            sha256_hash = compute_sha256(content_bytes)
        elif verified_receipt is not None:
            if not isinstance(verified_receipt, dict):
                raise ArtifactValidationError("verified_receipt must be a dictionary")

            schema_ver = verified_receipt.get("schema_version")
            if not schema_ver:
                raise ArtifactValidationError("verified_receipt missing required schema_version")

            receipt_id = verified_receipt.get("receipt_id")
            source_id = verified_receipt.get("source_identity") or verified_receipt.get("repository_identity")
            obj_id = verified_receipt.get("object_identity") or verified_receipt.get("path_identity")
            verifier_ref = verified_receipt.get("verifier_ref") or verified_receipt.get("verifier_provenance")
            blob_hash = verified_receipt.get("blob_hash") or verified_receipt.get("sha256_hash")

            byte_length = verified_receipt.get("byte_length", 0)
            sha256_hash = verified_receipt.get("sha256_hash", "")

            if not receipt_id or not source_id or not obj_id or not verifier_ref or not blob_hash:
                raise ArtifactValidationError("verified_receipt missing required contract identity or provenance fields")

            if byte_length <= 0 or not is_valid_sha256(sha256_hash):
                raise ArtifactValidationError("verified_receipt must contain valid byte_length > 0 and 64-char SHA-256")
        else:
            raise ArtifactValidationError("register_artifact requires either content_bytes or verified_receipt")

        now_iso = self._get_now_iso()
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")

            existing = conn.execute("SELECT * FROM artifact_references WHERE artifact_id = ?;", (artifact_id,)).fetchone()
            if existing:
                if existing["sha256_hash"] != sha256_hash or existing["byte_length"] != byte_length:
                    raise ArtifactValidationError(f"Artifact {artifact_id} registered previously with conflicting hash/length")
                conn.execute("COMMIT;")
                return dict(existing)

            conn.execute(
                """
                INSERT INTO artifact_references (
                    artifact_id, artifact_type, story_id, work_item_id, storage_class,
                    byte_length, sha256_hash, schema_version, created_at, producer_ref, sensitivity_class
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    artifact_id,
                    artifact_type,
                    story_id,
                    work_item_id,
                    storage_class,
                    byte_length,
                    sha256_hash,
                    schema_version,
                    now_iso,
                    producer_ref,
                    sensitivity_class,
                ),
            )
            conn.execute("COMMIT;")
            return {
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "story_id": story_id,
                "work_item_id": work_item_id,
                "storage_class": storage_class,
                "byte_length": byte_length,
                "sha256_hash": sha256_hash,
                "schema_version": schema_version,
                "created_at": now_iso,
                "producer_ref": producer_ref,
                "sensitivity_class": sensitivity_class,
            }
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def get_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """Fetch registered artifact reference."""
        conn = self.get_connection()
        try:
            row = conn.execute("SELECT * FROM artifact_references WHERE artifact_id = ?;", (artifact_id,)).fetchone()
            if not row:
                raise ArtifactNotFoundError(f"Artifact {artifact_id} not registered")
            return dict(row)
        finally:
            conn.close()

    # --- Work Item Management with Genesis Events ---

    def create_work_item(
        self,
        *,
        story_id: str,
        title: str,
        target_surface: str,
        work_item_id: Optional[str] = None,
        actor_ref: str = "producer_ref",
        correlation_id: Optional[str] = None,
        input_artifact_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new work item in DISCOVERED state with an atomic WORK_ITEM_CREATED genesis event."""
        now_iso = self._get_now_iso()
        item_id = work_item_id or f"wi_{compute_sha256(story_id + title + now_iso)[:16]}"
        corr_id = correlation_id or f"corr_init_{item_id}"
        input_arts = input_artifact_ids or []

        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")

            # Check if item exists
            existing = conn.execute("SELECT * FROM work_items WHERE work_item_id = ?;", (item_id,)).fetchone()
            if existing:
                if existing["story_id"] != story_id or existing["title"] != title or existing["target_surface"] != target_surface:
                    raise ValueError(f"Conflicting recreation for existing work item {item_id}")
                conn.execute("COMMIT;")
                return dict(existing)

            # Validate input artifacts exist and story association matches
            artifact_snapshots = []
            for art_id in input_arts:
                art_row = conn.execute("SELECT * FROM artifact_references WHERE artifact_id = ?;", (art_id,)).fetchone()
                if not art_row:
                    raise ArtifactNotFoundError(f"Input artifact {art_id} for genesis not found")

                art_story = art_row["story_id"]
                if art_story and art_story != story_id:
                    if art_row["storage_class"] not in ("GLOBAL", "REUSABLE") and art_row["sensitivity_class"] != "PUBLIC":
                        raise ArtifactValidationError(
                            f"Artifact {art_id} belongs to story {art_story} and cannot be bound to story {story_id}"
                        )

                artifact_snapshots.append({
                    "artifact_id": art_row["artifact_id"],
                    "artifact_type": art_row["artifact_type"],
                    "storage_class": art_row["storage_class"],
                    "byte_length": art_row["byte_length"],
                    "sha256_hash": art_row["sha256_hash"],
                    "schema_version": art_row["schema_version"],
                    "producer_ref": art_row["producer_ref"],
                })

            conn.execute(
                """
                INSERT INTO work_items (
                    work_item_id, story_id, title, current_state, state_version, target_surface, created_at, updated_at
                ) VALUES (?, ?, ?, 'DISCOVERED', 1, ?, ?, ?);
                """,
                (item_id, story_id, title, target_surface, now_iso, now_iso),
            )

            # Build Genesis Event (seq 1, WORK_ITEM_CREATED)
            genesis_payload_dict = {
                "event_schema_version": "contentops.event_payload.v1",
                "event_seq": 1,
                "work_item_id": item_id,
                "story_id": story_id,
                "title": title,
                "target_surface": target_surface,
                "state_version": 1,
                "from_state": "DISCOVERED",
                "to_state": "DISCOVERED",
                "previous_event_hash": GENESIS_PREVIOUS_HASH,
                "actor_class": "ContentOpsDurableStore",
                "actor_ref": actor_ref,
                "reason_code": "WORK_ITEM_INITIALIZATION",
                "explanation_hash": compute_sha256(f"Genesis event for work item {item_id} story {story_id}"),
                "correlation_id": corr_id,
                "policy_version": "contentops.policy.v1",
                "model_version": "NOT_APPLICABLE",
                "authority_type": "NONE",
                "authority_ref": None,
                "authority_effect": "NO_AUTHORITY_GRANTED",
                "lease_id": None,
                "lease_key": None,
                "fencing_token": 0,
                "input_artifact_ids": sorted(input_arts),
                "output_artifact_ids": [],
                "artifact_snapshots": artifact_snapshots,
                "timestamp_utc": now_iso,
            }
            event_payload_json = json.dumps(genesis_payload_dict, sort_keys=True)
            event_hash = compute_sha256(event_payload_json)
            event_id = f"evt_{compute_sha256(event_hash)[:16]}"
            transition_key = f"tr_{item_id}_v1_genesis"

            conn.execute(
                """
                INSERT INTO transition_events (
                    event_id, transition_key, work_item_id, event_seq, from_state, to_state, state_version,
                    actor_class, actor_ref, reason_code, explanation, explanation_hash, correlation_id,
                    policy_version, model_version, authority_type, authority_ref, authority_effect,
                    lease_id, lease_key, fencing_token, input_artifact_ids, output_artifact_ids,
                    artifact_snapshot_json, previous_event_hash, event_payload_json, event_hash, timestamp_utc
                ) VALUES (?, ?, ?, 1, 'DISCOVERED', 'DISCOVERED', 1, 'ContentOpsDurableStore', ?, 'WORK_ITEM_INITIALIZATION',
                          ?, ?, ?, 'contentops.policy.v1', 'NOT_APPLICABLE', 'NONE', NULL, 'NO_AUTHORITY_GRANTED',
                          NULL, NULL, 0, ?, '[]', ?, ?, ?, ?, ?);
                """,
                (
                    event_id,
                    transition_key,
                    item_id,
                    actor_ref,
                    f"Genesis event for work item {item_id} story {story_id}",
                    compute_sha256(f"Genesis event for work item {item_id} story {story_id}"),
                    corr_id,
                    json.dumps(sorted(input_arts)),
                    json.dumps(artifact_snapshots),
                    GENESIS_PREVIOUS_HASH,
                    event_payload_json,
                    event_hash,
                    now_iso,
                ),
            )

            conn.execute("COMMIT;")

            return {
                "work_item_id": item_id,
                "story_id": story_id,
                "title": title,
                "current_state": "DISCOVERED",
                "state_version": 1,
                "target_surface": target_surface,
                "created_at": now_iso,
                "updated_at": now_iso,
                "genesis_event_id": event_id,
                "genesis_event_hash": event_hash,
            }
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def get_work_item(self, work_item_id: str) -> Dict[str, Any]:
        """Fetch work item record."""
        conn = self.get_connection()
        try:
            row = conn.execute("SELECT * FROM work_items WHERE work_item_id = ?;", (work_item_id,)).fetchone()
            if not row:
                raise WorkItemNotFoundError(f"Work item {work_item_id} not found")
            return dict(row)
        finally:
            conn.close()

    # --- Leases & Heartbeats ---

    def acquire_lease(
        self,
        lease_key: str,
        owner_ref: str,
        ttl_seconds: int = 30,
        work_item_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Acquire or update a lease with a monotonic fencing token."""
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        expires_iso = datetime.fromtimestamp(now_dt.timestamp() + ttl_seconds, timezone.utc).isoformat()
        lease_id = f"lease_{compute_sha256(lease_key + owner_ref + now_iso)[:16]}"

        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")

            existing = conn.execute("SELECT * FROM leases WHERE lease_key = ?;", (lease_key,)).fetchone()
            if existing:
                if existing["status"] == "ACTIVE" and existing["expires_at"] > now_iso and existing["owner_ref"] != owner_ref:
                    raise LeaseConflictError(f"Lease {lease_key} is active and held by {existing['owner_ref']}")

                next_fencing_token = existing["fencing_token"] + 1
                lease_id = existing["lease_id"]
                conn.execute(
                    """
                    UPDATE leases
                    SET owner_ref = ?, fencing_token = ?, acquired_at = ?, renewed_at = ?, expires_at = ?, status = 'ACTIVE', work_item_id = ?
                    WHERE lease_key = ?;
                    """,
                    (owner_ref, next_fencing_token, now_iso, now_iso, expires_iso, work_item_id, lease_key),
                )
            else:
                next_fencing_token = 1
                conn.execute(
                    """
                    INSERT INTO leases (
                        lease_id, lease_key, work_item_id, owner_ref, fencing_token,
                        acquired_at, renewed_at, expires_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE');
                    """,
                    (lease_id, lease_key, work_item_id, owner_ref, next_fencing_token, now_iso, now_iso, expires_iso),
                )

            conn.execute("COMMIT;")
            return {
                "lease_id": lease_id,
                "lease_key": lease_key,
                "work_item_id": work_item_id,
                "owner_ref": owner_ref,
                "fencing_token": next_fencing_token,
                "acquired_at": now_iso,
                "renewed_at": now_iso,
                "expires_at": expires_iso,
                "status": "ACTIVE",
            }
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def renew_lease(self, lease_id: str, owner_ref: str, fencing_token: int, ttl_seconds: int = 30) -> Dict[str, Any]:
        """Renew an active lease verifying fencing token."""
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        expires_iso = datetime.fromtimestamp(now_dt.timestamp() + ttl_seconds, timezone.utc).isoformat()

        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            lease = conn.execute("SELECT * FROM leases WHERE lease_id = ?;", (lease_id,)).fetchone()
            if not lease:
                raise LeaseConflictError(f"Lease {lease_id} not found")

            if lease["fencing_token"] != fencing_token:
                raise StaleFencingTokenError(f"Stale fencing token {fencing_token}: current token is {lease['fencing_token']}")

            if lease["owner_ref"] != owner_ref:
                raise LeaseConflictError(f"Lease {lease_id} owner mismatch: expected {owner_ref}, got {lease['owner_ref']}")

            if lease["status"] != "ACTIVE":
                raise LeaseConflictError(f"Lease {lease_id} is in status {lease['status']}")

            conn.execute(
                "UPDATE leases SET renewed_at = ?, expires_at = ? WHERE lease_id = ?;",
                (now_iso, expires_iso, lease_id),
            )
            conn.execute("COMMIT;")

            res = dict(lease)
            res["renewed_at"] = now_iso
            res["expires_at"] = expires_iso
            return res
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def release_lease(self, lease_id: str, owner_ref: str, fencing_token: int) -> Dict[str, Any]:
        """Release an active lease verifying fencing token."""
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            lease = conn.execute("SELECT * FROM leases WHERE lease_id = ?;", (lease_id,)).fetchone()
            if not lease:
                raise LeaseConflictError(f"Lease {lease_id} not found")

            if lease["fencing_token"] != fencing_token:
                raise StaleFencingTokenError(f"Stale fencing token {fencing_token}: current token is {lease['fencing_token']}")

            if lease["owner_ref"] != owner_ref:
                raise LeaseConflictError(f"Lease {lease_id} owner mismatch")

            conn.execute("UPDATE leases SET status = 'RELEASED' WHERE lease_id = ?;", (lease_id,))
            conn.execute("COMMIT;")

            res = dict(lease)
            res["status"] = "RELEASED"
            return res
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def recover_stale_leases(self) -> List[str]:
        """Transition active leases whose expires_at is past now_utc to EXPIRED."""
        now_iso = self._get_now_iso()
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            stale_rows = conn.execute(
                "SELECT lease_id FROM leases WHERE status = 'ACTIVE' AND expires_at < ?;", (now_iso,)
            ).fetchall()
            stale_ids = [r["lease_id"] for r in stale_rows]
            if stale_ids:
                conn.execute(
                    f"UPDATE leases SET status = 'EXPIRED' WHERE lease_id IN ({','.join('?' for _ in stale_ids)});",
                    stale_ids,
                )
            conn.execute("COMMIT;")
            return stale_ids
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def claim_work_item(
        self,
        *,
        lease_key: str,
        work_item_id: str,
        owner_ref: str,
        ttl_seconds: int = 30,
    ) -> Dict[str, Any]:
        """Atomically claim a work item and acquire/renew its lease in one transaction."""
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        expires_iso = datetime.fromtimestamp(now_dt.timestamp() + ttl_seconds, timezone.utc).isoformat()

        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            item = conn.execute("SELECT * FROM work_items WHERE work_item_id = ?;", (work_item_id,)).fetchone()
            if not item:
                raise WorkItemNotFoundError(f"Work item {work_item_id} not found")

            # Verify no duplicate active assignment for another claim
            active_asgn = conn.execute(
                "SELECT * FROM assignments WHERE work_item_id = ? AND status = 'ACTIVE';", (work_item_id,)
            ).fetchone()
            if active_asgn and active_asgn["assignee_ref"] != owner_ref:
                existing_lease = conn.execute(
                    "SELECT * FROM leases WHERE work_item_id = ? AND status = 'ACTIVE';", (work_item_id,)
                ).fetchone()
                if existing_lease and existing_lease["expires_at"] > now_iso:
                    raise LeaseConflictError(f"Work item {work_item_id} actively assigned to {active_asgn['assignee_ref']}")

            existing = conn.execute("SELECT * FROM leases WHERE lease_key = ?;", (lease_key,)).fetchone()
            if existing:
                if existing["status"] == "ACTIVE" and existing["expires_at"] > now_iso and existing["owner_ref"] != owner_ref:
                    raise LeaseConflictError(f"Lease {lease_key} is held by {existing['owner_ref']}")
                next_fencing_token = existing["fencing_token"] + 1
                lease_id = existing["lease_id"]
                conn.execute(
                    """
                    UPDATE leases
                    SET owner_ref = ?, fencing_token = ?, acquired_at = ?, renewed_at = ?, expires_at = ?, status = 'ACTIVE', work_item_id = ?
                    WHERE lease_key = ?;
                    """,
                    (owner_ref, next_fencing_token, now_iso, now_iso, expires_iso, work_item_id, lease_key),
                )
            else:
                next_fencing_token = 1
                lease_id = f"lease_{compute_sha256(lease_key + owner_ref + now_iso)[:16]}"
                conn.execute(
                    """
                    INSERT INTO leases (
                        lease_id, lease_key, work_item_id, owner_ref, fencing_token,
                        acquired_at, renewed_at, expires_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE');
                    """,
                    (lease_id, lease_key, work_item_id, owner_ref, next_fencing_token, now_iso, now_iso, expires_iso),
                )

            # Record assignment
            assignment_id = f"asgn_{compute_sha256(work_item_id + owner_ref + str(next_fencing_token))[:16]}"
            conn.execute(
                """
                INSERT INTO assignments (assignment_id, work_item_id, assignee_ref, assigned_at, status)
                VALUES (?, ?, ?, ?, 'ACTIVE');
                """,
                (assignment_id, work_item_id, owner_ref, now_iso),
            )

            conn.execute("COMMIT;")
            return {
                "lease_id": lease_id,
                "lease_key": lease_key,
                "work_item_id": work_item_id,
                "owner_ref": owner_ref,
                "fencing_token": next_fencing_token,
                "assignment_id": assignment_id,
                "acquired_at": now_iso,
                "expires_at": expires_iso,
                "status": "ACTIVE",
            }
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def upsert_heartbeat(self, worker_id: str, lease_id: Optional[str] = None) -> Dict[str, Any]:
        """Record or update worker heartbeat."""
        now_iso = utc_now_iso()
        hb_id = f"hb_{compute_sha256(worker_id)[:16]}"
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute(
                """
                INSERT INTO heartbeats (heartbeat_id, worker_id, lease_id, last_seen_at, status)
                VALUES (?, ?, ?, ?, 'ALIVE')
                ON CONFLICT(worker_id) DO UPDATE SET
                    lease_id = excluded.lease_id,
                    last_seen_at = excluded.last_seen_at,
                    status = 'ALIVE';
                """,
                (hb_id, worker_id, lease_id, now_iso),
            )
            conn.execute("COMMIT;")
            return {"heartbeat_id": hb_id, "worker_id": worker_id, "lease_id": lease_id, "last_seen_at": now_iso, "status": "ALIVE"}
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def query_fresh_heartbeats(self, ttl_seconds: int = 60) -> List[Dict[str, Any]]:
        """Fetch all worker heartbeats updated within ttl_seconds."""
        now_dt = datetime.now(timezone.utc)
        cutoff_iso = datetime.fromtimestamp(now_dt.timestamp() - ttl_seconds, timezone.utc).isoformat()
        conn = self.get_connection()
        try:
            rows = conn.execute("SELECT * FROM heartbeats WHERE last_seen_at >= ? AND status = 'ALIVE';", (cutoff_iso,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def dispose_stale_heartbeats(self, ttl_seconds: int = 60) -> List[str]:
        """Mark heartbeats past ttl_seconds as DEAD."""
        now_dt = datetime.now(timezone.utc)
        cutoff_iso = datetime.fromtimestamp(now_dt.timestamp() - ttl_seconds, timezone.utc).isoformat()
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            stale_rows = conn.execute(
                "SELECT worker_id FROM heartbeats WHERE last_seen_at < ? AND status = 'ALIVE';", (cutoff_iso,)
            ).fetchall()
            stale_ids = [r["worker_id"] for r in stale_rows]
            if stale_ids:
                conn.execute(
                    f"UPDATE heartbeats SET status = 'DEAD' WHERE worker_id IN ({','.join('?' for _ in stale_ids)});",
                    stale_ids,
                )
            conn.execute("COMMIT;")
            return stale_ids
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    # --- Compare-And-Set State Machine with Cryptographic Event Payload Envelope ---

    def transition_state(
        self,
        *,
        work_item_id: str,
        expected_from_state: str,
        to_state: str,
        expected_state_version: int,
        actor_class: str,
        actor_ref: str,
        reason_code: str,
        explanation: str,
        lease_key: str,
        fencing_token: int,
        input_artifact_ids: List[str],
        output_artifact_ids: List[str],
        correlation_id: str,
        policy_version: str = "contentops.policy.v1",
        model_version: str = "NOT_APPLICABLE",
    ) -> Dict[str, Any]:
        """Perform Compare-And-Set state transition enforcing fencing tokens and canonical event payload envelope hashing."""
        if expected_from_state not in CANONICAL_STATES:
            raise InvalidStateTransitionError(f"Unknown from_state: {expected_from_state}")
        if to_state not in CANONICAL_STATES:
            raise InvalidStateTransitionError(f"Unknown to_state: {to_state}")

        allowed_targets = STATE_TRANSITION_GRAPH.get(expected_from_state, set())
        if to_state not in allowed_targets:
            raise InvalidStateTransitionError(
                f"Illegal state transition from {expected_from_state} to {to_state}. Allowed: {sorted(allowed_targets)}"
            )

        if to_state in WAVE02_PROTECTED_STATES:
            raise Wave02AuthorityViolationError(
                f"Wave 02 fail-closed guard: transition to protected authority state '{to_state}' is forbidden without registered approval envelope validator"
            )

        if not actor_class or not actor_ref or not reason_code or not explanation or not correlation_id or not lease_key:
            raise TransitionValidationError("Missing required transition parameter")

        now_iso = utc_now_iso()

        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")

            item = conn.execute("SELECT * FROM work_items WHERE work_item_id = ?;", (work_item_id,)).fetchone()
            if not item:
                raise WorkItemNotFoundError(f"Work item {work_item_id} not found")

            if item["current_state"] != expected_from_state or item["state_version"] != expected_state_version:
                raise CASStateConflictError(
                    f"CAS state conflict for {work_item_id}: expected ({expected_from_state}, v{expected_state_version}), "
                    f"actual ({item['current_state']}, v{item['state_version']})"
                )

            lease = conn.execute("SELECT * FROM leases WHERE lease_key = ?;", (lease_key,)).fetchone()
            if not lease:
                raise StaleFencingTokenError(f"Lease {lease_key} does not exist")

            if lease["status"] != "ACTIVE":
                raise StaleFencingTokenError(f"Lease {lease_key} is in status {lease['status']}, expected ACTIVE")

            if lease["expires_at"] <= now_iso:
                raise StaleFencingTokenError(f"Lease {lease_key} has expired at {lease['expires_at']}")

            if lease["fencing_token"] != fencing_token:
                raise StaleFencingTokenError(
                    f"Stale fencing token for {work_item_id}: provided token {fencing_token}, active token is {lease['fencing_token']}"
                )

            if lease["owner_ref"] != actor_ref:
                raise StaleFencingTokenError(f"Lease owner mismatch: expected {actor_ref}, got {lease['owner_ref']}")

            if lease["work_item_id"] and lease["work_item_id"] != work_item_id:
                raise StaleFencingTokenError(f"Lease work_item_id mismatch: expected {work_item_id}, got {lease['work_item_id']}")

            # Fetch and snapshot registered artifacts
            all_artifact_ids = input_artifact_ids + output_artifact_ids
            artifact_snapshots = []
            for art_id in all_artifact_ids:
                art_row = conn.execute("SELECT * FROM artifact_references WHERE artifact_id = ?;", (art_id,)).fetchone()
                if not art_row:
                    raise ArtifactNotFoundError(f"Referenced artifact {art_id} is not registered")
                artifact_snapshots.append({
                    "artifact_id": art_row["artifact_id"],
                    "artifact_type": art_row["artifact_type"],
                    "storage_class": art_row["storage_class"],
                    "byte_length": art_row["byte_length"],
                    "sha256_hash": art_row["sha256_hash"],
                    "schema_version": art_row["schema_version"],
                    "producer_ref": art_row["producer_ref"],
                })

            seq_row = conn.execute(
                "SELECT MAX(event_seq) AS max_seq FROM transition_events WHERE work_item_id = ?;", (work_item_id,)
            ).fetchone()
            event_seq = (seq_row["max_seq"] or 0) + 1
            new_state_version = expected_state_version + 1

            if event_seq == 1:
                previous_event_hash = GENESIS_PREVIOUS_HASH
            else:
                prev_row = conn.execute(
                    "SELECT event_hash FROM transition_events WHERE work_item_id = ? AND event_seq = ?;",
                    (work_item_id, event_seq - 1),
                ).fetchone()
                if not prev_row:
                    raise DurableStateCorruptionError(f"Missing preceding event seq {event_seq - 1} for work item {work_item_id}")
                previous_event_hash = prev_row["event_hash"]

            explanation_hash = compute_sha256(explanation)

            # Build canonical event payload JSON
            event_payload_dict = {
                "event_schema_version": "contentops.event_payload.v1",
                "event_seq": event_seq,
                "work_item_id": work_item_id,
                "story_id": item["story_id"],
                "state_version": new_state_version,
                "from_state": expected_from_state,
                "to_state": to_state,
                "previous_event_hash": previous_event_hash,
                "actor_class": actor_class,
                "actor_ref": actor_ref,
                "reason_code": reason_code,
                "explanation_hash": explanation_hash,
                "correlation_id": correlation_id,
                "policy_version": policy_version,
                "model_version": model_version,
                "authority_type": "NONE",
                "authority_ref": None,
                "authority_effect": "NO_AUTHORITY_GRANTED",
                "lease_id": lease["lease_id"],
                "lease_key": lease_key,
                "fencing_token": fencing_token,
                "input_artifact_ids": sorted(input_artifact_ids),
                "output_artifact_ids": sorted(output_artifact_ids),
                "artifact_snapshots": artifact_snapshots,
                "timestamp_utc": now_iso,
            }
            event_payload_json = json.dumps(event_payload_dict, sort_keys=True)
            event_hash = compute_sha256(event_payload_json)
            event_id = f"evt_{compute_sha256(event_hash)[:16]}"
            transition_key = f"tr_{work_item_id}_v{new_state_version}_{compute_sha256(event_payload_json)[:8]}"

            conn.execute(
                """
                INSERT INTO transition_events (
                    event_id, transition_key, work_item_id, event_seq, from_state, to_state, state_version,
                    actor_class, actor_ref, reason_code, explanation, explanation_hash, correlation_id,
                    policy_version, model_version, authority_type, authority_ref, authority_effect,
                    lease_id, lease_key, fencing_token, input_artifact_ids, output_artifact_ids,
                    artifact_snapshot_json, previous_event_hash, event_payload_json, event_hash, timestamp_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NONE', NULL, 'NO_AUTHORITY_GRANTED',
                          ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event_id,
                    transition_key,
                    work_item_id,
                    event_seq,
                    expected_from_state,
                    to_state,
                    new_state_version,
                    actor_class,
                    actor_ref,
                    reason_code,
                    explanation,
                    explanation_hash,
                    correlation_id,
                    policy_version,
                    model_version,
                    lease["lease_id"],
                    lease_key,
                    fencing_token,
                    json.dumps(input_artifact_ids),
                    json.dumps(output_artifact_ids),
                    json.dumps(artifact_snapshots),
                    previous_event_hash,
                    event_payload_json,
                    event_hash,
                    now_iso,
                ),
            )

            conn.execute(
                "UPDATE work_items SET current_state = ?, state_version = ?, updated_at = ? WHERE work_item_id = ?;",
                (to_state, new_state_version, now_iso, work_item_id),
            )

            conn.execute("COMMIT;")
            return {
                "work_item_id": work_item_id,
                "previous_state": expected_from_state,
                "current_state": to_state,
                "state_version": new_state_version,
                "event_id": event_id,
                "event_seq": event_seq,
                "event_hash": event_hash,
                "previous_event_hash": previous_event_hash,
                "updated_at": now_iso,
            }
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    # --- Deterministic Event Replay & Corruption Detection ---

    def replay_work_item_events(self, work_item_id: str) -> Dict[str, Any]:
        """Replay work item events starting from WORK_ITEM_CREATED genesis event, verifying payload envelope hashes and projections."""
        conn = self.get_connection()
        try:
            item = conn.execute("SELECT * FROM work_items WHERE work_item_id = ?;", (work_item_id,)).fetchone()
            if not item:
                raise WorkItemNotFoundError(f"Work item {work_item_id} not found")

            events = conn.execute(
                "SELECT * FROM transition_events WHERE work_item_id = ? ORDER BY event_seq ASC;", (work_item_id,)
            ).fetchall()

            if not events:
                raise DurableStateCorruptionError(f"Work item {work_item_id} has no transition events")

            genesis_evt = events[0]
            if genesis_evt["event_seq"] != 1 or genesis_evt["reason_code"] != "WORK_ITEM_INITIALIZATION":
                raise DurableStateCorruptionError(f"Work item {work_item_id} missing valid genesis event")

            current_state = "DISCOVERED"
            expected_seq = 1
            previous_hash = GENESIS_PREVIOUS_HASH

            for evt in events:
                if evt["event_seq"] != expected_seq:
                    raise DurableStateCorruptionError(
                        f"Event sequence gap in {work_item_id}: expected seq {expected_seq}, got {evt['event_seq']}"
                    )

                if evt["event_seq"] > 1 and evt["from_state"] != current_state:
                    raise DurableStateCorruptionError(
                        f"State mismatch in replay for {work_item_id} at seq {expected_seq}: expected from_state {current_state}, got {evt['from_state']}"
                    )

                if evt["previous_event_hash"] != previous_hash:
                    raise DurableStateCorruptionError(
                        f"Previous event hash mismatch in {work_item_id} at seq {expected_seq}: "
                        f"expected {previous_hash}, got {evt['previous_event_hash']}"
                    )

                # Reconstruct and verify payload envelope JSON and hash
                payload_dict = json.loads(evt["event_payload_json"])
                reconstructed_json = json.dumps(payload_dict, sort_keys=True)
                computed_hash = compute_sha256(reconstructed_json)
                if computed_hash != evt["event_hash"]:
                    raise DurableStateCorruptionError(
                        f"Event payload hash mismatch in {work_item_id} at seq {expected_seq}: "
                        f"computed {computed_hash}, stored {evt['event_hash']}"
                    )

                # Verify every column equals its corresponding payload JSON field
                col_checks = [
                    ("event_seq", evt["event_seq"]),
                    ("work_item_id", evt["work_item_id"]),
                    ("story_id", item["story_id"]),
                    ("state_version", evt["state_version"]),
                    ("from_state", evt["from_state"]),
                    ("to_state", evt["to_state"]),
                    ("previous_event_hash", evt["previous_event_hash"]),
                    ("actor_class", evt["actor_class"]),
                    ("actor_ref", evt["actor_ref"]),
                    ("reason_code", evt["reason_code"]),
                    ("explanation_hash", evt["explanation_hash"]),
                    ("correlation_id", evt["correlation_id"]),
                    ("policy_version", evt["policy_version"]),
                    ("model_version", evt["model_version"]),
                    ("authority_type", evt["authority_type"]),
                    ("authority_ref", evt["authority_ref"]),
                    ("authority_effect", evt["authority_effect"]),
                    ("lease_id", evt["lease_id"]),
                    ("lease_key", evt["lease_key"]),
                    ("fencing_token", evt["fencing_token"]),
                    ("timestamp_utc", evt["timestamp_utc"]),
                ]
                for field_name, col_val in col_checks:
                    if payload_dict.get(field_name) != col_val:
                        raise DurableStateCorruptionError(
                            f"Event payload column mismatch for field '{field_name}' in {work_item_id} seq {expected_seq}: "
                            f"column={col_val}, payload={payload_dict.get(field_name)}"
                        )

                # Verify snapshot artifact hashes match registered database records
                for snap in payload_dict.get("artifact_snapshots", []):
                    art_row = conn.execute("SELECT * FROM artifact_references WHERE artifact_id = ?;", (snap["artifact_id"],)).fetchone()
                    if not art_row or art_row["sha256_hash"] != snap["sha256_hash"] or art_row["byte_length"] != snap["byte_length"]:
                        raise DurableStateCorruptionError(
                            f"Replay artifact snapshot corruption for {snap['artifact_id']} in work item {work_item_id}"
                        )

                current_state = evt["to_state"]
                previous_hash = evt["event_hash"]
                expected_seq += 1

            expected_final_version = expected_seq - 1
            if item["current_state"] != current_state or item["state_version"] != expected_final_version:
                raise DurableStateCorruptionError(
                    f"Materialized projection mismatch for {work_item_id}: "
                    f"DB has ({item['current_state']}, v{item['state_version']}), replayed ({current_state}, v{expected_final_version})"
                )

            return {
                "work_item_id": work_item_id,
                "replayed_state": current_state,
                "replayed_version": expected_final_version,
                "event_count": len(events),
                "last_event_hash": previous_hash,
                "verification_status": "PASS",
            }
        finally:
            conn.close()

    def reconstruct_in_flight_state(self) -> Dict[str, Any]:
        """Verify state integrity across all work items and clean up expired leases/heartbeats."""
        recovered_leases = self.recover_stale_leases()
        dead_heartbeats = self.dispose_stale_heartbeats()
        conn = self.get_connection()
        try:
            items = conn.execute("SELECT work_item_id FROM work_items;").fetchall()
            verified_count = 0
            for item in items:
                self.replay_work_item_events(item["work_item_id"])
                verified_count += 1

            return {
                "restart_reconstruction_status": "PASS",
                "recovered_leases_count": len(recovered_leases),
                "dead_heartbeats_count": len(dead_heartbeats),
                "verified_work_items_count": verified_count,
            }
        finally:
            conn.close()

    # --- Redacted Evidence Export ---

    def export_redacted_store_evidence(self) -> Dict[str, Any]:
        """Export deterministic redacted store evidence querying live database PRAGMA state."""
        pragmas = self.query_pragmas()
        conn = self.get_connection()
        try:
            migrations = [dict(r) for r in conn.execute("SELECT * FROM schema_migrations ORDER BY version ASC;").fetchall()]
            raw_items = [dict(r) for r in conn.execute("SELECT * FROM work_items ORDER BY work_item_id ASC;").fetchall()]
            raw_events = [dict(r) for r in conn.execute("SELECT * FROM transition_events ORDER BY work_item_id ASC, event_seq ASC;").fetchall()]
            raw_leases = [dict(r) for r in conn.execute("SELECT * FROM leases ORDER BY lease_id ASC;").fetchall()]
            raw_artifacts = [dict(r) for r in conn.execute("SELECT * FROM artifact_references ORDER BY artifact_id ASC;").fetchall()]

            redacted_items = []
            for item in raw_items:
                redacted_items.append({
                    "work_item_id": item["work_item_id"],
                    "story_id": compute_sha256(item["story_id"])[:16],
                    "title": "[REDACTED_TITLE]",
                    "current_state": item["current_state"],
                    "state_version": item["state_version"],
                    "target_surface": item["target_surface"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                })

            redacted_events = []
            for evt in raw_events:
                redacted_events.append({
                    "event_id": evt["event_id"],
                    "work_item_id": evt["work_item_id"],
                    "event_seq": evt["event_seq"],
                    "from_state": evt["from_state"],
                    "to_state": evt["to_state"],
                    "state_version": evt["state_version"],
                    "actor_class": evt["actor_class"],
                    "actor_ref": "[REDACTED_ACTOR_REF]",
                    "reason_code": evt["reason_code"],
                    "explanation": "[REDACTED_EXPLANATION]",
                    "explanation_hash": evt["explanation_hash"],
                    "correlation_id": evt["correlation_id"],
                    "previous_event_hash": evt["previous_event_hash"],
                    "event_hash": evt["event_hash"],
                    "authority_type": evt["authority_type"],
                    "authority_effect": evt["authority_effect"],
                    "timestamp_utc": evt["timestamp_utc"],
                })

            return {
                "schema_version": "contentops.durable_store_export.v1",
                "database_pragmas": pragmas,
                "current_schema_version": self.get_current_schema_version(),
                "redaction_guarantee": "PASS_NO_SECRETS_CREDENTIALS_OR_PRIVATE_MATERIAL",
                "counts": {
                    "migrations": len(migrations),
                    "work_items": len(redacted_items),
                    "transition_events": len(redacted_events),
                    "leases": len(raw_leases),
                    "artifacts": len(raw_artifacts),
                },
                "migrations": migrations,
                "work_items": redacted_items,
                "transition_events": redacted_events,
            }
        finally:
            conn.close()
