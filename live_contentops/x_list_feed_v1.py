"""CC-258: Jim's X list as one private feed (Jim's decision 71); CC-785: read within seconds.

Two deterministic parts, with no model call:

- ``MinuteCapture.tick``: the capture of the locked X list through the existing ingestion
  browser (Chrome ``CapitalChronicleBot`` on CDP 9222, see ingestion_bootstrap_v1). Since CC-785
  it keeps one CDP session on the list tab and reads the ``ListLatestTweetsTimeline`` responses
  the page fetches by itself, between ticks too; a quiet page gets X's own "load new posts" key
  and, after a minute, one reload (``capture_once`` is the one-shot form). It appends
  only new posts to the canonical per-day sidecar files, in the existing row shape, so every
  current reader of those files (newsroom, read model, hourly audit) sees them. Unlike the
  30-minute capture it keeps recent dedup keys in memory instead of re-reading every sidecar
  file, and it records each payload's hash and size instead of saving a copy: a copy every
  minute would add about 1 GB of disk a day (470 KB per response, measured 31 Oct).
- ``build_feed`` / ``write_feed``: one stable JSON export, newest first. Each row has handle,
  text, url, tweet_id, posted_utc (the post id's own millisecond clock), ingested_utc (when the
  capture saw it) and lag_seconds (ingested minus posted). Beside it, ``x_list_shock_flags_v1.json``
  holds the fast squawks' posts of the last 15 minutes in the shape CC-087's shock trigger takes
  as ``--headlines`` flags.

Use (decision 62; Jim, 5 Nov 2026: Main needs these headlines for trading ideas and ContentOps
for article ideas): the feed serves every internal decision with no review step. Main's
market-context sweep reads it first, a burst may start a shock analysis pass (CC-087), the
newsroom takes leads from it and Codex Data keeps its rows. Two restrictions remain, each with
its reason. A post never arms an order by itself (global C7: an admitted official fact or a
fresh-quote rule arms). Post text is third-party content and is not republished in public
output (decision 44); public posts keep their own rights check. A post is a lead until its own
source confirms it.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import threading
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import quote
from urllib.request import Request, urlopen

from live_contentops import x_list_ingest_capture_v1 as capture_v1
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_dir

SCHEMA_VERSION = "contentops.x_list_feed.v1"
FEED_DIR = Path(r"A:\Capital Chronicle\Runtime\ContentOps\x_list_feed")
FEED_PATH = FEED_DIR / "x_list_feed_v1.json"
STOP_PATH = FEED_DIR / "STOP"
LOCK_PATH = FEED_DIR / "runner_v1.lock"
LOG_PATH = FEED_DIR / "runner_v1.log"
LOG_MAX_BYTES = 8_000_000
WINDOW_HOURS = 24.0
INTERVAL_SECONDS = 60.0
# CC-785 (24 Nov 2026): a missed probe once stopped capture for up to 30 minutes while Chrome was alive but slow.
RELAUNCH_AFTER_SECONDS = 120.0
PROBE_ATTEMPTS = 3
OWNER_RECHECK_SECONDS = 1800.0
TAB_REPLACEMENT_COOLDOWN_SECONDS = 300.0
SCROLL_WHEN_NEW_AT_LEAST = 15
# CC-785 (Jim, 24 Nov 2026: 7.6 minutes late is far too serious). The runner keeps one CDP
# session on the list tab and reads the timeline responses the page itself fetches. It acts on a
# quiet page only: X's own "load new posts" key after LIGHT_REFRESH_AFTER_SECONDS, one full reload
# after RELOAD_AFTER_SECONDS (never more than one a minute, the old rate).
MARKET_INTERVAL_SECONDS = 15.0
LIGHT_REFRESH_AFTER_SECONDS = 15.0
RELOAD_AFTER_SECONDS = 60.0
TIMELINE_SETTLE_SECONDS = 15.0
LIGHT_SETTLE_SECONDS = 5.0
AFTER_RESPONSE_SECONDS = 1.0
SESSION_TIMEOUT_SECONDS = 20.0
CATALOG_TIMEOUT_SECONDS = 10.0
BODY_TIMEOUT_SECONDS = 20.0
TAB_CREATE_TIMEOUT_SECONDS = 20.0
TAB_CLOSE_TIMEOUT_SECONDS = 10.0
PROBE_RETRY_TIMEOUT_SECONDS = 12.0
PROBE_RETRY_TIMEOUTS = (6.0, PROBE_RETRY_TIMEOUT_SECONDS)
# A STOP file ends the runner within one market interval, even when a call blocks mid-tick:
# the waits check it, and a watchdog ends the process if the loop has not stopped by then.
STOP_GRACE_SECONDS = 15.0
HEAL_AFTER_FAILURES = 2
P1_AFTER_FAILURES = 3
STALE_AFTER_MARKET_SECONDS = 60.0
STALE_AFTER_SECONDS = 180.0
NETWORK_BUFFER = {"maxTotalBufferSize": 16_000_000, "maxResourceBufferSize": 4_000_000}
FAILURE_STATES = frozenset({"NO_TIMELINE_RESPONSE", "CAPTURE_FAILED", "CDP_UNAVAILABLE", "NO_X_PAGE",
                            "BROWSER_NOT_READY", "REAUTH_REQUIRED"})
TAB_FAILURE_STATES = frozenset({"NO_TIMELINE_RESPONSE", "CAPTURE_FAILED", "CDP_UNAVAILABLE"})
LIGHT_REFRESH_KEY = {"key": ".", "code": "Period", "windowsVirtualKeyCode": 190, "nativeVirtualKeyCode": 190}
READING_RULE = ("STALE or P1 means the feed has read no timeline since stale_since_utc: data missing or "
                "stale (C7), never 'no news' (CC-786)")
FLAGS_NAME = "x_list_shock_flags_v1.json"
FAST_SQUAWKS = ("FirstSquawk", "financialjuice", "DeItaone", "wallstengine", "zerohedge")
FLAG_WINDOW_MINUTES = 15.0
FLAG_MAX = 40
X_EPOCH_MS = 1288834974657
GMT7 = timezone(timedelta(hours=7))
CAPTURE_ROUTE = "x_list_feed_v1_minute"
GRANT = "JIM_X_LIST_PRIVATE_MAIN_RESEARCH_USE_20261029"
USE = {
    "private": "every internal decision, no review step: Main trading ideas and shock passes, "
               "ContentOps article ideas, Codex Data rows (decision 62; Jim, 5 Nov 2026)",
    "arming": "a post never arms an order by itself (global C7: an admitted official fact or a "
              "fresh-quote rule arms)",
    "public": "post text is third-party content, not republished in public output (decision 44); "
              "public posts keep their own rights check",
    "confirmation": "a post is a lead until its own source confirms it",
    "source_grant": GRANT,
}


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def in_market_hours(moment: datetime) -> bool:
    """The FX week, Sunday 21:00Z to Friday 22:00Z: the runner captures every 15 s inside it."""
    utc = moment.astimezone(timezone.utc)
    minutes = utc.hour * 60 + utc.minute
    weekday = utc.weekday()
    if weekday == 5:
        return False
    if weekday == 6:
        return minutes >= 21 * 60
    if weekday == 4:
        return minutes < 22 * 60
    return True


def _is_list_url(url: Any) -> bool:
    return str(url or "").split("?", 1)[0].rstrip("/") == capture_v1.TARGET_LIST_URL


def posted_utc_from_id(tweet_id: Any) -> datetime | None:
    """X post ids carry their creation time in milliseconds (bits 22 and up)."""
    try:
        value = int(str(tweet_id).strip())
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    moment = datetime.fromtimestamp(((value >> 22) + X_EPOCH_MS) / 1000.0, tz=timezone.utc)
    return moment if moment.year >= 2010 else None


def _created_at(raw: Any) -> datetime | None:
    try:
        return datetime.strptime(str(raw), "%a %b %d %H:%M:%S %z %Y").astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def feed_row(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Project one sidecar row to the feed's row; None when it has no text or post id."""
    text = str(row.get("headline_text") or "").strip()
    tweet_id = str(row.get("tweet_id") or "").strip()
    if not text or not tweet_id:
        return None
    posted = posted_utc_from_id(tweet_id) or _created_at(row.get("created_at_raw"))
    if posted is None:
        return None
    ingested = _parse_utc(row.get("captured_at_utc_precise")) or _parse_utc(row.get("captured_at_utc"))
    handle = str(row.get("author_handle") or "").strip()
    url = str(row.get("tweet_url") or "").strip() or (
        f"https://x.com/{handle}/status/{tweet_id}" if handle else f"https://x.com/i/status/{tweet_id}")
    projected = {
        "handle": handle,
        "text": text,
        "url": url,
        "tweet_id": tweet_id,
        "posted_utc": _iso(posted),
        "ingested_utc": _iso(ingested) if ingested else None,
        "lag_seconds": round((ingested - posted).total_seconds(), 3) if ingested else None,
        "is_retweet": bool(row.get("is_retweet")),
        "tags": [str(tag) for tag in (row.get("candidate_catalyst_tags") or [])],
    }
    # CC-455: retain actual reader observations; never infer a reply edge from text.
    parent = row.get("in_reply_to_status_id")
    if parent is not None and str(parent).isdigit():
        projected["in_reply_to_status_id"] = str(parent)
    if row.get("quoted_author_handle"):
        projected["quoted_author_handle"] = str(row["quoted_author_handle"])
    if isinstance(row.get("metrics"), dict) and row["metrics"]:
        projected["metrics"] = dict(row["metrics"])
        projected["metrics_observed_at_utc"] = _iso(ingested) if ingested else None
    return projected


