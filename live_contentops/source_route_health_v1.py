"""Routing-only source/route health shared across bounded evidence acquisition.

This module owns no evidence, factual, numeric, permission, editorial, or publication authority.
It records sanitized transport outcomes so the canonical retrievers can avoid repeating a recently
failed exact route while continuing safe same-publisher recovery and unrelated routes.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = "contentops.source_route_health.v1"
DEFAULT_FAILURE_TTL_SECONDS = 6 * 60 * 60
SUPPRESSIBLE_FAILURE_CLASSES = frozenset(
    {"HTTP_401", "HTTP_403", "HTTP_404", "ACCESS_OR_WAF", "PAYWALL", "DEAD_LINK"}
)


def load_source_route_health_snapshot_read_only(
    path: str | Path,
) -> dict[str, Any]:
    """Read the existing routing-only projection without creating or repairing state."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    if (
        not isinstance(value, Mapping)
        or value.get("schema_version") != SCHEMA_VERSION
        or value.get("routing_only") is not True
        or value.get("exact_route_suppression_host_wide") is not False
        or value.get("sourceability_or_health_grants_factual_authority") is not False
        or value.get("sourceability_or_health_grants_numeric_authority") is not False
        or value.get("sourceability_or_health_grants_permission_authority") is not False
        or value.get("sourceability_or_health_grants_publication_authority") is not False
    ):
        return {}
    return dict(value)


def persist_source_route_health_snapshot(
    path: str | Path, snapshot: Mapping[str, Any]
) -> Path:
    """Atomically persist only a valid routing-only health projection."""
    value = dict(snapshot or {})
    if not load_source_route_health_snapshot_read_only_value(value):
        raise ValueError("source_route_health_snapshot_invalid")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, target)
    return target


def load_source_route_health_snapshot_read_only_value(
    value: Mapping[str, Any]
) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("schema_version") == SCHEMA_VERSION
        and value.get("routing_only") is True
        and value.get("exact_route_suppression_host_wide") is False
        and value.get("sourceability_or_health_grants_factual_authority") is False
        and value.get("sourceability_or_health_grants_numeric_authority") is False
        and value.get("sourceability_or_health_grants_permission_authority") is False
        and value.get("sourceability_or_health_grants_publication_authority") is False
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalized_host(host: str) -> str:
    return str(host or "").casefold().removeprefix("www.")


def normalized_route_identity(url: str) -> tuple[str, str]:
    parsed = urlsplit(str(url))
    host = normalized_host(str(parsed.hostname or ""))
    if parsed.scheme != "https" or not host:
        raise ValueError("source_route_health_url_invalid")
    path = parsed.path or "/"
    normalized_url = urlunsplit(("https", host, path, parsed.query, ""))
    return host, sha256(normalized_url.encode("utf-8")).hexdigest()


def classify_route_failure(value: BaseException | str | int) -> str:
    if isinstance(value, int):
        return f"HTTP_{value}" if value in {401, 403, 404} else "HTTP_OTHER"
    text = str(value).casefold()
    if "401" in text:
        return "HTTP_401"
    if "403" in text:
        return "HTTP_403"
    if "404" in text:
        return "HTTP_404"
    if "paywall" in text:
        return "PAYWALL"
    if "dead_link" in text or "not found" in text:
        return "DEAD_LINK"
    if any(marker in text for marker in ("access", "waf", "captcha", "forbidden")):
        return "ACCESS_OR_WAF"
    return "OTHER_TRANSPORT_FAILURE"


class SourceRouteHealthState:
    """In-memory projection whose snapshot is persisted by the existing cycle/supervisor state."""

    def __init__(
        self,
        initial: Mapping[str, Any] | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
        failure_ttl_seconds: int = DEFAULT_FAILURE_TTL_SECONDS,
    ) -> None:
        self._clock = clock or _utc_now
        self._failure_ttl_seconds = int(failure_ttl_seconds)
        self._routes: dict[str, dict[str, Any]] = {}
        self._hosts: dict[str, dict[str, Any]] = {}
        initial = initial if isinstance(initial, Mapping) else {}
        if initial.get("schema_version") == SCHEMA_VERSION:
            for row in initial.get("routes") or []:
                if isinstance(row, Mapping) and str(row.get("route_identity_sha256") or ""):
                    self._routes[str(row["route_identity_sha256"])] = dict(row)
            for row in initial.get("hosts") or []:
                if isinstance(row, Mapping) and str(row.get("normalized_host") or ""):
                    self._hosts[str(row["normalized_host"])] = dict(row)

    def should_suppress(self, url: str) -> dict[str, Any] | None:
        host, identity = normalized_route_identity(url)
        row = self._routes.get(identity)
        if not row or row.get("normalized_host") != host:
            return None
        if str(row.get("last_failure_class") or "") not in SUPPRESSIBLE_FAILURE_CLASSES:
            return None
        try:
            observed = datetime.fromisoformat(
                str(row.get("last_observed_at_utc") or "").replace("Z", "+00:00")
            )
        except ValueError:
            return None
        expires = observed + timedelta(seconds=self._failure_ttl_seconds)
        if self._clock() >= expires:
            return None
        return {
            "normalized_host": host,
            "route_identity_sha256": identity,
            "failure_class": row.get("last_failure_class"),
            "observed_at_utc": row.get("last_observed_at_utc"),
            "expires_at_utc": _iso(expires),
            "routing_only": True,
            "authority_granted": False,
        }

    def observe_success(self, url: str) -> None:
        self._observe(url, success=True, failure_class=None)

    def observe_failure(self, url: str, failure: BaseException | str | int) -> None:
        self._observe(url, success=False, failure_class=classify_route_failure(failure))

    def _observe(self, url: str, *, success: bool, failure_class: str | None) -> None:
        host, identity = normalized_route_identity(url)
        observed = _iso(self._clock())
        route = self._routes.setdefault(
            identity,
            {
                "normalized_host": host,
                "route_identity_sha256": identity,
                "success_count": 0,
                "failure_count": 0,
            },
        )
        host_row = self._hosts.setdefault(
            host,
            {
                "normalized_host": host,
                "success_count": 0,
                "failure_count": 0,
            },
        )
        key = "success_count" if success else "failure_count"
        route[key] = int(route.get(key) or 0) + 1
        host_row[key] = int(host_row.get(key) or 0) + 1
        route["last_observed_at_utc"] = observed
        host_row["last_observed_at_utc"] = observed
        if success:
            route["last_failure_class"] = None
            route["last_success_at_utc"] = observed
            host_row["last_success_at_utc"] = observed
        else:
            route["last_failure_class"] = failure_class
            host_row["last_failure_class"] = failure_class

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "failure_ttl_seconds": self._failure_ttl_seconds,
            "hosts": sorted(self._hosts.values(), key=lambda row: row["normalized_host"]),
            "routes": sorted(
                self._routes.values(), key=lambda row: row["route_identity_sha256"]
            ),
            "routing_only": True,
            "exact_route_suppression_host_wide": False,
            "safe_same_publisher_recovery_available": True,
            "autonomous_source_discovery_available": None,
            "sourceability_or_health_grants_factual_authority": False,
            "sourceability_or_health_grants_numeric_authority": False,
            "sourceability_or_health_grants_permission_authority": False,
            "sourceability_or_health_grants_publication_authority": False,
        }
