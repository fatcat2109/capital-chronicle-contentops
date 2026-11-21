"""CC-681 chart evidence on the existing per-destination readback."""
from collections.abc import Mapping
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re
from urllib.parse import parse_qs, urlsplit

import requests


ROUTES = frozenset({"discord", "facebook_page", "instagram_business", "linkedin", "linkedin_company",
                    "threads", "telegram", "x", "substack", "substack_notes", "youtube"})
API_IMAGE_ROUTES = frozenset({"discord", "facebook_page", "instagram_business", "threads"})
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
TELEGRAM_FEED = "https://t.me/s/CapitalChronicle"


def selected_charts(intent, destination):
    payload = intent.get("native_payload") or {}
    if not isinstance(payload, Mapping):
        return []
    ids = set(payload.get("media_asset_ids") or [])
    ids.update(asset_id for post in payload.get("posts") or [] if isinstance(post, Mapping)
               for asset_id in post.get("media_asset_ids") or [])
    if destination != "substack" and not ids:
        return []
    assets = intent.get("media_assets")
    if not assets and intent.get("output_dir"):
        try:
            context = json.loads((Path(intent["output_dir"]) / "run_context_v1.json").read_bytes())
            assets = (context.get("media") or {}).get("assets")
        except (OSError, ValueError):
            return []
    return [a for a in assets or [] if isinstance(a, Mapping) and a.get("asset_id")
            and a.get("modality") == "tradingview_chart_snapshot"
            and SHA256.fullmatch(str(a.get("sha256") or ""))
            and (a.get("asset_id") in ids if destination != "substack" else
                 not a.get("derivative_only") and a.get("article_inclusion") is not False
                 and a.get("canonical_article_media") is not False)]


def chart_symbol(asset):
    snapshot = asset.get("tradingview_snapshot") or {}
    symbol = snapshot.get("tv_symbol")
    if not symbol:
        try:
            source = urlsplit(asset.get("source_page_url")
                              or (asset.get("source_provenance") or {}).get("source_page_url")
                              or snapshot.get("chart_url") or "")
        except ValueError:
            return None
        if source.hostname in {"tradingview.com", "www.tradingview.com"}:
            symbol = next(iter(parse_qs(source.query).get("symbol", [])), "")
    return symbol if re.fullmatch(r"[A-Z0-9_]+:[A-Z0-9_.!-]+", str(symbol or "")) else None


def _telegram_images(html, object_id, *, include_link_preview=False):
    """Use the exact message's photo or its explicitly requested chart preview."""
    from .day_readback_v1 import _HTML

    post_id = f"capitalchronicle/{object_id}"
    tree = _HTML(html).root
    messages = [node for node in tree.walk() if node.attrs.get("data-post", "").casefold() == post_id]
    if len(messages) != 1:
        return None

    def own_images(node):
        classes = set(node.attrs.get("class", "").split())
        if node.hidden() or classes & {"tgme_widget_message_reply", "tgme_widget_message_forwarded_from"}:
            return
        if classes & {"tgme_widget_message_photo_wrap", "link_preview_image"}:
            image = re.search(r"background-image\s*:\s*url\(\s*['\"]?(https://[^'\"\s)]+)",
                              node.attrs.get("style", ""))
            yield ("link_preview_image" in classes, image[1] if image else None)
        for child in node.children:
            if not isinstance(child, str):
                yield from own_images(child)

    images = list(own_images(messages[0]))
    urls = [url for preview, url in images if not preview]
    if not urls and include_link_preview:
        urls = [url for preview, url in images if preview]
    return urls if all(urls) else None


def read_telegram_images(object_id, *, include_link_preview=False):
    """Read the exact ID on the one unsigned public Telegram channel feed."""
    if not re.fullmatch(r"\d{1,20}", str(object_id or "")):
        return None
    try:
        with requests.get(TELEGRAM_FEED, params={"after": int(object_id) - 1},
                          timeout=(3, 8), allow_redirects=False, stream=True) as response:
            if response.status_code != 200:
                return None
            data = bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data) > 2 * 1024 * 1024:
                    return None
            return _telegram_images(data.decode("utf-8", errors="replace"), object_id,
                                    include_link_preview=include_link_preview)
    except (OSError, ValueError, requests.RequestException):
        return None


