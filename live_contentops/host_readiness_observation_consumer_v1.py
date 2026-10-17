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
    "consume_current_host_readiness_observation",
]
