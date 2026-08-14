"""Lease-bound model execution for the single V2-01 replacement proof.

Generic and V1 traffic continue through the canonical shared pause marker. Only the
replacement runner can issue this process-local capability, and only explicitly named V2
entry points consume it.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import threading
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from live_contentops.llm_cost_governor_v1 import (
    LLMCostBudgetExceededError,
    llm_cycle_budget_scope,
    reconcile_provider_attempt,
    reserve_logical_invocation,
    reserve_provider_attempt,
)
from live_contentops.llm_operator_control_v1 import operator_pause_path
from live_contentops.nine_router_ordered_model_router_v2 import (
    MULTIMODAL_VIDEO_CRITIC_ROLE,
    ProviderResult,
    RetryBudget,
    V2_CREATIVE_ROLES,
    model_pool_for_role,
    retry_budget_for_role,
    route_llm_invocation,
)

SCHEMA_VERSION = "contentops.v2_isolated_llm_execution.v1"
TASK_ID = "TASK_CONTENTOPS_V2_CONCRETE_FIRST_XHIGH_REPLACEMENT_VERTICAL_SLICE_V1"
BRANCH = "task/v2-concrete-first-xhigh-replacement-vertical-slice-v1"
RUN_ID = "cc-v2-eia-hormuz-concrete-first-2026-v1"
BRAIN = "NineRouterGPT56Brain"
RUNNER_MODULE = "live_contentops.retention_native_replacement_runner_v2"
RUNNER_RELATIVE_PATH = Path("live_contentops/retention_native_replacement_runner_v2.py")
ALLOWED_COMPONENTS = frozenset({BRAIN, "CanonicalMultimodalCritic"})
ALLOWED_ROLES = frozenset({*V2_CREATIVE_ROLES, MULTIMODAL_VIDEO_CRITIC_ROLE})
ALLOWED_RUNTIME_NAMES = frozenset(
    {
        "v2_concrete_first_xhigh_replacement_20260813",
        "v2_codex_builder_ab_20260814",
    }
)
_ACTIVE_LEASE: ContextVar["V2ExecutionLease | None"] = ContextVar(
    "contentops_v2_isolated_execution_lease", default=None
)
_AUDIT_LOCK = threading.RLock()


class V2ExecutionLeaseError(RuntimeError):
    """Fail-closed lease validation error raised before provider I/O."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str | None:
    try:
        return _hash_bytes(path.read_bytes())
    except FileNotFoundError:
        return None


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args], capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise V2ExecutionLeaseError(f"git_identity_unavailable:{args[-1]}")
    return result.stdout.strip()


def _v1_daily_app_processes() -> list[dict[str, Any]]:
    command = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -match '^(python|pythonw).*' -and "
        "$_.CommandLine -match 'live_contentops.cli daily-app start' } | "
        "Select-Object ProcessId,Name,CreationDate | ConvertTo-Json -Compress"
    )
    observed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if observed.returncode != 0 or not observed.stdout.strip():
        return []
    value = json.loads(observed.stdout)
    rows = [value] if isinstance(value, dict) else list(value)
    return [
        {
            "process_id": int(row["ProcessId"]),
            "name": str(row["Name"]),
            "creation_date": str(row.get("CreationDate") or ""),
        }
        for row in rows
    ]


def _v1_process_state(rows: list[dict[str, Any]]) -> str:
    return "ACTIVE_OBSERVED" if rows else "NOT_RUNNING_OBSERVED"


def _v1_process_state_stable(
    before: list[dict[str, Any]], after: list[dict[str, Any]]
) -> bool:
    """Require the V1 process set to remain exactly stable, including stable absence."""
    return {row["process_id"] for row in before} == {row["process_id"] for row in after}


@dataclass(frozen=True)
class V2ExecutionLease:
    domain_id: str
    task_id: str
    branch: str
    worktree: str
    run_id: str
    brain: str
    control_root: Path
    lease_path: Path
    audit_path: Path
    nonce: str
    created_at_utc: str
    expires_at_utc: str


