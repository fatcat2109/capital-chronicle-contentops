"""The reviewed PNG reaches the exact existing Discord message via PATCH."""
import io
import json
from PIL import Image

from live_contentops.discord_live_adapter_v6 import execute_discord_edit


def test_exact_existing_message_receives_png_attachment(tmp_path, monkeypatch):
    path = tmp_path / "approved.png"
    Image.new("RGB", (1600, 900), "white").save(path)
    calls = []
    def open_request(request, **kwargs):
        calls.append(request)
        return io.BytesIO(json.dumps({"id": "123"}).encode())
    monkeypatch.setattr("urllib.request.urlopen", open_request)
    monkeypatch.setattr("live_contentops.live_telemetry_v6.classify_and_record_dispatch", lambda **kwargs: None)
    result = execute_discord_edit("123", "Reviewed copy https://capitalchronicle.substack.com/p/article",
        webhook_url="https://discord.com/api/webhooks/fixture/token", image_path=str(path), embeds=[])
    assert result["status"] == "SUCCESS" and len(calls) == 1
    request = calls[0]
    assert request.get_method() == "PATCH" and request.full_url.endswith("/messages/123")
    assert path.read_bytes() in request.data
    assert b'"attachments": [{"id": 0, "filename": "article-image.png"}]' in request.data


def test_invalid_image_never_writes(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("write")))
    result = execute_discord_edit("123", "copy", webhook_url="https://discord.com/api/webhooks/fixture/token",
        image_path=str(tmp_path / "missing.png"))
    assert result["definite_no_write"] is True
