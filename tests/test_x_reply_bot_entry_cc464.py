"""The actual minute CLI consumes private drafts before Main's export/publication."""
import importlib.util
import io
import json
from pathlib import Path
import sys

import pytest


@pytest.mark.parametrize("dry", [False, True])
def test_real_minute_entry_orders_bot_before_export_and_dry_run_calls_no_bot(tmp_path, monkeypatch, dry):
    spec = importlib.util.spec_from_file_location("cc464_minute", Path(__file__).parents[1] / "scripts/plan_status_posts.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    from live_contentops import x_reply_bot_v1 as bot
    from live_contentops import x_reply_tabs_v1 as tabs
    from live_contentops import event_timestamp_v1, event_pack_v1, plan_status_posts_v1
    order = []
    def refresh(store, **options):
        order.append("private-draft")
        assert options["binding_path"] == tmp_path / "control/x_reply_bot_binding.json"
        return {"status": "PENDING_JIM_BOT_START", "public_submit_actions": 0}
    def queue(*a, **k):
        order.append("main-export")
        return {"status": "EXPORT_STALE"}
    monkeypatch.setattr(bot, "refresh_due", refresh)
    monkeypatch.setattr(bot, "observe_due", lambda *a, **k: {"status": "OBSERVATION_NOT_DUE"})
    monkeypatch.setattr(cli, "queue_posts", queue)
    monkeypatch.setattr(tabs, "refresh_due", lambda *a, **k: {"status": "DISABLED"})
    monkeypatch.setattr(event_timestamp_v1, "maintain_timestamps", lambda: {"status": "UNCHANGED"})
    monkeypatch.setattr(event_pack_v1, "run_due_packs", lambda *a, **k: [])
    monkeypatch.setattr(plan_status_posts_v1, "record_run", lambda *a: tmp_path / "record.json")
    class Output(io.StringIO):
        def reconfigure(self, **kw):
            pass
    output = Output()
    monkeypatch.setattr(sys, "stdout", output)
    cli.main(["--store", str(tmp_path / "store.sqlite3"), "--publish", *(["--dry-run"] if dry else [])])
    value = json.loads(output.getvalue())
    assert order == (["main-export"] if dry else ["private-draft", "main-export"])
    assert ("reply_bot" not in value) if dry else value["reply_bot"]["status"] == "PENDING_JIM_BOT_START"


def test_feed_keeps_observed_reply_count_from_cdp_extraction(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location("cc464_ingestion", Path(__file__).parents[1] / "headline_ingestion/Data_Ingestion.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from live_contentops.x_list_feed_v1 import feed_row
    payload = {"legacy": {"full_text": "Gold after CPI", "id_str": "2120785000000000000",
        "created_at": "Wed Nov 11 15:00:00 +0000 2026", "reply_count": 7, "favorite_count": 2},
        "core": {"user_results": {"result": {"legacy": {"screen_name": "FirstSquawk"}}}}}
    row = module.recursive_tweet_extractor(payload)[0]
    assert row["metrics"]["replies"] == 7
    sidecar = module._tweet_sidecar_metadata(row)
    sidecar.update(headline_text=row["text"], captured_at_utc="2026-11-11T15:01:00Z")
    projected = feed_row(sidecar)
    assert projected["metrics"]["replies"] == 7 and projected["metrics_observed_at_utc"]
    del payload["legacy"]["reply_count"]
    assert "replies" not in module.recursive_tweet_extractor(payload)[0]["metrics"]
