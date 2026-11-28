"""Dec-15 FREE-tier Public-Disclosure & Rule A3 Zero-Leak Pre-Publish Firewall.

Standalone, pure-stdlib, read-only, fail-closed pre-publish gate inspecting
candidate ContentOps post, card, caption, chart-metadata, and digest JSON
payloads prior to any ~15 Dec 2026 FREE-tier publication.

Enforces:
1. Rule A3 zero private-alpha leakage:
   - Internal Kelly f* / geometric-growth g(f) / sizing / lot formulas
   - Exact stop-loss / take-profit / entry fill levels (preserving macro policy targets)
   - Account balance / equity / PnL / margin / R-expectancy figures (preserving macro terms)
   - Broker / MT5 / IBKR account identifiers (e.g., DUR343723, Exness MT5 logins)
   - Private Study #6..#11 JSON tags (private_only, public_export_forbidden, schemas)
   - Raw L4 / sleeve / portfolio weights and internal alpha-stack markers
   - All public-webapp-preview forbidden leak classes (Decision 184 s2.4 private
     sidecar tokens, window.__CC_*__ globals, book dump markers, CC-791
     PublicOddsLeakCheckV1 numeric market/prediction/FedWatch odds, Decision 83
     preview-host links, Decision 90 ET-only public times, Decision 109 / CC-855
     AI-model authorship leaks, and raw licensed vendor redistribution dumps)
2. CC-024 / Decision 96 FREE-only compliance:
   - Blocks paywall / VIP / paid subscription / pledge upsell CTAs and paid tiers
   - Blocks affiliate / referral / broker-IB links and promotional codes
   - Verifies strict pause-gate state (resume_at_utc >= 2026-12-14T17:00:00Z and
     3/3 publisher .stop awareness; fail-closed HOLD_PAUSED_BEFORE_DEC15 prior to
     2026-12-14T17:00:00Z)
3. Strict structural, numeric, and clock hygiene (Rule A3):
   - Rejects bool values in numeric/clock/count fields, NaN, Inf, -Inf, 1e400,
     10**400 (and huge ints overflowing IEEE-754), UTC OverflowError, naive
     timestamps, duplicate JSON object keys, UTF-8 BOM/invalid bytes, unpaired
     Unicode surrogates, deep nesting, and malformed JSON.
4. Deterministic SHA-256 content-hash receipts compatible with CC-1011 (b18f527bfe07):
   - Emits exact canonical UTF-8 LF JSON release manifest + candidate_sha256 +
     cc024_audit object (mode=FREE_ONLY, observed_at_utc, candidate_sha256,
     checked_artifact_count, paid_paywall_count, affiliate_count,
     raw_vendor_leak_count) and deterministic receipt_sha256 without echoing
     private source text in diagnostics.

Read-only: zero filesystem writes, zero network calls, zero process spawns.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import html
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import Any, Iterable, Mapping, Sequence
import unicodedata
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

POLICY = "CC_DEC15_PUBLIC_DISCLOSURE_FIREWALL_V1"
RECEIPT_SCHEMA = "Dec15PublicDisclosureFirewallReceiptV1"
RELEASE_MANIFEST_SCHEMA = "Dec15FreeReleaseManifestV1"
CC1011_COMPAT_COMMIT = "b18f527bfe07"

FREE_ONLY_MODE = "FREE_ONLY"
DEC15_PAUSE_BOUNDARY_UTC = "2026-12-14T17:00:00Z"
PUBLISHER_STOPS: tuple[str, ...] = (
    "runner-publisher.stop",
    "runner-publisher-b.stop",
    "runner-publisher-c.stop",
)

VERDICT_BLOCKED = "BLOCKED"
VERDICT_HOLD_PAUSED_BEFORE_DEC15 = "HOLD_PAUSED_BEFORE_DEC15"
VERDICT_READY_FREE_UNPAUSE = "READY_FREE_UNPAUSE"
VERDICT_ALLOW_FREE_PUBLISH = "ALLOW_FREE_PUBLISH"

GATE_MODE_PREFLIGHT = "preflight"
GATE_MODE_PUBLISH = "publish"
SUPPORTED_GATE_MODES = frozenset({GATE_MODE_PREFLIGHT, GATE_MODE_PUBLISH})

EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_HOLD_PAUSED = 2

SUPPORTED_PAYLOAD_KINDS = frozenset({
    "post",
    "card",
    "caption",
    "chart_metadata",
    "digest",
})
_PAYLOAD_KIND_ALIASES: Mapping[str, str] = {
    "post": "post",
    "article": "post",
    "market_wrap": "post",
    "market-wrap": "post",
    "wrap": "post",
    "card": "card",
    "data_card": "card",
    "data-card": "card",
    "caption": "caption",
    "chart_metadata": "chart_metadata",
    "chart-metadata": "chart_metadata",
    "chart": "chart_metadata",
    "digest": "digest",
    "daily_digest": "digest",
    "daily-digest": "digest",
}

UTC = timezone.utc
ET = ZoneInfo("America/New_York")

MAX_JSON_DEPTH = 64
MAX_PAYLOAD_BYTES = 10 * 1024 * 1024
MAX_JSON_INT_DIGITS = 308
MAX_JSON_INT_BIT_LENGTH = 1023
MAX_FINDINGS_REPORTED = 200

_UTC_CLOCK_RE = re.compile(
    r"^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]{1,9}))?(Z|\+00:00)$"
)
_ISO_OFFSET_CLOCK_RE = re.compile(
    r"^([0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]{1,9}))?"
    r"(Z|[+-][0-9]{2}:[0-9]{2})$"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\u2060\u2062\u2063\ufeff\u00ad]")
_WS_COLLAPSE_RE = re.compile(r"\s+")
_MD_STAR_ONLY_RE = re.compile(r"[`*~]")
_MD_EMPHASIS_RE = re.compile(r"[`*_~]")
_TRAILING_INDEX_RE = re.compile(r"(?:\[\d+\])+$")
_PURE_MONEY_OR_NUM_RE = re.compile(
    r"^\s*(?:(?:USD|EUR|GBP)\s*)?[$€£]?\s*[+-]?\d[\d,]*(?:\.\d+)?\s*(?:USD|EUR|GBP|dollars|%)?\s*$",
    re.IGNORECASE,
)
_UNICODE_DASH_TRANS = str.maketrans({
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2015": "-",
    "\u2212": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\uff05": "%",
    "\uff0b": "+",
})
_CAMEL_BOUNDARY_1_RE = re.compile(r"([a-z0-9])([A-Z])")
_CAMEL_BOUNDARY_2_RE = re.compile(r"([A-Z]+)([A-Z][a-z])")
_NON_SNAKE_RE = re.compile(r"[^a-z0-9]+")

# ---------------------------------------------------------------------------
# Strict numeric & timestamp field registries (reject bool & overflow values)
# ---------------------------------------------------------------------------

STRICT_NUMERIC_KEYS = frozenset({
    "width",
    "height",
    "checked_artifact_count",
    "paid_paywall_count",
    "affiliate_count",
    "raw_vendor_leak_count",
    "count",
    "item_count",
    "entry_count",
    "sequence",
    "order",
    "decimals",
    "precision",
    "probability_pct",
    "change_pct",
    "return_pct",
    "price",
    "close",
    "open",
    "high",
    "low",
    "value",
    "reading",
    "price_usd",
    "subscription_price",
    "monthly_price",
    "annual_price",
    "pledge_amount",
    "max_age_seconds",
    "age_seconds",
    "interval_minutes",
    "platform_limit",
    "word_count",
    "char_count",
    "bytes",
    "size_bytes",
    "epoch",
    "timestamp_epoch",
    "unix_timestamp",
    "reader_revision",
    "version",
})

UTC_TIMESTAMP_KEYS = frozenset({
    "as_of_utc",
    "observed_at_utc",
    "generated_at_utc",
    "published_at_utc",
    "captured_at_utc",
    "created_at_utc",
    "updated_at_utc",
    "dispatched_at_utc",
    "retrieved_at_utc",
    "known_at_utc",
    "event_time_utc",
    "cutoff_utc",
    "written_at_utc",
    "paused_at_utc",
    "resume_at_utc",
    "started_at_utc",
    "ended_at_utc",
    "frozen_at_utc",
    "data_cutoff_utc",
    "last_completed_bar_utc",
})

# ---------------------------------------------------------------------------
# Rule A3: Private-Alpha Key Registries (normalized snake_case)
# ---------------------------------------------------------------------------

KELLY_SIZING_LOT_KEYS = frozenset({
    "kelly",
    "kelly_f",
    "kelly_fraction",
    "kelly_weight",
    "kelly_weights",
    "kelly_sizing",
    "kelly_cagr_pct",
    "half_kelly",
    "quarter_kelly",
    "full_kelly",
    "is_kelly_f",
    "dd30_kelly",
    "dd30_kelly_optimal_f",
    "dd30_kelly_optimal_arm",
    "dd30_kelly_cagr_pct",
    "dd30_kelly_cagr_1x_pct",
    "dd30_kelly_cagr_2x_pct",
    "dd30_kelly_max_dd_pct",
    "dd30_kelly_quantized_desk_size",
    "dd30_kelly_weights_is_frozen",
    "dd30_kelly_p_dd_ge_30pct",
    "is_fitted_dd30_kelly_base_f",
    "crn_dd30_kelly",
    "f_star",
    "f_opt",
    "optimal_f",
    "kelly_g_f",
    "lot_size",
    "lots",
    "volume_lots",
    "min_lots",
    "position_size",
    "position_sizing",
    "sizing",
    "sizing_formula",
    "desk_size",
    "risk_allocation",
    "risk_per_trade",
    "risk_budget",
    "half_plan_risk",
    "discrete_lot_increment_cfd",
    "pure_lot_quantization_cagr_drag_pp",
    "pure_lot_quantization_g_drag_bps_yr",
    "exness_cfd_all_in_min_001_lot_risk_usd",
    "ibkr_micro_future_all_in_1ct_risk_usd",
    "max_contracts",
    "contract_qty",
    "order_qty",
    "notional_size",
    "leverage_ratio",
})

EXECUTION_LEVEL_FILL_KEYS = frozenset({
    "stop_loss",
    "stoploss",
    "sl",
    "sl_price",
    "sl_level",
    "stop_level",
    "stop_price",
    "broker_stop",
    "broker_stop_price",
    "trailing_stop",
    "take_profit",
    "takeprofit",
    "tp",
    "tp1",
    "tp2",
    "tp3",
    "tp_price",
    "tp_level",
    "target_level",
    "target_price",
    "profit_target",
    "entry_fill",
    "entry_fill_price",
    "entry_fill_level",
    "fill_price",
    "filled_price",
    "avg_fill_price",
    "average_fill_price",
    "execution_price",
    "fill_at_utc",
    "filled_at_utc",
    "entry_price",
    "entry_level",
    "limit_price",
    "order_price",
    "order_ticket",
    "ticket",
    "ticket_id",
    "order_id",
    "order_ref",
    "broker_order_id",
    "position_ticket",
    "position_tickets",
    "client_orders",
    "raw_positions",
    "open_positions_internal",
    "desk_positions_raw",
    "ibkr_positions",
    "exness_positions",
    "fills",
    "fill_records",
    "slippage_bps",
    "commission_usd_per_lot_roundtrip",
})

ACCOUNT_EQUITY_PNL_KEYS = frozenset({
    "account_balance",
    "cash_balance",
    "account_equity",
    "equity_usd",
    "equity_tiers",
    "solvency_equity_floor",
    "shared_solvency_equity_floor",
    "starting_capital",
    "capital_ladder_usd",
    "capital_ladder_regimes",
    "account_nav",
    "nav",
    "nav_usd",
    "net_liquidation",
    "account_value",
    "free_margin",
    "margin_used",
    "margin_level",
    "pnl",
    "pnl_usd",
    "realized_pnl",
    "realised_pnl",
    "unrealized_pnl",
    "unrealised_pnl",
    "floating_pnl",
    "daily_pnl",
    "weekly_pnl",
    "monthly_pnl",
    "net_pnl",
    "net_profit",
    "net_profit_pct",
    "realized_profit",
    "realised_profit",
    "drawdown_usd",
    "max_dd_usd",
    "r_multiple",
    "r_multiples",
    "expected_r",
    "expectancy",
    "best_r",
    "worst_r",
    "total_r",
    "avg_r",
    "ev_r",
    "weighted_ev_r_1x",
    "oos_ev_r",
    "l4_oos_ev_r",
    "fx_sleeve_oos_ev_r",
    "ustec_sleeve_oos_ev_r",
})

BROKER_IDENTIFIER_KEYS = frozenset({
    "account",
    "account_id",
    "account_number",
    "broker_account",
    "broker_login",
    "broker_server",
    "ibkr_account",
    "exness_account",
    "ibkr_book",
    "exness_book",
    "internal_book",
    "desk_book_internal",
    "ibkr_paper_account",
    "mt4",
    "mt5",
    "exness",
    "metatrader",
    "demo_account",
    "gateway_port",
    "api_key",
    "access_token",
    "secret",
    "password",
    "private_key",
})

PRIVATE_STUDY_TAG_KEYS = frozenset({
    "private_only",
    "public_export_forbidden",
    "private_text",
    "private_texts",
    "x_list",
    "jim_x_list",
    "cc983_uniform_small_account_grid_swap_free",
    "ingested_study_manifests",
    "part_a_five_regime_stress_decomposition",
    "part_b_rule_a4_cost_sensitivity_surface",
    "part_c_blinded_cohort_manifest_audit",
    "anti_safe_choice_standard",
})

L4_SLEEVE_WEIGHT_KEYS = frozenset({
    "l4",
    "l4_oos",
    "l4_weight",
    "l4_weights",
    "l4_trade_count",
    "l4_oos_cagr_pct",
    "l4_dd_prob_within_cap",
    "is_l4_count",
    "oos_l4_count",
    "total_all_l4_trades",
    "total_is_l4_trades",
    "total_oos_l4_trades",
    "overlay_deltas_vs_l4",
    "deltas_vs_b18_l4_floor",
    "stack_2a_minus_l4",
    "stack_5_minus_l4",
    "sleeve_weight",
    "sleeve_weights",
    "portfolio_weights",
    "portfolio_weights_used",
    "target_weight_pct",
    "gross_risk_weight_sum",
    "core_7_is_frozen_weights_quantized",
    "joint_8_is_frozen_weights_quantized",
    "active_weight_markets",
    "challenger_weight",
    "incumbent_weight",
    "floor_weight",
    "augmented_total_weight",
    "oos_1x_emp_total_weight",
    "oos_1x_rho100_total_weight",
    "market_sleeve_summary",
    "market_sleeve_summary_1x_0r",
    "orthogonal_slots",
    "max_orthogonal_slots",
    "orthogonal_slots_max",
    "slot_replacement_churn_mean_bps",
    "ibkr_cc362_options_live_allocation_pct",
    "ibkr_cc362_options_live_capital_allocation_pct",
})

CC024_PAYWALL_KEYS = frozenset({
    "paywall",
    "paywall_config",
    "paywall_settings",
    "paywall_mode",
    "is_paid",
    "paid_only",
    "paid_tier",
    "paid_plan",
    "paid_membership",
    "subscribers_only",
    "paid_subscribers_only",
    "vip_only",
    "members_only",
    "enable_paywall",
    "enable_pledges",
    "pledge_enabled",
    "paywall_cta",
    "upsell_cta",
    "checkout_url",
    "checkout_link",
    "payment_link",
    "stripe_price_id",
    "patreon_url",
    "subscription_price",
    "subscription_plan",
    "monthly_price",
    "annual_price",
    "price_usd",
    "pledge_amount",
})

CC024_AFFILIATE_KEYS = frozenset({
    "affiliate",
    "affiliate_url",
    "affiliate_link",
    "affiliate_code",
    "affiliate_id",
    "referral",
    "referral_url",
    "referral_link",
    "referral_code",
    "partner_url",
    "partner_link",
    "partner_code",
    "partner_ref",
    "broker_referral",
    "ib_link",
    "ib_url",
    "ib_code",
    "promo_code",
    "sponsor",
    "sponsored",
    "sponsored_by",
    "sponsor_url",
})

CC024_FORBIDDEN_TIER_VALUES = frozenset({
    "paid",
    "paid_only",
    "paid_tier",
    "paid_plan",
    "paid_subscription",
    "paid_member",
    "paid_members",
    "paid_subscribers",
    "paid_only_subscribers",
    "only_paid",
    "only_founding",
    "subscriber_only",
    "vip",
    "vip_only",
    "pro",
    "pro_only",
    "premium",
    "premium_only",
    "founding",
    "founding_only",
    "founding_member",
    "founding_members",
    "founding_members_only",
    "members",
    "member_only",
    "members_only",
    "subscribers_only",
    "paid_subscribers_only",
    "paywalled",
    "paywall",
    "subscriber_paid",
    "private",
    "private_only",
    "restricted",
    "tier_paid",
    "gold_tier",
    "silver_tier",
    "platinum_tier",
})

TIER_SELECTOR_KEYS = frozenset({
    "mode",
    "tier",
    "access_tier",
    "access_mode",
    "audience_tier",
    "audience",
    "substack_audience",
    "post_audience",
    "email_audience",
    "web_audience",
    "delivery_audience",
    "monetization_mode",
    "billing_tier",
    "subscription_tier",
    "release_mode",
    "publication_tier",
    "visibility_tier",
})

ALLOWED_FREE_TIER_VALUES = frozenset({
    "free",
    "free_only",
    "public",
    "public_free",
    "everyone",
    "all_readers",
    "all_subscribers",
    "free_subscribers",
    "open",
    "open_access",
})

_CC107_CARD_TIER_KEYS = frozenset({
    "rights_class",
    "source_ids",
    "use_label",
    "value",
    "visibility",
})
_CC107_CARD_TIER_VALUE_RE = re.compile(r"^(?:t[1-4]|anchor)$", re.IGNORECASE)

RIGHTS_KEYS = frozenset({
    "rights_class",
    "source_rights_class",
    "public_use_rights",
    "license_status",
    "licence_status",
    "reuse_rights",
    "distribution_rights",
    "visibility",
})

DENIED_RIGHTS_VALUES = frozenset({
    "not_granted",
    "unknown",
    "unclassified",
    "license_required",
    "licence_required",
    "conditional",
    "internal_only",
    "internal_research",
    "internal_research_only",
    "private",
    "private_only",
    "paid_only",
    "restricted",
    "restricted_redistribution",
    "denied",
    "none",
    "forbidden",
    "unverified",
    "personal_non_commercial",
    "non_commercial",
    "commercial_only",
    "no_redistribution",
    "fred_copyrighted",
    "copyrighted",
    "third_party_copyrighted",
    "copyrighted_third_party",
    "yahoo_finance",
    "substack_paid",
    "subscribers_only",
    "paid_members",
})

RAW_VENDOR_KEYS = frozenset({
    "raw_vendor_feed",
    "raw_vendor_payload",
    "raw_vendor_data",
    "licensed_feed_raw",
    "vendor_dump",
    "bloomberg_raw",
    "refinitiv_raw",
    "financialjuice_raw",
    "cme_fedwatch_raw",
    "kalshi_raw",
    "polymarket_raw",
    "optionstrat_raw",
    "unusual_whales_raw",
    "barchart_raw",
    "yahoo_finance_raw",
    "yfinance_raw",
    "fred_copyrighted_raw",
    "occ_gex_raw",
    "myfxbook_raw",
    "investing_com_raw",
    "cnbc_quote_raw",
})

# ---------------------------------------------------------------------------
# Verified live public-webapp-preview forbidden leak tables
# (parity with verify_d184_zero_leak_and_sunset_v1.py,
#  publication_schema_compat_v1.py, check-public-webapp.mjs,
#  preview_link_guard_v1.py, public_time_v1.py, public_decision_checks_v1.py)
# ---------------------------------------------------------------------------

PUBLIC_WEBAPP_FORBIDDEN_TOKENS: tuple[str, ...] = (
    "internal-economic-calendar",
    "internal-gamma-options",
    "internal-price-bars",
    "internal-financialjuice-wire",
    "alpha-stress-phase",
    "alpha-stress-summary",
    "attention-map-summary",
    "contentops-newsroom-summary",
    "market-forces-attribution",
    "window.__cc_",
    "__cc_economic_calendar__",
    "__cc_gamma_options__",
    "__cc_price_bars__",
    "__cc_financialjuice_wire__",
    "__cc_alpha_stress__",
    "__cc_attention_map__",
    "__cc_contentops_newsroom__",
    "__cc_market_forces__",
    "private_only",
    "public_export_forbidden",
    "_private_texts",
    "private-desk",
    "/__owner",
    "ibkr-book",
    "exness-book",
    ".private.json",
)

PUBLIC_WEBAPP_BOOK_DUMP_MARKERS: tuple[str, ...] = (
    "ibkr_book",
    "exness_book",
    "internal_book",
    "desk_book_internal",
    "raw_positions",
    "open_positions_internal",
    "desk_positions_raw",
    "client_orders",
    "account_nav",
    "account_equity",
    "free_margin",
    "margin_used",
    "margin_level",
    "account_number",
    "ibkr_positions",
    "exness_positions",
    "ibkr_account",
    "exness_account",
    "position_tickets",
)

_WINDOW_CC_GLOBAL_RE = re.compile(r"(?:window|globalThis)\.__cc_[a-z0-9_]+__", re.IGNORECASE)

# Decision 83 preview-host links (parity with live_contentops/preview_link_guard_v1.py)
_PREVIEW_HOST_RE = re.compile(
    r"github\.io|pages\.dev|workers\.dev|netlify\.app|vercel\.app|fatcat2109|capital-chronicle-preview",
    re.IGNORECASE,
)

# Unsafe / private URL schemes (parity with check-public-webapp.mjs safeHttps + R2-L1)
_UNSAFE_URL_RE = re.compile(
    r"(?:^|[\s\"'(<=\[,])(?:javascript:|vbscript:|data:(?:text/html|application/|image/svg)|"
    r"file:///|ftp://|ftps://|sftp://|ws://|wss://|blob:|https?://[^\s/@]+:[^\s/@]+@)",
    re.IGNORECASE,
)
_ATTR_SCHEME_RE = re.compile(
    r"\b(?:href|src)\s*=\s*[\"']?([a-z][a-z0-9+.-]*):",
    re.IGNORECASE,
)

# Decision 90 ET-only public times (parity with live_contentops/public_time_v1.py)
_FORBIDDEN_PUBLIC_TIME_RE = re.compile(
    r"\b(?:GMT|UTC)\s*\+\s*0?7(?::?00)?(?!\d)|Asia/Bangkok|"
    r"\bBangkok\s+(?:time|times)|\bVietnam(?:ese)?\s+time|"
    r"\b\d{1,2}:\d{2}\s+Bangkok\b",
    re.IGNORECASE,
)

# Decision 107 raw CFD / broker symbol names forbidden in public prose (parity with public_instruments_v1.py)
_DECISION_107_RAW_CFD_SYMBOL_RE = re.compile(
    r"\b(?:CFDs?|US500m?|USOILm?|XAUUSDm?|BTCUSDm?|USTECm?|EURUSDm|USDJPYm|GBPUSDm|XAGUSDm|"
    r"NAS100m?|SPX500m?|US30m|GER40m?|UK100m?|WTICOUSD)\b",
    re.IGNORECASE,
)

# Decision 109 / CC-432 / CC-801 / CC-855 public AI-model & authorship leak scrubber
_AI_MODEL_LEAK_RE = re.compile(
    r"\b(?:AI|artificial intelligence)[ -]+(?:generated|written|powered|assisted|"
    r"produced|run|agent|disclosure|label|desk|analysts?)\b|"
    r"\b(?:generated|written|made|operated|run)\s+(?:with|by)\s+(?:an?\s+)?(?:AI|LLM)\b|"
    r"\b(?:ChatGPT|GPT[- ]?\d[\w.-]*|gpt-[\w.-]+|Gemini(?:[ -][\w.-]+)?|"
    r"Claude(?:[ -](?:Opus|Sonnet|Haiku|Code|Desktop)[\w .-]*)?|"
    r"Sonnet|Haiku|Fable|Luna|agy|"
    r"Anthropic|OpenAI|DeepSeek[-\w]*|Grok[- ]?\d[\w.-]*|"
    r"Antigravity|Codex|Sol\s*6(?:\.\d+)?|Astra\s*\d)\b",
    re.IGNORECASE,
)

# CC-791 / PublicOddsLeakCheckV1 regexes (exact parity with Main publication_schema_compat_v1.py)
_CLAUSE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Za-z0-9(\[])|;\s*|\n+")
_ODDS_CUE_RE = re.compile(
    r"\b(?:Kalshi|Polymarket|PredictIt|Metaculus|Fed[ -]?Watch|prediction[ -]?markets?|event[ -]?odds|"
    r"market[ -]?implied|futures[- ]derived|rate\s+futures|fed\s+funds\s+futures|"
    r"SOFR\s+futures|OIS\s+pricing|odds|implied\s+probabilit(?:y|ies)|market\s+probabilit(?:y|ies))\b",
    re.IGNORECASE,
)
_ODDS_PCT_OR_CENTS_RE = re.compile(
    r"(?<!\w)\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b|percentage\s+points?\b|p\.?p\.?\b|\u00a2|cents?\b)",
    re.IGNORECASE,
)
_PRICED_AT_PCT_RE = re.compile(
    r"\b(?:priced(?:\s+in)?|pricing|implies?|implied)\s+(?:at|near|around|above|below|over|under)?\s*"
    r"\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)"
    r"|(?<!\w)\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)\s*(?:priced(?:\s+in)?|odds|chance|probability)\b"
    r"|(?<!\w)\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)\s+implied\b"
    r"(?!\s+(?:day|daily|move|vol|volatility|range|swing|yield|rate|inflation)\b)",
    re.IGNORECASE,
)
_POLICY_MOVE_PCT_RE = re.compile(
    r"\b(?:Federal\s+Reserve|Fed|FOMC|ECB|BoJ|BoE)\b[^.!?;]{0,90}\bfutures\b[^.!?;]{0,60}"
    r"\b(?:hike|cut|hold|rise|pause|easing|tightening|quarter-point)\b[^.!?;]{0,40}"
    r"(?<!\bto\s)(?<!\w)\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)"
    r"(?!\s*(?:yield|inflation|cpi|pce|gdp)\b)"
    r"|\b(?:Federal\s+Reserve|Fed|FOMC|ECB|BoJ|BoE)\s+(?:rate\s+)?(?:hike|cut|hold|pause)\s+"
    r"(?:(?:at|near|around|of|priced(?:\s+at)?)\s+|[:=]\s*)"
    r"\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)"
    r"|(?<!\w)\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)\s+"
    r"(?:(?:for|of|on)\s+)?(?:(?:a|an|the)\s+)?"
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?"
    r"(?:Federal\s+Reserve|Fed|FOMC|ECB|BoJ|BoE)\s+(?:rate\s+)?(?:hike|cut|hold|pause)\b",
    re.IGNORECASE,
)
_NUMERIC_GAP_PP_RE = re.compile(r"\bgap_pp\s*[:=]?\s*[+-]?\d+(?:\.\d+)?\b", re.IGNORECASE)

# Non-prose metadata keys exempt from clause-based odds prose scanning
_NON_PROSE_ODDS_KEYS = frozenset({
    "plan_id",
    "content_hash",
    "status_content_hash",
    "generated_at_utc",
    "at_utc",
    "expires_at_utc",
    "registered_at_utc",
    "registration_hash",
    "url",
    "canonical_url",
    "source_page_url",
    "chart_url",
    "schema",
    "schema_version",
    "contract_version",
    "asset_id",
    "status",
    "direction",
    "lane",
    "layer",
    "first_cause",
    "reason_code",
    "geometry_label",
    "entry_name",
    "data_state",
    "symbol",
    "tv_symbol",
    "kind",
    "exchange",
    "contract_month",
    "outcome_id",
    "score_hash",
    "sha256",
    "observations_sha256",
    "feed_sha256",
    "media_asset_id",
    "work_item_id",
    "dispatch_id",
    "readback_id",
    "digest_id",
    "card_id",
    "post_id",
})

# Technical/metadata keys exempt from Decision 107 raw-CFD prose checks
# (parity with live_contentops/public_instruments_v1.py:62-74)
_NON_PROSE_INSTRUMENT_KEYS = _NON_PROSE_ODDS_KEYS | frozenset({
    "market_asset",
    "market",
    "path",
    "file_path",
    "filename",
    "media_path",
    "image_path",
    "public_url",
    "public_analysis_url",
    "caption_id",
    "_key_name",
    "instrument_id",
    "series_id",
    "rights_basis",
    "modality",
    "provenance_status",
    "policy",
})

# ---------------------------------------------------------------------------
# Rule A3 Tokenized Key-Family Registries (snake_case & camelCase prefix/suffix)
# ---------------------------------------------------------------------------

_KELLY_KEY_PHRASES: tuple[tuple[str, ...], ...] = (
    ("kelly",),
    ("f", "star"),
    ("optimal", "f"),
    ("lot", "size"),
    ("lot", "sizes"),
    ("volume", "lots"),
    ("min", "lots"),
    ("position", "size"),
    ("position", "sizing"),
    ("sizing", "formula"),
    ("desk", "size"),
    ("risk", "per", "trade"),
    ("risk", "allocation"),
    ("risk", "budget"),
    ("half", "plan", "risk"),
    ("leverage", "ratio"),
    ("contract", "qty"),
    ("order", "qty"),
    ("notional", "size"),
)

_EXECUTION_KEY_PHRASES: tuple[tuple[str, ...], ...] = (
    ("stop", "loss"),
    ("stoploss",),
    ("stop", "level"),
    ("stop", "price"),
    ("broker", "stop"),
    ("trailing", "stop"),
    ("sl", "price"),
    ("sl", "level"),
    ("take", "profit"),
    ("takeprofit",),
    ("tp", "price"),
    ("tp", "level"),
    ("tp1",),
    ("tp2",),
    ("tp3",),
    ("profit", "target"),
    ("target", "level"),
    ("target", "price"),
    ("entry", "fill"),
    ("fill", "price"),
    ("filled", "price"),
    ("execution", "price"),
    ("entry", "price"),
    ("entry", "level"),
    ("limit", "price"),
    ("order", "price"),
    ("order", "ticket"),
    ("position", "ticket"),
    ("position", "tickets"),
    ("broker", "order"),
    ("slippage", "bps"),
    ("raw", "positions"),
    ("client", "orders"),
)

_ACCOUNT_PNL_KEY_PHRASES: tuple[tuple[str, ...], ...] = (
    ("pnl",),
    ("realized", "pnl"),
    ("realised", "pnl"),
    ("unrealized", "pnl"),
    ("unrealised", "pnl"),
    ("floating", "pnl"),
    ("account", "balance"),
    ("account", "equity"),
    ("account", "nav"),
    ("account", "value"),
    ("cash", "balance"),
    ("net", "liquidation"),
    ("free", "margin"),
    ("margin", "used"),
    ("margin", "level"),
    ("equity", "usd"),
    ("drawdown", "usd"),
    ("max", "dd", "usd"),
    ("r", "multiple"),
    ("r", "multiples"),
    ("expected", "r"),
    ("ev", "r"),
    ("expectancy",),
    ("starting", "capital"),
    ("capital", "ladder"),
    ("solvency", "equity"),
)

_BROKER_KEY_PHRASES: tuple[tuple[str, ...], ...] = (
    ("ibkr",),
    ("exness",),
    ("metatrader",),
    ("mt4",),
    ("mt5",),
    ("broker", "login"),
    ("broker", "account"),
    ("broker", "server"),
    ("demo", "account"),
    ("api", "key"),
    ("access", "token"),
    ("private", "key"),
    ("secret", "key"),
)

_PRIVATE_STUDY_KEY_PHRASES: tuple[tuple[str, ...], ...] = (
    ("private", "only"),
    ("public", "export", "forbidden"),
    ("private", "text"),
    ("private", "texts"),
    ("x", "list"),
    ("study", "6"),
    ("study", "7"),
    ("study", "8"),
    ("study", "9"),
    ("study", "10"),
    ("study", "11"),
)
_STUDY_TOKEN_RE = re.compile(r"^study(?:[6-9]|1[01])$")

_L4_SLEEVE_KEY_PHRASES: tuple[tuple[str, ...], ...] = (
    ("l4",),
    ("sleeve", "weight"),
    ("sleeve", "weights"),
    ("portfolio", "weight"),
    ("portfolio", "weights"),
    ("gross", "risk", "weight"),
    ("orthogonal", "slots"),
    ("fx", "sleeve"),
    ("ustec", "sleeve"),
    ("gold", "sleeve"),
    ("oil", "sleeve"),
    ("crypto", "sleeve"),
    ("equity", "sleeve"),
    ("market", "sleeve"),
    ("keep", "amplify"),
)

_CC791_ODDS_KEY_PHRASES: tuple[tuple[str, ...], ...] = (
    ("kalshi",),
    ("polymarket",),
    ("predictit",),
    ("metaculus",),
    ("fedwatch",),
    ("fed", "watch"),
    ("gap", "pp"),
    ("prediction", "market"),
    ("prediction", "markets"),
    ("event", "odds"),
    ("market", "odds"),
    ("implied", "odds"),
    ("implied", "probability"),
    ("market", "probability"),
    ("cut", "probability"),
    ("hike", "probability"),
    ("hold", "probability"),
    ("rate", "odds"),
    ("odds", "pct"),
)

_KEY_NUMERIC_LEVEL_RE = re.compile(
    r"(?:[$€£]\s*\d|[:=@]\s*[+-]?\d|\d+\.\d+|\s+[+-]?\d[\d,]*(?:\.\d+)?%?)"
)
_CHART_EXECUTION_OVERLAY_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:stop(?:[-\s]?loss)?|sl|target|tp\d*|take[-\s]?profit|fill|entry(?:[-\s]?fill)?)(?![A-Za-z0-9])",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Rule A3 Text Leak Regex Patterns
# ---------------------------------------------------------------------------

_PRICE_NUM = r"(?:USD\s*)?[$€£]?\s*[+-]?\d+(?:,\d{3})*(?:\.\d+)?"
_STANDALONE_PRICE_NUM = r"(?:(?:USD\s*)?[$€£]\s*\d+(?:,\d{3})*(?:\.\d+)?|\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d{3,})"

_KELLY_SIZING_LOT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "KELLY_F_STAR_OR_FORMULA",
        re.compile(
            r"(?:(?<!\w)f\s*\*(?:\s*[:=]\s*[0-9.]+%?)?(?!\w))"
            r"|\bf_star\b"
            r"|\bg\s*\(\s*f\s*\)"
            r"|\b(?:half|quarter|full|fractional|dd30|optimal)[-\s]+kelly\b"
            r"|\b\d+(?:\.\d+)?\s*[x×]\s*kelly\b"
            r"|\bkelly[-\s]+(?:criterion|fraction|sizing|size|weight|weights|optimal|cagr|bet|formula|leverage|f\*|arm|growth|multiplier|cap)\b"
            r"|\bkelly\s*[:=@]\s*[+-]?\d+(?:\.\d+)?%?"
            r"|\bdd30_kelly\w*",
            re.IGNORECASE,
        ),
    ),
    (
        "LOT_OR_POSITION_SIZING_FORMULA",
        re.compile(
            r"\b(?:lot\s+sizes?|position\s+siz(?:e|ing)|risk\s+per\s+trade|"
            r"risk\s+allocation|risk\s+budget|HALF_PLAN_RISK|"
            r"lot\s+quantization|discrete_lot_increment)\b"
            r"|(?<![\w.])(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|half\s+a|a\s+single)[-\s]*"
            r"(?:standard[-\s]+|mini[-\s]+|micro[-\s]+)?lots?\b"
            r"|\bpercent\s+of\s+(?:your|our|account)\s+(?:equity|capital|balance)\b"
            r"|\bsize\s*[:=@]\s*(?:\d+(?:\.\d+)?\s*(?:lots?|contracts?|units?|%)|[$€£]\s*\d)",
            re.IGNORECASE,
        ),
    ),
)

_POLICY_TARGET_PREFIX_RE = re.compile(
    r"\b(?:inflation|employment|unemployment|deficit|(?:fed|federal)\s+funds|policy\s+rate|"
    r"interest\s+rate|yield|reserve|(?:fed|ecb|boj|boe|central\s+bank)'s)(?:\s+rate)?\s+$",
    re.IGNORECASE,
)

_STOP_LOSS_RE = re.compile(
    r"\b(?:stop[-\s]?loss(?:es)?|broker[-\s]?stop|trailing[-\s]?stop)\b"
    r"|\bSL\s*(?:[:=@]\s*|\s+)" + _PRICE_NUM
    + r"|\bstop\s+(?:(?:at|below|above|near|around|level\s*[:=@]?)\s+|[:=@]\s*)" + _PRICE_NUM
    + r"|\bstop\s+" + _STANDALONE_PRICE_NUM
    + r"(?![\d.,%]|\s*[- ](?:year|month|day|week|hour|minute|bps?|percent|pct)\b)",
    re.IGNORECASE,
)

_TAKE_PROFIT_RE = re.compile(
    r"\b(?:take[-\s]?profits?|profit[-\s]?targets?|price[-\s]?targets?|model[-\s]?targets?|target[-\s]?level|target[-\s]?zone)\b"
    r"|\b(?:our|the\s+plan(?:'s)?|exit)\s+(?:price\s+)?target\b"
    r"|\bTP\d*\s*(?:[:=@]\s*|\s+)" + _PRICE_NUM
    + r"|\bTP[1-9]\b"
    r"|\btarget\s*(?:[:=@]\s*|\s+(?:(?:is|of|at|near|around|above|below)\s+)*)" + _PRICE_NUM
    + r"(?![\d.,%]|\s*(?:percent\b|pct\b|bps?\b|basis\s+points?\b|to\s+\d+(?:\.\d+)?\s*(?:%|percent\b)))"
    + r"|" + _PRICE_NUM + r"\s+(?:(?:profit|price|model)[-\s]+)?(?:target|take[-\s]+profit)\b",
    re.IGNORECASE,
)

_ENTRY_FILL_RE = re.compile(
    r"\b(?:entry\s+fill(?:\s+level|\s+price)?|fill(?:ed)?\s+(?:price|level)\s*[:=@]?\s*" + _PRICE_NUM
    + r"|avg(?:erage)?\s+fill\s*[:=@]?\s*" + _PRICE_NUM
    + r"|execution\s+(?:price|fill)\s*[:=@]?\s*" + _PRICE_NUM
    + r"|filled\s+at\s+" + _PRICE_NUM
    + r"|entered\s+(?:(?:long|short|buy|sell)\s+)?(?:at|near|around)\s+" + _PRICE_NUM
    + r"|entry\s+(?:price|level)\s*[:=@]?\s*" + _PRICE_NUM
    + r"|entry\s+(?:(?:at|near|around)\s+)?" + _PRICE_NUM
    + r"(?![\d.,%]|\s*(?:percent\b|pct\b|bps?\b|year|month|day|week|hour|minute))"
    + r"|limit\s+order\s+(?:filled|at)\s+" + _PRICE_NUM
    + r"|(?:buy|sell|long|short|entry)\s*[:=@]\s*" + _PRICE_NUM + r")\b",
    re.IGNORECASE,
)

_MACRO_BALANCE_EXEMPT_RE = re.compile(
    r"(?:\b(?:trade|fiscal|budget|current\s+account|capital\s+account|external|"
    r"payment|payments|supply[- ]demand|reserve|bank|dealer|fed|ecb|boj|central\s+bank)\s+$)",
    re.IGNORECASE,
)
_BALANCE_SHEET_SUFFIX_RE = re.compile(r"^\s*[- ]?sheets?\b", re.IGNORECASE)
_MACRO_EQUITY_PREFIX_RE = re.compile(
    r"\b(?:us|u\.s\.|global|european|asian|japanese|chinese|emerging[- ]market|em|"
    r"developed[- ]market|dm|public|private|foreign|domestic|broad|regional|tech|bank|financial)\s+$",
    re.IGNORECASE,
)
_MACRO_EQUITY_SUFFIX_RE = re.compile(
    r"^\s+(?:inflows?|outflows?|flows?|funds?|etfs?|markets?|index(?:es)?|indices|futures|"
    r"issuance|offerings?|valuations?|risk\s+premi(?:a|um)|strateg(?:y|ies)|rally|sell-?off|gains?|losses?|exposure)\b",
    re.IGNORECASE,
)
_PRIVATE_OWNER_PREFIX_RE = re.compile(
    r"\b(?:our|my|account|desk|client|broker|trading|solvency|starting)\s+$",
    re.IGNORECASE,
)
_MACRO_CAPITAL_PREFIX_RE = re.compile(
    r"\b(?:working|human|fixed|venture|private|foreign|domestic|cross[- ]border|global|"
    r"bank|regulatory|tier[- ]?1|equity|debt|market|cost\s+of)\s+$",
    re.IGNORECASE,
)
_MACRO_CAPITAL_SUFFIX_RE = re.compile(
    r"^\s+(?:inflows?|outflows?|flows?|markets?|spending|expenditures?|investment|"
    r"formation|flight|controls?|requirements?|ratios?|buffers?|gains?)\b",
    re.IGNORECASE,
)

_ACCOUNT_EQUITY_PNL_EXPLICIT_RE = re.compile(
    r"(?<!\bcurrent\s)(?<!\bcapital\s)\baccount\s+(?:balance|equity|nav|value|pnl|capital)\b"
    r"|\b(?:net\s+liquidation|free\s+margin|margin\s+(?:used|level)|"
    r"(?:our|my)\s+(?:balance|equity|capital|nav|pnl|account|drawdown|portfolio)|"
    r"realis?ed\s+(?:profit|loss|pnl)|unrealis?ed\s+(?:profit|loss|pnl)|"
    r"floating\s+(?:profit|loss|pnl)|p\s*&\s*l|"
    r"(?:(?:daily|weekly|monthly|quarterly|annual|ytd|total|net|gross|open|closed|book|desk|account|trading|strategy|model)\s+)?pnl\b|"
    r"solvency\s+equity\s+floor|capital\s+ladder\s+usd|"
    r"expected[ _-]?r|expectancy|reward[ -]to[ -]risk|r[ -]?multiples?)\b",
    re.IGNORECASE,
)

_BALANCE_MONEY_RE = re.compile(
    r"\b(balance|equity|capital|pnl|profit|loss|nav|drawdown)\b"
    r"(?![ -]?sheets?\b).{0,28}(?:[$€£]\s*\d|\d[\d,.]*\s*(?:USD|EUR|GBP|dollars)\b)",
    re.IGNORECASE,
)

_BROKER_IDENTIFIER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "IBKR_ACCOUNT_ID",
        re.compile(
            r"(?<![A-Za-z0-9])DUR[-_\s]?343723(?![A-Za-z0-9])"
            r"|(?<![A-Za-z0-9])(?:DU|DUR|DF)[-_\s]?\d{5,9}(?![A-Za-z0-9])"
            r"|(?<![A-Za-z0-9])U[-_]?\d{6,9}(?![A-Za-z0-9])"
            r"|(?<![A-Za-z0-9])IBKR[-_ ]?PAPER(?:[-_ ]?[A-Z0-9]+)?(?![A-Za-z0-9])"
            r"|(?<![A-Za-z0-9])ibkr[-_ ]?DUR[-_\s]?\d+(?![A-Za-z0-9])"
            r"|\b(?:IBKR\s+(?:account|paper\s+account|gateway|book|live\s+allocation|micro\s+future)|"
            r"Interactive\s+Brokers\s+account|TWS\s+port\s*400[12]|IDEALPRO)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "MT5_EXNESS_BROKER_ID",
        re.compile(
            r"(?<![A-Za-z0-9.])(?:279805139|279779602)(?![A-Za-z0-9])"
            r"|(?<![A-Za-z0-9])(?:Exness[A-Za-z0-9-]*|MT5\s*Trial\d*|MetaTrader\s*[45]?|MT[45]|"
            r"primary-demo-state-\d+)(?![A-Za-z0-9])"
            r"|\b(?:demo\s+account|broker\s+(?:login|account|server|ticket)|"
            r"model[\s-]+positions?|model[\s-]+calls?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "CREDENTIAL_OR_SECRET_TOKEN",
        re.compile(
            r"(?<![A-Za-z0-9])sk-[A-Za-z0-9]{16,}(?![A-Za-z0-9])"
            r"|\b(?:api[_ -]?key|access[_ -]?token|secret[_ -]?key|password|bearer\s+token)\s*[:=]\s*\S+",
            re.IGNORECASE,
        ),
    ),
)

_PRIVATE_STUDY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "PRIVATE_STUDY_6_TO_11_TAG",
        re.compile(
            r"(?<![A-Za-z0-9])Study(?:\s*#\s*|[-_\s])(?:[6-9]|1[01])(?![A-Za-z0-9])"
            r"|(?<![A-Za-z0-9])STUDY(?:[6-9]|1[01])_[A-Z0-9_]+"
            r"|(?<![A-Za-z0-9])Study(?:[6-9]|1[01])[A-Za-z0-9_]*PrivateV\d+(?![A-Za-z0-9])"
            r"|(?<![A-Za-z0-9])study(?:[6-9]|1[01])-(?:v\d|capital-ladder|3vehicle|orthogonal|post-cc\d+|regime-stress)(?![A-Za-z0-9])"
            r"|\b(?:private_only|public_export_forbidden)\b"
            r"|\bJIM_X_LIST_PRIVATE_MAIN_RESEARCH_USE\w*\b"
            r"|\b(?:JIM_X_LIST|PRIVATE_X_LIST)\b",
            re.IGNORECASE,
        ),
    ),
)

_L4_SLEEVE_WEIGHT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "L4_OR_SLEEVE_WEIGHT_LEAK",
        re.compile(
            r"\bL4\s+(?:sleeve|weight|weights|floor|stack|alpha|oos|cagr|ev|model|layer|signal|shadow|arena|ablation|allocation|exposure|trades?)\b"
            r"|\b(?:sleeve|portfolio|risk|kelly|l4|target|floor|incumbent|challenger|gross\s+risk)\s+weights?\b"
            r"|\b(?:STACK_[0-9A-Z]+_minus_L4|B18_L4|L4_FLOOR|L4_SLEEVE|KEEP_AMPLIFY)\b"
            r"|\b(?:fx_sleeve|ustec_sleeve|gold_sleeve|oil_sleeve|crypto_sleeve|equity_sleeve)\b"
            r"|\b(?:gross_risk_weight_sum|portfolio_weights_used|core_7_is_frozen_weights|joint_8_is_frozen_weights|"
            r"orthogonal_slots|slot_replacement_churn)\b",
            re.IGNORECASE,
        ),
    ),
)

_FRED_COPYRIGHTED_SERIES_IDS = (
    r"(?:SP500|DJIA|NASDAQCOM|NASDAQ100|VIXCLS|WILL5000[A-Z0-9_]*|BAML[A-Z0-9_]*|ICE[A-Z0-9_]*)"
)
_FRED_COPYRIGHTED_SERIES_EXACT_RE = re.compile(
    r"^(?:FRED\s*[:/]\s*)?" + _FRED_COPYRIGHTED_SERIES_IDS + r"$",
    re.IGNORECASE,
)

_RAW_VENDOR_LEAK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "RAW_VENDOR_REDISTRIBUTION_LEAK",
        re.compile(
            r"\b(?:raw_vendor_feed|raw_vendor_payload|licensed_feed_raw|vendor_dump|"
            r"Bloomberg\s+Terminal\s+(?:dump|feed|export|raw)|Refinitiv\s+raw|"
            r"FinancialJuice\s+(?:raw\s+)?wire|internal-financialjuice-wire|"
            r"OptionStrat\s+raw|Unusual\s+Whales\s+raw|Barchart\s+raw|"
            r"CME\s+Data\s+Terms\s+redistribution|INTERNAL_RESEARCH_ONLY|FRED_COPYRIGHTED)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "YAHOO_FINANCE_COMMERCIAL_RIGHTS",
        re.compile(
            r"(?:[a-z0-9-]+\.)?finance\.yahoo\.com|\byahoo\s+finance\b|\byfinance\b",
            re.IGNORECASE,
        ),
    ),
    (
        "FRED_COPYRIGHTED_SERIES",
        re.compile(
            r"\bFRED\s*[:/]\s*" + _FRED_COPYRIGHTED_SERIES_IDS + r"\b"
            + r"|\bFRED\b[^.!?;]{0,60}\b" + _FRED_COPYRIGHTED_SERIES_IDS + r"\b"
            + r"|(?:fred\.)?stlouisfed\.org/[^\s\"'<>]*?(?<![A-Za-z0-9])" + _FRED_COPYRIGHTED_SERIES_IDS + r"(?![A-Za-z0-9])"
            + r"|fredgraph\.(?:png|csv|svg)\?[^\s\"'<>]*?[?&]id=" + _FRED_COPYRIGHTED_SERIES_IDS + r"(?![A-Za-z0-9])"
            + r"|\b(?:VIXCLS|NASDAQCOM|NASDAQ100|WILL5000[A-Z0-9_]*|BAML[A-Z0-9_]{3,})\b",
            re.IGNORECASE,
        ),
    ),
    (
        "CNBC_QUOTE_COMMERCIAL_FEED",
        re.compile(
            r"\b(?:quote(?:-api)?\.cnbc\.com|cnbc\.com/quotes/)",
            re.IGNORECASE,
        ),
    ),
    (
        "INVESTING_MYFXBOOK_CONSENSUS",
        re.compile(
            r"\binvesting\.com\b|\bmyfxbook(?:\.com)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "OCC_OPTIONS_GEX_COMMERCIAL",
        re.compile(
            r"\btheocc\.com\b|\bocc\s+gex\b"
            r"|\bocc\b[^.!?;]{0,40}\b(?:options?|gamma|gex|oi|open\s+interest|market[- ]data)\b"
            r"|\b(?:options?|gamma|gex)\b[^.!?;]{0,40}\bocc\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TRADINGVIEW_EMBED_WIDGET_FORBIDDEN",
        re.compile(
            r"\bs3\.tradingview\.com\b|\bembed-widget\b|\bwidgetembed\b|\btradingview-widget\b|"
            r"tradingview\.com/(?:widget|embed-widget|external-embedding)\b",
            re.IGNORECASE,
        ),
    ),
)

# ---------------------------------------------------------------------------
# CC-024 / Decision 96 FREE-Only Paywall & Affiliate Regex Patterns
# ---------------------------------------------------------------------------

_CC024_PAYWALL_CTA_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "PAYWALL_OR_SUBSCRIPTION_UPSELL_CTA",
        re.compile(
            r"\b(?:upgrade\s+to\s+(?:a\s+)?(?:paid|pro|vip|premium|founding)\b"
            r"|become\s+a\s+paid\s+(?:subscriber|member)\b"
            r"|unlock\s+(?:full\s+access|this\s+post|vip|pro|premium|signals?|trades?|paid\s+content)\b"
            r"|behind\s+(?:the|our)\s+paywall\b"
            r"|paywall(?:ed)?\s+(?:only|content|tier|access|article|post)\b"
            r"|paid\s+(?:subscriptions?|members(?:hips?)?|subscribers?|readers?|newsletters?|plans?|access|tiers?|content|posts?|editions?|articles?)\b"
            r"|for\s+paid\s+(?:subscribers?|members?)\b"
            r"|subscribe\s+(?:now\s+)?for\s+[$€£]?\d+"
            r"|pledge\s+(?:your\s+)?(?:paid\s+)?support\b"
            r"|(?:monthly|annual)\s+(?:paid\s+)?subscription\b"
            r"|founding\s+member(?:\s+tier|\s+access|\s+plan)?\b"
            r"|start\s+your\s+(?:paid|premium|vip|7-day|14-day|free)\s+trial\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "VIP_OR_PAID_GROUP_CTA",
        re.compile(
            r"\b(?:join\s+(?:our|the)\s+(?:vip|premium|pro|paid|private)\s+"
            r"(?:channel|group|discord|telegram|tier|club|desk|room|alerts?|signals?)\b"
            r"|vip\s+(?:signals?|alerts?|channel|group|access|tier|membership|trade\s+alerts?|desk)\b"
            r"|premium\s+(?:signals?|alerts?|tier|membership|access|subscribers?|discord|telegram)\b"
            r"|pro\s+tier\s+(?:access|upgrade|only|signals?)\b"
            r"|paid\s+(?:signals?|alerts?|discord|telegram|membership)\b"
            r"|signal\s+service\b"
            r"|copy[- ]?trading\s+(?:service|group|channel)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "PAID_CHECKOUT_OR_PRICING_CTA",
        re.compile(
            r"(?:patreon\.com/|buymeacoffee\.com/|ko-fi\.com/|gumroad\.com/|whop\.com/|"
            r"lemonsqueezy\.com|mql5\.com/[^\s\"'<>]*/signals|social-trading\.exness(?:\.[a-z]+)?|"
            r"checkout\.stripe\.com|buy\.stripe\.com|"
            r"substack\.com/subscribe\?[^\s\"']*plan=(?:paid|monthly|annual|founding))"
            r"|\b(?:mql5\s+signals?|exness\s+social\s+trading)\b"
            r"|(?:[$€£]\s*\d+(?:\.\d{2})?\s*/\s*(?:mo|month|yr|year|wk|week)\b)"
            r"|(?:\bUSD\s*\d+(?:\.\d{2})?\s+per\s+(?:month|year|week)\b)",
            re.IGNORECASE,
        ),
    ),
)

_CC024_AFFILIATE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "AFFILIATE_OR_REFERRAL_PROMO",
        re.compile(
            r"\b(?:affiliate\s+(?:link|links|partner|code|program|offer)\b"
            r"|referral\s+(?:link|links|code|bonus|offer)\b"
            r"|use\s+(?:my|our)\s+(?:referral|promo|partner|affiliate)\s+code\b"
            r"|open\s+a\s+(?:broker|trading|exness|ibkr)\s+account\s+(?:using|via|with)\s+(?:our|this|my)\s+link\b"
            r"|sign\s+up\s+(?:via|with|using)\s+(?:our|my)\s+(?:partner|referral|affiliate)\b"
            r"|sponsored\s+(?:post|partner|content|by)\b)",
            re.IGNORECASE,
        ),
    ),
)

_AFFILIATE_QUERY_PARAMS = frozenset({
    "ref",
    "ref_code",
    "ref_id",
    "refer",
    "referrer",
    "aff",
    "aff_id",
    "aff_code",
    "affiliate",
    "affiliate_id",
    "partner",
    "partner_id",
    "partner_code",
    "referral",
    "referral_code",
    "ib",
    "ib_code",
    "via",
    "promo",
    "promo_code",
    "coupon",
    "sponsor",
    "broker_ref",
    "sub_id",
    "c_id",
})
_AFFILIATE_URL_PATH_RE = re.compile(
    r"(?:^|/)(?:ref|referral|referrals|affiliate|affiliates|partner-ref|ib-partner)(?:/|$)",
    re.IGNORECASE,
)

_URL_EXTRACT_RE = re.compile(r"https?://[^\s<>\"'\])]+", re.IGNORECASE)


class FirewallEvidenceError(ValueError):
    """Fail-closed firewall evidence error; never echoes private payload values."""

    def __init__(self, code: str, check: str, cause: str) -> None:
        self.code = code
        self.check = check
        self.cause = cause
        super().__init__(f"{code}: {cause}")


# ---------------------------------------------------------------------------
# Normalization, Canonical Serialization & Fail-Closed Parsing
# ---------------------------------------------------------------------------


def _is_valid_utf8_str(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return False
    return True


def _safe_receipt_str(value: Any, *, fallback: str | None = None) -> str | None:
    return value if _is_valid_utf8_str(value) else fallback


def _normalize_text(text: str) -> str:
    cleaned = html.unescape(text)
    if "&" in cleaned:
        cleaned = html.unescape(cleaned)
    if not cleaned.isascii():
        cleaned = unicodedata.normalize("NFKC", cleaned)
        cleaned = "".join(ch for ch in cleaned if unicodedata.category(ch) != "Cf")
        cleaned = cleaned.translate(_UNICODE_DASH_TRANS)
    return cleaned


def _scan_surfaces(norm: str) -> tuple[str, ...]:
    """Return deduplicated scan surfaces: whitespace-collapsed raw + markdown-stripped."""
    collapsed = _WS_COLLAPSE_RE.sub(" ", norm)
    no_star = _WS_COLLAPSE_RE.sub(" ", _MD_STAR_ONLY_RE.sub("", norm))
    plain_md = _WS_COLLAPSE_RE.sub(" ", _MD_EMPHASIS_RE.sub("", norm))
    out: list[str] = [collapsed]
    if no_star not in out:
        out.append(no_star)
    if plain_md not in out:
        out.append(plain_md)
    return tuple(out)


def _normalize_key(key: str) -> str:
    cleaned = _normalize_text(key)
    cleaned = _CAMEL_BOUNDARY_1_RE.sub(r"\1_\2", cleaned)
    cleaned = _CAMEL_BOUNDARY_2_RE.sub(r"\1_\2", cleaned)
    return _NON_SNAKE_RE.sub("_", cleaned.lower()).strip("_")


def _has_token_phrase(tokens: tuple[str, ...], phrases: Iterable[tuple[str, ...]]) -> str | None:
    n = len(tokens)
    for phrase in phrases:
        m = len(phrase)
        if m == 0 or m > n:
            continue
        if m == 1:
            if phrase[0] in tokens:
                return phrase[0]
        else:
            for idx in range(n - m + 1):
                if tokens[idx:idx + m] == phrase:
                    return "_".join(phrase)
    return None


def _is_paywall_key(key_norm: str) -> bool:
    return (
        key_norm in CC024_PAYWALL_KEYS
        or key_norm.startswith(("paywall_", "paid_"))
        or key_norm.endswith(("_paywall", "_price_usd", "_subscription_price"))
    )


def _is_tier_selector_key(key_norm: str) -> bool:
    return (
        key_norm in TIER_SELECTOR_KEYS
        or key_norm.endswith((
            "_audience",
            "_tier",
            "_paywall_mode",
            "_monetization_mode",
            "_release_mode",
            "_access_tier",
            "_access_mode",
            "_subscription_tier",
            "_billing_tier",
        ))
        or key_norm.startswith(("audience_", "substack_audience", "post_audience"))
    )


def _is_active_metadata_value(value: Any, *, depth: int = 0) -> bool:
    """Return True if a paywall/affiliate metadata value is active/non-zero/non-finite (never overflows)."""
    if depth > MAX_JSON_DEPTH:
        return True
    if value is None:
        return False
    if isinstance(value, bool):
        return value is True
    if isinstance(value, int):
        return value != 0
    if isinstance(value, float):
        return (not math.isfinite(value)) or value != 0.0
    if isinstance(value, str):
        return value.strip().lower() not in (
            "",
            "false",
            "0",
            "0.0",
            "none",
            "null",
            "off",
            "disabled",
            "free",
            "free_only",
            "no",
        )
    if isinstance(value, Mapping):
        if not value:
            return False
        return any(_is_active_metadata_value(v, depth=depth + 1) for v in value.values())
    if isinstance(value, (list, tuple)):
        if not value:
            return False
        return any(_is_active_metadata_value(v, depth=depth + 1) for v in value)
    return True


def _mapping_has_non_free_tier(value: Any, *, is_cc107_card_tier: bool = False, depth: int = 0) -> bool:
    """Inspect nested tier/audience objects fail-closed while preserving CC-107 card descriptors."""
    if depth > MAX_JSON_DEPTH:
        return True
    if isinstance(value, Mapping):
        for k, v in value.items():
            if not isinstance(k, str):
                return True
            k_norm = _normalize_key(k)
            if is_cc107_card_tier and k_norm in ("source_ids", "rights_class", "use_label"):
                continue
            if is_cc107_card_tier and k_norm == "value" and isinstance(v, str):
                v_norm = _normalize_key(v)
                if v_norm in CC024_FORBIDDEN_TIER_VALUES:
                    return True
                if _CC107_CARD_TIER_VALUE_RE.fullmatch(v.strip()) or v_norm in ALLOWED_FREE_TIER_VALUES:
                    continue
                return True
            if _mapping_has_non_free_tier(v, is_cc107_card_tier=False, depth=depth + 1):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_mapping_has_non_free_tier(item, is_cc107_card_tier=False, depth=depth + 1) for item in value)
    if isinstance(value, bool):
        return value is True
    if isinstance(value, int):
        return value != 0
    if isinstance(value, float):
        return (not math.isfinite(value)) or value != 0.0
    if isinstance(value, str):
        v_norm = _normalize_key(value)
        if not v_norm:
            return False
        if v_norm in CC024_FORBIDDEN_TIER_VALUES:
            return True
        return v_norm not in ALLOWED_FREE_TIER_VALUES
    if value is None:
        return False
    return True


def _redact_key_segment(raw_key: str) -> str:
    digest = sha256(raw_key.encode("utf-8", errors="replace")).hexdigest()[:8]
    return f"<REDACTED_KEY#{digest}>"


def _check_no_surrogates(text: str, field: str) -> None:
    try:
        text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise FirewallEvidenceError(
            "UNPAIRED_UNICODE_SURROGATE",
            field,
            f"{field}: unpaired Unicode surrogate disallowed",
        ) from exc


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize value to CC-1011 canonical UTF-8 LF JSON bytes."""
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, OverflowError, UnicodeEncodeError, RecursionError) as exc:
        raise FirewallEvidenceError(
            "CANONICAL_JSON_SERIALIZATION_FAILED",
            "canonical_json",
            f"cannot serialize canonical JSON: {type(exc).__name__}",
        ) from exc
    return encoded + b"\n"


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def _parse_utc_ns(value: Any, field: str) -> tuple[datetime, int]:
    """Parse strict RFC 3339 UTC timestamp with nanosecond precision, catching OverflowError."""
    if isinstance(value, bool) or not isinstance(value, str):
        raise FirewallEvidenceError(
            "UTC_CLOCK_INVALID",
            field,
            f"{field}: expected strict RFC 3339 UTC string",
        )
    match = _UTC_CLOCK_RE.fullmatch(value)
    if match is None:
        raise FirewallEvidenceError(
            "UTC_CLOCK_INVALID",
            field,
            f"{field}: invalid RFC 3339 UTC clock",
        )
    whole, fraction, _ = match.groups()
    try:
        dt = datetime.fromisoformat(whole).replace(tzinfo=UTC)
        # Verify safe zone conversion to ET as well so extreme dates cannot trigger OverflowError downstream.
        _ = dt.astimezone(ET)
    except (ValueError, OverflowError, OSError) as exc:
        raise FirewallEvidenceError(
            "UTC_CLOCK_OVERFLOW_OR_INVALID",
            field,
            f"{field}: UTC clock out of representable range ({type(exc).__name__})",
        ) from exc
    nanos = int((fraction or "").ljust(9, "0"))
    return dt, nanos


