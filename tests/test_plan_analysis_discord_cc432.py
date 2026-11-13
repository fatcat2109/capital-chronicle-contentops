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


def test_standalone_setup_links_in_its_own_discord_thread_without_a_count_root(ready,monkeypatch):
    store,packet,original=ready
    row=json.loads(store.get_outbox_message(original)['payload'])
    row.update(kind='setup',parent_key=None,run_key='internal-group-without-public-root',discord_delivery='bot_thread')
    with store.get_connection() as connection:
        connection.execute('UPDATE outbox_messages SET payload=? WHERE message_id=?',(json.dumps(row),original))
    link=pages.register_link(store,packet,original_key=original,destination='discord')
    assert link['native_payload']['discord_thread_parent_id']=='parent-discord'
    assert link['native_payload']['reply_to_id']=='parent-discord'
    assert pages.validate_link_plan(store,link['link_id'],link['plan'])==link
    assert store.get_outbox_message('internal-group-without-public-root') is None


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


def test_recovery_consumes_an_absent_text_link_without_refinalizing_its_bytes(ready):
    store, packet, original = ready
    bot_card(store, original)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    runtime = FixtureTransport()
    coordinator = Coordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"})
    link = pages.register_link(store, packet, original_key=original, destination="discord")
    posts.scope_to_post(coordinator, link["link_id"], link["plan"])
    registered = coordinator.register_plan(link["link_id"], link["plan"])["registered"][0]
    store.register_platform_dispatch(dispatch_id=registered["dispatch_id"],
        message_id=registered["message_id"], platform="discord", status="RECONCILED_ABSENT_SAFE_TO_RETRY")
    store.register_reconciliation(reconciliation_id=registered["reconciliation_id"],
        work_item_id=link["link_id"], status="RECONCILED_ABSENT_SAFE_TO_RETRY")
    store.set_outbox_status(registered["message_id"], "RECONCILED_ABSENT_SAFE_TO_RETRY")
    before = store.get_outbox_message(registered["message_id"])["payload"]
    coordinator.publish_plan(link["link_id"], link["plan"])
    assert pages.link_status(store, link)["confirmed"]
    assert runtime.publish_calls == ["discord"]
    assert store.get_outbox_message(registered["message_id"])["payload"] == before
    coordinator.publish_plan(link["link_id"], link["plan"])
    assert runtime.publish_calls == ["discord"]


def test_recovery_does_not_rebind_a_text_link_to_another_canonical(ready):
    store, packet, original = ready
    link = pages.register_link(store, packet, original_key=original, destination="discord")
    coordinator = Coordinator(store=store, transport_runtime=FixtureTransport())
    registered = coordinator.register_plan(link["link_id"], link["plan"])["registered"][0]
    message = store.get_outbox_message(registered["message_id"])
    with pytest.raises(ValueError, match="PLAN_ANALYSIS_LINK_CANONICAL_CHANGED"):
        coordinator._finalize_derivative_intent(message, canonical_url="https://capitalchronicle.substack.com/p/other")
    assert store.get_outbox_message(registered["message_id"])["payload"] == message["payload"]


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
            assert not body.get("embeds"), "A text-only reply must not send an empty embed."
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


@pytest.mark.parametrize("http_status,code", [(400, 50035), (403, 40333)])
def test_discord_wrapper_retains_provider_failure_for_exact_diagnosis(monkeypatch, http_status, code):
    from live_contentops import discord_live_adapter_v6 as adapter
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    failure = {"status": "FAILED", "error_code": http_status,
               "error_response": {"code": code, "message": "Provider rejection"}}
    monkeypatch.setattr(adapter, "execute_discord_post", lambda **_: failure)
    result = pipeline._publish_discord_verified(text="Original reply", canonical_url="https://example.test/page",
                                               title="", image_url=None, require_media=False)
    assert result == failure


