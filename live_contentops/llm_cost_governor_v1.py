"""Cycle/day cost governor shared by every canonical ContentOps text-model invocation.

The bounded JSON ledger is operational telemetry, not a second state database. It lives beside
the persistent operator fuse so day totals survive Daily App restarts. No prompt, output,
credential, model response, or session material is stored.
"""
from __future__ import annotations

import json
import math
import os
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterator, Mapping

from live_contentops.llm_operator_control_v1 import RUNTIME_CONTROL_ROOT

SCHEMA_VERSION = "contentops.llm_cost_governor.v1"
LEDGER_FILENAME = "llm_cost_ledger_v1.json"

TARGET_LOGICAL_CALLS_PER_CYCLE = 3
HARD_MAX_LOGICAL_CALLS_PER_CYCLE = 6
HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE = 12
HARD_MAX_TOKENS_PER_CYCLE = 250_000
HARD_MAX_TOKENS_PER_ACTIVE_DAY = 2_000_000
CANONICAL_MAX_OUTPUT_TOKEN_RESERVATION = 16_000

CYCLE_LOGICAL_BUDGET_EXHAUSTED = "llm_cycle_logical_call_budget_exhausted"
CYCLE_PROVIDER_ATTEMPT_BUDGET_EXHAUSTED = "llm_cycle_provider_attempt_budget_exhausted"
CYCLE_TOKEN_BUDGET_EXHAUSTED = "llm_cycle_token_budget_exhausted"
DAILY_TOKEN_BUDGET_EXHAUSTED = "llm_daily_token_budget_exhausted"
COST_TERMINAL_FAILURE_CLASSES = frozenset(
    {
        CYCLE_LOGICAL_BUDGET_EXHAUSTED,
        CYCLE_PROVIDER_ATTEMPT_BUDGET_EXHAUSTED,
        CYCLE_TOKEN_BUDGET_EXHAUSTED,
        DAILY_TOKEN_BUDGET_EXHAUSTED,
    }
)
ZERO_TOKEN_PRE_GENERATION_FAILURE_CLASSES = frozenset(
    {
        "requested_model_temporarily_unavailable",
        "quota_exhausted",
        "http_429_rate_limited",
    }
)

_LEDGER_LOCK = threading.RLock()
_ACTIVE_CYCLE_ID: ContextVar[str | None] = ContextVar("contentops_llm_cycle_id", default=None)
_ACTIVE_CONTROL_ROOT: ContextVar[Path | None] = ContextVar(
    "contentops_llm_control_root", default=None
)
_ACTIVE_NOW: ContextVar[datetime | None] = ContextVar("contentops_llm_budget_now", default=None)


class LLMCostBudgetExceededError(RuntimeError):
    def __init__(self, failure_class: str) -> None:
        self.failure_class = str(failure_class)
        super().__init__(self.failure_class.upper())


def _control_root() -> Path:
    return _ACTIVE_CONTROL_ROOT.get() or RUNTIME_CONTROL_ROOT


def ledger_path(control_root: str | Path | None = None) -> Path:
    return Path(control_root or _control_root()) / LEDGER_FILENAME


def _now() -> datetime:
    value = _ACTIVE_NOW.get() or datetime.now().astimezone()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def _active_day(now: datetime | None = None) -> str:
    return (now or _now()).astimezone().date().isoformat()


def _default_ledger() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "days": {}, "cycles": {}}


