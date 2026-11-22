"""CC-748: the manual posting desk, on a fake store and a fake private bot (no network)."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from urllib.parse import unquote

import pytest

from live_contentops import manual_desk_v1 as desk
from live_contentops import x_reply_bot_v1 as botlane

FIRST_POST = datetime(2026, 11, 23, 5, 0, tzinfo=timezone.utc)
CHAT = 123456789
LINK = "https://capitalchronicle.substack.com/p/gold-bearish-at-4050-wrong-above"
WRAP_LINK = "https://capitalchronicle.substack.com/p/weekend-market-wrap-november-22-2026"
NOTICE = ("Capital Chronicle offers analysis only, not financial advice or recommendations. "
          "Capital Chronicle may hold positions in the markets it covers.")
CALL = {"condition": "price trades into 4,050–4,080", "direction": "bearish", "market": "Gold",
        "horizon": "Entry can start until Tue 24 Nov, 4:00 PM ET. Filled positions close by Fri 4 Dec, 1:00 PM ET",
        "invalidation": "Gold plan cancelled on high at or above 4,160 before entry"}
LEAD = "Gold: armed, waiting for price to trade into 4,050–4,080."
CALL_LINE = ("We are bearish on Gold if price trades into 4,050–4,080. Gold plan cancelled on high at or above "
             "4,160 before entry. Entry can start until Tue 24 Nov, 4:00 PM ET. Filled positions close by "
             "Fri 4 Dec, 1:00 PM ET.")
PLAN_TEXT = "\n".join([
    "Macro: The US 10-year Treasury yield was 4.92% on 20 Nov and the 2-year yield was 4.63%, so markets "
    "expect the Federal Reserve to keep rates high for longer than they did a month ago.",
    "Cross-asset and contagion: Gold has moved against the dollar index over the last 60 sessions, about 0.8% "
    "for each 1% in the dollar, and the spillover measure shows it receiving shocks rather than sending them.",
    "Technical: The daily trend is down: the last close is 4% under its 20-day average and 6% under its 50-day.",
    "Scenarios: Main (55%): gold is below 4,000 at Fri 4 Dec, 1:00 PM ET. Alternative (45%): gold holds above "
    "4,160 and is above 4,050 at the exit.",
    LEAD, CALL_LINE, "Target level: 3,900.", "Registered 23 Nov 00:00 ET.", "", NOTICE, "", "Chart: TradingView"])
WRAP_TEXT = ("COMEX gold futures moved -9.54% from the previous week's close. That is -3.44 normal days. "
             "Chart: TradingView.\n\n" + WRAP_LINK + "\n\n" + NOTICE)


# ------------------------------------------------------------------ fake store

class FakeStore:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.executescript("""
            CREATE TABLE outbox_messages (message_id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL,
              destination TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING',
              created_at TEXT NOT NULL);
            CREATE TABLE platform_dispatches (dispatch_id TEXT PRIMARY KEY, message_id TEXT NOT NULL,
              platform TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', dispatched_at TEXT NOT NULL,
              public_object_id TEXT, public_object_url TEXT, public_object_url_hash TEXT);""")
        self.n = 0

    def row(self, work_item, destination, payload, *, status="DISPATCH_CONFIRMED", at=FIRST_POST,
            dispatch=True, url=None, message_id=None):
        self.n += 1
        message_id = message_id or f"m{self.n}"
        self.conn.execute("INSERT INTO outbox_messages VALUES (?,?,?,?,?,?)",
                          (message_id, work_item, destination, json.dumps(payload), status, at.isoformat()))
        if dispatch:
            self.conn.execute("INSERT INTO platform_dispatches (dispatch_id, message_id, platform, status, "
                              "dispatched_at, public_object_url) VALUES (?,?,?,?,?,?)",
                              ("d" + message_id, message_id, destination, "DISPATCH_CONFIRMED",
                               at.isoformat(), url))
        self.conn.commit()
        return message_id


def platform_payload(destination, text, output_dir, media=("cc465-zone",)):
    return {"native_payload": {"destination": destination, "text": text, "full_text": text,
                               "media_asset_ids": list(media)}, "output_dir": str(output_dir)}


@pytest.fixture
def world(tmp_path):
    store = FakeStore(tmp_path / "store.sqlite3")
    out = tmp_path / "outputs" / "plan-status-post-gold"
    (out / "media_assets").mkdir(parents=True)
    chart = out / "media_assets" / "zone.png"
    chart.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    (out / "delivery_media_manifest_v1.json").write_text(json.dumps({"assets": [
        {"media_asset_id": "cc465-zone", "absolute_local_source_path": str(chart)}]}), encoding="utf-8")
    binding = tmp_path / "control" / "x_reply_bot_binding.json"
    binding.parent.mkdir()
    binding.write_text(json.dumps({"bound_chat_id": CHAT, "update_offset": 0}), encoding="utf-8")
    return {"store": store, "out": out, "chart": chart, "binding": binding,
            "desk": tmp_path / "manual_desk", "tmp": tmp_path}


def add_plan_post(world, *, key="plan-status-post-gold", plan_id="plan_gold1", kind="setup", text=PLAN_TEXT,
                  at=FIRST_POST):
    store = world["store"]
    store.row("plan-status-posts-v1", "internal:plan-status-post", {
        "key": key, "plan_id": plan_id, "kind": kind, "instrument_title": "Gold", "lead": LEAD,
        "conditional_calls": [CALL], "text": text}, status="PUBLISHED", at=at, dispatch=False, message_id=key)
    store.row(key, "telegram", platform_payload("telegram", text, world["out"]), at=at)
    store.row(key, "x", platform_payload("x", text, world["out"]), at=at, dispatch=False, status="READY")
    return key


def confirm_page(world, *, plan_id="plan_gold1", at=None, url=LINK):
    page = "plan-analysis-" + plan_id
    world["store"].row(page, "substack", {"native_payload": {"title": "Gold: bearish at 4,050–4,080",
        "subtitle": "The original market view.", "body_markdown": "We are bearish on Gold if price trades "
        "into 4,050–4,080.\n\nThe full analysis follows."}, "output_dir": str(world["out"])},
        at=at or FIRST_POST + timedelta(minutes=5), url=url)


# --------------------------------------------------------------------- fake bot

class FakeBot:
    """CC-464's private-chat check on a fake transport. Records every call; no network."""
    private_chat = botlane.TelegramBot.private_chat

    def __init__(self, updates=(), fail_on=None):
        self.updates, self.calls, self.photos, self.fail_on = list(updates), [], [], fail_on
        self.next_id = 100

    def call(self, method, payload=None):
        self.calls.append((method, deepcopy(payload)))
        if self.fail_on and self.fail_on(method, payload):
            raise botlane.BotError("TELEGRAM_HTTP_500")
        if method == "getMe":
            return {"username": botlane.BOT_NAME}
        if method == "getWebhookInfo":
            return {"url": ""}
        if method == "getUpdates":
            return self.updates
        if method == "getChat":
            return {"id": payload["chat_id"], "type": "private"}
        self.next_id += 1
        return {"message_id": self.next_id, "date": int(FIRST_POST.timestamp())}

    def send_photo(self, chat_id, path):
        self.photos.append(Path(path).name)
        self.next_id += 1
        return {"message_id": self.next_id}

    def sent_texts(self):
        return [p["text"] for m, p in self.calls if m == "sendMessage"]


