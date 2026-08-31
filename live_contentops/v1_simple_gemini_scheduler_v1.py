"""Lightweight local scheduler for the current Simple-Gemini V1 operation.

The scheduler owns no newsroom, candidate frontier, publication database, transport, or second
public-write path. It reuses the owner-locked four-window calendar, production-day accounting,
canonical reconciled published-memory read model, and exact one-article production orchestrator
operation. The Simple semantic operation remains zero-write. When the production composition
injects the existing publication handoff, a qualified slot is delegated to the sole existing
``DurablePublicationCoordinator`` and its canonical store/recovery authority.

Durable JSON checkpoints are execution receipts only. They never become publication authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence
from uuid import uuid4

from live_contentops.daily_app_supervisor_v1 import (
    EditorialWindowPolicy,
    SIMPLE_GEMINI_RUNTIME,
    build_bootstrap_editorial_window_policy,
    owner_locked_editorial_opportunities,
)
from live_contentops.newsroom_production_day_v1 import (
    LIVE_OUTPUT_COUNT_BASIS,
    bounded_deficit_work_needed,
    count_reconciled_published_articles,
    load_qualified_article_records,
    newsroom_production_day_id,
    qualified_records_as_published_memory,
)
from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator
from live_contentops.published_corpus_read_model_v1 import (
    load_canonical_published_memory_read_only,
)
from live_contentops.source_route_health_v1 import (
    load_source_route_health_snapshot_read_only,
    persist_source_route_health_snapshot,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    MAX_LOGICAL_MODEL_INVOCATIONS,
    MAX_REVISION_ROUNDS,
    MAX_SELECTION_CANDIDATES,
    MAX_SOURCE_REQUESTS,
)

SCHEMA_VERSION = "contentops.v1_simple_gemini_local_scheduler.v1"
WINDOW_CHECKPOINT_SCHEMA_VERSION = "contentops.v1_simple_gemini_scheduler_window.v1"
SLOT_CHECKPOINT_SCHEMA_VERSION = "contentops.v1_simple_gemini_scheduler_slot.v1"
MEMORY_ACCESS_SCHEMA_VERSION = "contentops.v1_simple_scheduler_memory_access.v1"
STATE_DIRECTORY_NAME = "simple_gemini_scheduler_state_v1"
TRIGGER_SCHEDULED = "SCHEDULED"
ROUTINE_EDITORIAL_OWNER = SIMPLE_GEMINI_RUNTIME
TERMINAL_SLOT_STATES = frozenset(
    {"PUBLISHED", "QUALIFIED", "ABSTAINED", "BLOCKED", "SAFETY_BLOCKED"}
)
PUBLICATION_NONTERMINAL_STATES = frozenset(
    {"PUBLICATION_PENDING", "PUBLICATION_RECOVERY_REQUIRED", "PUBLICATION_BLOCKED"}
)

SimpleOperation = Callable[..., Mapping[str, Any]]
PublishedMemoryLoader = Callable[[], tuple[Sequence[Any], Mapping[str, Any]]]


class SimpleGeminiSchedulerSafetyError(RuntimeError):
    """A zero-write semantic or per-article ceiling invariant was violated."""

    def __init__(self, blockers: Sequence[str]) -> None:
        self.blockers = tuple(sorted({str(value) for value in blockers if str(value)}))
        super().__init__(
            "simple_gemini_scheduler_safety_blocked:" + ",".join(self.blockers)
        )


class SimpleGeminiSchedulerCheckpointError(RuntimeError):
    """A present checkpoint is invalid and therefore grants no re-execution authority."""


class _NonBlockingFileLock:
    """One-byte OS lock released automatically when a process exits or crashes."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle: Any = None
        self._windows = os.name == "nt"

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if self._windows:
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError):
            handle.close()
            return False
        self._handle = handle
        return True

    def release(self) -> None:
        handle = self._handle
        if handle is None:
            return
        try:
            handle.seek(0)
            if self._windows:
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
            self._handle = None

    def __del__(self) -> None:
        try:
            self.release()
        except Exception:
            pass


