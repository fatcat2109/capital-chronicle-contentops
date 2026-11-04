"""CC-258: Jim's X list as one private feed, refreshed every minute (Jim's decision 71).

Two deterministic parts, with no model call:

- ``MinuteCapture.capture_once``: one light capture of the locked X list through the existing
  ingestion browser (Chrome ``CapitalChronicleBot`` on CDP 9222, see ingestion_bootstrap_v1).
  It reloads the list page once, reads the ``ListLatestTweetsTimeline`` responses and appends
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

Use: private and internal, under JIM_X_LIST_PRIVATE_MAIN_RESEARCH_USE_20261029. The feed is
context. Main's market-context sweep reads it first, a burst may start a shock analysis pass
(CC-087), the newsroom takes leads from it and Codex Data keeps its rows. It never arms or
admits an order (global C7), its post text is never republished, and a post is never treated
as a confirmed fact.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from live_contentops import x_list_ingest_capture_v1 as capture_v1
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_dir

SCHEMA_VERSION = "contentops.x_list_feed.v1"
FEED_DIR = Path(r"A:\Capital Chronicle\Runtime\ContentOps\x_list_feed")
FEED_PATH = FEED_DIR / "x_list_feed_v1.json"
STOP_PATH = FEED_DIR / "STOP"
LOCK_PATH = FEED_DIR / "runner_v1.lock"
LOG_PATH = FEED_DIR / "runner_v1.log"
LOG_MAX_BYTES = 2_000_000
WINDOW_HOURS = 24.0
INTERVAL_SECONDS = 60.0
RELAUNCH_AFTER_SECONDS = 1800.0
OWNER_RECHECK_SECONDS = 1800.0
SCROLL_WHEN_NEW_AT_LEAST = 15
FLAGS_NAME = "x_list_shock_flags_v1.json"
FAST_SQUAWKS = ("FirstSquawk", "financialjuice", "DeItaone", "wallstengine", "zerohedge")
FLAG_WINDOW_MINUTES = 15.0
FLAG_MAX = 40
X_EPOCH_MS = 1288834974657
GMT7 = timezone(timedelta(hours=7))
CAPTURE_ROUTE = "x_list_feed_v1_minute"
GRANT = "JIM_X_LIST_PRIVATE_MAIN_RESEARCH_USE_20261029"
USE = {
    "grant": GRANT,
    "consumers": ["internal_research", "narrative_context"],
    "may": [
        "Main market-context sweep: read this feed first, then search the web",
        "start a shock analysis pass on a burst (CC-087)",
        "newsroom leads, checked against primary sources before publication",
        "Codex Data keeps the rows with their clocks",
    ],
    "never": [
        "arm, admit or size an order (global C7)",
        "republish or quote post text in public or subscriber output",
        "model training",
        "share with third parties",
        "treat a post as a confirmed fact",
    ],
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
    return {
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
               tail: SidecarTail | None = None) -> dict[str, Any]:
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
        "source": {"list_url": capture_v1.TARGET_LIST_URL, "sidecar_dir": str(directory)},
        "use": USE,
        "fields": {
            "posted_utc": "the post id's own clock, milliseconds",
            "ingested_utc": "when the capture saw the post (whole seconds for rows from the 30-minute capture)",
            "lag_seconds": "ingested_utc minus posted_utc",
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
                 now_fn: Callable[[], datetime] | None = None) -> None:
        self.module = module or capture_v1.load_data_ingestion_module()
        self.cdp_url = cdp_url
        self.client_factory = client_factory
        self.targets_fn = targets_fn or capture_v1.list_cdp_page_targets
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self.keys: set[str] = set()
        self._load_recent_keys()

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

    def capture_once(self, *, max_seconds: float = 40.0,
                     settle_seconds: float = capture_v1.RELOAD_SETTLE_MS / 1000.0,
                     scroll_seconds: float = capture_v1.SCROLL_WAIT_MS / 1000.0) -> dict[str, Any]:
        started = time.monotonic()
        result: dict[str, Any] = {"state": "CAPTURE_FAILED", "attempted_utc": _iso(self.now_fn()),
                                  "responses": 0, "new_rows": 0, "detail": None}

        def finish(**updates: Any) -> dict[str, Any]:
            result.update(updates)
            result["duration_seconds"] = round(time.monotonic() - started, 2)
            return result

        try:
            target = capture_v1.select_reusable_x_target(self.targets_fn(cdp_url=self.cdp_url, timeout_seconds=5.0))
        except Exception as exc:  # noqa: BLE001 - the feed records the cause and keeps running
            return finish(state="CDP_UNAVAILABLE",
                          detail=capture_v1.classify_capture_exception(exc, phase="CDP_TARGET_DISCOVERY")[1])
        if target is None:
            return finish(state="NO_X_PAGE", detail="NO_REUSABLE_X_PAGE_TARGET")
        if capture_v1._visible_url_is_login_redirect(str(target.get("url") or "")):
            return finish(state="REAUTH_REQUIRED", detail="LOGIN_REDIRECT_OBSERVED")
        try:
            client = self.client_factory(str(target["webSocketDebuggerUrl"]),
                                         timeout_seconds=capture_v1.DIRECT_CDP_COMMAND_TIMEOUT_SECONDS)
        except Exception as exc:  # noqa: BLE001
            return finish(state="CDP_UNAVAILABLE",
                          detail=capture_v1.classify_capture_exception(exc, phase="CDP_TARGET_CONNECT")[1])
        deadline = started + max_seconds
        pending: dict[str, str] = {}

        def consume(event: Mapping[str, Any]) -> None:
            method = str(event.get("method") or "")
            params = event.get("params") if isinstance(event.get("params"), dict) else {}
            if method == "Network.responseReceived":
                response = params.get("response") if isinstance(params.get("response"), dict) else {}
                url = str(response.get("url") or "")
                if capture_v1.TIMELINE_RESPONSE_MARKER not in url:
                    return
                status = int(float(response.get("status") or 0))
                if status == 200:
                    pending[str(params.get("requestId") or "")] = url
                else:
                    result["detail"] = f"TIMELINE_HTTP_{status}"
                return
            if method != "Network.loadingFinished":
                return
            request_id = str(params.get("requestId") or "")
            url = pending.pop(request_id, None)
            if url is None:
                return
            body = client.command("Network.getResponseBody", {"requestId": request_id}, timeout_seconds=10.0)
            text = str(body.get("body") or "")
            raw = base64.b64decode(text) if body.get("base64Encoded") else text.encode("utf-8")
            tweets = self.module.recursive_tweet_extractor(json.loads(raw.decode("utf-8")))
            meta = {"raw_payload_ref": None, "raw_payload_sha256": hashlib.sha256(raw).hexdigest(),
                    "raw_payload_byte_size": len(raw), "source_url_or_ref": url.split("?", 1)[0]}
            result["responses"] += 1
            result["new_rows"] += len(self.append(tweets, meta))

        def drain(seconds: float) -> None:
            end = min(deadline, time.monotonic() + seconds)
            while time.monotonic() < end:
                event = client.event(timeout_seconds=min(0.5, max(0.01, end - time.monotonic())))
                if event is not None:
                    consume(event)

        try:
            client.command("Page.enable")
            client.command("Network.enable")
            if capture_v1.TARGET_LIST_ID in str(target.get("url") or ""):
                client.command("Page.reload", timeout_seconds=30.0)
            else:
                client.command("Page.navigate", {"url": capture_v1.TARGET_LIST_URL}, timeout_seconds=30.0)
            capture_v1.record_browser_interaction_event(
                "navigation", reason="X_LIST_FEED_MINUTE_RELOAD", destination="x_ingestion")
            drain(settle_seconds)
            if result["new_rows"] >= SCROLL_WHEN_NEW_AT_LEAST:
                client.command("Runtime.evaluate", {
                    "expression": "window.scrollTo(0, document.body.scrollHeight)", "returnByValue": True})
                drain(scroll_seconds)
            evaluated = client.command("Runtime.evaluate", {"expression": "window.location.href",
                                                            "returnByValue": True})
            value = evaluated.get("result") if isinstance(evaluated.get("result"), dict) else {}
            if capture_v1._visible_url_is_login_redirect(str(value.get("value") or "")):
                return finish(state="REAUTH_REQUIRED", detail="LOGIN_REDIRECT_OBSERVED")
            if result["responses"]:
                return finish(state="CAPTURED")
            return finish(state="NO_TIMELINE_RESPONSE", detail=result["detail"] or "NO_TIMELINE_RESPONSE_WITHIN_SETTLE")
        except Exception as exc:  # noqa: BLE001
            return finish(detail=capture_v1.classify_capture_exception(exc, phase="MINUTE_CAPTURE")[1])
        finally:
            try:
                client.close()
            except Exception:  # noqa: BLE001 - detaching must not hide the capture result
                pass


def _log(path: Path, record: Mapping[str, Any]) -> None:
    try:
        if path.exists() and path.stat().st_size > LOG_MAX_BYTES:
            os.replace(path, path.with_suffix(".log.1"))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        pass


class FeedRunner:
    """One iteration a minute: keep the ingestion browser, capture, then rewrite the feed."""

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

    def _browser_ready(self) -> dict[str, Any]:
        now = self.clock()
        alive = self.bootstrap.probe_cdp(self.bootstrap.INGESTION_CDP_PORT)["cdp_alive"]
        if alive and self.owner_checked is not None and now - self.owner_checked < OWNER_RECHECK_SECONDS:
            return {"ready": True}
        if alive:
            state = self.bootstrap.ingestion_process_state()
            self.owner_checked = now if state["state"] == self.bootstrap.STATE_READY else None
            return {"ready": state["state"] == self.bootstrap.STATE_READY, "browser": state["state"],
                    "detail": state.get("detail")}
        self.owner_checked = None
        if self.last_launch is not None and now - self.last_launch < RELAUNCH_AFTER_SECONDS:
            return {"ready": False, "browser": "UNAVAILABLE", "detail": "WAITING_BEFORE_NEXT_LAUNCH"}
        self.last_launch = now
        launched = self.bootstrap.ensure_ingestion_runtime()
        if launched.get("status") not in {self.bootstrap.STATE_LAUNCHED, self.bootstrap.STATE_ALREADY_READY}:
            return {"ready": False, "browser": launched.get("status"), "detail": launched.get("detail")}
        session = self.bootstrap.probe_ingestion_session()
        self.owner_checked = now
        return {"ready": session.get("auth_state") != self.bootstrap.STATE_REAUTH_REQUIRED,
                "browser": launched.get("status"), "auth": session.get("auth_state"),
                "detail": session.get("detail")}

    def iterate(self) -> dict[str, Any]:
        browser = self._browser_ready()
        if browser["ready"]:
            if self.capture is None:
                self.capture = self.capture_factory()
            captured = self.capture.capture_once()
            if captured.get("state") == "NO_X_PAGE":
                self.bootstrap.probe_ingestion_session()
        else:
            captured = {"state": "BROWSER_NOT_READY", "attempted_utc": _iso(self.now_fn()),
                        "new_rows": 0, "browser": browser.get("browser"), "detail": browser.get("detail")}
        moment = self.now_fn()
        feed = build_feed(now=moment, capture=captured, tail=self.tail, sidecar_dir=self.sidecar_dir)
        written = write_feed(self.feed_path, feed)
        flags = shock_flags(feed, now=moment)
        flags_written = _atomic_write(self.feed_path.with_name(FLAGS_NAME), render_flags(flags))
        record = {"at_utc": feed["generated_at_utc"], "capture": captured, "rows": feed["row_count"],
                  "newest_age_seconds": feed["newest_age_seconds"], "feed_written": written,
                  "flags": len(flags), "flags_written": flags_written}
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


def run_forever(*, interval_seconds: float = INTERVAL_SECONDS, stop_path: Path = STOP_PATH,
                lock_path: Path = LOCK_PATH, runner: FeedRunner | None = None,
                sleep: Callable[[float], None] = time.sleep, max_iterations: int | None = None) -> dict[str, Any]:
    lock = _hold_lock(lock_path)
    if lock is None:
        return {"state": "ALREADY_RUNNING"}
    # Import the browser launcher's module now, so a later code update cannot mix versions.
    from live_contentops import daily_app_launcher_v1  # noqa: F401
    runner = runner or FeedRunner()
    iterations = 0
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
            remaining = interval_seconds - (time.monotonic() - started)
            while remaining > 0 and not stop_path.exists():
                sleep(min(5.0, remaining))
                remaining = interval_seconds - (time.monotonic() - started)
    finally:
        lock.close()
    return {"state": "STOPPED", "iterations": iterations}
