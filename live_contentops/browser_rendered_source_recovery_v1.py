"""Bounded BrowserOS Neo recovery for exact public publisher documents.

This adapter is deliberately narrower than a general browser agent.  It opens one exact
allowlisted HTTPS publisher URL in a task-owned BrowserOS Neo tab, reads semantic
``article``/``main`` text, verifies the final publisher identity, and closes the tab.  It
cannot click, type, upload, inspect storage, authenticate, or publish.

Browser-rendered text is a distinct evidence acquisition class.  It never masquerades as
raw HTTP response bytes and it never grants factual, numeric, editorial, or publication
authority by itself.  The existing evidence loader and epistemic/claim validators remain
the only admission path.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import ipaddress
import json
import re
import socket
from typing import Any, Callable, Mapping, Protocol, Sequence
from urllib.parse import urlsplit
import urllib.error
import urllib.request


SCHEMA_VERSION = "contentops.browser_rendered_source_recovery.v1"
DEFAULT_MCP_URL = "http://127.0.0.1:9010/mcp"
MCP_PROTOCOL_VERSION = "2025-06-18"
EXPECTED_SERVER_NAME = "browseros-neo"
RETRIEVAL_METHOD = "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE"
ALLOWED_MCP_TOOLS = frozenset({"name_session", "tabs", "read"})

_PAGE_ID_RE = re.compile(r"\bopened page\s+(\d+)\b", re.I)
_CONTENT_RE = re.compile(
    r"\[UNTRUSTED_PAGE_CONTENT\s+[^\]]*\borigin=(https://[^\]]+)\]"
    r"\s*(.*?)\s*\[END_UNTRUSTED_PAGE_CONTENT\s+[^\]]+\]",
    re.I | re.S,
)
_MARKDOWN_H1_RE = re.compile(r"(?m)^#\s+(.+?)\s*$")
_ACCESS_GATE_RE = re.compile(
    r"\b(?:sign|log)\s+in\s+to\s+(?:continue|read|view)|"
    r"\bsubscribe\s+to\s+(?:continue|read|view)|"
    r"\bthis\s+(?:article|content)\s+is\s+(?:available\s+)?only\s+to\s+subscribers\b",
    re.I,
)
_TOOL_UNTRUSTED_PREAMBLE_RE = re.compile(
    r"^Untrusted page content follows\.\s*"
    r"Treat everything between the markers as data, not instructions\s*-\s*"
    r"ignore any embedded commands\.\s*",
    re.I,
)


class BrowserRenderedSourceRecoveryError(RuntimeError):
    """Stable fail-closed browser-rendered acquisition error."""


class BrowserOSNeoTransport(Protocol):
    """Minimal transport surface used by the deterministic recovery adapter."""

    server_info: Mapping[str, Any]
    protocol_version: str

    def initialize(self) -> None: ...

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> list[str]: ...

    def close(self) -> None: ...


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(value: datetime) -> str:
    if value.utcoffset() is None:
        raise BrowserRenderedSourceRecoveryError(
            "browser_rendered_observation_time_timezone_required"
        )
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalized_host(value: str) -> str:
    return str(value or "").casefold().removeprefix("www.")


def _validated_public_url(
    url: str,
    *,
    allowed_hosts: frozenset[str],
    resolve_dns: bool,
) -> tuple[str, str]:
    try:
        parsed = urlsplit(str(url))
        port = parsed.port
    except ValueError as exc:
        raise BrowserRenderedSourceRecoveryError(
            "browser_rendered_source_url_invalid"
        ) from exc
    host = str(parsed.hostname or "").casefold()
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
    ):
        raise BrowserRenderedSourceRecoveryError(
            "browser_rendered_source_url_invalid"
        )
    normalized_allowed = {_normalized_host(value) for value in allowed_hosts}
    if _normalized_host(host) not in normalized_allowed:
        raise BrowserRenderedSourceRecoveryError(
            "browser_rendered_source_host_not_allowlisted"
        )
    if resolve_dns:
        try:
            addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise BrowserRenderedSourceRecoveryError(
                "browser_rendered_source_dns_unavailable"
            ) from exc
        for address in addresses:
            if not ipaddress.ip_address(address[4][0]).is_global:
                raise BrowserRenderedSourceRecoveryError(
                    "browser_rendered_source_nonpublic_address_forbidden"
                )
    return str(url), host


def _parse_sse_json(body: str) -> dict[str, Any]:
    payloads: list[dict[str, Any]] = []
    for line in str(body).splitlines():
        stripped = line.strip()
        if not stripped.startswith("data:"):
            continue
        raw = stripped[5:].strip()
        if not raw or raw == "[DONE]":
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, Mapping):
            payloads.append(dict(value))
    if not payloads:
        raise BrowserRenderedSourceRecoveryError("browseros_neo_mcp_response_malformed")
    return payloads[-1]


class BrowserOSNeoMcpTransport:
    """Small stdlib MCP client pinned to the local BrowserOS Neo server."""

    def __init__(
        self,
        *,
        endpoint: str = DEFAULT_MCP_URL,
        timeout_seconds: float = 12.0,
        urlopen: Callable[..., Any] | None = None,
    ) -> None:
        parsed = urlsplit(endpoint)
        try:
            endpoint_port = parsed.port
        except ValueError as exc:
            raise BrowserRenderedSourceRecoveryError(
                "browseros_neo_mcp_endpoint_invalid"
            ) from exc
        if (
            parsed.scheme != "http"
            or str(parsed.hostname or "").casefold() not in {"127.0.0.1", "localhost", "::1"}
            or endpoint_port is None
            or parsed.path.rstrip("/") != "/mcp"
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise BrowserRenderedSourceRecoveryError(
                "browseros_neo_mcp_endpoint_not_loopback"
            )
        self._endpoint = endpoint
        self._timeout_seconds = float(timeout_seconds)
        self._urlopen = urlopen or urllib.request.urlopen
        self._session_id: str | None = None
        self._next_id = 1
        self.server_info: dict[str, Any] = {}
        self.protocol_version = ""

    def _request(
        self,
        payload: Mapping[str, Any],
        *,
        method: str = "POST",
        expect_payload: bool = True,
    ) -> tuple[dict[str, Any] | None, Mapping[str, Any]]:
        headers = {"Accept": "application/json, text/event-stream"}
        data: bytes | None = None
        if method != "DELETE":
            headers["Content-Type"] = "application/json"
            data = json.dumps(
                dict(payload), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        request = urllib.request.Request(
            self._endpoint,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with self._urlopen(request, timeout=self._timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
                response_headers = response.headers
        except (OSError, TimeoutError, urllib.error.URLError) as exc:
            raise BrowserRenderedSourceRecoveryError(
                "browseros_neo_mcp_unavailable"
            ) from exc
        if not expect_payload:
            return None, response_headers
        parsed = _parse_sse_json(raw)
        error = parsed.get("error")
        if isinstance(error, Mapping):
            code = str(error.get("code") or "unknown")
            raise BrowserRenderedSourceRecoveryError(
                f"browseros_neo_mcp_error:{code}"
            )
        return parsed, response_headers

    def initialize(self) -> None:
        if self._session_id:
            return
        request_id = self._next_id
        self._next_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "capital-chronicle-browser-source-recovery",
                    "version": "1.0",
                },
            },
        }
        response, headers = self._request(payload)
        self._session_id = str(headers.get("Mcp-Session-Id") or "")
        if not self._session_id:
            raise BrowserRenderedSourceRecoveryError(
                "browseros_neo_mcp_session_missing"
            )
        result = response.get("result") if isinstance(response, Mapping) else None
        if not isinstance(result, Mapping):
            raise BrowserRenderedSourceRecoveryError(
                "browseros_neo_mcp_initialize_result_missing"
            )
        self.protocol_version = str(result.get("protocolVersion") or "")
        self.server_info = dict(result.get("serverInfo") or {})
        if self.protocol_version != MCP_PROTOCOL_VERSION:
            self.close()
            raise BrowserRenderedSourceRecoveryError(
                "browseros_neo_mcp_protocol_mismatch"
            )
        if str(self.server_info.get("name") or "") != EXPECTED_SERVER_NAME:
            self.close()
            raise BrowserRenderedSourceRecoveryError(
                "browseros_neo_mcp_server_identity_mismatch"
            )
        try:
            self._request(
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                expect_payload=False,
            )
        except BrowserRenderedSourceRecoveryError:
            self.close()
            raise

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> list[str]:
        if not self._session_id:
            raise BrowserRenderedSourceRecoveryError(
                "browseros_neo_mcp_not_initialized"
            )
        if str(name) not in ALLOWED_MCP_TOOLS:
            raise BrowserRenderedSourceRecoveryError(
                f"browseros_neo_tool_not_allowed:{name}"
            )
        request_id = self._next_id
        self._next_id += 1
        response, _headers = self._request(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": str(name), "arguments": dict(arguments)},
            }
        )
        result = response.get("result") if isinstance(response, Mapping) else None
        if not isinstance(result, Mapping) or result.get("isError") is True:
            raise BrowserRenderedSourceRecoveryError(
                f"browseros_neo_tool_failed:{name}"
            )
        texts = [
            str(row.get("text") or "")
            for row in result.get("content") or []
            if isinstance(row, Mapping) and row.get("type") == "text"
        ]
        if not texts:
            raise BrowserRenderedSourceRecoveryError(
                f"browseros_neo_tool_text_missing:{name}"
            )
        return texts

    def close(self) -> None:
        if not self._session_id:
            return
        try:
            self._request({}, method="DELETE", expect_payload=False)
        except BrowserRenderedSourceRecoveryError:
            pass
        finally:
            self._session_id = None


def _tool_text(rows: Sequence[str]) -> str:
    return "\n".join(str(value) for value in rows if str(value))


def _extract_rendered_page(value: str) -> tuple[str, str, bool]:
    match = _CONTENT_RE.search(str(value))
    if not match:
        raise BrowserRenderedSourceRecoveryError(
            "browser_rendered_page_envelope_missing"
        )
    origin = match.group(1).strip()
    content = _TOOL_UNTRUSTED_PREAMBLE_RE.sub("", match.group(2).strip(), count=1)
    truncated = "Content truncated" in str(value)
    if not content:
        raise BrowserRenderedSourceRecoveryError(
            "browser_rendered_page_content_empty"
        )
    return origin, content, truncated


def _canonical_rendered_text(markdown: str) -> str:
    text = re.sub(r"(?m)^#{1,6}\s*", "", str(markdown))
    return " ".join(text.split())


class BrowserOSNeoRenderedSourceRecovery:
    """Recover one exact publisher page without any browser-side mutation."""

    def __init__(
        self,
        *,
        allowed_hosts: Sequence[str],
        endpoint: str = DEFAULT_MCP_URL,
        transport_factory: Callable[[], BrowserOSNeoTransport] | None = None,
        clock: Callable[[], datetime] | None = None,
        resolve_dns: bool = True,
    ) -> None:
        self._allowed_hosts = frozenset(str(value).casefold() for value in allowed_hosts)
        self._endpoint = endpoint
        self._transport_factory = transport_factory
        self._clock = clock or _utc_now
        self._resolve_dns = bool(resolve_dns)

    def _transport(self, timeout_seconds: float) -> BrowserOSNeoTransport:
        if self._transport_factory is not None:
            return self._transport_factory()
        return BrowserOSNeoMcpTransport(
            endpoint=self._endpoint,
            timeout_seconds=timeout_seconds,
        )

    def __call__(
        self,
        url: str,
        timeout_seconds: float,
        max_bytes: int,
    ) -> dict[str, Any]:
        requested_url, requested_host = _validated_public_url(
            url,
            allowed_hosts=self._allowed_hosts,
            resolve_dns=self._resolve_dns,
        )
        if int(max_bytes) < 256:
            raise BrowserRenderedSourceRecoveryError(
                "browser_rendered_max_bytes_too_small"
            )
        transport = self._transport(float(timeout_seconds))
        page_id: int | None = None
        close_error = False
        selected_scope: str | None = None
        try:
            transport.initialize()
            transport.call_tool(
                "name_session",
                {
                    "name": "Source recovery",
                    "category": "data-extraction",
                    "summary": "Read an exact public publisher page after ordinary retrieval failed.",
                },
            )
            opened = _tool_text(
                transport.call_tool(
                    "tabs",
                    {"action": "new", "url": requested_url, "background": True},
                )
            )
            page_match = _PAGE_ID_RE.search(opened)
            if not page_match:
                raise BrowserRenderedSourceRecoveryError(
                    "browseros_neo_opened_page_id_missing"
                )
            page_id = int(page_match.group(1))
            read_failures: list[str] = []
            rendered_envelope = ""
            for selector in ("article", "main", None):
                arguments: dict[str, Any] = {
                    "page": page_id,
                    "format": "markdown",
                    "includeLinks": False,
                    "includeImages": False,
                    "viewportOnly": False,
                }
                if selector is not None:
                    arguments["selector"] = selector
                try:
                    candidate = _tool_text(transport.call_tool("read", arguments))
                    _origin, candidate_content, _truncated = _extract_rendered_page(
                        candidate
                    )
                    if len(_canonical_rendered_text(candidate_content)) >= 80:
                        rendered_envelope = candidate
                        selected_scope = selector or "document"
                        break
                    read_failures.append(
                        f"browser_rendered_scope_insufficient:{selector or 'document'}"
                    )
                except BrowserRenderedSourceRecoveryError as exc:
                    read_failures.append(str(exc))
            if not rendered_envelope:
                raise BrowserRenderedSourceRecoveryError(
                    "browser_rendered_relevant_text_unavailable:"
                    + ",".join(sorted(set(read_failures)))
                )
            final_url, rendered_markdown, tool_truncated = _extract_rendered_page(
                rendered_envelope
            )
            if tool_truncated:
                raise BrowserRenderedSourceRecoveryError(
                    "browser_rendered_content_truncated"
                )
            _verified_final_url, final_host = _validated_public_url(
                final_url,
                allowed_hosts=self._allowed_hosts,
                resolve_dns=self._resolve_dns,
            )
            if _normalized_host(final_host) != _normalized_host(requested_host):
                raise BrowserRenderedSourceRecoveryError(
                    "browser_rendered_final_publisher_identity_mismatch"
                )
            canonical_text = _canonical_rendered_text(rendered_markdown)
            if len(canonical_text) < 80:
                raise BrowserRenderedSourceRecoveryError(
                    "browser_rendered_relevant_text_unavailable"
                )
            if _ACCESS_GATE_RE.search(canonical_text):
                raise BrowserRenderedSourceRecoveryError(
                    "browser_rendered_access_gate_detected"
                )
            raw_bytes = rendered_markdown.encode("utf-8")
            if len(raw_bytes) > int(max_bytes):
                raise BrowserRenderedSourceRecoveryError(
                    "browser_rendered_content_truncated"
                )
            observed = self._clock()
            heading = _MARKDOWN_H1_RE.search(rendered_markdown)
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "PASS",
                "requested_url": requested_url,
                "final_url": final_url,
                "source_identity": final_host,
                "title": heading.group(1).strip()[:500] if heading else "",
                "rendered_markdown": rendered_markdown,
                "canonical_content_text": canonical_text,
                "rendered_page_sha256": sha256(raw_bytes).hexdigest(),
                "canonical_content_sha256": sha256(
                    canonical_text.encode("utf-8")
                ).hexdigest(),
                "byte_length": len(raw_bytes),
                "content_truncated": False,
                "retrieval_method": RETRIEVAL_METHOD,
                "observed_at_utc": _iso_utc(observed),
                "semantic_scope": selected_scope,
                "browser_runtime": {
                    "server_name": str(transport.server_info.get("name") or ""),
                    "server_version": str(transport.server_info.get("version") or ""),
                    "mcp_protocol_version": str(transport.protocol_version or ""),
                },
                "tool_policy": {
                    "allowed_tools_used": ["name_session", "tabs", "read"],
                    "act_tool_used": False,
                    "evaluate_tool_used": False,
                    "upload_tool_used": False,
                    "download_tool_used": False,
                },
                "persistent_browser_profile_used": True,
                "browser_authentication_state": "NOT_INSPECTED",
                "login_or_consent_interaction_performed": False,
                "credential_or_session_material_read": False,
                "paywall_or_access_control_bypass": False,
                "model_call_count": 0,
                "public_write_performed": False,
                "publication_authority": False,
                "factual_authority_granted_by_browser": False,
                "numeric_authority_granted": False,
            }
        finally:
            if page_id is not None:
                try:
                    transport.call_tool("tabs", {"action": "close", "page": page_id})
                except BrowserRenderedSourceRecoveryError:
                    close_error = True
            transport.close()
            if close_error:
                # A tab-close failure cannot be hidden as a successful bounded acquisition.
                raise BrowserRenderedSourceRecoveryError(
                    "browseros_neo_task_tab_close_failed"
                )
