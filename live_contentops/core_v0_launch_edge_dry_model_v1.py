"""Launch-edge dry model: the minimum SHADOW_ONLY proof of a future live cohort.

Work Package E, scope item E. This module builds **no** new approval engine and **no**
new outbox. It composes accepted components:

* :mod:`live_contentops.approval_payload_hash` — canonical payload hash input;
* :mod:`live_contentops.approval_ledger_revocation_expiration_contract` — validity
  windows, revocation, expiry, and the hash/scope match assessment;
* :mod:`live_contentops.idempotency_policy` — operation-level idempotency keys and the
  never-blind-retry duplicate classification;
* :mod:`live_contentops.kill_switch_policy` — fail-closed kill-switch evaluation.

What this module adds is only the missing seam: a *release intent* that binds all eight
required hashes at once, an authorization actor that can be either autonomous policy or
an operator decision, and a deterministic unknown-write / reconciliation classifier.

Nothing here executes. There is no dispatch, no outbox execution, no credential read, no
provider or network call, and no platform action. Every simulated operation is a local
state transition over immutable bytes, and every artifact carries the zero-live-action
envelope.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from live_contentops.approval_payload_hash import (
    canonical_payload_hash_input,
    compute_payload_hash,
)
from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import (
    _canonical_json,
    _logical_hash,
    zero_live_action_flags,
)
from live_contentops.idempotency_policy import (
    classify_duplicate_action,
    compute_idempotency_key,
)
from live_contentops.kill_switch_policy import (
    build_global_kill_switch_state,
    evaluate_kill_switch,
)

SCHEMA_VERSION = "contentops.core_v0_launch_edge_dry_model.v1"
OPERATING_MODE = "SHADOW_ONLY"

#: The current product modes. A future live release may be authorized either by exact
#: autonomous policy under an owner-authorized live scope, or through a supervised
#: operator gate. Human approval is deliberately *not* universally mandatory.
MODE_AUTONOMOUS_DEFAULT = "AUTONOMOUS_DEFAULT"
MODE_SUPERVISED_OPERATOR_GATE = "SUPERVISED_OPERATOR_GATE"
MODE_SHADOW_ONLY = "SHADOW_ONLY"
MODE_KILL_SWITCH = "KILL_SWITCH"
OPERATING_MODES: tuple[str, ...] = (
    MODE_AUTONOMOUS_DEFAULT,
    MODE_SUPERVISED_OPERATOR_GATE,
    MODE_SHADOW_ONLY,
    MODE_KILL_SWITCH,
)

#: The two authorization actors. Both must bind immutable bytes and deterministic gates;
#: neither is a boolean flag.
ACTOR_AUTONOMOUS_POLICY = "AUTONOMOUS_POLICY"
ACTOR_OPERATOR_DECISION = "OPERATOR_DECISION"
AUTHORIZATION_ACTORS: tuple[str, ...] = (ACTOR_AUTONOMOUS_POLICY, ACTOR_OPERATOR_DECISION)

#: The eight bindings a release authorization must carry. A release intent missing any
#: one of these is refused; that is what makes approval hash-bound rather than boolean.
REQUIRED_RELEASE_BINDINGS: tuple[str, ...] = (
    "package_hash",
    "evidence_hash",
    "visual_hash",
    "variant_hash",
    "policy_hash",
    "platform_id",
    "account_binding_id",
    "freshness_hash",
)

#: Simulated write outcomes. UNKNOWN is the dangerous one: a write may or may not have
#: landed, so it must never be blind-retried.
WRITE_CONFIRMED = "CONFIRMED"
WRITE_UNKNOWN = "UNKNOWN"
RECONCILED_CONFIRMED = "RECONCILED_CONFIRMED"
RECONCILED_ABSENT_SAFE_TO_RETRY = "RECONCILED_ABSENT_SAFE_TO_RETRY"
RECONCILIATION_PENDING = "RECONCILIATION_PENDING_OPERATOR_RECOVERY"


class LaunchEdgeError(RuntimeError):
    """Fail-closed launch-edge composition error."""


# ---------------------------------------------------------------------------
# Release intent
# ---------------------------------------------------------------------------


def build_release_intent(
    *,
    case_id: str,
    logical_day_id: str,
    platform_id: str,
    account_binding_id: str,
    package: Mapping[str, Any],
    variant: Mapping[str, Any],
    policy_hash: str,
    freshness: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind exact immutable bytes into one release intent.

    The intent is the unit a future live cohort would consume. It carries the eight
    required hashes and a single ``release_intent_hash`` over all of them, so any change
    to the package, its evidence, its visual, the chosen variant, the calibration policy,
    the destination, the account binding, or the freshness basis produces a different
    intent and invalidates any authorization bound to the old one.
    """
    evidence_hash = _logical_hash(package.get("evidence") or package.get("citations") or [])
    visual_hash = _logical_hash(
        package.get("visual_adaptation") or package.get("visual_strategy") or {}
    )
    bindings = {
        "package_hash": _logical_hash(package),
        "evidence_hash": evidence_hash,
        "visual_hash": visual_hash,
        "variant_hash": _logical_hash(variant),
        "policy_hash": str(policy_hash),
        "platform_id": str(platform_id),
        "account_binding_id": str(account_binding_id),
        "freshness_hash": _logical_hash(freshness),
    }
    missing = [name for name in REQUIRED_RELEASE_BINDINGS if not bindings.get(name)]
    if missing:
        raise LaunchEdgeError(f"release_intent_missing_bindings:{','.join(sorted(missing))}")

    intent = {
        "schema_version": SCHEMA_VERSION,
        "release_intent_id": f"ri_{_logical_hash(bindings)[:24]}",
        "case_id": str(case_id),
        "logical_day_id": str(logical_day_id),
        "operating_mode": OPERATING_MODE,
        "bindings": bindings,
        "bound_binding_names": list(REQUIRED_RELEASE_BINDINGS),
        "boolean_approval_accepted_as_authority": False,
        "payload_rebuilt_after_authorization": False,
        **zero_live_action_flags(),
    }
    intent["release_intent_hash"] = _logical_hash(bindings)
    return intent


def authorize_release(
    *,
    intent: Mapping[str, Any],
    actor: str,
    actor_ref: str,
    operating_mode: str,
    logical_now_utc: str,
    valid_for_seconds: int = 3600,
    autonomous_scope_id: str | None = None,
    operator_decision_id: str | None = None,
) -> dict[str, Any]:
    """Authorize one release intent under an explicit authorization actor.

    Both actors are first-class. ``AUTONOMOUS_POLICY`` requires an exact owner-authorized
    live scope identifier; ``OPERATOR_DECISION`` requires an exact operator decision
    identifier. Neither is a boolean: the authorization binds the intent hash, and any
    later byte change invalidates it.
    """
    if actor not in AUTHORIZATION_ACTORS:
        raise LaunchEdgeError(f"unknown_authorization_actor:{actor}")
    if operating_mode not in OPERATING_MODES:
        raise LaunchEdgeError(f"unknown_operating_mode:{operating_mode}")

    blockers: list[str] = []
    if actor == ACTOR_AUTONOMOUS_POLICY and not autonomous_scope_id:
        blockers.append("autonomous_policy_requires_exact_owner_authorized_live_scope")
    if actor == ACTOR_OPERATOR_DECISION and not operator_decision_id:
        blockers.append("operator_decision_requires_exact_decision_id")
    # This task is SHADOW_ONLY. An authorization may be *modelled* but can never be
    # valid for live dispatch from here.
    blockers.append("shadow_only_task_grants_no_live_dispatch_authority")

    authorization = {
        "schema_version": SCHEMA_VERSION,
        "authorization_id": f"auth_{_logical_hash([intent['release_intent_hash'], actor, actor_ref])[:24]}",
        "release_intent_id": str(intent["release_intent_id"]),
        "bound_release_intent_hash": str(intent["release_intent_hash"]),
        "authorization_actor": actor,
        "authorization_actor_ref": str(actor_ref),
        "autonomous_scope_id": autonomous_scope_id,
        "operator_decision_id": operator_decision_id,
        "operating_mode": operating_mode,
        "human_approval_universally_mandatory": False,
        "authorized_at_utc": str(logical_now_utc),
        "expires_at_utc": _add_seconds(str(logical_now_utc), valid_for_seconds),
        "valid_for_seconds": int(valid_for_seconds),
        "boolean_approval_accepted_as_authority": False,
        "valid_for_live_dispatch_now": False,
        "blocked_reasons": sorted(set(blockers)),
        **zero_live_action_flags(),
    }
    authorization["authorization_hash"] = _logical_hash(
        {k: v for k, v in authorization.items() if k != "authorization_hash"}
    )
    return authorization