def refresh(world, now, bot=None):
    bot = bot or FakeBot()
    result = desk.refresh_desk(world["store"].path, desk_root=world["desk"], binding_path=world["binding"],
                               bot=bot, now=now)
    return result, bot


def read_packs(world):
    return json.loads((world["desk"] / "packs.json").read_text(encoding="utf-8"))["packs"]


# ------------------------------------------------------------------------ tests

def test_pack_texts_fit_lead_with_the_call_and_end_with_the_link(world):
    add_plan_post(world)
    confirm_page(world)
    result, bot = refresh(world, FIRST_POST + timedelta(minutes=6))
    assert result["status"] == "OK"
    [pack] = read_packs(world)
    assert pack["page_state"] == "LINKED" and pack["substack_url"] == LINK
    assert pack["image_path"] == str(world["chart"]) and "full analysis follows" in pack["full_text"]
    for platform in desk.HAND_PLATFORMS:
        entry = pack["platforms"][platform]
        assert entry["status"] == "READY", (platform, entry.get("cause"))
        assert entry["text"].startswith(LEAD)
        assert entry["text"].endswith("Full analysis: " + LINK)
        assert CALL_LINE in desk.thread_as_copy([entry["text"]]) or platform == "x"
        assert entry["chars"] <= desk.LIMITS[platform]
    x = pack["platforms"]["x"]
    assert len(x["parts"]) > 1 and all(len(part) <= 280 for part in x["parts"])
    assert x["parts"][0].startswith(LEAD) and "Chart: TradingView" in x["parts"][0]
    assert x["parts"][-1].endswith("Full analysis: " + LINK)
    assert CALL_LINE in desk.thread_as_copy(x["parts"])
    assert unquote(x["composer_url"].removeprefix(desk.X_INTENT)) == x["parts"][0]
    # The 1000-character YouTube post drops whole optional lines, never the call.
    youtube = pack["platforms"]["youtube"]["text"]
    assert CALL_LINE in youtube and len(youtube) <= 1000 and "Macro:" not in youtube


