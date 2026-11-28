"""Hermetic adversarial tests for Dec-15 FREE-tier public-disclosure & Rule A3 firewall."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
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
        ("post", {"title": posts["wraps"]["daily"]["title"], "body": posts["wraps"]["daily"]["body_excerpt"]}),
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
