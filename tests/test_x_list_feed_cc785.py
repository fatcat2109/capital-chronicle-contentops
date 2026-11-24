"""CC-785: the X-list feed keeps its capture lag low (Jim, 24 Nov 2026: 7.6 minutes is far too late).

Local fakes only: no browser, no CDP port, no X request and no production file. The page and
browser clients, the CDP HTTP endpoint and the bootstrap are fakes; every path is under tmp_path.
"""
import hashlib
import json
import os
import socket
import subprocess
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote, urlsplit

import pytest
from websocket import WebSocketTimeoutException

from live_contentops import ingestion_bootstrap_v1 as bootstrap_module
from live_contentops import x_list_feed_v1 as feed

NOW = datetime(2026, 11, 23, 13, 50, tzinfo=timezone.utc)  # a Monday, in market hours
LIST_URL = "https://x.com/i/lists/1843870469143048642"
LOGIN_URL = "https://x.com/i/flow/login?redirect_after_login=%2Fi%2Flists%2F1"
TIMELINE = "https://x.com/i/api/graphql/abc/ListLatestTweetsTimeline?variables=x"


def _post_id(moment):
    return str((int(moment.timestamp() * 1000) - feed.X_EPOCH_MS) << 22)


def _tweet(seconds_before, handle="financialjuice", text=None):
    moment = NOW - timedelta(seconds=seconds_before)
    return {"id": _post_id(moment), "handle": handle, "text": text or f"{handle} post {seconds_before}"}


class FakeIngestion:
    def __init__(self, root):
        self.SIDECAR_DIR = str(root / "sidecars")

    def build_headline_sidecar_context(self):
        return {"dqr_status": "BLOCKED_FAIL_CLOSED"}

    def _utc_now_iso(self):
        return "2026-11-23T13:50:00Z"

    def _tweet_text(self, tweet):
        return tweet["text"]

    def _tweet_sidecar_metadata(self, tweet):
        return {"tweet_id": tweet["id"], "author_handle": tweet["handle"], "dedup_key": "x:" + tweet["id"],
                "tweet_url": f"https://x.com/{tweet['handle']}/status/{tweet['id']}"}

    def _tweet_timestamp(self, tweet):
        return "2026-11-23 20:50:00 GMT+7"

    def _headline_id(self, timestamp, text):
        return hashlib.sha256(f"{timestamp}\n{text}".encode()).hexdigest()[:24]

    def _sidecar_path_for_timestamp(self, timestamp):
        return os.path.join(self.SIDECAR_DIR, "step1_headline_sidecar_2026_11_23.jsonl")

    def recursive_tweet_extractor(self, payload):
        return payload["tweets"]


class PageClient:
    """One page target's CDP socket."""

    def __init__(self, cdp, target_id):
        self.cdp, self.target_id, self.events = cdp, target_id, []

    def command(self, method, params=None, *, timeout_seconds=10.0):
        self.cdp.commands.append((self.target_id, method))
        if self.target_id in self.cdp.failing_targets:
            raise WebSocketTimeoutException("fixture page command timeout")
        if method in {"Page.reload", "Page.navigate"} and self.cdp.reload_serves:
            self.cdp.serve(self)
        if method == "Input.dispatchKeyEvent" and params["type"] == "keyDown" and self.cdp.light_serves:
            self.cdp.serve(self)
        if method == "Network.getResponseBody":
            return {"body": json.dumps(self.cdp.bodies.pop(params["requestId"])), "base64Encoded": False}
        if method == "Runtime.evaluate" and params.get("expression") == "window.location.href":
            page = next((row for row in self.cdp.pages if row["id"] == self.target_id), None)
            return {"result": {"value": (page or {}).get("url", "")}}
        return {}

    def event(self, *, timeout_seconds):
        if self.events:
            return self.events.pop(0)
        time.sleep(min(timeout_seconds, 0.005))
        return None

    def close(self):
        pass


class BrowserClient:
    """The browser target's CDP socket (Target.createTarget / Target.closeTarget)."""

    def __init__(self, cdp):
        self.cdp = cdp

    def command(self, method, params=None, *, timeout_seconds=10.0):
        self.cdp.browser_commands.append((method, dict(params or {}), timeout_seconds))
        if method == "Target.createTarget":
            self.cdp.created += 1
            page = self.cdp.page(f"browser-{self.cdp.created}", params["url"])
            self.cdp.pages.append(page)
            return {"targetId": page["id"]}
        if method == "Target.closeTarget":
            self.cdp.pages = [row for row in self.cdp.pages if row["id"] != params["targetId"]]
            return {"success": True}
        return {}

    def close(self):
        pass


