"""Ops Product, 9 Nov 2026 (Jim): every live plan's reasoning reaches the posts, and it reads cleanly."""
from datetime import timedelta
import json
import sys

from live_contentops import plan_status_posts_v1 as p
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_status_posts_cc306 import main_root, plan, event, write_export, NOW  # noqa: F401
from test_plan_status_publication_cc306 import fake_host, no_real_snapshot  # noqa: F401
from test_plan_status_rationale_cc353 import export_plan


def main_like_plan():
    """Main's own wording, as in the 9 Nov 09:11Z rows."""
    row = export_plan()
    row.update(
        mechanism=("every bounce since has been sold: 91.449 (6 Nov 03:00 H1) fell to 88.20; the highs gave way; "
                   "and 90.464 fell to 88.422 by 07:30Z."),
        priced="a 13% weekly fall (press, context); daily ATR 3.79.",
        driver="the Iran risk premium, a CLEAR channel for oil.",
        zone_reason="zone 90.200-90.450 (the 9 Nov 03:00-04:30 M15 highs).",
        invalidation_reason="Stop 91.600, above the 91.449 bounce high.",
        opposite_mechanism="Hot CPI widens the US-Japan rate gap.",
        why_no_open="at the 1.11781 capture; the base case is below the 65-70% bar.")
    return row


def announced(store, source, *, why=None):
    """The plan's first post, published before the why block went live (or with it)."""
    key = p._row(plan_id=source["plan_id"], symbol=source["asset_id"], to="WAITING", at_utc=NOW.isoformat(),
                 cause="WAITING", plan={})["key"]
    store.create_work_item(story_id=p.WORK_ITEM_ID, title="Plan status posts (decision 79)", target_surface="MULTI_PLATFORM",
                           work_item_id=p.WORK_ITEM_ID)
    payload = {"schema_version": p.SCHEMA, "key": key, "plan_id": source["plan_id"], "symbol": source["asset_id"],
               "state": "WAITING", "at_utc": NOW.isoformat(), "text": "old", **({"why": why} if why else {})}
    store.register_outbox_message(message_id=key, work_item_id=p.WORK_ITEM_ID, destination=p.DESTINATION,
                                  payload=json.dumps(payload), status="PUBLISHED")


def test_reasons_read_cleanly():
    lines = p._rationale(p._built_plan(main_like_plan(), state="WAITING"))
    text = "\n".join(lines)
    assert "a clear channel for oil" in text and "CLEAR" not in text
    assert "press" not in text and "context" not in text
    assert "91.449 (5 Nov 22:00 ET H1)" in text          # 6 Nov 03:00 UTC is 5 Nov 22:00 in New York
    assert "the 8 Nov 22:00-23:30 ET M15 highs" in text
    assert "Why this invalidation level: Invalidation at 91.600, above the 91.449 bounce high." in text
    assert "07:30" not in text                           # an undated UTC clock is still left out
    assert "65-70%" not in text and "capture" not in text
    assert not [line for line in lines if line.startswith("Alternative mechanism")]   # repeats the alternative
    assert all(line.endswith((".", "…")) for line in lines)


def test_new_plan_post_puts_one_reason_per_line():
    row = p._row(plan_id="plan_why", symbol="USDJPY", to="WAITING", at_utc=NOW.isoformat(), cause="WAITING",
                 plan=p._built_plan(main_like_plan(), state="WAITING"))
    post = p.compose(row, first_plan_post=True)
    assert post["format"] == 2 and "\nWhy:\n• Base case 55%" in post["text"]
    assert "\n• Mechanism: every bounce since has been sold" in post["text"]