def test_the_public_check_withholds_copy_it_would_refuse(world):
    add_plan_post(world, text=PLAN_TEXT.replace("Target level: 3,900.", "Use 0.05 lots on the demo account."))
    confirm_page(world)
    refresh(world, FIRST_POST + timedelta(minutes=6))
    [pack] = read_packs(world)
    # The received copy is clean elsewhere; a private size line is never handed to Jim.
    statuses = {p: e["status"] for p, e in pack["platforms"].items()}
    assert set(statuses.values()) == {"WITHHELD"}
    assert all(e["cause"] == "PUBLIC_FILTER_PLAN_ANALYSIS_PRIVATE_ACCOUNT_OR_SIZE_FORBIDDEN"
               for e in pack["platforms"].values())


def test_a_pack_waits_for_its_page_then_is_released_page_pending_and_the_link_follows(world):
    add_plan_post(world)
    result, bot = refresh(world, FIRST_POST + timedelta(minutes=10))
    [pack] = read_packs(world)
    assert pack["page_state"] == "WAITING_FOR_PAGE" and not pack["released"]
    assert result["pushed"] == [] and not bot.sent_texts()
    assert "Waiting for its Substack page" in (world["desk"] / "index.html").read_text(encoding="utf-8")

    result, bot = refresh(world, FIRST_POST + timedelta(minutes=31))
    [pack] = read_packs(world)
    assert pack["page_state"] == "PAGE_PENDING" and pack["released"]
    assert [r["version_key"] for r in result["pushed"]] == [pack["pack_id"] + ":pending"]
    texts = bot.sent_texts()
    assert "Substack page pending" in texts[0]
    assert not any(LINK in t for t in texts)
    assert all(t.endswith(("markets it covers.", "Chart: TradingView")) for t in texts[-3:])
    assert "page pending" in (world["desk"] / "index.html").read_text(encoding="utf-8")

    confirm_page(world, at=FIRST_POST + timedelta(minutes=40))
    result, bot = refresh(world, FIRST_POST + timedelta(minutes=41))
    [pack] = read_packs(world)
    assert pack["page_state"] == "LINKED"
    assert [r["version_key"] for r in result["pushed"]] == [pack["pack_id"] + ":linked"]
    texts = bot.sent_texts()
    assert "now live" in texts[0] and LINK in texts[0]
    assert all(t.endswith("Full analysis: " + LINK) for t in texts[-3:])
    # Released 31 minutes after the first post; overdue 6 hours after release.
    later, _ = refresh(world, FIRST_POST + timedelta(minutes=31, hours=6))
    assert read_packs(world)[0]["state"] == "OVERDUE" and later["overdue"] == 1
    assert desk.overdue_packs(world["desk"])[0]["unposted_platforms"] == list(desk.HAND_PLATFORMS)


