"""CC-817 v2: High-Interval Market Forces Engine for ContentOps.

Upgrades ContentOps atop CC-817's baseline (live_contentops/market_attention_map_public_v1.py)
under Jim's 2026-11-25 19:05 GMT+7 directive, aligned with Main's CC-807 contract
(`cc-807-schema-contract-v1.json`, `MarketAttentionMapLiveV1` / `MarketAttentionMapRegisterV1`):
- Pure-code 15-30 minute allow-list poller reading Main's live attention map
  (`market_attention_map_live_v1.json`) with zero LLM calls per tick and strict
  stripping of private book/positions/prepared responses/surprise map/linked odds
  markets/raw X-list/wire text and proprietary market-implied numeric odds.
- Material-shift detector triggering ONLY on:
    1. New Top-5 entry (`NEW_TOP_FIVE_ENTRY`),
    2. Scenario branch flip (`BRANCH_FLIPPED`),
    3. >= 10 pp probability shift (`PROBABILITY_SHIFT_GE_10PP`, rendered strictly
       in qualitative words for market-implied odds), or
    4. Decision-point catalyst hit (`DECISION_POINT_CATALYST_HIT`).
- Per-theme anti-spam cooldown (>= 2 hours unless `BRANCH_FLIPPED`) and persisted
  exactly-once idempotency ledger so repeated polls never duplicate posts.
- Intraday Market Force Flash / Update renderer: immutable dated `WEB_ONLY`
  Substack theme page linking the prior edition + bound TradingView chart across
  all 7 core markets (incl. USTEC -> NASDAQ:NDX) + concise 10-platform short
  social copy with zero truncation.
- Session-Sync Market Forces Pulse (Pre-Asia / Pre-London / Pre-US Cash Open) for
  opt-in integration into `market_wrap_editorial_v1.py` without altering existing
  daily or weekly wraps when absent.
- Strict enforcement of all 5 public filters (CC-788, Decisions 40, 44, 90, 107,
  109, 157, 158) and zero Antigravity (`agy`) usage (Decision 168).
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Mapping
from zoneinfo import ZoneInfo

from . import market_attention_map_public_v1 as attention
from . import public_instruments_v1 as instruments
from . import tradingview_snapshot_v1 as tv
from .capital_chronicle_latest_report_consumer_v1 import sha256_of
from .event_article_guard_v1 import (
    CONFLICTS_NOTICE,
    PUBLIC_NOTICE,
    public_execution_copy_forbidden,
)
from .plan_reader_copy_v1 import et
from .preview_link_guard_v1 import find_forbidden_link
from .public_time_v1 import public_date, public_datetime

SCHEMA_VERSION = "contentops.market_forces_high_interval.v1"
FLASH_PAGE_SCHEMA_VERSION = "contentops.market_force_flash_page.v1"
PULSE_SCHEMA_VERSION = "contentops.session_sync_pulse.v1"
LEDGER_SCHEMA_VERSION = "contentops.market_forces_high_interval_ledger.v1"
FLASH_DESTINATION = "internal:market-force-flash"
DEFAULT_LIVE_MAP_FILENAME = "market_attention_map_live_v1.json"
DEFAULT_LIVE_MAP_PATH = Path(r"A:\Capital Chronicle\Runtime\MarketAttentionMap\market_attention_map_live_v1.json")

ET = ZoneInfo("America/New_York")

MIN_POLL_INTERVAL_MINUTES = 15
MAX_POLL_INTERVAL_MINUTES = 30
DEFAULT_POLL_INTERVAL_MINUTES = 15

MIN_COOLDOWN_MINUTES = 120
DEFAULT_COOLDOWN_MINUTES = 120
PROBABILITY_SHIFT_THRESHOLD_PP = Decimal("10")
SHARP_SHIFT_THRESHOLD_PP = Decimal("20")
DEFAULT_MAX_MAP_AGE_MINUTES = 60
DECISION_POINT_HIT_WINDOW_MINUTES = 30

TRIGGER_BRANCH_FLIPPED = "BRANCH_FLIPPED"
TRIGGER_NEW_TOP_FIVE = "NEW_TOP_FIVE_ENTRY"
TRIGGER_CATALYST_HIT = "DECISION_POINT_CATALYST_HIT"
TRIGGER_PROBABILITY_SHIFT = "PROBABILITY_SHIFT_GE_10PP"
TRIGGER_PRIORITY = (
    TRIGGER_BRANCH_FLIPPED,
    TRIGGER_NEW_TOP_FIVE,
    TRIGGER_CATALYST_HIT,
    TRIGGER_PROBABILITY_SHIFT,
)

SESSION_PRE_ASIA = "pre_asia"
SESSION_PRE_LONDON = "pre_london"
SESSION_PRE_US = "pre_us"
SESSION_LABELS = {
    SESSION_PRE_ASIA: "Pre-Asia Open",
    SESSION_PRE_LONDON: "Pre-London Open",
    SESSION_PRE_US: "Pre-US Cash Open",
}
SESSION_ORDER = (SESSION_PRE_ASIA, SESSION_PRE_LONDON, SESSION_PRE_US)

ALL_TEN_DESTINATIONS = (
    "x",
    "threads",
    "telegram",
    "discord",
    "linkedin",
    "linkedin_company",
    "instagram_business",
    "facebook_page",
    "youtube",
    "substack_notes",
)

_HIT_DP_STATUSES = frozenset({"hit", "triggered", "released", "confirmed", "passed", "occurred"})
_PRIVATE_TOP_KEYS = (
    "x_list_posts",
    "raw_x_posts",
    "x_posts",
    "wire_headlines",
    "raw_headlines",
    "private_headlines",
    "private_notes",
    "open_positions",
    "positions",
    "book",
    "portfolio",
    "prepared_responses",
    "prepared_response",
    "surprise_map",
    "priced_in_gap",
    "linked_odds_markets",
    "scoring_hooks",
    "branch_flip_evidence",
    "execution_plans",
    "armed_plans",
    "level2_triggers",
    "odds_markets",
    "prediction_markets",
    "broker_levels",
    "internal_notes",
    "joint_scenarios",
    "unknown_force_tickets",
    "public_boundary_notice",
)
_PRIVATE_THEME_KEYS = _PRIVATE_TOP_KEYS + (
    "kalshi",
    "polymarket",
    "fedwatch",
    "cme_fedwatch",
    "internal_rationale",
    "account_id",
    "account_number",
    "account_equity",
    "lot_size",
    "sizes",
    "watch_keywords",
)
_SAFE_CADENCE_KEYS = frozenset({
    "interval_minutes",
    "refresh_interval_minutes",
    "live_refresh_interval_minutes",
    "refresh_mode",
    "last_deep_pass_utc",
    "next_deep_pass_utc",
    "last_intraday_refresh_utc",
    "last_live_refresh_utc",
    "last_refresh_utc",
    "last_material_change_utc",
    "cadence_mode",
})
_ELLIPSIS = re.compile(r"(?:\.\.\.|…)")
_DIRECTION_LABELS = {
    "UP": "upside pressure",
    "DOWN": "downside pressure",
    "UP_THEN_EVENT_DOWN": "upside pressure then event-reversal risk",
    "DOWN_THEN_EVENT_UP": "downside pressure then event-reversal risk",
    "TWO_WAY": "two-way",
}


def _decimal_prob(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if not isinstance(value, (int, float, Decimal)):
        return None
    try:
        dec = Decimal(str(value))
    except InvalidOperation:
        return None
    if not dec.is_finite() or dec < Decimal("0") or dec > Decimal("100"):
        return None
    return dec.normalize()


def _decimal_delta(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if not isinstance(value, (int, float, Decimal)):
        return None
    try:
        dec = Decimal(str(value))
    except InvalidOperation:
        return None
    if not dec.is_finite() or abs(dec) > Decimal("100"):
        return None
    return dec.normalize()


def _sanitize_chain_sign(raw_sign: Any, raw_direction: Any) -> str:
    """Convert internal snake_case or bare directional tokens in CC-807 causal chains to Decision-158 prose."""
    sign = attention._clean_text(raw_sign)
    direction = attention._clean_text(raw_direction).upper()
    if not sign:
        return _DIRECTION_LABELS.get(direction, "two-way")
    # Preserve ordinary prose when it has no snake_case tokens or bare unconditional direction words.
    if "_" not in sign and not re.search(r"\b(?:bullish|bearish)\b", sign, re.I):
        return sign
    if direction in _DIRECTION_LABELS:
        return _DIRECTION_LABELS[direction]
    cleaned = sign.replace("_", " ")
    cleaned = re.sub(r"\bbullish\b", "upside", cleaned, flags=re.I)
    cleaned = re.sub(r"\bbearish\b", "downside", cleaned, flags=re.I)
    for code, short in attention.SHORT_MARKET_LABELS.items():
        cleaned = re.sub(rf"\b{code}\b", short, cleaned, flags=re.I)
    return attention._clean_text(cleaned) or "two-way"


def _filter_public_computed_metrics(raw_metrics: Any) -> list[dict[str, str]]:
    """Keep only free-page Capital Chronicle computed figures; strip replay R / stop / execution metrics."""
    projected = attention._project_computed_metrics(raw_metrics)
    kept: list[dict[str, str]] = []
    for item in projected:
        joined = f"{item['label']}: {item['value']}"
        if public_execution_copy_forbidden(joined):
            continue
        if re.search(r"\b(?:stop|replay|entry|exit|r[- ]?multiple)\b", joined, re.I):
            continue
        kept.append(item)
    return kept


def _harvest_extra_private_texts(raw_map: Mapping[str, Any]) -> list[str]:
    """Harvest private strings from all stripped containers so public filters catch verbatim echoes."""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, str):
            cleaned = attention._clean_text(node)
            if len(cleaned) >= 24:
                found.append(cleaned)
        elif isinstance(node, Mapping):
            for key, val in node.items():
                if isinstance(val, (Mapping, list)):
                    walk(val)
                elif isinstance(val, str) and (
                    key in {
                        "text", "headline", "body", "title", "quote", "summary",
                        "rationale", "note", "notes", "message", "question", "market_title",
                    }
                    or len(val.strip()) >= 24
                ):
                    walk(val)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for key in _PRIVATE_TOP_KEYS:
        if key in raw_map:
            walk(raw_map.get(key))
    for theme in raw_map.get("themes") or []:
        if not isinstance(theme, Mapping):
            continue
        for key in _PRIVATE_THEME_KEYS:
            if key in theme:
                walk(theme.get(key))
        for src in theme.get("primary_sources") or []:
            if isinstance(src, Mapping) and str(src.get("kind") or "").casefold() in attention._PRIVATE_WATCH_KINDS:
                walk(src)
        for ts in theme.get("timeline_sources") or []:
            if isinstance(ts, Mapping) and str(ts.get("source_kind") or "").casefold() in {
                "x_list", "x_account", "wire", "wire_headline", "private_feed",
            }:
                walk(ts)
        for dp in theme.get("decision_points") or theme.get("catalysts") or []:
            if not isinstance(dp, Mapping):
                continue
            for ws in dp.get("watch_signals") or dp.get("signals") or []:
                if isinstance(ws, Mapping) and str(ws.get("kind") or "").casefold() in attention._PRIVATE_WATCH_KINDS:
                    walk(ws)
    return list(dict.fromkeys(found))


def _normalize_branch_kind(raw_kind: Any) -> str:
    text = str(raw_kind or "alternative").strip().casefold()
    kind, _ = attention._BRANCH_KIND_MAP.get(text, ("alternative", "Alternative case"))
    return kind


def _source_class(raw_source: Any) -> str:
    source = str(raw_source or "").strip().casefold()
    if source in attention._OWN_PROBABILITY_SOURCES:
        return "capital_chronicle"
    return "market_implied"


def normalize_live_map_envelope(raw_map: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize CC-807 / §4.A field aliases into canonical register shape without mutating input."""
    if not isinstance(raw_map, Mapping):
        raise ValueError("MARKET_FORCES_LIVE_MAP_OBJECT_REQUIRED")
    as_of = (
        raw_map.get("as_of_utc")
        or raw_map.get("refreshed_at_utc")
        or raw_map.get("generated_at_utc")
        or raw_map.get("updated_at_utc")
    )
    if not as_of:
        raise ValueError("MARKET_FORCES_LIVE_MAP_CLOCK_REQUIRED")
    as_of_iso = attention.utc(as_of).isoformat()

    raw_themes = raw_map.get("themes")
    if not isinstance(raw_themes, list) or not raw_themes:
        raise ValueError("ATTENTION_MAP_THEMES_REQUIRED")

    normalized_themes: list[dict[str, Any]] = []
    for idx, raw in enumerate(raw_themes, start=1):
        if not isinstance(raw, Mapping):
            raise ValueError("ATTENTION_MAP_THEME_OBJECT_REQUIRED")
        theme_id = str(raw.get("theme_id") or raw.get("id") or raw.get("slug") or "").strip().lower()
        name = raw.get("name") or raw.get("title")
        one_line = raw.get("one_line") or raw.get("summary") or raw.get("thesis_one_line")
        status = raw.get("status") or raw.get("state") or ""
        rank = raw.get("rank") if raw.get("rank") is not None else raw.get("attention_rank")
        if rank is None:
            rank = idx
        updated_raw = (
            raw.get("updated_at_utc")
            or raw.get("last_updated_utc")
            or raw.get("last_refreshed_utc")
            or as_of_iso
        )
        first_seen_raw = (
            raw.get("first_seen_utc")
            or raw.get("opened_at_utc")
            or raw.get("created_at_utc")
            or updated_raw
        )

        raw_branches = raw.get("branches") if raw.get("branches") is not None else raw.get("scenario_branches")
        norm_branches: list[dict[str, Any]] = []
        if isinstance(raw_branches, list):
            for b in raw_branches:
                if not isinstance(b, Mapping):
                    continue
                prob_source = b.get("probability_source") or b.get("odds_source") or b.get("source_kind") or ""
                # CC-807 branches may carry both cc_probability_pct (own) and market_implied_probability_pct (private).
                # Only own Capital Chronicle probabilities enter the public branch projection; market odds stay words-only.
                if _source_class(prob_source) == "capital_chronicle":
                    pub_prob = (
                        b.get("cc_probability_pct")
                        if b.get("cc_probability_pct") is not None
                        else b.get("probability_pct")
                        if b.get("probability_pct") is not None
                        else b.get("probability")
                    )
                else:
                    pub_prob = None
                norm_branches.append({
                    "kind": b.get("kind") or b.get("case") or b.get("branch_type") or b.get("role") or "alternative",
                    "summary": b.get("summary") or b.get("market_move") or b.get("description") or b.get("expected_move") or "",
                    "probability_pct": pub_prob,
                    "probability_source": prob_source,
                    "market_lean_words": b.get("market_lean_words") or b.get("odds_words") or "",
                    "invalidation": b.get("invalidation") or b.get("what_proves_wrong") or b.get("falsifier") or "",
                })

        raw_chains = raw.get("causal_chains") if raw.get("causal_chains") is not None else raw.get("chains")
        norm_chains: list[dict[str, Any]] = []
        if isinstance(raw_chains, list):
            for c in raw_chains:
                if not isinstance(c, Mapping):
                    continue
                norm_chains.append({
                    "asset": c.get("asset") or c.get("market"),
                    "event": c.get("event") or "",
                    "channel": c.get("channel") or "",
                    "sign": _sanitize_chain_sign(c.get("sign"), c.get("direction")),
                    "rough_size": c.get("rough_size") or c.get("size") or "",
                })

        raw_dps = raw.get("decision_points") if raw.get("decision_points") is not None else raw.get("catalysts")
        norm_dps: list[dict[str, Any]] = []
        if isinstance(raw_dps, list):
            for dp in raw_dps:
                if not isinstance(dp, Mapping):
                    continue
                norm_dps.append({
                    "id": dp.get("id") or dp.get("event_id") or dp.get("catalyst_id") or "",
                    "title": dp.get("title") or dp.get("name") or dp.get("event") or "",
                    "at_utc": dp.get("at_utc") or dp.get("scheduled_at_utc"),
                    "scheduled_date": dp.get("scheduled_date") or dp.get("date_only"),
                    "watch_condition": dp.get("watch_condition") or dp.get("trigger_condition") or "",
                    "source_url": dp.get("source_url") or "",
                    "watch_signals": dp.get("watch_signals") if dp.get("watch_signals") is not None else dp.get("signals"),
                })

        norm_theme: dict[str, Any] = {
            "theme_id": theme_id,
            "rank": rank,
            "name": name,
            "one_line": one_line,
            "status": status,
            "first_seen_utc": first_seen_raw,
            "updated_at_utc": updated_raw,
            "lead_market": raw.get("lead_market") or raw.get("primary_market"),
            "affected_markets": (
                raw.get("affected_markets")
                if raw.get("affected_markets") is not None
                else raw.get("markets")
                if raw.get("markets") is not None
                else raw.get("covered_markets")
            ),
            "causal_chains": norm_chains,
            "branches": norm_branches,
            "market_lean_words": raw.get("market_lean_words") or raw.get("odds_words") or "",
            "priced_in_words": raw.get("priced_in_words") or raw.get("priced_in_summary") or "",
            "computed_metrics": _filter_public_computed_metrics(raw.get("computed_metrics")),
            "decision_points": norm_dps,
            "history": raw.get("history") or [],
        }
        # Pass private keys through ONLY so attention.project_public_register harvests _private_texts
        # and strips them completely from the public output.
        for pkey in ("x_list_posts", "wire_headlines", "raw_headlines", "prepared_responses", "prepared_response"):
            if pkey in raw:
                norm_theme[pkey] = raw[pkey]
        normalized_themes.append(norm_theme)

    envelope: dict[str, Any] = {
        "schema_version": str(raw_map.get("schema_version") or "cc807.theme_register.v1"),
        "as_of_utc": as_of_iso,
        "themes": normalized_themes,
    }
    for pkey in ("x_list_posts", "wire_headlines", "raw_headlines", "private_headlines"):
        if pkey in raw_map:
            envelope[pkey] = raw_map[pkey]
    return envelope


