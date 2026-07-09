"""V6 Live Platform Native Variant Generator with Threading & Image Search.

Reads the canonical article packet and generates tailored versions for LinkedIn,
Discord, Telegram, X (Twitter), and Threads. Supports threading for short-form
platforms and automatically downloads news hero images from Google.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from live_contentops.ai_research_canonical_article_engine_v6 import (
    call_live_provider,
    parse_llm_json,
)
from live_contentops.google_image_search_v6 import (
    execute_google_image_search_and_download,
)
from live_contentops.macro_chart_renderer_v6 import render_macro_chart
from live_contentops.media_content_audit_v6 import (
    _fed_funds_fixture_scope,
    _looks_like_fed_funds_topic,
    _looks_like_oil_topic,
    audit_media_candidate,
    build_current_macro_visual_pack,
)
from live_contentops.media_diversification_audit_v6 import audit_media_manifest

TASK_LABEL = "TASK_CONTENTOPS_V6_PLATFORM_NATIVE_VARIANT_GENERATOR_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_ARTICLE_PACKET = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS")
DEFAULT_PACKET_OUTPUT = DEFAULT_OUTPUT_DIR / "platform_variant_packet.json"
DEFAULT_DRY_RUN_MEDIA_FIXTURE_DIR = Path("docs/automation/V6_MEDIA_SYSTEM/downloads")


def _load_live_env_if_needed(enabled: bool) -> None:
    if enabled:
        load_dotenv()


def compute_packet_hash(data: dict[str, Any]) -> str:
    clone = dict(data)
    clone.pop("platform_variant_packet_id", None)
    clone.pop("exact_payload_hash", None)
    serialized = json.dumps(clone, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _contains_placeholder(text: str) -> bool:
    return any(marker in text.lower() for marker in ("stub", "scaffold", "placeholder", "lorem ipsum"))


def _contains_advice_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in (
        "you should buy",
        "you should sell",
        "buy now",
        "sell now",
        "guaranteed return",
        "risk-free return",
        "not financial advice but",
    ))


def _has_no_advice_context(text: str) -> bool:
    lowered = text.lower()
    return "not investment advice" in lowered or "without giving investment advice" in lowered or "educational" in lowered


def _ensure_no_advice_context(text: str) -> str:
    clean = text.strip()
    if _has_no_advice_context(clean):
        return clean
    return f"{clean}\n\nCapital Chronicle frames this as educational context, not investment advice."


def _generic_variant(text: str) -> bool:
    lowered = text.lower()
    return lowered.count("capital chronicle") == 0 and not any(term in lowered for term in ("macro", "policy", "shipping", "liquidity", "geopolitic", "yield", "data"))


def validate_platform_variants(variants: dict[str, str], variant_threads: dict[str, list[str]], live_run: bool = True) -> list[str]:
    required = {
        "substack": 1200,
        "linkedin": 120,
        "facebook": 120,
        "discord": 80,
        "telegram": 60,
        "threads": 80,
        "instagram_caption": 80,
    }
    failures: list[str] = []
    for platform, min_len in required.items():
        text = str(variants.get(platform, "")).strip()
        if len(text) < min_len:
            failures.append(f"{platform}_too_short:{len(text)}<{min_len}")
        if _contains_placeholder(text):
            failures.append(f"{platform}_placeholder_detected")
        if _contains_advice_phrase(text):
            failures.append(f"{platform}_financial_advice_phrase_detected")
        if platform in {"substack", "linkedin", "facebook", "instagram_caption"} and not _has_no_advice_context(text):
            failures.append(f"{platform}_no_advice_context_missing")
        if platform != "substack" and _generic_variant(text):
            failures.append(f"{platform}_generic_language_detected")
    limits = {"x": 280, "threads": 500}
    for platform in ("x", "threads"):
        thread = [str(item).strip() for item in variant_threads.get(platform, []) if str(item).strip()]
        if not thread:
            failures.append(f"{platform}_thread_missing")
        if any(_contains_placeholder(item) for item in thread):
            failures.append(f"{platform}_thread_placeholder_detected")
        if any(_contains_advice_phrase(item) for item in thread):
            failures.append(f"{platform}_thread_financial_advice_phrase_detected")
        for idx, item in enumerate(thread, start=1):
            if len(item) > limits[platform]:
                failures.append(f"{platform}_thread_item_too_long:{idx}:{len(item)}>{limits[platform]}")
    return failures


def _build_media_manifest(
    *,
    title: str,
    image_path: str | Path | None,
    public_image_url: str | None,
    source_metadata: dict[str, Any] | None = None,
    media_assets: list[dict[str, Any]] | None = None,
    media_audit: dict[str, Any] | None = None,
    source_csv: str | None = None,
) -> dict[str, Any]:
    chart = render_macro_chart(title, source_csv) if source_csv else {
        "chart_status": "BLOCKED",
        "warnings": ["chart_source_csv_missing"],
        "chart_path": None,
    }
    chart_ready = chart.get("chart_status") == "READY"
    assets = [dict(asset) for asset in (media_assets or []) if isinstance(asset, dict)]
    if not assets and (image_path or public_image_url):
        base_asset = dict(source_metadata or {})
        base_asset.setdefault("asset_id", "primary")
        if image_path:
            base_asset["local_path"] = str(image_path)
        if public_image_url:
            base_asset["public_url"] = public_image_url
        assets = [base_asset]
    news_ready = bool(image_path)
    public_ready = bool(public_image_url and image_path)
    instagram_image_url = _instagram_safe_image_url(public_image_url) if public_image_url else None
    selected = {
        "substack": str(image_path) if news_ready else None,
        "linkedin": str(image_path) if news_ready else None,
        "facebook": public_image_url if public_ready else None,
        "x": str(image_path) if news_ready else None,
        "threads": public_image_url if public_ready else None,
        "telegram": str(image_path) if news_ready else None,
        "discord": public_image_url if public_ready else None,
        "instagram": instagram_image_url if public_ready else None,
    }
    readiness = {
        "substack": news_ready,
        "linkedin": news_ready,
        "facebook": public_ready,
        "x": news_ready,
        "threads": public_ready,
        "telegram": news_ready,
        "discord": public_ready,
        "instagram": public_ready,
    }
    audit_blockers = list((media_audit or {}).get("blockers") or [])
    audit_warnings = list((media_audit or {}).get("warnings") or [])
    return {
        "primary_chart_path": chart.get("chart_path") if chart_ready else None,
        "primary_chart_public_url": None,
        "chart_metadata": chart,
        "news_image_path": str(image_path) if image_path else None,
        "news_image_public_url": public_image_url,
        "instagram_safe_image_public_url": instagram_image_url,
        "news_image_source_label": (source_metadata or {}).get("canonical_source_label") or (source_metadata or {}).get("source_label"),
        "news_image_source_query": (source_metadata or {}).get("query"),
        "news_image_source_url": (source_metadata or {}).get("source_url") or (source_metadata or {}).get("url"),
        "media_assets": assets,
        "media_content_audit": media_audit or {},
        "selected_media_by_platform": selected,
        "media_readiness_by_platform": readiness,
        "media_warnings": list(chart.get("warnings") or []) + audit_warnings + ([] if news_ready else ["news_image_missing"]),
        "media_blockers": audit_blockers,
        "rights_status": "sourceable_review_required" if news_ready and not audit_blockers else "not_ready",
    }


def summarize_validation(failures: list[str]) -> dict[str, Any]:
    blocked_platforms = sorted({failure.split("_", 1)[0] for failure in failures})
    return {
        "failure_count": len(failures),
        "blocked_platforms": blocked_platforms,
        "ready": not failures,
    }


def _render_source_trail(source_trail: list[dict[str, Any]]) -> str:
    if not source_trail:
        return ""
    lines = ["\n\n## Source trail"]
    for idx, item in enumerate(source_trail, start=1):
        label = item.get("label") or f"Source {idx}"
        origin = item.get("publisher_or_origin") or "source"
        claim = item.get("claim_supported") or "claim review required"
        lines.append(f"- {label} — {origin}: {claim}")
    return "\n".join(lines)


def _fallback_variants(title: str, subtitle: str, body_text: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    short = re.sub(r"\s+", " ", body_text).strip()
    summary = short[:900].rsplit(" ", 1)[0] if len(short) > 900 else short
    linkedin = f"{title}\n\n{subtitle}\n\n{summary}\n\nCapital Chronicle frames this as educational macro context, not investment advice."
    discord = f"**{title}**\n\n{summary[:1200]}\n\nDiscuss the data, assumptions, and transmission channels."
    telegram = f"Capital Chronicle: {title}\n\n{summary[:850]}"
    facebook = f"{title}\n\n{subtitle}\n\n{summary[:1600]}\n\nEducational macro analysis from Capital Chronicle."
    instagram_caption = f"{title}\n\n{summary[:1800]}\n\n#CapitalChronicle #Macro #Geopolitics"
    x_thread = []
    chunks = [summary[i:i + 230].strip() for i in range(0, min(len(summary), 1600), 230)]
    for idx, chunk in enumerate(chunks[:8], start=1):
        x_thread.append(f"{idx}/ {chunk}" if idx == 1 else f"{idx}/ {chunk}")
    threads_thread = [chunk for chunk in [summary[i:i + 450].strip() for i in range(0, min(len(summary), 2200), 450)] if chunk]
    return {
        "substack": body_text,
        "linkedin": linkedin,
        "facebook": facebook,
        "discord": discord,
        "telegram": telegram,
        "x": "\n\n---\n\n".join(x_thread),
        "threads": "\n\n---\n\n".join(threads_thread),
        "instagram_caption": instagram_caption,
    }, {"x": x_thread, "threads": threads_thread}


def _build_clean_image_query(title: str) -> str:
    # Strip common prefixes
    for prefix in ["Capital Chronicle Educational Briefing:", "Capital Chronicle Macro Volatility Briefing:", "Capital Chronicle:"]:
        if title.lower().startswith(prefix.lower()):
            title = title[len(prefix):].strip()
    # Remove non-alphanumeric chars except space and dash
    title = re.sub(r'[^a-zA-Z0-9\s-]', '', title).strip()
    title = re.sub(r"\bUS\b", "United States", title, flags=re.IGNORECASE)
    stopwords = {"as", "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "rise", "rises", "rising"}
    words = [word for word in title.split() if word.lower() not in stopwords]
    if len(words) > 9:
        words = words[:9]
    cleaned = " ".join(words)
    return f"{cleaned} macro financial chart news"


def _instagram_safe_image_url(public_image_url: str | None) -> str | None:
    """Return a square JPEG proxy URL for Instagram's strict aspect-ratio gate."""
    if not public_image_url:
        return None
    if "images.weserv.nl" in public_image_url:
        return public_image_url
    safe_source = urllib.parse.quote(public_image_url, safe=":/%._-~")
    return f"https://images.weserv.nl/?url={safe_source}&w=1080&h=1080&fit=contain&bg=white&output=jpg"


