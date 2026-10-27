"""Controlled protocol checks only; these fixtures do not prove a browser action."""
import json
from datetime import datetime, timezone

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import (
    NativeNeoExecutor, NativeNeoInputRequired, PENDING, TOOL, bind_native_neo_coordinator,
)
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.publication_coordinator_v1 import (
    DurablePublicationCoordinator, CanonicalDestinationTransportRuntimeV1,
    DISPATCH_CONFIRMED, RECONCILED_CONFIRMED, UNKNOWN_WRITE,
)


def setup(tmp_path, allow_publish=False):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    store.create_work_item(story_id="story", work_item_id="work", title="test", target_surface="test")
    executor = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path / "requests",
                                 native_invocation_id="controlled-test", allow_publish=allow_publish)
    return store, executor


def intent(destination="substack", **extra):
    return {"work_item_id": "work", "plan_hash": "plan", "package_identity": "pkg",
            "canonical_url": "https://capitalchronicle.substack.com/p/test",
            "payload": "Exact supported proposition.",
            "destination_plan": {"payload_hash": "hash", "surface": {
                "substack": "SUBSTACK_ARTICLE", "x": "X_POST", "youtube": "YOUTUBE_COMMUNITY_POST"}[destination]},
            **extra}


def response(executor, packet, result):
    request = packet["request"]
    executor.begin(request["request_sha256"])
    return {"tool_request_sha256": packet["tool_request_sha256"],
            "tool_observation": {"tool_name": TOOL, "native_invocation_id": "controlled-test",
                "surface": "CODEX_NATIVE_SUBAGENT", "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
                "observed_at_utc": datetime.now(timezone.utc).isoformat()},
            "result": {"request_sha256": request["request_sha256"], **result}}


def pending_readback(adapter, destination="substack", value=None):
    ids = {"substack": "123", "x": "123", "youtube": "Ugexample"}
    urls = {"substack": "https://capitalchronicle.substack.com/p/test", "x": "https://x.com/Capitalnicle/status/123",
            "youtube": "https://www.youtube.com/post/Ugexample"}
    with pytest.raises(NativeNeoInputRequired) as pending:
        adapter.readback(destination=destination, intent=value or intent(destination),
                         public_object_id=ids[destination], public_object_url=urls[destination])
    return pending.value.request, ids[destination], urls[destination]


@pytest.mark.parametrize("destination", ["substack", "x", "youtube"])
def test_exact_readback_restart_immutable_and_no_public_action(tmp_path, destination):
    store, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    packet, object_id, url = pending_readback(adapter, destination)
    observed = {"status": "SUCCESS", "observed_identity": packet["request"]["expected_identity"],
                "public_object_id": object_id, "public_object_url": url,
                "observed_text": "Exact supported proposition.", "content_verified": True}
    result = response(executor, packet, observed)
    executor.submit(packet["request"]["request_sha256"], result)
    restarted = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path,
                                   native_invocation_id="controlled-test")
    adapter = NeoDestinationHandoff(native_executor=restarted)
    actual = adapter.readback(destination=destination, intent=intent(destination), public_object_id=object_id, public_object_url=url)
    assert actual["verified"] is True
    assert store.list_platform_dispatches() == []
    with pytest.raises(ValueError, match="CONFLICT"):
        executor.submit(packet["request"]["request_sha256"], {**result, "result": {**result["result"], "observed_text": "changed"}})


def test_readback_requires_exact_text_url_media_and_thread(tmp_path):
    _, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent("x", native_payload={"posts": [{"text": "First source-bound post."}, {"text": "Second useful post."}]},
                   media_assets=[{"asset_id": "card", "sha256": "media-hash"}])
    packet, object_id, url = pending_readback(adapter, "x", value)
    result = response(executor, packet, {"status": "SUCCESS", "observed_identity": "@Capitalnicle",
        "public_object_id": object_id, "public_object_url": url, "content_verified": True,
        "observed_text": "First source-bound post. Second useful post.",
        "observed_media_sha256": ["media-hash"], "observed_thread": [
            {"public_object_id": "123", "public_object_url": url, "observed_text": "First source-bound post."},
            {"public_object_id": "124", "public_object_url": "https://x.com/Capitalnicle/status/124", "observed_text": "Second useful post."}]})
    executor.submit(packet["request"]["request_sha256"], result)
    actual = adapter.readback(destination="x", intent=value, public_object_id=object_id, public_object_url=url)
    assert actual["verified"] is True
    # Pure verification rejects content flags without exact observed text/media/order.
    bad = NeoDestinationHandoff(native_executor=lambda req: {**result["result"], "request_sha256": req["request_sha256"],
                                                            "observed_media_sha256": []})
    assert bad.readback(destination="x", intent=value, public_object_id=object_id, public_object_url=url)["verified"] is False