def _extract_detector_state(raw_map: Mapping[str, Any], public_register: Mapping[str, Any]) -> dict[str, Any]:
    """Build internal-only shift-detection state (NEVER serialized to public copy)."""
    raw_by_id: dict[str, Mapping[str, Any]] = {}
    for raw in raw_map.get("themes") or []:
        if isinstance(raw, Mapping):
            tid = str(raw.get("theme_id") or raw.get("id") or raw.get("slug") or "").strip().lower()
            if tid:
                raw_by_id[tid] = raw

    themes_state: dict[str, dict[str, Any]] = {}
    for pub in public_register["themes"]:
        tid = pub["theme_id"]
        raw = raw_by_id.get(tid) or {}
        live_state = raw.get("live_state") if isinstance(raw.get("live_state"), Mapping) else {}
        flip_evidence = raw.get("branch_flip_evidence") if isinstance(raw.get("branch_flip_evidence"), Mapping) else {}
        base = next(b for b in pub["branches"] if b["kind"] == "base")
        base_thesis_fp = sha256_of(base["summary"].casefold())

        # Collect BOTH Capital Chronicle own probabilities AND proprietary market-implied
        # probabilities/deltas strictly inside non-public detector state so >= 10 pp shifts
        # can be detected in pure code without ever leaking numeric market odds to public copy.
        # Keyed by branch_id (or deterministic kind#idx fallback) so multiple branches of the
        # same kind (e.g. multiple alternative cases) never clobber one another (M1).
        raw_branches = raw.get("branches") if raw.get("branches") is not None else raw.get("scenario_branches") or []
        branch_probs: dict[str, dict[str, Any]] = {}
        highest_kind: str | None = None
        highest_prob: Decimal | None = None
        branch_id_to_kind: dict[str, str] = {}
        for b_idx, rb in enumerate(raw_branches):
            if not isinstance(rb, Mapping):
                continue
            kind = _normalize_branch_kind(rb.get("kind") or rb.get("case") or rb.get("branch_type") or rb.get("role"))
            bid = attention._clean_text(rb.get("branch_id") or "")
            branch_key = bid or f"{kind}#{b_idx}"
            if bid:
                branch_id_to_kind[bid] = kind
            s_class = _source_class(rb.get("probability_source") or rb.get("odds_source") or rb.get("source_kind"))

            cc_prob = _decimal_prob(
                rb.get("cc_probability_pct")
                if rb.get("cc_probability_pct") is not None
                else (
                    rb.get("probability_pct")
                    if rb.get("probability_pct") is not None
                    else rb.get("probability")
                )
                if s_class == "capital_chronicle"
                else None
            )
            mkt_prob = _decimal_prob(
                rb.get("market_implied_probability_pct")
                if rb.get("market_implied_probability_pct") is not None
                else rb.get("odds_pct")
                if rb.get("odds_pct") is not None
                else (
                    rb.get("probability_pct")
                    if rb.get("probability_pct") is not None
                    else rb.get("probability")
                )
                if s_class == "market_implied"
                else None
            )

            # Separate single-tick 15m deltas from rolling 1h/24h cold-start deltas (H2).
            explicit_mkt_15m_deltas = [
                d
                for field in ("market_implied_delta_15m_pp", "market_odds_delta_pp", "odds_delta_pp")
                if (d := _decimal_delta(rb.get(field))) is not None
            ]
            explicit_mkt_delta_15m = max(explicit_mkt_15m_deltas, key=abs) if explicit_mkt_15m_deltas else None
            explicit_mkt_cold_deltas = [
                *explicit_mkt_15m_deltas,
                *(
                    d
                    for field in ("market_implied_delta_1h_pp", "market_implied_delta_24h_pp")
                    if (d := _decimal_delta(rb.get(field))) is not None
                ),
            ]
            explicit_mkt_delta_cold = max(explicit_mkt_cold_deltas, key=abs) if explicit_mkt_cold_deltas else None
            explicit_cc_delta = _decimal_delta(rb.get("cc_probability_delta_pp"))
            generic_delta = _decimal_delta(rb.get("probability_shift_pp"))
            if generic_delta is not None:
                if s_class == "capital_chronicle" and explicit_cc_delta is None:
                    explicit_cc_delta = generic_delta
                elif s_class == "market_implied":
                    if explicit_mkt_delta_15m is None:
                        explicit_mkt_delta_15m = generic_delta
                    if explicit_mkt_delta_cold is None:
                        explicit_mkt_delta_cold = generic_delta

            branch_probs[branch_key] = {
                "branch_key": branch_key,
                "branch_id": bid or None,
                "kind": kind,
                "source_class": s_class,
                "cc_probability_pct": str(cc_prob) if cc_prob is not None else None,
                "market_implied_probability_pct": str(mkt_prob) if mkt_prob is not None else None,
                "explicit_cc_delta_pp": str(explicit_cc_delta) if explicit_cc_delta is not None else None,
                "explicit_market_delta_15m_pp": str(explicit_mkt_delta_15m) if explicit_mkt_delta_15m is not None else None,
                "explicit_market_delta_cold_pp": str(explicit_mkt_delta_cold) if explicit_mkt_delta_cold is not None else None,
            }
            rank_prob = cc_prob if cc_prob is not None else mkt_prob
            if rank_prob is not None and (highest_prob is None or rank_prob > highest_prob):
                highest_prob = rank_prob
                highest_kind = kind

        active_branch_id = attention._clean_text(raw.get("active_branch_id") or "") or None
        explicit_dom = raw.get("dominant_branch") or raw.get("active_branch") or raw.get("leading_branch")
        if explicit_dom:
            dominant_branch_kind = _normalize_branch_kind(explicit_dom)
        elif active_branch_id and active_branch_id in branch_id_to_kind:
            dominant_branch_kind = branch_id_to_kind[active_branch_id]
        elif highest_kind is not None:
            dominant_branch_kind = highest_kind
        else:
            dominant_branch_kind = "base"

        theme_mkt_15m_deltas = [
            d
            for val in (
                raw.get("market_odds_delta_pp"),
                raw.get("odds_shift_pp"),
                raw.get("probability_shift_pp"),
                live_state.get("max_odds_delta_15m_pp"),
            )
            if (d := _decimal_delta(val)) is not None
        ]
        theme_market_delta_15m = max(theme_mkt_15m_deltas, key=abs) if theme_mkt_15m_deltas else None
        theme_mkt_cold_deltas = [
            *theme_mkt_15m_deltas,
            *(
                d
                for val in (
                    live_state.get("max_odds_delta_1h_pp"),
                    live_state.get("max_odds_delta_24h_pp"),
                )
                if (d := _decimal_delta(val)) is not None
            ),
        ]
        theme_market_delta_cold = max(theme_mkt_cold_deltas, key=abs) if theme_mkt_cold_deltas else None
        theme_market_prob = _decimal_prob(
            raw.get("market_implied_probability_pct")
            if raw.get("market_implied_probability_pct") is not None
            else raw.get("market_odds_pct")
        )

        # Decision-point hit metadata joined with projected public decision points by id/title.
        raw_dps = raw.get("decision_points") if raw.get("decision_points") is not None else raw.get("catalysts") or []
        raw_dp_by_id: dict[str, Mapping[str, Any]] = {}
        raw_dp_by_title: dict[str, Mapping[str, Any]] = {}
        for rdp in raw_dps:
            if not isinstance(rdp, Mapping):
                continue
            dp_id = attention._clean_text(rdp.get("id") or rdp.get("event_id") or rdp.get("catalyst_id") or "")
            dp_title = attention._clean_text(rdp.get("title") or rdp.get("name") or rdp.get("event") or "")
            if dp_id:
                raw_dp_by_id[dp_id] = rdp
            if dp_title:
                raw_dp_by_title[dp_title.casefold()] = rdp

        live_flags = {
            str(f).strip().upper()
            for f in (live_state.get("material_shift_flags") or [])
            if isinstance(f, str) and f.strip()
        }
        live_dp_hit = bool(
            live_state.get("decision_point_catalyst_hit") is True
            or "DECISION_POINT_CATALYST_HIT" in live_flags
        )
        reg_as_of = attention.utc(public_register["as_of_utc"])
        reg_date_et = reg_as_of.astimezone(ET).date()
        dp_states: list[dict[str, Any]] = []
        any_individual_dp_hit = False
        for pdp in pub.get("decision_points") or []:
            rdp = raw_dp_by_id.get(pdp["id"]) or raw_dp_by_title.get(pdp["title"].casefold()) or {}
            dp_status = str(rdp.get("status") or "").strip().casefold()
            hit_at = rdp.get("hit_at_utc") or rdp.get("triggered_at_utc") or rdp.get("released_at_utc")
            hit_at_iso = attention.utc(hit_at).isoformat() if hit_at else None
            explicit_hit = bool(
                rdp.get("hit") is True
                or rdp.get("triggered") is True
                or rdp.get("outcome_confirmed") is True
                or dp_status in _HIT_DP_STATUSES
                or hit_at_iso is not None
            )
            is_future_dated = False
            if pdp.get("at_utc"):
                is_future_dated = attention.utc(pdp["at_utc"]) > reg_as_of
            elif pdp.get("scheduled_date"):
                is_future_dated = date.fromisoformat(pdp["scheduled_date"]) > reg_date_et
            if explicit_hit:
                any_individual_dp_hit = True
            dp_states.append({
                "id": pdp["id"],
                "title": pdp["title"],
                "when_et": pdp["when_et"],
                "dated": bool(pdp.get("dated")),
                "at_utc": pdp.get("at_utc"),
                "scheduled_date": pdp.get("scheduled_date"),
                "is_future_dated": is_future_dated,
                "explicit_hit": explicit_hit,
                "hit_at_utc": hit_at_iso,
                "status": dp_status or None,
            })

        # H1: When Main sets theme-level `live_state.decision_point_catalyst_hit=True` without
        # per-DP hit flags, NEVER attribute it to a future-dated meeting (e.g. 9 Dec FOMC on 24 Nov).
        # Match only: (1) explicit hit DP id in live_state (if non-future), (2) dated DP whose clock
        # fell in [as_of - 30m, as_of], or (3) a unique undated watch_condition DP; else emit a
        # theme-level catalyst signal without polluting any future dated DP id in hit_decision_point_ids.
        theme_level_catalyst_hit = False
        theme_level_catalyst_hit_marker: str | None = None
        if live_dp_hit and not any_individual_dp_hit:
            live_hit_ts = (
                attention.utc(live_state["updated_at_utc"]).isoformat()
                if live_state.get("updated_at_utc")
                else public_register["as_of_utc"]
            )
            matched_dps: list[dict[str, Any]] = []
            explicit_live_ids: set[str] = set()
            if isinstance(live_state.get("catalyst_hit_dp_id"), str) and live_state["catalyst_hit_dp_id"].strip():
                explicit_live_ids.add(attention._clean_text(live_state["catalyst_hit_dp_id"]))
            for raw_cid in live_state.get("hit_decision_point_ids") or []:
                if isinstance(raw_cid, str) and raw_cid.strip():
                    explicit_live_ids.add(attention._clean_text(raw_cid))
            if explicit_live_ids:
                matched_dps = [
                    dp for dp in dp_states
                    if dp["id"] in explicit_live_ids and not dp["is_future_dated"]
                ]
            if not matched_dps:
                win_start = reg_as_of - timedelta(minutes=DECISION_POINT_HIT_WINDOW_MINUTES)
                matched_dps = [
                    dp for dp in dp_states
                    if dp.get("at_utc") and win_start <= attention.utc(dp["at_utc"]) <= reg_as_of
                ]
            if not matched_dps:
                undated_dps = [
                    dp for dp in dp_states
                    if not dp["dated"] and dp.get("at_utc") is None and dp.get("scheduled_date") is None
                ]
                if len(undated_dps) == 1:
                    matched_dps = undated_dps
            if matched_dps:
                for dp in matched_dps:
                    dp["explicit_hit"] = True
                    dp["hit_at_utc"] = live_hit_ts
            else:
                theme_level_catalyst_hit = True
                theme_level_catalyst_hit_marker = live_hit_ts

        flip_at = (
            raw.get("branch_flip_at_utc")
            or raw.get("last_branch_flip_utc")
            or flip_evidence.get("flipped_at_utc")
        )
        flip_at_iso = attention.utc(flip_at).isoformat() if flip_at else None
        explicit_branch_flipped = bool(
            raw.get("branch_flipped") is True
            or live_state.get("branch_flip_detected") is True
            or "BRANCH_FLIP" in live_flags
        )
        raw_mat_hash = attention._clean_text(
            str(raw.get("material_change_hash") or raw_map.get("material_change_hash") or "")
        )
        if not raw_mat_hash or raw_mat_hash.startswith("pending_"):
            material_hash = pub["revision_fingerprint"]
        else:
            material_hash = raw_mat_hash
        if theme_level_catalyst_hit:
            theme_level_catalyst_hit_marker = material_hash

        themes_state[tid] = {
            "theme_id": tid,
            "rank": pub["rank"],
            "status": pub["status"],
            "active_branch_id": active_branch_id,
            "base_case_fingerprint": pub["base_case_fingerprint"],
            "base_thesis_fingerprint": base_thesis_fp,
            "branch_flip_signature": pub["branch_flip_signature"],
            "revision_fingerprint": pub["revision_fingerprint"],
            "material_change_hash": material_hash,
            "dominant_branch_kind": dominant_branch_kind,
            "explicit_branch_flipped": explicit_branch_flipped,
            "branch_flip_at_utc": flip_at_iso,
            "branch_probabilities": branch_probs,
            "theme_market_probability_pct": str(theme_market_prob) if theme_market_prob is not None else None,
            "theme_market_delta_15m_pp": str(theme_market_delta_15m) if theme_market_delta_15m is not None else None,
            "theme_market_delta_cold_pp": str(theme_market_delta_cold) if theme_market_delta_cold is not None else None,
            "live_material_shift_flags": sorted(live_flags),
            "decision_points": dp_states,
            "theme_level_catalyst_hit": theme_level_catalyst_hit,
            "theme_level_catalyst_hit_marker": theme_level_catalyst_hit_marker,
        }

    top_mat_hash = attention._clean_text(str(raw_map.get("material_change_hash") or ""))
    if not top_mat_hash or top_mat_hash.startswith("pending_"):
        top_mat_hash = public_register["register_sha256"]

    return {
        "as_of_utc": public_register["as_of_utc"],
        "material_change_hash": top_mat_hash,
        "top_theme_ids": list(public_register["top_theme_ids"]),
        "themes": themes_state,
    }