def test_each_pack_is_sent_once_and_never_again_after_a_restart(world):
    add_plan_post(world)
    confirm_page(world)
    now = FIRST_POST + timedelta(minutes=6)
    first, bot = refresh(world, now)
    assert first["pushed"][0]["status"] == "SENT"
    assert bot.photos == ["zone.png"]
    # Header, then the X thread's parts, then one message each for the other three.
    pack = read_packs(world)[0]
    assert len(bot.sent_texts()) == 1 + len(pack["platforms"]["x"]["parts"]) + 3
    keyboards = [p.get("reply_markup") for m, p in bot.calls if m == "sendMessage" and p.get("reply_markup")]
    x_buttons = next(k for k in keyboards if any(b.get("text") == "Open X composer" for b in k["inline_keyboard"][0]))
    assert x_buttons["inline_keyboard"][0][0]["url"].startswith(desk.X_INTENT)
    assert x_buttons["inline_keyboard"][0][1]["callback_data"] == f"dk:p:{pack['pack_id'][6:]}:x"
    assert all(len(b["callback_data"].encode()) <= 64 for k in keyboards for row in k["inline_keyboard"]
               for b in row if "callback_data" in b)
    assert all("parse_mode" not in p for m, p in bot.calls if m == "sendMessage")  # plain text, long-press copy

    # A restart (a new process, a new bot object) reads the ledger and sends nothing.
    again, bot2 = refresh(world, now + timedelta(minutes=1))
    assert again["pushed"] == [] and not bot2.sent_texts() and not bot2.photos

    # A send interrupted after its SENDING line is uncertain, and is not repeated.
    world2 = dict(world, desk=world["tmp"] / "desk2")
    failing = FakeBot(fail_on=lambda method, payload: method == "sendMessage" and len(failing.sent_texts()) > 2)
    interrupted, _ = refresh(world2, now, bot=failing)
    assert interrupted["pushed"][0]["status"] == "UNCERTAIN"
    retry, bot3 = refresh(world2, now + timedelta(minutes=1))
    assert retry["pushed"] == [] and not bot3.sent_texts()


def update_callback(update_id, data, chat=CHAT, sender=CHAT):
    return {"update_id": update_id, "callback_query": {"id": "cb" + str(update_id), "data": data,
            "from": {"id": sender}, "message": {"chat": {"type": "private", "id": chat}}}}


def update_message(update_id, text, chat=CHAT, reply_to=None):
    message = {"chat": {"type": "private", "id": chat}, "from": {"id": chat}, "text": text}
    if reply_to is not None:
        message["reply_to_message"] = {"message_id": reply_to}
    return {"update_id": update_id, "message": message}