def _read_ledger(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _default_ledger()
    except (OSError, ValueError, TypeError) as exc:
        # Unknown accounting state must fail closed instead of silently resetting a budget.
        raise LLMCostBudgetExceededError(DAILY_TOKEN_BUDGET_EXHAUSTED) from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise LLMCostBudgetExceededError(DAILY_TOKEN_BUDGET_EXHAUSTED)
    payload.setdefault("days", {})
    payload.setdefault("cycles", {})
    return payload


def _write_ledger(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _bounded_cycle_key(cycle_id: str) -> str:
    value = str(cycle_id or "").strip()
    if value and len(value) <= 180:
        return value
    return "cycle-" + sha256(value.encode("utf-8")).hexdigest()[:32]


def _cycle_id(logical_invocation_id: str | None = None) -> str:
    active = _ACTIVE_CYCLE_ID.get()
    if active:
        return _bounded_cycle_key(active)
    value = str(logical_invocation_id or "standalone")
    return "standalone-" + sha256(value.encode("utf-8")).hexdigest()[:24]


def _cycle_row(ledger: dict[str, Any], cycle_id: str, day: str) -> dict[str, Any]:
    cycles = ledger.setdefault("cycles", {})
    row = cycles.setdefault(
        cycle_id,
        {
            "active_day": day,
            "logical_invocation_ids": [],
            "provider_attempts": 0,
            "accounted_tokens": 0,
        },
    )
    if row.get("active_day") != day:
        # A cycle/window identity is immutable and must never reset into a new day.
        raise LLMCostBudgetExceededError(CYCLE_TOKEN_BUDGET_EXHAUSTED)
    return row


def _day_row(ledger: dict[str, Any], day: str) -> dict[str, Any]:
    return ledger.setdefault("days", {}).setdefault(day, {"accounted_tokens": 0})


def _prune(ledger: dict[str, Any], now: datetime) -> None:
    oldest = (now.astimezone().date() - timedelta(days=14)).isoformat()
    ledger["days"] = {
        key: value for key, value in ledger.get("days", {}).items() if key >= oldest
    }
    ledger["cycles"] = {
        key: value
        for key, value in ledger.get("cycles", {}).items()
        if str(value.get("active_day") or "") >= oldest
    }


@contextmanager
def llm_cycle_budget_scope(
    cycle_id: str,
    *,
    control_root: str | Path | None = None,
    now: datetime | None = None,
) -> Iterator[None]:
    """Bind all nested logical calls/retries/repairs to one immutable cycle budget."""
    cycle_token = _ACTIVE_CYCLE_ID.set(_bounded_cycle_key(cycle_id))
    root_token = _ACTIVE_CONTROL_ROOT.set(Path(control_root) if control_root else None)
    now_token = _ACTIVE_NOW.set(now)
    try:
        yield
    finally:
        _ACTIVE_NOW.reset(now_token)
        _ACTIVE_CONTROL_ROOT.reset(root_token)
        _ACTIVE_CYCLE_ID.reset(cycle_token)


def reserve_logical_invocation(logical_invocation_id: str) -> None:
    with _LEDGER_LOCK:
        path = ledger_path()
        ledger = _read_ledger(path)
        now = _now()
        day = _active_day(now)
        cycle = _cycle_row(ledger, _cycle_id(logical_invocation_id), day)
        daily = _day_row(ledger, day)
        logical_ids = list(cycle.get("logical_invocation_ids") or [])
        if logical_invocation_id in logical_ids:
            return
        if len(logical_ids) >= HARD_MAX_LOGICAL_CALLS_PER_CYCLE:
            raise LLMCostBudgetExceededError(CYCLE_LOGICAL_BUDGET_EXHAUSTED)
        if int(cycle.get("accounted_tokens") or 0) >= HARD_MAX_TOKENS_PER_CYCLE:
            raise LLMCostBudgetExceededError(CYCLE_TOKEN_BUDGET_EXHAUSTED)
        if int(daily.get("accounted_tokens") or 0) >= HARD_MAX_TOKENS_PER_ACTIVE_DAY:
            raise LLMCostBudgetExceededError(DAILY_TOKEN_BUDGET_EXHAUSTED)
        logical_ids.append(str(logical_invocation_id))
        cycle["logical_invocation_ids"] = logical_ids
        _prune(ledger, now)
        _write_ledger(path, ledger)


def _estimated_prompt_tokens(prompt: str) -> int:
    # Conservative provider-independent approximation; actual usage replaces the reservation.
    return max(1, int(math.ceil(len(str(prompt or "").encode("utf-8")) / 4.0)))


def reserve_provider_attempt(prompt: str, *, logical_invocation_id: str) -> dict[str, Any]:
    with _LEDGER_LOCK:
        path = ledger_path()
        ledger = _read_ledger(path)
        now = _now()
        day = _active_day(now)
        cycle_id = _cycle_id(logical_invocation_id)
        cycle = _cycle_row(ledger, cycle_id, day)
        daily = _day_row(ledger, day)
        if int(cycle.get("provider_attempts") or 0) >= HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE:
            raise LLMCostBudgetExceededError(CYCLE_PROVIDER_ATTEMPT_BUDGET_EXHAUSTED)
        prompt_tokens = _estimated_prompt_tokens(prompt)
        reservation = prompt_tokens + CANONICAL_MAX_OUTPUT_TOKEN_RESERVATION
        if int(cycle.get("accounted_tokens") or 0) + reservation > HARD_MAX_TOKENS_PER_CYCLE:
            raise LLMCostBudgetExceededError(CYCLE_TOKEN_BUDGET_EXHAUSTED)
        if int(daily.get("accounted_tokens") or 0) + reservation > HARD_MAX_TOKENS_PER_ACTIVE_DAY:
            raise LLMCostBudgetExceededError(DAILY_TOKEN_BUDGET_EXHAUSTED)
        cycle["provider_attempts"] = int(cycle.get("provider_attempts") or 0) + 1
        cycle["accounted_tokens"] = int(cycle.get("accounted_tokens") or 0) + reservation
        daily["accounted_tokens"] = int(daily.get("accounted_tokens") or 0) + reservation
        _write_ledger(path, ledger)
        return {
            "cycle_id": cycle_id,
            "active_day": day,
            "reserved_tokens": reservation,
            "estimated_prompt_tokens": prompt_tokens,
        }


def reconcile_provider_attempt(
    reservation: Mapping[str, Any],
    usage: Mapping[str, Any] | None,
    *,
    failure_class: str | None = None,
) -> None:
    total = (usage or {}).get("total_tokens")
    if isinstance(total, (int, float)) and total >= 0:
        actual = int(total)
    elif str(failure_class or "") in ZERO_TOKEN_PRE_GENERATION_FAILURE_CLASSES:
        # These exact provider/router outcomes prove rejection before model generation. They
        # still consume the provider-attempt budget, but retaining a token reservation would
        # incorrectly starve later quality-authorized fallbacks in the same cycle.
        actual = 0
    else:
        return  # retain the conservative full reservation when usage/outcome is untrusted
    reserved = int(reservation.get("reserved_tokens") or 0)
    delta = actual - reserved
    with _LEDGER_LOCK:
        path = ledger_path()
        ledger = _read_ledger(path)
        cycle = _cycle_row(
            ledger,
            str(reservation["cycle_id"]),
            str(reservation["active_day"]),
        )
        daily = _day_row(ledger, str(reservation["active_day"]))
        cycle["accounted_tokens"] = max(0, int(cycle.get("accounted_tokens") or 0) + delta)
        daily["accounted_tokens"] = max(0, int(daily.get("accounted_tokens") or 0) + delta)
        _write_ledger(path, ledger)


def budget_snapshot(
    cycle_id: str, *, control_root: str | Path | None = None
) -> dict[str, Any]:
    path = ledger_path(control_root)
    with _LEDGER_LOCK:
        ledger = _read_ledger(path)
    row = dict((ledger.get("cycles") or {}).get(_bounded_cycle_key(cycle_id)) or {})
    day = str(row.get("active_day") or _active_day())
    return {
        "cycle": row,
        "day": dict((ledger.get("days") or {}).get(day) or {}),
        "limits": {
            "target_logical_calls": TARGET_LOGICAL_CALLS_PER_CYCLE,
            "hard_max_logical_calls": HARD_MAX_LOGICAL_CALLS_PER_CYCLE,
            "hard_max_provider_attempts": HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE,
            "hard_max_cycle_tokens": HARD_MAX_TOKENS_PER_CYCLE,
            "hard_max_daily_tokens": HARD_MAX_TOKENS_PER_ACTIVE_DAY,
        },
    }
