"""CC-283 design A: one composed BrowserOS Neo run per destination checks the account, publishes
and reads back. Controlled protocol checks only; these fixtures do not prove a browser action."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from live_contentops.destination_transport_registry_v1 import DestinationReadinessManager, READY_IDENTITY_AT_ACTION
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired, TOOL
from live_contentops.neo_destination_handoff_v1 import IDENTITIES, NeoDestinationHandoff
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1, DurablePublicationCoordinator, UNKNOWN_WRITE,
)
from test_native_neo_executor_v1 import intent

DESTINATION, SURFACE = "x", "X_POST"
OBJECT_ID, OBJECT_URL = "123", "https://x.com/Capitalnicle/status/123"


def now():
    return datetime.now(timezone.utc)


def composed_setup(tmp_path, monkeypatch, *, allow_publish=True):
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    store.create_work_item(story_id="story", work_item_id="work", title="test", target_surface="test")
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"],
                                   control_source="CONTROLLED_TEST")
    executor = NativeNeoExecutor(store, operation_id="work", output_dir=tmp_path / "requests",
                                 native_invocation_id="controlled-test", allow_publish=allow_publish,
                                 identity_at_action=True)
    runtime = CanonicalDestinationTransportRuntimeV1(neo_transport=NeoDestinationHandoff(native_executor=executor))
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda _: {"readiness_state": READY_IDENTITY_AT_ACTION})
    value = intent(DESTINATION)
    ids = coordinator._ids("work", "plan", DESTINATION)
    store.register_outbox_message(message_id=ids["message_id"], work_item_id="work", destination=DESTINATION,
                                  payload=json.dumps(value), status="READY")
    return store, executor, coordinator, ids, value


def pending_publish(coordinator, store, ids, value, executor):
    first = coordinator._dispatch_message(store.get_outbox_message(ids["message_id"]), canonical_url=value["canonical_url"])
    assert first["publish_called"] is False
    packets = [p for p in executor.pending() if p["request"]["action"] == "PUBLISH"]
    assert len(packets) == 1
    return packets[0]


def composed_response(packet, *, identity, result, dispatched=True, readback=True, surface="CODEX_NATIVE_SUBAGENT"):
    identity_at = now()
    dispatched_at = identity_at + timedelta(milliseconds=200)
    observed_at = dispatched_at + timedelta(milliseconds=400)
    tool = TOOL if surface.startswith("CODEX") else "mcp__browseros-neo__run"
    observation = {"tool_name": tool, "native_invocation_id": "controlled-test", "surface": surface,
                   "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF", "observed_at_utc": observed_at.isoformat()}
    if dispatched:
        observation["dispatched_at_utc"] = dispatched_at.isoformat()
    composed = {"identity": {**identity, "observed_at_utc": identity_at.isoformat()}}
    if readback:
        composed["readback"] = {"status": "SUCCESS", "observed_identity": IDENTITIES[DESTINATION],
            "public_object_id": OBJECT_ID, "public_object_url": OBJECT_URL,
            "observed_text": "Exact supported proposition.", "content_verified": True}
    return {"tool_request_sha256": packet["tool_request_sha256"], "tool_observation": observation,
            "result": {"request_sha256": packet["request"]["request_sha256"], **result}, "composed": composed}


MATCHED = {"authenticated": True, "observed_identity": IDENTITIES[DESTINATION]}
PUBLISHED = {"status": "SUCCESS", "observed_identity": IDENTITIES[DESTINATION],
             "public_object_id": OBJECT_ID, "public_object_url": OBJECT_URL}


@pytest.mark.parametrize("surface", ["CODEX_NATIVE_SUBAGENT", "CLAUDE_CODE_SESSION"])
def test_one_composed_run_records_identity_publish_and_readback(tmp_path, monkeypatch, surface):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    action = executor.begin(packet["request"]["request_sha256"])  # no separate identity step first
    assert action["composed_run"]["1_identity"]["expected_identity"] == IDENTITIES[DESTINATION]
    executor.submit(packet["request"]["request_sha256"],
                    composed_response(packet, identity=MATCHED, result=PUBLISHED, surface=surface))
    stored = executor._get(packet["request"]["request_sha256"], "response")["result"]
    assert stored["composed_identity"]["observed_identity"] == IDENTITIES[DESTINATION]
    # The run's readback is found by the adapter's 10-minute reuse; no further agent step is needed.
    reread = NeoDestinationHandoff(native_executor=executor).readback(
        destination=DESTINATION, intent=value, public_object_id=OBJECT_ID, public_object_url=OBJECT_URL)
    assert reread["verified"] is True
    assert [p for p in executor.pending() if not p.get("action_claimed")] == []


@pytest.mark.parametrize("identity", [
    {"authenticated": True, "observed_identity": "SomeoneElse"},   # another account
    {"authenticated": False, "observed_identity": None},           # unreadable
])
def test_identity_mismatch_stops_before_the_click_and_releases_the_claim(tmp_path, monkeypatch, identity):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    executor.begin(packet["request"]["request_sha256"])
    executor.submit(packet["request"]["request_sha256"], composed_response(
        packet, identity=identity, dispatched=False, readback=False,
        result={"status": "FAILED_BEFORE_WRITE", "definite_no_write": True, "public_write_performed": False}))
    result = NeoDestinationHandoff(native_executor=executor).publish(
        destination=DESTINATION, intent=value, authorization_context=None) if False else \
        executor._get(packet["request"]["request_sha256"], "response")["result"]
    assert result["status"] == "FAILED_BEFORE_WRITE" and result["definite_no_write"] is True
    assert result["reason_code"] == "NATIVE_NEO_COMPOSED_IDENTITY_MISMATCH"
    coordinator._dispatch_message(store.get_outbox_message(ids["message_id"]), canonical_url=value["canonical_url"])
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] != UNKNOWN_WRITE


def test_a_failure_after_the_click_stays_unknown_write(tmp_path, monkeypatch):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    executor.begin(packet["request"]["request_sha256"])
    executor.submit(packet["request"]["request_sha256"], composed_response(
        packet, identity=MATCHED, readback=False,
        result={"status": "FAILED_BEFORE_WRITE", "definite_no_write": True, "public_write_performed": False}))
    result = executor._get(packet["request"]["request_sha256"], "response")["result"]
    assert result["status"] == "UNKNOWN_WRITE" and result["definite_no_write"] is False
    assert result["reason_code"] == "NATIVE_NEO_FAILURE_AFTER_PUBLISH_CLICK"
    coordinator._dispatch_message(store.get_outbox_message(ids["message_id"]), canonical_url=value["canonical_url"])
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == UNKNOWN_WRITE


def test_the_deferred_proof_lives_only_inside_a_publishing_run(tmp_path, monkeypatch):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    manager = DestinationReadinessManager(store=store, neo_readiness_provider=executor.publication_readiness)
    row = manager.probe_surface(SURFACE)
    # Nothing was observed yet (the row stores identity_match as False); the coordinator's
    # gates accept this state by name and the executor requires the in-run observation.
    assert row["readiness_state"] == READY_IDENTITY_AT_ACTION and row["identity_match"] is False
    assert row["probe_kind"] == "NATIVE_NEO_IDENTITY_CHECKED_AT_ACTION"
    gated = DurablePublicationCoordinator(store=store, transport_runtime=coordinator.transport_runtime,
                                          readiness_manager=manager)
    first = gated._dispatch_message(store.get_outbox_message(ids["message_id"]), canonical_url=value["canonical_url"])
    assert first["publish_called"] is False and any(p["request"]["action"] == "PUBLISH" for p in executor.pending())
    # Outside a publishing operation the account must be observed first, as before.
    readonly = NativeNeoExecutor(store, operation_id="other", output_dir=tmp_path / "ro",
                                 native_invocation_id="controlled-test", identity_at_action=True)
    assert readonly.identity_at_action is False
    with pytest.raises(NativeNeoInputRequired):
        readonly.publication_readiness(SURFACE)
    packet = pending_publish(coordinator, store, ids, value, executor)
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    missing = composed_response(packet, identity=MATCHED, result=PUBLISHED)
    missing["composed"].pop("identity")
    with pytest.raises(ValueError, match="NATIVE_NEO_COMPOSED_IDENTITY_REQUIRED"):
        executor.submit(request_hash, missing)
    early = composed_response(packet, identity=MATCHED, result=PUBLISHED)
    early["composed"]["identity"]["observed_at_utc"] = (now() - timedelta(hours=1)).isoformat()  # before the claim
    with pytest.raises(ValueError, match="NATIVE_NEO_COMPOSED_IDENTITY_TIME_INVALID"):
        executor.submit(request_hash, early)
    late = composed_response(packet, identity=MATCHED, result=PUBLISHED)
    late["composed"]["identity"]["observed_at_utc"] = late["tool_observation"]["observed_at_utc"]  # after the click
    with pytest.raises(ValueError, match="NATIVE_NEO_COMPOSED_IDENTITY_TIME_INVALID"):
        executor.submit(request_hash, late)
    executor.submit(request_hash, composed_response(packet, identity=MATCHED, result=PUBLISHED))
    # The run's identity is evidence of this publish only: no other destination or operation reuses it.
    assert executor._fresh_identity_return(DESTINATION, SURFACE, IDENTITIES[DESTINATION]) is None
    other = NativeNeoExecutor(store, operation_id="another-operation", output_dir=tmp_path / "other",
                              native_invocation_id="controlled-test", allow_publish=True, identity_at_action=True)
    assert other._fresh_identity_return(DESTINATION, SURFACE, IDENTITIES[DESTINATION]) is None