def _load_image_metadata(image_path: str | Path | None) -> dict[str, Any]:
    if not image_path:
        return {}
    meta_path = Path(image_path).with_suffix(".json")
    if not meta_path.exists():
        return {}
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _load_committed_macro_visual_pack(
    *,
    article_title: str,
    fixture_dir: str | Path = DEFAULT_DRY_RUN_MEDIA_FIXTURE_DIR,
) -> list[dict[str, Any]]:
    """Load committed source-backed visuals without fetching or rendering."""
    root = Path(fixture_dir)
    lowered = article_title.lower()
    if _looks_like_fed_funds_topic(lowered):
        fixture_scope_defaults = _fed_funds_fixture_scope()
        patterns = (
            ("primary", "fed_funds_policy_corridor_context_*.png"),
            ("policy_corridor", "fed_funds_policy_floor_context_*.png"),
            ("sofr_context", "fed_funds_sofr_context_*.png"),
        )
    elif _looks_like_oil_topic(lowered):
        fixture_scope_defaults = {}
        patterns = (
            ("primary", "wti_current_volatility_context_*.png"),
            ("recent_price", "wti_recent_price_context_*.png"),
            ("hormuz_context", "hormuz_oil_chokepoint_context_*.png"),
        )
    else:
        return []
    assets: list[dict[str, Any]] = []
    for asset_id, pattern in patterns:
        candidates = sorted(root.glob(pattern), key=lambda path: path.name, reverse=True)
        for path in candidates:
            meta_path = path.with_suffix(".json")
            if not meta_path.exists():
                continue
            try:
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if str(metadata.get("asset_id") or asset_id) != asset_id:
                continue
            if not str(metadata.get("rights_status") or "").strip():
                continue
            if not str(metadata.get("why_selected") or "").strip():
                continue
            metadata = dict(metadata)
            metadata.update({key: value for key, value in fixture_scope_defaults.items() if key not in metadata})
            metadata["asset_id"] = asset_id
            metadata["local_path"] = str(path)
            metadata["dry_run_fixture_asset"] = True
            metadata["retrieval_method"] = "committed_local_source_backed_fixture"
            metadata.setdefault("public_url", None)
            metadata.setdefault("image_url", None)
            assets.append(metadata)
            break
    return assets


