import base64
from io import BytesIO
import json

import pytest

import live_contentops.nine_router_image_generation_v1 as mod


from PIL import Image

_png = BytesIO()
Image.new("RGB", (1, 1), (0, 0, 0)).save(_png, format="PNG")
PNG_1X1 = _png.getvalue()


class Response:
    def __init__(self, payload, status=200, content_type="application/json"):
        self.payload = (
            payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        )
        self.status = status
        self.headers = type("H", (), {"get_content_type": lambda self: content_type})()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_alias_preserved_and_wire_model_exact(tmp_path, monkeypatch):
    captured = {}

    def fake(req, timeout):
        captured["payload"] = json.loads(req.data)
        return Response(
            {
                "id": "img-1",
                "model": "gpt-5.5",
                "data": [{"b64_json": base64.b64encode(PNG_1X1).decode()}],
            }
        )

    monkeypatch.setattr(mod, "urlopen", fake)
    result = mod.generate_image(
        prompt="p",
        model="new/gpt-5.5",
        output_file=str(tmp_path / "x.png"),
        api_key="secret",
    )
    assert result.requested_model == "new/gpt-5.5"
    assert result.effective_model == "gpt-5.5"
    assert captured["payload"] == {
        "model": "gpt-5.5",
        "prompt": "p",
        "size": "1024x1024",
        "n": 1,
        "response_format": "b64_json",
    }


def test_base64_normalization_hash_dimensions_and_content_type(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mod,
        "urlopen",
        lambda req, timeout: Response(
            {"data": [{"b64_json": base64.b64encode(PNG_1X1).decode()}]}
        ),
    )
    out = tmp_path / "x.png"
    result = mod.generate_image(
        prompt="p", model="new/qwen-image-2.0", output_file=str(out), api_key="secret"
    )
    assert result.status == "GENERATION_SUCCESS"
    assert result.output_sha256 == mod.hashlib.sha256(PNG_1X1).hexdigest()
    assert result.width == result.height == 1
    assert result.content_type == "image/png"
    assert out.read_bytes() == PNG_1X1


def test_temporary_url_download_and_redaction(tmp_path, monkeypatch):
    calls = []

    def fake(req, timeout):
        calls.append(req.full_url)
        if len(calls) == 1:
            return Response(
                {"data": [{"url": "https://assets.example/out.png?sig=secret"}]}
            )
        return Response(PNG_1X1, content_type="image/png")

    monkeypatch.setattr(mod, "urlopen", fake)
    result = mod.generate_image(
        prompt="p",
        model="new/gpt-5.5",
        output_file=str(tmp_path / "x.png"),
        api_key="secret",
    )
    assert result.status == "GENERATION_SUCCESS"
    assert mod._redact_url(calls[1]) == "https://assets.example/out.png"
    assert "sig=" not in json.dumps(result.to_dict())


def test_async_polling_is_bounded_and_succeeds(tmp_path, monkeypatch):
    replies = iter(
        [
            Response({"task_id": "task-1", "status": "pending"}),
            Response(
                {
                    "task_id": "task-1",
                    "status": "completed",
                    "data": [{"b64_json": base64.b64encode(PNG_1X1).decode()}],
                }
            ),
        ]
    )
    monkeypatch.setattr(mod, "urlopen", lambda req, timeout: next(replies))
    monkeypatch.setattr(mod.time, "sleep", lambda _: None)
    result = mod.generate_image(
        prompt="p",
        model="new/wan2.7-image-pro",
        output_file=str(tmp_path / "x.png"),
        api_key="secret",
        poll_interval_seconds=0,
    )
    assert result.status == "GENERATION_SUCCESS"
    assert result.protocol_mode == "async_task_poll"
    assert result.poll_count == 1


def test_timeout(monkeypatch, tmp_path):
    clock = iter([0.0, 0.0, 0.0, 181.0, 181.0])
    monkeypatch.setattr(mod.time, "monotonic", lambda: next(clock, 181.0))
    monkeypatch.setattr(
        mod,
        "urlopen",
        lambda req, timeout: Response({"task_id": "task-1", "status": "pending"}),
    )
    result = mod.generate_image(
        prompt="p",
        model="new/gpt-5.5",
        output_file=str(tmp_path / "x.png"),
        api_key="secret",
        timeout_seconds=180,
    )
    assert result.error_class == "TIMEOUT"


def test_non_image_capability_classification():
    discovery = {
        "credential": "PRESENT",
        "models": [{"id": "new/gpt-5.5", "capabilities": {"imageOutput": False}}],
    }
    assert (
        mod.classify_capability("new/gpt-5.5", discovery)
        == "MODEL_CAPABILITY_NOT_IMAGE"
    )


def test_malformed_response(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mod, "urlopen", lambda req, timeout: Response({"unexpected": True})
    )
    result = mod.generate_image(
        prompt="p",
        model="new/gpt-5.5",
        output_file=str(tmp_path / "x.png"),
        api_key="secret",
    )
    assert result.error_class == "MALFORMED_RESPONSE"


def test_invalid_image_bytes_are_not_persisted(tmp_path, monkeypatch):
    encoded = base64.b64encode(b"not-an-image").decode()
    monkeypatch.setattr(
        mod, "urlopen", lambda req, timeout: Response({"data": [{"b64_json": encoded}]})
    )
    output = tmp_path / "x.png"
    result = mod.generate_image(
        prompt="p", model="new/gpt-5.5", output_file=str(output), api_key="secret"
    )
    assert result.error_class == "MALFORMED_RESPONSE"
    assert not output.exists()


def test_no_secret_serialization(tmp_path, monkeypatch):
    secret = "sentinel-never-serialize"
    monkeypatch.setattr(
        mod,
        "urlopen",
        lambda req, timeout: Response(
            {"data": [{"b64_json": base64.b64encode(PNG_1X1).decode()}]}
        ),
    )
    result = mod.generate_image(
        prompt="p",
        model="new/gpt-5.5",
        output_file=str(tmp_path / "x.png"),
        api_key=secret,
    )
    assert secret not in json.dumps(result.to_dict())
    assert "Bearer" not in json.dumps(result.to_dict())


def test_unknown_alias_fails_without_network(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mod, "urlopen", lambda *a, **k: pytest.fail("network must not run")
    )
    result = mod.generate_image(
        prompt="p",
        model="other/model",
        output_file=str(tmp_path / "x.png"),
        api_key="secret",
    )
    assert result.error_class == "MODEL_ALIAS_NOT_FOUND"


def test_fallback_order_is_owner_authorized(monkeypatch, tmp_path):
    seen = []

    def fake(**kwargs):
        seen.append(kwargs["model"])
        return mod.ImageGenerationResult(
            requested_model=kwargs["model"],
            status="FAILED",
            error_class="MODEL_CAPABILITY_NOT_IMAGE",
        )

    monkeypatch.setattr(mod, "generate_image", fake)
    _, attempts = mod.generate_with_fallback(
        prompt="p",
        output_file=str(tmp_path / "x.png"),
        width=1,
        height=1,
        api_key="secret",
    )
    assert seen == ["new/gpt-5.5", "new/wan2.7-image-pro", "new/qwen-image-2.0"]
    assert len(attempts) == 3
