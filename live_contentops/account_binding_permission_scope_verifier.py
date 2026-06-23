"""Account binding permission and scope verifier for ContentOps.

Local-only deterministic verifier. It never hydrates credentials, reads env,
performs network/API/provider calls, opens browsers, or enables live writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import re
from typing import Any, Iterable

from .platform_scope_permission_contract import (
    PLATFORM_IDS,
    PlatformScopePermissionContract,
    contracts_by_platform_id,
)

TASK_LABEL = "TASK_CONTENTOPS_ACCOUNT_BINDING_PERMISSION_SCOPE_VERIFIER_CORE_V0"
MODEL = "contentops.account_binding_permission_scope_verifier"
MODEL_VERSION = "0175_ACCOUNT_BINDING_PERMISSION_SCOPE_VERIFIER_V0"

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}\b", re.I),
    re.compile(r"\b[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\b(?:xox[baprs]-|sk-|ghp_|ya29\.)[A-Za-z0-9._~+/=-]{8,}\b", re.I),
    re.compile(r"(?i)(access_token|refresh_token|client_secret|api_secret|api_key|bot_token|cookie|authorization)\s*[:=]\s*[^\s,;]+"),
)

_ALLOWED_PLACEHOLDER_VALUES = {
    "unconfirmed_redacted",
    "redacted_destination_placeholder",
    "redacted_account_placeholder",
    "redacted_handle_placeholder",
}


@dataclass(frozen=True)
class DestinationBindingProof:
    destination_binding_id: str
    platform_id: str
    destination_kind: str
    display_name_redacted: str
    handle_redacted: str
    platform_account_id_redacted: str
    credential_handle_id: str
    operator_confirmed: bool
    confirmation_method: str
    permission_status: str
    scope_status: str
    account_binding_status: str
    wrong_account_detection_status: str
    official_docs_status: str
    last_verified_at: str | None
    public_destination_allowed_future: bool
    live_write_allowed_now: bool
    can_post_live_now: bool
    dispatchable_now: bool
    public_postable_now: bool
    read_only_probe_performed: bool
    read_only_probe_allowed_in_this_task: bool
    credential_hydration_performed: bool
    credential_hydration_allowed_in_this_task: bool
    approval_invalidation_fields: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    manual_fallback_required: bool
    re_ground_required_before_live: bool
    no_secret_output: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AccountBindingVerificationError(ValueError):
    """Raised when a binding proof fails closed."""


def _contains_secret_shaped_text(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if value in _ALLOWED_PLACEHOLDER_VALUES:
        return False
    return any(pattern.search(value) for pattern in _SECRET_PATTERNS)


def assert_no_secret_shaped_material(value: object) -> None:
    """Fail closed if any output-shaped value contains token-like material."""
    if isinstance(value, dict):
        for key, item in value.items():
            assert_no_secret_shaped_material(str(key))
            assert_no_secret_shaped_material(item)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            assert_no_secret_shaped_material(item)
        return
    if _contains_secret_shaped_text(value):
        raise AccountBindingVerificationError("secret_shaped_material_blocked")


def approval_invalidation_fields_for_binding(platform_id: str) -> tuple[str, ...]:
    """Return fields whose changes invalidate prior approval payload hashes."""
    common = (
        "destination_binding_id",
        "platform_id",
        "destination_kind",
        "platform_account_id_redacted",
        "credential_handle_id",
        "permission_status",
        "scope_status",
        "account_binding_status",
        "wrong_account_detection_status",
    )
    platform_specific: dict[str, tuple[str, ...]] = {
        "telegram_channel_destination": ("telegram_channel_admin_binding",),
        "telegram_remote_operator_inbox": ("operator_inbox_binding",),
        "linkedin_member_profile": ("linkedin_member_urn_redacted",),
        "linkedin_organization_page": ("linkedin_organization_urn_redacted", "organization_role_proof"),
        "facebook_page": ("facebook_page_id_redacted", "page_role_proof"),
        "instagram_professional_account": ("instagram_business_account_id_redacted", "media_container_permission"),
        "tiktok_account": ("tiktok_open_id_redacted", "video_upload_permission"),
        "youtube_channel": ("youtube_channel_id_redacted", "youtube_upload_permission"),
        "x_profile": ("x_user_id_redacted", "x_project_access"),
        "threads_profile": ("threads_user_id_redacted",),
        "substack_newsletter": ("substack_publication_url_redacted",),
    }
    return common + platform_specific.get(platform_id, ())


def derive_account_binding_status(
    *,
    operator_confirmed: bool,
    permission_status: str,
    scope_status: str,
    wrong_account_detection_status: str,
    official_docs_status: str,
) -> str:
    """Derive fail-closed binding status from local symbolic proof statuses."""
    if wrong_account_detection_status in {"wrong_account_detected", "wrong_destination_detected"}:
        return "wrong_account_blocked"
    if not operator_confirmed:
        return "operator_confirmation_missing_blocked"
    if permission_status != "permission_verified_symbolic":
        return "permission_unverified_blocked"
    if scope_status != "scope_verified_symbolic":
        return "scope_unverified_blocked"
    if official_docs_status != "official_docs_checked_current":
        return "official_docs_not_current_blocked"
    return "symbolically_ready_but_live_write_forbidden"


def explain_binding_blockers(
    proof: DestinationBindingProof,
    contract: PlatformScopePermissionContract | None = None,
) -> tuple[str, ...]:
    """Return deterministic blocker reason codes for a binding proof."""
    blockers: list[str] = []
    active_contract = contract or contracts_by_platform_id().get(proof.platform_id)
    if active_contract is None:
        blockers.append("unsupported_platform_id")
    else:
        if proof.destination_kind != active_contract.destination_kind:
            blockers.append("destination_kind_mismatch")
        if proof.public_destination_allowed_future != active_contract.public_destination_allowed_future:
            blockers.append("public_destination_future_mismatch")
    if not proof.destination_binding_id:
        blockers.append("destination_binding_id_missing")
    if not proof.credential_handle_id:
        blockers.append("credential_handle_id_missing")
    if not proof.operator_confirmed:
        blockers.append("operator_confirmation_missing")
    if proof.confirmation_method in {"", "not_confirmed", "not_confirmed_batch_a_bootstrap"}:
        blockers.append("confirmation_method_missing")
    if proof.permission_status != "permission_verified_symbolic":
        blockers.append("permission_unverified")
    if proof.scope_status != "scope_verified_symbolic":
        blockers.append("scope_unverified")
    if proof.account_binding_status != "symbolically_ready_but_live_write_forbidden":
        blockers.append(proof.account_binding_status)
    if proof.wrong_account_detection_status != "wrong_account_not_detected_symbolic":
        blockers.append("wrong_account_detection_not_clear")
    if proof.official_docs_status != "official_docs_checked_current":
        blockers.append("official_docs_not_current")
    if proof.last_verified_at is None:
        blockers.append("last_verified_at_missing")
    if proof.read_only_probe_performed:
        blockers.append("read_only_probe_forbidden_in_this_task")
    if proof.credential_hydration_performed:
        blockers.append("credential_hydration_forbidden_in_this_task")
    if (
        proof.live_write_allowed_now
        or proof.can_post_live_now
        or proof.dispatchable_now
        or proof.public_postable_now
        or proof.read_only_probe_allowed_in_this_task
        or proof.credential_hydration_allowed_in_this_task
    ):
        blockers.append("live_ready_flag_forbidden")
    if not proof.no_secret_output:
        blockers.append("no_secret_output_false")
    blockers.append("live_write_forbidden_until_future_gate")
    return tuple(dict.fromkeys(blockers))


def _base_proof(
    *,
    destination_binding_id: str,
    platform_id: str,
    credential_handle_id: str,
    operator_confirmed: bool = False,
    confirmation_method: str = "not_confirmed",
    permission_status: str = "permission_unverified_blocked",
    scope_status: str = "scope_unverified_blocked",
    wrong_account_detection_status: str = "not_checked_blocked",
    official_docs_status: str = "official_docs_checked_current",
    last_verified_at: str | None = None,
) -> DestinationBindingProof:
    contract = contracts_by_platform_id()[platform_id]
    binding_status = derive_account_binding_status(
        operator_confirmed=operator_confirmed,
        permission_status=permission_status,
        scope_status=scope_status,
        wrong_account_detection_status=wrong_account_detection_status,
        official_docs_status=official_docs_status,
    )
    initial = DestinationBindingProof(
        destination_binding_id=destination_binding_id,
        platform_id=platform_id,
        destination_kind=contract.destination_kind,
        display_name_redacted="unconfirmed_redacted",
        handle_redacted="unconfirmed_redacted",
        platform_account_id_redacted="unconfirmed_redacted",
        credential_handle_id=credential_handle_id,
        operator_confirmed=operator_confirmed,
        confirmation_method=confirmation_method,
        permission_status=permission_status,
        scope_status=scope_status,
        account_binding_status=binding_status,
        wrong_account_detection_status=wrong_account_detection_status,
        official_docs_status=official_docs_status,
        last_verified_at=last_verified_at,
        public_destination_allowed_future=contract.public_destination_allowed_future,
        live_write_allowed_now=False,
        can_post_live_now=False,
        dispatchable_now=False,
        public_postable_now=False,
        read_only_probe_performed=False,
        read_only_probe_allowed_in_this_task=False,
        credential_hydration_performed=False,
        credential_hydration_allowed_in_this_task=False,
        approval_invalidation_fields=approval_invalidation_fields_for_binding(platform_id),
        blocked_reasons=(),
        manual_fallback_required=True,
        re_ground_required_before_live=True,
        no_secret_output=True,
    )
    return replace(initial, blocked_reasons=explain_binding_blockers(initial, contract))


def build_symbolic_destination_binding_proofs() -> tuple[DestinationBindingProof, ...]:
    """Return symbolic, unverified, fail-closed binding proofs for all platforms."""
    specs = (
        ("x_profile_default", "x_profile", "x_oauth_user_context"),
        ("telegram_operator_inbox_default", "telegram_remote_operator_inbox", "telegram_bot_operator_inbox"),
        ("telegram_channel_default", "telegram_channel_destination", "telegram_bot_channel"),
        ("substack_newsletter_default", "substack_newsletter", "substack_publication_manual"),
        ("linkedin_member_default", "linkedin_member_profile", "linkedin_member_oauth"),
        ("linkedin_org_default", "linkedin_organization_page", "linkedin_organization_oauth"),
        ("threads_profile_default", "threads_profile", "threads_meta_oauth"),
        ("instagram_professional_default", "instagram_professional_account", "instagram_meta_oauth"),
        ("facebook_page_default", "facebook_page", "facebook_page_meta_oauth"),
        ("tiktok_account_default", "tiktok_account", "tiktok_oauth"),
        ("youtube_channel_default", "youtube_channel", "youtube_oauth"),
    )
    rows = tuple(
        _base_proof(destination_binding_id=bid, platform_id=platform_id, credential_handle_id=credential_handle_id)
        for bid, platform_id, credential_handle_id in specs
    )
    assert_no_live_write_allowed(rows)
    assert_no_secret_shaped_material([row.as_dict() for row in rows])
    return rows


def bindings_by_platform_id(
    rows: Iterable[DestinationBindingProof] | None = None,
) -> dict[str, DestinationBindingProof]:
    """Return binding proofs indexed by platform_id."""
    proofs = tuple(rows) if rows is not None else build_symbolic_destination_binding_proofs()
    return {proof.platform_id: proof for proof in proofs}


def assert_no_live_write_allowed(rows: Iterable[DestinationBindingProof]) -> None:
    """Fail if any binding claims current live write, dispatch, or public post readiness."""
    for row in rows:
        if row.live_write_allowed_now or row.can_post_live_now or row.dispatchable_now or row.public_postable_now:
            raise AccountBindingVerificationError("live_write_ready_now_forbidden")
        if row.read_only_probe_allowed_in_this_task or row.credential_hydration_allowed_in_this_task:
            raise AccountBindingVerificationError("live_probe_or_credential_hydration_forbidden")


def validate_binding_against_platform_contract(
    proof: DestinationBindingProof,
    contract: PlatformScopePermissionContract,
) -> DestinationBindingProof:
    """Validate a binding proof against its platform contract and fail closed."""
    assert_no_secret_shaped_material(proof.as_dict())
    if proof.platform_id != contract.platform_id:
        raise AccountBindingVerificationError("platform_contract_mismatch")
    if proof.destination_kind != contract.destination_kind:
        raise AccountBindingVerificationError("destination_kind_mismatch")
    blockers = explain_binding_blockers(proof, contract)
    checked = replace(proof, blocked_reasons=blockers)
    assert_no_live_write_allowed((checked,))
    if checked.account_binding_status == "symbolically_ready_but_live_write_forbidden":
        return replace(
            checked,
            blocked_reasons=tuple(dict.fromkeys(checked.blocked_reasons + ("live_write_forbidden_until_future_gate",))),
        )
    raise AccountBindingVerificationError("binding_not_ready:" + ",".join(blockers))


def validate_destination_binding_proof(proof: DestinationBindingProof) -> DestinationBindingProof:
    """Validate proof against known contracts. Always keeps live write forbidden."""
    contract = contracts_by_platform_id().get(proof.platform_id)
    if contract is None:
        raise AccountBindingVerificationError("unsupported_platform_id")
    return validate_binding_against_platform_contract(proof, contract)


def account_binding_permission_scope_packet() -> dict[str, Any]:
    """Return JSON-serializable account binding permission/scope evidence packet."""
    rows = build_symbolic_destination_binding_proofs()
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "platform_count": len(rows),
        "platform_ids": list(PLATFORM_IDS),
        "all_platforms_covered": sorted(row.platform_id for row in rows) == sorted(PLATFORM_IDS),
        "live_write_allowed_now": False,
        "can_post_live_now": False,
        "dispatchable_now": False,
        "public_postable_now": False,
        "read_only_probe_performed": False,
        "read_only_probe_allowed_in_this_task": False,
        "credential_hydration_performed": False,
        "credential_hydration_allowed_in_this_task": False,
        "raw_secret_values_persisted": False,
        "no_secret_output": True,
        "bindings": [row.as_dict() for row in rows],
    }
    assert_no_secret_shaped_material(packet)
    return packet
