"""Historical Wave 02 lineage compatibility and canonical schema-v4 migration.

This module deliberately keeps historical migration checksums as immutable evidence.
It recognizes an existing database by the exact recorded checksum set and canonical
schema fingerprint before converting the database into the current schema-v4 surface.
Unknown or ambiguous lineage fails closed.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from live_contentops.historical_schema_lineage_v1 import (
    CANONICAL_PRE_V4_LINEAGE_ID,
    HISTORICAL_CHECKSUM_LINEAGE_INDEX,
    HISTORICAL_SCHEMA_LINEAGES,
    ORIGINAL_NO_GENESIS_LINEAGE_ID,
)

CANONICAL_SCHEMA_VERSION = 8
#: Migration versions 1-4 are frozen historical evidence; their SQL bytes and checksums must
#: never change. Schema evolution beyond v4 appends NEW migrations only (migration v5 below).
GENESIS_PREVIOUS_HASH = "GENESIS_" + ("0" * 64)
LEGACY_QUARANTINE_SCOPE = "LEGACY_UNSCOPED_QUARANTINED"
CURRENT_MIGRATION_SQL: Mapping[int, str] = {
    1: "\nCREATE TABLE IF NOT EXISTS schema_migrations (\n version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL, description TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS operational_windows (window_id TEXT PRIMARY KEY, window_key TEXT NOT NULL UNIQUE, started_at TEXT NOT NULL, closed_at TEXT, status TEXT NOT NULL CHECK(status IN ('ACTIVE','CLOSED','HALTED')));\nCREATE TABLE IF NOT EXISTS scheduler_ticks (tick_id TEXT PRIMARY KEY, window_id TEXT NOT NULL, tick_number INTEGER NOT NULL, evaluated_at TEXT NOT NULL, work_items_evaluated INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(window_id) REFERENCES operational_windows(window_id));\nCREATE TABLE IF NOT EXISTS work_items (work_item_id TEXT PRIMARY KEY, story_id TEXT NOT NULL, title TEXT NOT NULL, current_state TEXT NOT NULL, state_version INTEGER NOT NULL DEFAULT 1, target_surface TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS story_versions (story_version_id TEXT PRIMARY KEY, story_id TEXT NOT NULL, version_num INTEGER NOT NULL, headline TEXT NOT NULL, body_text TEXT NOT NULL, created_at TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS assignments (assignment_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, assignee_ref TEXT NOT NULL, assigned_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ACTIVE','RELEASED','COMPLETED')), FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS artifact_references (artifact_id TEXT PRIMARY KEY, artifact_type TEXT NOT NULL, story_id TEXT, work_item_id TEXT, storage_class TEXT NOT NULL, byte_length INTEGER NOT NULL, sha256_hash TEXT NOT NULL, schema_version TEXT NOT NULL, created_at TEXT NOT NULL, producer_ref TEXT NOT NULL, sensitivity_class TEXT NOT NULL DEFAULT 'PUBLIC', FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS transition_events (event_id TEXT PRIMARY KEY, transition_key TEXT NOT NULL UNIQUE, work_item_id TEXT NOT NULL, from_state TEXT NOT NULL, to_state TEXT NOT NULL, state_version INTEGER NOT NULL, actor_class TEXT NOT NULL, actor_ref TEXT NOT NULL, reason_code TEXT NOT NULL, explanation TEXT NOT NULL, artifact_hash_set TEXT NOT NULL, correlation_id TEXT NOT NULL, timestamp_utc TEXT NOT NULL, authority_granted INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS model_invocations (invocation_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, model_id TEXT NOT NULL, prompt_tokens INTEGER NOT NULL DEFAULT 0, completion_tokens INTEGER NOT NULL DEFAULT 0, invoked_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS review_records (review_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, reviewer_ref TEXT NOT NULL, decision TEXT NOT NULL, notes TEXT NOT NULL, reviewed_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS operator_decisions (decision_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, operator_ref TEXT NOT NULL, action TEXT NOT NULL, notes TEXT NOT NULL, decided_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS leases (lease_id TEXT PRIMARY KEY, lease_key TEXT NOT NULL UNIQUE, work_item_id TEXT, owner_ref TEXT NOT NULL, fencing_token INTEGER NOT NULL, acquired_at TEXT NOT NULL, renewed_at TEXT NOT NULL, expires_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ACTIVE','EXPIRED','RELEASED')), FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS heartbeats (heartbeat_id TEXT PRIMARY KEY, worker_id TEXT NOT NULL UNIQUE, lease_id TEXT, last_seen_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ALIVE','DEAD')), FOREIGN KEY(lease_id) REFERENCES leases(lease_id));\nCREATE TABLE IF NOT EXISTS approval_envelopes (envelope_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, approved_by TEXT NOT NULL, expires_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'HELD', FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS outbox_messages (message_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, destination TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', created_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS platform_dispatches (dispatch_id TEXT PRIMARY KEY, message_id TEXT NOT NULL, platform TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', dispatched_at TEXT NOT NULL, FOREIGN KEY(message_id) REFERENCES outbox_messages(message_id));\nCREATE TABLE IF NOT EXISTS readbacks (readback_id TEXT PRIMARY KEY, dispatch_id TEXT NOT NULL, readback_data TEXT NOT NULL, read_at TEXT NOT NULL, FOREIGN KEY(dispatch_id) REFERENCES platform_dispatches(dispatch_id));\nCREATE TABLE IF NOT EXISTS reconciliations (reconciliation_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', reconciled_at TEXT NOT NULL, FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id));\nCREATE TABLE IF NOT EXISTS incidents (incident_id TEXT PRIMARY KEY, work_item_id TEXT, severity TEXT NOT NULL, description TEXT NOT NULL, created_at TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS metrics (metric_id TEXT PRIMARY KEY, metric_name TEXT NOT NULL, metric_value REAL NOT NULL, recorded_at TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS feedback_records (feedback_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL, source TEXT NOT NULL, rating REAL, recorded_at TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS learning_reviews (review_id TEXT PRIMARY KEY, summary TEXT NOT NULL, created_at TEXT NOT NULL);\nCREATE TRIGGER IF NOT EXISTS trg_transition_events_no_update BEFORE UPDATE ON transition_events BEGIN SELECT RAISE(ABORT,'transition_events are append-only: UPDATE forbidden'); END;\nCREATE TRIGGER IF NOT EXISTS trg_transition_events_no_delete BEFORE DELETE ON transition_events BEGIN SELECT RAISE(ABORT,'transition_events are append-only: DELETE forbidden'); END;\n",
    2: "\nALTER TABLE transition_events ADD COLUMN event_seq INTEGER;\nALTER TABLE transition_events ADD COLUMN previous_event_hash TEXT;\nALTER TABLE transition_events ADD COLUMN event_hash TEXT;\nALTER TABLE transition_events ADD COLUMN policy_version TEXT NOT NULL DEFAULT 'contentops.policy.v1';\nALTER TABLE transition_events ADD COLUMN model_version TEXT NOT NULL DEFAULT 'NOT_APPLICABLE';\nALTER TABLE transition_events ADD COLUMN authority_type TEXT NOT NULL DEFAULT 'NONE';\nALTER TABLE transition_events ADD COLUMN authority_ref TEXT;\nALTER TABLE transition_events ADD COLUMN authority_effect TEXT NOT NULL DEFAULT 'NO_AUTHORITY_GRANTED';\nALTER TABLE transition_events ADD COLUMN input_artifact_ids TEXT NOT NULL DEFAULT '[]';\nALTER TABLE transition_events ADD COLUMN output_artifact_ids TEXT NOT NULL DEFAULT '[]';\n",
    3: "\nCREATE TABLE transition_events_v3 (\n event_id TEXT PRIMARY KEY, transition_key TEXT NOT NULL UNIQUE, work_item_id TEXT NOT NULL,\n event_kind TEXT NOT NULL, event_seq INTEGER NOT NULL, from_state TEXT NOT NULL, to_state TEXT NOT NULL,\n state_version INTEGER NOT NULL, actor_class TEXT NOT NULL, actor_ref TEXT NOT NULL,\n reason_code TEXT NOT NULL, explanation TEXT NOT NULL, explanation_hash TEXT NOT NULL,\n correlation_id TEXT NOT NULL, policy_version TEXT NOT NULL, model_version TEXT NOT NULL,\n authority_type TEXT NOT NULL, authority_ref TEXT, authority_effect TEXT NOT NULL,\n lease_id TEXT, lease_key TEXT, fencing_token INTEGER NOT NULL, input_artifact_ids TEXT NOT NULL,\n output_artifact_ids TEXT NOT NULL, artifact_snapshot_json TEXT NOT NULL, previous_event_hash TEXT NOT NULL,\n event_payload_json TEXT NOT NULL, event_hash TEXT NOT NULL, timestamp_utc TEXT NOT NULL,\n FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)\n);\nALTER TABLE artifact_references ADD COLUMN artifact_scope TEXT NOT NULL DEFAULT 'STORY_EXACT';\nALTER TABLE artifact_references ADD COLUMN receipt_id TEXT;\nALTER TABLE artifact_references ADD COLUMN receipt_schema TEXT;\nALTER TABLE artifact_references ADD COLUMN receipt_source_identity TEXT;\nALTER TABLE artifact_references ADD COLUMN receipt_object_identity TEXT;\nALTER TABLE artifact_references ADD COLUMN receipt_verifier_identity TEXT;\nALTER TABLE artifact_references ADD COLUMN canonical_receipt_hash TEXT;\n",
    4: 'CREATE TABLE IF NOT EXISTS schema_lineage_metadata (\n    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),\n    source_lineage_id TEXT NOT NULL,\n    source_schema_fingerprint TEXT NOT NULL,\n    compatibility_version INTEGER NOT NULL,\n    dependency_manifest_json TEXT NOT NULL,\n    dependency_manifest_hash TEXT NOT NULL,\n    upgraded_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS legacy_projection_baselines (\n    work_item_id TEXT PRIMARY KEY,\n    lineage_id TEXT NOT NULL,\n    baseline_event_json TEXT NOT NULL,\n    baseline_event_hash TEXT NOT NULL,\n    original_projection_hash TEXT NOT NULL,\n    created_at TEXT NOT NULL,\n    FOREIGN KEY(work_item_id) REFERENCES work_items(work_item_id)\n);\n\nCREATE TABLE IF NOT EXISTS legacy_artifact_evidence (\n    artifact_id TEXT PRIMARY KEY,\n    source_lineage_id TEXT NOT NULL,\n    legacy_artifact_key TEXT,\n    legacy_storage_path TEXT,\n    legacy_sha256_hash TEXT NOT NULL,\n    legacy_byte_length INTEGER NOT NULL,\n    source_record_json TEXT NOT NULL,\n    source_record_hash TEXT NOT NULL,\n    migrated_scope TEXT NOT NULL,\n    FOREIGN KEY(artifact_id) REFERENCES artifact_references(artifact_id)\n);\n\nCREATE TABLE IF NOT EXISTS migration_failure_receipts (\n    receipt_id TEXT PRIMARY KEY,\n    source_lineage_id TEXT,\n    source_database_hash TEXT NOT NULL,\n    failed_version INTEGER NOT NULL,\n    error_class TEXT NOT NULL,\n    error_message_hash TEXT NOT NULL,\n    backup_path_hash TEXT NOT NULL,\n    restore_integrity_status TEXT NOT NULL,\n    recorded_at TEXT NOT NULL\n);\n\nCREATE INDEX IF NOT EXISTS idx_artifact_scope_identity\nON artifact_references(artifact_scope, story_id, work_item_id);\n',
}
CURRENT_MIGRATION_CHECKSUMS = {version: hashlib.sha256(sql.encode("utf-8")).hexdigest() for version, sql in CURRENT_MIGRATION_SQL.items()}

#: Declared canonical-JSON contract recorded in the dependency manifest.
#: This literal is hashed into ``schema_lineage_metadata`` for every migrated database,
#: so it MUST NOT change without a deliberate compatibility-version bump.
CANONICAL_JSON_CONTRACT = "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)"


def canonical_json(value: Any) -> str:
    """Return the single authoritative canonical JSON encoding for hashed evidence.

    This is the only canonical encoder in the Wave 02 durable-state surface. Every
    hash-chained artifact (event payloads, artifact snapshots, schema fingerprints,
    replay verification, and failure receipts) must serialize through this function
    so that written bytes and re-verified bytes are identical by construction.

    The keyword arguments are stated explicitly rather than left to interpreter
    defaults because they are load-bearing integrity guarantees, and they must stay
    exactly equivalent to :data:`CANONICAL_JSON_CONTRACT`:

    * ``sort_keys=True``   - key order cannot perturb the hash.
    * ``separators``       - no incidental whitespace.
    * ``ensure_ascii=True``- non-ASCII text is escaped to a pure-ASCII form, so the
      encoding never depends on ambient locale or console/filesystem codecs.
    * ``allow_nan=False``  - ``NaN``/``Infinity`` are rejected instead of emitting
      non-standard JSON tokens into an append-only, hash-chained ledger.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


