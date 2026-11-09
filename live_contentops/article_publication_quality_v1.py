"""Decision 93 at the existing article preparation and coordinator boundaries."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from time import monotonic

from live_contentops.article_scenarios_v1 import validate_article_scenarios, validate_social_scenarios
from live_contentops.published_images_v1 import ImagePolicyError, PublishedImages

POLICY = "JIM_DECISION_93"
EFFECTIVE_FROM = datetime(2026, 11, 6, 13, 55, tzinfo=timezone.utc)
SNAPSHOT_MAX_AGE = timedelta(minutes=15)


def piece_id(store, intent):
    return sha256((str(Path(store.db_path).resolve()) + "#" + str(intent["work_item_id"])).encode()).hexdigest()


def image_register(coordinator):
    feed = coordinator.published_content_path
    root = feed.parent if feed is not None else Path(coordinator.store.db_path).parent
    return PublishedImages(root / "published_images_v1.jsonl", published_feed=feed)


def applies(coordinator, intent):
    # The production store and every explicit publication-feed consumer enforce
    # the rule. Offline fixture stores have no publication feed or public grant.
    return (coordinator.published_content_path is not None
            and coordinator._clock() >= EFFECTIVE_FROM
            and not intent.get("plan_status_post") and not intent.get("daily_digest"))


def article_inputs(intent):
    path = Path(str(intent.get("output_dir") or "")) / "run_context_v1.json"
    if path.is_file():
        context = json.loads(path.read_bytes())
        media = context.get("media") or {}
        article = {**(context.get("article") or {}), **(intent.get("reader_presentation_article") or {})}
        assets = intent.get("media_assets") if intent.get("reader_presentation_review") else media.get("assets")
        return article, list(assets or []), context.get("source_documents") or []
    return intent.get("article") or {}, intent.get("media_assets") or [], intent.get("source_documents") or []


def validate_snapshot_asset(asset, *, market=None, now=None):
    """Validate the original download and its uncropped padding, never chart data."""
    from PIL import Image, ImageChops
    from live_contentops import tradingview_snapshot_v1 as tv
    snapshot = asset.get("tradingview_snapshot") or {}
    market = market or snapshot.get("market") or next((key for key, symbol in tv.SYMBOLS.items()
                                                      if symbol == snapshot.get("tv_symbol")), None)
    original, framed = Path(str(snapshot.get("path") or "")), Path(str(asset.get("path") or ""))
    if (asset.get("modality") != "tradingview_chart_snapshot" or market not in tv.SYMBOLS
            or snapshot.get("tv_symbol") != tv.SYMBOLS[market] or asset.get("credit") != tv.CREDIT
            or asset.get("rights_basis") != tv.RIGHTS_BASIS or snapshot.get("policy") != tv.POLICY
            or snapshot.get("interval") not in tv.INTERVAL_LABELS
            or snapshot.get("chart_url") != tv.chart_url(tv.SYMBOLS[market], snapshot.get("interval"))
            or asset.get("source_page_url") != snapshot.get("chart_url")
            or tv.CREDIT not in str(asset.get("caption") or "")
            or snapshot.get("target_drawn") is not False or snapshot.get("levels_drawn") != []
            or not original.is_file() or not framed.is_file()
            or sha256(original.read_bytes()).hexdigest() != snapshot.get("sha256")
            or sha256(framed.read_bytes()).hexdigest() != asset.get("sha256")):
        raise ImagePolicyError("TRADINGVIEW_SNAPSHOT_BINDING_INVALID")
    box = (snapshot.get("framing") or {}).get("original_box")
    with Image.open(original) as source, Image.open(framed) as image:
        if (not isinstance(box, list) or len(box) != 4 or
                (box[2] - box[0], box[3] - box[1]) != source.size or
                box[0] < 0 or box[1] < 0 or box[2] > image.width or box[3] > image.height or
                ImageChops.difference(source.convert("RGB"), image.crop(box).convert("RGB")).getbbox()):
            raise ImagePolicyError("TRADINGVIEW_ATTRIBUTION_CROPPED")
    if now is not None:
        try:
            captured = datetime.fromisoformat(snapshot["captured_at_utc"].replace("Z", "+00:00"))
            valid = captured.tzinfo is not None and timedelta(0) <= now - captured <= SNAPSHOT_MAX_AGE
        except (KeyError, ValueError, TypeError):
            valid = False
        if not valid:
            raise ImagePolicyError("TRADINGVIEW_SNAPSHOT_STALE")


def prepare_market_snapshot(article, assets, *, output_dir, now=None, capture=None):
    """Wire CC-316 before review/registration, so media identities freeze once."""
    from live_contentops import tradingview_snapshot_v1 as tv
    market = article.get("market_asset")
    if market not in tv.SYMBOLS:
        return article, assets
    started = monotonic()
    now = now or datetime.now(timezone.utc)
    snapshots = [a for a in assets if a.get("modality") == "tradingview_chart_snapshot"]
    if snapshots:
        try:
            for asset in snapshots:
                validate_snapshot_asset(asset, market=market, now=now)
        except ImagePolicyError as exc:
            if str(exc) != "TRADINGVIEW_SNAPSHOT_STALE":
                raise
            snapshots = []  # a new file/revision, never overwrite the old source
    if snapshots:
        snapshot_asset = {**snapshots[0], "article_inclusion": True, "canonical_article_media": True,
                          "placement_after": "introduction"}
    else:
        interval = tv.interval_for(article.get("valid_until_utc"), now)
        snapshot = (capture or tv.capture)(market, interval, Path(output_dir))
        snapshot_asset = tv.snapshot_asset(snapshot=snapshot, market=market, title=article["title"], out_dir=Path(output_dir))
        snapshot_asset.update(article_inclusion=True, canonical_article_media=True, placement_after="introduction")
        # Capture completes after the preparation clock. Validate against that
        # elapsed clock, so a just-downloaded image is not labelled future/stale.
        validate_snapshot_asset(snapshot_asset, market=market,
            now=now + timedelta(seconds=monotonic() - started))
    event = article.get("article_type") in {"EVENT_PREVIEW", "EVENT_REVIEW"} or article.get("release_analysis") is True
    other = [a for a in assets if a.get("modality") != "tradingview_chart_snapshot"]
    ordered = [*other, snapshot_asset] if event else [snapshot_asset, *other]
    article = {**article, "lead_image_asset_id": ordered[0]["asset_id"], "publication_quality_policy": POLICY}
    choices = article.get("post_visual_destination_media") or article.get("native_destination_media") or {}
    if choices:
        available = {a["asset_id"] for a in ordered}
        choices = {d: list(dict.fromkeys(([ordered[0]["asset_id"], snapshot_asset["asset_id"]]
                    if event else [snapshot_asset["asset_id"]]) + [i for i in ids if i in available]))[:5]
                   for d, ids in choices.items()}
        article.update(post_visual_destination_media=choices, native_destination_media=choices)
    return article, ordered


def before_article_write(coordinator, intent, destination):
    if not applies(coordinator, intent):
        return None
    article, assets, documents = article_inputs(intent)
    from live_contentops.public_instruments_v1 import validate_article, validate_payload
    validate_article(article)
    for asset in assets:
        validate_payload(article, asset)
    assets = [a for a in assets if a.get("article_inclusion") is not False
              and a.get("canonical_article_media") is not False]
    if not assets:
        raise ImagePolicyError("IMAGE_MISSING")
    lead = article.get("lead_image_asset_id") or assets[0]["asset_id"]
    if lead not in {a.get("asset_id") for a in assets}:
        raise ImagePolicyError("IMAGE_MISSING")
    market = article.get("market_asset")
    event = (article.get("article_type") in {"EVENT_PREVIEW", "EVENT_REVIEW"}
             or article.get("release_analysis") is True or any(
                 (d.get("source_reuse_constraints") or {}).get("article_types") in
                 (["EVENT_PREVIEW"], ["EVENT_REVIEW"]) for d in documents))
    required_market = event or article.get("six_market_piece") is True or str(intent["work_item_id"]).startswith(("cc124-", "cc107-"))
    if required_market and not market:
        raise ImagePolicyError("TRADINGVIEW_SNAPSHOT_MARKET_REQUIRED")
    if market:
        from live_contentops.tradingview_snapshot_v1 import SYMBOLS
        if market not in SYMBOLS:
            raise ImagePolicyError("TRADINGVIEW_SNAPSHOT_MARKET_REQUIRED")
        snapshots = [a for a in assets if a.get("modality") == "tradingview_chart_snapshot"]
        if not snapshots:
            raise ImagePolicyError("TRADINGVIEW_SNAPSHOT_REQUIRED")
        if not event and snapshots[0]["asset_id"] != lead:
            raise ImagePolicyError("TRADINGVIEW_LEAD_REQUIRED")
        if event and next(a for a in assets if a["asset_id"] == lead).get("modality") not in {
                "source_bound_data_card", "source_backed_chart"}:
            raise ImagePolicyError("RELEASE_CARD_LEAD_REQUIRED")
        validate_snapshot_asset(snapshots[0], market=market, now=coordinator._clock() if destination == "substack" else None)
    validate_article_scenarios(article, documents)
    if destination != "substack":
        payload = intent.get("native_payload")
        if payload is None:
            from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
            payload = _durable_intent_inputs(intent)["payloads"][destination]
        validate_social_scenarios(article, payload)
        validate_payload(article, payload)
        if market:
            from live_contentops.article_scenarios_v1 import payload_text
            from live_contentops.tradingview_snapshot_v1 import CREDIT
            if CREDIT not in payload_text(payload):
                raise ImagePolicyError("TRADINGVIEW_ATTRIBUTION_REQUIRED")
    return image_register(coordinator).reserve(piece_id=piece_id(coordinator.store, intent), assets=assets,
        lead_asset_id=lead, now=coordinator._clock(), canonical_url=intent.get("canonical_url"),
        enforce_cap=destination == "substack")


def settle_article_images(coordinator, intent, *, destination, status, canonical_url=None, published_at_utc=None):
    if not applies(coordinator, intent) or destination != "substack":
        return
    state = ("PUBLISHED" if status in {"RECONCILED_CONFIRMED", "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"}
             else "ABSENT" if status in {"DEFINITE_NO_WRITE", "RECONCILED_ABSENT_SAFE_TO_RETRY"} else None)
    if state:
        image_register(coordinator).settle(piece_id(coordinator.store, intent), state=state,
            canonical_url=canonical_url, now=coordinator._clock(), published_at_utc=published_at_utc)


def observe_published_images(coordinator, intent, dispatch, *, observed_url, published_at_utc=None):
    """Register delivered status/digest images too, without changing their contracts."""
    if coordinator.published_content_path is None or coordinator._clock() < EFFECTIVE_FROM:
        return
    _, assets, _ = article_inputs(intent)
    payload = intent.get("native_payload") or {}
    selected = list(payload.get("media_asset_ids") or []) if isinstance(payload, dict) else []
    if isinstance(payload, dict):
        selected += [i for p in payload.get("posts") or [] if isinstance(p, dict) for i in p.get("media_asset_ids") or []]
    if dispatch["platform"] != "substack" and selected:
        assets = [a for a in assets if a.get("asset_id") in selected]
    if not assets:
        return
    # The canonical reservation already binds its fingerprints and uncertain
    # clock interval. Extra observations must not erase that clock distinction.
    if dispatch["platform"] == "substack" and applies(coordinator, intent):
        return
    image_register(coordinator).seed(piece_id=piece_id(coordinator.store, intent),
        canonical_url=observed_url if dispatch["platform"] == "substack" else intent.get("canonical_url"),
        images=[{"asset_id": a["asset_id"], "path": a.get("path") or a.get("absolute_local_source_path")} for a in assets],
        published_at=published_at_utc or dispatch["dispatched_at"], observation_ref="coordinator:" + dispatch["dispatch_id"],
        counts_as_article=False, clock_basis="OBSERVED_PUBLICATION_CLOCK" if published_at_utc else "RETAINED_COORDINATOR_DISPATCH_CLOCK")
