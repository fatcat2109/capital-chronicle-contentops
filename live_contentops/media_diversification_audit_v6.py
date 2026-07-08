"""Manifest-level media diversification, provenance, and rights audit for V6.

Single-image content audits answer whether one candidate is stale or misleading.
This audit answers the product question: does the whole article visual package
have enough variety, source provenance, and rights discipline to publish without
pretending that a downloaded image is automatically editorial-grade?
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any

from live_contentops.media_content_audit_v6 import audit_media_candidate

SCHEMA_VERSION = "media_diversification_audit_v6.0"

MEDIA_CLASSES = {
    "data_chart",
    "official_photo",
    "news_context_image",
    "map_or_geography",
    "public_domain_or_commons",
    "operator_review_required",
}

CONTEXTUAL_CLASSES = {
    "official_photo",
    "news_context_image",
    "map_or_geography",
    "public_domain_or_commons",
}

SEARCH_METHOD_MARKERS = ("google", "image_search", "search", "public_fallback", "commons", "wikimedia")


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _host(url: str | None) -> str:
    try:
        return urllib.parse.urlparse(str(url or "")).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _media_assets(media_manifest_or_assets: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(media_manifest_or_assets, list):
        raw_assets = media_manifest_or_assets
    elif isinstance(media_manifest_or_assets, dict):
        raw_assets = media_manifest_or_assets.get("media_assets") if isinstance(media_manifest_or_assets.get("media_assets"), list) else []
    else:
        raw_assets = []
    return [dict(asset) for asset in raw_assets if isinstance(asset, dict)]


def _asset_class(asset: dict[str, Any]) -> str:
    explicit = str(asset.get("media_class") or asset.get("class") or "").strip()
    if explicit in MEDIA_CLASSES:
        return explicit
    text = " ".join(
        str(asset.get(key) or "")
        for key in ("visual_metric", "media_subject", "source_label", "canonical_source_label", "asset_id")
    ).lower()
    if any(term in text for term in ("map", "hormuz", "chokepoint", "geography")):
        return "map_or_geography"
    if any(term in text for term in ("chart", "series", "fred", "eia", "wti", "volatility", "price path")):
        return "data_chart"
    if "commons" in text or "public domain" in text:
        return "public_domain_or_commons"
    return "operator_review_required"


def _is_search_like(asset: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(asset.get(key) or "")
        for key in ("retrieval_method", "source_label", "canonical_source_label", "url", "source_url", "source_page_url", "query")
    ).lower()
    return any(marker in haystack for marker in SEARCH_METHOD_MARKERS)


def _source_url(asset: dict[str, Any]) -> str:
    return str(asset.get("source_page_url") or asset.get("source_url") or asset.get("url") or "").strip()


def _image_url(asset: dict[str, Any]) -> str:
    return str(asset.get("image_url") or asset.get("public_url") or asset.get("url") or "").strip()


def _rights_status(asset: dict[str, Any]) -> str:
    return str(asset.get("rights_status") or asset.get("rights_provenance_status") or asset.get("provenance_status") or "").strip().lower()


def _is_rights_safe(asset: dict[str, Any]) -> bool:
    if bool(asset.get("operator_review_required")):
        return False
    status = _rights_status(asset)
    return any(
        marker in status
        for marker in (
            "public_domain",
            "cc_owned",
            "source_backed_generated",
            "official_public",
            "creative_commons",
            "auto_publication_safe",
        )
    )


def _provenance_missing(asset: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not _source_url(asset):
        missing.append("source_page_url")
    if not str(asset.get("source_label") or asset.get("canonical_source_label") or "").strip():
        missing.append("source_label")
    if not _rights_status(asset):
        missing.append("rights_status")
    if not str(asset.get("provenance_status") or asset.get("canonical_source_label") or "").strip():
        missing.append("provenance_status")
    if not str(asset.get("why_selected") or "").strip():
        missing.append("why_selected")
    return missing


def _search_metadata_missing(asset: dict[str, Any]) -> list[str]:
    if not _is_search_like(asset):
        return []
    checks = {
        "query": asset.get("query"),
        "recency_or_time_filter": asset.get("recency_days") or asset.get("time_filter") or asset.get("tbs"),
        "source_page_url": _source_url(asset),
        "image_url": _image_url(asset),
        "source_domain": asset.get("source_domain") or _host(_source_url(asset) or _image_url(asset)),
        "retrieval_timestamp": asset.get("retrieval_timestamp"),
        "rights_status": _rights_status(asset),
        "why_selected": asset.get("why_selected"),
    }
    return [name for name, value in checks.items() if not str(value or "").strip()]


def _asset_token_relevance(asset: dict[str, Any], topic_text: str) -> bool:
    words = {tok for tok in re.findall(r"[a-z0-9]+", topic_text.lower()) if len(tok) > 3}
    asset_words = {
        tok
        for tok in re.findall(
            r"[a-z0-9]+",
            " ".join(str(asset.get(key) or "") for key in ("query", "visual_metric", "media_subject", "caption", "why_selected", "source_url")).lower(),
        )
        if len(tok) > 3
    }
    if not words:
        return True
    return bool(words & asset_words)


def audit_media_manifest(
    media_manifest_or_assets: dict[str, Any] | list[dict[str, Any]],
    *,
    article_title: str,
    article_text: str = "",
    expected_min_assets: int = 3,
    allow_two_asset_reason: str | None = None,
    as_of_date: str | None = None,
) -> dict[str, Any]:
    assets = _media_assets(media_manifest_or_assets)
    blockers: list[str] = []
    review_items: list[str] = []
    replacement_notes: list[str] = []
    audited_assets: list[dict[str, Any]] = []

    min_assets = 2 if allow_two_asset_reason else expected_min_assets
    if len(assets) < min_assets:
        blockers.append(f"media_asset_count_too_low:{len(assets)}<{min_assets}")
    if len(assets) == 2 and allow_two_asset_reason:
        review_items.append(f"two_asset_exception:{allow_two_asset_reason}")

    classes = [_asset_class(asset) for asset in assets]
    if "data_chart" not in classes:
        blockers.append("media_mix_missing_data_chart")
    if not (set(classes) & CONTEXTUAL_CLASSES):
        blockers.append("media_mix_missing_contextual_image_or_map")
    if len(assets) >= 3 and classes.count("data_chart") == len(classes):
        blockers.append("media_mix_repeated_chart_only")

    auto_publication_safe = True
    topic_text = f"{article_title} {article_text}"
    for idx, asset in enumerate(assets, start=1):
        asset_class = _asset_class(asset)
        source_url = _source_url(asset)
        image_url = _image_url(asset)
        provenance_missing = _provenance_missing(asset)
        search_missing = _search_metadata_missing(asset)
        rights_safe = _is_rights_safe(asset)
        if provenance_missing:
            blockers.append(f"media_provenance_missing:{asset.get('asset_id') or idx}:{','.join(provenance_missing)}")
        if search_missing:
            blockers.append(f"search_image_metadata_missing:{asset.get('asset_id') or idx}:{','.join(search_missing)}")
        if not rights_safe:
            auto_publication_safe = False
            review_items.append(f"media_rights_operator_review_required:{asset.get('asset_id') or idx}")
        if not _asset_token_relevance(asset, topic_text):
            review_items.append(f"media_semantic_relevance_weak:{asset.get('asset_id') or idx}")

        candidate_audit = None
        visual_metric = str(asset.get("visual_metric") or "").lower()
        is_primary_thesis_chart = str(asset.get("asset_id") or "").lower() == "primary" or "volatility" in visual_metric
        if asset_class == "data_chart" and is_primary_thesis_chart:
            candidate_audit = audit_media_candidate(
                article_title=article_title,
                article_text=article_text,
                image_path=asset.get("local_path"),
                public_image_url=asset.get("public_url") or asset.get("image_url"),
                source_metadata=asset,
                as_of_date=as_of_date,
            )
            if candidate_audit.get("audit_status") == "FAIL":
                blockers.append(
                    f"data_chart_content_audit_failed:{asset.get('asset_id') or idx}:"
                    + "|".join(candidate_audit.get("blockers") or ["unknown"])
                )
        if bool(asset.get("replacement_note")):
            replacement_notes.append(str(asset["replacement_note"]))
        audited_assets.append({
            "asset_id": asset.get("asset_id") or f"asset_{idx}",
            "media_class": asset_class,
            "source_label": asset.get("canonical_source_label") or asset.get("source_label"),
            "source_page_url": source_url,
            "image_url": image_url or None,
            "source_domain": asset.get("source_domain") or _host(source_url or image_url),
            "latest_observation_date": asset.get("latest_observation_date") or asset.get("time_coverage_end_date"),
            "latest_observation_year": asset.get("latest_observation_year") or asset.get("time_coverage_end_year"),
            "rights_status": asset.get("rights_status") or asset.get("rights_provenance_status"),
            "provenance_status": asset.get("provenance_status"),
            "operator_review_required": bool(asset.get("operator_review_required")) or not rights_safe,
            "why_selected": asset.get("why_selected"),
            "candidate_content_audit": candidate_audit,
        })

    status = "FAIL" if blockers else "PASS"
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_status": status,
        "auto_publication_safe": auto_publication_safe and status == "PASS",
        "asset_count": len(assets),
        "expected_min_assets": expected_min_assets,
        "minimum_allowed_assets": min_assets,
        "media_classes": classes,
        "blockers": list(dict.fromkeys(blockers)),
        "review_items": list(dict.fromkeys(review_items)),
        "replacement_notes": replacement_notes,
        "audited_assets": audited_assets,
        "retrieval_audit_timestamp": _utc_now(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit V6 media manifest diversification and rights.")
    parser.add_argument("manifest", help="Path to platform variant packet or media manifest JSON")
    parser.add_argument("--title", default="")
    parser.add_argument("--article-text", default="")
    parser.add_argument("--as-of-date", default=None)
    args = parser.parse_args(argv)
    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    manifest = data.get("media_manifest") if isinstance(data, dict) and isinstance(data.get("media_manifest"), dict) else data
    print(json.dumps(
        audit_media_manifest(
            manifest,
            article_title=args.title or str(data.get("title") or ""),
            article_text=args.article_text,
            as_of_date=args.as_of_date,
        ),
        indent=2,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
