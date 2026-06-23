"""Deterministic kill-switch policy for local dispatch preparation.

This module never enables live dispatch. It only classifies whether local outbox
preparation may proceed and records manual fallback state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_OUTBOX_IDEMPOTENCY_KILL_SWITCH_AUDIT_R1_COMPLETION_PATCH_V0"
MODEL = "contentops.kill_switch_policy"
MODEL_VERSION = "0174U2_KILL_SWITCH_POLICY_R1"

KILL_SWITCH_CLEAR = "kill_switch_clear"
KILL_SWITCH_ENGAGED = "kill_switch_engaged"
KILL_SWITCH_UNKNOWN = "kill_switch_unknown_fail_closed"

KILL_SWITCH_SCOPE_INACTIVE = "inactive"
KILL_SWITCH_SCOPE_GLOBAL_ACTIVE = "global_active"
KILL_SWITCH_SCOPE_PLATFORM_ACTIVE = "platform_active"

MANUAL_FALLBACK_NOT_REQUIRED = "manual_fallback_not_required"
MANUAL_FALLBACK_REQUIRED = "manual_fallback_required_operator_review"


@dataclass(frozen=True)
class KillSwitchDecision:
    """Value-only kill-switch decision."""

    status: str
    local_outbox_allowed: bool
    manual_fallback_state: str
    blocked_reasons: tuple[str, ...]
    live_readiness_blocked: bool = True
    does_not_block_preview: bool = True
    does_not_delete_outbox: bool = True
    dispatch_performed: bool = False
    live_request_performed: bool = False
    platform_api_called: bool = False
    credential_hydrated: bool = False
    auto_retry_allowed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": self.status,
            "local_outbox_allowed": self.local_outbox_allowed,
            "manual_fallback_state": self.manual_fallback_state,
            "blocked_reasons": list(self.blocked_reasons),
            "live_readiness_blocked": self.live_readiness_blocked,
            "does_not_block_preview": self.does_not_block_preview,
            "does_not_delete_outbox": self.does_not_delete_outbox,
            "dispatch_performed": self.dispatch_performed,
            "live_request_performed": self.live_request_performed,
            "platform_api_called": self.platform_api_called,
            "credential_hydrated": self.credential_hydrated,
            "auto_retry_allowed": self.auto_retry_allowed,
        }


def build_global_kill_switch_state(
    active: bool,
    reason: str,
    operator_id: str,
    activated_at: str,
    expires_at: str | None = None,
) -> dict[str, Any]:
    """Build deterministic global kill switch state."""
    scope = KILL_SWITCH_SCOPE_GLOBAL_ACTIVE if active else KILL_SWITCH_SCOPE_INACTIVE
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "scope": scope,
        "kill_switch_active": bool(active),
        "kill_switch_engaged": bool(active),
        "target_platform_ids": [],
        "allow_local_outbox": not active,
        "live_dispatch_enabled": False,
        "reason": reason,
        "operator_id": operator_id,
        "activated_at": activated_at,
        "expires_at": expires_at,
        "does_not_block_preview": True,
        "does_not_delete_outbox": True,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }


def build_platform_kill_switch_state(
    platform_id: str,
    active: bool,
    reason: str,
    operator_id: str,
    activated_at: str,
    expires_at: str | None = None,
) -> dict[str, Any]:
    """Build deterministic platform-scoped kill switch state."""
    scope = KILL_SWITCH_SCOPE_PLATFORM_ACTIVE if active else KILL_SWITCH_SCOPE_INACTIVE
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "scope": scope,
        "kill_switch_active": bool(active),
        "kill_switch_engaged": bool(active),
        "target_platform_ids": [platform_id] if platform_id else [],
        "allow_local_outbox": not active,
        "live_dispatch_enabled": False,
        "reason": reason,
        "operator_id": operator_id,
        "activated_at": activated_at,
        "expires_at": expires_at,
        "does_not_block_preview": True,
        "does_not_delete_outbox": True,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }


def is_kill_switch_blocking_platform(state: dict[str, Any] | None, platform_id: str) -> bool:
    """Return true when global or matching platform switch blocks live readiness."""
    if not state or state.get("kill_switch_active") is not True:
        return False
    scope = state.get("scope")
    if scope == KILL_SWITCH_SCOPE_GLOBAL_ACTIVE:
        return True
    if scope == KILL_SWITCH_SCOPE_PLATFORM_ACTIVE:
        return platform_id in set(state.get("target_platform_ids") or [])
    if state.get("kill_switch_engaged") is True:
        targets = set(state.get("target_platform_ids") or [])
        return not targets or platform_id in targets
    return False


def explain_kill_switch_blocker(state: dict[str, Any] | None, platform_id: str) -> dict[str, Any]:
    """Explain kill-switch blocker while preserving preview/outbox invariants."""
    blocking = is_kill_switch_blocking_platform(state, platform_id)
    if not state:
        scope = KILL_SWITCH_SCOPE_INACTIVE
        reason = "kill_switch_state_missing"
        operator_id = None
        activated_at = None
        expires_at = None
    else:
        scope = state.get("scope") or KILL_SWITCH_SCOPE_INACTIVE
        reason = state.get("reason")
        operator_id = state.get("operator_id")
        activated_at = state.get("activated_at")
        expires_at = state.get("expires_at")
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "platform_id": platform_id,
        "scope": scope,
        "blocking": blocking,
        "reason": reason,
        "operator_id": operator_id,
        "activated_at": activated_at,
        "expires_at": expires_at,
        "blocked_reasons": [f"kill_switch_{scope}"] if blocking else [],
        "does_not_block_preview": True,
        "does_not_delete_outbox": True,
        "live_readiness_blocked": blocking,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }


def evaluate_kill_switch(state: dict[str, Any] | None, platform_id: str | None = None) -> KillSwitchDecision:
    """Evaluate explicit local-outbox kill-switch state fail-closed."""
    if not state:
        return KillSwitchDecision(
            status=KILL_SWITCH_UNKNOWN,
            local_outbox_allowed=False,
            manual_fallback_state=MANUAL_FALLBACK_REQUIRED,
            blocked_reasons=("kill_switch_state_missing",),
            live_readiness_blocked=True,
        )

    platform = platform_id or state.get("platform_id") or ""
    if state.get("live_dispatch_enabled") is True:
        return KillSwitchDecision(
            status=KILL_SWITCH_ENGAGED,
            local_outbox_allowed=False,
            manual_fallback_state=MANUAL_FALLBACK_REQUIRED,
            blocked_reasons=("live_dispatch_enabled_not_allowed",),
            live_readiness_blocked=True,
        )

    if is_kill_switch_blocking_platform(state, platform):
        explanation = explain_kill_switch_blocker(state, platform)
        return KillSwitchDecision(
            status=KILL_SWITCH_ENGAGED,
            local_outbox_allowed=False,
            manual_fallback_state=MANUAL_FALLBACK_REQUIRED,
            blocked_reasons=tuple(explanation["blocked_reasons"] or ["kill_switch_engaged"]),
            live_readiness_blocked=True,
        )

    if state.get("kill_switch_engaged") is True and not state.get("scope"):
        return KillSwitchDecision(
            status=KILL_SWITCH_ENGAGED,
            local_outbox_allowed=False,
            manual_fallback_state=MANUAL_FALLBACK_REQUIRED,
            blocked_reasons=("kill_switch_engaged",),
            live_readiness_blocked=True,
        )

    if state.get("allow_local_outbox") is True or state.get("scope") == KILL_SWITCH_SCOPE_INACTIVE:
        return KillSwitchDecision(
            status=KILL_SWITCH_CLEAR,
            local_outbox_allowed=True,
            manual_fallback_state=MANUAL_FALLBACK_NOT_REQUIRED,
            blocked_reasons=(),
            live_readiness_blocked=False,
        )

    return KillSwitchDecision(
        status=KILL_SWITCH_UNKNOWN,
        local_outbox_allowed=False,
        manual_fallback_state=MANUAL_FALLBACK_REQUIRED,
        blocked_reasons=("explicit_local_outbox_allow_missing",),
        live_readiness_blocked=True,
    )


def no_auto_retry_policy() -> dict[str, Any]:
    """Hard no-auto-retry policy for dispatch preparation layer."""
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "auto_retry_allowed": False,
        "retry_loop_enabled": False,
        "scheduler_enabled": False,
        "manual_operator_review_required_after_block": True,
        "request_budget": 1,
    }


def kill_switch_policy_packet() -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "helper_api_completed": [
            "build_global_kill_switch_state",
            "build_platform_kill_switch_state",
            "is_kill_switch_blocking_platform",
            "explain_kill_switch_blocker",
        ],
        "states": [KILL_SWITCH_CLEAR, KILL_SWITCH_ENGAGED, KILL_SWITCH_UNKNOWN],
        "scopes": [KILL_SWITCH_SCOPE_INACTIVE, KILL_SWITCH_SCOPE_GLOBAL_ACTIVE, KILL_SWITCH_SCOPE_PLATFORM_ACTIVE],
        "manual_fallback_states": [MANUAL_FALLBACK_NOT_REQUIRED, MANUAL_FALLBACK_REQUIRED],
        "global_kill_switch_blocks_every_platform": True,
        "platform_kill_switch_blocks_only_selected_platform": True,
        "inactive_kill_switch_does_not_block_preview_or_approval": True,
        "active_kill_switch_does_not_delete_outbox": True,
        "active_kill_switch_blocks_live_readiness": True,
        "does_not_block_preview": True,
        "does_not_delete_outbox": True,
        "fail_closed_on_missing_state": True,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }
