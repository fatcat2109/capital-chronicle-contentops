"""Deterministic live-gate state machine for future supervised dispatch.

Pure state classification only. It never performs requests, hydrates credentials,
reads env, or enables live dispatch.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .account_binding_permission_scope_verifier import bindings_by_platform_id
from .approval_payload_hash import payload_hash_short
from .platform_scope_permission_contract import contracts_by_platform_id
from .platform_universe_registry_v2 import build_platform_universe_registry_v2
from .primary_payload_classes_contract import build_primary_payload_classes

TASK_LABEL = "TASK_CONTENTOPS_LIVE_GATE_STATE_MACHINE_AND_ERROR_CLASSIFIER_CORE_V0"
MODEL = "contentops.live_gate_state_machine"
MODEL_VERSION = "0175_LIVE_GATE_STATE_MACHINE_V0"

GATE_STATES = (
    "not_started",
    "blocked_by_platform_registry",
    "blocked_by_docs",
    "blocked_by_destination_binding",
    "blocked_by_scope_permission",
    "blocked_by_credential_handle",
    "blocked_by_approval",
    "blocked_by_outbox",
    "blocked_by_idempotency",
    "blocked_by_kill_switch",
    "blocked_by_audit_sink",
    "blocked_by_request_budget",
    "blocked_by_media_requirement",
    "blocked_by_app_review",
    "blocked_by_paid_or_quota_gate",
    "blocked_by_read_only_probe_required",
    "blocked_by_live_write_policy",
    "manual_fallback_required",
    "future_supervised_live_candidate",
    "live_dispatch_forbidden_now",
)

APP_REVIEW_PLATFORMS = {
    "linkedin_member_profile",
    "linkedin_organization_page",
    "threads_profile",
    "instagram_professional_account",
    "facebook_page",
    "tiktok_account",
    "youtube_channel",
}
PAID_OR_QUOTA_PLATFORMS = {"x_profile", "tiktok_account", "youtube_channel"}
MEDIA_GATED_PLATFORMS = {"instagram_professional_account", "tiktok_account", "youtube_channel"}
META_FAMILY = {"threads_profile", "instagram_professional_account", "facebook_page"}


@dataclass(frozen=True)
class LiveGateContext:
    platform_id: str
    payload_class_id: str
    destination_binding_id: str
    credential_handle_id: str
    payload_hash_short: str
    outbox_id: str | None = None
    platform_registry_present: bool = True
    docs_status: str = "official_docs_checked_current"
    destination_binding_status: str = "operator_confirmation_missing_blocked"
    permission_status: str = "permission_unverified_blocked"
    scope_status: str = "scope_unverified_blocked"
    account_binding_status: str = "operator_confirmation_missing_blocked"
    approval_status: str = "not_requested"
    outbox_status: str = "missing"
    idempotency_status: str = "missing"
    idempotency_duplicate: bool = False
    kill_switch_status: str = "kill_switch_unknown_fail_closed"
    audit_sink_ready: bool = False
    request_budget_used: int = 0
    media_requirement_satisfied: bool = False
    app_review_satisfied: bool = False
    paid_or_quota_gate_satisfied: bool = False
    read_only_probe_required_before_live: bool = True
    future_live_candidate_requested: bool = False
    public_destination_allowed_future: bool = False
    manual_fallback_required: bool = True
    re_ground_required_before_live: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LiveGateEvaluation:
    platform_id: str
    payload_class_id: str
    destination_binding_id: str
    credential_handle_id: str
    payload_hash_short: str
    outbox_id: str | None
    gate_state: str
    gate_passed_now: bool
    valid_for_live_dispatch_now: bool
    future_live_candidate_allowed_after_gates: bool
    blocked_reasons: tuple[str, ...]
    required_repairs: tuple[str, ...]
    manual_fallback_required: bool
    re_ground_required_before_live: bool
    request_budget: int
    auto_retry_allowed: bool
    no_live_api_call_performed: bool
    credential_hydration_performed: bool
    raw_response_persisted: bool

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["blocked_reasons"] = list(self.blocked_reasons)
        data["required_repairs"] = list(self.required_repairs)
        return data


def _registry_by_platform() -> dict[str, Any]:
    return {row.platform_id: row for row in build_platform_universe_registry_v2()}


def _payloads_by_platform() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in build_primary_payload_classes():
        result.setdefault(row.platform_id, row)
    return result


def build_live_gate_context(
    platform_id: str,
    payload_class_id: str | None = None,
    destination_binding_id: str | None = None,
    credential_handle_id: str | None = None,
    payload_hash_short_value: str | None = None,
    outbox_id: str | None = None,
    platform_registry: dict[str, Any] | None = None,
    docs_packet: dict[str, Any] | None = None,
    binding_packet: dict[str, Any] | None = None,
    approval_packet: dict[str, Any] | None = None,
    outbox_packet: dict[str, Any] | None = None,
    idempotency_packet: dict[str, Any] | None = None,
    kill_switch_packet: dict[str, Any] | None = None,
    audit_packet: dict[str, Any] | None = None,
    request_budget_used: int = 0,
    media_requirement_satisfied: bool | None = None,
    app_review_satisfied: bool | None = None,
    paid_or_quota_gate_satisfied: bool | None = None,
    read_only_probe_required_before_live: bool = True,
    future_live_candidate_requested: bool = False,
) -> LiveGateContext:
    registry = _registry_by_platform()
    payloads = _payloads_by_platform()
    bindings = bindings_by_platform_id()
    contracts = contracts_by_platform_id()
    reg = platform_registry if platform_registry is not None else (asdict(registry[platform_id]) if platform_id in registry else None)
    payload = payloads.get(platform_id)
    binding = binding_packet or (bindings.get(platform_id).as_dict() if platform_id in bindings else {})
    contract = contracts.get(platform_id)
    default_hash = payload_hash_short_value or payload_hash_short((platform_id + ":symbolic_payload").encode().hex().ljust(64, "0")[:64])

    return LiveGateContext(
        platform_id=platform_id,
        payload_class_id=payload_class_id or (payload.payload_class_id if payload else "missing_payload_class"),
        destination_binding_id=destination_binding_id if destination_binding_id is not None else str(binding.get("destination_binding_id") or ""),
        credential_handle_id=credential_handle_id if credential_handle_id is not None else str(binding.get("credential_handle_id") or ""),
        payload_hash_short=default_hash,
        outbox_id=outbox_id or ((outbox_packet or {}).get("outbox_id") or (outbox_packet or {}).get("outbox_entry_id")),
        platform_registry_present=reg is not None,
        docs_status=str((docs_packet or {}).get("docs_status") or binding.get("official_docs_status") or "official_docs_missing"),
        destination_binding_status=str(binding.get("account_binding_status") or "destination_binding_missing"),
        permission_status=str(binding.get("permission_status") or "permission_missing"),
        scope_status=str(binding.get("scope_status") or "scope_missing"),
        account_binding_status=str(binding.get("wrong_account_detection_status") or "not_checked_blocked"),
        approval_status=str((approval_packet or {}).get("approval_status") or (approval_packet or {}).get("status") or "not_requested"),
        outbox_status=str((outbox_packet or {}).get("status") or "missing"),
        idempotency_status=str((idempotency_packet or {}).get("status") or "missing"),
        idempotency_duplicate=bool((idempotency_packet or {}).get("duplicate") is True),
        kill_switch_status=str((kill_switch_packet or {}).get("status") or "kill_switch_unknown_fail_closed"),
        audit_sink_ready=bool((audit_packet or {}).get("ready") is True or (audit_packet or {}).get("audit_sink_ready") is True),
        request_budget_used=request_budget_used,
        media_requirement_satisfied=bool(media_requirement_satisfied) if media_requirement_satisfied is not None else (platform_id not in MEDIA_GATED_PLATFORMS),
        app_review_satisfied=bool(app_review_satisfied) if app_review_satisfied is not None else (platform_id not in APP_REVIEW_PLATFORMS),
        paid_or_quota_gate_satisfied=bool(paid_or_quota_gate_satisfied) if paid_or_quota_gate_satisfied is not None else (platform_id not in PAID_OR_QUOTA_PLATFORMS),
        read_only_probe_required_before_live=read_only_probe_required_before_live,
        future_live_candidate_requested=future_live_candidate_requested,
        public_destination_allowed_future=bool(contract.public_destination_allowed_future) if contract else False,
        manual_fallback_required=True,
        re_ground_required_before_live=True,
    )


def derive_live_gate_blockers(context: LiveGateContext | dict[str, Any]) -> tuple[str, ...]:
    ctx = context if isinstance(context, LiveGateContext) else LiveGateContext(**context)
    blockers: list[str] = []
    if not ctx.platform_registry_present:
        blockers.append("platform_registry_missing")
    if ctx.docs_status not in {"official_docs_checked_current", "official_docs_checked"}:
        blockers.append("official_docs_not_current")
    if not ctx.destination_binding_id or "missing" in ctx.destination_binding_status or "blocked" in ctx.destination_binding_status:
        blockers.append("destination_binding_not_verified")
    if "unverified" in ctx.permission_status or "verified" not in ctx.permission_status:
        blockers.append("permission_not_verified")
    if "unverified" in ctx.scope_status or "verified" not in ctx.scope_status:
        blockers.append("scope_not_verified")
    if not ctx.credential_handle_id:
        blockers.append("credential_handle_missing")
    if ctx.approval_status != "approved_current":
        blockers.append("approval_not_current")
    if ctx.outbox_status in {"", "missing", "blocked_by_approval", "blocked_by_kill_switch", "blocked_by_duplicate", "blocked_by_audit_sink"}:
        blockers.append("outbox_not_ready")
    if ctx.idempotency_duplicate or ctx.idempotency_status in {"missing", "duplicate_blocked", "blocked"}:
        blockers.append("idempotency_not_clear")
    if ctx.kill_switch_status != "kill_switch_clear":
        blockers.append("kill_switch_not_clear")
    if not ctx.audit_sink_ready:
        blockers.append("audit_sink_not_ready")
    if ctx.request_budget_used > 1:
        blockers.append("request_budget_exceeded")
    if ctx.platform_id in MEDIA_GATED_PLATFORMS and not ctx.media_requirement_satisfied:
        blockers.append("media_requirement_missing")
    if ctx.platform_id in APP_REVIEW_PLATFORMS and not ctx.app_review_satisfied:
        blockers.append("app_review_required")
    if ctx.platform_id in PAID_OR_QUOTA_PLATFORMS and not ctx.paid_or_quota_gate_satisfied:
        blockers.append("paid_or_quota_gate_required")
    if ctx.read_only_probe_required_before_live:
        blockers.append("read_only_probe_required_before_live")
    if ctx.platform_id == "telegram_remote_operator_inbox" and ctx.public_destination_allowed_future:
        blockers.append("operator_inbox_not_public_publish_destination")
    if ctx.platform_id == "substack_newsletter":
        blockers.append("substack_manual_export_no_official_api")
    blockers.append("live_write_policy_forbids_dispatch_now")
    return tuple(dict.fromkeys(blockers))


def _gate_state(blockers: tuple[str, ...], ctx: LiveGateContext) -> str:
    order = (
        ("platform_registry_missing", "blocked_by_platform_registry"),
        ("official_docs_not_current", "blocked_by_docs"),
        ("destination_binding_not_verified", "blocked_by_destination_binding"),
        ("permission_not_verified", "blocked_by_scope_permission"),
        ("scope_not_verified", "blocked_by_scope_permission"),
        ("credential_handle_missing", "blocked_by_credential_handle"),
        ("approval_not_current", "blocked_by_approval"),
        ("outbox_not_ready", "blocked_by_outbox"),
        ("idempotency_not_clear", "blocked_by_idempotency"),
        ("kill_switch_not_clear", "blocked_by_kill_switch"),
        ("audit_sink_not_ready", "blocked_by_audit_sink"),
        ("request_budget_exceeded", "blocked_by_request_budget"),
        ("media_requirement_missing", "blocked_by_media_requirement"),
        ("app_review_required", "blocked_by_app_review"),
        ("paid_or_quota_gate_required", "blocked_by_paid_or_quota_gate"),
        ("read_only_probe_required_before_live", "blocked_by_read_only_probe_required"),
        ("live_write_policy_forbids_dispatch_now", "blocked_by_live_write_policy"),
    )
    if not blockers:
        return "not_started"
    if blockers == ("live_write_policy_forbids_dispatch_now",) and ctx.future_live_candidate_requested:
        return "future_supervised_live_candidate"
    for blocker, state in order:
        if blocker in blockers:
            return state
    return "live_dispatch_forbidden_now"


def explain_live_gate_required_repairs(context: LiveGateContext | dict[str, Any]) -> tuple[str, ...]:
    repairs: list[str] = []
    for blocker in derive_live_gate_blockers(context):
        if blocker == "platform_registry_missing":
            repairs.append("add_or_select_supported_platform_registry_row")
        elif blocker == "official_docs_not_current":
            repairs.append("re_ground_official_docs_before_live")
        elif blocker == "destination_binding_not_verified":
            repairs.append("verify_destination_binding_and_wrong_account_check")
        elif blocker in {"permission_not_verified", "scope_not_verified"}:
            repairs.append("verify_scope_permission_and_role_proof")
        elif blocker == "credential_handle_missing":
            repairs.append("provide_symbolic_credential_handle_without_hydration")
        elif blocker == "approval_not_current":
            repairs.append("obtain_current_operator_approval")
        elif blocker == "outbox_not_ready":
            repairs.append("prepare_local_outbox_candidate")
        elif blocker == "idempotency_not_clear":
            repairs.append("resolve_idempotency_duplicate_or_unknown")
        elif blocker == "kill_switch_not_clear":
            repairs.append("confirm_kill_switch_clear")
        elif blocker == "audit_sink_not_ready":
            repairs.append("prepare_redacted_append_only_audit_sink")
        elif blocker == "request_budget_exceeded":
            repairs.append("reset_request_budget_to_1_and_review_quota")
        elif blocker == "media_requirement_missing":
            repairs.append("complete_media_container_or_upload_requirement")
        elif blocker == "app_review_required":
            repairs.append("complete_platform_app_review_or_product_access")
        elif blocker == "paid_or_quota_gate_required":
            repairs.append("confirm_paid_plan_quota_or_request_budget")
        elif blocker == "read_only_probe_required_before_live":
            repairs.append("run_separately_authorized_read_only_probe")
        elif blocker == "substack_manual_export_no_official_api":
            repairs.append("use_manual_export_fallback")
        elif blocker == "live_write_policy_forbids_dispatch_now":
            repairs.append("wait_for_explicit_future_live_write_gate")
    return tuple(dict.fromkeys(repairs))


def evaluate_live_gate_state(context: LiveGateContext | dict[str, Any]) -> LiveGateEvaluation:
    ctx = context if isinstance(context, LiveGateContext) else LiveGateContext(**context)
    blockers = derive_live_gate_blockers(ctx)
    repairs = explain_live_gate_required_repairs(ctx)
    state = _gate_state(blockers, ctx)
    future_candidate = state == "future_supervised_live_candidate"
    return LiveGateEvaluation(
        platform_id=ctx.platform_id,
        payload_class_id=ctx.payload_class_id,
        destination_binding_id=ctx.destination_binding_id,
        credential_handle_id=ctx.credential_handle_id,
        payload_hash_short=ctx.payload_hash_short,
        outbox_id=ctx.outbox_id,
        gate_state=state,
        gate_passed_now=False,
        valid_for_live_dispatch_now=False,
        future_live_candidate_allowed_after_gates=future_candidate,
        blocked_reasons=blockers,
        required_repairs=repairs,
        manual_fallback_required=True,
        re_ground_required_before_live=True,
        request_budget=1,
        auto_retry_allowed=False,
        no_live_api_call_performed=True,
        credential_hydration_performed=False,
        raw_response_persisted=False,
    )


def assert_no_live_dispatch_ready_now(evaluations: tuple[LiveGateEvaluation, ...] | list[LiveGateEvaluation] | tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> None:
    for index, item in enumerate(evaluations):
        data = item.as_dict() if isinstance(item, LiveGateEvaluation) else item
        if data.get("gate_passed_now") is not False:
            raise AssertionError(f"evaluation[{index}] gate_passed_now must be false")
        if data.get("valid_for_live_dispatch_now") is not False:
            raise AssertionError(f"evaluation[{index}] valid_for_live_dispatch_now must be false")
        if data.get("auto_retry_allowed") is not False:
            raise AssertionError(f"evaluation[{index}] auto_retry_allowed must be false")
        if data.get("no_live_api_call_performed") is not True:
            raise AssertionError(f"evaluation[{index}] no_live_api_call_performed must be true")
        if data.get("credential_hydration_performed") is not False:
            raise AssertionError(f"evaluation[{index}] credential_hydration_performed must be false")


def live_gate_state_machine_packet() -> dict[str, Any]:
    platform_ids = [row.platform_id for row in build_platform_universe_registry_v2()]
    evaluations = tuple(evaluate_live_gate_state(build_live_gate_context(platform_id)) for platform_id in platform_ids)
    assert_no_live_dispatch_ready_now(evaluations)
    rows = [item.as_dict() for item in evaluations]
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "gate_states": list(GATE_STATES),
        "platform_count": len(platform_ids),
        "platform_ids": platform_ids,
        "all_valid_for_live_dispatch_now_false": all(row["valid_for_live_dispatch_now"] is False for row in rows),
        "all_gate_passed_now_false": all(row["gate_passed_now"] is False for row in rows),
        "request_budget_all_1": all(row["request_budget"] == 1 for row in rows),
        "auto_retry_allowed_any": any(row["auto_retry_allowed"] for row in rows),
        "credential_hydration_performed_any": any(row["credential_hydration_performed"] for row in rows),
        "raw_response_persisted_any": any(row["raw_response_persisted"] for row in rows),
        "evaluations": rows,
    }
