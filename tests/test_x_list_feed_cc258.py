"""CC-258: the per-minute X-list capture and its private feed (local fixtures only).

No browser, network, provider or production file is touched: the ingestion module, the CDP
client and the browser bootstrap are fakes, and every path is under tmp_path.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timedelta, timezone

import pytest

from live_contentops import x_list_feed_v1 as feed

NOW = datetime(2026, 11, 5, 1, 0, tzinfo=timezone.utc)
LIST_URL = "https://x.com/i/lists/1843870469143048642"


def _post_id(moment):
    """Inverse of the X id clock, for fixtures."""
    return str((int(moment.timestamp() * 1000) - feed.X_EPOCH_MS) << 22)


def _sidecar_row(handle, text, posted, captured, *, tweet_id=None):
    tweet_id = tweet_id or _post_id(posted)
    return {"author_handle": handle, "headline_text": text, "tweet_id": tweet_id,
            "tweet_url": f"https://x.com/{handle}/status/{tweet_id}",
            "captured_at_utc": captured.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "candidate_catalyst_tags": ["macro"], "is_retweet": False}


def _write_sidecar(directory, day, rows, *, trailing=""):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"step1_headline_sidecar_{day}.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write((row if isinstance(row, str) else json.dumps(row)) + "\n")
        handle.write(trailing)
    return path


def test_post_id_clock_matches_the_post_time():
    # A real 31 Oct FirstSquawk post: created_at "Sat Oct 31 02:05:50 +0000 2026".
    assert feed.posted_utc_from_id("2116350907403452869") == datetime(
        2026, 10, 31, 2, 5, 50, 880000, tzinfo=timezone.utc)
    assert feed.posted_utc_from_id("not-an-id") is None


def test_feed_is_newest_first_deduplicated_windowed_and_line_readable(tmp_path):
    side = tmp_path / "sidecars"
    fj = NOW - timedelta(seconds=40)
    sq = NOW - timedelta(minutes=3)
    _write_sidecar(side, "2026_11_05", [
        _sidecar_row("financialjuice", "US ISM services 54.5", fj, fj + timedelta(seconds=20)),
        _sidecar_row("FirstSquawk", "Fed speaker headline", sq, sq + timedelta(seconds=50)),
        # The same post seen again later keeps its first ingest clock.
        _sidecar_row("financialjuice", "US ISM services 54.5", fj, fj + timedelta(seconds=80)),
        "{not json",
        {"author_handle": "x", "headline_text": "no id"},
    ])
    _write_sidecar(side, "2026_11_03", [
        _sidecar_row("DeItaone", "old news", NOW - timedelta(hours=30), NOW - timedelta(hours=30)),
    ])
    out = feed.build_feed(now=NOW, sidecar_dir=side, capture={"state": "CAPTURED"})
    assert [r["handle"] for r in out["rows"]] == ["financialjuice", "FirstSquawk"]
    first = out["rows"][0]
    assert first["lag_seconds"] == pytest.approx(20.0, abs=0.001)
    assert first["posted_utc"].endswith("Z") and first["url"].startswith("https://x.com/financialjuice/")
    assert out["row_count"] == 2 and out["newest_age_seconds"] == pytest.approx(40.0, abs=0.01)
    assert out["use"]["grant"] == "JIM_X_LIST_PRIVATE_MAIN_RESEARCH_USE_20261029"
    assert any("C7" in rule for rule in out["use"]["never"])
    rendered = feed.render_feed(out)
    assert json.loads(rendered)["rows"] == out["rows"]
    lines = rendered.decode("utf-8").splitlines()
    assert json.loads(lines[1].rstrip(","))["handle"] == "financialjuice"


def test_tail_reads_only_complete_appended_lines(tmp_path):
    side = tmp_path / "sidecars"
    posted = NOW - timedelta(minutes=1)
    path = _write_sidecar(side, "2026_11_05", [_sidecar_row("a", "one", posted, posted)])
    tail = feed.SidecarTail()
    assert feed.build_feed(now=NOW, sidecar_dir=side, tail=tail)["row_count"] == 1
    later = NOW - timedelta(seconds=30)
    partial = json.dumps(_sidecar_row("b", "two", later, later))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(partial[:20])
    assert feed.build_feed(now=NOW, sidecar_dir=side, tail=tail)["row_count"] == 1
    with path.open("a", encoding="utf-8") as handle:
        handle.write(partial[20:] + "\n")
    assert [r["handle"] for r in feed.build_feed(now=NOW, sidecar_dir=side, tail=tail)["rows"]] == ["b", "a"]


class FakeIngestion:
    def __init__(self, root):
        self.SIDECAR_DIR = str(root / "sidecars")

    def build_headline_sidecar_context(self):
        return {"dqr_status": "BLOCKED_FAIL_CLOSED"}

    def _utc_now_iso(self):
        return "2026-11-05T01:00:00Z"

    def _tweet_text(self, tweet):
        return tweet["text"]

    def _tweet_sidecar_metadata(self, tweet):
        return {"tweet_id": tweet["id"], "author_handle": tweet["handle"], "dedup_key": "x:" + tweet["id"],
                "tweet_url": f"https://x.com/{tweet['handle']}/status/{tweet['id']}"}

    def _tweet_timestamp(self, tweet):
        return "2026-11-05 08:00:00 GMT+7"

    def _headline_id(self, timestamp, text):
        return hashlib.sha256(f"{timestamp}\n{text}".encode()).hexdigest()[:24]

    def _sidecar_path_for_timestamp(self, timestamp):
        return os.path.join(self.SIDECAR_DIR, "step1_headline_sidecar_2026_11_05.jsonl")

    def recursive_tweet_extractor(self, payload):
        return payload["tweets"]


class FakeClient:
    payload = {"tweets": [
        {"id": _post_id(NOW - timedelta(seconds=30)), "handle": "financialjuice", "text": "US ISM services 54.5"},
        {"id": _post_id(NOW - timedelta(seconds=90)), "handle": "FirstSquawk", "text": "Fed speaker headline"},
    ]}
    href = LIST_URL

    def __init__(self, url, *, timeout_seconds):
        self.events, self.commands = [], []

    def command(self, method, params=None, *, timeout_seconds=10.0):
        self.commands.append(method)
        if method in {"Page.reload", "Page.navigate"}:
            url = "https://x.com/i/api/graphql/abc/ListLatestTweetsTimeline?variables=x"
            self.events += [
                {"method": "Network.responseReceived",
                 "params": {"requestId": "1", "response": {"url": url, "status": 200}}},
                {"method": "Network.loadingFinished", "params": {"requestId": "1"}},
            ]
        if method == "Network.getResponseBody":
            return {"body": json.dumps(self.payload), "base64Encoded": False}
        if method == "Runtime.evaluate":
            return {"result": {"value": self.href}}
        return {}

    def event(self, *, timeout_seconds):
        if self.events:
            return self.events.pop(0)
        time.sleep(min(timeout_seconds, 0.02))
        return None

    def close(self):
        pass


def _capture(tmp_path, url=LIST_URL, client=FakeClient):
    targets = lambda **_: [{"type": "page", "url": url, "webSocketDebuggerUrl": "ws://fake"}]
    return feed.MinuteCapture(module=FakeIngestion(tmp_path), client_factory=client,
                              targets_fn=targets, now_fn=lambda: NOW)


def test_minute_capture_appends_each_post_once_without_a_payload_copy(tmp_path):
    capture = _capture(tmp_path)
    first = capture.capture_once(settle_seconds=0.2)
    assert first["state"] == "CAPTURED" and first["new_rows"] == 2 and first["responses"] == 1
    again = capture.capture_once(settle_seconds=0.2)
    assert again["state"] == "CAPTURED" and again["new_rows"] == 0
    # A new runner reloads the recent keys from the files and still adds nothing twice.
    assert _capture(tmp_path).capture_once(settle_seconds=0.2)["new_rows"] == 0
    rows = [json.loads(line) for line in
            (tmp_path / "sidecars" / "step1_headline_sidecar_2026_11_05.jsonl").read_text().splitlines()]
    assert len(rows) == 2 and {r["capture_route"] for r in rows} == {feed.CAPTURE_ROUTE}
    assert all(r["raw_payload_ref"] is None and len(r["raw_payload_sha256"]) == 64 for r in rows)
    assert rows[0]["source_url_or_ref"].endswith("ListLatestTweetsTimeline")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["sidecars"]
    out = feed.build_feed(now=NOW, sidecar_dir=tmp_path / "sidecars")
    assert [r["handle"] for r in out["rows"]] == ["financialjuice", "FirstSquawk"]


def test_minute_capture_stops_at_a_login_page(tmp_path):
    login = "https://x.com/i/flow/login?redirect_after_login=%2Fi%2Flists%2F1"
    assert _capture(tmp_path, url=login).capture_once(settle_seconds=0.1)["state"] == "REAUTH_REQUIRED"

    class LoginAfterReload(FakeClient):
        href = login

    result = _capture(tmp_path, client=LoginAfterReload).capture_once(settle_seconds=0.1)
    assert result["state"] == "REAUTH_REQUIRED"


class FakeBootstrap:
    INGESTION_CDP_PORT = 9222
    STATE_READY, STATE_LAUNCHED, STATE_ALREADY_READY = "READY", "LAUNCHED", "ALREADY_READY"
    STATE_REAUTH_REQUIRED = "REAUTH_REQUIRED"

    def __init__(self, *, alive=False, owner="READY", launch="LAUNCH_FAILED"):
        self.alive, self.owner, self.launch = alive, owner, launch
        self.launches, self.session_probes = 0, 0

    def probe_cdp(self, port):
        return {"cdp_alive": self.alive}

    def ingestion_process_state(self):
        return {"state": self.owner, "detail": "fixture"}

    def ensure_ingestion_runtime(self):
        self.launches += 1
        return {"status": self.launch, "detail": "fixture"}

    def probe_ingestion_session(self):
        self.session_probes += 1
        return {"auth_state": "READY"}


def _runner(tmp_path, bootstrap, clock):
    return feed.FeedRunner(feed_path=tmp_path / "feed.json", log_path=tmp_path / "runner.log",
                           bootstrap=bootstrap, capture_factory=lambda: pytest.fail("no capture expected"),
                           clock=clock, now_fn=lambda: NOW, sidecar_dir=tmp_path / "sidecars")


def test_runner_writes_the_feed_while_the_browser_is_down_and_launches_once_per_half_hour(tmp_path):
    ticks = iter([0.0, 60.0, 1900.0])
    bootstrap = FakeBootstrap()
    runner = _runner(tmp_path, bootstrap, lambda: next(ticks))
    first = runner.iterate()
    assert first["capture"]["state"] == "BROWSER_NOT_READY" and first["feed_written"] is True
    runner.iterate()
    assert bootstrap.launches == 1
    runner.iterate()
    assert bootstrap.launches == 2
    written = json.loads((tmp_path / "feed.json").read_text(encoding="utf-8"))
    assert written["capture"]["state"] == "BROWSER_NOT_READY" and written["rows"] == []
    assert len((tmp_path / "runner.log").read_text().splitlines()) == 3


def test_runner_never_launches_over_a_foreign_port_9222_owner(tmp_path):
    bootstrap = FakeBootstrap(alive=True, owner="PORT_OWNER_UNPROVEN")
    record = _runner(tmp_path, bootstrap, lambda: 0.0).iterate()
    assert bootstrap.launches == 0 and record["capture"]["browser"] == "PORT_OWNER_UNPROVEN"


def test_runner_captures_through_a_ready_browser(tmp_path):
    bootstrap = FakeBootstrap(alive=True)
    runner = _runner(tmp_path, bootstrap, lambda: 0.0)

    class Quick:
        def __init__(self):
            self.inner = _capture(tmp_path)

        def capture_once(self):
            return self.inner.capture_once(settle_seconds=0.2)

    runner.capture_factory = Quick
    runner.iterate()
    written = json.loads((tmp_path / "feed.json").read_text(encoding="utf-8"))
    assert written["capture"]["state"] == "CAPTURED" and written["row_count"] == 2


def test_run_forever_honours_the_stop_file_and_runs_one_instance(tmp_path):
    stop, lock = tmp_path / "STOP", tmp_path / "runner.lock"
    held = feed._hold_lock(lock)
    try:
        assert feed.run_forever(stop_path=stop, lock_path=lock, runner=object())["state"] == "ALREADY_RUNNING"
    finally:
        held.close()
    stop.write_text("stop")
    assert feed.run_forever(stop_path=stop, lock_path=lock, runner=object()) == {"state": "STOPPED", "iterations": 0}
