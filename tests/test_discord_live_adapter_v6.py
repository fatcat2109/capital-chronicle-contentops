"""Unit tests for Discord Live Adapter."""
from __future__ import annotations

import json

import pytest

from live_contentops.discord_live_adapter_v6 import (
    execute_discord_comment,
    execute_discord_edit,
    execute_discord_post,
    readback_discord_post,
)


@pytest.mark.parametrize("provider_id", ["123456789", None])
def test_cc401_wait_true_uses_only_the_provider_message_id(monkeypatch, provider_id):
    from urllib.parse import urlsplit, parse_qs
    from live_contentops import discord_live_adapter_v6 as adapter, live_telemetry_v6
    import json
    from unittest.mock import MagicMock
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps({"id": provider_id}).encode()
    def send(request, **kwargs):
        assert parse_qs(urlsplit(request.full_url).query)["wait"] == ["true"]
        return response
    monkeypatch.setattr(adapter.urllib.request, "urlopen", send)
    monkeypatch.setattr(live_telemetry_v6, "classify_and_record_dispatch", lambda *a, **kw: None)
    result = adapter.execute_discord_post("fixture", webhook_url="https://discord.test/webhook?wait=false")
    assert result["id"] == provider_id
    from live_contentops.publication_coordinator_v1 import normalize_dispatch_result
    normalized = normalize_dispatch_result(result, destination="discord", surface="DISCORD_ANNOUNCEMENT", transport_type="WEBHOOK_API")
    assert normalized["status"] == ("DISPATCH_CONFIRMED" if provider_id else "UNKNOWN_WRITE")


