"""Live Telemetry and Diagnostic Logging for ContentOps V6.

Provides safe, thread-safe telemetry collection and structured platform error
classification under Fast Ship Mode.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import datetime
import json
import os
from pathlib import Path
import re
import threading
from typing import Any
import uuid

from .platform_error_classifier import (
    PlatformErrorInput,
    assert_redacted_error_safe,
    classify_platform_error,
)
from .v6_runtime_ledgers_v1 import (
    CANONICAL_LIVE_TELEMETRY_DIR,
    CANONICAL_LIVE_TELEMETRY_FILE,
    LEGACY_LIVE_TELEMETRY_FILE as _DEFAULT_LEGACY_LIVE_TELEMETRY_FILE,
    default_legacy_paths_for,
    prepare_runtime_jsonl_for_write,
    read_jsonl_records_with_fallback,
    same_path,
)

# Registry file path (canonical Runtime root; legacy repo path retained read-only for seamless fallback/seeding)
TELEMETRY_DIR = str(CANONICAL_LIVE_TELEMETRY_DIR)
TELEMETRY_FILE = str(CANONICAL_LIVE_TELEMETRY_FILE)
LEGACY_TELEMETRY_FILE = str(_DEFAULT_LEGACY_LIVE_TELEMETRY_FILE)

# Thread lock for atomic file appends
_write_lock = threading.Lock()


def _legacy_paths_for_telemetry(path: Path, explicit_legacy: Path | None = None) -> list[Path] | None:
    if explicit_legacy is not None:
        return [explicit_legacy]
    if not same_path(path, TELEMETRY_FILE):
        return None
    if same_path(LEGACY_TELEMETRY_FILE, _DEFAULT_LEGACY_LIVE_TELEMETRY_FILE):
        return default_legacy_paths_for("live_telemetry_registry")
    return [Path(LEGACY_TELEMETRY_FILE)]


@dataclass
class TelemetryEvent:
    event_id: str = field(default_factory=lambda: "tel_" + str(uuid.uuid4()).replace("-", ""))
    timestamp: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    platform_id: str = "unknown"
    action: str = "unknown"
    success: bool = False
    latency_ms: float = 0.0
    http_status: int | None = None
    error_class: str | None = None
    severity: str | None = None
    env_keys_present: list[str] = field(default_factory=list)
    payload_size_bytes: int = 0
    response_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TelemetryRegistry:
    """Thread-safe registry for persisting telemetry events and computing summaries."""

    def __init__(
        self,
        file_path: str | Path | None = None,
        *,
        legacy_file_path: str | Path | None = None,
    ):
        self.file_path = str(file_path) if file_path is not None else TELEMETRY_FILE
        self._legacy_file_path = Path(legacy_file_path) if legacy_file_path is not None else None

    def record_event(self, event: TelemetryEvent) -> None:
        """Validates error safety and appends the telemetry event to the JSONL file."""
        data = event.to_dict()
        # Verify no raw secrets/credentials exist in the telemetry payload
        assert_redacted_error_safe(data)

        target = Path(self.file_path)
        with _write_lock:
            prepare_runtime_jsonl_for_write(
                target,
                default_path=Path(TELEMETRY_FILE),
                legacy_paths=_legacy_paths_for_telemetry(target, self._legacy_file_path),
            )
            with open(target, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(data) + "\n")

    def get_events(self) -> list[dict[str, Any]]:
        """Reads all recorded events from the JSONL registry."""
        target = Path(self.file_path)
        events = []
        with _write_lock:
            raw_events = read_jsonl_records_with_fallback(
                target,
                default_path=Path(TELEMETRY_FILE),
                union_legacy=False,
                legacy_paths=_legacy_paths_for_telemetry(target, self._legacy_file_path),
            )
            for event in raw_events:
                if event.get("platform_id") == "x" and event.get("action") in {"post","comment","edit"}:
                    # Transport success in legacy receipts never proved platform readback.
                    observed = event.get("platform_readback") or {}
                    confirmed = observed.get("verified") is True and bool(observed.get("observed_public_object_id"))
                    event = {**event,"publication_state":"PUBLISHED" if confirmed else "UNVERIFIED",
                        "publication_confirmed":confirmed}
                events.append(event)
        return events

    def get_summary(self) -> dict[str, Any]:
        """Aggregates logged events into stats and platform metrics."""
        events = self.get_events()
        total = len(events)
        successes = sum(1 for e in events if e.get("success"))
        failures = total - successes

        avg_latency = 0.0
        if total > 0:
            avg_latency = sum(e.get("latency_ms", 0.0) for e in events) / total

        platform_metrics: dict[str, Any] = {}
        for e in events:
            pid = e.get("platform_id", "unknown")
            if pid not in platform_metrics:
                platform_metrics[pid] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                    "total_latency": 0.0,
                    "error_classes": {},
                }
            metrics = platform_metrics[pid]
            metrics["total"] += 1
            if e.get("success"):
                metrics["success"] += 1
            else:
                metrics["failure"] += 1
                eclass = e.get("error_class") or "none"
                metrics["error_classes"][eclass] = metrics["error_classes"].get(eclass, 0) + 1
            metrics["total_latency"] += e.get("latency_ms", 0.0)

        # Finalize averages
        for pid, metrics in platform_metrics.items():
            if metrics["total"] > 0:
                metrics["avg_latency_ms"] = metrics["total_latency"] / metrics["total"]
            else:
                metrics["avg_latency_ms"] = 0.0
            del metrics["total_latency"]

        return {
            "total_dispatches": total,
            "success_count": successes,
            "failure_count": failures,
            "success_rate": (successes / total) if total > 0 else 0.0,
            "avg_latency_ms": avg_latency,
            "platforms": platform_metrics,
        }


def get_environment_keys() -> list[str]:
    """Helper to detect set environment keys without leaking their values."""
    target_prefixes = ["TELEGRAM", "META", "FACEBOOK", "THREADS", "X_", "LINKEDIN", "SUBSTACK"]
    keys = []
    for key in os.environ:
        if any(prefix in key.upper() for prefix in target_prefixes):
            keys.append(key)
    # CC-297: names held in Credential Manager count as set (names only, never values).
    from live_contentops.secret_store_v1 import stored_secret_names
    for key in stored_secret_names():
        if key not in keys and any(prefix in key.upper() for prefix in target_prefixes):
            keys.append(key)
    return sorted(keys)


def sanitize_summary(msg: Any) -> str:
    """Sanitizes raw response fields to avoid leaks."""
    if not msg:
        return ""
    text = str(msg)
    # Redact common token patterns, bearer tokens, or client IDs
    text = re.sub(
        r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b", "<redacted_bot_token>", text
    )
    text = re.sub(
        r"bearer\s+[A-Za-z0-9._\-]{20,}", "Bearer <redacted_token>", text, flags=re.IGNORECASE
    )
    text = re.sub(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "<redacted_jwt>", text
    )
    return text[:200]


def classify_and_record_dispatch(
    platform_id: str,
    action: str,
    adapter_result: dict[str, Any],
    latency_ms: float,
    payload_size_bytes: int = 0,
    registry_file: str | Path | None = None,
) -> TelemetryEvent:
    """Classifies the adapter dispatch outcome, maps it to a TelemetryEvent, and records it."""
    status = adapter_result.get("status")
    success = status == "SUCCESS"

    http_status_val = adapter_result.get("error_code")
    http_status = int(http_status_val) if http_status_val is not None else None

    # Construct error input context
    err_resp = adapter_result.get("error_response")
    err_body = str(err_resp) if err_resp is not None else ""

    provider_code = None
    provider_type = None

    if isinstance(err_resp, dict):
        fb_err = err_resp.get("error", {})
        if isinstance(fb_err, dict):
            provider_code = str(fb_err.get("code") or "") or None
            provider_type = fb_err.get("type") or None

    # Guess contexts to wire into PlatformErrorInput
    permission_ctx = "unknown"
    scope_ctx = "unknown"
    media_ctx = "unknown"
    quota_ctx = "unknown"

    err_lower = err_body.lower()
    if "permission" in err_lower or "unauthorized" in err_lower:
        permission_ctx = "permission_missing"
    if "scope" in err_lower:
        scope_ctx = "scope_missing"
    if "media" in err_lower or "photo" in err_lower or "video" in err_lower or "image" in err_lower:
        media_ctx = "media_requirement_missing"
    if "rate" in err_lower or "quota" in err_lower or "limit" in err_lower:
        quota_ctx = "rate_limited"

    error_class = "none"
    severity = "info"

    if not success:
        err_input = PlatformErrorInput(
            platform_id=platform_id,
            endpoint_family=f"{platform_id}_{action}_dispatch",
            method="POST",
            http_status_class=str(http_status) if http_status else None,
            symbolic_status=status,
            provider_error_code_redacted=provider_code,
            provider_error_type_redacted=provider_type,
            permission_context=permission_ctx,
            scope_context=scope_ctx,
            media_context=media_ctx,
            quota_context=quota_ctx,
        )
        classification = classify_platform_error(err_input)
        error_class = classification.error_class
        severity = classification.severity

    # Extract safe response summary
    if success:
        resp_sum = f"Created post/comment ID: {adapter_result.get('id')}"
    else:
        resp_sum = sanitize_summary(adapter_result.get("error") or adapter_result.get("error_response") or "Unknown error")

    event = TelemetryEvent(
        platform_id=platform_id,
        action=action,
        success=success,
        latency_ms=latency_ms,
        http_status=http_status,
        error_class=error_class,
        severity=severity,
        env_keys_present=get_environment_keys(),
        payload_size_bytes=payload_size_bytes,
        response_summary=resp_sum,
    )

    registry = TelemetryRegistry(registry_file)
    registry.record_event(event)
    return event
