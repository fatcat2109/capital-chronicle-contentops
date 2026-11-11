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
After failure, text-capable destinations use text and image-required destinations are skipped.

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
from typing import Any, Mapping

POLICY = "contentops.tradingview_snapshot.v1"
CREDIT = "Chart: TradingView"
# Jim's decision 107 (10 Nov): charts European and US readers trust, futures, ETFs or spot, never a CFD feed.
# Each keeps the plan's price scale: spot gold and FX from ICE, the S&P 500 cash index, WTI's front-month
# futures (the DEMO book's oil follows it), spot Bitcoin. All six captured by this worker on 9 Nov, 17:50Z.
# The paused site's reviewed map (Main ui/src/product/public-desk/reviewed-tradingview-symbols.json) still
# lists the old CFD feeds; it follows when the site returns (decision 84).
SYMBOLS = {"XAUUSD": "FX_IDC:XAUUSD", "US500": "SP:SPX", "EURUSD": "FX_IDC:EURUSD",
           "USDJPY": "FX_IDC:USDJPY", "USOIL": "NYMEX:CL1!", "BTCUSD": "COINBASE:BTCUSD"}
NAMES = {"XAUUSD": "Gold spot / US dollar (ICE)", "US500": "S&P 500 index",
         "EURUSD": "Euro / US dollar spot (ICE)", "USDJPY": "US dollar / Japanese yen spot (ICE)",
         "USOIL": "WTI light crude oil futures, front month (NYMEX)", "BTCUSD": "Bitcoin / US dollar (Coinbase spot)"}
REVIEWED_MAP = Path(r"A:\Capital Chronicle\Worktrees\codex-web-cc254-clean\ui\src\product\public-desk"
                    r"\reviewed-tradingview-symbols.json")
INTERVAL_LABELS = {"60": "1h", "240": "4h", "D": "1D"}
# Ops Product, 5 Nov: 16:9 for X, Threads, Telegram, Discord, LinkedIn and Facebook; 4:5 for Instagram.
RATIOS = {"16:9": (16, 9), "4:5": (4, 5)}
# A 1910x850 page gives a snapshot of about 1524x856, already close to 16:9.
VIEWPORT = {"width": 1910, "height": 850}
PORTRAIT_VIEWPORT = {"width": 1472, "height": 1350}
TIMEOUT_SECONDS = 60
PLAYWRIGHT_PYTHON = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v1-runtime\venv\Scripts\python.exe")
OUTCOMES = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\tradingview_snapshot_outcomes_v1.jsonl")
RIGHTS_BASIS = ("TradingView Terms of Use section 4 (checked 5 Nov 2026): chart snapshots may be used in "
                "publications with TradingView's attribution clearly visible; the attribution is kept "
                "uncropped and the post says 'Chart: TradingView' (Jim's decision 82). Free pages only (reason 2a).")


class SnapshotError(RuntimeError):
    pass


class SnapshotPending(ValueError):
    """The existing minute consumer resumes the same capture, without a new job."""


PLAN_CACHE_SECONDS = 15 * 60
PLAN_WAIT_SECONDS = 5 * 60
PLAN_ATTEMPTS = 2


def plan_snapshot(row: Mapping[str, Any], folder: Path, *, snapshot=None, snapshot_allowed=None,
                  now: datetime | None = None, ratio: str = "16:9") -> dict | None:
    """CC-459's bounded capture/cache owner. A None result means text after two failures.

    Only image artifacts are cached; this is not another scheduler or publication store.
    The market, source download hash, capture clock and first failure stay bound.
    """
    now = now or datetime.now(timezone.utc)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    media = folder / "media_assets"
    market = row["symbol"]
    interval = interval_for((row.get("levels") or {}).get("valid_until_utc"), row["at_utc"])
    suffix = "" if ratio == "16:9" else "_" + ratio.replace(":", "x")
    state_path = folder / ("tradingview_capture" + suffix + "_v1.json")
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {
        "key": row["key"], "market": market, "started_at_utc": now.isoformat(), "attempts": 0}
    if state.get("key") != row["key"] or state.get("market") != market:
        raise ValueError("TRADINGVIEW_PLAN_CAPTURE_BINDING_CHANGED")

    def save():
        state_path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")

    cache_file = folder.parent / "tradingview_cache" / (market + suffix + ".json")
    taken = None
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        captured = _utc(cached.get("captured_at_utc"))
        if (captured and 0 <= (now - captured).total_seconds() < PLAN_CACHE_SECONDS
                and cached.get("tv_symbol") == SYMBOLS[market]
                and Path(cached["path"]).is_file() and _sha256(Path(cached["path"])) == cached["sha256"]):
            taken = cached
    except (OSError, ValueError, KeyError, TypeError):
        pass
    # Preserve this exact post's successful image even when it resumes after the cache expires.
    if not taken and state.get("snapshot"):
        prior = state["snapshot"]
        if prior.get("tv_symbol") == SYMBOLS[market] and _sha256(Path(prior["path"])) == prior["sha256"]:
            taken = prior
    if taken:
        asset = snapshot_asset(market, row.get("instrument_title") or NAMES[market], taken, media, ratio)
        validate_snapshot_asset(asset)
        if state.get("status") != "CAPTURED":
            state.update(status="CAPTURED", snapshot=taken, cache_hit=True)
            save()
            record_outcome({k: v for k, v in state.items() if k != "snapshot"})
        return asset
    if state.get("status") == "TEXT_ONLY":
        return None
    deadline = _utc(state["started_at_utc"]) + timedelta(seconds=PLAN_WAIT_SECONDS)
    while state["attempts"] < PLAN_ATTEMPTS and datetime.now(timezone.utc) < deadline:
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
                taken = capture(market, interval, media / "4x5" if suffix else media,
                    timeout=min(TIMEOUT_SECONDS, max(1, remaining)), ratio=ratio)
            asset = snapshot_asset(market, row.get("instrument_title") or NAMES[market], taken, media, ratio)
            validate_snapshot_asset(asset)
            state.update(status="CAPTURED", snapshot=taken, cache_hit=False)
            save()
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(taken, sort_keys=True), encoding="utf-8")
            record_outcome({k: v for k, v in state.items() if k != "snapshot"})
            return asset
        except Exception as exc:
            state.setdefault("first_cause", str(exc)[:200])
            state["cause"] = str(exc)[:200]
            save()
    state.update(status="TEXT_ONLY", cause=state.get("first_cause") or "TRADINGVIEW_CAPTURE_WAIT_EXPIRED")
    save()
    record_outcome(state)
    return None


