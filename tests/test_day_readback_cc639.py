"""CC-639: isolated projection of real Nov16 rows; no live stores or network."""
from copy import deepcopy
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
    assert bot["counts_by_kind_and_status"]["delivery"]["DELIVERED"] == bot["delivered_count"]
    assert all(set(item) == {"post_id", "status", "delivered_at_utc"} for item in bot["delivered_drafts"])


def test_public_redirect_refuses_signin_or_another_platform():
    from urllib.error import HTTPError
    from urllib.request import Request
    redirect = readback._PublicRedirects("telegram")
    with pytest.raises(HTTPError):
        redirect.redirect_request(Request("https://t.me/CapitalChronicle/186?embed=1"), None, 302, "Found", {}, "https://x.com/")
