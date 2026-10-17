"""Read-only current-host readiness observation for the Main -> ContentOps shadow path.

This module consumes one bounded operator observation and one self-contained Main handoff.  It
does not probe the host itself, write the store, start a scheduler, call a model/provider, or
cross a publication boundary.  If a caller supplies the existing BrowserOS preflight runner,
it is invoked once with the official bounded ``auto_open=True, reconnect_once=True`` contract;
the runner remains the only owner allowed to open the installed Neo shortcut.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Callable, Mapping, Sequence

from live_contentops.browser_rendered_source_recovery_v1 import (
    ALLOWED_MCP_TOOLS,
    DEFAULT_MCP_URL,
    EXPECTED_SERVER_NAME,
    MCP_PROTOCOL_VERSION,
    OFFICIAL_LAUNCHER_PATH,
)
from live_contentops.browseros_identity_shadow_gate_v1 import (
    STATUS_AMBIGUOUS as IDENTITY_STATUS_AMBIGUOUS,
    STATUS_CONFIRMED,
    STATUS_HUMAN_REQUIRED,
    STATUS_MISSING,
    evaluate_browseros_identity_shadow,
)
from live_contentops.destination_readback_shadow_gate_v1 import (
    CONFIRMED_SHADOW,
    HUMAN_REQUIRED as DESTINATION_HUMAN_REQUIRED,
    MISMATCH as DESTINATION_MISMATCH,
    MISSING as DESTINATION_MISSING,
    UNKNOWN_WRITE,
    evaluate_destination_readback_shadow,
)
from live_contentops.main_analysis_handoff_consumer_v1 import (
    STATUS_SHADOW_REVIEW_READY,
    consume_main_analysis_handoff_shadow,
)


SCHEMA_VERSION = "contentops.current_host_readiness_observation.v1"
STATUS_HOST_OBSERVED = "HOST_OBSERVED"
STATUS_RUNTIME_PROVEN = "RUNTIME_PROVEN"
STATUS_PUBLICLY_PROVEN = "PUBLICLY_PROVEN"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"
STATUS_DISABLED_BY_DEFAULT = "DISABLED_BY_DEFAULT"
STATUS_NOT_VERIFIED = "NOT_VERIFIED"
STATUS_STALE = "STALE_OBSERVATION"
STATUS_AMBIGUOUS = "AMBIGUOUS"
STATUS_UNAVAILABLE = "UNAVAILABLE"

PORTABLE_SCHEMA_VERSION = "contentops.portable_host_readiness_receipt.v1"
PORTABLE_CANONICALIZATION = "JSON_SORT_KEYS_COMPACT_ASCII_UTF8_NO_FLOAT_NAN"
PORTABLE_PROOF_LAYERS = (
    "IMPLEMENTED",
    "TESTED",
    "INTEGRATED",
    "HOST_OBSERVED",
    "RUNTIME_PROVEN",
    "PUBLICLY_PROVEN",
)
PORTABLE_PROOF_VALUES = frozenset({
    "IMPLEMENTED",
    "TESTED",
    "INTEGRATED",
    "HOST_OBSERVED",
    "RUNTIME_PROVEN",
    "PUBLICLY_PROVEN",
    "NOT_VERIFIED",
    "STALE",
    "BLOCKED",
    "AMBIGUOUS",
})
PORTABLE_CLASSIFICATIONS = frozenset({
    "HOST_OBSERVED",
    "RUNTIME_PROVEN",
    "PUBLICLY_PROVEN",
    "NOT_VERIFIED",
    "STALE",
    "BLOCKED",
    "AMBIGUOUS",
})
PORTABLE_RIGHTS_STATUS = "READ_ONLY_OPERATOR_OBSERVATION"
PORTABLE_REDACTION_POLICY = "REJECT_SECRET_MATERIAL_AND_REDACT_BEFORE_EXPORT_V1"
_PORTABLE_SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:^|_)(?:access[_-]?token|refresh[_-]?token|cookie|password|secret|authorization|"
    r"api[_-]?key|private[_-]?key|session[_-]?token|webhook[_-]?url)(?:$|_)",
)
_PORTABLE_SECRET_VALUE_RE = re.compile(
    r"(?i)(?:bearer\s+[A-Za-z0-9._~+/=-]{8,}|(?:sk|pk|rk)-[A-Za-z0-9_-]{12,}|"
    r"(?:access[_-]?token|refresh[_-]?token|api[_-]?key|password|secret|cookie)\s*[:=]\s*[^\s,;]{8,})"
)
_PORTABLE_FLAG_KEY_RE = re.compile(
    r"(?i)(?:^|_)(?:read|allowed|performed|status|count|available|proven|authority|required)(?:$|_)",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

MAX_OBSERVATION_AGE_SECONDS = 24 * 60 * 60
EXPECTED_TASK_NAMES = (
    "CapitalChronicle_ContentOps_V1_Daily_App_Runtime",
    "CapitalChronicle_ContentOps_V1_Hourly_Audit",
    "CapitalChronicle_ContentOps_V1_Simple_Scheduler",
)
EXPECTED_PROCESS_FILTER = ("ContentOps", "python", "node", "msedge")
EXPECTED_X_CDP_PORT = 9222
EXPECTED_PUBLICATION_CDP_PORT = 9223
EXPECTED_X_ROLE = "INGESTION_ONLY"
EXPECTED_PUBLICATION_ROLE = "PUBLISHING_READBACK_ONLY"
_ZERO_WRITE_KEYS = (
    "scheduler_started",
    "database_mutation",
    "model_call_performed",
    "provider_call_performed",
    "browser_action_performed",
    "public_write_performed",
    "publication_authority",
)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _hash(value: Any) -> str:
    return sha256(_canonical_json(value)).hexdigest()


def _parse_utc(value: Any, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _finish(result: dict[str, Any]) -> dict[str, Any]:
    result["readiness_receipt_sha256"] = _hash(
        {key: value for key, value in result.items() if key != "readiness_receipt_sha256"}
    )
    return result


def _base(bridge: Mapping[str, Any], observation: Mapping[str, Any], *, enabled: bool) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_DISABLED_BY_DEFAULT if not enabled else None,
        "enabled": bool(enabled),
        "shadow_only": True,
        "immutable_receipt": True,
        "observation_id": observation.get("observation_id"),
        "observed_at_utc": observation.get("observed_at_utc"),
        "packet_id": bridge.get("packet_id"),
        "packet_logical_hash": bridge.get("packet_logical_hash"),
        "shadow_receipt_sha256": None,
        "readiness_receipt_sha256": None,
        "validation_blockers": [],
        "failure_detail": None,
        "readiness_classification": STATUS_NOT_VERIFIED,
        "host_observed": False,
        "runtime_proven": False,
        "publicly_proven": False,
        "scheduler_started": False,
        "durable_store_write_count": 0,
        "database_mutation": False,
        "model_call_count": 0,
        "provider_call_count": 0,
        "browser_action_count": 0,
        "public_write_performed": False,
        "publication_authority": False,
        "browser_preflight_runner_invocation_count": 0,
    }


def _fail(result: dict[str, Any], blockers: Sequence[str], *, status: str = STATUS_FAIL_CLOSED) -> dict[str, Any]:
    result.update(
        {
            "status": status,
            "validation_blockers": list(dict.fromkeys(str(value) for value in blockers)),
            "failure_detail": ";".join(str(value) for value in blockers),
        }
    )
    return _finish(result)


def _require_mapping(value: Any, field: str, blockers: list[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        blockers.append(f"{field}_missing_or_not_object")
        return {}
    return value


def _validate_observation_time(
    observation: Mapping[str, Any],
    *,
    now_utc: str,
    blockers: list[str],
) -> tuple[str | None, int | None]:
    try:
        observed = _parse_utc(observation.get("observed_at_utc"), field="observed_at_utc")
        now = _parse_utc(now_utc, field="now_utc")
    except ValueError as exc:
        blockers.append(str(exc))
        return None, None
    age = int((now - observed).total_seconds())
    if age < 0:
        blockers.append("observation_timestamp_in_future")
    if age > MAX_OBSERVATION_AGE_SECONDS:
        blockers.append("observation_stale")
    return _utc_text(observed), max(0, age)


def _validate_browser(
    browser: Mapping[str, Any],
    *,
    blockers: list[str],
) -> str:
    status = str(browser.get("status") or "")
    endpoint = str(browser.get("endpoint") or "")
    if endpoint != DEFAULT_MCP_URL:
        blockers.append("browser_endpoint_not_allowlisted")
    tools = sorted(str(value) for value in browser.get("allowed_tools") or [])
    if tools != sorted(ALLOWED_MCP_TOOLS):
        blockers.append("browser_tool_allowlist_invalid")
    if browser.get("read_only") is not True or browser.get("credential_or_session_material_read") is not False:
        blockers.append("browser_read_only_boundary_invalid")
    if any(browser.get(key) is True for key in ("public_write_performed", "publication_authority", "browser_action_performed")):
        blockers.append("browser_side_effect_or_authority_flag")
    launcher_path = str(browser.get("official_launcher_path") or OFFICIAL_LAUNCHER_PATH)
    if launcher_path != OFFICIAL_LAUNCHER_PATH:
        blockers.append("browser_launcher_path_not_allowlisted")
    if int(browser.get("launcher_attempts") or 0) > 1:
        blockers.append("browser_launcher_attempt_budget_exceeded")
    if int(browser.get("reconnect_attempts") or 0) > 1:
        blockers.append("browser_reconnect_attempt_budget_exceeded")
    if status == "PASS":
        if str(browser.get("server_name") or "") != EXPECTED_SERVER_NAME:
            blockers.append("browser_server_identity_invalid")
        if str(browser.get("mcp_protocol_version") or "") != MCP_PROTOCOL_VERSION:
            blockers.append("browser_protocol_identity_invalid")
        if not str(browser.get("server_version") or ""):
            blockers.append("browser_server_version_missing")
        if browser.get("official_launcher_invoked") is True and int(browser.get("launcher_attempts") or 0) != 1:
            blockers.append("browser_launcher_observation_inconsistent")
        return STATUS_HOST_OBSERVED
    if status in {"BROWSER_UNAVAILABLE", STATUS_UNAVAILABLE, STATUS_NOT_VERIFIED, STATUS_MISSING}:
        return STATUS_UNAVAILABLE
    if status in {STATUS_AMBIGUOUS, STATUS_HUMAN_REQUIRED}:
        return STATUS_AMBIGUOUS
    blockers.append("browser_status_invalid")
    return STATUS_FAIL_CLOSED


def _validate_cdp(
    component: Mapping[str, Any],
    *,
    expected_port: int,
    expected_role: str,
    field: str,
    blockers: list[str],
) -> str:
    status = str(component.get("status") or "")
    if component.get("cdp_port") != expected_port:
        blockers.append(f"{field}_cdp_port_invalid")
    if component.get("role") != expected_role:
        blockers.append(f"{field}_role_invalid")
    if component.get("read_only") is not True:
        blockers.append(f"{field}_read_only_required")
    if any(component.get(key) is True for key in ("browser_action_performed", "public_write_performed", "publication_authority")):
        blockers.append(f"{field}_side_effect_or_authority_flag")
    if status in {"REACHABLE_READ_ONLY", "PASS_READ_ONLY", "PASS_TCP_ATTACHABLE"}:
        return STATUS_HOST_OBSERVED
    if status in {"UNAVAILABLE", "NOT_VERIFIED", "MISSING"}:
        return STATUS_UNAVAILABLE
    if status in {STATUS_AMBIGUOUS, STATUS_HUMAN_REQUIRED}:
        return STATUS_AMBIGUOUS
    blockers.append(f"{field}_status_invalid")
    return STATUS_FAIL_CLOSED


def _validate_tasks(tasks_component: Mapping[str, Any], blockers: list[str]) -> str:
    if tasks_component.get("status") not in {"OBSERVED", "DISABLED", "NOT_VERIFIED", "UNAVAILABLE"}:
        blockers.append("scheduler_task_observation_status_invalid")
    rows = tasks_component.get("tasks")
    if not isinstance(rows, list):
        blockers.append("scheduler_tasks_missing")
        return STATUS_NOT_VERIFIED
    by_name = {str(row.get("name") or ""): row for row in rows if isinstance(row, Mapping)}
    if set(by_name) != set(EXPECTED_TASK_NAMES):
        blockers.append("scheduler_task_name_set_invalid")
    if len(by_name) != len(rows):
        blockers.append("scheduler_task_duplicate_or_malformed")
    for name in EXPECTED_TASK_NAMES:
        row = by_name.get(name)
        if not isinstance(row, Mapping):
            continue
        if row.get("state_text") not in {"Disabled", "Ready", "Running", "Unknown", "NOT_VERIFIED"}:
            blockers.append(f"scheduler_task_state_text_invalid:{name}")
        if row.get("state_value") not in {1, 3, 4, 0, None}:
            blockers.append(f"scheduler_task_state_value_invalid:{name}")
    if tasks_component.get("status") in {"NOT_VERIFIED", "UNAVAILABLE"}:
        return STATUS_UNAVAILABLE
    return STATUS_HOST_OBSERVED


def _validate_process_filter(process: Mapping[str, Any], blockers: list[str]) -> str:
    terms = tuple(str(value) for value in process.get("filter_terms") or [])
    if terms != EXPECTED_PROCESS_FILTER:
        blockers.append("process_filter_terms_invalid")
    if process.get("status") not in {"OBSERVED", "NOT_VERIFIED", "UNAVAILABLE"}:
        blockers.append("process_filter_status_invalid")
    if not isinstance(process.get("matching_process_count"), int) or int(process.get("matching_process_count")) < 0:
        blockers.append("process_filter_count_invalid")
    if process.get("status") in {"NOT_VERIFIED", "UNAVAILABLE"}:
        return STATUS_UNAVAILABLE
    return STATUS_HOST_OBSERVED


def _validate_store_and_counters(
    store: Mapping[str, Any], counters: Mapping[str, Any], blockers: list[str]
) -> None:
    if store.get("status") not in {"READ_ONLY_INTEGRITY_PASS", "NOT_VERIFIED", "UNAVAILABLE"}:
        blockers.append("store_observation_status_invalid")
    if store.get("status") == "READ_ONLY_INTEGRITY_PASS":
        if str(store.get("integrity_check") or "").lower() != "ok":
            blockers.append("store_integrity_check_not_ok")
        if int(store.get("foreign_key_violation_count") or 0) != 0:
            blockers.append("store_foreign_key_violation_present")
        if int(store.get("unknown_write_count") or 0) != 0:
            blockers.append("store_unknown_write_present")
    for key in _ZERO_WRITE_KEYS:
        if counters.get(key) is True:
            blockers.append(f"counter_side_effect_flag:{key}")
    for key in ("durable_store_write_count", "model_call_count", "provider_call_count", "browser_action_count"):
        if not isinstance(counters.get(key), int) or int(counters.get(key)) < 0:
            blockers.append(f"counter_invalid:{key}")
    if int(counters.get("durable_store_write_count") or 0) != 0:
        blockers.append("durable_store_write_count_nonzero")


def _run_shadow_consumer(
    bridge: Mapping[str, Any],
    *,
    now_utc: str,
) -> dict[str, Any]:
    return consume_main_analysis_handoff_shadow(
        bridge,
        enabled=True,
        now_utc=now_utc,
    )


def consume_current_host_readiness_observation(
    bridge: Mapping[str, Any],
    observation: Mapping[str, Any],
    *,
    enabled: bool = False,
    now_utc: str | None = None,
    preflight_runner: Callable[..., Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Attach one bounded host observation to the existing Main handoff shadow receipt."""

    observation = dict(observation or {})
    result = _base(bridge or {}, observation, enabled=enabled)
    if not enabled:
        return _fail(result, ["host_readiness_observation_disabled_by_default"], status=STATUS_DISABLED_BY_DEFAULT)
    if not isinstance(bridge, Mapping):
        return _fail(result, ["main_bridge_missing_or_not_object"], status=STATUS_NOT_VERIFIED)
    if not isinstance(observation, Mapping):
        return _fail(result, ["host_observation_missing_or_not_object"], status=STATUS_NOT_VERIFIED)

    now = now_utc or _utc_text(datetime.now(timezone.utc))
    blockers: list[str] = []
    observed_at, age_seconds = _validate_observation_time(
        observation, now_utc=now, blockers=blockers
    )
    result["observed_at_utc"] = observed_at
    result["observation_age_seconds"] = age_seconds
    if observed_at is None:
        observation_freshness = "INVALID"
    elif any(value == "observation_stale" for value in blockers):
        observation_freshness = "STALE"
    elif any(value == "observation_timestamp_in_future" for value in blockers):
        observation_freshness = "FUTURE"
    else:
        observation_freshness = "FRESH"

    browser = dict(observation.get("browseros") or {})
    if not browser and preflight_runner is not None:
        try:
            browser = dict(preflight_runner(auto_open=True, reconnect_once=True))
            result["browser_preflight_runner_invocation_count"] = 1
        except (OSError, RuntimeError, TimeoutError, TypeError, ValueError) as exc:
            browser = {
                "status": "BROWSER_UNAVAILABLE",
                "endpoint": DEFAULT_MCP_URL,
                "official_launcher_path": OFFICIAL_LAUNCHER_PATH,
                "allowed_tools": sorted(ALLOWED_MCP_TOOLS),
                "read_only": True,
                "credential_or_session_material_read": False,
                "failure_detail": str(exc) or type(exc).__name__,
            }
            result["browser_preflight_runner_invocation_count"] = 1
    if not browser:
        blockers.append("browser_observation_missing")
    browser_class = _validate_browser(browser, blockers=blockers)

    x_cdp = _require_mapping(observation.get("x_ingestion_cdp"), "x_ingestion_cdp", blockers)
    publication_cdp = _require_mapping(observation.get("publication_cdp"), "publication_cdp", blockers)
    x_class = _validate_cdp(
        x_cdp,
        expected_port=EXPECTED_X_CDP_PORT,
        expected_role=EXPECTED_X_ROLE,
        field="x_ingestion_cdp",
        blockers=blockers,
    )
    publication_class = _validate_cdp(
        publication_cdp,
        expected_port=EXPECTED_PUBLICATION_CDP_PORT,
        expected_role=EXPECTED_PUBLICATION_ROLE,
        field="publication_cdp",
        blockers=blockers,
    )
    task_class = _validate_tasks(
        _require_mapping(observation.get("scheduler_tasks"), "scheduler_tasks", blockers),
        blockers,
    )
    process_class = _validate_process_filter(
        _require_mapping(observation.get("process_filter"), "process_filter", blockers),
        blockers,
    )
    store = _require_mapping(observation.get("store"), "store", blockers)
    counters = _require_mapping(observation.get("counters"), "counters", blockers)
    _validate_store_and_counters(store, counters, blockers)

    identity_input = observation.get("identity_shadow_input")
    if not isinstance(identity_input, Mapping):
        blockers.append("identity_shadow_input_missing")
        identity_shadow: dict[str, Any] = {"status": STATUS_MISSING}
    else:
        identity_shadow = evaluate_browseros_identity_shadow(**dict(identity_input))
    destination_input = observation.get("destination_shadow_input")
    if not isinstance(destination_input, Mapping):
        blockers.append("destination_shadow_input_missing")
        destination_shadow: dict[str, Any] = {"status": DESTINATION_MISSING}
    else:
        destination_shadow = evaluate_destination_readback_shadow(**dict(destination_input))
    result["identity_shadow"] = identity_shadow
    result["destination_shadow"] = destination_shadow

    if identity_shadow.get("status") in {IDENTITY_STATUS_AMBIGUOUS, STATUS_HUMAN_REQUIRED}:
        blockers.append("visible_identity_ambiguous_or_human_required")
    elif identity_shadow.get("status") != STATUS_CONFIRMED:
        blockers.append(f"visible_identity_not_confirmed:{identity_shadow.get('status')}")
    if destination_shadow.get("status") == UNKNOWN_WRITE:
        blockers.append("destination_unknown_write_stop_retry_readback_reconcile")
    elif destination_shadow.get("status") in {DESTINATION_HUMAN_REQUIRED, DESTINATION_MISMATCH}:
        blockers.append(f"destination_identity_ambiguous_or_mismatched:{destination_shadow.get('status')}")
    elif destination_shadow.get("status") != CONFIRMED_SHADOW:
        blockers.append(f"destination_shadow_not_confirmed:{destination_shadow.get('status')}")

    shadow = _run_shadow_consumer(bridge, now_utc=now)
    result["shadow_status"] = shadow.get("status")
    result["shadow_receipt_sha256"] = shadow.get("receipt_sha256")
    result["consumer_result"] = shadow
    if shadow.get("status") != STATUS_SHADOW_REVIEW_READY:
        blockers.append(f"main_shadow_not_ready:{shadow.get('status')}:{shadow.get('failure_detail')}")
    packet_binding = observation.get("packet_binding")
    if isinstance(packet_binding, Mapping):
        if packet_binding.get("packet_logical_hash") != bridge.get("packet_logical_hash"):
            blockers.append("observation_packet_hash_binding_mismatch")
        if packet_binding.get("shadow_receipt_sha256") != shadow.get("receipt_sha256"):
            blockers.append("observation_shadow_receipt_hash_binding_mismatch")

    public_flags = {
        "publicly_proven": observation.get("publicly_proven"),
        "public_write_performed": observation.get("public_write_performed"),
        "publication_authority": observation.get("publication_authority"),
    }
    if any(value is True for value in public_flags.values()):
        blockers.append("public_proof_or_authority_cannot_be_created_by_observer")
    runtime_proven = bool(observation.get("runtime_proven"))
    if runtime_proven and observation.get("runtime_evidence_status") != "PROVEN_READ_ONLY":
        blockers.append("runtime_proven_flag_without_read_only_runtime_evidence")
        runtime_proven = False

    result.update(
        {
            "browseros": browser,
            "x_ingestion_cdp": x_cdp,
            "publication_cdp": publication_cdp,
            "scheduler_tasks": observation.get("scheduler_tasks"),
            "process_filter": observation.get("process_filter"),
            "store": store,
            "counters": counters,
            "host_observed": not blockers,
            "runtime_proven": runtime_proven and not blockers,
            "publicly_proven": False,
            "proof_layers": {
                "HOST_OBSERVED": not blockers,
                "RUNTIME_PROVEN": runtime_proven and not blockers,
                "PUBLICLY_PROVEN": False,
            },
            "boundary_classes": {
                "browseros": browser_class,
                "x_ingestion_cdp": x_class,
                "publication_cdp": publication_class,
                "scheduler": task_class,
                "process_filter": process_class,
            },
            "evidence_taxonomy": {
                "observation_freshness": observation_freshness,
                "browseros": browser_class,
                "x_ingestion_cdp": x_class,
                "publication_cdp": publication_class,
                "scheduler": task_class,
                "process_filter": process_class,
                "visible_identity": str(identity_shadow.get("status") or STATUS_NOT_VERIFIED),
                "destination_identity": str(destination_shadow.get("status") or DESTINATION_MISSING),
            },
            "packet_hashes": {
                "main_packet_logical_hash": bridge.get("packet_logical_hash"),
                "v3_packet_logical_hash": shadow.get("v3_packet_logical_hash"),
                "shadow_receipt_sha256": shadow.get("receipt_sha256"),
            },
        }
    )
    if blockers:
        status = STATUS_AMBIGUOUS if any("ambiguous" in value or "mismatched" in value for value in blockers) else STATUS_FAIL_CLOSED
        result["readiness_classification"] = STATUS_AMBIGUOUS if status == STATUS_AMBIGUOUS else STATUS_NOT_VERIFIED
        return _fail(result, blockers, status=status)
    result["status"] = STATUS_RUNTIME_PROVEN if runtime_proven else STATUS_HOST_OBSERVED
    result["readiness_classification"] = result["status"]
    result["validation_blockers"] = []
    return _finish(result)


