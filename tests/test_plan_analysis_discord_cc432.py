"""The minute consumer replies to a bot card inside its existing Discord run thread."""
from copy import deepcopy
from hashlib import sha256
import json

import pytest

from live_contentops import plan_analysis_pages_v1 as pages, plan_status_posts_v1 as posts
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
from test_plan_analysis_distribution_cc435 import ready, confirm  # noqa: F401
from test_plan_analysis_pages_cc432 import source  # noqa: F401
from test_publication_coordinator_v1 import FixtureTransport, _set_mode


def bot_card(store, original):
    run_key = "confirmed-run"
    store.create_work_item(story_id=run_key, work_item_id=run_key, title="Run", target_surface="MULTI_PLATFORM")
    confirm(store, run_key, sha256(("plan-status-post:" + run_key).encode()).hexdigest(),
            "discord", "700", "https://discord.com/channels/42/1519311669216673802/700")
    row = json.loads(store.get_outbox_message(original)["payload"])
    row.update(discord_delivery="bot_thread", run_key=run_key, parent_key=run_key)
    with store.get_connection() as connection:
        connection.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (json.dumps(row), original))


def test_installed_consumer_sends_analysis_to_existing_run_thread_and_exact_card(ready, monkeypatch):
    store, packet, original = ready
    bot_card(store, original)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    runtime = FixtureTransport()
    coordinator = Coordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_AUTHENTICATED"})
    coordinator.allow_prior_confirmed_distribution = True
    observed = []

    def publish(value_store, value):
        coordinator.recovery_scope = {"work_item_id": value["link_id"], "plan": value["plan"], "exact_work_item_only": True}
        if value["destination"] == "discord":
            observed.append(deepcopy(value["native_payload"]))
        return coordinator.publish_plan(value["link_id"], value["plan"])

    monkeypatch.setattr(pages, "publish_link", publish)
    result = posts.publish_ready(store)
    discord = next(r for r in result["analysis_distribution"]["links"] if r["destination"] == "discord")
    assert discord["outcome"]["per_destination"]["discord"]["status"] == "DISPATCH_CONFIRMED", json.dumps(discord["outcome"]["per_destination"], indent=2)
    assert observed[0]["discord_thread_parent_id"] == "700"
    assert observed[0]["reply_to_id"] == "parent-discord"
    assert packet["summary"]["macro"] in observed[0]["full_text"]
    before = len(runtime.publish_calls)
    posts.publish_ready(store)
    assert len(runtime.publish_calls) == before


def test_thread_substitution_is_refused_before_publication(ready):
    store, packet, original = ready
    bot_card(store, original)
    link = pages.register_link(store, packet, original_key=original, destination="discord")
    link["discord_thread_parent_id"] = "unrelated-run"
    with store.get_connection() as connection:
        connection.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (json.dumps(link), link["link_id"]))
    with pytest.raises(ValueError, match="PLAN_ANALYSIS_DISCORD_THREAD_CHANGED"):
        pages.validate_link_plan(store, link["link_id"], link["plan"])


@pytest.mark.parametrize("field", ["reply_to_id", "discord_thread_parent_id", "text"])
def test_text_reply_image_contract_still_checks_exact_canonical_and_parent(ready,field):
    from live_contentops.publication_image_contract_v1 import validate_write
    store,packet,original=ready
    bot_card(store,original)
    link=pages.register_link(store,packet,original_key=original,destination="discord")
    coordinator=Coordinator(store=store,transport_runtime=None)
    coordinator.register_plan(link["link_id"],link["plan"])
    intent=json.loads(store.list_outbox_messages(destination="discord")[-1]["payload"])
    intent["native_payload"][field]="unrelated"
    with pytest.raises(ValueError):
        validate_write(coordinator,intent,"discord")


def test_frozen_legacy_link_keeps_its_original_thread_bytes(ready):
    store, packet, original = ready
    link = pages.register_link(store, packet, original_key=original, destination="discord")
    link.pop("discord_thread_parent_id")
    payload = json.dumps(link)
    with store.get_connection() as connection:
        connection.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (payload, link["link_id"]))
    bot_card(store, original)
    assert pages.register_link(store, packet, original_key=original, destination="discord") == link
    assert pages.validate_link_plan(store, link["link_id"], link["plan"]) == link
    assert store.get_outbox_message(link["link_id"])["payload"] == payload


