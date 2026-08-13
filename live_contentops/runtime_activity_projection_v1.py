"""Tiny, sanitized current-cycle instrumentation for the V1 operator cockpit.

This file is presentation telemetry, not lifecycle authority.  The durable store still owns
whether a cycle exists and every publication/readback/reconciliation fact.  The recorder only
projects the latest already-entered canonical stage so the local operator UI does not have to
guess from logs or partial artifacts.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional


SCHEMA_VERSION = "contentops.runtime_activity_projection.v1"
ACTIVITY_FILE_NAME = "runtime_activity_v1.json"
ACTIVITY_STAGES = (
    "HEADLINE_INGESTION",
    "CANDIDATE_SELECTION",
    "CC_CONTEXT",
    "GROUNDED_RESEARCH",
    "ARTICLE_WRITING",
    "FACTUAL_CHECK",
    "READER_VALUE_CHECK",
    "VISUAL_DISCOVERY",
    "MEDIA_BUILD",
    "PACKAGE_BUILD",
    "PUBLICATION_JIT",
    "CANONICAL_DISPATCH",
    "CANONICAL_READBACK",
    "DERIVATIVE_DISPATCH",
    "RECONCILIATION",
)
_STAGE_SET = frozenset(ACTIVITY_STAGES)
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_SAFE_DESTINATION_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_operator_label(value: Any, *, limit: int = 160) -> Optional[str]:
    """Return a concise display label with URLs/control characters removed."""
    if value in (None, ""):
        return None
    text = _URL_RE.sub("[link]", str(value))
    text = " ".join(text.replace("\x00", " ").split())
    return text[:limit] if text else None


def safe_story_label(cluster: Mapping[str, Any] | None) -> Optional[str]:
    row = dict(cluster or {})
    leaf = row.get("leaf_summaries")
    candidates = (
        row.get("selection_case"),
        row.get("why_now"),
        leaf[0] if isinstance(leaf, list) and leaf else None,
        row.get("seo_intent"),
    )
    return next((label for value in candidates if (label := safe_operator_label(value))), None)


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(dict(value), stream, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


class RuntimeActivityRecorderV1:
    """Record only explicit canonical stage entry with bounded nonsecret context."""

    def __init__(
        self,
        *,
        output_dir: str | Path,
        work_item_id: str,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.path = Path(output_dir) / ACTIVITY_FILE_NAME
        self.work_item_id = str(work_item_id)
        self._now_fn = now_fn

    def record(
        self,
        stage: str,
        *,
        cycle_started_at_utc: str | None = None,
        candidate_rank: int | None = None,
        candidate_count: int | None = None,
        story_label: Any = None,
        grounding: Any = None,
        destination: str | None = None,
        trigger: Any = None,
    ) -> dict[str, Any]:
        if stage not in _STAGE_SET:
            raise ValueError("runtime_activity_stage_invalid")
        if destination and not _SAFE_DESTINATION_RE.fullmatch(str(destination)):
            raise ValueError("runtime_activity_destination_invalid")
        now = _iso(self._now_fn())
        previous = _read(self.path)
        if previous and str(previous.get("work_item_id") or "") != self.work_item_id:
            raise ValueError("runtime_activity_work_item_identity_conflict")
        previous_stage = str(previous.get("current_stage") or "")
        completed = [
            str(item) for item in (previous.get("completed_stages") or [])
            if str(item) in _STAGE_SET
        ]
        if previous_stage in _STAGE_SET and previous_stage != stage and previous_stage not in completed:
            completed.append(previous_stage)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "work_item_id": self.work_item_id,
            "active": True,
            "cycle_started_at_utc": (
                previous.get("cycle_started_at_utc") or cycle_started_at_utc or now
            ),
            "current_stage": stage,
            "stage_started_at_utc": (
                previous.get("stage_started_at_utc") if previous_stage == stage else now
            ),
            "updated_at_utc": now,
            "completed_stages": completed,
            "candidate_rank": (
                max(1, int(candidate_rank)) if candidate_rank is not None else previous.get("candidate_rank")
            ),
            "candidate_count": (
                max(0, int(candidate_count)) if candidate_count is not None else previous.get("candidate_count")
            ),
            "safe_story_label": safe_operator_label(story_label) or previous.get("safe_story_label"),
            "grounding": safe_operator_label(grounding, limit=80) or previous.get("grounding"),
            "destination": str(destination) if destination else previous.get("destination"),
            "trigger": safe_operator_label(trigger, limit=48) or previous.get("trigger"),
            "presentation_only": True,
            "authority_granted": False,
            "contains_hidden_reasoning": False,
        }
        _atomic_write(self.path, payload)
        return payload

    def finish(self, *, terminal_result: Any, exact_reason: Any = None) -> dict[str, Any]:
        previous = _read(self.path)
        if not previous:
            return {}
        if str(previous.get("work_item_id") or "") != self.work_item_id:
            raise ValueError("runtime_activity_work_item_identity_conflict")
        payload = {
            **previous,
            "active": False,
            "updated_at_utc": _iso(self._now_fn()),
            "terminal_result": safe_operator_label(terminal_result, limit=96),
            "exact_reason": safe_operator_label(exact_reason, limit=180),
            "authority_granted": False,
        }
        _atomic_write(self.path, payload)
        return payload


def load_runtime_activity(path: str | Path) -> dict[str, Any]:
    """Load a valid projection without exposing its filesystem path or unknown fields."""
    value = _read(Path(path))
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or str(value.get("current_stage") or "") not in _STAGE_SET
        or not str(value.get("work_item_id") or "")
    ):
        return {}
    return {
        key: value.get(key)
        for key in (
            "schema_version", "work_item_id", "active", "cycle_started_at_utc",
            "current_stage", "stage_started_at_utc", "updated_at_utc",
            "completed_stages", "candidate_rank", "candidate_count",
            "safe_story_label", "grounding", "destination", "trigger",
            "terminal_result", "exact_reason", "presentation_only",
            "authority_granted", "contains_hidden_reasoning",
        )
    }
