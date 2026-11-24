"""CC-314 (Jim's decision 82, 5 Nov): a post about one market carries TradingView's own chart
snapshot of that market.

The image is TradingView's Download image (Ctrl+Alt+S), taken at posting time on a guest chart
in a throwaway Chromium profile Capital Chronicle owns (a fresh browser context per snapshot: no
account, no saved layout, no cookies, never Jim's TradingView or the X list feed's Chrome on CDP
9222). TradingView's Terms of Use, section 4, allow snapshots in publications while TradingView's
attribution stays clearly visible: the snapshot's own "Created with TradingView.com" header and
logo are never cropped (framing only pads), and each post says "Chart: TradingView". Section 3 bars
machine processing of TradingView content: one snapshot per post, displayed only, no data read.

CC-459: plan posts share one capture per market for 15 minutes. Two capture attempts fit within
a five-minute wait; the run budget defers capture, never substitutes a drawn levels picture.
New plan cards keep a plain checked download or a source-bound fact card when capture fails.

TradingView's guest chart refuses native drawings ("Cannot create shape"). CC-459 instead
places Capital Chronicle's supplied public plan levels on a copy of the download, against
the chart's visible axis and checked pane geometry. The original download stays unchanged.
Axis labels serve this displayed annotation only; they never become an analytical price feed.
"""
from __future__ import annotations

import hashlib
import base64
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping

POLICY = "contentops.tradingview_snapshot.v1"
CREDIT = "Chart: TradingView"
# Jim's decision 107 (10 Nov): charts European and US readers trust, futures, ETFs or spot, never a CFD feed.
# Each keeps the plan's price scale: spot gold and FX from ICE, the S&P 500 cash index, WTI's front-month
# futures (the DEMO book's oil follows it), spot Bitcoin. All six captured by this worker on 9 Nov, 17:50Z.
# The paused site's reviewed map (Main ui/src/product/public-desk/reviewed-tradingview-symbols.json) still
# lists the old CFD feeds; it follows when the site returns (decision 84).
# CC-788 (24 Nov 2026): the Nasdaq 100 follows the S&P 500's choice, the cash index (NASDAQ:NDX), never the
# reviewed map's CFD feed (OANDA:NAS100USD); like SP:SPX it has bars in New York cash hours only.
SYMBOLS = {"XAUUSD": "FX_IDC:XAUUSD", "US500": "SP:SPX", "EURUSD": "FX_IDC:EURUSD",
           "USDJPY": "FX_IDC:USDJPY", "USOIL": "NYMEX:CL1!", "BTCUSD": "COINBASE:BTCUSD",
           "USTEC": "NASDAQ:NDX"}
NAMES = {"XAUUSD": "Gold spot / US dollar (ICE)", "US500": "S&P 500 index",
         "EURUSD": "Euro / US dollar spot (ICE)", "USDJPY": "US dollar / Japanese yen spot (ICE)",
         "USOIL": "WTI light crude oil futures, front month (NYMEX)", "BTCUSD": "Bitcoin / US dollar (Coinbase spot)",
         "USTEC": "Nasdaq 100 index"}
REVIEWED_MAP = Path(r"A:\Capital Chronicle\Worktrees\codex-web-cc254-clean\ui\src\product\public-desk"
                    r"\reviewed-tradingview-symbols.json")
INTERVAL_LABELS = {"15": "15m", "60": "1h", "240": "4h", "D": "1D"}
INTERVAL_SECONDS = {"15": 900, "60": 3600, "240": 14400, "D": 86400}
# CC-778 (Builder K, 24 Nov 2026): a dated follow-up shows its move on a chart whose visible window runs from
# before the original call to the bar that resolved it. The worker sets that range through the chart page's own
# API, reads the range back, and the parent refuses any download whose window does not match or shows a later bar.
HISTORICAL_RANGE_UNCONFIRMED = "TRADINGVIEW_VISIBLE_RANGE_NOT_CONFIRMED"
# Ops Product, 5 Nov: 16:9 for X, Threads, Telegram, Discord, LinkedIn and Facebook; 4:5 for Instagram.
RATIOS = {"16:9": (16, 9), "4:5": (4, 5)}
# A 1910x850 page gives a snapshot of about 1524x856, already close to 16:9.
VIEWPORT = {"width": 1910, "height": 850}
PORTRAIT_VIEWPORT = {"width": 1472, "height": 1350}
TIMEOUT_SECONDS = 60
PLAN_RETRY_TIMEOUT_SECONDS = 90
# Builder E, 23 Nov 2026: a plan's chart (a post or its analysis page) gets 90 seconds on every attempt. On 23 Nov
# 04:01Z the BTC portrait download landed 61 s into a 60 s first attempt and was thrown away; two attempts of 90 s
# still fit in the five-minute capture window.
PLAN_ATTEMPT_TIMEOUT_SECONDS = 90
# A capture whose run stopped mid-attempt (22 Nov 19:39Z: the minute job's five-minute limit) left no cause. The
# next run records it and grants one more attempt, once, even after the five-minute window.
CAPTURE_INTERRUPTED = "TRADINGVIEW_CAPTURE_INTERRUPTED"
PRICE_SCALE_MISMATCH = "TRADINGVIEW_PRICE_SCALE_MISMATCH"
PLAYWRIGHT_PYTHON = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v1-runtime\venv\Scripts\python.exe")
OUTCOMES = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\tradingview_snapshot_outcomes_v1.jsonl")
RIGHTS_BASIS = ("TradingView Terms of Use section 4 (checked 5 Nov 2026): chart snapshots may be used in "
                "publications with TradingView's attribution clearly visible; the attribution is kept "
                "uncropped and the post says 'Chart: TradingView' (Jim's decision 82). Free pages only (reason 2a).")


class SnapshotError(RuntimeError):
    pass


class SnapshotPending(ValueError):
    """The existing minute consumer resumes the same capture, without a new job."""


class SnapshotUnavailable(SnapshotPending):
    """The required capture exhausted its attempts with a named cause."""


class TemplateSnapshotNotFit(SnapshotError):
    def __init__(self, cause, snapshot=None):
        super().__init__(cause)
        self.snapshot = snapshot


class TemplateImageRefused(ValueError):
    """The exact template failed a publication check after a valid chart capture."""


PLAN_CACHE_SECONDS = 15 * 60
PLAN_WAIT_SECONDS = 5 * 60
PLAN_ATTEMPTS = 2


