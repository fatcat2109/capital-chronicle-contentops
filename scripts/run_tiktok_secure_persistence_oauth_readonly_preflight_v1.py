"""Run the reviewed TikTok secure-persistence bootstrap under explicit authority."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Mapping
from typing import Any

from live_contentops.tiktok_local_desktop_oauth_pkce_v1 import (
    UrllibFormTokenTransport,
    TikTokAppCredentials,
    TikTokOAuthError,
    TikTokTokenSession,
    authorize_interactively,
    read_approved_credentials,
)
from live_contentops.tiktok_secure_refresh_store_readonly_preflight_v1 import (
    CREDENTIAL_TARGET,
    TikTokRefreshCredentialStore,
    TikTokSecureSessionError,
    UrllibUserInfoTransport,
    persist_supervised_session_after_preflight,
)


EXECUTION_FLAG = "--run-supervised-sandbox-oauth-and-persist"
CONFIRMATION_REQUIRED = "EXPLICIT_SUPERVISED_OAUTH_AND_PERSIST_CONFIRMATION_REQUIRED"
EXISTING_CREDENTIAL = (
    "EXISTING_REFRESH_CREDENTIAL_REQUIRES_EXPLICIT_REPLACEMENT_AUTHORITY"
)

_SUCCESS_FIELDS = (
    "result",
    "state_validated",
    "required_scopes_satisfied",
    "identity_preflight_success",
    "open_id_match",
    "display_name_received",
    "refresh_token_persisted",
    "access_token_persisted",
    "credential_target",
    "environment_mutated",
    "content_posting_calls",
    "media_uploads",
    "public_writes",
)


def _failure_receipt(classification: str) -> dict[str, Any]:
    return {
        "result": classification,
        "state_validated": False,
        "required_scopes_satisfied": False,
        "identity_preflight_success": False,
        "open_id_match": False,
        "display_name_received": False,
        "refresh_token_persisted": False,
        "access_token_persisted": False,
        "credential_target": CREDENTIAL_TARGET,
        "environment_mutated": False,
        "content_posting_calls": 0,
        "media_uploads": 0,
        "public_writes": 0,
    }


def _success_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    try:
        sanitized = {field: receipt[field] for field in _SUCCESS_FIELDS}
    except KeyError:
        raise TikTokSecureSessionError("REDACTED_RECEIPT_INVALID") from None
    if sanitized["access_token_persisted"] is not False:
        raise TikTokSecureSessionError("ACCESS_TOKEN_PERSISTENCE_FORBIDDEN")
    return sanitized


def _require_initial_target_absent(store: TikTokRefreshCredentialStore) -> None:
    try:
        store.load_refresh_session()
    except TikTokSecureSessionError as exc:
        if exc.classification == "MISSING_REFRESH_CREDENTIAL":
            return
        raise
    raise TikTokSecureSessionError(EXISTING_CREDENTIAL)


def main(
    argv: list[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    store: TikTokRefreshCredentialStore | None = None,
    token_transport: Any | None = None,
    user_info_transport: Any | None = None,
    credential_reader: Callable[
        [Mapping[str, str] | None], TikTokAppCredentials
    ] = read_approved_credentials,
    oauth_authorizer: Callable[..., TikTokTokenSession] = authorize_interactively,
) -> int:
    """Execute only when the exact supervised persistence flag is present."""

    parser = argparse.ArgumentParser(
        description="Supervised TikTok OAuth, read-only identity check, and secure persistence."
    )
    parser.add_argument(
        EXECUTION_FLAG,
        action="store_true",
        help="Authorize one supervised Sandbox OAuth and secure refresh persistence.",
    )
    args = parser.parse_args(argv)
    if not args.run_supervised_sandbox_oauth_and_persist:
        print(json.dumps(_failure_receipt(CONFIRMATION_REQUIRED), sort_keys=True))
        return 2

    try:
        active_store = store if store is not None else TikTokRefreshCredentialStore()
        _require_initial_target_absent(active_store)
        credentials = credential_reader(env)
        active_token_transport = (
            token_transport
            if token_transport is not None
            else UrllibFormTokenTransport()
        )
        session = oauth_authorizer(
            credentials,
            transport=active_token_transport,
        )
        active_user_info_transport = (
            user_info_transport
            if user_info_transport is not None
            else UrllibUserInfoTransport()
        )
        receipt = persist_supervised_session_after_preflight(
            session,
            store=active_store,
            user_info_transport=active_user_info_transport,
        )
        output = _success_receipt(receipt)
    except (TikTokOAuthError, TikTokSecureSessionError) as exc:
        print(json.dumps(_failure_receipt(exc.classification), sort_keys=True))
        return 2

    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