def test_execute_discord_post_dry_run():
    res = execute_discord_post(
        message="Test announcement message",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "discord"
    assert res["action"] == "post"
    assert res["payload_redacted"]["message"] == "Test announcement message"
    assert "discord_mock_msg_" in res["response"]["id"]


def test_execute_discord_comment_dry_run():
    res = execute_discord_comment(
        thread_id_or_url="1519311669216673802",
        message="Test thread comment",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "discord"
    assert res["action"] == "comment"
    assert res["payload_redacted"]["thread_id"] == "1519311669216673802"


def test_execute_discord_edit_dry_run():
    res = execute_discord_edit(
        message_id="123456789012345678",
        new_message="Updated content message",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "discord"
    assert res["action"] == "edit"
    assert res["payload_redacted"]["new_message"] == "Updated content message"


def test_readback_discord_post_proves_exact_object(monkeypatch):
    from live_contentops import discord_live_adapter_v6 as adapter

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps(
                {
                    "id": "1537129462486007910",
                    "channel_id": "1519311669216673802",
                    "guild_id": "1000000000000000000",
                    "content": "Exact text https://capitalchronicle.substack.com/p/article",
                    "embeds": [{"image": {"url": "https://example.test/image.png"}}],
                }
            ).encode()

    monkeypatch.setattr(adapter.urllib.request, "urlopen", lambda *_a, **_k: Response())
    result = readback_discord_post(
        message_id="1537129462486007910",
        expected_text="Exact text",
        canonical_url="https://capitalchronicle.substack.com/p/article",
        webhook_url="https://discord.test/api/webhooks/id/token",
    )

    assert result["status"] == "SUCCESS"
    assert result["verified"] is True
    assert result["write_exists"] is True
    assert result["meaningful_media_visible"] is True


def test_edit_existing_message_transmits_explicit_media_without_creating_a_post(monkeypatch):
    from live_contentops import discord_live_adapter_v6 as adapter
    import live_contentops.live_telemetry_v6 as telemetry
    calls = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def read(self): return b'{"id":"123"}'
    def opener(request, **_):
        calls.append(request)
        return Response()
    monkeypatch.setattr(adapter.urllib.request, "urlopen", opener)
    monkeypatch.setattr(telemetry, "classify_and_record_dispatch", lambda **_: None)
    embeds = [{"image": {"url": "https://example.test/original.jpeg"}}]
    result = execute_discord_edit("123", "Same copy", webhook_url="https://discord.test/api/webhooks/id/token", embeds=embeds)
    assert result["status"] == "SUCCESS" and len(calls) == 1
    assert calls[0].method == "PATCH" and calls[0].full_url.endswith('/messages/123')
    assert json.loads(calls[0].data) == {"content": "Same copy", "embeds": embeds}


def _discord_send(monkeypatch, tmp_path, *, selected, delivery_ready):
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    from hashlib import sha256
    from PIL import Image
    path = tmp_path / "photo.png"
    Image.new("RGB", (32, 32), "white").save(path)
    asset = {"asset_id": "reviewed-photo", "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}
    data = {"output_dir": tmp_path, "article": {"title": "Dated report"},
        "payloads": {"discord": {"text": "Reviewed copy", "media_asset_ids": [asset["asset_id"]] if selected else []}},
        "canonical_url": "https://capitalchronicle.substack.com/p/exact", "media_assets": [asset],
        "local_media": str(path), "public_image_url": "https://example.test/photo.png" if delivery_ready else ""}
    calls = []
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda _: data)
    monkeypatch.setattr(pipeline, "_publish_discord_verified", lambda **kw: calls.append(kw) or {"status": "SUCCESS"})
    result = pipeline._publish_one_destination_from_durable_intent(destination="discord", intent={"attempt_identity": "exact"},
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "exact"})
    return result, calls, data


@pytest.mark.parametrize("delivery_ready", [False, True])
def test_native_discord_send_never_omits_the_selected_image(monkeypatch, tmp_path, delivery_ready):
    # Decision 61 (49b238d0): every Discord post carries its selected, hash-verified image.
    result, calls, data = _discord_send(monkeypatch, tmp_path, selected=True, delivery_ready=delivery_ready)
    assert result["status"] == "SUCCESS" and len(calls) == 1
    assert calls[0]["image_path"] == data["local_media"]
    assert calls[0]["image_url"] == data["public_image_url"]


def test_native_discord_without_a_selected_image_is_definite_no_write(monkeypatch, tmp_path):
    # Replaces the former photo-optional case: a text-only Discord post is no longer sent.
    result, calls, _ = _discord_send(monkeypatch, tmp_path, selected=False, delivery_ready=False)
    assert result["status"] == "DEFINITE_NO_WRITE" and result["public_write_performed"] is False
    assert result["reason_code"] == "EVERY_POST_IMAGE_REQUIRED:discord" and calls == []


def test_discord_uploads_binary_attachment_and_reads_back_its_exact_hash(tmp_path, monkeypatch):
    from hashlib import sha256
    from PIL import Image
    from live_contentops import discord_live_adapter_v6 as adapter
    import live_contentops.live_telemetry_v6 as telemetry

    path = tmp_path / "own-card.png"
    Image.new("RGB", (100, 100), "navy").save(path)
    binary = path.read_bytes()
    canonical = "https://capitalchronicle.substack.com/p/exact"
    payload = {"id": "123", "channel_id": "1519311669216673802", "guild_id": "42",
               "content": "Reviewed " + canonical,
               "attachments": [{"content_type": "image/png", "url": "https://cdn.discordapp.com/attachments/42/card.png"}]}
    requests = []

    class Response:
        def __init__(self, data): self.data = data
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def read(self, *_): return self.data

    def opener(request, **_):
        requests.append(request)
        return Response(binary if isinstance(request, str) else json.dumps(payload).encode())

    monkeypatch.setattr(adapter.urllib.request, "urlopen", opener)
    monkeypatch.setattr(telemetry, "classify_and_record_dispatch", lambda **_: None)
    webhook = "https://discord.test/api/webhooks/id/token"
    sent = adapter.execute_discord_post(payload["content"], webhook_url=webhook, image_path=str(path),
                                        embeds=[{"title": "Exact", "url": canonical}])
    assert sent["status"] == "SUCCESS"
    assert requests[0].get_header("Content-type").startswith("multipart/form-data;")
    assert binary in requests[0].data
    assert b'name="files[0]"' in requests[0].data
    assert b'attachment://article-image.png' in requests[0].data
    observed = adapter.readback_discord_post(message_id="123", expected_text="Reviewed", canonical_url=canonical,
        webhook_url=webhook, expected_image_sha256=sha256(binary).hexdigest())
    assert observed["verified"] and observed["attached_article_visual"] and observed["image_sha256_match"]
    wrong = adapter.readback_discord_post(message_id="123", expected_text="Reviewed", canonical_url=canonical,
        webhook_url=webhook, expected_image_sha256="0" * 64)
    assert not wrong["verified"] and wrong["write_exists"]


@pytest.mark.parametrize("parent", ["700", "800"])
def test_thread_starter_uses_containment_while_inner_replies_keep_their_reference(monkeypatch, parent):
    from live_contentops import discord_live_adapter_v6 as adapter, live_telemetry_v6 as telemetry
    bodies = []

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def read(self): return b'{"id":"901"}'

    def send(request, **_):
        assert request.full_url == "https://discord.com/api/v10/channels/700/messages"
        bodies.append(json.loads(request.data))
        return Response()

    monkeypatch.setattr(adapter, "read_secret", lambda _: "fixture")
    monkeypatch.setattr(adapter, "_ensure_call_thread", lambda *a: {"status": "READY"})
    monkeypatch.setattr(adapter.urllib.request, "urlopen", send)
    monkeypatch.setattr(telemetry, "classify_and_record_dispatch", lambda **_: None)
    result = adapter.execute_discord_post("Exact original copy", webhook_url="https://discord.test/webhook",
        thread_parent_id="700", reply_to_message_id=parent)
    assert result["status"] == "SUCCESS"
    assert bodies[0]["content"] == "Exact original copy"
    if parent == "700":
        assert "message_reference" not in bodies[0]
    else:
        assert bodies[0]["message_reference"]["message_id"] == "800"
        assert bodies[0]["message_reference"]["fail_if_not_exists"]


@pytest.mark.parametrize("wrong", [None, "parent", "thread"])
def test_starter_link_recovery_checks_its_exact_thread_and_preserves_foreign_references(monkeypatch, wrong):
    from live_contentops import discord_live_adapter_v6 as adapter
    text = "Original analysis https://capitalchronicle.substack.com/p/original"
    message = {"id": "901", "channel_id": "700", "guild_id": "42", "content": text,
               "author": {"id": "99", "bot": True}, "attachments": [], "embeds": []}
    if wrong == "parent": message["message_reference"] = {"message_id": "800"}
    if wrong == "thread": message["channel_id"] = "701"

    class Response:
        def __init__(self, value): self.value = value
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def read(self): return json.dumps(self.value).encode()

    def get(request, **_):
        assert request.get_method() == "GET"
        url = request.full_url
        if url.endswith("/channels/700"):
            return Response({"id": "700", "parent_id": "1519311669216673802", "type": 11})
        if url.endswith("/users/@me"): return Response({"id": "99", "bot": True})
        return Response([message] if url.endswith("?limit=100") else message)

    monkeypatch.setattr(adapter, "read_secret", lambda _: "fixture")
    monkeypatch.setattr(adapter.urllib.request, "urlopen", get)
    result = adapter.find_discord_thread_post(thread_id="700", expected_text=text,
        canonical_url="https://capitalchronicle.substack.com/p/original", expected_parent_id="700", require_media=False)
    assert result["verified"] is (wrong is None)
    assert not result.get("write_absent")
    if wrong is None:
        assert result["thread_verified"] and result["reply_parent_verified"]
