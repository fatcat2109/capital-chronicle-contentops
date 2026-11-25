"""CC-817 offline dry-run and acceptance tests for the public market attention map.

Strictly offline (tmp_path + fake runners only; zero network calls, zero live
posting, zero writes to A:\\). Covers:
- Allow-list projection of §4.A / CC-807 theme register (stripping private
  responses, open positions, sizes, X-list posts, wire headlines, and market-
  implied numeric odds).
- Thursday 3 Dec dry run: weekly lead section ("The week ahead: what the market
  is watching"), top 5 detailed themes + remaining live themes 1-line each,
  merged coming-week calendar, and one immutable web-only Substack page per
  top theme (with TradingView chart binding across all 7 markets incl. USTEC).
- Sunday 6 Dec wrap integration via market_wrap_editorial_v1 + short platform
  copy leading with top 3 themes + canonical link across X, Threads, Telegram,
  Discord, LinkedIn, Instagram, Facebook, YouTube.
- Daily wrap one-line link for a mid-week Thursday/triggered theme change.
- Immutability / change-detection acceptance test: changed theme creates a new
  dated page linking the earlier page; unchanged theme creates NO new page and
  prints "no change since <ET date>" linking the latest page.
- All five public filters + voice + traceability refusals (Kalshi/Polymarket/
  FedWatch numbers, unnamed market-odds percentages, profit targets, X-list
  text/handles, DEMO/size/prepared-response leaks, non-ET clocks, AI labels,
  preview hosts, raw CFD codes, unbound figures).
- Codex gpt-6.2-sol high-effort theme-page drafting with fake runner (never agy)
  and deterministic code fallback on failure or filter rejection.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json

import pytest

from live_contentops import market_attention_map_public_v1 as attention
from live_contentops import market_wrap_editorial_v1 as wrap_editorial
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_market_wrap_cc689 import at, cash, pack, select_first  # noqa: F401
from test_tradingview_snapshot_cc314 import FIXTURE as TV_FIXTURE

THU_3_DEC = datetime(2026, 12, 3, 13, 0, tzinfo=timezone.utc)
SUN_6_DEC = datetime(2026, 12, 6, 15, 0, tzinfo=timezone.utc)


def _theme(
    theme_id: str,
    rank: int,
    name: str,
    one_line: str,
    *,
    lead_market: str = "USDJPY",
    status: str = "active",
    base_summary: str = "Rate differential widens as the Fed holds firm while the Bank of Japan stays gradual.",
    base_prob: int = 55,
    base_inv: str = "Bank of Japan signals an earlier hike or US real yields fall sharply.",
    bull_summary: str = "Dollar strengthens further against the yen on firmer US yields.",
    bull_prob: int = 25,
    bear_summary: str = "Carry unwinds drive a rapid yen rebound below the watch line.",
    bear_prob: int = 20,
    dp_at_utc: str = "2026-12-09T19:00:00Z",
    dp_title: str = "FOMC rate decision",
) -> dict:
    return {
        "theme_id": theme_id,
        "rank": rank,
        "name": name,
        "one_line": one_line,
        "status": status,
        "first_seen_utc": "2026-11-24T12:00:00Z",
        "updated_at_utc": "2026-12-03T12:00:00Z",
        "lead_market": lead_market,
        "affected_markets": [lead_market, "XAUUSD"] if lead_market != "XAUUSD" else ["XAUUSD", "US500"],
        "causal_chains": [
            {
                "event": name,
                "channel": "US and Japan front-end rate gap",
                "asset": lead_market,
                "sign": "higher if yields widen",
                "rough_size": "0.8 to 1.2 normal days",
            },
        ],
        "branches": [
            {
                "kind": "base",
                "summary": base_summary,
                "probability_pct": base_prob,
                "probability_source": "capital_chronicle",
                "market_lean_words": "rate futures lean toward a steady path",
                "invalidation": base_inv,
            },
            {
                "kind": "bull",
                "summary": bull_summary,
                "probability_pct": bull_prob,
                "probability_source": "capital_chronicle",
                "invalidation": "Yield spread narrows across two sessions.",
            },
            {
                "kind": "bear",
                "summary": bear_summary,
                "probability_pct": bear_prob,
                "probability_source": "kalshi",  # must be stripped from numeric output!
                "market_lean_words": "prediction markets treat a surprise reversal as unlikely",
                "invalidation": "Carry stays calm through the policy window.",
            },
        ],
        "market_lean_words": "rate futures lean toward a measured path while options price modest event risk",
        "priced_in_words": "Rate futures already price most of the expected policy path.",
        "computed_metrics": [
            {"label": "Options-implied event move (Capital Chronicle calculation)", "value": "0.9 normal days"},
            {"label": "Gamma regime (Capital Chronicle calculation)", "value": "neutral gamma"},
        ],
        "decision_points": [
            {
                "id": f"dp-{theme_id}",
                "title": dp_title,
                "at_utc": dp_at_utc,
                "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
                "watch_signals": [
                    {"kind": "official_page", "label": "Federal Reserve statement", "url": "https://www.federalreserve.gov"},
                    {"kind": "price_watch", "label": "160.00 yen intervention watch line"},
                    # Private signals below MUST be stripped by allow-list:
                    {"kind": "x_account", "label": "@FirstSquawk fast wire"},
                    {"kind": "x_list", "label": "https://x.com/DeItaone/status/12345"},
                ],
            },
        ],
        "history": [
            {"at_utc": "2026-11-30T13:00:00Z", "summary": "Opened theme ahead of the December central-bank meetings."},
            {"at_utc": "2026-12-03T12:00:00Z", "summary": "Refreshed causal chains after Wednesday US close."},
        ],
        # Private fields below MUST NEVER enter public output:
        "prepared_responses": [
            {"instrument": "USDJPY", "direction": "BUY", "stop": "0.5 normal days", "lane": "SHORT", "size": "0.5 lots"}
        ],
        "surprise_map": {"least_priced": "bear", "hurts_open_positions": ["DEMO 279805139"]},
        "x_list_posts": [
            {"text": "Private X-list wire rumor about unnamed central bank officials leaking early."}
        ],
        "wire_headlines": [
            {"headline": "Private Bloomberg wire copy that must never appear in public pages."}
        ],
    }


def sample_register(as_of: datetime = THU_3_DEC) -> dict:
    return {
        "schema_version": "cc807.theme_register.v1",
        "as_of_utc": as_of.isoformat(),
        "themes": [
            _theme("fed-boj-usdjpy", 1, "Fed and Bank of Japan rate gap",
                   "US yields and Bank of Japan policy drive the dollar-yen path near intervention levels",
                   lead_market="USDJPY", dp_at_utc="2026-12-09T19:00:00Z", dp_title="FOMC policy decision"),
            _theme("ai-capex-nasdaq", 2, "AI spending and chip leadership",
                   "Semiconductor demand and governance headlines steer Nasdaq 100 risk appetite",
                   lead_market="USTEC", dp_at_utc="2026-12-10T21:00:00Z", dp_title="Major chipmaker earnings call"),
            _theme("us-real-yields-gold", 3, "US real yields and gold demand",
                   "Real-rate direction and central-bank demand set the pace for gold",
                   lead_market="XAUUSD", dp_at_utc="2026-12-08T13:30:00Z", dp_title="US inflation release"),
            _theme("oil-supply-geopolitics", 4, "Crude supply and shipping risk",
                   "Supply discipline and transit risks keep WTI crude oil sensitive to headlines",
                   lead_market="USOIL", dp_at_utc="2026-12-11T15:30:00Z", dp_title="EIA petroleum report"),
            _theme("eurozone-growth-spread", 5, "Eurozone growth and rate spread",
                   "European growth data and rate expectations steer the euro against the dollar",
                   lead_market="EURUSD", dp_at_utc="2026-12-10T13:15:00Z", dp_title="ECB policy statement"),
            _theme("bitcoin-liquidity-flows", 6, "Bitcoin liquidity and fund flows",
                   "Dollar liquidity and spot fund flows guide Bitcoin momentum",
                   lead_market="BTCUSD", status="emerging",
                   dp_at_utc="2026-12-12T18:00:00Z", dp_title="Weekly fund flow tally"),
            _theme("sp500-earnings-breadth", 7, "S&P 500 breadth outside mega-caps",
                   "Index breadth tests whether gains extend beyond large technology names",
                   lead_market="US500", status="resolving",
                   dp_at_utc="2026-12-11T13:30:00Z", dp_title="US retail sales release"),
            _theme("past-resolved-theme", 8, "November election volatility",
                   "Post-election repricing has completed",
                   lead_market="US500", status="resolved",
                   dp_at_utc="2026-11-28T13:30:00Z", dp_title="Completed tally"),
        ],
    }


def _tv_asset(tmp_path, market: str = "USTEC") -> dict:
    snap = {
        "path": str(TV_FIXTURE),
        "sha256": sha256(TV_FIXTURE.read_bytes()).hexdigest(),
        "tv_symbol": tv.SYMBOLS[market],
        "interval": "240",
        "interval_label": "4h",
        "chart_url": tv.chart_url(tv.SYMBOLS[market], "240"),
        "page_title": "NDX 25,120.00" if market == "USTEC" else "USDJPY 158.90",
        "captured_at_utc": THU_3_DEC.isoformat(),
        "capture_ratio": "16:9",
    }
    return tv.snapshot_asset(market, attention.PUBLIC_MARKET_LABELS[market], snap, tmp_path / "media")


def test_allow_list_strips_private_fields_x_signals_and_market_odds_numbers():
    raw = sample_register()
    public = attention.project_public_register(raw, as_of_utc=THU_3_DEC)
    serialized = json.dumps({k: v for k, v in public.items() if k != "_private_texts"})
    for forbidden in ("prepared_responses", "surprise_map", "279805139", "0.5 lots",
                      "@FirstSquawk", "DeItaone", "Bloomberg wire", "Private X-list"):
        assert forbidden not in serialized
    first = public["themes"][0]
    # Base (capital_chronicle) keeps 55; Bear (kalshi) drops numeric 20 and keeps words only!
    assert first["branches"][0]["probability_pct"] == 55
    assert first["branches"][2]["probability_pct"] is None
    assert "unlikely" in first["branches"][2]["market_lean_words"]
    assert public["top_theme_ids"] == [
        "fed-boj-usdjpy", "ai-capex-nasdaq", "us-real-yields-gold",
        "oil-supply-geopolitics", "eurozone-growth-spread",
    ]
    assert "past-resolved-theme" not in public["live_theme_ids"]


def test_thursday_3_dec_dry_run_renders_weekly_section_and_five_immutable_theme_pages(tmp_path):
    public = attention.project_public_register(sample_register(THU_3_DEC), as_of_utc=THU_3_DEC)
    decisions = attention.plan_theme_pages(public, prior_pages={}, as_of_utc=THU_3_DEC)
    new_decisions = [d for d in decisions if d["action"] == "NEW_DATED_PAGE"]
    assert len(new_decisions) == 5

    store = ContentOpsDurableStore(tmp_path / "cc817.sqlite3")
    page_links = {}
    for decision in new_decisions:
        theme = next(t for t in public["themes"] if t["theme_id"] == decision["theme_id"])
        chart = _tv_asset(tmp_path / theme["theme_id"], theme["lead_market"]) if theme["lead_market"] == "USTEC" else None
        page = attention.render_theme_page(
            theme,
            as_of_utc=THU_3_DEC,
            reason=decision["reason"],
            chart_asset=chart,
            private_texts=public["_private_texts"],
        )
        assert page["web_only"] is True and page["send_email"] is False and page["never_edit"] is True
        body = page["native_payload"]["body_markdown"]
        assert "ET" in body and "GMT+7" not in body and "UTC" not in body
        assert "Kalshi" not in body and "Polymarket" not in body and "FedWatch" not in body
        assert "USTEC" not in body and "USDJPY" not in body and "XAUUSD" not in body
        assert attention.PUBLIC_NOTICE in body and attention.CONFLICTS_NOTICE in body
        if theme["lead_market"] == "USTEC":
            assert page["chart_requirement"]["tv_symbol"] == "NASDAQ:NDX"
            assert "Nasdaq 100 (NQ futures)" in body

        stored = attention.register_theme_page(store, page, output_dir=tmp_path / "pages")
        assert stored["plan"]["destinations"][0]["substack_delivery_mode"] == "WEB_ONLY"
        # Re-registering identical page is idempotent; mutating it is refused.
        assert attention.register_theme_page(store, page, output_dir=tmp_path / "pages")["page_id"] == page["page_id"]
        mutated = deepcopy(page)
        mutated["native_payload"]["body_markdown"] += "\nEdited."
        with pytest.raises(ValueError, match="CC817_THEME_PAGE_IMMUTABLE"):
            attention.register_theme_page(store, mutated, output_dir=tmp_path / "pages")
        page_links[theme["theme_id"]] = f"https://capitalchronicle.substack.com/p/{theme['theme_id']}-2026-12-03"

    section = attention.render_weekly_section(public, page_links=page_links, page_decisions=decisions)
    assert section["markdown"].startswith("## The week ahead: what the market is watching")
    assert len(section["top_theme_ids"]) == 5
    assert len(section["other_theme_ids"]) == 2
    assert len(section["top_three_lines"]) == 3
    assert "### Other live themes" in section["markdown"]
    assert "Bitcoin liquidity and fund flows" in section["markdown"]
    for url in page_links.values():
        assert url in section["markdown"]
    with pytest.raises(ValueError, match="CC817_THEME_PAGE_IMMUTABLE"):
        attention.require_immutable_theme_page({"attention_map_theme_page": stored["page_id"]})


def test_changed_theme_makes_new_page_linking_earlier_and_unchanged_theme_makes_none():
    first_reg = attention.project_public_register(sample_register(THU_3_DEC), as_of_utc=THU_3_DEC)
    prior_pages = {}
    for theme in first_reg["themes"][:5]:
        page = attention.render_theme_page(theme, as_of_utc=THU_3_DEC)
        prior_pages[theme["theme_id"]] = {
            "page_id": page["page_id"],
            "canonical_url": f"https://capitalchronicle.substack.com/p/{theme['theme_id']}-dec-3",
            "published_at_utc": THU_3_DEC.isoformat(),
            "revision_fingerprint": page["revision_fingerprint"],
            "base_case_fingerprint": page["base_case_fingerprint"],
            "branch_flip_signature": page["branch_flip_signature"],
        }

    # On Sunday 6 Dec: theme 1 base case changes; themes 2..5 are unchanged.
    raw_sun = sample_register(SUN_6_DEC)
    raw_sun["themes"][0]["updated_at_utc"] = SUN_6_DEC.isoformat()
    raw_sun["themes"][0]["branches"][0]["summary"] = "Bank of Japan hawkish shift narrows the rate gap and pulls the yen stronger."
    raw_sun["themes"][0]["branches"][0]["probability_pct"] = 60
    second_reg = attention.project_public_register(raw_sun, as_of_utc=SUN_6_DEC)

    decisions = attention.plan_theme_pages(second_reg, prior_pages=prior_pages, as_of_utc=SUN_6_DEC)
    by_id = {d["theme_id"]: d for d in decisions}

    assert by_id["fed-boj-usdjpy"]["action"] == "NEW_DATED_PAGE"
    assert by_id["fed-boj-usdjpy"]["reason"] == "BASE_CASE_CHANGED"
    for unchanged_id in ("ai-capex-nasdaq", "us-real-yields-gold", "oil-supply-geopolitics", "eurozone-growth-spread"):
        assert by_id[unchanged_id]["action"] == "UNCHANGED_LINK_LATEST"
        assert by_id[unchanged_id]["no_change_since_et"] == "December 3, 2026"
        assert by_id[unchanged_id]["latest_page_url"] == prior_pages[unchanged_id]["canonical_url"]

    new_page = attention.render_theme_page(
        second_reg["themes"][0],
        as_of_utc=SUN_6_DEC,
        reason=by_id["fed-boj-usdjpy"]["reason"],
        previous_page=by_id["fed-boj-usdjpy"]["previous_page"],
    )
    assert new_page["page_id"] != prior_pages["fed-boj-usdjpy"]["page_id"]
    assert new_page["previous_page_url"] == prior_pages["fed-boj-usdjpy"]["canonical_url"]
    assert f"Earlier edition (December 3, 2026): {prior_pages['fed-boj-usdjpy']['canonical_url']}" in new_page["native_payload"]["body_markdown"]

    links = {
        "fed-boj-usdjpy": "https://capitalchronicle.substack.com/p/fed-boj-usdjpy-dec-6",
        **{tid: prior_pages[tid]["canonical_url"] for tid in prior_pages if tid != "fed-boj-usdjpy"},
    }
    section = attention.render_weekly_section(second_reg, page_links=links, page_decisions=decisions)
    assert "no change since December 3, 2026" in section["markdown"]
    assert "https://capitalchronicle.substack.com/p/fed-boj-usdjpy-dec-6" in section["markdown"]


def test_sunday_and_daily_wrap_integration_and_all_platform_short_social_copies(tmp_path, pack):
    # 1. Sunday 6 Dec wrap carries the new lead section, merged calendar, and top-3 social lead.
    raw_sun = sample_register(SUN_6_DEC)
    public = attention.project_public_register(raw_sun, as_of_utc=SUN_6_DEC)
    links = {tid: f"https://capitalchronicle.substack.com/p/{tid}-dec-6" for tid in public["top_theme_ids"]}
    weekly_pack = deepcopy(pack)
    weekly_pack["slot"] = {
        "id": "cc689-weekly-2026-12-06",
        "edition": "weekly",
        "day_et": "2026-12-06",
        "start_utc": SUN_6_DEC.isoformat(),
        "deadline_utc": "2026-12-06T18:00:00+00:00",
    }
    weekly_pack["source_pack_as_of_utc"] = SUN_6_DEC.isoformat()
    weekly_pack["market_close_date"] = "2026-12-04"
    weekly_pack["attention_map"] = {"register": public, "page_links": links}

    manuscript = wrap_editorial.draft(weekly_pack, tmp_path / "weekly", call=select_first)
    article, _ = wrap_editorial.article_for(weekly_pack, manuscript)
    body = article["substack_body_markdown"]
    assert body.startswith("## The week ahead: what the market is watching")
    assert body.index("## The week ahead: what the market is watching") < body.index("## What changed since the last wrap")
    assert "FOMC policy decision (Fed and Bank of Japan rate gap)" in body

    canonical = "https://capitalchronicle.substack.com/p/weekend-market-wrap-2026-12-06"
    for dest in ("x", "threads", "telegram", "discord", "linkedin", "linkedin_company",
                 "instagram_business", "facebook_page", "youtube", "substack_notes"):
        social = wrap_editorial.derivative_payload(article, [], canonical, dest)
        assert canonical in social["full_text"]
        assert "Fed and Bank of Japan rate gap" in social["full_text"]
        assert "AI spending and chip leadership" in social["full_text"]
        assert "US real yields and gold demand" in social["full_text"]
        assert social["hard_truncation_used"] is False
        if dest == "x":
            assert all(len(p["text"]) <= 280 for p in social["posts"])

    # 2. Daily wrap carries one line with link for a mid-week Thursday theme change (no new slot).
    daily_pack = deepcopy(pack)
    daily_pack["attention_map_updates"] = [
        {
            "theme_name": "Fed and Bank of Japan rate gap",
            "date_et": "December 3, 2026",
            "summary": "Base case updated after Bank of Japan guidance shifted",
            "canonical_url": "https://capitalchronicle.substack.com/p/fed-boj-usdjpy-dec-3",
        }
    ]
    daily_manuscript = wrap_editorial.draft(daily_pack, tmp_path / "daily", call=select_first)
    daily_article, _ = wrap_editorial.article_for(daily_pack, daily_manuscript)
    assert "## Theme updates" in daily_article["substack_body_markdown"]
    assert "https://capitalchronicle.substack.com/p/fed-boj-usdjpy-dec-3" in daily_article["substack_body_markdown"]


@pytest.mark.parametrize("bad_line,cause", [
    ("Kalshi prices a hike at 68%.", "PREDICTION_MARKET_NUMBER_FORBIDDEN"),
    ("Polymarket shows 72% odds on the vote.", "PREDICTION_MARKET_NUMBER_FORBIDDEN"),
    ("CME FedWatch shows 95.1% for a hold.", "PREDICTION_MARKET_NUMBER_FORBIDDEN"),
    ("Priced in: Fed hike 100%.", "ATTENTION_MAP_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("Futures price 85% for a December cut.", "ATTENTION_MAP_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("Our profit target is 162.50 on the yen.", "SCENARIO_VOICE_TARGET_FORBIDDEN"),
    ("Price target at 4,200 on gold.", "SCENARIO_VOICE_TARGET_FORBIDDEN"),
    ("Posted on https://x.com/FirstSquawk/status/999.", "PLAN_ANALYSIS_PRIVATE_X_LIST_FORBIDDEN"),
    ("According to @FirstSquawk, officials met.", "ATTENTION_MAP_X_HANDLE_FORBIDDEN"),
    ("Release arrives at 20:30 GMT+7.", "PUBLIC_TIMEZONE_ET_REQUIRED"),
    ("Decision arrives at 19:00 UTC.", "ATTENTION_MAP_NON_ET_CLOCK_FORBIDDEN"),
    ("Written by Claude on our AI-run desk.", "PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN"),
    ("Our prepared response enters 0.5 lots.", "ATTENTION_MAP_BOOK_OR_RESPONSE_FORBIDDEN"),
    ("Preview at https://fatcat2109.github.io/theme.", "PREVIEW_HOST_LINK_FORBIDDEN"),
    ("USTEC moves higher on yields.", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"),
    ("Base case sees a 77.7% chance of a surge.", "ATTENTION_MAP_UNBOUND_FIGURE"),
])
def test_public_filters_refuse_every_cc817_prohibited_pattern(bad_line, cause):
    public = attention.project_public_register(sample_register(THU_3_DEC), as_of_utc=THU_3_DEC)
    text = f"{bad_line}\n\n{attention.PUBLIC_NOTICE}\n{attention.CONFLICTS_NOTICE}"
    with pytest.raises(ValueError, match=cause):
        attention.validate_attention_map_copy(
            text,
            public_theme=public["themes"][0],
            require_notice=True,
            private_texts=public["_private_texts"],
        )


def test_codex_high_effort_drafting_uses_codex_never_agy_and_falls_back_on_violation(tmp_path):
    public = attention.project_public_register(sample_register(THU_3_DEC), as_of_utc=THU_3_DEC)
    theme = public["themes"][0]
    seen = []

    def good_codex(prompt, **kwargs):
        seen.append((kwargs["callers"], kwargs["codex_effort"], kwargs["job"]))
        answer = {
            "scenarios": (
                "Base case (55%, Capital Chronicle estimate): Rate differential widens as the Fed holds firm.\n"
                "What would prove the base case wrong: Bank of Japan signals an earlier hike.\n"
                "Bull case (25%, Capital Chronicle estimate): Dollar strengthens further on firmer US yields.\n"
                "Bear case: Carry unwinds drive a rapid yen rebound."
            ),
            "causal_chains": "- USD/JPY (6J futures reference): Fed and Bank of Japan rate gap via US and Japan front-end rate gap.",
            "priced_in": "Rate futures already price most of the expected policy path.",
        }
        return json.dumps(answer).encode("utf-8"), {"status": "RETURNED", "caller": "codex"}

    page, rec = attention.draft_theme_page_with_codex(
        theme, as_of_utc=THU_3_DEC, output_dir=tmp_path / "good", call=good_codex
    )
    assert seen == [(("codex",), "high", "attention_map_theme_page")]
    assert rec["result"] == "PASS" and rec["fallback"] is None
    assert "Base case (55%, Capital Chronicle estimate)" in page["native_payload"]["body_markdown"]

    def bad_codex(prompt, **kwargs):
        answer = {
            "scenarios": "Kalshi prices this branch at 91% with a price target of 165.",
            "causal_chains": "USD/JPY (6J futures reference) reacts.",
            "priced_in": "FedWatch 95%.",
        }
        return json.dumps(answer).encode("utf-8"), {"status": "RETURNED", "caller": "codex"}

    fallback_page, bad_rec = attention.draft_theme_page_with_codex(
        theme, as_of_utc=THU_3_DEC, output_dir=tmp_path / "bad", call=bad_codex
    )
    assert bad_rec["result"] == "FAIL" and bad_rec["fallback"] == "code"
    assert "Kalshi" not in fallback_page["native_payload"]["body_markdown"]
    assert "91%" not in fallback_page["native_payload"]["body_markdown"]
    assert "Base case (55%, Capital Chronicle estimate)" in fallback_page["native_payload"]["body_markdown"]


def test_x1_direct_project_public_register_strips_internal_r_multiple_computed_metrics():
    """[X1] Direct callers to project_public_register never trip on Main CC-807 internal R-multiple computed_metrics."""
    raw = sample_register(THU_3_DEC)
    raw["themes"][1]["computed_metrics"] = [
        {"label": "Replay range on confirmation", "value": "+0.30R to +0.75R with half-normal-day stop"},
        {"label": "Speed expectancy", "value": "+0.23R 3h move"},
        {"label": "Historical 1d move", "value": "1.4% median (Capital Chronicle computed)"},
    ]
    raw["themes"][1]["open_position_impacts"] = [
        {"summary": "Confidential semiconductor desk memo alpha-delta-canary."}
    ]

    public = attention.project_public_register(raw, as_of_utc=THU_3_DEC)
    theme = next(t for t in public["themes"] if t["theme_id"] == "ai-capex-nasdaq")
    assert theme["computed_metrics"] == [
        {"label": "Historical 1d move", "value": "1.4% median (Capital Chronicle computed)"}
    ]
    assert "+0.30R to +0.75R with half-normal-day stop" in public["_private_texts"]

    page = attention.render_theme_page(theme, as_of_utc=THU_3_DEC)
    page_md = page["native_payload"]["body_markdown"]
    assert "+0.30R" not in page_md and "+0.75R" not in page_md and "half-normal-day stop" not in page_md
    assert "+0.23R" not in page_md
    assert "Historical 1d move: 1.4% median (Capital Chronicle computed)" in page_md
    attention.validate_attention_map_copy(page_md, public_register=public, require_notice=True)

    section = attention.render_weekly_section(public)
    assert "+0.30R" not in section["markdown"] and "half-normal-day stop" not in section["markdown"]
    attention.validate_attention_map_copy(section["markdown"], public_register=public, require_notice=False)

    # Adversarial verbatim echo of stripped internal R-multiple metric or open-position canary remains refused.
    with pytest.raises(ValueError):
        attention.validate_attention_map_copy(
            "Nasdaq 100 (NQ futures) sees +0.30R to +0.75R with half-normal-day stop.",
            public_register=public,
            require_notice=False,
        )
    with pytest.raises(ValueError, match="PLAN_ANALYSIS_PRIVATE_X_LIST_FORBIDDEN"):
        attention.validate_attention_map_copy(
            "Confidential semiconductor desk memo alpha-delta-canary.",
            public_register=public,
            require_notice=False,
        )


def test_x1_market_wrap_editorial_normalizes_raw_main_cc807_register_directly(tmp_path, pack):
    """[X1] Passing raw un-normalized Main CC-807 JSON directly into market_wrap_editorial_v1 strips R-multiples cleanly."""
    raw_main_cc807 = {
        "schema": "MarketAttentionMapRegisterV1",
        "as_of_utc": SUN_6_DEC.isoformat(),
        "themes": [
            {
                "theme_id": "nvidia_leadership_ai_capex",
                "name": "Semiconductor leadership and AI capital spending",
                "one_line": "Semiconductor guidance drives Nasdaq 100 and S&P 500 leadership.",
                "status": "active",
                "rank": 1,
                "first_seen_utc": THU_3_DEC.isoformat(),
                "updated_at_utc": SUN_6_DEC.isoformat(),
                "lead_market": "USTEC",
                "affected_markets": ["USTEC", "US500"],
                "causal_chains": [
                    {
                        "asset": "USTEC",
                        "event": "data-center demand guidance",
                        "channel": "earnings revision",
                        "direction": "bullish",
                        "rough_size": "one to two normal days",
                    }
                ],
                "branches": [
                    {
                        "branch_id": "base_capex_holds",
                        "kind": "base",
                        "summary": "Cloud spending guidance holds firm and supports Nasdaq 100 leadership.",
                        "probability_pct": 55,
                        "probability_source": "capital_chronicle",
                        "invalidation": "Hyperscaler guidance cuts capex materially.",
                    },
                    {
                        "branch_id": "alt_export_curbs",
                        "kind": "alternative",
                        "summary": "Tighter export rules cool semiconductor momentum.",
                        "probability_pct": 45,
                        "probability_source": "capital_chronicle",
                        "invalidation": "Licensing terms stay unchanged.",
                    },
                ],
                "computed_metrics": [
                    {"label": "Replay range on confirmation", "value": "+0.30R to +0.75R with half-normal-day stop"},
                    {"label": "Historical 1d move", "value": "1.6% median (Capital Chronicle computed)"},
                ],
                "prepared_responses": [{"note": "INTERNAL ONLY: arm equity index order on release."}],
                "open_position_impacts": [{"note": "INTERNAL ONLY: current book sizing canary string."}],
                "decision_points": [
                    {
                        "id": "dp_nvda_conf",
                        "event": "Semiconductor industry conference update",
                        "at_utc": "2026-12-08T14:00:00+00:00",
                        "watch_condition": "Forward data-center demand commentary",
                    }
                ],
            }
        ],
    }

    weekly_pack = deepcopy(pack)
    weekly_pack["slot"] = {
        "id": "cc689-weekly-2026-12-06",
        "edition": "weekly",
        "day_et": "2026-12-06",
        "start_utc": SUN_6_DEC.isoformat(),
        "deadline_utc": "2026-12-06T18:00:00+00:00",
    }
    weekly_pack["source_pack_as_of_utc"] = SUN_6_DEC.isoformat()
    weekly_pack["market_close_date"] = "2026-12-04"
    weekly_pack["attention_map"] = {"register": raw_main_cc807}

    manuscript = wrap_editorial.draft(weekly_pack, tmp_path / "weekly-raw-cc807", call=select_first)
    article, _ = wrap_editorial.article_for(weekly_pack, manuscript)
    body = article["substack_body_markdown"]
    assert body.startswith("## The week ahead: what the market is watching")
    assert "Semiconductor leadership and AI capital spending" in body
    assert "+0.30R" not in body and "+0.75R" not in body and "half-normal-day stop" not in body
    assert "INTERNAL ONLY" not in body
    assert "USTEC" not in body

    social = wrap_editorial.derivative_payload(
        article, [], "https://capitalchronicle.substack.com/p/weekend-wrap-2026-12-06", "x"
    )
    assert all(len(p["text"]) <= 280 for p in social["posts"])
    assert "+0.30R" not in social["full_text"] and "INTERNAL ONLY" not in social["full_text"]