def test_posted_tap_url_reply_and_packs_pull_through_the_one_bot_reader(world):
    add_plan_post(world)
    confirm_page(world)
    now = FIRST_POST + timedelta(minutes=6)
    _, sender = refresh(world, now)
    pack = read_packs(world)[0]
    short = pack["pack_id"][6:]
    ledger = [json.loads(l) for l in (world["desk"] / "sent.jsonl").read_text(encoding="utf-8").splitlines()]
    linkedin_message = next(r["message_id"] for r in ledger if r.get("platform") == "linkedin_company")
    updates = [
        update_callback(11, f"dk:p:{short}:x"),
        update_callback(12, f"dk:p:{short}:n", chat=987654321, sender=987654321),  # another chat: ignored
        update_message(13, "https://www.linkedin.com/feed/update/urn:li:activity:1/", reply_to=linkedin_message),
        update_message(14, "/packs"),
        update_message(15, "/packs", chat=987654321),                               # another chat: ignored
        update_message(16, "hello"),                                                # not for the desk
    ]
    bot = FakeBot(updates)
    store = object()  # desk updates never touch the operational store
    result = botlane.process_updates(store, binding_path=world["binding"], bot=bot, now=now)
    assert result["desk_updates"] == 3 and result["causes"] == {"CALLBACK_OUTSIDE_BOUND_PRIVATE_CHAT": 1}
    assert json.loads(world["binding"].read_text(encoding="utf-8"))["update_offset"] == 17
    answers = [p for m, p in bot.calls if m == "answerCallbackQuery"]
    assert answers == [{"callback_query_id": "cb11", "text": "Recorded: posted on X"}]
    assert str(CHAT) not in json.dumps(result)

    posted = [json.loads(l) for l in (world["desk"] / "posted.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(p["platform"], p["public_url"], p["piece_id"]) for p in posted] == [
        ("x", None, pack["piece_id"]),
        ("linkedin_company", "https://www.linkedin.com/feed/update/urn:li:activity:1/", pack["piece_id"])]
    assert posted[0]["posted_at_utc"] == now.isoformat()

    # The same updates read again (a stop before the offset was saved) change nothing.
    world["binding"].write_text(json.dumps({"bound_chat_id": CHAT, "update_offset": 0}), encoding="utf-8")
    botlane.process_updates(store, binding_path=world["binding"], bot=FakeBot(updates), now=now)
    assert len((world["desk"] / "posted.jsonl").read_text(encoding="utf-8").splitlines()) == 2
    assert len((world["desk"] / "inbox.jsonl").read_text(encoding="utf-8").splitlines()) == 1

    # The next desk refresh answers /packs once, with only the platforms not yet posted.
    pulled, bot = refresh(world, now + timedelta(minutes=1))
    assert [r["version_key"] for r in pulled["pulls"]] == [f"pull:14:{pack['pack_id']}"]
    texts = bot.sent_texts()
    assert "Not yet marked Posted" in texts[0]
    buttons = [b["callback_data"] for m, p in bot.calls if m == "sendMessage" and p.get("reply_markup")
               for row in p["reply_markup"]["inline_keyboard"] for b in row if "callback_data" in b]
    assert buttons == ["dk:l", f"dk:p:{short}:n", f"dk:p:{short}:y"]  # X and LinkedIn are marked Posted
    assert pack["platforms"]["substack_notes"]["text"] in texts
    page = (world["desk"] / "index.html").read_text(encoding="utf-8")
    assert "posted " in page and "urn:li:activity:1" in page
    again, bot = refresh(world, now + timedelta(minutes=2))
    assert again["pulls"] == [] and not bot.sent_texts()


def test_a_bare_link_counts_only_for_our_own_post(world):
    add_plan_post(world)
    confirm_page(world)
    now = FIRST_POST + timedelta(minutes=6)
    refresh(world, now)
    updates = [update_message(50, "https://x.com/SomeoneElse/status/1"),
               update_message(51, "https://x.com/Capitalnicle/status/2001")]
    result = botlane.process_updates(object(), binding_path=world["binding"], bot=FakeBot(updates), now=now)
    assert result["desk_updates"] == 1
    posted = [json.loads(l) for l in (world["desk"] / "posted.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(p["platform"], p["public_url"]) for p in posted] == [("x", "https://x.com/Capitalnicle/status/2001")]


def test_latest_packs_button_and_an_empty_pull(world):
    add_plan_post(world)
    confirm_page(world)
    now = FIRST_POST + timedelta(minutes=6)
    refresh(world, now)
    pack = read_packs(world)[0]
    short = pack["pack_id"][6:]
    updates = [update_callback(20 + n, f"dk:p:{short}:{code}") for n, code in enumerate("xnly")]
    updates.append(update_callback(30, "dk:l"))
    botlane.process_updates(object(), binding_path=world["binding"], bot=FakeBot(updates), now=now)
    result, bot = refresh(world, now + timedelta(minutes=1))
    assert read_packs(world)[0]["state"] == "POSTED"
    assert result["pulls"] == [{"update_id": 30, "status": "NONE_WAITING"}]
    assert bot.sent_texts() == ["No packs waiting: every recent pack is marked Posted."]


def test_wrap_and_article_packs(world):
    store = world["store"]
    wrap = "cc689-weekly-2026-11-22"
    store.row(wrap, "internal:market-wrap", {"title": "Weekend Market Wrap"}, status="EDITORIAL_INTERNAL",
              dispatch=False)
    store.row(wrap, "substack", {"output_dir": str(world["out"])}, url=WRAP_LINK)
    for destination in ("telegram", "substack_notes", "linkedin_company", "youtube"):
        store.row(wrap, destination, platform_payload(destination, WRAP_TEXT, world["out"]))
    article = "cc425-cpi-reaction-history"
    article_link = "https://capitalchronicle.substack.com/p/what-gold-did-after-each-cpi"
    store.row(article, "substack", {"native_payload": {"title": "What gold did after each CPI",
        "subtitle": "Gold rose after 7 of the last 12 CPI releases.", "body_markdown": "Gold rose after 7 of "
        "the last 12 CPI releases."}, "output_dir": str(world["out"])}, url=article_link)
    refresh(world, FIRST_POST + timedelta(minutes=1))
    packs = {p["kind"]: p for p in read_packs(world)}
    assert set(packs) == {"wrap", "article"}
    for kind, link in (("wrap", WRAP_LINK), ("article", article_link)):
        for platform, entry in packs[kind]["platforms"].items():
            assert entry["status"] == "READY", (kind, platform, entry.get("cause"))
            assert entry["text"].endswith("Full analysis: " + link)
            assert entry["text"].count(link) == 1  # the old bare link line is replaced, not repeated
            assert entry["chars"] <= desk.LIMITS[platform]
    assert packs["article"]["platforms"]["x"]["parts"][0].startswith("What gold did after each CPI")
    assert "Gold rose after 7" in packs["article"]["full_text"]


def test_superseded_plan_posts_and_unsent_pieces_make_no_pack(world):
    add_plan_post(world)
    world["store"].row("plan-status-posts-v1", "internal:plan-status-post", {
        "key": "plan-status-post-old", "plan_id": "plan_gold1", "kind": "setup", "lead": LEAD},
        status="SUPERSEDED_NOT_POSTED", dispatch=False, message_id="plan-status-post-old")
    world["store"].row("plan-status-posts-v1", "internal:plan-status-post", {
        "key": "plan-status-post-quiet", "plan_id": "plan_gold2", "kind": "update", "lead": LEAD},
        status="PUBLISHED", dispatch=False, message_id="plan-status-post-quiet")
    refresh(world, FIRST_POST + timedelta(minutes=6))
    assert [p["piece_id"] for p in read_packs(world)] == ["plan-status-post-gold"]


def test_the_store_is_opened_read_only(world):
    conn = desk.open_store_read_only(world["store"].path)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM outbox_messages")
    conn.close()


def test_a_desk_failure_never_stops_the_minute_job(world, monkeypatch, capsys):
    from scripts import plan_status_posts as entry
    from live_contentops import plan_status_posts_v1 as posts
    from live_contentops import (audience_collection_v1, call_followups_v1, daily_trend_board_v1,
                                 event_pack_v1, event_timestamp_v1, heavy_news_quotes_v1,
                                 model_invocation_usage_v1, neo_endpoint_executor_v1, plan_reader_editorial_v1,
                                 substack_daily_note_v1, x_reply_tabs_v1)
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    store = ContentOpsDurableStore(world["tmp"] / "minute" / "store.sqlite3", auto_migrate=True)
    order = []

    def stub(name):
        def run(*args, **kwargs):
            order.append(name)
            return {"status": "NO_DUE_WORK", "state": "NO_DUE_WORK", "public_submit_actions": 0}
        return run

    def broken(*args, **kwargs):
        order.append("desk")
        raise RuntimeError("desk exploded")

    monkeypatch.setattr(desk, "refresh_desk", broken)
    monkeypatch.setattr(posts, "queue_posts", lambda *a, **k: {"status": "EXPORT_STALE"})
    monkeypatch.setattr(posts, "read_export", lambda *a, **k: (_ for _ in ()).throw(ValueError("EXPORT_STALE")))
    for module, names in (
        (heavy_news_quotes_v1, ["refresh_due"]), (botlane, ["refresh_due", "observe_due"]),
        (x_reply_tabs_v1, ["refresh_due"]), (event_timestamp_v1, ["maintain_timestamps"]),
        (event_pack_v1, ["run_due_packs"]), (audience_collection_v1, ["run_collection"]),
        (model_invocation_usage_v1, ["import_native_invocations"]), (call_followups_v1, ["minute_due"]),
        (plan_reader_editorial_v1, ["run_due"]), (substack_daily_note_v1, ["run_due"]),
        (daily_trend_board_v1, ["run_due"]), (neo_endpoint_executor_v1, ["resume_stored_requests"]),
    ):
        for name in names:
            monkeypatch.setattr(module, name, stub(module.__name__.rsplit(".", 1)[-1] + "." + name))
    assert entry.main(["--publish", "--store", str(store.db_path)]) == 1  # the stale export, not the desk
    output = json.loads(capsys.readouterr().out)
    assert output["manual_desk"] == {"status": "DESK_FAILED", "cause": "RuntimeError", "public_submit_actions": 0}
    assert order.index("desk") < order.index("x_reply_bot_v1.refresh_due")
    assert "daily_trend_board_v1.run_due" in order and "substack_daily_note_v1.run_due" in order
    errors = (store.db_path.parent / "manual_desk" / "errors.jsonl").read_text(encoding="utf-8")
    assert "RuntimeError" in errors and "exploded" not in errors


def test_a_desk_fault_in_the_bot_reader_never_stops_the_reply_drafts(world, monkeypatch):
    monkeypatch.setattr(desk, "accept_update", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    bot = FakeBot([update_callback(40, "dk:p:abc:x"), update_message(41, "/packs")])
    result = botlane.process_updates(object(), binding_path=world["binding"], bot=bot, now=FIRST_POST)
    assert result["status"] == "BOUND" and result["causes"]["DESK_UPDATE_FAILED_OSError"] == 2
    assert json.loads(world["binding"].read_text(encoding="utf-8"))["update_offset"] == 42
