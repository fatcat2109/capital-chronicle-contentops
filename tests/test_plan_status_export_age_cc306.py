"""Ops Live, 9 Nov 2026: a status run refuses a plan-status export written more than 10 minutes ago, and says so.

From 20:54 to 22:06Z on 9 Nov the export was not rewritten. Main's reader refuses only a file dated in the
future, so each minute run read a file up to 72 minutes old. Controlled fixtures only (the stub Main reader
of test_plan_status_posts_cc306); the fixture export was written at 12:29:50Z on 5 Nov.
"""
# ruff: noqa: F811 -- pytest fixture imports intentionally share test parameter names.
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys

import pytest

from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_status_posts_cc306 import export, main_root, write_export  # noqa: F401

WRITTEN = datetime(2026, 11, 5, 12, 29, 50, tzinfo=timezone.utc)


def cli_module():
    spec = importlib.util.spec_from_file_location(
        "cc306_export_age_cli", Path(__file__).parents[1] / "scripts" / "plan_status_posts.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    return cli


def run_cli(monkeypatch, cli, store_path, folder, main_root, now, *extra):
    real_queue = posts.queue_posts  # the module's own function, so a second run never wraps twice
    monkeypatch.setattr(cli, "queue_posts", lambda *a, **kw: real_queue(*a, now=now, **kw))

    class Output(io.StringIO):
        def reconfigure(self, **kw):
            pass

    output = Output()
    monkeypatch.setattr(sys, "stdout", output)
    code = cli.main(["--store", str(store_path), "--export-dir", str(folder), "--main-root", str(main_root), *extra])
    return code, json.loads(output.getvalue())


def records(store_path):
    files = sorted((store_path.parent / posts.RUN_RECORD_FOLDER).glob("runs-*.jsonl"))
    return [json.loads(line) for f in files for line in f.read_text(encoding="utf-8").splitlines()]


def test_the_limit_is_ten_minutes():
    assert posts.EXPORT_MAX_AGE_MINUTES == 10


def test_an_export_written_more_than_ten_minutes_ago_is_refused_and_queues_nothing(tmp_path, export, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = posts.queue_posts(store, export, now=WRITTEN + timedelta(minutes=10, seconds=1),
                               main_root=main_root, python=sys.executable)
    assert result["status"] == "EXPORT_STALE"
    assert result["cause"] == ("PLAN_EXPORT_STALE: written at 2026-11-05T12:29:50Z, 601 s before this run; "
                               "the limit is 10 minutes")
    assert result["export_generated_at_utc"] == "2026-11-05T12:29:50Z"
    assert result["export_age_seconds"] == 601.0 and result["max_export_age_minutes"] == 10
    assert "queued" not in result and "latest_states" not in result
    assert store.list_outbox_messages(destination=posts.DESTINATION) == []


def test_an_export_written_within_ten_minutes_is_read_as_before(tmp_path, export, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = posts.queue_posts(store, export, now=WRITTEN + timedelta(minutes=10),
                               main_root=main_root, python=sys.executable)
    assert result["status"] == "OK" and result["queued"]
    assert result["export_generated_at_utc"] == "2026-11-05T12:29:50Z"
    assert result["export_age_seconds"] == 600.0 and result["max_export_age_minutes"] == 10


def test_the_minute_run_records_a_refusal_and_posts_nothing(tmp_path, export, main_root, monkeypatch):
    cli = cli_module()
    store_path = tmp_path / "store.sqlite3"
    ContentOpsDurableStore(store_path)
    monkeypatch.setattr(posts, "publish_ready", lambda *a, **kw: pytest.fail("a stale export must post nothing"))
    code, result = run_cli(monkeypatch, cli, store_path, export, main_root, WRITTEN + timedelta(minutes=72),
                           "--publish")
    assert code == 1 and result["status"] == "EXPORT_STALE" and "publication" not in result
    [line] = records(store_path)
    assert line["status"] == "EXPORT_STALE"
    assert line["cause"].startswith("PLAN_EXPORT_STALE: written at 2026-11-05T12:29:50Z, 4320 s before this run")
    assert line["export_generated_at_utc"] == "2026-11-05T12:29:50Z" and line["export_age_seconds"] == 4320.0
    assert line["max_export_age_minutes"] == 10 and line["queued"] == 0 and line["publication"] is None
    assert result["run_record"].endswith(".jsonl")


def test_every_run_records_the_export_age_and_a_dry_run_records_nothing(tmp_path, export, main_root, monkeypatch):
    cli = cli_module()
    store_path = tmp_path / "store.sqlite3"
    ContentOpsDurableStore(store_path)
    code, result = run_cli(monkeypatch, cli, store_path, export, main_root, WRITTEN + timedelta(seconds=10),
                           "--dry-run")
    assert code == 0 and result["status"] == "OK" and records(store_path) == []
    code, result = run_cli(monkeypatch, cli, store_path, export, main_root, WRITTEN + timedelta(seconds=10))
    assert code == 0
    [line] = records(store_path)
    assert line["status"] == "OK" and line["cause"] is None
    assert line["export_age_seconds"] == 10.0 and line["queued"] == len(result["queued"]) > 0
    datetime.fromisoformat(line["at_utc"].replace("Z", "+00:00"))


def test_a_refused_unreadable_export_is_recorded_too(tmp_path, main_root, monkeypatch):
    cli = cli_module()
    store_path = tmp_path / "store.sqlite3"
    ContentOpsDurableStore(store_path)
    folder = write_export(tmp_path / "bad", [], [], tampered=True)
    code, result = run_cli(monkeypatch, cli, store_path, folder, main_root, WRITTEN)
    assert code == 1 and result["status"] == "EXPORT_UNREADABLE"
    [line] = records(store_path)
    assert line["status"] == "EXPORT_UNREADABLE" and line["cause"].startswith("PLAN_EXPORT_UNREADABLE:")


def test_the_x_route_reads_the_export_with_the_limit_and_a_stale_file_extends_nothing(tmp_path, export, main_root,
                                                                                      monkeypatch):
    monkeypatch.setattr(posts, "EXPORT_DIR", export)
    monkeypatch.setattr(posts, "MAIN_ROOT", main_root)
    fresh_now = WRITTEN + timedelta(minutes=5)
    stale_now = WRITTEN + timedelta(minutes=11)
    assert posts._current_rows(fresh_now)
    assert posts._current_rows(stale_now) is None
    # A late active post (older than 60 minutes) is never extended to 24 hours from a stale export.
    late = {"state": "WAITING", "plan_id": "plan_gold", "at_utc": "2026-11-05T11:00:00Z"}
    assert posts._x_freshness_limit(late, stale_now) == posts.FRESHNESS_MINUTES
    # A why follow-up has no freshness at all while the export is stale.
    why = {"why_follow_up": True, "plan_id": "plan_gold", "at_utc": "2026-11-05T12:35:00Z",
           "levels": {"valid_until_utc": "2026-11-06T12:45:00Z"}}
    assert posts._x_freshness_limit(why, stale_now) == 0


def test_a_broken_export_still_stops_the_x_route(tmp_path, main_root, monkeypatch):
    folder = write_export(tmp_path / "bad", [], [], tampered=True)
    monkeypatch.setattr(posts, "EXPORT_DIR", folder)
    monkeypatch.setattr(posts, "MAIN_ROOT", main_root)
    with pytest.raises(posts.PlanPostError, match="PLAN_EXPORT_UNREADABLE"):
        posts._current_rows(WRITTEN)