DEPENDENCY_MANIFEST: Mapping[str, Any] = {
    "schema_version": "contentops.schema_v4_dependency_manifest.v1",
    "canonical_json": CANONICAL_JSON_CONTRACT,
    "genesis_previous_hash": GENESIS_PREVIOUS_HASH,
    "legacy_baseline_kind": "LEGACY_PROJECTION_BASELINE",
    "legacy_quarantine_scope": LEGACY_QUARANTINE_SCOPE,
    "historical_lineage_registry": {
        lineage_id: {
            "schema_fingerprint": lineage["schema_fingerprint"],
            "migration_checksums": dict(lineage["migration_checksums"]),
            "valid_genesis_present": lineage["valid_genesis_present"],
        }
        for lineage_id, lineage in HISTORICAL_SCHEMA_LINEAGES.items()
    },
    "migration_sql_checksums": CURRENT_MIGRATION_CHECKSUMS,
    "state_rules": "live_contentops.durable_operational_store_v1.TRANSITION_GRAPH",
    "authority_rule": "WAVE02_FORBIDDEN_AUTHORITY_STATES",
    "event_hash_rule": "sha256(canonical event_payload_json)",
}
DEPENDENCY_MANIFEST_JSON = canonical_json(DEPENDENCY_MANIFEST)
DEPENDENCY_MANIFEST_HASH = hashlib.sha256(DEPENDENCY_MANIFEST_JSON.encode("utf-8")).hexdigest()

