"""CC-314 (Jim's decision 82, 5 Nov): a post about one market carries TradingView's own chart
snapshot of that market.

The image is TradingView's Download image (Ctrl+Alt+S), taken at posting time on a guest chart
in a throwaway Chromium profile Capital Chronicle owns (a fresh browser context per snapshot: no
account, no saved layout, no cookies, never Jim's TradingView or the X list feed's Chrome on CDP
9222). TradingView's Terms of Use, section 4, allow snapshots in publications while TradingView's
attribution stays clearly visible: the snapshot's own "Created with TradingView.com" header and
logo are never cropped (framing only pads), and each post says "Chart: TradingView". Section 3 bars
machine processing of TradingView content: one snapshot per post, displayed only, no data read.

A failed snapshot never stops the post: the caller falls back to a fact card with the plan's own
numbers (decision 42), and every outcome is counted in OUTCOMES.

Drawings: TradingView's guest chart refuses programmatic and hotkey drawings (5 Nov probe:
"Cannot create shape" for horizontal_line and rectangle, Alt+H draws nothing), so no level is
drawn; the post's text carries the zone and invalidation. A target is never drawn (decision 40).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
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
TIMEOUT_SECONDS = 60
PLAYWRIGHT_PYTHON = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v1-runtime\venv\Scripts\python.exe")
OUTCOMES = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\tradingview_snapshot_outcomes_v1.jsonl")
RIGHTS_BASIS = ("TradingView Terms of Use section 4 (checked 5 Nov 2026): chart snapshots may be used in "
                "publications with TradingView's attribution clearly visible; the attribution is kept "
                "uncropped and the post says 'Chart: TradingView' (Jim's decision 82). Free pages only (reason 2a).")


class SnapshotError(RuntimeError):
    pass


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
               if line.strip() and json.loads(line).get("status") != "CAPTURED")


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
            worker=None, python: str | None = None) -> dict:
    """One TradingView Download image of the market at the interval, checked before use."""
    if market not in SYMBOLS or interval not in INTERVAL_LABELS:
        raise SnapshotError("TRADINGVIEW_SNAPSHOT_MARKET_OR_INTERVAL_UNSUPPORTED")
    tv_symbol = SYMBOLS[market]
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    args = {"url": chart_url(tv_symbol, interval), "out_dir": str(out_dir), "budget_ms": int(timeout * 1000) - 8000}
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
    return {"path": str(path), "sha256": _sha256(path), "width": size[0], "height": size[1],
            "tv_symbol": tv_symbol, "interval": interval, "interval_label": INTERVAL_LABELS[interval],
            "legend": legend, "page_title": result.get("page_title"), "chart_url": args["url"],
            "suggested_filename": result.get("suggested_filename"),
            "captured_at_utc": result.get("captured_at_utc"), "seconds": result.get("seconds")}


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
    return {"asset_id": "tradingview-snapshot-" + digest[:20], "path": str(framed_path), "sha256": digest,
            "width": framing["width"], "height": framing["height"], "mime_type": "image/png",
            "modality": "tradingview_chart_snapshot", "card_kind": "TRADINGVIEW_SNAPSHOT",
            "media_role": "delivery_only", "role": "market_chart", "delivery_only": True,
            "article_inclusion": False, "canonical_article_media": False,
            "provenance_status": "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE", "rights_basis": RIGHTS_BASIS,
            "attribution": "TradingView", "credit": CREDIT,
            "caption": f"{title}: {label} chart of {NAMES[market]}. {CREDIT}.",
            "alt_text": f"TradingView {label} candlestick chart of {NAMES[market]}, "
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
    if (snap.get("policy") != POLICY or asset.get("credit") != CREDIT
            or asset.get("provenance_status") != "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE"
            or not asset.get("rights_basis") or snap.get("levels_drawn") != []
            or snap.get("target_drawn") is not False
            or snap.get("tv_symbol") not in SYMBOLS.values()
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
                or ImageChops.difference(original.convert("RGB"), framed.convert("RGB").crop(box)).getbbox()):
            raise ValueError("TRADINGVIEW_SNAPSHOT_ATTRIBUTION_CROPPED_OR_CHANGED")
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chromium")
        try:
            # A new context is a fresh, empty profile: guest chart, nothing saved, nothing shared.
            context = browser.new_context(viewport=VIEWPORT, accept_downloads=True, locale="en-US",
                                          timezone_id="UTC", color_scheme="light")
            page = context.new_page()
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
            page.mouse.move(VIEWPORT["width"] // 3, VIEWPORT["height"] // 2)
            with page.expect_download(timeout=20000) as download:
                page.keyboard.press("Control+Alt+KeyS")
            name = download.value.suggested_filename
            target = out_dir / name
            download.value.save_as(str(target))
            return {"path": str(target), "suggested_filename": name, "legend": legend, "page_title": page.title(),
                    "captured_at_utc": datetime.now(timezone.utc).isoformat(), "seconds": round(time.time() - started, 1)}
        finally:
            browser.close()


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--worker":
    print(json.dumps(_worker(json.loads(sys.argv[2]))))
