from datetime import datetime, timedelta, timezone
import json
import sys

from live_contentops import day_readback_v1 as readback
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.plan_queue_clock_v1 import FIELD, PlanQueueClock, queue_event, read_queue_events
from test_day_readback_cc639 import recorded  # noqa: F401
from test_plan_call_cards_cc399 import call, write
from test_plan_status_export_age_cc306 import cli_module, run_cli
from test_plan_status_posts_cc306 import event, main_root  # noqa: F401

NOW = datetime(2026, 11, 20, 23, 55, tzinfo=timezone.utc)


def iso(at):
    return at.isoformat().replace("+00:00", "Z")


def parse(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def observation(store, clock):
    return PlanQueueClock(store, store.db_path.parent / posts.RUN_RECORD_FOLDER,
                          posts.record_run, clock=clock)


def test_own_outbox_clock_is_measured_after_exact_export_read(tmp_path, main_root, monkeypatch):
    from live_contentops import secret_store_v1

    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    monkeypatch.setattr(store, "_get_now_iso", lambda: iso(NOW + timedelta(seconds=34)))
    plan = call("id0000031", registered_at_utc=iso(NOW - timedelta(minutes=16)),
                time_exit_utc=iso(NOW + timedelta(hours=2)), entry_deadline_utc=iso(NOW + timedelta(hours=1)))
    transition = event(plan["plan_id"], "WAITING", plan["registered_at_utc"])
    folder = write(tmp_path / "export", [plan], [transition], generated_at_utc=iso(NOW - timedelta(seconds=11)))
    at = NOW
    record_row_failures = posts.record_row_failures

    def slow_quarantine(*args, **kwargs):
        nonlocal at
        at += timedelta(seconds=20)
        return record_row_failures(*args, **kwargs)

    monkeypatch.setattr(posts, "record_row_failures", slow_quarantine)
    monitor = observation(store, lambda: at)
    result = posts.queue_posts(store, folder, now=at, main_root=main_root, python=sys.executable, queue_clock=monitor)
    at += timedelta(seconds=60)
    monitor.finish(result)
    root = store.db_path.parent / posts.RUN_RECORD_FOLDER
    [queued] = read_queue_events(root, NOW - timedelta(seconds=1), at)
    assert queued["key"] == result["queued"][0]["key"]
    assert queued["first_seen_at_utc"] == iso(NOW)
    assert queued["first_export_at_utc"] == iso(NOW - timedelta(seconds=11))
    assert queued["source_event_at_utc"] == plan["registered_at_utc"]
    assert queued["queued_at_utc"] == store.get_outbox_message(queued["key"])["created_at"]
    assert queued["gap_seconds"] == 34 and not queued["target_missed"] and not queued["alarm"]
    [path] = root.glob("runs-*.jsonl")
    before, after = map(json.loads, path.read_text(encoding="utf-8").splitlines())
    assert before[FIELD]["stage"] == "OBSERVED" and before[FIELD]["events"][0]["key"] == queued["key"]
    assert after[FIELD]["stage"] == "COMPLETE"


def test_minute_entry_persists_queue_clock_before_followup_work(tmp_path, main_root, monkeypatch):
    from live_contentops import event_pack_v1, event_timestamp_v1, plan_queue_clock_v1, secret_store_v1

    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    queued_at = NOW + timedelta(seconds=15)
    monkeypatch.setattr(ContentOpsDurableStore, "_get_now_iso", lambda _: iso(queued_at))
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    clocks = iter((NOW, NOW, queued_at))
    monkeypatch.setattr(plan_queue_clock_v1, "PlanQueueClock",
                        lambda *args: PlanQueueClock(*args, clock=lambda: next(clocks)))
    monkeypatch.setattr(event_pack_v1, "run_due_packs", lambda *a, **k: {})
    root = store.db_path.parent / posts.RUN_RECORD_FOLDER

    def followup():
        events = read_queue_events(root, NOW - timedelta(seconds=1), queued_at)
        assert events[0]["gap_seconds"] == 15
        return {"status": "CHECKED"}

    monkeypatch.setattr(event_timestamp_v1, "maintain_timestamps", followup)
    plan = call("id0000032", registered_at_utc=iso(NOW - timedelta(minutes=1)),
                time_exit_utc=iso(NOW + timedelta(hours=2)), entry_deadline_utc=iso(NOW + timedelta(hours=1)))
    folder = write(tmp_path / "export", [plan], [event(plan["plan_id"], "WAITING", plan["registered_at_utc"])],
                   generated_at_utc=iso(NOW))
    code, result = run_cli(monkeypatch, cli_module(), store.db_path, folder, main_root, NOW)
    assert code == 0 and result["event_timestamp"]["status"] == "CHECKED"


def test_first_cause_and_one_alarm_survive_midnight_and_readback(recorded):
    _, store_path, feed, run = recorded
    store = ContentOpsDurableStore(store_path, auto_migrate=False)
    seen = datetime(2026, 11, 16, 23, 55, tzinfo=timezone.utc)
    row = {"key": "plan-status-post-late", "source_transition_id": "transition_late",
           "plan_id": "late-plan", "symbol": "EURUSD", "source_state": "FILLED",
           "to": "TRIGGERED", "at_utc": iso(seen - timedelta(minutes=30))}
    for elapsed, result in (
        (0, {"cause": "PLAN_EXPORT_STALE"}),
        (120, {"cause": "PLAN_NEVER_ANNOUNCED"}),
        (600, {"cause": "PLAN_NEVER_ANNOUNCED"}),
        (601, {"cause": "PLAN_NEVER_ANNOUNCED"}),
        (660, {"cause": "PLAN_NEVER_ANNOUNCED"}),
    ):
        at = seen + timedelta(seconds=elapsed)
        monitor = observation(store, lambda: at)
        monitor.observe([row], iso(at - timedelta(minutes=11)))
        monitor.finish(result)
    root = store_path.parent / posts.RUN_RECORD_FOLDER
    [alarm] = read_queue_events(root, seen, at)
    assert alarm["alarm"] and alarm["gap_seconds"] == 601
    assert alarm["first_cause"] == "PLAN_EXPORT_STALE" and alarm["queued_at_utc"] is None
    assert alarm["first_seen_at_utc"] == iso(seen)
    report = readback.build_report(run, store_path=store_path, feed_path=feed, since=iso(seen),
                                   until=iso(at), now=at, fetcher=None)
    [issue] = [row for row in report["decision_checks"]["issues"] if row["decision"] == "CC-732"]
    assert (issue["plan_id"], issue["state"], issue["gap_seconds"], issue["first_cause"]) == (
        "late-plan", "FILLED", 601, "PLAN_EXPORT_STALE")
    artifact = readback.write_decision_checks(run, report["decision_checks"])
    assert issue in json.loads(artifact.read_bytes())["issues"]
    assert "CC-732 · late-plan / FILLED · 601s" in readback.markdown(report).split("## Decision checks")[1]


def test_two_minute_target_and_ten_minute_alarm_use_own_clock():
    seen = {"first_seen_at_utc": iso(NOW)}
    assert not queue_event(seen, NOW + timedelta(seconds=120))["target_missed"]
    assert queue_event(seen, NOW + timedelta(seconds=121))["target_missed"]
    assert not queue_event(seen, NOW + timedelta(minutes=10))["alarm"]
    result = queue_event(seen, NOW + timedelta(minutes=10, seconds=1),
                         queued_at=iso(NOW + timedelta(minutes=10, seconds=1)))
    assert result["alarm"] and result["first_cause"] == "QUEUE_REGISTRATION_DELAY"
    earlier_queue = iso(NOW - timedelta(seconds=10))
    represented = queue_event(seen, NOW, queued_at=earlier_queue)
    assert represented["queued_at_utc"] == earlier_queue and represented["gap_seconds"] == 0


def test_november_19_retained_export_outbox_and_minute_records_show_three_delivery_delays():
    # Exact fields from Main's retained plan-transitions.public.json, the three internal
    # outbox rows and runs-20261118/19.jsonl. The old tick did not log per-row first-seen
    # clocks. Event-to-queue is an upper bound on seen-to-queue for these exact identities.
    rows = (
        ("plan-status-post-960ea79317611629d05a81761568bad4", "2026-11-19T10:25:07.855770Z",
         "2026-11-19T10:25:31.902531Z", "2026-11-19T10:27:28.853669Z", "2026-11-19T16:03:00Z"),
        ("plan-status-post-aa3bbf8562cd151747bbbfa271fd749d", "2026-11-19T09:44:07.552000Z",
         "2026-11-19T09:46:28.858456Z", "2026-11-19T10:06:49.363049Z", "2026-11-19T16:06:00Z"),
        ("plan-status-post-b85be66e77133fdfc0b7d2208296b1f8", "2026-11-18T17:14:15.642000Z",
         "2026-11-18T17:16:28.749045Z", "2026-11-18T17:23:24.821834Z", "2026-11-19T16:09:00Z"),
    )
    for key, event_at, queued_at, held_at, census_dispatch_minute in rows:
        source, queued, held, dispatched = map(parse, (event_at, queued_at, held_at, census_dispatch_minute))
        assert key.startswith("plan-status-post-")
        assert queued - source < timedelta(minutes=3)
        assert queued < held < dispatched
        assert dispatched - queued > timedelta(hours=5)
        # The held records' first cause was CARD_PARENT_NOT_CONFIRMED on all three.
