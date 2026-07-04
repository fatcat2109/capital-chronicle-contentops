"""V6 platform publication identity registry.

Stores public post identity captured from supervised browser/CDP flows. No API,
credential, cookie, localStorage, sessionStorage, or token material belongs here.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

X_STATUS_RE = re.compile(r"^https://(?:x|twitter)\.com/([^/?#]+)/status/(\d+)(?:[/?#].*)?$", re.IGNORECASE)
SECRET_KEYS = ("cookie", "token", "secret", "authorization", "password", "session", "localstorage", "sessionstorage")
DEFAULT_REGISTRY_PATH = Path("docs/automation/PUBLICATION_IDENTITY_REGISTRY/platform_publication_identity_registry.jsonl")
REGISTRY_IDEMPOTENCY_KEYS = (
    "platform",
    "payload_hash",
    "public_url",
    "capture_method",
    "exact_live_execution_id",
)
EXACT_LIVE_EXECUTED_STATUS = "EXECUTED_WITH_CAPTURED_PUBLIC_URL"
EXACT_LIVE_EXECUTION_PACKET_KIND = "x_cdp_exact_live_click_execution_v0"
EXACT_LIVE_CLICK_CAPTURE_METHOD = "x_cdp_exact_live_click_execution_outcome"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_x_status_identity(url: str) -> dict[str, str]:
    """Extracts X handle/status ID from a public status URL."""
    match = X_STATUS_RE.match((url or "").strip())
    if not match:
        raise ValueError("x_status_url_required")
    handle, status_id = match.groups()
    host = urlparse(url).netloc.lower()
    canonical = f"https://x.com/{handle}/status/{status_id}"
    return {"handle": handle, "platform_publication_id": status_id, "public_url": canonical, "source_host": host}


def is_x_status_url(url: str) -> bool:
    return bool(X_STATUS_RE.match((url or "").strip()))


ALLOWED_SAFETY_KEYS = {
    "cookie_read_performed",
    "local_storage_read_performed",
    "session_storage_read_performed",
    "token_or_header_read_performed",
    "raw_secret_output",
}
BLOCKED_SECRET_KEY_MARKERS = ("dump", "value", "raw", "authorization", "password", "secret")


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if key_lower not in ALLOWED_SAFETY_KEYS and any(marker in key_lower for marker in SECRET_KEYS + BLOCKED_SECRET_KEY_MARKERS):
                return True
            if _contains_secret_key(child):
                return True
    if isinstance(value, list):
        return any(_contains_secret_key(child) for child in value)
    return False


def make_registry_record(
    *,
    platform: str,
    payload_hash: str,
    public_url: str,
    dispatch_attempt_id: str | None = None,
    outbox_entry_id: str | None = None,
    approval_id: str | None = None,
    account_binding_ref: str | None = None,
    destination_binding_ref: str | None = None,
    parent_public_url: str | None = None,
    capture_method: str = "x_cdp_permalink_capture",
    confirmation_class: str = "captured_from_post_detail_url",
    no_paid_api_used: bool = True,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Builds and validates a publication identity registry record."""
    record: dict[str, Any] = {
        "platform": platform,
        "dispatch_attempt_id": dispatch_attempt_id,
        "outbox_entry_id": outbox_entry_id,
        "approval_id": approval_id,
        "payload_hash": payload_hash,
        "account_binding_ref": account_binding_ref,
        "destination_binding_ref": destination_binding_ref,
        "public_url": public_url,
        "parent_public_url": parent_public_url,
        "capture_method": capture_method,
        "confirmation_class": confirmation_class,
        "created_at_utc": created_at_utc or utc_now_iso(),
        "no_paid_api_used": no_paid_api_used,
        "cookie_read_performed": False,
        "local_storage_read_performed": False,
        "session_storage_read_performed": False,
        "token_or_header_read_performed": False,
        "raw_secret_output": False,
    }
    validate_registry_record(record)
    if platform == "x":
        identity = extract_x_status_identity(public_url)
        record.update(identity)
        record["thread_root_url"] = parent_public_url or identity["public_url"]
    seed = "|".join([platform, payload_hash, record["public_url"], record["created_at_utc"]])
    record["registry_record_id"] = "pubid_" + platform + "_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return record


def validate_registry_record(record: dict[str, Any]) -> None:
    """Raises ValueError when a registry record is unsafe or incomplete."""
    if _contains_secret_key(record):
        raise ValueError("secret_like_registry_field_blocked")
    if not record.get("platform"):
        raise ValueError("platform_required")
    if not record.get("payload_hash"):
        raise ValueError("payload_hash_required")
    if record.get("platform") == "x":
        if record.get("no_paid_api_used") is not True:
            raise ValueError("x_paid_api_flag_blocked")
        extract_x_status_identity(str(record.get("public_url") or ""))
        parent = record.get("parent_public_url")
        if parent is not None:
            extract_x_status_identity(str(parent))
    for flag in ("cookie_read_performed", "local_storage_read_performed", "session_storage_read_performed", "token_or_header_read_performed", "raw_secret_output"):
        if record.get(flag) is not False:
            raise ValueError(f"{flag}_must_be_false")