def parse_payload_timestamp_utc(value: Any, field: str) -> tuple[datetime, int]:
    """Parse a timestamp value inside a payload fail-closed against bool, naive, and OverflowError."""
    if isinstance(value, bool):
        raise FirewallEvidenceError(
            "BOOL_TIMESTAMP_FORBIDDEN",
            field,
            f"{field}: boolean disallowed as timestamp",
        )
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise FirewallEvidenceError(
                "NON_FINITE_TIMESTAMP_FORBIDDEN",
                field,
                f"{field}: non-finite numeric timestamp disallowed",
            )
        if isinstance(value, int) and value.bit_length() > MAX_JSON_INT_BIT_LENGTH:
            raise FirewallEvidenceError(
                "UTC_CLOCK_OVERFLOW",
                field,
                f"{field}: numeric timestamp overflow",
            )
        try:
            dt = datetime.fromtimestamp(float(value), tz=UTC)
            _ = dt.astimezone(ET)
        except (ValueError, OverflowError, OSError) as exc:
            raise FirewallEvidenceError(
                "UTC_CLOCK_OVERFLOW",
                field,
                f"{field}: numeric UTC timestamp overflow ({type(exc).__name__})",
            ) from exc
        return dt.replace(microsecond=0), dt.microsecond * 1000

    if not isinstance(value, str):
        raise FirewallEvidenceError(
            "UTC_CLOCK_INVALID",
            field,
            f"{field}: unsupported timestamp type {type(value).__name__}",
        )

    stripped = value.strip()
    base_field = _TRAILING_INDEX_RE.sub("", field)
    leaf_field = base_field.rsplit(".", 1)[-1]
    if base_field.endswith("_utc") or leaf_field in UTC_TIMESTAMP_KEYS:
        return _parse_utc_ns(stripped, field)

    match = _ISO_OFFSET_CLOCK_RE.fullmatch(stripped)
    if match is None:
        raise FirewallEvidenceError(
            "UTC_CLOCK_INVALID",
            field,
            f"{field}: timezone-aware ISO-8601 timestamp required",
        )
    whole, fraction, offset = match.groups()
    iso_norm = whole.replace(" ", "T") + ("+00:00" if offset == "Z" else offset)
    try:
        parsed = datetime.fromisoformat(iso_norm)
        if parsed.tzinfo is None:
            raise FirewallEvidenceError(
                "NAIVE_TIMESTAMP_FORBIDDEN",
                field,
                f"{field}: naive timestamp disallowed",
            )
        dt_utc = parsed.astimezone(UTC)
        _ = dt_utc.astimezone(ET)
    except FirewallEvidenceError:
        raise
    except (ValueError, OverflowError, OSError) as exc:
        raise FirewallEvidenceError(
            "UTC_CLOCK_OVERFLOW",
            field,
            f"{field}: UTC conversion overflow ({type(exc).__name__})",
        ) from exc
    nanos = int((fraction or "").ljust(9, "0"))
    return dt_utc, nanos


