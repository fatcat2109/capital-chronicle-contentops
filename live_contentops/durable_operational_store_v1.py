"""
ContentOps Durable Operational Store & Canonical State Machine v1

Module: live_contentops.durable_operational_store_v1
Scope: Single authoritative SQLite WAL operational store, versioned migrations,
       Compare-And-Set (CAS) state machine, append-only transition event log,
       transactional leases with monotonic fencing tokens, restart safety,
       deterministic replay, corruption verification, and redacted evidence export.
"""

import json
import hashlib
import os
import pathlib
import re
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Set


# Exception Hierarchy

class DurableStoreError(Exception):
    """Base exception for all durable operational store errors."""
    pass


class MigrationError(DurableStoreError):
    """Raised when schema migration or verification fails."""
    pass


class InvalidStateTransitionError(DurableStoreError):
    """Raised when an illegal state transition is attempted."""
    pass


class CASStateConflictError(DurableStoreError):
    """Raised when Compare-And-Set state or version check fails."""
    pass


class TransitionValidationError(DurableStoreError):
    """Raised when transition event bindings fail validation."""
    pass


class WorkItemNotFoundError(DurableStoreError):
    """Raised when a requested work item is not found."""
    pass


class StaleFencingTokenError(DurableStoreError):
    """Raised when an operation uses a stale or invalid lease fencing token."""
    pass


class LeaseConflictError(DurableStoreError):
    """Raised when acquiring a lease fails due to an active lease."""
    pass


class DurableStateCorruptionError(DurableStoreError):
    """Raised when state replay or projection mismatch/corruption is detected."""
    pass


# State Machine Definitions

VALID_STATES: Set[str] = {
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
}