class FakeCDP:
    def __init__(self, pages=None, *, connect_fails=False):
        self.pages = pages if pages is not None else [self.page("list"), self.page("unrelated", "https://x.com/home")]
        self.failing_targets = set()
        self.connect_fails = connect_fails
        self.reload_serves, self.light_serves = True, False
        self.tweets = [_tweet(30), _tweet(90, "FirstSquawk")]
        self.bodies, self.request_seq = {}, 0
        self.clients, self.commands, self.browser_commands = {}, [], []
        self.requests, self.opens, self.created = [], 0, 0
        self.create_error = self.close_error = False
        self.new_url = LIST_URL

    @staticmethod
    def page(target_id, url=LIST_URL):
        return {"id": target_id, "type": "page", "url": url, "webSocketDebuggerUrl": f"ws://fake/{target_id}"}

    def serve(self, client, tweets=None):
        self.request_seq += 1
        request_id = str(self.request_seq)
        self.bodies[request_id] = {"tweets": list(tweets if tweets is not None else self.tweets)}
        client.events += [
            {"method": "Network.requestWillBeSent", "params": {"requestId": request_id, "request": {"url": TIMELINE}}},
            {"method": "Network.responseReceived",
             "params": {"requestId": request_id, "response": {"url": TIMELINE, "status": 200}}},
            {"method": "Network.loadingFinished", "params": {"requestId": request_id}},
        ]

    def targets(self, **_):
        return [dict(row) for row in self.pages]

    def client(self, url, *, timeout_seconds):
        assert timeout_seconds == feed.SESSION_TIMEOUT_SECONDS
        if url == "ws://fake/browser":
            return BrowserClient(self)
        target_id = url.rsplit("/", 1)[-1]
        if self.connect_fails and target_id in self.failing_targets:
            raise WebSocketTimeoutException("fixture page connection timeout")
        self.clients[target_id] = PageClient(self, target_id)
        return self.clients[target_id]

    def http_open(self, request, *, timeout):
        url = urlsplit(request.full_url)
        self.requests.append((request.get_method(), url.path, unquote(url.query)))
        assert url.netloc == "127.0.0.1:9222"
        if url.path == "/json/version":
            assert timeout == feed.CATALOG_TIMEOUT_SECONDS
            payload = json.dumps({"webSocketDebuggerUrl": "ws://fake/browser"}).encode()
        elif url.path == "/json/new":
            # CC-785 cause 1: a loaded Chrome needed 6 s; the create gets 20 s.
            assert request.get_method() == "PUT" and unquote(url.query) == LIST_URL
            assert timeout == feed.TAB_CREATE_TIMEOUT_SECONDS
            self.opens += 1
            page = self.page(f"fresh-{self.opens}", self.new_url)
            self.pages.append(page)
            if self.create_error:
                raise TimeoutError("fixture create reply came too late")
            payload = json.dumps(page).encode()
        else:
            assert request.get_method() == "GET" and url.path.startswith("/json/close/")
            assert timeout == feed.TAB_CLOSE_TIMEOUT_SECONDS
            old_id = unquote(url.path.rsplit("/", 1)[-1])
            assert old_id != "unrelated"
            if self.close_error:
                raise TimeoutError("fixture close reply lost")
            self.pages = [row for row in self.pages if row["id"] != old_id]
            payload = b"Target is closing"

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return payload

        return Response()

    def count(self, method):
        return sum(1 for _, name in self.commands if name == method)


class FakeBootstrap:
    INGESTION_CDP_PORT = 9222
    STATE_READY, STATE_LAUNCHED, STATE_ALREADY_READY = "READY", "LAUNCHED", "ALREADY_READY"
    STATE_REAUTH_REQUIRED = "REAUTH_REQUIRED"

    def __init__(self, *, alive=True, key=(14200, 1)):
        self.alive, self.key = alive, key
        self.owner_checks, self.launches, self.key_reads = 0, 0, 0

    def probe_cdp(self, port, *, timeout=3.0):
        return {"cdp_alive": self.alive}

    def ingestion_process_state(self):
        self.owner_checks += 1
        if self.key is None:
            return {"state": "READY", "detail": "fixture", "pid": 14200}
        return {"state": "READY", "detail": "fixture", "pid": self.key[0], "start": self.key[1]}

    def listener_owner_key(self, port):
        self.key_reads += 1
        return self.key

    def ensure_ingestion_runtime(self):
        self.launches += 1
        return {"status": "LAUNCH_FAILED"}

    def probe_ingestion_session(self):
        return {"auth_state": "READY"}


