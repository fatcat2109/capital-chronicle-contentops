"""Deterministic browser budget, secret-safe diagnostics, and tiny local telemetry.

Browser automation is passive while idle.  Active interaction is authorized only by an exact
publication, exact reconciliation/readback, explicit destination verification, or due X intake.
The telemetry contains classifications and counters only; it never stores URLs, titles, command
lines, browser storage, credentials, or response bodies.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping
from urllib.parse import parse_qsl, urlsplit


SCHEMA_VERSION = "contentops.browser_interaction_budget.v1"
TELEMETRY_SCHEMA_VERSION = "contentops.browser_interaction_telemetry.v1"
SENSITIVE_QUERY_KEYS = frozenset({
    "code", "state", "access_token", "refresh_token", "client_secret",
    "authorization", "token",
})
_SENSITIVE_URL_ARGUMENT_RE = re.compile(
    r"https?://\S*[?&](?:code|state|access_token|refresh_token|client_secret|token)=",
    re.IGNORECASE,
)
_SAFE_TELEMETRY_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$")


def _safe_telemetry_label(value: Any) -> str | None:
    text = str(value or "").strip()
    return text if text and _SAFE_TELEMETRY_LABEL_RE.fullmatch(text) else None


@dataclass(frozen=True)
class BrowserInteractionBudgetV1:
    """Small testable policy object; values are seconds or per-attempt maxima."""

    edge_idle_readiness_navigation_max: int = 0
    edge_idle_auth_probe_max: int = 0
    edge_publication_active_probe_per_destination_attempt_max: int = 1
    edge_publication_tab_creation_per_destination_attempt_max: int = 1
    edge_global_social_probe_allowed: bool = False
    edge_unknown_write_readback_scope: str = "DESTINATION_LOCAL_ONLY"
    x_normal_interval_seconds: float = 1800.0
    x_hot_followup_interval_seconds: float = 900.0
    x_hot_followup_max: int = 1
    x_empty_interval_seconds: float = 3600.0
    x_transient_retry_min_seconds: float = 1800.0
    x_parallel_captures_max: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, **asdict(self)}


BROWSER_INTERACTION_BUDGET_V1 = BrowserInteractionBudgetV1()


def _path_classification(scheme: str, hostname: str, path: str) -> str:
    if hostname in {"127.0.0.1", "localhost", "::1"} and path == "/linkedin/oauth/callback":
        return "LINKEDIN_LOOPBACK_CALLBACK"
    if scheme in {"edge", "chrome", "about"}:
        return "BROWSER_INTERNAL"
    if hostname.endswith("substack.com"):
        return "SUBSTACK"
    if hostname in {"x.com", "twitter.com"}:
        return "X"
    if hostname.endswith("youtube.com") or hostname.endswith("google.com"):
        return "YOUTUBE"
    if hostname.endswith("linkedin.com"):
        return "LINKEDIN"
    if hostname:
        return "OTHER_WEB_OR_LOCAL"
    return "OTHER"


def sanitize_browser_target_metadata(target: Mapping[str, Any]) -> dict[str, Any]:
    """Return a URL/title-safe target classification; never return the raw URL or title."""

    try:
        parsed = urlsplit(str(target.get("url") or ""))
        keys = {str(key).casefold() for key, _value in parse_qsl(parsed.query, keep_blank_values=True)}
        hostname = str(parsed.hostname or "").casefold()
        path_class = _path_classification(parsed.scheme.casefold(), hostname, parsed.path)
        sensitive = bool(keys & SENSITIVE_QUERY_KEYS)
        return {
            "target_type": str(target.get("type") or "UNKNOWN"),
            "scheme": parsed.scheme.casefold() or None,
            "hostname": hostname or None,
            "path_classification": path_class,
            "query_present": bool(parsed.query),
            "fragment_present": bool(parsed.fragment),
            "oauth_sensitive_parameter_present": sensitive,
            "callback_query_contains_code": "code" in keys,
            "callback_query_contains_state": "state" in keys,
            "access_credential_parameter_present": "access_token" in keys,
            "client_credential_parameter_present": "client_secret" in keys,
            "callback_host_is_loopback": hostname in {"127.0.0.1", "localhost", "::1"},
            "title_classification": (
                "TITLE_REDACTED_SENSITIVE" if sensitive or path_class == "LINKEDIN_LOOPBACK_CALLBACK"
                else "TITLE_NOT_COLLECTED"
            ),
        }
    except Exception:
        return {
            "target_type": str(target.get("type") or "UNKNOWN"),
            "scheme": None,
            "hostname": None,
            "path_classification": "UNPARSEABLE_REDACTED",
            "query_present": False,
            "fragment_present": False,
            "oauth_sensitive_parameter_present": True,
            "callback_query_contains_code": False,
            "callback_query_contains_state": False,
            "access_credential_parameter_present": False,
            "client_credential_parameter_present": False,
            "callback_host_is_loopback": False,
            "title_classification": "TITLE_REDACTED_SENSITIVE",
        }


def sanitize_process_metadata(process: Mapping[str, Any]) -> dict[str, Any]:
    """Classify process ownership without returning its raw command line."""

    command_line = str(process.get("CommandLine") or process.get("command_line") or "")
    executable = str(process.get("Name") or process.get("name") or "").casefold()
    canonical_profile = "contentops-social-main" in command_line.casefold()
    cdp_port = 9223 if "--remote-debugging-port=9223" in command_line else (
        9222 if "--remote-debugging-port=9222" in command_line else None
    )
    return {
        "process_id": int(process.get("ProcessId") or process.get("pid") or 0),
        "executable_class": (
            "EDGE" if "edge" in executable else "CHROME" if "chrome" in executable else "OTHER"
        ),
        "canonical_profile_match": canonical_profile,
        "cdp_port": cdp_port,
        "contentops_ownership": bool(canonical_profile or "capitalchroniclebot" in command_line.casefold()),
        "sensitive_url_argument_present": bool(_SENSITIVE_URL_ARGUMENT_RE.search(command_line)),
    }


_telemetry_lock = threading.Lock()
_configured_root: Path | None = None


def configure_browser_interaction_telemetry(root: str | Path | None) -> None:
    global _configured_root
    _configured_root = Path(root).resolve() if root is not None else None


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(dict(value), stream, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def record_browser_interaction_event(
    event_type: str,
    *,
    reason: str,
    destination: str | None = None,
    occurred_at_utc: str | None = None,
) -> None:
    root = _configured_root
    if root is None:
        return
    allowed_events = {
        "active_probe", "global_probe", "navigation", "tab_created", "tab_closed", "x_capture",
    }
    if event_type not in allowed_events:
        raise ValueError("browser_interaction_event_type_invalid")
    row = {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "occurred_at_utc": occurred_at_utc or _iso_now(),
        "event_type": event_type,
        "reason": str(reason),
        "destination": str(destination) if destination else None,
    }
    with _telemetry_lock:
        root.mkdir(parents=True, exist_ok=True)
        with (root / "events.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")


@contextmanager
def browser_activity(state: str, *, reason: str, destination: str | None = None) -> Iterator[None]:
    if state not in {
        "PUBLICATION_ACTIVE", "RECONCILIATION_ACTIVE", "INGESTION_ACTIVE",
        "PERFORMANCE_OBSERVATION_ACTIVE",
    }:
        raise ValueError("browser_activity_state_invalid")
    root = _configured_root
    started = _iso_now()
    if root is not None:
        with _telemetry_lock:
            _atomic_json(root / "current_state.json", {
                "schema_version": TELEMETRY_SCHEMA_VERSION,
                "state": state,
                "reason": str(reason),
                "destination": str(destination) if destination else None,
                "started_at_utc": started,
                "last_active_browser_interaction_at_utc": started,
            })
    try:
        yield
    finally:
        finished = _iso_now()
        if root is not None:
            with _telemetry_lock:
                _atomic_json(root / "current_state.json", {
                    "schema_version": TELEMETRY_SCHEMA_VERSION,
                    "state": "IDLE",
                    "reason": str(reason),
                    "destination": str(destination) if destination else None,
                    "started_at_utc": None,
                    "last_active_browser_interaction_at_utc": finished,
                })


def browser_interaction_summary(
    root: str | Path | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    telemetry_root = Path(root).resolve() if root is not None else _configured_root
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = moment - timedelta(hours=1)
    state: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    if telemetry_root is not None:
        try:
            loaded = json.loads((telemetry_root / "current_state.json").read_text(encoding="utf-8"))
            state = dict(loaded) if isinstance(loaded, Mapping) else {}
        except (OSError, ValueError, TypeError):
            state = {}
        try:
            for line in (telemetry_root / "events.jsonl").read_text(encoding="utf-8").splitlines():
                value = json.loads(line)
                stamp = datetime.fromisoformat(str(value.get("occurred_at_utc") or "").replace("Z", "+00:00"))
                stamp = stamp.replace(tzinfo=stamp.tzinfo or timezone.utc).astimezone(timezone.utc)
                if stamp >= cutoff and isinstance(value, Mapping):
                    rows.append(dict(value))
        except (OSError, ValueError, TypeError):
            rows = []
    counts = {name: sum(1 for row in rows if row.get("event_type") == event) for name, event in {
        "browser_active_probe_count_last_hour": "active_probe",
        "browser_navigation_count_last_hour": "navigation",
        "browser_tabs_created_last_hour": "tab_created",
        "browser_tabs_closed_last_hour": "tab_closed",
        "x_capture_count_last_hour": "x_capture",
        "global_browser_probe_count_last_hour": "global_probe",
    }.items()}
    return {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "state": str(state.get("state") or "IDLE"),
        "last_active_browser_interaction_at_utc": state.get("last_active_browser_interaction_at_utc"),
        "last_reason": _safe_telemetry_label(state.get("reason")),
        "last_destination": _safe_telemetry_label(state.get("destination")),
        **counts,
    }
