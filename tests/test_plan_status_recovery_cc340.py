"""CC-340: missed active status posts recover through the existing queue and publisher."""
# ruff: noqa: F811 -- pytest fixture imports intentionally share test parameter names.
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

import pytest

from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_status_posts_cc306 import event, main_root, plan, write_export  # noqa: F401
from test_plan_status_publication_cc306 import fake_host, no_real_snapshot  # noqa: F401
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode

NOW = datetime(2026, 11, 6, 14, 35, tzinfo=timezone.utc)
AT = "2026-11-06T13:33:46.424024Z"


def source(tmp_path, state="TRIGGERED", *, deadline="2026-11-06T15:00:00Z", invalid=4110):
    gold = plan("gold", "XAUUSD", "BEARISH", 4033.406, 4085.1955, invalid=invalid, deadline=deadline)
    gold["entry_deadline_utc"] = "2026-11-06T13:50:00Z" if state == "TRIGGERED" else deadline
    events = [event("gold", "WAITING", "2026-11-06T13:33:06.251626Z")]
    if state != "WAITING":
        events.append(event("gold", state, AT))
    return write_export(tmp_path / "export", [gold], events)


def queue(store, folder, main_root, **kwargs):
    return posts.queue_posts(store, folder, main_root=main_root, python=sys.executable, now=NOW, **kwargs)


@pytest.mark.parametrize("state", ["WAITING", "TRIGGERED"])
def test_missed_active_state_queues_once_with_true_times(tmp_path, main_root, state):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    folder = source(tmp_path, state)
    result = queue(store, folder, main_root)
    assert [q["state"] for q in result["queued"]] == [state]
    row = json.loads(store.get_outbox_message(result["queued"][0]["key"])["payload"])
    assert row["late"] and row["late_active"]
    assert row["at_utc"].startswith("2026-11-06T13:33:")
    assert row["queued_at_utc"] == "2026-11-06T14:35:00Z"
    assert "Delayed update as of Fri 6 Nov, 09:35 ET." in row["text"]
    assert "Fri 6 Nov, 08:33 ET" in row["text"]
    assert queue(store, folder, main_root)["queued"] == []
    assert len(store.list_outbox_messages(destination=posts.DESTINATION)) == 1


# CC-360: a FILLED with no TRIGGERED is a resting order's fill and posts as the zone reached (CC-306 test).
@pytest.mark.parametrize("state", ["CANCELLED", "INVALIDATED", "EXPIRED", "VIEW_CHANGED"])
def test_ended_unannounced_plan_never_recovers_an_active_post(tmp_path, main_root, state):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    assert queue(store, source(tmp_path, state), main_root)["queued"] == []


@pytest.mark.parametrize("deadline,at", [
    ("2026-11-06T14:35:00Z", AT),  # expired exactly now
    ("2026-11-06T14:34:59Z", AT),
    (None, AT),
    ("2026-11-07T15:00:00Z", "2026-11-05T14:34:59Z"),  # older than 24 h
])
def test_late_recovery_requires_validity_and_is_bounded_to_24_hours(tmp_path, main_root, deadline, at):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    gold = plan("gold", "XAUUSD", "BEARISH", 4033, 4085, invalid=4110, deadline=deadline)
    folder = write_export(tmp_path / "export", [gold], [event("gold", "TRIGGERED", at)])
    assert queue(store, folder, main_root)["queued"] == []