def test_lost_readonly_observation_resumes_in_new_turn_without_reclaiming_write(tmp_path):
    store, first = setup(tmp_path)
    packet, object_id, url = pending_readback(NeoDestinationHandoff(native_executor=first))
    request_hash = packet["request"]["request_sha256"]
    first.begin(request_hash)
    original_claim = first._get(request_hash, "started")
    restarted = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path / "resume",
                                  native_invocation_id="resumed-readonly-turn")
    assert restarted.begin(request_hash)["tool_request_sha256"] == packet["tool_request_sha256"]
    with pytest.raises(ValueError, match="ALREADY_CLAIMED"):
        restarted.begin(request_hash)
    returned = {
        "tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"tool_name": TOOL, "native_invocation_id": "resumed-readonly-turn",
            "surface": "CODEX_DESKTOP_CONVERSATION", "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
            "observed_at_utc": datetime.now(timezone.utc).isoformat()},
        "result": {"request_sha256": request_hash, "status": "SUCCESS", "observed_identity": "capitalchronicle.substack.com",
            "public_object_id": object_id, "public_object_url": url, "observed_text": "Exact supported proposition.",
            "content_verified": True},
    }
    restarted.submit(request_hash, returned)
    result = NeoDestinationHandoff(native_executor=restarted).readback(destination="substack", intent=intent(),
        public_object_id=object_id, public_object_url=url)
    assert result["verified"] is True
    assert first._get(request_hash, "started") == original_claim
    assert store.list_platform_dispatches() == []


def test_new_turn_gets_its_own_identity_probe_even_in_same_five_minute_epoch(tmp_path):
    store, first = setup(tmp_path)
    now = datetime(2026, 10, 24, 0, 1, tzinfo=timezone.utc)
    first.clock = lambda: now
    with pytest.raises(NativeNeoInputRequired) as pending:
        first.readiness("SUBSTACK_ARTICLE")
    packet = pending.value.request
    first.begin(packet["request"]["request_sha256"])
    restarted = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path / "resume",
        native_invocation_id="new-identity-turn", clock=lambda: now)
    with pytest.raises(NativeNeoInputRequired) as fresh:
        restarted.readiness("SUBSTACK_ARTICLE")
    assert fresh.value.request["request"]["request_sha256"] != packet["request"]["request_sha256"]
    assert first._get(packet["request"]["request_sha256"], "started")["native_invocation_id"] == "controlled-test"
    assert [p["request"]["request_sha256"] for p in restarted.pending()] == [fresh.value.request["request"]["request_sha256"]]
    assert store.list_platform_dispatches() == []


def test_coordinator_pending_publish_and_claimed_loss_enters_readback_only(tmp_path, monkeypatch):
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store, executor = setup(tmp_path, allow_publish=True)
    executor.operation_id = "work"
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"],
        control_source="CONTROLLED_TEST")
    adapter = NeoDestinationHandoff(native_executor=executor)
    runtime = CanonicalDestinationTransportRuntimeV1(neo_transport=adapter)
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
                                               readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"})
    value = intent()
    ids = coordinator._ids("work", "plan", "substack")
    store.register_outbox_message(message_id=ids["message_id"], work_item_id="work", destination="substack",
                                  payload=json.dumps(value), status="READY")
    message = store.get_outbox_message(ids["message_id"])
    first = coordinator._dispatch_message(message, canonical_url=value["canonical_url"])
    assert first["status"] == PENDING and first["publish_called"] is False
    assert coordinator.recover_pending()["backlog_blocking_new_publication"] is True
    packet = executor.pending()[0]
    # Controlled boundary fixture; actual identity observations are separately proven in Neo.
    monkeypatch.setattr(executor, "readiness", lambda surface: {"authenticated": True, "native_executor_bound": True})
    executor.begin(packet["request"]["request_sha256"])
    with pytest.raises(ValueError, match="ALREADY_CLAIMED"):
        executor.begin(packet["request"]["request_sha256"])
    restarted = NativeNeoExecutor(store, operation_id="work", output_dir=tmp_path / "resume",
                                  native_invocation_id="new-publish-turn", allow_publish=True)
    with pytest.raises(ValueError, match="ALREADY_CLAIMED"):
        restarted.begin(packet["request"]["request_sha256"])
    recovered = coordinator.recover_pending()
    assert recovered["publish_calls"] == 0
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == UNKNOWN_WRITE
    assert any(p["request"]["action"] == "READBACK" for p in executor.pending())


