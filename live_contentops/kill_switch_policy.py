"""Deterministic kill-switch policy for local dispatch preparation.

This module never enables live dispatch. It only classifies whether local outbox
preparation may proceed and records manual fallback state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_OUTBOX_IDEMPOTENCY_KILL_SWITCH_AUDIT_V0"
MODEL = "contentops.kill_switch_policy"
MODEL_VERSION = "0174U2_KILL_SWITCH_POLICY_V1"

KILL_SWITCH_CLEAR = "kill_switch_clear"
KILL_SWITCH_ENGAGED = "kill_switch_engaged"
KILL_SWITCH_UNKNOWN = "kill_switch_unknown_fail_closed"

MANUAL_FALLBACK_NOT_REQUIRED = "manual_fallback_not_required"
MANUAL_FALLBACK_REQUIRED = "manual_fallback_required_operator_review"


@dataclass(frozen=True)
class KillSwitchDecision:
    """Value-only kill-switch decision."""

    status: str
    local_outbox_allowed: bool
    manual_fallback_state: str
    blocked_reasons: tuple[str, ...]
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
            "dispatch_performed": self.dispatch_performed,
            "live_request_performed": self.live_request_performed,
            "platform_api_called": self.platform_api_called,
            "credential_hydrated": self.credential_hydrated,
            "auto_retry_allowed": self.auto_retry_allowed,
        }


def evaluate_kill_switch(state: dict[str, Any] | None) -> KillSwitchDecision:
    """Evaluate explicit local-outbox kill-switch state fail-closed."""
    if not state:
        return KillSwitchDecision(
            status=KILL_SWITCH_UNKNOWN,
            local_outbox_allowed=False,
            manual_fallback_state=MANUAL_FALLBACK_REQUIRED,
            blocked_reasons=("kill_switch_state_missing",),
        )

    if state.get("live_dispatch_enabled") is True:
        return KillSwitchDecision(
            status=KILL_SWITCH_ENGAGED,
            local_outbox_allowed=False,
            manual_fallback_state=MANUAL_FALLBACK_REQUIRED,
            blocked_reasons=("live_dispatch_enabled_not_allowed",),
        )

    if state.get("kill_switch_engaged") is True:
        return KillSwitchDecision(
            status=KILL_SWITCH_ENGAGED,
            local_outbox_allowed=False,
            manual_fallback_state=MANUAL_FALLBACK_REQUIRED,
            blocked_reasons=("kill_switch_engaged",),
        )

    if state.get("allow_local_outbox") is True and state.get("snapshot_id"):
        return KillSwitchDecision(
            status=KILL_SWITCH_CLEAR,
            local_outbox_allowed=True,
            manual_fallback_state=MANUAL_FALLBACK_NOT_REQUIRED,
            blocked_reasons=(),
        )

    return KillSwitchDecision(
        status=KILL_SWITCH_UNKNOWN,
        local_outbox_allowed=False,
        manual_fallback_state=MANUAL_FALLBACK_REQUIRED,
        blocked_reasons=("explicit_local_outbox_allow_missing",),
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
    }


def kill_switch_policy_packet() -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "states": [KILL_SWITCH_CLEAR, KILL_SWITCH_ENGAGED, KILL_SWITCH_UNKNOWN],
        "manual_fallback_states": [MANUAL_FALLBACK_NOT_REQUIRED, MANUAL_FALLBACK_REQUIRED],
        "fail_closed_on_missing_state": True,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }
