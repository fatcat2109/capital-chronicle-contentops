"""CC-331: the retained CC-330 TOUCH export reaches the existing status-post consumer.

The fixture is copied byte for byte. The separate acceptance replay uses the exact Main
branch reader; these focused regressions use the existing controlled reader and transports.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

import pytest

from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
from test_plan_status_posts_cc306 import main_root  # noqa: F401
from test_plan_status_publication_cc306 import fake_host, no_real_snapshot  # noqa: F401
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode


FOLDER = Path(__file__).parent / "fixtures" / "cc331_touch_export"
OIL = "plan_509c186b2f272a801714acef"
EUR = "plan_5eb033547e64c256929ab849"
FILL_AT = "2026-11-06T08:32:25.128000Z"
NOW = datetime(2026, 11, 6, 10, 41, tzinfo=timezone.utc)


def copied_export():
    return {"status": json.loads((FOLDER / "plan-status.public.json").read_bytes()),
            "transitions": json.loads((FOLDER / "plan-transitions.public.json").read_bytes())}


def test_copied_export_bytes_match_the_retained_main_replay():
    evidence = json.loads((Path(__file__).parent / "evidence/cc-331/revalidation-20261110.json").read_bytes())
    for name, digest in evidence["export_sha256"].items():
        assert hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() == digest


def queue(store, main_root, **kw):
    return posts.queue_posts(store, FOLDER.resolve(), main_root=main_root, python=sys.executable, now=NOW, **kw)


def test_all_five_source_rows_keep_their_original_setup_and_event_clock():
    export = copied_export()
    rows = posts.rows_from_export(export)
    events = export["transitions"]["transitions"]
    assert len(rows) == len(events) == 5
    assert {r["plan_id"] for r in rows} == {OIL, EUR}
    for source, row in zip(events, rows):
        assert row["plan_id"] == source["plan_id"]
        assert row["at_utc"] == source["at_utc"]
        assert row["source_state"] == source["status"]
        assert row["source_transition_id"] == source["transition_id"]
        post = posts.compose(row)
        if source["status"] == "TRIGGERED":
            assert post == {"status": "NOT_POSTED", "cause": "FILL_EVENT_SUPERSEDES_TRIGGER"}
        else:
            assert post["status"] == "COMPOSED"
            assert PUBLIC_NOTICE in post["text"] and CONFLICTS_NOTICE in post["text"]
            assert "view changed" not in post["text"].lower()
    fill = next(r for r in rows if r["source_state"] == "FILLED")
    assert fill["at_utc"] == FILL_AT and fill["plan_id"] == EUR
    assert "filled at Fri 6 Nov, 03:32 ET" in posts.compose(fill)["text"]
    assert posts.compose({**fill, "to": "FILLED"})["text"] == posts.compose(fill)["text"]


def test_fill_copy_uses_only_public_fields_even_when_private_fields_are_present():
    export = deepcopy(copied_export())
    forbidden = {"account_id": "private-account-331", "server": "private-server-331",
                 "ticket": "ticket-331-private", "position_id": "position-331-private",
                 "fill_price": 1.11900331, "size": 987.331, "lots": 765.331,
                 "pnl": 24680.331, "target": 97531.331}
    for plan in export["status"]["plans"]:
        plan.update(forbidden)
    for event in export["transitions"]["transitions"]:
        event.update(forbidden)
    for row in posts.rows_from_export(export):
        post = posts.compose(row)
        if post["status"] != "COMPOSED":
            continue
        text = post["text"]
        assert not re.search(r"\b(?:DEMO|account|tickets?|lots?|P&L|targets?)\b|plan_|transition_", text, re.I)
        for value in forbidden.values():
            assert str(value) not in text


def test_frozen_export_dry_run_has_no_store_writes_and_repeat_keeps_exact_bytes(tmp_path, main_root):
    store_path = tmp_path / "store.sqlite3"
    store = ContentOpsDurableStore(store_path)
    before = hashlib.sha256(store_path.read_bytes()).hexdigest()
    dry = queue(store, main_root, dry_run=True)
    assert dry["status"] == "OK" and dry["transitions_read"] == 5
    assert [(q["state"], q["at_utc"]) for q in dry["would_queue"]] == [("TRIGGERED", FILL_AT)]
    assert hashlib.sha256(store_path.read_bytes()).hexdigest() == before
    assert store.list_outbox_messages(destination=posts.DESTINATION) == []
    result = queue(store, main_root)
    assert result["queued"] == dry["would_queue"]
    key = result["queued"][0]["key"]
    original = store.get_outbox_message(key)["payload"]
    payload = json.loads(original)
    assert (payload["source_state"], payload["plan_id"], payload["at_utc"]) == ("FILLED", EUR, FILL_AT)
    assert queue(store, main_root)["queued"] == []
    assert store.get_outbox_message(key)["payload"] == original
    assert len(store.list_outbox_messages(destination=posts.DESTINATION)) == 1


def test_later_trigger_backfill_keeps_the_existing_fill_identity(tmp_path, monkeypatch):
    full = copied_export()
    fill_only = deepcopy(full)
    fill_only["transitions"]["transitions"] = [
        e for e in fill_only["transitions"]["transitions"] if e["status"] != "TRIGGERED"]
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    monkeypatch.setattr(posts, "read_export", lambda *a, **kw: fill_only)
    first = posts.queue_posts(store, FOLDER, now=NOW)
    key = first["queued"][0]["key"]
    original = store.get_outbox_message(key)["payload"]
    monkeypatch.setattr(posts, "read_export", lambda *a, **kw: full)
    again = posts.queue_posts(store, FOLDER, now=NOW)
    assert again["queued"] == [] and again["already_queued"] == [key]
    assert store.get_outbox_message(key)["payload"] == original


@pytest.mark.parametrize("prior_status", [posts.READY, "PUBLISHING", "PUBLISHED"])
def test_true_fill_retires_only_an_unsent_earlier_trigger(tmp_path, monkeypatch, prior_status):
    export = copied_export()
    rows = posts.rows_from_export(export)
    trigger = next(r for r in rows if r["source_state"] == "TRIGGERED")
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    store.create_work_item(story_id=posts.WORK_ITEM_ID, title="Plan status posts (decision 79)", target_surface="MULTI_PLATFORM",
                           work_item_id=posts.WORK_ITEM_ID)
    frozen = json.dumps({"plan_id": EUR, "state": "TRIGGERED", "at_utc": trigger["at_utc"]})
    store.register_outbox_message(message_id=trigger["key"], work_item_id=posts.WORK_ITEM_ID,
                                  destination=posts.DESTINATION, payload=frozen, status=prior_status)
    monkeypatch.setattr(posts, "read_export", lambda *a, **kw: export)
    dry = posts.queue_posts(store, FOLDER, now=NOW, dry_run=True)
    assert dry["status"] == "OK" and store.get_outbox_message(trigger["key"])["status"] == prior_status
    result = posts.queue_posts(store, FOLDER, now=NOW)
    assert [q["at_utc"] for q in result["queued"]] == ([FILL_AT] if prior_status == posts.READY else [])
    if prior_status != posts.READY:
        expected = ("FILL_CONFIRMATION_PENDING_READBACK" if prior_status == "PUBLISHING"
                    else "FILL_CONFIRMATION_ALREADY_PUBLISHED")
        assert expected in {s["cause"] for s in result["not_posted"]}
    prior = store.get_outbox_message(trigger["key"])
    assert prior["status"] == (posts.SUPERSEDED if prior_status == posts.READY else prior_status)
    assert prior["payload"] == frozen


def test_trigger_and_fill_with_the_same_clock_share_one_existing_identity(tmp_path, monkeypatch):
    export = copied_export()
    for event in export["transitions"]["transitions"]:
        if event["status"] == "TRIGGERED":
            event["at_utc"] = FILL_AT
    monkeypatch.setattr(posts, "read_export", lambda *a, **kw: export)
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = posts.queue_posts(store, FOLDER, now=NOW)
    assert [q["at_utc"] for q in result["queued"]] == [FILL_AT]
    assert posts.queue_posts(store, FOLDER, now=NOW)["queued"] == []
    assert store.list_outbox_messages(destination=posts.DESTINATION)[0]["status"] == posts.READY


def test_copied_fill_reaches_the_existing_coordinator_once(tmp_path, main_root, no_real_snapshot):
    store, transport, coordinator = _coordinator(tmp_path, runtime=FixtureTransport())
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    result = queue(store, main_root)
    key = result["queued"][0]["key"]
    outcome = posts.publish_ready(store, now=NOW, latest_states=result["latest_states"],
                                  active_recoveries=result["active_recoveries"],
                                  coordinator_for=lambda *a: coordinator, root=tmp_path / "posts", host=fake_host)
    assert outcome["posts"][0]["status"] == "PUBLISHED"
    assert sorted(transport.publish_calls) == sorted(posts.API_DESTINATIONS)
    payload = json.loads(store.get_outbox_message(key)["payload"])
    assert payload["plan_id"] == EUR and payload["at_utc"] == FILL_AT
    assert "filled at Fri 6 Nov, 03:32 ET" in payload["text"]
    assert posts.publish_ready(store, now=NOW)["posts"] == []
    assert len(transport.publish_calls) == 3
