"""Redacted platform error classifier for future ContentOps live gates.

Classifies symbolic/redacted metadata only. No raw provider bodies, headers, tokens,
credential values, network calls, retries, or live requests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_LIVE_GATE_STATE_MACHINE_AND_ERROR_CLASSIFIER_CORE_V0"
MODEL = "contentops.platform_error_classifier"
MODEL_VERSION = "0175_PLATFORM_ERROR_CLASSIFIER_V0"

ERROR_CLASSES = (
    "none",
    "blocked_before_request",
    "credential_missing",
    "credential_invalid",
    "permission_missing",
    "scope_missing",
    "wrong_account",
    "destination_not_found",
    "app_review_required",
    "paid_or_quota_gate_required",
    "rate_limited",
    "request_budget_exceeded",
    "media_requirement_missing",
    "payload_invalid",
    "policy_violation",
    "unsupported_endpoint",
    "stale_official_docs",
    "transient_platform_error",
    "unknown_provider_error",
    "safety_stop_secret_risk",
)

SECRET_VALUE_RE = re.compile(
    r"(\b\d{6,12}:[A-Za-z0-9_-]{30,}\b|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b|bearer\s+[A-Za-z0-9._\-]{20,})",
    re.IGNORECASE,
)
SECRET_KEY_RE = re.compile(r"(?i)(raw_response|raw_header|headers|token|cookie|session|credential|authorization|provider_body)")


@dataclass(frozen=True)
class PlatformErrorInput:
    platform_id: str
    endpoint_family: str
    method: str
    http_status_class: str | None = None
    symbolic_status: str | None = None
    provider_error_code_redacted: str | None = None
    provider_error_type_redacted: str | None = None
    response_class: str | None = None
    request_budget_used: int = 0
    retry_count: int = 0
    permission_context: str = "unknown"
    scope_context: str = "unknown"
    account_binding_context: str = "unknown"
    media_context: str = "unknown"
    quota_context: str = "unknown"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlatformErrorClassification:
    error_class: str
    severity: str
    retry_allowed: bool
    auto_retry_allowed: bool
    manual_fallback_required: bool
    operator_action_required: bool
    credential_repair_required: bool
    scope_permission_repair_required: bool
    destination_rebind_required: bool
    app_review_required: bool
    quota_or_paid_gate_required: bool
    re_ground_docs_required: bool
    raw_response_safe_to_persist: bool
    raw_headers_safe_to_persist: bool
    token_safe_to_log: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PlatformErrorSafetyError(ValueError):
    """Raised when raw/secret-shaped error metadata is supplied."""


def _walk_secret_findings(value: Any, path: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_s = str(key)
            child_path = f"{path}.{key_s}" if path else key_s
            if SECRET_KEY_RE.search(key_s):
                findings.append(child_path)
            findings.extend(_walk_secret_findings(child, child_path))
    elif isinstance(value, (list, tuple)):
        for idx, child in enumerate(value):
            findings.extend(_walk_secret_findings(child, f"{path}[{idx}]"))
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        findings.append(path or "<value>")
    return sorted(set(findings))


def assert_redacted_error_safe(metadata: dict[str, Any] | PlatformErrorInput) -> None:
    data = metadata.as_dict() if isinstance(metadata, PlatformErrorInput) else dict(metadata or {})
    findings = _walk_secret_findings(data)
    if findings:
        raise PlatformErrorSafetyError(f"unsafe_error_metadata:{','.join(findings)}")


def _input(data: dict[str, Any] | PlatformErrorInput) -> PlatformErrorInput:
    if isinstance(data, PlatformErrorInput):
        return data
    raw = dict(data or {})
    assert_redacted_error_safe(raw)
    allowed = set(PlatformErrorInput.__dataclass_fields__)
    return PlatformErrorInput(**{key: value for key, value in raw.items() if key in allowed})


def classify_http_status_family(http_status_class: str | None, symbolic_status: str | None = None) -> str:
    status = (symbolic_status or http_status_class or "").lower()
    if status in {"none", "ok", "2xx", "success"}:
        return "none"
    if "blocked_before_request" in status:
        return "blocked_before_request"
    if "401" in status or "unauthorized" in status:
        return "credential_invalid"
    if "403" in status or "forbidden" in status:
        return "permission_missing"
    if "404" in status or "not_found" in status:
        return "destination_not_found"
    if "408" in status or "409" in status or "400" in status:
        return "payload_invalid"
    if "429" in status or "rate" in status:
        return "rate_limited"
    if "5xx" in status or "500" in status or "502" in status or "503" in status or "504" in status:
        return "transient_platform_error"
    return "unknown_provider_error"


def classify_permission_scope_error(permission_context: str, scope_context: str) -> str:
    p = (permission_context or "").lower()
    s = (scope_context or "").lower()
    if "missing" in p or "denied" in p or "unverified" in p:
        return "permission_missing"
    if "missing" in s or "denied" in s or "unverified" in s:
        return "scope_missing"
    return "none"


def classify_destination_error(account_binding_context: str) -> str:
    ctx = (account_binding_context or "").lower()
    if "wrong" in ctx or "mismatch" in ctx:
        return "wrong_account"
    if "not_found" in ctx or "missing_destination" in ctx or "destination_missing" in ctx:
        return "destination_not_found"
    return "none"


def classify_media_error(media_context: str) -> str:
    ctx = (media_context or "").lower()
    if "missing" in ctx or "required" in ctx or "invalid" in ctx:
        return "media_requirement_missing"
    return "none"


def classify_quota_error(quota_context: str, request_budget_used: int) -> str:
    ctx = (quota_context or "").lower()
    if request_budget_used > 1:
        return "request_budget_exceeded"
    if "paid" in ctx or "quota" in ctx or "budget" in ctx or "limit" in ctx:
        return "paid_or_quota_gate_required"
    return "none"


def _severity(error_class: str) -> str:
    if error_class == "none":
        return "info"
    if error_class in {"transient_platform_error", "rate_limited", "unknown_provider_error"}:
        return "review"
    if error_class == "safety_stop_secret_risk":
        return "safety_stop"
    return "blocker"


def _classification(error_class: str) -> PlatformErrorClassification:
    return PlatformErrorClassification(
        error_class=error_class,
        severity=_severity(error_class),
        retry_allowed=False,
        auto_retry_allowed=False,
        manual_fallback_required=error_class != "none",
        operator_action_required=error_class != "none",
        credential_repair_required=error_class in {"credential_missing", "credential_invalid"},
        scope_permission_repair_required=error_class in {"permission_missing", "scope_missing"},
        destination_rebind_required=error_class in {"wrong_account", "destination_not_found"},
        app_review_required=error_class == "app_review_required",
        quota_or_paid_gate_required=error_class in {"paid_or_quota_gate_required", "rate_limited", "request_budget_exceeded"},
        re_ground_docs_required=error_class in {"stale_official_docs", "unsupported_endpoint", "unknown_provider_error"},
        raw_response_safe_to_persist=False,
        raw_headers_safe_to_persist=False,
        token_safe_to_log=False,
    )


def classify_platform_error(metadata: dict[str, Any] | PlatformErrorInput) -> PlatformErrorClassification:
    try:
        item = _input(metadata)
        assert_redacted_error_safe(item)
    except PlatformErrorSafetyError:
        return _classification("safety_stop_secret_risk")

    symbolic = (item.symbolic_status or "").lower()
    combined = " ".join(str(x or "").lower() for x in (
        item.symbolic_status,
        item.provider_error_code_redacted,
        item.provider_error_type_redacted,
        item.response_class,
        item.permission_context,
        item.scope_context,
        item.account_binding_context,
        item.media_context,
        item.quota_context,
    ))

    ordered = (
        ("blocked_before_request", "blocked_before_request"),
        ("credential_missing", "credential_missing"),
        ("credential_invalid", "credential_invalid"),
        ("permission_missing", "permission_missing"),
        ("scope_missing", "scope_missing"),
        ("wrong_account", "wrong_account"),
        ("destination_not_found", "destination_not_found"),
        ("app_review_required", "app_review_required"),
        ("policy_violation", "policy_violation"),
        ("unsupported_endpoint", "unsupported_endpoint"),
        ("stale_official_docs", "stale_official_docs"),
        ("media_requirement_missing", "media_requirement_missing"),
        ("payload_invalid", "payload_invalid"),
    )
    for needle, error_class in ordered:
        if needle in combined:
            return _classification(error_class)

    for classifier in (
        lambda: classify_quota_error(item.quota_context, item.request_budget_used),
        lambda: classify_media_error(item.media_context),
        lambda: classify_destination_error(item.account_binding_context),
        lambda: classify_permission_scope_error(item.permission_context, item.scope_context),
    ):
        error_class = classifier()
        if error_class != "none":
            return _classification(error_class)

    if "rate" in combined or "429" in symbolic:
        return _classification("rate_limited")
    if "unknown" in combined and item.http_status_class in (None, "", "unknown"):
        return _classification("unknown_provider_error")

    return _classification(classify_http_status_family(item.http_status_class, item.symbolic_status))


def platform_error_classifier_packet() -> dict[str, Any]:
    examples = [
        classify_platform_error({
            "platform_id": "x_profile",
            "endpoint_family": "x_create_post_supervised_future",
            "method": "POST_SYMBOLIC",
            "symbolic_status": "blocked_before_request",
        }).as_dict(),
        classify_platform_error({
            "platform_id": "youtube_channel",
            "endpoint_family": "youtube_video_insert_supervised_future",
            "method": "POST_SYMBOLIC",
            "http_status_class": "429",
            "quota_context": "quota_limit_symbolic",
            "request_budget_used": 1,
        }).as_dict(),
    ]
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "error_classes": list(ERROR_CLASSES),
        "raw_response_safe_to_persist": False,
        "raw_headers_safe_to_persist": False,
        "token_safe_to_log": False,
        "unknown_error_auto_retry_allowed": False,
        "rate_limit_auto_retry_allowed": False,
        "permission_scope_retry_allowed": False,
        "examples": examples,
    }