def _safe_path_segment(raw_key: str) -> str:
    """Return raw_key unless it carries a surrogate, broker ID, private-alpha, or numeric-level pattern."""
    if not _is_valid_utf8_str(raw_key):
        return _redact_key_segment(raw_key)
    norm = _normalize_text(raw_key)
    if _KEY_NUMERIC_LEVEL_RE.search(norm):
        return _redact_key_segment(raw_key)
    surfaces = _scan_surfaces(norm)
    for surface in surfaces:
        for _, pattern in _BROKER_IDENTIFIER_PATTERNS:
            if pattern.search(surface):
                return _redact_key_segment(raw_key)
        for _, pattern in _KELLY_SIZING_LOT_PATTERNS:
            if pattern.search(surface):
                return _redact_key_segment(raw_key)
        if _STOP_LOSS_RE.search(surface) or _has_non_policy_take_profit(surface) or _ENTRY_FILL_RE.search(surface):
            return _redact_key_segment(raw_key)
        if _ACCOUNT_EQUITY_PNL_EXPLICIT_RE.search(surface) or _has_private_balance_money(surface):
            return _redact_key_segment(raw_key)
        for _, pattern in _PRIVATE_STUDY_PATTERNS:
            if pattern.search(surface):
                return _redact_key_segment(raw_key)
        for _, pattern in _L4_SLEEVE_WEIGHT_PATTERNS:
            if pattern.search(surface):
                return _redact_key_segment(raw_key)
        if _WINDOW_CC_GLOBAL_RE.search(surface):
            return _redact_key_segment(raw_key)
        lowered = surface.lower()
        if any(tok in lowered for tok in PUBLIC_WEBAPP_FORBIDDEN_TOKENS) or any(
            tok in lowered for tok in PUBLIC_WEBAPP_BOOK_DUMP_MARKERS
        ):
            return _redact_key_segment(raw_key)
    key_norm = _normalize_key(raw_key)
    tokens = tuple(t for t in key_norm.split("_") if t)
    if (
        key_norm in KELLY_SIZING_LOT_KEYS
        or key_norm in EXECUTION_LEVEL_FILL_KEYS
        or key_norm in ACCOUNT_EQUITY_PNL_KEYS
        or key_norm in BROKER_IDENTIFIER_KEYS
        or key_norm in PRIVATE_STUDY_TAG_KEYS
        or key_norm in L4_SLEEVE_WEIGHT_KEYS
        or key_norm in PUBLIC_WEBAPP_BOOK_DUMP_MARKERS
        or _has_token_phrase(tokens, _KELLY_KEY_PHRASES) is not None
        or _has_token_phrase(tokens, _EXECUTION_KEY_PHRASES) is not None
        or _has_token_phrase(tokens, _ACCOUNT_PNL_KEY_PHRASES) is not None
        or _has_token_phrase(tokens, _BROKER_KEY_PHRASES) is not None
        or _has_token_phrase(tokens, _PRIVATE_STUDY_KEY_PHRASES) is not None
        or any(_STUDY_TOKEN_RE.match(t) for t in tokens)
        or _has_token_phrase(tokens, _L4_SLEEVE_KEY_PHRASES) is not None
    ):
        return _redact_key_segment(raw_key)
    return raw_key


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in pairs:
        _check_no_surrogates(key, "json_key")
        if key in out:
            safe_k = _safe_path_segment(key)
            raise FirewallEvidenceError(
                "DUPLICATE_JSON_KEY_FORBIDDEN",
                "json_parse",
                f"duplicate JSON member disallowed: {safe_k!r}",
            )
        out[key] = val
    return out