def validate_exact_live_click_execution_for_registry(execution_packet: dict[str, Any]) -> None:
    """Requires a completed exact live-click outcome before registry append."""
    payload_hash = str(execution_packet.get("payload_hash") or "")
    captured_url = str(execution_packet.get("captured_public_x_url") or "")
    checks = {
        "packet_kind": execution_packet.get("packet_kind") == EXACT_LIVE_EXECUTION_PACKET_KIND,
        "execution_status": execution_packet.get("execution_status") == EXACT_LIVE_EXECUTED_STATUS,
        "registry_append_ready": execution_packet.get("registry_append_ready") is True,
        "registry_not_already_appended": execution_packet.get("publication_registry_record_appended") is False,
        "live_click_performed": execution_packet.get("live_click_performed") is True,
        "public_url_capture_performed": execution_packet.get("public_url_capture_performed") is True,
        "payload_hash_present": bool(payload_hash),
        "operator_payload_hash_match": execution_packet.get("operator_confirmed_payload_hash") == payload_hash,
        "captured_public_x_url_valid": is_x_status_url(captured_url),
        "no_blocked_reasons": not execution_packet.get("blocked_reasons"),
        "no_x_api_used": execution_packet.get("x_api_used") is False,
        "no_browser_or_cdp_probe": execution_packet.get("browser_or_cdp_probe_performed") is False,
        "no_public_url_fetch": execution_packet.get("public_url_fetch_made") is False,
    }
    blockers = [name for name, ok in checks.items() if ok is not True]
    if blockers:
        raise ValueError("execution_registry_reconciliation_failed:" + ",".join(blockers))


def make_registry_record_from_exact_live_click_execution(
    execution_packet: dict[str, Any],
    *,
    dispatch_attempt_id: str | None = None,
    outbox_entry_id: str | None = None,
    account_binding_ref: str | None = None,
    destination_binding_ref: str | None = None,
    parent_public_url: str | None = None,
) -> dict[str, Any]:
    """Builds a registry record only after execution packet reconciliation."""
    validate_exact_live_click_execution_for_registry(execution_packet)
    record = make_registry_record(
        platform="x",
        payload_hash=str(execution_packet["payload_hash"]),
        public_url=str(execution_packet["captured_public_x_url"]),
        dispatch_attempt_id=dispatch_attempt_id or str(execution_packet.get("exact_live_execution_id") or ""),
        outbox_entry_id=outbox_entry_id,
        approval_id=str(execution_packet.get("exact_live_authorization_id") or "") or None,
        account_binding_ref=account_binding_ref,
        destination_binding_ref=destination_binding_ref,
        parent_public_url=parent_public_url,
        capture_method=EXACT_LIVE_CLICK_CAPTURE_METHOD,
        confirmation_class="reconciled_from_exact_live_click_execution_packet",
    )
    record["exact_live_execution_id"] = execution_packet.get("exact_live_execution_id")
    record["source_execution_packet_kind"] = EXACT_LIVE_EXECUTION_PACKET_KIND
    validate_registry_record(record)
    return record


def registry_idempotency_key(record: dict[str, Any]) -> tuple[str, ...]:
    """Natural key used to prevent duplicate JSONL appends."""
    return tuple(str(record.get(key) or "") for key in REGISTRY_IDEMPOTENCY_KEYS)


def read_registry_records(path: Path | str = DEFAULT_REGISTRY_PATH) -> list[dict[str, Any]]:
    """Reads valid JSONL rows from the local registry path."""
    target = Path(path)
    if not target.exists():
        return []
    rows = []
    for line_number, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"registry_jsonl_invalid:{line_number}") from exc
        validate_registry_record(row)
        rows.append(row)
    return rows


def find_existing_registry_record(record: dict[str, Any], path: Path | str = DEFAULT_REGISTRY_PATH) -> dict[str, Any] | None:
    """Finds a prior row with the same natural publication identity."""
    key = registry_idempotency_key(record)
    return next((row for row in read_registry_records(path) if registry_idempotency_key(row) == key), None)


def audit_registry_records(path: Path | str = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    """Returns a local readback summary without fetching public URLs."""
    rows = read_registry_records(path)
    duplicate_keys = len(rows) - len({registry_idempotency_key(row) for row in rows})
    return {
        "registry_path": str(Path(path)),
        "row_count": len(rows),
        "duplicate_natural_key_count": duplicate_keys,
        "x_row_count": sum(1 for row in rows if row.get("platform") == "x"),
        "public_url_fetch_made": False,
        "browser_or_cdp_probe_performed": False,
        "x_api_used": False,
    }


def append_reconciled_exact_live_click_execution_record(
    execution_packet: dict[str, Any],
    path: Path | str = DEFAULT_REGISTRY_PATH,
    **record_kwargs: Any,
) -> Path:
    """Reconciles execution evidence, then appends the public identity record."""
    return append_registry_record(make_registry_record_from_exact_live_click_execution(execution_packet, **record_kwargs), path)


def append_registry_record(record: dict[str, Any], path: Path | str = DEFAULT_REGISTRY_PATH) -> Path:
    """Idempotently appends a validated record to JSONL and returns the target path."""
    validate_registry_record(record)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if find_existing_registry_record(record, target) is not None:
        return target
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return target


def child_reply_requires_parent(record: dict[str, Any]) -> bool:
    return bool(record.get("parent_public_url"))