def _project_cadence_metadata(raw_meta: Any) -> dict[str, Any]:
    if not isinstance(raw_meta, Mapping):
        return {}
    projected: dict[str, Any] = {}
    for key in _SAFE_CADENCE_KEYS:
        val = raw_meta.get(key)
        if val is None:
            continue
        if key.endswith("_utc"):
            projected[key] = attention.utc(val).isoformat()
        elif isinstance(val, (int, float)) and not isinstance(val, bool):
            projected[key] = val
        elif isinstance(val, str) and val.strip():
            projected[key] = attention._clean_text(val)
    policy = raw_meta.get("cadence_policy")
    if isinstance(policy, Mapping):
        live_interval = policy.get("live_refresh_interval_minutes")
        if isinstance(live_interval, int) and not isinstance(live_interval, bool):
            projected["live_refresh_interval_minutes"] = live_interval
    return projected


def project_live_attention_map(
    raw_map: Mapping[str, Any],
    *,
    as_of_utc: Any = None,
    max_age_minutes: int | None = DEFAULT_MAX_MAP_AGE_MINUTES,
) -> dict[str, Any]:
    """Allow-list project Main's live attention map and separate internal shift-detector telemetry.

    Returns `{"public_register": ..., "detector_state": ...}`.
    `public_register` contains ZERO private book/positions/prepared responses/X-list/wire text
    and ZERO proprietary market-implied numeric probabilities.
    """
    normalized = normalize_live_map_envelope(raw_map)
    map_as_of = attention.utc(normalized["as_of_utc"])
    if as_of_utc is not None:
        now = attention.utc(as_of_utc)
        if map_as_of > now:
            raise ValueError("MARKET_FORCES_LIVE_MAP_AFTER_CUTOFF")
        if max_age_minutes is not None and (now - map_as_of) > timedelta(minutes=max_age_minutes):
            raise ValueError("MARKET_FORCES_LIVE_MAP_STALE")

    public_reg = attention.project_public_register(normalized, as_of_utc=as_of_utc)
    extra_private = _harvest_extra_private_texts(raw_map)
    merged_private = list(dict.fromkeys([*(public_reg.get("_private_texts") or []), *extra_private]))
    public_reg["_private_texts"] = merged_private

    cadence = _project_cadence_metadata(raw_map.get("cadence_metadata"))
    if cadence:
        public_reg["cadence_metadata"] = cadence

    detector_state = _extract_detector_state(raw_map, public_reg)
    return {"public_register": public_reg, "detector_state": detector_state}


def validate_poll_interval(poll_interval_minutes: int) -> int:
    if isinstance(poll_interval_minutes, bool) or not isinstance(poll_interval_minutes, int):
        raise ValueError("MARKET_FORCES_POLL_INTERVAL_INVALID")
    if not MIN_POLL_INTERVAL_MINUTES <= poll_interval_minutes <= MAX_POLL_INTERVAL_MINUTES:
        raise ValueError("MARKET_FORCES_POLL_INTERVAL_INVALID")
    return poll_interval_minutes


def validate_cooldown_minutes(cooldown_minutes: int) -> int:
    if isinstance(cooldown_minutes, bool) or not isinstance(cooldown_minutes, int):
        raise ValueError("MARKET_FORCES_COOLDOWN_INVALID")
    if cooldown_minutes < MIN_COOLDOWN_MINUTES:
        raise ValueError("MARKET_FORCES_COOLDOWN_BELOW_MINIMUM")
    return cooldown_minutes


