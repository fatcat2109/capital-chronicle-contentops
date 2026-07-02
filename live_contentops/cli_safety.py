"""Redaction and safety helpers for operator-send CLIs.

OPERATOR NOTE: If a credential, webhook URL, or bot token is ever exposed in
chat logs, stdout, or repository files, you must IMMEDIATELY revoke and
regenerate it externally (e.g. via Discord Developer Portal or Telegram
BotFather). Never commit raw credentials to the repository or paste them into
chat transcripts.
"""
from __future__ import annotations

import json
from typing import Any

OPERATOR_SAFETY_NOTE = (
    "OPERATOR NOTE: If a credential, webhook URL, or bot token is ever exposed in "
    "chat logs, stdout, or repository files, you must IMMEDIATELY revoke and "
    "regenerate it externally (e.g. via Discord Developer Portal or Telegram "
    "BotFather). Never commit raw credentials to the repository or paste them into "
    "chat transcripts."
)


def assert_clean_of_secrets(evidence: dict[str, Any], secrets: list[str]) -> None:
    """Ensure that the evidence dict and its serialization do not contain raw secret values.

    If any raw secret is found, raises an AssertionError to block output generation.
    """
    serialized = json.dumps(evidence)
    for secret in secrets:
        if not secret:
            continue
        clean = secret.strip().strip('"').strip("'").strip()
        if len(clean) > 3 and clean in serialized:
            raise AssertionError("Secret leakage detected in evidence! Raw secret value was found in the output dict.")