def _asset_comparisons(digest, comparisons, urls, public_url):
    return [item for item in comparisons
            if (item.get("local_source_asset_sha256") or item.get("source_asset_sha256")) == digest
            and item.get("pixels_inspected") is True
            and item.get("public_object_url") == public_url
            and (urls is None or (item.get("observed_image_url") or item.get("public_image_url")) in urls)
            and SHA256.fullmatch(str(item.get("platform_sha256") or ""))]


def _asset_check(asset, comparisons, hashes, urls, public_url):
    digest = asset["sha256"]
    checked = _asset_comparisons(digest, comparisons, urls, public_url)
    if digest in hashes or any(item.get("source_pixels_match") is True for item in checked):
        status = "MATCH"
    elif urls == [] and not checked:
        status = "MISSING"
    elif urls and set(urls) <= {item.get("observed_image_url") or item.get("public_image_url")
                                for item in checked if item.get("source_pixels_match") is False}:
        status = "MISMATCH"
    else:
        status = "UNVERIFIED"
    return {"asset_id": asset["asset_id"], "expected_sha256": digest, "tradingview_symbol": chart_symbol(asset),
            "status": status, "observed_sha256": sorted(set(hashes) | {item["platform_sha256"] for item in checked})}


def observe(destination, intent, result, *, object_id=None, public_url=None):
    """Compare the frozen upload to the exact observed object's own image list."""
    if destination not in ROUTES or result.get("write_absent") is True:
        return None
    charts = selected_charts(intent, destination)
    if not charts:
        return None
    observed_id = next((str(result[key]) for key in ("public_object_id", "post_id", "media_id", "message_id",
                                                     "id", "activity_id", "root_post_id")
                        if result.get(key)), None)
    if not observed_id or (object_id and observed_id != str(object_id)):
        return None
    observed_url = result.get("public_object_url") or result.get("public_url")
    public_url = public_url or observed_url
    if public_url and observed_url and public_url.rstrip("/") != observed_url.rstrip("/"):
        return None

    urls = None
    hashes = []
    comparisons = []
    if destination in API_IMAGE_ROUTES:
        # These lists are emitted by the adapter only for the exact account object.
        urls = result.get("observed_image_urls")
        digest = result.get("observed_image_sha256")
        if SHA256.fullmatch(str(digest or "")):
            hashes = [digest]
    elif destination == "telegram":
        payload = intent.get("native_payload") or {}
        urls = read_telegram_images(observed_id,
                                    include_link_preview=bool(payload.get("telegram_text_with_card_preview")))
    elif result.get("verified") is True or result.get("write_exists") is True:
        urls = result.get("public_image_urls")
        if result.get("missing_required_media_observed") is True and not urls:
            urls = []
        comparisons = result.get("media_comparisons") or []
        hashes = [value for value in result.get("observed_media_sha256") or []
                  if SHA256.fullmatch(str(value))]

    # Retain current browser evidence. Compare the frozen original for any
    # asset whose pixels or exact bytes were not checked by that route.
    unchecked = [asset for asset in charts if asset["sha256"] not in hashes
                 and not _asset_comparisons(asset["sha256"], comparisons, urls, public_url)]
    if urls and unchecked:
        from .neo_endpoint_executor_v1 import compare_public_images

        request = {"destination": destination, "content_binding": {"media_manifest": unchecked}}
        measured = compare_public_images(request, {"public_image_urls": urls, "public_object_url": public_url})
        comparisons = [*comparisons, *measured["media_comparisons"]]
        hashes = sorted(set(hashes) | set(measured["observed_media_sha256"]))
    checks = []
    slots = result.get("observed_image_slots")
    carousel = (intent.get("native_payload") or {}).get("carousel_images") or []
    ordered_ids = [entry.get("asset_id") for entry in carousel] or [asset["asset_id"] for asset in charts]
    for asset in charts:
        if slots is not None and asset["asset_id"] in ordered_ids:
            index = ordered_ids.index(asset["asset_id"])
            slot = slots[index] if index < len(slots) else None
            candidates = None if slot is None else [slot] if slot else []
            scoped_comparisons = comparisons if candidates is not None else []
            checks.append(_asset_check(asset, scoped_comparisons, [], candidates, public_url))
        else:
            checks.append(_asset_check(asset, comparisons, hashes, urls, public_url))
    return {"public_object_id": observed_id, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "assets": checks}


