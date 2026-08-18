from __future__ import annotations

import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping


SCHEMA_VERSION = "contentops.v2.unattended_job_store.v2"
TERMINAL_STATES = frozenset({"OWNER_REVIEW_READY", "TERMINAL", "QUARANTINED"})
CANDIDATE_DECISIONS = frozenset({"QUALIFIED", "DEFERRED", "ABSTAIN"})
CREATIVE_RELAY_STATES = (
    "READY_FOR_CREATIVE",
    "CREATIVE_CLAIMED",
    "CREATIVE_READY",
    "HIGH_FINALIZATION",
    "LOCAL_TERMINAL_RESULT",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class JobStoreError(RuntimeError):
    pass


class V2JobStore:
    """Small V2-only SQLite job/outbox and immutable stage ledger."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    @contextmanager
    def transaction(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS video_jobs (
                    video_job_id TEXT PRIMARY KEY,
                    input_packet_path TEXT NOT NULL,
                    input_packet_hash TEXT NOT NULL,
                    target_format TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    state TEXT NOT NULL,
                    claimed_by TEXT,
                    claim_timestamp TEXT,
                    run_id TEXT,
                    retry_counters_json TEXT NOT NULL DEFAULT '{}',
                    last_valid_checkpoint TEXT,
                    terminal_result TEXT,
                    public_write_authority INTEGER NOT NULL DEFAULT 0 CHECK(public_write_authority = 0),
                    resume_count INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(input_packet_hash, target_format)
                );
                CREATE TABLE IF NOT EXISTS job_runs (
                    run_id TEXT PRIMARY KEY,
                    video_job_id TEXT NOT NULL REFERENCES video_jobs(video_job_id),
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    implementation_head TEXT NOT NULL,
                    proof_run_started_at TEXT,
                    manual_source_edits_after_start INTEGER NOT NULL DEFAULT 0,
                    manual_media_edits_after_start INTEGER NOT NULL DEFAULT 0,
                    manual_checkpoint_edits INTEGER NOT NULL DEFAULT 0,
                    public_write_authority INTEGER NOT NULL DEFAULT 0 CHECK(public_write_authority = 0)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_run_per_job
                    ON job_runs(video_job_id) WHERE status = 'ACTIVE';
                CREATE TABLE IF NOT EXISTS stage_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_job_id TEXT NOT NULL REFERENCES video_jobs(video_job_id),
                    run_id TEXT NOT NULL REFERENCES job_runs(run_id),
                    stage TEXT NOT NULL,
                    stage_version TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    input_hashes_json TEXT NOT NULL,
                    output_hashes_json TEXT NOT NULL,
                    artifact_records_json TEXT NOT NULL,
                    role_tool_identity TEXT NOT NULL,
                    model_provenance_json TEXT NOT NULL,
                    wall_time_seconds REAL NOT NULL,
                    safe_usage_json TEXT NOT NULL,
                    result TEXT NOT NULL,
                    retry_state_json TEXT NOT NULL,
                    next_legal_stage TEXT,
                    public_write_authority INTEGER NOT NULL DEFAULT 0 CHECK(public_write_authority = 0)
                );
                CREATE TRIGGER IF NOT EXISTS stage_events_immutable_update
                BEFORE UPDATE ON stage_events BEGIN
                    SELECT RAISE(ABORT, 'stage_events_are_append_only');
                END;
                CREATE TRIGGER IF NOT EXISTS stage_events_immutable_delete
                BEFORE DELETE ON stage_events BEGIN
                    SELECT RAISE(ABORT, 'stage_events_are_append_only');
                END;
                CREATE TABLE IF NOT EXISTS candidate_job_links (
                    candidate_key TEXT PRIMARY KEY,
                    video_job_id TEXT NOT NULL UNIQUE REFERENCES video_jobs(video_job_id),
                    source_content_hash TEXT NOT NULL,
                    trigger_packet_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    public_write_authority INTEGER NOT NULL DEFAULT 0 CHECK(public_write_authority = 0)
                );
                CREATE TABLE IF NOT EXISTS candidate_decisions (
                    candidate_version_id TEXT PRIMARY KEY,
                    candidate_key TEXT NOT NULL,
                    operator_run_id TEXT NOT NULL,
                    candidate_source_json TEXT NOT NULL,
                    qualification_inputs_json TEXT NOT NULL,
                    decision TEXT NOT NULL CHECK(decision IN ('QUALIFIED','DEFERRED','ABSTAIN')),
                    reason_codes_json TEXT NOT NULL,
                    freshness_json TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    source_v1_identity_json TEXT NOT NULL,
                    trigger_packet_path TEXT NOT NULL,
                    trigger_packet_hash TEXT NOT NULL,
                    video_job_id TEXT REFERENCES video_jobs(video_job_id),
                    created_at TEXT NOT NULL,
                    zero_public_write_state TEXT NOT NULL,
                    public_write_authority INTEGER NOT NULL DEFAULT 0 CHECK(public_write_authority = 0),
                    v1_write_count INTEGER NOT NULL DEFAULT 0 CHECK(v1_write_count = 0),
                    platform_write_count INTEGER NOT NULL DEFAULT 0 CHECK(platform_write_count = 0)
                );
                CREATE INDEX IF NOT EXISTS candidate_decisions_candidate_key
                    ON candidate_decisions(candidate_key, created_at);
                CREATE TRIGGER IF NOT EXISTS candidate_decisions_immutable_update
                BEFORE UPDATE ON candidate_decisions BEGIN
                    SELECT RAISE(ABORT, 'candidate_decisions_are_append_only');
                END;
                CREATE TRIGGER IF NOT EXISTS candidate_decisions_immutable_delete
                BEFORE DELETE ON candidate_decisions BEGIN
                    SELECT RAISE(ABORT, 'candidate_decisions_are_append_only');
                END;
                CREATE TABLE IF NOT EXISTS daily_operator_runs (
                    operator_run_id TEXT PRIMARY KEY,
                    completed_at TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    parent_model TEXT NOT NULL,
                    parent_reasoning_effort TEXT NOT NULL,
                    parent_task_id TEXT,
                    v1_read_snapshot_hash TEXT NOT NULL,
                    decision_count INTEGER NOT NULL,
                    qualified_count INTEGER NOT NULL,
                    created_job_count INTEGER NOT NULL,
                    result TEXT NOT NULL,
                    public_write_authority INTEGER NOT NULL DEFAULT 0 CHECK(public_write_authority = 0),
                    v1_write_count INTEGER NOT NULL DEFAULT 0 CHECK(v1_write_count = 0),
                    platform_write_count INTEGER NOT NULL DEFAULT 0 CHECK(platform_write_count = 0)
                );
                CREATE TRIGGER IF NOT EXISTS daily_operator_runs_immutable_update
                BEFORE UPDATE ON daily_operator_runs BEGIN
                    SELECT RAISE(ABORT, 'daily_operator_runs_are_append_only');
                END;
                CREATE TRIGGER IF NOT EXISTS daily_operator_runs_immutable_delete
                BEFORE DELETE ON daily_operator_runs BEGIN
                    SELECT RAISE(ABORT, 'daily_operator_runs_are_append_only');
                END;
                CREATE TABLE IF NOT EXISTS native_creative_handoffs (
                    handoff_id TEXT PRIMARY KEY,
                    operator_run_id TEXT NOT NULL,
                    candidate_version_id TEXT,
                    video_job_id TEXT REFERENCES video_jobs(video_job_id),
                    parent_task_id TEXT,
                    child_task_id TEXT NOT NULL UNIQUE,
                    child_model TEXT NOT NULL,
                    child_reasoning_effort TEXT NOT NULL,
                    child_worktree TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    governed_input_hash TEXT NOT NULL,
                    result_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    cli_invocation_count INTEGER NOT NULL DEFAULT 0 CHECK(cli_invocation_count = 0),
                    sdk_api_invocation_count INTEGER NOT NULL DEFAULT 0 CHECK(sdk_api_invocation_count = 0),
                    nine_router_creative_invocation_count INTEGER NOT NULL DEFAULT 0 CHECK(nine_router_creative_invocation_count = 0),
                    public_write_authority INTEGER NOT NULL DEFAULT 0 CHECK(public_write_authority = 0),
                    v1_write_count INTEGER NOT NULL DEFAULT 0 CHECK(v1_write_count = 0),
                    platform_write_count INTEGER NOT NULL DEFAULT 0 CHECK(platform_write_count = 0)
                );
                CREATE TRIGGER IF NOT EXISTS native_creative_handoffs_immutable_update
                BEFORE UPDATE ON native_creative_handoffs BEGIN
                    SELECT RAISE(ABORT, 'native_creative_handoffs_are_append_only');
                END;
                CREATE TRIGGER IF NOT EXISTS native_creative_handoffs_immutable_delete
                BEFORE DELETE ON native_creative_handoffs BEGIN
                    SELECT RAISE(ABORT, 'native_creative_handoffs_are_append_only');
                END;
                CREATE TABLE IF NOT EXISTS creative_relay_requests (
                    request_id TEXT PRIMARY KEY,
                    idempotence_key TEXT NOT NULL UNIQUE,
                    operator_run_id TEXT NOT NULL,
                    candidate_version_id TEXT,
                    video_job_id TEXT REFERENCES video_jobs(video_job_id),
                    purpose TEXT NOT NULL,
                    governed_input_path TEXT NOT NULL,
                    governed_input_hash TEXT NOT NULL,
                    parent_task_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    zero_public_write_state TEXT NOT NULL,
                    public_write_authority INTEGER NOT NULL DEFAULT 0 CHECK(public_write_authority = 0),
                    v1_write_count INTEGER NOT NULL DEFAULT 0 CHECK(v1_write_count = 0),
                    platform_write_count INTEGER NOT NULL DEFAULT 0 CHECK(platform_write_count = 0)
                );
                CREATE TRIGGER IF NOT EXISTS creative_relay_requests_immutable_update
                BEFORE UPDATE ON creative_relay_requests BEGIN
                    SELECT RAISE(ABORT, 'creative_relay_requests_are_append_only');
                END;
                CREATE TRIGGER IF NOT EXISTS creative_relay_requests_immutable_delete
                BEFORE DELETE ON creative_relay_requests BEGIN
                    SELECT RAISE(ABORT, 'creative_relay_requests_are_append_only');
                END;
                CREATE TABLE IF NOT EXISTS creative_relay_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL REFERENCES creative_relay_requests(request_id),
                    sequence_no INTEGER NOT NULL,
                    state TEXT NOT NULL CHECK(state IN (
                        'READY_FOR_CREATIVE','CREATIVE_CLAIMED','CREATIVE_READY',
                        'HIGH_FINALIZATION','LOCAL_TERMINAL_RESULT'
                    )),
                    actor_role TEXT NOT NULL,
                    actor_task_id TEXT NOT NULL,
                    actor_run_id TEXT NOT NULL,
                    actor_thread_id TEXT NOT NULL,
                    actor_model TEXT NOT NULL,
                    actor_reasoning_effort TEXT NOT NULL,
                    actor_worktree TEXT NOT NULL,
                    input_hashes_json TEXT NOT NULL,
                    output_hashes_json TEXT NOT NULL,
                    result_path TEXT,
                    result_hash TEXT,
                    terminal_result TEXT,
                    occurred_at TEXT NOT NULL,
                    public_write_authority INTEGER NOT NULL DEFAULT 0 CHECK(public_write_authority = 0),
                    v1_write_count INTEGER NOT NULL DEFAULT 0 CHECK(v1_write_count = 0),
                    platform_write_count INTEGER NOT NULL DEFAULT 0 CHECK(platform_write_count = 0),
                    UNIQUE(request_id, sequence_no),
                    UNIQUE(request_id, state)
                );
                CREATE TRIGGER IF NOT EXISTS creative_relay_events_immutable_update
                BEFORE UPDATE ON creative_relay_events BEGIN
                    SELECT RAISE(ABORT, 'creative_relay_events_are_append_only');
                END;
                CREATE TRIGGER IF NOT EXISTS creative_relay_events_immutable_delete
                BEFORE DELETE ON creative_relay_events BEGIN
                    SELECT RAISE(ABORT, 'creative_relay_events_are_append_only');
                END;
                """
            )

    def record_candidate_decision(
        self,
        *,
        candidate_version_id: str,
        candidate_key: str,
        operator_run_id: str,
        candidate_source: Mapping[str, Any],
        qualification_inputs: Mapping[str, Any],
        decision: str,
        reason_codes: list[str],
        freshness: Mapping[str, Any],
        evidence_refs: list[str],
        source_v1_identity: Mapping[str, Any],
        trigger_packet_path: str | Path,
        trigger_packet_hash: str,
        source_content_hash: str,
        video_job_id: str | None = None,
        target_format: str = "SHORT_9_16_1080X1920_30FPS",
        priority: int = 100,
    ) -> dict[str, Any]:
        if decision not in CANDIDATE_DECISIONS:
            raise JobStoreError(f"candidate_decision_invalid:{decision}")
        for label, value in (
            ("candidate_version_id", candidate_version_id),
            ("candidate_key", candidate_key),
            ("operator_run_id", operator_run_id),
        ):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
                raise JobStoreError(f"{label}_invalid")
        for label, value in (
            ("trigger_packet_hash", trigger_packet_hash),
            ("source_content_hash", source_content_hash),
        ):
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise JobStoreError(f"{label}_invalid")
        if decision == "QUALIFIED" and not video_job_id:
            raise JobStoreError("qualified_candidate_video_job_id_required")
        if decision != "QUALIFIED" and video_job_id is not None:
            raise JobStoreError("nonqualified_candidate_cannot_create_job")

        created_job = False
        linked_job_id: str | None = None
        with self.transaction(immediate=True) as connection:
            existing_decision = connection.execute(
                "SELECT * FROM candidate_decisions WHERE candidate_version_id=?",
                (candidate_version_id,),
            ).fetchone()
            if existing_decision is not None:
                row = dict(existing_decision)
                row["job_created"] = False
                row["idempotent_replay"] = True
                return row

            if decision == "QUALIFIED":
                assert video_job_id is not None
                if not re.fullmatch(r"[A-Za-z0-9_.-]+", video_job_id):
                    raise JobStoreError("video_job_id_invalid")
                link = connection.execute(
                    "SELECT * FROM candidate_job_links WHERE candidate_key=?",
                    (candidate_key,),
                ).fetchone()
                if link is not None:
                    if str(link["source_content_hash"]) != source_content_hash:
                        raise JobStoreError("candidate_key_content_hash_conflict")
                    linked_job_id = str(link["video_job_id"])
                else:
                    existing_job = connection.execute(
                        "SELECT * FROM video_jobs WHERE video_job_id=?",
                        (video_job_id,),
                    ).fetchone()
                    if existing_job is not None:
                        raise JobStoreError("candidate_video_job_id_conflict")
                    connection.execute(
                        """
                        INSERT INTO video_jobs(
                            video_job_id,input_packet_path,input_packet_hash,target_format,
                            priority,created_at,state,public_write_authority
                        ) VALUES(?,?,?,?,?,?,?,0)
                        """,
                        (
                            video_job_id,
                            str(Path(trigger_packet_path).resolve()),
                            trigger_packet_hash,
                            target_format,
                            int(priority),
                            utc_now(),
                            "WAITING_GOVERNED_INPUT",
                        ),
                    )
                    connection.execute(
                        """
                        INSERT INTO candidate_job_links(
                            candidate_key,video_job_id,source_content_hash,
                            trigger_packet_hash,created_at,public_write_authority
                        ) VALUES(?,?,?,?,?,0)
                        """,
                        (
                            candidate_key,
                            video_job_id,
                            source_content_hash,
                            trigger_packet_hash,
                            utc_now(),
                        ),
                    )
                    linked_job_id = video_job_id
                    created_job = True

            connection.execute(
                """
                INSERT INTO candidate_decisions(
                    candidate_version_id,candidate_key,operator_run_id,candidate_source_json,
                    qualification_inputs_json,decision,reason_codes_json,freshness_json,
                    evidence_refs_json,source_v1_identity_json,trigger_packet_path,
                    trigger_packet_hash,video_job_id,created_at,zero_public_write_state,
                    public_write_authority,v1_write_count,platform_write_count
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,0,0)
                """,
                (
                    candidate_version_id,
                    candidate_key,
                    operator_run_id,
                    _json(dict(candidate_source)),
                    _json(dict(qualification_inputs)),
                    decision,
                    _json(sorted(set(reason_codes))),
                    _json(dict(freshness)),
                    _json(sorted(set(evidence_refs))),
                    _json(dict(source_v1_identity)),
                    str(Path(trigger_packet_path).resolve()),
                    trigger_packet_hash,
                    linked_job_id,
                    utc_now(),
                    "ZERO_VIDEO_PUBLIC_WRITE",
                ),
            )
            row = dict(
                connection.execute(
                    "SELECT * FROM candidate_decisions WHERE candidate_version_id=?",
                    (candidate_version_id,),
                ).fetchone()
            )
            row["job_created"] = created_job
            row["idempotent_replay"] = False
            return row

    def activate_candidate_job(
        self,
        *,
        video_job_id: str,
        governed_input_packet_path: str | Path,
        governed_input_packet_hash: str,
    ) -> dict[str, Any]:
        if not re.fullmatch(r"[0-9a-f]{64}", governed_input_packet_hash):
            raise JobStoreError("governed_input_packet_hash_invalid")
        resolved = str(Path(governed_input_packet_path).resolve())
        with self.transaction(immediate=True) as connection:
            link = connection.execute(
                "SELECT * FROM candidate_job_links WHERE video_job_id=?",
                (video_job_id,),
            ).fetchone()
            if link is None:
                raise JobStoreError("candidate_job_link_missing")
            job = connection.execute(
                "SELECT * FROM video_jobs WHERE video_job_id=?",
                (video_job_id,),
            ).fetchone()
            if job is None:
                raise JobStoreError(f"unknown_job:{video_job_id}")
            if str(job["state"]) == "QUEUED":
                if (
                    str(job["input_packet_path"]) != resolved
                    or str(job["input_packet_hash"]) != governed_input_packet_hash
                ):
                    raise JobStoreError("candidate_job_governed_input_conflict")
                return dict(job)
            if str(job["state"]) != "WAITING_GOVERNED_INPUT":
                raise JobStoreError(f"candidate_job_not_activatable:{job['state']}")
            connection.execute(
                """
                UPDATE video_jobs SET input_packet_path=?,input_packet_hash=?,state='QUEUED'
                WHERE video_job_id=? AND state='WAITING_GOVERNED_INPUT'
                  AND public_write_authority=0
                """,
                (resolved, governed_input_packet_hash, video_job_id),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM video_jobs WHERE video_job_id=?", (video_job_id,)
                ).fetchone()
            )

    def candidate_decisions(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM candidate_decisions ORDER BY created_at,candidate_version_id"
                )
            ]

    def record_operator_run(
        self,
        *,
        operator_run_id: str,
        summary: Mapping[str, Any],
        parent_model: str,
        parent_reasoning_effort: str,
        parent_task_id: str | None,
        v1_read_snapshot_hash: str,
        decision_count: int,
        qualified_count: int,
        created_job_count: int,
        result: str,
    ) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", operator_run_id):
            raise JobStoreError("operator_run_id_invalid")
        if not re.fullmatch(r"[0-9a-f]{64}", v1_read_snapshot_hash):
            raise JobStoreError("v1_read_snapshot_hash_invalid")
        payload = _json(dict(summary))
        with self.transaction(immediate=True) as connection:
            existing = connection.execute(
                "SELECT * FROM daily_operator_runs WHERE operator_run_id=?",
                (operator_run_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["summary_json"]) != payload:
                    raise JobStoreError("operator_run_id_conflict")
                return dict(existing)
            connection.execute(
                """
                INSERT INTO daily_operator_runs(
                    operator_run_id,completed_at,summary_json,parent_model,
                    parent_reasoning_effort,parent_task_id,v1_read_snapshot_hash,
                    decision_count,qualified_count,created_job_count,result,
                    public_write_authority,v1_write_count,platform_write_count
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,0,0,0)
                """,
                (
                    operator_run_id,
                    utc_now(),
                    payload,
                    parent_model,
                    parent_reasoning_effort,
                    parent_task_id,
                    v1_read_snapshot_hash,
                    int(decision_count),
                    int(qualified_count),
                    int(created_job_count),
                    result,
                ),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM daily_operator_runs WHERE operator_run_id=?",
                    (operator_run_id,),
                ).fetchone()
            )

    def record_native_handoff(
        self,
        *,
        handoff_id: str,
        operator_run_id: str,
        child_task_id: str,
        child_model: str,
        child_reasoning_effort: str,
        child_worktree: str,
        purpose: str,
        governed_input_hash: str,
        result_hash: str,
        parent_task_id: str | None = None,
        candidate_version_id: str | None = None,
        video_job_id: str | None = None,
    ) -> dict[str, Any]:
        for label, value in (("handoff_id", handoff_id), ("operator_run_id", operator_run_id)):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
                raise JobStoreError(f"{label}_invalid")
        if not child_task_id.strip() or not child_worktree.strip():
            raise JobStoreError("native_child_identity_required")
        if (child_model, child_reasoning_effort) != ("gpt-5.6-sol", "xhigh"):
            raise JobStoreError("native_child_model_or_reasoning_mismatch")
        for label, value in (
            ("governed_input_hash", governed_input_hash),
            ("result_hash", result_hash),
        ):
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise JobStoreError(f"{label}_invalid")
        with self.transaction(immediate=True) as connection:
            existing = connection.execute(
                "SELECT * FROM native_creative_handoffs WHERE handoff_id=? OR child_task_id=?",
                (handoff_id, child_task_id),
            ).fetchone()
            if existing is not None:
                return dict(existing)
            connection.execute(
                """
                INSERT INTO native_creative_handoffs(
                    handoff_id,operator_run_id,candidate_version_id,video_job_id,
                    parent_task_id,child_task_id,child_model,child_reasoning_effort,
                    child_worktree,purpose,governed_input_hash,result_hash,created_at,
                    cli_invocation_count,sdk_api_invocation_count,
                    nine_router_creative_invocation_count,public_write_authority,
                    v1_write_count,platform_write_count
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,0,0,0,0,0,0)
                """,
                (
                    handoff_id,
                    operator_run_id,
                    candidate_version_id,
                    video_job_id,
                    parent_task_id,
                    child_task_id,
                    child_model,
                    child_reasoning_effort,
                    child_worktree,
                    purpose,
                    governed_input_hash,
                    result_hash,
                    utc_now(),
                ),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM native_creative_handoffs WHERE handoff_id=?",
                    (handoff_id,),
                ).fetchone()
            )

    @staticmethod
    def _validate_relay_identity(label: str, value: str) -> None:
        if not value.strip():
            raise JobStoreError(f"{label}_required")

    @staticmethod
    def _relay_latest_event(
        connection: sqlite3.Connection, request_id: str
    ) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT * FROM creative_relay_events
            WHERE request_id=? ORDER BY sequence_no DESC LIMIT 1
            """,
            (request_id,),
        ).fetchone()

    @staticmethod
    def _relay_request_with_state(
        connection: sqlite3.Connection, request_id: str
    ) -> dict[str, Any]:
        request = connection.execute(
            "SELECT * FROM creative_relay_requests WHERE request_id=?", (request_id,)
        ).fetchone()
        if request is None:
            raise JobStoreError(f"creative_request_unknown:{request_id}")
        latest = V2JobStore._relay_latest_event(connection, request_id)
        if latest is None:
            raise JobStoreError("creative_request_missing_initial_event")
        value = dict(request)
        value["state"] = str(latest["state"])
        value["latest_event"] = dict(latest)
        return value

    def create_creative_request(
        self,
        *,
        request_id: str,
        idempotence_key: str,
        operator_run_id: str,
        purpose: str,
        governed_input_path: str | Path,
        governed_input_hash: str,
        parent_task_id: str,
        parent_run_id: str,
        parent_thread_id: str,
        parent_worktree: str,
        parent_model: str = "gpt-5.6-sol",
        parent_reasoning_effort: str = "high",
        candidate_version_id: str | None = None,
        video_job_id: str | None = None,
    ) -> dict[str, Any]:
        for label, value in (
            ("request_id", request_id),
            ("idempotence_key", idempotence_key),
            ("operator_run_id", operator_run_id),
        ):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
                raise JobStoreError(f"{label}_invalid")
        for label, value in (
            ("purpose", purpose),
            ("parent_task_id", parent_task_id),
            ("parent_run_id", parent_run_id),
            ("parent_thread_id", parent_thread_id),
            ("parent_worktree", parent_worktree),
        ):
            self._validate_relay_identity(label, value)
        if (parent_model, parent_reasoning_effort) != ("gpt-5.6-sol", "high"):
            raise JobStoreError("creative_request_parent_model_or_reasoning_mismatch")
        if not re.fullmatch(r"[0-9a-f]{64}", governed_input_hash):
            raise JobStoreError("governed_input_hash_invalid")
        governed_path = str(Path(governed_input_path).resolve())
        expected = {
            "idempotence_key": idempotence_key,
            "operator_run_id": operator_run_id,
            "candidate_version_id": candidate_version_id,
            "video_job_id": video_job_id,
            "purpose": purpose,
            "governed_input_path": governed_path,
            "governed_input_hash": governed_input_hash,
            "parent_task_id": parent_task_id,
        }
        with self.transaction(immediate=True) as connection:
            if connection.execute(
                "SELECT 1 FROM daily_operator_runs WHERE operator_run_id=?",
                (operator_run_id,),
            ).fetchone() is None:
                raise JobStoreError("creative_request_operator_run_missing")
            existing = connection.execute(
                """
                SELECT * FROM creative_relay_requests
                WHERE request_id=? OR idempotence_key=?
                """,
                (request_id, idempotence_key),
            ).fetchone()
            if existing is not None:
                existing_value = dict(existing)
                for key, value in expected.items():
                    if existing_value[key] != value:
                        raise JobStoreError("creative_request_idempotence_conflict")
                result = self._relay_request_with_state(
                    connection, str(existing_value["request_id"])
                )
                result["idempotent_replay"] = True
                return result
            if video_job_id is not None and connection.execute(
                "SELECT 1 FROM video_jobs WHERE video_job_id=?", (video_job_id,)
            ).fetchone() is None:
                raise JobStoreError("creative_request_video_job_missing")
            connection.execute(
                """
                INSERT INTO creative_relay_requests(
                    request_id,idempotence_key,operator_run_id,candidate_version_id,
                    video_job_id,purpose,governed_input_path,governed_input_hash,
                    parent_task_id,created_at,zero_public_write_state,
                    public_write_authority,v1_write_count,platform_write_count
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,0,0,0)
                """,
                (
                    request_id,
                    idempotence_key,
                    operator_run_id,
                    candidate_version_id,
                    video_job_id,
                    purpose,
                    governed_path,
                    governed_input_hash,
                    parent_task_id,
                    utc_now(),
                    "ZERO_VIDEO_PUBLIC_WRITE",
                ),
            )
            connection.execute(
                """
                INSERT INTO creative_relay_events(
                    request_id,sequence_no,state,actor_role,actor_task_id,
                    actor_run_id,actor_thread_id,actor_model,actor_reasoning_effort,
                    actor_worktree,input_hashes_json,output_hashes_json,
                    occurred_at,public_write_authority,v1_write_count,platform_write_count
                ) VALUES(?,1,'READY_FOR_CREATIVE','HIGH_DAILY_OPERATOR',?,?,?,?,?,?,?,'{}',?,0,0,0)
                """,
                (
                    request_id,
                    parent_task_id,
                    parent_run_id,
                    parent_thread_id,
                    parent_model,
                    parent_reasoning_effort,
                    parent_worktree,
                    _json({"governed_input_hash": governed_input_hash}),
                    utc_now(),
                ),
            )
            result = self._relay_request_with_state(connection, request_id)
            result["idempotent_replay"] = False
            return result

    def claim_creative_request(
        self,
        *,
        worker_task_id: str,
        worker_run_id: str,
        worker_thread_id: str,
        worker_worktree: str,
        worker_model: str,
        worker_reasoning_effort: str,
        request_id: str | None = None,
    ) -> dict[str, Any] | None:
        for label, value in (
            ("worker_task_id", worker_task_id),
            ("worker_run_id", worker_run_id),
            ("worker_thread_id", worker_thread_id),
            ("worker_worktree", worker_worktree),
        ):
            self._validate_relay_identity(label, value)
        if (worker_model, worker_reasoning_effort) != ("gpt-5.6-sol", "xhigh"):
            raise JobStoreError("creative_worker_model_or_reasoning_mismatch")
        with self.transaction(immediate=True) as connection:
            if request_id is not None:
                request = connection.execute(
                    "SELECT * FROM creative_relay_requests WHERE request_id=?", (request_id,)
                ).fetchone()
            else:
                request = connection.execute(
                    """
                    SELECT r.* FROM creative_relay_requests r
                    JOIN creative_relay_events e ON e.request_id=r.request_id
                    WHERE e.sequence_no=(
                        SELECT MAX(e2.sequence_no) FROM creative_relay_events e2
                        WHERE e2.request_id=r.request_id
                    ) AND e.state='READY_FOR_CREATIVE'
                    ORDER BY r.created_at,r.request_id LIMIT 1
                    """
                ).fetchone()
            if request is None:
                return None
            selected_id = str(request["request_id"])
            latest = self._relay_latest_event(connection, selected_id)
            assert latest is not None
            if str(latest["state"]) != "READY_FOR_CREATIVE":
                claim = connection.execute(
                    """
                    SELECT * FROM creative_relay_events
                    WHERE request_id=? AND state='CREATIVE_CLAIMED'
                    """,
                    (selected_id,),
                ).fetchone()
                if claim is not None and all(
                    str(claim[key]) == expected
                    for key, expected in (
                        ("actor_task_id", worker_task_id),
                        ("actor_run_id", worker_run_id),
                        ("actor_thread_id", worker_thread_id),
                    )
                ):
                    result = self._relay_request_with_state(connection, selected_id)
                    result["idempotent_replay"] = True
                    return result
                raise JobStoreError(f"creative_request_not_claimable:{latest['state']}")
            connection.execute(
                """
                INSERT INTO creative_relay_events(
                    request_id,sequence_no,state,actor_role,actor_task_id,
                    actor_run_id,actor_thread_id,actor_model,actor_reasoning_effort,
                    actor_worktree,input_hashes_json,output_hashes_json,
                    occurred_at,public_write_authority,v1_write_count,platform_write_count
                ) VALUES(?,2,'CREATIVE_CLAIMED','XHIGH_CREATIVE_WORKER',?,?,?,?,?,?,?,'{}',?,0,0,0)
                """,
                (
                    selected_id,
                    worker_task_id,
                    worker_run_id,
                    worker_thread_id,
                    worker_model,
                    worker_reasoning_effort,
                    worker_worktree,
                    _json({"governed_input_hash": str(request["governed_input_hash"])}),
                    utc_now(),
                ),
            )
            result = self._relay_request_with_state(connection, selected_id)
            result["idempotent_replay"] = False
            return result

    def record_creative_result(
        self,
        *,
        request_id: str,
        worker_task_id: str,
        worker_run_id: str,
        worker_thread_id: str,
        result_path: str | Path,
        result_hash: str,
        output_hashes: Mapping[str, str],
    ) -> dict[str, Any]:
        if not re.fullmatch(r"[0-9a-f]{64}", result_hash):
            raise JobStoreError("creative_result_hash_invalid")
        resolved_result = str(Path(result_path).resolve())
        output_payload = _json(dict(output_hashes))
        with self.transaction(immediate=True) as connection:
            request = connection.execute(
                "SELECT * FROM creative_relay_requests WHERE request_id=?", (request_id,)
            ).fetchone()
            if request is None:
                raise JobStoreError(f"creative_request_unknown:{request_id}")
            claim = connection.execute(
                """
                SELECT * FROM creative_relay_events
                WHERE request_id=? AND state='CREATIVE_CLAIMED'
                """,
                (request_id,),
            ).fetchone()
            if claim is None:
                raise JobStoreError("creative_request_not_claimed")
            for key, expected in (
                ("actor_task_id", worker_task_id),
                ("actor_run_id", worker_run_id),
                ("actor_thread_id", worker_thread_id),
            ):
                if str(claim[key]) != expected:
                    raise JobStoreError("creative_result_claim_identity_mismatch")
            ready = connection.execute(
                """
                SELECT * FROM creative_relay_events
                WHERE request_id=? AND state='CREATIVE_READY'
                """,
                (request_id,),
            ).fetchone()
            if ready is not None:
                if (
                    str(ready["result_path"]) != resolved_result
                    or str(ready["result_hash"]) != result_hash
                    or str(ready["output_hashes_json"]) != output_payload
                ):
                    raise JobStoreError("creative_result_replay_conflict")
                result = self._relay_request_with_state(connection, request_id)
                result["idempotent_replay"] = True
                return result
            latest = self._relay_latest_event(connection, request_id)
            assert latest is not None
            if str(latest["state"]) != "CREATIVE_CLAIMED":
                raise JobStoreError(f"creative_result_not_recordable:{latest['state']}")
            connection.execute(
                """
                INSERT INTO creative_relay_events(
                    request_id,sequence_no,state,actor_role,actor_task_id,
                    actor_run_id,actor_thread_id,actor_model,actor_reasoning_effort,
                    actor_worktree,input_hashes_json,output_hashes_json,result_path,
                    result_hash,occurred_at,public_write_authority,v1_write_count,
                    platform_write_count
                ) VALUES(?,3,'CREATIVE_READY','XHIGH_CREATIVE_WORKER',?,?,?,?,?,?,?,?,?,?,?,0,0,0)
                """,
                (
                    request_id,
                    worker_task_id,
                    worker_run_id,
                    worker_thread_id,
                    str(claim["actor_model"]),
                    str(claim["actor_reasoning_effort"]),
                    str(claim["actor_worktree"]),
                    _json({"governed_input_hash": str(request["governed_input_hash"])}),
                    output_payload,
                    resolved_result,
                    result_hash,
                    utc_now(),
                ),
            )
            result = self._relay_request_with_state(connection, request_id)
            result["idempotent_replay"] = False
            return result

    def finalize_creative_request(
        self,
        *,
        request_id: str,
        finalizer_task_id: str,
        finalizer_run_id: str,
        finalizer_thread_id: str,
        finalizer_worktree: str,
        finalizer_model: str,
        finalizer_reasoning_effort: str,
        output_hashes: Mapping[str, str],
        terminal_result: str,
    ) -> dict[str, Any]:
        for label, value in (
            ("finalizer_task_id", finalizer_task_id),
            ("finalizer_run_id", finalizer_run_id),
            ("finalizer_thread_id", finalizer_thread_id),
            ("finalizer_worktree", finalizer_worktree),
            ("terminal_result", terminal_result),
        ):
            self._validate_relay_identity(label, value)
        if (finalizer_model, finalizer_reasoning_effort) != ("gpt-5.6-sol", "high"):
            raise JobStoreError("creative_finalizer_model_or_reasoning_mismatch")
        output_payload = _json(dict(output_hashes))
        with self.transaction(immediate=True) as connection:
            request = connection.execute(
                "SELECT * FROM creative_relay_requests WHERE request_id=?", (request_id,)
            ).fetchone()
            if request is None:
                raise JobStoreError(f"creative_request_unknown:{request_id}")
            creative_ready = connection.execute(
                """
                SELECT * FROM creative_relay_events
                WHERE request_id=? AND state='CREATIVE_READY'
                """,
                (request_id,),
            ).fetchone()
            if creative_ready is None:
                raise JobStoreError("creative_result_not_ready")
            terminal = connection.execute(
                """
                SELECT * FROM creative_relay_events
                WHERE request_id=? AND state='LOCAL_TERMINAL_RESULT'
                """,
                (request_id,),
            ).fetchone()
            if terminal is not None:
                if (
                    str(terminal["terminal_result"]) != terminal_result
                    or str(terminal["output_hashes_json"]) != output_payload
                ):
                    raise JobStoreError("creative_finalization_replay_conflict")
                result = self._relay_request_with_state(connection, request_id)
                result["idempotent_replay"] = True
                return result
            latest = self._relay_latest_event(connection, request_id)
            assert latest is not None
            if str(latest["state"]) != "CREATIVE_READY":
                raise JobStoreError(f"creative_request_not_finalizable:{latest['state']}")
            identity = (
                finalizer_task_id,
                finalizer_run_id,
                finalizer_thread_id,
                finalizer_model,
                finalizer_reasoning_effort,
                finalizer_worktree,
            )
            connection.execute(
                """
                INSERT INTO creative_relay_events(
                    request_id,sequence_no,state,actor_role,actor_task_id,
                    actor_run_id,actor_thread_id,actor_model,actor_reasoning_effort,
                    actor_worktree,input_hashes_json,output_hashes_json,
                    occurred_at,public_write_authority,v1_write_count,platform_write_count
                ) VALUES(?,4,'HIGH_FINALIZATION','HIGH_FINALIZER',?,?,?,?,?,?,?,?,?,0,0,0)
                """,
                (
                    request_id,
                    *identity,
                    _json({"creative_result_hash": str(creative_ready["result_hash"])}),
                    output_payload,
                    utc_now(),
                ),
            )
            connection.execute(
                """
                INSERT INTO creative_relay_events(
                    request_id,sequence_no,state,actor_role,actor_task_id,
                    actor_run_id,actor_thread_id,actor_model,actor_reasoning_effort,
                    actor_worktree,input_hashes_json,output_hashes_json,
                    terminal_result,occurred_at,public_write_authority,v1_write_count,
                    platform_write_count
                ) VALUES(?,5,'LOCAL_TERMINAL_RESULT','HIGH_FINALIZER',?,?,?,?,?,?,?,?,?,?,0,0,0)
                """,
                (
                    request_id,
                    *identity,
                    _json({"creative_result_hash": str(creative_ready["result_hash"])}),
                    output_payload,
                    terminal_result,
                    utc_now(),
                ),
            )
            result = self._relay_request_with_state(connection, request_id)
            result["idempotent_replay"] = False
            return result

    def creative_relay_requests(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            request_ids = [
                str(row["request_id"])
                for row in connection.execute(
                    "SELECT request_id FROM creative_relay_requests ORDER BY created_at,request_id"
                )
            ]
            return [self._relay_request_with_state(connection, value) for value in request_ids]

    def creative_relay_events(self, request_id: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as connection:
            if request_id is None:
                rows = connection.execute(
                    "SELECT * FROM creative_relay_events ORDER BY event_id"
                )
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM creative_relay_events
                    WHERE request_id=? ORDER BY sequence_no
                    """,
                    (request_id,),
                )
            return [dict(row) for row in rows]

    def operator_runs(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM daily_operator_runs ORDER BY completed_at,operator_run_id"
                )
            ]

    def native_handoffs(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM native_creative_handoffs ORDER BY created_at,handoff_id"
                )
            ]

    def daily_review_queue(self) -> dict[str, Any]:
        with self.connect() as connection:
            rows = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT j.video_job_id,j.state,j.terminal_result,j.created_at,
                           l.candidate_key,l.source_content_hash,
                           d.candidate_version_id,d.decision,d.operator_run_id
                    FROM video_jobs j
                    JOIN candidate_job_links l ON l.video_job_id=j.video_job_id
                    LEFT JOIN candidate_decisions d ON d.video_job_id=j.video_job_id
                    ORDER BY j.created_at,j.video_job_id,d.created_at DESC
                    """
                )
            ]
            relay_states = [
                str(row["state"])
                for row in connection.execute(
                    """
                    SELECT e.state FROM creative_relay_requests r
                    JOIN creative_relay_events e ON e.request_id=r.request_id
                    WHERE e.sequence_no=(
                        SELECT MAX(e2.sequence_no) FROM creative_relay_events e2
                        WHERE e2.request_id=r.request_id
                    )
                    ORDER BY r.created_at,r.request_id
                    """
                )
            ]
        deduped: dict[str, dict[str, Any]] = {}
        for row in rows:
            deduped.setdefault(str(row["video_job_id"]), row)
        items = list(deduped.values())
        return {
            "schema": "contentops.v2.daily_operator_review_queue.v1",
            "items": items,
            "item_count": len(items),
            "owner_review_ready_count": sum(
                str(item["state"]) == "OWNER_REVIEW_READY" for item in items
            ),
            "waiting_governed_input_count": sum(
                str(item["state"]) == "WAITING_GOVERNED_INPUT" for item in items
            ),
            "creative_relay_request_count": len(relay_states),
            "ready_for_creative_count": relay_states.count("READY_FOR_CREATIVE"),
            "creative_claimed_count": relay_states.count("CREATIVE_CLAIMED"),
            "creative_ready_count": relay_states.count("CREATIVE_READY"),
            "high_finalization_count": relay_states.count("HIGH_FINALIZATION"),
            "local_terminal_result_count": relay_states.count("LOCAL_TERMINAL_RESULT"),
            "public_write_authority": False,
        }

    def seed_job(
        self,
        *,
        video_job_id: str,
        input_packet_path: str | Path,
        input_packet_hash: str,
        target_format: str,
        priority: int = 100,
    ) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", video_job_id):
            raise JobStoreError("video_job_id_invalid")
        if not re.fullmatch(r"[0-9a-f]{64}", input_packet_hash):
            raise JobStoreError("input_packet_hash_invalid")
        if not target_format:
            raise JobStoreError("target_format_required")
        with self.transaction(immediate=True) as connection:
            existing = connection.execute(
                "SELECT * FROM video_jobs WHERE input_packet_hash=? AND target_format=?",
                (input_packet_hash, target_format),
            ).fetchone()
            if existing is not None:
                return dict(existing)
            connection.execute(
                """
                INSERT INTO video_jobs(
                    video_job_id,input_packet_path,input_packet_hash,target_format,
                    priority,created_at,state,public_write_authority
                ) VALUES(?,?,?,?,?,?,?,0)
                """,
                (
                    video_job_id,
                    str(Path(input_packet_path).resolve()),
                    input_packet_hash,
                    target_format,
                    int(priority),
                    utc_now(),
                    "QUEUED",
                ),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM video_jobs WHERE video_job_id=?", (video_job_id,)
                ).fetchone()
            )

    def claim_next(
        self,
        *,
        worker_id: str,
        implementation_head: str,
        lease_seconds: int = 900,
        proof_run_started_at: str | None = None,
    ) -> dict[str, Any] | None:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(seconds=max(1, int(lease_seconds)))
        ).isoformat().replace("+00:00", "Z")
        now = utc_now()
        with self.transaction(immediate=True) as connection:
            job = connection.execute(
                """
                SELECT * FROM video_jobs
                WHERE state IN ('QUEUED','RUNNING')
                  AND (claimed_by IS NULL OR claim_timestamp < ?)
                  AND public_write_authority = 0
                ORDER BY priority DESC, created_at ASC LIMIT 1
                """,
                (cutoff,),
            ).fetchone()
            if job is None:
                return None
            active = connection.execute(
                "SELECT * FROM job_runs WHERE video_job_id=? AND status='ACTIVE'",
                (job["video_job_id"],),
            ).fetchone()
            if active is None:
                run_id = f"run_{uuid.uuid4().hex}"
                connection.execute(
                    """
                    INSERT INTO job_runs(
                        run_id,video_job_id,status,started_at,implementation_head,
                        proof_run_started_at,public_write_authority
                    ) VALUES(?,?,?,?,?,?,0)
                    """,
                    (
                        run_id,
                        job["video_job_id"],
                        "ACTIVE",
                        now,
                        implementation_head,
                        proof_run_started_at,
                    ),
                )
                resume_count = int(job["resume_count"])
            else:
                run_id = str(active["run_id"])
                resume_count = int(job["resume_count"]) + 1
            updated = connection.execute(
                """
                UPDATE video_jobs
                SET claimed_by=?,claim_timestamp=?,run_id=?,state='RUNNING',resume_count=?
                WHERE video_job_id=?
                  AND (claimed_by IS NULL OR claim_timestamp < ?)
                  AND public_write_authority=0
                """,
                (
                    worker_id,
                    now,
                    run_id,
                    resume_count,
                    job["video_job_id"],
                    cutoff,
                ),
            )
            if updated.rowcount != 1:
                return None
            claimed = dict(
                connection.execute(
                    "SELECT * FROM video_jobs WHERE video_job_id=?", (job["video_job_id"],)
                ).fetchone()
            )
            claimed["run_id"] = run_id
            return claimed

    def append_event(
        self,
        *,
        video_job_id: str,
        run_id: str,
        stage: str,
        input_hashes: Mapping[str, str],
        output_hashes: Mapping[str, str],
        artifacts: list[Mapping[str, Any]],
        role_tool_identity: str,
        model_provenance: Mapping[str, Any] | None,
        wall_time_seconds: float,
        safe_usage: Mapping[str, Any] | None,
        result: str,
        retry_state: Mapping[str, Any] | None,
        next_legal_stage: str | None,
        state_pointer: str | None = None,
        terminal_result: str | None = None,
    ) -> int:
        with self.transaction(immediate=True) as connection:
            job = connection.execute(
                "SELECT public_write_authority FROM video_jobs WHERE video_job_id=?",
                (video_job_id,),
            ).fetchone()
            if job is None:
                raise JobStoreError(f"unknown_job:{video_job_id}")
            if int(job["public_write_authority"]) != 0:
                raise JobStoreError("public_write_authority_must_remain_false")
            cursor = connection.execute(
                """
                INSERT INTO stage_events(
                    video_job_id,run_id,stage,stage_version,occurred_at,input_hashes_json,
                    output_hashes_json,artifact_records_json,role_tool_identity,
                    model_provenance_json,wall_time_seconds,safe_usage_json,result,
                    retry_state_json,next_legal_stage,public_write_authority
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)
                """,
                (
                    video_job_id,
                    run_id,
                    stage,
                    "v1",
                    utc_now(),
                    _json(dict(input_hashes)),
                    _json(dict(output_hashes)),
                    _json([dict(item) for item in artifacts]),
                    role_tool_identity,
                    _json(dict(model_provenance or {})),
                    round(max(0.0, float(wall_time_seconds)), 6),
                    _json(dict(safe_usage or {})),
                    result,
                    _json(dict(retry_state or {})),
                    next_legal_stage,
                ),
            )
            if state_pointer is not None or terminal_result is not None:
                durable_state = (
                    state_pointer
                    if state_pointer in TERMINAL_STATES
                    else "RUNNING"
                )
                connection.execute(
                    """
                    UPDATE video_jobs
                    SET last_valid_checkpoint=COALESCE(?,last_valid_checkpoint),
                        state=COALESCE(?,state),terminal_result=COALESCE(?,terminal_result)
                    WHERE video_job_id=?
                    """,
                    (state_pointer, durable_state, terminal_result, video_job_id),
                )
            return int(cursor.lastrowid)

    def events(self, video_job_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM stage_events WHERE video_job_id=? ORDER BY event_id",
                    (video_job_id,),
                )
            ]

    def latest_success_by_stage(self, video_job_id: str) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for event in self.events(video_job_id):
            if event["result"].startswith("PASS"):
                result[event["stage"]] = event
            elif event["result"].startswith("INVALIDATED"):
                result.pop(event["stage"], None)
        return result

    def job(self, video_job_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM video_jobs WHERE video_job_id=?", (video_job_id,)
            ).fetchone()
            if row is None:
                raise JobStoreError(f"unknown_job:{video_job_id}")
            return dict(row)

    def jobs(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM video_jobs ORDER BY created_at, video_job_id"
                )
            ]

    def soak_summary(self) -> dict[str, Any]:
        jobs = self.jobs()
        with self.connect() as connection:
            runs = [dict(row) for row in connection.execute("SELECT * FROM job_runs")]
            events = [dict(row) for row in connection.execute("SELECT * FROM stage_events")]
        state_counts: dict[str, int] = {}
        for item in jobs:
            state = str(item["state"])
            state_counts[state] = state_counts.get(state, 0) + 1
        xhigh_executions = 0
        external_media_cost = 0.0
        exposed_model_cost = 0.0
        model_cost_exposed = False
        for event in events:
            provenance = json.loads(str(event["model_provenance_json"]))
            if provenance.get("declared_creative_reasoning_effort") == "xhigh":
                xhigh_executions += 1
            usage = json.loads(str(event["safe_usage_json"]))
            external_media_cost += float(usage.get("external_media_cost_usd") or 0.0)
            if usage.get("model_cost_usd") is not None:
                exposed_model_cost += float(usage["model_cost_usd"])
                model_cost_exposed = True
        public_write_values = [
            int(item["public_write_authority"]) for item in [*jobs, *runs, *events]
        ]
        if any(public_write_values):
            raise JobStoreError("soak_summary_public_write_authority_violation")
        started_jobs = sum(item.get("run_id") is not None for item in jobs)
        completed = int(state_counts.get("OWNER_REVIEW_READY", 0))
        quarantined = int(state_counts.get("QUARANTINED", 0))
        return {
            "schema": "contentops.v2.unattended_production_soak_summary.v1",
            "job_count": len(jobs),
            "started_job_count": started_jobs,
            "owner_review_ready_count": completed,
            "quarantined_job_count": quarantined,
            "queued_or_running_count": int(state_counts.get("QUEUED", 0))
            + int(state_counts.get("RUNNING", 0)),
            "all_started_jobs_succeeded": started_jobs > 0 and completed == started_jobs,
            "state_counts": state_counts,
            "run_count": len(runs),
            "resume_count": sum(int(item["resume_count"]) for item in jobs),
            "bounded_xhigh_creative_execution_count": xhigh_executions,
            "total_stage_wall_time_seconds": round(
                sum(float(event["wall_time_seconds"]) for event in events), 6
            ),
            "external_media_cost_usd": round(external_media_cost, 8),
            "model_cost_usd": round(exposed_model_cost, 8)
            if model_cost_exposed
            else None,
            "model_cost_exposed": model_cost_exposed,
            "manual_source_edits_after_start": sum(
                int(item["manual_source_edits_after_start"]) for item in runs
            ),
            "manual_media_edits_after_start": sum(
                int(item["manual_media_edits_after_start"]) for item in runs
            ),
            "manual_checkpoint_edits": sum(
                int(item["manual_checkpoint_edits"]) for item in runs
            ),
            "public_write_authority": False,
            "video_job_ids": [str(item["video_job_id"]) for item in jobs],
            "run_ids": [str(item["run_id"]) for item in runs],
        }

    def finalize(
        self, *, video_job_id: str, run_id: str, result: str, state: str
    ) -> None:
        if state not in TERMINAL_STATES:
            raise JobStoreError(f"not_terminal:{state}")
        now = utc_now()
        with self.transaction(immediate=True) as connection:
            connection.execute(
                """
                UPDATE video_jobs SET state=?,terminal_result=?,claimed_by=NULL,
                    claim_timestamp=NULL,last_valid_checkpoint=?
                WHERE video_job_id=? AND run_id=? AND public_write_authority=0
                """,
                (state, result, state, video_job_id, run_id),
            )
            connection.execute(
                "UPDATE job_runs SET status=?,completed_at=? WHERE run_id=? AND status='ACTIVE'",
                (state, now, run_id),
            )

    def release_claim(self, *, video_job_id: str, worker_id: str) -> None:
        with self.transaction(immediate=True) as connection:
            connection.execute(
                """
                UPDATE video_jobs SET claimed_by=NULL,claim_timestamp=NULL
                WHERE video_job_id=? AND claimed_by=? AND state='RUNNING'
                """,
                (video_job_id, worker_id),
            )

    def quarantine(
        self, *, video_job_id: str, run_id: str, reason: str
    ) -> None:
        self.finalize(
            video_job_id=video_job_id,
            run_id=run_id,
            result=reason,
            state="QUARANTINED",
        )