def _reject_json_constant(token: str) -> Any:
    raise FirewallEvidenceError(
        "NON_FINITE_NUMBER_FORBIDDEN",
        "json_parse",
        f"non-finite JSON constant disallowed: {token}",
    )


def _parse_finite_float(raw: str) -> float:
    try:
        number = float(raw)
    except (ValueError, OverflowError) as exc:
        raise FirewallEvidenceError(
            "NON_FINITE_NUMBER_FORBIDDEN",
            "json_parse",
            "JSON float outside finite IEEE-754 range",
        ) from exc
    if not math.isfinite(number):
        raise FirewallEvidenceError(
            "NON_FINITE_NUMBER_FORBIDDEN",
            "json_parse",
            "JSON float outside finite IEEE-754 range",
        )
    return number


def _parse_bounded_int(raw: str) -> int:
    digits = raw.lstrip("+-")
    if len(digits) > MAX_JSON_INT_DIGITS:
        raise FirewallEvidenceError(
            "INTEGER_OVERFLOW_FORBIDDEN",
            "json_parse",
            "JSON integer exceeds safe finite digit ceiling",
        )
    try:
        number = int(raw)
        if number.bit_length() > MAX_JSON_INT_BIT_LENGTH:
            raise OverflowError("bit_length exceeded")
        as_float = float(number)
    except (ValueError, OverflowError) as exc:
        raise FirewallEvidenceError(
            "INTEGER_OVERFLOW_FORBIDDEN",
            "json_parse",
            "JSON integer overflows finite IEEE-754 float range",
        ) from exc
    if not math.isfinite(as_float):
        raise FirewallEvidenceError(
            "INTEGER_OVERFLOW_FORBIDDEN",
            "json_parse",
            "JSON integer overflows finite IEEE-754 float range",
        )
    return number


def strict_loads_json_bytes(
    raw: bytes,
    *,
    label: str = "payload",
    allow_bom: bool = False,
) -> dict[str, Any]:
    """Parse UTF-8 JSON bytes fail-closed against BOM, NaN/Inf, 1e400, 10**400, dup keys, surrogates."""
    if not isinstance(raw, (bytes, bytearray)):
        raise FirewallEvidenceError(
            "MALFORMED_JSON_INPUT",
            label,
            f"{label}: expected bytes",
        )
    data = bytes(raw)
    if not data:
        raise FirewallEvidenceError(
            "EMPTY_JSON_PAYLOAD",
            label,
            f"{label}: empty JSON payload",
        )
    if len(data) > MAX_PAYLOAD_BYTES:
        raise FirewallEvidenceError(
            "PAYLOAD_TOO_LARGE",
            label,
            f"{label}: payload exceeds {MAX_PAYLOAD_BYTES} bytes",
        )
    if data.startswith(b"\xef\xbb\xbf"):
        if allow_bom:
            data = data[3:]
        else:
            raise FirewallEvidenceError(
                "UTF8_BOM_FORBIDDEN",
                label,
                f"{label}: UTF-8 BOM disallowed",
            )
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise FirewallEvidenceError(
            "INVALID_UTF8_JSON",
            label,
            f"{label}: invalid UTF-8 byte sequence",
        ) from exc
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_json_constant,
            parse_float=_parse_finite_float,
            parse_int=_parse_bounded_int,
        )
    except FirewallEvidenceError:
        raise
    except (ValueError, RecursionError) as exc:
        raise FirewallEvidenceError(
            "MALFORMED_JSON_PAYLOAD",
            label,
            f"{label}: malformed JSON ({type(exc).__name__})",
        ) from exc
    if not isinstance(parsed, dict):
        raise FirewallEvidenceError(
            "JSON_ROOT_OBJECT_REQUIRED",
            label,
            f"{label}: expected top-level JSON object",
        )
    # Round-trip check rejects unpaired Unicode surrogates inside decoded strings.
    canonical_json_bytes(parsed)
    return parsed


def _is_regular_file(path: Path) -> bool:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise FirewallEvidenceError(
            "FILE_STAT_FAILED",
            path.name,
            f"{path.name}: cannot stat path ({type(exc).__name__})",
        ) from exc
    if not stat.S_ISREG(mode):
        raise FirewallEvidenceError(
            "NON_REGULAR_FILE_FORBIDDEN",
            path.name,
            f"{path.name}: expected a regular file",
        )
    return True


def _read_regular_file(path: Path, *, label: str | None = None) -> bytes:
    tag = label or path.name
    if not _is_regular_file(path):
        raise FirewallEvidenceError(
            "REQUIRED_FILE_MISSING",
            tag,
            f"{tag}: file missing",
        )
    try:
        size = path.lstat().st_size
    except OSError as exc:
        raise FirewallEvidenceError(
            "FILE_READ_FAILED",
            tag,
            f"{tag}: cannot stat file ({type(exc).__name__})",
        ) from exc
    if size > MAX_PAYLOAD_BYTES:
        raise FirewallEvidenceError(
            "FILE_TOO_LARGE",
            tag,
            f"{tag}: file exceeds {MAX_PAYLOAD_BYTES} bytes",
        )
    try:
        return path.read_bytes()
    except OSError as exc:
        raise FirewallEvidenceError(
            "FILE_READ_FAILED",
            tag,
            f"{tag}: cannot read file ({type(exc).__name__})",
        ) from exc


def normalize_payload_kind(payload_kind: Any) -> str:
    if not isinstance(payload_kind, str) or not payload_kind.strip():
        raise FirewallEvidenceError(
            "UNSUPPORTED_PAYLOAD_KIND",
            "payload_kind",
            "payload_kind must be a non-empty string",
        )
    if not _is_valid_utf8_str(payload_kind):
        raise FirewallEvidenceError(
            "UNPAIRED_UNICODE_SURROGATE",
            "payload_kind",
            "payload_kind: unpaired Unicode surrogate disallowed",
        )
    normalized = _PAYLOAD_KIND_ALIASES.get(payload_kind.strip().lower())
    if normalized not in SUPPORTED_PAYLOAD_KINDS:
        raise FirewallEvidenceError(
            "UNSUPPORTED_PAYLOAD_KIND",
            "payload_kind",
            f"unsupported payload_kind: {payload_kind!r}",
        )
    return normalized


# ---------------------------------------------------------------------------
# Finding Builder (Redacted: Never Echoes Private Input Values)
# ---------------------------------------------------------------------------


def _finding(
    *,
    code: str,
    category: str,
    path: str,
    rule: str,
    summary: str,
    cc024_bucket: str | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "path": path,
        "rule": rule,
        "cc024_bucket": cc024_bucket,
        "summary": summary,
    }


def _dedupe_and_sort_findings(findings: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str | None, str, str, str, str, str | None]] = set()
    unique: list[dict[str, Any]] = []
    for item in findings:
        art_id = item.get("artifact_id")
        sig = (
            str(art_id) if art_id is not None else None,
            str(item["code"]),
            str(item["category"]),
            str(item["path"]),
            str(item["rule"]),
            item.get("cc024_bucket"),
        )
        if sig not in seen:
            seen.add(sig)
            unique.append(item)
    unique.sort(
        key=lambda r: (
            str(r.get("artifact_id") or ""),
            r["category"],
            r["code"],
            r["path"],
            r["rule"],
        )
    )
    return unique


# ---------------------------------------------------------------------------
# Pause-Gate Evaluator (CC-1011 Parity + Pre-Dec-15 Fail-Closed Boundary)
# ---------------------------------------------------------------------------


def evaluate_pause_gate(
    as_of_utc: Any,
    *,
    gate_mode: str = GATE_MODE_PREFLIGHT,
    pause_dir: Path | str | None = None,
    publisher_stops_dir: Path | str | None = None,
    pause_state: Mapping[str, Any] | None = None,
    require_restored_marker: bool = True,
) -> dict[str, Any]:
    """Verify Dec-15 pause boundary (2026-12-14T17:00:00Z) and 3/3 .stop awareness.

    In ``preflight`` mode (default, CC-1011 parity):
      - Requires pause manifest with ``resume_at_utc >= 2026-12-14T17:00:00Z``,
        ``paused_at_utc <= as_of_utc`` and ``paused_at_utc < 2026-12-14T17:00:00Z``.
      - Requires all 3/3 publisher ``.stop`` files present and ``restored.json`` absent.
      - Returns ``HOLD_PAUSED_BEFORE_DEC15`` when ``as_of_utc < 2026-12-14T17:00:00Z``.
      - Returns ``BLOCKED`` if ``2026-12-14T17:00:00Z <= as_of_utc < resume_at_utc``.
      - Returns ``READY_FREE_UNPAUSE`` when ``as_of_utc >= resume_at_utc >= 2026-12-14T17:00:00Z``.

    In ``publish`` mode (live pre-publish boundary):
      - Before ``2026-12-14T17:00:00Z``: ALWAYS fails closed with ``HOLD_PAUSED_BEFORE_DEC15``
        (or ``BLOCKED`` if pause manifest/clock is invalid).
      - At/after ``resume_at_utc >= 2026-12-14T17:00:00Z``: requires 0/3 ``.stop`` files
        active (and valid ``restored.json`` when ``require_restored_marker=True``) to
        return ``ALLOW_FREE_PUBLISH``.
    """
    if not isinstance(gate_mode, str) or gate_mode not in SUPPORTED_GATE_MODES:
        raise FirewallEvidenceError(
            "UNSUPPORTED_GATE_MODE",
            "gate_mode",
            f"unsupported gate_mode ({type(gate_mode).__name__})",
        )

    as_of = _parse_utc_ns(as_of_utc, "as_of_utc")
    cutoff = _parse_utc_ns(DEC15_PAUSE_BOUNDARY_UTC, "pause_until_utc")

    base_result: dict[str, Any] = {
        "gate_mode": gate_mode,
        "as_of_utc": as_of_utc,
        "pause_until_utc": DEC15_PAUSE_BOUNDARY_UTC,
        "before_dec15_boundary": as_of < cutoff,
        "paused_at_utc": None,
        "resume_at_utc": None,
        "publisher_stops_expected": list(PUBLISHER_STOPS),
        "publisher_stops_present": [],
        "publisher_stops_missing": list(PUBLISHER_STOPS),
        "restored_present": None,
        "verdict": VERDICT_BLOCKED,
        "publish_allowed": False,
        "failure_code": None,
        "failure_cause": None,
    }

    has_fs = pause_dir is not None or publisher_stops_dir is not None
    if has_fs and pause_state is not None:
        base_result["failure_code"] = "PAUSE_EVIDENCE_AMBIGUOUS"
        base_result["failure_cause"] = "supply either filesystem pause_dir/publisher_stops_dir or pause_state, not both"
        return base_result

    if not has_fs and pause_state is None:
        if as_of < cutoff:
            base_result["verdict"] = VERDICT_HOLD_PAUSED_BEFORE_DEC15
            base_result["failure_code"] = "HOLD_PAUSED_BEFORE_DEC15"
            base_result["failure_cause"] = "ContentOps remains strictly paused before 2026-12-14T17:00:00Z"
            return base_result
        base_result["failure_code"] = "PAUSE_GATE_EVIDENCE_REQUIRED"
        base_result["failure_cause"] = (
            "pause manifest and 3/3 publisher .stop evidence required at/after Dec-15 boundary"
        )
        return base_result

    try:
        if has_fs:
            if pause_dir is None or publisher_stops_dir is None:
                raise FirewallEvidenceError(
                    "PAUSE_GATE_EVIDENCE_INCOMPLETE",
                    "contentops_pause",
                    "both pause_dir and publisher_stops_dir are required",
                )
            if not isinstance(pause_dir, (str, os.PathLike)) or isinstance(pause_dir, bytes):
                raise FirewallEvidenceError(
                    "PAUSE_DIR_PATH_INVALID",
                    "contentops_pause",
                    f"pause_dir must be a filesystem path, got {type(pause_dir).__name__}",
                )
            if not isinstance(publisher_stops_dir, (str, os.PathLike)) or isinstance(publisher_stops_dir, bytes):
                raise FirewallEvidenceError(
                    "PUBLISHER_STOPS_DIR_PATH_INVALID",
                    "contentops_pause",
                    f"publisher_stops_dir must be a filesystem path, got {type(publisher_stops_dir).__name__}",
                )
            p_raw = os.fspath(pause_dir)
            s_raw = os.fspath(publisher_stops_dir)
            if not isinstance(p_raw, str) or not _is_valid_utf8_str(p_raw):
                raise FirewallEvidenceError(
                    "PAUSE_DIR_PATH_INVALID",
                    "contentops_pause",
                    "pause_dir path is not a valid UTF-8 string",
                )
            if not isinstance(s_raw, str) or not _is_valid_utf8_str(s_raw):
                raise FirewallEvidenceError(
                    "PUBLISHER_STOPS_DIR_PATH_INVALID",
                    "contentops_pause",
                    "publisher_stops_dir path is not a valid UTF-8 string",
                )
            p_dir = Path(p_raw)
            s_dir = Path(s_raw)
            manifest = strict_loads_json_bytes(
                _read_regular_file(p_dir / "manifest.json", label="pause_manifest"),
                label="pause_manifest",
                allow_bom=False,
            )
            stops_present = [name for name in PUBLISHER_STOPS if _is_regular_file(s_dir / name)]
            restored_path = p_dir / "restored.json"
            try:
                restored_path.lstat()
                restored_present = True
            except FileNotFoundError:
                restored_present = False
            except OSError as exc:
                raise FirewallEvidenceError(
                    "RESTORED_STAT_FAILED",
                    "restored_json",
                    f"cannot stat restored.json ({type(exc).__name__})",
                ) from exc
            restored_doc: dict[str, Any] | None = None
            if restored_present and gate_mode == GATE_MODE_PUBLISH:
                restored_doc = strict_loads_json_bytes(
                    _read_regular_file(restored_path, label="restored_json"),
                    label="restored_json",
                    allow_bom=False,
                )
        else:
            if not isinstance(pause_state, Mapping):
                raise FirewallEvidenceError(
                    "PAUSE_STATE_INVALID",
                    "contentops_pause",
                    "pause_state must be a mapping",
                )
            manifest = {
                "paused_at_utc": pause_state.get("paused_at_utc"),
                "resume_at_utc": pause_state.get("resume_at_utc"),
            }
            raw_stops = pause_state.get("publisher_stops_present")
            if raw_stops is None:
                raw_stops = pause_state.get("stops_present")
            if not isinstance(raw_stops, (list, tuple, set, frozenset)):
                raise FirewallEvidenceError(
                    "PAUSE_STOPS_STATE_INVALID",
                    "contentops_pause",
                    "pause_state requires explicit publisher_stops_present sequence",
                )
            valid_stop_names = set(PUBLISHER_STOPS)
            cleaned_stops: list[str] = []
            for item in raw_stops:
                if not isinstance(item, str) or item not in valid_stop_names:
                    raise FirewallEvidenceError(
                        "PAUSE_STOPS_STATE_INVALID",
                        "contentops_pause",
                        "pause_state contains unknown publisher stop filename",
                    )
                if item not in cleaned_stops:
                    cleaned_stops.append(item)
            stops_present = [name for name in PUBLISHER_STOPS if name in cleaned_stops]
            raw_restored = pause_state.get("restored_present", False)
            if not isinstance(raw_restored, bool):
                raise FirewallEvidenceError(
                    "PAUSE_RESTORED_FLAG_INVALID",
                    "contentops_pause",
                    "restored_present must be a boolean",
                )
            restored_present = raw_restored
            restored_doc = None
            if restored_present and ("restored_at_utc" in pause_state or "dry_run" in pause_state):
                restored_doc = {}
                if "restored_at_utc" in pause_state:
                    restored_doc["started_at_utc"] = pause_state["restored_at_utc"]
                if "dry_run" in pause_state:
                    restored_doc["dry_run"] = pause_state["dry_run"]

        paused_raw = manifest.get("paused_at_utc")
        resume_raw = manifest.get("resume_at_utc")
        paused_ns = _parse_utc_ns(paused_raw, "manifest.paused_at_utc")
        resume_ns = _parse_utc_ns(resume_raw, "manifest.resume_at_utc")

        stops_missing = [name for name in PUBLISHER_STOPS if name not in stops_present]
        base_result["paused_at_utc"] = paused_raw
        base_result["resume_at_utc"] = resume_raw
        base_result["publisher_stops_present"] = stops_present
        base_result["publisher_stops_missing"] = stops_missing
        base_result["restored_present"] = restored_present

        if paused_ns > as_of or paused_ns >= cutoff:
            raise FirewallEvidenceError(
                "PAUSE_START_CLOCK_INVALID",
                "contentops_pause",
                "pause did not begin before Dec-15 boundary and by observation cutoff",
            )
        if resume_ns < cutoff:
            raise FirewallEvidenceError(
                "PAUSE_RESUME_BEFORE_DEC15_BOUNDARY",
                "contentops_pause",
                "scheduled resume_at_utc is strictly before 2026-12-14T17:00:00Z",
            )

        if gate_mode == GATE_MODE_PREFLIGHT:
            if stops_missing:
                raise FirewallEvidenceError(
                    "PUBLISHER_STOPS_MISSING",
                    "contentops_pause",
                    f"publisher stops missing: {', '.join(stops_missing)}",
                )
            if restored_present:
                raise FirewallEvidenceError(
                    "PAUSE_RESTORED_MARKER_PRESENT",
                    "contentops_pause",
                    "restored.json exists; pause snapshot is no longer in pre-unpause state",
                )
            if as_of < cutoff:
                base_result["verdict"] = VERDICT_HOLD_PAUSED_BEFORE_DEC15
                base_result["publish_allowed"] = False
                return base_result
            if as_of < resume_ns:
                raise FirewallEvidenceError(
                    "PAUSE_RESUME_STILL_IN_FUTURE",
                    "contentops_pause",
                    "configured resume_at_utc is still in the future",
                )
            base_result["verdict"] = VERDICT_READY_FREE_UNPAUSE
            base_result["publish_allowed"] = False
            return base_result

        # gate_mode == GATE_MODE_PUBLISH
        if as_of < cutoff:
            base_result["verdict"] = VERDICT_HOLD_PAUSED_BEFORE_DEC15
            base_result["publish_allowed"] = False
            return base_result
        if as_of < resume_ns:
            raise FirewallEvidenceError(
                "PAUSE_RESUME_STILL_IN_FUTURE",
                "contentops_pause",
                "configured resume_at_utc is still in the future",
            )
        if stops_present:
            raise FirewallEvidenceError(
                "PUBLISHER_STOP_FILES_ACTIVE",
                "contentops_pause",
                f"active publisher stop files block publish: {', '.join(stops_present)}",
            )
        if require_restored_marker:
            if not restored_present:
                raise FirewallEvidenceError(
                    "RESTORED_MARKER_MISSING",
                    "contentops_pause",
                    "restored.json required before publish after Dec-15 unpause",
                )
            if restored_doc is None:
                raise FirewallEvidenceError(
                    "RESTORED_CLOCK_MISSING",
                    "contentops_pause",
                    "restored_at_utc / restored.json timestamp required when require_restored_marker=True",
                )
            if "dry_run" in restored_doc and restored_doc["dry_run"] is not False:
                raise FirewallEvidenceError(
                    "RESTORED_MARKER_DRY_RUN_FORBIDDEN",
                    "contentops_pause",
                    "restored.json dry_run marker must be false (dry-run output cannot authorize live publish)",
                )
            if "started_at_utc" in restored_doc:
                started_ns = _parse_utc_ns(restored_doc["started_at_utc"], "restored.started_at_utc")
                if "ended_at_utc" in restored_doc:
                    ended_ns = _parse_utc_ns(restored_doc["ended_at_utc"], "restored.ended_at_utc")
                    if ended_ns < started_ns or ended_ns > as_of:
                        raise FirewallEvidenceError(
                            "RESTORED_CLOCK_INVALID",
                            "contentops_pause",
                            "restored.json ended_at_utc outside [started_at_utc, as_of_utc]",
                        )
            elif "ended_at_utc" in restored_doc:
                started_ns = _parse_utc_ns(restored_doc["ended_at_utc"], "restored.ended_at_utc")
            else:
                raise FirewallEvidenceError(
                    "RESTORED_CLOCK_MISSING",
                    "contentops_pause",
                    "restored.json requires explicit started_at_utc (or ended_at_utc) timestamp",
                )
            if started_ns < resume_ns or started_ns > as_of:
                raise FirewallEvidenceError(
                    "RESTORED_CLOCK_INVALID",
                    "contentops_pause",
                    "restored.json clock outside [resume_at_utc, as_of_utc]",
                )
        base_result["verdict"] = VERDICT_ALLOW_FREE_PUBLISH
        base_result["publish_allowed"] = True
        return base_result

    except FirewallEvidenceError as exc:
        base_result["verdict"] = VERDICT_BLOCKED
        base_result["publish_allowed"] = False
        base_result["failure_code"] = exc.code
        base_result["failure_cause"] = exc.cause
        return base_result


# ---------------------------------------------------------------------------
# Deep Structural + Rule A3 + CC-024 + public-webapp-preview Scanner
# ---------------------------------------------------------------------------


def _match_public_odds_clause(clause: str) -> str | None:
    if _ODDS_CUE_RE.search(clause) and _ODDS_PCT_OR_CENTS_RE.search(clause):
        return "ODDS_CUE_WITH_PERCENT"
    if _PRICED_AT_PCT_RE.search(clause):
        return "PRICED_AT_PERCENT"
    if _POLICY_MOVE_PCT_RE.search(clause):
        return "POLICY_MOVE_PERCENT"
    if _NUMERIC_GAP_PP_RE.search(clause):
        return "NUMERIC_GAP_PP"
    return None


def _has_non_policy_take_profit(text: str) -> bool:
    for match in _TAKE_PROFIT_RE.finditer(text):
        snippet = match.group(0).lower()
        if snippet.startswith("target"):
            prefix = text[max(0, match.start() - 72):match.start()]
            if _POLICY_TARGET_PREFIX_RE.search(prefix):
                continue
        return True
    return False


def _has_private_balance_money(text: str) -> bool:
    for match in _BALANCE_MONEY_RE.finditer(text):
        word = match.group(1).lower()
        prefix = text[max(0, match.start() - 48):match.start()]
        suffix = text[match.end(1):match.end(1) + 28]
        has_private_owner = bool(_PRIVATE_OWNER_PREFIX_RE.search(prefix))
        if word == "balance":
            if not has_private_owner and (
                _MACRO_BALANCE_EXEMPT_RE.search(prefix) or _BALANCE_SHEET_SUFFIX_RE.search(suffix)
            ):
                continue
        if word == "equity":
            if not has_private_owner and (
                _MACRO_EQUITY_PREFIX_RE.search(prefix) or _MACRO_EQUITY_SUFFIX_RE.search(suffix)
            ):
                continue
        if word == "capital":
            if not has_private_owner and (
                _MACRO_CAPITAL_PREFIX_RE.search(prefix) or _MACRO_CAPITAL_SUFFIX_RE.search(suffix)
            ):
                continue
        if word in ("profit", "loss") and not has_private_owner and re.search(
            r"\b(?:corporate|operating|gross|quarterly|annual|bank|sector|industry|pre-?tax|net\s+operating)\s+$",
            prefix,
            re.IGNORECASE,
        ):
            continue
        return True
    return False


def _scan_urls_in_text(text: str, path: str, findings: list[dict[str, Any]]) -> None:
    if _UNSAFE_URL_RE.search(text):
        findings.append(
            _finding(
                code="PUBLIC_WEBAPP_UNSAFE_URL_SCHEME",
                category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                path=path,
                rule="UNSAFE_OR_CREDENTIALED_URL",
                summary="unsafe, file:///, javascript:, vbscript:, ftp:, or credentialed URL forbidden in public copy",
            )
        )
    for attr_match in _ATTR_SCHEME_RE.finditer(text):
        scheme = attr_match.group(1).lower()
        if scheme != "https":
            findings.append(
                _finding(
                    code="PUBLIC_WEBAPP_UNSAFE_URL_SCHEME",
                    category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                    path=path,
                    rule="NON_HTTPS_HREF_OR_SRC_SCHEME",
                    summary=f"non-HTTPS attribute URL scheme forbidden in public copy ({scheme}:)",
                )
            )
    for raw_url in _URL_EXTRACT_RE.findall(text):
        candidate = raw_url.rstrip(".,;:!?")
        try:
            parsed = urlsplit(candidate)
        except ValueError:
            findings.append(
                _finding(
                    code="MALFORMED_URL_IN_PAYLOAD",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule="MALFORMED_URL",
                    summary="malformed URL in candidate payload",
                )
            )
            continue
        if parsed.username or parsed.password:
            findings.append(
                _finding(
                    code="PUBLIC_WEBAPP_CREDENTIALED_URL",
                    category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                    path=path,
                    rule="URL_EMBEDDED_CREDENTIALS",
                    summary="URL with embedded credentials forbidden in public copy",
                )
            )
        if parsed.scheme.lower() == "http":
            findings.append(
                _finding(
                    code="PUBLIC_WEBAPP_NON_HTTPS_URL",
                    category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                    path=path,
                    rule="HTTPS_REQUIRED",
                    summary="plain http:// URL forbidden in public copy",
                )
            )
        if parsed.path and _AFFILIATE_URL_PATH_RE.search(parsed.path):
            findings.append(
                _finding(
                    code="CC024_AFFILIATE_URL_PATH",
                    category="CC024_AFFILIATE_PROMO",
                    path=path,
                    rule="AFFILIATE_URL_PATH",
                    cc024_bucket="affiliate_count",
                    summary="affiliate/referral URL path segment disallowed",
                )
            )
        qs = parse_qs(parsed.query, keep_blank_values=True)
        for param in qs:
            if param.strip().lower() in _AFFILIATE_QUERY_PARAMS:
                findings.append(
                    _finding(
                        code="CC024_AFFILIATE_URL_PARAM",
                        category="CC024_AFFILIATE_PROMO",
                        path=path,
                        rule="AFFILIATE_QUERY_PARAM",
                        cc024_bucket="affiliate_count",
                        summary=f"affiliate/referral URL query parameter disallowed ({param.lower()})",
                    )
                )