class Harness:
    def __init__(self, tmp_path, cdp=None, bootstrap=None):
        self.tmp_path, self.cdp = tmp_path, cdp or FakeCDP()
        self.t = [0.0]

        class QuickCapture(feed.MinuteCapture):
            def tick(self, **kwargs):
                kwargs.setdefault("settle_seconds", 0.05)
                kwargs.setdefault("light_settle_seconds", 0.02)
                kwargs.setdefault("scroll_seconds", 0)
                return super().tick(**kwargs)

        self.capture = QuickCapture(module=FakeIngestion(tmp_path), targets_fn=self.cdp.targets,
                                    client_factory=self.cdp.client, http_open=self.cdp.http_open,
                                    now_fn=self.now, mono_fn=lambda: self.t[0])
        self.bootstrap = bootstrap or FakeBootstrap()
        self.runner = self.new_runner()

    def now(self):
        return NOW + timedelta(seconds=self.t[0])

    def new_runner(self):
        return feed.FeedRunner(feed_path=self.tmp_path / "feed.json", log_path=self.tmp_path / "runner.log",
                               bootstrap=self.bootstrap, capture_factory=lambda: self.capture,
                               clock=lambda: self.t[0], now_fn=self.now, sidecar_dir=self.tmp_path / "sidecars")

    def tick(self, seconds):
        self.t[0] = float(seconds)
        return self.runner.iterate()["capture"]

    def exported(self):
        return json.loads((self.tmp_path / "feed.json").read_text(encoding="utf-8"))

    def log(self):
        return [json.loads(line) for line in (self.tmp_path / "runner.log").read_text().splitlines()]

    def sidecar_ids(self):
        path = self.tmp_path / "sidecars" / "step1_headline_sidecar_2026_11_23.jsonl"
        return [json.loads(line)["tweet_id"] for line in path.read_text().splitlines()]


# ---- the kept session: read the page's own fetches, refresh lightly, reload at most once a minute

def test_the_page_own_fetches_are_read_between_ticks_without_a_reload(tmp_path):
    h = Harness(tmp_path)
    first = h.tick(0)
    assert first["state"] == "CAPTURED" and first["refresh"] == "reload" and first["new_rows"] == 2
    # X's own page polls the list: the runner reads it while it waits and ticks at once.
    h.cdp.tweets = [_tweet(5, "DeItaone", "NVIDIA REINSTATED")]
    h.cdp.serve(h.cdp.clients["list"])
    h.t[0] = 5.0
    assert h.runner.idle(0.5) is True
    second = h.tick(5)
    assert second["state"] == "CAPTURED" and second["refresh"] is None and second["new_rows"] == 1
    assert second["api_requests"] == 1
    assert h.cdp.count("Page.reload") == 1 and h.cdp.count("Network.enable") == 1
    assert h.exported()["rows"][0]["text"] == "NVIDIA REINSTATED"
    # Exactly once: the same posts in a later reload add nothing.
    h.cdp.tweets = [_tweet(30), _tweet(5, "DeItaone", "NVIDIA REINSTATED")]
    assert h.tick(65)["new_rows"] == 0
    assert len(h.sidecar_ids()) == len(set(h.sidecar_ids())) == 3


def test_a_quiet_page_gets_the_light_key_and_at_most_one_reload_a_minute(tmp_path):
    h = Harness(tmp_path)
    h.tick(0)
    states = [h.tick(seconds)["state"] for seconds in range(15, 301, 15)]
    # The light key brings nothing here: one reload a minute, as before CC-785, and no failures.
    assert h.cdp.count("Page.reload") == 6
    assert h.cdp.count("Input.dispatchKeyEvent") == 2 * 15
    assert set(states) == {"LISTENING", "CAPTURED"} and h.runner.failure_streak == 0
    assert h.exported()["health"]["state"] == "OK"
    assert h.capture.light_misses == 15 and h.capture.light_hits == 0


