"""CC-459: plan levels placed against TradingView's visible axis, never an invented scale.

Only the visible price-axis labels and canvas geometry are read. No bars, series or
indicator values are acquired. A failed geometric check keeps the intact plain snapshot.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from statistics import median

from PIL import Image, ImageChops, ImageDraw

POLICY = "CC459_VISIBLE_PRICE_SCALE_V1"
# Six real guest captures, both delivery ratios, checked 11 Nov 2026:
# docs/publisher/CC-459/six-market-scale-proof.json (grid error <= .50 px).
VERIFIED_MARKETS = frozenset({"XAUUSD", "US500", "EURUSD", "USDJPY", "USOIL", "BTCUSD"})


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def geometry(result):
    """Locate the *same* canvas's price labels in the downloaded image by exact pixels."""
    probes = result.get("geometry_probe") or []
    axis = next(c for c in probes if c["parents"][0].get("name") == "price-axis-A" and len(c["labels"]) >= 6)
    pane = next(c for c in probes if c["parents"][0].get("cls") == "chart-gui-wrapper"
                and c["height"] == axis["height"] and c["rect"][1] == axis["rect"][1])
    with Image.open(result["path"]) as source, Image.open(result["axis_path"]) as transparent:
        source = source.convert("RGB")
        rgba = transparent.convert("RGBA")
        white = Image.new("RGBA", rgba.size, "white")
        white.alpha_composite(rgba)
        axis_image = white.convert("RGB")
        ap, sp = axis_image.load(), source.load()
        points = [(x, y, ap[x, y]) for y in range(25, min(axis_image.height - 25, 360))
                  for x in range(5, axis_image.width - 1) if max(ap[x, y]) < 210]
        if len(points) < 80:
            raise ValueError("TRADINGVIEW_AXIS_LABEL_PIXELS_INSUFFICIENT")
        points = points[::max(1, len(points) // 240)]
        scores = []
        for x in range(max(0, source.width - axis_image.width - 40), source.width - axis_image.width + 1):
            for y in range(min(130, source.height - axis_image.height + 1)):
                score = sum(sp[x + px, y + py] == color for px, py, color in points) / len(points)
                scores.append((score, x, y))
        scores.sort(reverse=True)
        score, x, y = scores[0]
        if score < .97 or score - scores[1][0] < .02:
            raise ValueError("TRADINGVIEW_AXIS_DOWNLOAD_PIXEL_MATCH_FAILED")
        if x - pane["width"] < 0 or y < 22 or source.height - y - pane["height"] < 40:
            raise ValueError("TRADINGVIEW_PANE_OR_ATTRIBUTION_GEOMETRY_INVALID")
        anchors = []
        for label in axis["labels"]:
            value = float(label["text"].replace(",", ""))
            if not math.isfinite(value) or label.get("baseline") != "middle":
                continue
            # The text's ink centre, verified against the actual grid below.
            center = label["y"] + (label["descent"] - label["ascent"]) / 2 + y
            anchors.append((value, center))

        def fit(points, mode):
            transformed = [(math.log(p) if mode == "log" else p, q) for p, q in points]
            mx, my = (sum(t[i] for t in transformed) / len(transformed) for i in (0, 1))
            slope = sum((a-mx)*(b-my) for a,b in transformed) / sum((a-mx)**2 for a,b in transformed)
            return slope, my-slope*mx

        best = None
        for mode in ("linear", "log"):
            if mode == "log" and any(p <= 0 for p, _ in anchors):
                continue
            transformed = [(math.log(p) if mode == "log" else p,q) for p,q in anchors]
            slopes = [(d-b)/(c-a) for i,(a,b) in enumerate(transformed)
                      for c,d in transformed[i+1:] if c != a]
            a = median(slopes)
            b = median(y-a*x for x,y in transformed)
            inside = [(p,q) for p,q in anchors if abs(a*(math.log(p) if mode == "log" else p)+b-q) <= 1]
            if len(inside) < 6:
                continue
            a, b = fit(inside, mode)
            error = max(abs(a*(math.log(p) if mode == "log" else p)+b-q) for p,q in inside)
            if a < 0 and error <= 1 and (best is None or len(inside) > len(best[3])):
                best = (a,b,mode,inside,error)
        if not best:
            raise ValueError("TRADINGVIEW_VISIBLE_PRICE_SCALE_NOT_USABLE")
        a,b,mode,inside,error = best
        # Independent check: visible grid pixels in the download lie within two
        # pixels of the page's observed price labels, at at least six anchors.
        checked = []
        left, right = x-pane["width"], x
        for value, expected in inside:
            candidates = []
            for sy in range(max(y, round(expected)-2), min(y+pane["height"], round(expected)+3)):
                count = sum(1 for sx in range(left+15, right-15)
                            if 150 <= min(sp[sx,sy]) <= max(sp[sx,sy]) < 235
                            and max(sp[sx,sy])-min(sp[sx,sy]) < 5)
                candidates.append((count, sy))
            count, actual = max(candidates)
            if count > pane["width"] / 12 and abs(actual-expected) <= 2:
                checked.append({"price": value, "page_y_in_download": expected,
                                "grid_y": actual, "error_px": abs(actual-expected)})
        if len(checked) < 6:
            raise ValueError("TRADINGVIEW_AXIS_GRID_PIXEL_CHECK_FAILED")
        return {"policy": POLICY, "pane_box": [left,y,right,y+pane["height"]],
                "axis_origin": [x,y], "axis_pixel_match": score,
                "mode": mode, "slope": a, "intercept": b,
                "max_label_error_px": error, "grid_checks": checked,
                "source_sha256": hashlib.sha256(Path(result["path"]).read_bytes()).hexdigest()}


def source_binding(row):
    """The levels the overlay draws. Decision 82: a target is never drawn, so none is bound."""
    levels = row.get("levels") or {}
    fields = ("zone_low", "zone_high", "invalidation_level", "tick_size", "valid_until_utc", "direction")
    bound = {k: levels[k] for k in fields if k in levels}
    return {"key": row["key"], "symbol": row["symbol"], "source_content_hash": row.get("source_content_hash"),
            "levels": bound}


def _drawn_binding(source):
    # Images made before CC-583 bound a target field too; it is not part of what is drawn.
    return {**source, "levels": {k: v for k, v in (source.get("levels") or {}).items()
                                 if k not in {"target", "target_level"}}}


def target_drawn(asset):
    """CC-583: whether the overlay drew a target, from what it drew (its markers), never
    from the raw snapshot's own record, which describes the plain download."""
    overlay = (asset or {}).get("plan_overlay") or {}
    return (overlay.get("target_drawn") is True
            or any(m.get("label") == "Target" for m in overlay.get("markers") or []))


def _price_y(scale, price):
    price = float(price)
    if not math.isfinite(price) or (scale["mode"] == "log" and price <= 0):
        raise ValueError("TRADINGVIEW_OVERLAY_LEVEL_NOT_FINITE_OR_LOG_COMPATIBLE")
    return scale["slope"] * (math.log(price) if scale["mode"] == "log" else price) + scale["intercept"]


def _draw(image, overlay, offset):
    from .fact_card_design_v1 import _font
    scale = overlay["scale"]
    ox, oy = offset
    left, top, right, bottom = scale["pane_box"]
    # Preserve the entire TradingView legend, price axis, header and logo.
    left, top, right, bottom = left+16+ox, top+62+oy, right-16+ox, bottom-12+oy
    draw = ImageDraw.Draw(image, "RGBA")
    levels = deepcopy(overlay["source"]["levels"])
    # Decision 82: "A target is never drawn", whatever the bound source carries.
    levels.pop("target", None)
    levels.pop("target_level", None)
    offset = (overlay.get("price_scale_check") or {}).get("level_offset", 0)
    if offset:
        for field in ("zone_low", "zone_high", "invalidation_level"):
            if levels.get(field) is not None:
                levels[field] = float(levels[field]) + offset
    if overlay.get("basis_label"):
        font = _font("semibold", 16)
        label = overlay["basis_label"]
        width = draw.textbbox((0, 0), label, font=font)[2] + 16
        draw.rectangle((left + 8, top, left + 8 + width, top + 25), fill=(255, 255, 255, 245))
        draw.text((left + 15, top + 2), label, font=font, fill=(31, 60, 80, 255))
        top += 30
    markers = []
    entry_colour = (31,95,191,255) if overlay.get("entry_colour") == "blue" else (25,110,95,255)
    colors = {"Entry low": entry_colour, "Entry high": entry_colour, "Invalidation": (175,40,57,255)}
    from .plan_call_cards_v1 import level as display_level
    for label, price in [("Entry low",levels.get("zone_low")), ("Entry high",levels.get("zone_high")),
                         ("Invalidation",levels.get("invalidation_level"))]:
        if price is None:
            continue
        display = display_level(price, levels)
        displayed_price = display.replace(",", "")
        exact = _price_y(scale, displayed_price)+oy
        line = round(exact)
        edge = "above view" if line < top else "below view" if line > bottom else None
        markers.append({"label": label, "price": price, "y": line, "expected_y": exact,
                        "error_px": abs(line-exact), "edge": edge})
    low, high = levels.get("zone_low"), levels.get("zone_high")
    if low is not None and high is not None:
        ya,yb = sorted((_price_y(scale,display_level(low,levels).replace(",", ""))+oy,
                        _price_y(scale,display_level(high,levels).replace(",", ""))+oy))
        if yb >= top and ya <= bottom:
            fill = (31,95,191,36) if overlay.get("entry_colour") == "blue" else (25,140,110,35)
            draw.rectangle((left,max(top,round(ya)),right,min(bottom,round(yb))), fill=fill)
    markers.sort(key=lambda m:m["y"])
    label_y = [max(top,min(bottom-24,m["y"]-10)) for m in markers]
    for i in range(1,len(label_y)):
        label_y[i] = max(label_y[i],label_y[i-1]+26)
    if label_y and label_y[-1] > bottom-24:
        delta = label_y[-1]-(bottom-24)
        label_y = [p-delta for p in label_y]
    for marker, ly in zip(markers,label_y):
        color = colors[marker["label"]]
        if not marker["edge"]:
            draw.line((left,marker["y"],right,marker["y"]),fill=color,width=2 if marker["label"] == "Invalidation" else 1)
        else:
            tip = top if marker["edge"] == "above view" else bottom
            direction = 1 if marker["edge"] == "above view" else -1
            draw.polygon([(left,tip),(left-6,tip+direction*10),(left+6,tip+direction*10)],fill=color)
        text = marker["label"]+": "+display_level(marker["price"],levels)+(f" ({marker['edge']})" if marker["edge"] else "")
        font = _font("semibold",16)
        width = draw.textbbox((0,0),text,font=font)[2]+16
        tx = max(left+12,right-width-8)
        draw.rectangle((tx,ly,tx+width,ly+24),fill=(255,255,255,242))
        draw.text((tx+7,ly+2),text,font=font,fill=color)
    return markers


def apply(asset, row, *, require_verified=True):
    if require_verified and row["symbol"] not in VERIFIED_MARKETS:
        return asset
    scale = asset["tradingview_snapshot"].get("chart_geometry")
    if not scale or scale.get("policy") != POLICY or scale["source_sha256"] != asset["tradingview_snapshot"]["sha256"]:
        raise ValueError("TRADINGVIEW_PRICE_SCALE_NOT_CAPTURED_OR_BOUND")
    result = deepcopy(asset)
    overlay = {"policy": POLICY, "scale": scale, "source": source_binding(row), "entry_colour": "blue"}
    if asset["tradingview_snapshot"].get("price_scale_check"):
        from .publication_image_contract_v1 import validate_scale
        check = validate_scale(row["symbol"], asset["tradingview_snapshot"])
        if check.get("comparison_basis") == "NOT_COMPARED" and row["symbol"] == "USOIL":
            return asset   # the futures basis is unknown without a quote: the plain chart, levels stay in the text
        overlay["price_scale_check"] = check
        if check["level_offset"]:
            delta = check["level_offset"]
            when = "at last close" if check.get("comparison_basis") == "LAST_CLOSE" else "at capture"
            overlay["basis_label"] = ("WTI futures = plan feed " + ("+" if delta >= 0 else "-")
                + f" {abs(delta):.3f} USD/bbl {when}")
    source = Path(asset["path"])
    with Image.open(source) as image:
        image = image.convert("RGB")
        overlay["markers"] = _draw(image,overlay,asset["tradingview_snapshot"]["framing"]["original_box"][:2])
        if not overlay["markers"] or any(m["error_px"] > 2 for m in overlay["markers"]):
            raise ValueError("TRADINGVIEW_OVERLAY_LEVEL_PIXEL_CHECK_FAILED")
        # Recorded from what was drawn; validate() below redraws, compares and refuses a target.
        overlay["target_drawn"] = any(m["label"] == "Target" for m in overlay["markers"])
        target = source.with_name(source.stem+"-levels-"+_hash(overlay)[:16]+".png")
        image.save(target,format="PNG")
    result.update(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  asset_id="tradingview-plan-"+_hash(overlay)[:20],plan_overlay=overlay,
                  caption=asset["caption"]+" Plan levels: Capital Chronicle.")
    validate(result)
    return result


def validate(asset, row=None):
    overlay = asset["plan_overlay"]
    snap = asset["tradingview_snapshot"]
    if target_drawn(asset):
        # Decision 82: an image whose overlay drew a target is never published.
        raise ValueError("TRADINGVIEW_OVERLAY_TARGET_DRAWN")
    if (overlay["policy"] != POLICY or overlay["scale"] != snap.get("chart_geometry")
            or overlay["scale"]["source_sha256"] != snap["sha256"]
            or (row and _hash(_drawn_binding(overlay["source"])) != _hash(source_binding(row)))):
        raise ValueError("TRADINGVIEW_OVERLAY_SOURCE_OR_SCALE_CHANGED")
    if overlay.get("price_scale_check") != snap.get("price_scale_check"):
        raise ValueError("TRADINGVIEW_OVERLAY_PRICE_BASIS_CHANGED")
    with Image.open(snap["path"]) as raw, Image.open(asset["path"]) as actual:
        expected = Image.new("RGB", (asset["width"],asset["height"]),"white")
        box = snap["framing"]["original_box"]
        expected.paste(raw.convert("RGB"),box[:2])
        markers = _draw(expected,overlay,box[:2])
        if markers != overlay["markers"] or ImageChops.difference(expected,actual.convert("RGB")).getbbox():
            raise ValueError("TRADINGVIEW_OVERLAY_PIXELS_OR_PROTECTED_ATTRIBUTION_CHANGED")
