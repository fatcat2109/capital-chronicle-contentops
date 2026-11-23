"""CC-774: a read that keeps observing the same incomplete result is recorded once.

21 Nov 2026: the minute job read the X thread of plan-result-post-e0f557aab6350bf4877ef518d5784123
98 times, every 1-5 minutes; each read found the post and returned
"SUCCESS / NEO_THREAD_READBACK_INCOMPLETE". The observation is now handed back as it is, and the
post is read again only when the read, the reader code or the endpoint changes, or once no sooner
than 30 minutes later: two reads per read and UTC day at most.
"""
from datetime import datetime, timedelta, timezone
import json
import sqlite3

import pytest

from live_contentops import neo_endpoint_executor_v1 as neo
from live_contentops import posted_chart_readback_v1 as charts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import (
    DESTINATION, READBACK_END_STATUS, READBACK_ENDED, observed_incomplete_readback,
)
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff

WORK = "plan-result-post-cc774-fixture"
START = datetime(2026, 11, 21, 0, 42, tzinfo=timezone.utc)
OBJECT_ID = "2123916685753327793"
OBJECT_URL = "https://x.com/Capitalnicle/status/2123916685753327793"
INCOMPLETE = {"status": "SUCCESS", "content_verified": False, "reason_code": "NEO_THREAD_READBACK_INCOMPLETE",
              "public_object_id": OBJECT_ID, "public_object_url": OBJECT_URL,
              "observed_text": "Gold: the plan's result.", "public_views_text": "148 Views"}
VERIFIED = {**INCOMPLETE, "content_verified": True, "reason_code": None}
PROFILE_DOWN = {"status": "READBACK_UNAVAILABLE", "verified": False, "reason_code": "NEO_REGISTERED_PROFILE_UNAVAILABLE"}
INTENT = {"work_item_id": WORK, "plan_hash": "plan", "package_identity": WORK,
          "payload": "Gold: the plan's result.", "native_payload": {"text": "Gold: the plan's result."},
          "destination_plan": {"payload_hash": "hash", "surface": "X_POST"}}


class Clock:
    def __init__(self):
        self.now = START

    def __call__(self):
        return self.now


class StubClient:
    def initialize(self):
        return None


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
    value.create_work_item(story_id=WORK, work_item_id=WORK, title="Plan result", target_surface="MULTI_PLATFORM")
    return value


@pytest.fixture
def clock(monkeypatch):
    value = Clock()

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return value.now

    monkeypatch.setattr(neo, "datetime", FixedDateTime)
    return value


@pytest.fixture
def browser(monkeypatch):
    state = {"result": dict(INCOMPLETE), "runs": 0, "views": 148}

    def perform(self, packet):
        state["runs"] += 1
        state["views"] += 3  # A live view count differs on every read of the same post.
        result = dict(state["result"])
        if "public_views_text" in result:
            result["public_views_text"] = f"{state['views']} Views"
        return {"result": {**result, "observed_identity": packet["request"]["expected_identity"]}, "identity": {}}
    monkeypatch.setattr(neo.NeoBrowserDriver, "perform", perform)
    return state


def minute_run(store, tmp_path, clock, *, parent=False):
    """One minute-job run: a fresh standalone executor with a new invocation id."""
    options = {"automatic_destinations": {"x"}} if parent else {}
    executor = neo.EndpointNeoExecutor(store, operation_id=WORK, output_dir=tmp_path / "native-neo",
        native_invocation_id="minute-parent", allow_publish=True, identity_at_action=True,
        client=StubClient(), clock=clock, **options)
    return executor, NeoDestinationHandoff(native_executor=executor, store=store)


def read(handoff, object_id=OBJECT_ID, object_url=OBJECT_URL):
    return handoff.readback(destination="x", intent=INTENT, public_object_id=object_id, public_object_url=object_url)


def rows(store):
    values = [json.loads(r["payload"]) for r in store.list_outbox_messages(destination=DESTINATION, work_item_id=WORK)]
    requests = [v["request"] for v in values if (v.get("request") or {}).get("action") == "READBACK"]
    ends = [r for r in store.list_outbox_messages(destination=DESTINATION, work_item_id=WORK)
            if r["status"] == READBACK_END_STATUS]
    return requests, ends


def test_the_21_nov_thread_is_read_twice_a_day_and_keeps_its_observation(store, tmp_path, clock, browser):
    """98 runs a few minutes apart through the day: two reads, the observation every run."""
    returned = []
    for run in range(98):
        clock.now = START + timedelta(minutes=3 * run)
        _, handoff = minute_run(store, tmp_path, clock)
        result = read(handoff)
        returned.append(result)
    requests, ends = rows(store)
    assert browser["runs"] == 2 and len(requests) == 2
    assert not ends
    observed = sorted(datetime.fromisoformat(r["native_tool_observation"]["observed_at_utc"])
                      for r in returned)
    assert observed[-1] - observed[0] >= timedelta(minutes=30)
    for result in returned:
        assert result["reason_code"] == "NEO_THREAD_READBACK_INCOMPLETE"
        assert result["public_object_id"] == OBJECT_ID and result["status"] != READBACK_ENDED
        assert result["write_exists"] is True  # The coordinator keeps CONTENT_INCOMPLETE, never pending.
    # Between the two reads, every run is handed the first read's exact return.
    assert {r["request_sha256"] for r in returned[1:10]} == {returned[0]["request_sha256"]}


