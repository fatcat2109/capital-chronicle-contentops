"""Bounded, auditable image-generation boundary for the canonical 9Router gateway.

This module deliberately does not assume that the chat and image transports are the same.
It discovers the gateway's image model registry first, preserves the exact requested alias,
and normalizes synchronous base64/URL or explicitly returned asynchronous task responses.
No retry is performed after task creation; polling is bounded and fail-closed.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .nine_router_provider_adapter_v2 import resolve_base_url

TARGET_MODELS = ("new/qwen-image-2.0", "new/wan2.7-image-pro", "new/gpt-5.5")
FALLBACK_ORDER = ("new/gpt-5.5", "new/wan2.7-image-pro", "new/qwen-image-2.0")
IMAGE_BASE_URL = "https://ai.api-cheap.site/v1"
WIRE_MODEL_BY_ALIAS = {
    "new/gpt-5.5": "gpt-5.5",
    "new/wan2.7-image-pro": "wan2.7-image-pro",
    "new/qwen-image-2.0": "qwen-image-2.0",
}
MAX_POLL_SECONDS = 180.0
POLL_INTERVAL_SECONDS = 2.0


@dataclass
class ImageGenerationResult:
    requested_model: str
    effective_model: str | None = None
    provider: str | None = None
    invocation_id: str | None = None
    status: str = "FAILED"
    prompt_hash: str = ""
    width: int | None = None
    height: int | None = None
    content_type: str | None = None
    output_file: str | None = None
    output_sha256: str | None = None
    latency_seconds: float | None = None
    usage: dict[str, Any] | None = None
    cost: dict[str, Any] | None = None
    synthetic: bool = True
    error_class: str | None = None
    protocol_mode: str | None = None
    poll_count: int = 0
    http_status: int | None = None
    response_shape: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _redact_url(value: str | None) -> str | None:
    if not value:
        return None
    p = urlsplit(str(value))
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def _json_request(
    url: str, key: str, payload: Mapping[str, Any] | None = None, timeout: float = 30.0
) -> tuple[int, Mapping[str, Any]]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(
        url,
        data=body,
        method="POST" if body is not None else "GET",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        loaded = json.loads(raw)
        if not isinstance(loaded, Mapping):
            raise ValueError("response_not_object")
        return int(getattr(response, "status", 200) or 200), loaded


def discover_image_capabilities(
    *, base_url: str | None = None, api_key: str | None = None
) -> dict[str, Any]:
    """Read-only image registry and general model metadata, with presence-only auth state."""
    key = api_key or os.getenv("NINE_ROUTER_API_KEY")
    if not key:
        return {
            "status": "PROVIDER_AUTHORIZATION_MISSING",
            "credential": "MISSING",
            "models": [],
        }
    base = resolve_base_url(base_url)
    out: dict[str, Any] = {
        "base_url": base,
        "credential": "PRESENT",
        "models": [],
        "image_registry": [],
    }
    for suffix, field in (("/models", "models"), ("/models/image", "image_registry")):
        try:
            status, payload = _json_request(f"{base}{suffix}", key)
            rows = payload.get("data") if isinstance(payload.get("data"), list) else []
            out[field] = [
                {
                    k: v
                    for k, v in row.items()
                    if k in ("id", "owned_by", "capabilities", "kind")
                }
                for row in rows
                if isinstance(row, Mapping)
            ]
            out[f"{field}_http_status"] = status
        except HTTPError as exc:
            out[f"{field}_http_status"] = int(exc.code)
            out[f"{field}_error_class"] = "HTTP_ERROR"
        except (URLError, TimeoutError, OSError):
            out[f"{field}_error_class"] = "GATEWAY_UNREACHABLE"
        except (ValueError, json.JSONDecodeError):
            out[f"{field}_error_class"] = "MALFORMED_RESPONSE"
    return out


def _dimensions(data: bytes) -> tuple[int | None, int | None, str | None]:
    try:
        from PIL import Image
        from io import BytesIO

        with Image.open(BytesIO(data)) as im:
            return int(im.width), int(im.height), str(im.format or "").lower() or None
    except Exception:
        return None, None, None


def _extract_bytes(payload: Mapping[str, Any]) -> tuple[bytes | None, str | None, str]:
    data = payload.get("data")
    item = (
        data[0]
        if isinstance(data, list) and data and isinstance(data[0], Mapping)
        else payload
    )
    if not isinstance(item, Mapping):
        return None, None, "unknown"
    for key in ("b64_json", "base64", "image_base64"):
        if isinstance(item.get(key), str):
            return base64.b64decode(item[key], validate=True), None, "sync_base64"
    for key in ("url", "image_url", "output_url"):
        if isinstance(item.get(key), str):
            return None, item[key], "sync_url"
    return None, None, "unknown"


def _error_class(status: int, detail: str) -> str:
    lowered = detail.lower()
    if status in (401, 403) and any(
        x in lowered
        for x in ("permission_denied", "not permitted", "authorization", "api key")
    ):
        return "PROVIDER_AUTHORIZATION_MISSING"
    if "does not support image generation" in lowered:
        return "MODEL_CAPABILITY_NOT_IMAGE"
    if "model" in lowered and any(
        x in lowered for x in ("not found", "unknown", "invalid model")
    ):
        return "MODEL_ALIAS_NOT_FOUND"
    return "PROVIDER_UPSTREAM_ERROR"


def build_generation_payload(
    *, prompt: str, requested_model: str, width: int, height: int
) -> dict[str, Any]:
    if requested_model not in WIRE_MODEL_BY_ALIAS:
        raise ValueError("MODEL_ALIAS_NOT_FOUND")
    return {
        "model": WIRE_MODEL_BY_ALIAS[requested_model],
        "prompt": prompt,
        "size": f"{width}x{height}",
        "n": 1,
        "response_format": "b64_json",
    }


def generate_image(
    *,
    prompt: str,
    model: str,
    output_file: str,
    width: int = 1024,
    height: int = 1024,
    base_url: str | None = IMAGE_BASE_URL,
    api_key: str | None = None,
    timeout_seconds: float = 180.0,
    poll_interval_seconds: float = POLL_INTERVAL_SECONDS,
) -> ImageGenerationResult:
    started = time.monotonic()
    result = ImageGenerationResult(
        requested_model=model,
        prompt_hash=_hash_prompt(prompt),
        width=width,
        height=height,
    )
    key = api_key or os.getenv("NINE_ROUTER_API_KEY")
    if not key:
        result.error_class = "PROVIDER_AUTHORIZATION_MISSING"
        return result
    try:
        base = resolve_base_url(base_url)
    except Exception as exc:
        result.error_class = type(exc).__name__
        return result
    try:
        payload = build_generation_payload(
            prompt=prompt, requested_model=model, width=width, height=height
        )
    except ValueError:
        result.error_class = "MODEL_ALIAS_NOT_FOUND"
        return result
    try:
        status, body = _json_request(
            f"{base}/images/generations", key, payload, min(timeout_seconds, 180.0)
        )
        result.http_status = status
    except HTTPError as exc:
        result.http_status = int(exc.code)
        detail = exc.read().decode("utf-8", errors="replace")[:500].lower()
        result.error_class = _error_class(result.http_status, detail)
        result.latency_seconds = round(time.monotonic() - started, 3)
        result.protocol_mode = "sync_images_generations"
        return result
    except (URLError, TimeoutError, OSError):
        result.error_class = "GATEWAY_ROUTE_UNSUPPORTED"
        return result
    except (ValueError, json.JSONDecodeError):
        result.error_class = "MALFORMED_RESPONSE"
        return result
    result.response_shape = "object"
    result.effective_model = (
        body.get("model") or body.get("resolved_model") or body.get("effective_model")
    )
    result.provider = (
        body.get("provider") if isinstance(body.get("provider"), str) else None
    )
    result.invocation_id = body.get("id") or body.get("task_id")
    result.usage = (
        dict(body["usage"]) if isinstance(body.get("usage"), Mapping) else None
    )
    result.cost = dict(body["cost"]) if isinstance(body.get("cost"), Mapping) else None
    try:
        raw, url, mode = _extract_bytes(body)
    except (ValueError, binascii.Error):
        result.error_class = "MALFORMED_RESPONSE"
        return result
    result.protocol_mode = mode
    task_status = str(body.get("status") or "").lower()
    if (
        raw is None
        and url is None
        and result.invocation_id
        and task_status in ("queued", "pending", "processing", "running")
    ):
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,200}", str(result.invocation_id)):
            result.error_class = "MALFORMED_RESPONSE"
            return result
        result.protocol_mode = "async_task_poll"
        deadline = started + min(float(timeout_seconds), MAX_POLL_SECONDS)
        while time.monotonic() < deadline:
            time.sleep(max(float(poll_interval_seconds), 0.0))
            result.poll_count += 1
            try:
                result.http_status, body = _json_request(
                    f"{base}/images/generations/{result.invocation_id}",
                    key,
                    timeout=min(30.0, max(1.0, deadline - time.monotonic())),
                )
            except HTTPError as exc:
                result.http_status = int(exc.code)
                result.error_class = "PROVIDER_UPSTREAM_ERROR"
                return result
            except (URLError, TimeoutError, OSError):
                result.error_class = "TIMEOUT"
                return result
            try:
                raw, url, _ = _extract_bytes(body)
            except (ValueError, binascii.Error):
                result.error_class = "MALFORMED_RESPONSE"
                return result
            task_status = str(body.get("status") or "").lower()
            if raw is not None or url is not None:
                break
            if task_status in ("failed", "error", "cancelled"):
                result.error_class = "PROVIDER_UPSTREAM_ERROR"
                return result
        if raw is None and url is None:
            result.error_class = "TIMEOUT"
            return result
    if raw is None and url is not None:
        try:
            with urlopen(Request(url), timeout=min(timeout_seconds, 30.0)) as response:
                raw = response.read()
                result.content_type = response.headers.get_content_type()
        except Exception:
            result.error_class = "MALFORMED_RESPONSE"
            return result
    if raw is None:
        result.error_class = "MALFORMED_RESPONSE"
        return result
    w, h, fmt = _dimensions(raw)
    if w is None or h is None or fmt not in ("png", "jpeg", "webp"):
        result.error_class = "MALFORMED_RESPONSE"
        return result
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "wb") as fh:
        fh.write(raw)
    result.output_file = output_file
    result.output_sha256 = hashlib.sha256(raw).hexdigest()
    result.width = w
    result.height = h
    result.content_type = result.content_type or (f"image/{fmt}" if fmt else None)
    result.status = "GENERATION_SUCCESS"
    result.latency_seconds = round(time.monotonic() - started, 3)
    return result


def generate_with_fallback(
    *,
    prompt: str,
    output_file: str,
    width: int,
    height: int,
    base_url: str | None = IMAGE_BASE_URL,
    api_key: str | None = None,
    timeout_seconds: float = 180.0,
) -> tuple[ImageGenerationResult, list[dict[str, Any]]]:
    """Try the owner-authorized image pool in exact quality order, once each."""
    attempts: list[dict[str, Any]] = []
    final: ImageGenerationResult | None = None
    for model in FALLBACK_ORDER:
        result = generate_image(
            prompt=prompt,
            model=model,
            output_file=output_file,
            width=width,
            height=height,
            base_url=base_url,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        attempts.append(result.to_dict())
        final = result
        if result.status == "GENERATION_SUCCESS":
            return result, attempts
        if result.error_class in ("PROVIDER_AUTHORIZATION_MISSING",):
            break
    assert final is not None
    return final, attempts


def classify_capability(model: str, discovery: Mapping[str, Any]) -> str:
    if discovery.get("credential") == "MISSING":
        return "PROVIDER_AUTHORIZATION_MISSING"
    rows = discovery.get("models") or []
    row = next(
        (r for r in rows if isinstance(r, Mapping) and r.get("id") == model), None
    )
    if row is None:
        return "MODEL_ALIAS_NOT_FOUND"
    caps = (
        row.get("capabilities") if isinstance(row.get("capabilities"), Mapping) else {}
    )
    if caps.get("imageOutput") is not True:
        return "MODEL_CAPABILITY_NOT_IMAGE"
    return "IMAGE_CAPABILITY_EXPOSED"


ARCHETYPES = {
    "macro": "Central-bank policy uncertainty expressed through monumental civic architecture, shifting light, abstract market geometry, and blank unmarked paper forms",
    "corporate": "Corporate earnings inflection expressed through refined industrial architecture, product silhouettes, layered materials, and abstract operational momentum",
    "geopolitical": "Global trade tension expressed through ports, shipping geometry, border-like spatial divisions, and interconnected supply routes without flags or military spectacle",
}


def _bakeoff_prompt(concept: str, aspect: str) -> str:
    side = "right" if aspect == "landscape" else "upper third"
    return (
        "Premium institutional financial-news editorial illustration. " + concept + ". "
        f"Compose for {'16:9' if aspect == 'landscape' else '9:16'} with generous calm negative space in the {side} for later headline and chart overlays. "
        "Dark restrained palette, precise sophisticated magazine art direction, clean visual hierarchy, subtle material realism. "
        "No logos, text, numbers, charts, fake documents, screenshots, identifiable people, documentary-event simulation, crypto aesthetics, neon saturation, or clutter. Conceptual illustration only."
    )


def _contact_sheet(paths: list[str], destination: str, title: str) -> None:
    if not paths:
        return
    from PIL import Image, ImageDraw

    thumbs = []
    for path in paths:
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((480, 320))
            thumbs.append((path, image.copy()))
    width = 1000
    cell_h = 380
    height = 70 + ((len(thumbs) + 1) // 2) * cell_h
    sheet = Image.new("RGB", (width, height), "#111820")
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 22), title, fill="#f0f3f5")
    for i, (path, image) in enumerate(thumbs):
        x = 20 + (i % 2) * 490
        y = 65 + (i // 2) * cell_h
        sheet.paste(image, (x, y))
        draw.text((x, y + 325), os.path.basename(path), fill="#c8d0d8")
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    sheet.save(destination, quality=90)


def run_controlled_bakeoff(
    output_root: str, *, api_key: str | None = None
) -> dict[str, Any]:
    """Run three smokes, then six controlled assets per working model (max 21 calls)."""
    root = os.path.abspath(output_root)
    for folder in ("smoke", "landscape", "vertical", "contact_sheets"):
        os.makedirs(os.path.join(root, folder), exist_ok=True)
    common = "Premium institutional editorial illustration for a financial-news publication: global central-bank policy uncertainty represented through architecture, light, paper documents and abstract market geometry; dark restrained palette; sophisticated magazine art direction; no logos; no text; no numbers; no identifiable real person."
    rows: list[dict[str, Any]] = []
    working: list[str] = []
    for model in FALLBACK_ORDER:
        out = os.path.join(root, "smoke", WIRE_MODEL_BY_ALIAS[model] + ".png")
        result = generate_image(
            prompt=common, model=model, output_file=out, api_key=api_key
        )
        rows.append(
            result.to_dict()
            | {"phase": "smoke", "wire_model": WIRE_MODEL_BY_ALIAS[model]}
        )
        if result.status == "GENERATION_SUCCESS":
            working.append(model)
    by_model: dict[str, list[str]] = {model: [] for model in working}
    by_aspect: dict[str, list[str]] = {"landscape": [], "vertical": []}
    for model in working:
        for archetype, concept in ARCHETYPES.items():
            for aspect, dims in (("landscape", (1280, 720)), ("vertical", (720, 1280))):
                filename = f"{WIRE_MODEL_BY_ALIAS[model]}_{archetype}_{aspect}.png"
                out = os.path.join(root, aspect, filename)
                result = generate_image(
                    prompt=_bakeoff_prompt(concept, aspect),
                    model=model,
                    output_file=out,
                    width=dims[0],
                    height=dims[1],
                    api_key=api_key,
                )
                rows.append(
                    result.to_dict()
                    | {
                        "phase": "bakeoff",
                        "archetype": archetype,
                        "aspect": aspect,
                        "wire_model": WIRE_MODEL_BY_ALIAS[model],
                    }
                )
                if result.status == "GENERATION_SUCCESS":
                    by_model[model].append(out)
                    by_aspect[aspect].append(out)
    for model, paths in by_model.items():
        _contact_sheet(
            paths,
            os.path.join(root, "contact_sheets", WIRE_MODEL_BY_ALIAS[model] + ".jpg"),
            model,
        )
    _contact_sheet(
        by_aspect["landscape"],
        os.path.join(root, "contact_sheets", "all_models_landscape.jpg"),
        "All models — landscape",
    )
    _contact_sheet(
        by_aspect["vertical"],
        os.path.join(root, "contact_sheets", "all_models_vertical.jpg"),
        "All models — vertical",
    )
    manifest = {
        "status": "PROVISIONAL_IMAGE_BAKEOFF_AWAITING_JIM_CHATGPT_VISUAL_REVIEW",
        "fallback_order": list(FALLBACK_ORDER),
        "generation_limit": 30,
        "generation_attempts": len(rows),
        "successful_generations": sum(
            r["status"] == "GENERATION_SUCCESS" for r in rows
        ),
        "working_models": working,
        "results": rows,
    }
    with open(
        os.path.join(root, "generation_manifest.json"), "w", encoding="utf-8"
    ) as fh:
        json.dump(manifest, fh, indent=2)
    return manifest
