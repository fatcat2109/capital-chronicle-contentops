"""Bounded direct image transport for the owner-authorized ai.api-cheap.site API.

This module is intentionally separate from the canonical 9Router text adapter.  It keeps
the requested model visible, accepts only the documented ``/v1/images/generations`` route,
normalizes base64 or temporary-URL responses, and never serializes credentials or signed
URLs.  It is an integration boundary for the Tier2 diagnostic only; it does not grant any
publication or V1 runtime authority.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import queue
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image

ENV_API_KEY = "AI_API_CHEAP_API_KEY"
DEFAULT_BASE_URL = "https://ai.api-cheap.site/v1"
IMAGE_PATH = "/images/generations"
OWNER_MODELS = ("gpt-5.5", "wan2.7-image-pro", "qwen-image-2.0")
MAX_CALLS = 24
MAX_WALL_SECONDS = 180.0
POLL_INTERVAL_SECONDS = 2.0

GenerationHttp = Callable[[Request, float], tuple[int, str, bytes]]


@dataclass(frozen=True)
class ImageGenerationResult:
    requested_model: str
    effective_model: str | None
    provider: str
    invocation_id: str | None
    status: str
    protocol_mode: str | None
    prompt_hash: str
    width: int | None
    height: int | None
    content_type: str | None
    output_file: str | None
    output_sha256: str | None
    latency_ms: int | None
    usage: dict[str, Any] | None
    cost: dict[str, Any] | None
    error_class: str | None
    http_status: int | None
    call_count: int
    retry_state: str | None = None
    request_outcome: str = "NOT_DISPATCHED"
    response_schema: str | None = None
    source_url_redacted: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DirectImageConfigError(ValueError):
    pass


class TransportWorkerLoss(RuntimeError):
    pass


def credential_presence(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return presence only; neither key nor Authorization value is ever returned."""
    source = env if env is not None else os.environ
    return {ENV_API_KEY: "PRESENT" if source.get(ENV_API_KEY) else "MISSING"}


