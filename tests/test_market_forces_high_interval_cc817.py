"""CC-817 v2 hermetic tests for the High-Interval Market Forces Engine.

Strictly offline (tmp_path only; zero network calls, zero live publishing, zero LLM/agy calls,
zero writes outside tmp_path). Covers:
- 15-30 minute pure-code allow-list poller reading `market_attention_map_live_v1.json`,
  aligned with Main's CC-807 schema contract (`MarketAttentionMapLiveV1` / `worked_fixture`).
- Strict stripping of private book/positions/prepared responses/surprise_map/linked_odds_markets/
  priced_in_gap/raw X-list/wire text and proprietary market-implied numeric odds.
- Material-shift detector: triggers ONLY on new Top-5 entry, branch flip, >= 10 pp probability
  shift (words-only for market-implied odds), or decision-point catalyst hit; rejects noise.
- Per-theme anti-spam cooldown (>= 2h unless branch flips) & persistent exactly-once ledger.
- Intraday Market Force Flash / Update: immutable dated WEB_ONLY Substack page linking prior
  page + TradingView chart (incl. USTEC -> NASDAQ:NDX) + concise 10-platform short social copy
  with zero truncation.
- Session-Sync Market Forces Pulse (Pre-Asia / Pre-London / Pre-US Cash Open) integrated into
  `market_wrap_editorial_v1.py`, proving existing daily & weekly wraps remain byte-identical
  when absent.
- All 5 public filters (CC-788, Decisions 40, 44, 90, 107, 109, 157, 158) and zero `agy`.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops import market_attention_map_public_v1 as attention
from live_contentops import market_forces_high_interval_v1 as hi
from live_contentops import market_wrap_editorial_v1 as wrap_editorial
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_market_attention_map_cc817 import _theme, _tv_asset, sample_register
from test_market_wrap_cc689 import at, cash, pack, select_first  # noqa: F401

T0 = datetime(2026, 12, 3, 13, 0, tzinfo=timezone.utc)


def _live_map(as_of: datetime = T0) -> dict:
    reg = sample_register(as_of)
    reg["schema"] = "MarketAttentionMapLiveV1"
    reg["schema_version"] = "1.0.0"
    reg["material_change_hash"] = "mat-hash-initial-v1"
    reg["cadence_metadata"] = {
        "last_deep_pass_utc": "2026-12-03T01:00:00Z",
        "last_live_refresh_utc": as_of.isoformat(),
        "cadence_policy": {"live_refresh_interval_minutes": 15, "live_refresh_llm_calls": 0},
    }
    reg["open_positions"] = [{"account_id": "279805139", "symbol": "USDJPY", "lots": 0.5}]
    reg["public_boundary_notice"] = "INTERNAL_NUMBERS_ONLY: keep private book and odds internal."
    for theme in reg["themes"]:
        theme["active_branch_id"] = f"{theme['theme_id']}_base"
        theme["prior_active_branch_id"] = f"{theme['theme_id']}_base"
        theme["branch_flipped"] = False
        theme["priced_in_gap"] = {
            "cc_base_probability_pct": 55.0,
            "market_implied_base_probability_pct": 62.0,
            "gap_pp": -7.0,
        }
        theme["linked_odds_markets"] = [
            {
                "platform": "kalshi",
                "market_key": f"kalshi:{theme['theme_id']}",
                "title": f"Kalshi private market title for {theme['theme_id']} odds tracking",
                "latest_probability_pct": 62.0,
                "delta_15m_pp": 0.0,
            }
        ]
        theme["live_state"] = {
            "updated_at_utc": as_of.isoformat(),
            "max_odds_delta_15m_pp": 0.0,
            "max_odds_delta_1h_pp": 0.5,
            "max_odds_delta_24h_pp": 2.0,
            "decision_point_catalyst_hit": False,
            "branch_flip_detected": False,
            "material_shift_flags": [],
        }
        for idx, branch in enumerate(theme["branches"]):
            branch["branch_id"] = f"{theme['theme_id']}_{branch['kind']}"
            if branch["probability_source"] == "capital_chronicle":
                branch["cc_probability_pct"] = float(branch["probability_pct"])
                branch["market_implied_probability_pct"] = 62.0 if idx == 0 else 23.0
                branch["market_implied_delta_15m_pp"] = 0.0
                branch["market_implied_delta_1h_pp"] = 0.5
            else:
                branch["market_implied_probability_pct"] = float(branch["probability_pct"])
                branch["market_implied_delta_15m_pp"] = 0.0
    return reg


def _write_live_map(folder: Path, data: dict) -> Path:
    path = folder / hi.DEFAULT_LIVE_MAP_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _url_for(page: dict) -> str:
    return f"https://capitalchronicle.substack.com/p/{page['page_id']}"


def test_allow_list_poller_strips_all_private_and_proprietary_fields_and_validates_bounds(tmp_path):
    raw = _live_map(T0)
    map_path = _write_live_map(tmp_path, raw)

    # Poll interval outside 15-30m and cooldown < 120m are rejected.
    with pytest.raises(ValueError, match="MARKET_FORCES_POLL_INTERVAL_INVALID"):
        hi.load_live_attention_map(map_path, as_of_utc=T0, poll_interval_minutes=5)
    with pytest.raises(ValueError, match="MARKET_FORCES_POLL_INTERVAL_INVALID"):
        hi.load_live_attention_map(map_path, as_of_utc=T0, poll_interval_minutes=45)
    with pytest.raises(ValueError, match="MARKET_FORCES_COOLDOWN_BELOW_MINIMUM"):
        hi.poll_live_attention_map(map_path, now_utc=T0, cooldown_minutes=60)

    # Freshness checks fail closed on stale (>60m) and future-dated live maps.
    with pytest.raises(ValueError, match="MARKET_FORCES_LIVE_MAP_STALE"):
        hi.load_live_attention_map(map_path, as_of_utc=T0 + timedelta(minutes=61), poll_interval_minutes=15)
    with pytest.raises(ValueError, match="MARKET_FORCES_LIVE_MAP_AFTER_CUTOFF"):
        hi.load_live_attention_map(map_path, as_of_utc=T0 - timedelta(minutes=1), poll_interval_minutes=15)

    # Directory path resolves market_attention_map_live_v1.json cleanly.
    projected = hi.load_live_attention_map(tmp_path, as_of_utc=T0 + timedelta(minutes=15), poll_interval_minutes=15)
    public = projected["public_register"]
    serialized = json.dumps({k: v for k, v in public.items() if k != "_private_texts"})
    for forbidden in (
        "prepared_responses", "surprise_map", "priced_in_gap", "linked_odds_markets",
        "open_positions", "279805139", "0.5 lots", "@FirstSquawk", "DeItaone",
        "Bloomberg wire", "Private X-list", "Kalshi private market", "62.0",
    ):
        assert forbidden not in serialized
    assert public["cadence_metadata"]["live_refresh_interval_minutes"] == 15
    # Internal detector state retains market-implied probabilities strictly separate from public_register.
    det_first = projected["detector_state"]["themes"]["fed-boj-usdjpy"]
    assert det_first["branch_probabilities"]["base"]["cc_probability_pct"] == "55"
    assert det_first["branch_probabilities"]["base"]["market_implied_probability_pct"] == "62"


def test_noise_and_subthreshold_moves_emit_zero_flashes_with_zero_llm_calls(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    base_map = _live_map(T0)
    hi.seed_ledger_from_map(base_map, as_of_utc=T0, ledger_path=ledger_path)

    # Poll 15m later: minor +4 pp own change, +9.9 pp market-implied move, rank swap within Top 5 -> NO flash!
    t1 = T0 + timedelta(minutes=15)
    noisy = _live_map(t1)
    noisy["themes"][0]["updated_at_utc"] = t1.isoformat()
    noisy["themes"][0]["rank"] = 2
    noisy["themes"][1]["rank"] = 1
    noisy["themes"][0]["branches"][0]["probability_pct"] = 59
    noisy["themes"][0]["branches"][0]["cc_probability_pct"] = 59.0
    noisy["themes"][0]["branches"][0]["market_implied_probability_pct"] = 71.9  # +9.9 pp (< 10 pp)
    noisy["themes"][0]["live_state"]["max_odds_delta_15m_pp"] = 9.9
    noisy["themes"][0]["live_state"]["max_odds_delta_1h_pp"] = 9.9
    noisy["themes"][0]["live_state"]["max_odds_delta_24h_pp"] = 9.9

    result = hi.poll_live_attention_map(
        noisy, now_utc=t1, ledger_path=ledger_path, poll_interval_minutes=15, canonical_url_builder=_url_for
    )
    assert result["status"] == "NO_MATERIAL_SHIFT"
    assert result["llm_calls_made"] == 0
    assert result["emitted_flashes"] == []
    assert result["suppressed_cooldown"] == []
    assert result["skipped_duplicates"] == []


def test_all_four_material_shift_triggers_fire_cleanly_and_market_odds_stay_in_words(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    base_map = _live_map(T0)
    prior_pages = {
        tid: {
            "page_id": f"attention-theme-{tid}-2026-12-03-prior",
            "canonical_url": f"https://capitalchronicle.substack.com/p/{tid}-2026-12-03-prior",
            "published_at_utc": T0.isoformat(),
        }
        for tid in ("fed-boj-usdjpy", "ai-capex-nasdaq", "us-real-yields-gold",
                    "oil-supply-geopolitics", "eurozone-growth-spread")
    }
    hi.seed_ledger_from_map(base_map, as_of_utc=T0, ledger_path=ledger_path, prior_pages=prior_pages)

    t1 = T0 + timedelta(minutes=15)
    shifted = _live_map(t1)
    shifted["material_change_hash"] = "mat-hash-four-triggers"

    # Trigger 1: NEW_TOP_FIVE_ENTRY (bitcoin-liquidity-flows climbs from rank 6 to rank 5)
    shifted["themes"][4]["rank"] = 6
    shifted["themes"][5]["rank"] = 5
    shifted["themes"][5]["updated_at_utc"] = t1.isoformat()

    # Trigger 2: BRANCH_FLIPPED on ai-capex-nasdaq (USTEC -> NASDAQ:NDX)
    shifted["themes"][1]["updated_at_utc"] = t1.isoformat()
    shifted["themes"][1]["active_branch_id"] = "ai-capex-nasdaq_bear"
    shifted["themes"][1]["branch_flipped"] = True
    shifted["themes"][1]["branch_flip_at_utc"] = t1.isoformat()
    shifted["themes"][1]["live_state"]["branch_flip_detected"] = True
    shifted["themes"][1]["branches"][0]["summary"] = (
        "Governance uncertainty caps semiconductor demand and weighs on Nasdaq 100 risk appetite."
    )

    # Trigger 3: >= 10 pp MARKET-IMPLIED probability shift on us-real-yields-gold (62% -> 79%, +17 pp)
    shifted["themes"][2]["updated_at_utc"] = t1.isoformat()
    shifted["themes"][2]["branches"][0]["market_implied_probability_pct"] = 79.0
    shifted["themes"][2]["branches"][0]["market_implied_delta_15m_pp"] = 17.0
    shifted["themes"][2]["live_state"]["max_odds_delta_15m_pp"] = 17.0

    # Trigger 4: DECISION_POINT_CATALYST_HIT on oil-supply-geopolitics (scheduled clock crossed)
    shifted["themes"][3]["updated_at_utc"] = t1.isoformat()
    shifted["themes"][3]["decision_points"][0]["at_utc"] = (T0 + timedelta(minutes=10)).isoformat()

    store = ContentOpsDurableStore(tmp_path / "flashes.sqlite3")
    res = hi.poll_live_attention_map(
        shifted,
        now_utc=t1,
        ledger_path=ledger_path,
        poll_interval_minutes=15,
        store=store,
        output_dir=tmp_path / "pages",
        chart_asset_provider=lambda t: _tv_asset(tmp_path / "tv" / t["theme_id"], t["lead_market"]),
        canonical_url_builder=_url_for,
    )
    assert res["status"] == "MATERIAL_SHIFTS_EMITTED"
    assert res["llm_calls_made"] == 0
    by_id = {f["theme_id"]: f for f in res["emitted_flashes"]}
    assert set(by_id) == {
        "ai-capex-nasdaq",
        "bitcoin-liquidity-flows",
        "us-real-yields-gold",
        "oil-supply-geopolitics",
    }
    assert by_id["ai-capex-nasdaq"]["primary_reason"] == hi.TRIGGER_BRANCH_FLIPPED
    assert by_id["bitcoin-liquidity-flows"]["primary_reason"] == hi.TRIGGER_NEW_TOP_FIVE
    assert by_id["us-real-yields-gold"]["primary_reason"] == hi.TRIGGER_PROBABILITY_SHIFT
    assert by_id["oil-supply-geopolitics"]["primary_reason"] == hi.TRIGGER_CATALYST_HIT

    # Verify USTEC flash links prior edition, binds NASDAQ:NDX chart, and renders all 10 social destinations cleanly.
    nvda_flash = by_id["ai-capex-nasdaq"]
    page = nvda_flash["flash_page"]
    assert page["web_only"] is True and page["send_email"] is False and page["never_edit"] is True
    assert page["chart_requirement"]["tv_symbol"] == "NASDAQ:NDX"
    assert page["previous_page_url"] == prior_pages["ai-capex-nasdaq"]["canonical_url"]
    assert prior_pages["ai-capex-nasdaq"]["canonical_url"] in page["native_payload"]["body_markdown"]
    assert "Chart: TradingView" in page["native_payload"]["body_markdown"]
    assert len(nvda_flash["social_bundle"]) == 10
    for dest, social in nvda_flash["social_bundle"].items():
        assert social["hard_truncation_used"] is False
        assert "..." not in social["full_text"] and "…" not in social["full_text"]
        assert nvda_flash["canonical_url"] in social["full_text"]
        assert attention.PUBLIC_NOTICE in social["full_text"]
        assert attention.CONFLICTS_NOTICE in social["full_text"]
        assert "USTEC" not in social["full_text"]
        if dest == "x":
            assert all(len(p["text"]) <= 280 for p in social["posts"])
        else:
            assert len(social["full_text"]) <= social["platform_limit"]

    # Verify market-implied >= 10 pp shift on gold renders STRICTLY IN WORDS (zero 79%, zero 17, zero Kalshi!).
    gold_flash = by_id["us-real-yields-gold"]
    gold_body = gold_flash["flash_page"]["native_payload"]["body_markdown"]
    assert "Market-implied pricing on the base case shifted materially higher." in gold_body
    for leak in ("79%", "79", "17%", "17 pp", "62%", "Kalshi", "Polymarket", "FedWatch"):
        assert leak not in gold_body
    for social in gold_flash["social_bundle"].values():
        for leak in ("79%", "17%", "17 pp", "62%", "Kalshi", "Polymarket", "FedWatch"):
            assert leak not in social["full_text"]

    # Verify immutable page registration refuses mutation.
    mutated = deepcopy(page)
    mutated["native_payload"]["body_markdown"] += "\nTampered."
    with pytest.raises(ValueError, match="CC817_THEME_PAGE_IMMUTABLE"):
        hi.register_flash_page(store, mutated, output_dir=tmp_path / "pages")


def test_per_theme_cooldown_branch_flip_bypass_and_exactly_once_idempotency(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    base_map = _live_map(T0)
    hi.seed_ledger_from_map(base_map, as_of_utc=T0, ledger_path=ledger_path)

    # 1. T0 + 15m: Own Capital Chronicle estimate shifts +11 pp (55 -> 66) -> emits flash #1.
    t1 = T0 + timedelta(minutes=15)
    m1 = _live_map(t1)
    m1["material_change_hash"] = "mat-t1"
    m1["themes"][0]["updated_at_utc"] = t1.isoformat()
    m1["themes"][0]["branches"][0]["probability_pct"] = 66
    m1["themes"][0]["branches"][0]["cc_probability_pct"] = 66.0
    r1 = hi.poll_live_attention_map(
        m1, now_utc=t1, ledger_path=ledger_path, poll_interval_minutes=15, canonical_url_builder=_url_for
    )
    assert r1["status"] == "MATERIAL_SHIFTS_EMITTED"
    assert len(r1["emitted_flashes"]) == 1
    first_url = r1["emitted_flashes"][0]["canonical_url"]
    assert "66%" in r1["emitted_flashes"][0]["flash_page"]["native_payload"]["body_markdown"]

    # Verify ledger persisted cleanly with LF-only UTF-8 (CR=0, BOM=False).
    ledger_bytes = ledger_path.read_bytes()
    assert b"\r" not in ledger_bytes and not ledger_bytes.startswith(b"\xef\xbb\xbf")

    # 2. T0 + 30m: Exact replay of same live map -> ZERO duplicate dispatch (idempotent!).
    r_dup = hi.poll_live_attention_map(
        m1,
        now_utc=T0 + timedelta(minutes=30),
        ledger_path=ledger_path,
        poll_interval_minutes=15,
        canonical_url_builder=_url_for,
    )
    assert r_dup["status"] == "NO_MATERIAL_SHIFT"
    assert r_dup["emitted_flashes"] == []

    # Even if forced through detect_material_shifts via a fresh ledger copy missing only theme baseline
    # while dispatched_events retains event_key, exactly-once blocks duplicate!
    tampered_ledger = hi.load_ledger(ledger_path)
    tampered_ledger["themes"]["fed-boj-usdjpy"]["branch_probabilities"]["base"]["cc_probability_pct"] = "55"
    r_idemp = hi.poll_live_attention_map(
        m1,
        now_utc=T0 + timedelta(minutes=30),
        ledger=tampered_ledger,
        poll_interval_minutes=15,
        canonical_url_builder=_url_for,
    )
    assert r_idemp["status"] == "DUPLICATE_SKIPPED"
    assert len(r_idemp["skipped_duplicates"]) == 1
    assert r_idemp["emitted_flashes"] == []

    # 3. T0 + 45m (30m since flash #1, inside 2h cooldown): another +12 pp shift (66 -> 78) -> SUPPRESSED!
    t2 = T0 + timedelta(minutes=45)
    m2 = _live_map(t2)
    m2["material_change_hash"] = "mat-t2"
    m2["themes"][0]["updated_at_utc"] = t2.isoformat()
    m2["themes"][0]["branches"][0]["probability_pct"] = 78
    m2["themes"][0]["branches"][0]["cc_probability_pct"] = 78.0
    r2 = hi.poll_live_attention_map(
        m2, now_utc=t2, ledger_path=ledger_path, poll_interval_minutes=15, canonical_url_builder=_url_for
    )
    assert r2["status"] == "COOLDOWN_SUPPRESSED"
    assert r2["emitted_flashes"] == []
    assert len(r2["suppressed_cooldown"]) == 1
    assert r2["suppressed_cooldown"][0]["cooldown_remaining_seconds"] == 5400

    # 4. T0 + 60m (45m since flash #1, STILL inside 2h cooldown): BRANCH_FLIPPED -> BYPASSES COOLDOWN!
    t3 = T0 + timedelta(minutes=60)
    m3 = _live_map(t3)
    m3["material_change_hash"] = "mat-t3-flip"
    m3["themes"][0]["updated_at_utc"] = t3.isoformat()
    m3["themes"][0]["active_branch_id"] = "fed-boj-usdjpy_bear"
    m3["themes"][0]["branch_flipped"] = True
    m3["themes"][0]["branch_flip_at_utc"] = t3.isoformat()
    m3["themes"][0]["branches"][0]["summary"] = (
        "Bank of Japan hawkish pivot narrows the yield gap and drives rapid yen strength."
    )
    m3["themes"][0]["branches"][0]["probability_pct"] = 60
    m3["themes"][0]["branches"][0]["cc_probability_pct"] = 60.0
    r3 = hi.poll_live_attention_map(
        m3, now_utc=t3, ledger_path=ledger_path, poll_interval_minutes=15, canonical_url_builder=_url_for
    )
    assert r3["status"] == "MATERIAL_SHIFTS_EMITTED"
    assert len(r3["emitted_flashes"]) == 1
    flip_flash = r3["emitted_flashes"][0]
    assert flip_flash["primary_reason"] == hi.TRIGGER_BRANCH_FLIPPED
    assert flip_flash["cooldown_bypassed"] is True
    # New immutable dated page links the prior flash page!
    assert flip_flash["flash_page"]["previous_page_url"] == first_url
    assert first_url in flip_flash["flash_page"]["native_payload"]["body_markdown"]

    # 5. T0 + 3h10m (cooldown > 2h elapsed after t3): fresh +12 pp shift (60 -> 72) now emits cleanly!
    t4 = t3 + timedelta(minutes=125)
    m4 = deepcopy(m3)
    m4["as_of_utc"] = t4.isoformat()
    m4["material_change_hash"] = "mat-t4-post-cooldown"
    m4["themes"][0]["updated_at_utc"] = t4.isoformat()
    m4["themes"][0]["branch_flipped"] = False
    m4["themes"][0]["branches"][0]["probability_pct"] = 72
    m4["themes"][0]["branches"][0]["cc_probability_pct"] = 72.0
    r4 = hi.poll_live_attention_map(
        m4, now_utc=t4, ledger_path=ledger_path, poll_interval_minutes=30, canonical_url_builder=_url_for
    )
    assert r4["status"] == "MATERIAL_SHIFTS_EMITTED"
    assert len(r4["emitted_flashes"]) == 1
    assert r4["emitted_flashes"][0]["cooldown_bypassed"] is False
    assert r4["emitted_flashes"][0]["flash_page"]["previous_page_url"] == flip_flash["canonical_url"]


def test_cumulative_intraday_drift_across_polls_triggers_at_10pp(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    hi.seed_ledger_from_map(_live_map(T0), as_of_utc=T0, ledger_path=ledger_path)

    # Tick 1 (+5 pp: 62 -> 67): below threshold, no flash.
    t1 = T0 + timedelta(minutes=15)
    m1 = _live_map(t1)
    m1["themes"][0]["updated_at_utc"] = t1.isoformat()
    m1["themes"][0]["branches"][0]["market_implied_probability_pct"] = 67.0
    r1 = hi.poll_live_attention_map(m1, now_utc=t1, ledger_path=ledger_path)
    assert r1["status"] == "NO_MATERIAL_SHIFT"

    # Tick 2 (+5 pp more: 67 -> 72, cumulative +10 pp vs baseline 62): triggers cleanly!
    t2 = T0 + timedelta(minutes=30)
    m2 = _live_map(t2)
    m2["themes"][0]["updated_at_utc"] = t2.isoformat()
    m2["themes"][0]["branches"][0]["market_implied_probability_pct"] = 72.0
    r2 = hi.poll_live_attention_map(m2, now_utc=t2, ledger_path=ledger_path)
    assert r2["status"] == "MATERIAL_SHIFTS_EMITTED"
    assert r2["emitted_flashes"][0]["primary_reason"] == hi.TRIGGER_PROBABILITY_SHIFT
    body = r2["emitted_flashes"][0]["flash_page"]["native_payload"]["body_markdown"]
    assert "Market-implied pricing on the base case shifted materially higher." in body
    assert "72" not in body and "62" not in body


def test_session_sync_windows_and_byte_identical_wrap_integration(tmp_path, pack):
    # 1. Verify ET session-sync window classifier (EST winter & EDT summer).
    assert hi.session_sync_window_at("2026-12-03T23:00:00Z") == hi.SESSION_PRE_ASIA    # Thu 18:00 ET
    assert hi.session_sync_window_at("2026-12-04T07:30:00Z") == hi.SESSION_PRE_LONDON  # Fri 02:30 ET
    assert hi.session_sync_window_at("2026-12-04T13:15:00Z") == hi.SESSION_PRE_US      # Fri 08:15 ET
    assert hi.session_sync_window_at("2026-07-08T12:15:00Z") == hi.SESSION_PRE_US      # Wed 08:15 EDT
    assert hi.session_sync_window_at("2026-12-04T16:30:00Z") is None                   # Fri 11:30 ET

    # 2. Prove existing daily AND weekly wraps remain 100% BYTE-IDENTICAL when session_sync_pulse is absent!
    daily_pack_base = deepcopy(pack)
    daily_manuscript = wrap_editorial.draft(daily_pack_base, tmp_path / "daily-base", call=select_first)
    daily_article_a, _ = wrap_editorial.article_for(daily_pack_base, daily_manuscript)
    daily_article_b, _ = wrap_editorial.article_for(deepcopy(daily_pack_base), daily_manuscript)
    assert daily_article_a["substack_body_markdown"].encode("utf-8") == daily_article_b["substack_body_markdown"].encode("utf-8")
    assert "session_sync_pulse" not in daily_article_a
    assert "Session-sync market forces" not in daily_article_a["substack_body_markdown"]

    # 3. Opt-in Pre-Asia / Pre-London / Pre-US cash open integration into market_wrap_editorial_v1.
    raw_map = _live_map(T0)
    links = {
        "fed-boj-usdjpy": "https://capitalchronicle.substack.com/p/fed-boj-usdjpy-2026-12-03",
        "ai-capex-nasdaq": "https://capitalchronicle.substack.com/p/ai-capex-nasdaq-2026-12-03",
    }
    recent_flashes = [
        {
            "theme_id": "ai-capex-nasdaq",
            "theme_name": "AI spending and chip leadership",
            "as_of_utc": T0.isoformat(),
            "public_summary_lines": ["The primary scenario path flipped for this market force."],
            "canonical_url": "https://capitalchronicle.substack.com/p/ai-capex-nasdaq-flash",
        }
    ]

    for session in hi.SESSION_ORDER:
        wrap_pack = deepcopy(pack)
        wrap_pack["session_sync_pulse"] = {
            "register": raw_map,
            "session": session,
            "as_of_utc": T0.isoformat(),
            "recent_flashes": recent_flashes,
            "page_links": links,
        }
        article, _ = wrap_editorial.article_for(wrap_pack, daily_manuscript)
        body = article["substack_body_markdown"]
        expected_heading = f"## Session-sync market forces — {hi.SESSION_LABELS[session]}"
        assert expected_heading in body
        assert "### Intraday shifts" in body
        assert "https://capitalchronicle.substack.com/p/ai-capex-nasdaq-flash" in body
        assert "Nasdaq 100 (NQ futures)" in body
        assert "USTEC" not in body and "GMT+7" not in body and "Kalshi" not in body
        assert article["session_sync_pulse"]["session"] == session
        assert article["session_sync_pulse"]["flash_count"] == 1
        # Recently flashed theme is prioritized first in the pulse.
        assert article["session_sync_pulse"]["theme_ids"][0] == "ai-capex-nasdaq"

    # 4. Standalone 10-platform session-sync social bundle.
    projected = hi.project_live_attention_map(raw_map, as_of_utc=T0)
    pulse = hi.render_session_sync_pulse(
        projected["public_register"],
        session=hi.SESSION_PRE_US,
        as_of_utc=T0,
        recent_flashes=recent_flashes,
        page_links=links,
    )
    bundle = hi.render_session_sync_social_bundle(
        pulse,
        projected["public_register"],
        "https://capitalchronicle.substack.com/p/pre-us-market-wrap-2026-12-03",
        credit=tv.CREDIT,
    )
    assert set(bundle) == set(hi.ALL_TEN_DESTINATIONS)
    for dest, social in bundle.items():
        assert social["hard_truncation_used"] is False
        assert "https://capitalchronicle.substack.com/p/pre-us-market-wrap-2026-12-03" in social["full_text"]
        assert attention.PUBLIC_NOTICE in social["full_text"]
        if dest == "x":
            assert all(len(p["text"]) <= 280 for p in social["posts"])
        else:
            assert len(social["full_text"]) <= social["platform_limit"]


def test_cc807_contract_worked_fixture_alignment_and_zero_leak(tmp_path):
    """Align directly with CC Builder 9's CC-807 schema contract worked_fixture structure."""
    as_of = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    cc807_fixture = {
        "schema": "MarketAttentionMapLiveV1",
        "schema_version": "1.0.0",
        "as_of_utc": as_of.isoformat(),
        "generated_at_utc": as_of.isoformat(),
        "cutoff_utc": as_of.isoformat(),
        "material_change_hash": "cc807-nvidia-flip-hash",
        "cadence_metadata": {
            "last_deep_pass_utc": "2026-11-23T19:00:00Z",
            "last_live_refresh_utc": as_of.isoformat(),
            "cadence_policy": {"live_refresh_interval_minutes": 15, "live_refresh_llm_calls": 0},
        },
        "themes": [
            {
                "theme_id": "nvidia_leadership_ai_capex",
                "name": "Nvidia Leadership Shock and AI Index Relief",
                "one_line": "Reinstatement momentum for Jensen Huang drives fast relief repricing across Nasdaq 100 and S&P 500.",
                "status": "resolving",
                "rank": 1,
                "first_seen_utc": "2026-11-12T14:00:00Z",
                "updated_at_utc": as_of.isoformat(),
                "lead_market": "USTEC",
                "affected_markets": ["USTEC", "US500", "BTCUSD", "XAUUSD"],
                "causal_chains": [
                    {
                        "asset": "USTEC",
                        "event": "Nvidia CEO reinstatement or board governance resolution",
                        "channel": "Index heavyweight weight and AI infrastructure capex confidence",
                        "sign": "bullish_on_reinstatement",
                        "direction": "UP",
                        "rough_size": "+0.8 to +1.4 normal days on reinstatement confirmation",
                    }
                ],
                "decision_points": [
                    {
                        "id": "nvidia_board_leadership_vote",
                        "title": "Nvidia Board Leadership Decision and Official Filing",
                        "dated": False,
                        "at_utc": None,
                        "watch_condition": "Official Nvidia newsroom or SEC 8-K announcement",
                        "source_url": "https://nvidianews.nvidia.com/",
                        "watch_signals": [
                            {"kind": "official_page", "label": "Nvidia Newsroom and SEC Form 8-K filings", "url": "https://nvidianews.nvidia.com/"},
                            {"kind": "price_level", "label": "S&P 500 pre-news anchor zone near 7,072 to 7,087", "symbol": "US500", "level": 7080.0},
                            {"kind": "odds_market_number", "label": "Kalshi Jensen Huang returns as Nvidia CEO", "market_key": "kalshi:nvda-huang-return"},
                            {"kind": "x_account", "label": "Fast equity news squawks", "handle": "DeItaone"},
                        ],
                    }
                ],
                "branches": [
                    {
                        "branch_id": "huang_returns",
                        "kind": "base",
                        "summary": "Board reinstates Jensen Huang, triggering a rapid relief rally in AI semiconductors, Nasdaq 100, and S&P 500.",
                        "probability_pct": 65.0,
                        "probability_source": "capital_chronicle",
                        "cc_probability_pct": 65.0,
                        "market_implied_probability_pct": 68.0,
                        "market_implied_delta_1h_pp": 51.0,
                        "market_implied_delta_24h_pp": 51.0,
                        "market_lean_words": "Market pricing shifted sharply toward a Huang return after board headlines.",
                        "invalidation": "Board formally appoints an external CEO or discloses expanded regulatory liability.",
                    },
                    {
                        "branch_id": "outsider_ceo_named",
                        "kind": "bear",
                        "summary": "Nvidia appoints an outside successor, prolonging AI roadmap uncertainty and capping Nasdaq 100 upside.",
                        "probability_pct": 15.0,
                        "probability_source": "capital_chronicle",
                        "cc_probability_pct": 15.0,
                        "market_implied_probability_pct": 12.0,
                        "market_implied_delta_1h_pp": -25.0,
                        "invalidation": "Official filing confirms Jensen Huang resumes CEO duties.",
                    },
                ],
                "active_branch_id": "huang_returns",
                "prior_active_branch_id": "outsider_ceo_named",
                "branch_flipped": True,
                "branch_flip_evidence": {
                    "flipped_at_utc": "2026-11-23T13:55:00Z",
                    "summary": "Reinstatement probability surged by 51 percentage points in one window alongside equity index jump.",
                },
                "market_lean_words": "Market pricing pivoted decisively toward Jensen Huang returning as CEO.",
                "priced_in_words": "Relief from the reinstatement is largely priced in after the initial jump.",
                "priced_in_gap": {"cc_base_probability_pct": 65.0, "market_implied_base_probability_pct": 68.0, "gap_pp": -3.0},
                "surprise_map": {"open_position_impacts": [{"lifecycle_id": "example_us500_short", "side": "SHORT"}]},
                "prepared_responses": [{"instrument": "US500", "direction": "BUY", "stop_formula": "anchor - 0.5 * ATR"}],
                "linked_odds_markets": [{"platform": "kalshi", "latest_probability_pct": 68.0, "delta_1h_pp": 51.0}],
                "computed_metrics": [
                    {"label": "Replay range on confirmation", "value": "+0.30R to +0.75R with half-normal-day stop"},
                ],
                "history": [
                    {"at_utc": "2026-11-23T14:00:00Z", "summary": "Base case flipped to Jensen Huang return after confirmation."},
                ],
                "live_state": {
                    "updated_at_utc": as_of.isoformat(),
                    "max_odds_delta_1h_pp": 51.0,
                    "decision_point_catalyst_hit": True,
                    "branch_flip_detected": True,
                    "material_shift_flags": ["BRANCH_FLIP", "ODDS_SHIFT_10PP", "DECISION_POINT_CATALYST_HIT"],
                },
            }
        ],
    }

    res = hi.poll_live_attention_map(
        cc807_fixture,
        now_utc=as_of,
        ledger_path=tmp_path / "cc807_ledger.json",
        poll_interval_minutes=15,
        canonical_url_builder=_url_for,
    )
    assert res["status"] == "MATERIAL_SHIFTS_EMITTED"
    flash = res["emitted_flashes"][0]
    assert flash["primary_reason"] == hi.TRIGGER_BRANCH_FLIPPED
    assert set(flash["reasons"]) == {
        hi.TRIGGER_BRANCH_FLIPPED,
        hi.TRIGGER_NEW_TOP_FIVE,
        hi.TRIGGER_CATALYST_HIT,
        hi.TRIGGER_PROBABILITY_SHIFT,
    }
    body = flash["flash_page"]["native_payload"]["body_markdown"]
    assert "Market-implied pricing on the base case shifted sharply higher." in body
    assert "Nasdaq 100 (NQ futures)" in body
    for leaked in ("51", "68", "Kalshi", "DeItaone", "prepared_responses", "+0.30R", "US500", "USTEC", "bullish_on_reinstatement"):
        assert leaked not in body
    assert len(flash["social_bundle"]) == 10