def test_when_the_light_key_works_no_reload_follows(tmp_path):
    h = Harness(tmp_path)
    h.tick(0)
    h.cdp.light_serves = True
    captured = [h.tick(seconds) for seconds in range(15, 301, 15)]
    assert all(row["state"] == "CAPTURED" and row["refresh"] == "light" for row in captured)
    assert h.cdp.count("Page.reload") == 1
    assert h.capture.light_hits == 20 and h.exported()["health"]["last_good_age_seconds"] == 0.0


def test_a_timeline_response_after_the_settle_is_still_read(tmp_path):
    h = Harness(tmp_path)
    h.cdp.reload_serves = False
    first = h.tick(0)
    assert first["state"] == "NO_TIMELINE_RESPONSE" and h.runner.failure_streak == 1
    # The reply of the slow reload lands after the settle: the kept session still reads it.
    h.cdp.serve(h.cdp.clients["list"])
    assert h.runner.idle(0.5) is True
    second = h.tick(15)
    assert second["state"] == "CAPTURED" and second["new_rows"] == 2 and h.runner.failure_streak == 0


# ---- the two-step self-heal and the P1 ------------------------------------------------------------

def _hung(tmp_path, *, connect_fails=False, pages=None):
    cdp = FakeCDP(pages=pages, connect_fails=connect_fails)
    cdp.failing_targets.add(pages[0]["id"] if pages else "list")
    return Harness(tmp_path, cdp=cdp)


@pytest.mark.parametrize("connect_fails", [False, True])
def test_two_failed_captures_replace_the_tab_and_the_next_tick_reads_the_fresh_one(tmp_path, connect_fails):
    h = _hung(tmp_path, connect_fails=connect_fails)
    first, second = h.tick(0), h.tick(15)
    assert first["page_socket_failed"] and second["page_socket_failed"]
    assert "tab_replacement" not in first
    heal = second["tab_replacement"]
    assert heal["state"] == "TAB_REPLACED" and heal["method"] == "http"
    assert heal["old_target_id"] == "list" and heal["new_target_id"] == "fresh-1"
    assert h.cdp.requests == [("PUT", "/json/new", LIST_URL), ("GET", "/json/close/list", "")]
    assert {row["id"] for row in h.cdp.pages} == {"fresh-1", "unrelated"}
    assert h.exported()["health"]["state"] == "STALE" and h.runner.p1 is None
    third = h.tick(30)
    assert third["state"] == "CAPTURED" and third["target_id"] == "fresh-1"
    health = h.exported()["health"]
    assert health["state"] == "OK" and health["failure_streak"] == 0 and health["last_heal"] == heal


def test_a_third_failure_recreates_the_tab_through_the_browser_target_and_raises_the_p1(tmp_path):
    h = _hung(tmp_path)
    h.cdp.failing_targets.add("fresh-1")
    h.tick(0)
    h.tick(15)
    third = h.tick(30)
    heal = third["tab_replacement"]
    assert heal["state"] == "TAB_REPLACED" and heal["method"] == "browser"
    assert heal["old_target_id"] == "fresh-1" and heal["new_target_id"] == "browser-1"
    assert [name for name, _, _ in h.cdp.browser_commands] == ["Target.createTarget", "Target.closeTarget"]
    assert third["p1_event"] == "RAISED"
    health = h.exported()["health"]
    assert health["state"] == "P1" and health["p1"]["failure_streak"] == 3
    assert health["p1"]["cause"].startswith("CAPTURE_FAILED:") and health["p1"]["first_failure_utc"] == "2026-11-23T13:50:00.000Z"
    assert health["stale_since_utc"] == "2026-11-23T13:50:00.000Z"  # the runner start: no good read yet
    fourth = h.tick(45)
    assert fourth["state"] == "CAPTURED" and fourth["target_id"] == "browser-1" and fourth["p1_event"] == "CLEARED"
    health = h.exported()["health"]
    assert health["state"] == "OK" and health["p1"] is None and health["last_p1"]["cleared_utc"] == "2026-11-23T13:50:45.000Z"
    events = [row["p1"]["event"] for row in h.log() if "p1" in row]
    assert events == ["RAISED", "CLEARED"]


