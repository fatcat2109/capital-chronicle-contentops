"""A supplied correction reaches the existing consumer once, with frozen reply targets."""
import json

import pytest

from live_contentops import plan_status_correction_cc359 as correction
from live_contentops import plan_status_posts_v1 as posts
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
from test_plan_status_publication_cc306 import fake_host
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode


def prepared(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    for n, key in enumerate(correction.ORIGINAL_KEYS):
        store.create_work_item(story_id=key, title="Original", target_surface="MULTI_PLATFORM", work_item_id=key)
        store.register_outbox_message(message_id=key, work_item_id=key, destination=posts.DESTINATION,
                                      payload=json.dumps({"historical": n}), status="PUBLISHED")
        for d in ("telegram", "discord", "threads"):
            message = key + d
            store.register_outbox_message(message_id=message, work_item_id=key, destination=d, payload="{}")
            store.register_platform_dispatch(dispatch_id=message, message_id=message, platform=d,
                status="DISPATCH_CONFIRMED", public_object_id=str(100 + n), public_object_url=None)
    root = tmp_path / "posts"
    plan = correction.prepare(store, root=root, host=fake_host)
    return store, transport, coordinator, plan, root


def test_correction_reaches_live_consumer_once_and_preserves_originals(tmp_path):
    store, transport, coordinator, plan, root = prepared(tmp_path)
    originals = [store.get_outbox_message(k) for k in correction.ORIGINAL_KEYS]
    coordinator.execute_plan(correction.KEY, plan)
    intents = {m["destination"]: json.loads(m["payload"]) for m in store.list_outbox_messages()
               if m["work_item_id"] == correction.KEY and m["destination"] in posts.POST_DESTINATIONS}
    assert set(intents) == set(posts.POST_DESTINATIONS)
    for d, intent in intents.items():
        data = _durable_intent_inputs(intent)
        assert data["payloads"][d]["full_text"] == correction.TEXT
        assert data["payloads"][d] == intent["native_payload"]
        assert "https://" not in data["payloads"][d]["text"]
        if d in {"threads", "telegram"}:
            assert intent["native_payload"]["reply_to_id"] == "100"
            assert len(intent["native_payload"]["correction_of"]) == 2
        if d == "x":
            assert all(posts._x_length(p["text"]) <= 280 for p in intent["native_payload"]["posts"])
        assert data["local_media"].endswith(".png")
    assert sorted(transport.publish_calls) == sorted(posts.POST_DESTINATIONS)
    coordinator.execute_plan(correction.KEY, plan)
    assert len(transport.publish_calls) == 5
    assert originals == [store.get_outbox_message(k) for k in correction.ORIGINAL_KEYS]
    again = correction.prepare(store, root=root, host=fake_host)
    assert again == plan
    changed = dict(intents["telegram"])
    changed["native_payload"] = {**changed["native_payload"], "reply_to_id": "999"}
    with pytest.raises(posts.PlanPostError, match="COPY_CHANGED"):
        posts.validate_status_post_intent(store, changed)


@pytest.mark.parametrize("local", [False, True])
def test_telegram_photo_serializes_exact_reply_without_mutating_original(tmp_path, monkeypatch, local):
    from live_contentops import telegram_live_adapter_v6 as adapter
    import urllib.request
    monkeypatch.setattr(adapter, "_guard_non_dry_run_telegram_action", lambda **k: {"dispatch_allowed": True})
    monkeypatch.setattr("live_contentops.live_telemetry_v6.classify_and_record_dispatch", lambda **k: None)
    sent = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self): return b'{"ok":true,"result":{"message_id":200}}'
    def send(request, **kwargs):
        sent.append(request)
        return Response()
    monkeypatch.setattr(urllib.request, "urlopen", send)
    photo = "https://example.test/card.png"
    if local:
        path = tmp_path / "card.png"
        path.write_bytes(b"fixture")
        photo = str(path)
    result = adapter.execute_telegram_photo(photo_url=photo, caption=correction.TEXT, bot_token="fixture",
        chat_id="fixture", reply_to_message_id="104", parse_mode=None)
    assert result["status"] == "SUCCESS"
    assert sent[0].method == "POST" and sent[0].full_url.endswith("/sendPhoto")
    if local:
        assert b'name="reply_parameters"' in sent[0].data and b'{"message_id": 104}' in sent[0].data
    else:
        assert json.loads(sent[0].data)["reply_parameters"] == {"message_id": 104}