def _scan_string_value(
    raw_text: str,
    *,
    path: str,
    leaf_key_norm: str,
    findings: list[dict[str, Any]],
) -> None:
    try:
        _check_no_surrogates(raw_text, path)
    except FirewallEvidenceError as exc:
        findings.append(
            _finding(
                code=exc.code,
                category="STRUCTURAL_HYGIENE",
                path=path,
                rule="UNPAIRED_SURROGATE",
                summary="unpaired Unicode surrogate disallowed",
            )
        )
        return

    norm = _normalize_text(raw_text)
    if not norm.strip():
        return
    surfaces = _scan_surfaces(norm)
    lowered_surfaces = tuple(s.lower() for s in surfaces)

    # 1. Rule A3 — Kelly f* / sizing / lot formulas
    for rule_name, pattern in _KELLY_SIZING_LOT_PATTERNS:
        if any(pattern.search(s) for s in surfaces):
            findings.append(
                _finding(
                    code="RULE_A3_KELLY_SIZING_LOT_LEAK",
                    category="RULE_A3_PRIVATE_ALPHA",
                    path=path,
                    rule=rule_name,
                    summary=f"internal Kelly/sizing/lot formula blocked ({rule_name})",
                )
            )

    # 2. Rule A3 — Exact stop-loss / take-profit / entry fill levels
    if any(_STOP_LOSS_RE.search(s) for s in surfaces):
        findings.append(
            _finding(
                code="RULE_A3_STOP_LOSS_LEVEL_LEAK",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule="STOP_LOSS_LEVEL",
                summary="exact stop-loss / broker-stop level blocked",
            )
        )
    if any(_has_non_policy_take_profit(s) for s in surfaces):
        findings.append(
            _finding(
                code="RULE_A3_TAKE_PROFIT_LEVEL_LEAK",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule="TAKE_PROFIT_OR_PRICE_TARGET",
                summary="take-profit / trade target level blocked (Decision 157 / Rule A3)",
            )
        )
    if any(_ENTRY_FILL_RE.search(s) for s in surfaces):
        findings.append(
            _finding(
                code="RULE_A3_ENTRY_FILL_LEVEL_LEAK",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule="ENTRY_FILL_LEVEL",
                summary="exact entry/execution fill level blocked",
            )
        )

    # 3. Rule A3 — Account balance / equity / PnL figures
    if any(_ACCOUNT_EQUITY_PNL_EXPLICIT_RE.search(s) or _has_private_balance_money(s) for s in surfaces):
        findings.append(
            _finding(
                code="RULE_A3_ACCOUNT_BALANCE_EQUITY_PNL_LEAK",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule="ACCOUNT_BALANCE_EQUITY_PNL",
                summary="private account balance / equity / PnL / expectancy figure blocked",
            )
        )

    # 4. Rule A3 — Broker / MT5 / IBKR account identifiers (incl. DUR343723)
    for rule_name, pattern in _BROKER_IDENTIFIER_PATTERNS:
        if any(pattern.search(s) for s in surfaces):
            findings.append(
                _finding(
                    code="RULE_A3_BROKER_ACCOUNT_IDENTIFIER_LEAK",
                    category="RULE_A3_PRIVATE_ALPHA",
                    path=path,
                    rule=rule_name,
                    summary=f"broker/MT5/IBKR account identifier or credential blocked ({rule_name})",
                )
            )

    # 5. Rule A3 — Private Study #6..#11 tags
    for rule_name, pattern in _PRIVATE_STUDY_PATTERNS:
        if any(pattern.search(s) for s in surfaces):
            findings.append(
                _finding(
                    code="RULE_A3_PRIVATE_STUDY_TAG_LEAK",
                    category="RULE_A3_PRIVATE_ALPHA",
                    path=path,
                    rule=rule_name,
                    summary=f"private Study #6..#11 or private-only tag blocked ({rule_name})",
                )
            )

    # 6. Rule A3 — Raw L4 / sleeve weights
    for rule_name, pattern in _L4_SLEEVE_WEIGHT_PATTERNS:
        if any(pattern.search(s) for s in surfaces):
            findings.append(
                _finding(
                    code="RULE_A3_L4_SLEEVE_WEIGHT_LEAK",
                    category="RULE_A3_PRIVATE_ALPHA",
                    path=path,
                    rule=rule_name,
                    summary=f"raw L4 / sleeve weight or alpha-stack marker blocked ({rule_name})",
                )
            )

    # 7. public-webapp-preview forbidden leak classes
    for tok in PUBLIC_WEBAPP_FORBIDDEN_TOKENS:
        if any(tok in low for low in lowered_surfaces):
            findings.append(
                _finding(
                    code="PUBLIC_WEBAPP_PRIVATE_TOKEN_LEAK",
                    category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                    path=path,
                    rule=f"TOKEN:{tok}",
                    summary=f"public-webapp-preview forbidden private token blocked ({tok})",
                )
            )
    if any(_WINDOW_CC_GLOBAL_RE.search(s) for s in surfaces):
        findings.append(
            _finding(
                code="PUBLIC_WEBAPP_PRIVATE_GLOBAL_LEAK",
                category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                path=path,
                rule="WINDOW_CC_PRIVATE_GLOBAL",
                summary="internal window.__CC_*__ sidecar global blocked",
            )
        )
    for book_tok in PUBLIC_WEBAPP_BOOK_DUMP_MARKERS:
        if any(book_tok in low for low in lowered_surfaces):
            findings.append(
                _finding(
                    code="PUBLIC_WEBAPP_BOOK_DUMP_MARKER_LEAK",
                    category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                    path=path,
                    rule=f"BOOK_MARKER:{book_tok}",
                    summary=f"internal book-dump marker blocked ({book_tok})",
                )
            )
    if any(_PREVIEW_HOST_RE.search(s) for s in surfaces):
        findings.append(
            _finding(
                code="PREVIEW_HOST_LINK_FORBIDDEN",
                category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                path=path,
                rule="DECISION_83_PREVIEW_HOST",
                summary="preview/staging host or fatcat2109 link blocked (Decision 83)",
            )
        )
    if any(_FORBIDDEN_PUBLIC_TIME_RE.search(s) for s in surfaces):
        findings.append(
            _finding(
                code="PUBLIC_TIMEZONE_ET_REQUIRED",
                category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                path=path,
                rule="DECISION_90_NON_ET_CLOCK",
                summary="GMT+7 / UTC+7 / Bangkok / Vietnam clock forbidden in public copy (Decision 90)",
            )
        )
    if any(_AI_MODEL_LEAK_RE.search(s) for s in surfaces):
        findings.append(
            _finding(
                code="PUBLIC_AI_MODEL_AUTHORSHIP_LEAK",
                category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                path=path,
                rule="DECISION_109_CC855_AI_LABEL",
                summary="internal AI model or authorship label forbidden in public copy",
            )
        )

    # Decision 107 raw CFD / broker symbol prose check (exempting URLs & technical metadata/ID keys)
    if leaf_key_norm not in _NON_PROSE_INSTRUMENT_KEYS and not leaf_key_norm.endswith(("_id", "_ids")):
        for surface in surfaces:
            without_urls = _URL_EXTRACT_RE.sub(" ", surface)
            if _DECISION_107_RAW_CFD_SYMBOL_RE.search(without_urls):
                findings.append(
                    _finding(
                        code="PUBLIC_RAW_CFD_SYMBOL_DECISION_107",
                        category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                        path=path,
                        rule="DECISION_107_RAW_CFD_SYMBOL",
                        summary="raw CFD / broker symbol name forbidden in public prose (Decision 107)",
                    )
                )
                break

    # CC-791 / PublicOddsLeakCheckV1 (clause-level scan over prose fields, preserving line boundaries)
    if leaf_key_norm not in _NON_PROSE_ODDS_KEYS:
        clause_texts: list[str] = [norm]
        stripped_md_lines = _MD_EMPHASIS_RE.sub("", norm)
        if stripped_md_lines != norm:
            clause_texts.append(stripped_md_lines)
        for clause_text in clause_texts:
            for clause in _CLAUSE_SPLIT_RE.split(clause_text):
                segment = _WS_COLLAPSE_RE.sub(" ", clause).strip()
                if not segment:
                    continue
                odds_rule = _match_public_odds_clause(segment)
                if odds_rule is not None:
                    findings.append(
                        _finding(
                            code="PUBLIC_ODDS_LEAK_CC791",
                            category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                            path=path,
                            rule=odds_rule,
                            cc024_bucket="raw_vendor_leak_count",
                            summary=f"numeric market/prediction/FedWatch odds blocked ({odds_rule})",
                        )
                    )

    # Raw licensed vendor & CC-024 commercial data-rights leak
    for rule_name, pattern in _RAW_VENDOR_LEAK_PATTERNS:
        if any(pattern.search(s) for s in surfaces):
            findings.append(
                _finding(
                    code="CC024_RAW_VENDOR_LEAK",
                    category="CC024_RAW_VENDOR_LEAK",
                    path=path,
                    rule=rule_name,
                    cc024_bucket="raw_vendor_leak_count",
                    summary=f"raw licensed vendor or commercial data-rights source blocked ({rule_name})",
                )
            )

    # 8. CC-024 / Decision 96 FREE-only paywall / VIP / subscription upsells
    for rule_name, pattern in _CC024_PAYWALL_CTA_PATTERNS:
        if any(pattern.search(s) for s in surfaces):
            findings.append(
                _finding(
                    code="CC024_PAYWALL_UPSELL_FORBIDDEN",
                    category="CC024_PAYWALL_UPSELL",
                    path=path,
                    rule=rule_name,
                    cc024_bucket="paid_paywall_count",
                    summary=f"paywall / VIP / paid subscription CTA blocked ({rule_name})",
                )
            )

    # 9. CC-024 affiliate / referral promo CTAs and URL params/paths
    for rule_name, pattern in _CC024_AFFILIATE_PATTERNS:
        if any(pattern.search(s) for s in surfaces):
            findings.append(
                _finding(
                    code="CC024_AFFILIATE_PROMO_FORBIDDEN",
                    category="CC024_AFFILIATE_PROMO",
                    path=path,
                    rule=rule_name,
                    cc024_bucket="affiliate_count",
                    summary=f"affiliate / referral promotional CTA blocked ({rule_name})",
                )
            )
    _scan_urls_in_text(norm, path, findings)


def _check_key_name(
    raw_key: str,
    key_norm: str,
    safe_key: str,
    path: str,
    value: Any,
    findings: list[dict[str, Any]],
) -> None:
    tokens = tuple(t for t in key_norm.split("_") if t)
    is_redacted = safe_key != raw_key
    display_key = safe_key if is_redacted else key_norm

    kelly_match = key_norm if key_norm in KELLY_SIZING_LOT_KEYS else _has_token_phrase(tokens, _KELLY_KEY_PHRASES)
    if kelly_match is not None:
        findings.append(
            _finding(
                code="RULE_A3_FORBIDDEN_KELLY_SIZING_KEY",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule=f"KEY:{kelly_match}",
                summary=f"forbidden internal Kelly/sizing/lot field blocked ({kelly_match})",
            )
        )

    exec_match = key_norm if key_norm in EXECUTION_LEVEL_FILL_KEYS else _has_token_phrase(tokens, _EXECUTION_KEY_PHRASES)
    if exec_match is not None:
        findings.append(
            _finding(
                code="RULE_A3_FORBIDDEN_EXECUTION_KEY",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule=f"KEY:{exec_match}",
                summary=f"forbidden stop-loss/take-profit/fill execution field blocked ({exec_match})",
            )
        )

    acct_match = key_norm if key_norm in ACCOUNT_EQUITY_PNL_KEYS else _has_token_phrase(tokens, _ACCOUNT_PNL_KEY_PHRASES)
    if acct_match is None and key_norm in ("balance", "equity"):
        # Allow macro narrative strings under bare 'balance'/'equity' keys (B16C21-L1)
        # while blocking numeric/mapping/currency account values.
        is_private_acct_val = (
            (isinstance(value, (int, float)) and not isinstance(value, bool))
            or isinstance(value, Mapping)
            or (isinstance(value, str) and bool(_PURE_MONEY_OR_NUM_RE.match(value.strip())))
        )
        if is_private_acct_val:
            acct_match = key_norm
    if acct_match is not None:
        findings.append(
            _finding(
                code="RULE_A3_FORBIDDEN_ACCOUNT_PNL_KEY",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule=f"KEY:{acct_match}",
                summary=f"forbidden account balance/equity/PnL field blocked ({acct_match})",
            )
        )

    broker_match = key_norm if key_norm in BROKER_IDENTIFIER_KEYS else _has_token_phrase(tokens, _BROKER_KEY_PHRASES)
    if broker_match is not None:
        findings.append(
            _finding(
                code="RULE_A3_FORBIDDEN_BROKER_KEY",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule=f"KEY:{broker_match}",
                summary=f"forbidden broker/MT5/IBKR/secret field blocked ({broker_match})",
            )
        )

    study_match = (
        key_norm
        if key_norm in PRIVATE_STUDY_TAG_KEYS
        else _has_token_phrase(tokens, _PRIVATE_STUDY_KEY_PHRASES)
        or next((t for t in tokens if _STUDY_TOKEN_RE.match(t)), None)
    )
    if study_match is not None:
        findings.append(
            _finding(
                code="RULE_A3_FORBIDDEN_PRIVATE_STUDY_KEY",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule=f"KEY:{study_match}",
                summary=f"forbidden private Study #6..#11 / private-only key blocked ({study_match})",
            )
        )

    l4_match = key_norm if key_norm in L4_SLEEVE_WEIGHT_KEYS else _has_token_phrase(tokens, _L4_SLEEVE_KEY_PHRASES)
    if l4_match is not None:
        findings.append(
            _finding(
                code="RULE_A3_FORBIDDEN_L4_SLEEVE_KEY",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule=f"KEY:{l4_match}",
                summary=f"forbidden raw L4 / sleeve weight field blocked ({l4_match})",
            )
        )

    odds_key_match = _has_token_phrase(tokens, _CC791_ODDS_KEY_PHRASES)
    if odds_key_match is not None:
        findings.append(
            _finding(
                code="PUBLIC_ODDS_LEAK_CC791",
                category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                path=path,
                rule=f"ODDS_KEY:{odds_key_match}",
                cc024_bucket="raw_vendor_leak_count",
                summary=f"structured market/prediction/FedWatch odds field blocked ({odds_key_match})",
            )
        )

    if key_norm in RAW_VENDOR_KEYS:
        findings.append(
            _finding(
                code="CC024_FORBIDDEN_RAW_VENDOR_KEY",
                category="CC024_RAW_VENDOR_LEAK",
                path=path,
                rule=f"KEY:{key_norm}",
                cc024_bucket="raw_vendor_leak_count",
                summary=f"forbidden raw vendor data field blocked ({key_norm})",
            )
        )
    if key_norm in ("series_id", "fred_series", "fred_id", "fred_series_id") and isinstance(value, str):
        if _FRED_COPYRIGHTED_SERIES_EXACT_RE.fullmatch(_normalize_text(value).strip()):
            findings.append(
                _finding(
                    code="CC024_RAW_VENDOR_LEAK",
                    category="CC024_RAW_VENDOR_LEAK",
                    path=path,
                    rule="FRED_COPYRIGHTED_SERIES",
                    cc024_bucket="raw_vendor_leak_count",
                    summary=f"copyrighted FRED series disallowed ({key_norm})",
                )
            )
    if key_norm in PUBLIC_WEBAPP_BOOK_DUMP_MARKERS:
        findings.append(
            _finding(
                code="PUBLIC_WEBAPP_BOOK_DUMP_KEY",
                category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                path=path,
                rule=f"KEY:{key_norm}",
                summary=f"forbidden book-dump field blocked ({key_norm})",
            )
        )

    # Explicit non-public export flags
    if key_norm in ("public_export", "public_output_allowed") and value is not True:
        findings.append(
            _finding(
                code="RULE_A3_NON_PUBLIC_EXPORT_FLAG",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule=f"FLAG:{key_norm}",
                summary=f"{key_norm} must not be false/non-true on a public release candidate",
            )
        )

    # Decision 157: chart target_drawn must never be true
    if key_norm == "target_drawn" and value is not False:
        findings.append(
            _finding(
                code="DECISION_157_CHART_TARGET_DRAWN_FORBIDDEN",
                category="RULE_A3_PRIVATE_ALPHA",
                path=path,
                rule="CHART_TARGET_DRAWN",
                summary="chart target_drawn must be explicitly false (Decision 157)",
            )
        )

    # CC-024 paywall / paid-tier metadata keys (recursive, exact int without float overflow)
    is_paywall = _is_paywall_key(key_norm)
    if is_paywall:
        if _is_active_metadata_value(value):
            findings.append(
                _finding(
                    code="CC024_PAYWALL_FIELD_ACTIVE",
                    category="CC024_PAYWALL_UPSELL",
                    path=path,
                    rule=f"KEY:{display_key}",
                    cc024_bucket="paid_paywall_count",
                    summary=f"active paywall / paid-pricing metadata blocked ({display_key})",
                )
            )
    if _is_tier_selector_key(key_norm) and not is_paywall:
        if isinstance(value, str):
            val_norm = _normalize_key(value)
            if val_norm in CC024_FORBIDDEN_TIER_VALUES or val_norm not in ALLOWED_FREE_TIER_VALUES:
                findings.append(
                    _finding(
                        code="CC024_NON_FREE_TIER_FORBIDDEN",
                        category="CC024_PAYWALL_UPSELL",
                        path=path,
                        rule=f"TIER:{display_key}",
                        cc024_bucket="paid_paywall_count",
                        summary=f"non-FREE publication tier/audience/mode blocked ({display_key})",
                    )
                )
        elif isinstance(value, Mapping):
            is_cc107 = (
                key_norm == "tier"
                and bool(value)
                and all(isinstance(k, str) and _normalize_key(k) in _CC107_CARD_TIER_KEYS for k in value)
            )
            if _mapping_has_non_free_tier(value, is_cc107_card_tier=is_cc107):
                findings.append(
                    _finding(
                        code="CC024_NON_FREE_TIER_FORBIDDEN",
                        category="CC024_PAYWALL_UPSELL",
                        path=path,
                        rule=f"TIER:{display_key}",
                        cc024_bucket="paid_paywall_count",
                        summary=f"non-FREE publication tier/audience descriptor blocked ({display_key})",
                    )
                )
        elif value is not None:
            findings.append(
                _finding(
                    code="CC024_NON_FREE_TIER_FORBIDDEN",
                    category="CC024_PAYWALL_UPSELL",
                    path=path,
                    rule=f"TIER_TYPE:{display_key}",
                    cc024_bucket="paid_paywall_count",
                    summary=f"invalid non-string tier/audience/mode field blocked ({display_key})",
                )
            )
    if key_norm in CC024_AFFILIATE_KEYS:
        if _is_active_metadata_value(value):
            findings.append(
                _finding(
                    code="CC024_AFFILIATE_FIELD_ACTIVE",
                    category="CC024_AFFILIATE_PROMO",
                    path=path,
                    rule=f"KEY:{display_key}",
                    cc024_bucket="affiliate_count",
                    summary=f"affiliate / referral metadata field blocked ({display_key})",
                )
            )
    if key_norm in RIGHTS_KEYS or key_norm.endswith("_rights_class"):
        if isinstance(value, str):
            val_norm = _normalize_key(value)
            if not val_norm or val_norm in DENIED_RIGHTS_VALUES:
                findings.append(
                    _finding(
                        code="CC024_DENIED_PUBLIC_RIGHTS",
                        category="CC024_RAW_VENDOR_LEAK",
                        path=path,
                        rule=f"RIGHTS:{display_key}",
                        cc024_bucket="raw_vendor_leak_count",
                        summary=f"non-public / licensed rights classification blocked ({display_key})",
                    )
                )
        else:
            findings.append(
                _finding(
                    code="CC024_RIGHTS_CLASS_INVALID",
                    category="CC024_RAW_VENDOR_LEAK",
                    path=path,
                    rule=f"RIGHTS_TYPE:{display_key}",
                    cc024_bucket="raw_vendor_leak_count",
                    summary=f"non-string rights classification disallowed ({display_key})",
                )
            )

    # Also scan raw key text itself for smuggled private tokens (e.g. {"DUR343723": 1})
    _scan_string_value(raw_key, path=f"{path}#key", leaf_key_norm="_key_name", findings=findings)


