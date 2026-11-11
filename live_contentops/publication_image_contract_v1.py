"""CC-463 / decision 124: the image contract at the sole write boundary.

This module validates the existing chart service's output. It neither dispatches
posts nor obtains broker data. Saved Main quotes are used only for the displayed
price-scale comparison; no terminal, account or order API is imported.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs

POLICY = "CC463_TRADINGVIEW_FIRST_V1"
EFFECTIVE_FROM = datetime(2026, 11, 11, 14, 39, tzinfo=timezone.utc)
QUOTE_SKEW_SECONDS = 120
QUOTE_ROOT = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research")
# Percentage differences, not fractions. Initial limits and the retained
# observations (including their clock separation) are in CC-463/README.md.
MAX_DIFFERENCE_PCT = {"XAUUSD": .25, "US500": 1., "EURUSD": .10,
                      "USDJPY": .10, "USOIL": 1.50, "BTCUSD": .25}


class ImageContractError(ValueError):
    def __init__(self, cause, **details):
        super().__init__(cause)
        self.details = details


def utc(value):
    if isinstance(value, datetime):
        at = value
    else:
        at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if at.tzinfo is None:
        raise ImageContractError("TRADINGVIEW_PRICE_CLOCK_REQUIRED")
    return at.astimezone(timezone.utc)


def number(value):
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ImageContractError("TRADINGVIEW_PRICE_NOT_VALID") from None
    if isinstance(value, bool) or not math.isfinite(result) or result <= 0:
        raise ImageContractError("TRADINGVIEW_PRICE_NOT_VALID")
    return result


def chart_last_price(title):
    # The displayed last price in the guest chart's title, never a bar series.
    match = re.match(r"^\S+\s+([\d,]+(?:\.\d+)?)(?:\s|$)", str(title))
    if not match:
        raise ImageContractError("TRADINGVIEW_LAST_PRICE_NOT_VISIBLE")
    return number(match[1].replace(",", ""))


def saved_main_quote(market, captured_at, *, root=None):
    """Use the nearest exact tick already held by Main, with both clocks bound.

    File discovery is bounded to Main's existing preparation paths, and only
    recently written captures are parsed. No account fields leave this reader.
    An injected root keeps tests completely separate from the operating files.
    """
    at, root = utc(captured_at), Path(root or QUOTE_ROOT)
    paths = []
    for pattern in ("t2-runs/*/request/capture.json", "brain-runs/*/request/capture.json",
                    "brain-runs/*/shadow-driver/request/capture.json",
                    "daily-research-portfolio-*/requests/*/capture.json",
                    "daily-research-portfolio-*/.native-preparation/capture.json"):
        paths.extend(root.glob(pattern))
    candidates = []
    for path in sorted(set(paths), key=lambda p: p.stat().st_mtime, reverse=True):
        if abs(path.stat().st_mtime - at.timestamp()) > QUOTE_SKEW_SECONDS + 60:
            continue
        try:
            raw = path.read_bytes()
            data = json.loads(raw)
            if data.get("schema") != "CapitalChroniclePrimaryDemoAccountCaptureV1":
                continue
            if data.get("content_hash") != sha256(json.dumps(
                    {k: v for k, v in data.items() if k != "content_hash"},
                    sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                    allow_nan=False).encode()).hexdigest():
                continue
            tick = data.get("ticks", {}).get(market) or {}
            tick_at = datetime.fromtimestamp(
                tick["time_msc"] / 1000 if tick.get("time_msc") else tick["time"], timezone.utc)
            bid, ask = number(tick["bid"]), number(tick["ask"])
            known = utc(data["known_at_utc"])
            skew = (at - tick_at).total_seconds()
            if bid > ask or not -2 <= skew <= QUOTE_SKEW_SECONDS or known > at:
                continue
            candidates.append((abs(skew), {"market": market, "instrument": market,
                "price": (bid + ask) / 2, "quoted_at_utc": tick_at.isoformat(),
                "known_at_utc": known.isoformat(), "source_path": str(path.resolve()),
                "source_sha256": sha256(raw).hexdigest(), "source_content_hash": data["content_hash"],
                "price_basis": "plan_feed"}))
        except (OSError, ValueError, TypeError, KeyError, OverflowError):
            continue
        if len(candidates) >= 3:
            break
    if not candidates:
        raise ImageContractError("TRADINGVIEW_CONTEMPORANEOUS_MAIN_QUOTE_UNAVAILABLE", market=market,
                                 maximum_clock_skew_seconds=QUOTE_SKEW_SECONDS)
    return min(candidates, key=lambda item: item[0])[1]


def compare_scale(market, snapshot, quote):
    from .tradingview_snapshot_v1 import SYMBOLS
    if market not in SYMBOLS or snapshot.get("tv_symbol") != SYMBOLS[market]:
        raise ImageContractError("TRADINGVIEW_MARKET_SYMBOL_MISMATCH")
    if quote.get("market") != market or quote.get("instrument") != market:
        raise ImageContractError("TRADINGVIEW_PLAN_QUOTE_INSTRUMENT_MISMATCH")
    price = chart_last_price(snapshot.get("page_title"))
    own = number(quote.get("price"))
    skew = (utc(snapshot["captured_at_utc"]) - utc(quote["quoted_at_utc"])).total_seconds()
    if not -2 <= skew <= QUOTE_SKEW_SECONDS or utc(quote["known_at_utc"]) > utc(snapshot["captured_at_utc"]):
        raise ImageContractError("TRADINGVIEW_PLAN_QUOTE_STALE", clock_skew_seconds=skew)
    if not quote.get("source_path") or not quote.get("source_sha256"):
        raise ImageContractError("TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED")
    difference = price - own
    difference_pct = abs(difference) / own * 100
    result = {"policy": POLICY, "market": market, "tv_symbol": SYMBOLS[market],
        "chart_sha256": snapshot["sha256"], "chart_price": price, "quote": dict(quote),
        "captured_at_utc": snapshot["captured_at_utc"], "clock_skew_seconds": skew,
        "difference": difference, "difference_pct": difference_pct,
        "maximum_difference_pct": MAX_DIFFERENCE_PCT[market],
        "level_offset": difference if market == "USOIL" and quote.get("price_basis") != "chart_futures" else 0.}
    if difference_pct > MAX_DIFFERENCE_PCT[market]:
        raise ImageContractError("TRADINGVIEW_PRICE_SCALE_MISMATCH", **result)
    return result


def bind_scale(market, snapshot, *, quote=None):
    snapshot = dict(snapshot)
    snapshot["price_scale_check"] = compare_scale(market, snapshot,
        quote or saved_main_quote(market, snapshot["captured_at_utc"]))
    return snapshot


def validate_scale(market, snapshot):
    check = snapshot.get("price_scale_check") or {}
    if check.get("policy") != POLICY:
        raise ImageContractError("TRADINGVIEW_PRICE_SCALE_CHECK_REQUIRED")
    if check != compare_scale(market, snapshot, check.get("quote") or {}):
        raise ImageContractError("TRADINGVIEW_PRICE_SCALE_BINDING_CHANGED")
    return check


def image_type(asset):
    snapshot = asset.get("tradingview_snapshot") or {}
    symbol = str(snapshot.get("tv_symbol") or "")
    if asset.get("modality") == "tradingview_chart_snapshot":
        return "TRADINGVIEW_ECONOMIC_CHART" if symbol.startswith(("ECONOMICS:", "FRED:")) else "TRADINGVIEW_MARKET_CHART"
    if asset.get("modality") == "fred_graph":
        return "FRED_GRAPH"
    if asset.get("modality") == "documentary_photo":
        return "PHOTO"
    if asset.get("card_kind") or asset.get("modality") in {
            "source_bound_data_card", "source_backed_chart", "plan_fact_card", "plan_call_card"}:
        return "DRAWN_CARD"
    return "OTHER"


def _macro(article, intent):
    decision = article.get("visual_editorial_decision") or {}
    return bool(article.get("macro_data_post") or article.get("release_analysis")
        or article.get("article_type") in {"EVENT_PREVIEW", "EVENT_REVIEW"}
        or decision.get("analysis_scope") == "RELEASE_OR_POLICY" or intent.get("event_pack"))


def scope(store, intent, article):
    from .tradingview_snapshot_v1 import SYMBOLS
    if intent.get("plan_status_post"):
        from .plan_status_posts_v1 import _row_payload
        row = _row_payload(store, str(intent["plan_status_post"]))
        members = [_row_payload(store, key) for key in row["card_keys"]] if row.get("kind") == "run" else [row]
        return {m["symbol"]: m for m in members if m.get("symbol") in SYMBOLS}, False
    market = article.get("market_asset") or intent.get("market_asset")
    # Economic releases lead with the source series, even if their analysis also
    # discusses one financial market. Pure market commentary uses its market.
    return ({market: None} if market in SYMBOLS else {}), _macro(article, intent)


def _fred(asset):
    """Accept a source-bound FRED graph, never a locally drawn graph with a label."""
    graph = asset.get("fred_graph") or {}
    url = urlparse(str(graph.get("image_url") or ""))
    series = graph.get("series_ids") or []
    actual = parse_qs(url.query).get("id", [""])[0].split(",")
    source = urlparse(str(asset.get("source_page_url") or ""))
    if (image_type(asset) != "FRED_GRAPH" or url.scheme != "https"
            or url.hostname != "fred.stlouisfed.org" or url.path != "/graph/fredgraph.png"
            or not series or series != actual or source.hostname != "fred.stlouisfed.org"
            or not graph.get("source") or not graph.get("window")
            or "FRED" not in str(asset.get("credit") or "") or not asset.get("rights_basis")
            or not asset.get("sha256") or sha256(Path(asset["path"]).read_bytes()).hexdigest() != asset["sha256"]):
        raise ImageContractError("MACRO_SOURCE_GRAPH_BINDING_INVALID")


def validate_write(coordinator, intent, destination):
    """Check actual transport-selected media, once, for every fresh post type."""
    if coordinator._clock() < EFFECTIVE_FROM:
        return None
    from .article_publication_quality_v1 import article_inputs
    article, _, _ = article_inputs(intent)
    markets, macro = scope(coordinator.store, intent, article)
    if not markets and not macro:
        return None
    from ._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
    data = _durable_intent_inputs(intent)
    assets = data["media_assets"]
    if destination == "substack":
        assets = [a for a in assets if a.get("article_inclusion") is not False
                  and a.get("canonical_article_media") is not False]
    if not assets:
        # Only the existing bounded capture owner can establish exhaustion.
        folder = Path(str(intent.get("output_dir") or ""))
        rows = list(markets.values())
        states = []
        for row in rows:
            path = (folder.parent / row["key"] if row else folder) / "tradingview_capture_v1.json"
            state = json.loads(path.read_bytes()) if path.is_file() else {}
            states.append(state)
        if (destination != "instagram_business" and states and all(
                s.get("status") == "TEXT_ONLY" and (s.get("attempts", 0) >= 2
                or (coordinator._clock() - utc(s["started_at_utc"])).total_seconds() >= 300) for s in states)):
            return {"policy": POLICY, "text_fallback": True,
                    "first_causes": [s.get("first_cause") or s.get("cause") for s in states]}
        raise ImageContractError("MACRO_SOURCE_GRAPH_REQUIRED" if macro else "TRADINGVIEW_FIRST_IMAGE_REQUIRED")
    from . import tradingview_snapshot_v1 as tv
    lead = assets[0]
    if macro:
        if image_type(lead) == "FRED_GRAPH":
            _fred(lead)
        elif image_type(lead) == "TRADINGVIEW_ECONOMIC_CHART":
            tv.validate_snapshot_asset(lead)
        else:
            raise ImageContractError("MACRO_SOURCE_GRAPH_REQUIRED")
    else:
        if image_type(lead) != "TRADINGVIEW_MARKET_CHART" or lead.get("preceding_card"):
            raise ImageContractError("TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE")
        for asset in assets:
            if image_type(asset) != "TRADINGVIEW_MARKET_CHART":
                continue
            snap = asset.get("tradingview_snapshot") or {}
            market = next((m for m in markets if tv.SYMBOLS[m] == snap.get("tv_symbol")), None)
            if not market:
                raise ImageContractError("TRADINGVIEW_MARKET_SYMBOL_MISMATCH")
            tv.validate_snapshot_asset(asset, {"market_asset": market})
            check = validate_scale(market, snap)
            row = markets[market]
            if row:
                levels = row.get("levels") or {}
                instrument = levels.get("public_instrument") or {}
                if levels.get("price_basis") == "instrument" and instrument.get("kind") == "FUT" and market != "USOIL":
                    raise ImageContractError("TRADINGVIEW_PLAN_PRICE_BASIS_MISMATCH")
            if check["level_offset"] and row:
                overlay = asset.get("plan_overlay") or {}
                if overlay.get("price_scale_check") != check or not overlay.get("basis_label"):
                    raise ImageContractError("TRADINGVIEW_WTI_BASIS_LABEL_REQUIRED")
    if destination == "instagram_business":
        for asset in assets:
            snap = asset.get("tradingview_snapshot") or {}
            framing = snap.get("framing") or {}
            if (framing.get("mode") != "NATIVE_VIEWPORT" or snap.get("capture_ratio") != "4:5"
                    or abs(asset["width"] / asset["height"] - .8) > .003
                    or framing.get("original_box") != [0, 0, asset["width"], asset["height"]]):
                raise ImageContractError("INSTAGRAM_NATIVE_4X5_CHART_REQUIRED")
    return {"policy": POLICY, "markets": sorted(markets), "macro": macro,
            "first_image_type": image_type(lead)}
