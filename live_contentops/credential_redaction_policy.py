"""Redaction policy for Batch A credential/probe outputs.

Never returns raw secret values, token length, prefix, suffix, or digest.
"""

from __future__ import annotations

import re
from typing import Any

REDACTION_POLICY_ID = "batch_a_no_secret_prefix_suffix_digest_v1"
SECRET_SENTINELS = (
    "SECRET_SHAPED_VALUE_REDACTED",
    "AUTH_HEADER_REDACTED",
    "COOKIE_REDACTED",
    "TOKEN_REDACTED",
)
_SECRET_PATTERNS = (
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}\b", re.I),
    re.compile(r"\b[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\b(?:xox[baprs]-|sk-|ghp_|ya29\.)[A-Za-z0-9._~+/=-]{8,}\b", re.I),
    re.compile(r"(?i)(access_token|refresh_token|client_secret|api_secret|api_key|bot_token|cookie|authorization)\s*[:=]\s*[^\s,;]+"),
)


def contains_secret_shaped_text(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return any(pattern.search(value) for pattern in _SECRET_PATTERNS)


def redact_text(value: object) -> str:
    text = str(value)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED_SECRET_SHAPED_TEXT]", text)
    return text


def assert_no_secret_shaped_text(value: object) -> None:
    if contains_secret_shaped_text(value):
        raise ValueError("secret_shaped_text_blocked_by_redaction_policy")


def redacted_presence(value_present: bool, key_name: str) -> str:
    assert_no_secret_shaped_text(key_name)
    return "present_redacted" if value_present else "missing"


def sanitize_for_output(data: Any) -> Any:
    if isinstance(data, dict):
        return {str(k): sanitize_for_output(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [sanitize_for_output(v) for v in data]
    if isinstance(data, str):
        return redact_text(data)
    return data