TRANSITION_GRAPH: Dict[str, Set[str]] = {
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


# Utility Functions

def utc_now_iso() -> str:
    """Return ISO-8601 formatted UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def compute_sha256(data: str | bytes) -> str:
    """Compute SHA-256 hex string."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def is_valid_sha256(hash_str: str) -> bool:
    """Validate 64-char hex SHA-256 format."""
    return bool(re.match(r"^[a-fA-F0-9]{64}$", hash_str))


# Embedded Schema Migrations

MIGRATIONS: List[Tuple[int, str, str]] = [
    (
        1,
        "Initial Wave 02 Durable Operational Store Schema",
        """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operational_windows (
    window_id TEXT PRIMARY KEY,
    window_key TEXT UNIQUE NOT NULL,
    start_utc TEXT NOT NULL,
    end_utc TEXT NOT NULL,
    status TEXT NOT NULL,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduler_ticks (
    tick_id TEXT PRIMARY KEY,
    tick_key TEXT UNIQUE NOT NULL,
    window_id TEXT NOT NULL REFERENCES operational_windows(window_id),
    tick_utc TEXT NOT NULL,
    status TEXT NOT NULL,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS work_items (
    work_item_id TEXT PRIMARY KEY,
    work_item_key TEXT UNIQUE NOT NULL,
    story_id TEXT NOT NULL,
    title TEXT NOT NULL,
    target_surface TEXT NOT NULL,
    current_state TEXT NOT NULL,
    state_version INTEGER NOT NULL DEFAULT 1,
    lock_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS story_versions (
    story_version_id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    version_num INTEGER NOT NULL,
    candidate_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(story_id, version_num)
);

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    assignee TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    status TEXT NOT NULL,
    unassigned_at TEXT,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS artifact_references (
    artifact_id TEXT PRIMARY KEY,
    artifact_key TEXT UNIQUE NOT NULL,
    artifact_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    byte_length INTEGER NOT NULL,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transition_events (
    event_id TEXT PRIMARY KEY,
    transition_key TEXT UNIQUE NOT NULL,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    state_version INTEGER NOT NULL,
    actor_class TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    explanation TEXT,
    artifact_hash_set TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    authority_granted INTEGER NOT NULL CHECK (authority_granted IN (0, 1))
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

CREATE TABLE IF NOT EXISTS model_invocations (
    invocation_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    provider_model_id TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    response_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_records (
    review_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    reviewer_role TEXT NOT NULL,
    review_disposition TEXT NOT NULL,
    review_hash TEXT NOT NULL,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operator_decisions (
    decision_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    operator_ref TEXT NOT NULL,
    decision TEXT NOT NULL,
    decision_hash TEXT NOT NULL,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leases (
    lease_id TEXT PRIMARY KEY,
    lease_key TEXT UNIQUE NOT NULL,
    work_item_id TEXT REFERENCES work_items(work_item_id),
    owner_ref TEXT NOT NULL,
    fencing_token INTEGER NOT NULL,
    acquired_at TEXT NOT NULL,
    renewed_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'EXPIRED', 'RELEASED'))
);

CREATE TABLE IF NOT EXISTS heartbeats (
    heartbeat_id TEXT PRIMARY KEY,
    worker_id TEXT UNIQUE NOT NULL,
    last_heartbeat_at TEXT NOT NULL,
    status TEXT NOT NULL,
    metadata_json TEXT
);

-- Schema-ready Wave 03+ placeholder tables (no execution logic in Wave 02)

CREATE TABLE IF NOT EXISTS approval_envelopes (
    envelope_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    approver_ref TEXT NOT NULL,
    envelope_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outbox_messages (
    message_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    target_surface TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS platform_dispatches (
    dispatch_id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES outbox_messages(message_id),
    platform_id TEXT NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS readbacks (
    readback_id TEXT PRIMARY KEY,
    dispatch_id TEXT NOT NULL REFERENCES platform_dispatches(dispatch_id),
    status TEXT NOT NULL,
    readback_hash TEXT NOT NULL,
    verified_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reconciliations (
    reconciliation_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    status TEXT NOT NULL,
    reconciliation_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    work_item_id TEXT REFERENCES work_items(work_item_id),
    severity TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics (
    metric_id TEXT PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback_records (
    feedback_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    feedback_kind TEXT NOT NULL,
    feedback_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_reviews (
    review_id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    learning_disposition TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""
    ),
]


# Core Class: ContentOpsDurableStore

class ContentOpsDurableStore:
    """
    Single authoritative SQLite WAL operational store for ContentOps.
    """

    def __init__(self, db_path: str | pathlib.Path, busy_timeout_ms: int = 5000, auto_migrate: bool = True):
        self.db_path = pathlib.Path(db_path).resolve()
        self.busy_timeout_ms = busy_timeout_ms
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        if auto_migrate:
            self.run_migrations()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=self.busy_timeout_ms / 1000.0, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms};")
        conn.row_factory = sqlite3.Row
        return conn

    # Migration Subsystem

    def get_current_schema_version(self) -> int:
        conn = self.get_connection()
        try:
            res = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations';").fetchone()
            if not res:
                return 0
            row = conn.execute("SELECT MAX(version) AS max_v FROM schema_migrations;").fetchone()
            return row["max_v"] if row and row["max_v"] is not None else 0
        finally:
            conn.close()

    def create_backup(self) -> pathlib.Path:
        backup_path = self.db_path.with_suffix(f".sqlite.bak.{int(time.time())}")
        if self.db_path.exists():
            import shutil
            shutil.copy2(self.db_path, backup_path)
        return backup_path

    def run_migrations(self) -> int:
        current_version = self.get_current_schema_version()
        applied_count = 0

        for version, description, sql_script in MIGRATIONS:
            if version <= current_version:
                continue

            checksum = compute_sha256(sql_script)
            backup_file = self.create_backup()

            conn = self.get_connection()
            try:
                conn.executescript(sql_script)
                conn.execute(
                    "INSERT INTO schema_migrations (version, checksum, applied_at, description) VALUES (?, ?, ?, ?);",
                    (version, checksum, utc_now_iso(), description)
                )
                applied_count += 1
            except Exception as exc:
                conn.close()
                if backup_file.exists():
                    import shutil
                    shutil.copy2(backup_file, self.db_path)
                raise MigrationError(f"Failed migration version {version}: {exc}") from exc
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        self.verify_schema_integrity()
        return applied_count

    def verify_schema_integrity(self) -> bool:
        conn = self.get_connection()
        try:
            res = conn.execute("PRAGMA integrity_check;").fetchall()
            messages = [row[0] for row in res]
            if messages != ["ok"]:
                raise MigrationError(f"Database integrity check failed: {messages}")

            rows = conn.execute("SELECT version, checksum FROM schema_migrations ORDER BY version ASC;").fetchall()
            for row in rows:
                v = row["version"]
                expected_ck = row["checksum"]
                for mv, _, msql in MIGRATIONS:
                    if mv == v:
                        actual_ck = compute_sha256(msql)
                        if actual_ck != expected_ck:
                            raise MigrationError(f"Migration version {v} checksum mismatch! Expected {expected_ck}, got {actual_ck}")
            return True
        finally:
            conn.close()

    # Work Item & CAS Transition Subsystem

    def create_work_item(self, story_id: str, title: str, target_surface: str, work_item_key: Optional[str] = None) -> Dict[str, Any]:
        if not work_item_key:
            work_item_key = f"wi_{story_id}_{target_surface}_{compute_sha256(title)[:8]}"
        work_item_id = f"item_{compute_sha256(work_item_key)[:16]}"
        now = utc_now_iso()

        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute(
                """
                INSERT INTO work_items (
                    work_item_id, work_item_key, story_id, title, target_surface,
                    current_state, state_version, lock_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?);
                """,
                (work_item_id, work_item_key, story_id, title, target_surface, "DISCOVERED", now, now)
            )
            conn.execute("COMMIT;")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK;")
            # Row already exists, fetch it
            row = conn.execute("SELECT * FROM work_items WHERE work_item_key = ?;", (work_item_key,)).fetchone()
            return dict(row)
        finally:
            conn.close()

        return self.get_work_item(work_item_id)

    def get_work_item(self, work_item_id: str) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            row = conn.execute("SELECT * FROM work_items WHERE work_item_id = ?;", (work_item_id,)).fetchone()
            if not row:
                raise WorkItemNotFoundError(f"Work item {work_item_id} not found")
            return dict(row)
        finally:
            conn.close()

    def transition_state(
        self,
        work_item_id: str,
        expected_from_state: str,
        to_state: str,
        expected_state_version: int,
        actor_class: str,
        actor_ref: str,
        reason_code: str,
        explanation: str,
        artifact_hash_set: List[str] | str,
        correlation_id: str,
        authority_granted: bool = False,
    ) -> Dict[str, Any]:
        # 1. State machine validation
        if expected_from_state not in VALID_STATES:
            raise InvalidStateTransitionError(f"Invalid from_state: {expected_from_state}")
        if to_state not in VALID_STATES:
            raise InvalidStateTransitionError(f"Invalid to_state: {to_state}")
        if to_state not in TRANSITION_GRAPH.get(expected_from_state, set()):
            raise InvalidStateTransitionError(f"Illegal transition from {expected_from_state} to {to_state}")

        # 2. Binding validations
        if not actor_class or not actor_ref:
            raise TransitionValidationError("actor_class and actor_ref are required")
        if not reason_code:
            raise TransitionValidationError("reason_code is required")
        if not correlation_id:
            raise TransitionValidationError("correlation_id is required")

        # Parse and validate artifact_hash_set
        if isinstance(artifact_hash_set, list):
            hashes = artifact_hash_set
        elif isinstance(artifact_hash_set, str):
            try:
                hashes = json.loads(artifact_hash_set)
                if not isinstance(hashes, list):
                    hashes = [artifact_hash_set]
            except json.JSONDecodeError:
                hashes = [artifact_hash_set]
        else:
            raise TransitionValidationError("artifact_hash_set must be a list or hash string")

        if not hashes:
            raise TransitionValidationError("artifact_hash_set cannot be empty")
        for h in hashes:
            if not is_valid_sha256(h):
                raise TransitionValidationError(f"Malformed artifact SHA-256 hash: {h}")

        canonical_hash_set_json = json.dumps(sorted(hashes))
        now = utc_now_iso()
        transition_key = f"tr_{work_item_id}_v{expected_state_version + 1}_{compute_sha256(now + to_state)[:8]}"
        event_id = f"evt_{compute_sha256(transition_key)[:16]}"

        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")

            # 3. CAS state check
            row = conn.execute("SELECT current_state, state_version FROM work_items WHERE work_item_id = ?;", (work_item_id,)).fetchone()
            if not row:
                raise WorkItemNotFoundError(f"Work item {work_item_id} not found")

            curr_state = row["current_state"]
            curr_version = row["state_version"]

            if curr_state != expected_from_state or curr_version != expected_state_version:
                raise CASStateConflictError(
                    f"CAS conflict on item {work_item_id}: expected ({expected_from_state}, v{expected_state_version}), "
                    f"found ({curr_state}, v{curr_version})"
                )

            next_version = curr_version + 1

            # Update work item projection
            conn.execute(
                """
                UPDATE work_items
                SET current_state = ?, state_version = ?, updated_at = ?
                WHERE work_item_id = ? AND state_version = ?;
                """,
                (to_state, next_version, now, work_item_id, expected_state_version)
            )

            # Insert append-only transition event
            conn.execute(
                """
                INSERT INTO transition_events (
                    event_id, transition_key, work_item_id, from_state, to_state,
                    state_version, actor_class, actor_ref, reason_code, explanation,
                    artifact_hash_set, correlation_id, timestamp_utc, authority_granted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event_id, transition_key, work_item_id, expected_from_state, to_state,
                    next_version, actor_class, actor_ref, reason_code, explanation,
                    canonical_hash_set_json, correlation_id, now, 1 if authority_granted else 0
                )
            )

            conn.execute("COMMIT;")
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()

        return self.get_work_item(work_item_id)

    # Event Replay & Corruption Verification

    def replay_work_item_events(self, work_item_id: str) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            item_row = conn.execute("SELECT * FROM work_items WHERE work_item_id = ?;", (work_item_id,)).fetchone()
            if not item_row:
                raise WorkItemNotFoundError(f"Work item {work_item_id} not found")

            events = conn.execute(
                "SELECT * FROM transition_events WHERE work_item_id = ? ORDER BY state_version ASC;",
                (work_item_id,)
            ).fetchall()

            if not events:
                # Discovered initial state without transitions
                computed_state = item_row["current_state"]
                computed_version = item_row["state_version"]
            else:
                computed_state = "DISCOVERED"
                computed_version = 1
                for ev in events:
                    if ev["from_state"] != computed_state:
                        raise DurableStateCorruptionError(
                            f"Replay corruption on item {work_item_id}: event expected from {computed_state}, got {ev['from_state']}"
                        )
                    if ev["state_version"] != computed_version + 1:
                        raise DurableStateCorruptionError(
                            f"Replay corruption on item {work_item_id}: event version expected {computed_version + 1}, got {ev['state_version']}"
                        )
                    computed_state = ev["to_state"]
                    computed_version = ev["state_version"]

            if computed_state != item_row["current_state"] or computed_version != item_row["state_version"]:
                raise DurableStateCorruptionError(
                    f"Durable state corruption on item {work_item_id}: "
                    f"materialized state ({item_row['current_state']}, v{item_row['state_version']}) "
                    f"does not match replayed state ({computed_state}, v{computed_version})"
                )

            return {
                "work_item_id": work_item_id,
                "replayed_state": computed_state,
                "replayed_version": computed_version,
                "event_count": len(events),
                "verification": "PASS",
            }
        finally:
            conn.close()

    # Lease & Fencing Token Subsystem

    def acquire_lease(
        self,
        lease_key: str,
        owner_ref: str,
        ttl_seconds: int = 30,
        work_item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        expires_iso = datetime.fromtimestamp(now_dt.timestamp() + ttl_seconds, timezone.utc).isoformat()
        lease_id = f"lease_{compute_sha256(lease_key + owner_ref + now_iso)[:16]}"

        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")

            existing = conn.execute("SELECT * FROM leases WHERE lease_key = ?;", (lease_key,)).fetchone()
            if existing:
                if existing["status"] == "ACTIVE" and existing["expires_at"] > now_iso:
                    raise LeaseConflictError(f"Lease {lease_key} is active and held by {existing['owner_ref']}")
                
                next_fencing_token = existing["fencing_token"] + 1
                lease_id = existing["lease_id"]
                conn.execute(
                    """
                    UPDATE leases
                    SET owner_ref = ?, fencing_token = ?, acquired_at = ?, renewed_at = ?, expires_at = ?, status = 'ACTIVE', work_item_id = ?
                    WHERE lease_key = ?;
                    """,
                    (owner_ref, next_fencing_token, now_iso, now_iso, expires_iso, work_item_id, lease_key)
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
                    (lease_id, lease_key, work_item_id, owner_ref, next_fencing_token, now_iso, now_iso, expires_iso)
                )

            conn.execute("COMMIT;")
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()

        return self.get_lease(lease_id)

    def renew_lease(self, lease_id: str, owner_ref: str, fencing_token: int, ttl_seconds: int = 30) -> Dict[str, Any]:
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        expires_iso = datetime.fromtimestamp(now_dt.timestamp() + ttl_seconds, timezone.utc).isoformat()

        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            lease = conn.execute("SELECT * FROM leases WHERE lease_id = ?;", (lease_id,)).fetchone()
            if not lease:
                raise LeaseConflictError(f"Lease {lease_id} not found")

            if lease["status"] != "ACTIVE":
                raise LeaseConflictError(f"Lease {lease_id} is not active ({lease['status']})")
            if lease["owner_ref"] != owner_ref:
                raise LeaseConflictError(f"Lease owner mismatch: {lease['owner_ref']} vs {owner_ref}")
            if lease["fencing_token"] != fencing_token:
                raise StaleFencingTokenError(f"Fencing token mismatch for lease {lease_id}: current {lease['fencing_token']}, got {fencing_token}")

            # Check if lease expired in real time
            if lease["expires_at"] < now_iso:
                conn.execute("UPDATE leases SET status = 'EXPIRED' WHERE lease_id = ?;", (lease_id,))
                conn.execute("COMMIT;")
                raise LeaseConflictError(f"Lease {lease_id} has expired")

            conn.execute(
                "UPDATE leases SET renewed_at = ?, expires_at = ? WHERE lease_id = ?;",
                (now_iso, expires_iso, lease_id)
            )
            conn.execute("COMMIT;")
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()

        return self.get_lease(lease_id)

    def release_lease(self, lease_id: str, owner_ref: str, fencing_token: int) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            lease = conn.execute("SELECT * FROM leases WHERE lease_id = ?;", (lease_id,)).fetchone()
            if not lease:
                raise LeaseConflictError(f"Lease {lease_id} not found")

            if lease["owner_ref"] != owner_ref:
                raise LeaseConflictError(f"Lease owner mismatch: {lease['owner_ref']} vs {owner_ref}")
            if lease["fencing_token"] != fencing_token:
                raise StaleFencingTokenError(f"Fencing token mismatch for lease {lease_id}")

            conn.execute("UPDATE leases SET status = 'RELEASED' WHERE lease_id = ?;", (lease_id,))
            conn.execute("COMMIT;")
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()

        return self.get_lease(lease_id)

    def get_lease(self, lease_id: str) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            row = conn.execute("SELECT * FROM leases WHERE lease_id = ?;", (lease_id,)).fetchone()
            if not row:
                raise LeaseConflictError(f"Lease {lease_id} not found")
            return dict(row)
        finally:
            conn.close()

    def recover_stale_leases(self) -> List[str]:
        now_iso = utc_now_iso()
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            stale_rows = conn.execute(
                "SELECT lease_id FROM leases WHERE status = 'ACTIVE' AND expires_at < ?;",
                (now_iso,)
            ).fetchall()
            stale_ids = [row["lease_id"] for row in stale_rows]

            if stale_ids:
                conn.execute(
                    f"UPDATE leases SET status = 'EXPIRED' WHERE lease_id IN ({','.join(['?']*len(stale_ids))});",
                    stale_ids
                )

            conn.execute("COMMIT;")
            return stale_ids
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()

    # Restart Safety & Reconstruct In-Flight State

    def reconstruct_in_flight_state(self) -> Dict[str, Any]:
        expired_leases = self.recover_stale_leases()
        conn = self.get_connection()
        try:
            work_items = conn.execute("SELECT work_item_id FROM work_items;").fetchall()
            verifications = []
            for wi in work_items:
                res = self.replay_work_item_events(wi["work_item_id"])
                verifications.append(res)

            return {
                "recovered_leases_count": len(expired_leases),
                "recovered_lease_ids": expired_leases,
                "verified_work_items_count": len(verifications),
                "verifications": verifications,
                "restart_reconstruction_status": "PASS",
            }
        finally:
            conn.close()

    # Redacted Evidence Export

    def export_redacted_store_evidence(self) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            migrations = [dict(r) for r in conn.execute("SELECT * FROM schema_migrations ORDER BY version ASC;").fetchall()]
            windows_count = conn.execute("SELECT COUNT(*) AS c FROM operational_windows;").fetchone()["c"]
            ticks_count = conn.execute("SELECT COUNT(*) AS c FROM scheduler_ticks;").fetchone()["c"]
            work_items_rows = [dict(r) for r in conn.execute("SELECT work_item_id, story_id, target_surface, current_state, state_version, lock_version, created_at, updated_at FROM work_items;").fetchall()]
            events_rows = [dict(r) for r in conn.execute("SELECT event_id, transition_key, work_item_id, from_state, to_state, state_version, actor_class, reason_code, artifact_hash_set, correlation_id, timestamp_utc, authority_granted FROM transition_events ORDER BY timestamp_utc ASC;").fetchall()]
            leases_rows = [dict(r) for r in conn.execute("SELECT lease_id, lease_key, work_item_id, fencing_token, acquired_at, renewed_at, expires_at, status FROM leases;").fetchall()]

            # Perform deterministic replay check on all work items
            replay_results = [self.replay_work_item_events(wi["work_item_id"]) for wi in work_items_rows]

            return {
                "schema_version": "contentops.durable_store_export.v1",
                "database_path": str(self.db_path.name),
                "wal_mode_enabled": True,
                "foreign_keys_enabled": True,
                "schema_migrations": migrations,
                "counts": {
                    "operational_windows": windows_count,
                    "scheduler_ticks": ticks_count,
                    "work_items": len(work_items_rows),
                    "transition_events": len(events_rows),
                    "leases": len(leases_rows),
                },
                "work_items": work_items_rows,
                "transition_events": events_rows,
                "leases": leases_rows,
                "replay_verifications": replay_results,
                "redaction_guarantee": "PASS_NO_SECRETS_CREDENTIALS_OR_PRIVATE_MATERIAL",
            }
        finally:
            conn.close()
