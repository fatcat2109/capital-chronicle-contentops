"""CC-683: a read-back that cannot run ends once with its cause instead of being asked every run.

20 Nov 2026, 02:08Z-04:13Z: the minute job wrote a LinkedIn READBACK request for the gold result
post 52 times (LinkedIn had no automatic route; every run carried a new invocation id).
"""
from datetime import datetime, timedelta, timezone
import json
import sqlite3

import pytest

from live_contentops import neo_endpoint_executor_v1 as neo
from live_contentops import native_neo_executor_v1 as native
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import (
    DESTINATION, READBACK_END_STATUS, READBACK_ENDED, READBACK_NO_ROUTE, NativeNeoInputRequired,
    readback_binding, unrunnable_readback_cause,
)
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff

WORK = "plan-result-post-cc683-fixture"
START = datetime(2026, 11, 20, 2, 8, tzinfo=timezone.utc)
OBJECT_ID = "1990000000000000123"
OBJECT_URL = "https://x.com/Capitalnicle/status/1990000000000000123"


class Clock:
    def __init__(self):
        self.now = START

    def __call__(self):
        return self.now


class StubClient:
    """No network: the endpoint is up or down as the test says."""
    def __init__(self, up=True):
        self.up = up
        self.initialized = 0

    def initialize(self):
        if not self.up:
            raise neo.NeoEndpointError("OFFLINE")
        self.initialized += 1


@pytest.fixture
def store(tmp_path):
    seed = ContentOpsDurableStore(tmp_path / "seed.sqlite3")
    control = seed.get_operating_control()
    seed.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"],
                                  control_source="CONTROLLED_TEST")
    path = tmp_path / "copied.sqlite3"
    with sqlite3.connect(seed.db_path) as source, sqlite3.connect(path) as target:
        source.backup(target)
    value = ContentOpsDurableStore(path)
    value.create_work_item(story_id=WORK, work_item_id=WORK, title="Gold result", target_surface="MULTI_PLATFORM")
    return value


@pytest.fixture
def clock(monkeypatch):
    value = Clock()

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return value.now

    # The endpoint stamps its observation with datetime.now; keep it on the test clock.
    monkeypatch.setattr(neo, "datetime", FixedDateTime)
    return value


@pytest.fixture
def browser(monkeypatch):
    """The Neo page script, replaced: each read returns the configured observation."""
    state = {"result": {"status": "READBACK_UNAVAILABLE", "verified": False,
                        "reason_code": "NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND"}, "runs": 0}

    def perform(self, packet):
        state["runs"] += 1
        return {"result": {**state["result"], "observed_identity": packet["request"]["expected_identity"]},
                "identity": {}}
    monkeypatch.setattr(neo.NeoBrowserDriver, "perform", perform)
    return state


INTENT = {"work_item_id": WORK, "plan_hash": "plan", "package_identity": WORK,
          "payload": "Gold: hit its target.", "native_payload": {"text": "Gold: hit its target."},
          "destination_plan": {"payload_hash": "hash", "surface": "X_POST"}}


def minute_run(store, tmp_path, clock, client, *, routes=None, parent=False):
    """One minute-job run: a fresh standalone executor (a new invocation id), as the job builds it."""
    options = {"automatic_destinations": routes} if parent else {}
    executor = neo.EndpointNeoExecutor(store, operation_id=WORK, output_dir=tmp_path / "native-neo",
        native_invocation_id="minute-parent", allow_publish=True, identity_at_action=True,
        client=client, clock=clock, **options)
    if routes is not None and not parent:
        executor.automatic_destinations = set(routes)
    return executor, NeoDestinationHandoff(native_executor=executor, store=store)


def read(handoff):
    return handoff.readback(destination="x", intent=INTENT, public_object_id=OBJECT_ID, public_object_url=OBJECT_URL)


def neo_rows(store):
    rows = store.list_outbox_messages(destination=DESTINATION, work_item_id=WORK)
    requests = [json.loads(r["payload"])["request"] for r in rows
                if (json.loads(r["payload"]).get("request") or {}).get("action") == "READBACK"]
    ends = [json.loads(r["payload"]) for r in rows if r["status"] == READBACK_END_STATUS]
    return requests, ends


