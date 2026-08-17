"""Run the reviewed TikTok Desktop OAuth helper in a supervised local session."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.tiktok_local_desktop_oauth_pkce_v1 import (  # noqa: E402
    UrllibFormTokenTransport,
    TikTokOAuthError,
    authorize_interactively,
    failure_receipt,
    read_approved_credentials,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Supervised local TikTok Desktop OAuth PKCE bootstrap."
    )
    parser.add_argument(
        "--run-supervised-sandbox-oauth",
        action="store_true",
        help="Explicitly authorize environment reads, browser consent, and token exchange.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    args = parser.parse_args(argv)
    if not args.run_supervised_sandbox_oauth:
        print(
            json.dumps(
                {
                    "result": "EXPLICIT_SUPERVISED_OAUTH_CONFIRMATION_REQUIRED",
                    "secrets_persisted": False,
                    "environment_mutated": False,
                    "public_writes": 0,
                },
                sort_keys=True,
            )
        )
        return 2
    try:
        credentials = read_approved_credentials()
        session = authorize_interactively(
            credentials,
            transport=UrllibFormTokenTransport(),
            callback_timeout_seconds=args.timeout_seconds,
        )
    except TikTokOAuthError as exc:
        print(json.dumps(failure_receipt(exc), sort_keys=True))
        return 2
    print(json.dumps(session.redacted_receipt(), sort_keys=True))
    return 0 if session.required_scopes_satisfied else 3


if __name__ == "__main__":
    raise SystemExit(main())