def test_failures_after_the_third_retry_the_browser_step_every_five_minutes(tmp_path):
    h = _hung(tmp_path)
    h.cdp.failing_targets.update({"fresh-1", "browser-1", "browser-2"})
    for seconds in range(0, 331, 15):
        h.tick(seconds)
    heals = [row["capture"]["tab_replacement"]["method"] for row in h.log() if "tab_replacement" in row["capture"]]
    assert heals == ["http", "browser", "browser"]
    assert h.runner.p1 is not None and h.runner.failure_streak == 23


def test_replacement_adopts_a_tab_whose_reply_came_late_and_closes_orphan_list_tabs(tmp_path):
    pages = [FakeCDP.page("hung"), FakeCDP.page("orphan"), FakeCDP.page("unrelated", "https://x.com/home")]
    h = _hung(tmp_path, pages=pages)
    h.cdp.create_error = True
    h.tick(0)
    heal = h.tick(15)["tab_replacement"]
    assert heal["state"] == "TAB_REPLACED" and heal["adopted_late_target"] is True
    assert heal["create_detail"] == "TAB_REPLACEMENT_TIMEOUT:TimeoutError"
    assert heal["closed_target_ids"] == ["hung", "orphan"]
    assert {row["id"] for row in h.cdp.pages} == {"fresh-1", "unrelated"}
    assert h.tick(30)["target_id"] == "fresh-1"


def test_attaching_closes_list_tabs_left_behind_so_one_stays(tmp_path):
    pages = [FakeCDP.page("list"), FakeCDP.page("orphan"), FakeCDP.page("unrelated", "https://x.com/home")]
    h = Harness(tmp_path, cdp=FakeCDP(pages=pages))
    first = h.tick(0)
    assert first["state"] == "CAPTURED" and first["orphans_closed"] == ["orphan"]
    assert {row["id"] for row in h.cdp.pages} == {"list", "unrelated"}


def test_a_close_failure_keeps_the_new_tab_preferred_after_a_restart(tmp_path):
    h = _hung(tmp_path)
    h.cdp.close_error = True
    h.tick(0)
    heal = h.tick(15)["tab_replacement"]
    assert heal["state"] == "TAB_REPLACEMENT_FAILED" and heal["detail"] == "CDP_TARGET_CLOSE_NOT_ACKNOWLEDGED"
    assert heal["new_target_id"] == "fresh-1"
    h.capture.preferred_target_id = None
    h.capture.close_session()
    h.runner = h.new_runner()  # a restart reads the heal record from the export
    h.runner.capture = None
    captured = h.tick(30)
    assert captured["state"] == "CAPTURED" and captured["target_id"] == "fresh-1" and h.cdp.opens == 1


def test_an_unrelated_x_tab_is_never_closed(tmp_path):
    h = _hung(tmp_path, pages=[FakeCDP.page("home", "https://x.com/home")])
    h.tick(0)
    heal = h.tick(15)["tab_replacement"]
    assert heal["state"] == "TAB_REPLACEMENT_SKIPPED" and heal["detail"] == "FAILED_TARGET_NOT_LIST_PAGE"
    assert h.cdp.requests == []


@pytest.mark.parametrize("when", ["page", "new_tab"])
def test_login_redirects_stay_reauth_required(tmp_path, when):
    h = _hung(tmp_path)
    if when == "page":
        h.cdp.pages[0]["url"] = LOGIN_URL
        for seconds in (0, 15, 30):
            assert h.tick(seconds)["state"] == "REAUTH_REQUIRED"
        assert h.cdp.requests == []  # never a tab step on a sign-in page
        assert h.exported()["health"]["p1"]["cause"] == "REAUTH_REQUIRED:LOGIN_REDIRECT_OBSERVED"
    else:
        h.cdp.new_url = LOGIN_URL
        h.tick(0)
        assert h.tick(15)["state"] == "REAUTH_REQUIRED"
        assert h.cdp.requests == [("PUT", "/json/new", LIST_URL)]
        assert any(row["id"] == "list" for row in h.cdp.pages)


def test_quiet_listening_neither_counts_nor_resets_a_failure_streak(tmp_path):
    h = Harness(tmp_path)
    h.runner.capture = object()
    for state in ("CAPTURE_FAILED", "LISTENING", "CAPTURE_FAILED", "LISTENING"):
        h.runner._account({"state": state, "detail": "fixture"}, moment=NOW)
    assert h.runner.failure_streak == 2 and h.runner.p1 is None