def test_unrunnable_readback_with_no_route_writes_one_request_and_one_end(store, tmp_path, clock):
    """The 20 Nov case: no automatic route for the destination, 52 minute runs."""
    hashes = set()
    for minute in range(52):
        clock.now = START + timedelta(minutes=2 * minute)
        _, handoff = minute_run(store, tmp_path, clock, StubClient(), routes={"substack_notes"})
        with pytest.raises(NativeNeoInputRequired) as waiting:
            read(handoff)
        hashes.add(waiting.value.request["request"]["request_sha256"])
    requests, ends = neo_rows(store)
    assert len(requests) == 1 and len(hashes) == 1
    assert len(ends) == 1
    assert ends[0]["result"] == {"request_sha256": requests[0]["request_sha256"], "status": READBACK_ENDED,
                                 "reason_code": READBACK_NO_ROUTE, "readback_try": 1,
                                 "next_try": "NEXT_UTC_DAY_OR_CHANGED_CAUSE"}
    # The one issued request stays the pending request a native turn could still run.
    executor, _ = minute_run(store, tmp_path, clock, StubClient(), routes={"substack_notes"})
    assert [p["request"]["request_sha256"] for p in executor.pending()] == [requests[0]["request_sha256"]]


def test_a_route_that_appears_is_a_changed_cause_and_reads_at_once(store, tmp_path, clock, browser):
    _, handoff = minute_run(store, tmp_path, clock, StubClient(), routes={"substack_notes"})
    with pytest.raises(NativeNeoInputRequired):
        read(handoff)
    clock.now += timedelta(minutes=1)
    browser["result"] = {"status": "SUCCESS", "verified": True, "content_verified": True,
                         "public_object_id": OBJECT_ID, "public_object_url": OBJECT_URL,
                         "observed_text": "Gold: hit its target."}
    _, handoff = minute_run(store, tmp_path, clock, StubClient())  # x is routed now
    result = read(handoff)
    assert browser["runs"] == 1 and result["request_sha256"] != READBACK_ENDED
    requests, ends = neo_rows(store)
    assert len(requests) == 2 and len(ends) == 1


def test_unreadable_object_is_read_twice_a_day_not_every_minute(store, tmp_path, clock, browser):
    """The 610-a-day case: the read runs and returns the same READBACK_UNAVAILABLE cause."""
    results = []
    for minute in range(0, 24 * 60 - 130, 3):  # every third minute through 20 Nov
        clock.now = START + timedelta(minutes=minute)
        _, handoff = minute_run(store, tmp_path, clock, StubClient())
        results.append(read(handoff))
    requests, ends = neo_rows(store)
    assert browser["runs"] == 2 and len(requests) == 2 and len(ends) == 2
    assert [e["result"]["readback_try"] for e in ends] == [1, 2]
    assert {e["result"]["reason_code"] for e in ends} == {"NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND"}
    second = datetime.fromisoformat(ends[1]["ended_at_utc"]) - datetime.fromisoformat(ends[0]["ended_at_utc"])
    assert second >= timedelta(minutes=30)
    assert ends[0]["result"]["next_try"].startswith("AFTER_") and ends[1]["result"]["next_try"] == "NEXT_UTC_DAY_OR_CHANGED_CAUSE"
    # Between tries the run gets the end, never a verified or absent read.
    assert all(r["verified"] is False and r["write_absent"] is False for r in results)
    assert results[1]["reason_code"] == "NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND"
    # A new UTC day may read once more.
    clock.now = datetime(2026, 11, 21, 0, 1, tzinfo=timezone.utc)
    _, handoff = minute_run(store, tmp_path, clock, StubClient())
    read(handoff)
    assert browser["runs"] == 3


