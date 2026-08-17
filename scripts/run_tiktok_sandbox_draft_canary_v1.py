"""Run the exact TikTok Sandbox draft canary only under one-attempt authority."""

from __future__ import annotations

import argparse
import hmac
import json
import os
from typing import Any

from live_contentops.tiktok_local_desktop_oauth_pkce_v1 import (
    UrllibFormTokenTransport,
)
from live_contentops.tiktok_sandbox_draft_canary_v1 import (
    EXACT_PACKAGE_ID,
    AcceptedSecureSessionProvider,
    AcceptedShortPackageResolver,
    CanaryJournal,
    TikTokCanaryError,
    TikTokSandboxDraftCanaryExecutor,
    UrllibTikTokCanaryTransport,
    deterministic_canary_attempt_id,
)
from live_contentops.tiktok_secure_refresh_store_readonly_preflight_v1 import (
    TikTokRefreshCredentialStore,
    UrllibUserInfoTransport,
)


EXECUTION_FLAG = "--run-exact-tiktok-sandbox-draft-canary"
READBACK_ONLY_FLAG = "--readback-only-existing-attempt"
ATTEMPT_ID_FLAG = "--authorized-attempt-id"


def _not_authorized_receipt(result: str) -> dict[str, Any]:
    return {
        "schema": "contentops.v2.tiktok_sandbox_draft_canary_receipt.v1",
        "result": result,
        "attempt_id": "",
        "package_id": EXACT_PACKAGE_ID,
        "media_sha256": "",
        "destination_alias": "TIKTOK_SANDBOX_PRIMARY",
        "environment": "SANDBOX",
        "delivery_intent": "DRAFT_DELIVERY",
        "owner_authority_scope": "ONE_EXACT_TIKTOK_SANDBOX_DRAFT_DELIVERY",
        "oauth_refresh_success": False,
        "identity_preflight_success": False,
        "required_scopes_satisfied": False,
        "logical_draft_delivery_attempts": 0,
        "mutation_http_calls": 0,
        "status_readback_calls": 0,
        "publish_id_present": False,
        "terminal_provider_status": None,
        "draft_delivery_confirmed": False,
        "creator_finalization_required": True,
        "creator_finalization_observed": False,
        "public_post_confirmed": False,
        "access_token_persisted": False,
        "refresh_token_rotation_persisted": False,
        "unknown_write": False,
        "content_posting_mode": "UPLOAD_TO_TIKTOK_DRAFT",
        "public_writes": 0,
        "v1_mutations": 0,
        "scheduler_mutations": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="One exact owner-authorized TikTok Sandbox draft-delivery canary."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        EXECUTION_FLAG,
        action="store_true",
        help="Attempt one exact Upload-to-TikTok Sandbox draft delivery.",
    )
    mode.add_argument(
        READBACK_ONLY_FLAG,
        action="store_true",
        help="Read back an existing journaled attempt; cannot initialize or upload.",
    )
    parser.add_argument(ATTEMPT_ID_FLAG)
    args = parser.parse_args(argv)

    if not (
        args.run_exact_tiktok_sandbox_draft_canary
        or args.readback_only_existing_attempt
    ):
        print(
            json.dumps(
                _not_authorized_receipt("EXACT_CANARY_EXECUTION_FLAG_REQUIRED"),
                sort_keys=True,
            )
        )
        return 2
    if not args.authorized_attempt_id:
        print(
            json.dumps(
                _not_authorized_receipt("AUTHORIZED_ATTEMPT_ID_REQUIRED"),
                sort_keys=True,
            )
        )
        return 2

    # Resolve the fixed nonsecret authority and reject a wrong attempt before constructing
    # any credential or network-capable dependency. The executor repeats this hard gate.
    resolver = AcceptedShortPackageResolver()
    try:
        authority = resolver.describe_authority()
        expected_attempt_id = deterministic_canary_attempt_id(
            package_id=authority.package_id,
            media_sha256=authority.media_sha256,
        )
    except TikTokCanaryError as exc:
        output = _not_authorized_receipt(exc.classification)
        print(json.dumps(output, sort_keys=True))
        return 2
    if not hmac.compare_digest(args.authorized_attempt_id, expected_attempt_id):
        output = _not_authorized_receipt("OWNER_AUTHORIZED_ATTEMPT_ID_MISMATCH")
        output.update(
            attempt_id=expected_attempt_id,
            media_sha256=authority.media_sha256,
        )
        print(json.dumps(output, sort_keys=True))
        return 2

    store = TikTokRefreshCredentialStore()
    secure_provider = AcceptedSecureSessionProvider(
        store=store,
        token_transport=UrllibFormTokenTransport(),
        user_info_transport=UrllibUserInfoTransport(),
        env=os.environ,
    )
    executor = TikTokSandboxDraftCanaryExecutor(
        resolver=resolver,
        secure_session_provider=secure_provider,
        transport=UrllibTikTokCanaryTransport(),
        journal=CanaryJournal(),
    )
    receipt = executor.run(
        authorized_attempt_id=args.authorized_attempt_id,
        readback_only=args.readback_only_existing_attempt,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["result"] == "DRAFT_DELIVERY_CONFIRMED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