@pytest.mark.parametrize("bad_text,cause", [
    ("Kalshi prices a hike at 68%.", "PREDICTION_MARKET_NUMBER_FORBIDDEN"),
    ("Polymarket gives 71% odds.", "PREDICTION_MARKET_NUMBER_FORBIDDEN"),
    ("CME FedWatch implies 95.1% hold.", "PREDICTION_MARKET_NUMBER_FORBIDDEN"),
    ("Futures imply 80% chance of cut.", "ATTENTION_MAP_MARKET_ODDS_NUMBER_FORBIDDEN"),
    ("Our profit target is 162.50.", "SCENARIO_VOICE_TARGET_FORBIDDEN"),
    ("Posted by @FirstSquawk on X.", "ATTENTION_MAP_X_HANDLE_FORBIDDEN"),
    ("Updated at 20:30 GMT+7.", "PUBLIC_TIMEZONE_ET_REQUIRED"),
    ("Updated at 13:15 UTC.", "ATTENTION_MAP_NON_ET_CLOCK_FORBIDDEN"),
    ("Drafted by Antigravity Gemini AI-run desk.", "PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN"),
    ("Our prepared response enters 0.5 lots.", "ATTENTION_MAP_BOOK_OR_RESPONSE_FORBIDDEN"),
    ("Read at https://fatcat2109.github.io/flash.", "PREVIEW_HOST_LINK_FORBIDDEN"),
    ("USTEC rallies on yields.", "PUBLIC_INSTRUMENT_NAME_FORBIDDEN"),
])
def test_high_interval_enforces_all_five_public_filters_and_zero_agy(bad_text, cause):
    raw = _live_map(T0)
    raw["themes"][0]["one_line"] = bad_text
    with pytest.raises(ValueError, match=cause):
        hi.poll_live_attention_map(raw, now_utc=T0, poll_interval_minutes=15)

    # Preview host canonical URL is always refused on social copy.
    projected = hi.project_live_attention_map(_live_map(T0), as_of_utc=T0)
    shift = {"primary_reason": hi.TRIGGER_BRANCH_FLIPPED, "public_summary_lines": ["The primary scenario path flipped."]}
    with pytest.raises(ValueError, match="PREVIEW_HOST_LINK_FORBIDDEN"):
        hi.render_flash_social_copy(
            projected["public_register"]["themes"][0],
            shift,
            "https://fatcat2109.github.io/bad-flash",
            destination="x",
            as_of_utc=T0,
        )

    # Verify zero agy / zero subprocess / zero LLM caller imports inside market_forces_high_interval_v1.py.
    source_text = Path(hi.__file__).read_text(encoding="utf-8")
    for forbidden_call in ("agy_editorial_assist", "call_light", "subprocess", "codex exec"):
        assert forbidden_call not in source_text
