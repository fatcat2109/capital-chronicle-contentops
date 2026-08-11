from __future__ import annotations

import base64
import hashlib
import io
import json
import time
from types import SimpleNamespace
from pathlib import Path
from urllib.request import Request

import pytest
from PIL import Image

import live_contentops.direct_image_api_v1 as direct_image
from live_contentops.direct_image_api_v1 import (
    DirectImageConfigError,
    ImageGenerationResult,
    MAX_CALLS,
    TransportWorkerLoss,
    credential_presence,
    generate_image,
    resolve_base_url,
)
from scripts.run_direct_image_bakeoff_v1 import JOURNAL_SCHEMA, run


def _png(width: int = 64, height: int = 36) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), "#203040").save(buffer, format="PNG")
    return buffer.getvalue()


def test_exact_endpoint_payload_and_model_identity(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel-secret-never-serialize")
    seen: dict[str, object] = {}

    def http(request: Request, timeout: float) -> tuple[int, str, bytes]:
        seen["url"] = request.full_url
        seen["method"] = request.method
        seen["payload"] = json.loads((request.data or b"").decode())
        seen["timeout"] = timeout
        payload = {
            "id": "img_test",
            "model": "gpt-5.5",
            "data": [{"b64_json": base64.b64encode(_png()).decode()}],
        }
        return 200, "application/json", json.dumps(payload).encode()

    result = generate_image(
        model="gpt-5.5",
        prompt="editorial concept",
        width=1536,
        height=864,
        output_file=tmp_path / "image.png",
        http=http,
    )

    assert seen["url"] == "https://ai.api-cheap.site/v1/images/generations"
    assert seen["method"] == "POST"
    assert seen["payload"] == {
        "model": "gpt-5.5",
        "prompt": "editorial concept",
        "size": "1536x864",
        "n": 1,
        "response_format": "b64_json",
    }
    assert result.requested_model == "gpt-5.5"
    assert result.effective_model == "gpt-5.5"
    assert result.protocol_mode == "base64"
    assert result.request_outcome == "CONFIRMED_SUCCESS"
    assert result.retry_state == "NO_RETRY"


def test_credentials_are_presence_only_and_never_serialized(
    monkeypatch, tmp_path: Path
) -> None:
    secret = "sentinel-secret-never-serialize"
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", secret)

    def http(request: Request, timeout: float) -> tuple[int, str, bytes]:
        payload = {"data": [{"b64_json": base64.b64encode(_png()).decode()}]}
        return 200, "application/json", json.dumps(payload).encode()

    result = generate_image(
        model="qwen-image-2.0",
        prompt="safe prompt",
        width=64,
        height=36,
        output_file=tmp_path / "image.png",
        http=http,
    )
    serialized = json.dumps(result.to_dict(), sort_keys=True)
    assert credential_presence() == {"AI_API_CHEAP_API_KEY": "PRESENT"}
    assert secret not in serialized
    assert "authorization" not in serialized.lower()


def test_nine_router_credential_is_never_read(monkeypatch, tmp_path: Path) -> None:
    class GuardedEnvironment(dict[str, str]):
        def get(self, key: str, default: str | None = None) -> str | None:
            assert key != "NINE_ROUTER_API_KEY"
            return super().get(key, default)

    guarded = GuardedEnvironment(
        {
            "AI_API_CHEAP_API_KEY": "direct-only-secret",
            "NINE_ROUTER_API_KEY": "must-never-be-read",
        }
    )
    monkeypatch.setattr(direct_image, "os", SimpleNamespace(environ=guarded))

    def http(request: Request, timeout: float) -> tuple[int, str, bytes]:
        payload = {"data": [{"b64_json": base64.b64encode(_png()).decode()}]}
        return 200, "application/json", json.dumps(payload).encode()

    result = generate_image(
        model="gpt-5.5",
        prompt="safe prompt",
        width=64,
        height=36,
        output_file=tmp_path / "image.png",
        http=http,
    )
    assert result.status == "SUCCESS"
    assert credential_presence(guarded) == {"AI_API_CHEAP_API_KEY": "PRESENT"}


def test_temporary_url_is_downloaded_and_query_is_redacted(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel")
    calls: list[str] = []

    def http(request: Request, timeout: float) -> tuple[int, str, bytes]:
        calls.append(request.full_url)
        if request.method == "POST":
            payload = {
                "data": [
                    {"url": "https://assets.example.test/out/image.png?sig=secret"}
                ]
            }
            return 200, "application/json", json.dumps(payload).encode()
        return 200, "image/png", _png()

    result = generate_image(
        model="wan2.7-image-pro",
        prompt="safe prompt",
        width=64,
        height=36,
        output_file=tmp_path / "image.png",
        http=http,
    )
    assert result.status == "SUCCESS"
    assert result.protocol_mode == "url"
    assert result.source_url_redacted == "https://assets.example.test/out/image.png"
    assert "sig=" not in json.dumps(result.to_dict())
    assert len(calls) == 2
    assert result.call_count == 1


def test_image_dimensions_type_and_hash_are_validated(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel")
    content = _png(80, 45)

    def http(request: Request, timeout: float) -> tuple[int, str, bytes]:
        payload = {"data": [{"b64_json": base64.b64encode(content).decode()}]}
        return 200, "application/json", json.dumps(payload).encode()

    output = tmp_path / "image.png"
    result = generate_image(
        model="gpt-5.5",
        prompt="safe prompt",
        width=80,
        height=45,
        output_file=output,
        http=http,
    )
    assert (result.width, result.height, result.content_type) == (80, 45, "image/png")
    assert result.output_sha256 == hashlib.sha256(content).hexdigest()
    assert output.read_bytes() == content


@pytest.mark.parametrize(
    ("status", "payload", "expected"),
    [
        (401, {"error": {"code": "invalid_api_key"}}, "PROVIDER_AUTHORIZATION_MISSING"),
        (404, {"error": {"code": "route_not_found"}}, "GATEWAY_ROUTE_UNSUPPORTED"),
        (400, {"error": {"code": "model_not_found"}}, "MODEL_ALIAS_NOT_FOUND"),
        (
            400,
            {"error": {"message": "model does not support image generation"}},
            "MODEL_CAPABILITY_NOT_IMAGE",
        ),
        (503, {"error": {"code": "upstream_unavailable"}}, "PROVIDER_UPSTREAM_ERROR"),
        (504, {"error": {"code": "timeout"}}, "TIMEOUT"),
    ],
)
def test_precise_http_failure_classification(
    monkeypatch, tmp_path: Path, status: int, payload: dict, expected: str
) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel")

    def http(request: Request, timeout: float) -> tuple[int, str, bytes]:
        return status, "application/json", json.dumps(payload).encode()

    result = generate_image(
        model="gpt-5.5",
        prompt="safe prompt",
        width=64,
        height=36,
        output_file=tmp_path / "image.png",
        http=http,
    )
    assert result.status == "FAILED"
    assert result.error_class == expected
    assert result.http_status == status
    assert result.request_outcome == "CONFIRMED_PROVIDER_REJECTION"
    assert result.retry_state == "NO_RETRY"


def test_malformed_response_and_missing_credential_are_exact(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel")

    def bad_http(request: Request, timeout: float) -> tuple[int, str, bytes]:
        return 200, "application/json", b"not-json"

    malformed = generate_image(
        model="gpt-5.5",
        prompt="safe prompt",
        width=64,
        height=36,
        output_file=tmp_path / "bad.png",
        http=bad_http,
    )
    assert malformed.error_class == "MALFORMED_RESPONSE"
    assert malformed.request_outcome == "CONFIRMED_MALFORMED_RESPONSE"
    assert malformed.retry_state == "NO_RETRY"
    monkeypatch.delenv("AI_API_CHEAP_API_KEY")
    missing = generate_image(
        model="gpt-5.5",
        prompt="safe prompt",
        width=64,
        height=36,
        output_file=tmp_path / "missing.png",
        http=bad_http,
    )
    assert missing.error_class == "PROVIDER_AUTHORIZATION_MISSING"
    assert missing.call_count == 0
    assert missing.request_outcome == "NOT_DISPATCHED"


def test_base_url_and_call_budget_fail_closed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel")
    with pytest.raises(DirectImageConfigError, match="host_not_allowed"):
        resolve_base_url("https://example.com/v1")
    with pytest.raises(DirectImageConfigError, match="host_not_allowed"):
        resolve_base_url("https://ai.api-cheap.site:8443/v1")
    assert resolve_base_url() == "https://ai.api-cheap.site/v1"
    with pytest.raises(DirectImageConfigError, match="max_calls_out_of_bounds"):
        generate_image(
            model="gpt-5.5",
            prompt="safe prompt",
            width=64,
            height=36,
            output_file=tmp_path / "image.png",
            max_calls=MAX_CALLS + 1,
        )


def test_hard_wall_returns_ambiguous_timeout_without_retry(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel")
    calls = 0

    def blocked(request: Request, timeout: float) -> tuple[int, str, bytes]:
        nonlocal calls
        calls += 1
        time.sleep(0.25)
        return 500, "application/json", b"{}"

    started = time.monotonic()
    result = generate_image(
        model="wan2.7-image-pro",
        prompt="safe prompt",
        width=64,
        height=36,
        output_file=tmp_path / "never.png",
        timeout_seconds=0.03,
        http=blocked,
    )
    elapsed = time.monotonic() - started
    assert elapsed < 0.15
    assert calls == 1
    assert result.status == "AMBIGUOUS"
    assert result.error_class == "TIMEOUT"
    assert result.request_outcome == "AMBIGUOUS_PROVIDER_OUTCOME"
    assert result.retry_state == "NO_RETRY"
    assert result.call_count == 1


def test_disconnect_and_worker_loss_are_ambiguous_no_retry(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel")

    def disconnected(request: Request, timeout: float) -> tuple[int, str, bytes]:
        raise ConnectionResetError("connection dropped")

    disconnect = generate_image(
        model="qwen-image-2.0",
        prompt="safe prompt",
        width=64,
        height=36,
        output_file=tmp_path / "disconnect.png",
        http=disconnected,
    )
    assert (disconnect.error_class, disconnect.request_outcome, disconnect.retry_state) == (
        "TRANSPORT_DISCONNECT",
        "AMBIGUOUS_PROVIDER_OUTCOME",
        "NO_RETRY",
    )

    def lost(*args: object, **kwargs: object) -> tuple[int, str, bytes]:
        raise TransportWorkerLoss("worker lost")

    monkeypatch.setattr(direct_image, "_bounded_http_call", lost)
    worker_loss = generate_image(
        model="qwen-image-2.0",
        prompt="safe prompt",
        width=64,
        height=36,
        output_file=tmp_path / "worker.png",
        http=disconnected,
    )
    assert (worker_loss.error_class, worker_loss.request_outcome, worker_loss.retry_state) == (
        "WORKER_LOSS",
        "AMBIGUOUS_PROVIDER_OUTCOME",
        "NO_RETRY",
    )


def _fake_success(**kwargs: object) -> ImageGenerationResult:
    output = Path(str(kwargs["output_file"]))
    content = _png(int(kwargs["width"]), int(kwargs["height"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)
    return ImageGenerationResult(
        requested_model=str(kwargs["model"]),
        effective_model=str(kwargs["model"]),
        provider="ai.api-cheap.site",
        invocation_id="test-id",
        status="SUCCESS",
        protocol_mode="base64",
        prompt_hash=hashlib.sha256(str(kwargs["prompt"]).encode()).hexdigest(),
        width=int(kwargs["width"]),
        height=int(kwargs["height"]),
        content_type="image/png",
        output_file=str(output),
        output_sha256=hashlib.sha256(content).hexdigest(),
        latency_ms=1,
        usage=None,
        cost=None,
        error_class=None,
        http_status=200,
        call_count=1,
        retry_state="NO_RETRY",
        request_outcome="CONFIRMED_SUCCESS",
    )


def test_bakeoff_reconciles_valid_artifact_and_resumes_without_retries(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel")
    smoke = tmp_path / "smoke" / "gpt-5_5.png"
    smoke.parent.mkdir(parents=True)
    original = _png(91, 57)
    smoke.write_bytes(original)
    calls: list[str] = []

    def tracked(**kwargs: object) -> ImageGenerationResult:
        calls.append(str(kwargs["output_file"]))
        return _fake_success(**kwargs)

    first = run(tmp_path, models=("gpt-5.5",), generate=tracked)
    assert len(calls) == 6
    assert smoke.read_bytes() == original
    assert first["total_generation_calls"] == 7
    assert first["status"] == "BAKEOFF_COMPLETE_FOR_SUCCESSFUL_MODELS"
    assert first["artifact_reconciliation"]["valid_existing_artifacts"][0][
        "output_sha256"
    ] == hashlib.sha256(original).hexdigest()

    calls.clear()
    second = run(tmp_path, models=("gpt-5.5",), generate=tracked)
    assert calls == []
    assert second["total_generation_calls"] == 7
    assert len(second["artifacts"]) == 7


def test_unfinished_dispatch_journal_is_never_reissued(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AI_API_CHEAP_API_KEY", "sentinel")
    tmp_path.mkdir(parents=True, exist_ok=True)
    journal = {
        "schema_version": JOURNAL_SCHEMA,
        "records": {
            "smoke:wan2.7-image-pro": {
                "state": "DISPATCH_STARTED",
                "dispatch_policy": "ONE_ATTEMPT_NO_AUTOMATIC_RETRY",
            }
        },
    }
    (tmp_path / "attempt_journal.json").write_text(json.dumps(journal), encoding="utf-8")
    calls: list[str] = []

    def forbidden(**kwargs: object) -> ImageGenerationResult:
        calls.append("unexpected")
        return _fake_success(**kwargs)

    manifest = run(tmp_path, models=("wan2.7-image-pro",), generate=forbidden)
    assert calls == []
    outcome = manifest["model_outcomes"]["wan2.7-image-pro"]
    assert outcome["status"] == "AMBIGUOUS"
    assert outcome["error_class"] == "WORKER_LOSS"
    assert outcome["retry_state"] == "NO_RETRY"
    assert manifest["total_generation_calls"] == 1