def test_a_repaired_reader_is_a_changed_cause(store, tmp_path, clock, browser, monkeypatch):
    for minute in (0, 31, 40):
        clock.now = START + timedelta(minutes=minute)
        _, handoff = minute_run(store, tmp_path, clock, StubClient())
        read(handoff)
    assert browser["runs"] == 2
    executor, handoff = minute_run(store, tmp_path, clock, StubClient())
    executor.executor_revision = "repaired-reader"
    read(handoff)
    assert browser["runs"] == 3


def test_endpoint_outage_keeps_one_request_and_reads_when_the_endpoint_returns(store, tmp_path, clock, browser):
    down = StubClient(up=False)
    issued = set()
    for minute in range(10):
        clock.now = START + timedelta(minutes=minute)
        _, handoff = minute_run(store, tmp_path, clock, down)
        with pytest.raises(NativeNeoInputRequired) as waiting:
            read(handoff)
        issued.add(waiting.value.request["request"]["request_sha256"])
    requests, ends = neo_rows(store)
    assert len(issued) == 1 and len(requests) == 1 and len(ends) == 1
    assert ends[0]["result"]["reason_code"] == "NEO_ENDPOINT_UNAVAILABLE"
    clock.now += timedelta(minutes=1)
    _, handoff = minute_run(store, tmp_path, clock, StubClient(up=True))
    read(handoff)
    assert browser["runs"] == 1


def test_native_parent_reads_keep_their_pending_protocol(store, tmp_path, clock):
    """Under a native parent the parent runs reads this executor does not route: no end, as before."""
    for minute in (0, 11):
        clock.now = START + timedelta(minutes=minute)
        _, handoff = minute_run(store, tmp_path, clock, StubClient(), routes={"youtube"}, parent=True)
        with pytest.raises(NativeNeoInputRequired):
            read(handoff)
    requests, ends = neo_rows(store)
    assert len(requests) == 2 and ends == []


def test_binding_ignores_per_run_fields_and_keeps_the_object():
    base = {"action": "READBACK", "destination": "x", "public_object_id": "1", "request_sha256": "a",
            "native_invocation_id": "neo-endpoint:1", "observation_epoch": 1, "readback_transport_revision": "r1",
            "content_binding": {"artifact_manifest": [{"path": "C:\\run\\delivery_media_manifest_v1.json", "sha256": "1"}]}}
    same = {**base, "request_sha256": "b", "native_invocation_id": "neo-endpoint:2", "observation_epoch": 2,
            "readback_transport_revision": "r2",
            "content_binding": {"artifact_manifest": [{"path": "C:\\run\\delivery_media_manifest_v1.json", "sha256": "2"}]}}
    assert readback_binding(base) == readback_binding(same)
    assert readback_binding(base) != readback_binding({**base, "public_object_id": "2"})
    assert readback_binding(base) != readback_binding({**base, "latest_dispatch_attempt_at_utc": "2026-11-20T02:00:00+00:00"})


@pytest.mark.parametrize("result, cause", [
    ({"status": "READBACK_UNAVAILABLE", "reason_code": "PUBLIC_PLAN_FEED_COVERAGE_UNVERIFIED"}, "PUBLIC_PLAN_FEED_COVERAGE_UNVERIFIED"),
    ({"status": "FAILED_BEFORE_WRITE", "reason_code": "LOCAL_VALIDATION_ERROR"}, "LOCAL_VALIDATION_ERROR"),
    ({"status": "SKIPPED"}, "SKIPPED"),
    ({"status": "READBACK_COMPLETE", "target_post_absent": True}, None),
    ({"status": "READBACK_UNAVAILABLE", "public_object_id": "1", "observed_text": "x"}, None),
    ({"status": "SUCCESS", "verified": True}, None),
])
def test_only_a_read_that_observed_nothing_ends(result, cause):
    assert unrunnable_readback_cause(result) == cause


def test_publish_requests_are_untouched(store, tmp_path, clock):
    """Only READBACK requests are gated; a write keeps every existing claim rule."""
    executor, _ = minute_run(store, tmp_path, clock, StubClient())
    assert executor._ended_readback({"action": "PUBLISH", "request_sha256": "a", "work_item_id": WORK}) is None
    assert native.READBACK_TRIES_PER_DAY == 2
