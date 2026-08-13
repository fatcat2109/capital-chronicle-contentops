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
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from live_contentops.credential_redaction_policy import redacted_presence
from live_contentops.nine_router_ordered_model_router_v2 import (
    AUTHORIZED_MODELS,
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

MINIMAL_RAW_REQUEST_FIELDS: frozenset[str] = frozenset({"model", "messages"})
OPTIONAL_GENERATION_FIELDS: frozenset[str] = frozenset(
    {
        "max_tokens",
        "temperature",
        "reasoning_effort",
        "response_format",
        "tools",
        "tool_choice",
        "top_p",
        "seed",
        "stop",
        "frequency_penalty",
        "presence_penalty",
    }
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
    """Accumulate an SSE delta stream's text content, matching the accepted gateway shape.

    Retained for callers that only need the text. :func:`_parse_sse_full` is the version
    used by :func:`call_nine_router`, since a true multi-chunk stream (as returned for some
    models) carries the resolved model and usage on later chunks, not the first.
    """
    parsed = _parse_sse_full(text)
    return parsed["text"] if parsed is not None else None


def _parse_sse_full(text: str) -> "dict[str, Any] | None":
    """Accumulate a full SSE stream: text content plus the last-seen model/usage/id.

    A true multi-chunk stream reports the resolved model on every chunk but usage only on
    the final chunk (where ``finish_reason`` is set). Scanning every chunk — not just the
    first — is required to observe usage and to be robust if a future gateway response
    varies which chunk carries which field.
    """
    tokens: list[str] = []
    observed_model: str | None = None
    observed_usage: Mapping[str, Any] | None = None
    observed_id: str | None = None
    saw_any_chunk = False
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
        saw_any_chunk = True
        if isinstance(chunk.get("model"), str):
            observed_model = chunk["model"]
        if isinstance(chunk.get("id"), str):
            observed_id = observed_id or chunk["id"]
        usage = chunk.get("usage")
        if isinstance(usage, Mapping):
            observed_usage = usage
        choices = chunk.get("choices") or []
        if not choices:
            continue
        delta = choices[0].get("delta") or {}
        content = delta.get("content") or (choices[0].get("message") or {}).get("content")
        if content:
            tokens.append(str(content))
    if not saw_any_chunk:
        return None
    return {
        "text": "".join(tokens) if tokens else None,
        "model": observed_model,
        "usage": observed_usage,
        "id": observed_id,
    }


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
    """Strip the gateway's routing prefix and any ``(effort)`` suffix from a model ID.

    9router accepts ``new/claude-fable-5`` and reports back ``claude-fable-5``. That is a
    naming convention, not a substitution, so comparing the two raw strings would raise a
    false identity mismatch on every healthy call. Normalising both sides keeps the real
    invariant — did we get the model we asked for — while still catching a genuine swap.

    A pool entry may also carry a trailing ``(high)``-style reasoning-effort selector (see
    :func:`split_model_and_effort`). That selector is not part of the model's identity, so it
    is stripped here too.
    """
    if value is None:
        return None
    text = str(value).strip()
    bare = text.split("/", 1)[1] if "/" in text else text
    if bare.endswith(")") and "(" in bare:
        bare = bare[: bare.rindex("(")]
    return bare


def split_model_and_effort(model: str) -> "tuple[str, str | None]":
    """Split an opaque pool entry into the wire model ID and an optional effort selector.

    ``vx/gemini-3.1-pro-preview(high)`` is one opaque authorized string in the router's
    pool, but the gateway does not accept the ``(high)`` suffix as part of the Vertex model
    path — it builds the upstream endpoint by appending the model string directly, so a
    trailing ``(high)`` produces ``Invalid Endpoint name`` (HTTP 400) rather than routing to
    a high-effort variant. The gateway does accept effort as a separate ``reasoning_effort``
    request field. This function performs the split at the wire boundary only; the router
    and evidence trail continue to treat the full string (with suffix) as the one exact
    authorized pool entry.
    """
    text = str(model).strip()
    if text.endswith(")") and "(" in text:
        idx = text.rindex("(")
        return text[:idx], text[idx + 1 : -1] or None
    return text, None


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


def _call_nine_router_impl(
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
    wire_model, effort = split_model_and_effort(model)
    request_payload: dict[str, Any] = {
        "model": wire_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if effort:
        request_payload["reasoning_effort"] = effort
    body = json.dumps(request_payload).encode("utf-8")
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
    sse: "dict[str, Any] | None" = None
    parsed = _load_json_body(raw)
    if parsed is not None:
        payload = parsed
        text = _extract_text(payload)
    elif "data:" in raw:
        sse = _parse_sse_full(raw)
        text = sse["text"] if sse is not None else None
    if text is None and sse is None and not payload:
        return ProviderResult(
            status_code=status, failure_class="structured_output_malformed", text=raw[:2000]
        )

    resolved_model = sse["model"] if sse is not None else _observed_model(payload)
    invocation_id = (sse or {}).get("id") or (
        str(payload.get("id")) if payload.get("id") else None
    )
    usage = (sse or {}).get("usage") if sse is not None else _extract_usage(payload)
    if isinstance(usage, Mapping) and not isinstance(usage, dict):
        usage = dict(usage)

    if not text:
        return ProviderResult(
            status_code=status,
            resolved_model=resolved_model,
            failure_class="structured_output_malformed",
        )

    return ProviderResult(
        text=text,
        resolved_model=resolved_model,
        provider_invocation_id=invocation_id,
        status_code=status,
        usage=usage or _extract_usage(payload),
        cost=_extract_cost(payload),
    )


def _prompt_bytes(prompt: Any) -> bytes:
    if isinstance(prompt, str):
        return prompt.encode("utf-8")
    return json.dumps(
        prompt, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _write_minimal_raw_receipt(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _call_nine_router_minimal_raw_impl(
    prompt: Any,
    model: str,
    timeout_seconds: float,
    *,
    evidence_dir: Path,
    isolated_execution_domain_id: str,
    base_url: str | None = None,
) -> ProviderResult:
    """Send exactly ``model`` + ``messages`` and preserve response bytes before parsing.

    This is the controlled V2 XHIGH experiment boundary. It deliberately does not share
    the configured request builder above, so optional generation fields cannot leak onto
    this wire request through defaults or a future refactor.
    """
    if model not in AUTHORIZED_MODELS:
        raise NineRouterAdapterError(f"unauthorized_model:{model}")
    wire_model, effort = split_model_and_effort(model)
    if effort is not None:
        raise NineRouterAdapterError("minimal_raw_model_requires_optional_effort_field")

    evidence_dir = Path(evidence_dir).resolve()
    receipt_path = evidence_dir / "minimal_raw_provider_receipt_v1.json"
    if receipt_path.exists():
        raise NineRouterAdapterError("minimal_raw_experiment_receipt_already_exists")

    env = getattr(os, "environ")
    api_key = env.get(ENV_API_KEY)
    if not api_key:
        raise NineRouterAdapterError(f"{ENV_API_KEY}_missing")
    resolved_base = resolve_base_url(base_url)
    prompt_bytes = _prompt_bytes(prompt)
    request_payload: dict[str, Any] = {
        "model": wire_model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if set(request_payload) != MINIMAL_RAW_REQUEST_FIELDS:
        raise NineRouterAdapterError("minimal_raw_request_field_set_invalid")
    leaked = sorted(set(request_payload) & OPTIONAL_GENERATION_FIELDS)
    if leaked:
        raise NineRouterAdapterError(
            f"minimal_raw_optional_generation_fields_present:{','.join(leaked)}"
        )
    body = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")

    evidence_dir.mkdir(parents=True, exist_ok=True)
    request_metadata = {
        "schema_version": "contentops.nine_router.minimal_raw_request.v1",
        "isolated_execution_domain_id": isolated_execution_domain_id,
        "requested_model": model,
        "wire_model": wire_model,
        "request_body_field_names": sorted(request_payload),
        "optional_generation_fields_absent": True,
        "optional_generation_fields_checked": sorted(OPTIONAL_GENERATION_FIELDS),
        "messages_count": 1,
        "message_roles": ["user"],
        "prompt_sha256": sha256(prompt_bytes).hexdigest(),
        "prompt_character_size": len(prompt) if isinstance(prompt, str) else None,
        "prompt_byte_size": len(prompt_bytes),
        "request_body_sha256": sha256(body).hexdigest(),
        "request_body_byte_size": len(body),
        "transport_header_names": ["Authorization", "Content-Type"],
        "contains_credentials": False,
        "public_write": False,
    }
    _write_minimal_raw_receipt(evidence_dir / "request_metadata_v1.json", request_metadata)

    url_request = importlib.import_module("urllib.request")
    url_error = importlib.import_module("urllib.error")
    request = url_request.Request(
        f"{resolved_base}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    started = time.monotonic()
    raw_bytes: bytes | None = None
    status: int | None = None
    failure_class: str | None = None
    retry_after: float | None = None
    try:
        with url_request.urlopen(request, timeout=timeout_seconds) as response:
            raw_bytes = response.read()
            status = int(getattr(response, "status", 200) or 200)
    except url_error.HTTPError as exc:  # noqa: PERF203 - response evidence is required
        status = int(getattr(exc, "code", 0) or 0)
        retry_after = _retry_after_from_headers(getattr(exc, "headers", None))
        try:
            raw_bytes = exc.read()
        except Exception:  # pragma: no cover - body already consumed
            raw_bytes = b""
        failure_class = _classify_http_error(
            status, raw_bytes.decode("utf-8", errors="replace")[:2000]
        )
    except url_error.URLError as exc:
        failure_class = classify_failure(getattr(exc, "reason", exc))
    except (TimeoutError, OSError) as exc:
        failure_class = classify_failure(exc)
    latency_seconds = round(time.monotonic() - started, 4)

    # The untouched provider body is durable before any JSON/SSE parsing or repair occurs.
    raw_response_path: Path | None = None
    raw_response_sha256: str | None = None
    raw_response_byte_size = 0
    if raw_bytes is not None:
        raw_response_path = evidence_dir / "provider_response_body.bin"
        raw_response_path.write_bytes(raw_bytes)
        raw_response_sha256 = sha256(raw_bytes).hexdigest()
        raw_response_byte_size = len(raw_bytes)

    if failure_class is not None:
        receipt = request_metadata | {
            "schema_version": "contentops.nine_router.minimal_raw_provider_receipt.v1",
            "effective_model": None,
            "http_status": status,
            "failure_class": failure_class,
            "retry_after_seconds": retry_after,
            "latency_seconds": latency_seconds,
            "provider_invocation_id": None,
            "raw_response_path": str(raw_response_path) if raw_response_path else None,
            "raw_response_sha256": raw_response_sha256,
            "raw_response_byte_size": raw_response_byte_size,
            "raw_model_output_path": None,
            "raw_model_output_sha256": None,
            "raw_model_output_byte_size": 0,
            "usage": None,
            "cost": None,
        }
        _write_minimal_raw_receipt(receipt_path, receipt)
        return ProviderResult(
            status_code=status,
            retry_after_seconds=retry_after,
            failure_class=failure_class,
        )

    raw = (raw_bytes or b"").decode("utf-8", errors="replace")
    payload: Mapping[str, Any] = {}
    text: str | None = None
    sse: dict[str, Any] | None = None
    parsed = _load_json_body(raw)
    if parsed is not None:
        payload = parsed
        text = _extract_text(payload)
    elif "data:" in raw:
        sse = _parse_sse_full(raw)
        text = sse["text"] if sse is not None else None

    resolved_model = sse["model"] if sse is not None else _observed_model(payload)
    invocation_id = (sse or {}).get("id") or (
        str(payload.get("id")) if payload.get("id") else None
    )
    usage = (sse or {}).get("usage") if sse is not None else _extract_usage(payload)
    if isinstance(usage, Mapping) and not isinstance(usage, dict):
        usage = dict(usage)
    cost = _extract_cost(payload)
    output_path: Path | None = None
    output_sha256: str | None = None
    output_size = 0
    if text is not None:
        output_bytes = text.encode("utf-8")
        output_path = evidence_dir / "raw_model_output.txt"
        output_path.write_bytes(output_bytes)
        output_sha256 = sha256(output_bytes).hexdigest()
        output_size = len(output_bytes)

    parse_failure = None if text else "structured_output_malformed"
    receipt = request_metadata | {
        "schema_version": "contentops.nine_router.minimal_raw_provider_receipt.v1",
        "effective_model": resolved_model,
        "http_status": status,
        "failure_class": parse_failure,
        "retry_after_seconds": None,
        "latency_seconds": latency_seconds,
        "provider_invocation_id": invocation_id,
        "raw_response_path": str(raw_response_path) if raw_response_path else None,
        "raw_response_sha256": raw_response_sha256,
        "raw_response_byte_size": raw_response_byte_size,
        "raw_model_output_path": str(output_path) if output_path else None,
        "raw_model_output_sha256": output_sha256,
        "raw_model_output_byte_size": output_size,
        "usage": usage or _extract_usage(payload),
        "cost": cost,
    }
    _write_minimal_raw_receipt(receipt_path, receipt)
    if parse_failure:
        return ProviderResult(
            status_code=status,
            resolved_model=resolved_model,
            provider_invocation_id=invocation_id,
            failure_class=parse_failure,
            usage=usage or _extract_usage(payload),
            cost=cost,
        )
    return ProviderResult(
        text=text,
        resolved_model=resolved_model,
        provider_invocation_id=invocation_id,
        status_code=status,
        usage=usage or _extract_usage(payload),
        cost=cost,
    )


def call_nine_router(
    prompt: str,
    model: str,
    timeout_seconds: float = 60.0,
    *,
    max_tokens: int = 16000,
    temperature: float = 0.2,
    base_url: str | None = None,
) -> ProviderResult:
    """Canonical adapter; the shared/global operator fuse remains authoritative."""
    from live_contentops.llm_operator_control_v1 import assert_llm_operator_execution_enabled

    assert_llm_operator_execution_enabled()
    return _call_nine_router_impl(
        prompt, model, timeout_seconds, max_tokens=max_tokens,
        temperature=temperature, base_url=base_url,
    )


def call_nine_router_v2_isolated(
    prompt: str,
    model: str,
    timeout_seconds: float = 60.0,
    *,
    role_task_id: str,
    logical_invocation_id: str,
    component: str,
    max_tokens: int = 16000,
    temperature: float = 0.2,
    base_url: str | None = None,
) -> ProviderResult:
    """Explicit V2-only lease consumer; never a generic fuse override."""
    from live_contentops.v2_isolated_llm_execution_v1 import (
        assert_v2_execution_authorized,
        record_provider_attempt,
    )

    lease = assert_v2_execution_authorized(
        role_task_id=role_task_id, logical_invocation_id=logical_invocation_id,
        component=component, model=model, public_write=False,
    )
    prompt_sha256 = __import__("hashlib").sha256(str(prompt).encode("utf-8")).hexdigest()
    try:
        result = _call_nine_router_impl(
            prompt, model, timeout_seconds, max_tokens=max_tokens,
            temperature=temperature, base_url=base_url,
        )
    except BaseException as exc:
        record_provider_attempt(
            lease=lease, logical_invocation_id=logical_invocation_id,
            role_task_id=role_task_id, component=component, requested_model=model,
            prompt_sha256=prompt_sha256, error_class=type(exc).__name__,
        )
        raise
    record_provider_attempt(
        lease=lease, logical_invocation_id=logical_invocation_id,
        role_task_id=role_task_id, component=component, requested_model=model,
        prompt_sha256=prompt_sha256, result=result,
    )
    return result


def call_nine_router_v2_isolated_minimal_raw(
    prompt: Any,
    model: str,
    timeout_seconds: float,
    *,
    role_task_id: str,
    logical_invocation_id: str,
    component: str,
    evidence_dir: Path,
    base_url: str | None = None,
) -> ProviderResult:
    """Lease-bound V2 call whose request body contains only ``model`` and ``messages``."""
    from live_contentops.v2_isolated_llm_execution_v1 import (
        assert_v2_execution_authorized,
        record_provider_attempt,
    )

    lease = assert_v2_execution_authorized(
        role_task_id=role_task_id,
        logical_invocation_id=logical_invocation_id,
        component=component,
        model=model,
        public_write=False,
    )
    prompt_bytes = _prompt_bytes(prompt)
    prompt_sha256 = sha256(prompt_bytes).hexdigest()
    try:
        result = _call_nine_router_minimal_raw_impl(
            prompt,
            model,
            timeout_seconds,
            evidence_dir=Path(evidence_dir),
            isolated_execution_domain_id=lease.domain_id,
            base_url=base_url,
        )
    except BaseException as exc:
        record_provider_attempt(
            lease=lease,
            logical_invocation_id=logical_invocation_id,
            role_task_id=role_task_id,
            component=component,
            requested_model=model,
            prompt_sha256=prompt_sha256,
            error_class=type(exc).__name__,
        )
        raise
    record_provider_attempt(
        lease=lease,
        logical_invocation_id=logical_invocation_id,
        role_task_id=role_task_id,
        component=component,
        requested_model=model,
        prompt_sha256=prompt_sha256,
        result=result,
    )
    return result


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
