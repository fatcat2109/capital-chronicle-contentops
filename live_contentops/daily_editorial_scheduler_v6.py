"""Daily newsroom scheduler for ContentOps V6.

Headline sidecars are treated as catalyst context only. They can raise urgency,
suggest source needs, and surface narrative clusters, but they are not market
price truth, macro-print truth, source clearance, or trading input.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "daily_editorial_scheduler_v6.0"
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob

DEFAULT_SIDECAR_GLOB = canonical_headline_sidecar_glob()
DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_DAILY_EDITORIAL_SCHEDULE")
DEFAULT_SLOT_COUNT = 6

TAG_WEIGHTS = {
    "central_bank": 16,
    "inflation": 15,
    "labor": 14,
    "energy": 14,
    "geopolitics": 14,
    "volatility": 11,
    "risk_off": 11,
    "rates": 10,
    "earnings": 7,
}

OFFICIAL_SOURCE_TERMS = {
    "fed": "Federal Reserve policy/communication source",
    "fomc": "Federal Reserve policy/communication source",
    "treasury": "U.S. Treasury rates/source table",
    "eia": "EIA energy release/source table",
    "cpi": "BLS CPI release/source table",
    "jobs": "BLS labor release/source table",
    "payroll": "BLS labor release/source table",
    "opec": "OPEC/energy official source",
    "inventory": "EIA inventory release/source table",
}


@dataclass
class HeadlineItem:
    topic: str
    text: str
    author: str
    timestamp: str
    tags: list[str]
    sidecar_path: str
    raw: dict[str, Any]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return rows


def _first_text(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    tweet = row.get("tweet") if isinstance(row.get("tweet"), dict) else {}
    for key in keys:
        value = tweet.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _tags(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in (
        "tags",
        "topic_tags",
        "auto_tags",
        "category_tags",
        "candidate_catalyst_tags",
        "follow_up_data_need_candidates",
    ):
        raw = row.get(key)
        if isinstance(raw, list):
            values.extend(str(item).strip().lower() for item in raw if str(item).strip())
    quality = row.get("quality_flags") if isinstance(row.get("quality_flags"), dict) else {}
    for key, value in quality.items():
        if value is True:
            values.append(str(key).strip().lower())
    return sorted(set(values))


def load_headline_sidecars(sidecar_glob: str = DEFAULT_SIDECAR_GLOB) -> list[HeadlineItem]:
    items: list[HeadlineItem] = []
    for path_str in sorted(glob.glob(sidecar_glob)):
        path = Path(path_str)
        for row in _load_jsonl(path):
            text = _first_text(row, ("text", "headline_text", "headline", "tweet_text", "content", "body"))
            if not text:
                continue
            topic = _first_text(row, ("topic", "headline_text", "headline", "title")) or text[:110]
            author = _first_text(row, ("author", "author_handle", "author_name", "username", "source")) or "headline_sidecar"
            timestamp = _first_text(row, ("timestamp_gmt7", "headline_timestamp", "timestamp", "created_at", "published_at"))
            items.append(HeadlineItem(
                topic=re.sub(r"\s+", " ", topic).strip(),
                text=re.sub(r"\s+", " ", text).strip(),
                author=author,
                timestamp=timestamp,
                tags=_tags(row),
                sidecar_path=str(path),
                raw=row,
            ))
    return items


def _dedupe_key(item: HeadlineItem) -> str:
    raw_key = (
        item.raw.get("dedup_key")
        or item.raw.get("headline_id")
        or item.raw.get("text_sha256")
        or item.text.lower()
    )
    return re.sub(r"[^a-z0-9]+", "-", str(raw_key).lower()).strip("-")[:120]


def _freshness_score(timestamp: str) -> int:
    if not timestamp:
        return 8
    match = re.search(r"(20\d{2})[-_/](\d{1,2})[-_/](\d{1,2})", timestamp)
    if not match:
        return 10
    try:
        dt = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), tzinfo=timezone.utc)
    except Exception:
        return 10
    age_days = max(0, (datetime.now(timezone.utc) - dt).days)
    return max(6, 24 - min(age_days, 18))


def _source_needs(item: HeadlineItem) -> list[str]:
    text = f"{item.topic} {item.text} {' '.join(item.tags)}".lower()
    needs = []
    for term, need in OFFICIAL_SOURCE_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", text):
            needs.append(need)
    if any(tag in item.tags for tag in ("energy", "geopolitics")):
        needs.append("Primary energy/geopolitical source check before drafting")
    if not needs:
        needs.append("Primary source review before canonical article generation")
    return sorted(set(needs))


def _media_needs(item: HeadlineItem) -> list[str]:
    tags = set(item.tags)
    text = f"{item.topic} {item.text}".lower()
    needs = ["source-backed data chart where numeric claims are used"]
    if tags & {"energy", "geopolitics"} or any(term in text for term in ("oil", "hormuz", "iran", "opec", "shipping")):
        needs.append("contextual map/photo/official visual with rights/provenance review")
    if tags & {"central_bank", "rates", "inflation", "labor"}:
        needs.append("official-release chart or table screenshot replacement generated from source data")
    return needs


def _article_type(item: HeadlineItem) -> str:
    text = f"{item.topic} {item.text} {' '.join(item.tags)}".lower()
    if any(term in text for term in ("breaking", "urgent", "just in")):
        return "breaking_news"
    if any(term in text for term in ("cpi", "payroll", "jobs report", "fomc", "eia", "inventory", "treasury auction")):
        return "official_release"
    if any(tag in item.tags for tag in ("central_bank", "inflation", "labor", "energy", "geopolitics", "volatility")):
        return "rapid_analysis"
    if any(term in text for term in ("explainer", "deep dive", "why")):
        return "deep_research"
    return "evergreen_explainer"


def _readiness(item: HeadlineItem, source_needs: list[str], media_needs: list[str]) -> str:
    if item.raw.get("numeric_truth_authority") is True or item.raw.get("forecast_readiness_authority") is True:
        return "BLOCKED"
    text = f"{item.topic} {item.text}".lower()
    if item.tags and any(term in text for term in OFFICIAL_SOURCE_TERMS):
        return "READY_FOR_PIPELINE"
    if not item.tags:
        return "NEEDS_SOURCE_REVIEW"
    return "NEEDS_SOURCE_REVIEW"


def _rank_item(item: HeadlineItem, covered_terms: set[str]) -> dict[str, Any]:
    text = f"{item.topic} {item.text}".lower()
    tag_score = sum(TAG_WEIGHTS.get(tag, 0) for tag in item.tags)
    official_score = 12 if any(term in text for term in OFFICIAL_SOURCE_TERMS) else 0
    impact = min(100, 35 + tag_score + official_score)
    urgency = min(100, _freshness_score(item.timestamp) + math.ceil(tag_score * 0.85) + official_score)
    topic_terms = {tok for tok in re.findall(r"[a-z0-9]+", text) if len(tok) > 4}
    novelty_penalty = 18 if topic_terms & covered_terms else 0
    source_needs = _source_needs(item)
    media_needs = _media_needs(item)
    article_type = _article_type(item)
    readiness = _readiness(item, source_needs, media_needs)
    return {
        "topic": item.topic[:160],
        "angle": _angle_for_item(item),
        "urgency_score": max(0, urgency - novelty_penalty),
        "impact_score": max(0, impact - novelty_penalty),
        "source_needs": source_needs,
        "media_needs": media_needs,
        "suggested_article_type": article_type,
        "readiness": readiness,
        "headline_sidecar_context_only": True,
        "numeric_truth_authority": False,
        "source_clearance_authority": False,
        "sidecar_path": item.sidecar_path,
        "source_headline_author": item.author,
        "source_headline_timestamp": item.timestamp,
        "tags": item.tags,
    }


def _angle_for_item(item: HeadlineItem) -> str:
    text = f"{item.topic} {item.text}".lower()
    if "oil" in text or "energy" in item.tags:
        return "Separate current energy-price evidence from supply-risk narrative and policy pass-through."
    if "fed" in text or "central_bank" in item.tags:
        return "Frame the policy signal against rates, inflation expectations, and market-pricing limits."
    if "inflation" in item.tags or "cpi" in text:
        return "Treat the release as source-backed inflation evidence before drawing growth or policy conclusions."
    if "geopolitics" in item.tags:
        return "Map the geopolitical channel, source constraints, and market-transmission path without trade advice."
    return "Build a rapid evidence map before deciding whether this deserves long-form treatment."


def _fallback_schedule_items(schedule_date: str, slot_count: int) -> list[dict[str, Any]]:
    fallback_topics = [
        ("Official release watch", "Check the calendar for CPI, jobs, EIA inventory, FOMC, Treasury auction, and central-bank remarks before deep research."),
        ("Energy and geopolitics watch", "Look for current oil, shipping, sanctions, OPEC, and chokepoint developments with rights-safe maps/photos."),
        ("Rates and recession dashboard", "Update yield-curve, Treasury, Fed, credit, and recession-risk context from official data sources."),
        ("Inflation pass-through monitor", "Track energy, shelter, goods, wages, and policy communication for source-backed inflation framing."),
        ("Market volatility rapid analysis", "Use current source-backed charts before publishing any volatility narrative."),
        ("Deep research reserve", "Use only if major current news density is low or the day already covers important official releases."),
    ]
    out = []
    for idx, (topic, angle) in enumerate(fallback_topics[:slot_count], start=1):
        out.append({
            "slot_index": idx,
            "topic": topic,
            "angle": angle,
            "urgency_score": 52 - idx,
            "impact_score": 58 - idx,
            "source_needs": ["No headline sidecars found; perform primary source review before drafting"],
            "media_needs": ["Source-backed data chart", "contextual rights-safe visual if topic warrants"],
            "suggested_article_type": "rapid_analysis" if idx < slot_count else "deep_research",
            "readiness": "NEEDS_SOURCE_REVIEW",
            "headline_sidecar_context_only": True,
            "numeric_truth_authority": False,
            "source_clearance_authority": False,
            "schedule_note": f"Fallback watchlist for {schedule_date}; not a claim that news occurred.",
        })
    return out


def build_daily_editorial_schedule(
    *,
    schedule_date: str,
    sidecar_glob: str = DEFAULT_SIDECAR_GLOB,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    slot_count: int = DEFAULT_SLOT_COUNT,
    covered_topics: list[str] | None = None,
) -> dict[str, Any]:
    items = load_headline_sidecars(sidecar_glob)
    covered_terms = {
        tok
        for topic in (covered_topics or [])
        for tok in re.findall(r"[a-z0-9]+", topic.lower())
        if len(tok) > 4
    }
    deduped: dict[str, HeadlineItem] = {}
    for item in items:
        deduped.setdefault(_dedupe_key(item), item)

    ranked = [_rank_item(item, covered_terms) for item in deduped.values()]
    ranked.sort(key=lambda row: (row["readiness"] == "READY_FOR_PIPELINE", row["urgency_score"], row["impact_score"]), reverse=True)
    if ranked:
        slots = []
        article_type_counts = Counter()
        for row in ranked:
            if len(slots) >= slot_count:
                break
            row = dict(row)
            row["slot_index"] = len(slots) + 1
            if row["suggested_article_type"] == "deep_research" and len(slots) < 3:
                row["readiness"] = "NEEDS_SOURCE_REVIEW"
                row.setdefault("scheduler_notes", []).append("Deep research deferred until current-news slots are covered.")
            article_type_counts[row["suggested_article_type"]] += 1
            slots.append(row)
    else:
        slots = _fallback_schedule_items(schedule_date, slot_count)
        article_type_counts = Counter(row["suggested_article_type"] for row in slots)

    output = {
        "schema_version": SCHEMA_VERSION,
        "schedule_date": schedule_date,
        "sidecar_glob": sidecar_glob,
        "headline_sidecar_count": len(items),
        "headline_sidecars_are_catalyst_only": True,
        "forbidden_uses": [
            "market_price_truth",
            "macro_print_truth",
            "source_clearance",
            "trade_signal",
            "broker_execution_input",
        ],
        "target_article_slots": slot_count,
        "article_type_counts": dict(article_type_counts),
        "slots": slots,
        "scheduler_notes": [
            "Prioritize current official releases, fresh macro/geopolitical news, source availability, media availability, and novelty.",
            "Deep research/explainer work is secondary unless current-news density is low or key releases are already covered.",
        ],
    }
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"daily_schedule_{schedule_date.replace('-', '_')}.json"
    output["output_path"] = str(output_path)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the V6 daily editorial schedule from headline sidecars.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--sidecar-glob", default=DEFAULT_SIDECAR_GLOB)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--slot-count", type=int, default=DEFAULT_SLOT_COUNT)
    args = parser.parse_args(argv)
    schedule = build_daily_editorial_schedule(
        schedule_date=args.date,
        sidecar_glob=args.sidecar_glob,
        output_dir=args.output_dir,
        slot_count=args.slot_count,
    )
    print(json.dumps({
        "schedule_date": schedule["schedule_date"],
        "output_path": schedule["output_path"],
        "headline_sidecar_count": schedule["headline_sidecar_count"],
        "slot_count": len(schedule["slots"]),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