def _add_seconds(iso_utc: str, seconds: int) -> str:
    from live_contentops.core_v0_repeated_shadow_soak_v1 import _iso, _parse_utc
    from datetime import timedelta

    return _iso(_parse_utc(iso_utc) + timedelta(seconds=int(seconds)))


def revalidate_authorization(
    *,
    authorization: Mapping[str, Any],
    intent: Mapping[str, Any],
    logical_now_utc: str,
) -> dict[str, Any]:
    """Re-check an authorization against the current intent bytes and logical time.

    This is the expiry-and-invalidation gate. If the bound bytes changed, or the
    authorization has expired, it is refused — no post-authorization payload rebuild is
    ever accepted.
    """
    from live_contentops.core_v0_repeated_shadow_soak_v1 import _parse_utc

    bytes_match = str(authorization["bound_release_intent_hash"]) == str(
        intent["release_intent_hash"]
    )
    expired = _parse_utc(str(logical_now_utc)) >= _parse_utc(str(authorization["expires_at_utc"]))
    blockers = list(authorization.get("blocked_reasons") or [])
    if not bytes_match:
        blockers.append("bound_bytes_changed_authorization_invalidated")
    if expired:
        blockers.append("authorization_expired")

    result = {
        "schema_version": SCHEMA_VERSION,
        "authorization_id": str(authorization["authorization_id"]),
        "release_intent_id": str(intent["release_intent_id"]),
        "evaluated_at_utc": str(logical_now_utc),
        "bound_bytes_match": bytes_match,
        "expired": expired,
        "still_valid": bytes_match and not expired,
        "valid_for_live_dispatch_now": False,
        "payload_rebuilt_after_authorization": False,
        "blocked_reasons": sorted(set(blockers)),
        **zero_live_action_flags(),
    }
    result["revalidation_hash"] = _logical_hash(result)
    return result


# ---------------------------------------------------------------------------
# Simulated operations, idempotency, and unknown-write reconciliation
# ---------------------------------------------------------------------------


def build_simulated_operation(
    *,
    intent: Mapping[str, Any],
    authorization: Mapping[str, Any],
    destination_binding_id: str,
    payload_text: str,
    media_manifest_hash: str,
    policy_snapshot_id: str,
    existing_keys: Sequence[str] = (),
) -> dict[str, Any]:
    """Build one simulated, idempotent, non-executing operation for one destination.

    The idempotency key is derived by the accepted
    :func:`live_contentops.idempotency_policy.compute_idempotency_key`, so a repeated
    operation for identical bytes collapses to the same key and is suppressed.
    """
    platform_id = str(intent["bindings"]["platform_id"])
    hash_input = canonical_payload_hash_input(
        platform_id=platform_id,
        destination_binding_id=str(destination_binding_id),
        credential_handle_id="SHADOW_ONLY_NO_CREDENTIAL_HANDLE",
        payload_schema_version=SCHEMA_VERSION,
        adapter_version="shadow_only_no_adapter",
        payload_class_id="core_v0_soak_shadow_package",
        payload_text=str(payload_text),
        platform_formatting=platform_id,
        media_manifest_hash=str(media_manifest_hash),
        policy_snapshot_id=str(policy_snapshot_id),
    )
    payload_hash = compute_payload_hash(hash_input)

    candidate = {
        "payload_hash": payload_hash,
        "platform_id": platform_id,
        "payload_class_id": "core_v0_soak_shadow_package",
        "destination_binding_id": str(destination_binding_id),
        "credential_handle_id": "SHADOW_ONLY_NO_CREDENTIAL_HANDLE",
        "media_manifest_hash": str(media_manifest_hash),
        "policy_snapshot_id": str(policy_snapshot_id),
        "approval_ledger_entry_id": str(authorization["authorization_id"]),
        "approval_event_id": str(authorization["authorization_hash"]),
        "dispatch_intent_class": "shadow_only_simulated_no_dispatch",
    }
    idempotency_key = compute_idempotency_key(candidate)
    duplicate = idempotency_key in set(existing_keys)

    operation = {
        "schema_version": SCHEMA_VERSION,
        "operation_id": f"op_{idempotency_key[:24]}",
        "release_intent_id": str(intent["release_intent_id"]),
        "authorization_id": str(authorization["authorization_id"]),
        "platform_id": platform_id,
        "destination_binding_id": str(destination_binding_id),
        "payload_hash": payload_hash,
        "idempotency_key": idempotency_key,
        "duplicate_suppressed": duplicate,
        "operation_status": "SIMULATED_NOT_EXECUTED",
        "outbox_executed": False,
        "platform_action_performed": False,
        "credential_hydrated": False,
        "valid_for_live_dispatch_now": False,
        **zero_live_action_flags(),
    }
    operation["operation_hash"] = _logical_hash(operation)
    return operation