def plan_snapshot(row: Mapping[str, Any], folder: Path, *, snapshot=None, snapshot_allowed=None,
                  now: datetime | None = None, ratio: str = "16:9", image_input=None,
                  source_snapshot=None, required_chart=False, plan_post=False,
                  sample_after_publication=False) -> dict | None:
    """Use the shared cache or make a bounded capture for this plan and ratio.

    Only image artifacts are cached; this is not another scheduler or publication store.
    The market, source download hash, capture clock and first failure stay bound.
    """
    now = now or datetime.now(timezone.utc)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    media = folder / "media_assets"
    market = row["symbol"]
    tv_symbol = SYMBOLS.get(market, market)
    title = row.get("instrument_title") or NAMES.get(market, market)
    interval = interval_for((row.get("levels") or {}).get("valid_until_utc"), row["at_utc"])
    if market.startswith(("ECONOMICS:", "FRED:")):
        interval = "D"
    suffix = "" if ratio == "16:9" else "_" + ratio.replace(":", "x")
    if image_input:
        suffix += "_cc465"
    def image_asset(taken):
        if image_input:
            from .image_quality_v1 import TEMPLATE_FIT_CAUSES, prepare_asset
            try:
                card = prepare_asset(image_input, "W" if ratio == "16:9" else "T", media, taken,
                                     sample_after_publication=sample_after_publication)
            except ValueError as exc:
                if str(exc) in TEMPLATE_FIT_CAUSES:
                    raise TemplateSnapshotNotFit(str(exc), taken) from exc
                raise TemplateImageRefused(str(exc)) from exc
            return {**card, "media_role": "delivery_only", "article_inclusion": False,
                    "canonical_article_media": False, "provenance_status": "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE"}
        return snapshot_asset(market,title,taken,media,ratio)
    state_path = folder / ("tradingview_capture" + suffix + "_v1.json")
    initial = {
        "key": row["key"], "market": market, "started_at_utc": now.isoformat(), "attempts": 0,
        "attempt_causes": []}
    required = required_chart or bool(row.get("state_alert_contract"))
    if required:
        initial["required_chart"] = True
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else initial.copy()
    if state.get("key") != row["key"] or state.get("market") != market:
        raise ValueError("TRADINGVIEW_PLAN_CAPTURE_BINDING_CHANGED")

    def save():
        state_path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")

    def attempt_ended(cause):
        if isinstance(state.get("attempt_causes"), list) and len(state["attempt_causes"]) < state["attempts"]:
            state["attempt_causes"].append(str(cause)[:200])

    def plain_asset():
        return snapshot_asset(market, title, state["plain_snapshot"], media, ratio)

    cache_file = folder.parent / "tradingview_cache" / (market.replace(":", "-") + suffix + ".json")
    taken = None
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        captured = _utc(cached.get("captured_at_utc"))
        if (captured and 0 <= (now - captured).total_seconds() < PLAN_CACHE_SECONDS
                and cached.get("tv_symbol") == tv_symbol
                and (not (image_input or plan_post) or cached.get("interval") == interval)
                and Path(cached["path"]).is_file() and _sha256(Path(cached["path"])) == cached["sha256"]):
            taken = cached
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if not taken and source_snapshot:
        source_time = _utc(source_snapshot.get("captured_at_utc"))
        if (source_snapshot.get("tv_symbol") != tv_symbol or source_snapshot.get("interval") != interval
                or source_snapshot.get("capture_ratio", "16:9") != ratio or source_time is None or source_time > now
                or _sha256(Path(source_snapshot["path"])) != source_snapshot.get("sha256")):
            raise SnapshotError("TRADINGVIEW_SOURCE_PAGE_SNAPSHOT_BINDING_CHANGED")
        # The confirmed article's own image feeds its social card. Keep its
        # actual capture clock and prior failures; this is no new observation.
        taken = dict(source_snapshot)
    # Preserve this exact post's successful image even when it resumes after the cache expires.
    if not taken and state.get("snapshot"):
        prior = state["snapshot"]
        if prior.get("tv_symbol") == tv_symbol and _sha256(Path(prior["path"])) == prior["sha256"]:
            taken = prior
    if taken and not (plan_post and state.get("status") in {"PLAIN_SNAPSHOT", "PLAN_CARD"}):
        asset = image_asset(taken)
        validate_snapshot_asset(asset)
        if state.get("status") != "CAPTURED":
            state.update(status="CAPTURED", snapshot=taken, cache_hit=True)
            save()
            record_outcome({k: v for k, v in state.items() if k != "snapshot"})
        return asset
    if state.get("status") == "TEXT_ONLY":
        if required and not state.get("required_chart"):
            # Give a retained post its first bounded capture under the required-chart policy.
            state = {**initial, "prior_failure": {
                field: state.get(field) for field in ("started_at_utc", "attempts", "first_cause", "cause")}}
            save()
        else:
            cause = state.get("cause") or "IMAGE_TRADINGVIEW_CAPTURE_REQUIRED"
            if required:
                raise SnapshotUnavailable(cause)
            if image_input:
                raise SnapshotPending(cause)
            return None
    if plan_post and state.get("status") == "PLAIN_SNAPSHOT":
        return plain_asset()
    if plan_post and state.get("status") == "PLAN_CARD":
        raise SnapshotUnavailable(state["cause"])
    if state["attempts"] == 0 and state.get("status") == "DEFERRED":
        # A deferral starts no clock (Builder F, 23 Nov): the five-minute window counts from the first real
        # attempt, so several short runs in a row cannot use it up before any capture is tried.
        state.setdefault("first_deferred_at_utc", state["started_at_utc"])
        state["started_at_utc"] = datetime.now(timezone.utc).isoformat()
    deadline = _utc(state["started_at_utc"]) + timedelta(seconds=PLAN_WAIT_SECONDS)
    allowed = PLAN_ATTEMPTS
    if isinstance(state.get("attempt_causes"), list):
        lost = state["attempts"] - len(state["attempt_causes"])
        if lost > 0:
            # The process stopped during an attempt (no cause was saved). Name it, then give it one more try.
            state["attempt_causes"] += [CAPTURE_INTERRUPTED] * lost
            state.setdefault("first_cause", CAPTURE_INTERRUPTED)
            state["cause"] = CAPTURE_INTERRUPTED
            save()
        if CAPTURE_INTERRUPTED in state["attempt_causes"]:
            allowed += 1
            if state["attempts"] < allowed and "interrupted_retry_until_utc" not in state:
                state["interrupted_retry_until_utc"] = (datetime.now(timezone.utc) + timedelta(
                    seconds=PLAN_ATTEMPT_TIMEOUT_SECONDS + 30)).isoformat()
                save()
            if state.get("interrupted_retry_until_utc"):
                deadline = max(deadline, _utc(state["interrupted_retry_until_utc"]))
    plan_row = plan_post or bool(row.get("levels"))
    while state["attempts"] < allowed and datetime.now(timezone.utc) < deadline:
        if snapshot_allowed is not None and not snapshot_allowed():
            state.update(status="DEFERRED", cause="TRADINGVIEW_CAPTURE_DEFERRED_RUN_TIME_BUDGET")
            save()
            record_outcome(state)
            raise SnapshotPending(state["cause"])
        state["attempts"] += 1
        save()
        try:
            if snapshot:
                taken = (snapshot(market, interval, media) if ratio == "16:9" else
                         snapshot(market, interval, media / "4x5", ratio=ratio))
            else:
                remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
                retry = plan_post and state["attempts"] > 1
                # Only a portrait goes under 4x5 (the 16:9 template capture used to share its attempt folders).
                capture_dir = media / "4x5" if ratio == "4:5" else media
                if plan_post:
                    capture_dir = capture_dir / f"attempt-{state['attempts']}"
                taken = capture(market, interval, capture_dir,
                    timeout=min(PLAN_ATTEMPT_TIMEOUT_SECONDS if plan_row else TIMEOUT_SECONDS, max(1, remaining)),
                    ratio=ratio, **({"allow_plain_scale_mismatch": True, "reset_price_scale": retry} if plan_post else {}),
                    **({"chart_size":(1600,700) if ratio=="16:9" else (1080,850)} if image_input else {}))
            if plan_post and taken.get("plain_price_scale_cause") == PRICE_SCALE_MISMATCH:
                state["plain_snapshot"] = taken
                raise SnapshotError(PRICE_SCALE_MISMATCH)
            asset = image_asset(taken)
            validate_snapshot_asset(asset)
            state.update(status="CAPTURED", snapshot=taken, cache_hit=False)
            save()
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(taken, sort_keys=True), encoding="utf-8")
            record_outcome({k: v for k, v in state.items() if k not in {"snapshot", "plain_snapshot"}})
            return asset
        except TemplateSnapshotNotFit as exc:
            attempt_ended(exc)
            save()
            raise
        except TemplateImageRefused as exc:
            attempt_ended(exc)
            state.update(status="IMAGE_HELD", snapshot=taken, cause=str(exc))
            save()
            record_outcome({k: v for k, v in state.items() if k != "snapshot"})
            raise
        except Exception as exc:
            if image_input and str(exc) == "IMAGE_CHART_CAPTURE_SHAPE":
                attempt_ended(exc)
                save()
                raise TemplateSnapshotNotFit(str(exc)) from exc
            state.setdefault("first_cause", str(exc)[:200])
            state["cause"] = str(exc)[:200]
            # The final cause stays the first one (CC-734 binds it); each attempt's own cause is kept.
            attempt_ended(exc)
            save()
    state.update(status="TEXT_ONLY", cause=state.get("first_cause") or "TRADINGVIEW_CAPTURE_WAIT_EXPIRED")
    if plan_post:
        plain = state.get("plain_snapshot")
        state["status"] = "PLAIN_SNAPSHOT" if plain else "PLAN_CARD"
        save()
        record_outcome({k: v for k, v in state.items() if k != "plain_snapshot"})
        if plain:
            return plain_asset()
        raise SnapshotUnavailable(state["cause"])
    if image_input:
        state["status"] = "IMAGE_HELD"
    save()
    record_outcome(state)
    if required:
        raise SnapshotUnavailable(state["cause"])
    if image_input:
        raise SnapshotPending(state["cause"])
    return None


# Jim decision 87 (CC-316): memory measurements never gate capture.


def late_plan_snapshot(row, folder, late, *, snapshot=None, snapshot_allowed=None):
    """Use a new checked chart for the confirmed copy, with one later capture if needed."""
    market = row["symbol"]
    interval = interval_for((row.get("levels") or {}).get("valid_until_utc"), row["at_utc"])
    failures = [json.loads(path.read_bytes()) for path in folder.glob("tradingview_capture*_v1.json")]
    failed_at = min((_utc(s["started_at_utc"]) for s in failures
                     if s.get("status") in {"PLAN_CARD", "PLAIN_SNAPSHOT"}), default=None)
    if failed_at is None:
        return None
    state_path = late / "tradingview_capture_v1.json"
    prior = json.loads(state_path.read_bytes()) if state_path.is_file() else {}
    cache = folder.parent / "tradingview_cache"
    cached = [json.loads(path.read_bytes()) for path in (cache / (market + ".json"),
                                                        cache / (market + "_cc465.json")) if path.is_file()]

    def asset(taken):
        from .publication_image_contract_v1 import validate_scale

        if (not taken or taken.get("tv_symbol") != SYMBOLS[market] or taken.get("interval") != interval
                or (captured := _utc(taken.get("captured_at_utc"))) is None or captured <= failed_at
                or taken.get("plain_price_scale_cause")):
            return None
        validate_scale(market, taken)
        image = snapshot_asset(market, row["instrument_title"], taken, late / "media_assets")
        validate_snapshot_asset(image, {"market_asset": market})
        return image

    for taken in (prior.get("snapshot"), *cached):
        try:
            if image := asset(taken):
                return image
        except (OSError, ValueError, KeyError):
            continue
    if prior or (snapshot_allowed is not None and not snapshot_allowed()):
        return None
    late.mkdir(parents=True, exist_ok=True)
    try:
        with state_path.open("x", encoding="utf-8") as handle:
            json.dump({"status": "STARTED"}, handle)
    except FileExistsError:
        return None
    try:
        media = late / "media_assets"
        taken = (snapshot(market, interval, media) if snapshot else
                 capture(market, interval, media, timeout=PLAN_RETRY_TIMEOUT_SECONDS, reset_price_scale=True))
        image = asset(taken)
        state = {"status": "CAPTURED", "snapshot": taken} if image else {"status": "FAILED", "cause": "LATE_CHART_CAPTURE_UNBOUND"}
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        image = None
        state = {"status": "FAILED", "cause": str(exc)[:200]}
    state_path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    return image


