"""9router provider adapter for the canonical ordered model router.

This is the thin, auditable boundary between the router's policy and the real gateway. It
does exactly three things: build the request, observe the response, and report what it saw
as a :class:`ProviderResult`. It makes no retry, fallback, or acceptance decision — those
belong to :mod:`live_contentops.nine_router_ordered_model_router_v2` alone.

Two safety properties matter here.

**Credentials are used, never surfaced.** The key is read from the environment through the
existing runtime binding, sent in the Authorization header, and never returned, logged,
hashed into an ID, or stored. Only presence is ever reported, via
:func:`credential_presence`.

**The base URL is constrained.** The gateway host must be loopback or an explicitly
allowed 9router host. There was previously no allowlist covering AI providers, so an
untrusted ``NINE_ROUTER_BASE_URL`` could have redirected model traffic anywhere; this
module closes that gap and fails closed.
"""
from __future__ import annotations

import importlib
import json
import os
import time
from typing import Any, Mapping
from urllib.parse import urlparse

from live_contentops.credential_redaction_policy import redacted_presence
from live_contentops.nine_router_ordered_model_router_v2 import (
    AUTHORIZED_MODELS,
    GATEWAY,
    ProviderResult,
    classify_failure,
)

SCHEMA_VERSION = "contentops.nine_router_provider_adapter.v2"

ENV_API_KEY = "NINE_ROUTER_API_KEY"
ENV_BASE_URL = "NINE_ROUTER_BASE_URL"
DEFAULT_BASE_URL = "http://localhost:20128/v1"

#: Hosts the 9router gateway may live on. Loopback covers the local gateway; the named
#: hosts cover a managed deployment. Anything else fails closed rather than sending
#: credentialed model traffic to an unvetted endpoint.
ALLOWED_GATEWAY_HOSTS: frozenset[str] = frozenset(
    {"localhost", "127.0.0.1", "::1", "9router.local", "api.9router.ai", "9router"}
)


class NineRouterAdapterError(RuntimeError):
    """Fail-closed 9router adapter error. Never carries credential material."""


def credential_presence() -> dict[str, str]:
    """Presence-only credential report. Never returns or hints at a value."""
    env = getattr(os, "environ")
    return {
        ENV_API_KEY: redacted_presence(bool(env.get(ENV_API_KEY)), ENV_API_KEY),
        ENV_BASE_URL: redacted_presence(bool(env.get(ENV_BASE_URL)), ENV_BASE_URL),
    }


def resolve_base_url(raw: str | None = None) -> str:
    """Resolve and allowlist-check the gateway base URL."""
    env = getattr(os, "environ")
    base_url = (raw or env.get(ENV_BASE_URL) or DEFAULT_BASE_URL).rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https"):
        raise NineRouterAdapterError(f"gateway_scheme_not_allowed:{parsed.scheme}")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_GATEWAY_HOSTS:
        raise NineRouterAdapterError(f"gateway_host_not_in_allowlist:{host}")
    return base_url


def _extract_usage(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    usage = payload.get("usage")
    if not isinstance(usage, Mapping):
        return None
    keep = ("prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens")
    out = {k: usage[k] for k in keep if isinstance(usage.get(k), (int, float))}
    return out or None


def _extract_cost(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    for key in ("cost", "total_cost", "cost_usd"):
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return {"usd": float(value)}
        if isinstance(value, Mapping):
            out = {k: float(v) for k, v in value.items() if isinstance(v, (int, float))}
            if out:
                return out
    usage = payload.get("usage")
    if isinstance(usage, Mapping) and isinstance(usage.get("cost"), (int, float)):
        return {"usd": float(usage["cost"])}
    return None


def _extract_text(payload: Mapping[str, Any]) -> str | None:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], Mapping) else None
        if isinstance(message, Mapping) and isinstance(message.get("content"), str):
            return message["content"]
        if isinstance(choices[0], Mapping) and isinstance(choices[0].get("text"), str):
            return choices[0]["text"]
    return None


def _parse_sse(text: str) -> str | None:
    """Accumulate an SSE delta stream, matching the accepted gateway behaviour."""
    tokens: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload_text = line[5:].strip()
        if payload_text == "[DONE]":
            continue
        try:
            chunk = json.loads(payload_text)
        except json.JSONDecodeError:
            continue
        choices = chunk.get("choices") or []
        if not choices:
            continue
        delta = choices[0].get("delta") or {}
        content = delta.get("content") or (choices[0].get("message") or {}).get("content")
        if content:
            tokens.append(str(content))
    return "".join(tokens) if tokens else None


def _load_json_body(raw: str) -> Mapping[str, Any] | None:
    """Parse a JSON completion body, tolerating the gateway's trailing SSE sentinel."""
    for candidate in (raw, raw.split("data:")[0]):
        text = candidate.strip()
        if not text:
            continue
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(loaded, Mapping):
            return loaded
    return None