def classify_unknown_write(
    *,
    operation: Mapping[str, Any],
    readback_present: bool | None,
) -> dict[str, Any]:
    """Classify a simulated write whose readback may be unknown.

    Three outcomes, and only one of them permits another attempt:

    * ``readback_present is True`` — reconciliation found the object; the operation is
      confirmed and must **not** be retried;
    * ``readback_present is False`` — reconciliation proved nothing was created; the
      operation is safe to retry under the *same* idempotency key;
    * ``readback_present is None`` — reconciliation is absent; the state stays UNKNOWN,
      auto-retry is forbidden, and an operator recovery is required.
    """
    if readback_present is True:
        state = RECONCILED_CONFIRMED
        auto_retry = False
        reason = "reconciliation_found_object_no_retry"
    elif readback_present is False:
        state = RECONCILED_ABSENT_SAFE_TO_RETRY
        auto_retry = False
        reason = "reconciliation_proved_absent_retry_allowed_under_same_idempotency_key"
    else:
        state = RECONCILIATION_PENDING
        auto_retry = False
        reason = "unknown_write_unreconciled_operator_recovery_required"

    duplicate_class = classify_duplicate_action(
        {"status": "unknown_result"} if readback_present is None else {"status": "ok"}
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "operation_id": str(operation["operation_id"]),
        "idempotency_key": str(operation["idempotency_key"]),
        "initial_write_state": WRITE_UNKNOWN,
        "readback_present": readback_present,
        "resolution_state": state,
        "auto_retry_allowed": auto_retry,
        "blind_retry_performed": False,
        "duplicate_simulated_object_created": False,
        "retry_would_reuse_same_idempotency_key": True,
        "safe_to_retry": state == RECONCILED_ABSENT_SAFE_TO_RETRY,
        "requires_operator_recovery": state == RECONCILIATION_PENDING,
        "reason": reason,
        "idempotency_duplicate_action": duplicate_class["duplicate_action"],
        "idempotency_auto_retry_allowed": duplicate_class["auto_retry_allowed"],
        **zero_live_action_flags(),
    }
    result["reconciliation_hash"] = _logical_hash(result)
    return result


def evaluate_release_queue_under_kill_switch(
    *,
    operations: Sequence[Mapping[str, Any]],
    kill_switch_active: bool,
    operator_id: str = "soak_drill_operator",
    activated_at: str = "2026-07-15T00:00:00Z",
) -> dict[str, Any]:
    """Process a simulated release queue with the kill switch engaged.

    Uses the accepted fail-closed :func:`evaluate_kill_switch`. When engaged, no
    operation may be processed, and the queue must be preserved rather than deleted.
    """
    state = build_global_kill_switch_state(
        active=bool(kill_switch_active),
        reason="soak_drill_kill_switch_engaged" if kill_switch_active else "soak_drill_clear",
        operator_id=operator_id,
        activated_at=activated_at,
    )
    decision = evaluate_kill_switch(state)
    blocked = bool(kill_switch_active) or not bool(decision.local_outbox_allowed)
    result = {
        "schema_version": SCHEMA_VERSION,
        "kill_switch_active": bool(kill_switch_active),
        "kill_switch_status": decision.status,
        "queued_operation_count": len(operations),
        "operations_processed": 0 if blocked else 0,
        "operations_blocked": len(operations) if blocked else 0,
        "queue_preserved_not_deleted": True,
        "outbox_executed": False,
        "platform_action_performed": False,
        "blocked_reasons": list(decision.blocked_reasons),
        **zero_live_action_flags(),
    }
    result["kill_switch_evaluation_hash"] = _logical_hash(result)
    return result