def _walk_and_inspect(
    value: Any,
    *,
    path: str,
    leaf_key_norm: str,
    depth: int,
    active_ids: set[int],
    findings: list[dict[str, Any]],
) -> None:
    if depth > MAX_JSON_DEPTH:
        findings.append(
            _finding(
                code="MAX_JSON_DEPTH_EXCEEDED",
                category="STRUCTURAL_HYGIENE",
                path=path,
                rule="MAX_DEPTH",
                summary=f"JSON nesting depth exceeds maximum {MAX_JSON_DEPTH}",
            )
        )
        return

    # Strict bool-in-numeric-field guard (Python bool is a subclass of int)
    if isinstance(value, bool):
        if leaf_key_norm in STRICT_NUMERIC_KEYS:
            findings.append(
                _finding(
                    code="BOOL_IN_NUMERIC_FIELD_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule=f"BOOL_NUMERIC:{leaf_key_norm}",
                    summary=f"boolean value disallowed in numeric field ({leaf_key_norm})",
                )
            )
        elif leaf_key_norm in UTC_TIMESTAMP_KEYS or leaf_key_norm.endswith("_utc"):
            findings.append(
                _finding(
                    code="BOOL_TIMESTAMP_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule=f"BOOL_CLOCK:{leaf_key_norm}",
                    summary=f"boolean value disallowed in timestamp field ({leaf_key_norm})",
                )
            )
        return

    if value is None:
        return

    if isinstance(value, int):
        if value.bit_length() > MAX_JSON_INT_BIT_LENGTH:
            findings.append(
                _finding(
                    code="INTEGER_OVERFLOW_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule="INT_BIT_LENGTH_OVERFLOW",
                    summary="integer exceeds safe finite IEEE-754 range",
                )
            )
            return
        try:
            as_float = float(value)
        except OverflowError:
            findings.append(
                _finding(
                    code="INTEGER_OVERFLOW_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule="INT_FLOAT_OVERFLOW",
                    summary="integer overflows IEEE-754 float range",
                )
            )
            return
        if not math.isfinite(as_float):
            findings.append(
                _finding(
                    code="INTEGER_OVERFLOW_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule="INT_NON_FINITE",
                    summary="integer overflows finite float range",
                )
            )
            return
        if leaf_key_norm in ("width", "height") and value <= 0:
            findings.append(
                _finding(
                    code="NON_POSITIVE_DIMENSION_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule=f"POSITIVE_INT:{leaf_key_norm}",
                    summary=f"chart dimension {leaf_key_norm} must be a positive integer",
                )
            )
        if leaf_key_norm in UTC_TIMESTAMP_KEYS or leaf_key_norm.endswith("_utc"):
            try:
                parse_payload_timestamp_utc(value, path)
            except FirewallEvidenceError as exc:
                findings.append(
                    _finding(
                        code=exc.code,
                        category="STRUCTURAL_HYGIENE",
                        path=path,
                        rule="PAYLOAD_UTC_CLOCK",
                        summary=exc.cause,
                    )
                )
        return

    if isinstance(value, float):
        if not math.isfinite(value):
            findings.append(
                _finding(
                    code="NON_FINITE_NUMBER_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule="FLOAT_NON_FINITE",
                    summary="NaN or Inf floating-point value disallowed",
                )
            )
            return
        if leaf_key_norm in ("width", "height"):
            findings.append(
                _finding(
                    code="NON_INTEGER_DIMENSION_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule=f"INTEGER_REQUIRED:{leaf_key_norm}",
                    summary=f"chart dimension {leaf_key_norm} must be an integer",
                )
            )
        if leaf_key_norm in UTC_TIMESTAMP_KEYS or leaf_key_norm.endswith("_utc"):
            try:
                parse_payload_timestamp_utc(value, path)
            except FirewallEvidenceError as exc:
                findings.append(
                    _finding(
                        code=exc.code,
                        category="STRUCTURAL_HYGIENE",
                        path=path,
                        rule="PAYLOAD_UTC_CLOCK",
                        summary=exc.cause,
                    )
                )
        return

    if isinstance(value, str):
        if leaf_key_norm in UTC_TIMESTAMP_KEYS or leaf_key_norm.endswith("_utc"):
            try:
                parse_payload_timestamp_utc(value, path)
            except FirewallEvidenceError as exc:
                findings.append(
                    _finding(
                        code=exc.code,
                        category="STRUCTURAL_HYGIENE",
                        path=path,
                        rule="PAYLOAD_UTC_CLOCK",
                        summary=exc.cause,
                    )
                )
        _scan_string_value(value, path=path, leaf_key_norm=leaf_key_norm, findings=findings)
        return

    if isinstance(value, Mapping):
        obj_id = id(value)
        if obj_id in active_ids:
            findings.append(
                _finding(
                    code="CYCLIC_JSON_STRUCTURE_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule="CYCLE_DETECTED",
                    summary="cyclic reference disallowed in candidate payload",
                )
            )
            return
        active_ids.add(obj_id)
        try:
            for raw_key, child in value.items():
                if not isinstance(raw_key, str):
                    findings.append(
                        _finding(
                            code="NON_STRING_JSON_KEY_FORBIDDEN",
                            category="STRUCTURAL_HYGIENE",
                            path=path,
                            rule="NON_STRING_KEY",
                            summary="all JSON object keys must be strings",
                        )
                    )
                    continue
                safe_key = _safe_path_segment(raw_key)
                child_path = f"{path}.{safe_key}"
                key_norm = _normalize_key(raw_key)
                _check_key_name(raw_key, key_norm, safe_key, child_path, child, findings)
                _walk_and_inspect(
                    child,
                    path=child_path,
                    leaf_key_norm=key_norm,
                    depth=depth + 1,
                    active_ids=active_ids,
                    findings=findings,
                )
        finally:
            active_ids.remove(obj_id)
        return

    if isinstance(value, (list, tuple)):
        obj_id = id(value)
        if obj_id in active_ids:
            findings.append(
                _finding(
                    code="CYCLIC_JSON_STRUCTURE_FORBIDDEN",
                    category="STRUCTURAL_HYGIENE",
                    path=path,
                    rule="CYCLE_DETECTED",
                    summary="cyclic sequence disallowed in candidate payload",
                )
            )
            return
        active_ids.add(obj_id)
        try:
            for idx, item in enumerate(value):
                item_path = f"{path}[{idx}]"
                _walk_and_inspect(
                    item,
                    path=item_path,
                    leaf_key_norm=leaf_key_norm,
                    depth=depth + 1,
                    active_ids=active_ids,
                    findings=findings,
                )
        finally:
            active_ids.remove(obj_id)
        return

    findings.append(
        _finding(
            code="UNSUPPORTED_JSON_VALUE_TYPE",
            category="STRUCTURAL_HYGIENE",
            path=path,
            rule=f"TYPE:{type(value).__name__}",
            summary=f"non-JSON value type disallowed ({type(value).__name__})",
        )
    )


def _iter_overlay_strings(obj: Any, *, depth: int = 0) -> Iterable[str]:
    if depth > 8:
        return
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, Mapping):
        for v in obj.values():
            yield from _iter_overlay_strings(v, depth=depth + 1)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _iter_overlay_strings(item, depth=depth + 1)


def _check_chart_overlay_sequence(
    entries: Any,
    *,
    base_path: str,
    findings: list[dict[str, Any]],
) -> None:
    if not isinstance(entries, (list, tuple)):
        return
    for idx, entry in enumerate(entries):
        flagged = False
        for raw_text in _iter_overlay_strings(entry):
            if not _is_valid_utf8_str(raw_text):
                continue
            norm = _normalize_text(raw_text)
            for surface in _scan_surfaces(norm):
                if _CHART_EXECUTION_OVERLAY_RE.search(surface):
                    flagged = True
                    break
            if flagged:
                break
        if flagged:
            findings.append(
                _finding(
                    code="RULE_A3_CHART_EXECUTION_LEVEL_DRAWN",
                    category="RULE_A3_PRIVATE_ALPHA",
                    path=f"{base_path}[{idx}]",
                    rule="CHART_LEVELS_EXECUTION_LEAK",
                    summary="execution stop/target/fill overlay forbidden on public chart",
                )
            )


def _check_chart_metadata_contract(payload: Mapping[str, Any], findings: list[dict[str, Any]]) -> None:
    """Enforce extra fail-closed invariants on chart_metadata payloads."""
    snapshot = payload.get("tradingview_snapshot")
    if isinstance(snapshot, Mapping):
        if snapshot.get("target_drawn") is True:
            findings.append(
                _finding(
                    code="DECISION_157_CHART_TARGET_DRAWN_FORBIDDEN",
                    category="RULE_A3_PRIVATE_ALPHA",
                    path="$.tradingview_snapshot.target_drawn",
                    rule="CHART_TARGET_DRAWN",
                    summary="chart snapshot target_drawn must be false (Decision 157)",
                )
            )
        for overlay_key in ("levels_drawn", "annotations", "lines"):
            _check_chart_overlay_sequence(
                snapshot.get(overlay_key),
                base_path=f"$.tradingview_snapshot.{overlay_key}",
                findings=findings,
            )
    for overlay_key in ("levels_drawn", "annotations", "lines"):
        _check_chart_overlay_sequence(
            payload.get(overlay_key),
            base_path=f"$.{overlay_key}",
            findings=findings,
        )