def test_real_coordinator_and_api_route_confirm_text_link_inside_the_card_thread(ready, monkeypatch):
    from live_contentops import discord_live_adapter_v6 as adapter, live_telemetry_v6 as telemetry
    from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1
    store, packet, original = ready
    bot_card(store, original)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    original_dispatch = Coordinator._ids(original, sha256(("plan-status-post:" + original).encode()).hexdigest(), "discord")
    with store.get_connection() as connection:
        connection.execute("UPDATE platform_dispatches SET public_object_id=?, public_object_url=? WHERE dispatch_id=?",
                           ("800", "https://discord.com/channels/42/700/800", original_dispatch["dispatch_id"]))
    link = pages.register_link(store, packet, original_key=original, destination="discord")
    calls = []
    observed = {"id": "901", "channel_id": "700", "guild_id": "42",
                "content": link["native_payload"]["text"], "message_reference": {"message_id": "800"},
                "attachments": [], "embeds": []}

    class Response:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def read(self): return json.dumps(self.payload).encode()

    def request(req, **kwargs):
        method, url = req.get_method(), req.full_url
        calls.append((method, url))
        if url == "https://discord.test/webhook":
            return Response({"channel_id": "1519311669216673802"})
        if url == "https://discord.com/api/v10/channels/700":
            return Response({"id": "700", "parent_id": "1519311669216673802", "type": 11})
        if method == "POST":
            assert url == "https://discord.com/api/v10/channels/700/messages"
            body = json.loads(req.data)
            assert body["message_reference"]["message_id"] == "800"
            assert packet["summary"]["macro"] in body["content"]
        else:
            assert url == "https://discord.com/api/v10/channels/700/messages/901"
        return Response(observed)

    monkeypatch.setattr(adapter, "read_secret", lambda name: "fixture-bot" if name == "DISCORD_BOT_TOKEN" else "https://discord.test/webhook")
    monkeypatch.setattr(adapter.urllib.request, "urlopen", request)
    monkeypatch.setattr(telemetry, "classify_and_record_dispatch", lambda **kw: None)
    coordinator = Coordinator(store=store, transport_runtime=CanonicalDestinationTransportRuntimeV1(),
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"})
    posts.scope_to_post(coordinator, link["link_id"], link["plan"])
    result = coordinator.publish_plan(link["link_id"], link["plan"])
    assert result["per_destination"]["discord"]["status"] == "DISPATCH_CONFIRMED", json.dumps(result["per_destination"], indent=2)
    assert pages.link_status(store, link)["confirmed"]
    assert sum(method == "POST" for method, _ in calls) == 1
    coordinator.publish_plan(link["link_id"], link["plan"])
    assert sum(method == "POST" for method, _ in calls) == 1
    # A later process must read the same text-only reply through the API too.
    fresh = Coordinator(store=store, transport_runtime=CanonicalDestinationTransportRuntimeV1(),
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"})
    ids = Coordinator._ids(link["link_id"], link["plan"]["plan_hash"], "discord")
    fresh.readback_existing_dispatch(ids["dispatch_id"])
    assert pages.link_status(store, link)["confirmed"]
    assert calls[-1] == ("GET", "https://discord.com/api/v10/channels/700/messages/901")
    assert sum(method == "POST" for method, _ in calls) == 1


@pytest.mark.parametrize("wrong", [None, "thread", "parent", "text", "canonical"])
def test_text_link_readback_requires_body_link_thread_and_parent(monkeypatch, wrong):
    from live_contentops import discord_live_adapter_v6 as adapter
    canonical = "https://capitalchronicle.substack.com/p/original-plan"
    text = "The full original plan: " + canonical
    payload = {"id": "901", "channel_id": "700", "guild_id": "42", "content": text,
               "message_reference": {"message_id": "800"}, "attachments": [], "embeds": []}
    if wrong == "thread": payload["channel_id"] = "unrelated"
    if wrong == "parent": payload["message_reference"]["message_id"] = "unrelated"
    if wrong == "text": payload["content"] = canonical
    if wrong == "canonical": payload["content"] = "The full original plan"

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def read(self): return json.dumps(payload).encode()

    monkeypatch.setattr(adapter, "read_secret", lambda name: "fixture")
    monkeypatch.setattr(adapter.urllib.request, "urlopen", lambda *a, **kw: Response())
    kwargs = dict(message_id="901", expected_text=text, canonical_url=canonical,
                  webhook_url="https://discord.test/webhook", thread_id="700", expected_parent_id="800")
    assert not adapter.readback_discord_post(**kwargs)["verified"]
    observed = adapter.readback_discord_post(**kwargs, require_media=False)
    assert observed["verified"] is (wrong is None)
    assert not observed["meaningful_media_visible"]
    assert not adapter.readback_discord_post(**kwargs, require_media=False,
        expected_image_sha256="f" * 64)["verified"]


@pytest.mark.parametrize("case", ["found", "found_without_guild", "absent", "full_page", "wrong_thread", "foreign_author", "duplicate", "changed_body"])
def test_coordinator_recovers_lost_discord_id_or_preserves_uncertainty(ready,monkeypatch,case):
    from live_contentops import discord_live_adapter_v6 as adapter
    from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1
    store,packet,original=ready
    bot_card(store,original)
    link=pages.register_link(store,packet,original_key=original,destination="discord")
    coordinator=Coordinator(store=store,transport_runtime=CanonicalDestinationTransportRuntimeV1())
    coordinator.register_plan(link["link_id"],link["plan"])
    ids=Coordinator._ids(link["link_id"],link["plan"]["plan_hash"],"discord")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"],message_id=ids["message_id"],
        platform="discord",status="UNKNOWN_WRITE")
    message={"id":"901","channel_id":"700","guild_id":"42","content":link["native_payload"]["text"],
        "author":{"id":"99","bot":True},"message_reference":{"message_id":"parent-discord"},
        "attachments":[],"embeds":[]}
    messages=[message]
    if case=="found_without_guild": message.pop('guild_id')
    if case=="absent": messages=[]
    if case=="full_page": messages=[{**message,"id":str(1000+i),"content":"Unrelated post."} for i in range(100)]
    if case=="foreign_author": message["author"]["id"]="98"
    if case=="duplicate": messages.append({**message,"id":"902"})
    if case=="changed_body": message["content"]="Other text: "+link["canonical_url"]
    calls=[]
    class Response:
        def __init__(self,value): self.value=value
        def __enter__(self):return self
        def __exit__(self,*_):return None
        def read(self):return json.dumps(self.value).encode()
    def request(req,**kwargs):
        assert req.get_method()=="GET"
        calls.append(req.full_url)
        if req.full_url.endswith('/users/@me'):return Response({'id':'99','bot':True})
        if req.full_url.endswith('/channels/700'):
            return Response({'id':'700','parent_id':'wrong' if case=='wrong_thread' else '1519311669216673802','type':11,'guild_id':'42'})
        if req.full_url.endswith('/messages?limit=100'):return Response(messages)
        assert req.full_url.endswith('/messages/901')
        return Response(message)
    monkeypatch.setattr(adapter,'read_secret',lambda name:'fixture')
    monkeypatch.setattr(adapter.urllib.request,'urlopen',request)
    result=coordinator.readback_existing_dispatch(ids['dispatch_id'])
    dispatch=store.get_platform_dispatch(ids['dispatch_id'])
    if case in {'found','found_without_guild'}:
        assert result['reconciliation_status']=='RECONCILED_CONFIRMED',result
        assert dispatch['status']=='DISPATCH_CONFIRMED'
        assert dispatch['public_object_id']=='901'
        assert dispatch['public_object_url']=='https://discord.com/channels/42/700/901'
    elif case=='absent':
        assert result['reconciliation_status']=='RECONCILED_ABSENT_SAFE_TO_RETRY',result
        assert dispatch['status']=='RECONCILED_ABSENT_SAFE_TO_RETRY'
    else:
        assert result['reconciliation_status']=='RECONCILIATION_PENDING',result
        assert dispatch['status']=='UNKNOWN_WRITE'
    assert not result['public_write_performed'] and not result['publish_called']