def test_the_later_try_waits_30_minutes_and_a_new_utc_day_reads_again(store, tmp_path, clock, browser):
    for minute in (0, 29):
        clock.now = START + timedelta(minutes=minute)
        read(minute_run(store, tmp_path, clock)[1])
    assert browser["runs"] == 1
    clock.now = START + timedelta(minutes=30)
    read(minute_run(store, tmp_path, clock)[1])
    assert browser["runs"] == 2
    clock.now = START + timedelta(hours=20)
    read(minute_run(store, tmp_path, clock)[1])
    assert browser["runs"] == 2
    clock.now = START + timedelta(days=1)
    read(minute_run(store, tmp_path, clock)[1])
    assert browser["runs"] == 3


def test_a_changed_post_or_reader_reads_at_once(store, tmp_path, clock, browser):
    read(minute_run(store, tmp_path, clock)[1])
    clock.now = START + timedelta(minutes=2)
    other = "2123916685753327794"
    browser["result"] = {**INCOMPLETE, "public_object_id": other, "public_object_url": OBJECT_URL[:-1] + "4"}
    read(minute_run(store, tmp_path, clock)[1], object_id=other, object_url=OBJECT_URL[:-1] + "4")
    assert browser["runs"] == 2
    clock.now = START + timedelta(minutes=4)
    browser["result"] = dict(INCOMPLETE)
    executor, handoff = minute_run(store, tmp_path, clock)
    executor.executor_revision = "repaired-reader"
    read(handoff)
    assert browser["runs"] == 3


def test_an_observation_outranks_a_later_read_that_could_not_run(store, tmp_path, clock, browser):
    """The later try hits a profile that did not load: later runs still get the observation, not an end."""
    first = read(minute_run(store, tmp_path, clock)[1])
    clock.now = START + timedelta(minutes=31)
    browser["result"] = dict(PROFILE_DOWN)
    read(minute_run(store, tmp_path, clock)[1])
    assert browser["runs"] == 2 and len(rows(store)[1]) == 1  # CC-683 ended that try once.
    for minute in (35, 50, 70):
        clock.now = START + timedelta(minutes=minute)
        result = read(minute_run(store, tmp_path, clock)[1])
        assert result["reason_code"] == "NEO_THREAD_READBACK_INCOMPLETE"
        assert result["request_sha256"] == first["request_sha256"]
        assert result["write_exists"] is True
    assert browser["runs"] == 2


def test_a_verified_read_is_not_held(store, tmp_path, clock, browser):
    browser["result"] = dict(VERIFIED)
    read(minute_run(store, tmp_path, clock)[1])
    clock.now = START + timedelta(minutes=15)
    read(minute_run(store, tmp_path, clock)[1])
    assert browser["runs"] == 2  # Unchanged: the 10-minute reuse of a verified read, then a new read.


def test_a_native_parent_keeps_its_own_protocol(store, tmp_path, clock, browser):
    executor, _ = minute_run(store, tmp_path, clock, parent=True)
    request = {"action": "READBACK", "destination": "x", "work_item_id": WORK, "request_sha256": "a" * 64}
    assert executor._repeated_incomplete_readback(request) is None


def test_only_an_observed_incomplete_read_qualifies():
    request = {"public_object_id": OBJECT_ID, "public_object_url": OBJECT_URL}
    observed = {**INCOMPLETE, "native_tool_return_sha256": "b" * 64,
                "native_tool_observation": {"observed_at_utc": START.isoformat()}}
    assert observed_incomplete_readback(request, observed)
    assert not observed_incomplete_readback(request, {**observed, "content_verified": True})
    assert not observed_incomplete_readback(request, {**observed, "content_verified": None})
    assert not observed_incomplete_readback(request, {**PROFILE_DOWN, "native_tool_return_sha256": "b" * 64})
    assert not observed_incomplete_readback(request, {k: v for k, v in observed.items()
                                                      if k != "native_tool_return_sha256"})
    # A deferred image comparison asks for the full read at once (5 Nov EIA).
    assert not observed_incomplete_readback(request, {**observed, "media_check_state": "PENDING_BINARY_COMPARISON"})


def test_a_reused_observation_keeps_its_chart_evidence_time():
    """The coordinator's evidence row of a handed-back read is the same row, not one per run."""
    digest = "c" * 64
    intent = {"native_payload": {"media_asset_ids": ["chart"]}, "media_assets": [
        {"asset_id": "chart", "modality": "tradingview_chart_snapshot", "sha256": digest}]}
    result = {"public_object_id": OBJECT_ID, "public_object_url": OBJECT_URL, "write_exists": True,
              "observed_media_sha256": [digest], "public_image_urls": ["https://pbs.twimg.com/media/a.png"],
              "native_tool_observation": {"observed_at_utc": START.isoformat()}}
    seen = charts.observe("x", intent, result, object_id=OBJECT_ID, public_url=OBJECT_URL)
    assert seen["observed_at_utc"] == START.isoformat()
    assert seen["assets"][0]["status"] == "MATCH"
    assert charts.observe("x", intent, result, object_id=OBJECT_ID, public_url=OBJECT_URL) == seen
