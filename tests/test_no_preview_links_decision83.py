"""Jim's decision 83 (5 Nov): until Capital Chronicle owns its own domain, no post on social media or
Substack links to the preview or any other host. Every route refuses such a copy or link before the
write with PREVIEW_HOST_LINK_FORBIDDEN. Controlled fixtures and fake transports only."""
from __future__ import annotations

import json
import sys

import pytest

from live_contentops import publication_coordinator_v1 as coordinator_module
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _publish_one_destination_from_durable_intent
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff, _social_canonical
from live_contentops.plan_status_posts_v1 import API_DESTINATIONS, prepare_post, queue_posts
from live_contentops.preview_link_guard_v1 import REASON, find_forbidden_link
from test_plan_status_posts_cc306 import NOW, export as export_fixture, main_root  # noqa: F401
from test_plan_status_publication_cc306 import fake_host, no_real_snapshot  # noqa: F401
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode

HOSTS = ["https://fatcat2109.github.io/capital-chronicle-preview/articles/" + "a" * 32 + "/",
         "https://capital-chronicle.pages.dev/x", "https://cc.workers.dev/x", "https://cc.netlify.app/x",
         "https://cc.vercel.app/x", "https://example.github.io/x", "see capital-chronicle-preview soon",
         "fatcat2109"]


@pytest.mark.parametrize("text", HOSTS)
def test_the_guard_finds_every_forbidden_host(text):
    assert find_forbidden_link({"text": "Gold: new plan. " + text}) is not None


def test_the_guard_passes_a_substack_link_and_plain_copy():
    assert find_forbidden_link({"text": "Read it: https://capitalchronicle.substack.com/p/gold"},
                               "https://capitalchronicle.substack.com/p/gold") is None


def test_the_preview_article_is_never_a_social_canonical():
    assert not _social_canonical(HOSTS[0])
    assert _social_canonical("https://capitalchronicle.substack.com/p/gold")


def test_site_first_plans_take_the_substack_route():
    confirmed, absent, confirm = coordinator_module._site_first_owners()
    assert coordinator_module.SITE_LINKS_ALLOWED is False
    assert confirmed() is None and absent() is True and confirm() is None


@pytest.fixture
def registered(tmp_path, export_fixture, main_root):
    store, transport, coordinator = _coordinator(tmp_path, runtime=FixtureTransport())
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    queued = queue_posts(store, export_fixture, now=NOW, main_root=main_root, python=sys.executable)
    key = queued["queued"][0]["key"]
    plan = prepare_post(store, key, root=tmp_path / "posts", host=fake_host, destinations=API_DESTINATIONS)
    store.create_work_item(story_id=key, title="Plan status post", target_surface="MULTI_PLATFORM", work_item_id=key)
    coordinator.register_plan(key, plan)
    return store, transport, coordinator, key


def _tampered(store, key, destination, text):
    message = next(r for r in store.list_outbox_messages()
                   if r["work_item_id"] == key and r["destination"] == destination)
    intent = json.loads(message["payload"])
    intent["native_payload"] = {**intent["native_payload"], "text": text, "full_text": text}
    return {**message, "payload": json.dumps(intent)}, intent


@pytest.mark.parametrize("destination", API_DESTINATIONS)
def test_the_coordinator_refuses_a_preview_link_before_any_write(registered, destination):
    store, transport, coordinator, key = registered
    message, _ = _tampered(store, key, destination, "Gold: new plan. https://fatcat2109.github.io/capital-chronicle-preview/")
    outcome = coordinator._dispatch_message(message, canonical_url=None)
    assert outcome["status"] == REASON and outcome["publish_called"] is False
    assert transport.publish_calls == [] and store.list_platform_dispatches() == []


def test_the_coordinator_refuses_a_preview_canonical_link(registered):
    store, transport, coordinator, key = registered
    message = next(r for r in store.list_outbox_messages() if r["work_item_id"] == key and r["destination"] == "telegram")
    outcome = coordinator._dispatch_message(message, canonical_url="https://capital-chronicle.pages.dev/a/")
    assert outcome["status"] == REASON and transport.publish_calls == []


@pytest.mark.parametrize("destination", API_DESTINATIONS)
def test_the_transport_router_refuses_the_final_payload(registered, destination, monkeypatch):
    store, _, _, key = registered
    _, intent = _tampered(store, key, destination, "Gold: new plan. https://cc.netlify.app/plan")
    called = []
    monkeypatch.setattr("live_contentops.telegram_live_adapter_v6.execute_telegram_photo", lambda **kw: called.append(kw))
    monkeypatch.setattr("live_contentops.discord_live_adapter_v6.execute_discord_post", lambda **kw: called.append(kw))
    monkeypatch.setattr("live_contentops.threads_adapter_v6.execute_threads_post", lambda **kw: called.append(kw))
    intent["attempt_identity"] = "attempt-1"
    result = _publish_one_destination_from_durable_intent(destination=destination, intent=intent,
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "attempt-1"})
    assert result["reason_code"] == REASON and result["definite_no_write"] is True and called == []


@pytest.mark.parametrize("destination,canonical,payload", [
    ("x", "https://capitalchronicle.substack.com/p/gold", "Gold. https://cc.vercel.app/gold"),
    ("x", HOSTS[0], "Gold."),
    ("substack", None, "# Gold\n\nThe chart lives at https://fatcat2109.github.io/capital-chronicle-preview/."),
])
def test_the_agent_route_refuses_before_any_request(destination, canonical, payload):
    intent = {"work_item_id": "work", "plan_hash": "plan", "package_identity": "pkg", "canonical_url": canonical,
              "distribution_policy": "SITE_FIRST_V1", "payload": payload, "native_payload": {"text": payload},
              "destination_plan": {"payload_hash": "hash", "surface": "X_POST" if destination == "x" else "SUBSTACK_ARTICLE"}}
    auth = {"schema_version": "contentops.canonical_machine_authorization.v1", "operating_mode": "AUTONOMOUS_DEFAULT",
            "destination": destination, "dispatch_attempt_identity": "dispatch_1", "work_item_id": "work",
            "payload_hash": "hash"}
    seen = []
    handoff = NeoDestinationHandoff(native_executor=lambda request: seen.append(request))
    with pytest.raises(ValueError, match=REASON + "|RECONCILED_CANONICAL_URL_REQUIRED"):
        handoff.request(destination=destination, action="PUBLISH", intent=intent, authorization_context=auth)
    assert seen == []


def test_a_status_post_carries_no_link_on_any_destination(registered):
    store, _, _, key = registered
    for row in store.list_outbox_messages():
        if row["work_item_id"] != key:
            continue
        intent = json.loads(row["payload"])
        assert intent.get("canonical_url") in (None, "")
        assert find_forbidden_link(intent["native_payload"]) is None and "https://" not in intent["native_payload"]["text"]