@pytest.mark.parametrize('recovery_owner', ['unbound', 'readonly', 'other-operation'])
def test_unrelated_recovery_preserves_claimed_native_write_and_late_return(tmp_path, monkeypatch, recovery_owner):
    monkeypatch.setattr('live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled', lambda: None)
    store, executor = setup(tmp_path, allow_publish=True)
    executor.operation_id = 'work'
    control = store.get_operating_control()
    store.update_operating_control(operating_mode='AUTONOMOUS_DEFAULT',
        expected_state_version=control['state_version'], control_source='CONTROLLED_TEST')
    coordinator = DurablePublicationCoordinator(store=store,
        transport_runtime=CanonicalDestinationTransportRuntimeV1(
            neo_transport=NeoDestinationHandoff(native_executor=executor)),
        readiness_provider=lambda _: {'readiness_state': 'READY_AUTHENTICATED'})
    value = intent()
    ids = coordinator._ids('work', 'plan', 'substack')
    store.register_outbox_message(message_id=ids['message_id'], work_item_id='work', destination='substack',
        payload=json.dumps(value), status='READY')
    message = store.get_outbox_message(ids['message_id'])
    assert coordinator._dispatch_message(message, canonical_url=value['canonical_url'])['status'] == PENDING
    packet = executor.pending()[0]
    monkeypatch.setattr(executor, 'readiness', lambda _: {'authenticated': True, 'native_executor_bound': True})
    executor.begin(packet['request']['request_sha256'])
    claim = executor._get(packet['request']['request_sha256'], 'started')

    foreign = None if recovery_owner == 'unbound' else NativeNeoExecutor(store,
        operation_id='another-work' if recovery_owner == 'other-operation' else 'work',
        output_dir=tmp_path/'foreign', native_invocation_id='unrelated-recovery',
        allow_publish=recovery_owner != 'readonly')
    recovery = DurablePublicationCoordinator(store=store,
        transport_runtime=CanonicalDestinationTransportRuntimeV1(
            neo_transport=NeoDestinationHandoff(native_executor=foreign)))
    outcome = recovery.recover_pending()
    assert outcome['publish_calls'] == 0
    assert store.get_platform_dispatch(ids['dispatch_id'])['status'] == PENDING
    assert executor._get(packet['request']['request_sha256'], 'started') == claim

    executor.submit(packet['request']['request_sha256'], {
        'tool_request_sha256': packet['tool_request_sha256'],
        'tool_observation': {'tool_name': TOOL, 'native_invocation_id': executor.native_invocation_id,
            'surface': 'CODEX_NATIVE_SUBAGENT', 'observation_source': 'CONTROLLED_TEST_NOT_BROWSER_PROOF',
            'observed_at_utc': datetime.now(timezone.utc).isoformat()},
        'result': {'request_sha256': packet['request']['request_sha256'], 'status': 'SUCCESS',
            'observed_identity': 'capitalchronicle.substack.com', 'public_object_id': '123',
            'public_object_url': value['canonical_url']}})
    resumed = coordinator.recover_pending()
    assert store.get_platform_dispatch(ids['dispatch_id'])['public_object_id'] == '123'
    assert any(p['request']['action'] == 'READBACK' for p in executor.pending())
    assert resumed['publish_calls'] == 0  # Consumes the saved return; no second native action.


def test_existing_dispatch_readback_stays_in_coordinator_without_write(tmp_path):
    store, executor = setup(tmp_path)
    coordinator, bound = bind_native_neo_coordinator(store, operation_id="same-op", output_dir=tmp_path,
                                                    native_invocation_id="controlled-test")
    value = intent()
    ids = coordinator._ids("work", "plan", "substack")
    store.register_outbox_message(message_id=ids["message_id"], work_item_id="work", destination="substack",
                                  payload=json.dumps(value), status=DISPATCH_CONFIRMED)
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"], platform="substack",
        status=DISPATCH_CONFIRMED, public_object_id="123", public_object_url=value["canonical_url"])
    first = coordinator.readback_existing_dispatch(ids["dispatch_id"])
    assert first["publish_called"] is False and first["reconciliation_status"] != RECONCILED_CONFIRMED
    packet = bound.pending()[0]
    bound.submit(packet["request"]["request_sha256"], response(bound, packet, {
        "status": "SUCCESS", "observed_identity": "capitalchronicle.substack.com", "public_object_id": "123",
        "public_object_url": value["canonical_url"], "observed_text": value["payload"], "content_verified": True}))
    second = coordinator.readback_existing_dispatch(ids["dispatch_id"])
    assert second["reconciliation_status"] == RECONCILED_CONFIRMED
    assert second["public_write_performed"] is False
    assert len(store.list_platform_dispatches()) == 1


def test_readonly_publish_and_unclaimed_or_wrong_return_fail_closed(tmp_path):
    _, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent()
    auth = {"schema_version": "contentops.canonical_machine_authorization.v1", "operating_mode": "AUTONOMOUS_DEFAULT",
            "destination": "substack", "dispatch_attempt_identity": "attempt", "work_item_id": "work", "payload_hash": "hash"}
    assert adapter.publish(destination="substack", intent=value, authorization_context=auth)["definite_no_write"] is True
    packet, _, _ = pending_readback(adapter)
    with pytest.raises(ValueError, match="BINDING"):
        executor.submit(packet["request"]["request_sha256"], {})