def _utc(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    at = datetime.fromisoformat(text)
    return at if at.tzinfo else at.replace(tzinfo=timezone.utc)


def interval_for(valid_until_utc: Any, at_utc: Any) -> str:
    """The plan's validity sets the timeframe: up to 1 day, 1 hour; up to 1 week, 4 hours; longer, daily."""
    end, start = _utc(valid_until_utc), _utc(at_utc) or datetime.now(timezone.utc)
    if end is None:
        return "240"
    hours = (end - start).total_seconds() / 3600
    return "60" if hours <= 24 else "240" if hours <= 24 * 7 else "D"


def chart_url(tv_symbol: str, interval: str) -> str:
    return f"https://www.tradingview.com/chart/?symbol={tv_symbol}&interval={interval}"


def reviewed_symbols(path: Path = REVIEWED_MAP) -> dict:
    """asset -> symbol from the site's reviewed map (used by the check, not at posting time)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get("instruments") or {}
    out = {}
    for row in rows.values() if isinstance(rows, Mapping) else rows:
        if isinstance(row, Mapping) and (row.get("review") or {}).get("status") == "REVIEWED":
            out[row.get("asset_id") or row.get("asset")] = row.get("symbol")
    return out


def frame(source: Path, target: Path, ratio: str = "16:9") -> dict:
    """Pad the snapshot to the ratio on white. Never crops or scales: every original pixel,
    TradingView's attribution included, is kept at its own size."""
    from PIL import Image
    rw, rh = RATIOS[ratio]
    with Image.open(source) as image:
        image = image.convert("RGB")
        width, height = image.size
        if ratio == "4:5":
            if abs(width / height - .8) > .003:
                raise SnapshotError("INSTAGRAM_NATIVE_4X5_CHART_REQUIRED")
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target, format="PNG", optimize=True)
            return {"ratio": ratio, "mode": "NATIVE_VIEWPORT", "width": width, "height": height,
                    "original_box": [0, 0, width, height]}
        if width * rh >= height * rw:
            out_w, out_h = width, -(-width * rh // rw)
        else:
            out_w, out_h = -(-height * rw // rh), height
        canvas = Image.new("RGB", (out_w, out_h), (255, 255, 255))
        left, top = (out_w - width) // 2, (out_h - height) // 2
        canvas.paste(image, (left, top))
        target.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(target, format="PNG", optimize=True)
    return {"ratio": ratio, "width": out_w, "height": out_h, "original_box": [left, top, left + width, top + height]}


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record_outcome(entry: Mapping[str, Any], path: Path | None = None) -> None:
    path = Path(path or OUTCOMES)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"recorded_at_utc": datetime.now(timezone.utc).isoformat(), **entry},
                                    sort_keys=True) + "\n")
    except OSError:
        pass  # counting never stops a post


def failure_count(path: Path | None = None) -> int:
    path = Path(path or OUTCOMES)
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines()
               if line.strip() and json.loads(line).get("status") in {
                   "FAILED", "TEXT_ONLY", "SKIPPED_RUN_TIME_BUDGET"})