DEPENDENCY_MANIFEST_V2: Mapping[str, Any] = {
    "schema_version": "contentops.schema_v4_dependency_manifest.v2",
    "canonical_json": CANONICAL_JSON_CONTRACT,
    "genesis_previous_hash": GENESIS_PREVIOUS_HASH,
    "legacy_baseline_kind": "LEGACY_PROJECTION_BASELINE",
    "legacy_quarantine_scope": LEGACY_QUARANTINE_SCOPE,
    "historical_lineage_registry": {
        lineage_id: {
            "schema_fingerprint": lineage["schema_fingerprint"],
            "migration_checksums": dict(lineage["migration_checksums"]),
            "valid_genesis_present": lineage["valid_genesis_present"],
        }
        for lineage_id, lineage in HISTORICAL_SCHEMA_LINEAGES.items()
    },
    "migration_sql_checksums": CURRENT_MIGRATION_CHECKSUMS,
    "migration_sql_hashes": {v: hashlib.sha256(sql.encode("utf-8")).hexdigest() for v, sql in CURRENT_MIGRATION_SQL.items()},
    "migration_transform_versions": {
        1: "sql_only.v1",
        2: "legacy_sequence.v2",
        3: "legacy_envelope.v3",
        4: "historical_lineage_compatibility.v4",
    },
    "migration_sql_source": "live_contentops.historical_schema_compatibility_v1.CURRENT_MIGRATION_SQL",
    "state_transition_graph": {
        "DISCOVERED": ["EVIDENCE_PENDING"],
        "EVIDENCE_PENDING": ["EVIDENCE_BLOCKED", "EVIDENCE_READY"],
        "EVIDENCE_READY": ["ASSIGNMENT_CANDIDATE"],
        "EVIDENCE_BLOCKED": ["DEFERRED", "REJECTED"],
        "ASSIGNMENT_CANDIDATE": ["ASSIGNED", "DEFERRED", "DUPLICATE", "REJECTED"],
        "ASSIGNED": ["PRODUCTION_IN_PROGRESS"],
        "PRODUCTION_IN_PROGRESS": ["REVIEW_BLOCKED", "REVIEW_READY"],
        "REVIEW_BLOCKED": ["HELD", "REJECTED"],
        "REVIEW_READY": ["OPERATOR_PENDING"],
        "OPERATOR_PENDING": ["APPROVED_EXACT", "EXPIRED", "HELD", "REJECTED"],
        "APPROVED_EXACT": ["OUTBOX_READY"],
        "HELD": ["DEFERRED", "REJECTED"],
        "EXPIRED": ["CLOSED"],
        "OUTBOX_READY": ["DISPATCHING"],
        "DISPATCHING": ["DISPATCH_BLOCKED", "DISPATCH_COMPLETE", "PARTIAL_SUCCESS", "UNKNOWN_WRITE"],
        "PARTIAL_SUCCESS": ["OPERATOR_RECOVERY_REQUIRED", "RECONCILING"],
        "UNKNOWN_WRITE": ["OPERATOR_RECOVERY_REQUIRED", "RECONCILING"],
        "DISPATCH_BLOCKED": ["DEAD_LETTER", "HELD"],
        "DISPATCH_COMPLETE": ["RECONCILING"],
        "RECONCILING": ["COMPLETE", "DEAD_LETTER", "OPERATOR_RECOVERY_REQUIRED"],
        "COMPLETE": ["OBSERVATION_PENDING"],
        "DEAD_LETTER": ["CLOSED", "OPERATOR_RECOVERY_REQUIRED"],
        "OPERATOR_RECOVERY_REQUIRED": ["ASSIGNMENT_CANDIDATE", "CLOSED"],
        "OBSERVATION_PENDING": ["LEARNING_REVIEW_READY"],
        "LEARNING_REVIEW_READY": ["CLOSED"],
        "CLOSED": [],
        "DEFERRED": ["ASSIGNMENT_CANDIDATE"],
        "DUPLICATE": ["CLOSED"],
        "REJECTED": ["CLOSED"],
    },
    "protected_state_set": [
        "APPROVED_EXACT", "COMPLETE", "DISPATCHING", "DISPATCH_BLOCKED",
        "DISPATCH_COMPLETE", "OUTBOX_READY", "PARTIAL_SUCCESS", "RECONCILING", "UNKNOWN_WRITE",
    ],
    "accepted_event_schema_set": [
        "contentops.event_payload.historical_v1",
        "contentops.event_payload.legacy_projection_baseline.v1",
        "contentops.event_payload.legacy_v1",
        "contentops.event_payload.v1",
    ],
    # Dotted paths in this manifest are asserted to resolve by the test suite; they are
    # written as literals rather than imported because importing the store module here
    # would invert the dependency direction (the store imports this module).
    "event_envelope_builder": "live_contentops.durable_operational_store_v1.build_event_envelope",
    "artifact_scopes": ["GLOBAL_REUSABLE", "LEGACY_UNSCOPED_QUARANTINED", "STORY_EXACT", "WORK_ITEM_EXACT"],
    "append_immutability_guard_sql": [
        "CREATE TRIGGER IF NOT EXISTS trg_transition_events_append_authorized BEFORE INSERT ON transition_events BEGIN SELECT CASE WHEN contentops_append_authorized() != 1 THEN RAISE(ABORT,'transition_events INSERT requires canonical append authorization') END; END",
        "CREATE TRIGGER IF NOT EXISTS trg_artifact_references_insert_authorized BEFORE INSERT ON artifact_references BEGIN SELECT CASE WHEN contentops_artifact_insert_authorized() != 1 THEN RAISE(ABORT,'artifact_references INSERT requires canonical registration authorization') END; END",
    ],
    "replay_validation_semantics": "canonical_json_hash_chain_replay_v1",
}
DEPENDENCY_MANIFEST_V2_JSON = canonical_json(DEPENDENCY_MANIFEST_V2)
DEPENDENCY_MANIFEST_V2_HASH = hashlib.sha256(DEPENDENCY_MANIFEST_V2_JSON.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# Schema migration v5 — public-object identity persistence.
#
# Migration v5 is appended WITHOUT touching the frozen v1-v4 migration SQL/checksums.
# It extends ``platform_dispatches`` with the exact external public-object identity
# returned by the publisher, so a restart can answer "which exact external post did
# this dispatch create?" from durable state alone and resume readback/reconciliation
# without republishing. Migration 1-4 checksums are intentionally excluded from this
# constant so the historical dependency manifests above remain byte-frozen evidence.
# ---------------------------------------------------------------------------
MIGRATION_V5_SQL = (
    "\nALTER TABLE platform_dispatches ADD COLUMN public_object_id TEXT;\n"
    "ALTER TABLE platform_dispatches ADD COLUMN public_object_url TEXT;\n"
    "ALTER TABLE platform_dispatches ADD COLUMN public_object_url_hash TEXT;\n"
)
MIGRATION_V5_CHECKSUM = hashlib.sha256(MIGRATION_V5_SQL.encode("utf-8")).hexdigest()

DEPENDENCY_MANIFEST_V3: Mapping[str, Any] = {
    "schema_version": "contentops.schema_v5_dependency_manifest.v1",
    "canonical_json": CANONICAL_JSON_CONTRACT,
    "genesis_previous_hash": GENESIS_PREVIOUS_HASH,
    "legacy_baseline_kind": "LEGACY_PROJECTION_BASELINE",
    "legacy_quarantine_scope": LEGACY_QUARANTINE_SCOPE,
    "historical_lineage_registry": {
        lineage_id: {
            "schema_fingerprint": lineage["schema_fingerprint"],
            "migration_checksums": dict(lineage["migration_checksums"]),
            "valid_genesis_present": lineage["valid_genesis_present"],
        }
        for lineage_id, lineage in HISTORICAL_SCHEMA_LINEAGES.items()
    },
    "migration_sql_checksums": {**CURRENT_MIGRATION_CHECKSUMS, 5: MIGRATION_V5_CHECKSUM},
    "migration_sql_hashes": {
        **{v: hashlib.sha256(sql.encode("utf-8")).hexdigest() for v, sql in CURRENT_MIGRATION_SQL.items()},
        5: MIGRATION_V5_CHECKSUM,
    },
    "migration_transform_versions": {
        1: "sql_only.v1",
        2: "legacy_sequence.v2",
        3: "legacy_envelope.v3",
        4: "historical_lineage_compatibility.v4",
        5: "sql_only.v5",
    },
    "migration_sql_source": "live_contentops.historical_schema_compatibility_v1.CURRENT_MIGRATION_SQL / MIGRATION_V5_SQL",
    "public_object_identity_columns": {
        "table": "platform_dispatches",
        "columns": ["public_object_id", "public_object_url", "public_object_url_hash"],
        "invariant": "write_once_exact_external_identity_no_last_write_wins",
    },
    "state_rules": "live_contentops.durable_operational_store_v1.TRANSITION_GRAPH",
    "authority_rule": "WAVE02_FORBIDDEN_AUTHORITY_STATES",
    "event_hash_rule": "sha256(canonical event_payload_json)",
}
DEPENDENCY_MANIFEST_V3_JSON = canonical_json(DEPENDENCY_MANIFEST_V3)
DEPENDENCY_MANIFEST_V3_HASH = hashlib.sha256(DEPENDENCY_MANIFEST_V3_JSON.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# Schema migration v6 — durable performance observations + learning policy versions.
#
# Migration v6 is appended WITHOUT touching the frozen v1-v5 migration SQL/checksums.
# It adds the exact durable surface for the Final Daily App closed-loop:
#   * performance_observations  — append-only, idempotent-by-identity platform-native
#     performance observations linked to the exact canonical dispatch/public-object lineage.
#   * learning_policy_versions  — immutable, append-only history of accepted learning-policy
#     versions (parent-retained; rollback creates a NEW version, never a rewrite).
# UNAVAILABLE metrics are never stored as zeros; availability state is explicit.
# ---------------------------------------------------------------------------
MIGRATION_V6_SQL = (
    "\nCREATE TABLE IF NOT EXISTS performance_observations (\n"
    "    observation_id TEXT PRIMARY KEY,\n"
    "    schema_version TEXT NOT NULL,\n"
    "    dispatch_id TEXT NOT NULL,\n"
    "    work_item_id TEXT NOT NULL,\n"
    "    platform TEXT NOT NULL,\n"
    "    public_object_id TEXT NOT NULL,\n"
    "    public_object_url_hash TEXT,\n"
    "    observation_window TEXT NOT NULL,\n"
    "    scheduled_for_utc TEXT NOT NULL,\n"
    "    collected_at_utc TEXT,\n"
    "    collector_capability_version TEXT NOT NULL,\n"
    "    collection_status TEXT NOT NULL,\n"
    "    metrics_native_json TEXT NOT NULL,\n"
    "    metric_availability_json TEXT NOT NULL,\n"
    "    source_identity TEXT NOT NULL,\n"
    "    observation_hash TEXT NOT NULL,\n"
    "    learning_eligible INTEGER NOT NULL DEFAULT 0,\n"
    "    FOREIGN KEY(dispatch_id) REFERENCES platform_dispatches(dispatch_id)\n"
    ");\n"
    "CREATE INDEX IF NOT EXISTS idx_perf_obs_dispatch_window\n"
    "ON performance_observations(dispatch_id, observation_window);\n"
    "CREATE INDEX IF NOT EXISTS idx_perf_obs_due\n"
    "ON performance_observations(collection_status, scheduled_for_utc);\n"
    "\nCREATE TABLE IF NOT EXISTS learning_policy_versions (\n"
    "    policy_version TEXT PRIMARY KEY,\n"
    "    parent_policy_version TEXT,\n"
    "    created_at_utc TEXT NOT NULL,\n"
    "    status TEXT NOT NULL,\n"
    "    decision TEXT NOT NULL,\n"
    "    sample_count INTEGER NOT NULL DEFAULT 0,\n"
    "    confidence REAL NOT NULL DEFAULT 0,\n"
    "    formula_version TEXT NOT NULL,\n"
    "    observation_ids_json TEXT NOT NULL,\n"
    "    evaluation_window TEXT NOT NULL,\n"
    "    accepted_changes_json TEXT NOT NULL,\n"
    "    bounded_delta_json TEXT NOT NULL,\n"
    "    rollback_reference TEXT,\n"
    "    decision_reason TEXT NOT NULL,\n"
    "    policy_payload_json TEXT NOT NULL,\n"
    "    policy_hash TEXT NOT NULL\n"
    ");\n"
    "CREATE INDEX IF NOT EXISTS idx_learning_policy_status_created\n"
    "ON learning_policy_versions(status, created_at_utc);\n"
)
MIGRATION_V6_CHECKSUM = hashlib.sha256(MIGRATION_V6_SQL.encode("utf-8")).hexdigest()

DEPENDENCY_MANIFEST_V4: Mapping[str, Any] = {
    "schema_version": "contentops.schema_v6_dependency_manifest.v1",
    "canonical_json": CANONICAL_JSON_CONTRACT,
    "genesis_previous_hash": GENESIS_PREVIOUS_HASH,
    "legacy_baseline_kind": "LEGACY_PROJECTION_BASELINE",
    "legacy_quarantine_scope": LEGACY_QUARANTINE_SCOPE,
    "historical_lineage_registry": {
        lineage_id: {
            "schema_fingerprint": lineage["schema_fingerprint"],
            "migration_checksums": dict(lineage["migration_checksums"]),
            "valid_genesis_present": lineage["valid_genesis_present"],
        }
        for lineage_id, lineage in HISTORICAL_SCHEMA_LINEAGES.items()
    },
    "migration_sql_checksums": {**CURRENT_MIGRATION_CHECKSUMS, 5: MIGRATION_V5_CHECKSUM, 6: MIGRATION_V6_CHECKSUM},
    "migration_sql_hashes": {
        **{v: hashlib.sha256(sql.encode("utf-8")).hexdigest() for v, sql in CURRENT_MIGRATION_SQL.items()},
        5: MIGRATION_V5_CHECKSUM,
        6: MIGRATION_V6_CHECKSUM,
    },
    "migration_transform_versions": {
        1: "sql_only.v1",
        2: "legacy_sequence.v2",
        3: "legacy_envelope.v3",
        4: "historical_lineage_compatibility.v4",
        5: "sql_only.v5",
        6: "sql_only.v6",
    },
    "migration_sql_source": "live_contentops.historical_schema_compatibility_v1.CURRENT_MIGRATION_SQL / MIGRATION_V5_SQL / MIGRATION_V6_SQL",
    "public_object_identity_columns": {
        "table": "platform_dispatches",
        "columns": ["public_object_id", "public_object_url", "public_object_url_hash"],
        "invariant": "write_once_exact_external_identity_no_last_write_wins",
    },
    "performance_learning_tables": ["performance_observations", "learning_policy_versions"],
    "state_rules": "live_contentops.durable_operational_store_v1.TRANSITION_GRAPH",
    "authority_rule": "WAVE02_FORBIDDEN_AUTHORITY_STATES",
    "event_hash_rule": "sha256(canonical event_payload_json)",
}
DEPENDENCY_MANIFEST_V4_JSON = canonical_json(DEPENDENCY_MANIFEST_V4)
DEPENDENCY_MANIFEST_V4_HASH = hashlib.sha256(DEPENDENCY_MANIFEST_V4_JSON.encode("utf-8")).hexdigest()

# Schema migration v7 — one restart-safe operating-mode control. Migrations v1-v6
# remain byte/checksum frozen; changing this row never launches work or a publisher.
MIGRATION_V7_SQL = (
    "\nCREATE TABLE IF NOT EXISTS operating_controls (\n"
    "    singleton_id INTEGER PRIMARY KEY CHECK(singleton_id = 1),\n"
    "    operating_mode TEXT NOT NULL CHECK(operating_mode IN "
    "('AUTONOMOUS_DEFAULT','SUPERVISED_OPERATOR_GATE','SHADOW_ONLY','KILL_SWITCH')),\n"
    "    state_version INTEGER NOT NULL CHECK(state_version >= 1),\n"
    "    updated_at_utc TEXT NOT NULL,\n"
    "    control_source TEXT NOT NULL\n"
    ");\n"
    "INSERT INTO operating_controls "
    "(singleton_id, operating_mode, state_version, updated_at_utc, control_source) "
    "VALUES (1, 'AUTONOMOUS_DEFAULT', 1, "
    "strftime('%Y-%m-%dT%H:%M:%fZ','now'), 'SCHEMA_V7_INITIAL_PRODUCT_DEFAULT');\n"
)
MIGRATION_V7_CHECKSUM = hashlib.sha256(MIGRATION_V7_SQL.encode("utf-8")).hexdigest()

DEPENDENCY_MANIFEST_V5: Mapping[str, Any] = {
    **DEPENDENCY_MANIFEST_V4,
    "schema_version": "contentops.schema_v7_dependency_manifest.v1",
    "migration_sql_checksums": {
        **DEPENDENCY_MANIFEST_V4["migration_sql_checksums"], 7: MIGRATION_V7_CHECKSUM,
    },
    "migration_sql_hashes": {
        **DEPENDENCY_MANIFEST_V4["migration_sql_hashes"], 7: MIGRATION_V7_CHECKSUM,
    },
    "migration_transform_versions": {
        **DEPENDENCY_MANIFEST_V4["migration_transform_versions"], 7: "sql_only.v7",
    },
    "migration_sql_source": (
        "live_contentops.historical_schema_compatibility_v1.CURRENT_MIGRATION_SQL / "
        "MIGRATION_V5_SQL / MIGRATION_V6_SQL / MIGRATION_V7_SQL"
    ),
    "operating_control": {
        "table": "operating_controls",
        "singleton_id": 1,
        "allowed_modes": [
            "AUTONOMOUS_DEFAULT", "SUPERVISED_OPERATOR_GATE", "SHADOW_ONLY", "KILL_SWITCH",
        ],
        "invariant": "cas_only_policy_change_zero_publication_side_effects",
    },
}
DEPENDENCY_MANIFEST_V5_JSON = canonical_json(DEPENDENCY_MANIFEST_V5)
DEPENDENCY_MANIFEST_V5_HASH = hashlib.sha256(DEPENDENCY_MANIFEST_V5_JSON.encode("utf-8")).hexdigest()

# Schema migration v8 — current destination/surface readiness.
#
# Migrations v1-v7 remain byte/checksum frozen.  This table stores only the latest sanitized
# read-only probe result used by the Daily App Platforms/Incidents views and publication gate;
# it is not a credential store and it does not manufacture historical readiness.
MIGRATION_V8_SQL = (
    "\nCREATE TABLE IF NOT EXISTS destination_readiness (\n"
    "    surface TEXT PRIMARY KEY,\n"
    "    platform TEXT NOT NULL,\n"
    "    transport_registry_version TEXT NOT NULL,\n"
    "    transport_type TEXT NOT NULL,\n"
    "    readiness_state TEXT NOT NULL CHECK(readiness_state IN "
    "('READY_AUTHENTICATED','READY_NON_BROWSER_BINDING','REAUTH_REQUIRED',"
    "'AUTH_INVALID','IDENTITY_MISMATCH','PERMISSION_MISSING','SESSION_UNAVAILABLE',"
    "'TRANSPORT_UNAVAILABLE','TRANSIENT_DEGRADED','CAPABILITY_UNSUPPORTED')),\n"
    "    destination_identity TEXT,\n"
    "    identity_match INTEGER NOT NULL CHECK(identity_match IN (0,1)),\n"
    "    probe_kind TEXT NOT NULL,\n"
    "    probed_at_utc TEXT NOT NULL,\n"
    "    sanitized_detail_json TEXT NOT NULL\n"
    ");\n"
    "CREATE INDEX IF NOT EXISTS idx_destination_readiness_state\n"
    "ON destination_readiness(readiness_state, platform);\n"
)
MIGRATION_V8_CHECKSUM = hashlib.sha256(MIGRATION_V8_SQL.encode("utf-8")).hexdigest()

DEPENDENCY_MANIFEST_V6: Mapping[str, Any] = {
    **DEPENDENCY_MANIFEST_V5,
    "schema_version": "contentops.schema_v8_dependency_manifest.v1",
    "migration_sql_checksums": {
        **DEPENDENCY_MANIFEST_V5["migration_sql_checksums"], 8: MIGRATION_V8_CHECKSUM,
    },
    "migration_sql_hashes": {
        **DEPENDENCY_MANIFEST_V5["migration_sql_hashes"], 8: MIGRATION_V8_CHECKSUM,
    },
    "migration_transform_versions": {
        **DEPENDENCY_MANIFEST_V5["migration_transform_versions"], 8: "sql_only.v8",
    },
    "migration_sql_source": (
        "live_contentops.historical_schema_compatibility_v1.CURRENT_MIGRATION_SQL / "
        "MIGRATION_V5_SQL / MIGRATION_V6_SQL / MIGRATION_V7_SQL / MIGRATION_V8_SQL"
    ),
    "destination_readiness": {
        "table": "destination_readiness",
        "authority": "latest_bounded_sanitized_read_only_identity_probe",
        "ready_states": ["READY_AUTHENTICATED", "READY_NON_BROWSER_BINDING"],
        "secret_values_allowed": False,
    },
}
DEPENDENCY_MANIFEST_V6_JSON = canonical_json(DEPENDENCY_MANIFEST_V6)
DEPENDENCY_MANIFEST_V6_HASH = hashlib.sha256(DEPENDENCY_MANIFEST_V6_JSON.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RecognizedLineage:
    lineage_id: str
    schema_fingerprint: str
    migration_checksums: Tuple[Tuple[int, str], ...]


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


#: Backwards-compatible private alias for existing call sites in this module.
#: Intentionally the same object as :func:`canonical_json` so no second
#: canonical encoder can ever exist in this surface.
_canonical_json = canonical_json


def _quoted(conn: sqlite3.Connection, value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _table_columns(conn: sqlite3.Connection, table: str) -> Tuple[str, ...]:
    return tuple(row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall())


def schema_fingerprint(conn: sqlite3.Connection) -> str:
    """Return the frozen canonical sqlite schema fingerprint used by the lineage registry."""
    objects = []
    for row in conn.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
    ).fetchall():
        item: Dict[str, Any] = {"type": row[0], "name": row[1], "table": row[2], "sql": row[3]}
        if row[0] == "table":
            item["columns"] = [
                {"cid": col[0], "name": col[1], "type": col[2], "notnull": col[3], "default": col[4], "pk": col[5]}
                for col in conn.execute(f"PRAGMA table_info({row[1]})").fetchall()
            ]
        objects.append(item)
    return _sha256(_canonical_json(objects))


def recorded_migration_checksums(conn: sqlite3.Connection) -> Tuple[Tuple[int, str], ...]:
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()
    if not exists:
        return tuple()
    return tuple((int(row[0]), str(row[1])) for row in conn.execute(
        "SELECT version,checksum FROM schema_migrations ORDER BY version"
    ).fetchall())


def recognize_lineage(conn: sqlite3.Connection) -> RecognizedLineage:
    checksums = recorded_migration_checksums(conn)
    lineage_id = HISTORICAL_CHECKSUM_LINEAGE_INDEX.get(checksums)
    if lineage_id is None:
        raise ValueError("historical_schema_lineage_unknown_checksum_set")
    expected = HISTORICAL_SCHEMA_LINEAGES[lineage_id]
    actual_fingerprint = schema_fingerprint(conn)
    if actual_fingerprint != expected["schema_fingerprint"]:
        raise ValueError("historical_schema_lineage_checksum_fingerprint_mismatch")
    return RecognizedLineage(lineage_id, actual_fingerprint, checksums)


def _copy_rows(conn: sqlite3.Connection, source: str, target: str, expressions: Mapping[str, str]) -> None:
    source_columns = set(_table_columns(conn, source))
    target_columns = _table_columns(conn, target)
    insert_columns = [col for col in target_columns if col in expressions or col in source_columns]
    select_expr = [expressions.get(col, col) for col in insert_columns]
    conn.execute(
        f"INSERT INTO {target} ({','.join(insert_columns)}) SELECT {','.join(select_expr)} FROM {source}"
    )


def _source_rows_hash(conn: sqlite3.Connection, table: str) -> str:
    columns = _table_columns(conn, table)
    if not columns:
        return _sha256("[]")
    rows = [dict(zip(columns, row)) for row in conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()]
    return _sha256(_canonical_json(rows))


def _snapshot_projection(row: sqlite3.Row | Sequence[Any], columns: Sequence[str]) -> Dict[str, Any]:
    record = dict(zip(columns, row))
    return {key: record.get(key) for key in ("work_item_id", "story_id", "title", "target_surface", "current_state", "state_version", "created_at", "updated_at")}


def _legacy_event_order(rows: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
    def key(row: Mapping[str, Any]) -> Tuple[int, str, str]:
        return int(row["state_version"]), str(row.get("timestamp_utc") or ""), str(row["event_id"])
    ordered = sorted(rows, key=key)
    versions = [int(row["state_version"]) for row in ordered]
    if len(versions) != len(set(versions)) or any(next_v != prev_v + 1 for prev_v, next_v in zip(versions, versions[1:])):
        raise ValueError("historical_schema_lineage_ambiguous_event_order")
    return ordered


def _legacy_artifact_hashes(raw: Any) -> Sequence[str]:
    try:
        values = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("historical_event_invalid_artifact_hash_set") from exc
    if not isinstance(values, list) or any(not isinstance(value, str) or len(value) != 64 for value in values):
        raise ValueError("historical_event_invalid_artifact_hash_set")
    return sorted(values)


def _artifact_snapshot(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: row.get(key)
        for key in (
            "artifact_id", "artifact_type", "story_id", "work_item_id", "artifact_scope",
            "storage_class", "byte_length", "sha256_hash", "schema_version", "producer_ref",
            "receipt_id", "receipt_schema", "receipt_source_identity", "receipt_object_identity",
            "receipt_verifier_identity", "canonical_receipt_hash",
        )
    }


def _event_payload(
    *,
    event_schema_version: str,
    event_seq: int,
    work: Mapping[str, Any],
    event: Mapping[str, Any],
    previous_hash: str,
    input_ids: Sequence[str],
    snapshots: Sequence[Mapping[str, Any]],
    explanation_hash: str,
    unresolved_hashes: Sequence[str],
    source_record_hash: str,
) -> Dict[str, Any]:
    return {
        "event_schema_version": event_schema_version,
        "event_kind": event.get("event_kind") or "STATE_TRANSITION",
        "event_seq": event_seq,
        "work_item_id": work["work_item_id"],
        "story_id": work["story_id"],
        "title": work["title"],
        "target_surface": work["target_surface"],
        "state_version": int(event["state_version"]),
        "from_state": event["from_state"],
        "to_state": event["to_state"],
        "previous_event_hash": previous_hash,
        "actor_class": event["actor_class"],
        "actor_ref": event["actor_ref"],
        "reason_code": event["reason_code"],
        "explanation_hash": explanation_hash,
        "correlation_id": event["correlation_id"],
        "policy_version": event.get("policy_version") or "contentops.policy.v1",
        "model_version": event.get("model_version") or "NOT_APPLICABLE",
        "authority_type": event.get("authority_type") or "NONE",
        "authority_ref": event.get("authority_ref"),
        "authority_effect": event.get("authority_effect") or "NO_AUTHORITY_GRANTED",
        "lease_id": event.get("lease_id"),
        "lease_key": event.get("lease_key"),
        "fencing_token": int(event.get("fencing_token") or 0),
        "input_artifact_ids": sorted(input_ids),
        "output_artifact_ids": sorted(json.loads(event.get("output_artifact_ids") or "[]")),
        "artifact_snapshots": list(snapshots),
        "timestamp_utc": event["timestamp_utc"],
        "legacy_migration": {
            "migration_generated": False,
            "source_event_id": event["event_id"],
            "source_record_hash": source_record_hash,
            "unresolved_artifact_sha256": sorted(unresolved_hashes),
        },
    }


def _convert_artifacts(conn: sqlite3.Connection, lineage_id: str) -> None:
    columns = set(_table_columns(conn, "artifact_references_legacy"))
    rows = conn.execute("SELECT * FROM artifact_references_legacy ORDER BY artifact_id").fetchall()
    names = _table_columns(conn, "artifact_references_legacy")
    for raw in rows:
        row = dict(zip(names, raw))
        digest = row.get("sha256_hash") or row.get("content_hash")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("historical_artifact_invalid_hash")
        story_id = row.get("story_id")
        work_item_id = row.get("work_item_id")
        if work_item_id:
            scope = "WORK_ITEM_EXACT"
        elif story_id:
            scope = "STORY_EXACT"
        else:
            scope = LEGACY_QUARANTINE_SCOPE
        source_record_json = _canonical_json(row)
        source_record_hash = _sha256(source_record_json)
        metadata = {
            "source_lineage_id": lineage_id,
            "legacy_artifact_key": row.get("artifact_key"),
            "legacy_storage_path": row.get("storage_path"),
            "legacy_metadata_json": row.get("metadata_json"),
            "source_record_hash": source_record_hash,
        }
        conn.execute(
            "INSERT INTO artifact_references (artifact_id,artifact_type,story_id,work_item_id,storage_class,byte_length,sha256_hash,schema_version,created_at,producer_ref,sensitivity_class,artifact_scope,receipt_schema,receipt_id,receipt_source_identity,receipt_object_identity,receipt_verifier_identity,canonical_receipt_hash) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (row["artifact_id"], row["artifact_type"], story_id, work_item_id,
             row.get("storage_class") or "LEGACY", int(row["byte_length"]), digest,
             row.get("schema_version") or "contentops.legacy_artifact.v1", row["created_at"],
             row.get("producer_ref") or "LEGACY_UNKNOWN", row.get("sensitivity_class") or "PUBLIC",
             scope, "contentops.legacy_artifact_receipt.v1", f"legacy_{row['artifact_id']}",
             lineage_id, row.get("storage_path") or row["artifact_id"], "HISTORICAL_SCHEMA_V4_MIGRATOR",
             _sha256(_canonical_json(metadata))),
        )
        conn.execute(
            "INSERT INTO legacy_artifact_evidence VALUES (?,?,?,?,?,?,?,?,?)",
            (row["artifact_id"], lineage_id, row.get("artifact_key"), row.get("storage_path"),
             digest, int(row["byte_length"]), source_record_json, source_record_hash, scope),
        )


def _convert_events(conn: sqlite3.Connection, lineage: Mapping[str, Any]) -> None:
    event_names = _table_columns(conn, "transition_events_legacy")
    work_names = _table_columns(conn, "work_items")
    works = [dict(zip(work_names, row)) for row in conn.execute("SELECT * FROM work_items ORDER BY work_item_id").fetchall()]
    artifacts = {
        row["sha256_hash"]: dict(row)
        for row in conn.execute("SELECT * FROM artifact_references WHERE artifact_scope != ?", (LEGACY_QUARANTINE_SCOPE,)).fetchall()
    }
    for work in works:
        raw_rows = [dict(zip(event_names, row)) for row in conn.execute(
            "SELECT * FROM transition_events_legacy WHERE work_item_id=?", (work["work_item_id"],)
        ).fetchall()]
        original_projection = _snapshot_projection(tuple(work.get(name) for name in work_names), work_names)
        projection_hash = _sha256(_canonical_json(original_projection))
        if not lineage["valid_genesis_present"]:
            ordered = list(_legacy_event_order(raw_rows))
            baseline_timestamp = str(work.get("created_at") or (ordered[0]["timestamp_utc"] if ordered else "1970-01-01T00:00:00+00:00"))
            baseline = {
                "event_schema_version": "contentops.event_payload.legacy_projection_baseline.v1",
                "event_kind": "LEGACY_PROJECTION_BASELINE",
                "event_seq": 1,
                "work_item_id": work["work_item_id"],
                "story_id": work["story_id"],
                "title": work["title"],
                "target_surface": work["target_surface"],
                "state_version": 1,
                "from_state": "DISCOVERED",
                "to_state": "DISCOVERED",
                "previous_event_hash": GENESIS_PREVIOUS_HASH,
                "actor_class": "ContentOpsHistoricalSchemaV4Migrator",
                "actor_ref": "historical_lineage_compatibility",
                "reason_code": "LEGACY_PROJECTION_BASELINE",
                "explanation_hash": _sha256("deterministic historical no-genesis projection baseline"),
                "correlation_id": f"legacy_baseline_{work['work_item_id']}",
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
                "timestamp_utc": baseline_timestamp,
                "source_lineage_id": lineage["lineage_id"],
                "source_migration_checksums": [
                    {"version": int(version), "checksum": checksum}
                    for version, checksum in sorted(lineage["migration_checksums"].items())
                ],
                "migration_generated": True,
                "original_projection": original_projection,
                "original_projection_hash": projection_hash,
                "source_record_hash": _sha256(_canonical_json(work)),
            }
            baseline_explanation = "Deterministic baseline for recognized no-genesis lineage"
            baseline["explanation_hash"] = _sha256(baseline_explanation)
            payload_json = _canonical_json(baseline)
            previous_hash = _sha256(payload_json)
            conn.execute(
                "INSERT INTO transition_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"evt_legacy_baseline_{_sha256(work['work_item_id'])[:16]}", f"tr_legacy_baseline_{work['work_item_id']}", work["work_item_id"],
                 "LEGACY_PROJECTION_BASELINE", 1, "DISCOVERED", "DISCOVERED", 1, "ContentOpsHistoricalSchemaV4Migrator", "historical_lineage_compatibility",
                 "LEGACY_PROJECTION_BASELINE", baseline_explanation, baseline["explanation_hash"], baseline["correlation_id"],
                 "contentops.policy.v1", "NOT_APPLICABLE", "NONE", None, "NO_AUTHORITY_GRANTED", None, None, 0, "[]", "[]", "[]",
                 GENESIS_PREVIOUS_HASH, payload_json, previous_hash, baseline_timestamp),
            )
            conn.execute(
                "INSERT INTO legacy_projection_baselines VALUES (?,?,?,?,?,?)",
                (work["work_item_id"], lineage["lineage_id"], payload_json, previous_hash, projection_hash, baseline_timestamp),
            )
            start_seq = 2
        else:
            ordered = sorted(raw_rows, key=lambda row: int(row.get("event_seq") or row["state_version"]))
            if not ordered:
                raise ValueError("historical_schema_lineage_missing_valid_genesis")
            start_seq = 1
            previous_hash = GENESIS_PREVIOUS_HASH
        for offset, event in enumerate(ordered):
            event_seq = start_seq + offset
            source_record_hash = _sha256(_canonical_json(event))
            source_hashes = _legacy_artifact_hashes(event.get("artifact_hash_set")) if "artifact_hash_set" in event else []
            input_ids = [artifacts[digest]["artifact_id"] for digest in source_hashes if digest in artifacts]
            unresolved = [digest for digest in source_hashes if digest not in artifacts]
            snapshots = [_artifact_snapshot(artifacts[digest]) for digest in source_hashes if digest in artifacts]
            explanation = event.get("explanation") or ""
            explanation_hash = event.get("explanation_hash") or _sha256(explanation)
            if event.get("event_payload_json"):
                try:
                    payload = json.loads(event["event_payload_json"])
                except json.JSONDecodeError as exc:
                    raise ValueError("historical_event_invalid_payload_json") from exc
                payload["event_seq"] = event_seq
                payload["previous_event_hash"] = previous_hash
                payload.setdefault("event_kind", "WORK_ITEM_CREATED" if event_seq == 1 else "STATE_TRANSITION")
                payload.setdefault("story_id", work["story_id"])
                payload.setdefault("title", work["title"])
                payload.setdefault("target_surface", work["target_surface"])
                payload["legacy_migration"] = {
                    "migration_generated": False,
                    "source_event_id": event["event_id"],
                    "source_record_hash": source_record_hash,
                    "unresolved_artifact_sha256": sorted(unresolved),
                }
                payload_json = _canonical_json(payload)
            else:
                payload = _event_payload(
                    event_schema_version="contentops.event_payload.historical_v1", event_seq=event_seq,
                    work=work, event=event, previous_hash=previous_hash, input_ids=input_ids,
                    snapshots=snapshots, explanation_hash=explanation_hash,
                    unresolved_hashes=unresolved, source_record_hash=source_record_hash,
                )
                payload_json = _canonical_json(payload)
            event_hash = _sha256(payload_json)
            event_kind = payload.get("event_kind") or ("WORK_ITEM_CREATED" if event_seq == 1 else "STATE_TRANSITION")
            conn.execute(
                "INSERT INTO transition_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (event["event_id"], event["transition_key"], work["work_item_id"], event_kind, event_seq,
                 event["from_state"], event["to_state"], int(event["state_version"]), event["actor_class"], event["actor_ref"],
                 event["reason_code"], explanation, explanation_hash, event["correlation_id"], event.get("policy_version") or "contentops.policy.v1",
                 event.get("model_version") or "NOT_APPLICABLE", event.get("authority_type") or "NONE", event.get("authority_ref"),
                 event.get("authority_effect") or "NO_AUTHORITY_GRANTED", event.get("lease_id"), event.get("lease_key"), int(event.get("fencing_token") or 0),
                 _canonical_json(input_ids), event.get("output_artifact_ids") or "[]", _canonical_json(snapshots), previous_hash,
                 payload_json, event_hash, event["timestamp_utc"]),
            )
            previous_hash = event_hash


def _split_sql_statements(sql_script: str) -> Sequence[str]:
    """Split only on SQLite-complete boundaries, preserving trigger bodies."""
    statements = []
    current = []
    for character in sql_script:
        current.append(character)
        if character == ";":
            candidate = "".join(current).strip()
            if candidate and sqlite3.complete_statement(candidate):
                statements.append(candidate)
                current = []
    remainder = "".join(current).strip()
    if remainder:
        if not sqlite3.complete_statement(remainder):
            raise sqlite3.OperationalError("migration SQL ended with an incomplete statement")
        statements.append(remainder)
    return statements


def _create_verified_backup(source: sqlite3.Connection, backup_path: pathlib.Path) -> str:
    """Create one SQLite-consistent backup and return its exact file hash."""
    destination = sqlite3.connect(str(backup_path))
    try:
        source.backup(destination)
        if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("historical_schema_v4_backup_integrity_failed")
    finally:
        destination.close()
    return _sha256(backup_path.read_bytes())


def _record_migration_failure_receipt(
    *,
    db_path: pathlib.Path,
    backup_path: pathlib.Path,
    source_lineage_id: Optional[str],
    source_database_hash: str,
    error: Exception,
    restore_integrity_status: str,
    recorded_at: str,
) -> pathlib.Path:
    """Persist only redacted migration-failure metadata outside the restored database."""
    error_message_hash = _sha256(str(error))
    backup_path_hash = _sha256(backup_path.name)
    receipt_material = {
        "source_lineage_id": source_lineage_id,
        "source_database_hash": source_database_hash,
        # Frozen historical migration target: the historical upgrader migrates exactly to v4.
        "failed_version": 4,
        "error_class": type(error).__name__,
        "error_message_hash": error_message_hash,
        "backup_path_hash": backup_path_hash,
        "restore_integrity_status": restore_integrity_status,
        "recorded_at": recorded_at,
    }
    receipt_id = f"migration_failure_{_sha256(_canonical_json(receipt_material))[:32]}"
    receipt_path = db_path.with_name(f"{db_path.name}.{receipt_id}.sqlite")
    receipt = sqlite3.connect(str(receipt_path))
    try:
        receipt.execute("""
            CREATE TABLE IF NOT EXISTS migration_failure_receipts (
                receipt_id TEXT PRIMARY KEY,
                source_lineage_id TEXT,
                source_database_hash TEXT NOT NULL,
                failed_version INTEGER NOT NULL,
                error_class TEXT NOT NULL,
                error_message_hash TEXT NOT NULL,
                backup_path_hash TEXT NOT NULL,
                restore_integrity_status TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            )
        """)
        receipt.execute(
            "INSERT OR REPLACE INTO migration_failure_receipts VALUES (?,?,?,?,?,?,?,?,?)",
            (
                receipt_id, source_lineage_id, source_database_hash, 4,
                type(error).__name__, error_message_hash, backup_path_hash,
                restore_integrity_status, recorded_at,
            ),
        )
        receipt.commit()
        if receipt.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("historical_schema_v4_failure_receipt_integrity_failed")
    finally:
        receipt.close()
    return receipt_path


def _verify_upgraded_database(
    conn: sqlite3.Connection,
    *,
    db_path: pathlib.Path,
    recognized: RecognizedLineage,
    source_table_rows: Mapping[str, Sequence[Mapping[str, Any]]],
) -> Dict[str, Any]:
    """Verify schema authority, source-row preservation, integrity, and replay after commit."""
    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("historical_schema_v4_post_commit_integrity_failed")
    if conn.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("historical_schema_v4_post_commit_foreign_key_failed")

    migration_rows = [dict(row) for row in conn.execute(
        "SELECT version,checksum,applied_at,description FROM schema_migrations ORDER BY version"
    ).fetchall()]
    source_migrations = list(source_table_rows.get("schema_migrations", ()))
    if migration_rows[:len(source_migrations)] != source_migrations:
        raise ValueError("historical_schema_v4_source_migration_history_changed")
    if len(migration_rows) != len(source_migrations) + 1:
        raise ValueError("historical_schema_v4_migration_history_length_failed")
    if migration_rows[-1]["version"] != 4 or migration_rows[-1]["checksum"] != CURRENT_MIGRATION_CHECKSUMS[4]:
        raise ValueError("historical_schema_v4_post_commit_checksum_failed")

    metadata = conn.execute("SELECT * FROM schema_lineage_metadata WHERE singleton_id=1").fetchone()
    if (
        metadata is None
        or metadata["source_lineage_id"] != recognized.lineage_id
        or metadata["source_schema_fingerprint"] != recognized.schema_fingerprint
        or metadata["compatibility_version"] != 4
        or metadata["dependency_manifest_hash"] not in (DEPENDENCY_MANIFEST_HASH, DEPENDENCY_MANIFEST_V2_HASH)
        or metadata["dependency_manifest_json"] not in (DEPENDENCY_MANIFEST_JSON, DEPENDENCY_MANIFEST_V2_JSON)
    ):
        raise ValueError("historical_schema_v4_lineage_metadata_failed")

    transformed_tables = {"artifact_references", "transition_events", "schema_migrations"}
    for table, expected_rows in source_table_rows.items():
        if table in transformed_tables:
            continue
        columns = _table_columns(conn, table)
        actual_rows = [dict(zip(columns, row)) for row in conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()]
        if actual_rows != list(expected_rows):
            raise ValueError(f"historical_schema_v4_source_rows_changed:{table}")

    artifact_evidence = {
        row["artifact_id"]: row["source_record_hash"]
        for row in conn.execute("SELECT artifact_id,source_record_hash FROM legacy_artifact_evidence").fetchall()
    }
    for source_artifact in source_table_rows.get("artifact_references", ()):
        artifact_id = str(source_artifact["artifact_id"])
        if artifact_evidence.get(artifact_id) != _sha256(_canonical_json(source_artifact)):
            raise ValueError("historical_schema_v4_artifact_source_hash_failed")

    migrated_events = {
        row["event_id"]: json.loads(row["event_payload_json"])
        for row in conn.execute("SELECT event_id,event_kind,event_payload_json FROM transition_events").fetchall()
        if row["event_kind"] != "LEGACY_PROJECTION_BASELINE"
    }
    for source_event in source_table_rows.get("transition_events", ()):
        payload = migrated_events.get(str(source_event["event_id"]))
        legacy = payload.get("legacy_migration") if isinstance(payload, dict) else None
        if not isinstance(legacy, dict) or legacy.get("source_record_hash") != _sha256(_canonical_json(source_event)):
            raise ValueError("historical_schema_v4_event_source_hash_failed")

    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    store = ContentOpsDurableStore(db_path, auto_migrate=False)
    replay_hashes: Dict[str, str] = {}
    for row in conn.execute("SELECT work_item_id FROM work_items ORDER BY work_item_id").fetchall():
        replay = store.replay_work_item_events(row[0])
        if replay.get("verification_status") != "PASS":
            raise ValueError("historical_schema_v4_post_commit_replay_failed")
        replay_hashes[row[0]] = _sha256(_canonical_json(replay))
    return {"replay_hashes": replay_hashes}


def upgrade_historical_database(db_path: pathlib.Path, *, now_iso: Optional[str] = None) -> Dict[str, Any]:
    """Recognize and atomically upgrade one exact historical database to schema v4."""
    db_path = pathlib.Path(db_path).resolve()
    timestamp = now_iso or datetime.now(timezone.utc).isoformat()
    source = sqlite3.connect(str(db_path))
    source.row_factory = sqlite3.Row
    try:
        recognized = recognize_lineage(source)
        lineage = HISTORICAL_SCHEMA_LINEAGES[recognized.lineage_id]
        source_tables = [
            row[0]
            for row in source.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        source_table_rows = {
            table: [
                dict(zip(_table_columns(source, table), row))
                for row in source.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            ]
            for table in source_tables
        }
        source_table_hashes = {
            table: _sha256(_canonical_json(rows))
            for table, rows in source_table_rows.items()
        }
        backup_token = _sha256(f"{recognized.lineage_id}:{recognized.schema_fingerprint}:{timestamp}")[:16]
        backup_path = db_path.with_name(f"{db_path.name}.recovery.{backup_token}.sqlite")
        source_hash = _create_verified_backup(source, backup_path)
    finally:
        source.close()

    conn = sqlite3.connect(str(db_path), isolation_level=None)
    conn.row_factory = sqlite3.Row
    verification: Dict[str, Any] = {}
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("BEGIN IMMEDIATE")
        for table in ("transition_events", "artifact_references"):
            conn.execute(f"ALTER TABLE {table} RENAME TO {table}_legacy")
        for trigger in (
            "trg_transition_events_no_update", "trg_transition_events_no_delete",
            "trg_artifact_references_no_update", "trg_artifact_references_no_delete",
        ):
            conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        for version in (1, 2, 3):
            for statement in _split_sql_statements(CURRENT_MIGRATION_SQL[version]):
                if not statement.upper().startswith("ALTER TABLE TRANSITION_EVENTS ADD COLUMN"):
                    try:
                        conn.execute(statement)
                    except sqlite3.OperationalError as exc:
                        if "already exists" not in str(exc) and "duplicate column" not in str(exc):
                            raise
        conn.execute("DROP TABLE transition_events")
        conn.execute("ALTER TABLE transition_events_v3 RENAME TO transition_events")
        for statement in _split_sql_statements(CURRENT_MIGRATION_SQL[4]):
            conn.execute(statement)
        _convert_artifacts(conn, recognized.lineage_id)
        _convert_events(conn, lineage)
        conn.execute(
            "INSERT INTO schema_lineage_metadata VALUES (1,?,?,?,?,?,?)",
            (recognized.lineage_id, recognized.schema_fingerprint, 4,
             DEPENDENCY_MANIFEST_V2_JSON, DEPENDENCY_MANIFEST_V2_HASH, timestamp),
        )
        conn.execute(
            "INSERT INTO schema_migrations (version,checksum,applied_at,description) VALUES (?,?,?,?)",
            (4, CURRENT_MIGRATION_CHECKSUMS[4], timestamp, "Wave 02 Schema v4: Historical Lineage Compatibility and Dependency Manifest"),
        )
        conn.execute("DROP TABLE transition_events_legacy")
        conn.execute("DROP TABLE artifact_references_legacy")
        for statement in _split_sql_statements("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_transition_events_work_item_seq ON transition_events(work_item_id,event_seq);
        CREATE TRIGGER IF NOT EXISTS trg_transition_events_append_authorized BEFORE INSERT ON transition_events BEGIN SELECT CASE WHEN contentops_append_authorized() != 1 THEN RAISE(ABORT, 'transition_events INSERT requires canonical append authorization') END; END;
        CREATE TRIGGER IF NOT EXISTS trg_transition_events_no_update BEFORE UPDATE ON transition_events BEGIN SELECT RAISE(ABORT, 'transition_events are append-only: UPDATE forbidden'); END;
        CREATE TRIGGER IF NOT EXISTS trg_transition_events_no_delete BEFORE DELETE ON transition_events BEGIN SELECT RAISE(ABORT, 'transition_events are append-only: DELETE forbidden'); END;
        CREATE TRIGGER IF NOT EXISTS trg_artifact_references_insert_authorized BEFORE INSERT ON artifact_references BEGIN SELECT CASE WHEN contentops_artifact_insert_authorized() != 1 THEN RAISE(ABORT, 'artifact_references INSERT requires canonical registration authorization') END; END;
        CREATE TRIGGER IF NOT EXISTS trg_artifact_references_no_update BEFORE UPDATE ON artifact_references BEGIN SELECT RAISE(ABORT, 'artifact_references are immutable: UPDATE forbidden'); END;
        CREATE TRIGGER IF NOT EXISTS trg_artifact_references_no_delete BEFORE DELETE ON artifact_references BEGIN SELECT RAISE(ABORT, 'artifact_references are immutable: DELETE forbidden'); END;
        """):
            conn.execute(statement)
        conn.execute("COMMIT")
        conn.execute("PRAGMA foreign_keys=ON")
        verification = _verify_upgraded_database(
            conn,
            db_path=db_path,
            recognized=recognized,
            source_table_rows=source_table_rows,
        )
    except Exception as exc:
        if conn.in_transaction:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
        conn.close()
        restore_status = "FAIL_RESTORE_NOT_VERIFIED"
        try:
            for suffix in ("-wal", "-shm"):
                pathlib.Path(f"{db_path}{suffix}").unlink(missing_ok=True)
            shutil.copy2(backup_path, db_path)
            if _sha256(db_path.read_bytes()) != source_hash:
                raise RuntimeError("historical_schema_v4_restore_source_hash_failed")
            restored = sqlite3.connect(str(db_path))
            try:
                if restored.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("historical_schema_v4_restore_integrity_failed")
            finally:
                restored.close()
            if _sha256(db_path.read_bytes()) != source_hash:
                raise RuntimeError("historical_schema_v4_restore_post_check_hash_failed")
            restore_status = "PASS_SOURCE_HASH_AND_SQLITE_INTEGRITY"
        except Exception as restore_exc:
            restore_status = f"FAIL_{type(restore_exc).__name__}"
            try:
                _record_migration_failure_receipt(
                    db_path=db_path, backup_path=backup_path,
                    source_lineage_id=recognized.lineage_id, source_database_hash=source_hash,
                    error=exc, restore_integrity_status=restore_status, recorded_at=timestamp,
                )
            except Exception as receipt_exc:
                raise RuntimeError(
                    f"historical_schema_v4_restore_and_receipt_failed:{type(restore_exc).__name__}:{type(receipt_exc).__name__}"
                ) from exc
            raise RuntimeError(f"historical_schema_v4_restore_failed:{type(restore_exc).__name__}") from exc
        receipt_path = _record_migration_failure_receipt(
            db_path=db_path, backup_path=backup_path,
            source_lineage_id=recognized.lineage_id, source_database_hash=source_hash,
            error=exc, restore_integrity_status=restore_status, recorded_at=timestamp,
        )
        if hasattr(exc, "add_note"):
            exc.add_note(f"migration_failure_receipt_hash={_sha256(receipt_path.name)}")
        raise
    else:
        conn.close()
        backup_path.unlink(missing_ok=True)
    return {
        "status": "PASS_HISTORICAL_SCHEMA_V4_COMPATIBILITY",
        "source_lineage_id": recognized.lineage_id,
        "source_schema_fingerprint": recognized.schema_fingerprint,
        "source_database_hash": source_hash,
        "source_table_hashes": source_table_hashes,
        "dependency_manifest_hash": DEPENDENCY_MANIFEST_V2_HASH,
        "target_schema_version": 4,
        **verification,
    }