def load_live_attention_map(
    source: Path | str | Mapping[str, Any],
    *,
    as_of_utc: Any,
    max_age_minutes: int | None = DEFAULT_MAX_MAP_AGE_MINUTES,
    poll_interval_minutes: int = DEFAULT_POLL_INTERVAL_MINUTES,
) -> dict[str, Any]:
    """Load and allow-list project Main's `market_attention_map_live_v1.json` in pure code."""
    validate_poll_interval(poll_interval_minutes)
    if isinstance(source, Mapping):
        raw_map = source
    else:
        path = Path(source)
        if path.is_dir():
            path = path / DEFAULT_LIVE_MAP_FILENAME
        if not path.is_file():
            raise FileNotFoundError(f"MARKET_FORCES_LIVE_MAP_MISSING:{path}")
        raw_map = json.loads(path.read_bytes().decode("utf-8"))
    return project_live_attention_map(raw_map, as_of_utc=as_of_utc, max_age_minutes=max_age_minutes)


# ---------------------------------------------------------------------------
# Persistent Ledger (Per-theme cooldown + exactly-once idempotency)
# ---------------------------------------------------------------------------

def empty_ledger() -> dict[str, Any]:
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "last_poll_as_of_utc": None,
        "last_map_sha256": None,
        "last_top_theme_ids": [],
        "themes": {},
        "dispatched_events": {},
        "suppressed_events": [],
    }