def _kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def _run_worker(args: dict, *, timeout: float, python: str | None) -> dict:
    python = python or (str(PLAYWRIGHT_PYTHON) if PLAYWRIGHT_PYTHON.is_file() else sys.executable)
    if Path(python).name.lower() == "pythonw.exe":
        python = str(Path(python).with_name("python.exe"))
    with TemporaryDirectory(prefix=".snapshot-", dir=args["out_dir"]) as attempt_dir:
        result_path = Path(attempt_dir) / "result.json"
        request = {**args, "worker_result_path": str(result_path)}
        process = subprocess.Popen([python, "-B", str(Path(__file__).resolve()), "--worker", json.dumps(request)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            out, err = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(process.pid)
            out, err = process.communicate()
            if not result_path.is_file():
                raise SnapshotError("TRADINGVIEW_SNAPSHOT_TIMEOUT") from None
        if result_path.is_file():
            return json.loads(result_path.read_bytes())
    return _worker_output(process.returncode, out, err)


def _worker_output(returncode: int, out: bytes, err: bytes) -> dict:
    """The worker's result, or its named cause.

    Before 23 Nov the cause was stderr's last line. For a Playwright error that is the call log
    ("- waiting 500ms", the late BTC chart of 23 Nov 04:06Z), never the error itself.
    """
    lines = [line for line in out.decode("utf-8", "replace").splitlines() if line.startswith("{")]
    last = json.loads(lines[-1]) if lines else None
    if isinstance(last, dict) and last.get("error"):
        raise SnapshotError(str(last["error"])[:200])
    if returncode != 0 or not lines:
        text = [line.strip() for line in err.decode("utf-8", "replace").strip().splitlines() if line.strip()]
        named = [line for line in text if re.match(r"^[\w.]+(?:Error|Exception)\b", line)]
        tail = named[-1:] or text[-1:] or ["no output"]
        raise SnapshotError("TRADINGVIEW_SNAPSHOT_WORKER_FAILED:" + tail[0][:200])
    return last


class _StepBudget:
    """One deadline for the whole worker (Builder E, 23 Nov 2026).

    The step waits used to be fractions of the budget that together came to about 1.6 times it
    (goto 1/2, canvas 1/3, title 1/4, paint 2.5 s, download 20 s), so a slow page ran into the
    parent's kill and left only TRADINGVIEW_SNAPSHOT_TIMEOUT. Each wait now gets at most what is
    left, and a spent budget or a failed step names its step.
    """

    def __init__(self, budget_ms: int, clock=None):
        import time
        self.clock = clock or time.monotonic
        self.deadline = self.clock() + budget_ms / 1000
        self.step = "launch"

    def at(self, step: str) -> "_StepBudget":
        self.step = step
        return self

    def left(self, cap_ms: float) -> int:
        remaining = int((self.deadline - self.clock()) * 1000)
        if remaining <= 0:
            raise SnapshotError("TRADINGVIEW_WORKER_BUDGET_SPENT:" + self.step)
        return max(1, min(int(cap_ms), remaining))

    def cause(self, exc: BaseException) -> str:
        if isinstance(exc, SnapshotError):
            return str(exc)
        kind = "TIMEOUT" if "Timeout" in type(exc).__name__ else "FAILED"
        return f"TRADINGVIEW_WORKER_STEP_{kind}:{self.step}"


def capture(market: str, interval: str, out_dir: Path, *, timeout: float = TIMEOUT_SECONDS,
            worker=None, python: str | None = None, ratio: str = "16:9", quote_provider=None,
            chart_size: tuple[int, int] | None = None, reset_price_scale=False,
            allow_plain_scale_mismatch=False, visible_range: Mapping[str, Any] | None = None) -> dict:
    """One TradingView Download image of the market at the interval, checked before use.

    visible_range (CC-778) asks for a historical window: {"from_utc", "show_from_utc", "last_bar_open_utc"}.
    The download must show every bar from show_from_utc through the bar opening at last_bar_open_utc and no
    later bar; its scale is then checked against quote_provider(market, visible_to_utc), the held close there.
    """
    economic = bool(re.fullmatch(r"(?:ECONOMICS|FRED):[A-Z0-9_]+", str(market)))
    if (market not in SYMBOLS and not economic) or interval not in INTERVAL_LABELS or ratio not in RATIOS:
        raise SnapshotError("TRADINGVIEW_SNAPSHOT_MARKET_OR_INTERVAL_UNSUPPORTED")
    tv_symbol = market if economic else SYMBOLS[market]
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if visible_range and (economic or quote_provider is None):
        raise SnapshotError("TRADINGVIEW_HISTORICAL_WINDOW_NEEDS_HELD_CLOSE_PROVIDER")
    if not economic and worker is None and quote_provider is None:
        from .chart_price_reference_v1 import prepare_chart_quote
        prepare_chart_quote(market)
    args = {"url": chart_url(tv_symbol, interval), "out_dir": str(out_dir),
            "budget_ms": int(timeout * 1000) - 8000, "ratio": ratio}
    if visible_range:
        step = INTERVAL_SECONDS[interval]
        last_open = int(_utc(visible_range["last_bar_open_utc"]).timestamp())
        # The right edge sits just under half a bar past the last bar's open: that bar shows whole, the next none.
        args["visible_range"] = {"from": int(_utc(visible_range["from_utc"]).timestamp()),
                                 "to": last_open + int(step * .45), "last_bar_open": last_open, "step": step}
    if reset_price_scale:
        args["reset_price_scale"] = True
    if chart_size is not None:
        if tuple(chart_size) not in {(1600, 700), (1080, 850)}:
            raise SnapshotError("IMAGE_CHART_CAPTURE_SIZE_UNSUPPORTED")
        args["chart_size"] = list(chart_size)
    result = (worker or (lambda a: _run_worker(a, timeout=timeout, python=python)))(args)
    path = Path(str(result.get("path") or ""))
    ticker = tv_symbol.split(":", 1)[1]
    if not path.is_file() or path.parent != out_dir:
        raise SnapshotError("TRADINGVIEW_SNAPSHOT_FILE_MISSING")
    # TradingView names its download <TICKER>_<date>_<time>.png.
    if not re.fullmatch(re.escape(ticker) + r"_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.png",
                        str(result.get("suggested_filename") or "")):
        raise SnapshotError("TRADINGVIEW_SNAPSHOT_NOT_THIS_SYMBOL")
    legend = str(result.get("legend") or "")
    # TradingView's toolbar writes daily as "D" (or "1D"); hours as "1h" and "4h".
    accepted = {INTERVAL_LABELS[interval]} | ({"D"} if interval == "D" else set())
    if not accepted & set(re.split(r"[\s·•]+", legend)):
        raise SnapshotError("TRADINGVIEW_SNAPSHOT_INTERVAL_NOT_CONFIRMED")
    from PIL import Image
    with Image.open(path) as image:
        if image.format != "PNG" or min(image.size) < 400:
            raise SnapshotError("TRADINGVIEW_SNAPSHOT_IMAGE_INVALID")
        size = image.size
    scale = {}
    if result.get("geometry_probe"):
        from live_contentops.tradingview_plan_overlay_v1 import geometry
        try:
            scale = {"chart_geometry": geometry(result)}
        except (ValueError, KeyError, OSError, StopIteration, ZeroDivisionError) as exc:
            scale = {"chart_geometry_cause": str(exc) or "TRADINGVIEW_PRICE_SCALE_NOT_USABLE"}
    if chart_size and (min(size[0]/chart_size[0], size[1]/chart_size[1]) < .97
            or abs(size[0]/size[1]/(chart_size[0]/chart_size[1])-1) > .03):
        raise SnapshotError("IMAGE_CHART_CAPTURE_SHAPE")
    if not chart_size and ratio == "4:5" and abs(size[0] / size[1] - .8) > .003:
        raise SnapshotError("INSTAGRAM_NATIVE_4X5_CHART_REQUIRED")
    taken = {"path": str(path), "sha256": _sha256(path), "width": size[0], "height": size[1], **scale,
            "capture_ratio": ratio, "capture_viewport": result.get("capture_viewport"),
            "tv_symbol": tv_symbol, "interval": interval, "interval_label": INTERVAL_LABELS[interval],
            "legend": legend, "page_title": result.get("page_title"), "chart_url": args["url"],
            "suggested_filename": result.get("suggested_filename"),
            "captured_at_utc": result.get("captured_at_utc"), "seconds": result.get("seconds")}
    if chart_size:
        taken["template_chart_size"] = list(chart_size)
    if visible_range:
        taken.update(historical_window(result, visible_range, interval))
        from .publication_image_contract_v1 import bind_scale, not_compared
        quote = quote_provider(market, taken["visible_to_utc"])
        if quote is None or taken.get("visible_last_price") is None:
            # Nothing to compare: the right symbol is still bound, and no level is offset (WTI draws no level).
            cause = ("TRADINGVIEW_HISTORICAL_HELD_CLOSE_UNAVAILABLE" if quote is None
                     else "TRADINGVIEW_HISTORICAL_LAST_CLOSE_UNREAD")
            taken["price_scale_check"] = not_compared(market, taken, cause)
            return taken
        taken = bind_scale(market, taken, quote=quote)
        record_outcome({"status": "PRICE_SCALE_CHECKED", "market": market,
            "captured_at_utc": taken["captured_at_utc"], "visible_to_utc": taken["visible_to_utc"],
            "price_scale_check": taken["price_scale_check"], "chart_sha256": taken["sha256"]})
        return taken
    if not economic and (worker is None or quote_provider is not None):
        from .publication_image_contract_v1 import ImageContractError, bind_scale
        try:
            taken = bind_scale(market, taken,
                quote=quote_provider(market, taken["captured_at_utc"]) if quote_provider else None)
        except ImageContractError as error:
            record_outcome({"status": "PRICE_SCALE_REFUSED", "market": market,
                "cause": str(error), "captured_at_utc": taken["captured_at_utc"],
                "price_scale_check": error.details, "chart_sha256": taken["sha256"]})
            if allow_plain_scale_mismatch and str(error) == PRICE_SCALE_MISMATCH:
                # The download already passed ticker, interval, format and size checks.
                # The unsafe scale is retained as evidence and never used to draw levels.
                return {**taken, "plain_price_scale_cause": str(error)}
            raise
        record_outcome({"status": "PRICE_SCALE_CHECKED", "market": market,
            "captured_at_utc": taken["captured_at_utc"],
            "price_scale_check": taken["price_scale_check"], "chart_sha256": taken["sha256"]})
    return taken


def _displayed_number(text: Any) -> float | None:
    """A value as the chart displays it (thousands commas, a typographic minus), or None."""
    cleaned = str(text or "").strip().replace(",", "").replace("−", "-")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return value if value == value and abs(value) != float("inf") else None


def historical_window(result: Mapping[str, Any], visible_range: Mapping[str, Any], interval: str) -> dict:
    """CC-778: the window the worker read back, checked against the request; refused when it differs.

    The download shows every bar from show_from_utc (the original call's bar) through the bar that opens at
    last_bar_open_utc, and no later bar. visible_to_utc is that last bar's close.
    """
    observed = result.get("visible_range_observed") or {}
    if observed.get("error"):
        raise SnapshotError(str(observed["error"])[:200])
    step = INTERVAL_SECONDS[interval]
    last_open = int(_utc(visible_range["last_bar_open_utc"]).timestamp())
    show_from = int(_utc(visible_range["show_from_utc"]).timestamp())
    try:
        seen_from, seen_to = float(observed["from"]), float(observed["to"])
    except (KeyError, TypeError, ValueError):
        raise SnapshotError(HISTORICAL_RANGE_UNCONFIRMED) from None
    if not (seen_from <= show_from and last_open <= seen_to < last_open + step / 2):
        raise SnapshotError(HISTORICAL_RANGE_UNCONFIRMED)
    def iso(epoch):
        return datetime.fromtimestamp(epoch, timezone.utc).isoformat()
    window = {"visible_from_utc": iso(int(seen_from)), "visible_to_utc": iso(last_open + step),
              "last_bar_open_utc": iso(last_open), "visible_range_observed": {"from": seen_from, "to": seen_to},
              "visible_last_price": _displayed_number(result.get("visible_last_close")),
              "live_values_hidden": result.get("live_values_hidden") is True,
              "method": "guest TradingView Download image; visible range set and read back through the chart "
                        "page's own API; legend read on the window's last bar; original pixels unchanged"}
    if result.get("visible_last_close_cause"):
        window["visible_last_close_cause"] = str(result["visible_last_close_cause"])[:200]
    return window


def snapshot_asset(market: str, title: str, snapshot: Mapping[str, Any], out_dir: Path,
                   ratio: str = "16:9") -> dict:
    """The framed snapshot as a delivery-only post image (the coordinator's media record)."""
    source = Path(snapshot["path"])
    framed_path = Path(out_dir).resolve() / f"tradingview-{snapshot['sha256'][:16]}-{ratio.replace(':', 'x')}.png"
    framing = frame(source, framed_path, ratio)
    digest = _sha256(framed_path)
    label = snapshot["interval_label"]
    captured = _utc(snapshot.get("captured_at_utc")) or datetime.now(timezone.utc)
    from live_contentops.public_time_v1 import public_timestamp
    when = public_timestamp(captured)
    name = NAMES.get(market, market.split(":")[-1])
    return {"asset_id": "tradingview-snapshot-" + digest[:20], "path": str(framed_path), "sha256": digest,
            "width": framing["width"], "height": framing["height"], "mime_type": "image/png",
            "modality": "tradingview_chart_snapshot", "card_kind": "TRADINGVIEW_SNAPSHOT",
            "media_role": "delivery_only", "role": "market_chart", "delivery_only": True,
            "article_inclusion": False, "canonical_article_media": False,
            "provenance_status": "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE", "rights_basis": RIGHTS_BASIS,
            "attribution": "TradingView", "credit": CREDIT,
            "caption": f"{title}: {label} chart of {name}. {CREDIT}.",
            "alt_text": f"TradingView {label} chart of {name}, "
                        f"captured {when}.",
            "source_page_url": snapshot["chart_url"],
            "tradingview_snapshot": {**dict(snapshot), "framing": framing, "policy": POLICY,
                                     "levels_drawn": [], "target_drawn": False},
            "publication_authority": False}


def validate_snapshot_asset(asset: Mapping[str, Any], article: Mapping[str, Any] | None = None) -> None:
    """Validate the exact download and uncropped pixels; never treat it as a data series."""
    from PIL import Image, ImageChops
    if asset.get("image_template"):
        from .image_quality_v1 import validate_asset
        validate_asset(asset, require_vision=False)
        return
    snap = asset["tradingview_snapshot"]
    market = (article or {}).get("market_asset")
    from live_contentops.tradingview_plan_overlay_v1 import target_drawn
    if target_drawn(asset):
        # CC-583 / decision 82: snap["target_drawn"] describes the plain download only.
        raise ValueError("TRADINGVIEW_OVERLAY_TARGET_DRAWN")
    if ((article or {}).get("paid") or (article or {}).get("paywall")
            or (article or {}).get("audience") in {"paid", "paid_subscribers"}):
        raise ValueError("PUBLIC_REDISTRIBUTION_NOT_LICENSED")
    economic = bool(re.fullmatch(r"(?:ECONOMICS|FRED):[A-Z0-9_]+", str(snap.get("tv_symbol") or "")))
    # CC-536's bound method illustration uses its retained Bitstamp download.
    # A plan still requires the reviewed instrument's exact price scale below.
    measured_method = (not market and (article or {}).get("measured_odds_series") == "CC536_MEASURED_ODDS_SERIES_V1"
                       and snap.get("tv_symbol") == "BITSTAMP:BTCUSD")
    if (snap.get("policy") != POLICY or asset.get("credit") != CREDIT
            or asset.get("provenance_status") != "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE"
            or not asset.get("rights_basis") or snap.get("levels_drawn") != []
            or snap.get("target_drawn") is not False
            or (snap.get("tv_symbol") not in SYMBOLS.values() and not economic and not measured_method)
            or (market and not economic and SYMBOLS.get(market) != snap.get("tv_symbol"))
            or snap.get("chart_url") != chart_url(snap["tv_symbol"], snap["interval"])
            or snap.get("interval") not in INTERVAL_LABELS):
        raise ValueError("TRADINGVIEW_SNAPSHOT_BINDING_INVALID")
    if _sha256(Path(asset["path"])) != asset["sha256"] or _sha256(Path(snap["path"])) != snap["sha256"]:
        raise ValueError("TRADINGVIEW_SNAPSHOT_BYTES_CHANGED")
    with Image.open(snap["path"]) as original, Image.open(asset["path"]) as framed:
        box = snap["framing"]["original_box"]
        if (original.format != "PNG" or min(original.size) < 400
                or (box[2] - box[0], box[3] - box[1]) != original.size
                or framed.size != (asset["width"], asset["height"])
                or (not asset.get("plan_overlay") and
                    ImageChops.difference(original.convert("RGB"), framed.convert("RGB").crop(box)).getbbox())):
            raise ValueError("TRADINGVIEW_SNAPSHOT_ATTRIBUTION_CROPPED_OR_CHANGED")
        if asset.get("plan_overlay"):
            from live_contentops.tradingview_plan_overlay_v1 import validate
            validate(asset)
        top = asset.get("preceding_card")
        if top:
            if _sha256(Path(top["path"])) != top["sha256"]:
                raise ValueError("TRADINGVIEW_PRECEDING_CARD_BYTES_CHANGED")
            with Image.open(top["path"]) as card:
                if ImageChops.difference(card.convert("RGB"), framed.convert("RGB").crop(top["box"])).getbbox():
                    raise ValueError("TRADINGVIEW_PRECEDING_CARD_PIXELS_CHANGED")


def _single_image_panel(asset: dict, card: dict, folder: Path) -> dict:
    """Single-image transports display the release card first, then the intact chart."""
    from copy import deepcopy
    from PIL import Image
    panel = deepcopy(asset)
    with Image.open(card["path"]) as first, Image.open(asset["path"]) as chart:
        width, height = max(first.width, chart.width), first.height + chart.height
        canvas = Image.new("RGB", (width, height), "white")
        x1, x2 = (width - first.width) // 2, (width - chart.width) // 2
        canvas.paste(first.convert("RGB"), (x1, 0))
        canvas.paste(chart.convert("RGB"), (x2, first.height))
        name = hashlib.sha256((card["sha256"] + asset["sha256"]).encode()).hexdigest()[:20]
        path = folder / ("card-and-tradingview-" + name + ".png")
        canvas.save(path, format="PNG")
        box = panel["tradingview_snapshot"]["framing"]["original_box"]
        panel["tradingview_snapshot"]["framing"]["original_box"] = [
            box[0] + x2, box[1] + first.height, box[2] + x2, box[3] + first.height]
        panel["preceding_card"] = {**deepcopy(card), "box": [x1, 0, x1 + first.width, first.height]}
    panel.update(asset_id="tradingview-panel-" + name, path=str(path), sha256=_sha256(path),
        width=width, height=height, derivative_only=True,
        article_inclusion=False, canonical_article_media=False,
        caption=str(card.get("caption") or "") + ". " + asset["caption"],
        alt_text=str(card.get("alt_text") or "") + ". " + asset["alt_text"])
    return panel


def prepare_article_snapshot(article: Mapping[str, Any], assets: list[dict], *, output_dir: Path,
                             selected_candidate: Mapping[str, Any] | None = None) -> tuple[dict, list[dict]]:
    """Capture once before article registration; keep the current card on any failure.

    The writer names the discussed market. A single structured candidate asset can
    supply it too. We never pick an arbitrary market from a multi-market release.
    """
    from .publication_image_contract_v1 import EFFECTIVE_FROM
    if datetime.now(timezone.utc) >= EFFECTIVE_FROM:
        return prepare_contract_article(article, assets, output_dir=output_dir,
                                        selected_candidate=selected_candidate)
    from copy import deepcopy
    article, assets = deepcopy(article), deepcopy(assets)
    candidate = selected_candidate or {}
    aliases = {"GOLD": "XAUUSD", **{m: m for m in SYMBOLS}}
    value = article.get("market_asset")
    if not value:
        values = candidate.get("asset_ids") or []
        if isinstance(values, str):
            values = [values]
        markets = {aliases[str(v).upper()] for v in values if str(v).upper() in aliases}
        value = next(iter(markets)) if len(markets) == 1 else None
    market = aliases.get(str(value).upper())
    if not market:
        return article, assets
    article["market_asset"] = market
    if article.get("retrospective") or "Retrospective analysis, written on" in str(article.get("substack_body_markdown")):
        article["tradingview_snapshot_outcome"] = {"status": "JIM_DECISION_19B_NO_POST_EVENT_CHART", "market": market}
        return article, assets
    # Terms section 4: free publication only, until written paid-use permission.
    if article.get("paid") or article.get("paywall") or article.get("audience") in {"paid", "paid_subscribers"}:
        article["tradingview_snapshot_outcome"] = {"status": "PUBLIC_REDISTRIBUTION_NOT_LICENSED", "market": market}
        return article, assets
    existing = next((a for a in assets if a.get("modality") == "tradingview_chart_snapshot"
                     and not a.get("derivative_only")), None)
    folder = Path(output_dir) / "media" / "tradingview"
    # This is an operation artifact, reused on resume including a failed attempt.
    key = hashlib.sha256(json.dumps([market, article.get("title"), article.get("substack_body_markdown")],
                                    sort_keys=True).encode()).hexdigest()[:20]
    saved = folder / (key + ".json")
    try:
        if existing:
            asset = existing
        elif saved.is_file():
            prior = json.loads(saved.read_text(encoding="utf-8"))
            if prior["status"] != "CAPTURED":
                article["tradingview_snapshot_outcome"] = prior
                return article, assets
            asset = prior["asset"]
        else:
            taken = capture(market, "240", folder)
            asset = snapshot_asset(market, article["title"], taken, folder)
        validate_snapshot_asset(asset, article)
        asset = {**asset, "placement_after": "standfirst", "article_inclusion": True,
                 "canonical_article_media": True,
                 "canonical_article_section_association": "introduction"}
        outcome = {"status": "CAPTURED", "market": market, "asset": asset}
    except Exception as exc:  # A failed optional capture never stops the article.
        outcome = {"status": "FAILED", "market": market, "cause": str(exc)[:200]}
        asset = None
    if not saved.is_file():
        try:
            folder.mkdir(parents=True, exist_ok=True)
            saved.write_text(json.dumps(outcome, sort_keys=True), encoding="utf-8")
        except OSError:
            pass
        record_outcome({k: v for k, v in outcome.items() if k != "asset"})
    article["tradingview_snapshot_outcome"] = {k: v for k, v in outcome.items() if k != "asset"}
    if asset:
        event = article.get("article_type") in {"EVENT_PREVIEW", "EVENT_REVIEW"} or article.get("release_analysis") is True
        decision_93 = bool(article.get("scenario_analysis")) or article.get("publication_quality_policy") == "JIM_DECISION_93"
        if decision_93:
            article["publication_quality_policy"] = "JIM_DECISION_93"
        # Preserve the older card inference for retained requests. Decision 93
        # explicitly distinguishes a market lead from a release-card lead.
        card_first = event or not decision_93
        if not existing:
            assets.append(asset)  # Keep the release card first.
        first_card = (next((a for a in assets if a.get("modality") == "source_bound_data_card"), None)
                      or next((a for a in assets if a.get("modality") == "source_backed_chart"), None)) if card_first else None
        selected = asset
        if first_card:
            try:
                selected = _single_image_panel(asset, first_card, folder)
                validate_snapshot_asset(selected, article)
            except Exception as exc:
                article["tradingview_snapshot_outcome"] = {"status": "FAILED", "market": market,
                    "cause": "SINGLE_IMAGE_PANEL_FAILED:" + str(exc)[:160]}
                record_outcome(article["tradingview_snapshot_outcome"])
                return article, [a for a in assets if a.get("modality") != "tradingview_chart_snapshot"]
            if selected["asset_id"] not in {a["asset_id"] for a in assets}:
                assets.append(selected)
            # The current compiler may have appended its release card after a
            # photo/history chart. Keep that card first on the canonical too.
            assets = [first_card, asset, *(a for a in assets
                      if a["asset_id"] not in {first_card["asset_id"], asset["asset_id"]})]
        elif decision_93:
            assets = [asset, *(a for a in assets if a["asset_id"] != asset["asset_id"])]
        article["lead_image_asset_id"] = assets[0]["asset_id"]
        article["tradingview_snapshot_asset_ids"] = [selected["asset_id"]]
        from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
        # One exact image also reaches transports with a single-image API. The
        # canonical keeps the separate release card first and snapshot second.
        choices = {d: [selected["asset_id"]] for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS}
        article["native_destination_media"] = choices
        if article.get("post_visual_destination_media") is not None:
            article["post_visual_destination_media"] = choices
        if article.get("visual_editorial_decision"):
            article["visual_editorial_decision"]["channel_media"] = choices
            article["visual_editorial_decision"]["tradingview_snapshot_asset_ids"] = [selected["asset_id"]]
    return article, assets


def _bound_article_snapshot(assets, article, folder, ratio):
    from .publication_image_contract_v1 import validate_scale

    market = article["market_asset"]
    for asset in assets:
        captured = asset.get("tradingview_snapshot") or {}
        if (asset.get("modality") == "tradingview_chart_snapshot"
                and captured.get("tv_symbol") == SYMBOLS[market]
                and (captured.get("framing") or {}).get("ratio") == ratio
                and asset.get("path") and captured.get("path")
                and all(Path(path).resolve().is_relative_to(folder.resolve())
                        for path in (asset["path"], captured["path"]))):
            try:
                validate_snapshot_asset(asset, article)
                validate_scale(market, captured)
            except (ValueError, OSError):
                continue
            return asset
    state_path = folder / ("tradingview_capture_v1.json" if ratio == "16:9" else "tradingview_capture_4x5_v1.json")
    if state_path.is_file():
        state = json.loads(state_path.read_bytes())
        captured = state.get("snapshot") or {}
        if (state.get("status") == "CAPTURED" and state.get("market") == market
                and captured.get("capture_ratio") == ratio and captured.get("path")
                and Path(captured["path"]).resolve().is_relative_to(folder.resolve())):
            validate_scale(market, captured)
            asset = snapshot_asset(market, article["title"], captured, folder / "media_assets", ratio)
            validate_snapshot_asset(asset, article)
            return asset
    return None


def prepare_contract_article(article, assets, *, output_dir, selected_candidate=None, snapshot=None):
    """Decision 124 using the existing bounded capture and image owner."""
    from copy import deepcopy
    if article.get("morning_map") and not article.get("image_input_v1"):
        from .image_template_inputs_v1 import for_morning_map
        data = for_morning_map(article)
        if data:
            article = {**article, "image_input_v1": data}
    if article.get("image_input_v1"):
        from .image_quality_v1 import prepare_article_media
        return prepare_article_media(article, assets, output_dir=output_dir, snapshot=snapshot)
    from .publication_image_contract_v1 import POLICY as CONTRACT, _macro, image_type
    article, assets = deepcopy(article), deepcopy(assets)
    aliases = {"GOLD": "XAUUSD", **{m: m for m in SYMBOLS}}
    value = article.get("market_asset")
    if not value:
        ids = (selected_candidate or {}).get("asset_ids") or []
        ids = [ids] if isinstance(ids, str) else ids
        markets = {aliases[str(v).upper()] for v in ids if str(v).upper() in aliases}
        value = next(iter(markets)) if len(markets) == 1 else None
    market = aliases.get(str(value).upper())
    macro = _macro(article, {})
    if not market and not macro:
        return article, assets
    if market:
        article["market_asset"] = market
    # Retrospectives must use an event-bound retained chart, never today's
    # capture. Rights and historical objects retain their existing restrictions.
    if article.get("retrospective") or "Retrospective analysis, written on" in str(article.get("substack_body_markdown")):
        return article, assets
    if article.get("paid") or article.get("paywall") or article.get("audience") in {"paid", "paid_subscribers"}:
        raise SnapshotError("PUBLIC_REDISTRIBUTION_NOT_LICENSED")
    article["publication_image_contract"] = CONTRACT
    first = next((a for a in assets if image_type(a) == "FRED_GRAPH"), None) if macro else None
    symbol = article.get("macro_chart_symbol") if macro else market
    if macro and not first and not re.fullmatch(r"(?:ECONOMICS|FRED):[A-Z0-9_]+", str(symbol or "")):
        raise ValueError("MACRO_SOURCE_SERIES_SYMBOL_REQUIRED")
    folder = Path(output_dir) / "media" / "tradingview"
    key = hashlib.sha256(json.dumps([symbol, article.get("title"), article.get("substack_body_markdown")],
        sort_keys=True).encode()).hexdigest()[:24]
    row = {"key": key, "symbol": symbol, "instrument_title": article["title"],
           "at_utc": datetime.now(timezone.utc).isoformat(), "levels": {}}
    if not first and market and not macro:
        first = _bound_article_snapshot(assets, article, folder, "16:9")
    if not first:
        first = plan_snapshot(row, folder, snapshot=snapshot)
        article.update(tradingview_capture_state_path=str((folder / "tradingview_capture_v1.json").resolve()),
                       tradingview_capture_key=key)
    from .destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
    if first is None:
        article.update(tradingview_text_fallback=True, lead_image_asset_id=None,
            tradingview_instagram_skip="TRADINGVIEW_CAPTURE_FAILED_IMAGE_REQUIRED")
        choices = {d: [] for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS}
        article.update(native_destination_media=choices, post_visual_destination_media=choices)
        # CC-777 (decision 82): the article's own data card leads instead of text only, when it has one.
        return article_card_fallback(article, assets, output_dir=output_dir)
    first.update(article_inclusion=True, canonical_article_media=True, placement_after="introduction")
    # No locally drawn headline card leads a new market or macro article.
    portrait = None
    if first.get("modality") == "tradingview_chart_snapshot":
        if market and not macro:
            portrait = _bound_article_snapshot(assets, article, folder, "4:5")
        if not portrait:
            portrait = plan_snapshot(row, folder, snapshot=snapshot, ratio="4:5")
    rest = [a for a in assets if a["asset_id"] != first["asset_id"] and not a.get("post_card_binding")
            and not (market and not macro and a.get("modality") == "tradingview_chart_snapshot")]
    assets = [first, *rest]
    if first.get("modality") == "tradingview_chart_snapshot":
        if portrait:
            portrait.update(derivative_only=True, article_inclusion=False, canonical_article_media=False)
            assets.append(portrait)
    if not portrait:
        article["tradingview_instagram_skip"] = "TRADINGVIEW_PORTRAIT_CAPTURE_FAILED_IMAGE_REQUIRED"
    choices = {d: [first["asset_id"]] for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS}
    choices["instagram_business"] = [portrait["asset_id"]] if portrait else []
    article.update(lead_image_asset_id=first["asset_id"], tradingview_snapshot_asset_ids=[first["asset_id"]],
                   native_destination_media=choices, post_visual_destination_media=choices)
    if article.get("visual_editorial_decision"):
        article["visual_editorial_decision"].update(channel_media=choices,
            tradingview_snapshot_asset_ids=[first["asset_id"]] if first.get("tradingview_snapshot") else [])
    return article, assets


# CC-777, decision 82 on ordinary articles (Builder H, 23 Nov 2026). An article whose own bounded capture ended
# text-only goes out led by its own data card: the article's facts, never a title alone and never a target
# (decisions 40 and 157). The card is bound to that capture state and its cause, so the write boundary can check it.
ARTICLE_CARD_MODALITIES = ("source_bound_data_card", "source_backed_chart")
ARTICLE_CARD_TARGET = re.compile(r"(?<!inflation )\btargets?\b|\btake[- ]profit\b", re.I)


def article_card_refusal(asset: Mapping[str, Any]) -> str | None:
    """Why this asset cannot stand in for an article's failed chart; None when it can."""
    packet = asset.get("data_card_packet") or {}
    if asset.get("modality") not in ARTICLE_CARD_MODALITIES:
        return "ARTICLE_CHART_FALLBACK_NOT_A_DATA_CARD"
    if (asset.get("image_template") or asset.get("post_card_binding") or asset.get("derivative_only")
            or asset.get("preceding_card")):
        return "ARTICLE_CHART_FALLBACK_NOT_THE_ARTICLES_OWN_CARD"
    if asset.get("modality") == "source_bound_data_card":
        if asset.get("card_kind") == "TITLE_ONLY" or not packet.get("facts"):
            return "ARTICLE_CHART_FALLBACK_TITLE_ONLY"
    elif not (asset.get("owned_diagram_data_sha256") or asset.get("source_links") or asset.get("editorial_data_packet")):
        return "ARTICLE_CHART_FALLBACK_NO_BOUND_DATA"
    shown = " ".join(str(value or "") for value in (asset.get("alt_text"), asset.get("caption"), packet.get("title"),
                                                    json.dumps(packet.get("facts") or [], sort_keys=True)))
    if ARTICLE_CARD_TARGET.search(shown):
        return "ARTICLE_CHART_FALLBACK_TARGET_REFUSED"
    path = Path(str(asset.get("path") or ""))
    if not asset.get("path") or not path.is_file() or _sha256(path) != asset.get("sha256"):
        return "ARTICLE_CHART_FALLBACK_BYTES_CHANGED"
    return None


def article_card_fallback(article: Mapping[str, Any], assets: list[dict], *, output_dir) -> tuple[dict, list[dict]]:
    """Lead with the article's own card once its own capture ended text-only; otherwise keep the text fallback."""
    from copy import deepcopy
    from PIL import Image
    from .destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
    from .publication_image_contract_v1 import _macro

    article = deepcopy(dict(article))
    market = article.get("market_asset")
    if market not in SYMBOLS or _macro(article, {}) or not article.get("tradingview_text_fallback"):
        return article, []
    path = Path(str(article.get("tradingview_capture_state_path") or "")).resolve()
    state = json.loads(path.read_bytes()) if (path.is_relative_to(Path(output_dir).resolve())
                                               and path.is_file()) else {}
    if (state.get("key") != article.get("tradingview_capture_key") or state.get("market") != market
            or state.get("status") != "TEXT_ONLY" or not state.get("cause")):
        return article, []
    refusals = {}
    card = None
    for asset in assets or []:
        cause = article_card_refusal(asset)
        if cause is None:
            card = asset
            break
        refusals[str(asset.get("asset_id"))] = cause
    if card is None:
        # Still text only: record why no card could stand in (NO_CARD when the article had none).
        article["tradingview_card_fallback_refused"] = refusals or {"": "ARTICLE_CHART_FALLBACK_NO_CARD"}
        return article, []
    binding = {"key": state["key"], "market": market, "ratio": "16:9", "cause": state["cause"]}
    card = {**deepcopy(card), "article_chart_fallback": binding, "article_inclusion": True,
            "canonical_article_media": True, "placement_after": "introduction"}
    with Image.open(card["path"]) as image:
        portrait_ok = .8 - .003 <= image.width / image.height <= 1.91
    choices = {d: [card["asset_id"]] for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS}
    article.pop("tradingview_text_fallback", None)
    article.pop("tradingview_instagram_skip", None)
    if not portrait_ok:
        choices["instagram_business"] = []
        article["tradingview_instagram_skip"] = "ARTICLE_CHART_FALLBACK_CARD_RATIO_IMAGE_REQUIRED"
    article.update(lead_image_asset_id=card["asset_id"], native_destination_media=choices,
                   post_visual_destination_media=choices,
                   tradingview_card_fallback={"asset_id": card["asset_id"], "cause": state["cause"],
                                              "key": state["key"], "market": market})
    if article.get("visual_editorial_decision"):
        article["visual_editorial_decision"].update(channel_media=choices, tradingview_snapshot_asset_ids=[])
    record_outcome({"status": "ARTICLE_FACT_CARD", "key": state["key"], "market": market,
                    "cause": state["cause"], "asset_id": card["asset_id"]})
    return article, [card]


def fallback_card(*, title: str, facts: list[tuple[str, str]], dated_line: str, out_dir: Path,
                  kicker: str = "Plan status", ratio: str = "16:9") -> dict:
    """CC-290's fact card with the plan's own numbers, as a delivery-only post image."""
    from live_contentops.fact_card_design_v1 import CardSpec, INSTAGRAM_SIZE, X_SIZE, render_fact_card
    packet = {"policy": POLICY, "kind": "PLAN_FACT_CARD", "title": title, "facts": [list(f) for f in facts],
              "dated_line": dated_line, "kicker": kicker}
    digest = hashlib.sha256(json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()
    path = Path(out_dir).resolve() / f"plan-fact-card-{digest[:20]}-{ratio.replace(':', 'x')}.png"
    size = INSTAGRAM_SIZE if ratio == "4:5" else X_SIZE
    render_fact_card(path, CardSpec(title=title, facts=tuple(facts), kicker=kicker, dated_line=dated_line),
                     size=size)
    width, height = size
    alt = title + ". " + ". ".join(f"{k}: {v}" for k, v in facts) + ". " + dated_line
    return {"asset_id": "plan-fact-card-" + digest[:20] + "-" + ratio.replace(":", "x"),
            "path": str(path), "sha256": _sha256(path),
            "width": width, "height": height, "mime_type": "image/png",
            "modality": "plan_fact_card", "card_kind": "PLAN_FACT_CARD",
            "media_role": "delivery_only", "role": "plan_facts", "delivery_only": True,
            "article_inclusion": False, "canonical_article_media": False,
            "provenance_status": "VERIFIED_CAPITAL_CHRONICLE_PLAN_EXPORT",
            "rights_basis": "Capital Chronicle's own plan numbers in its own card design (CC-290).",
            "attribution": "Capital Chronicle", "caption": title, "alt_text": alt,
            "data_card_packet": packet, "publication_authority": False}


# Decision 82 on a plan's analysis page (Builder E, 23 Nov 2026). The 22 Nov BTC page went out text-only after its
# capture failed; a page now carries CC-290's fact card with the plan's own numbers instead. No target (40, 157).
PAGE_STATUS_WORDS = {"WAITING": "Waiting for price to reach the entry zone", "TRIGGERED": "Entry filled",
                     "FILLED": "Entry filled", "CANCELLED": "Plan cancelled", "INVALIDATED": "Plan invalidated",
                     "EXPIRED": "Plan expired", "VIEW_CHANGED": "View changed", "CLOSED": "Plan closed",
                     "RESULT": "Plan closed"}


def page_card_facts(plan: Mapping[str, Any], status: Mapping[str, Any] | None = None) -> list[list[str]]:
    """Zone, invalidation, status and time of one plan, from Main's own registration. Never a target."""
    from .plan_status_posts_v1 import _built_plan, _display_plan, _instrument_title, _when, plan_facts

    state = (status or {}).get("status") or plan.get("status") or "WAITING"
    at = (status or {}).get("status_at_utc") or plan.get("status_at_utc") or plan["registered_at_utc"]
    levels = _display_plan(_built_plan(plan, state=state))
    row = {"instrument_title": _instrument_title(plan["asset_id"], levels), "price_basis": levels.get("price_basis"),
           "levels": levels, "entries": levels.get("entries") or [], "state": state, "at_utc": at}
    facts = [[label, PAGE_STATUS_WORDS.get(state, value) if label == "Status" else value]
             for label, value in plan_facts(row)]
    labels = {label for label, _ in facts}
    if not {"Entry zone", "Invalidation", "Status", "As of"} <= labels:
        raise ValueError("PLAN_PAGE_FACT_CARD_LEVELS_MISSING")
    if any(re.search(r"target", label + " " + value, re.I) for label, value in facts):
        raise ValueError("PLAN_PAGE_FACT_CARD_TARGET_REFUSED")
    return facts


def page_fact_card(plan: Mapping[str, Any], folder: Path, *, status: Mapping[str, Any] | None = None) -> dict | None:
    """The page's fact card once its own bounded capture has ended text-only; otherwise None."""
    from .plan_status_posts_v1 import TITLES

    folder = Path(folder)
    key, market = "plan-analysis-" + plan["plan_id"], plan["asset_id"]
    path = folder / "tradingview_capture_v1.json"
    state = json.loads(path.read_bytes()) if path.is_file() else {}
    if (state.get("key") != key or state.get("market") != market or state.get("status") != "TEXT_ONLY"
            or not state.get("cause")):
        return None
    facts = page_card_facts(plan, status)
    asset = fallback_card(title=f"{TITLES[market]}: our plan's levels", facts=[tuple(f) for f in facts],
                          dated_line=dict(facts)["As of"], out_dir=folder / "media_assets", kicker="Plan levels")
    asset["plan_chart_fallback"] = {"key": key, "market": market, "ratio": "16:9", "cause": state["cause"]}
    return asset


# --- worker: runs in the Playwright venv, one snapshot, then exits -------------------------

_RANGE_SCRIPT = """async ({from, to}) => {
    const api = window.TradingViewApi;
    if (!api || typeof api.activeChart !== 'function') return {error: 'TRADINGVIEW_CHART_API_ABSENT'};
    const chart = api.activeChart();
    // Hide the live last-price line and label, so the historical window shows no current value.
    const overrides = {'mainSeriesProperties.showPriceLine': false, 'scalesProperties.showSeriesLastValue': false,
                       'mainSeriesProperties.showCountdown': false};
    let hidden = false;
    for (const target of [api, chart]) {
        try {
            if (typeof target.applyOverrides === 'function') { await target.applyOverrides(overrides); hidden = true; break; }
        } catch (e) {}
    }
    try {
        await chart.setVisibleRange({from, to}, {applyDefaultRightMargin: false, percentRightMargin: 0});
    } catch (e) {
        return {error: 'TRADINGVIEW_VISIBLE_RANGE_REFUSED'};
    }
    return {live_values_hidden: hidden};
}"""


def _read_visible_range(page) -> dict:
    try:
        return page.evaluate("""() => {
            const range = window.TradingViewApi.activeChart().getVisibleRange();
            return {from: range.from, to: range.to}; }""")
    except Exception:
        return {"error": HISTORICAL_RANGE_UNCONFIRMED}


def _apply_visible_range(page, steps, window: Mapping[str, Any]) -> dict:
    """CC-778: set the dated window through the chart page's own API; older bars load before the read-back."""
    outcome = page.evaluate(_RANGE_SCRIPT, {"from": window["from"], "to": window["to"]})
    if outcome.get("error"):
        raise SnapshotError(outcome["error"])
    page.wait_for_timeout(steps.at("historical_bars").left(2500))
    return {"live_values_hidden": outcome.get("live_values_hidden") is True}


def _hover_last_bar(page, steps, window: Mapping[str, Any]) -> dict:
    """Rest the cursor on the window's last bar, so the legend shows that bar and never a live value."""
    pane = page.evaluate("""() => {
        const canvases = [...document.querySelectorAll('.chart-gui-wrapper canvas')]
            .map(c => c.getBoundingClientRect()).filter(r => r.width > 200 && r.height > 200);
        canvases.sort((a, b) => b.width * b.height - a.width * a.height);
        const r = canvases[0];
        return r ? [r.x, r.y, r.width, r.height] : null; }""")
    if not pane:
        return {"visible_last_close_cause": "TRADINGVIEW_CHART_PANE_NOT_FOUND"}
    x, y, width, height = pane
    bars = max(1.0, (window["to"] - window["from"]) / window["step"])
    page.mouse.move(x + width - .45 * width / bars, y + height / 2)
    page.wait_for_timeout(steps.at("legend_last_bar").left(600))
    close = page.evaluate("""() => {
        const items = [...document.querySelectorAll('[data-name="legend-series-item"] [class*="valueItem"]')];
        for (const item of items) {
            const title = item.querySelector('[class*="valueTitle"]');
            const value = item.querySelector('[class*="valueValue"]');
            if (title && value && title.innerText.trim() === 'C') return value.innerText.trim();
        }
        return null; }""")
    if close is None:
        return {"visible_last_close": None, "visible_last_close_cause": "TRADINGVIEW_LEGEND_CLOSE_NOT_FOUND"}
    return {"visible_last_close": close, "visible_last_close_cause": None}


def _worker(args: dict) -> dict:
    import time
    from playwright.sync_api import sync_playwright
    started = time.time()
    budget = max(15000, int(args.get("budget_ms") or 50000))
    steps = _StepBudget(budget)
    out_dir = Path(args["out_dir"])
    viewport = dict(PORTRAIT_VIEWPORT if args.get("ratio") == "4:5" else VIEWPORT)
    try:
        return _worker_steps(args, steps, started, budget, out_dir, viewport, sync_playwright)
    except Exception as exc:
        raise SnapshotError(steps.cause(exc)) from exc


def _worker_steps(args, steps, started, budget, out_dir, viewport, sync_playwright):
    import time
    reset_cause = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chromium", timeout=steps.at("launch").left(30000))
        try:
            # A new context is a fresh, empty profile: guest chart, nothing saved, nothing shared.
            context = browser.new_context(viewport=viewport, accept_downloads=True, locale="en-US",
                                          timezone_id="UTC", color_scheme="light")
            page = context.new_page()
            if args.get("probe_geometry", True):
                page.add_init_script("""(() => {
                    const fill = CanvasRenderingContext2D.prototype.fillText;
                    const seen = new WeakMap();
                    window.__cc459Labels = seen;
                    for (const name of ['clearRect', 'fillRect']) {
                        const original = CanvasRenderingContext2D.prototype[name];
                        CanvasRenderingContext2D.prototype[name] = function(x,y,w,h,...rest) {
                            if (x <= 0 && y <= 0 && w >= this.canvas.width-1 && h >= this.canvas.height-1)
                                seen.delete(this.canvas);
                            return original.call(this,x,y,w,h,...rest);
                        };
                    }
                    CanvasRenderingContext2D.prototype.fillText = function(text, x, y, ...rest) {
                        if (/^-?[\\d,.]+$/.test(String(text))) {
                            let labels = seen.get(this.canvas);
                            if (!labels) seen.set(this.canvas, labels = new Map());
                            const t = this.getTransform();
                            const m = this.measureText(String(text));
                            labels.set(String(text), {text: String(text), x: t.a*x+t.e, y: t.d*y+t.f,
                                baseline: this.textBaseline, font: this.font,
                                ascent: m.actualBoundingBoxAscent, descent: m.actualBoundingBoxDescent});
                        }
                        return fill.call(this, text, x, y, ...rest);
                    };
                })();""")
            page.goto(args["url"], wait_until="domcontentloaded", timeout=steps.at("open_chart").left(budget // 2))
            page.wait_for_selector("canvas", timeout=steps.at("chart_canvas").left(budget // 3))
            page.wait_for_function(
                "() => { const t = document.title || ''; return /\\d/.test(t); }",
                timeout=steps.at("price_title").left(budget // 4))
            page.wait_for_timeout(steps.at("paint").left(2500))  # last bars paint
            if args.get("reset_price_scale"):
                # Optional: the parent checks the price scale of every download anyway. A click that
                # cannot land (an overlay, a slow axis) no longer fails the whole retry.
                try:
                    page.locator('[data-name="price-axis-A"] canvas').first.dblclick(
                        timeout=steps.at("reset_price_scale").left(5000))
                    page.wait_for_timeout(steps.left(500))
                except SnapshotError:
                    raise
                except Exception as exc:
                    reset_cause = steps.cause(exc)
            window_range = args.get("visible_range")
            history = {}
            if window_range:
                history = _apply_visible_range(page, steps, window_range)
            legend = page.evaluate("""() => {
                const q = s => [...document.querySelectorAll(s)].map(e => e.innerText.trim()).filter(Boolean);
                return [...q('[data-name="legend-source-title"]'), ...q('[data-qa-id="legend-source-title"]'),
                        ...q('#header-toolbar-intervals button[aria-checked="true"]'),
                        ...q('#header-toolbar-intervals')].join(' · '); }""")
            # TradingView's download excludes page chrome. Resize the *chart*
            # viewport against its measured download dimensions; never pad or
            # crop a wide chart into a portrait. At most two geometry repairs.
            for shape_attempt in range(3):
                if window_range:
                    if shape_attempt:
                        # A resize moves the left edge; set the same window again before this download.
                        history = _apply_visible_range(page, steps, window_range)
                    history.update(_hover_last_bar(page, steps, window_range))
                else:
                    page.mouse.move(viewport["width"] // 3, viewport["height"] // 2)
                geometry_probe = page.evaluate("""() => [...document.querySelectorAll('canvas')].map(c => {
                    const r = c.getBoundingClientRect();
                    return {width: c.width, height: c.height, rect: [r.x,r.y,r.width,r.height],
                        parents: [c.parentElement, c.parentElement?.parentElement].map(e =>
                            ({name:e?.getAttribute('data-name'), cls:e?.className})),
                        labels: [...(window.__cc459Labels?.get(c)?.values() || [])]};
                })""") if args.get("probe_geometry", True) else None
                if args.get("probe_geometry", True):
                    axis_png = page.locator('[data-name="price-axis-A"] canvas').first.evaluate("c => c.toDataURL('image/png').split(',')[1]")
                    axis_file = out_dir / "price-axis.png"
                    axis_file.write_bytes(base64.b64decode(axis_png))
                with page.expect_download(timeout=steps.at("download").left(20000)) as download:
                    page.keyboard.press("Control+Alt+KeyS")
                name = download.value.suggested_filename
                target = out_dir / name
                download.value.save_as(str(target))
                from PIL import Image
                with Image.open(target) as image:
                    width, height = image.size
                wanted = args.get("chart_size")
                if wanted and (width, height) == tuple(wanted):
                    break
                if not wanted and (args.get("ratio") != "4:5" or width * 5 == height * 4):
                    break
                if shape_attempt == 2:
                    raise SnapshotError("INSTAGRAM_NATIVE_4X5_CHART_REQUIRED")
                target_height = wanted[1] if wanted else -(-height // 5) * 5
                target_width = wanted[0] if wanted else target_height * 4 // 5
                viewport = {"width": viewport["width"] + target_width - width,
                            "height": viewport["height"] + target_height - height}
                page.set_viewport_size(viewport)
                page.wait_for_timeout(steps.at("resize").left(500))  # bounded canvas repaint after resize
            result = {"path": str(target), "suggested_filename": name, "legend": legend, "page_title": page.title(),
                    "capture_ratio": args.get("ratio", "16:9"), "capture_viewport": viewport,
                    "captured_at_utc": datetime.now(timezone.utc).isoformat(), "seconds": round(time.time() - started, 1),
                    **({"geometry_probe": geometry_probe, "axis_path": str(axis_file)} if geometry_probe else {}),
                    **({"price_scale_reset_cause": reset_cause} if reset_cause else {}), **history}
            if window_range:
                # The window as it stood after the download, read once more for the parent's check.
                result["visible_range_observed"] = _read_visible_range(page)
            # The parent still checks the symbol, interval, PNG and price scale.
            # Save this download's metadata before Chromium closes its context.
            if args.get("worker_result_path"):
                result_path = Path(args["worker_result_path"])
                staged = result_path.with_suffix(".tmp")
                staged.write_text(json.dumps(result), encoding="utf-8")
                staged.replace(result_path)
            if geometry_probe:
                (out_dir / "visible-axis-geometry.json").write_text(json.dumps(result,sort_keys=True),encoding="utf-8")
            return result
        finally:
            browser.close()


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--worker":
    try:
        print(json.dumps(_worker(json.loads(sys.argv[2]))))
    except SnapshotError as error:
        print(json.dumps({"error": str(error)[:200]}))
        raise SystemExit(1)