def _sidecar_name(day: date) -> str:
    return f"step1_headline_sidecar_{day:%Y_%m_%d}.jsonl"


def sidecar_paths(sidecar_dir: Path, *, now: datetime, window_hours: float) -> list[Path]:
    """Per-day files are keyed by the post's GMT+7 date; read one day either side."""
    first = (now - timedelta(hours=window_hours)).astimezone(GMT7).date() - timedelta(days=1)
    last = now.astimezone(GMT7).date() + timedelta(days=1)
    paths, day = [], first
    while day <= last:
        path = Path(sidecar_dir) / _sidecar_name(day)
        if path.is_file():
            paths.append(path)
        day += timedelta(days=1)
    return paths


class SidecarTail:
    """Reads appended bytes only: the sidecar files are append-only per-day logs."""

    def __init__(self) -> None:
        self._files: dict[str, tuple[int, list[dict[str, Any]]]] = {}

    def rows(self, paths: Iterable[Path]) -> list[dict[str, Any]]:
        keep: dict[str, tuple[int, list[dict[str, Any]]]] = {}
        out: list[dict[str, Any]] = []
        for path in paths:
            key = str(path)
            offset, rows = self._files.get(key, (0, []))
            try:
                size = path.stat().st_size
                if size < offset:
                    offset, rows = 0, []
                if size > offset:
                    with path.open("rb") as handle:
                        handle.seek(offset)
                        chunk = handle.read(size - offset)
                    complete = chunk.rfind(b"\n") + 1
                    rows = rows + _parse_lines(chunk[:complete])
                    offset += complete
            except OSError:
                pass
            keep[key] = (offset, rows)
            out.extend(rows)
        self._files = keep
        return out


def _parse_lines(chunk: bytes) -> list[dict[str, Any]]:
    rows = []
    for line in chunk.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except ValueError:
            continue
        if isinstance(raw, dict):
            row = feed_row(raw)
            if row is not None:
                rows.append(row)
    return rows


def build_feed(*, now: datetime | None = None, sidecar_dir: Path | None = None,
               window_hours: float = WINDOW_HOURS, capture: Mapping[str, Any] | None = None,
               tail: SidecarTail | None = None, health: Mapping[str, Any] | None = None) -> dict[str, Any]:
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    directory = Path(sidecar_dir or canonical_headline_sidecar_dir())
    cutoff, ceiling = moment - timedelta(hours=window_hours), moment + timedelta(minutes=5)
    reader = tail or SidecarTail()
    by_id: dict[str, dict[str, Any]] = {}
    for row in reader.rows(sidecar_paths(directory, now=moment, window_hours=window_hours)):
        posted = _parse_utc(row["posted_utc"])
        if posted is None or posted < cutoff or posted > ceiling:
            continue
        prior = by_id.get(row["tweet_id"])
        if prior is None or (row["ingested_utc"] or "~") < (prior["ingested_utc"] or "~"):
            by_id[row["tweet_id"]] = row
    rows = sorted(by_id.values(), key=lambda r: (r["posted_utc"], r["tweet_id"]), reverse=True)
    newest = _parse_utc(rows[0]["posted_utc"]) if rows else None
    hour_lags = sorted(r["lag_seconds"] for r in rows if r["lag_seconds"] is not None
                       and _parse_utc(r["posted_utc"]) >= moment - timedelta(hours=1))
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _iso(moment),
        "window_hours": window_hours,
        "row_count": len(rows),
        "newest_posted_utc": _iso(newest) if newest else None,
        "newest_age_seconds": round((moment - newest).total_seconds(), 1) if newest else None,
        "ingest_lag_seconds_median_last_hour": hour_lags[len(hour_lags) // 2] if hour_lags else None,
        "capture": dict(capture or {}),
        # CC-785: whether the capture is reading the list at all; a stale feed is missing data.
        "health": dict(health) if health else None,
        "source": {"list_url": capture_v1.TARGET_LIST_URL, "sidecar_dir": str(directory)},
        "use": USE,
        "fields": {
            "posted_utc": "the post id's own clock, milliseconds",
            "ingested_utc": "when the capture saw the post (whole seconds for rows from the 30-minute capture)",
            "lag_seconds": "ingested_utc minus posted_utc",
            "health.stale_since_utc": "set while the feed is stale: the last time a timeline response "
                                      "was read (or the runner start); null when fresh",
            "health.failure_streak": "failed captures in a row (quiet listening ticks do not count)",
            "health.failure_cause": "the latest failed capture's state and detail",
            "health.p1": "raised after 3 failed captures in a row; cleared by the next good capture",
        },
        "rows": rows,
    }