def _asset_caption(asset: dict[str, Any], default_label: str = "Chart") -> str:
    caption = str(asset.get("caption") or "").strip()
    source_label = str(asset.get("canonical_source_label") or asset.get("source_label") or "").strip()
    if not caption:
        caption = f"{default_label} supporting the article's macro setup."
    if source_label and source_label.lower() not in caption.lower():
        caption = f"{caption.rstrip('.')}. Source: {source_label}."
    return re.sub(r"\s+\.", ".", caption)


def _visual_marker_block(asset: dict[str, Any], index: int) -> str:
    asset_id = str(asset.get("asset_id") or f"visual_{index + 1}").strip()
    label = "Chart" if "chart" in str(asset.get("visual_metric") or "").lower() else "Visual"
    return f"\n\n[[VISUAL:{asset_id}]]\n\n*{label}: {_asset_caption(asset, label)}*\n\n"


def _find_insert_positions(body: str, asset_count: int) -> list[int]:
    headings = list(re.finditer(r"(?m)^###\s+.+$", body))
    source_match = re.search(r"(?m)^##\s+Source trail\b", body)
    end_or_sources = source_match.start() if source_match else len(body)
    if not headings:
        return [min(len(body), end_or_sources)] * asset_count
    positions: list[int] = []
    for idx in range(asset_count):
        if idx == 0:
            positions.append(headings[0].start())
        elif idx == 1 and len(headings) >= 3:
            positions.append(headings[2].start())
        elif idx == 1 and len(headings) >= 2:
            positions.append(headings[1].start())
        else:
            positions.append(end_or_sources)
    return positions


