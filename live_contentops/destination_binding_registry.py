"""Destination binding bootstrap registry for Batch A.

Bindings are redacted placeholders. No destination is live-write allowed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_MULTI_PLATFORM_LIVE_FOUNDATION_BATCH_A_DOCS_CREDENTIALS_BINDINGS_AND_READONLY_PROBES_V0"


@dataclass(frozen=True)
class DestinationBindingRow:
    destination_binding_id: str
    platform_id: str
    destination_kind: str
    display_name_redacted: str
    handle_redacted: str
    platform_account_id_redacted: str
    operator_confirmed: bool
    confirmation_method: str
    credential_handle_id: str
    permission_status: str
    scope_status: str
    wrong_account_detection_status: str
    last_verified_at: str | None
    live_write_allowed: bool
    blocked_reasons: tuple[str, ...]


def build_destination_bindings() -> tuple[DestinationBindingRow, ...]:
    specs = (
        ("telegram_operator_inbox_default", "telegram_remote_operator", "operator_inbox", "telegram_operator_chat"),
        ("telegram_channel_default", "telegram_channel_destination", "channel", "telegram_channel"),
        ("x_profile_default", "x_profile", "profile", "x_bearer"),
        ("linkedin_member_default", "linkedin_member_profile", "member_profile", "linkedin_member"),
        ("linkedin_org_default", "linkedin_organization_page", "organization_page", "linkedin_org"),
        ("substack_newsletter_default", "substack_newsletter", "newsletter_publication", "substack_publication"),
        ("facebook_page_default", "facebook_page", "page", "facebook_page"),
        ("instagram_professional_default", "instagram_professional_account", "professional_account", "instagram_business"),
        ("threads_profile_default", "threads_profile", "profile", "threads_user"),
        ("tiktok_account_default", "tiktok_account", "account", "tiktok_open"),
        ("youtube_channel_default", "youtube_channel", "channel", "youtube_channel"),
    )
    return tuple(
        DestinationBindingRow(
            destination_binding_id=bid,
            platform_id=platform_id,
            destination_kind=kind,
            display_name_redacted="unconfirmed_redacted",
            handle_redacted="unconfirmed_redacted",
            platform_account_id_redacted="unconfirmed_redacted",
            operator_confirmed=False,
            confirmation_method="not_confirmed_batch_a_bootstrap",
            credential_handle_id=cred,
            permission_status="unverified_blocked",
            scope_status="unverified_blocked",
            wrong_account_detection_status="not_checked_blocked",
            last_verified_at=None,
            live_write_allowed=False,
            blocked_reasons=("operator_confirmation_missing", "permission_unverified", "scope_unverified", "batch_a_live_write_forbidden"),
        )
        for bid, platform_id, kind, cred in specs
    )


def destination_binding_packet() -> dict[str, Any]:
    rows = [asdict(row) for row in build_destination_bindings()]
    return {"task_label": TASK_LABEL, "live_write_allowed": False, "rows": rows}