def issue_v2_execution_lease(*, repo_root: Path, runtime: Path) -> V2ExecutionLease:
    """Issue the one-proof capability; direct callers outside the runner are rejected."""
    repo_root = repo_root.resolve()
    runtime = runtime.resolve()
    expected_runner = (repo_root / RUNNER_RELATIVE_PATH).resolve()
    if not any(
        Path(frame.filename).resolve() == expected_runner
        for frame in inspect.stack()[1:10]
    ):
        raise V2ExecutionLeaseError("lease_issuer_not_v2_replacement_runner")
    if Path(_git(repo_root, "rev-parse", "--show-toplevel")).resolve() != repo_root:
        raise V2ExecutionLeaseError("lease_worktree_identity_mismatch")
    if _git(repo_root, "branch", "--show-current") != BRANCH:
        raise V2ExecutionLeaseError("lease_branch_identity_mismatch")
    if runtime.name not in ALLOWED_RUNTIME_NAMES:
        raise V2ExecutionLeaseError("lease_run_root_mismatch")
    shared_marker = operator_pause_path()
    if not shared_marker.is_file():
        raise V2ExecutionLeaseError("shared_global_pause_must_remain_active")
    processes = _v1_daily_app_processes()
    now = _utc_now()
    nonce = uuid.uuid4().hex + uuid.uuid4().hex
    domain_id = f"v2-01-{uuid.uuid4().hex}"
    control_root = runtime / "v2_control" / domain_id
    lease = V2ExecutionLease(
        domain_id=domain_id,
        task_id=TASK_ID,
        branch=BRANCH,
        worktree=str(repo_root),
        run_id=RUN_ID,
        brain=BRAIN,
        control_root=control_root,
        lease_path=control_root / "execution_lease_v1.json",
        audit_path=control_root / "execution_audit_v1.json",
        nonce=nonce,
        created_at_utc=_iso(now),
        expires_at_utc=_iso(now + timedelta(hours=12)),
    )
    common = {
        "schema_version": SCHEMA_VERSION,
        "domain_id": domain_id,
        "task_id": TASK_ID,
        "branch": BRANCH,
        "worktree": str(repo_root),
        "run_id": RUN_ID,
        "brain": BRAIN,
        "allowed_components": sorted(ALLOWED_COMPONENTS),
        "allowed_roles": sorted(ALLOWED_ROLES),
        "allowed_models_by_role": {
            role: list(model_pool_for_role(role)) for role in sorted(ALLOWED_ROLES)
        },
        "zero_public_write": True,
        "nonce_sha256": _hash_bytes(nonce.encode()),
        "created_at_utc": lease.created_at_utc,
        "expires_at_utc": lease.expires_at_utc,
        "shared_global_pause": {
            "path": str(shared_marker),
            "present": True,
            "sha256": _hash_file(shared_marker),
        },
        "v1_daily_app_before": processes,
        "v1_daily_app_state_before": _v1_process_state(processes),
        "contains_secrets": False,
    }
    _atomic_json(lease.lease_path, common | {"state": "ACTIVE"})
    _atomic_json(
        lease.audit_path,
        common
        | {
            "state": "ACTIVE",
            "provider_attempts": [],
            "logical_invocations": [],
            "v1_provider_calls_authorized_by_v2_lease": 0,
            "public_writes": 0,
        },
    )
    return lease


