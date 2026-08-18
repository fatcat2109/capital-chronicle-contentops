from __future__ import annotations

import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping


SCHEMA_VERSION = "contentops.v2.unattended_job_store.v1"
TERMINAL_STATES = frozenset({"OWNER_REVIEW_READY", "TERMINAL", "QUARANTINED"})


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
                """
            )

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