def render_feed(feed: Mapping[str, Any]) -> bytes:
    """Valid JSON with one row per line, so a reader can take the newest N lines."""
    header = json.dumps({k: v for k, v in feed.items() if k != "rows"}, ensure_ascii=False)
    rows = list(feed.get("rows") or [])
    lines = [header[:-1] + ', "rows": [']
    lines += [json.dumps(row, ensure_ascii=False) + ("," if i < len(rows) - 1 else "") for i, row in enumerate(rows)]
    lines.append("]}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def shock_flags(feed: Mapping[str, Any], *, now: datetime, handles: Iterable[str] = FAST_SQUAWKS,
                minutes: float = FLAG_WINDOW_MINUTES, limit: int = FLAG_MAX) -> list[dict[str, Any]]:
    """CC-087's ``--headlines`` input: the fast squawks' own posts of the last minutes, newest first.

    The shock trigger attaches these as flags; under its C7 rule they never fire or arm by themselves.
    """
    cutoff = now - timedelta(minutes=minutes)
    wanted = {handle.lower() for handle in handles}
    flags: list[dict[str, Any]] = []
    for row in feed.get("rows") or []:
        posted = _parse_utc(row["posted_utc"])
        if posted is None or posted < cutoff:
            break
        if row["handle"].lower() in wanted and not row["is_retweet"]:
            flags.append({"title": row["text"], "source": f"X list @{row['handle']}",
                          "at_utc": row["posted_utc"], "url": row["url"], "tags": row["tags"]})
            if len(flags) >= limit:
                break
    return flags


def render_flags(flags: list[Mapping[str, Any]]) -> bytes:
    if not flags:
        return b"[]\n"
    return ("[\n" + ",\n".join(json.dumps(flag, ensure_ascii=False) for flag in flags) + "\n]\n").encode("utf-8")


def write_feed(path: Path, feed: Mapping[str, Any], *, attempts: int = 5) -> bool:
    """Atomic replace; a reader holding the file open only delays this minute's write."""
    return _atomic_write(path, render_feed(feed), attempts=attempts)


def _atomic_write(path: Path, payload: bytes, *, attempts: int = 5) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(attempts):
        fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
            os.replace(temporary, path)
            return True
        except PermissionError:
            time.sleep(0.2 * (attempt + 1))
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return False