def _normalise_section_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _heading_ranges(body: str) -> list[dict[str, Any]]:
    headings = list(re.finditer(r"(?m)^###\s+(.+)$", body))
    source_match = re.search(r"(?m)^##\s+Source trail\b", body)
    source_start = source_match.start() if source_match else len(body)
    ranges: list[dict[str, Any]] = []
    for idx, heading in enumerate(headings):
        next_start = headings[idx + 1].start() if idx + 1 < len(headings) else source_start
        ranges.append({
            "title": heading.group(1).strip(),
            "title_key": _normalise_section_key(heading.group(1)),
            "start": heading.start(),
            "end": min(next_start, source_start),
        })
    return ranges


def _slot_insert_position(body: str, placement_after_section: str | None) -> int | None:
    placement_key = _normalise_section_key(placement_after_section)
    headings = _heading_ranges(body)
    source_match = re.search(r"(?m)^##\s+Source trail\b", body)
    source_start = source_match.start() if source_match else len(body)
    if not placement_key:
        return None
    if placement_key == "intro":
        return headings[0]["start"] if headings else source_start
    for heading in headings:
        title_key = heading["title_key"]
        if placement_key == title_key or placement_key in title_key or title_key in placement_key:
            return heading["end"]
    return None


def _slot_ordered_assets_and_positions(
    body: str,
    assets: list[dict[str, Any]],
    visual_slots: list[dict[str, Any]] | None,
) -> list[tuple[int, dict[str, Any]]]:
    fallback_positions = _find_insert_positions(body, len(assets))
    if not visual_slots:
        return list(zip(fallback_positions, assets))

    slots_by_id = {
        str(slot.get("asset_id") or "").strip(): slot
        for slot in visual_slots
        if isinstance(slot, dict) and str(slot.get("asset_id") or "").strip()
    }
    positioned: list[tuple[int, dict[str, Any]]] = []
    for idx, asset in enumerate(assets):
        asset_id = str(asset.get("asset_id") or ("primary" if idx == 0 else f"visual_{idx + 1}")).strip()
        slot = slots_by_id.get(asset_id)
        position = None
        if slot:
            position = _slot_insert_position(body, str(slot.get("placement_after_section") or ""))
        if position is None:
            position = fallback_positions[min(idx, len(fallback_positions) - 1)]
        positioned.append((position, asset))
    return positioned