def _iso_utc(value: datetime | str) -> str:
    parsed = (
        value
        if isinstance(value, datetime)
        else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    )
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: datetime | str) -> datetime:
    return datetime.fromisoformat(_iso_utc(value).replace("Z", "+00:00"))


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _write_checkpoint(path: Path, payload: Mapping[str, Any]) -> None:
    value = {
        key: item for key, item in dict(payload).items() if key != "checkpoint_sha256"
    }
    value["checkpoint_sha256"] = _logical_hash(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _load_checkpoint(path: Path, *, schema_version: str) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = _read_json(path)
    expected = str(value.get("checkpoint_sha256") or "")
    material = {key: item for key, item in value.items() if key != "checkpoint_sha256"}
    if value.get("schema_version") != schema_version or expected != _logical_hash(
        material
    ):
        raise SimpleGeminiSchedulerCheckpointError(
            f"simple_gemini_scheduler_checkpoint_invalid:{path}"
        )
    return value


def simple_gemini_slot_id(
    *, production_day_id: str, window_id: str, slot_ordinal: int
) -> str:
    """Return the stable production-day/window/ordinal identity for one article operation."""
    if int(slot_ordinal) < 1:
        raise ValueError("simple_gemini_slot_ordinal_invalid")
    identity = {
        "newsroom_production_day_id": str(production_day_id),
        "window_id": str(window_id),
        "slot_ordinal": int(slot_ordinal),
    }
    return "simple-gemini-slot-" + _logical_hash(identity)[:32]


def _memory_identity(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(
            value.get("article_identity")
            or value.get("story_identity")
            or value.get("content_hash")
            or ""
        )
    return str(
        getattr(value, "article_identity", "")
        or getattr(value, "story_identity", "")
        or getattr(value, "content_hash", "")
        or ""
    )


def _dedupe_memory(values: Sequence[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        identity = _memory_identity(value)
        if not identity or identity in seen:
            continue
        seen.add(identity)
        result.append(value)
    return result


def _result_safety_blockers(result: Mapping[str, Any]) -> list[str]:
    """Validate only the zero-write Simple semantic result, never coordinator output."""
    blockers: list[str] = []
    if int(result.get("candidate_count") or 0) > MAX_SELECTION_CANDIDATES:
        blockers.append("selection_candidate_ceiling_exceeded")
    if (
        int(result.get("candidate_limit") or MAX_SELECTION_CANDIDATES)
        != MAX_SELECTION_CANDIDATES
    ):
        blockers.append("selection_candidate_ceiling_changed")
    if int(result.get("source_request_count") or 0) > MAX_SOURCE_REQUESTS:
        blockers.append("source_get_ceiling_exceeded")
    if (
        int(result.get("logical_model_invocation_count") or 0)
        > MAX_LOGICAL_MODEL_INVOCATIONS
    ):
        blockers.append("flash_logical_call_ceiling_exceeded")
    if int(result.get("provider_attempt_count") or 0) > MAX_LOGICAL_MODEL_INVOCATIONS:
        blockers.append("provider_attempt_ceiling_exceeded")
    if result.get("revision_performed") not in {None, False, True}:
        blockers.append("revision_state_invalid")
    if int(bool(result.get("revision_performed"))) > MAX_REVISION_ROUNDS:
        blockers.append("revision_ceiling_exceeded")
    if int(result.get("codex_runtime_model_call_count") or 0) != 0:
        blockers.append("codex_runtime_call_detected")
    if result.get("public_write_performed") is not False:
        blockers.append("public_write_detected")
    if int(result.get("provider_publication_writes") or 0) != 0:
        blockers.append("provider_publication_write_detected")
    if int(result.get("unknown_write_count") or 0) != 0:
        blockers.append("unknown_write_detected")
    if result.get("unknown_write_detected") is True:
        blockers.append("unknown_write_detected")
    return blockers


def _publication_fields(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "publication_state": str(result.get("state") or "PUBLICATION_RECOVERY_REQUIRED"),
        "publication_work_item_id": str(result.get("work_item_id") or "") or None,
        "publication_plan_hash": str(result.get("plan_hash") or "") or None,
        "canonical_article_real_published": bool(
            result.get("canonical_article_real_published")
        ),
        "canonical_url": result.get("canonical_url"),
        "distribution_status": result.get("distribution_status"),
        "derivative_confirmed_count": int(result.get("derivative_confirmed_count") or 0),
        "derivative_attempted_count": int(result.get("derivative_attempted_count") or 0),
        "publication_coordinator_dispatched": bool(
            result.get("publication_coordinator_dispatched")
        ),
        "public_write_performed": bool(result.get("public_write_performed")),
        "provider_publication_writes": int(
            result.get("provider_publication_writes")
            or result.get("publication_write_attempt_count")
            or 0
        ),
        "unknown_write_count": int(
            result.get("unknown_write_count")
            or int(bool(result.get("unknown_write_detected")))
        ),
        "unknown_write_detected": bool(result.get("unknown_write_detected")),
        "publication_bridge_model_call_count": int(
            result.get("bridge_model_call_count") or 0
        ),
        "publication_bridge_source_get_count": int(
            result.get("bridge_source_get_count") or 0
        ),
    }


class SimpleGeminiLocalScheduler:
    """Tick-driven local owner of exactly the existing four routine opportunities."""

    def __init__(
        self,
        *,
        scheduler_root: str | Path,
        published_memory_store: str | Path | None = None,
        published_memory_output_root: str | Path | None = None,
        policy: EditorialWindowPolicy | None = None,
        simple_operation: SimpleOperation | None = None,
        published_memory_loader: PublishedMemoryLoader | None = None,
        publication_handoff: Any = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.scheduler_root = Path(scheduler_root).resolve()
        self.scheduler_root.mkdir(parents=True, exist_ok=True)
        self.policy = policy or build_bootstrap_editorial_window_policy()
        if len(self.policy.core_windows) != 4:
            raise ValueError("simple_gemini_scheduler_requires_exactly_four_windows")
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._orchestrator = ContentOpsProductionOrchestrator()
        self._simple_operation = (
            simple_operation or self._execute_canonical_simple_operation
        )
        self._publication_handoff = publication_handoff
        self._source_route_health_path = (
            Path(published_memory_output_root).resolve()
            / "source_route_health_v1.json"
            if published_memory_output_root is not None
            else None
        )
        if published_memory_loader is None:
            if published_memory_store is None or published_memory_output_root is None:
                raise ValueError("canonical_published_memory_paths_required")

            def canonical_loader() -> tuple[Sequence[Any], Mapping[str, Any]]:
                return load_canonical_published_memory_read_only(
                    store_path=published_memory_store,
                    output_root=published_memory_output_root,
                )

            published_memory_loader = canonical_loader
        self._published_memory_loader = published_memory_loader

    def _execute_canonical_simple_operation(self, **kwargs: Any) -> Mapping[str, Any]:
        return self._orchestrator.execute("run_v1_simple_gemini_newsroom", **kwargs)

    def _window_state_dir(self, production_day_id: str, window_id: str) -> Path:
        return (
            self.scheduler_root / STATE_DIRECTORY_NAME / production_day_id / window_id
        )

    def _window_checkpoint_path(self, production_day_id: str, window_id: str) -> Path:
        return self._window_state_dir(production_day_id, window_id) / "window_v1.json"

    def _slot_checkpoint_path(
        self, production_day_id: str, window_id: str, slot_id: str
    ) -> Path:
        return (
            self._window_state_dir(production_day_id, window_id)
            / "slots"
            / f"{slot_id}.json"
        )

    def _slot_output_dir(
        self, production_day_id: str, window_id: str, slot_id: str
    ) -> Path:
        return self.scheduler_root / production_day_id / window_id / slot_id

    def _source_blocked_candidate_ids_for_production_day(
        self, production_day_id: str
    ) -> set[str]:
        """Reuse existing daily slot artifacts to avoid repeating exhausted candidates."""
        attempted: set[str] = set()
        state_day_root = self.scheduler_root / STATE_DIRECTORY_NAME / production_day_id
        if state_day_root.is_dir():
            for slot_path in sorted(state_day_root.glob("**/slots/*.json")):
                try:
                    slot = _load_checkpoint(
                        slot_path, schema_version=SLOT_CHECKPOINT_SCHEMA_VERSION
                    )
                except SimpleGeminiSchedulerCheckpointError:
                    continue
                attempted.update(
                    str(value)
                    for value in slot.get("source_blocked_candidate_ids") or []
                    if str(value)
                )
        day_root = self.scheduler_root / production_day_id
        if not day_root.is_dir():
            return attempted
        for receipt_path in sorted(
            day_root.glob("**/simple_gemini_newsroom_receipt_v1.json")
        ):
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            except (OSError, TypeError, ValueError):
                continue
            if not isinstance(receipt, Mapping):
                continue
            for row in receipt.get("candidate_attempt_history") or []:
                if not isinstance(row, Mapping) or row.get("status") != "SOURCE_BLOCKED":
                    continue
                candidate_id = str(row.get("candidate_id") or "")
                if candidate_id:
                    attempted.add(candidate_id)
        return attempted

    def _currently_due_windows(self, now: datetime) -> list[dict[str, Any]]:
        rows = owner_locked_editorial_opportunities(
            self.policy,
            reference_utc=now,
            through_utc=now,
            active_window_grace_hours=1.0,
            capacity=1,
        )
        return [
            dict(row)
            for row in rows
            if _parse_utc(row["start_utc"]) <= now
            and now < _parse_utc(row["end_utc"]) + timedelta(hours=1)
        ]

    def _load_memory(
        self, *, production_day_id: str, reference: datetime, slot_output_dir: Path
    ) -> tuple[list[Any], dict[str, Any]]:
        canonical, canonical_proof = self._published_memory_loader()
        qualified = load_qualified_article_records(
            self.scheduler_root,
            production_day_id=production_day_id,
        )
        zero_write_memory = qualified_records_as_published_memory(
            qualified,
            reference=reference,
        )
        combined = _dedupe_memory([*list(canonical), *zero_write_memory])
        proof = {
            "schema_version": MEMORY_ACCESS_SCHEMA_VERSION,
            "canonical_access": dict(canonical_proof),
            "qualified_zero_write_article_count": len(qualified),
            "combined_duplicate_suppression_count": len(combined),
            "combined_identity_set_sha256": _logical_hash(
                sorted(_memory_identity(value) for value in combined)
            ),
            "production_store_mutated": False,
            "second_publication_store_created": False,
            "public_write_performed": False,
        }
        slot_output_dir.mkdir(parents=True, exist_ok=True)
        (slot_output_dir / "published_memory_access_v1.json").write_text(
            json.dumps(proof, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return combined, proof

    @staticmethod
    def _slot_terminal_payload(
        *,
        claim: Mapping[str, Any],
        result: Mapping[str, Any],
        state: str,
        blockers: Sequence[str],
        qualified_count_before: int,
        qualified_count_after: int,
        memory_proof: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            **{
                key: value for key, value in claim.items() if key != "checkpoint_sha256"
            },
            "state": state,
            "terminal": True,
            "classification": str(result.get("classification") or "BLOCKED"),
            "exact_next_blocker": str(result.get("exact_next_blocker") or "") or None,
            "terminal_blockers": sorted(
                {str(value) for value in blockers if str(value)}
            ),
            "qualified_article_count_before": int(qualified_count_before),
            "qualified_article_count_after": int(qualified_count_after),
            "new_qualified_article_count": max(
                0, int(qualified_count_after) - int(qualified_count_before)
            ),
            "candidate_count": int(result.get("candidate_count") or 0),
            "candidate_limit": MAX_SELECTION_CANDIDATES,
            "source_request_count": int(result.get("source_request_count") or 0),
            "source_request_limit": MAX_SOURCE_REQUESTS,
            "logical_model_invocation_count": int(
                result.get("logical_model_invocation_count") or 0
            ),
            "logical_model_invocation_limit": MAX_LOGICAL_MODEL_INVOCATIONS,
            "revision_performed": bool(result.get("revision_performed")),
            "maximum_revision_rounds": MAX_REVISION_ROUNDS,
            "codex_runtime_model_call_count": int(
                result.get("codex_runtime_model_call_count") or 0
            ),
            "public_write_performed": bool(result.get("public_write_performed")),
            "provider_publication_writes": int(
                result.get("provider_publication_writes") or 0
            ),
            "unknown_write_count": int(result.get("unknown_write_count") or 0),
            "article_identity": str(result.get("article_identity") or "") or None,
            "source_blocked_candidate_ids": sorted(
                {
                    str(row.get("candidate_id") or "")
                    for row in result.get("candidate_attempt_history") or []
                    if isinstance(row, Mapping)
                    and row.get("status") == "SOURCE_BLOCKED"
                    and str(row.get("candidate_id") or "")
                }
            ),
            "published_memory_access": dict(memory_proof),
        }

    def _resume_interrupted_publication_slots(self) -> dict[str, Any]:
        summary = {
            "resume_attempt_count": 0,
            "resumed_published_count": 0,
            "pending_recovery": False,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
            "publication_coordinator_dispatched": False,
        }
        if self._publication_handoff is None:
            return summary
        state_root = self.scheduler_root / STATE_DIRECTORY_NAME
        if not state_root.exists():
            return summary
        for slot_path in sorted(state_root.glob("**/slots/*.json")):
            prior = _load_checkpoint(
                slot_path,
                schema_version=SLOT_CHECKPOINT_SCHEMA_VERSION,
            )
            if prior.get("terminal") is True:
                continue
            output_dir = Path(str(prior.get("output_dir") or ""))
            if not output_dir.is_dir() or not (
                output_dir / "qualified_article_record_v1.json"
            ).is_file():
                continue
            summary["resume_attempt_count"] += 1
            try:
                publication = dict(
                    self._publication_handoff.resume(
                        slot_id=str(prior.get("slot_id") or slot_path.stem),
                        slot_output_dir=output_dir,
                    )
                    or {}
                )
            except Exception as exc:  # recovery remains no-model and fail-closed
                publication = {
                    "state": "PUBLICATION_RECOVERY_REQUIRED",
                    "publication_coordinator_dispatched": False,
                    "public_write_performed": False,
                    "unknown_write_detected": True,
                    "unknown_write_count": 1,
                    "safe_error_classification": type(exc).__name__,
                }
            publication_state = str(
                publication.get("state") or "PUBLICATION_RECOVERY_REQUIRED"
            )
            published = publication_state == "PUBLISHED"
            updated = {
                **{
                    key: value
                    for key, value in prior.items()
                    if key != "checkpoint_sha256"
                },
                "state": publication_state,
                "terminal": published,
                "exact_next_blocker": (
                    None if published else "PUBLICATION_RECOVERY_REQUIRED"
                ),
                **_publication_fields(publication),
            }
            _write_checkpoint(slot_path, updated)
            summary["resumed_published_count"] += int(published)
            summary["public_write_performed"] = bool(
                summary["public_write_performed"]
                or publication.get("public_write_performed")
            )
            summary["provider_publication_writes"] += int(
                publication.get("provider_publication_writes")
                or publication.get("publication_write_attempt_count")
                or 0
            )
            summary["unknown_write_count"] += int(
                publication.get("unknown_write_count")
                or int(bool(publication.get("unknown_write_detected")))
            )
            summary["publication_coordinator_dispatched"] = bool(
                summary["publication_coordinator_dispatched"]
                or publication.get("publication_coordinator_dispatched")
            )
            if not published:
                summary["pending_recovery"] = True
                break
        return summary

    def tick(self, *, now: datetime | str | None = None) -> dict[str, Any]:
        moment = _parse_utc(now or self._clock())
        report: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "tick_at_utc": _iso_utc(moment),
            "policy_version": self.policy.policy_version,
            "configured_routine_window_count": len(self.policy.core_windows),
            "due_window_count": 0,
            "window_id": None,
            "newsroom_production_day_id": newsroom_production_day_id(moment),
            "session": None,
            "slot_capacity": 0,
            "slot_terminal_count": 0,
            "simple_operation_invocation_count": 0,
            "exactly_one_routine_editorial_owner": True,
            "routine_editorial_owner": ROUTINE_EDITORIAL_OWNER,
            "published_memory_refresh_count": 0,
            "published_accounting_refresh_count": 0,
            "published_articles_before_window": None,
            "live_output_count_basis": LIVE_OUTPUT_COUNT_BASIS,
            "gemini_logical_call_count": 0,
            "source_get_count": 0,
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
            "native_codex_automation_routed": False,
            "native_desktop_routine_invocation_count": 0,
            "legacy_rolling_x_routine_invocation_count": 0,
            "publication_coordinator_dispatched": False,
            "publication_resume": None,
            "publication_recovery_preflight": None,
            "classification": "IDLE_NOT_DUE",
            "slots": [],
        }
        if self._publication_handoff is not None:
            resumed = self._resume_interrupted_publication_slots()
            report["publication_resume"] = resumed
            report["public_write_performed"] = bool(resumed["public_write_performed"])
            report["provider_publication_writes"] = int(
                resumed["provider_publication_writes"]
            )
            report["unknown_write_count"] = int(resumed["unknown_write_count"])
            report["publication_coordinator_dispatched"] = bool(
                resumed["publication_coordinator_dispatched"]
            )
            if resumed["pending_recovery"]:
                report["classification"] = "PUBLICATION_RECOVERY_PENDING"
                return report

        due = self._currently_due_windows(moment)
        report["due_window_count"] = len(due)
        if not due:
            return report
        if len(due) != 1:
            raise RuntimeError("simple_gemini_due_window_identity_ambiguous")
        window = due[0]
        window_id = str(window["opportunity_id"])
        production_day_id = newsroom_production_day_id(str(window["start_utc"]))
        session = str(window["session"])
        operation_cutoff = min(
            moment,
            _parse_utc(str(window["end_utc"])) - timedelta(microseconds=1),
        )
        report.update(
            {
                "window_id": window_id,
                "newsroom_production_day_id": production_day_id,
                "session": session,
            }
        )
        window_path = self._window_checkpoint_path(production_day_id, window_id)
        window_lock = _NonBlockingFileLock(window_path.with_name("window.lock"))
        if not window_lock.acquire():
            report["classification"] = "WINDOW_ACTIVE_OTHER_PROCESS"
            return report
        try:
            return self._tick_acquired_window(
                moment=moment,
                report=report,
                window=window,
                window_id=window_id,
                production_day_id=production_day_id,
                session=session,
                operation_cutoff=operation_cutoff,
                window_path=window_path,
            )
        finally:
            window_lock.release()

    def _tick_acquired_window(
        self,
        *,
        moment: datetime,
        report: dict[str, Any],
        window: Mapping[str, Any],
        window_id: str,
        production_day_id: str,
        session: str,
        operation_cutoff: datetime,
        window_path: Path,
    ) -> dict[str, Any]:
        existing_window = _load_checkpoint(
            window_path,
            schema_version=WINDOW_CHECKPOINT_SCHEMA_VERSION,
        )
        if existing_window.get("terminal") is True:
            report["classification"] = "WINDOW_ALREADY_TERMINAL"
            report["slot_capacity"] = int(existing_window.get("slot_capacity") or 0)
            report["slot_terminal_count"] = int(
                existing_window.get("slot_terminal_count") or 0
            )
            return report

        canonical_before_window, canonical_accounting_proof = self._published_memory_loader()
        report["published_accounting_refresh_count"] += 1
        published_before_window = count_reconciled_published_articles(
            canonical_before_window, production_day_id=production_day_id
        )
        report["published_articles_before_window"] = published_before_window
        qualified_before_window = len(
            load_qualified_article_records(
                self.scheduler_root,
                production_day_id=production_day_id,
            )
        )
        slot_capacity = int(
            existing_window.get("slot_capacity")
            or bounded_deficit_work_needed(
                session=session,
                published_articles_today=published_before_window,
            )
        )
        report["slot_capacity"] = slot_capacity
        window_claim = existing_window or {
            "schema_version": WINDOW_CHECKPOINT_SCHEMA_VERSION,
            "window_id": window_id,
            "trigger": TRIGGER_SCHEDULED,
            "policy_id": self.policy.policy_id,
            "policy_version": self.policy.policy_version,
            "session": session,
            "start_utc": str(window["start_utc"]),
            "end_utc": str(window["end_utc"]),
            "newsroom_production_day_id": production_day_id,
            "slot_capacity": slot_capacity,
            "qualified_articles_before_window": qualified_before_window,
            "published_articles_before_window": published_before_window,
            "live_output_count_basis": LIVE_OUTPUT_COUNT_BASIS,
            "canonical_published_accounting_proof": dict(canonical_accounting_proof),
            "state": "RUNNING",
            "terminal": False,
            "public_write_authority": (
                "DELEGATED_TO_DURABLE_PUBLICATION_COORDINATOR"
                if self._publication_handoff is not None
                else "ZERO"
            ),
        }
        _write_checkpoint(window_path, window_claim)

        if self._publication_handoff is not None:
            recovery = dict(self._publication_handoff.recover_preflight() or {})
            report["publication_recovery_preflight"] = recovery
            report["public_write_performed"] = bool(
                report["public_write_performed"] or recovery.get("publish_calls")
            )
            report["provider_publication_writes"] += int(
                recovery.get("publish_calls") or 0
            )
            if int(recovery.get("backlog_remaining") or 0) > 0 or recovery.get(
                "backlog_blocking_new_publication"
            ) is True:
                report["classification"] = "PUBLICATION_RECOVERY_PENDING"
                _write_checkpoint(
                    window_path,
                    {
                        **{
                            key: value
                            for key, value in window_claim.items()
                            if key != "checkpoint_sha256"
                        },
                        "state": "PUBLICATION_RECOVERY_PENDING",
                        "terminal": False,
                        "publication_recovery_preflight": recovery,
                    },
                )
                return report

        slot_receipts: list[dict[str, Any]] = []
        safety_error: SimpleGeminiSchedulerSafetyError | None = None
        publication_recovery_pending = False
        attempted_candidate_ids = (
            self._source_blocked_candidate_ids_for_production_day(production_day_id)
        )
        for ordinal in range(1, slot_capacity + 1):
            slot_id = simple_gemini_slot_id(
                production_day_id=production_day_id,
                window_id=window_id,
                slot_ordinal=ordinal,
            )
            slot_path = self._slot_checkpoint_path(
                production_day_id, window_id, slot_id
            )
            prior_slot = _load_checkpoint(
                slot_path,
                schema_version=SLOT_CHECKPOINT_SCHEMA_VERSION,
            )
            if (
                prior_slot.get("terminal") is True
                and prior_slot.get("state") in TERMINAL_SLOT_STATES
            ):
                slot_receipts.append(prior_slot)
                continue
            if prior_slot and prior_slot.get("terminal") is not True:
                slot_output_dir = Path(str(prior_slot.get("output_dir") or ""))
                can_resume_publication = bool(
                    self._publication_handoff is not None
                    and slot_output_dir.is_dir()
                    and (slot_output_dir / "qualified_article_record_v1.json").is_file()
                )
                if can_resume_publication:
                    try:
                        publication = dict(
                            self._publication_handoff.resume(
                                slot_id=slot_id,
                                slot_output_dir=slot_output_dir,
                            )
                            or {}
                        )
                    except Exception as exc:
                        publication = {
                            "state": "PUBLICATION_RECOVERY_REQUIRED",
                            "publication_coordinator_dispatched": False,
                            "public_write_performed": False,
                            "unknown_write_detected": True,
                            "unknown_write_count": 1,
                            "safe_error_classification": type(exc).__name__,
                        }
                    published = str(publication.get("state") or "") == "PUBLISHED"
                    resumed = {
                        **{
                            key: value
                            for key, value in prior_slot.items()
                            if key != "checkpoint_sha256"
                        },
                        "state": str(
                            publication.get("state")
                            or "PUBLICATION_RECOVERY_REQUIRED"
                        ),
                        "terminal": published,
                        "exact_next_blocker": (
                            None if published else "PUBLICATION_RECOVERY_REQUIRED"
                        ),
                        **_publication_fields(publication),
                    }
                    _write_checkpoint(slot_path, resumed)
                    persisted = _load_checkpoint(
                        slot_path, schema_version=SLOT_CHECKPOINT_SCHEMA_VERSION
                    )
                    slot_receipts.append(persisted)
                    if not published:
                        publication_recovery_pending = True
                        break
                    continue
                interrupted = {
                    **{
                        key: value
                        for key, value in prior_slot.items()
                        if key != "checkpoint_sha256"
                    },
                    "state": "BLOCKED",
                    "terminal": True,
                    "classification": "BLOCKED_INTERRUPTED_SLOT",
                    "exact_next_blocker": "INTERRUPTED_SLOT_NOT_REINVOKED_AFTER_RESTART",
                    "terminal_blockers": [
                        "interrupted_slot_not_reinvoked_after_restart"
                    ],
                    "new_qualified_article_count": 0,
                    "codex_runtime_model_call_count": 0,
                    "public_write_performed": False,
                    "provider_publication_writes": 0,
                    "unknown_write_count": 0,
                }
                _write_checkpoint(slot_path, interrupted)
                slot_receipts.append(
                    _load_checkpoint(
                        slot_path, schema_version=SLOT_CHECKPOINT_SCHEMA_VERSION
                    )
                )
                continue

            slot_output_dir = self._slot_output_dir(
                production_day_id, window_id, slot_id
            )
            claim = {
                "schema_version": SLOT_CHECKPOINT_SCHEMA_VERSION,
                "slot_id": slot_id,
                "slot_ordinal": ordinal,
                "window_id": window_id,
                "session": session,
                "newsroom_production_day_id": production_day_id,
                "run_id": slot_id,
                "operation_cutoff_utc": _iso_utc(operation_cutoff),
                "output_dir": str(slot_output_dir),
                "state": "RUNNING",
                "terminal": False,
                "public_write_authority": (
                    "DELEGATED_TO_DURABLE_PUBLICATION_COORDINATOR"
                    if self._publication_handoff is not None
                    else "ZERO"
                ),
            }
            _write_checkpoint(slot_path, claim)
            qualified_before = len(
                load_qualified_article_records(
                    self.scheduler_root,
                    production_day_id=production_day_id,
                )
            )
            memory, memory_proof = self._load_memory(
                production_day_id=production_day_id,
                reference=moment,
                slot_output_dir=slot_output_dir,
            )
            report["published_memory_refresh_count"] += 1
            report["simple_operation_invocation_count"] += 1
            try:
                result = dict(
                    self._simple_operation(
                        output_dir=slot_output_dir,
                        cutoff_utc=_iso_utc(operation_cutoff),
                        run_id=slot_id,
                        published_memory=memory,
                        source_route_health=(
                            load_source_route_health_snapshot_read_only(
                                self._source_route_health_path
                            )
                            if self._source_route_health_path is not None
                            else {}
                        ),
                        attempted_candidate_ids=sorted(attempted_candidate_ids),
                    )
                )
            except Exception as exc:
                result = {
                    "classification": "BLOCKED_SIMPLE_OPERATION_EXCEPTION",
                    "exact_next_blocker": type(exc).__name__,
                    "candidate_limit": MAX_SELECTION_CANDIDATES,
                    "codex_runtime_model_call_count": 0,
                    "public_write_performed": False,
                    "provider_publication_writes": 0,
                    "unknown_write_count": 0,
                }
            updated_health = result.get("updated_source_route_health")
            if (
                self._source_route_health_path is not None
                and isinstance(updated_health, Mapping)
                and updated_health
            ):
                persist_source_route_health_snapshot(
                    self._source_route_health_path,
                    updated_health,
                )
            for row in result.get("candidate_attempt_history") or []:
                if not isinstance(row, Mapping) or row.get("status") != "SOURCE_BLOCKED":
                    continue
                candidate_id = str(row.get("candidate_id") or "")
                if candidate_id:
                    attempted_candidate_ids.add(candidate_id)
            blockers = _result_safety_blockers(result)
            qualified_after = len(
                load_qualified_article_records(
                    self.scheduler_root,
                    production_day_id=production_day_id,
                )
            )
            new_qualified = qualified_after - qualified_before
            classification = str(result.get("classification") or "")
            if blockers:
                state = "SAFETY_BLOCKED"
            elif (
                classification == "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE"
                and new_qualified == 1
            ):
                state = "QUALIFIED"
            elif classification == "NO_PUBLICATION" and new_qualified == 0:
                state = "ABSTAINED"
            else:
                state = "BLOCKED"
                blockers.append("simple_result_and_qualified_record_inconsistent")

            if state == "QUALIFIED" and self._publication_handoff is not None:
                pending = self._slot_terminal_payload(
                    claim=claim,
                    result=result,
                    state="PUBLICATION_PENDING",
                    blockers=(),
                    qualified_count_before=qualified_before,
                    qualified_count_after=qualified_after,
                    memory_proof=memory_proof,
                )
                pending["terminal"] = False
                pending["public_write_authority"] = (
                    "DELEGATED_TO_DURABLE_PUBLICATION_COORDINATOR"
                )
                _write_checkpoint(slot_path, pending)
                returned_plan = result.get("publication_lifecycle_plan")
                returned_plan = (
                    returned_plan if isinstance(returned_plan, Mapping) else None
                )
                try:
                    publication = dict(
                        self._publication_handoff.publish(
                            slot_id=slot_id,
                            slot_output_dir=slot_output_dir,
                            returned_plan=returned_plan,
                        )
                        or {}
                    )
                except Exception as exc:
                    publication = {
                        "state": "PUBLICATION_RECOVERY_REQUIRED",
                        "publication_coordinator_dispatched": False,
                        "public_write_performed": False,
                        "unknown_write_detected": True,
                        "unknown_write_count": 1,
                        "safe_error_classification": type(exc).__name__,
                    }
                published = str(publication.get("state") or "") == "PUBLISHED"
                publication_receipt = {
                    **{
                        key: value
                        for key, value in pending.items()
                        if key != "checkpoint_sha256"
                    },
                    "state": (
                        "PUBLISHED"
                        if published
                        else str(
                            publication.get("state")
                            or "PUBLICATION_RECOVERY_REQUIRED"
                        )
                    ),
                    "terminal": published,
                    "exact_next_blocker": (
                        None if published else "PUBLICATION_RECOVERY_REQUIRED"
                    ),
                    **_publication_fields(publication),
                }
                _write_checkpoint(slot_path, publication_receipt)
                persisted_terminal = _load_checkpoint(
                    slot_path,
                    schema_version=SLOT_CHECKPOINT_SCHEMA_VERSION,
                )
                slot_receipts.append(persisted_terminal)
                if not published:
                    publication_recovery_pending = True
                    break
                continue

            terminal = self._slot_terminal_payload(
                claim=claim,
                result=result,
                state=state,
                blockers=blockers,
                qualified_count_before=qualified_before,
                qualified_count_after=qualified_after,
                memory_proof=memory_proof,
            )
            _write_checkpoint(slot_path, terminal)
            persisted_terminal = _load_checkpoint(
                slot_path,
                schema_version=SLOT_CHECKPOINT_SCHEMA_VERSION,
            )
            slot_receipts.append(persisted_terminal)
            if blockers and state == "SAFETY_BLOCKED":
                safety_error = SimpleGeminiSchedulerSafetyError(blockers)
                break

        report["slots"] = [
            {
                "slot_id": row.get("slot_id"),
                "slot_ordinal": row.get("slot_ordinal"),
                "state": row.get("state"),
                "classification": row.get("classification"),
                "exact_next_blocker": row.get("exact_next_blocker"),
                "article_identity": row.get("article_identity"),
                "canonical_url": row.get("canonical_url"),
                "distribution_status": row.get("distribution_status"),
            }
            for row in slot_receipts
        ]
        report["slot_terminal_count"] = sum(
            1 for row in slot_receipts if row.get("terminal") is True
        )
        report["gemini_logical_call_count"] = sum(
            int(row.get("logical_model_invocation_count") or 0) for row in slot_receipts
        )
        report["source_get_count"] = sum(
            int(row.get("source_request_count") or 0) for row in slot_receipts
        )
        report["codex_runtime_model_call_count"] = sum(
            int(row.get("codex_runtime_model_call_count") or 0) for row in slot_receipts
        )
        report["public_write_performed"] = bool(
            report["public_write_performed"]
            or any(row.get("public_write_performed") is True for row in slot_receipts)
        )
        report["provider_publication_writes"] += sum(
            int(row.get("provider_publication_writes") or 0) for row in slot_receipts
        )
        report["unknown_write_count"] += sum(
            int(row.get("unknown_write_count") or 0) for row in slot_receipts
        )
        report["publication_coordinator_dispatched"] = bool(
            report["publication_coordinator_dispatched"]
            or any(
                row.get("publication_coordinator_dispatched") is True
                for row in slot_receipts
            )
        )
        report["classification"] = (
            "PUBLICATION_RECOVERY_PENDING"
            if publication_recovery_pending
            else "SAFETY_BLOCKED"
            if safety_error is not None
            else "TERMINAL_PUBLISHED"
            if any(row.get("state") == "PUBLISHED" for row in slot_receipts)
            else "TERMINAL_QUALIFIED"
            if any(row.get("state") == "QUALIFIED" for row in slot_receipts)
            else "TERMINAL_NO_PUBLICATION"
        )
        window_terminal = {
            **{
                key: value
                for key, value in window_claim.items()
                if key != "checkpoint_sha256"
            },
            "state": report["classification"],
            "terminal": not publication_recovery_pending,
            "slot_terminal_count": report["slot_terminal_count"],
            "slot_ids": [row.get("slot_id") for row in slot_receipts],
            "qualified_article_count_before": qualified_before_window,
            "qualified_article_count_after": len(
                load_qualified_article_records(
                    self.scheduler_root,
                    production_day_id=production_day_id,
                )
            ),
            "gemini_logical_call_count": report["gemini_logical_call_count"],
            "source_get_count": report["source_get_count"],
            "codex_runtime_model_call_count": report["codex_runtime_model_call_count"],
            "public_write_performed": report["public_write_performed"],
            "provider_publication_writes": report["provider_publication_writes"],
            "unknown_write_count": report["unknown_write_count"],
            "native_codex_automation_routed": False,
            "publication_coordinator_dispatched": report[
                "publication_coordinator_dispatched"
            ],
            "public_write_authority": (
                "DELEGATED_TO_DURABLE_PUBLICATION_COORDINATOR"
                if self._publication_handoff is not None
                else "ZERO"
            ),
        }
        _write_checkpoint(window_path, window_terminal)
        if safety_error is not None:
            raise safety_error
        return report

    def run_forever(
        self,
        *,
        poll_seconds: float = 60.0,
        max_ticks: Optional[int] = None,
        on_tick: Callable[[Mapping[str, Any]], None] | None = None,
        stop_requested: Callable[[], bool] | None = None,
    ) -> int:
        """Run cheap local ticks; idle ticks do no semantic/source work unless recovery is pending."""
        if float(poll_seconds) <= 0:
            raise ValueError("simple_gemini_scheduler_poll_seconds_invalid")
        ticks = 0
        while max_ticks is None or ticks < int(max_ticks):
            if stop_requested is not None and stop_requested():
                break
            result = self.tick()
            ticks += 1
            if on_tick is not None:
                on_tick(result)
            if max_ticks is not None and ticks >= int(max_ticks):
                break
            remaining = float(poll_seconds)
            while remaining > 0:
                if stop_requested is not None and stop_requested():
                    return ticks
                interval = min(0.25, remaining)
                time.sleep(interval)
                remaining -= interval
        return ticks