def test_repaired_composer_refusal_recovers_only_latest_active_state(tmp_path, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    folder = source(tmp_path, invalid=None)
    first = posts.queue_posts(store, folder, main_root=main_root, python=sys.executable,
                              now=NOW - timedelta(hours=1))
    assert first["queued"] == []
    assert {s["cause"] for s in first["not_posted"]} == {"PLAN_INVALIDATION_LEVEL_MISSING"}
    repaired = queue(store, source(tmp_path), main_root)
    assert [q["state"] for q in repaired["queued"]] == ["TRIGGERED"]


def test_replay_nfp_export_reader_failure_then_recovery_queues_gold_without_history_flood(tmp_path, monkeypatch):
    fixture = json.loads((Path(__file__).parent / "fixtures" / "cc340_nfp_rows.json").read_text(encoding="utf-8"))
    rows = fixture["rows"]
    assert any(r["to"] == "FILLED" for r in rows)
    assert max(r["at_utc"] for r in rows if r["symbol"] == "XAUUSD" and r["to"] == "TRIGGERED") == AT
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")

    def failed(*args, **kwargs):
        raise posts.PlanPostError("PLAN_EXPORT_UNREADABLE:PLAN_EXPORT_TRANSITION_INVALID")

    monkeypatch.setattr(posts, "read_transitions", failed)
    assert posts.queue_posts(store, now=NOW - timedelta(hours=1))["status"] == "EXPORT_UNREADABLE"
    assert store.list_outbox_messages(destination=posts.DESTINATION) == []
    monkeypatch.setattr(posts, "read_transitions", lambda *a, **kw: rows)
    result = posts.queue_posts(store, now=NOW)
    assert [(q["symbol"], q["state"]) for q in result["queued"]] == [("XAUUSD", "TRIGGERED")]
    assert posts.queue_posts(store, now=NOW)["queued"] == []


@pytest.mark.parametrize("state", ["WAITING", "TRIGGERED"])
def test_recovered_post_reaches_real_coordinator_once(tmp_path, main_root, state):
    store, transport, coordinator = _coordinator(tmp_path, runtime=FixtureTransport())
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    folder = source(tmp_path, state)
    result = queue(store, folder, main_root)
    key = result["queued"][0]["key"]
    outcome = posts.publish_ready(store, now=NOW, latest_states=result["latest_states"],
                                  active_recoveries=result["active_recoveries"],
                                  coordinator_for=lambda *a: coordinator, root=tmp_path / "posts", host=fake_host)
    assert outcome["posts"][0]["status"] == "PUBLISHED"
    assert sorted(transport.publish_calls) == sorted(posts.API_DESTINATIONS)
    frozen = store.get_outbox_message(key)["payload"]
    assert posts.publish_ready(store, now=NOW, active_recoveries=result["active_recoveries"])["posts"] == []
    assert len(transport.publish_calls) == 3 and store.get_outbox_message(key)["payload"] == frozen


def test_exact_24_hour_boundary_and_earlier_waiting_expiry():
    public_plan = plan("gold", "XAUUSD", "BEARISH", 4033, 4085, invalid=4110,
                       deadline="2026-11-06T15:00:00Z")
    public_plan["entry_deadline_utc"] = "2026-11-06T16:00:00Z"
    row = posts.rows_from_export({"status": {"plans": [public_plan]}, "transitions": {"transitions": [
        event("gold", "WAITING", "2026-11-05T14:35:00Z")]}})[0]
    assert row["plan"]["valid_until_utc"] == "2026-11-06T15:00:00Z"
    assert row["key"] in posts.active_recoveries([row], NOW)
    assert posts.active_recoveries([row], NOW + timedelta(microseconds=1)) == {}


def test_ambiguous_recovered_write_is_read_back_without_duplicate_dispatch(tmp_path, main_root):
    store, transport, coordinator = _coordinator(tmp_path, runtime=FixtureTransport(raise_after_write=True, ambiguous=True))
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    folder = source(tmp_path)
    result = queue(store, folder, main_root)
    options = dict(now=NOW, latest_states=result["latest_states"], active_recoveries=result["active_recoveries"],
                   coordinator_for=lambda *a: coordinator, root=tmp_path / "posts", host=fake_host)
    posts.publish_ready(store, **options)
    calls = list(transport.publish_calls)
    assert calls
    assert queue(store, folder, main_root)["queued"] == []
    posts.publish_ready(store, **options)
    assert transport.publish_calls == calls and transport.readback_calls


def test_cli_passes_recovery_context_to_the_existing_publisher(tmp_path, main_root, monkeypatch):
    import importlib.util
    import io

    spec = importlib.util.spec_from_file_location("cc340_plan_status_cli", Path(__file__).parents[1] / "scripts" / "plan_status_posts.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    store, transport, coordinator = _coordinator(tmp_path, runtime=FixtureTransport())
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    folder = source(tmp_path)
    real_queue, real_publish = cli.queue_posts, posts.publish_ready
    monkeypatch.setattr(cli, "queue_posts", lambda *a, **kw: real_queue(*a, now=NOW, **kw))
    monkeypatch.setattr(posts, "publish_ready", lambda *a, **kw: real_publish(
        *a, now=NOW, coordinator_for=lambda *a: coordinator, root=tmp_path / "posts", host=fake_host, **kw))

    class Output(io.StringIO):
        def reconfigure(self, **kw):
            pass

    output = Output()
    monkeypatch.setattr(sys, "stdout", output)
    assert cli.main(["--store", str(tmp_path / "store.sqlite3"), "--export-dir", str(folder),
                     "--main-root", str(main_root), "--publish"]) == 0
    result = json.loads(output.getvalue())
    assert result["publication"]["posts"][0]["status"] == "PUBLISHED"
    assert sorted(transport.publish_calls) == sorted(posts.API_DESTINATIONS)


@pytest.mark.parametrize("ended", [False, True])
def test_recovery_is_revalidated_before_media_or_dispatch(tmp_path, main_root, ended):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = queue(store, source(tmp_path), main_root)
    now = NOW if ended else datetime(2026, 11, 6, 15, tzinfo=timezone.utc)
    result = queue(store, source(tmp_path, "CANCELLED"), main_root) if ended else result
    outcome = posts.publish_ready(store, now=now, latest_states=result["latest_states"],
                                  active_recoveries=result["active_recoveries"])
    assert outcome["posts"][0]["status"] == posts.SUPERSEDED


def test_a_previously_stale_row_resumes_with_same_key_bytes_and_coordinator(tmp_path, main_root):
    store, transport, coordinator = _coordinator(tmp_path, runtime=FixtureTransport())
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    folder = source(tmp_path, "WAITING")
    first = posts.queue_posts(store, folder, main_root=main_root, python=sys.executable,
                              now=NOW - timedelta(hours=1))
    key = first["queued"][0]["key"]
    original = store.get_outbox_message(key)["payload"]
    assert posts.publish_ready(store, now=NOW)["posts"][0]["status"] == posts.STALE
    dry = queue(store, folder, main_root, dry_run=True)
    assert key in dry["already_queued"] and store.get_outbox_message(key)["status"] == posts.STALE
    result = queue(store, folder, main_root)
    assert result["queued"] == [] and key in result["already_queued"]
    assert store.get_outbox_message(key)["payload"] == original
    outcome = posts.publish_ready(store, now=NOW, latest_states=result["latest_states"],
                                  active_recoveries=result["active_recoveries"],
                                  coordinator_for=lambda *a: coordinator, root=tmp_path / "posts", host=fake_host)
    assert outcome["posts"][0]["status"] == "PUBLISHED"
    assert len(transport.publish_calls) == 3


def test_late_x_publish_rechecks_source_and_readback_survives_expiry(tmp_path, main_root, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    folder = source(tmp_path)
    result = queue(store, folder, main_root)
    key = result["queued"][0]["key"]
    rows = posts.read_transitions(folder, main_root=main_root, python=sys.executable)
    monkeypatch.setattr(posts, "read_transitions", lambda: rows)
    action = {"value": "PUBLISH"}

    class Executor:
        def __init__(self, *a, **kw):
            pass

        def _get(self, *a):
            return {"request": {"destination": "x", "action": action["value"]}}

        def begin(self, sha):
            return {"begun": sha}

    monkeypatch.setattr("live_contentops.native_neo_executor_v1.NativeNeoExecutor", Executor)
    assert posts.begin_x(store, key, "a" * 64, native_invocation_id="test", now=NOW) == {"begun": "a" * 64}
    later = NOW + timedelta(hours=1)
    with pytest.raises(posts.PlanPostError, match="PLAN_STATUS_X_STALE_NOT_POSTED"):
        posts.begin_x(store, key, "a" * 64, native_invocation_id="test", now=later)
    action["value"] = "READBACK"
    assert posts.begin_x(store, key, "a" * 64, native_invocation_id="test", now=later)["begun"] == "a" * 64