def load_ledger(path: Path | str) -> dict[str, Any]:
    ledger_path = Path(path)
    if not ledger_path.is_file():
        return empty_ledger()
    data = json.loads(ledger_path.read_bytes().decode("utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != LEDGER_SCHEMA_VERSION:
        raise ValueError("MARKET_FORCES_LEDGER_SCHEMA_INVALID")
    base = empty_ledger()
    base.update(data)
    return base


def save_ledger(path: Path | str, ledger: Mapping[str, Any]) -> Path:
    """Persist ledger atomically as UTF-8 LF-only canonical JSON (CR=0, BOM=False)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    encoded = (json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    tmp.write_bytes(encoded)
    os.replace(tmp, target)
    return target


def _snapshot_theme_baseline(det_theme: Mapping[str, Any], *, as_of_utc: str) -> dict[str, Any]:
    hit_ids = sorted({
        dp["id"]
        for dp in det_theme.get("decision_points") or []
        if dp.get("explicit_hit") and not dp.get("is_future_dated")
    })
    return {
        "theme_id": det_theme["theme_id"],
        "rank": det_theme["rank"],
        "status": det_theme["status"],
        "baseline_as_of_utc": as_of_utc,
        "active_branch_id": det_theme.get("active_branch_id"),
        "base_case_fingerprint": det_theme["base_case_fingerprint"],
        "base_thesis_fingerprint": det_theme["base_thesis_fingerprint"],
        "branch_flip_signature": det_theme["branch_flip_signature"],
        "revision_fingerprint": det_theme["revision_fingerprint"],
        "material_change_hash": det_theme["material_change_hash"],
        "dominant_branch_kind": det_theme["dominant_branch_kind"],
        "last_branch_flip_marker": det_theme.get("branch_flip_at_utc") or (
            det_theme["material_change_hash"] if det_theme.get("explicit_branch_flipped") else None
        ),
        "branch_probabilities": det_theme["branch_probabilities"],
        "theme_market_probability_pct": det_theme.get("theme_market_probability_pct"),
        "hit_decision_point_ids": hit_ids,
        "last_theme_catalyst_hit_marker": det_theme.get("theme_level_catalyst_hit_marker")
        if det_theme.get("theme_level_catalyst_hit")
        else None,
        "last_dispatched_at_utc": None,
        "last_dispatched_event_key": None,
        "latest_page": None,
    }


def seed_ledger_from_map(
    source: Path | str | Mapping[str, Any],
    *,
    as_of_utc: Any,
    ledger_path: Path | str | None = None,
    prior_pages: Mapping[str, Mapping[str, Any]] | None = None,
    max_age_minutes: int | None = DEFAULT_MAX_MAP_AGE_MINUTES,
) -> dict[str, Any]:
    """Baseline the high-interval ledger from an existing live map without emitting flashes."""
    projected = load_live_attention_map(source, as_of_utc=as_of_utc, max_age_minutes=max_age_minutes)
    public_reg = projected["public_register"]
    det = projected["detector_state"]
    ledger = load_ledger(ledger_path) if ledger_path else empty_ledger()
    ledger["last_poll_as_of_utc"] = public_reg["as_of_utc"]
    ledger["last_map_sha256"] = public_reg["register_sha256"]
    ledger["last_top_theme_ids"] = list(public_reg["top_theme_ids"])
    prior_pages = prior_pages or {}
    for tid, det_theme in det["themes"].items():
        entry = _snapshot_theme_baseline(det_theme, as_of_utc=public_reg["as_of_utc"])
        if tid in prior_pages:
            entry["latest_page"] = dict(prior_pages[tid])
        elif tid in ledger["themes"] and ledger["themes"][tid].get("latest_page"):
            entry["latest_page"] = ledger["themes"][tid]["latest_page"]
        ledger["themes"][tid] = entry
    if ledger_path is not None:
        save_ledger(ledger_path, ledger)
    return ledger


# ---------------------------------------------------------------------------
# Material-Shift Detector (Pure Code, Zero LLM Calls)
# ---------------------------------------------------------------------------

def _public_prob_shift_sentence(
    *,
    source_class: str,
    branch_kind: str | None,
    direction: str,
    magnitude_word: str,
    own_new_pct: Decimal | None = None,
) -> str:
    """Describe a >= 10 pp probability shift cleanly.

    CRITICAL COMPLIANCE RULE (Decision 44 / CC-788 / CC-817):
    - Market-implied shifts (`kalshi`, `polymarket`, `fedwatch`, `options`, `futures`)
      are rendered STRICTLY IN WORDS: zero percentage digits, zero `pp` numbers,
      zero prediction-market or FedWatch names.
    - Own Capital Chronicle shifts describe the direction in words and trace the
      new percentage explicitly to our labelled Capital Chronicle estimate.
    """
    if branch_kind is None:
        if source_class == "capital_chronicle":
            return f"Capital Chronicle's scenario probabilities shifted {magnitude_word} {direction}."
        return f"Market-implied pricing for this market force shifted {magnitude_word} {direction}."
    _, branch_label = attention._BRANCH_KIND_MAP.get(branch_kind, ("alternative", "Alternative case"))
    scenario_phrase = branch_label.lower()
    if source_class == "capital_chronicle":
        if own_new_pct is not None:
            pct_str = attention._format_probability(
                int(own_new_pct) if own_new_pct == int(own_new_pct) else float(own_new_pct)
            )
            return (
                f"Capital Chronicle's estimate for the {scenario_phrase} shifted "
                f"{magnitude_word} {direction} to {pct_str}%."
            )
        return f"Capital Chronicle's estimate for the {scenario_phrase} shifted {magnitude_word} {direction}."
    return f"Market-implied pricing on the {scenario_phrase} shifted {magnitude_word} {direction}."


def detect_material_shifts(
    projected: Mapping[str, Any],
    ledger: Mapping[str, Any] | None = None,
    *,
    prior_pages: Mapping[str, Mapping[str, Any]] | None = None,
    top_five_only: bool = True,
) -> list[dict[str, Any]]:
    """Pure-code detector for material intraday shifts across the live attention map.

    Triggers ONLY on:
      1. `NEW_TOP_FIVE_ENTRY`
      2. `BRANCH_FLIPPED` (bypasses per-theme 2-hour cooldown)
      3. `PROBABILITY_SHIFT_GE_10PP` (>= 10 pp own or market-implied shift; market-implied rendered in words)
      4. `DECISION_POINT_CATALYST_HIT` (explicitly hit/triggered or scheduled clock crossed)
    """
    public_reg = projected["public_register"]
    det = projected["detector_state"]
    ledger = ledger or empty_ledger()
    prior_pages = prior_pages or {}

    curr_as_of = attention.utc(public_reg["as_of_utc"])
    prev_poll_raw = ledger.get("last_poll_as_of_utc")
    prev_poll_as_of = attention.utc(prev_poll_raw) if prev_poll_raw else None

    known_top_ids = set(ledger.get("last_top_theme_ids") or []) | set(prior_pages.keys())
    top_ids = set(public_reg["top_theme_ids"])
    theme_ledger = ledger.get("themes") or {}
    pub_by_id = {t["theme_id"]: t for t in public_reg["themes"]}

    shifts: list[dict[str, Any]] = []
    for pub_theme in public_reg["themes"]:
        if pub_theme["status"] not in attention.LIVE_STATUSES:
            continue
        tid = pub_theme["theme_id"]
        in_top_five = tid in top_ids
        prev_state = theme_ledger.get(tid)
        has_prior_page = bool(prior_pages.get(tid) or (prev_state and prev_state.get("latest_page")))
        if top_five_only and not in_top_five and not has_prior_page:
            continue

        det_theme = det["themes"][tid]
        reasons: list[str] = []
        shift_details: dict[str, Any] = {}
        public_lines: list[str] = []

        # 1. New Top-5 entry
        if in_top_five and tid not in known_top_ids:
            reasons.append(TRIGGER_NEW_TOP_FIVE)
            public_lines.append("This market force entered Capital Chronicle's top five watched themes.")

        # 2. Scenario branch flip
        branch_flipped = False
        if prev_state is not None:
            curr_active = det_theme.get("active_branch_id")
            prev_active = prev_state.get("active_branch_id")
            if curr_active and prev_active and curr_active != prev_active:
                branch_flipped = True
                shift_details["branch_flip_kind"] = "ACTIVE_BRANCH_ID_CHANGED"
            elif det_theme["dominant_branch_kind"] != prev_state.get("dominant_branch_kind"):
                branch_flipped = True
                shift_details["branch_flip_kind"] = "DOMINANT_BRANCH_CHANGED"
            elif det_theme["base_thesis_fingerprint"] != prev_state.get("base_thesis_fingerprint"):
                branch_flipped = True
                shift_details["branch_flip_kind"] = "BASE_THESIS_FLIPPED"
        if det_theme.get("explicit_branch_flipped"):
            flip_marker = det_theme.get("branch_flip_at_utc") or det_theme["material_change_hash"]
            prev_marker = prev_state.get("last_branch_flip_marker") if prev_state else None
            if flip_marker != prev_marker:
                branch_flipped = True
                shift_details.setdefault("branch_flip_kind", "EXPLICIT_BRANCH_FLIP")
        if branch_flipped:
            reasons.append(TRIGGER_BRANCH_FLIPPED)
            public_lines.append("The primary scenario path flipped for this market force.")

        # 3. >= 10 pp probability shift (own Capital Chronicle estimate OR market-implied odds)
        # Keyed per branch_id (M1) and baselined cleanly against stored branch probabilities (H2)
        # so rolling 24h live_state deltas never spam flashes on unchanged themes or +1 pp wiggles.
        best_shift: dict[str, Any] | None = None
        curr_branch_probs = det_theme.get("branch_probabilities") or {}
        prev_branch_probs = (prev_state or {}).get("branch_probabilities") or {}
        any_curr_branch_mkt = any(
            b.get("market_implied_probability_pct") is not None for b in curr_branch_probs.values()
        )
        has_branch_mkt_baseline = False
        for branch_key, curr_b in curr_branch_probs.items():
            kind = curr_b.get("kind") or _normalize_branch_kind(branch_key.split("#", 1)[0])
            prev_b = prev_branch_probs.get(branch_key)
            if prev_b is None and not curr_b.get("branch_id"):
                prev_b = prev_branch_probs.get(kind)
            prev_b = prev_b or {}

            # 3a. Check Capital Chronicle own estimate delta
            curr_cc = _decimal_prob(
                Decimal(curr_b["cc_probability_pct"]) if curr_b.get("cc_probability_pct") is not None else None
            )
            prev_cc = _decimal_prob(
                Decimal(prev_b["cc_probability_pct"]) if prev_b.get("cc_probability_pct") is not None else None
            )
            cc_delta: Decimal | None = None
            if curr_cc is not None and prev_cc is not None:
                cc_delta = curr_cc - prev_cc
            elif prev_state is None and curr_b.get("explicit_cc_delta_pp") is not None:
                cc_delta = _decimal_delta(Decimal(curr_b["explicit_cc_delta_pp"]))
            if cc_delta is not None and abs(cc_delta) >= PROBABILITY_SHIFT_THRESHOLD_PP:
                cand = {
                    "branch_key": branch_key,
                    "branch_id": curr_b.get("branch_id"),
                    "branch_kind": kind,
                    "source_class": "capital_chronicle",
                    "abs_delta_pp": abs(cc_delta),
                    "direction": "higher" if cc_delta > 0 else "lower",
                    "magnitude_word": "sharply" if abs(cc_delta) >= SHARP_SHIFT_THRESHOLD_PP else "materially",
                    "own_new_pct": curr_cc,
                    "delta_bucket": f"{branch_key}:capital_chronicle:{'up' if cc_delta > 0 else 'down'}:{int(abs(cc_delta))}",
                }
                if best_shift is None or cand["abs_delta_pp"] > best_shift["abs_delta_pp"]:
                    best_shift = cand

            # 3b. Check market-implied odds delta per branch (strictly rendered in words!)
            curr_mkt = _decimal_prob(
                Decimal(curr_b["market_implied_probability_pct"])
                if curr_b.get("market_implied_probability_pct") is not None
                else None
            )
            prev_mkt = _decimal_prob(
                Decimal(prev_b["market_implied_probability_pct"])
                if prev_b.get("market_implied_probability_pct") is not None
                else None
            )
            mkt_delta: Decimal | None = None
            if curr_mkt is not None and prev_mkt is not None:
                has_branch_mkt_baseline = True
                mkt_delta = curr_mkt - prev_mkt
            elif prev_state is None and curr_b.get("explicit_market_delta_cold_pp") is not None:
                mkt_delta = _decimal_delta(Decimal(curr_b["explicit_market_delta_cold_pp"]))
            elif curr_mkt is None and curr_b.get("explicit_market_delta_15m_pp") is not None:
                mkt_delta = _decimal_delta(Decimal(curr_b["explicit_market_delta_15m_pp"]))
            if mkt_delta is not None and abs(mkt_delta) >= PROBABILITY_SHIFT_THRESHOLD_PP:
                cand = {
                    "branch_key": branch_key,
                    "branch_id": curr_b.get("branch_id"),
                    "branch_kind": kind,
                    "source_class": "market_implied",
                    "abs_delta_pp": abs(mkt_delta),
                    "direction": "higher" if mkt_delta > 0 else "lower",
                    "magnitude_word": "sharply" if abs(mkt_delta) >= SHARP_SHIFT_THRESHOLD_PP else "materially",
                    "own_new_pct": None,
                    "delta_bucket": f"{branch_key}:market_implied:{'up' if mkt_delta > 0 else 'down'}:{int(abs(mkt_delta))}",
                }
                if best_shift is None or cand["abs_delta_pp"] > best_shift["abs_delta_pp"]:
                    best_shift = cand

        # 3c. Theme-level market-implied odds fallback (ONLY when branch-level probabilities are absent;
        # never falls back to rolling 24h deltas once a baseline exists, and never mislabels as base case!).
        curr_tm = (
            Decimal(det_theme["theme_market_probability_pct"])
            if det_theme.get("theme_market_probability_pct") is not None
            else None
        )
        prev_tm = (
            Decimal(prev_state["theme_market_probability_pct"])
            if prev_state and prev_state.get("theme_market_probability_pct") is not None
            else None
        )
        tm_delta: Decimal | None = None
        if curr_tm is not None and prev_tm is not None:
            tm_delta = curr_tm - prev_tm
        elif not has_branch_mkt_baseline and not any_curr_branch_mkt:
            if prev_state is None and det_theme.get("theme_market_delta_cold_pp") is not None:
                tm_delta = _decimal_delta(Decimal(det_theme["theme_market_delta_cold_pp"]))
            elif prev_state is not None and det_theme.get("theme_market_delta_15m_pp") is not None:
                tm_delta = _decimal_delta(Decimal(det_theme["theme_market_delta_15m_pp"]))
        if tm_delta is not None and abs(tm_delta) >= PROBABILITY_SHIFT_THRESHOLD_PP:
            cand = {
                "branch_key": "theme",
                "branch_id": None,
                "branch_kind": None,
                "source_class": "market_implied",
                "abs_delta_pp": abs(tm_delta),
                "direction": "higher" if tm_delta > 0 else "lower",
                "magnitude_word": "sharply" if abs(tm_delta) >= SHARP_SHIFT_THRESHOLD_PP else "materially",
                "own_new_pct": None,
                "delta_bucket": f"theme:market_implied:{'up' if tm_delta > 0 else 'down'}:{int(abs(tm_delta))}",
            }
            if best_shift is None or cand["abs_delta_pp"] > best_shift["abs_delta_pp"]:
                best_shift = cand

        if best_shift is not None:
            reasons.append(TRIGGER_PROBABILITY_SHIFT)
            shift_details["probability_shift_source_class"] = best_shift["source_class"]
            shift_details["probability_shift_direction"] = best_shift["direction"]
            shift_details["probability_shift_branch_kind"] = best_shift["branch_kind"]
            shift_details["probability_shift_branch_id"] = best_shift["branch_id"]
            shift_details["probability_shift_bucket"] = best_shift["delta_bucket"]
            public_lines.append(
                _public_prob_shift_sentence(
                    source_class=best_shift["source_class"],
                    branch_kind=best_shift["branch_kind"],
                    direction=best_shift["direction"],
                    magnitude_word=best_shift["magnitude_word"],
                    own_new_pct=best_shift["own_new_pct"],
                )
            )

        # 4. Decision-point catalyst hit (H1: never falsely mark future-dated meetings as hit!)
        already_hit = set((prev_state or {}).get("hit_decision_point_ids") or [])
        newly_hit_dps: list[dict[str, Any]] = []
        for dp in det_theme.get("decision_points") or []:
            dp_id = dp["id"]
            if dp_id in already_hit:
                continue
            hit = False
            if dp.get("explicit_hit") and not dp.get("is_future_dated"):
                hit_at = attention.utc(dp["hit_at_utc"]) if dp.get("hit_at_utc") else None
                if hit_at is None or hit_at <= curr_as_of:
                    hit = True
            elif dp.get("at_utc"):
                dp_time = attention.utc(dp["at_utc"])
                if prev_poll_as_of is not None:
                    if prev_poll_as_of < dp_time <= curr_as_of:
                        hit = True
                else:
                    window_start = curr_as_of - timedelta(minutes=DECISION_POINT_HIT_WINDOW_MINUTES)
                    if window_start <= dp_time <= curr_as_of:
                        hit = True
            if hit:
                newly_hit_dps.append({"id": dp_id, "title": dp["title"], "when_et": dp["when_et"]})

        theme_catalyst_marker: str | None = None
        if newly_hit_dps:
            reasons.append(TRIGGER_CATALYST_HIT)
            shift_details["hit_decision_points"] = newly_hit_dps
            for dp in newly_hit_dps:
                public_lines.append(
                    f"Tracked decision point reached: {dp['title'].rstrip('.')} ({dp['when_et']})."
                )
        elif det_theme.get("theme_level_catalyst_hit"):
            marker = det_theme.get("theme_level_catalyst_hit_marker") or det_theme["material_change_hash"]
            prev_cat_marker = (prev_state or {}).get("last_theme_catalyst_hit_marker")
            if marker != prev_cat_marker:
                reasons.append(TRIGGER_CATALYST_HIT)
                theme_catalyst_marker = marker
                shift_details["theme_level_catalyst_hit_marker"] = marker
                public_lines.append("A tracked catalyst watch condition triggered for this theme.")

        if not reasons:
            continue

        ordered_reasons = [r for r in TRIGGER_PRIORITY if r in reasons]
        primary_reason = ordered_reasons[0]
        idempotency_payload = {
            "theme_id": tid,
            "primary_reason": primary_reason,
            "reasons": ordered_reasons,
            "revision_fingerprint": pub_theme["revision_fingerprint"],
            "material_change_hash": det_theme["material_change_hash"],
            "hit_dp_ids": sorted(dp["id"] for dp in newly_hit_dps),
            "theme_catalyst_marker": theme_catalyst_marker,
            "shift_bucket": shift_details.get("probability_shift_bucket"),
        }
        event_key = sha256_of(idempotency_payload)

        shifts.append({
            "event_key": event_key,
            "theme_id": tid,
            "theme_name": pub_theme["name"],
            "rank": pub_theme["rank"],
            "primary_reason": primary_reason,
            "reasons": ordered_reasons,
            "bypasses_cooldown": TRIGGER_BRANCH_FLIPPED in ordered_reasons,
            "public_summary_lines": public_lines,
            "hit_decision_point_ids": [dp["id"] for dp in newly_hit_dps],
            "theme_catalyst_marker": theme_catalyst_marker,
            "shift_details": shift_details,
            "as_of_utc": public_reg["as_of_utc"],
            "public_theme": pub_by_id[tid],
        })

    shifts.sort(key=lambda item: (TRIGGER_PRIORITY.index(item["primary_reason"]), item["rank"], item["theme_id"]))
    return shifts


# ---------------------------------------------------------------------------
# Intraday Market Force Flash / Update Page & 10-Platform Short Social Copy
# ---------------------------------------------------------------------------

def _reason_headline_tag(primary_reason: str) -> str:
    return {
        TRIGGER_BRANCH_FLIPPED: "Scenario flip",
        TRIGGER_NEW_TOP_FIVE: "New top-five theme",
        TRIGGER_CATALYST_HIT: "Catalyst reached",
        TRIGGER_PROBABILITY_SHIFT: "Scenario shift",
    }.get(primary_reason, "Intraday update")


def render_market_force_flash(
    public_theme: Mapping[str, Any],
    shift_event: Mapping[str, Any],
    *,
    as_of_utc: Any,
    previous_page: Mapping[str, Any] | None = None,
    chart_asset: Mapping[str, Any] | None = None,
    private_texts: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Render one immutable dated WEB_ONLY Substack flash page linking any prior edition."""
    stamp = attention.utc(as_of_utc)
    day_et = stamp.astimezone(ET).date().isoformat()
    date_label = public_date(stamp)
    clock_et = et(stamp)
    theme_id = public_theme["theme_id"]
    lead_market = public_theme.get("lead_market")
    if not lead_market or lead_market not in tv.SYMBOLS:
        raise ValueError("ATTENTION_MAP_LEAD_MARKET_REQUIRED:" + theme_id)

    title = f"{public_theme['name']} — intraday scenario update ({date_label})"
    subtitle = public_theme["one_line"].rstrip(".") + "."
    extra_sources: list[str] = [
        date_label,
        clock_et,
        attention.PUBLIC_MARKET_LABELS[lead_market],
        tv.NAMES[lead_market],
    ]
    for m in public_theme.get("affected_markets") or []:
        if m in attention.PUBLIC_MARKET_LABELS:
            extra_sources.append(attention.PUBLIC_MARKET_LABELS[m])

    paragraphs: list[str] = [
        f"{subtitle} Updated {clock_et}. Theme state: {public_theme['status']}.",
    ]
    previous_url = None
    if previous_page:
        previous_url = str(previous_page.get("canonical_url") or "")
        if not previous_url or find_forbidden_link(previous_url):
            raise ValueError("ATTENTION_MAP_PREVIOUS_PAGE_URL_INVALID")
        prior_at = previous_page.get("published_at_utc") or previous_page.get("as_of_utc")
        prior_label = public_date(attention.utc(prior_at)) if prior_at else "earlier edition"
        extra_sources.append(prior_label)
        paragraphs.append(
            f"Earlier edition ({prior_label}): {previous_url}. Earlier scenario pages remain unchanged."
        )

    shift_lines = [
        f"- {attention._clean_text(line).rstrip('.')}."
        for line in (shift_event.get("public_summary_lines") or [])
        if attention._clean_text(line)
    ]
    if not shift_lines:
        shift_lines = ["- Scenario register updated on new market evidence."]
    paragraphs.extend(["## What shifted", "\n".join(shift_lines)])

    scenario_lines: list[str] = []
    for branch in public_theme["branches"]:
        scenario_lines.append(attention._branch_line(branch))
        scenario_lines.append(
            f"What would prove the {branch['label'].lower()} wrong: {branch['invalidation'].rstrip('.')}."
        )
    if public_theme.get("market_lean_words"):
        scenario_lines.append(f"Market lean: {public_theme['market_lean_words'].rstrip('.')}.")
    paragraphs.extend(["## Scenarios", *scenario_lines])

    chain_lines = [
        f"- {chain['market_label']}: {chain['event'].rstrip('.')} -> "
        f"{chain['channel'].rstrip('.')} ({chain['sign']}; {chain['rough_size'].rstrip('.')})."
        for chain in (public_theme.get("causal_chains") or [])
    ]
    covered_in_chains = {c["market"] for c in (public_theme.get("causal_chains") or [])}
    for market in public_theme.get("affected_markets") or [lead_market]:
        if market in attention.PUBLIC_MARKET_LABELS and market not in covered_in_chains:
            chain_lines.append(
                f"- {attention.PUBLIC_MARKET_LABELS[market]}: tracked market exposure for this theme."
            )
    if not chain_lines:
        chain_lines.append(f"- {attention.PUBLIC_MARKET_LABELS[lead_market]}: primary market for this theme.")
    paragraphs.extend(["## How it reaches our markets", "\n".join(chain_lines)])

    priced_lines: list[str] = []
    if public_theme.get("priced_in_words"):
        priced_lines.append(public_theme["priced_in_words"].rstrip(".") + ".")
    else:
        priced_lines.append("Market pricing is described qualitatively; no third-party odds numbers are quoted.")
    for metric in public_theme.get("computed_metrics") or []:
        priced_lines.append(f"- {metric['label']}: {metric['value']}.")
    paragraphs.extend(["## What is priced in", "\n".join(priced_lines)])

    dp_lines: list[str] = []
    for dp in public_theme.get("decision_points") or []:
        line = f"- {dp['when_et']} — {dp['title'].rstrip('.')}."
        if dp.get("watch_signals"):
            labels = ", ".join(sig["label"] for sig in dp["watch_signals"])
            line += f" Watch signals: {labels}."
        dp_lines.append(line)
    if not dp_lines:
        dp_lines.append("- No dated decision point is currently scheduled.")
    paragraphs.extend(["## Decision points and watch signals", "\n".join(dp_lines)])

    history_lines = [
        f"- {row['date_et']}: {row['summary'].rstrip('.')}."
        for row in (public_theme.get("history") or [])
    ] or [f"- {public_theme['first_seen_et']}: Theme first added to the map."]
    paragraphs.extend(["## History of changes", "\n".join(history_lines)])

    paragraphs.extend([
        f"{tv.CREDIT} ({tv.NAMES[lead_market]}).",
        PUBLIC_NOTICE,
        CONFLICTS_NOTICE,
    ])
    body = "\n\n".join(paragraphs)

    media_assets: list[dict[str, Any]] = []
    if chart_asset is not None:
        tv.validate_snapshot_asset(chart_asset, {"market_asset": lead_market})
        media_assets.append(dict(chart_asset))

    article = {
        "title": title,
        "subtitle": subtitle,
        "body_markdown": body,
        "market_asset": lead_market,
        "public_instrument_policy": instruments.POLICY,
    }
    full_text = "\n\n".join([title, subtitle, body])
    attention.validate_attention_map_copy(
        full_text,
        public_theme=public_theme,
        require_notice=True,
        private_texts=private_texts,
        extra_allowed_sources=tuple(extra_sources),
    )
    instruments.validate_article(article)

    event_key = str(shift_event.get("event_key") or public_theme["revision_fingerprint"])
    page_id = f"attention-flash-{theme_id}-{day_et}-{event_key[:10]}"
    return {
        "schema_version": FLASH_PAGE_SCHEMA_VERSION,
        "page_id": page_id,
        "event_key": event_key,
        "theme_id": theme_id,
        "theme_name": public_theme["name"],
        "as_of_utc": stamp.isoformat(),
        "date_et": date_label,
        "clock_et": clock_et,
        "primary_reason": shift_event.get("primary_reason") or TRIGGER_PROBABILITY_SHIFT,
        "reasons": list(shift_event.get("reasons") or []),
        "flash_update": True,
        "web_only": True,
        "send_email": False,
        "never_edit": True,
        "previous_page_id": previous_page.get("page_id") if previous_page else None,
        "previous_page_url": previous_url,
        "lead_market": lead_market,
        "chart_requirement": {
            "market_asset": lead_market,
            "tv_symbol": tv.SYMBOLS[lead_market],
            "policy": "CC463_TRADINGVIEW_FIRST_V1",
            "credit": tv.CREDIT,
        },
        "revision_fingerprint": public_theme["revision_fingerprint"],
        "base_case_fingerprint": public_theme["base_case_fingerprint"],
        "branch_flip_signature": public_theme["branch_flip_signature"],
        "native_payload": {"title": title, "subtitle": subtitle, "body_markdown": body},
        "media_assets": media_assets,
    }


def register_flash_page(store, flash_packet: Mapping[str, Any], *, output_dir: Path) -> dict[str, Any]:
    """Persist an immutable WEB_ONLY Substack flash page in ContentOpsDurableStore."""
    return attention.register_theme_page(store, flash_packet, output_dir=output_dir)


def render_flash_social_copy(
    public_theme: Mapping[str, Any],
    shift_event: Mapping[str, Any],
    canonical_url: str,
    *,
    destination: str,
    as_of_utc: Any,
    credit: str = tv.CREDIT,
    media_asset_ids: list[str] | tuple[str, ...] = (),
    private_texts: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Render concise short social copy for one of the 10 platforms with zero truncation."""
    if not canonical_url or find_forbidden_link(canonical_url):
        raise ValueError("PREVIEW_HOST_LINK_FORBIDDEN")
    if destination not in attention._PLATFORM_LIMITS:
        raise ValueError("MARKET_FORCES_SOCIAL_DESTINATION_INVALID:" + str(destination))

    stamp = attention.utc(as_of_utc)
    clock_et = et(stamp)
    limit = attention._PLATFORM_LIMITS[destination]
    tag = _reason_headline_tag(str(shift_event.get("primary_reason") or ""))
    shift_line = (
        attention._clean_text(shift_event["public_summary_lines"][0]).rstrip(".") + "."
        if shift_event.get("public_summary_lines")
        else "Scenario map updated on new evidence."
    )
    base = next(b for b in public_theme["branches"] if b["kind"] == "base")
    base_line = attention._branch_line(base)
    lead_market = public_theme.get("lead_market")
    market_short = attention.SHORT_MARKET_LABELS.get(lead_market, "")
    credit_suffix = f" {credit.strip().rstrip('.')}." if credit and credit.strip() else ""
    notices = f"{PUBLIC_NOTICE}\n{CONFLICTS_NOTICE}"
    media_ids = list(media_asset_ids)

    lead_compact = f"{tag} — {public_theme['name']}: {shift_line}"
    lead_with_clock = f"{tag} ({clock_et}) — {public_theme['name']}: {shift_line}"
    lead_minimal = f"{tag}: {public_theme['name']}."
    if market_short and market_short.casefold() not in lead_minimal.casefold():
        market_note = f"Key market: {attention.PUBLIC_MARKET_LABELS[lead_market]}."
    else:
        market_note = ""

    extra_sources = (
        clock_et,
        credit_suffix,
        attention.PUBLIC_MARKET_LABELS.get(lead_market, ""),
    )

    if destination == "x":
        from .plan_status_posts_v1 import _x_length

        root_candidates = [
            f"{lead_with_clock}\n{base_line}{credit_suffix}",
            f"{lead_compact}\n{base_line}{credit_suffix}",
            f"{lead_with_clock}{credit_suffix}",
            f"{lead_compact}{credit_suffix}",
            f"{lead_minimal}{credit_suffix}",
        ]
        root = next((cand for cand in root_candidates if _x_length(cand) <= 280), None)
        if root is None:
            raise ValueError("MARKET_FORCES_FLASH_SOCIAL_COPY_EXCEEDS_LIMIT:x")
        reply_link = f"{canonical_url}\n\n{notices}"
        if _x_length(reply_link) > 280:
            raise ValueError("MARKET_FORCES_FLASH_SOCIAL_COPY_EXCEEDS_LIMIT:x")
        texts = [root, reply_link]
        if base_line not in root and _x_length(base_line) <= 280:
            texts.append(base_line)
        elif market_note and market_note not in root and _x_length(market_note) <= 280:
            texts.append(market_note)
        full_text = "\n\n".join(texts)
        if _ELLIPSIS.search(full_text):
            raise ValueError("MARKET_FORCES_TRUNCATION_FORBIDDEN")
        attention.validate_attention_map_copy(
            full_text,
            public_theme=public_theme,
            require_notice=True,
            private_texts=private_texts,
            extra_allowed_sources=extra_sources,
        )
        payload = {
            "destination": destination,
            "format": "thread",
            "text": texts[0],
            "root_text": texts[0],
            "reply_texts": texts[1:],
            "full_text": full_text,
            "posts": [
                {"order": i, "role": "reply" if i else "root", "text": t, "media_asset_ids": [] if i else media_ids}
                for i, t in enumerate(texts)
            ],
            "media_asset_ids": media_ids,
            "platform_limit": limit,
            "hard_truncation_used": False,
        }
        instruments.validate_payload({"public_instrument_policy": instruments.POLICY}, payload)
        return payload

    rich_parts = [lead_with_clock, base_line]
    if market_note:
        rich_parts.append(market_note)
    candidates = [
        "\n".join(rich_parts) + credit_suffix + f"\n\n{canonical_url}\n\n{notices}",
        f"{lead_with_clock}\n{base_line}{credit_suffix}\n\n{canonical_url}\n\n{notices}",
        f"{lead_compact}\n{base_line}{credit_suffix}\n\n{canonical_url}\n\n{notices}",
        f"{lead_with_clock}{credit_suffix}\n\n{canonical_url}\n\n{notices}",
        f"{lead_compact}{credit_suffix}\n\n{canonical_url}\n\n{notices}",
        f"{lead_minimal}{credit_suffix}\n\n{canonical_url}\n\n{notices}",
    ]
    full = next((cand for cand in candidates if len(cand) <= limit), None)
    if full is None:
        raise ValueError("MARKET_FORCES_FLASH_SOCIAL_COPY_EXCEEDS_LIMIT:" + destination)
    if _ELLIPSIS.search(full):
        raise ValueError("MARKET_FORCES_TRUNCATION_FORBIDDEN")
    attention.validate_attention_map_copy(
        full,
        public_theme=public_theme,
        require_notice=True,
        private_texts=private_texts,
        extra_allowed_sources=extra_sources,
    )
    payload = {
        "destination": destination,
        "format": "market_force_flash_social",
        "text": full,
        "full_text": full,
        "media_asset_ids": media_ids,
        "platform_limit": limit,
        "hard_truncation_used": False,
    }
    instruments.validate_payload({"public_instrument_policy": instruments.POLICY}, payload)
    return payload


def render_flash_social_bundle(
    public_theme: Mapping[str, Any],
    shift_event: Mapping[str, Any],
    canonical_url: str,
    *,
    as_of_utc: Any,
    destinations: tuple[str, ...] = ALL_TEN_DESTINATIONS,
    credit: str = tv.CREDIT,
    media_asset_ids: list[str] | tuple[str, ...] = (),
    private_texts: tuple[str, ...] | list[str] = (),
) -> dict[str, dict[str, Any]]:
    """Render validated concise short social copy across all 10 platforms without truncation."""
    return {
        dest: render_flash_social_copy(
            public_theme,
            shift_event,
            canonical_url,
            destination=dest,
            as_of_utc=as_of_utc,
            credit=credit,
            media_asset_ids=media_asset_ids,
            private_texts=private_texts,
        )
        for dest in destinations
    }


# ---------------------------------------------------------------------------
# High-Interval Pure-Code Poller (15-30m Cadence, Cooldown & Idempotency)
# ---------------------------------------------------------------------------

def poll_live_attention_map(
    source: Path | str | Mapping[str, Any],
    *,
    now_utc: Any,
    ledger_path: Path | str | None = None,
    ledger: dict[str, Any] | None = None,
    prior_pages: Mapping[str, Mapping[str, Any]] | None = None,
    poll_interval_minutes: int = DEFAULT_POLL_INTERVAL_MINUTES,
    cooldown_minutes: int = DEFAULT_COOLDOWN_MINUTES,
    max_age_minutes: int | None = DEFAULT_MAX_MAP_AGE_MINUTES,
    top_five_only: bool = True,
    store=None,
    output_dir: Path | str | None = None,
    chart_asset_provider: Callable[[Mapping[str, Any]], Mapping[str, Any] | None] | None = None,
    canonical_url_builder: Callable[[Mapping[str, Any]], str] | None = None,
) -> dict[str, Any]:
    """Run one 15-30 minute pure-code poll cycle (zero LLM calls, zero live publishing).

    Enforces:
      - Allow-list projection and freshness check on `market_attention_map_live_v1.json`,
      - Material-shift detection (4 triggers only),
      - Exactly-once idempotency ledger check,
      - Per-theme anti-spam cooldown (>= 2h unless `BRANCH_FLIPPED`),
      - Immutable dated WEB_ONLY flash page + optional 10-platform short social bundle.
    """
    validate_poll_interval(poll_interval_minutes)
    validate_cooldown_minutes(cooldown_minutes)
    now = attention.utc(now_utc)

    active_ledger = (
        ledger
        if ledger is not None
        else load_ledger(ledger_path)
        if ledger_path is not None
        else empty_ledger()
    )

    projected = load_live_attention_map(
        source,
        as_of_utc=now,
        max_age_minutes=max_age_minutes,
        poll_interval_minutes=poll_interval_minutes,
    )
    public_reg = projected["public_register"]
    det = projected["detector_state"]
    prior_pages = prior_pages or {}
    private_texts = public_reg.get("_private_texts") or []

    shifts = detect_material_shifts(
        projected,
        active_ledger,
        prior_pages=prior_pages,
        top_five_only=top_five_only,
    )

    emitted_flashes: list[dict[str, Any]] = []
    suppressed_cooldown: list[dict[str, Any]] = []
    skipped_duplicates: list[dict[str, Any]] = []
    cooldown_seconds = cooldown_minutes * 60

    dispatched_theme_ids: set[str] = set()
    suppressed_theme_ids: set[str] = set()

    for shift in shifts:
        tid = shift["theme_id"]
        event_key = shift["event_key"]
        theme_entry = active_ledger["themes"].get(tid) or {}

        # 1. Exactly-once idempotency check
        if event_key in active_ledger["dispatched_events"]:
            skipped_duplicates.append({
                "theme_id": tid,
                "event_key": event_key,
                "primary_reason": shift["primary_reason"],
                "reason": "DUPLICATE_ALREADY_DISPATCHED",
                "prior_page_id": active_ledger["dispatched_events"][event_key]["page_id"],
            })
            continue

        # 2. Per-theme anti-spam cooldown (>= 2h unless BRANCH_FLIPPED)
        last_sent_raw = theme_entry.get("last_dispatched_at_utc")
        cooldown_bypassed = False
        if last_sent_raw:
            last_sent = attention.utc(last_sent_raw)
            elapsed = (now - last_sent).total_seconds()
            if elapsed < cooldown_seconds:
                if shift["bypasses_cooldown"]:
                    cooldown_bypassed = True
                else:
                    remaining = max(0, int(cooldown_seconds - elapsed))
                    next_eligible = (last_sent + timedelta(seconds=cooldown_seconds)).isoformat()
                    record = {
                        "theme_id": tid,
                        "event_key": event_key,
                        "primary_reason": shift["primary_reason"],
                        "reasons": shift["reasons"],
                        "status": "COOLDOWN_SUPPRESSED",
                        "suppressed_at_utc": now.isoformat(),
                        "cooldown_remaining_seconds": remaining,
                        "next_eligible_utc": next_eligible,
                    }
                    suppressed_cooldown.append(record)
                    active_ledger["suppressed_events"].append(record)
                    active_ledger["suppressed_events"] = active_ledger["suppressed_events"][-200:]
                    suppressed_theme_ids.add(tid)
                    continue

        # 3. Render immutable WEB_ONLY flash page (linking prior page if any)
        prev_page = theme_entry.get("latest_page") or prior_pages.get(tid)
        chart_asset = chart_asset_provider(shift["public_theme"]) if chart_asset_provider else None
        flash_page = render_market_force_flash(
            shift["public_theme"],
            shift,
            as_of_utc=now,
            previous_page=prev_page,
            chart_asset=chart_asset,
            private_texts=private_texts,
        )
        stored_page = None
        if store is not None and output_dir is not None:
            stored_page = register_flash_page(store, flash_page, output_dir=Path(output_dir))

        canonical_url = canonical_url_builder(flash_page) if canonical_url_builder else None
        social_bundle = None
        if canonical_url:
            media_ids = [a["asset_id"] for a in flash_page.get("media_assets") or [] if a.get("asset_id")]
            social_bundle = render_flash_social_bundle(
                shift["public_theme"],
                shift,
                canonical_url,
                as_of_utc=now,
                media_asset_ids=media_ids,
                private_texts=private_texts,
            )

        # 4. Record in exactly-once ledger and advance baseline for this theme
        active_ledger["dispatched_events"][event_key] = {
            "event_key": event_key,
            "theme_id": tid,
            "primary_reason": shift["primary_reason"],
            "reasons": shift["reasons"],
            "page_id": flash_page["page_id"],
            "canonical_url": canonical_url,
            "emitted_at_utc": now.isoformat(),
            "map_as_of_utc": public_reg["as_of_utc"],
            "cooldown_bypassed": cooldown_bypassed,
            "status": "EMITTED",
        }
        updated_entry = _snapshot_theme_baseline(det["themes"][tid], as_of_utc=public_reg["as_of_utc"])
        prior_hits = set(theme_entry.get("hit_decision_point_ids") or [])
        updated_entry["hit_decision_point_ids"] = sorted(
            prior_hits | set(updated_entry["hit_decision_point_ids"]) | set(shift["hit_decision_point_ids"])
        )
        if shift.get("theme_catalyst_marker"):
            updated_entry["last_theme_catalyst_hit_marker"] = shift["theme_catalyst_marker"]
        elif theme_entry.get("last_theme_catalyst_hit_marker"):
            updated_entry["last_theme_catalyst_hit_marker"] = theme_entry["last_theme_catalyst_hit_marker"]
        updated_entry["last_dispatched_at_utc"] = now.isoformat()
        updated_entry["last_dispatched_event_key"] = event_key
        if canonical_url:
            updated_entry["latest_page"] = {
                "page_id": flash_page["page_id"],
                "canonical_url": canonical_url,
                "published_at_utc": now.isoformat(),
                "as_of_utc": public_reg["as_of_utc"],
                "revision_fingerprint": flash_page["revision_fingerprint"],
                "base_case_fingerprint": flash_page["base_case_fingerprint"],
                "branch_flip_signature": flash_page["branch_flip_signature"],
            }
        elif prev_page:
            updated_entry["latest_page"] = dict(prev_page)
        active_ledger["themes"][tid] = updated_entry
        dispatched_theme_ids.add(tid)

        emitted_flashes.append({
            "event_key": event_key,
            "theme_id": tid,
            "theme_name": shift["theme_name"],
            "primary_reason": shift["primary_reason"],
            "reasons": shift["reasons"],
            "cooldown_bypassed": cooldown_bypassed,
            "public_summary_lines": shift["public_summary_lines"],
            "flash_page": flash_page,
            "stored_page": stored_page,
            "canonical_url": canonical_url,
            "social_bundle": social_bundle,
        })

    # Seed any newly observed themes that didn't trigger or get suppressed, while preserving
    # baseline probabilities for non-dispatched themes so cumulative >= 10 pp drift is caught.
    for tid, det_theme in det["themes"].items():
        if tid in dispatched_theme_ids or tid in suppressed_theme_ids:
            continue
        if tid not in active_ledger["themes"]:
            entry = _snapshot_theme_baseline(det_theme, as_of_utc=public_reg["as_of_utc"])
            if tid in prior_pages:
                entry["latest_page"] = dict(prior_pages[tid])
            active_ledger["themes"][tid] = entry
        else:
            active_ledger["themes"][tid]["rank"] = det_theme["rank"]
            active_ledger["themes"][tid]["status"] = det_theme["status"]

    active_ledger["last_poll_as_of_utc"] = public_reg["as_of_utc"]
    active_ledger["last_map_sha256"] = public_reg["register_sha256"]
    active_ledger["last_top_theme_ids"] = [
        tid for tid in public_reg["top_theme_ids"] if tid not in suppressed_theme_ids
    ]

    if ledger_path is not None:
        save_ledger(ledger_path, active_ledger)

    if emitted_flashes:
        status = "MATERIAL_SHIFTS_EMITTED"
    elif suppressed_cooldown:
        status = "COOLDOWN_SUPPRESSED"
    elif skipped_duplicates:
        status = "DUPLICATE_SKIPPED"
    else:
        status = "NO_MATERIAL_SHIFT"

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "polled_at_utc": now.isoformat(),
        "polled_at_et": et(now),
        "map_as_of_utc": public_reg["as_of_utc"],
        "poll_interval_minutes": poll_interval_minutes,
        "cooldown_minutes": cooldown_minutes,
        "llm_calls_made": 0,
        "emitted_flashes": emitted_flashes,
        "suppressed_cooldown": suppressed_cooldown,
        "skipped_duplicates": skipped_duplicates,
        "public_register": public_reg,
        "ledger": active_ledger,
    }


# ---------------------------------------------------------------------------
# Session-Sync Market Forces Pulse (Pre-Asia / Pre-London / Pre-US Cash Open)
# ---------------------------------------------------------------------------

def session_sync_window_at(at_utc: Any) -> str | None:
    """Classify an instant into one of the three session-sync windows using New York ET time."""
    local = public_datetime(attention.utc(at_utc))
    weekday = local.weekday()  # Mon=0 .. Sun=6
    clock = local.time()

    # Pre-Asia Open: Sun-Thu 17:00-19:30 ET (ahead of Tokyo cash open)
    if weekday in {0, 1, 2, 3, 6} and time(17, 0) <= clock <= time(19, 30):
        return SESSION_PRE_ASIA
    # Pre-London Open: Mon-Fri 01:30-03:30 ET (ahead of London cash open)
    if weekday in {0, 1, 2, 3, 4} and time(1, 30) <= clock <= time(3, 30):
        return SESSION_PRE_LONDON
    # Pre-US Cash Open: Mon-Fri 07:30-09:30 ET (ahead of US cash open; aligns with daily wrap)
    if weekday in {0, 1, 2, 3, 4} and time(7, 30) <= clock <= time(9, 30):
        return SESSION_PRE_US
    return None


def render_session_sync_pulse(
    register_or_public: Mapping[str, Any],
    *,
    session: str | None = None,
    as_of_utc: Any = None,
    recent_flashes: list[Mapping[str, Any]] | None = None,
    page_links: Mapping[str, str] | None = None,
    max_themes: int = 3,
    private_texts: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Render a concise Session-Sync Market Forces Pulse for Pre-Asia, Pre-London, or Pre-US open.

    Safe to embed directly into `market_wrap_editorial_v1.article_for()` (require_notice=False
    since the wrap prints both Decision 40 notices once at the end).
    """
    if register_or_public.get("schema_version") == attention.SCHEMA_VERSION:
        public_reg = register_or_public
    else:
        projected = project_live_attention_map(register_or_public, as_of_utc=as_of_utc, max_age_minutes=None)
        public_reg = projected["public_register"]

    stamp = attention.utc(as_of_utc or public_reg["as_of_utc"])
    resolved_session = session or session_sync_window_at(stamp) or SESSION_PRE_US
    if resolved_session not in SESSION_LABELS:
        raise ValueError("MARKET_FORCES_SESSION_INVALID:" + str(resolved_session))

    session_label = SESSION_LABELS[resolved_session]
    heading = f"Session-sync market forces — {session_label}"
    clock_et = et(stamp)
    page_links = page_links or {}
    recent_flashes = list(recent_flashes or [])
    flashed_ids = [str(f.get("theme_id") or "") for f in recent_flashes if f.get("theme_id")]

    live_themes = [t for t in public_reg["themes"] if t["status"] in attention.LIVE_STATUSES]
    if not live_themes:
        raise ValueError("ATTENTION_MAP_NO_LIVE_THEMES")

    prioritized = sorted(
        live_themes,
        key=lambda t: (0 if t["theme_id"] in flashed_ids else 1, t["rank"], t["theme_id"]),
    )[:max(1, min(max_themes, attention.TOP_THEME_COUNT))]

    extra_sources: list[str] = [clock_et]
    lines: list[str] = [f"## {heading}", f"Market forces snapshot as of {clock_et}."]
    top_lines: list[str] = []

    for theme in prioritized:
        tid = theme["theme_id"]
        lead_market = theme.get("lead_market")
        market_label = attention.PUBLIC_MARKET_LABELS.get(lead_market, "")
        if market_label:
            extra_sources.append(market_label)
        base = next(b for b in theme["branches"] if b["kind"] == "base")
        parts = [
            f"- {theme['name']} ({theme['status']}): {attention._branch_line(base)}",
        ]
        if market_label:
            parts.append(f"Lead market: {market_label}.")
        next_dp = theme["decision_points"][0] if theme.get("decision_points") else None
        if next_dp:
            parts.append(f"Next catalyst: {next_dp['when_et']} — {next_dp['title'].rstrip('.')}.")
        url = page_links.get(tid)
        if url:
            if find_forbidden_link(url):
                raise ValueError("PREVIEW_HOST_LINK_FORBIDDEN")
            parts.append(f"Scenario page: {url}")
        bullet = " ".join(parts)
        lines.append(bullet)
        top_lines.append(f"{theme['name']}: {theme['one_line'].rstrip('.')}.")

    flash_lines: list[str] = []
    for item in recent_flashes:
        name = attention._clean_text(item.get("theme_name") or item.get("name") or "")
        summary_list = item.get("public_summary_lines")
        summary = attention._clean_text(
            summary_list[0] if isinstance(summary_list, list) and summary_list else item.get("summary") or ""
        )
        url = str(item.get("canonical_url") or "")
        if url and find_forbidden_link(url):
            raise ValueError("PREVIEW_HOST_LINK_FORBIDDEN")
        if not name or not summary:
            continue
        flash_clock = item.get("clock_et") or (
            et(attention.utc(item["as_of_utc"])) if item.get("as_of_utc") else ""
        )
        if flash_clock:
            extra_sources.append(flash_clock)
        suffix = f" ({flash_clock})" if flash_clock else ""
        url_tail = f" {url}" if url else ""
        flash_lines.append(f"- {name}{suffix}: {summary.rstrip('.')}.{url_tail}")

    markdown = "\n\n".join(lines[:2]) + "\n\n" + "\n".join(lines[2 : 2 + len(prioritized)])
    if flash_lines:
        markdown += "\n\n### Intraday shifts\n" + "\n".join(flash_lines)

    all_private = list(private_texts)
    if public_reg.get("_private_texts"):
        all_private.extend(public_reg["_private_texts"])

    attention.validate_attention_map_copy(
        markdown,
        public_register=public_reg,
        require_notice=False,
        private_texts=all_private,
        extra_allowed_sources=tuple(extra_sources),
    )
    instruments.validate_payload({"public_instrument_policy": instruments.POLICY}, {"text": markdown})

    return {
        "schema_version": PULSE_SCHEMA_VERSION,
        "session": resolved_session,
        "session_label": session_label,
        "heading": heading,
        "as_of_utc": stamp.isoformat(),
        "as_of_et": clock_et,
        "markdown": markdown,
        "theme_ids": [t["theme_id"] for t in prioritized],
        "top_lines": top_lines,
        "flash_count": len(flash_lines),
        "register_sha256": public_reg["register_sha256"],
        "extra_allowed_sources": list(dict.fromkeys(extra_sources)),
    }


def validate_session_sync_pulse(
    pulse: Mapping[str, Any],
    *,
    register_or_public: Mapping[str, Any] | None,
    private_texts: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Validate a pre-rendered session-sync pulse with full register figure traceability and private-text checks (M2)."""
    if not isinstance(pulse, Mapping) or pulse.get("schema_version") != PULSE_SCHEMA_VERSION:
        raise ValueError("SESSION_SYNC_PULSE_SCHEMA_INVALID")
    if not isinstance(register_or_public, Mapping):
        raise ValueError("SESSION_SYNC_PULSE_REGISTER_REQUIRED")
    if register_or_public.get("schema_version") == attention.SCHEMA_VERSION:
        public_reg = register_or_public
    else:
        projected = project_live_attention_map(
            register_or_public,
            as_of_utc=pulse.get("as_of_utc"),
            max_age_minutes=None,
        )
        public_reg = projected["public_register"]

    all_private = list(private_texts)
    if public_reg.get("_private_texts"):
        all_private.extend(public_reg["_private_texts"])

    extra_sources: list[str] = []
    if pulse.get("as_of_et"):
        extra_sources.append(str(pulse["as_of_et"]))
    for src in pulse.get("extra_allowed_sources") or []:
        if isinstance(src, str) and src.strip():
            extra_sources.append(src)
    for theme in public_reg.get("themes") or []:
        lead = theme.get("lead_market")
        if lead in attention.PUBLIC_MARKET_LABELS:
            extra_sources.append(attention.PUBLIC_MARKET_LABELS[lead])

    attention.validate_attention_map_copy(
        pulse.get("markdown") or "",
        public_register=public_reg,
        require_notice=False,
        private_texts=all_private,
        extra_allowed_sources=tuple(dict.fromkeys(extra_sources)),
    )
    instruments.validate_payload({"public_instrument_policy": instruments.POLICY}, {"text": pulse.get("markdown") or ""})
    return dict(pulse)


def render_session_sync_social_bundle(
    pulse: Mapping[str, Any],
    public_register: Mapping[str, Any],
    canonical_url: str,
    *,
    destinations: tuple[str, ...] = ALL_TEN_DESTINATIONS,
    credit: str = "",
    media_asset_ids: list[str] | tuple[str, ...] = (),
    private_texts: tuple[str, ...] | list[str] = (),
) -> dict[str, dict[str, Any]]:
    """Render concise 10-platform short social copy for a session-sync market forces pulse."""
    if not canonical_url or find_forbidden_link(canonical_url):
        raise ValueError("PREVIEW_HOST_LINK_FORBIDDEN")
    session_label = pulse["session_label"]
    clock_et = pulse["as_of_et"]
    top_lines = list(pulse.get("top_lines") or [])
    if not top_lines:
        raise ValueError("ATTENTION_MAP_NO_LIVE_THEMES")

    notices = f"{PUBLIC_NOTICE}\n{CONFLICTS_NOTICE}"
    credit_suffix = f" {credit.strip().rstrip('.')}." if credit and credit.strip() else ""
    extra_sources = (clock_et, credit_suffix)
    media_ids = list(media_asset_ids)
    all_private = list(private_texts)
    if public_register.get("_private_texts"):
        all_private.extend(public_register["_private_texts"])

    bundle: dict[str, dict[str, Any]] = {}
    for dest in destinations:
        if dest not in attention._PLATFORM_LIMITS:
            raise ValueError("MARKET_FORCES_SOCIAL_DESTINATION_INVALID:" + str(dest))
        limit = attention._PLATFORM_LIMITS[dest]
        header = f"{session_label} market forces ({clock_et}):"
        bullets = [f"- {line}" for line in top_lines]
        if dest == "x":
            from .plan_status_posts_v1 import _x_length

            root_candidates = [
                f"{header}\n" + "\n".join(bullets) + credit_suffix,
                f"{session_label} market forces:\n" + "\n".join(bullets) + credit_suffix,
                f"{header}\n{bullets[0]}{credit_suffix}",
                f"{session_label} market forces: {top_lines[0]}{credit_suffix}",
            ]
            root = next((c for c in root_candidates if _x_length(c) <= 280), None)
            if root is None:
                fallback_root = f"{session_label} market forces ({clock_et}).{credit_suffix}"
                if _x_length(fallback_root) > 280:
                    raise ValueError("MARKET_FORCES_SESSION_SOCIAL_COPY_EXCEEDS_LIMIT:x")
                root = fallback_root
            reply_link = f"{canonical_url}\n\n{notices}"
            if _x_length(reply_link) > 280:
                raise ValueError("MARKET_FORCES_SESSION_SOCIAL_COPY_EXCEEDS_LIMIT:x")
            texts = [root, reply_link]
            missing = [b for b in bullets if b not in root and b.removeprefix("- ") not in root]
            if missing:
                joined = "\n".join(missing)
                if _x_length(joined) <= 280:
                    texts.append(joined)
                else:
                    for item in missing:
                        if _x_length(item) <= 280:
                            texts.append(item)
            full_text = "\n\n".join(texts)
            if _ELLIPSIS.search(full_text):
                raise ValueError("MARKET_FORCES_TRUNCATION_FORBIDDEN")
            attention.validate_attention_map_copy(
                full_text,
                public_register=public_register,
                require_notice=True,
                private_texts=all_private,
                extra_allowed_sources=extra_sources,
            )
            payload = {
                "destination": dest,
                "format": "thread",
                "text": texts[0],
                "root_text": texts[0],
                "reply_texts": texts[1:],
                "full_text": full_text,
                "posts": [
                    {"order": i, "role": "reply" if i else "root", "text": t, "media_asset_ids": [] if i else media_ids}
                    for i, t in enumerate(texts)
                ],
                "media_asset_ids": media_ids,
                "platform_limit": limit,
                "hard_truncation_used": False,
            }
            instruments.validate_payload({"public_instrument_policy": instruments.POLICY}, payload)
            bundle[dest] = payload
            continue

        candidates = [
            f"{header}\n" + "\n".join(bullets) + credit_suffix + f"\n\n{canonical_url}\n\n{notices}",
            f"{session_label} market forces:\n" + "\n".join(bullets) + credit_suffix + f"\n\n{canonical_url}\n\n{notices}",
            f"{header}\n{bullets[0]}{credit_suffix}\n\n{canonical_url}\n\n{notices}",
            f"{session_label} market forces ({clock_et}).{credit_suffix}\n\n{canonical_url}\n\n{notices}",
        ]
        full = next((c for c in candidates if len(c) <= limit), None)
        if full is None:
            raise ValueError("MARKET_FORCES_SESSION_SOCIAL_COPY_EXCEEDS_LIMIT:" + dest)
        if _ELLIPSIS.search(full):
            raise ValueError("MARKET_FORCES_TRUNCATION_FORBIDDEN")
        attention.validate_attention_map_copy(
            full,
            public_register=public_register,
            require_notice=True,
            private_texts=all_private,
            extra_allowed_sources=extra_sources,
        )
        payload = {
            "destination": dest,
            "format": "session_sync_pulse_social",
            "text": full,
            "full_text": full,
            "media_asset_ids": media_ids,
            "platform_limit": limit,
            "hard_truncation_used": False,
        }
        instruments.validate_payload({"public_instrument_policy": instruments.POLICY}, payload)
        bundle[dest] = payload
    return bundle
