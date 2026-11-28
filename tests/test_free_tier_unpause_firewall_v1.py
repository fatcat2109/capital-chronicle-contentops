"""Hermetic tests for V2.1-C6 ~15 Dec FREE-Only CC-024 Unpause Firewall & CC-817 v2 Live-Schema Rehearsal.

Strictly offline (tmp_path only; zero network calls, zero live publishing, zero writes
outside tmp_path, zero Task Scheduler mutations, zero browser/LLM/agy calls).

Covers:
  1. Pillar (a) CC-024 Commercial-Rights Firewall & all 5 Capital Chronicle public filters
     (Investing.com/Myfxbook, OCC/Yahoo GEX, FRED SP500, TradingView paywall/embedded
     widgets vs allowed static snapshot credits, raw X-list/wire quotes, AI/model labels,
     private book/positions/prepared responses, preview hosts, unnamed market-odds % and
     Kalshi/Polymarket/FedWatch numbers, price targets, non-ET clocks, raw CFD symbols).
  2. Pillar (b) FREE_ONLY_MODE guarantee (zero paywall HTML, paid tiers, checkout links,
     referral links, paid audience/tier metadata, or non-zero prices prior to Q1 2027).
  3. Pillar (c) V2.1-C6 Day-1 SHA-256 track-record hash chain & citation lineage
     (`L4ShadowSleeveArenaLedgerRecordV1` + `CapitalChronicleTrackRecordChainV1`) AND
     zero active Claude / Anthropic / `agy` runtime dependencies post-04 Dec.
  4. Pillar (d) Strictly fail-closed integrity (malformed/duplicate-key JSON, non-finite
     numbers, stale pre-15-Dec pause manifests including live `pause-20261123` shape,
     premature unpause clocks, kill switches, and Rule A3 zero silent waivers).
  5. Live-Schema CC-817 v2 High-Interval End-to-End Dry-Run Rehearsal matching CURRENT
     Live Main `d96c30c78f39` `CC-807` schema (all 14 top-level keys & 33 per-theme keys,
     immutable `WEB_ONLY` Substack theme/flash pages, 10-platform short social bundles,
     Pre-Asia/Pre-London/Pre-US session-sync pulses, `market_wrap_editorial_v1` wrap
     embedding, and read-only live-import parity check against Live Main `d96c30c78f39`).
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import math
from pathlib import Path
import sys
from typing import Any

import pytest

from live_contentops import free_tier_unpause_firewall_v1 as fw
from live_contentops import market_attention_map_public_v1 as attention
from live_contentops import market_forces_high_interval_v1 as hi
from live_contentops import market_wrap_editorial_v1 as wrap_editorial
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
from test_market_attention_map_cc817 import _tv_asset
from test_market_wrap_cc689 import at, cash, pack, select_first  # noqa: F401


DEC15_OPEN_UTC = datetime(2026, 12, 15, 13, 0, tzinfo=timezone.utc)
DEC15_PRE_ASIA_UTC = datetime(2026, 12, 15, 23, 0, tzinfo=timezone.utc)      # 18:00 ET
DEC15_PRE_LONDON_UTC = datetime(2026, 12, 15, 7, 30, tzinfo=timezone.utc)    # 02:30 ET
DEC15_PRE_US_UTC = datetime(2026, 12, 15, 13, 30, tzinfo=timezone.utc)       # 08:30 ET
LIVE_MAIN_REPO = Path(r"A:\Capital Chronicle\main-jim-research-dashboard-20261025")
CC691_POSTS_PATH = Path(__file__).parent / "fixtures" / "cc691" / "posts.json"


# ---------------------------------------------------------------------------
# Hermetic Builders (Day-1 SHA-256 Arena Chain, Pause Manifest, CC-807 Live Map)
# ---------------------------------------------------------------------------


def _build_arena_chain_records(count: int = 3) -> list[dict[str, Any]]:
    """Construct a deterministic valid L4ShadowSleeveArenaLedgerRecordV1 SHA-256 hash chain."""
    records: list[dict[str, Any]] = []
    prev_sha = fw.GENESIS_PREV_SHA256
    base_dt = datetime(2026, 12, 1, 13, 0, tzinfo=timezone.utc)
    kinds = ("DECISION_SEAL", "SHADOW_FILL", "SHADOW_CLOSE")

    for seq in range(1, count + 1):
        cutoff_dt = base_dt + timedelta(days=seq)
        known_dt = cutoff_dt - timedelta(minutes=5)
        cutoff_iso = cutoff_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        known_iso = known_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        kind = kinds[(seq - 1) % len(kinds)]
        sleeve_id = "l4_macro_sleeve_a"
        payload = {
            "event_seq": seq,
            "symbol": "XAUUSD",
            "signal_side": "LONG",
            "entry_price_private": 2650.5 + seq,
            "stop_price_private": 2620.0,
            "account_id": "279805139",
            "prepared_response_note": f"PRIVATE_ARENA_SENTINEL_ROW_{seq}_MUST_NEVER_APPEAR_PUBLICLY",
            "signed_r_private": 0.75 if kind == "SHADOW_CLOSE" else 0.0,
        }
        payload_sha = fw.sha256_canonical(payload)
        record_id = "arena_" + fw.sha256_canonical(
            [seq, kind, sleeve_id, cutoff_iso, prev_sha, payload_sha]
        )[:24]
        envelope = {
            "schema": fw.ARENA_LEDGER_SCHEMA,
            "schema_version": "1.0.0",
            "sequence": seq,
            "record_id": record_id,
            "record_kind": kind,
            "sleeve_id": sleeve_id,
            "cutoff_utc": cutoff_iso,
            "known_at_max_utc": known_iso,
            "prev_record_sha256": prev_sha,
            "payload_sha256": payload_sha,
            "private_only": True,
            "public_export_forbidden": True,
            "payload": payload,
        }
        rec_sha = fw.sha256_canonical(envelope)
        row = {**envelope, "record_sha256": rec_sha}
        records.append(row)
        prev_sha = rec_sha
    return records


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    body = "\n".join(fw.canonical_json(r) for r in rows) + "\n"
    path.write_bytes(body.encode("utf-8"))
    return path


def _valid_dec15_pause_manifest() -> dict[str, Any]:
    return {
        "authority": "JIM_V21_C6_DEC15_FREE_ONLY_UNPAUSE_20261127",
        "paused_at_utc": "2026-11-30T00:00:00Z",
        "resume_at_utc": "2026-12-14T17:00:00Z",
        "cause": "V21_C6_PAUSE_20261130_UNTIL_20261215_FREE_ONLY_CC024_CLEAN",
        "unpause_mode": fw.FREE_ONLY_MODE,
        "cc024_clean_required": True,
        "suspended_destinations": sorted(fw.ALL_FREE_DESTINATIONS),
        "tasks": [
            {"name": "ContentOps_Daily_Digest_1900", "driver": "python-neo", "enabled": True},
            {"name": "ContentOps_Market_Forces_Poll_15m", "driver": "codex-desktop", "enabled": True},
        ],
        "stop_files": ["A:/Capital Chronicle/Runtime/ContentOps/control/pause.stop"],
    }


def _clean_outbound_payload(text: str | None = None, **extra: Any) -> dict[str, Any]:
    body = text if text is not None else (
        "US Treasury yields eased after BLS CPI data matched consensus, supporting gold (GC futures) "
        "and Nasdaq 100 (NQ futures). Base case (55%, Capital Chronicle estimate): real yields stabilize "
        "near recent lows while the Federal Reserve's 2% inflation target anchors longer-term expectations. "
        "Chart: TradingView. Free public-page snapshot.\n\n"
        f"{PUBLIC_NOTICE}\n{CONFLICTS_NOTICE}"
    )
    payload: dict[str, Any] = {
        "destination": "substack",
        "audience": "everyone",
        "substack_delivery_mode": "WEB_ONLY",
        "paywall": False,
        "price_usd": 0,
        "title": "Macro rates and gold scenario review (15 Dec 2026)",
        "body_markdown": body,
        "chart_url": "https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD",
        "sources": [
            {"source": "BLS", "url": "https://www.bls.gov/cpi/"},
            {"source": "Federal Reserve H.15", "url": "https://www.federalreserve.gov/releases/h15/"},
            {"source": "NY Fed", "url": "https://www.newyorkfed.org/research/policy/nowcast"},
            {"source": "US Treasury", "url": "https://home.treasury.gov/"},
            {"source": "TradingView Lightweight Charts", "url": "https://www.tradingview.com/lightweight-charts/"},
        ],
    }
    payload.update(extra)
    return payload


def _cc807_live_schema_theme(
    *,
    theme_id: str,
    name: str,
    one_line: str,
    rank: int,
    lead_market: str,
    affected_markets: list[str],
    as_of: datetime,
    status: str = "active",
    base_summary: str,
    base_invalidation: str,
    alt_summary: str,
    alt_invalidation: str,
    base_cc_pct: float = 55.0,
    base_mkt_pct: float = 62.0,
    alt_cc_pct: float = 25.0,
    alt_mkt_pct: float = 23.0,
    dp_id: str,
    dp_title: str,
    dp_at_utc: str | None,
    dp_watch_condition: str | None = None,
) -> dict[str, Any]:
    """Exact 33-key theme matching CURRENT Live Main d96c30c78f39 tools/product/market_attention_map_v1.py."""
    first_seen = (as_of - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated = as_of.strftime("%Y-%m-%dT%H:%M:%SZ")
    dp_entry: dict[str, Any] = {
        "id": dp_id,
        "title": dp_title,
        "dated": dp_at_utc is not None,
        "at_utc": dp_at_utc,
        "watch_condition": dp_watch_condition,
        "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "watch_signals": [
            {
                "kind": "official_page",
                "label": "Official central bank and statistical release calendar",
                "url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            },
            {
                "kind": "odds_market_number",
                "label": f"Kalshi private odds tracker for {theme_id}",
                "market_key": f"kalshi:{theme_id}",
            },
            {
                "kind": "x_account",
                "label": f"Private squawk stream for {theme_id}",
                "handle": "FirstSquawk",
            },
        ],
    }
    return {
        "theme_id": theme_id,
        "name": name,
        "one_line": one_line,
        "status": status,
        "rank": rank,
        "attention_score": round(96.0 - rank * 4.5, 2),
        "first_seen_utc": first_seen,
        "updated_at_utc": updated,
        "lead_market": lead_market,
        "affected_markets": list(affected_markets),
        "causal_chains": [
            {
                "asset": lead_market,
                "event": f"Policy and macro repricing around {name}",
                "channel": "Rate differentials, risk premium, and cross-asset funding flows",
                "sign": "upside_on_confirmation",
                "direction": "UP",
                "rough_size": "+0.6 to +1.1 normal days on confirmation",
            },
            *[
                {
                    "asset": secondary_market,
                    "event": f"Cross-asset spillover from {name}",
                    "channel": "Rate expectations and institutional risk-appetite transmission",
                    "sign": "two_way",
                    "direction": "TWO_WAY",
                    "rough_size": "moderate regime spillover",
                }
                for secondary_market in affected_markets
                if secondary_market != lead_market
            ],
        ],
        "decision_points": [dp_entry],
        "branches": [
            {
                "branch_id": f"{theme_id}_base",
                "kind": "base",
                "summary": base_summary,
                "probability_pct": base_cc_pct,
                "probability_source": "capital_chronicle",
                "cc_probability_pct": base_cc_pct,
                "market_implied_probability_pct": base_mkt_pct,
                "market_implied_delta_15m_pp": 0.0,
                "market_implied_delta_1h_pp": 0.5,
                "market_implied_delta_24h_pp": 1.5,
                "market_lean_words": "Market pricing leans moderately toward the base scenario.",
                "invalidation": base_invalidation,
            },
            {
                "branch_id": f"{theme_id}_bear",
                "kind": "bear",
                "summary": alt_summary,
                "probability_pct": alt_cc_pct,
                "probability_source": "capital_chronicle",
                "cc_probability_pct": alt_cc_pct,
                "market_implied_probability_pct": alt_mkt_pct,
                "market_implied_delta_15m_pp": 0.0,
                "market_implied_delta_1h_pp": -0.5,
                "market_implied_delta_24h_pp": -1.5,
                "market_lean_words": "Markets treat the downside path as a secondary risk.",
                "invalidation": alt_invalidation,
            },
        ],
        "active_branch_id": f"{theme_id}_base",
        "prior_active_branch_id": f"{theme_id}_base",
        "branch_flipped": False,
        "branch_flip_evidence": {
            "flipped_at_utc": None,
            "summary": f"Private branch flip diagnostics for {theme_id} internal desk use only.",
        },
        "market_lean_words": "Market pricing leans cautiously toward the primary path without extreme crowding.",
        "priced_in_words": "Most baseline repricing is reflected, leaving tail reactions asymmetric around catalysts.",
        "priced_in_gap": {
            "cc_base_probability_pct": base_cc_pct,
            "market_implied_base_probability_pct": base_mkt_pct,
            "gap_pp": round(base_cc_pct - base_mkt_pct, 2),
        },
        "surprise_map": {
            "open_position_impacts": [
                {"lifecycle_id": f"private_{theme_id}_pos", "account_id": "279805139", "lots": 0.5}
            ]
        },
        "prepared_responses": [
            {
                "instrument": lead_market,
                "direction": "BUY",
                "stop_formula": "anchor - 0.5 * ATR",
                "note": f"PRIVATE_PREPARED_RESPONSE_SECRET_{theme_id}_DO_NOT_LEAK",
            }
        ],
        "linked_odds_markets": [
            {
                "platform": "kalshi",
                "market_key": f"kalshi:{theme_id}",
                "title": f"Kalshi private contract for {theme_id} odds monitoring",
                "latest_probability_pct": base_mkt_pct,
                "delta_15m_pp": 0.0,
            }
        ],
        "computed_metrics": [
            {"label": "Replay range on confirmation", "value": "+0.35R to +0.85R with half-normal-day stop"},
            {"label": "Historical 10-year yield beta", "value": "moderate sensitivity around release days"},
        ],
        "primary_sources": [
            {
                "kind": "official_page",
                "title": "Federal Reserve Monetary Policy Calendar",
                "url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            },
            {
                "kind": "x_list",
                "title": f"Private X-list commentary on {theme_id} captured via JIM_X_LIST",
                "handle": "@DeItaone",
            },
        ],
        "timeline_sources": [
            {
                "source_kind": "wire_headline",
                "headline": f"Bloomberg wire private flash on {theme_id} must never reach public copy",
                "observed_at_utc": updated,
            }
        ],
        "watch_keywords": ["macro", "policy", lead_market.lower()],
        "scoring_hooks": {"private_edge_score": 0.82, "book_correlation": 0.41},
        "history": [
            {"at_utc": first_seen, "summary": "Theme added to the Capital Chronicle attention map."},
        ],
        "live_state": {
            "updated_at_utc": updated,
            "max_odds_delta_15m_pp": 0.0,
            "max_odds_delta_1h_pp": 0.5,
            "max_odds_delta_24h_pp": 1.5,
            "decision_point_catalyst_hit": False,
            "branch_flip_detected": False,
            "material_shift_flags": [],
        },
        "material_change_hash": f"cc807-live-{theme_id}-v1",
        "x_list_posts": [
            f"Private X-list post from @FirstSquawk about {theme_id} that must stay strictly private."
        ],
        "wire_headlines": [
            f"Private Reuters wire headline on {theme_id} for internal narrative context only."
        ],
    }


def _cc807_live_schema_envelope(as_of: datetime = DEC15_OPEN_UTC) -> dict[str, Any]:
    """Exact 14-key Live Main d96c30c78f39 MarketAttentionMapLiveV1 across 6 themes & all 7 core markets."""
    iso = as_of.strftime("%Y-%m-%dT%H:%M:%SZ")
    themes = [
        _cc807_live_schema_theme(
            theme_id="usdjpy_fed_boj_mof",
            name="Fed-BoJ Rate Gap and Yen Intervention Watch",
            one_line="US-Japan yield spreads and official Tokyo jawboning keep yen risk asymmetric.",
            rank=1,
            lead_market="USDJPY",
            affected_markets=["USDJPY", "XAUUSD", "US500"],
            as_of=as_of,
            base_summary="Yield differentials keep USD/JPY elevated until official Tokyo intervention risk rises.",
            base_invalidation="Bank of Japan delivers a faster tightening signal alongside lower US yields.",
            alt_summary="Coordinated official Tokyo resistance narrows carry appetite and drives yen strength.",
            alt_invalidation="US Treasury yields break higher while Japanese officials stay passive.",
            dp_id="mof_intervention_watch",
            dp_title="Ministry of Finance FX Intervention Watch",
            dp_at_utc=None,
            dp_watch_condition="Official Tokyo FX remarks or sharp intraday yen reversal",
        ),
        _cc807_live_schema_theme(
            theme_id="nvidia_leadership_ai_capex",
            name="AI Infrastructure Capex and Mega-Cap Tech",
            one_line="Hyperscaler spending guidance anchors Nasdaq 100 and S&P 500 equity leadership.",
            rank=2,
            lead_market="USTEC",
            affected_markets=["USTEC", "US500", "BTCUSD"],
            as_of=as_of,
            base_summary="Steady cloud capital expenditure sustains semiconductor demand and Nasdaq 100 leadership.",
            base_invalidation="Major cloud providers cut capital spending guidance or signal slower AI utilization.",
            alt_summary="Capex deceleration weighs on semiconductor multiples and broader Nasdaq 100 sentiment.",
            alt_invalidation="Quarterly supply-chain orders confirm accelerating data-center shipments.",
            dp_id="semi_guidance_update",
            dp_title="Semiconductor Supply-Chain Guidance Window",
            dp_at_utc=(as_of + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        _cc807_live_schema_theme(
            theme_id="us_real_yields_gold",
            name="US Real Yields and Central Bank Gold Demand",
            one_line="Real-rate direction and official reserve accumulation govern gold trend persistence.",
            rank=3,
            lead_market="XAUUSD",
            affected_markets=["XAUUSD", "EURUSD", "US500"],
            as_of=as_of,
            base_summary="Contained real yields and steady sovereign demand keep gold supported on pullbacks.",
            base_invalidation="Sustained jump in US real yields triggers broad precious-metals liquidation.",
            alt_summary="Higher real rates and a firmer dollar cap gold momentum and force consolidation.",
            alt_invalidation="Soft inflation data pulls US real yields lower across the curve.",
            dp_id="treasury_tips_auction",
            dp_title="US Treasury TIPS Auction Demand Read",
            dp_at_utc=(as_of + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        _cc807_live_schema_theme(
            theme_id="oil_supply_balance",
            name="OPEC Supply Discipline and Energy Balances",
            one_line="Producer quota compliance and refinery margins shape WTI crude oil risk.",
            rank=4,
            lead_market="USOIL",
            affected_markets=["USOIL", "US500", "XAUUSD"],
            as_of=as_of,
            base_summary="Balanced inventory draws keep WTI crude oil range-bound while supply risk stays contained.",
            base_invalidation="Unexpected producer quota breakdown floods physical crude balances.",
            alt_summary="Supply disruption tightens prompt spreads and lifts headline energy inflation risk.",
            alt_invalidation="US crude output and commercial inventories build consistently across weekly reports.",
            dp_id="eia_weekly_inventory",
            dp_title="EIA Weekly Petroleum Status Report",
            dp_at_utc=(as_of + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        _cc807_live_schema_theme(
            theme_id="eurozone_growth_spread",
            name="Eurozone Policy Divergence and Sovereign Spreads",
            one_line="European growth softness versus US demand drives EUR/USD rate spreads.",
            rank=5,
            lead_market="EURUSD",
            affected_markets=["EURUSD", "US500"],
            as_of=as_of,
            base_summary="Wider US-Eurozone rate spreads cap EUR/USD rallies unless European data firms.",
            base_invalidation="Eurozone activity indicators surprise higher while US growth cools.",
            alt_summary="Fiscal support and firmer European services inflation lift EUR/USD back toward range highs.",
            alt_invalidation="European central bank officials signal faster policy easing.",
            dp_id="ecb_policy_statement",
            dp_title="ECB Monetary Policy Statement and Press Conference",
            dp_at_utc=(as_of + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        _cc807_live_schema_theme(
            theme_id="btc_liquidity_flows",
            name="Dollar Liquidity and Institutional Digital Asset Flows",
            one_line="Net dollar liquidity and ETF flow momentum steer Bitcoin regime shifts.",
            rank=6,
            lead_market="BTCUSD",
            affected_markets=["BTCUSD", "USTEC", "US500"],
            as_of=as_of,
            base_summary="Constructive liquidity conditions support institutional Bitcoin allocation during risk-on sessions.",
            base_invalidation="Sharp liquidity contraction and sustained ETF outflows reverse risk appetite.",
            alt_summary="Tighter financial conditions trigger broad de-risking across digital assets.",
            alt_invalidation="Treasury cash drawdowns add reserves and stabilize institutional inflows.",
            dp_id="fed_balance_sheet_h41",
            dp_title="Federal Reserve H.4.1 Liquidity Release",
            dp_at_utc=(as_of + timedelta(days=2, hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
    ]
    return {
        "schema": "MarketAttentionMapLiveV1",
        "schema_version": "1.0.0",
        "as_of_utc": iso,
        "generated_at_utc": iso,
        "cutoff_utc": iso,
        "material_change_hash": "cc807-live-envelope-dec15-v1",
        "cadence_metadata": {
            "last_deep_pass_utc": "2026-12-15T01:00:00Z",
            "last_live_refresh_utc": iso,
            "cadence_policy": {"live_refresh_interval_minutes": 15, "live_refresh_llm_calls": 0},
        },
        "themes": themes,
        "joint_scenarios": [{"id": "private_joint_1", "note": "Private cross-theme portfolio correlation"}],
        "unknown_force_tickets": [{"id": "uf_1", "note": "Private desk unknown force ticket"}],
        "open_positions": [{"account_id": "279805139", "symbol": "USDJPY", "lots": 0.5}],
        "prepared_responses": [{"instrument": "US500", "stop_formula": "anchor - 0.5*ATR"}],
        "public_boundary_notice": "INTERNAL_NUMBERS_ONLY: never publish raw book, odds, or wire headlines.",
        "provenance": {"source_commit": "d96c30c78f39", "llm_calls": 0},
    }


def _url_for(page: dict[str, Any]) -> str:
    slug = str(page["page_id"]).replace("_", "-")
    return f"https://capitalchronicle.substack.com/p/{slug}"


# ---------------------------------------------------------------------------
# Pillar (a): CC-024 Commercial-Rights Firewall & 5 Public Filters
# ---------------------------------------------------------------------------


def test_pillar_a_cc024_clean_free_sources_and_static_tv_credit_pass():
    payload = _clean_outbound_payload()
    res = fw.verify_outbound_free_payload(
        payload,
        now_utc=DEC15_OPEN_UTC,
        destination="substack",
        require_notice=True,
    )
    assert res["status"] == "PASS"
    assert res["mode"] == fw.FREE_ONLY_MODE
    assert res["cc024"]["cc024_clean"] is True
    assert res["public_write_performed"] is False


@pytest.mark.parametrize("bad_text,expected_code", [
    ("Consensus from Investing.com points to a higher print.", "CC024_INVESTING_OR_MYFXBOOK_FORBIDDEN"),
    ("Calendar sourced via Myfxbook economic feed.", "CC024_INVESTING_OR_MYFXBOOK_FORBIDDEN"),
    ("Preview consensus from fxstreet.com suggests a slowdown.", "CC024_INVESTING_OR_MYFXBOOK_FORBIDDEN"),
    ("Options gamma exposure computed from OCC open interest data.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("Dealer GEX levels pulled from Yahoo Finance options chain.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("Option quotes from https://www.theocc.com/ show heavy call OI.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("Index series sourced from https://fred.stlouisfed.org/series/SP500.", "CC024_FRED_SP500_FORBIDDEN"),
    ("We chart FRED: SP500 alongside real yields.", "CC024_FRED_SP500_FORBIDDEN"),
    ("Interactive chart via https://s3.tradingview.com/tv.js widget.", "CC024_TRADINGVIEW_WIDGET_FORBIDDEN"),
    ('<iframe src="https://widget.tradingview.com/embed-widget/mini/"></iframe>', "CC024_TRADINGVIEW_WIDGET_FORBIDDEN"),
    ("Embedded paid TradingView widget tracks intraday ticks.", "CC024_TRADINGVIEW_WIDGET_FORBIDDEN"),
    ("New TradingView.widget({symbol: 'NASDAQ:NDX'}) loaded on page.", "CC024_TRADINGVIEW_WIDGET_FORBIDDEN"),
    ("Breaking update via https://x.com/FirstSquawk/status/1999999.", "CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN"),
    ("According to @FirstSquawk, bond desks saw heavy bids.", "CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN"),
    ("Captured in JIM_X_LIST during the London session.", "CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN"),
    ("Bloomberg wire reported traders trimmed duration exposure.", "CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN"),
    ("Drafted by our Claude Opus editorial pipeline.", "CC024_AI_MODEL_LABEL_FORBIDDEN"),
    ("Gemini 4 Neon reviewed the morning macro note.", "CC024_AI_MODEL_LABEL_FORBIDDEN"),
    ("Written by Codex GPT-6.2-sol and Antigravity agents.", "CC024_AI_MODEL_LABEL_FORBIDDEN"),
    ("Capital Chronicle is an AI-run trading research desk.", "CC024_AI_MODEL_LABEL_FORBIDDEN"),
    ("Our open book holds 0.5 lots on account 279805139.", "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ("DEMO account equity gained $1,250 on the move.", "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ("Our prepared responses arm a breakout order above resistance.", "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ("Read the preview at https://fatcat2109.github.io/capital-chronicle-preview/.", "PREVIEW_HOST_LINK_FORBIDDEN"),
    ("Staged on https://cc-preview.pages.dev/note.", "PREVIEW_HOST_LINK_FORBIDDEN"),
    ("Markets imply 68% chance of a December hold.", "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("Rate pause is priced in at 84% ahead of the meeting.", "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("Kalshi prices the outcome at 62% this morning.", "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("Polymarket gives 71 cents on the policy decision.", "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("CME FedWatch shows 95.1% odds of unchanged policy.", "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("Desk spread gap_pp: 14.2 between model and market.", "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("Our price target is 165.00 into year-end.", "CC024_PRICE_TARGET_FORBIDDEN"),
    ("TP1: 3,985 and take-profit at 4,050.", "CC024_PRICE_TARGET_FORBIDDEN"),
    ("Published at 20:30 GMT+7 ahead of CPI.", "PUBLIC_TIMEZONE_ET_REQUIRED"),
    ("Data capture closed at 13:15 UTC.", "ATTENTION_MAP_NON_ET_CLOCK_FORBIDDEN"),
    ("USTEC outperformed while US500 and XAUUSD consolidated.", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"),
    ("Debug leak api_key=secret_token_value_123456.", "CC024_SECRET_FORBIDDEN"),
])
def test_pillar_a_cc024_blocks_all_forbidden_sources_and_leaks(bad_text: str, expected_code: str):
    payload = _clean_outbound_payload(text=bad_text)
    with pytest.raises(fw.FreeTierFirewallError) as exc_info:
        fw.verify_outbound_free_payload(payload, now_utc=DEC15_OPEN_UTC, destination="substack")
    codes = {v["code"] for v in exc_info.value.violations}
    assert expected_code in codes, f"Expected {expected_code}, got {codes}"


def test_pillar_a_cc024_blocks_structured_metadata_and_private_text_echo():
    # Structured FRED SP500 object
    p_fred = _clean_outbound_payload(
        sources=[{"source": "FRED", "series_id": "SP500", "url": "https://fred.stlouisfed.org/"}]
    )
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_FRED_SP500_FORBIDDEN"):
        fw.verify_cc024_commercial_firewall(p_fred)

    # Structured TradingView widget metadata
    p_tv = _clean_outbound_payload(chart={"modality": "tradingview_widget"})
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_TRADINGVIEW_WIDGET_FORBIDDEN"):
        fw.verify_cc024_commercial_firewall(p_tv)

    # Private keys / flags inside payload
    p_priv = _clean_outbound_payload(prepared_responses=[{"symbol": "gold", "action": "watch"}])
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"):
        fw.verify_cc024_commercial_firewall(p_priv)

    p_flag = _clean_outbound_payload(private_only=True)
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"):
        fw.verify_cc024_commercial_firewall(p_flag)

    # Verbatim private X-list / wire text echo caught even without handle/domain
    secret_wire = "Exclusive internal desk wire note about Japanese pension rebalancing flows."
    p_echo = _clean_outbound_payload(
        text=f"Macro note: {secret_wire}\n\n{PUBLIC_NOTICE}\n{CONFLICTS_NOTICE}"
    )
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN"):
        fw.verify_cc024_commercial_firewall(p_echo, private_texts=[secret_wire])

    # Missing mandatory public analysis notice when require_notice=True
    p_no_notice = _clean_outbound_payload(
        text="Treasury yields drifted lower ahead of the afternoon auction. Chart: TradingView."
    )
    with pytest.raises(fw.FreeTierFirewallError, match="PUBLIC_ANALYSIS_NOTICE_REQUIRED"):
        fw.verify_cc024_commercial_firewall(p_no_notice, require_notice=True)


# ---------------------------------------------------------------------------
# Pillar (b): FREE_ONLY_MODE Guarantee (Zero Paid / Paywall / Gate Markers)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_marker", [
    "<!--paywall-->",
    "Read the rest [paywall] in our archive.",
    '<div class="paywall-banner">Locked</div>',
    "Continue at https://capitalchronicle.substack.com/subscribe?next=/p/macro",
    "This section is for paid subscribers only.",
    "Upgrade to paid for full weekly scenarios.",
    "Unlock full access to our macro dashboard.",
    "Join our Telegram VIP channel for real-time updates.",
    "Now launching the Paid Research Tier at $29/mo.",
    "Checkout via https://checkout.stripe.com/pay/cs_test_123.",
    "Subscribe through https://whop.com/capital-chronicle/.",
    "Billing hosted on https://capitalchronicle.lemonsqueezy.com/checkout.",
    "Follow live trades at https://www.mql5.com/en/signals/123456.",
    "Open an account with our Exness partner referral link.",
])
def test_pillar_b_free_only_blocks_all_paywall_and_paid_copy_markers(bad_marker: str):
    payload = _clean_outbound_payload(text=f"Daily macro summary.\n\n{bad_marker}\n\n{PUBLIC_NOTICE}")
    with pytest.raises(fw.FreeTierFirewallError, match="FREE_ONLY_PAYWALL_MARKER_FORBIDDEN"):
        fw.verify_free_only_mode(payload, now_utc=DEC15_OPEN_UTC)


@pytest.mark.parametrize("extra_fields,expected_code", [
    ({"paywall": True}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"paid_tier_enabled": True}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"subscription_gate": True}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"audience": "only_paid"}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"substack_delivery_mode": "PAID_ONLY"}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"tier": "paid_research_tier"}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"operating_tier": "vip"}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"price_usd": 19.0}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"monthly_price_usd": 29}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"price_usd": True}, "FREE_ONLY_INVALID_PRICE_TYPE"),
])
def test_pillar_b_free_only_blocks_paid_metadata_flags_and_prices(
    extra_fields: dict[str, Any], expected_code: str
):
    payload = _clean_outbound_payload(**extra_fields)
    with pytest.raises(fw.FreeTierFirewallError, match=expected_code):
        fw.verify_free_only_mode(payload, now_utc=DEC15_OPEN_UTC)


def test_pillar_b_free_only_passes_clean_free_payload_and_checks_destination():
    res = fw.verify_free_only_mode(_clean_outbound_payload(), now_utc=DEC15_OPEN_UTC)
    assert res["status"] == "PASS"
    assert res["mode"] == fw.FREE_ONLY_MODE
    assert res["paid_markers_found"] == 0
    assert res["pre_q1_2027_free_lock"] is True

    with pytest.raises(fw.FreeTierFirewallError, match="FREE_TIER_DESTINATION_INVALID"):
        fw.verify_outbound_free_payload(
            _clean_outbound_payload(),
            now_utc=DEC15_OPEN_UTC,
            destination="telegram_vip",
        )


# ---------------------------------------------------------------------------
# Pillar (c): V2.1-C6 Day-1 SHA-256 Hash Chain & Post-04 Dec Zero Claude/AGY
# ---------------------------------------------------------------------------


def test_pillar_c_day1_arena_hash_chain_and_citation_lineage_roundtrip(tmp_path: Path):
    records = _build_arena_chain_records(3)
    chain_path = _write_jsonl(tmp_path / "arena_ledger_v1.jsonl", records)

    verified = fw.verify_day1_hash_chain(chain_path, max_clock_utc=DEC15_OPEN_UTC)
    assert verified["valid"] is True
    assert verified["ledger_schema"] == fw.ARENA_LEDGER_SCHEMA
    assert verified["record_count"] == 3
    assert verified["genesis_record_sha256"] == records[0]["record_sha256"]
    assert verified["chain_tip_sha256"] == records[-1]["record_sha256"]
    assert verified["file_sha256"] is not None

    citation = fw.build_public_track_record_citation(
        chain_path,
        as_of_utc=DEC15_OPEN_UTC,
        summary_lines=("All records sealed offline prior to public reference.",),
    )
    assert citation["schema"] == fw.TRACK_RECORD_CITATION_SCHEMA
    assert citation["mode"] == fw.FREE_ONLY_MODE
    assert citation["chain_tip_sha256"] == records[-1]["record_sha256"]

    # Private ledger payload strings MUST NEVER leak into the public citation.
    serialized_citation = json.dumps(citation)
    for private_secret in (
        "PRIVATE_ARENA_SENTINEL_ROW_1",
        "279805139",
        "entry_price_private",
        "stop_price_private",
        "signed_r_private",
    ):
        assert private_secret not in serialized_citation

    checked = fw.verify_track_record_citation_lineage(
        citation,
        now_utc=DEC15_OPEN_UTC,
        chain_records_or_path=chain_path,
        private_texts=["PRIVATE_ARENA_SENTINEL_ROW_1_MUST_NEVER_APPEAR_PUBLICLY"],
    )
    assert checked["status"] == "PASS"
    assert checked["chain_cross_verified"] is True


def test_pillar_c_generic_track_record_chain_supported(tmp_path: Path):
    payload_1 = {"event": "signal_recorded", "asset_label": "gold", "direction": "upside"}
    p_sha_1 = fw.sha256_canonical(payload_1)
    env_1 = {
        "schema": fw.GENERIC_TRACK_CHAIN_SCHEMA,
        "schema_version": "1.0.0",
        "sequence": 1,
        "record_id": "tr_0001",
        "record_kind": "PUBLIC_CALL_RECORD",
        "cutoff_utc": "2026-12-10T13:00:00Z",
        "known_at_max_utc": "2026-12-10T12:55:00Z",
        "prev_record_sha256": fw.GENESIS_PREV_SHA256,
        "payload_sha256": p_sha_1,
        "payload": payload_1,
    }
    row_1 = {**env_1, "record_sha256": fw.sha256_canonical(env_1)}
    chain_path = _write_jsonl(tmp_path / "generic_chain.jsonl", [row_1])

    citation = fw.build_public_track_record_citation(chain_path, as_of_utc=DEC15_OPEN_UTC)
    assert citation["record_count"] == 1
    assert citation["genesis_record_sha256"] == citation["chain_tip_sha256"] == row_1["record_sha256"]


def test_pillar_c_hash_chain_and_citation_tampering_fails_closed(tmp_path: Path):
    base_records = _build_arena_chain_records(2)

    # 1. Tampered payload
    bad_payload = deepcopy(base_records)
    bad_payload[1]["payload"]["signed_r_private"] = 9.99
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_PAYLOAD_SHA_MISMATCH"):
        fw.verify_day1_hash_chain(bad_payload, max_clock_utc=DEC15_OPEN_UTC)

    # 2. Broken prev_record_sha256 link
    bad_prev = deepcopy(base_records)
    bad_prev[1]["prev_record_sha256"] = "a" * 64
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_PREV_SHA_MISMATCH"):
        fw.verify_day1_hash_chain(bad_prev, max_clock_utc=DEC15_OPEN_UTC)

    # 3. Tampered record_sha256
    bad_rec_sha = deepcopy(base_records)
    bad_rec_sha[0]["record_sha256"] = "b" * 64
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_RECORD_SHA_MISMATCH"):
        fw.verify_day1_hash_chain(bad_rec_sha, max_clock_utc=DEC15_OPEN_UTC)

    # 4. Tampered Arena privacy flag
    bad_priv = deepcopy(base_records)
    bad_priv[0]["private_only"] = False
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_ARENA_PRIVACY_TAMPERED"):
        fw.verify_day1_hash_chain(bad_priv, max_clock_utc=DEC15_OPEN_UTC)

    # 5. known_at_max_utc > cutoff_utc (lookahead violation)
    bad_known = deepcopy(base_records)
    bad_known[0]["known_at_max_utc"] = "2026-12-02T14:00:00Z"
    with pytest.raises(fw.FreeTierFirewallError, match="CLOCK_AFTER_CUTOFF"):
        fw.verify_day1_hash_chain(bad_known, max_clock_utc=DEC15_OPEN_UTC)

    # 6. Non-monotonic cutoff clock
    bad_mono = deepcopy(base_records)
    bad_mono[1]["cutoff_utc"] = "2026-12-01T12:00:00Z"
    bad_mono[1]["known_at_max_utc"] = "2026-12-01T11:55:00Z"
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_CLOCK_NON_MONOTONIC"):
        fw.verify_day1_hash_chain(bad_mono, max_clock_utc=DEC15_OPEN_UTC)

    # 7. CRLF / BOM / Truncated JSONL file checks
    valid_bytes = ("\n".join(fw.canonical_json(r) for r in base_records) + "\n").encode("utf-8")
    crlf_path = tmp_path / "crlf.jsonl"
    crlf_path.write_bytes(valid_bytes.replace(b"\n", b"\r\n"))
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_CR_FORBIDDEN"):
        fw.verify_day1_hash_chain(crlf_path)

    bom_path = tmp_path / "bom.jsonl"
    bom_path.write_bytes(b"\xef\xbb\xbf" + valid_bytes)
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_BOM_FORBIDDEN"):
        fw.verify_day1_hash_chain(bom_path)

    trunc_path = tmp_path / "trunc.jsonl"
    trunc_path.write_bytes(valid_bytes[:-1])
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_TRUNCATED"):
        fw.verify_day1_hash_chain(trunc_path)

    # 8. Tampered citation seal & missing tip hash in prose
    citation = fw.build_public_track_record_citation(base_records, as_of_utc=DEC15_OPEN_UTC)
    tampered_seal = deepcopy(citation)
    tampered_seal["record_count"] = 99
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CITATION_SEAL_MISMATCH"):
        fw.verify_track_record_citation_lineage(tampered_seal, now_utc=DEC15_OPEN_UTC)

    missing_tip = {k: v for k, v in citation.items() if k != "citation_sha256"}
    missing_tip["public_summary_text"] = f"Summary without hash.\n{PUBLIC_NOTICE}\n{CONFLICTS_NOTICE}"
    missing_tip["citation_sha256"] = fw.sha256_canonical(missing_tip)
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CITATION_TIP_NOT_IN_PUBLIC_COPY"):
        fw.verify_track_record_citation_lineage(missing_tip, now_utc=DEC15_OPEN_UTC)


def test_pillar_c_zero_claude_and_agy_dependencies_post_dec04(tmp_path: Path):
    ctrl = tmp_path / "control"
    ctrl.mkdir()
    clean_tasks = [
        {"name": "DailyDigest1900", "enabled": True, "driver": "python-neo", "command": "python scripts/run_daily_digest_1900.py"},
        {"name": "LegacyClaudeTask", "enabled": False, "driver": "claude", "command": "claude -p legacy"},
    ]
    res = fw.verify_zero_claude_and_agy_dependencies(
        now_utc=DEC15_OPEN_UTC,
        runtime_config={"editorial_owner": "codex", "model": "gpt-6.2-sol", "digest_driver": "python-neo"},
        control_dir=ctrl,
        scheduled_tasks=clean_tasks,
        editorial_agent="codex",
        digest_driver="python-neo",
        live_provider="openai",
    )
    assert res["status"] == "PASS"
    assert res["claude_sunset_active"] is True
    assert res["agy_terms_block_active"] is True
    assert res["active_claude_dependencies"] == 0
    assert res["active_agy_dependencies"] == 0

    # Refusal matrix post-04 Dec
    with pytest.raises(fw.FreeTierFirewallError, match="CLAUDE_EDITORIAL_AGENT_RETIRED_CC855"):
        fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, editorial_agent="claude")

    with pytest.raises(fw.FreeTierFirewallError, match="CLAUDE_ROUTE_RETIRED_CC855"):
        fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, digest_driver="claude")

    with pytest.raises(fw.FreeTierFirewallError, match="AGY_BLOCKED_TERMS_OF_SERVICE_20261124"):
        fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, digest_driver="agy")

    with pytest.raises(fw.FreeTierFirewallError, match="ANTHROPIC_PROVIDER_RETIRED_CC855"):
        fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, live_provider="anthropic")

    with pytest.raises(fw.FreeTierFirewallError, match="AGY_BLOCKED_TERMS_OF_SERVICE_20261124"):
        fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, live_provider="agy")

    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_CLAUDE_DEPENDENCY_FORBIDDEN"):
        fw.verify_zero_claude_and_agy_dependencies(
            now_utc=DEC15_OPEN_UTC,
            runtime_config={"runner": "claude -p daily_digest"},
        )

    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_AGY_DEPENDENCY_FORBIDDEN"):
        fw.verify_zero_claude_and_agy_dependencies(
            now_utc=DEC15_OPEN_UTC,
            runtime_config={"helper": r"C:\Users\bullw\.gemini\bin\agy.exe"},
        )

    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_CLAUDE_SCHEDULED_TASK_FORBIDDEN"):
        fw.verify_zero_claude_and_agy_dependencies(
            now_utc=DEC15_OPEN_UTC,
            scheduled_tasks=[{"name": "BadTask", "enabled": True, "command": "claude.exe -p run"}],
        )

    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_AGY_SCHEDULED_TASK_FORBIDDEN"):
        fw.verify_zero_claude_and_agy_dependencies(
            now_utc=DEC15_OPEN_UTC,
            scheduled_tasks=[{"name": "BadAgy", "enabled": True, "command": "agy.exe --prompt test"}],
        )

    # Presence of agy_neo_routes.json in control_dir fails closed
    (ctrl / "agy_neo_routes.json").write_text('{"x": "AGY"}\n', encoding="utf-8")
    with pytest.raises(fw.FreeTierFirewallError, match="AGY_NEO_ROUTES_PRESENT_FORBIDDEN_CC801"):
        fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, control_dir=ctrl)


# ---------------------------------------------------------------------------
# Pillar (d): Fail-Closed Integrity, Non-Finite Numbers, Stale Manifests, Rule A3
# ---------------------------------------------------------------------------


def test_pillar_d_strict_json_nonfinite_clocks_and_rule_a3_waivers():
    # Duplicate JSON keys
    with pytest.raises(fw.FreeTierFirewallError, match="DUPLICATE_JSON_KEY"):
        fw.load_strict_json_bytes(b'{"a": 1, "a": 2}')

    # NaN / Infinity in JSON bytes
    for bad_json in (b'{"x": NaN}', b'{"x": Infinity}', b'{"x": -Infinity}'):
        with pytest.raises(fw.FreeTierFirewallError, match="NONFINITE_NUMBER_FORBIDDEN"):
            fw.load_strict_json_bytes(bad_json)

    # Non-finite Python floats and Decimals in payloads
    for bad_num in (math.nan, math.inf, -math.inf, Decimal("NaN"), Decimal("Infinity")):
        with pytest.raises(fw.FreeTierFirewallError, match="NONFINITE_NUMBER_FORBIDDEN"):
            fw.verify_outbound_free_payload(
                _clean_outbound_payload(metric_val=bad_num),
                now_utc=DEC15_OPEN_UTC,
            )

    # Naive, date-only, bool, and future clocks
    with pytest.raises(fw.FreeTierFirewallError, match="UTC_CLOCK_NAIVE_FORBIDDEN"):
        fw.parse_strict_utc(datetime(2026, 12, 15, 13, 0), field_name="now_utc")
    with pytest.raises(fw.FreeTierFirewallError, match="UTC_CLOCK_INVALID_FORMAT"):
        fw.parse_strict_utc("2026-12-15", field_name="now_utc")
    with pytest.raises(fw.FreeTierFirewallError, match="UTC_CLOCK_REQUIRED"):
        fw.parse_strict_utc(True, field_name="now_utc")
    with pytest.raises(fw.FreeTierFirewallError, match="CLOCK_AFTER_CUTOFF"):
        fw.parse_strict_utc("2026-12-16T00:00:00Z", field_name="ts", max_clock_utc=DEC15_OPEN_UTC)

    # Rule A3: zero silent waivers anywhere in payload or manifest
    for waiver_key, waiver_val in (
        ("skip_cc024", True),
        ("waive_firewall", True),
        ("allow_stale_manifest", True),
        ("force_unpause", True),
        ("waiver", "temporary"),
    ):
        with pytest.raises(fw.FreeTierFirewallError, match="SILENT_WAIVER_FORBIDDEN_RULE_A3"):
            fw.verify_outbound_free_payload(
                _clean_outbound_payload(**{waiver_key: waiver_val}),
                now_utc=DEC15_OPEN_UTC,
            )


def test_pillar_d_pause_manifest_blocks_stale_pre_dec15_and_premature_unpause(tmp_path: Path):
    ctrl = tmp_path / "control"
    ctrl.mkdir()
    valid = _valid_dec15_pause_manifest()
    manifest_path = tmp_path / "dec15_manifest.json"
    manifest_path.write_text(json.dumps(valid, indent=2) + "\n", encoding="utf-8")

    # 1. Valid manifest on 15 Dec 2026 passes cleanly
    res = fw.verify_pause_manifest_for_dec15_unpause(manifest_path, now_utc=DEC15_OPEN_UTC, control_dir=ctrl)
    assert res["status"] == "PASS"
    assert res["unpause_mode"] == fw.FREE_ONLY_MODE
    assert res["cc024_clean_required"] is True

    # 2. One second before 15 Dec 00:00 GMT+7 (2026-12-14T16:59:59Z) -> REFUSED
    with pytest.raises(fw.FreeTierFirewallError, match="UNPAUSE_BEFORE_DEC15_WINDOW"):
        fw.verify_pause_manifest_for_dec15_unpause(
            manifest_path,
            now_utc=datetime(2026, 12, 14, 16, 59, 59, tzinfo=timezone.utc),
            control_dir=ctrl,
        )

    # 3. Exact shape of live stale pause-20261123/manifest.json (resume 29 Nov) -> REFUSED
    stale_live_shape = {
        "authority": "JIM_20261123_PAUSE_EXTENDED_20261126",
        "paused_at_utc": "2026-11-23T04:50:00Z",
        "resume_at_utc": "2026-11-29T18:00:00Z",
        "cause": "JIM_PAUSE_20261123T0450Z_UNTIL_20261125T1600Z",
        "suspended_destinations": ["x", "substack"],
        "tasks": [],
        "stop_files": [],
    }
    with pytest.raises(fw.FreeTierFirewallError) as exc_info:
        fw.verify_pause_manifest_for_dec15_unpause(stale_live_shape, now_utc=DEC15_OPEN_UTC)
    codes = {v["code"] for v in exc_info.value.violations}
    assert {
        "PAUSE_MANIFEST_STALE_PRE_DEC15",
        "PAUSE_MANIFEST_STALE_CAUSE",
        "PAUSE_MANIFEST_FREE_ONLY_MODE_REQUIRED",
        "PAUSE_MANIFEST_CC024_FLAG_REQUIRED",
    } <= codes

    # 4. Missing manifest file -> REFUSED
    with pytest.raises(fw.FreeTierFirewallError, match="PAUSE_MANIFEST_MISSING"):
        fw.verify_pause_manifest_for_dec15_unpause(tmp_path / "does_not_exist.json", now_utc=DEC15_OPEN_UTC)

    # 5. Control dir hard stops: KILL_SWITCH, llm_operator_pause.flag, restored.json
    for flag_name, expected in (
        ("KILL_SWITCH", "GLOBAL_KILL_SWITCH_PRESENT"),
        ("llm_operator_pause.flag", "LLM_OPERATOR_PAUSE_FLAG_PRESENT"),
        ("restored.json", "PAUSE_MANIFEST_ALREADY_RESTORED"),
    ):
        flag_dir = tmp_path / f"ctrl_{flag_name}"
        flag_dir.mkdir()
        (flag_dir / flag_name).write_text("active\n", encoding="utf-8")
        with pytest.raises(fw.FreeTierFirewallError, match=expected):
            fw.verify_pause_manifest_for_dec15_unpause(manifest_path, now_utc=DEC15_OPEN_UTC, control_dir=flag_dir)


# ---------------------------------------------------------------------------
# Deliverable 2: Live-Schema CC-817 v2 High-Interval End-to-End Dry-Run Rehearsal
# ---------------------------------------------------------------------------


def test_live_schema_cc817_high_interval_end_to_end_rehearsal_passes_dec15_firewall(tmp_path: Path, pack):
    """Full end-to-end rehearsal using CURRENT Live Main d96c30c78f39 CC-807 schema (14 envelope / 33 theme keys)."""
    raw_t0 = _cc807_live_schema_envelope(DEC15_OPEN_UTC)
    assert len(raw_t0.keys()) == 14
    assert all(len(t.keys()) >= 31 for t in raw_t0["themes"])

    # 1. Allow-list projection strips every private field and harvests _private_texts
    projected_t0 = hi.project_live_attention_map(raw_t0, as_of_utc=DEC15_OPEN_UTC)
    public_t0 = projected_t0["public_register"]
    private_texts = list(public_t0["_private_texts"])
    assert len(private_texts) >= 12
    pub_serialized = json.dumps({k: v for k, v in public_t0.items() if k != "_private_texts"})
    for stripped in (
        "prepared_responses", "surprise_map", "priced_in_gap", "linked_odds_markets",
        "open_positions", "279805139", "PRIVATE_PREPARED_RESPONSE_SECRET",
        "FirstSquawk", "DeItaone", "Bloomberg wire", "Reuters wire", "+0.35R", "62.0",
    ):
        assert stripped not in pub_serialized

    # 2. Render & persist Top-5 immutable WEB_ONLY Substack theme pages + verify immutability + firewall PASS
    store = ContentOpsDurableStore(tmp_path / "rehearsal_store.sqlite3")
    pages_dir = tmp_path / "theme_pages"
    prior_pages: dict[str, dict[str, Any]] = {}
    outbound_bundle: list[dict[str, Any]] = []

    top_themes = [t for t in public_t0["themes"] if t["theme_id"] in set(public_t0["top_theme_ids"])]
    assert len(top_themes) == 5
    for theme in top_themes:
        chart = _tv_asset(tmp_path / "tv" / theme["theme_id"], theme["lead_market"])
        page = attention.render_theme_page(
            theme,
            as_of_utc=DEC15_OPEN_UTC,
            chart_asset=chart,
            private_texts=private_texts,
        )
        assert page["web_only"] is True and page["send_email"] is False and page["never_edit"] is True
        stored = attention.register_theme_page(store, page, output_dir=pages_dir)
        assert stored["plan"]["destinations"][0]["substack_delivery_mode"] == "WEB_ONLY"
        fw_res = fw.verify_outbound_free_payload(
            page,
            now_utc=DEC15_OPEN_UTC,
            destination="substack",
            private_texts=private_texts,
            require_notice=True,
        )
        assert fw_res["status"] == "PASS"
        outbound_bundle.append(page)
        prior_pages[theme["theme_id"]] = {
            "page_id": page["page_id"],
            "canonical_url": _url_for(page),
            "published_at_utc": DEC15_OPEN_UTC.isoformat(),
            "as_of_utc": DEC15_OPEN_UTC.isoformat(),
            "revision_fingerprint": page["revision_fingerprint"],
            "base_case_fingerprint": page["base_case_fingerprint"],
            "branch_flip_signature": page["branch_flip_signature"],
        }

    # Verify immutable page edit refusal
    mutated_page = deepcopy(outbound_bundle[0])
    mutated_page["native_payload"]["body_markdown"] += "\nEdited after publish."
    with pytest.raises(ValueError, match="CC817_THEME_PAGE_IMMUTABLE"):
        attention.register_theme_page(store, mutated_page, output_dir=pages_dir)

    # 3. Seed high-interval ledger & confirm quiet 15m tick emits ZERO flashes (0 LLM calls)
    ledger_path = tmp_path / "hi_ledger.json"
    hi.seed_ledger_from_map(raw_t0, as_of_utc=DEC15_OPEN_UTC, ledger_path=ledger_path, prior_pages=prior_pages)

    t1 = DEC15_OPEN_UTC + timedelta(minutes=15)
    quiet_map = _cc807_live_schema_envelope(t1)
    quiet_res = hi.poll_live_attention_map(
        quiet_map,
        now_utc=t1,
        ledger_path=ledger_path,
        poll_interval_minutes=15,
        canonical_url_builder=_url_for,
    )
    assert quiet_res["status"] == "NO_MATERIAL_SHIFT"
    assert quiet_res["llm_calls_made"] == 0
    assert quiet_res["emitted_flashes"] == []

    # 4. Material shift tick (all 4 triggers across themes): immutable WEB_ONLY flashes + 10-platform social copy
    t2 = DEC15_OPEN_UTC + timedelta(minutes=30)
    shifted = _cc807_live_schema_envelope(t2)
    shifted["material_change_hash"] = "cc807-live-dec15-shifts-t2"

    # Trigger A: DECISION_POINT_CATALYST_HIT on usdjpy_fed_boj_mof (undated MoF watch)
    shifted["themes"][0]["live_state"]["decision_point_catalyst_hit"] = True
    shifted["themes"][0]["live_state"]["material_shift_flags"] = ["DECISION_POINT_CATALYST_HIT"]
    shifted["themes"][0]["material_change_hash"] = "cc807-mof-watch-hit"

    # Trigger B: BRANCH_FLIPPED on nvidia_leadership_ai_capex (USTEC -> NASDAQ:NDX)
    shifted["themes"][1]["active_branch_id"] = "nvidia_leadership_ai_capex_bear"
    shifted["themes"][1]["branch_flipped"] = True
    shifted["themes"][1]["live_state"]["branch_flip_detected"] = True
    shifted["themes"][1]["live_state"]["material_shift_flags"] = ["BRANCH_FLIP"]
    shifted["themes"][1]["branches"][0]["summary"] = (
        "Slower cloud capex guidance caps semiconductor demand and weighs on Nasdaq 100 risk appetite."
    )
    shifted["themes"][1]["material_change_hash"] = "cc807-nvda-flip"

    # Trigger C: PROBABILITY_SHIFT_GE_10PP market-implied on us_real_yields_gold (62% -> 78%, words-only!)
    shifted["themes"][2]["branches"][0]["market_implied_probability_pct"] = 78.0
    shifted["themes"][2]["branches"][0]["market_implied_delta_15m_pp"] = 16.0
    shifted["themes"][2]["live_state"]["max_odds_delta_15m_pp"] = 16.0
    shifted["themes"][2]["material_change_hash"] = "cc807-gold-16pp"

    # Trigger D: NEW_TOP_FIVE_ENTRY (btc_liquidity_flows enters rank 5)
    shifted["themes"][4]["rank"] = 6
    shifted["themes"][5]["rank"] = 5
    shifted["themes"][5]["material_change_hash"] = "cc807-btc-top5"

    poll_res = hi.poll_live_attention_map(
        shifted,
        now_utc=t2,
        ledger_path=ledger_path,
        poll_interval_minutes=15,
        store=store,
        output_dir=pages_dir,
        chart_asset_provider=lambda th: _tv_asset(tmp_path / "tv_flash" / th["theme_id"], th["lead_market"]),
        canonical_url_builder=_url_for,
    )
    assert poll_res["status"] == "MATERIAL_SHIFTS_EMITTED"
    assert poll_res["llm_calls_made"] == 0
    assert len(poll_res["emitted_flashes"]) == 4

    flashed_by_id = {f["theme_id"]: f for f in poll_res["emitted_flashes"]}
    assert flashed_by_id["nvidia_leadership_ai_capex"]["primary_reason"] == hi.TRIGGER_BRANCH_FLIPPED
    assert flashed_by_id["btc_liquidity_flows"]["primary_reason"] == hi.TRIGGER_NEW_TOP_FIVE
    assert flashed_by_id["usdjpy_fed_boj_mof"]["primary_reason"] == hi.TRIGGER_CATALYST_HIT
    assert flashed_by_id["us_real_yields_gold"]["primary_reason"] == hi.TRIGGER_PROBABILITY_SHIFT

    # Every flash page AND all 10 social destinations pass FREE_ONLY + CC-024 firewall!
    for flash in poll_res["emitted_flashes"]:
        fpage = flash["flash_page"]
        assert fpage["web_only"] is True and fpage["send_email"] is False and fpage["never_edit"] is True
        outbound_bundle.append(fpage)
        assert set(flash["social_bundle"]) == set(hi.ALL_TEN_DESTINATIONS)
        for dest, social in flash["social_bundle"].items():
            assert social["hard_truncation_used"] is False
            assert "..." not in social["full_text"] and "…" not in social["full_text"]
            s_res = fw.verify_outbound_free_payload(
                social,
                now_utc=t2,
                destination=dest,
                private_texts=private_texts,
                require_notice=True,
            )
            assert s_res["status"] == "PASS"
            outbound_bundle.append(social)

    # 5. Session-Sync Pulses (Pre-Asia, Pre-London, Pre-US) + 10-platform social copy + CC-689 wrap integration
    page_links = {tid: p["canonical_url"] for tid, p in prior_pages.items()}
    recent_flashes = [
        {
            "theme_id": f["theme_id"],
            "theme_name": f["theme_name"],
            "public_summary_lines": f["public_summary_lines"],
            "canonical_url": f["canonical_url"],
            "as_of_utc": t2.isoformat(),
        }
        for f in poll_res["emitted_flashes"]
    ]
    for session_key, session_ts in (
        (hi.SESSION_PRE_LONDON, DEC15_PRE_LONDON_UTC),
        (hi.SESSION_PRE_US, DEC15_PRE_US_UTC),
        (hi.SESSION_PRE_ASIA, DEC15_PRE_ASIA_UTC),
    ):
        pulse = hi.render_session_sync_pulse(
            poll_res["public_register"],
            session=session_key,
            as_of_utc=session_ts,
            recent_flashes=recent_flashes,
            page_links=page_links,
            private_texts=private_texts,
        )
        assert pulse["session"] == session_key
        assert fw.verify_outbound_free_payload(
            pulse, now_utc=session_ts, private_texts=private_texts
        )["status"] == "PASS"
        outbound_bundle.append(pulse)

        ss_bundle = hi.render_session_sync_social_bundle(
            pulse,
            poll_res["public_register"],
            f"https://capitalchronicle.substack.com/p/session-wrap-{session_key}-2026-12-15",
            credit=tv.CREDIT,
            private_texts=private_texts,
        )
        assert set(ss_bundle) == set(hi.ALL_TEN_DESTINATIONS)
        for dest, social in ss_bundle.items():
            assert fw.verify_outbound_free_payload(
                social,
                now_utc=session_ts,
                destination=dest,
                private_texts=private_texts,
                require_notice=True,
            )["status"] == "PASS"
            outbound_bundle.append(social)

    # Embed Pre-US session-sync pulse into a CC-689 daily wrap via market_wrap_editorial_v1
    pre_us_pulse = hi.render_session_sync_pulse(
        poll_res["public_register"],
        session=hi.SESSION_PRE_US,
        as_of_utc=DEC15_PRE_US_UTC,
        recent_flashes=recent_flashes,
        page_links=page_links,
        private_texts=private_texts,
    )
    pre_us_pulse["public_register"] = poll_res["public_register"]
    wrap_pack = deepcopy(pack)
    wrap_pack["session_sync_pulse"] = pre_us_pulse
    manuscript = wrap_editorial.draft(deepcopy(pack), tmp_path / "wrap_draft", call=select_first)
    wrap_article, _ = wrap_editorial.article_for(wrap_pack, manuscript)
    assert "## Session-sync market forces — Pre-US Cash Open" in wrap_article["substack_body_markdown"]
    assert fw.verify_outbound_free_payload(
        wrap_article,
        now_utc=DEC15_PRE_US_UTC,
        destination="substack",
        private_texts=private_texts,
        require_notice=True,
    )["status"] == "PASS"
    outbound_bundle.append(wrap_article)

    # 6. Full Unified ~15 Dec FREE-Only CC-024 Unpause Preflight across ALL emitted artifacts!
    arena_records = _build_arena_chain_records(3)
    chain_path = _write_jsonl(tmp_path / "day1_arena_chain.jsonl", arena_records)
    citation = fw.build_public_track_record_citation(chain_path, as_of_utc=DEC15_PRE_ASIA_UTC)
    ctrl_dir = tmp_path / "control_clean"
    ctrl_dir.mkdir()

    preflight = fw.run_free_tier_unpause_preflight(
        now_utc=DEC15_PRE_ASIA_UTC,
        pause_manifest=_valid_dec15_pause_manifest(),
        outbound_payloads=outbound_bundle,
        track_record_citation=citation,
        track_record_chain=chain_path,
        runtime_config={"editorial_owner": "codex", "model": "gpt-6.2-sol", "digest_driver": "python-neo"},
        control_dir=ctrl_dir,
        scheduled_tasks=[
            {"name": "DailyDigest1900", "enabled": True, "driver": "python-neo"},
            {"name": "MarketForcesPoller15m", "enabled": True, "driver": "codex-desktop"},
        ],
        editorial_agent="codex",
        digest_driver="python-neo",
        private_texts=private_texts,
    )
    assert preflight["status"] == "PASS"
    assert preflight["mode"] == fw.FREE_ONLY_MODE
    assert preflight["cc024_clean"] is True
    assert preflight["public_write_performed"] is False
    assert preflight["gates"]["gate_4_outbound_payloads"]["payload_count"] == len(outbound_bundle)
    assert len(preflight["report_sha256"]) == 64


def test_readonly_live_main_d96c30c78f39_cc807_schema_parity_rehearsal(tmp_path: Path):
    """Read-only parity proof importing CURRENT Live Main d96c30c78f39 CC-807 modules strictly inside tmp_path."""
    main_module = LIVE_MAIN_REPO / "tools" / "product" / "market_attention_map_v1.py"
    if not main_module.is_file():
        pytest.skip("Live Main d96c30c78f39 checkout not mounted in this environment")

    prev_path = list(sys.path)
    prev_modules = set(sys.modules)
    try:
        sys.path.insert(0, str(LIVE_MAIN_REPO))
        from tools.product import market_attention_map_live_refresh_v1 as main_refresh  # type: ignore
        from tools.product import market_attention_map_v1 as main_map  # type: ignore

        fixture = main_map.build_worked_fixture()
        reg_path = tmp_path / main_map.REGISTER_FILE
        reg_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        refresh_summary = main_refresh.refresh_live_map(
            root=tmp_path,
            now_utc=datetime(2026, 11, 24, 12, 15, tzinfo=timezone.utc),
            odds_snapshot={},
            odds_watch_root=tmp_path / "no_odds",
            headline_rows=[],
            headline_sources_config=tmp_path / "no_headlines.json",
            price_snapshot={"USDJPY": {"price": 161.2, "move_15m_pct": 0.45}},
            options_snapshot={},
            write_output=True,
        )
        live_path = tmp_path / main_map.LIVE_FILE
        assert live_path.is_file()
        assert isinstance(refresh_summary, dict)
        live_map = json.loads(live_path.read_text(encoding="utf-8"))
        assert len(live_map.get("themes") or []) >= 2
        assert live_map["schema"] == "MarketAttentionMapLiveV1"
    finally:
        sys.path[:] = prev_path
        for mod_name in list(sys.modules):
            if mod_name not in prev_modules and mod_name.startswith("tools"):
                sys.modules.pop(mod_name, None)

    live_as_of = attention.utc(live_map["as_of_utc"])
    projected = hi.project_live_attention_map(live_map, as_of_utc=live_as_of)
    public_reg = projected["public_register"]
    private_texts = list(public_reg["_private_texts"])
    assert len(public_reg["themes"]) >= 2

    # Render theme pages, poll material shifts, render session-sync pulse & 10-platform social copy
    outbound_items: list[dict[str, Any]] = []
    for theme in public_reg["themes"]:
        page = attention.render_theme_page(theme, as_of_utc=live_as_of, private_texts=private_texts)
        assert page["web_only"] is True and page["send_email"] is False
        assert fw.verify_outbound_free_payload(
            page, now_utc=live_as_of, destination="substack", private_texts=private_texts, require_notice=True
        )["status"] == "PASS"
        outbound_items.append(page)

    poll = hi.poll_live_attention_map(
        live_map,
        now_utc=live_as_of,
        ledger_path=tmp_path / "main_parity_ledger.json",
        poll_interval_minutes=15,
        canonical_url_builder=_url_for,
    )
    assert poll["llm_calls_made"] == 0
    for flash in poll["emitted_flashes"]:
        outbound_items.append(flash["flash_page"])
        assert set(flash["social_bundle"]) == set(hi.ALL_TEN_DESTINATIONS)
        for dest, social in flash["social_bundle"].items():
            assert fw.verify_outbound_free_payload(
                social, now_utc=live_as_of, destination=dest, private_texts=private_texts, require_notice=True
            )["status"] == "PASS"
            outbound_items.append(social)

    pulse = hi.render_session_sync_pulse(
        public_reg, session=hi.SESSION_PRE_US, as_of_utc=live_as_of, private_texts=private_texts
    )
    ss_bundle = hi.render_session_sync_social_bundle(
        pulse,
        public_reg,
        "https://capitalchronicle.substack.com/p/main-d96c30c7-parity-pulse",
        credit=tv.CREDIT,
        private_texts=private_texts,
    )
    assert set(ss_bundle) == set(hi.ALL_TEN_DESTINATIONS)
    for dest, social in ss_bundle.items():
        assert fw.verify_outbound_free_payload(
            social, now_utc=live_as_of, destination=dest, private_texts=private_texts, require_notice=True
        )["status"] == "PASS"
        outbound_items.append(social)

    assert len(outbound_items) >= 12


def test_cc691_golden_confirmed_posts_pass_free_only_and_cc024_firewall():
    """Confirm historical CC-691 golden posts contain zero paywall markers or CC-024 rights violations."""
    saved = json.loads(CC691_POSTS_PATH.read_text(encoding="utf-8"))
    for key in ("timed_plan_update", "plan_analysis_reply"):
        text = saved[key]["text"]
        assert fw.verify_free_only_mode(text, now_utc=DEC15_OPEN_UTC)["status"] == "PASS"
        assert fw.verify_cc024_commercial_firewall(
            text, check_instruments=False, check_public_time=True
        )["cc024_clean"] is True
    for wrap_kind in ("daily", "weekend"):
        wrap = saved["wraps"][wrap_kind]
        assert fw.verify_free_only_mode(wrap["body_excerpt"], now_utc=DEC15_OPEN_UTC)["status"] == "PASS"
        assert fw.verify_cc024_commercial_firewall(
            wrap["body_excerpt"], check_instruments=False, check_public_time=True
        )["cc024_clean"] is True


# ---------------------------------------------------------------------------
# Cycle #22 Combined Remediation Regressions (B11-M1..M4, B11-L1..L3,
# SW2-M1..M4, SW2-L1, B11C37-H1/H2/M1..M3/L1)
# ---------------------------------------------------------------------------


def test_remediation_b11_m1_restored_json_beside_manifest_blocks_unpause(tmp_path: Path):
    """B11-M1: restored.json beside manifest.json must block even if control_dir is separate or None."""
    pause_dir = tmp_path / "pause-20261130"
    pause_dir.mkdir()
    manifest_path = pause_dir / "manifest.json"
    manifest_path.write_text(json.dumps(_valid_dec15_pause_manifest(), indent=2) + "\n", encoding="utf-8")
    (pause_dir / "restored.json").write_text('{"restored_at_utc": "2026-12-15T00:00:00Z"}\n', encoding="utf-8")

    separate_ctrl = tmp_path / "control_clean"
    separate_ctrl.mkdir()

    # Blocked with separate clean control_dir
    with pytest.raises(fw.FreeTierFirewallError, match="PAUSE_MANIFEST_ALREADY_RESTORED"):
        fw.verify_pause_manifest_for_dec15_unpause(
            manifest_path, now_utc=DEC15_OPEN_UTC, control_dir=separate_ctrl
        )
    # Blocked even when control_dir=None
    with pytest.raises(fw.FreeTierFirewallError, match="PAUSE_MANIFEST_ALREADY_RESTORED"):
        fw.verify_pause_manifest_for_dec15_unpause(
            manifest_path, now_utc=DEC15_OPEN_UTC, control_dir=None
        )
    # Explicit allow_already_restored=True still permits inspection when requested
    res = fw.verify_pause_manifest_for_dec15_unpause(
        manifest_path, now_utc=DEC15_OPEN_UTC, control_dir=separate_ctrl, allow_already_restored=True
    )
    assert res["status"] == "PASS"


@pytest.mark.parametrize("extra_field,bad_value,expected_code", [
    ("content", "USTEC breaks higher while XAUUSD pauses.", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"),
    ("description", "TP1: 3,985 and price target is 165.00.", "CC024_PRICE_TARGET_FORBIDDEN"),
    ("html", "<p>Polymarket gives 72% odds on a rate hold.</p>", "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("body_html", "<p>Markets priced in at 84% ahead of FOMC.</p>", "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("heading", "Pre-US Session Note (20:30 GMT+7)", "PUBLIC_TIMEZONE_ET_REQUIRED"),
    ("top_lines", ["Macro update closed at 13:15 UTC."], "ATTENTION_MAP_NON_ET_CLOCK_FORBIDDEN"),
    ("bullets", ["Trader @macro_desk_leak posted fresh flows."], "CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN"),
    ("notes", "DEMO account holds 0.5 lots and gained $1,250 on account 279805139.", "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ("custom_display_field", "XAUUSD rally targets TP1: 4,050.", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"),
    ("as_of_utc", "Published at 20:30 GMT+7", "PUBLIC_TIMEZONE_ET_REQUIRED"),
    ("market_asset", "USTEC price target 25000", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"),
])
def test_remediation_b11_m2_and_b11c37_h1_recursive_prose_scan_closes_unlisted_fields(
    extra_field: str, bad_value: Any, expected_code: str
):
    """B11-M2 + B11C37-H1: clean title/body_markdown MUST NOT mask violations in ANY other display field."""
    payload = _clean_outbound_payload(**{extra_field: bad_value})
    with pytest.raises(fw.FreeTierFirewallError) as exc_info:
        fw.verify_outbound_free_payload(payload, now_utc=DEC15_OPEN_UTC, destination="substack")
    codes = {v["code"] for v in exc_info.value.violations}
    assert expected_code in codes, f"Expected {expected_code}, got {codes}"


def test_remediation_b11_m2_verbatim_private_echo_caught_in_unlisted_field():
    """B11-M2 + B11C37-H1: verbatim private_texts echo inside unlisted display key must fail closed."""
    secret_wire = "Confidential internal liquidity note on Tokyo sovereign desk rebalancing."
    payload = _clean_outbound_payload(excerpt=f"Daily summary note: {secret_wire}")
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN"):
        fw.verify_outbound_free_payload(
            payload, now_utc=DEC15_OPEN_UTC, destination="substack", private_texts=[secret_wire]
        )


def test_remediation_b11_m3_b11c37_m2_b11_l2_legacy_dirs_allowed_and_active_refs_blocked(tmp_path: Path):
    """B11-M3 + B11C37-M2 + B11-L2: legacy directory names pass while active providers/script_path fail closed."""
    ctrl = tmp_path / "control"
    ctrl.mkdir()
    # Permanent legacy workspace directory names MUST NOT false-positive.
    res = fw.verify_zero_claude_and_agy_dependencies(
        now_utc=DEC15_OPEN_UTC,
        runtime_config={
            "editorial_owner": "codex",
            "model": "gpt-6.2-sol",
            "main_research_dir": r"A:\Capital Chronicle\ResearchRuns\claude-main-research\capture.json",
            "ops_integrations_dir": r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\codex-exec\runner-publisher.stop",
        },
        control_dir=ctrl,
        scheduled_tasks=[
            {
                "name": "DailyDigest1900",
                "enabled": True,
                "driver": "python-neo",
                "command": "python scripts/run_daily_digest_1900.py --driver python-neo",
                "main_root": r"A:\Capital Chronicle\ResearchRuns\claude-main-research",
                "stop_root": r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\codex-exec",
            }
        ],
        editorial_agent="codex",
        digest_driver="python-neo",
        live_provider="openai",
    )
    assert res["status"] == "PASS"

    # Active Claude / Anthropic / AGY live_provider variants MUST fail closed.
    for bad_claude_provider in ("claude-code", "claude-opus", "claude-sonnet", "anthropic-api", "anthropic-messages"):
        with pytest.raises(fw.FreeTierFirewallError, match="ANTHROPIC_PROVIDER_RETIRED_CC855"):
            fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, live_provider=bad_claude_provider)

    for bad_agy_provider in ("agy-cli", "antigravity-cli", "antigravity"):
        with pytest.raises(fw.FreeTierFirewallError, match="AGY_BLOCKED_TERMS_OF_SERVICE_20261124"):
            fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, live_provider=bad_agy_provider)

    # Enabled scheduled task referencing Claude or AGY in script_path (including inside legacy dir!) MUST fail closed.
    for bad_script in (
        "C:/ops/run_claude_poster.ps1",
        r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\run_claude_poster.ps1",
    ):
        with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_CLAUDE_SCHEDULED_TASK_FORBIDDEN"):
            fw.verify_zero_claude_and_agy_dependencies(
                now_utc=DEC15_OPEN_UTC,
                scheduled_tasks=[
                    {"name": "SneakyPoster", "enabled": True, "driver": "python-neo", "script_path": bad_script}
                ],
            )

    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_AGY_SCHEDULED_TASK_FORBIDDEN"):
        fw.verify_zero_claude_and_agy_dependencies(
            now_utc=DEC15_OPEN_UTC,
            scheduled_tasks=[
                {"name": "SneakyAgy", "enabled": True, "driver": "python-neo", "script_path": "C:/ops/run_agy_poster.ps1"}
            ],
        )


def test_remediation_b11_m4_citation_as_of_et_and_cutoff_utc_lineage_verified(tmp_path: Path):
    """B11-M4: forged as_of_et or mismatched cutoff_utc (even re-sealed) MUST fail closed."""
    records = _build_arena_chain_records(3)
    chain_path = _write_jsonl(tmp_path / "arena_chain_b11m4.jsonl", records)
    citation = fw.build_public_track_record_citation(chain_path, as_of_utc=DEC15_OPEN_UTC)

    # 1. Forged as_of_et re-sealed with valid citation_sha256 -> TRACK_RECORD_CITATION_DATE_ET_MISMATCH
    forged_et = {k: v for k, v in citation.items() if k != "citation_sha256"}
    forged_et["as_of_et"] = "1999-01-01"
    forged_et["citation_sha256"] = fw.sha256_canonical(forged_et)
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CITATION_DATE_ET_MISMATCH"):
        fw.verify_track_record_citation_lineage(forged_et, now_utc=DEC15_OPEN_UTC)

    # 2. Forged cutoff_utc (earlier than chain's real last_cutoff_utc) re-sealed -> TRACK_RECORD_CITATION_CHAIN_MISMATCH
    forged_cutoff = {k: v for k, v in citation.items() if k != "citation_sha256"}
    forged_cutoff["cutoff_utc"] = "2026-12-01T00:00:00Z"
    forged_cutoff["citation_sha256"] = fw.sha256_canonical(forged_cutoff)
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CITATION_CHAIN_MISMATCH"):
        fw.verify_track_record_citation_lineage(
            forged_cutoff, now_utc=DEC15_OPEN_UTC, chain_records_or_path=chain_path
        )


def test_remediation_sw2_m1_and_b11c37_m3_utc_overflow_normalized():
    """SW2-M1 + B11C37-M3: out-of-range aware datetimes / ET conversions MUST raise FreeTierFirewallError."""
    for bad_ts in (
        "0001-01-01T00:00:00+01:00",
        "0001-01-01T00:00:00+05:00",
        "9999-12-31T23:59:59-01:00",
        "9999-12-31T23:59:59-05:00",
        datetime(1, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=1))),
        datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone(timedelta(hours=-1))),
    ):
        with pytest.raises(fw.FreeTierFirewallError, match="UTC_CLOCK_OUT_OF_RANGE"):
            fw.parse_strict_utc(bad_ts, field_name="now_utc")

    # Overflowing max_clock_utc also normalizes cleanly
    with pytest.raises(fw.FreeTierFirewallError, match="UTC_CLOCK_OUT_OF_RANGE"):
        fw.parse_strict_utc(
            "2026-12-15T13:00:00Z",
            field_name="ts",
            max_clock_utc=datetime(1, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=1))),
        )

    # build_public_track_record_citation at year-0001 UTC (ET = UTC-5 overflows datetime.min)
    payload_1 = {"event": "genesis_boundary", "asset": "gold"}
    p_sha = fw.sha256_canonical(payload_1)
    env_1 = {
        "schema": fw.GENERIC_TRACK_CHAIN_SCHEMA,
        "schema_version": "1.0.0",
        "sequence": 1,
        "record_id": "tr_min_0001",
        "record_kind": "PUBLIC_CALL_RECORD",
        "cutoff_utc": "0001-01-01T00:00:00Z",
        "known_at_max_utc": "0001-01-01T00:00:00Z",
        "prev_record_sha256": fw.GENESIS_PREV_SHA256,
        "payload_sha256": p_sha,
        "payload": payload_1,
    }
    row_1 = {**env_1, "record_sha256": fw.sha256_canonical(env_1)}
    with pytest.raises(fw.FreeTierFirewallError, match="UTC_CLOCK_OUT_OF_RANGE"):
        fw.build_public_track_record_citation([row_1], as_of_utc="0001-01-01T00:00:00Z")


@pytest.mark.parametrize("extra_fields,expected_code", [
    ({"price_usd": "29.00"}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"price_usd": "$19"}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"monthly_price_usd": "USD 49.00"}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"price_usd": "free"}, "FREE_ONLY_INVALID_PRICE_TYPE"),
    ({"price_usd": "0"}, "FREE_ONLY_INVALID_PRICE_TYPE"),
    ({"price_usd": 10**400}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"price_usd": -(10**400)}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"price_usd": 10**5000}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"price_usd": Decimal("1e-400")}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"paywall": "true"}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"paywall": 1}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"paywall_enabled": "enabled"}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"paid_tier_enabled": "yes"}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"substack_audience": "only_paid"}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"newsletter_tier": "vip"}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
])
def test_remediation_sw2_m2_b11c37_m1_b11_l1_free_only_strict_types_and_precision(
    extra_fields: dict[str, Any], expected_code: str
):
    """SW2-M2 + B11C37-M1 + B11-L1: string prices, non-bool flags, 10**400, Decimal(1e-400), suffixed audience."""
    payload = _clean_outbound_payload(**extra_fields)
    with pytest.raises(fw.FreeTierFirewallError, match=expected_code):
        fw.verify_free_only_mode(payload, now_utc=DEC15_OPEN_UTC)


@pytest.mark.parametrize("bad_text,expected_code", [
    ("Download via https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500.", "CC024_FRED_SP500_FORBIDDEN"),
    ("Chart link: https://fred.stlouisfed.org/graph/?id=SP500", "CC024_FRED_SP500_FORBIDDEN"),
    ("Raw text series: https://fred.stlouisfed.org/data/SP500.txt", "CC024_FRED_SP500_FORBIDDEN"),
    ("Source: Yahoo Finance (https://finance.yahoo.com/quote/%5EGSPC).", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("Gold futures fetched from https://finance.yahoo.com/quote/GC=F.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("Equity index levels pulled via yfinance this morning.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("Consensus earnings calendar attributed to Yahoo Finance.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
])
def test_remediation_sw2_m3_and_b11c37_h2_fred_sp500_and_all_yahoo_finance_blocked(
    bad_text: str, expected_code: str
):
    """SW2-M3 + B11C37-H2: ALL stlouisfed.org/...sp500 URLs and ALL commercial Yahoo Finance citations blocked."""
    payload = _clean_outbound_payload(text=bad_text)
    with pytest.raises(fw.FreeTierFirewallError, match=expected_code):
        fw.verify_cc024_commercial_firewall(payload)

    # Clean non-SP500 FRED Treasury series still passes cleanly.
    clean_fred = _clean_outbound_payload(
        sources=[{"source": "FRED", "series_id": "DGS10", "url": "https://fred.stlouisfed.org/series/DGS10"}]
    )
    assert fw.verify_cc024_commercial_firewall(clean_fred)["cc024_clean"] is True


def test_remediation_sw2_m4_pause_manifest_free_only_types_and_gate2_task_scan(tmp_path: Path):
    """SW2-M4: pause manifest enforces FREE_ONLY_MODE, strict list element types, and gate_2 task inspection."""
    # 1. Paid flags / prices inside pause manifest fail closed
    paid_flag_manifest = {**_valid_dec15_pause_manifest(), "paywall_enabled": True}
    with pytest.raises(fw.FreeTierFirewallError, match="FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"):
        fw.verify_pause_manifest_for_dec15_unpause(paid_flag_manifest, now_utc=DEC15_OPEN_UTC)

    paid_price_manifest = {**_valid_dec15_pause_manifest(), "price_usd": 49}
    with pytest.raises(fw.FreeTierFirewallError, match="FREE_ONLY_NONZERO_PRICE_FORBIDDEN"):
        fw.verify_pause_manifest_for_dec15_unpause(paid_price_manifest, now_utc=DEC15_OPEN_UTC)

    # 2. Untyped list elements fail closed
    bad_dests = {**_valid_dec15_pause_manifest(), "suspended_destinations": [123, True, None]}
    with pytest.raises(fw.FreeTierFirewallError, match="PAUSE_MANIFEST_DESTINATIONS_INVALID_ELEMENT"):
        fw.verify_pause_manifest_for_dec15_unpause(bad_dests, now_utc=DEC15_OPEN_UTC)

    bad_tasks = {**_valid_dec15_pause_manifest(), "tasks": [123, True, None]}
    with pytest.raises(fw.FreeTierFirewallError, match="PAUSE_MANIFEST_TASKS_INVALID_ELEMENT"):
        fw.verify_pause_manifest_for_dec15_unpause(bad_tasks, now_utc=DEC15_OPEN_UTC)

    bad_stops = {**_valid_dec15_pause_manifest(), "stop_files": [123, True, None]}
    with pytest.raises(fw.FreeTierFirewallError, match="PAUSE_MANIFEST_STOP_FILES_INVALID_ELEMENT"):
        fw.verify_pause_manifest_for_dec15_unpause(bad_stops, now_utc=DEC15_OPEN_UTC)

    # Dict-shaped stop_files (matching live pause-20261123/manifest.json shape) are accepted
    dict_stops = {
        **_valid_dec15_pause_manifest(),
        "stop_files": [{"path": "A:/Capital Chronicle/Runtime/ContentOps/control/pause.stop", "existed_before": False}],
    }
    assert fw.verify_pause_manifest_for_dec15_unpause(dict_stops, now_utc=DEC15_OPEN_UTC)["status"] == "PASS"

    # 3. gate_2 inspects pause_manifest["tasks"] even when scheduled_tasks=None!
    records = _build_arena_chain_records(2)
    chain_path = _write_jsonl(tmp_path / "chain_sw2m4.jsonl", records)
    citation = fw.build_public_track_record_citation(chain_path, as_of_utc=DEC15_OPEN_UTC)
    bad_manifest_task = {
        **_valid_dec15_pause_manifest(),
        "tasks": [
            {"name": "SneakyManifestClaude", "enabled": True, "driver": "claude", "command": "claude -p run"}
        ],
    }
    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_CLAUDE_SCHEDULED_TASK_FORBIDDEN"):
        fw.run_free_tier_unpause_preflight(
            now_utc=DEC15_OPEN_UTC,
            pause_manifest=bad_manifest_task,
            outbound_payloads=[_clean_outbound_payload()],
            track_record_citation=citation,
            track_record_chain=chain_path,
            scheduled_tasks=None,
        )


def test_remediation_sw2_l1_b11_l3_b11c37_l1_canonical_json_preflight_and_private_flags(tmp_path: Path):
    """SW2-L1 + B11-L3 + B11C37-L1: finite Decimal in canonical_json, preflight dest/notice, non-bool private flags."""
    # SW2-L1: finite Decimal wrapped cleanly as FreeTierFirewallError
    with pytest.raises(fw.FreeTierFirewallError, match="NON_CANONICAL_JSON_VALUE"):
        fw.canonical_json({"value": Decimal("1.5")})

    # B11C37-L1: truthy string/int private_only / public_export_forbidden fail closed
    for bad_flag in (
        {"private_only": "true"},
        {"private_only": 1},
        {"public_export_forbidden": "yes"},
        {"public_export_forbidden": 1},
    ):
        with pytest.raises(fw.FreeTierFirewallError, match="CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"):
            fw.verify_cc024_commercial_firewall(_clean_outbound_payload(**bad_flag))

    # B11-L3: non-string destination fails closed AND require_notice=True is wired through preflight
    records = _build_arena_chain_records(2)
    chain_path = _write_jsonl(tmp_path / "chain_b11l3.jsonl", records)
    citation = fw.build_public_track_record_citation(chain_path, as_of_utc=DEC15_OPEN_UTC)

    bad_dest_payload = _clean_outbound_payload(destination=123)
    with pytest.raises(fw.FreeTierFirewallError, match="FREE_TIER_DESTINATION_INVALID"):
        fw.run_free_tier_unpause_preflight(
            now_utc=DEC15_OPEN_UTC,
            pause_manifest=_valid_dec15_pause_manifest(),
            outbound_payloads=[bad_dest_payload],
            track_record_citation=citation,
            track_record_chain=chain_path,
        )

    no_notice_payload = _clean_outbound_payload(
        text="Treasury yields eased after CPI matched expectations. Chart: TradingView."
    )
    with pytest.raises(fw.FreeTierFirewallError, match="PUBLIC_ANALYSIS_NOTICE_REQUIRED"):
        fw.run_free_tier_unpause_preflight(
            now_utc=DEC15_OPEN_UTC,
            pause_manifest=_valid_dec15_pause_manifest(),
            outbound_payloads=[no_notice_payload],
            track_record_citation=citation,
            track_record_chain=chain_path,
            require_notice=True,
        )


# ---------------------------------------------------------------------------
# Cycle #24 Unified 10M + Polish Hardening Regressions
# (Ops Product B16C22-M1..M4 / L1..L4, Batch #159 B16C22-N1..N4,
#  V2.4-DA10 DA10-T2B-M1..M3 / L1, Batch #154 L1/L2, Batch #155 L1..L3)
# ---------------------------------------------------------------------------


def test_c24_m1_real_manifest_state_before_tasks_schema_and_hostile_detection(tmp_path: Path):
    """B16C22-M1: real ContentOps manifest.json tasks (state_before without enabled) pass when clean & catch hostile refs."""
    records = _build_arena_chain_records(2)
    chain_path = _write_jsonl(tmp_path / "chain_c24_m1.jsonl", records)
    citation = fw.build_public_track_record_citation(chain_path, as_of_utc=DEC15_OPEN_UTC)
    ctrl_dir = tmp_path / "control_m1"
    ctrl_dir.mkdir()

    real_schema_manifest = {
        **_valid_dec15_pause_manifest(),
        "tasks": [
            {"name": "CapitalChronicle-PlanStatusPosts-V1", "state_before": "Running"},
            {"name": "CapitalChronicle-MarketWrap-V1", "state_before": "Ready"},
            {"name": "CapitalChronicle-ManualDesk-V1", "state_before": "Running"},
            {"name": "CapitalChronicle-LegacyClaude-V1", "state_before": "Disabled", "cmd": "claude -p legacy"},
        ],
        "stop_files": [
            {
                "path": r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\codex-exec\runner-publisher.stop",
                "existed_before": False,
            }
        ],
    }
    res = fw.run_free_tier_unpause_preflight(
        now_utc=DEC15_OPEN_UTC,
        pause_manifest=real_schema_manifest,
        outbound_payloads=[_clean_outbound_payload()],
        track_record_citation=citation,
        track_record_chain=chain_path,
        control_dir=ctrl_dir,
        scheduled_tasks=None,
    )
    assert res["status"] == "PASS"

    # Active/Ready state_before task with hostile Claude or AGY ref MUST fail closed!
    hostile_claude_manifest = {
        **real_schema_manifest,
        "tasks": [
            {"name": "CapitalChronicle-ClaudeDigest-V1", "state_before": "Ready"},
        ],
    }
    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_CLAUDE_SCHEDULED_TASK_FORBIDDEN"):
        fw.run_free_tier_unpause_preflight(
            now_utc=DEC15_OPEN_UTC,
            pause_manifest=hostile_claude_manifest,
            outbound_payloads=[_clean_outbound_payload()],
            track_record_citation=citation,
            track_record_chain=chain_path,
            control_dir=ctrl_dir,
            scheduled_tasks=None,
        )

    hostile_agy_manifest = {
        **real_schema_manifest,
        "tasks": [
            {"name": "CapitalChronicle-AgyHelper-V1", "state_before": "Running"},
        ],
    }
    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_AGY_SCHEDULED_TASK_FORBIDDEN"):
        fw.run_free_tier_unpause_preflight(
            now_utc=DEC15_OPEN_UTC,
            pause_manifest=hostile_agy_manifest,
            outbound_payloads=[_clean_outbound_payload()],
            track_record_citation=citation,
            track_record_chain=chain_path,
            control_dir=ctrl_dir,
            scheduled_tasks=None,
        )

    # Explicit non-bool `enabled` MUST STILL fail closed even when `state_before` is also present!
    for bad_task in (
        {"name": "BadEnabledBool", "enabled": "true", "state_before": "Ready"},
        {"name": "BadEnabledInt", "enabled": 1},
        {"name": "MissingBoth"},
        {"name": "EmptyStateBefore", "state_before": ""},
        {"name": "InvalidStateBefore", "state_before": "Bogus"},
        {"name": "NonStrStateBefore", "state_before": 123},
    ):
        with pytest.raises(fw.FreeTierFirewallError, match="SCHEDULED_TASK_ENABLED_BOOL_REQUIRED"):
            fw.verify_zero_claude_and_agy_dependencies(
                now_utc=DEC15_OPEN_UTC,
                scheduled_tasks=[bad_task],
            )


def test_c24_m2_local_filesystem_path_prose_and_ai_label_bypasses_sealed():
    """B16C22-M2: hostile prose starting with / or C:\\ in *_path/*_dir keys never bypasses Section 2 or 3."""
    secret = "Confidential internal liquidity note on Tokyo sovereign desk rebalancing."

    # Slash-prefixed hostile prose in chart_path MUST trigger BOTH Section 2 and Section 3 violations.
    p_slash = _clean_outbound_payload(
        chart_path=(
            "/ Drafted by Claude Opus! USTEC TP1: 25,000 at 20:30 GMT+7! "
            f"Kalshi 72%! DEMO account 279805139! @leak_handle! {secret}"
        )
    )
    with pytest.raises(fw.FreeTierFirewallError) as exc_slash:
        fw.verify_cc024_commercial_firewall(p_slash, private_texts=[secret])
    codes_slash = {v["code"] for v in exc_slash.value.violations}
    assert {
        "CC024_AI_MODEL_LABEL_FORBIDDEN",
        "CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN",
        "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN",
        "CC024_MARKET_ODDS_NUMBER_FORBIDDEN",
        "CC024_PRICE_TARGET_FORBIDDEN",
        "PUBLIC_TIMEZONE_ET_REQUIRED",
        "PUBLIC_INSTRUMENT_NAME_FORBIDDEN",
    } <= codes_slash

    # Windows-drive-prefixed hostile prose in notes_dir MUST fail closed across Section 2 & 3.
    p_win = _clean_outbound_payload(
        notes_dir=(
            "C:\\ Written by Gemini 4 Neon and Claude Sonnet. "
            "Our price target is 4,200 on XAUUSD at 14:00 UTC. Polymarket 78%."
        )
    )
    with pytest.raises(fw.FreeTierFirewallError) as exc_win:
        fw.verify_cc024_commercial_firewall(p_win)
    codes_win = {v["code"] for v in exc_win.value.violations}
    assert {
        "CC024_AI_MODEL_LABEL_FORBIDDEN",
        "CC024_PRICE_TARGET_FORBIDDEN",
        "PUBLIC_INSTRUMENT_NAME_FORBIDDEN",
        "ATTENTION_MAP_NON_ET_CLOCK_FORBIDDEN",
        "CC024_MARKET_ODDS_NUMBER_FORBIDDEN",
    } <= codes_win

    # Compact slash-prefixed bypass without leading space after / MUST also fail closed.
    p_compact = _clean_outbound_payload(
        chart_path="/USTEC TP1: 4200 Claude Opus @insider 84% priced in"
    )
    with pytest.raises(fw.FreeTierFirewallError) as exc_compact:
        fw.verify_cc024_commercial_firewall(p_compact)
    assert "CC024_AI_MODEL_LABEL_FORBIDDEN" in {v["code"] for v in exc_compact.value.violations}

    # Genuine local path containing non-legacy AI model label MUST fail Section 2!
    p_valid_ai_path = _clean_outbound_payload(
        chart_path=r"C:\Capital Chronicle\Claude-Opus\chart.png"
    )
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_AI_MODEL_LABEL_FORBIDDEN"):
        fw.verify_cc024_commercial_firewall(p_valid_ai_path)

    # Genuine local path inside permanent legacy dir MUST still pass cleanly.
    p_valid_legacy = _clean_outbound_payload(
        chart_path=r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\chart.png"
    )
    assert fw.verify_cc024_commercial_firewall(p_valid_legacy)["cc024_clean"] is True


@pytest.mark.parametrize("bad_free_text", [
    "This section is for **paid** subscribers only.",
    "**Upgrade** to **paid** for full access.",
    "**Unlock** full access to our research.",
    "Now launching our **paid** research tier.",
    "Full scenarios sit behind the **paywall**.",
    "This section is for _paid_ subscribers only.",
    "<p>For &#112;aid subscribers only. Upgrade to &#112;aid.</p>",
    "<p>Checkout: https://checkout.stripe&#46;com/pay/cs_123</p>",
    "<p>For <b>pa</b>id subscribers only.</p>",
    "For pa\x00id subscribers only.",
    "For p\ufe0faid subscribers only.",
    "For p\u034faid subscribers only.",
    "<p>For pa&#8203;id subscribers only.</p>",
])
def test_c24_m3_free_only_blocks_markdown_html_entities_nul_and_mn_invisibles(bad_free_text: str):
    """B16C22-M3: Markdown emphasis, HTML entities, ASCII NUL, and Mn/Cf invisibles blocked in FREE_ONLY_MODE."""
    payload = _clean_outbound_payload(text=bad_free_text)
    with pytest.raises(fw.FreeTierFirewallError, match="FREE_ONLY_PAYWALL_MARKER_FORBIDDEN"):
        fw.verify_free_only_mode(payload, now_utc=DEC15_OPEN_UTC)


@pytest.mark.parametrize("bad_cc024_text,expected_code", [
    ("Close data from **Yahoo** Finance.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("Close data from *Yahoo* Finance.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("Calendar via **investing**.com today.", "CC024_INVESTING_OR_MYFXBOOK_FORBIDDEN"),
    ("**US**TEC outperformed today.", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"),
    ("Published at 20:30 **GMT**+7.", "PUBLIC_TIMEZONE_ET_REQUIRED"),
    ("<p>Source: Yahoo&#32;Finance close.</p>", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("<p>&#75;alshi prices the hold at 68%.</p>", "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("<p>&#84;P1: 3,985 on gold.</p>", "CC024_PRICE_TARGET_FORBIDDEN"),
    ("Source: Ya\x00hoo Finance close.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("Source: Y\u034fah\u034foo Finance close.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ("<strong>Yahoo</strong> Finance intraday chart.", "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
])
def test_c24_m3_cc024_blocks_markdown_html_entities_nul_and_mn_invisibles(
    bad_cc024_text: str, expected_code: str
):
    """B16C22-M3: Markdown emphasis, HTML entities, ASCII NUL, and Mn invisibles blocked across CC-024 & Section 3."""
    payload = _clean_outbound_payload(text=bad_cc024_text)
    with pytest.raises(fw.FreeTierFirewallError) as exc_info:
        fw.verify_cc024_commercial_firewall(payload)
    codes = {v["code"] for v in exc_info.value.violations}
    assert expected_code in codes, f"Expected {expected_code}, got {codes}"


@pytest.mark.parametrize("extra_fields,expected_code", [
    ({"audience": "only_founding"}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"substack_audience": "only_founding"}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"tier": {"name": "PAID"}}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"audience": {"level": "only_paid"}}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"audience": ["only_paid"]}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"tier": ["vip"]}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"audience": True}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"delivery_tier": "pro"}, "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN"),
    ({"affiliate": True}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"affiliate_enabled": True}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"referral_code": "EXNESS_REF_123"}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"price_cents": 2900}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"amount_cents": 1900}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"monthly_price": 29}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"annual_price": 290}, "FREE_ONLY_NONZERO_PRICE_FORBIDDEN"),
    ({"free": False}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"is_free": False}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"free": 0}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
    ({"paid": True}, "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN"),
])
def test_c24_m4_paid_founding_nested_tier_affiliate_pro_and_free_false_blocked(
    extra_fields: dict[str, Any], expected_code: str
):
    """B16C22-M4 + #154 L1 + #155 L2: founding audience, nested tier/audience, affiliate, price_cents, pro, free=False."""
    payload = _clean_outbound_payload(**extra_fields)
    with pytest.raises(fw.FreeTierFirewallError, match=expected_code):
        fw.verify_free_only_mode(payload, now_utc=DEC15_OPEN_UTC)


def test_c24_n1_control_dir_fail_closed_on_invalid_paths(tmp_path: Path):
    """B16C22-N1: nonexistent dir, regular file, DOS CON, ADS, trailing dot fail closed with CONTROL_DIR_INVALID."""
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_valid_dec15_pause_manifest()) + "\n", encoding="utf-8")

    bad_ctrl_dirs = [
        tmp_path / "no_such_control_dir",
        manifest_path,  # regular file, not a directory
        tmp_path / "CON",
        tmp_path / "NUL",
        str(tmp_path / "ctrl_dir") + ":hidden",
        str(tmp_path / "ctrl_dir") + ".",
        123,
    ]
    for bad_ctrl in bad_ctrl_dirs:
        with pytest.raises(fw.FreeTierFirewallError, match="CONTROL_DIR_INVALID"):
            fw.verify_pause_manifest_for_dec15_unpause(
                manifest_path, now_utc=DEC15_OPEN_UTC, control_dir=bad_ctrl
            )
        with pytest.raises(fw.FreeTierFirewallError, match="CONTROL_DIR_INVALID"):
            fw.verify_zero_claude_and_agy_dependencies(
                now_utc=DEC15_OPEN_UTC, control_dir=bad_ctrl
            )


@pytest.mark.parametrize("extra_fields,expected_code", [
    ({"rights_class": "non_commercial"}, "CC024_RIGHTS_CLASS_FORBIDDEN"),
    ({"rights_class": "personal_only"}, "CC024_RIGHTS_CLASS_FORBIDDEN"),
    ({"rights_class": "CC024_RESTRICTED"}, "CC024_RIGHTS_CLASS_FORBIDDEN"),
    ({"rights_class": "LICENSE_REQUIRED"}, "CC024_RIGHTS_CLASS_FORBIDDEN"),
    ({"rights_class": "FRED_COPYRIGHTED"}, "CC024_RIGHTS_CLASS_FORBIDDEN"),
    ({"rights_class": ["LICENSE_REQUIRED"]}, "CC024_RIGHTS_CLASS_INVALID"),
    ({"rights_class": True}, "CC024_RIGHTS_CLASS_INVALID"),
    ({"rights_class": 123}, "CC024_RIGHTS_CLASS_INVALID"),
    ({"rights_class": ""}, "CC024_RIGHTS_CLASS_INVALID"),
    ({"sources": [{"source": "FeedX", "rights_class": "non_commercial"}]}, "CC024_RIGHTS_CLASS_FORBIDDEN"),
    ({"body_markdown": "Quote https://www.yahoo.com/finance/quote/GSPC"}, "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ({"body_markdown": "Quote https://finance.yahoo.co.uk/quote/FTSE"}, "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN"),
    ({"body_markdown": "FRED https://fred.stlouisfed.org/series/%53P500"}, "CC024_FRED_SP500_FORBIDDEN"),
    ({"body_markdown": "FRED https://fred.stlouisfed.org/series/%2553%2550500"}, "CC024_FRED_SP500_FORBIDDEN"),
    ({"body_markdown": "FRED https://fred.stlouisfed.org/series/VIXCLS"}, "CC024_FRED_SP500_FORBIDDEN"),
    ({"body_markdown": "FRED https://fred.stlouisfed.org/series/DJIA"}, "CC024_FRED_SP500_FORBIDDEN"),
    ({"body_markdown": "FRED https://fred.stlouisfed.org/series/NASDAQCOM"}, "CC024_FRED_SP500_FORBIDDEN"),
    ({"sources": [{"source": "FRED", "series_id": "VIXCLS", "url": "https://fred.stlouisfed.org/"}]}, "CC024_FRED_SP500_FORBIDDEN"),
])
def test_c24_n2_l1_rights_class_yahoo_variants_and_fred_encoded_copyrighted_blocked(
    extra_fields: dict[str, Any], expected_code: str
):
    """B16C22-N2 + B16C22-L1 + #155 L1 + DA10-T2B-M1: rights_class, yahoo.com/finance, co.uk, %53P500, VIXCLS/DJIA."""
    payload = _clean_outbound_payload(**extra_fields)
    with pytest.raises(fw.FreeTierFirewallError) as exc_info:
        fw.verify_cc024_commercial_firewall(payload)
    codes = {v["code"] for v in exc_info.value.violations}
    assert expected_code in codes, f"Expected {expected_code}, got {codes}"

    # Legitimate ContentOps public rights_class values & public FRED Treasury series still PASS.
    for clean_rc in ("CC_OWN_ANALYSIS", "CC_MODEL_ESTIMATE", "PUBLIC_DOMAIN", "BLS_OFFICIAL_PUBLIC"):
        clean_p = _clean_outbound_payload(
            rights_class=clean_rc,
            sources=[{"source": "FRED", "series_id": "DGS10", "url": "https://fred.stlouisfed.org/series/DGS10", "rights_class": "PUBLIC_DOMAIN"}],
        )
        assert fw.verify_cc024_commercial_firewall(clean_p)["cc024_clean"] is True


def test_c24_n3_l2_live_provider_and_task_legacy_stripping_bypass_closed():
    """B16C22-N3 + B16C22-L2: no legacy-path stripping on live_provider or bare task cmds; compact claude4/agy2 blocked."""
    for bad_claude_prov in (
        "claude-main-research",
        "--no-claude-cli-login",
        "claude3",
        "claude4",
        "anthropicapi",
    ):
        with pytest.raises(fw.FreeTierFirewallError, match="ANTHROPIC_PROVIDER_RETIRED_CC855"):
            fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, live_provider=bad_claude_prov)

    for bad_agy_prov in ("agy2", "antigravity2"):
        with pytest.raises(fw.FreeTierFirewallError, match="AGY_BLOCKED_TERMS_OF_SERVICE_20261124"):
            fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, live_provider=bad_agy_prov)

    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_CLAUDE_DEPENDENCY_FORBIDDEN"):
        fw.verify_zero_claude_and_agy_dependencies(
            now_utc=DEC15_OPEN_UTC,
            runtime_config={"cmd": "anthropicapi call"},
        )
    with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_AGY_DEPENDENCY_FORBIDDEN"):
        fw.verify_zero_claude_and_agy_dependencies(
            now_utc=DEC15_OPEN_UTC,
            runtime_config={"cmd": "myagy run"},
        )
    for bad_task_cmd in ("claude-main-research", "--no-claude-cli-login", "/usr/bin/claude-main-research"):
        with pytest.raises(fw.FreeTierFirewallError, match="ACTIVE_CLAUDE_SCHEDULED_TASK_FORBIDDEN"):
            fw.verify_zero_claude_and_agy_dependencies(
                now_utc=DEC15_OPEN_UTC,
                scheduled_tasks=[{"name": "SneakyTask", "enabled": True, "cmd": bad_task_cmd}],
            )

    # Pure legacy workspace directory path metadata + non-Claude command with disable flag stays clean.
    res = fw.verify_zero_claude_and_agy_dependencies(
        now_utc=DEC15_OPEN_UTC,
        runtime_config={
            "main_research_dir": r"A:\Capital Chronicle\ResearchRuns\claude-main-research\capture.json",
            "ops_dir": r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\codex-exec",
        },
        scheduled_tasks=[
            {
                "name": "DailyDigest1900",
                "enabled": True,
                "command": "python scripts/run_daily_digest_1900.py --driver python-neo --no-claude-cli-login",
                "main_root": r"A:\Capital Chronicle\ResearchRuns\claude-main-research",
            }
        ],
    )
    assert res["status"] == "PASS"


@pytest.mark.parametrize("bad_text,expected_code", [
    ("Routed via acct_DUR343723 and login_279805139.", "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ("Account DUR-343723 and DUR 343723 active.", "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ("Watch US500m and XAUUSDm and USTECm today.", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"),
    ("FX raw broker tickers EURUSDm, USDJPYm, USOILm, BTCUSDm.", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"),
])
def test_c24_da10_m1_broker_ids_and_raw_cfd_suffixes_blocked(bad_text: str, expected_code: str):
    """DA10-T2B-M1: underscore/hyphen/space broker IDs and Decision 107 raw CFD m-suffix symbols fail closed."""
    payload = _clean_outbound_payload(text=bad_text)
    with pytest.raises(fw.FreeTierFirewallError) as exc_info:
        fw.verify_cc024_commercial_firewall(payload)
    codes = {v["code"] for v in exc_info.value.violations}
    assert expected_code in codes, f"Expected {expected_code}, got {codes}"
    for v in exc_info.value.violations:
        assert "DUR343723" not in v.get("detail", "")
        assert "279805139" not in v.get("detail", "")


@pytest.mark.parametrize("bad_keys,expected_code", [
    ({"gold_stop_loss": 3920.0, "xauusd_take_profit": 4210.0}, "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ({"desk_lot_size": 0.05, "xauusd_kelly_weight": 0.12}, "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ({"goldStopLoss": 3920.0, "xauusdTakeProfit": 4210.0, "deskKellyFraction": 0.04}, "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ({"kalshi_odds_pct": 86, "fedwatch_cut_probability": 0.863}, "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ({"gap_pp": 14.2, "polymarket_yes_price": 0.78}, "CC024_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ({"Kelly f* = 0.042": 1}, "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ({"stop-loss 3920.50": 1}, "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
    ({"acct_DUR343723": 1}, "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"),
])
def test_c24_da10_m2_prefixed_camelcase_and_hostile_dict_keys_blocked_and_redacted(
    bad_keys: dict[str, Any], expected_code: str
):
    """DA10-T2B-M2: snake_case/camelCase private-alpha, CC-791 odds, and hostile private dict keys blocked & redacted."""
    payload = _clean_outbound_payload(**bad_keys)
    with pytest.raises(fw.FreeTierFirewallError) as exc_info:
        fw.verify_cc024_commercial_firewall(payload)
    codes = {v["code"] for v in exc_info.value.violations}
    assert expected_code in codes, f"Expected {expected_code}, got {codes}"
    for secret_key in bad_keys:
        for v in exc_info.value.violations:
            assert secret_key not in v.get("location", ""), f"Unredacted key leaked in location: {v}"
            assert secret_key not in v.get("detail", ""), f"Unredacted key leaked in detail: {v}"
            assert "<REDACTED_KEY#" in v.get("location", "")


def test_c24_da10_m3_lone_utf16_surrogates_in_values_and_keys_fail_closed():
    """DA10-T2B-M3: lone UTF-16 surrogates in values, keys, or JSON bytes raise INVALID_UNICODE_SURROGATE cleanly."""
    with pytest.raises(fw.FreeTierFirewallError, match="INVALID_UNICODE_SURROGATE"):
        fw.verify_cc024_commercial_firewall(_clean_outbound_payload(text="Hello \ud800 world."))
    with pytest.raises(fw.FreeTierFirewallError, match="INVALID_UNICODE_SURROGATE") as exc_k:
        fw.verify_cc024_commercial_firewall(_clean_outbound_payload(**{"bad\ud800key": "ok"}))
    assert "<REDACTED_KEY#" in exc_k.value.violations[0]["location"]
    # Confirm violation payload itself encodes cleanly as UTF-8
    json.dumps(exc_k.value.violations).encode("utf-8")

    with pytest.raises(fw.FreeTierFirewallError, match="INVALID_UNICODE_SURROGATE"):
        fw.verify_free_only_mode(_clean_outbound_payload(**{"bad\udfffkey": "ok"}), now_utc=DEC15_OPEN_UTC)
    with pytest.raises(fw.FreeTierFirewallError, match="INVALID_UNICODE_SURROGATE"):
        fw.canonical_json({"bad\ud800key": "ok"})
    with pytest.raises(fw.FreeTierFirewallError, match="INVALID_UNICODE_SURROGATE"):
        fw.load_strict_json_bytes(b'{"a": "\\ud800"}')


def test_c24_polish_url_schemes_oversized_int_private_zero_arena_null_ads_and_restored_dry_run(tmp_path: Path):
    """Polish: unsafe URL schemes, 10**5000 guards, private_only=0, Arena null kind/sleeve, ADS/trailing-dot, L3/L4/#155 L3."""
    # DA10-T2B-L1: unsafe URL schemes blocked
    for bad_url in (
        "javascript:alert(1)",
        "vbscript:msgbox(1)",
        "data:text/html,<script>alert(1)</script>",
        "javascript%3aalert(1)",
        "javascript&#58;alert(1)",
    ):
        with pytest.raises(fw.FreeTierFirewallError, match="CC024_UNSAFE_URL_SCHEME_FORBIDDEN"):
            fw.verify_cc024_commercial_firewall(_clean_outbound_payload(url=bad_url))

    # B16C22-N4: private_only / public_export_forbidden falsy 0 / 0.0 / Decimal(0) fail closed
    for zero_val in (0, 0.0, Decimal(0)):
        with pytest.raises(fw.FreeTierFirewallError, match="CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"):
            fw.verify_cc024_commercial_firewall(_clean_outbound_payload(private_only=zero_val))
        with pytest.raises(fw.FreeTierFirewallError, match="CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"):
            fw.verify_cc024_commercial_firewall(_clean_outbound_payload(public_export_forbidden=zero_val))

    # B16C22-N4: 10**5000 never raises uncaught ValueError (4,300-digit int str limit)
    huge = 10**5000
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN"):
        fw.verify_cc024_commercial_firewall(_clean_outbound_payload(series_id=huge, private_only=huge))
    with pytest.raises(fw.FreeTierFirewallError, match="FREE_TIER_DESTINATION_INVALID"):
        fw.verify_outbound_free_payload(_clean_outbound_payload(), now_utc=DEC15_OPEN_UTC, destination=huge)  # type: ignore[arg-type]
    with pytest.raises(fw.FreeTierFirewallError, match="EDITORIAL_AGENT_INVALID"):
        fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, editorial_agent=huge)  # type: ignore[arg-type]
    with pytest.raises(fw.FreeTierFirewallError, match="DIGEST_1900_DRIVER_INVALID"):
        fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, digest_driver=huge)  # type: ignore[arg-type]
    with pytest.raises(fw.FreeTierFirewallError, match="LIVE_PROVIDER_INVALID"):
        fw.verify_zero_claude_and_agy_dependencies(now_utc=DEC15_OPEN_UTC, live_provider=huge)  # type: ignore[arg-type]
    with pytest.raises(fw.FreeTierFirewallError, match="PAUSE_MANIFEST_FREE_ONLY_MODE_REQUIRED"):
        fw.verify_pause_manifest_for_dec15_unpause(
            {**_valid_dec15_pause_manifest(), "unpause_mode": huge, "cc024_clean_required": huge},
            now_utc=DEC15_OPEN_UTC,
        )

    # B16C22-N4: Arena hash-chain rejects record_kind=None and sleeve_id=None
    p_sha = fw.sha256_canonical({"event": "test"})
    rec_id_null = "arena_" + fw.sha256_canonical(
        [1, "", "", "2026-12-02T13:00:00Z", fw.GENESIS_PREV_SHA256, p_sha]
    )[:24]
    env_null_kind = {
        "schema": fw.ARENA_LEDGER_SCHEMA,
        "schema_version": "1.0.0",
        "sequence": 1,
        "record_id": rec_id_null,
        "record_kind": None,
        "sleeve_id": "l4_macro",
        "cutoff_utc": "2026-12-02T13:00:00Z",
        "known_at_max_utc": "2026-12-02T12:55:00Z",
        "prev_record_sha256": fw.GENESIS_PREV_SHA256,
        "payload_sha256": p_sha,
        "private_only": True,
        "public_export_forbidden": True,
        "payload": {"event": "test"},
    }
    row_null_kind = {**env_null_kind, "record_sha256": fw.sha256_canonical(env_null_kind)}
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_RECORD_KIND_INVALID"):
        fw.verify_day1_hash_chain([row_null_kind], max_clock_utc=DEC15_OPEN_UTC)

    env_null_sleeve = {**env_null_kind, "record_kind": "DECISION_SEAL", "sleeve_id": None}
    row_null_sleeve = {**env_null_sleeve, "record_sha256": fw.sha256_canonical(env_null_sleeve)}
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_SLEEVE_ID_INVALID"):
        fw.verify_day1_hash_chain([row_null_sleeve], max_clock_utc=DEC15_OPEN_UTC)

    # B16C22-N4: Windows trailing dot & NTFS ADS rejected on manifest and hash-chain paths
    mpath = tmp_path / "manifest.json"
    mpath.write_text(json.dumps(_valid_dec15_pause_manifest()) + "\n", encoding="utf-8")
    with pytest.raises(fw.FreeTierFirewallError, match="PAUSE_MANIFEST_PATH_INVALID"):
        fw.verify_pause_manifest_for_dec15_unpause(str(mpath) + ".", now_utc=DEC15_OPEN_UTC)
    with pytest.raises(fw.FreeTierFirewallError, match="PAUSE_MANIFEST_PATH_INVALID"):
        fw.verify_pause_manifest_for_dec15_unpause(str(mpath) + ":hidden", now_utc=DEC15_OPEN_UTC)

    cpath = _write_jsonl(tmp_path / "chain_ads.jsonl", _build_arena_chain_records(1))
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_PATH_INVALID"):
        fw.verify_day1_hash_chain(str(cpath) + ".")
    with pytest.raises(fw.FreeTierFirewallError, match="TRACK_RECORD_CHAIN_PATH_INVALID"):
        fw.verify_day1_hash_chain(str(cpath) + ":hidden")

    # B16C22-L3: compact TP1:3985 / USTEC:TP1:25000 blocked even in status/primary_reason
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_PRICE_TARGET_FORBIDDEN"):
        fw.verify_cc024_commercial_firewall(_clean_outbound_payload(status="TP1:3985"))
    with pytest.raises(fw.FreeTierFirewallError) as exc_tp:
        fw.verify_cc024_commercial_firewall(_clean_outbound_payload(primary_reason="USTEC:TP1:25000"))
    assert {"CC024_PRICE_TARGET_FORBIDDEN", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"} <= {
        v["code"] for v in exc_tp.value.violations
    }

    # #155 L3: compact private_texts echo caught in Section 2 even inside skipped technical ID keys
    compact_secret = "CONFIDENTIAL_DESK_TOKEN_ALPHA_9876543210"
    with pytest.raises(fw.FreeTierFirewallError, match="CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN"):
        fw.verify_cc024_commercial_firewall(
            _clean_outbound_payload(id=compact_secret),
            private_texts=[compact_secret],
        )

    # B16C22-L4: restored.json with dry_run=True fails closed even under allow_already_restored=True
    (tmp_path / "restored.json").write_text(
        json.dumps({"started_at_utc": "2026-12-15T00:00:00Z", "dry_run": True}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(fw.FreeTierFirewallError, match="RESTORED_MARKER_DRY_RUN_FORBIDDEN"):
        fw.verify_pause_manifest_for_dec15_unpause(
            mpath, now_utc=DEC15_OPEN_UTC, allow_already_restored=True
        )
    (tmp_path / "restored.json").write_text(
        json.dumps({"started_at_utc": "2026-12-15T00:00:00Z", "dry_run": False}) + "\n",
        encoding="utf-8",
    )
    assert fw.verify_pause_manifest_for_dec15_unpause(
        mpath, now_utc=DEC15_OPEN_UTC, allow_already_restored=True
    )["status"] == "PASS"