def normalize_model_identity(value: str | None) -> str | None:
    """Strip the gateway's routing prefix from a reported effective model.

    9router accepts ``new/claude-fable-5`` and reports back ``claude-fable-5``. That is a
    naming convention, not a substitution, so comparing the two raw strings would raise a
    false identity mismatch on every healthy call. Normalising both sides keeps the real
    invariant — did we get the model we asked for — while still catching a genuine swap.
    """
    if value is None:
        return None
    text = str(value).strip()
    return text.split("/", 1)[1] if "/" in text else text


def _observed_model(payload: Mapping[str, Any]) -> str | None:
    """The gateway-reported effective model, or None when it does not expose one.

    Returning ``None`` is deliberate and honest: the router downgrades to
    ``MODEL_IDENTITY_NOT_PROVIDER_VERIFIABLE`` rather than assuming the request was honoured.
    """
    for key in ("model", "resolved_model", "effective_model"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def call_nine_router(
    prompt: str,
    model: str,
    timeout_seconds: float = 60.0,
    *,
    max_tokens: int = 16000,
    temperature: float = 0.2,
    base_url: str | None = None,
) -> ProviderResult:
    """Perform one bounded 9router chat completion and report what was observed.

    Never raises for provider-side failure: every failure is classified and returned as a
    :class:`ProviderResult` so the router owns the decision. Only configuration problems
    (missing credential, disallowed host, unauthorized model) raise.
    """
    if model not in AUTHORIZED_MODELS:
        raise NineRouterAdapterError(f"unauthorized_model:{model}")

    env = getattr(os, "environ")
    api_key = env.get(ENV_API_KEY)
    if not api_key:
        raise NineRouterAdapterError(f"{ENV_API_KEY}_missing")
    resolved_base = resolve_base_url(base_url)

    url_request = importlib.import_module("urllib.request")
    url_error = importlib.import_module("urllib.error")
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
    ).encode("utf-8")
    request = url_request.Request(
        f"{resolved_base}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            # Used, never returned or logged.
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    started = time.monotonic()
    try:
        with url_request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            status = int(getattr(response, "status", 200) or 200)
    except url_error.HTTPError as exc:  # noqa: PERF203 - distinct handling per class
        retry_after = _retry_after_from_headers(getattr(exc, "headers", None))
        code = int(getattr(exc, "code", 0) or 0)
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:2000]
        except Exception:  # pragma: no cover - body already consumed
            detail = ""
        return ProviderResult(
            status_code=code,
            retry_after_seconds=retry_after,
            failure_class=_classify_http_error(code, detail),
        )
    except url_error.URLError as exc:
        return ProviderResult(failure_class=classify_failure(getattr(exc, "reason", exc)))
    except (TimeoutError, OSError) as exc:
        return ProviderResult(failure_class=classify_failure(exc))

    del started  # latency is measured by the router around this call

    # The gateway appends a ``data: [DONE]`` trailer to an otherwise plain JSON body, so a
    # bare "data:" test would misroute a real completion into the SSE parser. Try strict
    # JSON first, then JSON with the trailer stripped, and only then treat it as a stream.
    payload: Mapping[str, Any] = {}
    text: str | None = None
    parsed = _load_json_body(raw)
    if parsed is not None:
        payload = parsed
        text = _extract_text(payload)
    elif "data:" in raw:
        text = _parse_sse(raw)
    if text is None and not payload:
        return ProviderResult(
            status_code=status, failure_class="structured_output_malformed", text=raw[:2000]
        )

    if not text:
        return ProviderResult(
            status_code=status,
            resolved_model=_observed_model(payload),
            failure_class="structured_output_malformed",
        )

    return ProviderResult(
        text=text,
        resolved_model=_observed_model(payload),
        provider_invocation_id=str(payload.get("id")) if payload.get("id") else None,
        status_code=status,
        usage=_extract_usage(payload),
        cost=_extract_cost(payload),
    )


#: Gateway error markers that scope a 403/404 to *one model* rather than the credential.
#: A gateway that does not carry a given model must be failed over, not treated as an auth
#: failure — otherwise one missing model hard-blocks the whole newsroom.
_MODEL_SCOPED_ERROR_MARKERS: tuple[str, ...] = (
    "invalid_model",
    "model_not_found",
    "unknown_model",
    "model_not_available",
    "does not have access to model",
    "no such model",
)


def _classify_http_error(status_code: int, body: str) -> str:
    """Classify an HTTP error, separating credential failure from model unavailability.

    401 is always a credential failure and always terminal. A 403/404 is terminal *unless*
    the gateway body explicitly scopes the refusal to one model, which is a
    model-availability condition and is fallback-eligible. Anything ambiguous stays
    terminal: the fail-closed default must not be weakened to buy a retry.
    """
    lowered = (body or "").lower()
    if status_code in (403, 404) and any(
        marker in lowered for marker in _MODEL_SCOPED_ERROR_MARKERS
    ):
        return "requested_model_temporarily_unavailable"
    return classify_failure(status_code=status_code)


def _retry_after_from_headers(headers: Any) -> float | None:
    if headers is None:
        return None
    try:
        value = headers.get("Retry-After")
    except AttributeError:
        return None
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None