def report_copy(copy, runtime, market, expected_symbol):
    """Project saved evidence onto the copy and prepare at most one reply for its object."""
    from .public_decision_checks_v1 import clock

    if copy.platform not in ROUTES:
        return None, None
    folder = copy.intent.get("output_dir")
    if folder and not Path(folder).resolve().is_relative_to(runtime):
        return None, None
    assets = selected_charts(copy.intent, copy.platform)
    object_id = str(copy.row.get("public_object_id") or "")
    if not assets or not object_id:
        return None, None

    observed_at = None
    proof = {}
    for read_at, record in reversed(copy.history):
        seen = clock(read_at)
        if not seen or seen > copy.end or record.get("action"):
            continue
        current = record.get("readback", record)
        chart = current.get("posted_chart_readback") or {}
        if chart.get("public_object_id") == object_id and current.get("identity_match") is True:
            stamped = clock(chart.get("observed_at_utc")) or seen
            if stamped > copy.end:
                continue
            for asset in chart.get("assets") or []:
                if asset.get("status") in {"MATCH", "MISSING", "MISMATCH"}:
                    key = (asset.get("asset_id"), asset.get("expected_sha256"))
                    if key not in proof:
                        proof[key] = asset
                        observed_at = max(observed_at, stamped) if observed_at else stamped

    checked = []
    for asset in assets:
        received = proof.get((asset["asset_id"], asset["sha256"]), {})
        symbol = chart_symbol(asset)
        status = received.get("status")
        if status not in {"MATCH", "MISSING", "MISMATCH"}:
            status = "UNVERIFIED"
        checked.append({"asset_id": asset["asset_id"], "expected_sha256": asset["sha256"],
                        "tradingview_symbol": symbol or "", "status": status,
                        "observed_sha256": [h for h in received.get("observed_sha256") or []
                                            if isinstance(h, str) and SHA256.fullmatch(h)]})

    statuses = {asset["status"] for asset in checked}
    symbols = {asset["tradingview_symbol"] for asset in checked if asset["tradingview_symbol"]}
    symbol_mismatch = expected_symbol and symbols and expected_symbol not in symbols
    if symbol_mismatch:
        status, cause = "MISMATCH", "MARKET_TRADINGVIEW_SYMBOL_MISMATCH"
    elif "MISMATCH" in statuses:
        status, cause = "MISMATCH", "POSTED_CHART_MISMATCH"
    elif "MISSING" in statuses:
        status, cause = "MISSING", "POSTED_CHART_MISSING"
    elif "UNVERIFIED" in statuses:
        status, cause = "UNVERIFIED", "POSTED_CHART_READBACK_UNAVAILABLE"
    elif expected_symbol and not symbols:
        status, cause = "UNVERIFIED", "MARKET_TRADINGVIEW_SYMBOL_UNVERIFIED"
    else:
        status, cause = "MATCH", None
    check = {"piece_id": copy.piece, "platform": copy.platform, "public_url": copy.url, "public_object_id": object_id,
             "status": status, "first_cause": cause, "market": market, "expected_symbol": expected_symbol,
             "observed_at_utc": observed_at.isoformat() if observed_at else None, "assets": checked}
    repair_assets = [asset for asset, evidence in zip(assets, checked) if evidence["status"] in {"MISMATCH", "MISSING"}
                     and evidence["tradingview_symbol"] and (not expected_symbol or evidence["tradingview_symbol"] == expected_symbol)]
    if not repair_assets or status not in {"MISSING", "MISMATCH"}:
        return check, None

    media = []
    for asset in repair_assets:
        try:
            path = Path(asset.get("path") or asset.get("absolute_local_source_path") or "").resolve()
            if path.is_relative_to(runtime) and sha256(path.read_bytes()).hexdigest() == asset["sha256"]:
                media.append({"asset_id": asset["asset_id"], "sha256": asset["sha256"],
                              "path": str(path), "tradingview_symbol": chart_symbol(asset)})
        except OSError:
            continue
    if not media:
        check["correction_cause"] = "BOUND_CHART_BYTES_UNAVAILABLE"
        return check, None

    from .plan_status_posts_v1 import PUBLIC_NOTICE

    key = sha256(f"{copy.platform}:{object_id}".encode()).hexdigest()[:24]
    reply = {"correction_id": "cc681-chart-" + key, "owner": "Codex Publisher", "piece_id": copy.piece,
             "platform": copy.platform, "reply_to_id": object_id, "reply_to_url": copy.url,
             "text": "Correction: Here is the TradingView chart for our earlier post.\n\n" + PUBLIC_NOTICE,
             "media_assets": media}
    return check, reply