def failed_empty_embed(ready, *, uncertain=False, lose_return=False):
    from datetime import datetime, timezone
    store, packet, original = ready
    bot_card(store, original)
    _set_mode(store, "AUTONOMOUS_DEFAULT")

    class Transport(FixtureTransport):
        def readback(self, **kwargs):
            if not kwargs["public_object_id"]:
                return ({"status": "AMBIGUOUS", "verified": False} if uncertain else
                        {"status": "NOT_FOUND", "verified": False, "write_absent": True})
            return super().readback(**kwargs)

    runtime = Transport(raise_after_write=lose_return)
    coordinator = Coordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda _: {"readiness_state": "READY_NON_BROWSER_BINDING"})
    link = pages.register_link(store, packet, original_key=original, destination="discord")
    posts.scope_to_post(coordinator, link["link_id"], link["plan"])
    ids = coordinator.register_plan(link["link_id"], link["plan"])["registered"][0]
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="discord", status="DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE")
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id=link["link_id"],
                                  status="RECONCILED_ABSENT_SAFE_TO_RETRY")
    coordinator._record_retry_attempt(ids["dispatch_id"], link["link_id"])
    at = datetime.now(timezone.utc).isoformat()
    coordinator._record_destination_day_failure({"work_item_id": link["link_id"]}, "discord",
        {"dispatch_id": ids["dispatch_id"], "status": "UNKNOWN_WRITE", "attempt_started_at_utc": at})
    evidence = {"event_id": "measured-http-rejection", "timestamp": at, "platform_id": "discord", "action": "post",
        "http_status": 400, "error_response": {"code": 50035, "errors": {"embeds": {"0": {
            "description": {"_errors": [{"code": "BASE_TYPE_REQUIRED"}]}}}}}}
    return store, coordinator, runtime, link, ids, evidence


def test_repaired_empty_embed_completes_the_same_live_consumer_reply_once(ready):
    store, coordinator, runtime, link, ids, evidence = failed_empty_embed(ready)
    before = store.get_outbox_message(ids["message_id"])["payload"]
    result = pages.repair_discord_empty_embed(coordinator, link, evidence)
    assert result["status"] == "DISPATCH_CONFIRMED", result
    assert pages.link_status(store, link)["confirmed"]
    assert runtime.publish_calls == ["discord"]
    assert coordinator._destination_day_failure("discord") is None
    assert store.get_outbox_message(ids["message_id"])["payload"] == before
    assert pages.repair_discord_empty_embed(coordinator, link, evidence)["publish_called"] is False
    assert runtime.publish_calls == ["discord"]


@pytest.mark.parametrize("wrong", ["restriction", "other_field", "other_time", "other_dispatch"])
def test_empty_embed_correction_does_not_release_a_platform_failure(ready, wrong):
    store, coordinator, runtime, link, ids, evidence = failed_empty_embed(ready)
    if wrong == "restriction":
        evidence.update(http_status=403, error_response={"code": 40333})
    elif wrong == "other_field":
        evidence["error_response"]["errors"] = {"content": {"_errors": [{"code": "BASE_TYPE_REQUIRED"}]}}
    elif wrong == "other_time":
        evidence["timestamp"] = "2020-01-01T00:00:00Z"
    else:
        with store.get_connection() as connection:
            connection.execute("UPDATE incidents SET description=? WHERE severity='DISPATCH_FAILURE'",
                (json.dumps({"dispatch_id": "other", "attempt_started_at_utc": evidence["timestamp"]}),))
    with pytest.raises(ValueError, match="EXACT_DISCORD_EMPTY_EMBED_REJECTION_REQUIRED"):
        pages.repair_discord_empty_embed(coordinator, link, evidence)
    assert coordinator._destination_day_failure("discord") is not None
    assert runtime.publish_calls == []


def test_empty_embed_correction_preserves_uncertain_absence(ready):
    _, coordinator, runtime, link, _, evidence = failed_empty_embed(ready, uncertain=True)
    result = pages.repair_discord_empty_embed(coordinator, link, evidence)
    assert result["reconciliation_status"] == "RECONCILIATION_PENDING"
    assert coordinator._destination_day_failure("discord") is not None
    assert runtime.publish_calls == []


def test_lost_correction_return_cannot_allocate_another_send(ready):
    _, coordinator, runtime, link, _, evidence = failed_empty_embed(ready, lose_return=True)
    pages.repair_discord_empty_embed(coordinator, link, evidence)
    again = pages.repair_discord_empty_embed(coordinator, link, evidence)
    assert again["status"] == "CORRECTION_ALREADY_ATTEMPTED_READBACK_ONLY"
    assert runtime.publish_calls == ["discord"]


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