def test_replay_of_the_23_nov_failure_run_heals_before_1357(tmp_path):
    """The saved log, 23 Nov 13:54-14:03Z: the old runner never healed; the new one does at once."""
    saved = [
        ("2026-11-23T13:54:46.043Z", "CAPTURED", None),
        ("2026-11-23T13:55:45.990Z", "NO_TIMELINE_RESPONSE", "NO_TIMELINE_RESPONSE_WITHIN_SETTLE"),
        ("2026-11-23T13:56:55.725Z", "CAPTURE_FAILED", "MINUTE_CAPTURE_TIMEOUT:WebSocketTimeoutException"),
        ("2026-11-23T13:57:46.949Z", "NO_TIMELINE_RESPONSE", "NO_TIMELINE_RESPONSE_WITHIN_SETTLE"),
        ("2026-11-23T13:58:54.359Z", "NO_TIMELINE_RESPONSE", "NO_TIMELINE_RESPONSE_WITHIN_SETTLE"),
        ("2026-11-23T14:03:51.623Z", "CAPTURED", None),
    ]
    clock = [NOW]
    heals = []

    class Replay:
        preferred_target_id = None

        def __init__(self):
            self.rows = iter(saved)

        def tick(self):
            at, state, detail = next(self.rows)
            clock[0] = feed._parse_utc(at)
            row = {"state": state, "detail": detail, "attempted_utc": at, "target_id": "F9002430"}
            if state == "CAPTURED":
                row["last_timeline_utc"] = at
            return row

        def heal_target(self, target_id, *, method):
            heals.append((feed._iso(clock[0]), method))
            return {"state": "TAB_REPLACED", "method": method, "attempted_utc": feed._iso(clock[0])}

    runner = feed.FeedRunner(feed_path=tmp_path / "feed.json", log_path=tmp_path / "runner.log",
                             bootstrap=FakeBootstrap(), capture_factory=Replay, clock=lambda: 0.0,
                             now_fn=lambda: clock[0], sidecar_dir=tmp_path / "sidecars")
    records = [runner.iterate() for _ in saved]
    assert heals[0] == ("2026-11-23T13:56:55.725Z", "http") and heals[0][0] < "2026-11-23T13:57:00"
    assert heals[1] == ("2026-11-23T13:57:46.949Z", "browser")
    assert records[3]["p1"]["event"] == "RAISED" and records[3]["health"]["state"] == "P1"
    assert records[3]["health"]["stale_since_utc"] == "2026-11-23T13:54:46.043Z"
    assert records[5]["health"]["state"] == "OK" and records[5]["p1"]["event"] == "CLEARED"


# ---- the stale marker --------------------------------------------------------------------------------

def test_the_export_marks_a_feed_stale_after_a_minute_without_a_read_in_market_hours(tmp_path):
    h = Harness(tmp_path)
    h.tick(0)
    h.cdp.reload_serves = False
    h.tick(30)
    assert h.exported()["health"]["state"] == "OK"
    h.tick(45)
    assert h.exported()["health"]["stale_since_utc"] is None
    h.t[0] = 61.0
    h.capture.last_reload_mono = 61.0  # the reload budget is spent: the tick only listens
    h.runner.iterate()
    health = h.exported()["health"]
    assert health["state"] == "STALE" and health["stale_since_utc"] == "2026-11-23T13:50:00.000Z"
    assert health["last_good_age_seconds"] == 61.0 and "never 'no news'" in health["reading_rule"]
    # A restart keeps the last good read, so the marker does not reset to "fresh".
    restarted = h.new_runner()
    assert restarted.last_good_utc == NOW


def test_market_hours_and_the_tick_interval(tmp_path):
    def at(day, hour, minute=0):
        return datetime(2026, 11, day, hour, minute, tzinfo=timezone.utc)

    assert feed.in_market_hours(at(22, 20, 59)) is False  # Sunday before the open
    assert feed.in_market_hours(at(22, 21, 0)) is True
    assert feed.in_market_hours(at(25, 3)) is True       # Wednesday
    assert feed.in_market_hours(at(27, 21, 59)) is True  # Friday
    assert feed.in_market_hours(at(27, 22, 0)) is False
    assert feed.in_market_hours(at(28, 12)) is False     # Saturday
    runner = feed.FeedRunner(feed_path=tmp_path / "feed.json", bootstrap=FakeBootstrap(), now_fn=lambda: at(25, 3))
    assert runner.next_interval() == feed.MARKET_INTERVAL_SECONDS == 15.0
    runner.now_fn = lambda: at(28, 12)
    assert runner.next_interval() == feed.INTERVAL_SECONDS == 60.0


