"""Hermetic adversarial tests for Dec-15 FREE-tier public-disclosure & Rule A3 firewall."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from live_contentops import dec15_public_disclosure_firewall_v1 as fw

DEC15_BOUNDARY = "2026-12-14T17:00:00Z"
BEFORE_DEC15_US = "2026-12-14T16:59:59.999999Z"
BEFORE_DEC15_NS = "2026-12-14T16:59:59.999999999Z"
AFTER_DEC15 = "2026-12-14T17:05:00Z"
FIXTURES_CC691 = Path(__file__).parent / "fixtures" / "cc691" / "posts.json"


# ---------------------------------------------------------------------------
# Hermetic Clean FREE-Tier Fixtures & Pause Snapshot Helpers
# ---------------------------------------------------------------------------


def clean_post_payload() -> dict:
    return {
        "post_id": "cc-wrap-20261215-pre-us",
        "mode": "FREE_ONLY",
        "audience_tier": "FREE",
        "title": "Pre-US macro wrap: Treasury yields ease, gold steadies ahead of CPI",
        "subtitle": "This edition is free to read for all subscribers.",
        "published_at_utc": "2026-12-15T13:15:00Z",
        "display_time_et": "08:15 ET on 15 December 2026",
        "canonical_url": "https://capitalchronicle.substack.com/p/pre-us-macro-wrap-dec-15",
        "body_markdown": (
            "Federal Reserve balance sheet runoff slowed into year-end while the US trade balance "
            "narrowed to $68.5 billion and the current account balance improved. "
            "A 10-2 vote kept the federal funds target at 3.75 to 4 percent alongside the 2% inflation target. "
            "A lot of investors watched the 10-year Treasury yield slip 4 bps as gold traded near 4,050.\n\n"
            "## Scenarios\n"
            "Base case (55%): Gold holds its 4,027-4,147 range if CPI prints in line.\n"
            "Alternative case (25%): Upside break above 4,147 if core inflation cools.\n\n"
            "Capital Chronicle offers analysis only, not financial advice or recommendations. "
            "Capital Chronicle may hold positions in the markets it covers."
        ),
        "notices": [
            "Capital Chronicle offers analysis only, not financial advice or recommendations.",
            "Capital Chronicle may hold positions in the markets it covers.",
        ],
    }


def clean_educational_post_payload() -> dict:
    return {
        "post_id": "cc-edu-20261215-real-yields",
        "mode": "FREE_ONLY",
        "title": "How real yields transmit into gold and currency pricing",
        "published_at_utc": "2026-12-15T15:00:00Z",
        "canonical_url": "https://capitalchronicle.substack.com/p/real-yields-gold-primer",
        "body": (
            "Real yields measure nominal Treasury rates adjusted for inflation expectations. "
            "When real yields fall, non-yielding assets such as gold face lower opportunity cost. "
            "Capital Chronicle offers analysis only, not financial advice or recommendations."
        ),
    }


def clean_card_payload() -> dict:
    return {
        "card_id": "cc-card-us-cpi-20261215",
        "mode": "FREE_ONLY",
        "headline": "US Consumer Price Index (November release)",
        "tier": {
            "rights_class": "PUBLIC_FACT_IDENTITY",
            "source_ids": [],
            "use_label": "PUBLIC_FACT",
            "value": "T1",
            "visibility": "public",
        },
        "display_date_et": "15 December 2026, 08:30 ET",
        "known_at_utc": "2026-12-15T13:30:00Z",
        "rows": [
            {"label": "Headline CPI m/m", "value": 0.2, "unit": "percent", "decimals": 1},
            {"label": "Core CPI m/m", "value": 0.2, "unit": "percent", "decimals": 1},
        ],
        "source_attribution": "U.S. Bureau of Labor Statistics (public domain).",
        "notices": ["Capital Chronicle offers analysis only, not financial advice or recommendations."],
    }


def clean_caption_payload() -> dict:
    return {
        "caption_id": "cc-cap-xauusd-20261215",
        "platform": "instagram_business",
        "mode": "FREE_ONLY",
        "caption": (
            "Gold spot / US dollar (1h) ahead of the New York cash open at 08:15 ET. "
            "Chart: TradingView. Full free note on Substack. "
            "Capital Chronicle offers analysis only, not financial advice or recommendations."
        ),
        "alt_text": "TradingView 1h chart of Gold spot / US dollar, captured 08:10 ET on 15 December 2026.",
        "canonical_url": "https://capitalchronicle.substack.com/p/pre-us-macro-wrap-dec-15",
    }


def clean_chart_metadata_payload() -> dict:
    return {
        "asset_id": "tradingview-snapshot-20261215-xauusd",
        "mode": "FREE_ONLY",
        "width": 1524,
        "height": 858,
        "sha256": "a" * 64,
        "modality": "tradingview_chart_snapshot",
        "credit": "Chart: TradingView",
        "public_use_rights": "TRADINGVIEW_FREE_PUBLIC_SNAPSHOT",
        "rights_basis": "TradingView Terms of Use section 4: free pages only with visible attribution.",
        "caption": "Gold: 1h chart of Gold spot / US dollar (ICE). Chart: TradingView.",
        "alt_text": "TradingView 1h chart of Gold spot / US dollar, captured 08:10 ET on 15 December 2026.",
        "source_page_url": "https://www.tradingview.com/chart/?symbol=FX_IDC:XAUUSD&interval=60",
        "tradingview_snapshot": {
            "tv_symbol": "FX_IDC:XAUUSD",
            "chart_url": "https://www.tradingview.com/chart/?symbol=FX_IDC:XAUUSD&interval=60",
            "interval": "60",
            "captured_at_utc": "2026-12-15T13:10:00Z",
            "levels_drawn": [],
            "target_drawn": False,
        },
    }


def clean_digest_payload() -> dict:
    return {
        "digest_id": "cc-digest-20261215",
        "mode": "FREE_ONLY",
        "digest_date_et": "15 December 2026",
        "generated_at_utc": "2026-12-15T12:00:00Z",
        "headline": "Capital Chronicle daily link index — 15 December 2026 (ET)",
        "entries": [
            {
                "title": "Pre-US macro wrap: Treasury yields ease",
                "published_at_et": "08:15 ET",
                "canonical_url": "https://capitalchronicle.substack.com/p/pre-us-macro-wrap-dec-15",
            },
            {
                "title": "How real yields transmit into gold",
                "published_at_et": "10:00 ET",
                "canonical_url": "https://capitalchronicle.substack.com/p/real-yields-gold-primer",
            },
        ],
        "notices": ["Capital Chronicle offers analysis only, not financial advice or recommendations."],
    }


def make_pause_snapshot(
    tmp_path: Path,
    *,
    paused_at: str = "2026-11-23T04:56:22.3575958Z",
    resume_at: str = DEC15_BOUNDARY,
    stops: tuple[str, ...] = fw.PUBLISHER_STOPS,
    restored_at: str | None = None,
) -> tuple[Path, Path]:
    pause_dir = tmp_path / "pause"
    stops_dir = tmp_path / "stops"
    pause_dir.mkdir(parents=True, exist_ok=True)
    stops_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.dumps(
        {"paused_at_utc": paused_at, "resume_at_utc": resume_at, "cause": "DEC15_FREE_PAUSE"},
        indent=2,
    ) + "\n"
    (pause_dir / "manifest.json").write_bytes(manifest.encode("utf-8"))
    for name in stops:
        (stops_dir / name).write_bytes(b"paused\n")
    if restored_at is not None:
        restored = json.dumps({"started_at_utc": restored_at}) + "\n"
        (pause_dir / "restored.json").write_bytes(restored.encode("utf-8"))
    return pause_dir, stops_dir


def assert_receipt_hash_valid(receipt: dict) -> None:
    claimed = receipt["receipt_sha256"]
    assert isinstance(claimed, str) and len(claimed) == 64
    body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    expected = fw.sha256_hex(fw.canonical_json_bytes(body))
    assert claimed == expected


def assert_cc1011_free_audit_compatible(receipt: dict, *, as_of_utc: str) -> None:
    """Assert exact parity with CC-1011 (b18f527bfe07) _free_audit() contract."""
    audit = receipt["cc024_audit"]
    manifest_bytes = fw.canonical_json_bytes(receipt["release_manifest"])
    assert manifest_bytes.endswith(b"\n") and b"\r" not in manifest_bytes
    expected_digest = sha256(manifest_bytes).hexdigest()
    assert audit["mode"] == "FREE_ONLY"
    assert audit["candidate_sha256"] == expected_digest
    assert receipt["candidate_sha256"] == expected_digest
    assert type(audit["checked_artifact_count"]) is int and audit["checked_artifact_count"] > 0
    for count_field in ("paid_paywall_count", "affiliate_count", "raw_vendor_leak_count"):
        assert type(audit[count_field]) is int and audit[count_field] == 0
    assert fw._parse_utc_ns(audit["observed_at_utc"], "obs") <= fw._parse_utc_ns(as_of_utc, "as_of")


# ---------------------------------------------------------------------------
# 1. Positive Clean FREE-Tier Controls (All 5 Payload Kinds + CC-691 Parity)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "factory"),
    [
        ("post", clean_post_payload),
        ("post", clean_educational_post_payload),
        ("card", clean_card_payload),
        ("caption", clean_caption_payload),
        ("chart_metadata", clean_chart_metadata_payload),
        ("digest", clean_digest_payload),
    ],
)
def test_clean_free_tier_controls_pass_preflight_and_publish_after_dec15(tmp_path, kind, factory):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path, resume_at=DEC15_BOUNDARY)
    pre = fw.evaluate_payload(
        factory(),
        payload_kind=kind,
        as_of_utc=DEC15_BOUNDARY,
        gate_mode="preflight",
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert pre["verdict"] == fw.VERDICT_READY_FREE_UNPAUSE
    assert pre["publish_allowed"] is False
    assert pre["counts"]["total_findings"] == 0
    assert_receipt_hash_valid(pre)
    assert_cc1011_free_audit_compatible(pre, as_of_utc=DEC15_BOUNDARY)

    pub_pause, pub_stops = make_pause_snapshot(
        tmp_path / "live",
        resume_at=DEC15_BOUNDARY,
        stops=(),
        restored_at=DEC15_BOUNDARY,
    )
    pub = fw.evaluate_payload(
        factory(),
        payload_kind=kind,
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_dir=pub_pause,
        publisher_stops_dir=pub_stops,
    )
    assert pub["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH
    assert pub["publish_allowed"] is True
    assert pub["counts"]["total_findings"] == 0
    assert_receipt_hash_valid(pub)
    assert_cc1011_free_audit_compatible(pub, as_of_utc=AFTER_DEC15)


def test_payload_kind_aliases_and_unknown_kind_fail_closed(tmp_path):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    for alias, canonical in (
        ("chart-metadata", "chart_metadata"),
        ("market-wrap", "post"),
        ("daily-digest", "digest"),
    ):
        assert fw.normalize_payload_kind(alias) == canonical

    bad = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="private_signal_blast",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert bad["verdict"] == fw.VERDICT_BLOCKED
    assert bad["publish_allowed"] is False
    assert any(f["code"] == "UNSUPPORTED_PAYLOAD_KIND" for f in bad["findings"])
    assert bad["cc024_audit"]["mode"] == fw.VERDICT_BLOCKED


def test_cc691_committed_clean_fixtures_pass_and_pre_cc791_odds_wrap_blocks(tmp_path):
    posts = json.loads(FIXTURES_CC691.read_bytes().decode("utf-8"))
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)

    for kind, obj in (
        ("chart_metadata", posts["charts"]["gold"]["asset"]),
        ("chart_metadata", posts["charts"]["bitcoin"]["asset"]),
        ("post", {"text": posts["timed_plan_update"]["text"], "event_utc": posts["timed_plan_update"]["event_utc"]}),
        ("post", {"text": posts["plan_analysis_reply"]["text"], "canonical_url": posts["plan_analysis_reply"]["public_analysis_url"]}),
    ):
        rec = fw.evaluate_payload(
            obj,
            payload_kind=kind,
            as_of_utc=DEC15_BOUNDARY,
            pause_dir=pause_dir,
            publisher_stops_dir=stops_dir,
        )
        assert rec["verdict"] == fw.VERDICT_READY_FREE_UNPAUSE, rec["findings"]
        assert rec["counts"]["total_findings"] == 0

    # Historical 9 Nov daily wrap predated Decision 107 and uses raw CFD table symbols (USOIL/BTCUSD/XAUUSD/US500).
    daily_rec = fw.evaluate_payload(
        {"title": posts["wraps"]["daily"]["title"], "body": posts["wraps"]["daily"]["body_excerpt"]},
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert daily_rec["verdict"] == fw.VERDICT_BLOCKED
    assert {f["code"] for f in daily_rec["findings"]} == {"PUBLIC_RAW_CFD_SYMBOL_DECISION_107"}

    # Replacing those 4 pre-Decision-107 table tickers with Decision-107 instrument names makes the wrap clean.
    d107_body = (
        posts["wraps"]["daily"]["body_excerpt"]
        .replace("| USOIL |", "| WTI |")
        .replace("| BTCUSD |", "| Bitcoin |")
        .replace("| XAUUSD |", "| Gold |")
        .replace("| US500 |", "| S&P 500 |")
    )
    daily_clean_rec = fw.evaluate_payload(
        {"title": posts["wraps"]["daily"]["title"], "body": d107_body},
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert daily_clean_rec["verdict"] == fw.VERDICT_READY_FREE_UNPAUSE, daily_clean_rec["findings"]
    assert daily_clean_rec["counts"]["total_findings"] == 0

    # Historical 8 Nov weekend wrap predated CC-791 and contains "odds of a December Fed rate rise to about 78-80%".
    weekend_rec = fw.evaluate_payload(
        {"title": posts["wraps"]["weekend"]["title"], "body": posts["wraps"]["weekend"]["body_excerpt"]},
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert weekend_rec["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "PUBLIC_ODDS_LEAK_CC791" for f in weekend_rec["findings"])


# ---------------------------------------------------------------------------
# 2. Rule A3 Hostile Private-Alpha Leak Injections
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "mutator", "expected_code"),
    [
        # Kelly f* / g(f) / sizing / lot formulas
        ("kelly_f_star_text", lambda p: p.update(body_markdown="Optimal sizing uses f* = 0.042."), "RULE_A3_KELLY_SIZING_LOT_LEAK"),
        ("kelly_zwsp_evasion", lambda p: p.update(body_markdown="Use f\u200b* = 0.03 for growth."), "RULE_A3_KELLY_SIZING_LOT_LEAK"),
        ("kelly_gf_formula", lambda p: p.update(body_markdown="Geometric growth g(f) peaks at 1.8%."), "RULE_A3_KELLY_SIZING_LOT_LEAK"),
        ("half_kelly_text", lambda p: p.update(body_markdown="Desk runs half-Kelly sizing on gold."), "RULE_A3_KELLY_SIZING_LOT_LEAK"),
        ("lot_size_text", lambda p: p.update(body_markdown="Open 0.05 lots on XAUUSD."), "RULE_A3_KELLY_SIZING_LOT_LEAK"),
        ("position_sizing_text", lambda p: p.update(body_markdown="Position sizing uses HALF_PLAN_RISK."), "RULE_A3_KELLY_SIZING_LOT_LEAK"),
        ("kelly_key", lambda p: p.update(dd30_kelly_optimal_f=0.035), "RULE_A3_FORBIDDEN_KELLY_SIZING_KEY"),
        ("camel_lot_key", lambda p: p.update(lotSize=0.10), "RULE_A3_FORBIDDEN_KELLY_SIZING_KEY"),
        # Stop-loss / take-profit / entry fill levels
        ("stop_loss_text", lambda p: p.update(body_markdown="Place stop-loss at 3,920."), "RULE_A3_STOP_LOSS_LEVEL_LEAK"),
        ("sl_colon_text", lambda p: p.update(body_markdown="SL: 3,920 on gold."), "RULE_A3_STOP_LOSS_LEVEL_LEAK"),
        ("take_profit_text", lambda p: p.update(body_markdown="Take-profit at 4,210."), "RULE_A3_TAKE_PROFIT_LEVEL_LEAK"),
        ("tp1_text", lambda p: p.update(body_markdown="TP1: 4,185 for the move."), "RULE_A3_TAKE_PROFIT_LEVEL_LEAK"),
        ("price_target_text", lambda p: p.update(body_markdown="Our $4,200 target stays intact."), "RULE_A3_TAKE_PROFIT_LEVEL_LEAK"),
        ("entry_fill_text", lambda p: p.update(body_markdown="Entry fill at 4,012.50 confirmed."), "RULE_A3_ENTRY_FILL_LEVEL_LEAK"),
        ("filled_at_text", lambda p: p.update(body_markdown="Order filled at 4,015.20 in London."), "RULE_A3_ENTRY_FILL_LEVEL_LEAK"),
        ("camel_stop_key", lambda p: p.update(stopLoss=3920.0), "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
        ("camel_tp_key", lambda p: p.update(takeProfit=4210.0), "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
        ("entry_fill_key", lambda p: p.update(entry_fill_price=4012.5), "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
        # Account balance / equity / PnL figures
        ("account_balance_text", lambda p: p.update(body_markdown="The account balance is $100,000."), "RULE_A3_ACCOUNT_BALANCE_EQUITY_PNL_LEAK"),
        ("realized_pnl_text", lambda p: p.update(body_markdown="Realized PnL reached +$4,200."), "RULE_A3_ACCOUNT_BALANCE_EQUITY_PNL_LEAK"),
        ("our_equity_text", lambda p: p.update(body_markdown="Our equity sits at 50,000 USD."), "RULE_A3_ACCOUNT_BALANCE_EQUITY_PNL_LEAK"),
        ("net_liquidation_text", lambda p: p.update(body_markdown="Net liquidation hit 1,000,183."), "RULE_A3_ACCOUNT_BALANCE_EQUITY_PNL_LEAK"),
        ("balance_key", lambda p: p.update(accountBalance=50000.0), "RULE_A3_FORBIDDEN_ACCOUNT_PNL_KEY"),
        ("pnl_key", lambda p: p.update(daily_pnl=1250.0), "RULE_A3_FORBIDDEN_ACCOUNT_PNL_KEY"),
        # Broker / MT5 / IBKR account identifiers (incl. DUR343723)
        ("dur343723_text", lambda p: p.update(body_markdown="Routed via DUR343723 paper book."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("dur343723_fullwidth", lambda p: p.update(body_markdown="Account \uff24\uff35\uff32\uff13\uff14\uff13\uff17\uff12\uff13 active."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("dur343723_as_key", lambda p: p.update({"DUR343723": "ok"}), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("ibkr_live_id", lambda p: p.update(body_markdown="Live IBKR U1234567 margin check."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("mt5_login_id", lambda p: p.update(body_markdown="Demo login 279805139 on Exness-MT5Trial8."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("model_position_d117", lambda p: p.update(body_markdown="Capital Chronicle's model position stays open."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("api_secret_leak", lambda p: p.update(body_markdown="Token sk-abcd1234efgh5678ijkl9012 leaked."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("ibkr_account_key", lambda p: p.update(ibkrAccount="paper"), "RULE_A3_FORBIDDEN_BROKER_KEY"),
        # Private Study #6..#11 tags
        ("private_only_true", lambda p: p.update(private_only=True), "RULE_A3_FORBIDDEN_PRIVATE_STUDY_KEY"),
        ("private_only_false", lambda p: p.update(private_only=False), "RULE_A3_FORBIDDEN_PRIVATE_STUDY_KEY"),
        ("public_export_forbidden", lambda p: p.update(public_export_forbidden=True), "RULE_A3_FORBIDDEN_PRIVATE_STUDY_KEY"),
        ("public_export_false", lambda p: p.update(public_export=False), "RULE_A3_NON_PUBLIC_EXPORT_FLAG"),
        ("study6_text", lambda p: p.update(body_markdown="Findings from Study #6 PIT sweep."), "RULE_A3_PRIVATE_STUDY_TAG_LEAK"),
        ("study10_schema_text", lambda p: p.update(schema="Study10PostCC936JointAlphaFrontierPrivateV1"), "RULE_A3_PRIVATE_STUDY_TAG_LEAK"),
        ("study11_id_text", lambda p: p.update(study_id="STUDY11_UNIFIED_CAPITAL_LADDER_SYNTHESIS_1K_TO_50K"), "RULE_A3_PRIVATE_STUDY_TAG_LEAK"),
        # Raw L4 / sleeve weights
        ("l4_key", lambda p: p.update(L4={"cagr": 42.1}), "RULE_A3_FORBIDDEN_L4_SLEEVE_KEY"),
        ("sleeve_weights_key", lambda p: p.update(sleeve_weights={"XAUUSD": 0.4, "USTEC": 0.6}), "RULE_A3_FORBIDDEN_L4_SLEEVE_KEY"),
        ("l4_text", lambda p: p.update(body_markdown="Raw L4 sleeve weight increased to 0.45."), "RULE_A3_L4_SLEEVE_WEIGHT_LEAK"),
        ("stack_l4_text", lambda p: p.update(body_markdown="STACK_5_minus_L4 outperformance."), "RULE_A3_L4_SLEEVE_WEIGHT_LEAK"),
        # Nested deep inside list-of-dicts
        ("nested_list_dur343723", lambda p: p.update(items=[{"notes": ["clean", {"tag": "IBKR_PAPER_DUR343723"}]}]), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
    ],
)
def test_rule_a3_private_alpha_leaks_are_blocked_and_redacted(tmp_path, label, mutator, expected_code):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    payload = clean_post_payload()
    mutator(payload)
    rec = fw.evaluate_payload(
        payload,
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED, f"{label} unexpectedly passed"
    assert rec["publish_allowed"] is False
    assert rec["cc024_audit"]["mode"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == expected_code for f in rec["findings"]), (label, rec["findings"])
    # Verify private secrets/account IDs are NEVER echoed verbatim in receipts.
    serialized = json.dumps(rec)
    for sensitive in ("DUR343723", "279805139", "U1234567", "sk-abcd1234efgh5678ijkl9012", "$100,000"):
        assert sensitive not in serialized


def test_chart_metadata_blocks_target_drawn_and_execution_overlay_levels(tmp_path):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    bad_target = clean_chart_metadata_payload()
    bad_target["tradingview_snapshot"]["target_drawn"] = True
    r1 = fw.evaluate_payload(
        bad_target,
        payload_kind="chart_metadata",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert r1["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "DECISION_157_CHART_TARGET_DRAWN_FORBIDDEN" for f in r1["findings"])

    bad_levels = clean_chart_metadata_payload()
    bad_levels["tradingview_snapshot"]["levels_drawn"] = [{"label": "Broker stop", "price": 3950}]
    r2 = fw.evaluate_payload(
        bad_levels,
        payload_kind="chart_metadata",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert r2["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "RULE_A3_CHART_EXECUTION_LEVEL_DRAWN" for f in r2["findings"])


# ---------------------------------------------------------------------------
# 3. public-webapp-preview Forbidden Leak Classes & CC-024 Paywall / Affiliate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "mutator", "expected_code", "expected_bucket"),
    [
        ("sidecar_token", lambda p: p.update(body_markdown="Loaded internal-gamma-options sidecar."), "PUBLIC_WEBAPP_PRIVATE_TOKEN_LEAK", None),
        ("window_cc_global", lambda p: p.update(body_markdown="window.__CC_PRICE_BARS__ injected."), "PUBLIC_WEBAPP_PRIVATE_GLOBAL_LEAK", None),
        ("book_dump_marker", lambda p: p.update(body_markdown="Snapshot of ibkr_book attached."), "PUBLIC_WEBAPP_BOOK_DUMP_MARKER_LEAK", None),
        ("owner_route", lambda p: p.update(canonical_url="https://capitalchronicle.substack.com/__owner/desk"), "PUBLIC_WEBAPP_PRIVATE_TOKEN_LEAK", None),
        ("preview_host_d83", lambda p: p.update(canonical_url="https://fatcat2109.github.io/capital-chronicle-preview/"), "PREVIEW_HOST_LINK_FORBIDDEN", None),
        ("unsafe_js_url", lambda p: p.update(body_markdown="Click javascript:alert(1) now."), "PUBLIC_WEBAPP_UNSAFE_URL_SCHEME", None),
        ("http_non_https_url", lambda p: p.update(canonical_url="http://capitalchronicle.substack.com/p/test"), "PUBLIC_WEBAPP_NON_HTTPS_URL", None),
        ("credentialed_url", lambda p: p.update(canonical_url="https://user:pass@capitalchronicle.substack.com/p/test"), "PUBLIC_WEBAPP_CREDENTIALED_URL", None),
        ("non_et_gmt7_d90", lambda p: p.update(display_time_et="09:00 GMT+7 on 15 Dec 2026"), "PUBLIC_TIMEZONE_ET_REQUIRED", None),
        ("non_et_bangkok_d90", lambda p: p.update(body_markdown="Published at 19:00 Bangkok time."), "PUBLIC_TIMEZONE_ET_REQUIRED", None),
        ("ai_model_claude_cc855", lambda p: p.update(body_markdown="Drafted by Claude Opus for readers."), "PUBLIC_AI_MODEL_AUTHORSHIP_LEAK", None),
        ("ai_model_gemini", lambda p: p.update(body_markdown="Reviewed by Gemini desk analysts."), "PUBLIC_AI_MODEL_AUTHORSHIP_LEAK", None),
        ("odds_kalshi_cc791", lambda p: p.update(body_markdown="Kalshi markets price 86% odds of a hold."), "PUBLIC_ODDS_LEAK_CC791", "raw_vendor_leak_count"),
        ("odds_fedwatch_cc791", lambda p: p.update(body_markdown="CME FedWatch shows 86.3% probability of a cut."), "PUBLIC_ODDS_LEAK_CC791", "raw_vendor_leak_count"),
        ("odds_gap_pp_cc791", lambda p: p.update(body_markdown="Divergence gap_pp: 14.2 versus crowd."), "PUBLIC_ODDS_LEAK_CC791", "raw_vendor_leak_count"),
        ("raw_vendor_feed", lambda p: p.update(raw_vendor_feed={"wire": "fj"}), "CC024_FORBIDDEN_RAW_VENDOR_KEY", "raw_vendor_leak_count"),
        ("denied_rights_class", lambda p: p.update(rights_class="LICENSE_REQUIRED"), "CC024_DENIED_PUBLIC_RIGHTS", "raw_vendor_leak_count"),
        # CC-024 / Decision 96 Paywall, VIP, Subscription Upsell CTAs
        ("paywall_cta", lambda p: p.update(body_markdown="Upgrade to paid to unlock full access behind the paywall."), "CC024_PAYWALL_UPSELL_FORBIDDEN", "paid_paywall_count"),
        ("vip_group_cta", lambda p: p.update(body_markdown="Join our VIP Telegram channel for trade alerts."), "CC024_PAYWALL_UPSELL_FORBIDDEN", "paid_paywall_count"),
        ("paid_pricing_cta", lambda p: p.update(body_markdown="Subscribe now for $29/month or join Patreon."), "CC024_PAYWALL_UPSELL_FORBIDDEN", "paid_paywall_count"),
        ("patreon_link", lambda p: p.update(canonical_url="https://patreon.com/capitalchronicle"), "CC024_PAYWALL_UPSELL_FORBIDDEN", "paid_paywall_count"),
        ("substack_paid_plan_url", lambda p: p.update(canonical_url="https://capitalchronicle.substack.com/subscribe?plan=monthly"), "CC024_PAYWALL_UPSELL_FORBIDDEN", "paid_paywall_count"),
        ("paywall_flag_true", lambda p: p.update(paywall=True), "CC024_PAYWALL_FIELD_ACTIVE", "paid_paywall_count"),
        ("mode_paid", lambda p: p.update(mode="PAID"), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("tier_vip_str", lambda p: p.update(tier="VIP"), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("tier_vip_nested", lambda p: p.update(tier={"value": "VIP"}), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("price_usd_nonzero", lambda p: p.update(price_usd=19.99), "CC024_PAYWALL_FIELD_ACTIVE", "paid_paywall_count"),
        # CC-024 Affiliate / Referral Promos
        ("affiliate_cta", lambda p: p.update(body_markdown="Use our referral code CC2026 to open a broker account using our link."), "CC024_AFFILIATE_PROMO_FORBIDDEN", "affiliate_count"),
        ("affiliate_url_param", lambda p: p.update(canonical_url="https://capitalchronicle.substack.com/p/wrap?ref=partner99"), "CC024_AFFILIATE_URL_PARAM", "affiliate_count"),
        ("affiliate_key", lambda p: p.update(affiliate_url="https://partner.example/cc"), "CC024_AFFILIATE_FIELD_ACTIVE", "affiliate_count"),
    ],
)
def test_public_webapp_leaks_and_cc024_paywall_affiliate_blocked(
    tmp_path, label, mutator, expected_code, expected_bucket
):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    payload = clean_post_payload()
    mutator(payload)
    rec = fw.evaluate_payload(
        payload,
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED, label
    assert rec["publish_allowed"] is False
    assert rec["cc024_audit"]["mode"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == expected_code for f in rec["findings"]), (label, rec["findings"])
    if expected_bucket is not None:
        assert rec["cc024_audit"][expected_bucket] >= 1


# ---------------------------------------------------------------------------
# 4. bool / NaN / Inf / 1e400 / 10**400 / UTC OverflowError / Malformed JSON
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "raw_bytes", "expected_code"),
    [
        ("nan_raw_json", b'{"title":"ok","value":NaN}', "NON_FINITE_NUMBER_FORBIDDEN"),
        ("inf_raw_json", b'{"title":"ok","value":Infinity}', "NON_FINITE_NUMBER_FORBIDDEN"),
        ("neg_inf_raw_json", b'{"title":"ok","value":-Infinity}', "NON_FINITE_NUMBER_FORBIDDEN"),
        ("1e400_raw_json", b'{"title":"ok","value":1e400}', "NON_FINITE_NUMBER_FORBIDDEN"),
        ("neg_1e400_raw_json", b'{"title":"ok","value":-1e400}', "NON_FINITE_NUMBER_FORBIDDEN"),
        ("10_pow_400_raw_json", ('{"title":"ok","value":' + "1" + "0" * 400 + "}").encode("utf-8"), "INTEGER_OVERFLOW_FORBIDDEN"),
        ("neg_10_pow_400_raw_json", ('{"title":"ok","value":-' + "1" + "0" * 400 + "}").encode("utf-8"), "INTEGER_OVERFLOW_FORBIDDEN"),
        ("10_pow_5000_raw_json", ('{"title":"ok","value":' + "1" + "0" * 5000 + "}").encode("utf-8"), "INTEGER_OVERFLOW_FORBIDDEN"),
        ("duplicate_json_key", b'{"mode":"PAID","mode":"FREE_ONLY"}', "DUPLICATE_JSON_KEY_FORBIDDEN"),
        ("utf8_bom", b'\xef\xbb\xbf{"title":"ok"}', "UTF8_BOM_FORBIDDEN"),
        ("invalid_utf8", b'{"title":"\xff"}', "INVALID_UTF8_JSON"),
        ("unpaired_surrogate", b'{"title":"\\ud800"}', "CANONICAL_JSON_SERIALIZATION_FAILED"),
        ("empty_payload", b"", "EMPTY_JSON_PAYLOAD"),
        ("malformed_truncated", b'{"title":"ok"', "MALFORMED_JSON_PAYLOAD"),
        ("malformed_trailing_comma", b'{"title":"ok",}', "MALFORMED_JSON_PAYLOAD"),
        ("non_object_root_array", b'["not","an","object"]', "JSON_ROOT_OBJECT_REQUIRED"),
        ("bool_in_width_raw", b'{"width":true,"height":858}', "BOOL_IN_NUMERIC_FIELD_FORBIDDEN"),
        ("bool_in_count_raw", b'{"checked_artifact_count":false}', "BOOL_IN_NUMERIC_FIELD_FORBIDDEN"),
        ("bool_in_timestamp_raw", b'{"published_at_utc":true}', "BOOL_TIMESTAMP_FORBIDDEN"),
    ],
)
def test_raw_json_hostile_numbers_bools_and_malformed_inputs_fail_closed(tmp_path, label, raw_bytes, expected_code):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    rec = fw.evaluate_payload_bytes(
        raw_bytes,
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED, label
    assert rec["publish_allowed"] is False
    assert rec["cc024_audit"]["mode"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == expected_code for f in rec["findings"]), (label, rec["findings"])
    assert_receipt_hash_valid(rec)


@pytest.mark.parametrize(
    ("label", "payload", "expected_code"),
    [
        ("in_memory_nan", {"title": "ok", "value": float("nan")}, "NON_FINITE_NUMBER_FORBIDDEN"),
        ("in_memory_pos_inf", {"title": "ok", "value": float("inf")}, "NON_FINITE_NUMBER_FORBIDDEN"),
        ("in_memory_neg_inf", {"title": "ok", "value": float("-inf")}, "NON_FINITE_NUMBER_FORBIDDEN"),
        ("in_memory_10_pow_400", {"title": "ok", "value": 10**400}, "INTEGER_OVERFLOW_FORBIDDEN"),
        ("in_memory_neg_10_pow_400", {"title": "ok", "value": -(10**400)}, "INTEGER_OVERFLOW_FORBIDDEN"),
        ("in_memory_bool_width", {"width": True, "height": 858}, "BOOL_IN_NUMERIC_FIELD_FORBIDDEN"),
        ("in_memory_bool_price", {"price": False}, "BOOL_IN_NUMERIC_FIELD_FORBIDDEN"),
        ("in_memory_bool_tier", {"tier": True}, "CC024_NON_FREE_TIER_FORBIDDEN"),
        ("in_memory_non_positive_width", {"width": 0, "height": 858}, "NON_POSITIVE_DIMENSION_FORBIDDEN"),
        ("in_memory_float_width", {"width": 1524.5, "height": 858}, "NON_INTEGER_DIMENSION_FORBIDDEN"),
        ("in_memory_non_json_set", {"title": "ok", "tags": {"a", "b"}}, "UNSUPPORTED_JSON_VALUE_TYPE"),
        ("in_memory_non_string_key", {123: "ok"}, "NON_STRING_JSON_KEY_FORBIDDEN"),
        ("in_memory_surrogate_str", {"title": "\ud800"}, "UNPAIRED_UNICODE_SURROGATE"),
    ],
)
def test_in_memory_hostile_python_values_fail_closed(tmp_path, label, payload, expected_code):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    rec = fw.evaluate_payload(
        payload,
        payload_kind="chart_metadata" if "width" in payload else "post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED, label
    assert rec["publish_allowed"] is False
    assert any(f["code"] == expected_code for f in rec["findings"]), (label, rec["findings"])
    assert_receipt_hash_valid(rec)


def test_deep_nesting_and_cyclic_structures_fail_closed(tmp_path):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    deep: dict = {"leaf": "ok"}
    for _ in range(fw.MAX_JSON_DEPTH + 5):
        deep = {"nest": deep}
    rec_deep = fw.evaluate_payload(
        deep,
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec_deep["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "MAX_JSON_DEPTH_EXCEEDED" for f in rec_deep["findings"])

    cyclic: dict = {"title": "cycle"}
    cyclic["self"] = cyclic
    rec_cyc = fw.evaluate_payload(
        cyclic,
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec_cyc["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "CYCLIC_JSON_STRUCTURE_FORBIDDEN" for f in rec_cyc["findings"])


@pytest.mark.parametrize(
    "bad_as_of",
    [
        True,
        False,
        None,
        1234567890,
        "2026-12-14T17:00:00",  # naive
        "2026-12-15T00:00:00+07:00",  # non-UTC offset disallowed on strict UTC clock
        "9999-12-31T23:59:59-05:00",  # UTC OverflowError if converted
        "0001-01-01T00:00:00+05:00",  # UTC OverflowError if converted
        "0001-01-01T00:00:00Z",  # ET conversion OverflowError
        "2026-02-30T00:00:00Z",  # nonexistent date
        "not-a-timestamp",
    ],
)
def test_as_of_utc_overflow_bool_and_invalid_clocks_fail_closed(tmp_path, bad_as_of):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    rec = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=bad_as_of,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED
    assert rec["publish_allowed"] is False
    assert any(f["path"] == "$.as_of_utc" for f in rec["findings"])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("published_at_utc", "9999-12-31T23:59:59-05:00"),
        ("published_at_utc", "0001-01-01T00:00:00+05:00"),
        ("published_at_utc", "0001-01-01T00:00:00Z"),
        ("captured_at_utc", "2026-12-15T00:00:00"),  # naive
        ("known_at_utc", 1e20),  # epoch OverflowError
        ("known_at_utc", 10**400),  # huge int OverflowError
        ("known_at_utc", float("inf")),  # Inf timestamp
        ("known_at_utc", True),  # bool timestamp
    ],
)
def test_payload_utc_overflow_and_naive_timestamps_fail_closed(tmp_path, field, value):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    payload = clean_post_payload()
    payload[field] = value
    rec = fw.evaluate_payload(
        payload,
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED
    assert rec["publish_allowed"] is False


def test_parse_payload_timestamp_utc_handles_offset_overflow_directly():
    for bad in ("9999-12-31T23:59:59-05:00", "0001-01-01T00:00:00+05:00", 1e20, 10**400):
        with pytest.raises(fw.FirewallEvidenceError) as exc_info:
            fw.parse_payload_timestamp_utc(bad, "published_at")
        assert exc_info.value.code == "UTC_CLOCK_OVERFLOW"


# ---------------------------------------------------------------------------
# 5. Pause-Gate Boundary Tests (16:59:59.999999Z vs 17:00:00Z & 3/3 .stop)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("before_ts", [BEFORE_DEC15_US, BEFORE_DEC15_NS, "2026-11-28T05:00:00Z"])
def test_strict_hold_paused_before_dec15_in_both_preflight_and_publish_modes(tmp_path, before_ts):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path / "pre", resume_at=DEC15_BOUNDARY)
    pre = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=before_ts,
        gate_mode="preflight",
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert pre["verdict"] == fw.VERDICT_HOLD_PAUSED_BEFORE_DEC15
    assert pre["publish_allowed"] is False
    assert pre["pause_gate"]["before_dec15_boundary"] is True
    assert_cc1011_free_audit_compatible(pre, as_of_utc=before_ts)

    # Even if someone prematurely removed all 3 .stop files and wrote restored.json before 17:00:00Z,
    # publish mode STILL fails closed with HOLD_PAUSED_BEFORE_DEC15.
    early_pause, early_stops = make_pause_snapshot(
        tmp_path / "early_pub",
        resume_at=DEC15_BOUNDARY,
        stops=(),
        restored_at=before_ts,
    )
    pub = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=before_ts,
        gate_mode="publish",
        pause_dir=early_pause,
        publisher_stops_dir=early_stops,
    )
    assert pub["verdict"] == fw.VERDICT_HOLD_PAUSED_BEFORE_DEC15
    assert pub["publish_allowed"] is False


def test_hostile_leak_before_dec15_is_blocked_not_masked_as_hold(tmp_path):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path, resume_at=DEC15_BOUNDARY)
    leaking = clean_post_payload()
    leaking["body_markdown"] += "\nAccount DUR343723 stop-loss 3900."
    rec = fw.evaluate_payload(
        leaking,
        payload_kind="post",
        as_of_utc=BEFORE_DEC15_US,
        gate_mode="preflight",
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED
    assert rec["pause_gate"]["verdict"] == fw.VERDICT_HOLD_PAUSED_BEFORE_DEC15
    assert rec["cc024_audit"]["mode"] == fw.VERDICT_BLOCKED


@pytest.mark.parametrize(
    ("at_boundary",),
    [
        ("2026-12-14T17:00:00Z",),
        ("2026-12-14T17:00:00.000000Z",),
        ("2026-12-14T17:00:00+00:00",),
    ],
)
def test_exact_dec15_boundary_transitions_cleanly(tmp_path, at_boundary):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path / "pre", resume_at=DEC15_BOUNDARY)
    pre = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=at_boundary,
        gate_mode="preflight",
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert pre["verdict"] == fw.VERDICT_READY_FREE_UNPAUSE
    assert pre["publish_allowed"] is False

    pub_dir, pub_stops = make_pause_snapshot(
        tmp_path / "pub",
        resume_at=DEC15_BOUNDARY,
        stops=(),
        restored_at=at_boundary,
    )
    pub = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=at_boundary,
        gate_mode="publish",
        pause_dir=pub_dir,
        publisher_stops_dir=pub_stops,
    )
    assert pub["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH
    assert pub["publish_allowed"] is True


@pytest.mark.parametrize(
    ("resume_at", "expected_code"),
    [
        ("2026-11-29T18:00:00Z", "PAUSE_RESUME_BEFORE_DEC15_BOUNDARY"),
        ("2026-12-14T16:59:59.999999999Z", "PAUSE_RESUME_BEFORE_DEC15_BOUNDARY"),
        ("2026-12-14T17:00:00.000000001Z", "PAUSE_RESUME_STILL_IN_FUTURE"),
    ],
)
def test_pause_manifest_resume_clock_constraints(tmp_path, resume_at, expected_code):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path, resume_at=resume_at)
    rec = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        gate_mode="preflight",
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED
    assert rec["pause_gate"]["failure_code"] == expected_code


@pytest.mark.parametrize("missing_stop", fw.PUBLISHER_STOPS)
def test_all_three_stop_files_enforced_in_preflight_and_publish(tmp_path, missing_stop):
    # Preflight requires all 3/3 .stop files present.
    remaining = tuple(s for s in fw.PUBLISHER_STOPS if s != missing_stop)
    pause_dir, stops_dir = make_pause_snapshot(tmp_path / "pre", stops=remaining)
    pre = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        gate_mode="preflight",
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert pre["verdict"] == fw.VERDICT_BLOCKED
    assert pre["pause_gate"]["failure_code"] == "PUBLISHER_STOPS_MISSING"
    assert pre["pause_gate"]["publisher_stops_missing"] == [missing_stop]

    # Publish requires 0/3 .stop files active; any single active stop blocks publish.
    pub_pause, pub_stops = make_pause_snapshot(
        tmp_path / "pub",
        stops=(missing_stop,),
        restored_at=DEC15_BOUNDARY,
    )
    pub = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        gate_mode="publish",
        pause_dir=pub_pause,
        publisher_stops_dir=pub_stops,
    )
    assert pub["verdict"] == fw.VERDICT_BLOCKED
    assert pub["pause_gate"]["failure_code"] == "PUBLISHER_STOP_FILES_ACTIVE"
    assert pub["publish_allowed"] is False


def test_pause_restored_marker_and_missing_evidence_fail_closed(tmp_path):
    # Preflight blocks if restored.json already exists.
    p1, s1 = make_pause_snapshot(tmp_path / "p1", restored_at=DEC15_BOUNDARY)
    r1 = fw.evaluate_payload(
        clean_post_payload(),
        as_of_utc=DEC15_BOUNDARY,
        gate_mode="preflight",
        pause_dir=p1,
        publisher_stops_dir=s1,
    )
    assert r1["verdict"] == fw.VERDICT_BLOCKED
    assert r1["pause_gate"]["failure_code"] == "PAUSE_RESTORED_MARKER_PRESENT"

    # Publish blocks if restored.json missing (when require_restored_marker=True).
    p2, s2 = make_pause_snapshot(tmp_path / "p2", stops=(), restored_at=None)
    r2 = fw.evaluate_payload(
        clean_post_payload(),
        as_of_utc=DEC15_BOUNDARY,
        gate_mode="publish",
        pause_dir=p2,
        publisher_stops_dir=s2,
    )
    assert r2["verdict"] == fw.VERDICT_BLOCKED
    assert r2["pause_gate"]["failure_code"] == "RESTORED_MARKER_MISSING"

    # Publish blocks if restored.json timestamp precedes resume_at_utc.
    p3, s3 = make_pause_snapshot(tmp_path / "p3", stops=(), restored_at=BEFORE_DEC15_US)
    r3 = fw.evaluate_payload(
        clean_post_payload(),
        as_of_utc=DEC15_BOUNDARY,
        gate_mode="publish",
        pause_dir=p3,
        publisher_stops_dir=s3,
    )
    assert r3["verdict"] == fw.VERDICT_BLOCKED
    assert r3["pause_gate"]["failure_code"] == "RESTORED_CLOCK_INVALID"

    # No pause evidence supplied at Dec-15 boundary fails closed (no silent live defaults).
    r4 = fw.evaluate_payload(clean_post_payload(), as_of_utc=DEC15_BOUNDARY, gate_mode="preflight")
    assert r4["verdict"] == fw.VERDICT_BLOCKED
    assert r4["pause_gate"]["failure_code"] == "PAUSE_GATE_EVIDENCE_REQUIRED"

    # In-memory pause_state works hermetically.
    r5 = fw.evaluate_payload(
        clean_post_payload(),
        as_of_utc=DEC15_BOUNDARY,
        gate_mode="publish",
        pause_state={
            "paused_at_utc": "2026-11-23T04:56:22Z",
            "resume_at_utc": DEC15_BOUNDARY,
            "publisher_stops_present": [],
            "restored_present": True,
            "restored_at_utc": DEC15_BOUNDARY,
        },
    )
    assert r5["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH
    assert r5["publish_allowed"] is True


# ---------------------------------------------------------------------------
# 6. Deterministic SHA-256 Receipts, Batch CC-1011 Parity, Dir Scan & CLI
# ---------------------------------------------------------------------------


def test_deterministic_hashes_and_multi_artifact_cc1011_release_batch(tmp_path):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    post_a = clean_post_payload()
    post_reordered = dict(reversed(list(post_a.items())))

    r1 = fw.evaluate_payload(
        post_a, payload_kind="post", as_of_utc=DEC15_BOUNDARY, pause_dir=pause_dir, publisher_stops_dir=stops_dir
    )
    r2 = fw.evaluate_payload(
        post_reordered, payload_kind="post", as_of_utc=DEC15_BOUNDARY, pause_dir=pause_dir, publisher_stops_dir=stops_dir
    )
    assert r1["payload_sha256"] == r2["payload_sha256"]
    assert r1["candidate_sha256"] == r2["candidate_sha256"]
    assert r1["receipt_sha256"] == r2["receipt_sha256"]

    batch = [
        {"artifact_id": "wrap-post", "payload_kind": "post", "payload": clean_post_payload()},
        {"artifact_id": "cpi-card", "payload_kind": "card", "payload": clean_card_payload()},
        {"artifact_id": "ig-caption", "payload_kind": "caption", "payload": clean_caption_payload()},
        {"artifact_id": "tv-chart", "payload_kind": "chart_metadata", "payload": clean_chart_metadata_payload()},
        {"artifact_id": "daily-digest", "payload_kind": "digest", "payload": clean_digest_payload()},
    ]
    batch_rec = fw.evaluate_release_batch(
        batch,
        as_of_utc=DEC15_BOUNDARY,
        observed_at_utc="2026-12-14T16:59:00Z",
        gate_mode="preflight",
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert batch_rec["verdict"] == fw.VERDICT_READY_FREE_UNPAUSE
    assert batch_rec["counts"]["checked_artifact_count"] == 5
    assert batch_rec["counts"]["total_findings"] == 0
    assert_receipt_hash_valid(batch_rec)
    assert_cc1011_free_audit_compatible(batch_rec, as_of_utc=DEC15_BOUNDARY)

    # Causality check: observed_at_utc after as_of_utc must block.
    future_obs = fw.evaluate_release_batch(
        batch,
        as_of_utc=DEC15_BOUNDARY,
        observed_at_utc=AFTER_DEC15,
        gate_mode="preflight",
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert future_obs["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "OBSERVED_AFTER_AS_OF_CUTOFF" for f in future_obs["findings"])


def test_scan_public_directory_readonly_clean_vs_leaking(tmp_path):
    pub_dir = tmp_path / "public-preview"
    pub_dir.mkdir()
    (pub_dir / "post.public.json").write_bytes(fw.canonical_json_bytes(clean_post_payload()))
    (pub_dir / "chart-data.json").write_bytes(
        fw.canonical_json_bytes([{"series_id": "bls:cpi", "observations": [{"period": "2026-11", "value": 0.2}]}])
    )
    clean_scan = fw.scan_public_directory_readonly(pub_dir)
    assert clean_scan["exists"] is True
    assert clean_scan["files_scanned"] == 2
    assert clean_scan["clean_files"] == 2
    assert clean_scan["failed_files"] == 0

    (pub_dir / "study11.private.json").write_bytes(
        fw.canonical_json_bytes({"private_only": True, "public_export_forbidden": True, "account": "DUR343723"})
    )
    dirty_scan = fw.scan_public_directory_readonly(pub_dir)
    assert dirty_scan["failed_files"] == 1
    assert dirty_scan["findings_count"] >= 3


def test_standalone_cli_exit_codes_and_zero_mutation(tmp_path, capsys):
    repo_root = Path(__file__).resolve().parents[1]
    pause_dir, stops_dir = make_pause_snapshot(tmp_path / "pre", resume_at=DEC15_BOUNDARY)
    payload_file = tmp_path / "post.json"
    payload_file.write_bytes(fw.canonical_json_bytes(clean_post_payload()))
    before_files = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    # 1. Preflight before Dec 15 -> exit 0, verdict HOLD_PAUSED_BEFORE_DEC15 (CC-1011 parity)
    proc_hold = subprocess.run(
        [
            sys.executable, "-B", "-m", "live_contentops.dec15_public_disclosure_firewall_v1",
            "--payload", str(payload_file), "--payload-kind", "post",
            "--as-of-utc", BEFORE_DEC15_US, "--gate-mode", "preflight",
            "--pause-dir", str(pause_dir), "--publisher-stops-dir", str(stops_dir),
        ],
        cwd=str(repo_root),
        capture_output=True, text=True, check=False,
    )
    assert proc_hold.returncode == fw.EXIT_OK, proc_hold.stderr
    assert proc_hold.stderr == ""
    hold_doc = json.loads(proc_hold.stdout)
    assert hold_doc["verdict"] == fw.VERDICT_HOLD_PAUSED_BEFORE_DEC15
    assert_receipt_hash_valid(hold_doc)

    # 2. Publish mode before Dec 15 -> non-zero exit EXIT_HOLD_PAUSED (2)
    rc_pub_hold = fw.main([
        "--payload", str(payload_file), "--payload-kind", "post",
        "--as-of-utc", BEFORE_DEC15_US, "--gate-mode", "publish",
        "--pause-dir", str(pause_dir), "--publisher-stops-dir", str(stops_dir),
    ])
    assert rc_pub_hold == fw.EXIT_HOLD_PAUSED
    assert json.loads(capsys.readouterr().out)["verdict"] == fw.VERDICT_HOLD_PAUSED_BEFORE_DEC15

    # 3. Preflight at Dec 15 boundary -> exit 0, READY_FREE_UNPAUSE
    rc_ready = fw.main([
        "--payload", str(payload_file), "--payload-kind", "post",
        "--as-of-utc", DEC15_BOUNDARY, "--gate-mode", "preflight",
        "--pause-dir", str(pause_dir), "--publisher-stops-dir", str(stops_dir),
    ])
    assert rc_ready == fw.EXIT_OK
    assert json.loads(capsys.readouterr().out)["verdict"] == fw.VERDICT_READY_FREE_UNPAUSE

    # Verify zero filesystem mutation across all read-only CLI runs.
    after_files = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before_files == after_files

    # 4. Leaking payload -> exit 1 (EXIT_BLOCKED)
    bad_file = tmp_path / "bad.json"
    leaking = deepcopy(clean_post_payload())
    leaking["body_markdown"] += "\nUpgrade to paid VIP signals via DUR343723."
    bad_file.write_bytes(fw.canonical_json_bytes(leaking))
    rc_blocked = fw.main([
        "--payload", str(bad_file), "--payload-kind", "post",
        "--as-of-utc", DEC15_BOUNDARY, "--gate-mode", "preflight",
        "--pause-dir", str(pause_dir), "--publisher-stops-dir", str(stops_dir),
    ])
    assert rc_blocked == fw.EXIT_BLOCKED
    blocked_out = json.loads(capsys.readouterr().out)
    assert blocked_out["verdict"] == fw.VERDICT_BLOCKED
    assert "DUR343723" not in json.dumps(blocked_out)


@pytest.mark.parametrize(
    ("kind", "factory", "field", "hostile_value", "expected_code"),
    [
        ("card", clean_card_payload, "headline", "Kelly f* = 0.05 CPI card", "RULE_A3_KELLY_SIZING_LOT_LEAK"),
        ("caption", clean_caption_payload, "caption", "Chart from DUR343723 desk.", "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("chart_metadata", clean_chart_metadata_payload, "width", True, "BOOL_IN_NUMERIC_FIELD_FORBIDDEN"),
        ("digest", clean_digest_payload, "headline", "Daily digest — upgrade to paid VIP tier", "CC024_PAYWALL_UPSELL_FORBIDDEN"),
    ],
)
def test_all_five_payload_kinds_enforce_firewall(tmp_path, kind, factory, field, hostile_value, expected_code):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    obj = factory()
    obj[field] = hostile_value
    rec = fw.evaluate_payload(
        obj,
        payload_kind=kind,
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == expected_code for f in rec["findings"])


def test_evaluate_payload_file_missing_and_directory_fail_closed(tmp_path):
    pause_dir, stops_dir = make_pause_snapshot(tmp_path)
    missing = fw.evaluate_payload_file(
        tmp_path / "does-not-exist.json",
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert missing["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "REQUIRED_FILE_MISSING" for f in missing["findings"])

    as_dir = fw.evaluate_payload_file(
        tmp_path,
        payload_kind="post",
        as_of_utc=DEC15_BOUNDARY,
        pause_dir=pause_dir,
        publisher_stops_dir=stops_dir,
    )
    assert as_dir["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "NON_REGULAR_FILE_FORBIDDEN" for f in as_dir["findings"])


# ---------------------------------------------------------------------------
# 7. Cycle #23a Combined Remediation Regressions (Ops Product + Reviewer 2 #143)
# ---------------------------------------------------------------------------


def _publish_pause_state() -> dict:
    return {
        "paused_at_utc": "2026-11-23T04:56:22Z",
        "resume_at_utc": DEC15_BOUNDARY,
        "publisher_stops_present": [],
        "restored_present": True,
        "restored_at_utc": DEC15_BOUNDARY,
    }


@pytest.mark.parametrize(
    ("label", "mutator", "expected_code"),
    [
        # B16C21-H1 + R2-H2: CC-024 commercial data-rights deny-list
        ("b1_yahoo_finance_url", lambda p: p.update(body_markdown="S&P 500 close from Yahoo Finance (https://finance.yahoo.com/quote/%5EGSPC)."), "CC024_RAW_VENDOR_LEAK"),
        ("b2_yfinance_query1", lambda p: p.update(body_markdown="Daily prices pulled via yfinance and query1.finance.yahoo.com."), "CC024_RAW_VENDOR_LEAK"),
        ("b3_fred_sp500_csv", lambda p: p.update(body_markdown="Chart data: https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500"), "CC024_RAW_VENDOR_LEAK"),
        ("b4_fred_sp500_vixcls", lambda p: p.update(body_markdown="Series FRED:SP500 and https://fred.stlouisfed.org/series/SP500 plus FRED:VIXCLS."), "CC024_RAW_VENDOR_LEAK"),
        ("r2_c6_fredgraph_png_sp500", lambda p: p.update(body_markdown="https://fred.stlouisfed.org/graph/fredgraph.png?id=SP500"), "CC024_RAW_VENDOR_LEAK"),
        ("r2_c6b_fred_baml", lambda p: p.update(body_markdown="High-yield spread from BAMLH0A0HYM2."), "CC024_RAW_VENDOR_LEAK"),
        ("r2_c6b_fred_nasdaqcom", lambda p: p.update(body_markdown="Index series NASDAQCOM and FRED:DJIA plus WILL5000IND."), "CC024_RAW_VENDOR_LEAK"),
        ("r2_c6b_series_id_sp500", lambda p: p.update(series_id="SP500"), "CC024_RAW_VENDOR_LEAK"),
        ("r2_c5_cnbc_quote", lambda p: p.update(body_markdown="Quotes via https://quote.cnbc.com/quote-html-webservice/restQuote"), "CC024_RAW_VENDOR_LEAK"),
        ("b5_investing_myfxbook", lambda p: p.update(body_markdown="Investing.com consensus and Myfxbook retail sentiment (https://www.myfxbook.com/community/outlook)."), "CC024_RAW_VENDOR_LEAK"),
        ("b6_occ_gex", lambda p: p.update(body_markdown="OCC options gamma exposure from https://www.theocc.com/market-data/"), "CC024_RAW_VENDOR_LEAK"),
        ("b7_tv_embed_widget", lambda p: p.update(body_markdown="Embed https://s3.tradingview.com/external-embedding/embed-widget-tickers.js"), "CC024_RAW_VENDOR_LEAK"),
        ("b7_tv_widgetembed", lambda p: p.update(body_markdown="Widget https://www.tradingview.com/widgetembed/?symbol=SPX"), "CC024_RAW_VENDOR_LEAK"),
        ("r2_c7_rights_fred_copyrighted", lambda p: p.update(rights_class="FRED_COPYRIGHTED"), "CC024_DENIED_PUBLIC_RIGHTS"),
        ("r2_c8_rights_list_non_string", lambda p: p.update(rights_class=["LICENSE_REQUIRED"]), "CC024_RIGHTS_CLASS_INVALID"),
        ("r2_c8_rights_int_non_string", lambda p: p.update(rights_class=123), "CC024_RIGHTS_CLASS_INVALID"),
        ("r2_c8_rights_none_non_string", lambda p: p.update(rights_class=None), "CC024_RIGHTS_CLASS_INVALID"),
    ],
)
def test_remediation_b16c21_h1_and_r2_h2_commercial_rights_blocked(label, mutator, expected_code):
    payload = clean_post_payload()
    mutator(payload)
    rec = fw.evaluate_payload(
        payload,
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=_publish_pause_state(),
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED, label
    assert rec["publish_allowed"] is False
    assert rec["cc024_audit"]["mode"] == fw.VERDICT_BLOCKED
    assert rec["cc024_audit"]["raw_vendor_leak_count"] >= 1, (label, rec["cc024_audit"])
    assert any(f["code"] == expected_code for f in rec["findings"]), (label, rec["findings"])
    assert_receipt_hash_valid(rec)


def test_remediation_b16c21_h1_preserves_public_fred_and_decision82_tradingview():
    p_fred = clean_post_payload()
    p_fred["body_markdown"] = (
        "10-year Treasury yield via FRED:DGS10 "
        "(https://fred.stlouisfed.org/series/DGS10 and https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10). "
        "Capital Chronicle offers analysis only, not financial advice or recommendations."
    )
    r_fred = fw.evaluate_payload(
        p_fred,
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=_publish_pause_state(),
    )
    assert r_fred["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, r_fred["findings"]
    assert r_fred["publish_allowed"] is True

    r_tv = fw.evaluate_payload(
        clean_chart_metadata_payload(),
        payload_kind="chart_metadata",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=_publish_pause_state(),
    )
    assert r_tv["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, r_tv["findings"]
    assert r_tv["publish_allowed"] is True


@pytest.mark.parametrize(
    ("label", "mutator", "expected_code", "expected_bucket"),
    [
        # B16C21-H2 + R2-H2: Substack audience, nested paywall/tier, paid prose, roadmap rails, affiliates
        ("b8_audience_only_paid", lambda p: p.update(audience="only_paid"), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("b9_audience_only_founding", lambda p: p.update(audience="only_founding"), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("b10_substack_audience_only_paid", lambda p: p.update(substack_audience="only_paid"), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("r2_c2_subscription_tier_sub_only", lambda p: p.update(subscription_tier="subscriber_only"), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("allowlist_unlisted_audience", lambda p: p.update(audience="inner_circle_members"), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("b11_nested_paywall_dict", lambda p: p.update(paywall={"enabled": True}), "CC024_PAYWALL_FIELD_ACTIVE", "paid_paywall_count"),
        ("r2_c1_nested_sub_price_dict", lambda p: p.update(subscription_price={"amount": 29, "currency": "USD"}), "CC024_PAYWALL_FIELD_ACTIVE", "paid_paywall_count"),
        ("r2_c1_nested_paid_tier_list", lambda p: p.update(paid_tier=["gold", "vip"]), "CC024_PAYWALL_FIELD_ACTIVE", "paid_paywall_count"),
        ("b12_nested_tier_paid", lambda p: p.update(tier={"name": "PAID"}), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("r2_c2_nested_tier_vip", lambda p: p.update(tier={"name": "VIP"}), "CC024_NON_FREE_TIER_FORBIDDEN", "paid_paywall_count"),
        ("r2_c3_paid_subscription_prose", lambda p: p.update(body_markdown="Get a paid subscription today. Paid members get early access."), "CC024_PAYWALL_UPSELL_FORBIDDEN", "paid_paywall_count"),
        ("b13_lemonsqueezy", lambda p: p.update(body_markdown="Join at https://capitalchronicle.lemonsqueezy.com/checkout"), "CC024_PAYWALL_UPSELL_FORBIDDEN", "paid_paywall_count"),
        ("b13_mql5_signals", lambda p: p.update(body_markdown="Subscribe at https://www.mql5.com/en/signals/12345"), "CC024_PAYWALL_UPSELL_FORBIDDEN", "paid_paywall_count"),
        ("b13_exness_social", lambda p: p.update(body_markdown="Mirror via https://social-trading.exness.com/strategy/99"), "CC024_PAYWALL_UPSELL_FORBIDDEN", "paid_paywall_count"),
        ("b14_affiliate_bool_key", lambda p: p.update(affiliate=True), "CC024_AFFILIATE_FIELD_ACTIVE", "affiliate_count"),
        ("b14_referral_str_key", lambda p: p.update(referral="jim123"), "CC024_AFFILIATE_FIELD_ACTIVE", "affiliate_count"),
        ("r2_c4b_referral_path", lambda p: p.update(body_markdown="Open via https://ibkr.com/referral/jim123"), "CC024_AFFILIATE_URL_PATH", "affiliate_count"),
        ("r2_c4b_ref_path_and_params", lambda p: p.update(body_markdown="Visit https://broker.example/ref/abc?partner_code=cc&ib=123&via=jim"), "CC024_AFFILIATE_URL_PARAM", "affiliate_count"),
    ],
)
def test_remediation_b16c21_h2_and_r2_h2_paywall_audience_and_affiliate_blocked(
    label, mutator, expected_code, expected_bucket
):
    payload = clean_post_payload()
    mutator(payload)
    rec = fw.evaluate_payload(
        payload,
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=_publish_pause_state(),
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED, label
    assert rec["publish_allowed"] is False
    assert rec["cc024_audit"][expected_bucket] >= 1, (label, rec["cc024_audit"])
    assert any(f["code"] == expected_code for f in rec["findings"]), (label, rec["findings"])
    assert_receipt_hash_valid(rec)


def test_remediation_b16c21_h2_allows_free_audience_and_cc107_anchor_card_tier():
    p = clean_post_payload()
    p["audience"] = "everyone"
    p["substack_audience"] = "free"
    p["paywall"] = {"enabled": False}
    p["paid_tier"] = []
    rec = fw.evaluate_payload(
        p,
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=_publish_pause_state(),
    )
    assert rec["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, rec["findings"]

    card = clean_card_payload()
    card["tier"]["value"] = "ANCHOR"
    rec_card = fw.evaluate_payload(
        card,
        payload_kind="card",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=_publish_pause_state(),
    )
    assert rec_card["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, rec_card["findings"]


@pytest.mark.parametrize(
    ("label", "mutator", "expected_code"),
    [
        # B16C21-M2: Markdown split, HTML entities, Unicode Cf (LRM/Invisible Times/Sep)
        ("md_bold_stop_loss", lambda p: p.update(body_markdown="Use **stop**-loss at 3920."), "RULE_A3_STOP_LOSS_LEVEL_LEAK"),
        ("md_bold_take_profit", lambda p: p.update(body_markdown="Set **take**-profit at 4210."), "RULE_A3_TAKE_PROFIT_LEVEL_LEAK"),
        ("md_bold_dur", lambda p: p.update(body_markdown="Account **DUR**343723 active."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("md_bold_exness", lambda p: p.update(body_markdown="Routed on **Ex**ness trial server."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("md_bold_paid", lambda p: p.update(body_markdown="This post is for **paid** subscribers only."), "CC024_PAYWALL_UPSELL_FORBIDDEN"),
        ("html_entity_gmt7", lambda p: p.update(body_markdown="Published 09:00 GMT&#43;7 today."), "PUBLIC_TIMEZONE_ET_REQUIRED"),
        ("html_entity_dur", lambda p: p.update(body_markdown="Account &#68;UR343723 active."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("cf_lrm_dur", lambda p: p.update(body_markdown="Account DU\u200eR343723 active."), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("cf_lrm_stoploss", lambda p: p.update(body_markdown="Set stop\u200eloss at 3920."), "RULE_A3_STOP_LOSS_LEVEL_LEAK"),
        ("cf_lrm_gmt7", lambda p: p.update(body_markdown="Published 09:00 GMT\u200e+7 today."), "PUBLIC_TIMEZONE_ET_REQUIRED"),
        ("cf_lrm_f_star", lambda p: p.update(body_markdown="Optimal f\u200e* = 0.04 on gold."), "RULE_A3_KELLY_SIZING_LOT_LEAK"),
        ("r2_b1_cf_invisible_times_sep", lambda p: p.update(body_markdown="D\u2062U\u2063R343723"), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("r2_b2_newline_take_profit", lambda p: p.update(body_markdown="take\nprofit"), "RULE_A3_TAKE_PROFIT_LEVEL_LEAK"),
        # R2-H1: Broker boundaries/separators & prefixed snake/camelCase keys & CC-791 odds keys
        ("r2_a1_acct_dur_key", lambda p: p.update({"acct_DUR343723": "ok"}), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("r2_a2_underscore_broker_ids", lambda p: p.update(body_markdown="Routed via acct_DUR343723 and login_279805139 and acct_U1234567"), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("r2_a3_hyphen_space_dur", lambda p: p.update(body_markdown="Account DUR-343723 and DUR 343723"), "RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK"),
        ("r2_a4_gold_stop_loss", lambda p: p.update(gold_stop_loss=3920.0), "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
        ("r2_a4_xauusd_take_profit", lambda p: p.update(xauusd_take_profit=4210.0), "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
        ("r2_a4_gold_entry_fill", lambda p: p.update(gold_entry_fill=4012.5), "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
        ("r2_a5_desk_lot_size", lambda p: p.update(desk_lot_size=0.05), "RULE_A3_FORBIDDEN_KELLY_SIZING_KEY"),
        ("r2_a5_xauusd_kelly_weight", lambda p: p.update(xauusd_kelly_weight=0.12), "RULE_A3_FORBIDDEN_KELLY_SIZING_KEY"),
        ("r2_a5_xauusd_realized_pnl", lambda p: p.update(xauusd_realized_pnl=4200.0), "RULE_A3_FORBIDDEN_ACCOUNT_PNL_KEY"),
        ("r2_a5_xauusd_sleeve_weight", lambda p: p.update(xauusd_sleeve_weight=0.35), "RULE_A3_FORBIDDEN_L4_SLEEVE_KEY"),
        ("r2_a6_camel_goldStopLoss", lambda p: p.update(goldStopLoss=3920.0), "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
        ("r2_a6_camel_xauusdTakeProfit", lambda p: p.update(xauusdTakeProfit=4210.0), "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
        ("r2_a6_camel_deskKellyFraction", lambda p: p.update(deskKellyFraction=0.04), "RULE_A3_FORBIDDEN_KELLY_SIZING_KEY"),
        ("r2_a7_kalshi_odds_pct", lambda p: p.update(kalshi_odds_pct=86), "PUBLIC_ODDS_LEAK_CC791"),
        ("r2_a7_fedwatch_cut_prob", lambda p: p.update(fedwatch_cut_probability=0.863), "PUBLIC_ODDS_LEAK_CC791"),
        ("r2_a7_gap_pp", lambda p: p.update(gap_pp=14.2), "PUBLIC_ODDS_LEAK_CC791"),
        ("r2_a7_polymarket_yes_price", lambda p: p.update(polymarket_yes_price=0.78), "PUBLIC_ODDS_LEAK_CC791"),
        # B16C21-M3 + R2-H1: Decision 157 target/SL/Entry/Kelly/PnL/Study prose
        ("c4a_gold_target_num", lambda p: p.update(body_markdown="Gold target 4,200 into Friday."), "RULE_A3_TAKE_PROFIT_LEVEL_LEAK"),
        ("c4b_sl_space_num", lambda p: p.update(body_markdown="SL 3,920 protects the setup."), "RULE_A3_STOP_LOSS_LEVEL_LEAK"),
        ("c4c_entry_space_num", lambda p: p.update(body_markdown="Entry 4,012.50 after CPI."), "RULE_A3_ENTRY_FILL_LEVEL_LEAK"),
        ("c4d_our_target_zone", lambda p: p.update(body_markdown="Our target zone is 4,200-4,250."), "RULE_A3_TAKE_PROFIT_LEVEL_LEAK"),
        ("r2_b3_kelly_variants", lambda p: p.update(body_markdown="0.5x Kelly (Kelly-optimal, Kelly = 0.04) with 0.05-lot sizing"), "RULE_A3_KELLY_SIZING_LOT_LEAK"),
        ("r2_b4_entered_at", lambda p: p.update(body_markdown="Entered at 4,012.50 after open."), "RULE_A3_ENTRY_FILL_LEVEL_LEAK"),
        ("r2_b4_weekly_pnl", lambda p: p.update(body_markdown="Weekly PnL: +3.2%."), "RULE_A3_ACCOUNT_BALANCE_EQUITY_PNL_LEAK"),
        ("r2_b5_study_10_hyphen", lambda p: p.update(body_markdown="study_10 and Study-8 results."), "RULE_A3_PRIVATE_STUDY_TAG_LEAK"),
    ],
)
def test_remediation_r2_h1_m2_m3_unicode_evasion_keys_and_prose_blocked(label, mutator, expected_code):
    payload = clean_post_payload()
    mutator(payload)
    rec = fw.evaluate_payload(
        payload,
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=_publish_pause_state(),
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED, label
    assert rec["publish_allowed"] is False
    assert any(f["code"] == expected_code for f in rec["findings"]), (label, rec["findings"])
    assert_receipt_hash_valid(rec)


def test_remediation_m3_l2_r2_l2_chart_overlay_word_boundary_and_all_values():
    ps = _publish_pause_state()
    for label, entry in (
        ("c7_name_stop_3950", {"name": "Stop 3950", "value": 3950}),
        ("r2_c10_name_stop_loss", {"name": "stop_loss", "price": 3900}),
        ("title_tp1", {"title": "TP1 4210"}),
    ):
        chart = clean_chart_metadata_payload()
        chart["tradingview_snapshot"]["levels_drawn"] = [entry]
        rec = fw.evaluate_payload(chart, payload_kind="chart_metadata", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
        assert rec["verdict"] == fw.VERDICT_BLOCKED, label
        assert any(f["code"] == "RULE_A3_CHART_EXECUTION_LEVEL_DRAWN" for f in rec["findings"]), (label, rec["findings"])

    # B16C21-L2 (C8): 'Tesla support' must NOT false-positive on substring 'sl' inside 'Tesla'.
    benign_chart = clean_chart_metadata_payload()
    benign_chart["tradingview_snapshot"]["levels_drawn"] = [{"label": "Tesla support", "price": 240}]
    rec_ok = fw.evaluate_payload(
        benign_chart,
        payload_kind="chart_metadata",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=ps,
    )
    assert rec_ok["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, rec_ok["findings"]
    assert rec_ok["publish_allowed"] is True


def test_remediation_m1_r2_m1_no_uncaught_crashes_on_overflow_surrogates_and_hostile_inputs():
    ps = _publish_pause_state()
    cases = [
        ("price_usd_10_400", lambda: fw.evaluate_payload({**clean_post_payload(), "price_usd": 10**400}, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)),
        ("paywall_10_400", lambda: fw.evaluate_payload({**clean_post_payload(), "paywall": 10**400}, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)),
        ("monthly_price_neg_10_400", lambda: fw.evaluate_payload({**clean_post_payload(), "monthly_price": -(10**400)}, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)),
        ("price_usd_nan", lambda: fw.evaluate_payload({**clean_post_payload(), "price_usd": float("nan")}, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)),
        ("price_usd_inf", lambda: fw.evaluate_payload({**clean_post_payload(), "price_usd": float("inf")}, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)),
        ("surrogate_dict_key", lambda: fw.evaluate_payload({"bad\ud800key": "ok"}, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)),
        ("surrogate_as_of_utc", lambda: fw.evaluate_payload(clean_post_payload(), as_of_utc="2026-12-15\ud800", gate_mode="publish", pause_state=ps)),
        ("surrogate_observed_at_utc", lambda: fw.evaluate_payload(clean_post_payload(), as_of_utc=AFTER_DEC15, observed_at_utc="2026-12-14\ud800", gate_mode="publish", pause_state=ps)),
        ("surrogate_artifact_id", lambda: fw.evaluate_payload(clean_post_payload(), as_of_utc=AFTER_DEC15, artifact_id="art\ud800", gate_mode="publish", pause_state=ps)),
        ("object_gate_mode", lambda: fw.evaluate_payload(clean_post_payload(), as_of_utc=AFTER_DEC15, gate_mode=object(), pause_state=ps)),
        ("list_gate_mode", lambda: fw.evaluate_payload(clean_post_payload(), as_of_utc=AFTER_DEC15, gate_mode=[], pause_state=ps)),
        ("surrogate_gate_mode", lambda: fw.evaluate_payload(clean_post_payload(), as_of_utc=AFTER_DEC15, gate_mode="pub\ud800", pause_state=ps)),
        ("int_spec_path", lambda: fw.evaluate_release_batch([{"path": 123}], as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)),
        ("int_payload_file", lambda: fw.evaluate_payload_file(123, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)),
        ("int_raw_bytes", lambda: fw.evaluate_release_batch([{"raw_bytes": 123}], as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)),
    ]
    for label, fn in cases:
        rec = fn()
        assert rec["verdict"] == fw.VERDICT_BLOCKED, label
        assert rec["publish_allowed"] is False, label
        assert_receipt_hash_valid(rec)


def test_remediation_m5_r2_m2_restored_json_dry_run_and_falsey_started_at_rejected(tmp_path):
    # C9: restored.json with dry_run=true must NEVER authorize publish.
    for label, restored_obj, expected_code in (
        ("dry_run_true", {"started_at_utc": DEC15_BOUNDARY, "dry_run": True}, "RESTORED_MARKER_DRY_RUN_FORBIDDEN"),
        ("dry_run_str_false", {"started_at_utc": DEC15_BOUNDARY, "dry_run": "false"}, "RESTORED_MARKER_DRY_RUN_FORBIDDEN"),
        ("dry_run_int_1", {"started_at_utc": DEC15_BOUNDARY, "dry_run": 1}, "RESTORED_MARKER_DRY_RUN_FORBIDDEN"),
        ("dry_run_none", {"started_at_utc": DEC15_BOUNDARY, "dry_run": None}, "RESTORED_MARKER_DRY_RUN_FORBIDDEN"),
        # R2-M2 (D7): explicit falsey started_at_utc must NOT fall back via `or` to ended_at_utc.
        ("started_false_fallback", {"started_at_utc": False, "ended_at_utc": DEC15_BOUNDARY}, "UTC_CLOCK_INVALID"),
        ("started_empty_fallback", {"started_at_utc": "", "ended_at_utc": DEC15_BOUNDARY}, "UTC_CLOCK_INVALID"),
        ("started_none_fallback", {"started_at_utc": None, "ended_at_utc": DEC15_BOUNDARY}, "UTC_CLOCK_INVALID"),
    ):
        p_dir, s_dir = make_pause_snapshot(tmp_path / label, resume_at=DEC15_BOUNDARY, stops=(), restored_at=None)
        (p_dir / "restored.json").write_bytes((json.dumps(restored_obj) + "\n").encode("utf-8"))
        rec = fw.evaluate_payload(
            clean_post_payload(),
            payload_kind="post",
            as_of_utc=AFTER_DEC15,
            gate_mode="publish",
            pause_dir=p_dir,
            publisher_stops_dir=s_dir,
        )
        assert rec["verdict"] == fw.VERDICT_BLOCKED, label
        assert rec["publish_allowed"] is False, label
        assert rec["pause_gate"]["failure_code"] == expected_code, (label, rec["pause_gate"])

    # Valid explicit dry_run=false passes cleanly.
    ok_dir, ok_stops = make_pause_snapshot(tmp_path / "ok_live", resume_at=DEC15_BOUNDARY, stops=(), restored_at=None)
    (ok_dir / "restored.json").write_bytes(
        (json.dumps({"started_at_utc": DEC15_BOUNDARY, "dry_run": False}) + "\n").encode("utf-8")
    )
    rec_ok = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_dir=ok_dir,
        publisher_stops_dir=ok_stops,
    )
    assert rec_ok["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH
    assert rec_ok["publish_allowed"] is True


def test_remediation_r2_m3_unified_key_redactor_zero_verbatim_echo():
    ps = _publish_pause_state()
    # D6: private-alpha & numeric-level dict keys never echoed in receipt findings/paths
    rec_d6 = fw.evaluate_payload(
        {"Kelly f* = 0.042": 1, "stop-loss 3920.50": 1, "Study #10 L4 weights 0.45": 1},
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=ps,
    )
    assert rec_d6["verdict"] == fw.VERDICT_BLOCKED
    s_d6 = json.dumps(rec_d6)
    for leaked in ("Kelly f*", "0.042", "stop-loss 3920.50", "3920.50", "Study #10", "L4 weights", "0.45"):
        assert leaked not in s_d6, (leaked, s_d6)
    assert "<REDACTED_KEY#" in s_d6
    assert_receipt_hash_valid(rec_d6)

    # D13: duplicate-key broker suffix never echoed in duplicate-key diagnostic
    rec_d13 = fw.evaluate_payload_bytes(
        b'{"acct_DUR343723":1,"acct_DUR343723":2}',
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=ps,
    )
    assert rec_d13["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "DUPLICATE_JSON_KEY_FORBIDDEN" for f in rec_d13["findings"])
    s_d13 = json.dumps(rec_d13)
    assert "DUR343723" not in s_d13
    assert "acct_DUR343723" not in s_d13
    assert "<REDACTED_KEY#" in s_d13
    assert_receipt_hash_valid(rec_d13)


def test_remediation_m4_r2_m4_batch_dedupe_preserves_distinct_artifact_ids():
    ps = _publish_pause_state()
    bad_a = clean_post_payload()
    bad_a["body_markdown"] = "Upgrade to paid VIP signals via DUR343723."
    bad_b = clean_post_payload()
    bad_b["body_markdown"] = "Upgrade to paid VIP signals via DUR343723."
    rec = fw.evaluate_release_batch(
        [
            {"artifact_id": "art-1", "payload_kind": "post", "payload": bad_a},
            {"artifact_id": "art-2", "payload_kind": "post", "payload": bad_b},
        ],
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=ps,
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED
    assert [(a["artifact_id"], a["finding_count"]) for a in rec["artifacts"]] == [("art-1", 3), ("art-2", 3)]
    assert rec["counts"]["total_findings"] == 6
    assert rec["cc024_audit"]["paid_paywall_count"] == 4
    assert sorted({f["artifact_id"] for f in rec["findings"]}) == ["art-1", "art-2"]
    assert_receipt_hash_valid(rec)


@pytest.mark.parametrize(
    ("label", "text", "expected_code"),
    [
        # B16C21-M6 + R2-M5: Decision 107 raw CFD/broker symbols + Decision 109 AI labels
        ("d107_ustec_cfd_us500_xauusd", "USTEC CFD and US500 jumped while XAUUSD steadied.", "PUBLIC_RAW_CFD_SYMBOL_DECISION_107"),
        ("d107_broker_suffix_m", "US500m and XAUUSDm and USTECm moved overnight.", "PUBLIC_RAW_CFD_SYMBOL_DECISION_107"),
        ("d109_sonnet", "Edited by Sonnet before release.", "PUBLIC_AI_MODEL_AUTHORSHIP_LEAK"),
        ("d109_haiku", "Drafted by Haiku summary pass.", "PUBLIC_AI_MODEL_AUTHORSHIP_LEAK"),
        ("d109_fable", "Reviewed by Fable model.", "PUBLIC_AI_MODEL_AUTHORSHIP_LEAK"),
        ("d109_luna", "Prepared by Luna desk pass.", "PUBLIC_AI_MODEL_AUTHORSHIP_LEAK"),
        ("d109_agy", "Generated with agy CLI helper.", "PUBLIC_AI_MODEL_AUTHORSHIP_LEAK"),
        # R2-L1: dangerous / non-HTTP URL schemes
        ("r2_l1_href_js", "Click href=javascript:alert(1) now.", "PUBLIC_WEBAPP_UNSAFE_URL_SCHEME"),
        ("r2_l1_vbscript", "Run vbscript:msgbox(1) inline.", "PUBLIC_WEBAPP_UNSAFE_URL_SCHEME"),
        ("r2_l1_ftp", "Download ftp://files.example/a today.", "PUBLIC_WEBAPP_UNSAFE_URL_SCHEME"),
    ],
)
def test_remediation_m6_r2_m5_r2_l1_decision107_ai_labels_and_url_schemes(label, text, expected_code):
    payload = clean_post_payload()
    payload["body_markdown"] = text
    rec = fw.evaluate_payload(
        payload,
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=_publish_pause_state(),
    )
    assert rec["verdict"] == fw.VERDICT_BLOCKED, label
    assert any(f["code"] == expected_code for f in rec["findings"]), (label, rec["findings"])


def test_remediation_l1_l3_l4_r2_l3_macro_flows_list_utc_and_dir_scan_hardening(tmp_path, monkeypatch):
    ps = _publish_pause_state()

    # B16C21-L1 (D1 & D3): macro equity/capital flow journalism stays clean; numeric bare equity/balance still blocks
    macro_post = clean_post_payload()
    macro_post["body_markdown"] = (
        "US equity outflows reached $12 billion while foreign capital inflows hit $45 billion. "
        "Capital Chronicle offers analysis only, not financial advice or recommendations."
    )
    macro_post["equity"] = "US equity outflows slowed into Friday."
    macro_post["balance"] = "US trade balance narrowed to $68.5 billion."
    r_macro = fw.evaluate_payload(macro_post, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
    assert r_macro["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, r_macro["findings"]

    num_equity = clean_post_payload()
    num_equity["equity"] = 50000.0
    r_num_eq = fw.evaluate_payload(num_equity, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
    assert r_num_eq["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "RULE_A3_FORBIDDEN_ACCOUNT_PNL_KEY" for f in r_num_eq["findings"])

    # B16C21-L3 (A5): list-wrapped *_utc timestamps enforce strict UTC
    list_utc = clean_post_payload()
    list_utc["published_at_utc"] = ["2026-12-15T12:00:00+07:00"]
    r_list_utc = fw.evaluate_payload(list_utc, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
    assert r_list_utc["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "UTC_CLOCK_INVALID" for f in r_list_utc["findings"])

    # B16C21-L4 (D7): expanded private filenames & max_files truncated flag
    pub_dir = tmp_path / "pub_dir"
    pub_dir.mkdir()
    for fname in ("private-desk.json", "attention-map-summary.json", "contentops-newsroom-summary.json", "market-forces-attribution.json", "_private_texts.json"):
        (pub_dir / fname).write_bytes(b'{"title":"clean"}\n')
    scan_bad_names = fw.scan_public_directory_readonly(pub_dir)
    assert scan_bad_names["failed_files"] == 5
    assert scan_bad_names["clean_files"] == 0
    assert scan_bad_names["truncated"] is False
    assert all("PUBLIC_WEBAPP_FORBIDDEN_FILENAME" in f["codes"] for f in scan_bad_names["failures"])

    scan_trunc = fw.scan_public_directory_readonly(pub_dir, max_files=2)
    assert scan_trunc["files_scanned"] == 2
    assert scan_trunc["truncated"] is True

    # R2-L3: symlink mode & lstat OSError fail closed cleanly in scan_public_directory_readonly and evaluate_pause_gate
    sym_dir = tmp_path / "sym_dir"
    sym_dir.mkdir()
    target_f = sym_dir / "bad_link.json"
    target_f.write_bytes(b'{"ok":1}\n')
    real_lstat = Path.lstat

    def fake_lstat_symlink(self, *args, **kwargs):
        if self.name == "bad_link.json":
            class _FakeStat:
                st_mode = fw.stat.S_IFLNK | 0o777
                st_size = 10
            return _FakeStat()
        return real_lstat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", fake_lstat_symlink)
    scan_sym = fw.scan_public_directory_readonly(sym_dir)
    assert scan_sym["failed_files"] == 1
    assert scan_sym["failures"][0]["codes"] == ["NON_REGULAR_FILE_FORBIDDEN"]

    p_dir, s_dir = make_pause_snapshot(tmp_path / "lstat_err", resume_at=DEC15_BOUNDARY, stops=(), restored_at=DEC15_BOUNDARY)

    def fake_lstat_perm_error(self, *args, **kwargs):
        if self.name == "restored.json":
            raise PermissionError("access denied")
        return real_lstat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", fake_lstat_perm_error)
    r_perm = fw.evaluate_payload(
        clean_post_payload(),
        payload_kind="post",
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_dir=p_dir,
        publisher_stops_dir=s_dir,
    )
    assert r_perm["verdict"] == fw.VERDICT_BLOCKED
    assert r_perm["pause_gate"]["failure_code"] == "RESTORED_STAT_FAILED"


# ---------------------------------------------------------------------------
# Cycle #23a-r2: Unified Ops Product #98/#99 + Batch #172/#173 (7M / 6L)
# ---------------------------------------------------------------------------


def test_c23a_r2_m1_and_m6_nul_hostile_pathlike_ads_nt_prefix_and_dos_device_paths(tmp_path):
    ps = _publish_pause_state()
    clean_file = tmp_path / "clean.json"
    clean_file.write_bytes(json.dumps(clean_post_payload()).encode("utf-8") + b"\n")

    class _BadPathBytes:
        def __fspath__(self):
            return b"foo.json"

    class _BadPathValueErr:
        def __fspath__(self):
            raise ValueError("boom")

    class _BadPathTypeErr:
        def __fspath__(self):
            raise TypeError("bad type")

    # M1: NUL bytes & hostile PathLike never raise uncaught ValueError/TypeError.
    for hostile in ("foo\x00bar.json", _BadPathBytes(), _BadPathValueErr(), _BadPathTypeErr(), "   "):
        r_file = fw.evaluate_payload_file(hostile, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
        assert r_file["verdict"] == fw.VERDICT_BLOCKED
        assert r_file["publish_allowed"] is False

        r_batch = fw.evaluate_release_batch(
            [{"path": hostile}], as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps
        )
        assert r_batch["verdict"] == fw.VERDICT_BLOCKED

        r_pause = fw.evaluate_pause_gate(
            AFTER_DEC15,
            gate_mode="publish",
            pause_dir=hostile,
            publisher_stops_dir=tmp_path,
        )
        assert r_pause["verdict"] == fw.VERDICT_BLOCKED

        r_scan = fw.scan_public_directory_readonly(hostile)
        assert r_scan["exists"] is False
        assert r_scan["failed_files"] == 1
        assert r_scan["findings_count"] == 1

    # M6: Real Windows NTFS Alternate Data Stream (clean.json:secret) blocked before open.
    ads_str = str(clean_file) + ":secret"
    try:
        Path(ads_str).write_bytes(json.dumps(clean_post_payload()).encode("utf-8") + b"\n")
    except OSError:
        pass
    r_ads = fw.evaluate_payload_file(ads_str, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
    assert r_ads["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "WINDOWS_ADS_PATH_FORBIDDEN" for f in r_ads["findings"])

    # M6: NT/device prefixes, raw UNC, trailing dot/space, DOS reserved names (CON .dir / CON .json).
    hostile_win_paths = [
        (r"\??\C:\Windows\win.ini", "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        ("/??/C:/Windows/win.ini", "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        (r"\\.\NUL", "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        (r"\\?\C:\clean.json", "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        (r"\\server\share\clean.json", "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        ("//server/share/clean.json", "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        (str(tmp_path / "CON .dir" / "clean.json"), "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        (str(tmp_path / "CON .json"), "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        (str(tmp_path / "NUL.json"), "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        (str(tmp_path / "com1.json"), "WINDOWS_DEVICE_PATH_FORBIDDEN"),
        (str(tmp_path / "clean.json."), "WINDOWS_TRAILING_DOT_OR_SPACE_FORBIDDEN"),
        (str(tmp_path / "clean.json "), "WINDOWS_TRAILING_DOT_OR_SPACE_FORBIDDEN"),
        (str(tmp_path / "dir." / "clean.json"), "WINDOWS_TRAILING_DOT_OR_SPACE_FORBIDDEN"),
    ]
    for bad_path, expected_code in hostile_win_paths:
        rec = fw.evaluate_payload_file(bad_path, as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
        assert rec["verdict"] == fw.VERDICT_BLOCKED, bad_path
        assert any(f["code"] == expected_code for f in rec["findings"]), (bad_path, rec["findings"])


def test_c23a_r2_m2_duplicate_and_private_artifact_id_redacted_and_blocked():
    ps = _publish_pause_state()
    clean = clean_post_payload()

    # Duplicate private broker artifact_id triggers BOTH DUPLICATE_ARTIFACT_ID and private block with 0 echo.
    r_dup_priv = fw.evaluate_release_batch(
        [
            {"artifact_id": "acct_DUR343723", "payload_kind": "post", "payload": clean},
            {"artifact_id": "acct_DUR343723", "payload_kind": "post", "payload": clean},
        ],
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=ps,
    )
    assert r_dup_priv["verdict"] == fw.VERDICT_BLOCKED
    codes = {f["code"] for f in r_dup_priv["findings"]}
    assert "DUPLICATE_ARTIFACT_ID" in codes
    assert "RULE_A3_PRIVATE_ARTIFACT_ID_FORBIDDEN" in codes
    assert "DUR343723" not in json.dumps(r_dup_priv)

    # Single private broker artifact_id also fails closed with 0 echo.
    r_single_priv = fw.evaluate_payload(
        clean, payload_kind="post", artifact_id="acct_DUR343723", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps
    )
    assert r_single_priv["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "RULE_A3_PRIVATE_ARTIFACT_ID_FORBIDDEN" for f in r_single_priv["findings"])
    assert "DUR343723" not in json.dumps(r_single_priv)

    # Duplicate numeric-version artifact_id ("post 1.0") also triggers DUPLICATE_ARTIFACT_ID.
    r_dup_ver = fw.evaluate_release_batch(
        [
            {"artifact_id": "post 1.0", "payload_kind": "post", "payload": clean},
            {"artifact_id": "post 1.0", "payload_kind": "post", "payload": clean},
        ],
        as_of_utc=AFTER_DEC15,
        gate_mode="publish",
        pause_state=ps,
    )
    assert r_dup_ver["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "DUPLICATE_ARTIFACT_ID" for f in r_dup_ver["findings"])


@pytest.mark.parametrize(
    "case_name,field,value",
    [
        ("ascii_nul_broker", "body", "Account D\x00UR343723 active."),
        ("ascii_nul_paid", "body", "For pa\x00id subscribers only."),
        ("ascii_nul_yahoo", "body", "Data from Ya\x00hoo Finance."),
        ("ascii_nul_stoploss", "body", "Set stop\x00loss at 3920."),
        ("ascii_soh_broker", "body", "Account D\x01UR343723 active."),
        ("mn_cgj_broker", "body", "Account DU\u034fR343723 active."),
        ("mn_cgj_paid", "body", "For pa\u034fid subscribers only."),
        ("mn_vs16_stoploss", "body", "Set stop\ufe0floss at 3920."),
        ("html_bold_stoploss", "body_html", "<p>Set <b>stop</b>-loss at 3920.</p>"),
        ("html_span_broker", "body_html", "<p>Account <span>DUR</span>343723</p>"),
        ("html_em_paid", "body_html", "<p>For <em>paid</em> subscribers only.</p>"),
        ("tab_split_js_href", "body_html", '<a href="java\tscript:alert(1)">click</a>'),
        ("entity_tab_js_href", "body_html", '<a href="java&#x09;script:alert(1)">click</a>'),
        ("newline_split_js_href", "body_html", '<a href="java\nscript:alert(1)">click</a>'),
        ("md_split_affiliate_url", "body", "Open https://broker.example/**ref**/abc now."),
        ("html_split_affiliate_url", "body_html", "Open https://broker.example/<b>ref</b>/abc now."),
        ("triple_html_entity_broker", "body", "Account &amp;amp;#68;UR343723 active."),
        ("pct_encoded_affiliate_path", "body", "See https://broker.example/%61ffiliate/jim for details."),
        ("pct_encoded_ref_path", "body", "See https://broker.example/%72%65%66/jim123 for details."),
        ("pct_encoded_fred_sp500_url", "body", "Chart https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP%3500 here."),
        ("pct_encoded_relative_fred", "body", "Relative fredgraph.csv?id=SP%3500 feed."),
    ],
)
def test_c23a_r2_m3_and_batch172_l1_l2_obfuscation_html_xss_and_url_evasions_blocked(case_name, field, value):
    ps = _publish_pause_state()
    p = clean_post_payload()
    p[field] = value
    rec = fw.evaluate_payload(p, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
    assert rec["verdict"] == fw.VERDICT_BLOCKED, (case_name, rec)
    assert rec["publish_allowed"] is False


def test_c23a_r2_m4_clean_macro_prose_allowed_while_real_levels_and_icebofa_stay_blocked():
    ps = _publish_pause_state()
    clean_sentences = [
        "The Federal Reserve inflation target is 2% while the 2026 target of 2.0 percent holds.",
        "FRED data for DGS10 rose as ICE Brent crude rallied into the close.",
        "FRED industrial production fell after severe ice storms hit Texas.",
        "Sticky services inflation could stop 2026 rate cuts from accelerating.",
        "Treasury liquidity measures back-stop 500 billion in money market flows.",
        "Calendar entry 1 highlights US payrolls at 08:30 ET.",
        "Data entry 2026 reflects revised BLS benchmarks.",
    ]
    for sentence in clean_sentences:
        p = clean_post_payload()
        p["body"] = sentence
        rec = fw.evaluate_payload(p, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
        assert rec["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, (sentence, rec["findings"])

    # Real private levels & copyrighted FRED ICE BofA series MUST remain blocked.
    hostile_sentences = [
        ("Stop 3950 on gold.", "RULE_A3_STOP_LOSS_LEVEL_LEAK"),
        ("Stop at 2026 on break.", "RULE_A3_STOP_LOSS_LEVEL_LEAK"),
        ("Entry 4,012.50 on pullback.", "RULE_A3_ENTRY_FILL_LEVEL_LEAK"),
        ("Entry 3950 triggered.", "RULE_A3_ENTRY_FILL_LEVEL_LEAK"),
        ("Gold target 4,200 into Friday.", "RULE_A3_TAKE_PROFIT_LEVEL_LEAK"),
        ("Gold $2,026 target active.", "RULE_A3_TAKE_PROFIT_LEVEL_LEAK"),
        ("FRED:ICEBOFA_HY credit spread.", "CC024_RAW_VENDOR_LEAK"),
        ("FRED:ICEBAML_IG index series.", "CC024_RAW_VENDOR_LEAK"),
    ]
    for sentence, expected_code in hostile_sentences:
        p = clean_post_payload()
        p["body"] = sentence
        rec = fw.evaluate_payload(p, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
        assert rec["verdict"] == fw.VERDICT_BLOCKED, sentence
        assert any(f["code"] == expected_code for f in rec["findings"]), (sentence, rec["findings"])


def test_c23a_r2_m5_windows_ntfs_junction_fails_closed_without_traversal(tmp_path):
    pub_dir = tmp_path / "pub_junction_root"
    ext_dir = tmp_path / "external_secret_dir"
    pub_dir.mkdir()
    ext_dir.mkdir()
    (ext_dir / "external.json").write_bytes(b'{"title":"clean"}\n')
    junction_dir = pub_dir / "escape_junction"

    created = False
    try:
        proc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction_dir), str(ext_dir)],
            capture_output=True,
            text=True,
        )
        created = proc.returncode == 0
        if created:
            scan = fw.scan_public_directory_readonly(pub_dir)
            assert scan["failed_files"] == 1
            assert scan["clean_files"] == 0
            assert scan["failures"][0]["file"] == "escape_junction"
            assert scan["failures"][0]["codes"] == ["NON_REGULAR_FILE_FORBIDDEN"]

            # Root junction itself also fails closed.
            scan_root = fw.scan_public_directory_readonly(junction_dir)
            assert scan_root["exists"] is False
            assert scan_root["failed_files"] == 1
            assert scan_root["failures"][0]["codes"] == ["NON_REGULAR_FILE_FORBIDDEN"]
    finally:
        if created and junction_dir.exists():
            os.rmdir(junction_dir)


def test_c23a_r2_m7_investing_structured_ids_blocked_and_sec_investing_public_allowed():
    ps = _publish_pause_state()
    for token in (
        "release_betas.US_NFP.consensus.investing.NFP_PAYROLL_CHANGE",
        "src:cite:investing:us_nfp_20261106",
        "CITED_SOURCE_INVESTING",
        "investing_com",
    ):
        p = clean_post_payload()
        p["body"] = f"Metric identifier {token} in snapshot."
        rec = fw.evaluate_payload(p, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
        assert rec["verdict"] == fw.VERDICT_BLOCKED, token
        assert any(
            f["code"] == "CC024_RAW_VENDOR_LEAK" and f["rule"] == "INVESTING_MYFXBOOK_CONSENSUS"
            for f in rec["findings"]
        ), (token, rec["findings"])

    # SEC clean macro prose must stay 100% green.
    p_clean = clean_post_payload()
    p_clean["body"] = "SEC disclosures protect the investing public during market volatility."
    rec_clean = fw.evaluate_payload(
        p_clean, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps
    )
    assert rec_clean["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, rec_clean["findings"]


def test_c23a_r2_ops_l1_to_l4_fredgraph_yahoo_compact_keys_redaction_and_event_tier(tmp_path):
    ps = _publish_pause_state()

    # Ops L1: bare fredgraph?id=... & legacy Yahoo endpoints blocked; public DGS10 allowed.
    for raw in (
        "fredgraph.csv?id=SP500",
        "fredgraph.png?id=DJIA",
        "fredgraph.svg?id=ICEBOFA",
        "https://ichart.yahoo.com/table.csv?s=SPY",
        "https://chart.yahoo.com/z?s=GLD",
        "https://fc.yahoo.com/data",
    ):
        p = clean_post_payload()
        p["body"] = f"Reference {raw}"
        rec = fw.evaluate_payload(p, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
        assert rec["verdict"] == fw.VERDICT_BLOCKED, raw
        assert any(f["code"] == "CC024_RAW_VENDOR_LEAK" for f in rec["findings"]), (raw, rec["findings"])

    p_dgs10 = clean_post_payload()
    p_dgs10["body"] = "Public Treasury yield series fredgraph.csv?id=DGS10 remains lawful."
    r_dgs10 = fw.evaluate_payload(
        p_dgs10, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps
    )
    assert r_dgs10["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, r_dgs10["findings"]

    # Ops L2: xauusdPnL, deskPnL, goldSL, goldTP, Study10, study8 all blocked.
    for key, expected_code in (
        ("xauusdPnL", "RULE_A3_FORBIDDEN_ACCOUNT_PNL_KEY"),
        ("deskPnL", "RULE_A3_FORBIDDEN_ACCOUNT_PNL_KEY"),
        ("goldSL", "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
        ("goldTP", "RULE_A3_FORBIDDEN_EXECUTION_KEY"),
    ):
        p = clean_post_payload()
        p[key] = 42.5
        rec = fw.evaluate_payload(p, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
        assert rec["verdict"] == fw.VERDICT_BLOCKED, key
        assert any(f["code"] == expected_code for f in rec["findings"]), (key, rec["findings"])

    for study_tok in ("Study10", "study8"):
        p = clean_post_payload()
        p["body"] = f"See {study_tok} notes."
        rec = fw.evaluate_payload(p, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps)
        assert rec["verdict"] == fw.VERDICT_BLOCKED, study_tok
        assert any(f["code"] == "RULE_A3_PRIVATE_STUDY_TAG_LEAK" for f in rec["findings"]), study_tok

    # Ops L3: hostile payload_kind="DUR343723" and gate_mode="DUR343723" never echo raw value.
    r_kind = fw.evaluate_payload(
        clean_post_payload(), payload_kind="DUR343723", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps
    )
    assert r_kind["verdict"] == fw.VERDICT_BLOCKED
    assert "DUR343723" not in json.dumps(r_kind)

    r_mode = fw.evaluate_payload(
        clean_post_payload(), payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="DUR343723", pause_state=ps
    )
    assert r_mode["verdict"] == fw.VERDICT_BLOCKED
    assert "DUR343723" not in json.dumps(r_mode)

    # Ops L4: event_tier="T1" allowed while event_tier="paid" blocked; DIRECTORY_MISSING reports failed_files=1.
    p_event_t1 = clean_post_payload()
    p_event_t1["event_tier"] = "T1"
    r_ev = fw.evaluate_payload(
        p_event_t1, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps
    )
    assert r_ev["verdict"] == fw.VERDICT_ALLOW_FREE_PUBLISH, r_ev["findings"]

    p_event_paid = clean_post_payload()
    p_event_paid["event_tier"] = "paid"
    r_ev_paid = fw.evaluate_payload(
        p_event_paid, payload_kind="post", as_of_utc=AFTER_DEC15, gate_mode="publish", pause_state=ps
    )
    assert r_ev_paid["verdict"] == fw.VERDICT_BLOCKED
    assert any(f["code"] == "CC024_NON_FREE_TIER_FORBIDDEN" for f in r_ev_paid["findings"])

    missing_scan = fw.scan_public_directory_readonly(tmp_path / "does_not_exist_dir")
    assert missing_scan["exists"] is False
    assert missing_scan["failed_files"] == 1
    assert missing_scan["findings_count"] == 1
    assert missing_scan["failures"][0]["code"] == "DIRECTORY_MISSING"