# Jim decision 87 (CC-316): memory measurements never gate capture.


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
    process = subprocess.Popen([python, "-B", str(Path(__file__).resolve()), "--worker", json.dumps(args)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        out, err = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(process.pid)
        process.communicate()
        raise SnapshotError("TRADINGVIEW_SNAPSHOT_TIMEOUT")
    lines = [line for line in out.decode("utf-8", "replace").splitlines() if line.startswith("{")]
    if process.returncode != 0 or not lines:
        tail = err.decode("utf-8", "replace").strip().splitlines()[-1:] or ["no output"]
        raise SnapshotError("TRADINGVIEW_SNAPSHOT_WORKER_FAILED:" + tail[0][:200])
    return json.loads(lines[-1])


def capture(market: str, interval: str, out_dir: Path, *, timeout: float = TIMEOUT_SECONDS,
            worker=None, python: str | None = None, ratio: str = "16:9", quote_provider=None) -> dict:
    """One TradingView Download image of the market at the interval, checked before use."""
    economic = bool(re.fullmatch(r"(?:ECONOMICS|FRED):[A-Z0-9_]+", str(market)))
    if (market not in SYMBOLS and not economic) or interval not in INTERVAL_LABELS or ratio not in RATIOS:
        raise SnapshotError("TRADINGVIEW_SNAPSHOT_MARKET_OR_INTERVAL_UNSUPPORTED")
    tv_symbol = market if economic else SYMBOLS[market]
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    args = {"url": chart_url(tv_symbol, interval), "out_dir": str(out_dir),
            "budget_ms": int(timeout * 1000) - 8000, "ratio": ratio}
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
    if ratio == "4:5" and abs(size[0] / size[1] - .8) > .003:
        raise SnapshotError("INSTAGRAM_NATIVE_4X5_CHART_REQUIRED")
    taken = {"path": str(path), "sha256": _sha256(path), "width": size[0], "height": size[1], **scale,
            "capture_ratio": ratio, "capture_viewport": result.get("capture_viewport"),
            "tv_symbol": tv_symbol, "interval": interval, "interval_label": INTERVAL_LABELS[interval],
            "legend": legend, "page_title": result.get("page_title"), "chart_url": args["url"],
            "suggested_filename": result.get("suggested_filename"),
            "captured_at_utc": result.get("captured_at_utc"), "seconds": result.get("seconds")}
    if not economic and (worker is None or quote_provider is not None):
        from .publication_image_contract_v1 import bind_scale
        taken = bind_scale(market, taken,
            quote=quote_provider(market, taken["captured_at_utc"]) if quote_provider else None)
    return taken


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
    snap = asset["tradingview_snapshot"]
    market = (article or {}).get("market_asset")
    if ((article or {}).get("paid") or (article or {}).get("paywall")
            or (article or {}).get("audience") in {"paid", "paid_subscribers"}):
        raise ValueError("PUBLIC_REDISTRIBUTION_NOT_LICENSED")
    economic = bool(re.fullmatch(r"(?:ECONOMICS|FRED):[A-Z0-9_]+", str(snap.get("tv_symbol") or "")))
    if (snap.get("policy") != POLICY or asset.get("credit") != CREDIT
            or asset.get("provenance_status") != "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE"
            or not asset.get("rights_basis") or snap.get("levels_drawn") != []
            or snap.get("target_drawn") is not False
            or (snap.get("tv_symbol") not in SYMBOLS.values() and not economic)
            or (market and SYMBOLS.get(market) != snap.get("tv_symbol"))
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


def fallback_card(*, title: str, facts: list[tuple[str, str]], dated_line: str, out_dir: Path,
                  kicker: str = "Plan status") -> dict:
    """CC-290's fact card with the plan's own numbers, as a delivery-only post image."""
    from live_contentops.fact_card_design_v1 import CardSpec, X_SIZE, render_fact_card
    packet = {"policy": POLICY, "kind": "PLAN_FACT_CARD", "title": title, "facts": [list(f) for f in facts],
              "dated_line": dated_line, "kicker": kicker}
    digest = hashlib.sha256(json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()
    path = Path(out_dir).resolve() / f"plan-fact-card-{digest[:20]}.png"
    render_fact_card(path, CardSpec(title=title, facts=tuple(facts), kicker=kicker, dated_line=dated_line),
                     size=X_SIZE)
    width, height = X_SIZE
    alt = title + ". " + ". ".join(f"{k}: {v}" for k, v in facts) + ". " + dated_line
    return {"asset_id": "plan-fact-card-" + digest[:20], "path": str(path), "sha256": _sha256(path),
            "width": width, "height": height, "mime_type": "image/png",
            "modality": "plan_fact_card", "card_kind": "PLAN_FACT_CARD",
            "media_role": "delivery_only", "role": "plan_facts", "delivery_only": True,
            "article_inclusion": False, "canonical_article_media": False,
            "provenance_status": "VERIFIED_CAPITAL_CHRONICLE_PLAN_EXPORT",
            "rights_basis": "Capital Chronicle's own plan numbers in its own card design (CC-290).",
            "attribution": "Capital Chronicle", "caption": title, "alt_text": alt,
            "data_card_packet": packet, "publication_authority": False}


# --- worker: runs in the Playwright venv, one snapshot, then exits -------------------------

def _worker(args: dict) -> dict:
    import time
    from playwright.sync_api import sync_playwright
    started = time.time()
    budget = max(15000, int(args.get("budget_ms") or 50000))
    out_dir = Path(args["out_dir"])
    viewport = dict(PORTRAIT_VIEWPORT if args.get("ratio") == "4:5" else VIEWPORT)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chromium")
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
            page.goto(args["url"], wait_until="domcontentloaded", timeout=budget // 2)
            page.wait_for_selector("canvas", timeout=budget // 3)
            page.wait_for_function(
                "() => { const t = document.title || ''; return /\\d/.test(t); }", timeout=budget // 4)
            page.wait_for_timeout(2500)  # last bars paint
            legend = page.evaluate("""() => {
                const q = s => [...document.querySelectorAll(s)].map(e => e.innerText.trim()).filter(Boolean);
                return [...q('[data-name="legend-source-title"]'), ...q('[data-qa-id="legend-source-title"]'),
                        ...q('#header-toolbar-intervals button[aria-checked="true"]'),
                        ...q('#header-toolbar-intervals')].join(' · '); }""")
            # TradingView's download excludes page chrome. Resize the *chart*
            # viewport against its measured download dimensions; never pad or
            # crop a wide chart into a portrait. At most two geometry repairs.
            for shape_attempt in range(3):
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
                with page.expect_download(timeout=20000) as download:
                    page.keyboard.press("Control+Alt+KeyS")
                name = download.value.suggested_filename
                target = out_dir / name
                download.value.save_as(str(target))
                from PIL import Image
                with Image.open(target) as image:
                    width, height = image.size
                if args.get("ratio") != "4:5" or width * 5 == height * 4:
                    break
                if shape_attempt == 2:
                    raise SnapshotError("INSTAGRAM_NATIVE_4X5_CHART_REQUIRED")
                target_height = -(-height // 5) * 5
                viewport = {"width": viewport["width"] + target_height * 4 // 5 - width,
                            "height": viewport["height"] + target_height - height}
                page.set_viewport_size(viewport)
                page.wait_for_timeout(500)  # bounded canvas repaint after resize
            result = {"path": str(target), "suggested_filename": name, "legend": legend, "page_title": page.title(),
                    "capture_ratio": args.get("ratio", "16:9"), "capture_viewport": viewport,
                    "captured_at_utc": datetime.now(timezone.utc).isoformat(), "seconds": round(time.time() - started, 1),
                    **({"geometry_probe": geometry_probe, "axis_path": str(axis_file)} if geometry_probe else {})}
            if geometry_probe:
                (out_dir / "visible-axis-geometry.json").write_text(json.dumps(result,sort_keys=True),encoding="utf-8")
            return result
        finally:
            browser.close()


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--worker":
    print(json.dumps(_worker(json.loads(sys.argv[2]))))
