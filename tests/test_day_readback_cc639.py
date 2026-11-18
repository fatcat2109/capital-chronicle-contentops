"""CC-639: isolated projection of real Nov16 rows; no live stores or network."""
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import sqlite3

import pytest

from live_contentops import day_readback_v1 as readback

FIXTURE = Path(__file__).parent / "fixtures/cc639_day_readback_20261116.json"
NOW = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
SCHEMA = """
CREATE TABLE outbox_messages(message_id TEXT PRIMARY KEY,work_item_id TEXT,destination TEXT,payload TEXT,status TEXT,created_at TEXT);
CREATE TABLE platform_dispatches(dispatch_id TEXT PRIMARY KEY,message_id TEXT,platform TEXT,status TEXT,dispatched_at TEXT,public_object_id TEXT,public_object_url TEXT,public_object_url_hash TEXT);
CREATE TABLE readbacks(readback_id TEXT PRIMARY KEY,dispatch_id TEXT,readback_data TEXT,read_at TEXT);
CREATE TABLE reconciliations(reconciliation_id TEXT PRIMARY KEY,work_item_id TEXT,status TEXT,reconciled_at TEXT);
"""


@pytest.fixture
def recorded(tmp_path):
    data = json.loads(FIXTURE.read_bytes())
    store = tmp_path / "store.sqlite3"
    with sqlite3.connect(store) as conn:
        conn.executescript(SCHEMA)
        for table in ("outbox_messages", "platform_dispatches", "readbacks", "reconciliations"):
            for row in data[table]:
                conn.execute(f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", tuple(row.values()))
    feed = tmp_path / "published.jsonl"
    feed.write_text("".join(json.dumps(row) + "\n" for row in data["feed"]), encoding="utf-8")
    root = tmp_path / "route-1900"
    previous = root / "20261115T121550Z"
    previous.mkdir(parents=True)
    (previous / "result.json").write_text("{}", encoding="utf-8")
    run = root / "20261116T121550Z"
    run.mkdir()
    (run / "result.json").write_text(json.dumps(data["run_result"]), encoding="utf-8")
    (run / "16-readback-observation.json").write_text(json.dumps(data["digest_observation"]), encoding="utf-8")
    return data, store, feed, run


def getter_for(data, *, damage_187=False):
    """Construct page HTML from the published intent, not a claim of live HTTP."""
    texts = {}
    for row in data["outbox_messages"]:
        payload = json.loads(row["payload"])
        dispatch = next((d for d in data["platform_dispatches"] if d["message_id"] == row["message_id"]), {})
        url = dispatch.get("public_object_url")
        if url:
            texts[url] = (readback._expected(payload), payload)
    calls = []

    def get(platform, url):
        calls.append((platform, url))
        assert platform in {"substack", "substack_notes", "telegram"}
        assert "x.com" not in url and "web.telegram" not in url
        original = url.split("?", 1)[0]
        text, payload = texts.get(original, ("", {}))
        title = data["feed"][0]["title"] if original.endswith("following-the-trend-worked-unevenly") else ""
        if platform == "telegram":
            if damage_187 and original.endswith("/187"):
                # The reported defect: keep the real first line, cut the rest and its link.
                text = text.split("\n")[0] + "\nMacro: We need the rate"
            html = f'<div class="tgme_widget_message_text js-message_text">{escape(text)}</div>'
        else:
            html = f'<h1 class="post-title">{escape(title)}</h1><article>{escape(text)}</article>'
        return {"http_status": 200, "html": html}
    return get, calls


def build(recorded, **kwargs):
    data, store, feed, run = recorded
    get, calls = getter_for(data)
    report = readback.build_report(run, store_path=store, feed_path=feed, now=NOW, fetcher=get, **kwargs)
    return report, calls


def test_nov16_piece_channels_and_digest_are_consumed(recorded):
    report, calls = build(recorded)
    piece = next(p for p in report["pieces"] if p["piece_id"] == "substack:225143229")
    routes = {r["platform"]: r for r in piece["platforms"]}
    assert {p for p, r in routes.items() if r["status"] == "DISPATCH_CONFIRMED"} == {
        "substack", "telegram", "x", "threads", "facebook_page", "instagram_business", "linkedin_company", "discord"}
    assert routes["telegram"]["public_url"] == "https://t.me/CapitalChronicle/186"
    assert routes["telegram"]["public_readback"]["text_complete"] is True
    assert routes["linkedin"]["status"] == "RECONCILED_ABSENT_SAFE_TO_RETRY"
    assert routes["youtube"]["first_cause"] == "YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED"
    assert routes["x"]["public_readback"] is None
    digest = report["digest"]
    assert digest["state"] == "CONFIRMED" and digest["packet_present"]
    assert digest["public_url"] == "https://capitalchronicle.substack.com/p/capital-chronicle-daily-digest-november-9cf"
    assert (digest["recipients"], digest["opens"], digest["open_rate_percent"]) == (5, 1, 20)
    assert len(calls) == len(set(calls))
    assert report["window"]["since_utc"] == "2026-11-15T12:15:50+00:00"


def test_telegram187_cutoff_and_missing_link_use_the_stored_full_text(recorded):
    data, store, feed, run = recorded
    get, _ = getter_for(data, damage_187=True)
    report = readback.build_report(run, store_path=store, feed_path=feed, now=NOW,
        since="2026-11-16T12:15:50Z", until="2026-11-17T00:00:00Z", fetcher=get)
    problems = {r["first_cause"] for r in report["exceptions"] if r["public_url"] == "https://t.me/CapitalChronicle/187"}
    assert {"PUBLIC_TEXT_CUT_OFF", "PUBLIC_LINK_MISSING"} <= problems
    piece = next(p for p in report["pieces"] if p["piece_id"].startswith("plan-analysis-link-"))
    assert piece["platforms"][0]["public_readback"]["first_line_matches"] is True
    assert piece["platforms"][0]["store_readback"]["verified"] is True


def test_expected_missing_row_and_failure_without_dispatch_are_reported(recorded):
    _, store, _, _ = recorded
    with sqlite3.connect(store) as conn:
        message = conn.execute("SELECT message_id FROM outbox_messages WHERE destination='threads'").fetchone()[0]
        conn.execute("DELETE FROM platform_dispatches WHERE message_id=?", (message,))
        conn.execute("DELETE FROM outbox_messages WHERE message_id=?", (message,))
        conn.execute("INSERT INTO outbox_messages VALUES(?,?,?,?,?,?)", (
            "uncertain-without-dispatch", "orphan-public-piece", "x", "{}", "UNKNOWN_WRITE", "2026-11-16T11:00:00Z"))
    report, calls = build(recorded)
    assert any(e["platform"] == "threads" and e["first_cause"] == "EXPECTED_PLATFORM_ROW_MISSING" for e in report["exceptions"])
    assert any(e["message_id"] == "uncertain-without-dispatch" and e["status"] == "UNKNOWN_WRITE" for e in report["exceptions"])


def test_database_is_opened_read_only_and_no_private_payload_leaves(recorded, monkeypatch):
    _, store, feed, run = recorded
    before = sha256(store.read_bytes()).hexdigest()
    real_connect = sqlite3.connect
    opened = []

    def connect(database, **kwargs):
        assert str(database).endswith("?mode=ro") and kwargs["uri"] is True
        conn = real_connect(database, **kwargs)
        opened.append(conn)
        return conn

    monkeypatch.setattr(readback.sqlite3, "connect", connect)
    report, _ = build(recorded)
    paths = readback.write_report(run, report)
    assert sha256(store.read_bytes()).hexdigest() == before
    assert all(p.is_file() for p in paths)
    keys = re.findall(r'"([^"\\]+)"\s*:', paths[0].read_text(encoding="utf-8"))
    assert not any(readback.PRIVATE_KEY.search(k) for k in keys)
    assert "post_to_draft_minutes" not in paths[0].read_text(encoding="utf-8")
    assert all(report[k] == 0 for k in ("browser_opens", "public_writes", "model_calls"))


def test_http_failure_is_not_a_text_mismatch_and_other_destinations_continue(recorded):
    _, store, feed, run = recorded
    report = readback.build_report(run, store_path=store, feed_path=feed, now=NOW,
        fetcher=lambda *args: {"http_status": 403, "first_cause": "HTTP_403"})
    assert any(e["first_cause"] == "HTTP_403" for e in report["exceptions"])
    assert not any(e["first_cause"] in {"PUBLIC_LINK_MISSING", "PUBLIC_TEXT_MISMATCH"} for e in report["exceptions"])
    assert report["digest"]["recipients"] == 5


@pytest.mark.parametrize("url", ["https://x.com/Capitalnicle/status/1", "https://web.telegram.org/a/",
    "https://t.me/+private", "https://capitalchronicle.substack.com/sign-in", "https://evil.test/p/post",
    "https://capitalchronicle.substack.com/p/post?token=hidden"])
def test_public_fetch_never_opens_an_unapproved_url(url, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("network opener reached for a forbidden URL")
    monkeypatch.setattr(readback, "build_opener", forbidden)
    assert readback.fetch_public("substack", url)["first_cause"] == "PUBLIC_GET_NOT_ALLOWED"


def test_visible_post_body_is_required_not_metadata_or_navigation():
    html = '<h1>Exact title</h1><nav>Our full text https://capitalchronicle.substack.com/p/source</nav><article>Our full</article>'
    result = readback.check_public_text("substack", html, expected_title="Exact title",
        expected_text="Our full text https://capitalchronicle.substack.com/p/source")
    assert result["text_complete"] is False and result["links_match"] is False


def test_reply_deliveries_are_counts_and_public_post_ids_without_draft_copy(recorded):
    report, _ = build(recorded)
    bot = report["reply_bot"]
    assert bot["delivered_count"] >= 1
    assert next(r["count"] for r in bot["counts_by_kind_and_status"] if r["kind"] == "delivery"
                and r["status"] == "DELIVERED") == bot["delivered_count"]
    assert all(set(item) == {"post_id", "status", "delivered_at_utc"} for item in bot["delivered_drafts"])


def test_public_redirect_refuses_signin_or_another_platform():
    from urllib.error import HTTPError
    from urllib.request import Request
    redirect = readback._PublicRedirects("telegram")
    with pytest.raises(HTTPError):
        redirect.redirect_request(Request("https://t.me/CapitalChronicle/186?embed=1"), None, 302, "Found", {}, "https://x.com/")


def test_first_cut_fallback_is_yesterday_not_fifty_seconds_ago(tmp_path):
    run = tmp_path / "20261116T121550Z"
    run.mkdir()
    window, _ = readback.report_window(run, now=datetime(2026, 11, 16, 12, 40, tzinfo=timezone.utc))
    assert window["since_utc"] == "2026-11-15T12:15:00+00:00"
    assert window["cut_source"] == "PREVIOUS_SCHEDULED_1915_NO_PREVIOUS_RUN_RETAINED"


def test_private_data_and_private_named_causes_never_become_output_fields(recorded):
    _, store, _, run = recorded
    sentinels = ["PRIVATE-DRAFT-SENTINEL", "PRIVATE-CHAT-SENTINEL", "PRIVATE-KEY-SENTINEL"]
    with sqlite3.connect(store) as conn:
        conn.execute("INSERT INTO outbox_messages VALUES(?,?,?,?,?,?)", (
            "private-data", "private-reply", "internal:x-reply-bot-run", json.dumps({
                "chat_id": sentinels[1], "secret": sentinels[2], "draft_text": sentinels[0],
                "binding": {"phone": sentinels[1]}, "cause": "BOT_TOKEN_NOT_CONFIGURED"}),
            "BINDING_UNAVAILABLE", "2026-11-16T11:05:00Z"))
    report, _ = build(recorded)
    paths = readback.write_report(run, report)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not any(s in text for s in sentinels)
    assert {"first_cause": "BOT_TOKEN_NOT_CONFIGURED", "count": 1} in report["reply_bot"]["counts_by_first_cause"]


def test_http_runs_after_the_read_only_snapshot_is_closed(recorded, monkeypatch):
    data, store, feed, run = recorded
    real_connect = sqlite3.connect
    opened = []

    def connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        opened.append(conn)
        return conn

    getter, _ = getter_for(data)

    def fetch(platform, url):
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            opened[0].execute("SELECT 1")
        return getter(platform, url)

    monkeypatch.setattr(readback.sqlite3, "connect", connect)
    report = readback.build_report(run, store_path=store, feed_path=feed, now=NOW, fetcher=fetch)
    assert report["pieces"]


def test_http_text_comparison_accepts_a_link_label_with_the_exact_target():
    html = '<div class="tgme_widget_message_text">Our first line. <a href="https://capitalchronicle.substack.com/p/source">Read the full piece</a></div>'
    result = readback.check_public_text("telegram", html,
        expected_text="Our first line. https://capitalchronicle.substack.com/p/source")
    assert result["first_line_matches"] is True and result["links_match"] is True


@pytest.mark.parametrize("reply_complete", [True, False])
def test_telegram_reply_embed_uses_its_own_text_and_links(reply_complete):
    canonical = "https://capitalchronicle.substack.com/p/source"
    full_reply = f'Reply first line.<br>Second sentence. <a href="{canonical}">Read the analysis</a>'
    quote = "The parent post's text." if reply_complete else full_reply
    reply = full_reply if reply_complete else "Reply first line."
    html = f"""
    <div class="tgme_widget_message">
      <a class="tgme_widget_message_reply" href="https://t.me/CapitalChronicle/202">
        <div class="tgme_widget_message_text">{quote}</div>
      </a>
      <div class="tgme_widget_message_text js-message_text">{reply}</div>
    </div>
    """
    result = readback.check_public_text("telegram", html,
        expected_text=f"Reply first line.\nSecond sentence. {canonical}")
    assert result["first_line_matches"] is True
    assert result["text_complete"] is reply_complete
    assert result["links_match"] is reply_complete
    assert result["exceptions"] == ([] if reply_complete else ["PUBLIC_TEXT_CUT_OFF", "PUBLIC_LINK_MISSING"])


def test_cli_is_the_consumer_and_writes_both_files(recorded, monkeypatch, capsys):
    from scripts import run_day_readback as cli
    data, store, feed, run = recorded
    getter, _ = getter_for(data)
    real_build = readback.build_report
    monkeypatch.setattr(cli, "build_report", lambda *args, **kwargs: real_build(*args, **kwargs, fetcher=getter))
    result = cli.main(["--run-dir", str(run), "--store", str(store), "--feed", str(feed)])
    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["state"] == "READBACK_WRITTEN"
    report = json.loads((run / "day_readback.json").read_bytes())
    assert report["digest"]["recipients"] == 5
    assert "Exceptions:" in (run / "day_readback.md").read_text(encoding="utf-8")
    assert output["exceptions"] == report["exceptions"]


def test_piece_lines_use_stored_copy_and_first_dispatch_clock(recorded):
    _, store, _, run = recorded
    first_line = "USD/JPY: the entry window ended with no entry."
    with sqlite3.connect(store) as conn:
        conn.executemany("INSERT INTO outbox_messages VALUES(?,?,?,?,?,?)", [
            ("earlier-outbox", "plan-result-post-test", "x",
             json.dumps({"payload": "A different channel's first line."}),
             "DISPATCH_CONFIRMED", "2026-11-16T09:00:00Z"),
            ("first-dispatch", "plan-result-post-test", "facebook_page",
             json.dumps({"native_payload": {"text": f"\n  {first_line}\nFurther details."}}),
             "UNKNOWN_WRITE", "2026-11-16T09:01:00Z"),
            ("queued-outbox", "queued-piece", "x", json.dumps({"payload": "A queued market update."}),
             "READY", "2026-11-16T09:05:00Z"),
        ])
        conn.executemany("INSERT INTO platform_dispatches VALUES(?,?,?,?,?,?,?,?)", [
            ("later", "earlier-outbox", "x", "DISPATCH_CONFIRMED", "2026-11-16T05:20:00-05:00", None, None, None),
            ("first", "first-dispatch", "facebook_page", "UNKNOWN_WRITE", "2026-11-16T10:15:00Z", None, None, None),
        ])

    report, _ = build(recorded)
    json_path, markdown_path = readback.write_report(run, report)
    pieces = {piece["piece_id"]: piece for piece in json.loads(json_path.read_bytes())["pieces"]}
    result = pieces["plan-result-post-test"]
    assert result["first_line"] == first_line
    assert result["first_dispatch_at_utc"] == "2026-11-16T10:15:00+00:00"
    assert result["published_at_utc"] is None
    assert pieces["queued-piece"]["first_dispatch_at_utc"] is None
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    assert any(line.startswith(f"- {first_line} (16 Nov 2026 17:15 GMT+7):") for line in lines)
    assert "- A queued market update. (dispatch time unrecorded): x=READY." in lines
    assert all("Further details." not in line for line in lines)


def test_sealed_outlets_without_store_rows_keep_public_identity(recorded):
    _, store, _, _ = recorded
    with sqlite3.connect(store) as conn:
        conn.execute("DELETE FROM platform_dispatches WHERE message_id IN (SELECT message_id FROM outbox_messages WHERE work_item_id='cc536-measured-odds-2')")
        conn.execute("DELETE FROM outbox_messages WHERE work_item_id='cc536-measured-odds-2'")
    report, _ = build(recorded)
    piece = next(p for p in report["pieces"] if p["piece_id"] == "substack:225143229")
    assert piece["first_dispatch_at_utc"] is None
    assert f"- {piece['title']} (dispatch time unrecorded):" in readback.markdown(report)
    telegram = next(r for r in piece["platforms"] if r["platform"] == "telegram")
    assert telegram["status"] == "MISSING_ROW" and telegram["public_url"] == "https://t.me/CapitalChronicle/186"
    assert telegram["public_readback"]["http_status"] == 200


def test_sealed_feed_failure_still_uses_store_publications(recorded):
    _, _, feed, _ = recorded
    feed.write_bytes(feed.read_bytes().rstrip(b"\n"))
    report, _ = build(recorded)
    assert any(e["first_cause"] == "TORN_FEED_TAIL_READBACK_REQUIRED" for e in report["exceptions"])
    piece = next(p for p in report["pieces"] if p["piece_id"] == "cc536-measured-odds-2")
    assert any(r["public_url"] == "https://t.me/CapitalChronicle/186" for r in piece["platforms"])
    assert report["digest"]["recipients"] == 5


def test_native_first_cause_is_used_when_the_dispatch_has_no_readback(recorded):
    _, store, _, _ = recorded
    with sqlite3.connect(store) as conn:
        conn.execute("DELETE FROM readbacks WHERE dispatch_id IN (SELECT dispatch_id FROM platform_dispatches WHERE platform='linkedin_company')")
    report, _ = build(recorded)
    piece = next(p for p in report["pieces"] if p["piece_id"] == "substack:225143229")
    company = next(r for r in piece["platforms"] if r["platform"] == "linkedin_company")
    assert company["store_readback"] is None
    assert company["first_cause"] == "NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND"
    member = next(r for r in piece["platforms"] if r["platform"] == "linkedin")
    assert member["first_cause"] == "FIRST_CAUSE_NOT_RECORDED"


def test_hidden_full_text_does_not_mask_a_cut_off_post():
    html = '<div class="tgme_widget_message_text">First line. <span hidden>Second sentence and link. <a href="https://capitalchronicle.substack.com/p/source">Read it</a></span></div>'
    check = readback.check_public_text("telegram", html,
        expected_text="First line.\nSecond sentence and link. https://capitalchronicle.substack.com/p/source")
    assert check["first_cause"] == "PUBLIC_TEXT_CUT_OFF"
    assert check["links_match"] is False


def test_relative_public_links_match_and_bad_anchors_do_not_abort():
    html = '<article>First line. <a href="/p/source">Our source</a><a href="http://[invalid">broken</a></article>'
    result = readback.check_public_text("substack", html, expected_text="First line. https://capitalchronicle.substack.com/p/source",
        page_url="https://capitalchronicle.substack.com/p/current")
    assert result["links_match"] is True


def test_notes_use_only_the_note_body_and_its_exact_link():
    html = '<nav>Our note https://capitalchronicle.substack.com/p/source</nav><div class="comment-body">Our note.</div>'
    result = readback.check_public_text("substack_notes", html,
        expected_text="Our note. https://capitalchronicle.substack.com/p/source")
    assert result["first_line_matches"] and not result["links_match"]


@pytest.mark.parametrize("link_location", ["body", "attachment", "reply"])
def test_substack_permalink_checks_its_own_body_and_attachment(link_location):
    canonical = "https://capitalchronicle.substack.com/p/source"
    link = f'<a href="{canonical}">View the analysis</a>'
    attachment = f'<a class="postAttachment-eYV3fM" href="{canonical}">Analysis card</a>'
    html = f"""
    <div class="comment-body">Unrelated reply. {attachment}</div>
    <div class="feedPermalinkUnit-JBJrHa">
      <div class="feedCommentBody-UWho7S">
        <div class="richTextBody-dR7ynA">Read the analysis. {link if link_location == "body" else ""}</div>
      </div>
      {attachment if link_location == "attachment" else ""}
    </div>
    """
    result = readback.check_public_text("substack_notes", html, expected_text=f"Read the analysis. {canonical}")
    assert result["first_line_matches"] and result["text_complete"]
    assert result["links_match"] is (link_location != "reply")


def test_digest_link_inside_bold_markdown_matches_the_rendered_anchor():
    canonical = "https://capitalchronicle.substack.com/p/source"
    html = f'<article><strong><a href="{canonical}">Read the analysis</a></strong></article>'
    result = readback.check_public_text("substack", html, expected_text=f"**[Read the analysis]({canonical})**")
    assert result["text_complete"] and result["links_match"]
    assert result["exceptions"] == []


def test_failure_readback_is_selected_after_an_old_dispatch_clock(recorded):
    _, store, _, _ = recorded
    with sqlite3.connect(store) as conn:
        conn.execute("INSERT INTO outbox_messages VALUES(?,?,?,?,?,?)", (
            "old-message", "old-piece", "x", "{}", "UNKNOWN_WRITE", "2026-11-10T10:00:00Z"))
        conn.execute("INSERT INTO platform_dispatches VALUES(?,?,?,?,?,?,?,?)", (
            "old-dispatch", "old-message", "x", "UNKNOWN_WRITE", "2026-11-10T10:01:00Z", None, None, None))
        conn.execute("INSERT INTO readbacks VALUES(?,?,?,?)", ("new-read", "old-dispatch",
            json.dumps({"status": "UNKNOWN_WRITE", "reason_code": "EXACT_PUBLIC_OBJECT_NOT_FOUND"}), "2026-11-16T11:00:00Z"))
    report, _ = build(recorded)
    assert any(e["dispatch_id"] == "old-dispatch" and e["first_cause"] == "EXACT_PUBLIC_OBJECT_NOT_FOUND" for e in report["exceptions"])


def test_link_queries_are_checked_instead_of_matching_any_same_path():
    html = '<article>First line. <a href="https://example.com/data?series=wrong">Source</a></article>'
    result = readback.check_public_text("substack", html,
        expected_text="First line. https://example.com/data?series=correct")
    assert result["links_match"] is False


def test_internal_and_contradictory_outbox_uncertainty_are_explicit(recorded):
    _, store, _, _ = recorded
    with sqlite3.connect(store) as conn:
        conn.execute("UPDATE outbox_messages SET status='UNKNOWN_WRITE' WHERE destination='telegram' AND work_item_id='cc536-measured-odds-2'")
        conn.execute("INSERT INTO outbox_messages VALUES(?,?,?,?,?,?)", (
            "private-uncertainty", "reply-delivery", "internal:x-reply-bot-delivery", json.dumps({"cause": "SEND_TIMED_OUT"}),
            "UNKNOWN_WRITE", "2026-11-16T11:05:00Z"))
    report, _ = build(recorded)
    assert any(e["platform"] == "telegram" and e["status"] == "UNKNOWN_WRITE" for e in report["exceptions"])
    assert any(e["message_id"] == "private-uncertainty" and e["first_cause"] == "SEND_TIMED_OUT" for e in report["exceptions"])