def test_announced_plan_without_why_gets_its_reasoning_once(tmp_path, main_root):
    source = main_like_plan()
    folder = write_export(tmp_path / "export", [source], [event(source["plan_id"], "WAITING", NOW.isoformat())])
    store = ContentOpsDurableStore(tmp_path / "store.db")
    announced(store, source)
    later = NOW + timedelta(hours=3)
    first = p.queue_posts(store, folder, now=later, main_root=main_root, python=sys.executable)
    whys = [q for q in first["queued"] if q["state"] == "WHY"]
    assert len(whys) == 1 and whys[0]["key"].startswith(p.WHY_PREFIX)
    assert whys[0]["text"].startswith("USD/JPY: the reasoning behind our plan. If price trades into")
    assert "\n• Why this zone: " in whys[0]["text"]
    row = p._row_payload(store, whys[0]["key"])
    assert row["why_follow_up"] and row["format"] == 2 and row["at_utc"].startswith("2026-11-05T15:30")
    again = p.queue_posts(store, folder, now=later + timedelta(minutes=1), main_root=main_root, python=sys.executable)
    assert not [q for q in again["queued"] if q["state"] == "WHY"]
    assert [m["message_id"] for m in store.list_outbox_messages(destination=p.DESTINATION)
            if m["message_id"].startswith(p.WHY_PREFIX)] == [whys[0]["key"]]


def test_no_follow_up_once_the_reasoning_went_out_or_the_plan_ended(tmp_path, main_root):
    source = main_like_plan()
    folder = write_export(tmp_path / "export", [source], [event(source["plan_id"], "WAITING", NOW.isoformat())])
    store = ContentOpsDurableStore(tmp_path / "store.db")
    announced(store, source, why=["Mechanism: already posted."])
    assert not [q for q in p.queue_posts(store, folder, now=NOW + timedelta(hours=3), main_root=main_root,
                                         python=sys.executable)["queued"] if q["state"] == "WHY"]
    store = ContentOpsDurableStore(tmp_path / "store2.db")
    announced(store, source)
    assert not [q for q in p.queue_posts(store, folder, now=NOW + timedelta(days=2), main_root=main_root,
                                         python=sys.executable)["queued"] if q["state"] == "WHY"]


def test_follow_up_copy_fits_every_destination_and_x_carries_the_whole_reasoning(tmp_path, main_root,
                                                                                    no_real_snapshot):
    source = main_like_plan()
    folder = write_export(tmp_path / "export", [source], [event(source["plan_id"], "WAITING", NOW.isoformat())])
    store = ContentOpsDurableStore(tmp_path / "store.db")
    announced(store, source)
    queued = p.queue_posts(store, folder, now=NOW + timedelta(hours=3), main_root=main_root, python=sys.executable)
    key = [q for q in queued["queued"] if q["state"] == "WHY"][0]["key"]
    row = p._row_payload(store, key)
    payloads = p.destination_payloads(row, card_id="card")
    threads = payloads["threads"]["text"]
    assert len(threads) <= p.LIMITS["threads"] and "Why: every bounce since has been sold" in threads
    x_posts = [post["text"] for post in payloads["x"]["posts"]]
    assert all(p._x_length(text) <= p.LIMITS["x"] for text in x_posts)
    assert "Positioning:" in "\n".join(x_posts) and x_posts[-1] == p._split(row["text"])[1]
    package = p.prepare_post(store, key, root=tmp_path / "posts", host=fake_host)
    for part, plan_ in enumerate([package, *package["continuations"]]):
        work_id = plan_.get("work_item_id", key)
        parsed = p.validate_status_post_plan(store, work_id, plan_)
        for d in plan_["destinations"]:
            limit = p.LIMITS[d["destination"]] if not part else p.REST_LIMITS.get(d["destination"],
                                                                                 p.LIMITS[d["destination"]])
            assert len(d["payload"]) <= limit or d["destination"] == "x"
            intent = {"work_item_id": work_id, "plan_status_post": key, "plan_status_part": part,
                      "output_dir": plan_["output_dir"], "destination_plan": d,
                      "native_payload": parsed["payloads"][d["destination"]]}
            p.validate_status_post_intent(store, intent)
    assert p.card_article(row)["title"] == "USD/JPY: the reasoning behind our plan"