def _read_active_payload(lease: V2ExecutionLease) -> dict[str, Any]:
    try:
        payload = json.loads(lease.lease_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError, TypeError) as exc:
        raise V2ExecutionLeaseError("v2_execution_lease_absent_or_malformed") from exc
    expected = {
        "state": "ACTIVE",
        "domain_id": lease.domain_id,
        "task_id": TASK_ID,
        "branch": BRANCH,
        "worktree": lease.worktree,
        "run_id": RUN_ID,
        "brain": BRAIN,
        "zero_public_write": True,
        "nonce_sha256": _hash_bytes(lease.nonce.encode()),
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise V2ExecutionLeaseError("v2_execution_lease_identity_mismatch")
    try:
        expiry = datetime.fromisoformat(
            str(payload["expires_at_utc"]).replace("Z", "+00:00")
        )
    except (KeyError, ValueError) as exc:
        raise V2ExecutionLeaseError("v2_execution_lease_expiry_malformed") from exc
    if _utc_now() >= expiry:
        raise V2ExecutionLeaseError("v2_execution_lease_expired")
    marker = operator_pause_path()
    before = payload.get("shared_global_pause") or {}
    if not marker.is_file() or _hash_file(marker) != before.get("sha256"):
        raise V2ExecutionLeaseError("shared_global_pause_changed_during_v2_lease")
    return payload


def assert_v2_execution_authorized(
    *,
    role_task_id: str,
    logical_invocation_id: str,
    component: str,
    model: str | None = None,
    public_write: bool = False,
) -> V2ExecutionLease:
    lease = _ACTIVE_LEASE.get()
    if lease is None:
        raise V2ExecutionLeaseError("v2_execution_lease_not_active_in_runner")
    _read_active_payload(lease)
    if public_write:
        raise V2ExecutionLeaseError(
            "v2_execution_lease_has_zero_public_write_authority"
        )
    if component not in ALLOWED_COMPONENTS:
        raise V2ExecutionLeaseError("v2_execution_component_not_authorized")
    if role_task_id not in ALLOWED_ROLES:
        raise V2ExecutionLeaseError("v2_execution_role_not_authorized")
    if not str(logical_invocation_id).startswith("inv_v2_"):
        raise V2ExecutionLeaseError("v2_logical_invocation_identity_mismatch")
    if model is not None and model not in model_pool_for_role(role_task_id):
        raise V2ExecutionLeaseError("v2_execution_model_not_authorized_for_role")
    return lease


def _append_audit(lease: V2ExecutionLease, key: str, row: Mapping[str, Any]) -> None:
    with _AUDIT_LOCK:
        payload = json.loads(lease.audit_path.read_text(encoding="utf-8"))
        payload.setdefault(key, []).append(dict(row))
        _atomic_json(lease.audit_path, payload)


def record_provider_attempt(
    *,
    lease: V2ExecutionLease,
    logical_invocation_id: str,
    role_task_id: str,
    component: str,
    requested_model: str,
    prompt_sha256: str,
    result: ProviderResult | None = None,
    error_class: str | None = None,
) -> None:
    _append_audit(
        lease,
        "provider_attempts",
        {
            "attempt_id": uuid.uuid4().hex,
            "at_utc": _iso(_utc_now()),
            "logical_invocation_id": logical_invocation_id,
            "role": role_task_id,
            "component": component,
            "requested_model": requested_model,
            "effective_model": result.resolved_model if result else None,
            "provider_invocation_id_sha256": (
                _hash_bytes(str(result.provider_invocation_id).encode())
                if result and result.provider_invocation_id
                else None
            ),
            "prompt_sha256": prompt_sha256,
            "status_code": result.status_code if result else None,
            "failure_class": error_class or (result.failure_class if result else None),
            "public_write": False,
        },
    )


def routed_v2_isolated_invocation(
    *,
    prompt: str,
    role_task_id: str,
    logical_invocation_id: str,
    component: str,
    provider_call: Callable[[str, str, float], ProviderResult],
    work_item_id: str | None = None,
    timeout_seconds: float = 60.0,
    validator: Callable[[str], Any] | None = None,
    governed_input: Any = None,
    prompt_template: str = "unspecified",
    prompt_version: str = "v1",
    budget: RetryBudget | None = None,
    model_pool_override: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    lease = assert_v2_execution_authorized(
        role_task_id=role_task_id,
        logical_invocation_id=logical_invocation_id,
        component=component,
    )
    with llm_cycle_budget_scope(logical_invocation_id, control_root=lease.control_root):
        reserve_logical_invocation(logical_invocation_id)

        def governed_provider(
            current_prompt: str, model: str, timeout: float
        ) -> ProviderResult:
            assert_v2_execution_authorized(
                role_task_id=role_task_id,
                logical_invocation_id=logical_invocation_id,
                component=component,
                model=model,
            )
            try:
                reservation = reserve_provider_attempt(
                    current_prompt, logical_invocation_id=logical_invocation_id
                )
            except LLMCostBudgetExceededError as exc:
                return ProviderResult(error=exc, failure_class=exc.failure_class)
            result = provider_call(current_prompt, model, timeout)
            reconcile_provider_attempt(
                reservation, result.usage, failure_class=result.failure_class
            )
            return result

        role_model_pool = model_pool_for_role(role_task_id)
        selected_model_pool = model_pool_override or role_model_pool
        if any(model not in role_model_pool for model in selected_model_pool):
            raise V2ExecutionLeaseError(
                "v2_model_pool_override_not_authorized_for_role"
            )
        summary = route_llm_invocation(
            logical_invocation_id=logical_invocation_id,
            role_task_id=role_task_id,
            work_item_id=work_item_id,
            prompt=prompt,
            provider_call=governed_provider,
            validator=validator,
            governed_input=governed_input,
            prompt_template=prompt_template,
            prompt_version=prompt_version,
            timeout_seconds=timeout_seconds,
            budget=budget
            or retry_budget_for_role(
                role_task_id=role_task_id, logical_invocation_id=logical_invocation_id
            ),
            model_pool=selected_model_pool,
        )
    _append_audit(
        lease,
        "logical_invocations",
        {
            "logical_invocation_id": logical_invocation_id,
            "role": role_task_id,
            "component": component,
            "terminal_disposition": summary.get("terminal_disposition"),
            "requested_models": summary.get("models_attempted_in_order"),
            "effective_model": summary.get("selected_model"),
            "output_sha256": summary.get("output_hash"),
            "public_write": False,
        },
    )
    return summary


@contextmanager
def active_v2_execution_lease(
    *, repo_root: Path, runtime: Path
) -> Iterator[V2ExecutionLease]:
    lease = issue_v2_execution_lease(repo_root=repo_root, runtime=runtime)
    token = _ACTIVE_LEASE.set(lease)
    try:
        yield lease
    finally:
        _ACTIVE_LEASE.reset(token)
        marker = operator_pause_path()
        processes = _v1_daily_app_processes()
        audit = json.loads(lease.audit_path.read_text(encoding="utf-8"))
        unchanged = (
            marker.is_file()
            and _hash_file(marker) == audit["shared_global_pause"]["sha256"]
        )
        audit.update(
            {
                "state": "REVOKED",
                "revoked_at_utc": _iso(_utc_now()),
                "shared_global_pause_after": {
                    "path": str(marker),
                    "present": marker.is_file(),
                    "sha256": _hash_file(marker),
                    "unchanged": unchanged,
                },
                "v1_daily_app_after": processes,
                "v1_daily_app_state_after": _v1_process_state(processes),
                "v1_daily_app_continuity": _v1_process_state_stable(
                    list(audit["v1_daily_app_before"]), processes
                ),
                "v1_provider_calls_authorized_by_v2_lease": 0,
                "public_writes": 0,
            }
        )
        _atomic_json(lease.audit_path, audit)
        payload = json.loads(lease.lease_path.read_text(encoding="utf-8"))
        payload.update({"state": "REVOKED", "revoked_at_utc": audit["revoked_at_utc"]})
        _atomic_json(lease.lease_path, payload)