def resolve_base_url(raw: str | None = None) -> str:
    value = (raw or DEFAULT_BASE_URL).rstrip("/")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() != "ai.api-cheap.site"
        or parsed.port is not None
    ):
        raise DirectImageConfigError("direct_image_host_not_allowed")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise DirectImageConfigError("direct_image_url_contains_sensitive_material")
    if parsed.path != "/v1":
        raise DirectImageConfigError("direct_image_base_path_must_equal_v1")
    return value


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _safe_schema(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return type(payload).__name__
    keys = sorted(str(k) for k in payload.keys())
    return "object{" + ",".join(keys[:30]) + (",..." if len(keys) > 30 else "") + "}"


def _effective_model(payload: Mapping[str, Any]) -> str | None:
    for key in ("model", "effective_model", "resolved_model"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _usage(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    value = payload.get("usage")
    return dict(value) if isinstance(value, Mapping) else None


def _cost(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    for key in ("cost", "total_cost", "cost_usd"):
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return {"usd": float(value)}
        if isinstance(value, Mapping):
            return {
                str(k): v for k, v in value.items() if isinstance(v, (int, float))
            } or None
    return None


def _error_class(status: int | None, error_payload: Any) -> str:
    text = (
        json.dumps(error_payload, sort_keys=True).lower()
        if error_payload is not None
        else ""
    )
    if status in (401, 403) or any(
        x in text for x in ("unauthorized", "invalid api key", "authentication")
    ):
        return "PROVIDER_AUTHORIZATION_MISSING"
    if any(
        x in text
        for x in (
            "model_not_found",
            "model not found",
            "unknown model",
            "invalid model",
        )
    ):
        return "MODEL_ALIAS_NOT_FOUND"
    if any(
        x in text
        for x in (
            "not an image",
            "image capability",
            "unsupported image",
            "images not supported",
            "does not support image",
        )
    ):
        return "MODEL_CAPABILITY_NOT_IMAGE"
    if status == 404 or any(
        x in text
        for x in ("route_not_found", "endpoint_not_found", "unsupported route")
    ):
        return "GATEWAY_ROUTE_UNSUPPORTED"
    if status in (408, 504):
        return "TIMEOUT"
    if status is not None and status >= 500:
        return "PROVIDER_UPSTREAM_ERROR"
    return "OTHER_EXACT_ERROR"


def _default_http(request: Request, timeout: float) -> tuple[int, str, bytes]:
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL is validated
            return (
                int(response.status),
                response.headers.get("Content-Type", ""),
                response.read(),
            )
    except HTTPError as exc:
        return int(exc.code), exc.headers.get("Content-Type", ""), exc.read()


def _bounded_http_call(
    http: GenerationHttp, request: Request, timeout: float
) -> tuple[int, str, bytes]:
    """Return from a network call after a hard wall-time bound.

    The worker is daemonized so an upstream socket that ignores its read timeout
    cannot keep the bakeoff process alive. Injected test transports use the same
    boundary, which keeps the production and test call budgets aligned.
    """
    result_queue: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)

    def worker() -> None:
        try:
            result_queue.put(("result", http(request, timeout)))
        except BaseException as exc:  # propagate the exact transport failure
            result_queue.put(("error", exc))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(max(0.001, timeout))
    if thread.is_alive():
        raise TimeoutError("bounded_http_call_timeout")
    try:
        kind, value = result_queue.get_nowait()
    except queue.Empty as exc:
        raise TransportWorkerLoss("bounded_http_worker_lost") from exc
    if kind == "error":
        raise value
    return value


def _redacted_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return "invalid_url"
    path = parsed.path or "/"
    return f"{parsed.scheme}://{parsed.hostname}{path}"


def _decode_output(
    payload: Mapping[str, Any],
) -> tuple[bytes | None, str | None, str | None, str | None]:
    data = payload.get("data")
    item: Mapping[str, Any] | None = None
    if isinstance(data, list) and data and isinstance(data[0], Mapping):
        item = data[0]
    elif isinstance(payload.get("image"), Mapping):
        item = payload["image"]
    if item is None:
        return None, None, None, None
    for key in ("b64_json", "base64", "image_base64"):
        encoded = item.get(key)
        if isinstance(encoded, str) and encoded:
            try:
                return base64.b64decode(encoded, validate=True), "base64", None, None
            except (ValueError, base64.binascii.Error):
                return None, "base64", None, "MALFORMED_RESPONSE"
    for key in ("url", "image_url"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return None, "url", value, None
    return None, None, None, None


def _validate_image(content: bytes) -> tuple[int, int, str]:
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            width, height = image.size
            content_type = Image.MIME.get(
                image.format or "", "application/octet-stream"
            )
    except Exception as exc:  # PIL raises several format-specific exceptions
        raise ValueError("image_bytes_invalid") from exc
    if width < 1 or height < 1 or not content_type.startswith("image/"):
        raise ValueError("image_dimensions_or_type_invalid")
    return int(width), int(height), content_type


def _download_url(
    value: str, http: GenerationHttp, timeout: float
) -> tuple[bytes, str]:
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("output_url_invalid")
    request = Request(value, method="GET", headers={"Accept": "image/*"})
    status, content_type, body = http(request, timeout)
    if status < 200 or status >= 300:
        raise ValueError(f"output_download_http_{status}")
    return body, content_type.split(";", 1)[0].lower() or "application/octet-stream"


def _failure_result(
    *,
    model: str,
    prompt: str,
    started: float,
    error_class: str,
    call_count: int,
    request_outcome: str,
    retry_state: str | None,
    protocol_mode: str | None = "sync",
    effective_model: str | None = None,
    invocation_id: str | None = None,
    http_status: int | None = None,
    usage: dict[str, Any] | None = None,
    cost: dict[str, Any] | None = None,
    response_schema: str | None = None,
    source_url_redacted: str | None = None,
) -> ImageGenerationResult:
    return ImageGenerationResult(
        requested_model=model,
        effective_model=effective_model,
        provider="ai.api-cheap.site",
        invocation_id=invocation_id,
        status="AMBIGUOUS" if request_outcome.startswith("AMBIGUOUS_") else "FAILED",
        protocol_mode=protocol_mode,
        prompt_hash=_prompt_hash(prompt),
        width=None,
        height=None,
        content_type=None,
        output_file=None,
        output_sha256=None,
        latency_ms=int((time.monotonic() - started) * 1000),
        usage=usage,
        cost=cost,
        error_class=error_class,
        http_status=http_status,
        call_count=call_count,
        retry_state=retry_state,
        request_outcome=request_outcome,
        response_schema=response_schema,
        source_url_redacted=source_url_redacted,
    )


def generate_image(
    *,
    model: str,
    prompt: str,
    width: int,
    height: int,
    output_file: str | Path,
    timeout_seconds: float = 60.0,
    max_calls: int = 1,
    http: GenerationHttp | None = None,
) -> ImageGenerationResult:
    """Dispatch exactly once inside a hard wall and never retry an uncertain call."""
    if model not in OWNER_MODELS:
        raise DirectImageConfigError(f"model_not_owner_selected:{model}")
    if max_calls < 1 or max_calls > MAX_CALLS:
        raise DirectImageConfigError("max_calls_out_of_bounds")
    if timeout_seconds <= 0:
        raise DirectImageConfigError("timeout_must_be_positive")
    base_url = resolve_base_url()
    api_key = os.environ.get(ENV_API_KEY)
    started = time.monotonic()
    if not api_key:
        return _failure_result(
            model=model,
            prompt=prompt,
            started=started,
            error_class="PROVIDER_AUTHORIZATION_MISSING",
            call_count=0,
            request_outcome="NOT_DISPATCHED",
            retry_state=None,
            protocol_mode=None,
        )
    target = Path(output_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model,
        "prompt": prompt,
        "size": f"{width}x{height}",
        "n": 1,
        "response_format": "b64_json",
    }
    request = Request(
        base_url + IMAGE_PATH,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    http_call = http or _default_http
    deadline = started + min(float(timeout_seconds), MAX_WALL_SECONDS)

    def remaining() -> float:
        value = deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError("generation_hard_wall_expired")
        return value

    calls = 1
    try:
        status, _response_type, raw = _bounded_http_call(http_call, request, remaining())
    except TimeoutError:
        return _failure_result(
            model=model,
            prompt=prompt,
            started=started,
            error_class="TIMEOUT",
            call_count=calls,
            request_outcome="AMBIGUOUS_PROVIDER_OUTCOME",
            retry_state="NO_RETRY",
        )
    except TransportWorkerLoss as exc:
        return _failure_result(
            model=model,
            prompt=prompt,
            started=started,
            error_class="WORKER_LOSS",
            call_count=calls,
            request_outcome="AMBIGUOUS_PROVIDER_OUTCOME",
            retry_state="NO_RETRY",
            response_schema=type(exc).__name__,
        )
    except (URLError, ConnectionError, OSError, EOFError) as exc:
        return _failure_result(
            model=model,
            prompt=prompt,
            started=started,
            error_class="TRANSPORT_DISCONNECT",
            call_count=calls,
            request_outcome="AMBIGUOUS_PROVIDER_OUTCOME",
            retry_state="NO_RETRY",
            response_schema=type(exc).__name__,
        )
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _failure_result(
            model=model,
            prompt=prompt,
            started=started,
            error_class="MALFORMED_RESPONSE",
            call_count=calls,
            request_outcome="CONFIRMED_MALFORMED_RESPONSE",
            retry_state="NO_RETRY",
            http_status=status,
        )
    if not isinstance(decoded, Mapping):
        return _failure_result(
            model=model,
            prompt=prompt,
            started=started,
            error_class=(
                _error_class(status, decoded)
                if status < 200 or status >= 300
                else "MALFORMED_RESPONSE"
            ),
            call_count=calls,
            request_outcome=(
                "CONFIRMED_PROVIDER_REJECTION"
                if status < 200 or status >= 300
                else "CONFIRMED_MALFORMED_RESPONSE"
            ),
            retry_state="NO_RETRY",
            http_status=status,
            response_schema=_safe_schema(decoded),
        )
    if status < 200 or status >= 300:
        return _failure_result(
            model=model,
            prompt=prompt,
            started=started,
            error_class=_error_class(status, decoded),
            call_count=calls,
            request_outcome="CONFIRMED_PROVIDER_REJECTION",
            retry_state="NO_RETRY",
            effective_model=_effective_model(decoded),
            invocation_id=(
                decoded.get("id") if isinstance(decoded.get("id"), str) else None
            ),
            http_status=status,
            usage=_usage(decoded),
            cost=_cost(decoded),
            response_schema=_safe_schema(decoded),
        )
    content, protocol, output_url, decode_error = _decode_output(decoded)
    if decode_error:
        error = decode_error
    elif content is None and output_url:
        try:
            content, _ = _download_url(
                output_url,
                lambda download_request, download_timeout: _bounded_http_call(
                    http_call, download_request, download_timeout
                ),
                remaining(),
            )
        except TimeoutError:
            return _failure_result(
                model=model,
                prompt=prompt,
                started=started,
                error_class="TIMEOUT",
                call_count=calls,
                request_outcome="AMBIGUOUS_OUTPUT_RETRIEVAL",
                retry_state="NO_RETRY",
                protocol_mode=protocol,
                effective_model=_effective_model(decoded),
                invocation_id=(
                    decoded.get("id")
                    if isinstance(decoded.get("id"), str)
                    else None
                ),
                http_status=status,
                usage=_usage(decoded),
                cost=_cost(decoded),
                response_schema=_safe_schema(decoded),
                source_url_redacted=_redacted_url(output_url),
            )
        except (TransportWorkerLoss, URLError, ConnectionError, OSError, EOFError) as exc:
            return _failure_result(
                model=model,
                prompt=prompt,
                started=started,
                error_class=(
                    "WORKER_LOSS"
                    if isinstance(exc, TransportWorkerLoss)
                    else "TRANSPORT_DISCONNECT"
                ),
                call_count=calls,
                request_outcome="AMBIGUOUS_OUTPUT_RETRIEVAL",
                retry_state="NO_RETRY",
                protocol_mode=protocol,
                effective_model=_effective_model(decoded),
                invocation_id=(
                    decoded.get("id")
                    if isinstance(decoded.get("id"), str)
                    else None
                ),
                http_status=status,
                usage=_usage(decoded),
                cost=_cost(decoded),
                response_schema=type(exc).__name__,
                source_url_redacted=_redacted_url(output_url),
            )
        except ValueError:
            error = "MALFORMED_RESPONSE"
        else:
            error = None
    else:
        error = None if content is not None else "MALFORMED_RESPONSE"
    if error or content is None:
        return _failure_result(
            model=model,
            prompt=prompt,
            started=started,
            error_class=error or "MALFORMED_RESPONSE",
            call_count=calls,
            request_outcome="CONFIRMED_MALFORMED_RESPONSE",
            retry_state="NO_RETRY",
            protocol_mode=protocol,
            effective_model=_effective_model(decoded),
            invocation_id=(
                decoded.get("id") if isinstance(decoded.get("id"), str) else None
            ),
            http_status=status,
            usage=_usage(decoded),
            cost=_cost(decoded),
            response_schema=_safe_schema(decoded),
            source_url_redacted=_redacted_url(output_url) if output_url else None,
        )
    try:
        actual_width, actual_height, content_type = _validate_image(content)
    except ValueError:
        return _failure_result(
            model=model,
            prompt=prompt,
            started=started,
            error_class="MALFORMED_RESPONSE",
            call_count=calls,
            request_outcome="CONFIRMED_MALFORMED_RESPONSE",
            retry_state="NO_RETRY",
            protocol_mode=protocol,
            effective_model=_effective_model(decoded),
            invocation_id=(
                decoded.get("id") if isinstance(decoded.get("id"), str) else None
            ),
            http_status=status,
            usage=_usage(decoded),
            cost=_cost(decoded),
            response_schema=_safe_schema(decoded),
            source_url_redacted=_redacted_url(output_url) if output_url else None,
        )
    temporary = target.with_suffix(target.suffix + ".partial")
    temporary.write_bytes(content)
    temporary.replace(target)
    digest = hashlib.sha256(content).hexdigest()
    return ImageGenerationResult(
        requested_model=model,
        effective_model=_effective_model(decoded),
        provider="ai.api-cheap.site",
        invocation_id=(
            decoded.get("id") if isinstance(decoded.get("id"), str) else None
        ),
        status="SUCCESS",
        protocol_mode=protocol,
        prompt_hash=_prompt_hash(prompt),
        width=actual_width,
        height=actual_height,
        content_type=content_type,
        output_file=str(target),
        output_sha256=digest,
        latency_ms=int((time.monotonic() - started) * 1000),
        usage=_usage(decoded),
        cost=_cost(decoded),
        error_class=None,
        http_status=status,
        call_count=calls,
        retry_state="NO_RETRY",
        request_outcome="CONFIRMED_SUCCESS",
        response_schema=_safe_schema(decoded),
        source_url_redacted=_redacted_url(output_url) if output_url else None,
    )


def result_json(result: ImageGenerationResult) -> dict[str, Any]:
    """Serialize only normalized, secret-free result fields."""
    return result.to_dict()