def _inspect_single_artifact(
    payload: Any,
    *,
    payload_kind: str,
    artifact_id: str,
    raw_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Inspect one candidate artifact (already parsed or raw bytes) and return deterministic summary."""
    findings: list[dict[str, Any]] = []
    kind = normalize_payload_kind(payload_kind)
    parsed_obj: dict[str, Any] | None = None
    payload_hash: str

    if raw_bytes is not None:
        if isinstance(raw_bytes, (bytes, bytearray)):
            payload_hash = sha256_hex(bytes(raw_bytes))
        else:
            payload_hash = sha256_hex(f"<non-bytes:{type(raw_bytes).__name__}>".encode("utf-8"))
        try:
            parsed_obj = strict_loads_json_bytes(raw_bytes, label=artifact_id, allow_bom=False)
        except FirewallEvidenceError as exc:
            findings.append(
                _finding(
                    code=exc.code,
                    category="STRUCTURAL_HYGIENE",
                    path="$",
                    rule=exc.code,
                    summary=exc.cause,
                )
            )
    else:
        if not isinstance(payload, Mapping):
            payload_hash = sha256_hex(f"<non-mapping:{type(payload).__name__}>".encode("utf-8"))
            findings.append(
                _finding(
                    code="JSON_ROOT_OBJECT_REQUIRED",
                    category="STRUCTURAL_HYGIENE",
                    path="$",
                    rule="JSON_ROOT_OBJECT_REQUIRED",
                    summary=f"expected JSON object mapping, got {type(payload).__name__}",
                )
            )
        else:
            parsed_obj = dict(payload)
            _walk_and_inspect(
                parsed_obj,
                path="$",
                leaf_key_norm="$root",
                depth=0,
                active_ids=set(),
                findings=findings,
            )
            if kind == "chart_metadata":
                _check_chart_metadata_contract(parsed_obj, findings)
            try:
                payload_hash = sha256_hex(canonical_json_bytes(parsed_obj))
            except FirewallEvidenceError as exc:
                payload_hash = sha256_hex(f"<unserializable:{artifact_id}:{exc.code}>".encode("utf-8"))
                findings.append(
                    _finding(
                        code=exc.code,
                        category="STRUCTURAL_HYGIENE",
                        path="$",
                        rule=exc.code,
                        summary=exc.cause,
                    )
                )

    if raw_bytes is not None and parsed_obj is not None:
        _walk_and_inspect(
            parsed_obj,
            path="$",
            leaf_key_norm="$root",
            depth=0,
            active_ids=set(),
            findings=findings,
        )
        if kind == "chart_metadata":
            _check_chart_metadata_contract(parsed_obj, findings)
        # Recompute canonical content hash over parsed object for deterministic CC-1011 receipt parity.
        try:
            payload_hash = sha256_hex(canonical_json_bytes(parsed_obj))
        except FirewallEvidenceError as exc:
            findings.append(
                _finding(
                    code=exc.code,
                    category="STRUCTURAL_HYGIENE",
                    path="$",
                    rule=exc.code,
                    summary=exc.cause,
                )
            )

    deduped = _dedupe_and_sort_findings(findings)
    return {
        "artifact_id": artifact_id,
        "payload_kind": kind,
        "payload_sha256": payload_hash,
        "clean": len(deduped) == 0,
        "finding_count": len(deduped),
        "findings": deduped,
    }


# ---------------------------------------------------------------------------
# Public Firewall Entrypoints & CC-1011 Compatible Receipts
# ---------------------------------------------------------------------------


def evaluate_release_batch(
    artifacts: Sequence[Mapping[str, Any]],
    *,
    as_of_utc: Any,
    observed_at_utc: Any = None,
    gate_mode: str = GATE_MODE_PREFLIGHT,
    pause_dir: Path | str | None = None,
    publisher_stops_dir: Path | str | None = None,
    pause_state: Mapping[str, Any] | None = None,
    require_restored_marker: bool = True,
) -> dict[str, Any]:
    """Evaluate one or more candidate artifacts and emit a CC-1011-compatible receipt.

    Each item in ``artifacts`` must be a mapping containing:
      - ``artifact_id`` (optional str; defaults to ``artifact-<idx>``)
      - ``payload_kind`` (str: ``post``, ``card``, ``caption``, ``chart_metadata``, ``digest``)
      - exactly one of ``payload`` (Mapping), ``raw_bytes`` (bytes), or ``path`` (Path/str)
    """
    top_findings: list[dict[str, Any]] = []
    gate_mode_valid = isinstance(gate_mode, str) and gate_mode in SUPPORTED_GATE_MODES
    safe_gate_mode = (
        gate_mode
        if gate_mode_valid
        else (gate_mode if _is_valid_utf8_str(gate_mode) else f"<invalid:{type(gate_mode).__name__}>")
    )
    if not gate_mode_valid:
        if isinstance(gate_mode, str) and not _is_valid_utf8_str(gate_mode):
            top_findings.append(
                _finding(
                    code="UNPAIRED_UNICODE_SURROGATE",
                    category="STRUCTURAL_HYGIENE",
                    path="$.gate_mode",
                    rule="UNPAIRED_SURROGATE",
                    summary="gate_mode: unpaired Unicode surrogate disallowed",
                )
            )
        top_findings.append(
            _finding(
                code="UNSUPPORTED_GATE_MODE",
                category="STRUCTURAL_HYGIENE",
                path="$.gate_mode",
                rule="UNSUPPORTED_GATE_MODE",
                summary=f"unsupported gate_mode ({type(gate_mode).__name__})",
            )
        )

    as_of_valid = True
    as_of_ns = None
    if isinstance(as_of_utc, str) and not _is_valid_utf8_str(as_of_utc):
        as_of_valid = False
        top_findings.append(
            _finding(
                code="UNPAIRED_UNICODE_SURROGATE",
                category="STRUCTURAL_HYGIENE",
                path="$.as_of_utc",
                rule="UNPAIRED_SURROGATE",
                summary="as_of_utc: unpaired Unicode surrogate disallowed",
            )
        )
    else:
        try:
            as_of_ns = _parse_utc_ns(as_of_utc, "as_of_utc")
        except FirewallEvidenceError as exc:
            as_of_valid = False
            as_of_ns = None
            top_findings.append(
                _finding(
                    code=exc.code,
                    category="STRUCTURAL_HYGIENE",
                    path="$.as_of_utc",
                    rule=exc.code,
                    summary=exc.cause,
                )
            )

    obs_raw = as_of_utc if observed_at_utc is None else observed_at_utc
    if isinstance(obs_raw, str) and not _is_valid_utf8_str(obs_raw):
        top_findings.append(
            _finding(
                code="UNPAIRED_UNICODE_SURROGATE",
                category="STRUCTURAL_HYGIENE",
                path="$.observed_at_utc",
                rule="UNPAIRED_SURROGATE",
                summary="observed_at_utc: unpaired Unicode surrogate disallowed",
            )
        )
    else:
        try:
            obs_ns = _parse_utc_ns(obs_raw, "observed_at_utc")
            if as_of_ns is not None and obs_ns > as_of_ns:
                top_findings.append(
                    _finding(
                        code="OBSERVED_AFTER_AS_OF_CUTOFF",
                        category="STRUCTURAL_HYGIENE",
                        path="$.observed_at_utc",
                        rule="CAUSALITY_VIOLATION",
                        summary="observed_at_utc cannot be after as_of_utc",
                    )
                )
        except FirewallEvidenceError as exc:
            top_findings.append(
                _finding(
                    code=exc.code,
                    category="STRUCTURAL_HYGIENE",
                    path="$.observed_at_utc",
                    rule=exc.code,
                    summary=exc.cause,
                )
            )

    if as_of_valid and gate_mode_valid:
        pause_gate = evaluate_pause_gate(
            as_of_utc,
            gate_mode=gate_mode,
            pause_dir=pause_dir,
            publisher_stops_dir=publisher_stops_dir,
            pause_state=pause_state,
            require_restored_marker=require_restored_marker,
        )
    else:
        pause_gate = {
            "gate_mode": safe_gate_mode,
            "as_of_utc": _safe_receipt_str(as_of_utc, fallback=None),
            "pause_until_utc": DEC15_PAUSE_BOUNDARY_UTC,
            "before_dec15_boundary": None,
            "paused_at_utc": None,
            "resume_at_utc": None,
            "publisher_stops_expected": list(PUBLISHER_STOPS),
            "publisher_stops_present": [],
            "publisher_stops_missing": list(PUBLISHER_STOPS),
            "restored_present": None,
            "verdict": VERDICT_BLOCKED,
            "publish_allowed": False,
            "failure_code": "OBSERVATION_CLOCK_OR_MODE_INVALID",
            "failure_cause": "cannot evaluate pause gate without valid as_of_utc and gate_mode",
        }

    artifact_results: list[dict[str, Any]] = []
    if not isinstance(artifacts, Sequence) or isinstance(artifacts, (str, bytes, bytearray)) or len(artifacts) == 0:
        top_findings.append(
            _finding(
                code="EMPTY_ARTIFACT_BATCH",
                category="STRUCTURAL_HYGIENE",
                path="$.artifacts",
                rule="EMPTY_ARTIFACT_BATCH",
                summary="at least one candidate artifact is required",
            )
        )
    else:
        seen_ids: set[str] = set()
        for idx, spec in enumerate(artifacts):
            if not isinstance(spec, Mapping):
                top_findings.append(
                    _finding(
                        code="INVALID_ARTIFACT_SPEC",
                        category="STRUCTURAL_HYGIENE",
                        path=f"$.artifacts[{idx}]",
                        rule="INVALID_ARTIFACT_SPEC",
                        summary="artifact specification must be a mapping",
                    )
                )
                continue
            art_id = spec.get("artifact_id")
            if art_id is None:
                art_id = f"artifact-{idx + 1}"
            if isinstance(art_id, str) and not _is_valid_utf8_str(art_id):
                art_id = f"artifact-{idx + 1}"
                top_findings.append(
                    _finding(
                        code="UNPAIRED_UNICODE_SURROGATE",
                        category="STRUCTURAL_HYGIENE",
                        path=f"$.artifacts[{idx}].artifact_id",
                        rule="UNPAIRED_SURROGATE",
                        summary="artifact_id: unpaired Unicode surrogate disallowed",
                    )
                )
            elif not isinstance(art_id, str) or not art_id.strip():
                art_id = f"artifact-{idx + 1}"
                top_findings.append(
                    _finding(
                        code="INVALID_ARTIFACT_ID",
                        category="STRUCTURAL_HYGIENE",
                        path=f"$.artifacts[{idx}].artifact_id",
                        rule="INVALID_ARTIFACT_ID",
                        summary="artifact_id must be a non-empty string",
                    )
                )
            else:
                safe_art_id = _safe_path_segment(art_id)
                if art_id in seen_ids:
                    top_findings.append(
                        _finding(
                            code="DUPLICATE_ARTIFACT_ID",
                            category="STRUCTURAL_HYGIENE",
                            path=f"$.artifacts[{idx}].artifact_id",
                            rule="DUPLICATE_ARTIFACT_ID",
                            summary=f"duplicate artifact_id disallowed ({safe_art_id})",
                        )
                    )
                art_id = safe_art_id
            seen_ids.add(art_id)

            kind_raw = spec.get("payload_kind", "post")
            try:
                kind = normalize_payload_kind(kind_raw)
            except FirewallEvidenceError as exc:
                top_findings.append(
                    _finding(
                        code=exc.code,
                        category="STRUCTURAL_HYGIENE",
                        path=f"$.artifacts[{idx}].payload_kind",
                        rule=exc.code,
                        summary=exc.cause,
                    )
                )
                continue

            sources_present = sum(
                1 for k in ("payload", "raw_bytes", "path") if k in spec and spec[k] is not None
            )
            if sources_present != 1:
                top_findings.append(
                    _finding(
                        code="AMBIGUOUS_ARTIFACT_SOURCE",
                        category="STRUCTURAL_HYGIENE",
                        path=f"$.artifacts[{idx}]",
                        rule="AMBIGUOUS_ARTIFACT_SOURCE",
                        summary="specify exactly one of payload, raw_bytes, or path",
                    )
                )
                continue

            if spec.get("path") is not None:
                raw_path = spec["path"]
                if not isinstance(raw_path, (str, os.PathLike)) or isinstance(raw_path, bytes):
                    top_findings.append(
                        _finding(
                            code="INVALID_ARTIFACT_PATH",
                            category="STRUCTURAL_HYGIENE",
                            path=f"$.artifacts[{idx}].path",
                            rule="INVALID_ARTIFACT_PATH",
                            summary=f"artifact path must be str or PathLike, got {type(raw_path).__name__}",
                        )
                    )
                    continue
                try:
                    fspath_val = os.fspath(raw_path)
                except TypeError:
                    top_findings.append(
                        _finding(
                            code="INVALID_ARTIFACT_PATH",
                            category="STRUCTURAL_HYGIENE",
                            path=f"$.artifacts[{idx}].path",
                            rule="INVALID_ARTIFACT_PATH",
                            summary=f"artifact path is not a valid PathLike ({type(raw_path).__name__})",
                        )
                    )
                    continue
                if not isinstance(fspath_val, str) or not _is_valid_utf8_str(fspath_val):
                    top_findings.append(
                        _finding(
                            code="UNPAIRED_UNICODE_SURROGATE" if isinstance(fspath_val, str) else "INVALID_ARTIFACT_PATH",
                            category="STRUCTURAL_HYGIENE",
                            path=f"$.artifacts[{idx}].path",
                            rule="INVALID_ARTIFACT_PATH",
                            summary="artifact path must be a valid UTF-8 string",
                        )
                    )
                    continue
                try:
                    file_bytes = _read_regular_file(Path(fspath_val), label=art_id)
                except FirewallEvidenceError as exc:
                    top_findings.append(
                        _finding(
                            code=exc.code,
                            category="STRUCTURAL_HYGIENE",
                            path=f"$.artifacts[{idx}].path",
                            rule=exc.code,
                            summary=exc.cause,
                        )
                    )
                    continue
                res = _inspect_single_artifact(None, payload_kind=kind, artifact_id=art_id, raw_bytes=file_bytes)
            elif spec.get("raw_bytes") is not None:
                raw_b = spec["raw_bytes"]
                if isinstance(raw_b, str):
                    try:
                        raw_b = raw_b.encode("utf-8", errors="strict")
                    except UnicodeEncodeError:
                        top_findings.append(
                            _finding(
                                code="UNPAIRED_UNICODE_SURROGATE",
                                category="STRUCTURAL_HYGIENE",
                                path=f"$.artifacts[{idx}].raw_bytes",
                                rule="UNPAIRED_SURROGATE",
                                summary="unpaired Unicode surrogate disallowed in raw JSON string",
                            )
                        )
                        continue
                res = _inspect_single_artifact(None, payload_kind=kind, artifact_id=art_id, raw_bytes=raw_b)
            else:
                res = _inspect_single_artifact(spec["payload"], payload_kind=kind, artifact_id=art_id, raw_bytes=None)

            for item in res["findings"]:
                item["artifact_id"] = art_id
            artifact_results.append(res)

    all_findings = list(top_findings)
    for res in artifact_results:
        all_findings.extend(res["findings"])
    all_findings = _dedupe_and_sort_findings(all_findings)

    # Compute exact CC-024 / CC-1011 counters (strict int, never bool)
    paid_paywall_count = sum(1 for f in all_findings if f.get("cc024_bucket") == "paid_paywall_count")
    affiliate_count = sum(1 for f in all_findings if f.get("cc024_bucket") == "affiliate_count")
    raw_vendor_leak_count = sum(1 for f in all_findings if f.get("cc024_bucket") == "raw_vendor_leak_count")
    rule_a3_private_leak_count = sum(1 for f in all_findings if f["category"] == "RULE_A3_PRIVATE_ALPHA")
    public_webapp_leak_count = sum(1 for f in all_findings if f["category"] == "PUBLIC_WEBAPP_FORBIDDEN_LEAK")
    structural_error_count = sum(1 for f in all_findings if f["category"] == "STRUCTURAL_HYGIENE")

    checked_artifact_count = len(artifact_results)
    release_manifest = {
        "schema": RELEASE_MANIFEST_SCHEMA,
        "mode": FREE_ONLY_MODE,
        "pause_until_utc": DEC15_PAUSE_BOUNDARY_UTC,
        "artifacts": [
            {
                "artifact_id": r["artifact_id"],
                "payload_kind": r["payload_kind"],
                "payload_sha256": r["payload_sha256"],
                "clean": r["clean"],
            }
            for r in sorted(artifact_results, key=lambda x: (x["artifact_id"], x["payload_kind"]))
        ],
    }
    release_manifest_bytes = canonical_json_bytes(release_manifest)
    candidate_sha256 = sha256_hex(release_manifest_bytes)

    cc024_mode = FREE_ONLY_MODE if (not all_findings and checked_artifact_count > 0) else VERDICT_BLOCKED
    cc024_audit = {
        "mode": cc024_mode,
        "observed_at_utc": _safe_receipt_str(obs_raw, fallback=""),
        "candidate_sha256": candidate_sha256,
        "checked_artifact_count": int(checked_artifact_count),
        "paid_paywall_count": int(paid_paywall_count),
        "affiliate_count": int(affiliate_count),
        "raw_vendor_leak_count": int(raw_vendor_leak_count),
    }

    # Final verdict decision: fail-closed on ANY finding or pause-gate block.
    if all_findings:
        verdict = VERDICT_BLOCKED
        publish_allowed = False
    elif pause_gate["verdict"] == VERDICT_BLOCKED:
        verdict = VERDICT_BLOCKED
        publish_allowed = False
    elif pause_gate["verdict"] == VERDICT_HOLD_PAUSED_BEFORE_DEC15:
        verdict = VERDICT_HOLD_PAUSED_BEFORE_DEC15
        publish_allowed = False
    elif pause_gate["verdict"] == VERDICT_READY_FREE_UNPAUSE:
        verdict = VERDICT_READY_FREE_UNPAUSE
        publish_allowed = False
    elif pause_gate["verdict"] == VERDICT_ALLOW_FREE_PUBLISH:
        verdict = VERDICT_ALLOW_FREE_PUBLISH
        publish_allowed = True
    else:
        verdict = VERDICT_BLOCKED
        publish_allowed = False

    category_counts = dict(sorted(Counter(f["category"] for f in all_findings).items()))
    code_counts = dict(sorted(Counter(f["code"] for f in all_findings).items()))

    receipt_body: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "policy": POLICY,
        "cc1011_compat_commit": CC1011_COMPAT_COMMIT,
        "verdict": verdict,
        "publish_allowed": publish_allowed,
        "gate_mode": safe_gate_mode,
        "as_of_utc": _safe_receipt_str(as_of_utc, fallback=None),
        "pause_until_utc": DEC15_PAUSE_BOUNDARY_UTC,
        "payload_sha256": artifact_results[0]["payload_sha256"] if len(artifact_results) == 1 else None,
        "candidate_sha256": candidate_sha256,
        "release_manifest": release_manifest,
        "cc024_audit": cc024_audit,
        "pause_gate": pause_gate,
        "counts": {
            "checked_artifact_count": int(checked_artifact_count),
            "total_findings": int(len(all_findings)),
            "rule_a3_private_leak_count": int(rule_a3_private_leak_count),
            "public_webapp_leak_count": int(public_webapp_leak_count),
            "paid_paywall_count": int(paid_paywall_count),
            "affiliate_count": int(affiliate_count),
            "raw_vendor_leak_count": int(raw_vendor_leak_count),
            "structural_error_count": int(structural_error_count),
            "by_category": category_counts,
            "by_code": code_counts,
        },
        "artifacts": [
            {
                "artifact_id": r["artifact_id"],
                "payload_kind": r["payload_kind"],
                "payload_sha256": r["payload_sha256"],
                "clean": r["clean"],
                "finding_count": r["finding_count"],
            }
            for r in artifact_results
        ],
        "findings": all_findings[:MAX_FINDINGS_REPORTED],
        "findings_truncated": len(all_findings) > MAX_FINDINGS_REPORTED,
    }
    receipt_sha256 = sha256_hex(canonical_json_bytes(receipt_body))
    return {**receipt_body, "receipt_sha256": receipt_sha256}


def evaluate_payload(
    payload: Any,
    *,
    payload_kind: str = "post",
    as_of_utc: Any,
    observed_at_utc: Any = None,
    artifact_id: str = "candidate-1",
    gate_mode: str = GATE_MODE_PREFLIGHT,
    pause_dir: Path | str | None = None,
    publisher_stops_dir: Path | str | None = None,
    pause_state: Mapping[str, Any] | None = None,
    require_restored_marker: bool = True,
) -> dict[str, Any]:
    """Evaluate a single in-memory candidate payload object."""
    return evaluate_release_batch(
        [{"artifact_id": artifact_id, "payload_kind": payload_kind, "payload": payload}],
        as_of_utc=as_of_utc,
        observed_at_utc=observed_at_utc,
        gate_mode=gate_mode,
        pause_dir=pause_dir,
        publisher_stops_dir=publisher_stops_dir,
        pause_state=pause_state,
        require_restored_marker=require_restored_marker,
    )


def evaluate_payload_bytes(
    raw_bytes: bytes | str,
    *,
    payload_kind: str = "post",
    as_of_utc: Any,
    observed_at_utc: Any = None,
    artifact_id: str = "candidate-1",
    gate_mode: str = GATE_MODE_PREFLIGHT,
    pause_dir: Path | str | None = None,
    publisher_stops_dir: Path | str | None = None,
    pause_state: Mapping[str, Any] | None = None,
    require_restored_marker: bool = True,
) -> dict[str, Any]:
    """Evaluate raw JSON bytes (or str) fail-closed before any publication."""
    return evaluate_release_batch(
        [{"artifact_id": artifact_id, "payload_kind": payload_kind, "raw_bytes": raw_bytes}],
        as_of_utc=as_of_utc,
        observed_at_utc=observed_at_utc,
        gate_mode=gate_mode,
        pause_dir=pause_dir,
        publisher_stops_dir=publisher_stops_dir,
        pause_state=pause_state,
        require_restored_marker=require_restored_marker,
    )


_FORBIDDEN_PUBLIC_FILENAME_TOKENS: tuple[str, ...] = (
    ".private.",
    "ibkr-book",
    "exness-book",
    "ibkr_book",
    "exness_book",
    "internal-economic-calendar",
    "internal-gamma-options",
    "internal-price-bars",
    "internal-financialjuice-wire",
    "alpha-stress-phase",
    "alpha-stress-summary",
    "private-desk",
    "private_desk",
    "attention-map-summary",
    "contentops-newsroom-summary",
    "market-forces-attribution",
    "_private_texts",
    "private_only",
    "desk-record.private",
)


def evaluate_payload_file(
    path: Path | str,
    *,
    payload_kind: str = "post",
    as_of_utc: Any,
    observed_at_utc: Any = None,
    artifact_id: str | None = None,
    gate_mode: str = GATE_MODE_PREFLIGHT,
    pause_dir: Path | str | None = None,
    publisher_stops_dir: Path | str | None = None,
    pause_state: Mapping[str, Any] | None = None,
    require_restored_marker: bool = True,
) -> dict[str, Any]:
    """Evaluate a single regular JSON file read-only from disk."""
    if isinstance(path, (str, os.PathLike)) and not isinstance(path, bytes):
        try:
            fs_val = os.fspath(path)
        except TypeError:
            fs_val = None
        if isinstance(fs_val, str) and _is_valid_utf8_str(fs_val):
            target: Any = Path(fs_val)
            art_id = artifact_id or target.name or "candidate-1"
        else:
            target = path
            art_id = artifact_id or "candidate-1"
    else:
        target = path
        art_id = artifact_id or "candidate-1"
    return evaluate_release_batch(
        [{"artifact_id": art_id, "payload_kind": payload_kind, "path": target}],
        as_of_utc=as_of_utc,
        observed_at_utc=observed_at_utc,
        gate_mode=gate_mode,
        pause_dir=pause_dir,
        publisher_stops_dir=publisher_stops_dir,
        pause_state=pause_state,
        require_restored_marker=require_restored_marker,
    )


def scan_public_directory_readonly(
    directory: Path | str,
    *,
    allowed_suffixes: tuple[str, ...] = (".json",),
    max_files: int = 2000,
) -> dict[str, Any]:
    """Read-only audit of a public directory (e.g. public-webapp-preview) for leak parity."""
    if not isinstance(directory, (str, os.PathLike)) or isinstance(directory, bytes):
        return {
            "exists": False,
            "directory": f"<invalid:{type(directory).__name__}>",
            "files_scanned": 0,
            "clean_files": 0,
            "failed_files": 1,
            "findings_count": 1,
            "truncated": False,
            "failures": [{"file": "<invalid>", "code": "INVALID_DIRECTORY_PATH"}],
        }
    root = Path(directory)
    if not root.is_dir():
        return {
            "exists": False,
            "directory": str(root),
            "files_scanned": 0,
            "clean_files": 0,
            "failed_files": 0,
            "findings_count": 0,
            "truncated": False,
            "failures": [{"file": str(root), "code": "DIRECTORY_MISSING"}],
        }
    effective_max = 0 if (isinstance(max_files, bool) or not isinstance(max_files, int) or max_files < 0) else max_files
    files_scanned = 0
    clean_files = 0
    failures: list[dict[str, Any]] = []
    findings_total = 0
    truncated = False
    for candidate in sorted(root.rglob("*")):
        rel = candidate.relative_to(root).as_posix()
        try:
            st = candidate.lstat()
        except OSError as exc:
            if files_scanned >= effective_max:
                truncated = True
                break
            files_scanned += 1
            findings_total += 1
            failures.append({
                "file": rel,
                "finding_count": 1,
                "codes": ["FILE_STAT_FAILED"],
                "error": type(exc).__name__,
            })
            continue
        mode = st.st_mode
        if stat.S_ISDIR(mode):
            continue
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            if files_scanned >= effective_max:
                truncated = True
                break
            files_scanned += 1
            findings_total += 1
            failures.append({
                "file": rel,
                "finding_count": 1,
                "codes": ["NON_REGULAR_FILE_FORBIDDEN"],
            })
            continue
        if candidate.suffix.lower() not in allowed_suffixes:
            continue
        if files_scanned >= effective_max:
            truncated = True
            break
        files_scanned += 1
        rel_lower = rel.lower()
        file_findings: list[dict[str, Any]] = []
        for bad_tok in _FORBIDDEN_PUBLIC_FILENAME_TOKENS:
            if bad_tok in rel_lower:
                file_findings.append(
                    _finding(
                        code="PUBLIC_WEBAPP_FORBIDDEN_FILENAME",
                        category="PUBLIC_WEBAPP_FORBIDDEN_LEAK",
                        path=rel,
                        rule=f"FILENAME:{bad_tok}",
                        summary=f"forbidden private filename in public directory ({bad_tok})",
                    )
                )
        try:
            raw = _read_regular_file(candidate, label=rel)
            if raw.startswith(b"\xef\xbb\xbf"):
                raise FirewallEvidenceError("UTF8_BOM_FORBIDDEN", rel, f"{rel}: UTF-8 BOM disallowed")
            parsed = json.loads(
                raw.decode("utf-8", errors="strict"),
                object_pairs_hook=_reject_duplicate_json_keys,
                parse_constant=_reject_json_constant,
                parse_float=_parse_finite_float,
                parse_int=_parse_bounded_int,
            )
            _walk_and_inspect(
                parsed,
                path="$",
                leaf_key_norm="$root",
                depth=0,
                active_ids=set(),
                findings=file_findings,
            )
        except (FirewallEvidenceError, UnicodeDecodeError, ValueError, RecursionError) as exc:
            file_findings.append(
                _finding(
                    code="PUBLIC_FILE_JSON_INVALID",
                    category="STRUCTURAL_HYGIENE",
                    path=rel,
                    rule=type(exc).__name__,
                    summary=f"invalid UTF-8 strict JSON ({type(exc).__name__})",
                )
            )
        deduped = _dedupe_and_sort_findings(file_findings)
        if deduped:
            findings_total += len(deduped)
            failures.append({
                "file": rel,
                "finding_count": len(deduped),
                "codes": sorted({f["code"] for f in deduped}),
            })
        else:
            clean_files += 1
    return {
        "exists": True,
        "directory": str(root),
        "files_scanned": files_scanned,
        "clean_files": clean_files,
        "failed_files": len(failures),
        "findings_count": findings_total,
        "truncated": truncated,
        "failures": failures[:100],
    }


def _exit_code_for_receipt(receipt: Mapping[str, Any]) -> int:
    verdict = receipt.get("verdict")
    mode = receipt.get("gate_mode")
    if verdict == VERDICT_BLOCKED:
        return EXIT_BLOCKED
    if verdict == VERDICT_HOLD_PAUSED_BEFORE_DEC15:
        return EXIT_OK if mode == GATE_MODE_PREFLIGHT else EXIT_HOLD_PAUSED
    if verdict in (VERDICT_READY_FREE_UNPAUSE, VERDICT_ALLOW_FREE_PUBLISH):
        return EXIT_OK
    return EXIT_BLOCKED


def main(argv: Sequence[str] | None = None) -> int:
    """Read-only CLI printing deterministic JSON receipt to stdout."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--payload",
        action="append",
        required=True,
        type=Path,
        help="Path to candidate JSON payload file (repeatable for release batches)",
    )
    parser.add_argument(
        "--payload-kind",
        action="append",
        default=None,
        help="Payload kind matching each --payload (post, card, caption, chart_metadata, digest)",
    )
    parser.add_argument("--as-of-utc", required=True, help="RFC 3339 UTC observation clock")
    parser.add_argument("--observed-at-utc", default=None, help="Optional CC-024 observed_at_utc clock")
    parser.add_argument(
        "--gate-mode",
        choices=(GATE_MODE_PREFLIGHT, GATE_MODE_PUBLISH),
        default=GATE_MODE_PREFLIGHT,
        help="preflight (CC-1011 pre-unpause check) or publish (live Dec-15+ send gate)",
    )
    parser.add_argument("--pause-dir", type=Path, default=None, help="Pause snapshot directory with manifest.json")
    parser.add_argument(
        "--publisher-stops-dir",
        type=Path,
        default=None,
        help="Directory holding runner-publisher{,-b,-c}.stop markers",
    )
    parser.add_argument(
        "--no-require-restored-marker",
        action="store_true",
        help="In publish mode, allow publish without restored.json once stops are cleared at/after resume_at_utc",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    kinds = list(args.payload_kind or [])
    if not kinds:
        kinds = ["post"] * len(args.payload)
    elif len(kinds) == 1 and len(args.payload) > 1:
        kinds = kinds * len(args.payload)
    elif len(kinds) != len(args.payload):
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "policy": POLICY,
            "verdict": VERDICT_BLOCKED,
            "publish_allowed": False,
            "gate_mode": args.gate_mode,
            "error": "PAYLOAD_KIND_COUNT_MISMATCH",
        }
        print(json.dumps(receipt, sort_keys=True, allow_nan=False))
        return EXIT_BLOCKED

    batch = [
        {"artifact_id": path.name, "payload_kind": kind, "path": path}
        for path, kind in zip(args.payload, kinds)
    ]
    receipt = evaluate_release_batch(
        batch,
        as_of_utc=args.as_of_utc,
        observed_at_utc=args.observed_at_utc,
        gate_mode=args.gate_mode,
        pause_dir=args.pause_dir,
        publisher_stops_dir=args.publisher_stops_dir,
        require_restored_marker=not args.no_require_restored_marker,
    )
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return _exit_code_for_receipt(receipt)


if __name__ == "__main__":
    raise SystemExit(main())