def test_run_forever_ticks_at_once_when_the_page_brings_new_posts(tmp_path):
    calls = []

    class Runner:
        log_path = tmp_path / "runner.log"

        def iterate(self):
            calls.append("iterate")

        def next_interval(self):
            return 15.0

        def idle(self, seconds, sleep):
            calls.append("idle")
            return True

    result = feed.run_forever(stop_path=tmp_path / "STOP", lock_path=tmp_path / "lock", runner=Runner(),
                              sleep=lambda _: pytest.fail("no plain sleep while the session listens"),
                              max_iterations=3)
    assert result == {"state": "STOPPED", "iterations": 3}
    assert calls == ["iterate", "idle", "iterate", "idle", "iterate"]


def test_stop_ends_a_runner_whose_call_blocks_mid_tick(tmp_path):
    """24 Nov: the old runner ignored STOP for 150 s; a blocked call now ends within the grace."""
    import threading

    release, exits = threading.Event(), []
    stop = tmp_path / "STOP"

    class Blocked:
        log_path = tmp_path / "runner.log"

        def iterate(self):
            stop.write_text("stop")
            release.wait(10.0)  # a hung CDP socket or PowerShell child

    def hard_exit(code):
        exits.append((code, time.monotonic()))
        release.set()

    started = time.monotonic()
    result = feed.run_forever(stop_path=stop, lock_path=tmp_path / "lock", runner=Blocked(),
                              stop_grace_seconds=0.3, hard_exit=hard_exit, max_iterations=1)
    assert exits and exits[0][0] == 0 and exits[0][1] - started < 3.0
    assert result["iterations"] == 1
    assert any(json.loads(line).get("stop") == "WATCHDOG_EXIT" for line in (tmp_path / "runner.log").read_text().splitlines())


def test_a_stop_cuts_the_settle_wait_short(tmp_path):
    h = Harness(tmp_path)
    h.cdp.reload_serves = False
    h.capture.should_stop = lambda: True
    started = time.monotonic()
    captured = h.capture.tick(force_reload=True, settle_seconds=30.0)
    assert captured["refresh"] == "reload" and time.monotonic() - started < 2.0


def test_the_runner_gives_its_capture_the_stop_check(tmp_path):
    h = Harness(tmp_path)
    h.tick(0)
    h.runner.stop_path = tmp_path / "STOP"
    assert h.capture.should_stop() is False
    (tmp_path / "STOP").write_text("stop")
    assert h.capture.should_stop() is True


# ---- the browser checks: slow is not dead, and the owner is proved once ----------------------------

def test_a_slow_probe_is_not_a_dead_browser(tmp_path):
    class Slow(FakeBootstrap):
        def __init__(self):
            super().__init__()
            self.timeouts = []

        def probe_cdp(self, port, *, timeout=3.0):
            self.timeouts.append(timeout)
            return {"cdp_alive": timeout > 3.0}

    h = Harness(tmp_path, bootstrap=Slow())
    captured = h.tick(0)
    assert captured["state"] == "CAPTURED" and captured["browser_probe"] == "SLOW"
    assert h.bootstrap.timeouts == [3.0, 6.0] and h.bootstrap.launches == 0


def test_the_port_owner_is_proved_once_then_rechecked_by_pid_and_start_time(tmp_path):
    h = Harness(tmp_path)
    for seconds in (0, 15, 30, 45):
        h.tick(seconds)
    assert h.bootstrap.owner_checks == 1 and h.bootstrap.key_reads == 3
    h.bootstrap.key = (999, 7)  # another process (or a restarted Chrome) now holds the port
    h.tick(60)
    assert h.bootstrap.owner_checks == 2 and h.runner.owner_key == (999, 7)


def test_without_the_native_read_the_owner_proof_holds_for_its_half_hour(tmp_path):
    h = Harness(tmp_path, bootstrap=FakeBootstrap(key=None))
    for seconds in (0, 15, 1799):
        h.tick(seconds)
    assert h.bootstrap.owner_checks == 1
    h.tick(1801)
    assert h.bootstrap.owner_checks == 2