def _insert_substack_visual_markers(
    body: str,
    media_assets: list[dict[str, Any]],
    visual_slots: list[dict[str, Any]] | None = None,
) -> str:
    assets = [dict(asset) for asset in media_assets if isinstance(asset, dict) and (asset.get("local_path") or asset.get("public_url"))]
    if not assets:
        return body
    if re.search(r"\[\[VISUAL:[a-zA-Z0-9_-]+\]\]", body):
        return body
    if visual_slots:
        slot_ids = [str(slot.get("asset_id") or "").strip() for slot in visual_slots if isinstance(slot, dict)]
        ordered = []
        for slot_id in slot_ids:
            match = next((asset for asset in assets if str(asset.get("asset_id") or "") == slot_id), None)
            if match:
                ordered.append(match)
        ordered.extend(asset for asset in assets if asset not in ordered)
        assets = ordered
    updated = body
    positioned_assets = _slot_ordered_assets_and_positions(body, assets, visual_slots)
    for idx, (position, asset) in enumerate(sorted(positioned_assets, key=lambda item: item[0], reverse=True)):
        updated = updated[:position].rstrip() + _visual_marker_block(asset, idx) + updated[position:].lstrip()
    return updated.strip()


def _single_asset_from_search(image_path: str | Path | None, public_image_url: str | None, source_metadata: dict[str, Any]) -> list[dict[str, Any]]:
    if not image_path and not public_image_url:
        return []
    asset = dict(source_metadata or {})
    asset.setdefault("asset_id", "primary")
    asset.setdefault("visual_metric", asset.get("query") or "search image")
    if image_path:
        asset["local_path"] = str(image_path)
    if public_image_url:
        asset["public_url"] = public_image_url
    return [asset]


def create_branded_fallback_image(title: str, output_path: Path) -> bool:
    """Generates a high-quality branded Capital Chronicle cover card using matplotlib."""
    try:
        import matplotlib
        matplotlib.use('Agg')  # use non-interactive backend
        import matplotlib.pyplot as plt
        import textwrap
        
        # 1200x630 pixels is standard cover preview card (approx 1.91:1)
        fig, ax = plt.subplots(figsize=(12, 6.3), dpi=100)
        fig.patch.set_facecolor('#0f172a')  # slate-900 (brand dark bg)
        ax.set_facecolor('#0f172a')
        
        # Draw clean emblem/symbol (gold concentric ring representation or digit 8)
        ax.text(0.5, 0.70, "8", color='#f59e0b', fontsize=72, fontweight='bold', ha='center', va='center')
        
        # Brand Typography
        ax.text(0.5, 0.52, "CAPITAL CHRONICLE", color='#f8fafc', fontsize=28, fontweight='bold', ha='center', va='center')
        ax.text(0.5, 0.44, "EDUCATIONAL BRIEFING", color='#f59e0b', fontsize=18, fontweight='bold', ha='center', va='center')
        
        # Clean title text wrapping
        clean_title = title
        for prefix in ["Capital Chronicle Educational Briefing:", "Capital Chronicle Macro Volatility Briefing:", "Capital Chronicle:"]:
            if clean_title.lower().startswith(prefix.lower()):
                clean_title = clean_title[len(prefix):].strip()
        
        wrapped = "\n".join(textwrap.wrap(clean_title, width=55))
        ax.text(0.5, 0.24, wrapped, color='#94a3b8', fontsize=16, style='italic', ha='center', va='center')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
        plt.close(fig)
        print(f"[Info] Generated branded fallback cover card at: {output_path}")
        return True
    except Exception as e:
        print(f"[Warning] Failed to generate branded fallback card: {e}")
        return False