class MinuteCapture:
    """One light capture per call through the existing ingestion browser's X list page."""

    def __init__(self, *, module: Any = None, cdp_url: str = capture_v1.CDP_URL_DEFAULT,
                 client_factory: Callable[..., Any] = capture_v1._DirectCDPPageClient,
                 targets_fn: Callable[..., list] | None = None,
                 now_fn: Callable[[], datetime] | None = None,
                 http_open: Callable[..., Any] = urlopen,
                 mono_fn: Callable[[], float] = time.monotonic) -> None:
        self.module = module or capture_v1.load_data_ingestion_module()
        self.cdp_url = cdp_url
        self.client_factory = client_factory
        self.targets_fn = targets_fn or capture_v1.list_cdp_page_targets
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self.http_open = http_open
        self.mono_fn = mono_fn
        self.preferred_target_id: str | None = None
        self.keys: set[str] = set()
        # CC-785: one session on the list tab, kept between ticks.
        self.session: Any = None
        self.session_target_id: str | None = None
        self.session_url = ""
        self.pending: dict[str, str] = {}
        self.last_timeline_mono: float | None = None
        self.last_timeline_utc: str | None = None
        self.last_reload_mono: float | None = None
        self.last_light_mono: float | None = None
        self.light_pending = False
        self.light_hits = self.light_misses = 0
        self._carry = self._new_counts()
        self.should_stop: Callable[[], bool] = lambda: False
        self._load_recent_keys()

    @staticmethod
    def _new_counts() -> dict[str, Any]:
        return {"responses": 0, "new_rows": 0, "api_requests": 0, "detail": None}

    def _load_recent_keys(self) -> None:
        directory = Path(self.module.SIDECAR_DIR)
        today = self.now_fn().astimezone(GMT7).date()
        for offset in range(-3, 2):
            path = directory / _sidecar_name(today + timedelta(days=offset))
            if not path.is_file():
                continue
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(row, dict):
                        key = str(row.get("dedup_key") or row.get("headline_id") or "")
                        if key:
                            self.keys.add(key)

    def append(self, tweets: list, payload_meta: Mapping[str, Any]) -> list[dict[str, Any]]:
        if not tweets:
            return []
        context = self.module.build_headline_sidecar_context()
        captured_at = self.module._utc_now_iso()
        precise = _iso(self.now_fn())
        by_path: dict[str, list[dict[str, Any]]] = {}
        for tweet in tweets:
            text = self.module._tweet_text(tweet)
            if not text:
                continue
            metadata = self.module._tweet_sidecar_metadata(tweet)
            timestamp = self.module._tweet_timestamp(tweet)
            headline_id = self.module._headline_id(timestamp, text)
            identity = str(metadata.get("dedup_key") or headline_id)
            if identity in self.keys:
                continue
            self.keys.add(identity)
            row = {
                "schema_version": "step1_headline_catalyst_sidecar_v1",
                "headline_id": headline_id,
                "headline_text": text,
                "headline_timestamp": timestamp,
                "source_platform": "x_cdp_list_latest_tweets_timeline",
                "captured_at_utc": captured_at,
                "captured_at_utc_precise": precise,
                "capture_route": CAPTURE_ROUTE,
                **dict(payload_meta),
                **metadata,
                **context,
            }
            by_path.setdefault(self.module._sidecar_path_for_timestamp(timestamp), []).append(row)
        written: list[dict[str, Any]] = []
        for sidecar_path, rows in by_path.items():
            Path(sidecar_path).parent.mkdir(parents=True, exist_ok=True)
            with open(sidecar_path, "a", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                    written.append(row)
        return written

    # ---- CC-785: one session on the list tab ---------------------------------------------------

    def _page_call(self, result: dict[str, Any]) -> Callable[..., Any]:
        def page_call(call: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
            try:
                return call(*args, **kwargs)
            except Exception as exc:
                from websocket import WebSocketException
                if isinstance(exc, (TimeoutError, ConnectionError, WebSocketException)):
                    result["page_socket_failed"] = True
                raise
        return page_call

    def close_session(self) -> None:
        client, self.session, self.pending = self.session, None, {}
        if client is not None:
            try:
                client.close()
            except Exception:  # noqa: BLE001 - detaching must not hide the capture result
                pass

    def _consume(self, client: Any, event: Mapping[str, Any], counts: dict[str, Any],
                 page_call: Callable[..., Any]) -> None:
        method = str(event.get("method") or "")
        params = event.get("params") if isinstance(event.get("params"), dict) else {}
        if method == "Network.requestWillBeSent":
            request = params.get("request") if isinstance(params.get("request"), dict) else {}
            if "/i/api/" in str(request.get("url") or ""):
                counts["api_requests"] += 1
            return
        if method == "Network.responseReceived":
            response = params.get("response") if isinstance(params.get("response"), dict) else {}
            url = str(response.get("url") or "")
            if capture_v1.TIMELINE_RESPONSE_MARKER not in url:
                return
            status = int(float(response.get("status") or 0))
            if status == 200:
                self.pending[str(params.get("requestId") or "")] = url
            else:
                counts["detail"] = f"TIMELINE_HTTP_{status}"
            return
        if method == "Network.loadingFailed":
            if self.pending.pop(str(params.get("requestId") or ""), None) is not None:
                counts["detail"] = "TIMELINE_LOADING_FAILED"
            return
        if method != "Network.loadingFinished":
            return
        request_id = str(params.get("requestId") or "")
        url = self.pending.pop(request_id, None)
        if url is None:
            return
        body = page_call(client.command, "Network.getResponseBody", {"requestId": request_id},
                         timeout_seconds=BODY_TIMEOUT_SECONDS)
        text = str(body.get("body") or "")
        raw = base64.b64decode(text) if body.get("base64Encoded") else text.encode("utf-8")
        tweets = self.module.recursive_tweet_extractor(json.loads(raw.decode("utf-8")))
        meta = {"raw_payload_ref": None, "raw_payload_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_payload_byte_size": len(raw), "source_url_or_ref": url.split("?", 1)[0]}
        counts["responses"] += 1
        counts["new_rows"] += len(self.append(tweets, meta))
        self.last_timeline_mono = self.mono_fn()
        self.last_timeline_utc = _iso(self.now_fn())
        if self.light_pending:
            self.light_hits += 1
            self.light_pending = False

    def _drain(self, client: Any, seconds: float, counts: dict[str, Any], page_call: Callable[..., Any],
               *, until_response: bool) -> None:
        """Read events for up to ``seconds``; stop shortly after a timeline response when asked."""
        end = time.monotonic() + max(0.0, seconds)
        first = counts["responses"]
        cut = False
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0 or self.should_stop():
                return
            event = page_call(client.event, timeout_seconds=min(0.5, max(0.01, remaining)))
            if event is not None:
                self._consume(client, event, counts, page_call)
            if until_response and not cut and counts["responses"] > first:
                cut = True
                end = min(end, time.monotonic() + AFTER_RESPONSE_SECONDS)

    def _list_targets(self) -> list[dict[str, Any]]:
        return self.targets_fn(cdp_url=self.cdp_url, timeout_seconds=CATALOG_TIMEOUT_SECONDS)

    def _open_session(self, result: dict[str, Any], page_call: Callable[..., Any]) -> Any:
        try:
            targets = self._list_targets()
            target = next((dict(row) for row in targets
                           if self.preferred_target_id and row.get("id") == self.preferred_target_id
                           and (_is_list_url(row.get("url"))
                                or capture_v1._visible_url_is_login_redirect(str(row.get("url") or "")))), None)
            target = target or capture_v1.select_reusable_x_target(targets)
        except Exception as exc:  # noqa: BLE001 - the feed records the cause and keeps running
            result.update(state="CDP_UNAVAILABLE",
                          detail=capture_v1.classify_capture_exception(exc, phase="CDP_TARGET_DISCOVERY")[1])
            return None
        if target is None:
            result.update(state="NO_X_PAGE", detail="NO_REUSABLE_X_PAGE_TARGET")
            return None
        target_id, url = str(target.get("id") or ""), str(target.get("url") or "")
        result["target_id"] = target_id
        if capture_v1._visible_url_is_login_redirect(url):
            result.update(state="REAUTH_REQUIRED", detail="LOGIN_REDIRECT_OBSERVED")
            return None
        try:
            client = page_call(self.client_factory, str(target["webSocketDebuggerUrl"]),
                               timeout_seconds=SESSION_TIMEOUT_SECONDS)
        except Exception as exc:  # noqa: BLE001
            result.update(state="CDP_UNAVAILABLE",
                          detail=capture_v1.classify_capture_exception(exc, phase="CDP_TARGET_CONNECT")[1])
            return None
        try:
            page_call(client.command, "Page.enable", timeout_seconds=SESSION_TIMEOUT_SECONDS)
            page_call(client.command, "Network.enable", dict(NETWORK_BUFFER), timeout_seconds=SESSION_TIMEOUT_SECONDS)
        except Exception as exc:  # noqa: BLE001
            try:
                client.close()
            except Exception:  # noqa: BLE001
                pass
            result.update(state="CAPTURE_FAILED",
                          detail=capture_v1.classify_capture_exception(exc, phase="SESSION_ATTACH")[1])
            return None
        self.session, self.session_target_id, self.session_url, self.pending = client, target_id, url, {}
        result["attached"] = True
        if _is_list_url(url):
            # Exactly one list tab: close list tabs an earlier replacement left behind.
            orphans = [str(row.get("id") or "") for row in targets
                       if _is_list_url(row.get("url")) and str(row.get("id") or "") != target_id]
            if orphans:
                closed, failed = self._close_targets(orphans, method="http")
                result["orphans_closed"] = closed
                if failed:
                    result["orphans_not_closed"] = failed
        return client

    def listen(self, seconds: float) -> int:
        """Between ticks: read what the page fetches by itself; returns the new rows it added."""
        client = self.session
        if client is None:
            return 0
        before = self._carry["new_rows"]
        marker: dict[str, Any] = {}
        try:
            self._drain(client, seconds, self._carry, self._page_call(marker), until_response=True)
        except Exception as exc:  # noqa: BLE001 - the next tick reattaches and reports it
            self._carry["detail"] = capture_v1.classify_capture_exception(exc, phase="IDLE_LISTEN")[1]
            self.close_session()
        return self._carry["new_rows"] - before

    def tick(self, *, force_reload: bool = False, settle_seconds: float = TIMELINE_SETTLE_SECONDS,
             light_settle_seconds: float = LIGHT_SETTLE_SECONDS,
             scroll_seconds: float = capture_v1.SCROLL_WAIT_MS / 1000.0,
             light_after: float = LIGHT_REFRESH_AFTER_SECONDS,
             reload_after: float = RELOAD_AFTER_SECONDS) -> dict[str, Any]:
        """One capture tick on the kept session.

        Timeline responses the page fetched since the last tick count first. A quiet page gets X's
        own "load new posts" key after ``light_after`` seconds and one full reload after
        ``reload_after`` seconds, never more than one reload per ``reload_after``. States:
        CAPTURED (a timeline response was read), LISTENING (quiet, nothing due: not a failure),
        NO_TIMELINE_RESPONSE (a reload brought none: a failure) and the attach failures.
        """
        started = time.monotonic()
        carry, self._carry = self._carry, self._new_counts()
        result: dict[str, Any] = {"state": "CAPTURE_FAILED", "attempted_utc": _iso(self.now_fn()),
                                  "responses": carry["responses"], "new_rows": carry["new_rows"],
                                  "api_requests": carry["api_requests"], "detail": None, "refresh": None}
        if carry["detail"]:
            result["idle_detail"] = carry["detail"]

        def finish(**updates: Any) -> dict[str, Any]:
            result.update(updates)
            result["duration_seconds"] = round(time.monotonic() - started, 2)
            result["last_timeline_utc"] = self.last_timeline_utc
            result["light_refresh"] = {"hits": self.light_hits, "misses": self.light_misses}
            return result

        page_call = self._page_call(result)
        client, opened = self.session, False
        if client is None:
            client = self._open_session(result, page_call)
            if client is None:
                return finish()
            opened = True
        result["target_id"] = self.session_target_id
        try:
            self._drain(client, 0.05, result, page_call, until_response=False)
            now = self.mono_fn()

            def since(mark: float | None) -> float:
                return float("inf") if mark is None else now - mark

            quiet = result["responses"] == 0
            reload_due = force_reload or opened or since(self.last_timeline_mono) >= reload_after
            if quiet and reload_due and (force_reload or since(self.last_reload_mono) >= reload_after):
                result["refresh"] = "reload"
                self.last_reload_mono = now
                if capture_v1.TARGET_LIST_ID in self.session_url:
                    page_call(client.command, "Page.reload", timeout_seconds=30.0)
                else:
                    page_call(client.command, "Page.navigate", {"url": capture_v1.TARGET_LIST_URL},
                              timeout_seconds=30.0)
                    self.session_url = capture_v1.TARGET_LIST_URL
                capture_v1.record_browser_interaction_event(
                    "navigation", reason="X_LIST_FEED_MINUTE_RELOAD", destination="x_ingestion")
                self._drain(client, settle_seconds, result, page_call, until_response=True)
                if result["new_rows"] >= SCROLL_WHEN_NEW_AT_LEAST:
                    page_call(client.command, "Runtime.evaluate", {
                        "expression": "window.scrollTo(0, document.body.scrollHeight)", "returnByValue": True})
                    self._drain(client, scroll_seconds, result, page_call, until_response=False)
            elif quiet and since(self.last_timeline_mono) >= light_after and since(self.last_light_mono) >= light_after:
                # X's own keyboard shortcut for "load new posts": one timeline request, no page load.
                result["refresh"] = "light"
                self.last_light_mono = now
                self.light_pending = True
                for kind in ("keyDown", "keyUp"):
                    params = {"type": kind, **LIGHT_REFRESH_KEY}
                    if kind == "keyDown":
                        params["text"] = "."
                    page_call(client.command, "Input.dispatchKeyEvent", params, timeout_seconds=10.0)
                capture_v1.record_browser_interaction_event(
                    "x_capture", reason="X_LIST_FEED_LIGHT_REFRESH", destination="x_ingestion")
                self._drain(client, light_settle_seconds, result, page_call, until_response=True)
                if self.light_pending:
                    self.light_misses += 1
                    self.light_pending = False
            if result["refresh"] or opened:
                evaluated = page_call(client.command, "Runtime.evaluate",
                                      {"expression": "window.location.href", "returnByValue": True})
                value = evaluated.get("result") if isinstance(evaluated.get("result"), dict) else {}
                href = str(value.get("value") or "")
                if href:
                    self.session_url = href
                if capture_v1._visible_url_is_login_redirect(href):
                    self.close_session()
                    return finish(state="REAUTH_REQUIRED", detail="LOGIN_REDIRECT_OBSERVED")
            if result["responses"]:
                return finish(state="CAPTURED")
            if result["refresh"] == "reload":
                return finish(state="NO_TIMELINE_RESPONSE",
                              detail=result["detail"] or "NO_TIMELINE_RESPONSE_WITHIN_SETTLE")
            age = since(self.last_timeline_mono)
            return finish(state="LISTENING", detail=result["detail"] or "NO_NEW_TIMELINE_RESPONSE_YET",
                          timeline_age_seconds=None if age == float("inf") else round(age, 1))
        except Exception as exc:  # noqa: BLE001
            if result.get("page_socket_failed"):
                self.close_session()
            return finish(state="CAPTURE_FAILED",
                          detail=capture_v1.classify_capture_exception(exc, phase="MINUTE_CAPTURE")[1])

    def capture_once(self, *, max_seconds: float = 40.0,
                     settle_seconds: float = TIMELINE_SETTLE_SECONDS,
                     scroll_seconds: float = capture_v1.SCROLL_WAIT_MS / 1000.0) -> dict[str, Any]:
        """One full capture on a fresh attachment (``--once``); the runner uses ``tick``."""
        self.close_session()
        try:
            return self.tick(force_reload=True, settle_seconds=min(settle_seconds, max_seconds),
                             scroll_seconds=scroll_seconds)
        finally:
            self.close_session()

    # ---- CC-785: replacing a failed list tab -------------------------------------------------

    def _http(self, path: str, *, method: str = "GET", timeout: float) -> bytes:
        with self.http_open(Request(f"{self.cdp_url}{path}", method=method), timeout=timeout) as response:
            return response.read()

    def _browser_client(self) -> Any:
        version = json.loads(self._http("/json/version", timeout=CATALOG_TIMEOUT_SECONDS).decode("utf-8"))
        url = str(version.get("webSocketDebuggerUrl") or "") if isinstance(version, dict) else ""
        if not url:
            raise capture_v1.IngestCaptureError("BROWSER_TARGET_ENDPOINT_MISSING")
        return self.client_factory(url, timeout_seconds=SESSION_TIMEOUT_SECONDS)

    def _create_list_target(self, method: str) -> tuple[str, str]:
        if method == "browser":
            client = self._browser_client()
            try:
                created = client.command("Target.createTarget", {"url": capture_v1.TARGET_LIST_URL},
                                         timeout_seconds=TAB_CREATE_TIMEOUT_SECONDS)
            finally:
                client.close()
            return str(created.get("targetId") or ""), capture_v1.TARGET_LIST_URL
        fresh = json.loads(self._http(f"/json/new?{quote(capture_v1.TARGET_LIST_URL, safe='')}", method="PUT",
                                      timeout=TAB_CREATE_TIMEOUT_SECONDS).decode("utf-8"))
        if not isinstance(fresh, dict):
            return "", ""
        return str(fresh.get("id") or ""), str(fresh.get("url") or "")

    def _close_targets(self, target_ids: Iterable[str], *, method: str) -> tuple[list[str], list[str]]:
        closed: list[str] = []
        failed: list[str] = []
        ids = [target_id for target_id in target_ids if target_id]
        if not ids:
            return closed, failed
        client = None
        try:
            if method == "browser":
                client = self._browser_client()
            for target_id in ids:
                try:
                    if client is not None:
                        done = client.command("Target.closeTarget", {"targetId": target_id},
                                              timeout_seconds=TAB_CLOSE_TIMEOUT_SECONDS)
                        ok = bool(done.get("success", True))
                    else:
                        reply = self._http(f"/json/close/{quote(target_id, safe='')}", timeout=TAB_CLOSE_TIMEOUT_SECONDS)
                        ok = reply.decode("utf-8").strip() == "Target is closing"
                except Exception:  # noqa: BLE001 - a lost reply is recorded, never retried here
                    ok = False
                (closed if ok else failed).append(target_id)
        except Exception:  # noqa: BLE001
            failed.extend(target_id for target_id in ids if target_id not in closed and target_id not in failed)
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:  # noqa: BLE001
                    pass
        return closed, failed

    def heal_target(self, target_id: str, *, method: str = "http") -> dict[str, Any]:
        """Open a fresh list tab, adopt it even if its reply came late, then close the failed tab and
        every other list tab, so exactly one stays. ``method`` "http" uses /json/new, "browser" the
        browser target's Target.createTarget (the second step of the self-heal)."""
        result: dict[str, Any] = {"state": "TAB_REPLACEMENT_FAILED", "method": method, "old_target_id": target_id,
                                  "attempted_utc": _iso(self.now_fn())}
        self.close_session()
        try:
            before = self._list_targets()
            target = next((row for row in before if str(row.get("id") or "") == target_id), None)
            url = str((target or {}).get("url") or "")
            if capture_v1._visible_url_is_login_redirect(url):
                return {**result, "state": "REAUTH_REQUIRED", "detail": "LOGIN_REDIRECT_OBSERVED"}
            if target is not None and not _is_list_url(url):
                return {**result, "state": "TAB_REPLACEMENT_SKIPPED", "detail": "FAILED_TARGET_NOT_LIST_PAGE"}
            known = {str(row.get("id") or "") for row in before}
            new_id, new_url, create_detail = "", "", None
            try:
                new_id, new_url = self._create_list_target(method)
            except Exception as exc:  # noqa: BLE001 - a late reply may still have created the tab
                create_detail = capture_v1.classify_capture_exception(exc, phase="TAB_REPLACEMENT")[1]
            if not new_id or new_id in known:
                try:
                    after = self._list_targets()
                except Exception:  # noqa: BLE001
                    after = []
                adopted = next((row for row in after if str(row.get("id") or "") not in known and (
                    _is_list_url(row.get("url"))
                    or capture_v1._visible_url_is_login_redirect(str(row.get("url") or "")))), None)
                if adopted is None:
                    return {**result, "detail": create_detail or "NEW_LIST_TARGET_INVALID"}
                new_id, new_url = str(adopted.get("id") or ""), str(adopted.get("url") or "")
                result["adopted_late_target"] = True
                if create_detail:
                    result["create_detail"] = create_detail
            login = capture_v1._visible_url_is_login_redirect(new_url)
            if not login and not _is_list_url(new_url):
                return {**result, "detail": "NEW_LIST_TARGET_INVALID"}
            result["new_target_id"] = new_id
            # If closing the old tab fails, the next capture still uses the new one.
            self.preferred_target_id = new_id
            if login:
                return {**result, "state": "REAUTH_REQUIRED", "detail": "LOGIN_REDIRECT_OBSERVED"}
            stale = [str(row.get("id") or "") for row in before
                     if _is_list_url(row.get("url")) and str(row.get("id") or "") != new_id]
            closed, failed = self._close_targets(stale, method=method)
            if closed:
                result["closed_target_ids"] = closed
            if failed:
                result["close_failed_target_ids"] = failed
                if target_id in failed:
                    return {**result, "detail": "CDP_TARGET_CLOSE_NOT_ACKNOWLEDGED"}
            return {**result, "state": "TAB_REPLACED", "replaced_utc": _iso(self.now_fn())}
        except Exception as exc:  # noqa: BLE001
            return {**result, "detail": capture_v1.classify_capture_exception(exc, phase="TAB_REPLACEMENT")[1]}

    def replace_hung_target(self, target_id: str) -> dict[str, Any]:
        """CC-595 name, kept for callers: the first self-heal step."""
        return self.heal_target(target_id, method="http")


def _log(path: Path, record: Mapping[str, Any]) -> None:
    try:
        if path.exists() and path.stat().st_size > LOG_MAX_BYTES:
            os.replace(path, path.with_suffix(".log.1"))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        pass


class FeedRunner:
    """One tick every 15 s in market hours (60 s outside): keep the browser, capture, rewrite the feed."""

    def __init__(self, *, feed_path: Path = FEED_PATH, log_path: Path = LOG_PATH,
                 bootstrap: Any = None, capture_factory: Callable[[], Any] = MinuteCapture,
                 clock: Callable[[], float] = time.monotonic,
                 now_fn: Callable[[], datetime] | None = None, sidecar_dir: Path | None = None) -> None:
        if bootstrap is None:
            from live_contentops import ingestion_bootstrap_v1 as bootstrap
        self.bootstrap = bootstrap
        self.feed_path, self.log_path = feed_path, log_path
        self.capture_factory, self.clock = capture_factory, clock
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self.sidecar_dir = sidecar_dir
        self.capture: Any = None
        self.tail = SidecarTail()
        self.last_launch: float | None = None
        self.owner_checked: float | None = None
        self.owner_key: Any = None
        self.failure_streak = 0
        self.first_failure_utc: str | None = None
        self.failure_cause: str | None = None
        self.last_good_utc: datetime | None = None
        self.p1: dict[str, Any] | None = None
        self.last_p1: dict[str, Any] | None = None
        self.started_utc = self.now_fn()
        self.stop_path: Path | None = None
        # Keep the heal record, the last good read and a raised P1 across ordinary runner
        # restarts in the existing feed, without another state file.
        self.last_tab_replacement: dict[str, Any] = {}
        try:
            previous = json.loads(Path(feed_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            previous = None
        if isinstance(previous, dict):
            capture = previous.get("capture") if isinstance(previous.get("capture"), dict) else {}
            health = previous.get("health") if isinstance(previous.get("health"), dict) else {}
            retained = health.get("last_heal") or capture.get("last_tab_replacement")
            if isinstance(retained, dict):
                self.last_tab_replacement = dict(retained)
            self.last_good_utc = _parse_utc(health.get("last_good_capture_utc"))
            if isinstance(health.get("p1"), dict):
                self.p1 = dict(health["p1"])
            if isinstance(health.get("last_p1"), dict):
                self.last_p1 = dict(health["last_p1"])

    def stop_requested(self) -> bool:
        try:
            return self.stop_path is not None and Path(self.stop_path).exists()
        except OSError:
            return False

    def next_interval(self) -> float:
        return MARKET_INTERVAL_SECONDS if in_market_hours(self.now_fn()) else INTERVAL_SECONDS

    def idle(self, seconds: float, sleep: Callable[[float], None] = time.sleep) -> bool:
        """Wait for the next tick while reading the page's own fetches; True when new posts came in."""
        capture = self.capture
        if capture is not None and getattr(capture, "session", None) is not None and hasattr(capture, "listen"):
            return capture.listen(seconds) > 0
        sleep(seconds)
        return False

    def _account(self, captured: dict[str, Any], *, moment: datetime) -> None:
        """Failure streak, the two-step self-heal and the P1 alarm (CC-785)."""
        state = str(captured.get("state") or "")
        if state == "CAPTURED":
            self.last_good_utc = _parse_utc(captured.get("last_timeline_utc")) or moment
            self.failure_streak, self.first_failure_utc, self.failure_cause = 0, None, None
            if self.p1 is not None:
                self.last_p1 = {**self.p1, "cleared_utc": _iso(moment)}
                self.p1 = None
                captured["p1_event"] = "CLEARED"
        elif state in FAILURE_STATES:
            self.failure_streak += 1
            self.first_failure_utc = self.first_failure_utc or str(captured.get("attempted_utc") or _iso(moment))
            self.failure_cause = f"{state}:{captured.get('detail') or captured.get('browser') or ''}".rstrip(":")
        captured["failure_streak"] = self.failure_streak
        target_id = str(captured.get("target_id") or "")
        if state in TAB_FAILURE_STATES and target_id and self.failure_streak >= HEAL_AFTER_FAILURES:
            method = "http" if self.failure_streak == HEAL_AFTER_FAILURES else "browser"
            last_attempt = _parse_utc(self.last_tab_replacement.get("attempted_utc"))
            elapsed = (moment - last_attempt).total_seconds() if last_attempt else float("inf")
            # Step 1 at two failures (unless a heal ran in the last minute), step 2 at three, then
            # step 2 again at most every TAB_REPLACEMENT_COOLDOWN_SECONDS while failures go on.
            if self.failure_streak == HEAL_AFTER_FAILURES:
                due = elapsed >= RELOAD_AFTER_SECONDS
            elif self.failure_streak == P1_AFTER_FAILURES:
                due = True
            else:
                due = elapsed >= TAB_REPLACEMENT_COOLDOWN_SECONDS
            if due and hasattr(self.capture, "heal_target"):
                heal = self.capture.heal_target(target_id, method=method)
                heal["failure_streak"] = self.failure_streak
                self.last_tab_replacement = heal
                captured["tab_replacement"] = heal
                if heal["state"] == "REAUTH_REQUIRED":
                    captured.update(state="REAUTH_REQUIRED", detail="LOGIN_REDIRECT_OBSERVED")
                    self.failure_cause = "REAUTH_REQUIRED:LOGIN_REDIRECT_OBSERVED"
        if self.failure_streak >= P1_AFTER_FAILURES and self.p1 is None:
            self.p1 = {"level": "P1", "raised_utc": _iso(moment), "first_failure_utc": self.first_failure_utc,
                       "failure_streak": self.failure_streak, "cause": self.failure_cause,
                       "plain": (f"X-list feed: {self.failure_streak} failed captures in a row since "
                                 f"{self.first_failure_utc}; latest cause {self.failure_cause}. "
                                 "News from the list is not reaching Main.")}
            captured["p1_event"] = "RAISED"
        if self.p1 is not None:
            self.p1["failure_streak"] = max(int(self.p1.get("failure_streak") or 0), self.failure_streak)
            self.p1["cause"] = self.failure_cause or self.p1.get("cause")
        if self.last_tab_replacement:
            captured["last_tab_replacement"] = self.last_tab_replacement

    def _health(self, moment: datetime) -> dict[str, Any]:
        market = in_market_hours(moment)
        stale_after = STALE_AFTER_MARKET_SECONDS if market else STALE_AFTER_SECONDS
        age = (moment - self.last_good_utc).total_seconds() if self.last_good_utc else None
        stale = age is None or age >= stale_after or self.failure_streak >= HEAL_AFTER_FAILURES
        return {
            "state": "P1" if self.p1 else ("STALE" if stale else "OK"),
            "stale": stale,
            "stale_since_utc": _iso(self.last_good_utc or self.started_utc) if stale else None,
            "last_good_capture_utc": _iso(self.last_good_utc) if self.last_good_utc else None,
            "last_good_age_seconds": round(age, 1) if age is not None else None,
            "stale_after_seconds": stale_after,
            "failure_streak": self.failure_streak,
            "first_failure_utc": self.first_failure_utc,
            "failure_cause": self.failure_cause,
            "last_heal": self.last_tab_replacement or None,
            "p1": self.p1,
            "last_p1": self.last_p1,
            "interval_seconds": MARKET_INTERVAL_SECONDS if market else INTERVAL_SECONDS,
            "market_hours": market,
            "reading_rule": READING_RULE,
        }

    def _owner_key(self) -> Any:
        key_fn = getattr(self.bootstrap, "listener_owner_key", None)
        if key_fn is None:
            return None
        try:
            return key_fn(self.bootstrap.INGESTION_CDP_PORT)
        except Exception:  # noqa: BLE001 - the timed recheck covers a failed native read
            return None

    def _browser_ready(self) -> dict[str, Any]:
        now = self.clock()
        port = self.bootstrap.INGESTION_CDP_PORT
        alive = self.bootstrap.probe_cdp(port)["cdp_alive"]
        slow = False
        # CC-785 cause 2: a slow answer is not a dead browser. Retry with longer, bounded timeouts
        # (6 s, then 12 s: at most 21 s in all) before the browser counts as down.
        for timeout in PROBE_RETRY_TIMEOUTS[:max(0, PROBE_ATTEMPTS - 1)]:
            if alive or self.stop_requested():
                break
            alive = self.bootstrap.probe_cdp(port, timeout=timeout)["cdp_alive"]
            slow = alive
        if alive:
            extra = {"probe": "SLOW"} if slow else {}
            if self.owner_checked is not None:
                # CC-785 cause 3: prove the owner once, then recheck that the same PID with the same
                # start time still holds the port (native, milliseconds) instead of PowerShell.
                key = self._owner_key() if self.owner_key is not None else None
                if self.owner_key is not None and key is not None:
                    if key == self.owner_key:
                        return {"ready": True, **extra}
                elif now - self.owner_checked < OWNER_RECHECK_SECONDS:
                    return {"ready": True, **extra}
            state = self.bootstrap.ingestion_process_state()
            if state["state"] == self.bootstrap.STATE_READY:
                self.owner_checked = now
                self.owner_key = ((int(state["pid"]), int(state["start"])) if state.get("pid") and state.get("start")
                                  else self._owner_key())
                return {"ready": True, "browser": state["state"], "detail": state.get("detail"), **extra}
            self.owner_checked, self.owner_key = None, None
            return {"ready": False, "browser": state["state"], "detail": state.get("detail")}
        self.owner_checked, self.owner_key = None, None
        if self.last_launch is not None and now - self.last_launch < RELAUNCH_AFTER_SECONDS:
            return {"ready": False, "browser": "UNAVAILABLE", "detail": "WAITING_BEFORE_NEXT_LAUNCH"}
        self.last_launch = now
        launched = self.bootstrap.ensure_ingestion_runtime()
        if launched.get("status") not in {self.bootstrap.STATE_LAUNCHED, self.bootstrap.STATE_ALREADY_READY}:
            return {"ready": False, "browser": launched.get("status"), "detail": launched.get("detail")}
        session = self.bootstrap.probe_ingestion_session()
        self.owner_checked = now
        self.owner_key = self._owner_key()
        return {"ready": session.get("auth_state") != self.bootstrap.STATE_REAUTH_REQUIRED,
                "browser": launched.get("status"), "auth": session.get("auth_state"),
                "detail": session.get("detail")}

    def iterate(self) -> dict[str, Any]:
        browser = self._browser_ready()
        if browser["ready"]:
            if self.capture is None:
                self.capture = self.capture_factory()
                if hasattr(self.capture, "should_stop"):
                    self.capture.should_stop = self.stop_requested
                if hasattr(self.capture, "preferred_target_id"):
                    self.capture.preferred_target_id = self.last_tab_replacement.get("new_target_id")
            captured = self.capture.tick() if hasattr(self.capture, "tick") else self.capture.capture_once()
            if browser.get("probe"):
                captured["browser_probe"] = browser["probe"]
            if captured.get("state") == "NO_X_PAGE":
                self.bootstrap.probe_ingestion_session()
        else:
            if self.capture is not None and hasattr(self.capture, "close_session"):
                self.capture.close_session()
            captured = {"state": "BROWSER_NOT_READY", "attempted_utc": _iso(self.now_fn()),
                        "new_rows": 0, "browser": browser.get("browser"), "detail": browser.get("detail")}
        moment = self.now_fn()
        self._account(captured, moment=moment)
        health = self._health(moment)
        feed = build_feed(now=moment, capture=captured, tail=self.tail, sidecar_dir=self.sidecar_dir, health=health)
        written = write_feed(self.feed_path, feed)
        flags = shock_flags(feed, now=moment)
        flags_written = _atomic_write(self.feed_path.with_name(FLAGS_NAME), render_flags(flags))
        record = {"at_utc": feed["generated_at_utc"], "capture": captured, "rows": feed["row_count"],
                  "newest_age_seconds": feed["newest_age_seconds"], "feed_written": written,
                  "flags": len(flags), "flags_written": flags_written,
                  "health": {key: health[key] for key in ("state", "stale_since_utc", "last_good_age_seconds",
                                                          "failure_streak", "failure_cause")}}
        if captured.get("p1_event"):
            record["p1"] = {"event": captured["p1_event"], **(self.p1 or self.last_p1 or {})}
        _log(self.log_path, record)
        return record


def _hold_lock(path: Path) -> Any:
    """One runner per machine: an exclusive byte lock the OS releases when the process ends."""
    import msvcrt

    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+b")
    try:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        handle.close()
        return None
    return handle


def _start_stop_watchdog(stop_path: Path, done: threading.Event, *, grace_seconds: float,
                         hard_exit: Callable[[int], Any], log_path: Path) -> threading.Thread:
    """End the process when STOP has been present for ``grace_seconds`` and the loop still runs.

    The loop's own waits honour STOP within seconds; this covers a call that blocks (a hung CDP
    socket or a PowerShell child). The feed writes are atomic replaces, and the OS releases the lock.
    """
    def watch() -> None:
        seen: float | None = None
        while not done.wait(min(1.0, max(0.05, grace_seconds / 4))):
            if not stop_path.exists():
                seen = None
                continue
            seen = seen if seen is not None else time.monotonic()
            if time.monotonic() - seen >= grace_seconds:
                _log(log_path, {"at_utc": _iso(datetime.now(timezone.utc)), "stop": "WATCHDOG_EXIT",
                                "detail": f"STOP present {grace_seconds:.0f} s while a call blocked"})
                hard_exit(0)
                return

    thread = threading.Thread(target=watch, name="x-list-feed-stop-watchdog", daemon=True)
    thread.start()
    return thread


def run_forever(*, interval_seconds: float | None = None, stop_path: Path = STOP_PATH,
                lock_path: Path = LOCK_PATH, runner: FeedRunner | None = None,
                sleep: Callable[[float], None] = time.sleep, max_iterations: int | None = None,
                stop_grace_seconds: float = STOP_GRACE_SECONDS,
                hard_exit: Callable[[int], Any] = os._exit) -> dict[str, Any]:
    """Tick every 15 s in market hours and 60 s outside (``interval_seconds`` fixes it); between
    ticks the runner reads the page's own fetches and ticks at once when new posts arrive. A STOP
    file ends it within ``stop_grace_seconds``, even mid-tick."""
    lock = _hold_lock(lock_path)
    if lock is None:
        return {"state": "ALREADY_RUNNING"}
    # Import the browser launcher's module now, so a later code update cannot mix versions.
    from live_contentops import daily_app_launcher_v1  # noqa: F401
    runner = runner or FeedRunner()
    if hasattr(runner, "stop_path"):
        runner.stop_path = stop_path
    iterations = 0
    done = threading.Event()
    _start_stop_watchdog(stop_path, done, grace_seconds=stop_grace_seconds, hard_exit=hard_exit,
                         log_path=getattr(runner, "log_path", LOG_PATH))
    try:
        while not stop_path.exists():
            started = time.monotonic()
            try:
                runner.iterate()
            except Exception as exc:  # noqa: BLE001 - one bad minute must not end the feed
                _log(runner.log_path, {"at_utc": _iso(datetime.now(timezone.utc)),
                                       "error": type(exc).__name__, "detail": str(exc)[:200]})
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            interval = interval_seconds
            if interval is None:
                interval = runner.next_interval() if hasattr(runner, "next_interval") else INTERVAL_SECONDS
            idle = getattr(runner, "idle", None)
            remaining = interval - (time.monotonic() - started)
            while remaining > 0 and not stop_path.exists():
                step = min(5.0, remaining)
                if idle is not None:
                    try:
                        if idle(step, sleep):
                            break
                    except Exception:  # noqa: BLE001 - waiting must not end the feed
                        sleep(step)
                else:
                    sleep(step)
                remaining = interval - (time.monotonic() - started)
    finally:
        done.set()
        lock.close()
    return {"state": "STOPPED", "iterations": iterations}