# ---- ingestion_bootstrap_v1: native owner check, patient probe, launch flags --------------------------

windows_only = pytest.mark.skipif(os.name != "nt", reason="the native owner check reads the Windows TCP table")


@windows_only
@pytest.mark.parametrize("family,host", [(socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")])
def test_the_native_listener_read_finds_this_process_on_its_own_port(family, host):
    listener = socket.socket(family, socket.SOCK_STREAM)
    try:
        listener.bind((host, 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        started = time.perf_counter()
        assert bootstrap_module._native_listener_pid(port) == os.getpid()
        identity = bootstrap_module._native_process_identity(os.getpid())
        assert time.perf_counter() - started < 2.0
        assert identity["start"] > 0 and "pytest" in identity["cmd"].lower()
        assert bootstrap_module.listener_owner_key(port) == (os.getpid(), identity["start"])
    finally:
        listener.close()
    assert bootstrap_module._native_listener_pid(port) is None


def test_the_owner_check_uses_the_native_read_before_powershell(monkeypatch, tmp_path):
    profile = tmp_path / "CapitalChronicleBot"
    monkeypatch.setattr(bootstrap_module, "canonical_ingestion_user_data_dir", lambda env=None: profile)
    monkeypatch.setattr(bootstrap_module, "probe_cdp", lambda port, **kwargs: {"cdp_alive": True})
    monkeypatch.setattr(bootstrap_module, "_native_listener_pid", lambda port: 14200)
    monkeypatch.setattr(bootstrap_module, "_powershell_json", lambda *a, **k: pytest.fail("no PowerShell needed"))
    monkeypatch.setattr(bootstrap_module, "_native_process_identity", lambda pid: {
        "pid": pid, "start": 133, "cmd": f'"chrome.exe" --remote-debugging-port=9222 --user-data-dir="{profile}"'})
    state = bootstrap_module.ingestion_process_state()
    assert state == {"state": "READY", "detail": "CANONICAL_INGESTION_PROFILE_ON_CDP_9222", "pid": 14200,
                     "start": 133, "owner_check": "NATIVE"}
    monkeypatch.setattr(bootstrap_module, "_native_process_identity", lambda pid: {
        "pid": pid, "start": 133, "cmd": '"chrome.exe" --user-data-dir="C:/Users/x/Default"'})
    assert bootstrap_module.ingestion_process_state()["state"] == "PORT_OWNER_UNPROVEN"
    # Without a native answer the PowerShell inventory is still the fallback.
    monkeypatch.setattr(bootstrap_module, "_native_process_identity", lambda pid: None)
    monkeypatch.setattr(bootstrap_module, "_powershell_json", lambda *a, **k: None)
    assert bootstrap_module.ingestion_process_state()["detail"] == "CDP_LISTENER_OWNER_NOT_RESOLVED"


def test_the_patient_probe_retries_once_with_a_longer_timeout(monkeypatch):
    seen = []

    def fake_get(url, *, timeout):
        seen.append(timeout)
        return {"Browser": "Chrome/142"} if timeout > 3.0 else None

    monkeypatch.setattr(bootstrap_module, "_http_get_json", fake_get)
    assert bootstrap_module.probe_cdp_patient(9222) == {"cdp_alive": True, "browser": "Chrome/142", "retried": True}
    assert seen == [3.0, bootstrap_module.PROBE_RETRY_TIMEOUT_SECONDS]


def test_a_relaunched_ingestion_chrome_keeps_its_page_timers_running_when_hidden(monkeypatch, tmp_path):
    profile = tmp_path / "CapitalChronicleBot"
    profile.mkdir()
    commands = []

    class Process:
        pid = 4242

    monkeypatch.setattr(bootstrap_module, "find_chrome_binary", lambda env=None: tmp_path / "chrome.exe")
    monkeypatch.setattr(bootstrap_module, "canonical_ingestion_user_data_dir", lambda env=None: profile)
    monkeypatch.setattr(subprocess, "Popen", lambda command, **kwargs: commands.append(command) or Process())
    launched = bootstrap_module._launch_canonical_ingestion_browser()
    assert launched["state"] == bootstrap_module.STATE_LAUNCHED
    command = commands[0]
    assert "--remote-debugging-port=9222" in command and f"--user-data-dir={profile}" in command
    assert set(bootstrap_module.BACKGROUND_THROTTLING_FLAGS) <= set(command)