def generate_live_platform_variants(
    article_packet_path: str | Path = DEFAULT_ARTICLE_PACKET,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    live_run: bool = False,
    timeout_seconds: int = 20,
    dry_run_image_search_isolated: bool | None = None,
) -> dict[str, Any]:
    _load_live_env_if_needed(live_run)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if dry_run_image_search_isolated is None:
        dry_run_image_search_isolated = not live_run
    env_lookup_allowed = bool(live_run or not dry_run_image_search_isolated)
    as_of_date = os.environ.get("CONTENTOPS_AS_OF_DATE") if env_lookup_allowed else None
    source_csv = os.environ.get("CONTENTOPS_MACRO_CHART_CSV") if env_lookup_allowed else None
    try:
        with open(article_packet_path, "r", encoding="utf-8") as f:
            article_data = json.load(f)
    except Exception as exc:
        print(f"[Warning] Failed to load canonical article: {exc}")
        article_data = {}

    article_draft = article_data.get("canonical_article_draft", {})
    title = article_draft.get("title", "Capital Chronicle Macro Volatility Briefing")
    subtitle = article_draft.get("subtitle", "Process-led macro analysis")
    intro = article_draft.get("intro", "")
    conclusion = article_draft.get("conclusion", "")
    sections = article_draft.get("sections", [])
    body_text = f"{intro}\n\n"
    for section in sections:
        body_text += f"### {section.get('title')}\n{section.get('body')}\n\n"
    body_text += conclusion
    body_text += _render_source_trail(article_draft.get("source_trail") or [])

    variants, variant_threads = _fallback_variants(title, subtitle, body_text)
    image_path = None
    public_image_url = None
    source_metadata: dict[str, Any] = {}
    media_assets: list[dict[str, Any]] = []
    media_audit: dict[str, Any] = {}
    media_replacement_notes: list[str] = []
    provider_call_made = False
    provider_recovery_used = False
    provider_attempts: list[dict[str, Any]] = []
    validation_failures: list[str] = []
    image_search_network_attempted = False
    source_backed_generation_network_attempted = False
    dry_run_fixture_media_used = False

    recency_days = 365
    if not dry_run_image_search_isolated:
        try:
            recency_days = int(os.environ.get("CONTENTOPS_MEDIA_SEARCH_RECENCY_DAYS", "365"))
        except Exception:
            recency_days = 365

    if dry_run_image_search_isolated:
        media_replacement_notes.append("dry_run_image_search_skipped_network_isolated")
    else:
        try:
            # 1. Try refined specific query
            image_search_network_attempted = True
            image_query = _build_clean_image_query(title)
            image_path, public_image_url = execute_google_image_search_and_download(image_query, recency_days=recency_days)

            # 2. Fall back to generic query if specific failed
            if not image_path:
                fallback_query = "global economy financial chart news"
                print(f"[Info] Specific image query failed. Trying fallback: '{fallback_query}'")
                image_path, public_image_url = execute_google_image_search_and_download(
                    fallback_query,
                    custom_filename="img_generic_fallback.jpg",
                    recency_days=recency_days,
                )
        except Exception as e:
            print(f"[Warning] Google Image search/generation failed: {e}")

    source_metadata = _load_image_metadata(image_path)
    if image_path or public_image_url:
        media_audit = audit_media_candidate(
            article_title=title,
            article_text=body_text,
            image_path=image_path,
            public_image_url=public_image_url,
            source_metadata=source_metadata,
            as_of_date=as_of_date,
        )
        if media_audit.get("audit_status") == "FAIL":
            media_replacement_notes.append("search_candidate_rejected:" + "|".join(media_audit.get("blockers") or []))
            print(f"[Warning] Search visual rejected by media content audit: {media_audit.get('blockers')}")

    if not image_path or media_audit.get("audit_status") == "FAIL":
        try:
            if dry_run_image_search_isolated:
                source_backed_assets = _load_committed_macro_visual_pack(article_title=title)
                dry_run_fixture_media_used = bool(source_backed_assets)
                if source_backed_assets:
                    media_replacement_notes.append("committed_source_backed_visual_pack_selected")
                elif _looks_like_fed_funds_topic(title.lower()):
                    source_backed_assets = build_current_macro_visual_pack(
                        title,
                        output_dir=Path("docs/automation/V6_MEDIA_SYSTEM/downloads"),
                        as_of_date=as_of_date,
                    )
                    dry_run_fixture_media_used = bool(source_backed_assets)
                    if source_backed_assets:
                        media_replacement_notes.append("local_source_backed_rates_visual_pack_generated")
            else:
                source_backed_generation_network_attempted = True
                source_backed_assets = build_current_macro_visual_pack(
                    title,
                    output_dir=Path("docs/automation/V6_MEDIA_SYSTEM/downloads"),
                    as_of_date=as_of_date,
                )
        except Exception as exc:
            print(f"[Warning] Source-backed chart pack generation failed: {exc}")
            source_backed_assets = []
        if source_backed_assets:
            media_replacement_notes.append("source_backed_chart_pack_selected")
            media_assets = source_backed_assets
            source_metadata = dict(media_assets[0])
            image_path = source_metadata.get("local_path")
            public_image_url = source_metadata.get("public_url")
            media_audit = audit_media_candidate(
                article_title=title,
                article_text=body_text,
                image_path=image_path,
                public_image_url=public_image_url,
                source_metadata=source_metadata,
                as_of_date=as_of_date,
            )

    if not image_path:
        print("[Info] No audited visual available. Generating local branded fallback card and blocking dispatch until reviewed...")
        fallback_filename = f"fallback_{hashlib.md5(title.encode('utf-8')).hexdigest()[:12]}.png"
        local_fallback_path = Path("docs/automation/V6_MEDIA_SYSTEM/downloads") / fallback_filename
        if create_branded_fallback_image(title, local_fallback_path):
            image_path = str(local_fallback_path)
            public_image_url = None
            source_metadata = {
                "asset_id": "primary",
                "source_label": "Capital Chronicle generated fallback card",
                "canonical_source_label": "Capital Chronicle generated fallback card",
                "query": title,
                "visual_metric": "branded text cover card",
                "local_path": image_path,
            }
            media_audit = audit_media_candidate(
                article_title=title,
                article_text=body_text,
                image_path=image_path,
                public_image_url=public_image_url,
                source_metadata=source_metadata,
                as_of_date=as_of_date,
            )

    if not image_path and not media_audit:
        media_audit = audit_media_candidate(
            article_title=title,
            article_text=body_text,
            image_path=None,
            public_image_url=None,
            source_metadata={},
            as_of_date=as_of_date,
        )

    if not media_assets:
        media_assets = _single_asset_from_search(image_path, public_image_url, source_metadata)
    if media_replacement_notes:
        media_audit.setdefault("replacement_notes", media_replacement_notes)
    if media_audit.get("audit_status") == "FAIL":
        validation_failures.append("media_content_audit_failed:" + "|".join(media_audit.get("blockers") or ["unknown"]))

    variants["substack"] = _insert_substack_visual_markers(
        str(variants.get("substack", "")),
        media_assets,
        article_draft.get("visual_slots") if isinstance(article_draft.get("visual_slots"), list) else None,
    )

    media_manifest = _build_media_manifest(
        title=title,
        image_path=image_path,
        public_image_url=public_image_url,
        source_metadata=source_metadata,
        media_assets=media_assets,
        media_audit=media_audit,
        source_csv=source_csv,
    )
    media_manifest["dry_run_image_search_isolated"] = bool(dry_run_image_search_isolated)
    media_manifest["image_search_network_attempted"] = image_search_network_attempted
    media_manifest["source_backed_generation_network_attempted"] = source_backed_generation_network_attempted
    media_manifest["dry_run_fixture_media_used"] = dry_run_fixture_media_used
    media_manifest["live_platform_api_called"] = False
    media_manifest["credential_lookup_performed"] = False
    media_diversification_audit = audit_media_manifest(
        media_manifest,
        article_title=title,
        article_text=body_text,
        expected_min_assets=3,
        as_of_date=as_of_date,
    )
    media_manifest["media_diversification_audit"] = media_diversification_audit
    if media_diversification_audit.get("audit_status") == "FAIL":
        validation_failures.append(
            "media_diversification_audit_failed:"
            + "|".join(media_diversification_audit.get("blockers") or ["unknown"])
        )
    if live_run and not media_diversification_audit.get("auto_publication_safe", False):
        validation_failures.append("media_rights_operator_review_required")

    if live_run:
        _load_live_env_if_needed(True)
        api_key = os.environ.get("NINE_ROUTER_API_KEY")
        if not api_key:
            validation_failures.append("NINE_ROUTER_API_KEY_missing")
        else:
            prompt = (
                f"You are a platform content editor for Capital Chronicle. Convert this canonical article into platform-native editorial distribution.\n"
                f"Title: {title}\nSubtitle: {subtitle}\nArticle:\n{body_text}\n\n"
                f"Return ONLY raw JSON: {{\"linkedin\": str, \"facebook\": str, \"discord\": str, \"telegram\": str, "
                f"\"instagram_caption\": str, \"x_thread\": [str], \"threads_thread\": [str]}}.\n"
                f"Rules: no stubs/placeholders, no financial advice, concrete article-specific language, X posts <= 280 chars, Threads posts <= 500 chars.\n"
                f"Each platform must use a different editorial lead, one concrete evidence hook from the article, and a native pacing style. "
                f"Do not repeat the same first sentence across platforms. LinkedIn should read like a professional analyst note; "
                f"X and Threads should be concise thread-native; Discord and Telegram should sound like a newsroom channel update; "
                f"Instagram/Facebook should give enough chart context for a visual-first post."
            )
            try:
                llm_text = call_live_provider(prompt, "9router", timeout_seconds)
                provider_call_made = True
                llm_data = parse_llm_json(llm_text) or {}
                if not llm_data:
                    provider_attempts.append({"provider": "9router", "status": "failed", "failure": "variant_provider_json_parse_empty", "timeout_seconds": timeout_seconds})
                    validation_failures.append("variant_provider_json_parse_empty")
                else:
                    provider_attempts.append({"provider": "9router", "status": "accepted", "failure": None, "timeout_seconds": timeout_seconds})
                for key in ("linkedin", "facebook", "discord", "telegram", "instagram_caption"):
                    if llm_data.get(key):
                        variants[key] = str(llm_data[key])
                if llm_data.get("x_thread"):
                    variant_threads["x"] = [str(x) for x in llm_data["x_thread"]]
                    variants["x"] = "\n\n---\n\n".join(variant_threads["x"])
                if llm_data.get("threads_thread"):
                    variant_threads["threads"] = [str(x) for x in llm_data["threads_thread"]]
                    variants["threads"] = "\n\n---\n\n".join(variant_threads["threads"])
            except Exception as exc:
                provider_call_made = True
                provider_recovery_used = True
                provider_attempts.append({"provider": "9router", "status": "failed", "failure": f"variant_provider_failed:{type(exc).__name__}:{exc}", "timeout_seconds": timeout_seconds})
                validation_failures.append(f"variant_provider_failed:{type(exc).__name__}:{exc}")

    for key in ("substack", "linkedin", "facebook", "instagram_caption"):
        variants[key] = _ensure_no_advice_context(str(variants.get(key, "")))

    validation_failures.extend(validate_platform_variants(variants, variant_threads, live_run=live_run))
    validation_summary = summarize_validation(validation_failures)
    variant_status = "VARIANT_READY" if not validation_failures else "VARIANT_VALIDATION_FAILED"

    for plat, text in variants.items():
        suffix = "telegram_operator_preview.md" if plat == "telegram" else f"{plat}_variant.md"
        out_file = output_dir / suffix
        out_file.write_text("\n".join([
            f"# {plat.upper()} NATIVE VARIANT",
            f"- **Status**: {variant_status}",
            f"- **Associated Image**: {image_path or 'None'}",
            f"- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            text,
        ]) + "\n", encoding="utf-8")

    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "source_article_id": article_data.get("packet_id"),
        "source_intent_id": article_data.get("operator_idea_id"),
        "variant_status": variant_status,
        "variant_stage": "platform_native_validated" if not validation_failures else "platform_native_validation_failed",
        "target_platforms": ["substack", "discord", "linkedin", "facebook", "x", "threads", "telegram", "instagram"],
        "variants": variants,
        "variant_threads": variant_threads,
        "image_path": str(image_path) if image_path else None,
        "public_image_url": public_image_url,
        "media_manifest": media_manifest,
        "provider_call_made": provider_call_made,
        "provider_recovery_used": provider_recovery_used,
        "provider_attempts": provider_attempts,
        "dry_run_image_search_isolated": bool(dry_run_image_search_isolated),
        "image_search_network_attempted": image_search_network_attempted,
        "source_backed_generation_network_attempted": source_backed_generation_network_attempted,
        "dry_run_fixture_media_used": dry_run_fixture_media_used,
        "live_platform_api_called": False,
        "credential_lookup_performed": False,
        "validation_failures": validation_failures,
        "validation_summary": validation_summary,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    }

    packet["platform_variant_packet_id"] = f"variant_packet_{compute_packet_hash(packet)[:12]}"
    packet["exact_payload_hash"] = compute_packet_hash(packet)
    write_json(output_dir / "platform_variant_packet.json", packet)
    try:
        write_json(Path("ui/contentops_v5/src/data/platform_variant_packet.json"), packet)
        print("[Info] Copied variant packet to UI src/data folder")
    except Exception as e:
        print(f"[Warning] Failed to copy variant packet to UI src/data: {e}")
    return packet


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Live Platform Variant Generator")
    parser.add_argument("--article-packet", default=str(DEFAULT_ARTICLE_PACKET))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--live-run", action="store_true", help="Run 9router live generation")
    args = parser.parse_args(argv)
    
    packet = generate_live_platform_variants(
        article_packet_path=args.article_packet,
        output_dir=args.output_dir,
        live_run=args.live_run
    )
    
    print(json.dumps({
        "platform_variant_packet_id": packet["platform_variant_packet_id"],
        "variant_status": packet["variant_status"],
        "image_path": packet["image_path"],
        "provider_call_made": packet["provider_call_made"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
