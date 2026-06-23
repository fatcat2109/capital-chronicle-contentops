"""Approval payload hash core module for ContentOps.

Provides deterministic SHA-256 hashing for payload structures.
Ensures zero secret-shaped material, raw credentials, or session values are hashed.
"""

from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_APPROVAL_LEDGER_PAYLOAD_HASH_INVALIDATION_V0"
MODEL = "contentops.approval_payload_hash"
MODEL_VERSION = "0174U1_APPROVAL_PAYLOAD_HASH_V1"

SECRET_PATTERNS = [
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b"),  # Telegram bot token
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),  # JWT token
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}"),  # Bearer token
]

FORBIDDEN_KEYWORDS = re.compile(
    r"(?i)(cookie|sessionStorage|localStorage|password|secret_key|session_id|set-cookie|auth_header)"
)


def canonical_payload_hash_input(
    platform_id: str,
    destination_binding_id: str,
    credential_handle_id: str,
    payload_schema_version: str,
    adapter_version: str,
    payload_class_id: str,
    payload_text: str,
    platform_formatting: str,
    thread_split: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    caption: str | None = None,
    hashtags: tuple[str, ...] | list[str] = (),
    media_manifest_hash: str | None = None,
    alt_text_hash: str | None = None,
    link_preview_class: str = "none",
    visibility_class: str = "public",
    disclosure_class: str = "none",
    content_lane: str = "general",
    policy_snapshot_id: str = "v1",
    source_or_research_packet_id: str | None = None,
    guardrail_result_id: str | None = None,
) -> dict[str, Any] | None:
    """Constructs a stable ordered canonical representation of the payload hash input."""
    raw_dict = {
        "platform_id": platform_id,
        "destination_binding_id": destination_binding_id,
        "credential_handle_id": credential_handle_id,
        "payload_schema_version": payload_schema_version,
        "adapter_version": adapter_version,
        "payload_class_id": payload_class_id,
        "payload_text": payload_text,
        "platform_formatting": platform_formatting,
        "thread_split": thread_split,
        "title": title,
        "subtitle": subtitle,
        "caption": caption,
        "hashtags": sorted(list(hashtags)),
        "media_manifest_hash": media_manifest_hash,
        "alt_text_hash": alt_text_hash,
        "link_preview_class": link_preview_class,
        "visibility_class": visibility_class,
        "disclosure_class": disclosure_class,
        "content_lane": content_lane,
        "policy_snapshot_id": policy_snapshot_id,
        "source_or_research_packet_id": source_or_research_packet_id,
        "guardrail_result_id": guardrail_result_id,
    }
    # Sort dictionary keys to guarantee canonical JSON format
    return {k: raw_dict[k] for k in sorted(raw_dict.keys())}


def assert_payload_hash_input_safe(input_dict: dict[str, Any]) -> None:
    """Verifies that no secret-shaped strings or forbidden keyword patterns exist in the input dict."""
    def check_value(val: Any) -> None:
        if isinstance(val, str):
            # Check secret patterns
            for pattern in SECRET_PATTERNS:
                if pattern.search(val):
                    raise AssertionError("Secret-shaped string detected in payload hash input.")
            # Check forbidden keywords
            if FORBIDDEN_KEYWORDS.search(val):
                raise AssertionError("Forbidden credential, cookie, or session keyword detected in input.")
        elif isinstance(val, dict):
            for k, v in val.items():
                if FORBIDDEN_KEYWORDS.search(k):
                    raise AssertionError(f"Forbidden key '{k}' detected in input.")
                check_value(v)
        elif isinstance(val, (list, tuple)):
            for item in val:
                check_value(item)

    check_value(input_dict)


def compute_payload_hash(input_dict: dict[str, Any]) -> str:
    """Computes the deterministic SHA-256 payload hash from canonical dictionary."""
    assert_payload_hash_input_safe(input_dict)
    serialized = json.dumps(input_dict, ensure_ascii=False, sort_keys=True)
    return sha256(serialized.encode("utf-8")).hexdigest()


def payload_hash_short(full_hash: str) -> str:
    """Returns a short 8-character prefix of the payload hash."""
    return full_hash[:8]


def approval_payload_hash_packet() -> dict[str, Any]:
    """Generates the approval payload hash contract description packet."""
    demo_input = canonical_payload_hash_input(
        platform_id="x_profile",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        payload_schema_version="v1",
        adapter_version="1.0.0",
        payload_class_id="x_short_post",
        payload_text="Grounded macro insight",
        platform_formatting="plain",
    )
    assert demo_input is not None
    full_hash = compute_payload_hash(demo_input)
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "demo_hash_input": demo_input,
        "demo_hash": full_hash,
        "demo_hash_short": payload_hash_short(full_hash),
    }