def _portable_canonical_bytes(value: Any) -> bytes:
    """Serialize portable receipts without Python-specific ``default=str`` coercion."""

    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("portable_receipt_non_json_value") from exc


def portable_receipt_sha256(value: Mapping[str, Any]) -> str:
    """Hash the canonical portable payload, excluding its self-hash field."""

    body = {
        key: item for key, item in value.items() if key != "portable_receipt_sha256"
    }
    return sha256(_portable_canonical_bytes(body)).hexdigest()


def _portable_sensitive_paths(value: Any, *, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized = key_text.replace("-", "_").casefold()
            if _PORTABLE_SENSITIVE_KEY_RE.search(normalized) and not _PORTABLE_FLAG_KEY_RE.search(normalized):
                if item not in (None, "", False, 0, [], {}):
                    found.append(child_path)
            found.extend(_portable_sensitive_paths(item, path=child_path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found.extend(_portable_sensitive_paths(item, path=f"{path}[{index}]"))
    elif isinstance(value, str) and _PORTABLE_SECRET_VALUE_RE.search(value):
        found.append(path)
    return found


def _portable_redact(value: Any, *, path: str = "$") -> tuple[Any, list[str]]:
    redacted_paths: list[str] = []
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized = key_text.replace("-", "_").casefold()
            sensitive_key = (
                _PORTABLE_SENSITIVE_KEY_RE.search(normalized) is not None
                and _PORTABLE_FLAG_KEY_RE.search(normalized) is None
            )
            if sensitive_key and item not in (None, "", False, 0, [], {}):
                output[key_text] = "<REDACTED>"
                redacted_paths.append(child_path)
                continue
            safe, paths = _portable_redact(item, path=child_path)
            output[key_text] = safe
            redacted_paths.extend(paths)
        return output, redacted_paths
    if isinstance(value, (list, tuple)):
        output = []
        for index, item in enumerate(value):
            safe, paths = _portable_redact(item, path=f"{path}[{index}]")
            output.append(safe)
            redacted_paths.extend(paths)
        return output, redacted_paths
    if isinstance(value, str) and _PORTABLE_SECRET_VALUE_RE.search(value):
        return "<REDACTED>", [path]
    return value, []


def _portable_source_receipt_hash_valid(receipt: Mapping[str, Any]) -> bool:
    supplied = str(receipt.get("readiness_receipt_sha256") or "")
    return bool(_SHA256_RE.fullmatch(supplied)) and supplied == _hash(
        {key: value for key, value in receipt.items() if key != "readiness_receipt_sha256"}
    )


def _portable_observation_projection(source: Mapping[str, Any]) -> dict[str, Any]:
    """Keep the exact host/readiness observations while omitting the nested editorial packet."""

    fields = (
        "schema_version",
        "status",
        "readiness_classification",
        "observation_id",
        "observed_at_utc",
        "observation_age_seconds",
        "browseros",
        "x_ingestion_cdp",
        "publication_cdp",
        "scheduler_tasks",
        "process_filter",
        "store",
        "counters",
        "identity_shadow",
        "destination_shadow",
        "shadow_status",
        "shadow_receipt_sha256",
        "packet_hashes",
        "evidence_taxonomy",
        "boundary_classes",
        "proof_layers",
        "host_observed",
        "runtime_proven",
        "publicly_proven",
        "scheduler_started",
        "durable_store_write_count",
        "database_mutation",
        "model_call_count",
        "provider_call_count",
        "browser_action_count",
        "public_write_performed",
        "publication_authority",
        "validation_blockers",
        "failure_detail",
    )
    return {field: source[field] for field in fields if field in source}


def _portable_layer_value(
    source: Mapping[str, Any],
    layer: str,
    supplied: Mapping[str, Any],
) -> str:
    value = supplied.get(layer)
    if value in PORTABLE_PROOF_VALUES:
        return str(value)
    source_layers = source.get("proof_layers") if isinstance(source.get("proof_layers"), Mapping) else {}
    source_value = source_layers.get(layer)
    if source_value is True:
        return layer
    if source_value in PORTABLE_PROOF_VALUES:
        return str(source_value)
    return "NOT_VERIFIED"


def _portable_classification(
    source: Mapping[str, Any],
    *,
    freshness_status: str,
    secret_material: bool,
    source_hash_valid: bool,
) -> str:
    if secret_material or not source_hash_valid:
        return "BLOCKED"
    if freshness_status == "STALE":
        return "STALE"
    source_class = str(source.get("readiness_classification") or source.get("status") or "")
    if source_class in {"AMBIGUOUS", "HUMAN_REQUIRED"}:
        return "AMBIGUOUS"
    if source_class == STATUS_HOST_OBSERVED and source.get("host_observed") is True:
        return "HOST_OBSERVED"
    if source_class == STATUS_RUNTIME_PROVEN and source.get("runtime_proven") is True:
        return "RUNTIME_PROVEN"
    if source_class == STATUS_PUBLICLY_PROVEN and source.get("publicly_proven") is True:
        return "PUBLICLY_PROVEN"
    return "NOT_VERIFIED"


def _portable_base(
    *,
    source_repository: str,
    source_branch: str,
    source_head: str,
    source_receipt_sha256: str | None,
    observation_id: str | None,
    observed_at_utc: str | None,
    known_at_utc: str,
    as_of_utc: str,
    source_hash_valid: bool,
) -> dict[str, Any]:
    return {
        "schema_version": PORTABLE_SCHEMA_VERSION,
        "canonicalization": PORTABLE_CANONICALIZATION,
        "export_status": "PASS" if source_hash_valid else "BLOCKED",
        "classification": "NOT_VERIFIED" if source_hash_valid else "BLOCKED",
        "source": {
            "repository": source_repository,
            "branch": source_branch,
            "head": source_head,
            "producer_schema": SCHEMA_VERSION,
            "source_receipt_sha256": source_receipt_sha256,
            "source_receipt_hash_verified": source_hash_valid,
        },
        "observation": {
            "observation_id": observation_id,
            "observed_at_utc": observed_at_utc,
            "known_at_utc": known_at_utc,
        },
        "freshness": {
            "as_of_utc": as_of_utc,
            "known_at_utc": known_at_utc,
            "age_seconds": None,
            "max_age_seconds": MAX_OBSERVATION_AGE_SECONDS,
            "status": "UNAVAILABLE",
        },
        "rights": {
            "status": PORTABLE_RIGHTS_STATUS,
            "basis": "READ_ONLY_HOST_OBSERVATION_NO_PUBLICATION_OR_ACCOUNT_AUTHORITY",
            "redaction_policy": PORTABLE_REDACTION_POLICY,
            "raw_payload_included": False,
        },
        "proof_layers": {layer: "NOT_VERIFIED" for layer in PORTABLE_PROOF_LAYERS},
        "packet_hashes": {},
        "zero_effect": {
            "scheduler_started": False,
            "durable_store_write_count": 0,
            "database_mutation": False,
            "model_call_count": 0,
            "provider_call_count": 0,
            "browser_action_count": 0,
            "public_write_performed": False,
            "publication_authority": False,
        },
        "redaction": {
            "applied": False,
            "secret_material_detected": False,
            "redacted_paths": [],
            "raw_payload_not_included": True,
        },
        "validation_blockers": [],
        "portable_receipt_sha256": None,
    }


def export_portable_host_readiness_receipt(
    readiness_receipt: Mapping[str, Any],
    *,
    source_repository: str,
    source_branch: str,
    source_head: str,
    known_at_utc: str | None = None,
    as_of_utc: str | None = None,
    max_age_seconds: int = MAX_OBSERVATION_AGE_SECONDS,
    producer_proof_layers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Export a deterministic, redacted receipt that a foreign consumer can validate alone."""

    source = dict(readiness_receipt or {})
    source_hash_valid = _portable_source_receipt_hash_valid(source)
    source_hash = str(source.get("readiness_receipt_sha256") or "") or None
    observed_at = source.get("observed_at_utc")
    known_at = known_at_utc or str(observed_at or "")
    as_of = as_of_utc or known_at
    result = _portable_base(
        source_repository=str(source_repository),
        source_branch=str(source_branch),
        source_head=str(source_head),
        source_receipt_sha256=source_hash,
        observation_id=str(source.get("observation_id") or "") or None,
        observed_at_utc=str(observed_at or "") or None,
        known_at_utc=known_at,
        as_of_utc=as_of,
        source_hash_valid=source_hash_valid,
    )
    blockers: list[str] = []
    if not source_hash_valid:
        blockers.append("source_readiness_receipt_hash_invalid")
    if not source_repository or not source_branch or not source_head:
        blockers.append("source_provenance_incomplete")
    try:
        observed_dt = _parse_utc(known_at, field="known_at_utc")
        as_of_dt = _parse_utc(as_of, field="as_of_utc")
        age_seconds = int((as_of_dt - observed_dt).total_seconds())
        result["freshness"].update({
            "age_seconds": age_seconds,
            "max_age_seconds": int(max_age_seconds),
            "status": "FRESH" if 0 <= age_seconds <= int(max_age_seconds) else "STALE",
        })
        if age_seconds < 0:
            blockers.append("known_at_after_as_of")
    except ValueError as exc:
        blockers.append(str(exc))
        result["freshness"]["status"] = "UNAVAILABLE"
    source_projection = _portable_observation_projection(source)
    safe_source, redacted_paths = _portable_redact(source_projection)
    secret_paths = _portable_sensitive_paths(source_projection)
    secret_material = bool(secret_paths)
    result["redaction"].update({
        "applied": bool(redacted_paths),
        "secret_material_detected": secret_material,
        "redacted_paths": sorted(set(redacted_paths + secret_paths)),
    })
    if secret_material:
        blockers.append("secret_material_rejected_from_portable_export")
    if blockers:
        result["export_status"] = "BLOCKED"
        result["validation_blockers"] = list(dict.fromkeys(blockers))
        result["classification"] = _portable_classification(
            source,
            freshness_status=str(result["freshness"]["status"]),
            secret_material=secret_material,
            source_hash_valid=source_hash_valid,
        )
        if result["classification"] == "NOT_VERIFIED":
            result["classification"] = "BLOCKED"
    else:
        result["observation"]["source"] = safe_source
        supplied_layers = dict(producer_proof_layers or {})
        result["proof_layers"] = {
            layer: _portable_layer_value(source, layer, supplied_layers)
            for layer in PORTABLE_PROOF_LAYERS
        }
        result["proof_layers"]["HOST_OBSERVED"] = (
            "HOST_OBSERVED" if source.get("host_observed") is True else "NOT_VERIFIED"
        )
        result["proof_layers"]["RUNTIME_PROVEN"] = (
            "RUNTIME_PROVEN" if source.get("runtime_proven") is True else "NOT_VERIFIED"
        )
        result["proof_layers"]["PUBLICLY_PROVEN"] = (
            "PUBLICLY_PROVEN" if source.get("publicly_proven") is True else "NOT_VERIFIED"
        )
        result["packet_hashes"] = dict(source.get("packet_hashes") or {})
        result["zero_effect"] = {
            key: source.get(key, result["zero_effect"].get(key))
            for key in result["zero_effect"]
        }
        result["observation"]["source"] = safe_source
        result["classification"] = _portable_classification(
            source,
            freshness_status=str(result["freshness"]["status"]),
            secret_material=False,
            source_hash_valid=True,
        )
        if result["freshness"]["status"] == "STALE":
            result["classification"] = "STALE"
    result["portable_receipt_sha256"] = portable_receipt_sha256(result)
    return result


def validate_portable_host_readiness_receipt(
    receipt: Mapping[str, Any],
) -> list[str]:
    """Validate the portable envelope without importing any ContentOps implementation owner."""

    blockers: list[str] = []
    if receipt.get("schema_version") != PORTABLE_SCHEMA_VERSION:
        blockers.append("portable_schema_version_invalid")
    if receipt.get("canonicalization") != PORTABLE_CANONICALIZATION:
        blockers.append("portable_canonicalization_invalid")
    supplied_hash = str(receipt.get("portable_receipt_sha256") or "")
    if not _SHA256_RE.fullmatch(supplied_hash) or supplied_hash != portable_receipt_sha256(receipt):
        blockers.append("portable_receipt_hash_invalid")
    source = receipt.get("source") if isinstance(receipt.get("source"), Mapping) else {}
    for key in ("repository", "branch", "head", "producer_schema", "source_receipt_sha256"):
        if not source.get(key):
            blockers.append(f"portable_source_{key}_missing")
    source_hash = str(source.get("source_receipt_sha256") or "")
    if source_hash and not _SHA256_RE.fullmatch(source_hash):
        blockers.append("portable_source_receipt_hash_invalid")
    layers = receipt.get("proof_layers") if isinstance(receipt.get("proof_layers"), Mapping) else {}
    for layer in PORTABLE_PROOF_LAYERS:
        if layers.get(layer) not in PORTABLE_PROOF_VALUES:
            blockers.append(f"portable_proof_layer_invalid:{layer}")
    classification = str(receipt.get("classification") or "")
    if classification not in PORTABLE_CLASSIFICATIONS:
        blockers.append("portable_classification_invalid")
    freshness = receipt.get("freshness") if isinstance(receipt.get("freshness"), Mapping) else {}
    if freshness.get("status") not in {"FRESH", "STALE", "UNAVAILABLE"}:
        blockers.append("portable_freshness_status_invalid")
    rights = receipt.get("rights") if isinstance(receipt.get("rights"), Mapping) else {}
    if rights.get("status") != PORTABLE_RIGHTS_STATUS or rights.get("raw_payload_included") is not False:
        blockers.append("portable_rights_boundary_invalid")
    redaction = receipt.get("redaction") if isinstance(receipt.get("redaction"), Mapping) else {}
    if redaction.get("raw_payload_not_included") is not True:
        blockers.append("portable_redaction_raw_payload_boundary_invalid")
    secret_paths = _portable_sensitive_paths(receipt)
    if secret_paths:
        blockers.append("portable_secret_material_present")
    if receipt.get("export_status") == "PASS" and receipt.get("validation_blockers"):
        blockers.append("portable_pass_contains_blockers")
    if receipt.get("export_status") == "BLOCKED" and not receipt.get("validation_blockers"):
        blockers.append("portable_blocked_without_blockers")
    return list(dict.fromkeys(blockers))


__all__ = [
    "EXPECTED_PROCESS_FILTER",
    "EXPECTED_TASK_NAMES",
    "SCHEMA_VERSION",
    "STATUS_AMBIGUOUS",
    "STATUS_DISABLED_BY_DEFAULT",
    "STATUS_FAIL_CLOSED",
    "STATUS_HOST_OBSERVED",
    "STATUS_NOT_VERIFIED",
    "STATUS_PUBLICLY_PROVEN",
    "STATUS_RUNTIME_PROVEN",
    "STATUS_STALE",
    "STATUS_UNAVAILABLE",
    "PORTABLE_CANONICALIZATION",
    "PORTABLE_CLASSIFICATIONS",
    "PORTABLE_PROOF_LAYERS",
    "PORTABLE_PROOF_VALUES",
    "PORTABLE_SCHEMA_VERSION",
    "consume_current_host_readiness_observation",
    "export_portable_host_readiness_receipt",
    "portable_receipt_sha256",
    "validate_portable_host_readiness_receipt",
]
