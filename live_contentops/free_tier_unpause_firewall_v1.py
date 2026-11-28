"""V2.1-C6 ~15 Dec 2026 FREE-Only CC-024-Clean Unpause Firewall & Preflight.

Pure-code, strictly fail-closed preflight and outbound-payload verifier for the
~15 Dec 2026 FREE-only ContentOps unpause (`monetization-and-live-roadmap-20261127.md`,
`pillars-v2-1-official-decision-20261126.md` section 4, `CC-024`, Decisions 40, 44,
72b, 83, 90, 107, 109, 157, 158, 168, 184):

  (a) CC-024 Commercial-Rights & Public Compliance Firewall:
      Blocks Investing.com / Myfxbook consensus, OCC / Yahoo GEX, FRED SP500,
      TradingView paywall/embedded widgets (while keeping static public snapshot
      credits like "Chart: TradingView"), raw X-list / wire quotes, AI / model
      labels, private book / positions / prepared responses, preview hosts,
      unnamed market-odds percentages & prediction-market/FedWatch numbers,
      price targets, non-ET public clocks, and raw CFD instrument codes.
  (b) FREE_ONLY_MODE Guarantee:
      Guarantees zero paid paywall, paid-tier, checkout, referral, or
      subscription-gate markers or metadata flags emitted prior to the Q1 2027
      Paid Tier launch.
  (c) V2.1-C6 Day-1 SHA-256 Track-Record Citation Lineage & Post-04 Dec Sunset:
      Verifies Day-1 SHA-256 hash-chained signal/fill ledgers (compatible with
      `L4ShadowSleeveArenaLedgerRecordV1` and `CapitalChronicleTrackRecordChainV1`)
      and public `ContentOpsTrackRecordCitationV1` lineage seals, AND confirms
      zero active Claude / Anthropic / `agy` runtime dependencies post-04 Dec.
  (d) Strictly Fail-Closed Integrity (Zero Silent Waivers — Rule A3):
      Refuses missing or malformed inputs, duplicate JSON keys, non-finite
      numbers (`NaN`, `Inf`, `-Inf`), bool-as-int coercions, naive/date-only/
      future clocks, stale pre-15-Dec pause manifests, premature unpause clocks,
      active kill switches, and any waiver/bypass key.

Strictly offline pure Python stdlib + local `live_contentops` guards:
zero network calls, zero process-environment reads, zero subprocess spawns, zero LLM
calls, zero live writes.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence
import unicodedata
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from . import agy_editorial_assist_v1 as agy_assist
from . import agy_neo_answerer_v1 as agy_neo
from . import ai_research_canonical_article_engine_v6 as v6_engine
from . import event_article_guard_v1 as event_guard
from . import market_attention_map_public_v1 as attention
from . import native_desktop_editorial_v1 as native_editorial
from . import plan_analysis_pages_v1 as plan_pages
from . import public_decision_checks_v1 as decision_checks
from . import public_instruments_v1 as instruments
from . import scenario_voice_v1 as voice
from .preview_link_guard_v1 import find_forbidden_link
from .public_time_v1 import find_forbidden_public_time, public_date
from .reader_article_contract_v1 import INTERNAL_MODEL_AND_CLOCK_PHRASES

SCHEMA_VERSION = "contentops.free_tier_unpause_firewall.v1"
TRACK_RECORD_CITATION_SCHEMA = "ContentOpsTrackRecordCitationV1"
TRACK_RECORD_CITATION_SCHEMA_VERSION = "1.0.0"

FREE_ONLY_MODE = "FREE_ONLY_MODE"
UTC = timezone.utc
ET = ZoneInfo("America/New_York")

# Fri 04 Dec 2026 00:00 GMT+7 == 2026-12-03T17:00:00Z (CC-855 / Decision 184).
POST_DEC04_CLAUDE_SUNSET_UTC = native_editorial.CLAUDE_SUNSET_UTC
# Tue 15 Dec 2026 00:00 GMT+7 == 2026-12-14T17:00:00Z (V2.1-C6 pause through 30 Nov - 14 Dec).
DEC15_FREE_UNPAUSE_EARLIEST_UTC = datetime(2026, 12, 14, 17, 0, tzinfo=UTC)
# Q1 2027 earliest paid-tier boundary (roadmap Step 2 targets Mar 2027).
PAID_TIER_EARLIEST_UTC = datetime(2027, 1, 1, 0, 0, tzinfo=UTC)

GENESIS_PREV_SHA256 = "0" * 64
ARENA_LEDGER_SCHEMA = "L4ShadowSleeveArenaLedgerRecordV1"
GENERIC_TRACK_CHAIN_SCHEMA = "CapitalChronicleTrackRecordChainV1"
SUPPORTED_CHAIN_SCHEMAS = frozenset({ARENA_LEDGER_SCHEMA, GENERIC_TRACK_CHAIN_SCHEMA})

FREE_SEED_DESTINATIONS = frozenset({"x", "substack", "telegram", "discord"})
ALL_FREE_DESTINATIONS = frozenset({
    "x",
    "substack",
    "substack_notes",
    "telegram",
    "discord",
    "threads",
    "linkedin",
    "linkedin_company",
    "facebook_page",
    "instagram_business",
    "youtube",
})

ALLOWED_POST_DEC04_DIGEST_DRIVERS = frozenset({"python-neo", "codex-astra", "codex-desktop"})
FORBIDDEN_RETIRED_DRIVERS = frozenset({
    "claude",
    "claude-cli",
    "claude-desktop",
    "claude-code",
    "claude-legacy",
    "anthropic",
    "agy",
    "antigravity",
    "antigravity-cli",
})

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})$"
)

# Rule A3: Zero silent waivers / bypass keys permitted anywhere in inputs.
_SILENT_WAIVER_KEYS = frozenset({
    "skip_cc024",
    "waive_cc024",
    "waive_firewall",
    "bypass_firewall",
    "bypass_free_only",
    "skip_free_only",
    "allow_paid_override",
    "allow_stale_manifest",
    "ignore_stale_manifest",
    "ignore_claude_sunset",
    "skip_claude_sunset",
    "allow_agy",
    "skip_hash_chain",
    "waive_hash_chain",
    "force_unpause",
    "silent_waiver",
    "waiver",
    "waivers",
})

# Private / execution / internal-only keys that must never appear in outbound public payloads.
_FORBIDDEN_PRIVATE_KEYS = frozenset({
    "prepared_responses",
    "prepared_response",
    "open_positions",
    "open_position_impacts",
    "surprise_map",
    "priced_in_gap",
    "linked_odds_markets",
    "x_list_posts",
    "raw_x_posts",
    "x_posts",
    "wire_headlines",
    "raw_headlines",
    "private_headlines",
    "private_notes",
    "account_id",
    "account_number",
    "account_equity",
    "lot_size",
    "stop_formula",
    "formula_params",
    "level2_triggers",
    "armed_plans",
    "broker_levels",
    "execution_plans",
    "scoring_hooks",
    "branch_flip_evidence",
    "public_boundary_notice",
})

# Narrow technical-metadata keys skipped ONLY from display-prose-specific checks
# (Section 2 global scan still inspects EVERY string in the payload).
# Values under these keys are skipped ONLY when they match strict machine-token shapes
# (ISO-8601 UTC timestamp, compact single identifier/code/hash, pure URL, or local FS path).
_NON_PROSE_UTC_KEYS = frozenset({"utc"})
_NON_PROSE_MARKET_CODE_KEYS = frozenset({
    "lead_market",
    "market_asset",
    "asset_id",
    "tv_symbol",
    "symbol",
    "affected_markets",
    "asset",
    "instrument",
    "canonical_symbol",
})
_NON_PROSE_ID_KEYS = frozenset({
    "id",
    "sha256",
    "schema",
    "schema_version",
    "contract_version",
    "ledger_schema",
    "public_instrument_policy",
    "mode",
    "unpause_mode",
    "substack_delivery_mode",
    "destination",
    "platform",
    "session",
    "status",
    "state",
    "primary_reason",
    "trigger",
    "triggers",
    "material_shift_flags",
    "reader_contract",
    "provenance_status",
})
_NON_PROSE_ID_SUFFIXES = ("_id", "_ids", "_sha256", "_hash", "_fingerprint", "_signature")
_NON_PROSE_URL_KEYS = frozenset({
    "url",
    "canonical_url",
    "source_url",
    "source_page_url",
    "chart_url",
    "public_url",
})
_COMPACT_TOKEN_RE = re.compile(r"^[A-Za-z0-9:_./-]{1,128}$")
_PURE_URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.I)

# ---------------------------------------------------------------------------
# (a) CC-024 Commercial-Rights & Public Compliance Patterns
# ---------------------------------------------------------------------------

_INVESTING_MYFXBOOK_RE = re.compile(
    r"\binvesting\.com\b|\bmyfxbook(?:\.com)?\b|\bfxstreet\.com\b",
    re.I,
)
_OCC_YAHOO_GEX_RE = re.compile(
    r"\btheocc\.com\b"
    r"|\boptions\s+clearing\s+corporation\b"
    r"|\bOCC\b[^.\n]{0,65}\b(?:open\s+interest|options?|gex|gamma|oi\b|series|chain|quotes?|data)\b"
    r"|\b(?:open\s+interest|options?|gex|gamma|option\s+chain)\b[^.\n]{0,65}\bOCC\b"
    r"|\bfinance\.yahoo\.com\b"
    r"|\byahoo\s+finance\b"
    r"|\byfinance\b"
    r"|\byahoo[_-]?(?:options|gex|finance)\b"
    r"|\bocc[_-]?(?:oi|gex|options)\b"
    r"|\bOPRA\s+derived\b|\bCboe\s+delayed\s+quotes?\b",
    re.I,
)
_FRED_SP500_RE = re.compile(
    r"(?:fred\.)?stlouisfed\.org/[^\s\"'<>]*\bsp500\b"
    r"|stlouisfed\.org/[^\s\"'<>]*[?&=,/]sp500(?:\b|\.|&|$)"
    r"|\bFRED\s*[:/\-]\s*SP500\b"
    r"|\bFRED\b[^.\n]{0,50}\bSP500\b"
    r"|\bSP500\b[^.\n]{0,50}\b(?:FRED|st\.?\s*louis\s+fed|stlouisfed\.org)\b",
    re.I,
)
_TRADINGVIEW_WIDGET_RE = re.compile(
    r"s3\.tradingview\.com"
    r"|widget\.tradingview\.com"
    r"|tradingview\.com/(?:external-embedding|embed-widget|widget(?:embed)?)"
    r"|\btradingview[-_ ]?widget\b"
    r"|\bembed[-_ ]widget\b"
    r"|\bTradingView\.widget\s*\("
    r"|<iframe\b[^>]*tradingview"
    r"|<script\b[^>]*tradingview"
    r"|\btradingview\b[^.\n]{0,45}\b(?:paywall|paid|embedded?)\s+widgets?\b"
    r"|\b(?:paywall|paid)\s+tradingview\s+widgets?\b",
    re.I,
)
_RAW_X_OR_WIRE_RE = re.compile(
    r"https?://(?:www\.)?(?:x|twitter)\.com/"
    r"|\b(?:JIM_X_LIST|PRIVATE_X_LIST|X_LIST_FEED|X[-_ ]list)\b"
    r"|\b(?:Bloomberg|Reuters|Dow\s+Jones|FinancialJuice)\s+wire\b"
    r"|\b(?:FirstSquawk|DeItaone|WalterBloomberg|headline_wire_feed)\b",
    re.I,
)
_EXTRA_AI_MODEL_RE = re.compile(
    r"\b(?:gpt[- .]?[3456](?:\.\d+)?[\w.-]*|claude[- ]?(?:opus|sonnet|haiku|code|desktop)?|"
    r"gemini[- .]?[1234][\w.-]*|deepseek[-\w]*|grok[- ]?\d[\w.-]*|llama[- ]?\d|"
    r"language\s+model|llm\s+(?:desk|pipeline|agent|model)|as\s+an\s+AI)\b",
    re.I,
)
_PRIVATE_LABEL_RE = re.compile(
    r"\b(?:PRIVATE[_ ]*ONLY|INTERNAL[_ ]*PROVENANCE|INTERNAL[_ ]*NUMBERS[_ ]*ONLY|"
    r"BROKER[_ ]*PROXY[_ ]*RAW[_ ]*PRIVATE|CODEX[_ ]*DIGEST[_ ]*INTERNAL|"
    r"DEMO[_ ]*DERIVED[_ ]*PRIVATE|PUBLIC[_ ]*EXPORT[_ ]*FORBIDDEN)\b",
    re.I,
)

# PublicOddsLeakCheckV1 / CC-791 / CC-788 / CC-817 unnamed market-odds & policy-move % detectors.
_OWN_ESTIMATE_SHIFT_RE = re.compile(
    r"Capital Chronicle(?:'s|’s)\s+estimate\s+for\s+the\s+(?:base|bull|bear|alternative)\s+case\s+"
    r"shifted\s+(?:sharply|materially)\s+(?:higher|lower)\s+to\s+\d+(?:\.\d+)?%",
    re.I,
)
_OWN_CASE_SHORT_RE = re.compile(
    r"\b(?:Base|Bull|Bear|Alternative)\s+case\s*\(\d+(?:\.\d+)?%\)",
    re.I,
)
_PRICED_AT_PCT_RE = re.compile(
    r"\b(?:priced(?:\s+in)?|pricing|implies?|implied)\s+(?:at|near|around|above|below|over|under)?\s*"
    r"\d+(?:\.\d+)?(?:\s*[-\u2013]\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)"
    r"|(?<!\w)\d+(?:\.\d+)?(?:\s*[-\u2013]\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)\s*(?:priced(?:\s+in)?|odds|chance|probability)\b"
    r"|(?<!\w)\d+(?:\.\d+)?(?:\s*[-\u2013]\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)\s+implied\b"
    r"(?!\s+(?:day|daily|move|vol|volatility|range|swing|yield|rate|inflation)\b)",
    re.I,
)
_POLICY_MOVE_PCT_RE = re.compile(
    r"\b(?:Federal\s+Reserve|Fed|FOMC|ECB|BoJ|BoE)\b[^.!?;]{0,90}\bfutures\b[^.!?;]{0,60}"
    r"\b(?:hike|cut|hold|rise|pause|easing|tightening|quarter-point)\b[^.!?;]{0,40}"
    r"(?<!\bto\s)(?<!\w)\d+(?:\.\d+)?(?:\s*[-\u2013]\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)"
    r"(?!\s*(?:yield|inflation|cpi|pce|gdp)\b)"
    r"|\b(?:Federal\s+Reserve|Fed|FOMC|ECB|BoJ|BoE)\s+(?:rate\s+)?(?:hike|cut|hold|pause)\s+"
    r"(?:(?:at|near|around|of|priced(?:\s+at)?)\s+|[:=]\s*)"
    r"\d+(?:\.\d+)?(?:\s*[-\u2013]\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)"
    r"|(?<!\w)\d+(?:\.\d+)?(?:\s*[-\u2013]\s*\d+(?:\.\d+)?)?\s*(?:%|percent\b)\s+"
    r"(?:(?:for|of|on)\s+)?(?:(?:a|an|the)\s+)?"
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?"
    r"(?:Federal\s+Reserve|Fed|FOMC|ECB|BoJ|BoE)\s+(?:rate\s+)?(?:hike|cut|hold|pause)\b",
    re.I,
)
_NUMERIC_GAP_PP_RE = re.compile(r"\bgap_pp\s*[:=]?\s*[+-]?\d+(?:\.\d+)?\b", re.I)
_ODDS_PCT_OR_CENTS_RE = re.compile(
    r"(?<!\w)\d+(?:\.\d+)?\s*(?:%|percent\b|percentage\s+points?\b|p\.?p\.?\b|\u00a2|cents?\b)",
    re.I,
)

# ---------------------------------------------------------------------------
# (b) FREE_ONLY_MODE Paywall / Paid-Tier / Subscription-Gate Patterns
# ---------------------------------------------------------------------------

_PAID_AUDIENCE_VALUES = frozenset({
    "only_paid",
    "paid",
    "paid_only",
    "paid_subscribers",
    "paid_members",
    "paid_tier",
    "paid_research_tier",
    "founding",
    "founding_members",
    "premium",
    "vip",
    "telegram_vip",
    "members_only",
    "subscriber_only",
    "paywalled",
    "paywall",
})
_PAID_BOOLEAN_KEYS = frozenset({
    "paywall",
    "is_paid",
    "paid_only",
    "paid_tier",
    "paid_tier_enabled",
    "subscription_gate",
    "requires_subscription",
    "subscriber_only",
    "monetization_enabled",
    "checkout_enabled",
    "paywall_enabled",
})
_PAID_PRICE_KEYS = frozenset({
    "price_usd",
    "subscription_price_usd",
    "monthly_price_usd",
    "annual_price_usd",
    "fee_usd",
    "tier_price_usd",
})
_PAYWALL_TEXT_RE = re.compile(
    r"<!--\s*paywall\s*-->"
    r"|<!--\s*paid\b[^>]*-->"
    r"|\[paywall\]"
    r"|class\s*=\s*[\"'][^\"']*paywall[^\"']*[\"']"
    r"|data-paywall\b"
    r"|/subscribe\?next="
    r"|\bpaid\s+subscribers?\s+only\b"
    r"|\bfor\s+paid\s+subscribers?\b"
    r"|\bupgrade\s+to\s+paid\b"
    r"|\bunlock\s+(?:full\s+access|this\s+post|the\s+rest|paid)\b"
    r"|\bbehind\s+(?:the|a|our)\s+paywall\b"
    r"|\bsubscribe\s+to\s+unlock\b"
    r"|\bbecome\s+a\s+paid\s+(?:subscriber|member)\b"
    r"|\bpaid\s+research\s+tier\b"
    r"|\b(?:paid|premium|vip)\s+tier\b"
    r"|\btelegram\s+vip\b"
    r"|\bsubscription[- ]gate[ds]?\b"
    r"|\bmonthly\s+subscription\b"
    r"|\bsubscribe\s+for\s+\$\d+"
    r"|\$\d+(?:\.\d{2})?\s*/\s*(?:mo|month|yr|year)\b"
    r"|\b(?:checkout|buy)\.stripe\.com\b"
    r"|\b(?:whop|lemonsqueezy|patreon|memberful)\.com\b"
    r"|\bmql5\.com(?:/en)?/signals\b"
    r"|\bexness\b[^.\n]{0,40}\b(?:partner|referral|social\s+trading)\b",
    re.I,
)

# ---------------------------------------------------------------------------
# (c) Retired Claude / AGY Runtime Command & Config Patterns
# ---------------------------------------------------------------------------

# Exact permanent historical workspace directory names / disable flags that do NOT represent
# active Claude CLI/API dependencies (Decision 184 / CC-855).
_HARMLESS_CLAUDE_LEGACY_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?:claude-main-research|claude-ops-integrations|claude-main-events)(?![A-Za-z0-9_-])"
    r"|--no-claude-cli-login(?![A-Za-z0-9_-])",
    re.I,
)
_CLAUDE_CMD_RE = re.compile(
    r"(?<![A-Za-z0-9])claude(?:\.exe)?(?![A-Za-z0-9])"
    r"|\bCLAUDE_CODE_SESSION\b|\bNATIVE_CLAUDE_CODE\b"
    r"|\bclaude[-_]?(?:opus|sonnet|haiku|code|desktop|cli|legacy|api|poster|runner|agent|messages)\b"
    r"|(?<![A-Za-z0-9])anthropic(?![A-Za-z0-9])",
    re.I,
)
_AGY_CMD_RE = re.compile(
    r"(?<![A-Za-z0-9])agy(?:\.exe)?(?![A-Za-z0-9])"
    r"|(?<![A-Za-z0-9])antigravity(?:[-_]?cli)?(?![A-Za-z0-9])"
    r"|\bROUTE_AGY\b",
    re.I,
)


def _has_active_claude_ref(text: str) -> bool:
    cleaned = _HARMLESS_CLAUDE_LEGACY_PATH_RE.sub(" ", _normalize_text(text))
    return bool(_CLAUDE_CMD_RE.search(cleaned))


def _has_active_agy_ref(text: str) -> bool:
    return bool(_AGY_CMD_RE.search(_normalize_text(text)))


_STALE_PRE_DEC15_CAUSE_RE = re.compile(
    r"UNTIL_202611(?:2[3-9]|30)|UNTIL_202612(?:0\d|1[0-4])",
    re.I,
)


class FreeTierFirewallError(ValueError):
    """Fail-closed exception raised when any FREE-only / CC-024 / V2.1-C6 gate fails."""

    def __init__(
        self,
        reason_code: str,
        *,
        violations: Sequence[Mapping[str, Any]] = (),
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.reason_code = str(reason_code)
        self.violations = [dict(v) for v in violations]
        self.details = dict(details or {})
        super().__init__(self.reason_code)


# ---------------------------------------------------------------------------
# Strict Canonical JSON, Finite Numbers, Clocks, and Rule A3 Guards
# ---------------------------------------------------------------------------


def canonical_json(value: Any) -> str:
    """Deterministic compact UTF-8 canonical JSON rejecting NaN/Infinity and non-JSON types."""
    assert_no_nonfinite_numbers(value, path="$")
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise FreeTierFirewallError(
            "NON_CANONICAL_JSON_VALUE",
            violations=[{"code": "NON_CANONICAL_JSON_VALUE", "location": "$", "detail": type(exc).__name__}],
        ) from exc


def sha256_canonical(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_strict_json_bytes(
    raw: bytes,
    *,
    label: str = "input",
    forbid_cr_bom: bool = False,
) -> Any:
    """Parse JSON bytes strictly: rejects UTF-8 errors, duplicate keys, NaN/Infinity, and optional CR/BOM."""
    if not isinstance(raw, (bytes, bytearray)):
        raise FreeTierFirewallError(
            "MALFORMED_JSON_BYTES_REQUIRED",
            violations=[{"code": "MALFORMED_JSON_BYTES_REQUIRED", "location": label}],
        )
    data = bytes(raw)
    if forbid_cr_bom:
        if data.startswith(b"\xef\xbb\xbf"):
            raise FreeTierFirewallError(
                "UTF8_BOM_FORBIDDEN",
                violations=[{"code": "UTF8_BOM_FORBIDDEN", "location": label}],
            )
        if b"\r" in data:
            raise FreeTierFirewallError(
                "CR_BYTES_FORBIDDEN",
                violations=[{"code": "CR_BYTES_FORBIDDEN", "location": label}],
            )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FreeTierFirewallError(
            "INVALID_UTF8_INPUT",
            violations=[{"code": "INVALID_UTF8_INPUT", "location": label}],
        ) from exc

    def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, val in pairs:
            if key in out:
                raise FreeTierFirewallError(
                    "DUPLICATE_JSON_KEY",
                    violations=[{"code": "DUPLICATE_JSON_KEY", "location": f"{label}.{key}"}],
                )
            out[key] = val
        return out

    def _no_nonfinite_constant(token: str) -> Any:
        raise FreeTierFirewallError(
            "NONFINITE_NUMBER_FORBIDDEN",
            violations=[{"code": "NONFINITE_NUMBER_FORBIDDEN", "location": label, "token": token}],
        )

    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_no_nonfinite_constant,
        )
    except FreeTierFirewallError:
        raise
    except ValueError as exc:
        raise FreeTierFirewallError(
            "MALFORMED_JSON_INPUT",
            violations=[{"code": "MALFORMED_JSON_INPUT", "location": label}],
        ) from exc

    assert_no_nonfinite_numbers(parsed, path=label)
    return parsed


def assert_no_nonfinite_numbers(value: Any, *, path: str = "$") -> None:
    """Recursively fail closed on NaN, +Inf, or -Inf in float/Decimal values."""
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise FreeTierFirewallError(
                "NONFINITE_NUMBER_FORBIDDEN",
                violations=[{"code": "NONFINITE_NUMBER_FORBIDDEN", "location": path, "value": repr(value)}],
            )
        return
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise FreeTierFirewallError(
                "NONFINITE_NUMBER_FORBIDDEN",
                violations=[{"code": "NONFINITE_NUMBER_FORBIDDEN", "location": path, "value": str(value)}],
            )
        return
    if isinstance(value, Mapping):
        for k, v in value.items():
            if not isinstance(k, str):
                raise FreeTierFirewallError(
                    "NON_STRING_MAPPING_KEY",
                    violations=[{"code": "NON_STRING_MAPPING_KEY", "location": path}],
                )
            assert_no_nonfinite_numbers(v, path=f"{path}.{k}")
        return
    if isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            assert_no_nonfinite_numbers(item, path=f"{path}[{idx}]")


def assert_no_silent_waivers(value: Any, *, path: str = "$") -> None:
    """Rule A3: fail closed if any silent waiver / bypass / override key is supplied."""
    if isinstance(value, Mapping):
        for k, v in value.items():
            k_norm = str(k).strip().lower()
            if k_norm in _SILENT_WAIVER_KEYS:
                if v is not None and v is not False and v != [] and v != {} and v != "":
                    raise FreeTierFirewallError(
                        "SILENT_WAIVER_FORBIDDEN_RULE_A3",
                        violations=[{"code": "SILENT_WAIVER_FORBIDDEN_RULE_A3", "location": f"{path}.{k}"}],
                    )
                # Even an explicit falsy waiver key on a security-critical contract is disallowed when named waiver/skip.
                if k_norm in {"waiver", "waivers", "silent_waiver"} and v is not None:
                    raise FreeTierFirewallError(
                        "SILENT_WAIVER_FORBIDDEN_RULE_A3",
                        violations=[{"code": "SILENT_WAIVER_FORBIDDEN_RULE_A3", "location": f"{path}.{k}"}],
                    )
            assert_no_silent_waivers(v, path=f"{path}.{k}")
    elif isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            assert_no_silent_waivers(item, path=f"{path}[{idx}]")


def parse_strict_utc(
    value: Any,
    *,
    field_name: str,
    max_clock_utc: datetime | None = None,
) -> datetime:
    """Parse an explicit timezone-aware ISO-8601 UTC/offset instant; reject naive/date-only/bool/future/out-of-range."""
    if isinstance(value, bool) or value is None:
        raise FreeTierFirewallError(
            "UTC_CLOCK_REQUIRED",
            violations=[{"code": "UTC_CLOCK_REQUIRED", "location": field_name}],
        )
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise FreeTierFirewallError(
                "UTC_CLOCK_NAIVE_FORBIDDEN",
                violations=[{"code": "UTC_CLOCK_NAIVE_FORBIDDEN", "location": field_name}],
            )
        try:
            parsed = value.astimezone(UTC)
        except OverflowError as exc:
            raise FreeTierFirewallError(
                "UTC_CLOCK_OUT_OF_RANGE",
                violations=[{"code": "UTC_CLOCK_OUT_OF_RANGE", "location": field_name}],
            ) from exc
    elif isinstance(value, str):
        cleaned = value.strip()
        if not cleaned or not _ISO_DATETIME_RE.fullmatch(cleaned):
            raise FreeTierFirewallError(
                "UTC_CLOCK_INVALID_FORMAT",
                violations=[{"code": "UTC_CLOCK_INVALID_FORMAT", "location": field_name}],
            )
        try:
            parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except ValueError as exc:
            raise FreeTierFirewallError(
                "UTC_CLOCK_INVALID_FORMAT",
                violations=[{"code": "UTC_CLOCK_INVALID_FORMAT", "location": field_name}],
            ) from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise FreeTierFirewallError(
                "UTC_CLOCK_NAIVE_FORBIDDEN",
                violations=[{"code": "UTC_CLOCK_NAIVE_FORBIDDEN", "location": field_name}],
            )
        try:
            parsed = parsed.astimezone(UTC)
        except OverflowError as exc:
            raise FreeTierFirewallError(
                "UTC_CLOCK_OUT_OF_RANGE",
                violations=[{"code": "UTC_CLOCK_OUT_OF_RANGE", "location": field_name}],
            ) from exc
    else:
        raise FreeTierFirewallError(
            "UTC_CLOCK_INVALID_TYPE",
            violations=[{"code": "UTC_CLOCK_INVALID_TYPE", "location": field_name}],
        )

    if max_clock_utc is not None:
        if not isinstance(max_clock_utc, datetime) or max_clock_utc.tzinfo is None or max_clock_utc.utcoffset() is None:
            raise FreeTierFirewallError(
                "UTC_CLOCK_NAIVE_FORBIDDEN",
                violations=[{"code": "UTC_CLOCK_NAIVE_FORBIDDEN", "location": "max_clock_utc"}],
            )
        try:
            max_utc = max_clock_utc.astimezone(UTC)
        except OverflowError as exc:
            raise FreeTierFirewallError(
                "UTC_CLOCK_OUT_OF_RANGE",
                violations=[{"code": "UTC_CLOCK_OUT_OF_RANGE", "location": "max_clock_utc"}],
            ) from exc
        if parsed > max_utc:
            raise FreeTierFirewallError(
                "CLOCK_AFTER_CUTOFF",
                violations=[{
                    "code": "CLOCK_AFTER_CUTOFF",
                    "location": field_name,
                    "observed_utc": _iso_utc(parsed),
                    "max_utc": _iso_utc(max_utc),
                }],
            )
    return parsed


def _iso_utc(dt: datetime) -> str:
    try:
        utc_dt = dt.astimezone(UTC)
    except OverflowError as exc:
        raise FreeTierFirewallError(
            "UTC_CLOCK_OUT_OF_RANGE",
            violations=[{"code": "UTC_CLOCK_OUT_OF_RANGE", "location": "utc"}],
        ) from exc
    return f"{utc_dt.year:04d}-{utc_dt.month:02d}-{utc_dt.day:02d}T{utc_dt.hour:02d}:{utc_dt.minute:02d}:{utc_dt.second:02d}Z"


def _safe_public_date(dt: datetime, *, field_name: str = "as_of_utc") -> str:
    try:
        return public_date(dt)
    except OverflowError as exc:
        raise FreeTierFirewallError(
            "UTC_CLOCK_OUT_OF_RANGE",
            violations=[{"code": "UTC_CLOCK_OUT_OF_RANGE", "location": field_name}],
        ) from exc


def _normalize_text(text: str) -> str:
    if text.isascii():
        return text
    normalized = unicodedata.normalize("NFKC", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Cf")


def _iter_all_strings(node: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, Mapping):
        for k, v in node.items():
            yield from _iter_all_strings(v, f"{path}.{k}")
    elif isinstance(node, (list, tuple)):
        for idx, item in enumerate(node):
            yield from _iter_all_strings(item, f"{path}[{idx}]")


def _should_skip_prose_field(loc: str, key_lower: str | None, value: str) -> bool:
    """Return True ONLY for narrow non-prose technical fields whose values match strict machine shapes."""
    if key_lower is None:
        return False
    stripped = _normalize_text(value).strip()
    if not stripped:
        return True
    if key_lower.endswith("_utc") or key_lower in _NON_PROSE_UTC_KEYS:
        return bool(_ISO_DATETIME_RE.fullmatch(stripped))
    if key_lower in _NON_PROSE_MARKET_CODE_KEYS:
        return bool(_COMPACT_TOKEN_RE.fullmatch(stripped))
    if key_lower in _NON_PROSE_ID_KEYS or key_lower.endswith(_NON_PROSE_ID_SUFFIXES):
        return bool(_COMPACT_TOKEN_RE.fullmatch(stripped))
    if key_lower in _NON_PROSE_URL_KEYS or key_lower.endswith(("_url", "_urls")):
        return bool(_PURE_URL_RE.fullmatch(stripped))
    if key_lower in _LOCAL_FS_PATH_KEYS or key_lower.endswith(("_path", "_dir")):
        return _is_local_filesystem_path(loc, stripped)
    return False


def _iter_display_prose(
    node: Any,
    path: str = "$",
    *,
    key_lower: str | None = None,
) -> Iterable[tuple[str, str]]:
    """Recursively yield ALL outbound display strings, excluding only strict non-prose technical tokens."""
    if isinstance(node, str):
        if not _should_skip_prose_field(path, key_lower, node):
            yield path, node
        return
    if isinstance(node, Mapping):
        for k, v in node.items():
            child_key = str(k).strip().lower()
            yield from _iter_display_prose(v, f"{path}.{k}", key_lower=child_key)
        return
    if isinstance(node, (list, tuple)):
        for idx, item in enumerate(node):
            yield from _iter_display_prose(item, f"{path}[{idx}]", key_lower=key_lower)


_STRIP_URLS_RE = re.compile(r"https?://[^\s<>\"'()\[\]]+")
_SENTENCE_SPLIT_RE = re.compile(r"[\n.!?](?!\d)|;\s*")
_FRED_SRC_BLOB_RE = re.compile(r"\b(?:fred|stlouisfed|st\.?\s*louis)\b", re.I)
_MODALITY_WIDGET_RE = re.compile(r"\b(?:tradingview[_ -]?widget|embed[_ -]?widget|paywall[_ -]?widget)\b", re.I)
_PRICE_PREFIX_RE = re.compile(r"^(?:USD|EUR|GBP|CAD|AUD|CHF)?\s*[$€£]?\s*", re.I)
_PRICE_PERIOD_SUFFIX_RE = re.compile(r"\s*/\s*(?:mo|month|yr|year|wk|week)\b.*$", re.I)
_INTERNAL_MODEL_PHRASES_RE = re.compile(
    r"(?<!\w)(?:"
    + "|".join(
        re.escape(phrase)
        for phrase in INTERNAL_MODEL_AND_CLOCK_PHRASES
        if phrase not in {"GMT+7", "UTC+7"}
    )
    + r")(?!\w)",
    re.I,
)


def _strip_urls(text: str) -> str:
    return _STRIP_URLS_RE.sub(" ", text)


def _safe_num_repr(value: Any) -> str:
    try:
        return str(value)[:80]
    except ValueError:
        return f"<{type(value).__name__}:oversized>"


def _parse_price_string_decimal(value: str) -> Decimal | None:
    cleaned = _normalize_text(value).strip()
    if not cleaned:
        return None
    stripped = _PRICE_PREFIX_RE.sub("", cleaned)
    stripped = _PRICE_PERIOD_SUFFIX_RE.sub("", stripped)
    stripped = stripped.replace(",", "").strip()
    if not stripped:
        return None
    try:
        dec = Decimal(stripped)
    except InvalidOperation:
        return None
    return dec if dec.is_finite() else None


_PAID_TIER_METADATA_EXACT_KEYS = frozenset({
    "audience",
    "visibility",
    "access_tier",
    "tier",
    "paywall_mode",
    "monetization_tier",
    "substack_delivery_mode",
    "operating_tier",
    "unpause_mode",
    "distribution_tier",
})
_PAID_TIER_METADATA_SUFFIXES = (
    "_audience",
    "_tier",
    "_paywall_mode",
    "_delivery_mode",
    "_visibility",
)


# ---------------------------------------------------------------------------
# (b) FREE_ONLY_MODE Guarantee
# ---------------------------------------------------------------------------


def verify_free_only_mode(
    payload: Any,
    *,
    now_utc: datetime | str | None = None,
    path: str = "$",
) -> dict[str, Any]:
    """Guarantee zero paid paywall, paid-tier, checkout, or subscription-gate markers in FREE_ONLY_MODE."""
    if payload is None:
        raise FreeTierFirewallError(
            "OUTBOUND_PAYLOAD_MISSING",
            violations=[{"code": "OUTBOUND_PAYLOAD_MISSING", "location": path}],
        )
    assert_no_nonfinite_numbers(payload, path=path)
    assert_no_silent_waivers(payload, path=path)

    checked_now: datetime | None = None
    if now_utc is not None:
        checked_now = parse_strict_utc(now_utc, field_name="now_utc")

    violations: list[dict[str, str]] = []

    def _walk(node: Any, loc: str) -> None:
        if isinstance(node, Mapping):
            for k, v in node.items():
                key_l = str(k).strip().lower()
                child_loc = f"{loc}.{k}"
                if key_l in _PAID_BOOLEAN_KEYS and v is not False and v is not None:
                    violations.append({
                        "code": "FREE_ONLY_PAYWALL_FLAG_FORBIDDEN",
                        "location": child_loc,
                        "detail": f"{k}={_safe_num_repr(v)}",
                    })
                if (
                    key_l in _PAID_TIER_METADATA_EXACT_KEYS
                    or key_l.endswith(_PAID_TIER_METADATA_SUFFIXES)
                ) and isinstance(v, str):
                    val_l = _normalize_text(v).strip().lower().replace("-", "_").replace(" ", "_")
                    if val_l in _PAID_AUDIENCE_VALUES or "paid" in val_l or "paywall" in val_l or "vip" in val_l:
                        violations.append({
                            "code": "FREE_ONLY_PAID_TIER_METADATA_FORBIDDEN",
                            "location": child_loc,
                            "detail": v.strip()[:80],
                        })
                if key_l in _PAID_PRICE_KEYS:
                    if v is None:
                        pass
                    elif isinstance(v, bool):
                        violations.append({
                            "code": "FREE_ONLY_INVALID_PRICE_TYPE",
                            "location": child_loc,
                        })
                    elif isinstance(v, (int, float, Decimal)):
                        if v != 0:
                            violations.append({
                                "code": "FREE_ONLY_NONZERO_PRICE_FORBIDDEN",
                                "location": child_loc,
                                "detail": _safe_num_repr(v),
                            })
                    elif isinstance(v, str):
                        parsed_price = _parse_price_string_decimal(v)
                        if parsed_price is not None and parsed_price != 0:
                            violations.append({
                                "code": "FREE_ONLY_NONZERO_PRICE_FORBIDDEN",
                                "location": child_loc,
                                "detail": v.strip()[:80],
                            })
                        else:
                            violations.append({
                                "code": "FREE_ONLY_INVALID_PRICE_TYPE",
                                "location": child_loc,
                                "detail": v.strip()[:80],
                            })
                    else:
                        violations.append({
                            "code": "FREE_ONLY_INVALID_PRICE_TYPE",
                            "location": child_loc,
                        })
                _walk(v, child_loc)
        elif isinstance(node, (list, tuple)):
            for idx, item in enumerate(node):
                _walk(item, f"{loc}[{idx}]")
        elif isinstance(node, str):
            text = _normalize_text(node)
            match = _PAYWALL_TEXT_RE.search(text)
            if match:
                violations.append({
                    "code": "FREE_ONLY_PAYWALL_MARKER_FORBIDDEN",
                    "location": loc,
                    "detail": match.group(0)[:80],
                })

    _walk(payload, path)

    if violations:
        raise FreeTierFirewallError(
            violations[0]["code"],
            violations=violations,
            details={"mode": FREE_ONLY_MODE, "paid_tier_earliest_utc": _iso_utc(PAID_TIER_EARLIEST_UTC)},
        )

    return {
        "status": "PASS",
        "mode": FREE_ONLY_MODE,
        "paid_markers_found": 0,
        "checked_at_utc": _iso_utc(checked_now) if checked_now is not None else None,
        "pre_q1_2027_free_lock": checked_now < PAID_TIER_EARLIEST_UTC if checked_now is not None else True,
    }


# ---------------------------------------------------------------------------
# (a) CC-024 Commercial-Rights & Public Compliance Firewall
# ---------------------------------------------------------------------------


_LOCAL_FS_PATH_KEYS = frozenset({
    "path",
    "file_path",
    "output_dir",
    "local_path",
    "png_path",
    "screenshot_path",
    "chart_path",
})
_LOCAL_FS_PATH_VALUE_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|/)")


def _is_local_filesystem_path(loc: str, value: str) -> bool:
    leaf = loc.rsplit(".", 1)[-1].split("[", 1)[0].strip().lower()
    if leaf not in _LOCAL_FS_PATH_KEYS and not leaf.endswith(("_path", "_dir")):
        return False
    stripped = value.strip()
    if not stripped or "\n" in stripped or "\r" in stripped:
        return False
    if stripped.lower().startswith(("http://", "https://")):
        return False
    return bool(_LOCAL_FS_PATH_VALUE_RE.match(stripped))


def _find_ai_model_label(text: str) -> str | None:
    if m := plan_pages._MODELS.search(text):
        return m.group(0)
    if m := _EXTRA_AI_MODEL_RE.search(text):
        return m.group(0)
    if m := _INTERNAL_MODEL_PHRASES_RE.search(text):
        return m.group(0)
    return None


def _find_market_odds_violation(text: str) -> str | None:
    plain_no_links = _strip_urls(text)
    scrubbed = attention._OWN_ESTIMATE_HEADING.sub("Case", plain_no_links)
    scrubbed = _OWN_ESTIMATE_SHIFT_RE.sub("Capital Chronicle estimate shifted", scrubbed)
    scrubbed = _OWN_CASE_SHORT_RE.sub("Case", scrubbed)

    if m := attention._UNNAMED_MARKET_ODDS.search(scrubbed):
        return f"UNNAMED_MARKET_ODDS:{m.group(0)[:60]}"
    if m := _PRICED_AT_PCT_RE.search(scrubbed):
        return f"PRICED_AT_PERCENT:{m.group(0)[:60]}"
    if m := _POLICY_MOVE_PCT_RE.search(scrubbed):
        return f"POLICY_MOVE_PERCENT:{m.group(0)[:60]}"
    if m := _NUMERIC_GAP_PP_RE.search(scrubbed):
        return f"NUMERIC_GAP_PP:{m.group(0)[:60]}"

    for sentence in _SENTENCE_SPLIT_RE.split(scrubbed):
        seg = sentence.strip()
        if not seg:
            continue
        cleaned_seg = event_guard.NAMED_NUMBER.sub(" ", seg)
        if (attention._PREDICTION_WORD.search(seg) or event_guard.ODDS_SOURCE.search(seg)) and (
            _ODDS_PCT_OR_CENTS_RE.search(cleaned_seg) or event_guard._NUMBER.search(cleaned_seg)
        ):
            return f"PREDICTION_MARKET_NUMBER:{seg[:80]}"
    return None


def _find_price_target_violation(text: str) -> str | None:
    try:
        voice.validate_copy(text)
    except ValueError as exc:
        return str(exc)
    if decision_checks.plan_target_present(text):
        return "PUBLIC_PLAN_TARGET_PRESENT"
    return None


def verify_cc024_commercial_firewall(
    payload: Any,
    *,
    private_texts: Sequence[str] = (),
    check_instruments: bool = True,
    check_public_time: bool = True,
    require_notice: bool = False,
    path: str = "$",
) -> dict[str, Any]:
    """Enforce the CC-024 commercial-rights firewall and all five Capital Chronicle public filters."""
    if payload is None:
        raise FreeTierFirewallError(
            "OUTBOUND_PAYLOAD_MISSING",
            violations=[{"code": "OUTBOUND_PAYLOAD_MISSING", "location": path}],
        )
    if isinstance(payload, str) and not payload.strip():
        raise FreeTierFirewallError(
            "OUTBOUND_COPY_EMPTY",
            violations=[{"code": "OUTBOUND_COPY_EMPTY", "location": path}],
        )
    if isinstance(payload, Mapping) and not payload:
        raise FreeTierFirewallError(
            "OUTBOUND_PAYLOAD_EMPTY",
            violations=[{"code": "OUTBOUND_PAYLOAD_EMPTY", "location": path}],
        )

    assert_no_nonfinite_numbers(payload, path=path)
    assert_no_silent_waivers(payload, path=path)

    violations: list[dict[str, str]] = []
    norm_private = [
        " ".join(_normalize_text(str(item)).casefold().split())
        for item in (private_texts or ())
        if isinstance(item, str) and len(" ".join(_normalize_text(item).split())) >= 24
    ]

    # 1. Structural inspection across all dict keys/metadata (catches private containers,
    #    FRED SP500 series objects, OCC/Yahoo GEX provider metadata, and TradingView widgets).
    def _walk_structure(node: Any, loc: str) -> None:
        if isinstance(node, Mapping):
            series_val = str(node.get("series_id") or node.get("series") or "").strip().upper()
            src_blob = " ".join(
                str(node.get(k) or "")
                for k in ("source", "provider", "data_source", "publisher", "attribution", "url", "source_url")
            )
            if series_val == "SP500" and _FRED_SRC_BLOB_RE.search(src_blob):
                violations.append({
                    "code": "CC024_FRED_SP500_FORBIDDEN",
                    "location": loc,
                    "detail": "series_id=SP500",
                })
            modality_blob = " ".join(
                str(node.get(k) or "")
                for k in ("modality", "widget_type", "embed_type", "kind", "type")
            )
            if _MODALITY_WIDGET_RE.search(modality_blob):
                violations.append({
                    "code": "CC024_TRADINGVIEW_WIDGET_FORBIDDEN",
                    "location": loc,
                    "detail": modality_blob.strip()[:80],
                })
            for priv_flag in ("private_only", "public_export_forbidden"):
                if priv_flag in node and node[priv_flag] not in (False, None):
                    violations.append({
                        "code": "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN",
                        "location": f"{loc}.{priv_flag}",
                        "detail": f"{priv_flag}={repr(node[priv_flag])[:40]}",
                    })
            for k, v in node.items():
                k_l = str(k).strip().lower()
                child_loc = f"{loc}.{k}"
                if k_l in _FORBIDDEN_PRIVATE_KEYS:
                    violations.append({
                        "code": "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN",
                        "location": child_loc,
                        "detail": f"forbidden_key:{k}",
                    })
                _walk_structure(v, child_loc)
        elif isinstance(node, (list, tuple)):
            for idx, item in enumerate(node):
                _walk_structure(item, f"{loc}[{idx}]")

    _walk_structure(payload, path)

    # 2. Global string scan across ALL strings (text, URLs, citations, metadata).
    all_strings = list(_iter_all_strings(payload, path))
    if not all_strings:
        raise FreeTierFirewallError(
            "OUTBOUND_COPY_EMPTY",
            violations=[{"code": "OUTBOUND_COPY_EMPTY", "location": path}],
        )

    for loc, raw_text in all_strings:
        text = _normalize_text(raw_text)
        if not text.strip():
            continue

        if m := _INVESTING_MYFXBOOK_RE.search(text):
            violations.append({
                "code": "CC024_INVESTING_OR_MYFXBOOK_FORBIDDEN",
                "location": loc,
                "detail": m.group(0),
            })
        if m := _OCC_YAHOO_GEX_RE.search(text):
            violations.append({
                "code": "CC024_OCC_OR_YAHOO_GEX_FORBIDDEN",
                "location": loc,
                "detail": m.group(0)[:80],
            })
        if m := _FRED_SP500_RE.search(text):
            violations.append({
                "code": "CC024_FRED_SP500_FORBIDDEN",
                "location": loc,
                "detail": m.group(0)[:80],
            })
        if m := _TRADINGVIEW_WIDGET_RE.search(text):
            violations.append({
                "code": "CC024_TRADINGVIEW_WIDGET_FORBIDDEN",
                "location": loc,
                "detail": m.group(0)[:80],
            })
        if m := _RAW_X_OR_WIRE_RE.search(text):
            violations.append({
                "code": "CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN",
                "location": loc,
                "detail": m.group(0)[:80],
            })
        if hit := find_forbidden_link(text):
            violations.append({
                "code": "PREVIEW_HOST_LINK_FORBIDDEN",
                "location": loc,
                "detail": hit,
            })
        if m := plan_pages._SECRET.search(text):
            violations.append({
                "code": "CC024_SECRET_FORBIDDEN",
                "location": loc,
                "detail": "secret_pattern_matched",
            })
        if not _is_local_filesystem_path(loc, text):
            if label := _find_ai_model_label(text):
                violations.append({
                    "code": "CC024_AI_MODEL_LABEL_FORBIDDEN",
                    "location": loc,
                    "detail": label,
                })
        if m := _PRIVATE_LABEL_RE.search(text):
            violations.append({
                "code": "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN",
                "location": loc,
                "detail": m.group(0),
            })

    # 3. Visible public prose scan (recursively scans ALL outbound strings except strict
    #    machine-token technical fields, catching handles, private book/responses, unnamed odds,
    #    price targets, ET clock violations, raw CFD names, verbatim private echoes, and notices).
    prose_items = list(_iter_display_prose(payload, path))

    combined_prose_chunks: list[str] = []
    for loc, raw_text in prose_items:
        text = _normalize_text(raw_text)
        if not text.strip():
            continue
        combined_prose_chunks.append(text)
        plain_no_links = _strip_urls(text)

        if m := attention._X_HANDLE.search(plain_no_links):
            violations.append({
                "code": "CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN",
                "location": loc,
                "detail": m.group(0),
            })
        if norm_private:
            folded = " ".join(text.casefold().split())
            for secret_line in norm_private:
                if secret_line in folded:
                    violations.append({
                        "code": "CC024_RAW_X_LIST_OR_WIRE_FORBIDDEN",
                        "location": loc,
                        "detail": "verbatim_private_text_echo",
                    })
                    break
        if (
            event_guard.public_execution_copy_forbidden(text)
            or plan_pages._PRIVATE.search(text)
            or plan_pages._MONEY.search(text)
            or attention._BOOK_OR_RESPONSE.search(text)
        ):
            violations.append({
                "code": "CC024_PRIVATE_BOOK_OR_RESPONSE_FORBIDDEN",
                "location": loc,
                "detail": "private_book_or_execution_copy",
            })
        if odds_hit := _find_market_odds_violation(text):
            violations.append({
                "code": "CC024_MARKET_ODDS_NUMBER_FORBIDDEN",
                "location": loc,
                "detail": odds_hit,
            })
        if target_hit := _find_price_target_violation(text):
            violations.append({
                "code": "CC024_PRICE_TARGET_FORBIDDEN",
                "location": loc,
                "detail": target_hit,
            })
        if check_public_time:
            if tz_hit := find_forbidden_public_time(text):
                violations.append({
                    "code": "PUBLIC_TIMEZONE_ET_REQUIRED",
                    "location": loc,
                    "detail": tz_hit,
                })
            if clk_hit := attention._NON_ET_CLOCK.search(plain_no_links):
                violations.append({
                    "code": "ATTENTION_MAP_NON_ET_CLOCK_FORBIDDEN",
                    "location": loc,
                    "detail": clk_hit.group(0),
                })
        if check_instruments:
            try:
                instruments.validate_payload(
                    {"public_instrument_policy": instruments.POLICY},
                    {"text": text},
                )
            except ValueError as exc:
                violations.append({
                    "code": "PUBLIC_INSTRUMENT_NAME_FORBIDDEN",
                    "location": loc,
                    "detail": str(exc),
                })

    combined_prose = "\n".join(combined_prose_chunks)
    if require_notice and event_guard.PUBLIC_NOTICE not in combined_prose:
        violations.append({
            "code": "PUBLIC_ANALYSIS_NOTICE_REQUIRED",
            "location": path,
        })

    if violations:
        raise FreeTierFirewallError(
            violations[0]["code"],
            violations=violations,
            details={"violation_count": len(violations)},
        )

    return {
        "status": "PASS",
        "cc024_clean": True,
        "surfaces_checked": len(prose_items),
        "all_strings_checked": len(all_strings),
        "prose_sha256": sha256(combined_prose.encode("utf-8")).hexdigest(),
    }


def verify_outbound_free_payload(
    payload: Any,
    *,
    now_utc: datetime | str,
    destination: str | None = None,
    private_texts: Sequence[str] = (),
    check_instruments: bool = True,
    check_public_time: bool = True,
    require_notice: bool = False,
) -> dict[str, Any]:
    """Unified fail-closed outbound gate: FREE_ONLY_MODE + CC-024 + all 5 public filters."""
    now_dt = parse_strict_utc(now_utc, field_name="now_utc")
    if destination is not None:
        if not isinstance(destination, str) or destination.strip().lower() not in ALL_FREE_DESTINATIONS:
            raise FreeTierFirewallError(
                "FREE_TIER_DESTINATION_INVALID",
                violations=[{"code": "FREE_TIER_DESTINATION_INVALID", "location": "destination", "detail": repr(destination)}],
            )
    free_res = verify_free_only_mode(payload, now_utc=now_dt)
    cc024_res = verify_cc024_commercial_firewall(
        payload,
        private_texts=private_texts,
        check_instruments=check_instruments,
        check_public_time=check_public_time,
        require_notice=require_notice,
    )
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "mode": FREE_ONLY_MODE,
        "destination": destination.strip().lower() if isinstance(destination, str) else None,
        "checked_at_utc": _iso_utc(now_dt),
        "public_write_performed": False,
        "free_only": free_res,
        "cc024": cc024_res,
    }


# ---------------------------------------------------------------------------
# (c.1) V2.1-C6 Day-1 SHA-256 Track-Record Hash Chain & Public Citation Lineage
# ---------------------------------------------------------------------------


def verify_day1_hash_chain(
    records_or_path: Path | str | Sequence[Mapping[str, Any]],
    *,
    max_clock_utc: datetime | str | None = None,
) -> dict[str, Any]:
    """Fail-closed verifier for V2.1-C6 Day-1 SHA-256 hash-chained track-record ledgers.

    Fully compatible with:
      - `L4ShadowSleeveArenaLedgerRecordV1` (Day-1 Shadow Arena ledger JSONL/records)
      - `CapitalChronicleTrackRecordChainV1` (generic SHA-256 chained signal/fill ledger)
    """
    max_dt = parse_strict_utc(max_clock_utc, field_name="max_clock_utc") if max_clock_utc is not None else None
    file_sha256: str | None = None
    rows: list[Mapping[str, Any]] = []

    if isinstance(records_or_path, (Path, str)):
        p = Path(records_or_path)
        if not p.is_file():
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_MISSING",
                violations=[{"code": "TRACK_RECORD_CHAIN_MISSING", "location": str(p)}],
            )
        raw = p.read_bytes()
        if not raw:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_EMPTY",
                violations=[{"code": "TRACK_RECORD_CHAIN_EMPTY", "location": str(p)}],
            )
        if raw.startswith(b"\xef\xbb\xbf"):
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_BOM_FORBIDDEN",
                violations=[{"code": "TRACK_RECORD_CHAIN_BOM_FORBIDDEN", "location": str(p)}],
            )
        if b"\r" in raw:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_CR_FORBIDDEN",
                violations=[{"code": "TRACK_RECORD_CHAIN_CR_FORBIDDEN", "location": str(p)}],
            )
        if not raw.endswith(b"\n"):
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_TRUNCATED",
                violations=[{"code": "TRACK_RECORD_CHAIN_TRUNCATED", "location": str(p)}],
            )
        file_sha256 = sha256(raw).hexdigest()
        for line_no, raw_line in enumerate(raw.splitlines(), start=1):
            parsed = load_strict_json_bytes(raw_line, label=f"chain_line_{line_no}")
            if not isinstance(parsed, Mapping):
                raise FreeTierFirewallError(
                    "TRACK_RECORD_CHAIN_ROW_NOT_OBJECT",
                    violations=[{"code": "TRACK_RECORD_CHAIN_ROW_NOT_OBJECT", "location": f"line:{line_no}"}],
                )
            rows.append(parsed)
    elif isinstance(records_or_path, Sequence) and not isinstance(records_or_path, (bytes, bytearray)):
        if not records_or_path:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_EMPTY",
                violations=[{"code": "TRACK_RECORD_CHAIN_EMPTY", "location": "chain"}],
            )
        for idx, item in enumerate(records_or_path, start=1):
            if not isinstance(item, Mapping):
                raise FreeTierFirewallError(
                    "TRACK_RECORD_CHAIN_ROW_NOT_OBJECT",
                    violations=[{"code": "TRACK_RECORD_CHAIN_ROW_NOT_OBJECT", "location": f"row:{idx}"}],
                )
            assert_no_nonfinite_numbers(item, path=f"chain[{idx}]")
            rows.append(item)
    else:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CHAIN_INVALID_INPUT",
            violations=[{"code": "TRACK_RECORD_CHAIN_INVALID_INPUT", "location": "chain"}],
        )

    expected_prev = GENESIS_PREV_SHA256
    genesis_sha: str | None = None
    seen_ids: set[str] = set()
    detected_schema: str | None = None
    last_cutoff_dt: datetime | None = None
    kind_counts: Counter[str] = Counter()

    for line_no, row in enumerate(rows, start=1):
        loc = f"chain[{line_no}]"
        assert_no_silent_waivers(row, path=loc)

        schema = row.get("schema")
        if schema not in SUPPORTED_CHAIN_SCHEMAS:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_SCHEMA_INVALID",
                violations=[{"code": "TRACK_RECORD_CHAIN_SCHEMA_INVALID", "location": loc, "detail": repr(schema)}],
            )
        if detected_schema is None:
            detected_schema = str(schema)
        elif str(schema) != detected_schema:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_MIXED_SCHEMA",
                violations=[{"code": "TRACK_RECORD_CHAIN_MIXED_SCHEMA", "location": loc}],
            )

        seq = row.get("sequence")
        if type(seq) is not int or seq != line_no:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_SEQUENCE_MISMATCH",
                violations=[{"code": "TRACK_RECORD_CHAIN_SEQUENCE_MISMATCH", "location": loc, "detail": repr(seq)}],
            )

        rec_id = row.get("record_id")
        if not isinstance(rec_id, str) or not rec_id.strip() or rec_id in seen_ids:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_RECORD_ID_INVALID",
                violations=[{"code": "TRACK_RECORD_CHAIN_RECORD_ID_INVALID", "location": loc}],
            )

        cutoff_dt = parse_strict_utc(row.get("cutoff_utc"), field_name=f"{loc}.cutoff_utc", max_clock_utc=max_dt)
        parse_strict_utc(row.get("known_at_max_utc"), field_name=f"{loc}.known_at_max_utc", max_clock_utc=cutoff_dt)
        if last_cutoff_dt is not None and cutoff_dt < last_cutoff_dt:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_CLOCK_NON_MONOTONIC",
                violations=[{"code": "TRACK_RECORD_CHAIN_CLOCK_NON_MONOTONIC", "location": loc}],
            )
        last_cutoff_dt = cutoff_dt

        prev_sha = row.get("prev_record_sha256")
        if not isinstance(prev_sha, str) or prev_sha != expected_prev:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_PREV_SHA_MISMATCH",
                violations=[{"code": "TRACK_RECORD_CHAIN_PREV_SHA_MISMATCH", "location": loc}],
            )

        payload_obj = row.get("payload")
        if not isinstance(payload_obj, Mapping):
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_PAYLOAD_NOT_OBJECT",
                violations=[{"code": "TRACK_RECORD_CHAIN_PAYLOAD_NOT_OBJECT", "location": loc}],
            )
        expected_payload_sha = sha256_canonical(payload_obj)
        if row.get("payload_sha256") != expected_payload_sha:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_PAYLOAD_SHA_MISMATCH",
                violations=[{"code": "TRACK_RECORD_CHAIN_PAYLOAD_SHA_MISMATCH", "location": loc}],
            )

        # Arena ledger Day-1 strict identity & privacy checks (exact parity with l4_shadow_sleeve_arena_v1.py).
        if schema == ARENA_LEDGER_SCHEMA:
            if row.get("private_only") is not True or row.get("public_export_forbidden") is not True:
                raise FreeTierFirewallError(
                    "TRACK_RECORD_CHAIN_ARENA_PRIVACY_TAMPERED",
                    violations=[{"code": "TRACK_RECORD_CHAIN_ARENA_PRIVACY_TAMPERED", "location": loc}],
                )
            kind = str(row.get("record_kind") or "")
            sleeve_id = str(row.get("sleeve_id") or "")
            expected_rec_id = "arena_" + sha256_canonical(
                [seq, kind, sleeve_id, _iso_utc(cutoff_dt), expected_prev, expected_payload_sha]
            )[:24]
            if rec_id != expected_rec_id:
                raise FreeTierFirewallError(
                    "TRACK_RECORD_CHAIN_RECORD_ID_MISMATCH",
                    violations=[{"code": "TRACK_RECORD_CHAIN_RECORD_ID_MISMATCH", "location": loc}],
                )

        envelope = {k: v for k, v in row.items() if k != "record_sha256"}
        expected_rec_sha = sha256_canonical(envelope)
        rec_sha = row.get("record_sha256")
        if not isinstance(rec_sha, str) or not _SHA256_HEX_RE.fullmatch(rec_sha) or rec_sha != expected_rec_sha:
            raise FreeTierFirewallError(
                "TRACK_RECORD_CHAIN_RECORD_SHA_MISMATCH",
                violations=[{"code": "TRACK_RECORD_CHAIN_RECORD_SHA_MISMATCH", "location": loc}],
            )

        if genesis_sha is None:
            genesis_sha = rec_sha
        expected_prev = rec_sha
        seen_ids.add(rec_id)
        if isinstance(row.get("record_kind"), str):
            kind_counts[str(row["record_kind"])] += 1

    return {
        "valid": True,
        "ledger_schema": detected_schema,
        "record_count": len(rows),
        "genesis_record_sha256": genesis_sha,
        "chain_tip_sha256": expected_prev,
        "last_cutoff_utc": _iso_utc(last_cutoff_dt) if last_cutoff_dt is not None else None,
        "kind_counts": dict(sorted(kind_counts.items())),
        "file_sha256": file_sha256,
    }


def build_public_track_record_citation(
    records_or_path: Path | str | Sequence[Mapping[str, Any]],
    *,
    as_of_utc: datetime | str,
    prev_published_tip_sha256: str | None = None,
    summary_lines: Sequence[str] = (),
    include_notices: bool = True,
) -> dict[str, Any]:
    """Construct a sealed public-safe ContentOpsTrackRecordCitationV1 from a verified Day-1 hash chain.

    Exports ONLY the cryptographic SHA-256 chain commitment, record count, ET date,
    and optional verified public summary lines — ZERO private ledger payloads.
    """
    as_of_dt = parse_strict_utc(as_of_utc, field_name="as_of_utc")
    chain_info = verify_day1_hash_chain(records_or_path, max_clock_utc=as_of_dt)

    if prev_published_tip_sha256 is not None:
        if not isinstance(prev_published_tip_sha256, str) or not _SHA256_HEX_RE.fullmatch(prev_published_tip_sha256):
            raise FreeTierFirewallError(
                "TRACK_RECORD_PREV_TIP_INVALID",
                violations=[{"code": "TRACK_RECORD_PREV_TIP_INVALID", "location": "prev_published_tip_sha256"}],
            )

    date_et = _safe_public_date(as_of_dt, field_name="as_of_utc")
    tip = str(chain_info["chain_tip_sha256"])
    genesis = str(chain_info["genesis_record_sha256"])
    count = int(chain_info["record_count"])

    lines: list[str] = [
        f"Capital Chronicle public track-record commitment ({date_et}).",
        f"Verified SHA-256 chain records: {count}.",
        f"Chain tip SHA-256: {tip}.",
        f"Genesis SHA-256: {genesis}.",
    ]
    for raw_line in summary_lines:
        cleaned = " ".join(str(raw_line).strip().split())
        if cleaned:
            lines.append(cleaned)
    if include_notices:
        lines.extend([event_guard.PUBLIC_NOTICE, event_guard.CONFLICTS_NOTICE])
    summary_text = "\n".join(lines)

    body: dict[str, Any] = {
        "schema": TRACK_RECORD_CITATION_SCHEMA,
        "schema_version": TRACK_RECORD_CITATION_SCHEMA_VERSION,
        "mode": FREE_ONLY_MODE,
        "as_of_utc": _iso_utc(as_of_dt),
        "as_of_et": date_et,
        "cutoff_utc": chain_info["last_cutoff_utc"],
        "ledger_schema": chain_info["ledger_schema"],
        "record_count": count,
        "genesis_record_sha256": genesis,
        "chain_tip_sha256": tip,
        "prev_published_tip_sha256": prev_published_tip_sha256,
        "public_summary_text": summary_text,
    }
    citation = {**body, "citation_sha256": sha256_canonical(body)}
    verify_track_record_citation_lineage(
        citation,
        now_utc=as_of_dt,
        chain_records_or_path=records_or_path,
    )
    return citation


def verify_track_record_citation_lineage(
    citation: Any,
    *,
    now_utc: datetime | str,
    chain_records_or_path: Path | str | Sequence[Mapping[str, Any]] | None = None,
    private_texts: Sequence[str] = (),
) -> dict[str, Any]:
    """Fail-closed verifier for public V2.1-C6 SHA-256 track-record citation lineage."""
    now_dt = parse_strict_utc(now_utc, field_name="now_utc")
    if not isinstance(citation, Mapping):
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_OBJECT_REQUIRED",
            violations=[{"code": "TRACK_RECORD_CITATION_OBJECT_REQUIRED", "location": "citation"}],
        )
    assert_no_nonfinite_numbers(citation, path="citation")
    assert_no_silent_waivers(citation, path="citation")

    if citation.get("schema") != TRACK_RECORD_CITATION_SCHEMA:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_SCHEMA_INVALID",
            violations=[{"code": "TRACK_RECORD_CITATION_SCHEMA_INVALID", "location": "citation.schema"}],
        )
    if citation.get("schema_version") != TRACK_RECORD_CITATION_SCHEMA_VERSION:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_VERSION_INVALID",
            violations=[{"code": "TRACK_RECORD_CITATION_VERSION_INVALID", "location": "citation.schema_version"}],
        )
    if citation.get("mode") != FREE_ONLY_MODE:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_FREE_MODE_REQUIRED",
            violations=[{"code": "TRACK_RECORD_CITATION_FREE_MODE_REQUIRED", "location": "citation.mode"}],
        )

    as_of_dt = parse_strict_utc(citation.get("as_of_utc"), field_name="citation.as_of_utc", max_clock_utc=now_dt)
    cutoff_dt = parse_strict_utc(citation.get("cutoff_utc"), field_name="citation.cutoff_utc", max_clock_utc=as_of_dt)
    expected_as_of_et = _safe_public_date(as_of_dt, field_name="citation.as_of_utc")
    if citation.get("as_of_et") != expected_as_of_et:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_DATE_ET_MISMATCH",
            violations=[{
                "code": "TRACK_RECORD_CITATION_DATE_ET_MISMATCH",
                "location": "citation.as_of_et",
                "expected": expected_as_of_et,
                "observed": repr(citation.get("as_of_et")),
            }],
        )

    ledger_schema = citation.get("ledger_schema")
    if ledger_schema not in SUPPORTED_CHAIN_SCHEMAS:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_LEDGER_SCHEMA_INVALID",
            violations=[{"code": "TRACK_RECORD_CITATION_LEDGER_SCHEMA_INVALID", "location": "citation.ledger_schema"}],
        )

    count = citation.get("record_count")
    if type(count) is not int or count < 1:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_COUNT_INVALID",
            violations=[{"code": "TRACK_RECORD_CITATION_COUNT_INVALID", "location": "citation.record_count"}],
        )

    genesis = citation.get("genesis_record_sha256")
    tip = citation.get("chain_tip_sha256")
    if not isinstance(genesis, str) or not _SHA256_HEX_RE.fullmatch(genesis):
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_GENESIS_INVALID",
            violations=[{"code": "TRACK_RECORD_CITATION_GENESIS_INVALID", "location": "citation.genesis_record_sha256"}],
        )
    if not isinstance(tip, str) or not _SHA256_HEX_RE.fullmatch(tip):
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_TIP_INVALID",
            violations=[{"code": "TRACK_RECORD_CITATION_TIP_INVALID", "location": "citation.chain_tip_sha256"}],
        )
    if count == 1 and tip != genesis:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_SINGLE_RECORD_TIP_MISMATCH",
            violations=[{"code": "TRACK_RECORD_CITATION_SINGLE_RECORD_TIP_MISMATCH", "location": "citation.chain_tip_sha256"}],
        )
    if count > 1 and tip == genesis:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_STALE_GENESIS_TIP",
            violations=[{"code": "TRACK_RECORD_CITATION_STALE_GENESIS_TIP", "location": "citation.chain_tip_sha256"}],
        )

    prev_tip = citation.get("prev_published_tip_sha256")
    if prev_tip is not None:
        if not isinstance(prev_tip, str) or not _SHA256_HEX_RE.fullmatch(prev_tip):
            raise FreeTierFirewallError(
                "TRACK_RECORD_CITATION_PREV_TIP_INVALID",
                violations=[{"code": "TRACK_RECORD_CITATION_PREV_TIP_INVALID", "location": "citation.prev_published_tip_sha256"}],
            )

    claimed_seal = citation.get("citation_sha256")
    body = {k: v for k, v in citation.items() if k != "citation_sha256"}
    expected_seal = sha256_canonical(body)
    if not isinstance(claimed_seal, str) or not _SHA256_HEX_RE.fullmatch(claimed_seal) or claimed_seal != expected_seal:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_SEAL_MISMATCH",
            violations=[{"code": "TRACK_RECORD_CITATION_SEAL_MISMATCH", "location": "citation.citation_sha256"}],
        )

    summary_text = citation.get("public_summary_text")
    if not isinstance(summary_text, str) or not summary_text.strip():
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_SUMMARY_REQUIRED",
            violations=[{"code": "TRACK_RECORD_CITATION_SUMMARY_REQUIRED", "location": "citation.public_summary_text"}],
        )
    if tip not in summary_text:
        raise FreeTierFirewallError(
            "TRACK_RECORD_CITATION_TIP_NOT_IN_PUBLIC_COPY",
            violations=[{"code": "TRACK_RECORD_CITATION_TIP_NOT_IN_PUBLIC_COPY", "location": "citation.public_summary_text"}],
        )

    # Ensure the citation itself obeys FREE_ONLY_MODE + CC-024 + public filters.
    verify_outbound_free_payload(
        citation,
        now_utc=now_dt,
        private_texts=private_texts,
        check_instruments=True,
        check_public_time=True,
        require_notice=True,
    )

    chain_verified: dict[str, Any] | None = None
    if chain_records_or_path is not None:
        chain_verified = verify_day1_hash_chain(chain_records_or_path, max_clock_utc=now_dt)
        if (
            chain_verified["ledger_schema"] != ledger_schema
            or chain_verified["record_count"] != count
            or chain_verified["genesis_record_sha256"] != genesis
            or chain_verified["chain_tip_sha256"] != tip
            or chain_verified["last_cutoff_utc"] != _iso_utc(cutoff_dt)
        ):
            raise FreeTierFirewallError(
                "TRACK_RECORD_CITATION_CHAIN_MISMATCH",
                violations=[{"code": "TRACK_RECORD_CITATION_CHAIN_MISMATCH", "location": "citation"}],
            )

    return {
        "status": "PASS",
        "ledger_schema": ledger_schema,
        "record_count": count,
        "genesis_record_sha256": genesis,
        "chain_tip_sha256": tip,
        "citation_sha256": expected_seal,
        "chain_cross_verified": chain_verified is not None,
    }


# ---------------------------------------------------------------------------
# (c.2) Zero Active Claude / AGY Runtime Dependencies Post-04 Dec (CC-855)
# ---------------------------------------------------------------------------


def verify_zero_claude_and_agy_dependencies(
    *,
    now_utc: datetime | str,
    runtime_config: Mapping[str, Any] | None = None,
    control_dir: Path | str | None = None,
    scheduled_tasks: Sequence[Mapping[str, Any]] | None = None,
    editorial_agent: str | None = None,
    digest_driver: str | None = None,
    live_provider: str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Verify zero active Claude, Anthropic, or Antigravity (`agy`) runtime dependencies post-04 Dec."""
    now_dt = parse_strict_utc(now_utc, field_name="now_utc")
    if runtime_config is not None:
        if not isinstance(runtime_config, Mapping):
            raise FreeTierFirewallError(
                "RUNTIME_CONFIG_OBJECT_REQUIRED",
                violations=[{"code": "RUNTIME_CONFIG_OBJECT_REQUIRED", "location": "runtime_config"}],
            )
        assert_no_nonfinite_numbers(runtime_config, path="runtime_config")
        assert_no_silent_waivers(runtime_config, path="runtime_config")
    if scheduled_tasks is not None:
        if not isinstance(scheduled_tasks, Sequence) or isinstance(scheduled_tasks, (str, bytes)):
            raise FreeTierFirewallError(
                "SCHEDULED_TASKS_SEQUENCE_REQUIRED",
                violations=[{"code": "SCHEDULED_TASKS_SEQUENCE_REQUIRED", "location": "scheduled_tasks"}],
            )
        assert_no_nonfinite_numbers(scheduled_tasks, path="scheduled_tasks")
        assert_no_silent_waivers(scheduled_tasks, path="scheduled_tasks")

    violations: list[dict[str, str]] = []
    sunset_active = native_editorial.claude_sunset_active(now_dt, env=env)

    # 1. Confirm CC-801 / Decision 168 AGY_TERMS_BLOCK is live in code.
    if not agy_assist.AGY_TERMS_BLOCK or not agy_assist.agy_blocked("agy.exe"):
        violations.append({
            "code": "AGY_TERMS_BLOCK_INACTIVE",
            "location": "agy_editorial_assist_v1",
        })
    runner_probe = agy_neo.AgyRunner(Path("agy.exe"))
    if runner_probe.blocked_cause() != agy_assist.AGY_TERMS_BLOCK:
        violations.append({
            "code": "AGY_RUNNER_GUARD_INACTIVE",
            "location": "agy_neo_answerer_v1",
        })

    # 2. Confirm agy_neo_routes.json is absent in control_dir if supplied.
    if control_dir is not None:
        ctrl = Path(control_dir)
        agy_routes = ctrl / "agy_neo_routes.json"
        if agy_routes.exists():
            violations.append({
                "code": "AGY_NEO_ROUTES_PRESENT_FORBIDDEN_CC801",
                "location": str(agy_routes),
            })

    # 3. Validate editorial_agent, digest_driver, and live_provider bindings.
    if editorial_agent is not None:
        try:
            native_editorial.assert_new_editorial_agent_allowed(editorial_agent, now=now_dt, env=env)
        except ValueError as exc:
            violations.append({
                "code": str(exc),
                "location": "editorial_agent",
                "detail": str(editorial_agent),
            })

    if digest_driver is not None:
        if not isinstance(digest_driver, str) or not digest_driver.strip():
            violations.append({
                "code": "DIGEST_1900_DRIVER_INVALID",
                "location": "digest_driver",
                "detail": repr(digest_driver),
            })
        else:
            drv = _normalize_text(digest_driver).strip().lower()
            if drv in {"agy", "antigravity", "antigravity-cli"} or _has_active_agy_ref(drv):
                violations.append({"code": agy_assist.AGY_TERMS_BLOCK, "location": "digest_driver", "detail": drv})
            elif drv in FORBIDDEN_RETIRED_DRIVERS or _has_active_claude_ref(drv):
                violations.append({"code": "CLAUDE_ROUTE_RETIRED_CC855", "location": "digest_driver", "detail": drv})
            elif drv not in ALLOWED_POST_DEC04_DIGEST_DRIVERS:
                violations.append({
                    "code": "DIGEST_1900_DRIVER_INVALID",
                    "location": "digest_driver",
                    "detail": drv,
                })

    if live_provider is not None:
        if not isinstance(live_provider, str) or not live_provider.strip():
            violations.append({
                "code": "LIVE_PROVIDER_INVALID",
                "location": "live_provider",
                "detail": repr(live_provider),
            })
        else:
            prov = _normalize_text(live_provider).strip().lower()
            if prov in {"agy", "antigravity", "antigravity-cli"} or _has_active_agy_ref(prov):
                violations.append({
                    "code": agy_assist.AGY_TERMS_BLOCK,
                    "location": "live_provider",
                    "detail": prov,
                })
            elif prov in {"anthropic", "claude"} or prov in FORBIDDEN_RETIRED_DRIVERS or _has_active_claude_ref(prov):
                violations.append({
                    "code": v6_engine.ANTHROPIC_PROVIDER_RETIRED,
                    "location": "live_provider",
                    "detail": prov,
                })

    # 4. Scan runtime_config for any active agy or post-04-Dec Claude/Anthropic binding.
    if runtime_config is not None:
        for loc, text in _iter_all_strings(runtime_config, "runtime_config"):
            if _has_active_agy_ref(text):
                violations.append({
                    "code": "ACTIVE_AGY_DEPENDENCY_FORBIDDEN",
                    "location": loc,
                    "detail": text[:80],
                })
            if sunset_active and _has_active_claude_ref(text):
                violations.append({
                    "code": "ACTIVE_CLAUDE_DEPENDENCY_FORBIDDEN",
                    "location": loc,
                    "detail": text[:80],
                })

    # 5. Scan ALL string fields of every enabled scheduled task for active agy / Claude invocations.
    checked_tasks = 0
    for idx, task in enumerate(scheduled_tasks or ()):
        if not isinstance(task, Mapping):
            violations.append({
                "code": "SCHEDULED_TASK_OBJECT_REQUIRED",
                "location": f"scheduled_tasks[{idx}]",
            })
            continue
        checked_tasks += 1
        enabled = task.get("enabled")
        if not isinstance(enabled, bool):
            violations.append({
                "code": "SCHEDULED_TASK_ENABLED_BOOL_REQUIRED",
                "location": f"scheduled_tasks[{idx}].enabled",
            })
            continue
        if not enabled:
            continue
        task_name = str(task.get("name") or f"task_{idx}")
        for loc, text in _iter_all_strings(task, f"scheduled_tasks[{task_name}]"):
            if _has_active_agy_ref(text):
                violations.append({
                    "code": "ACTIVE_AGY_SCHEDULED_TASK_FORBIDDEN",
                    "location": loc,
                    "detail": text[:100],
                })
            if sunset_active and _has_active_claude_ref(text):
                violations.append({
                    "code": "ACTIVE_CLAUDE_SCHEDULED_TASK_FORBIDDEN",
                    "location": loc,
                    "detail": text[:100],
                })

    if violations:
        raise FreeTierFirewallError(
            violations[0]["code"],
            violations=violations,
            details={"claude_sunset_active": sunset_active, "checked_tasks": checked_tasks},
        )

    return {
        "status": "PASS",
        "claude_sunset_utc": _iso_utc(POST_DEC04_CLAUDE_SUNSET_UTC),
        "claude_sunset_active": sunset_active,
        "agy_terms_block_active": True,
        "active_claude_dependencies": 0,
        "active_agy_dependencies": 0,
        "checked_tasks": checked_tasks,
    }


# ---------------------------------------------------------------------------
# (d) Pause Manifest Validation & Unified ~15 Dec Unpause Preflight
# ---------------------------------------------------------------------------


def _load_pause_manifest_object(
    manifest_or_path: Path | str | Mapping[str, Any],
) -> tuple[Mapping[str, Any], str, Path | None]:
    """Load and structurally validate raw pause manifest bytes or mapping."""
    if isinstance(manifest_or_path, (Path, str)):
        p = Path(manifest_or_path)
        manifest_source = str(p)
        if not p.is_file():
            raise FreeTierFirewallError(
                "PAUSE_MANIFEST_MISSING",
                violations=[{"code": "PAUSE_MANIFEST_MISSING", "location": manifest_source}],
            )
        raw = p.read_bytes()
        # Accept UTF-8 with or without BOM for existing Windows-authored manifests, but reject NaN/dup keys.
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        parsed = load_strict_json_bytes(raw, label="pause_manifest")
        manifest_parent: Path | None = p.parent
    elif isinstance(manifest_or_path, Mapping):
        manifest_source = "in_memory_manifest"
        parsed = manifest_or_path
        assert_no_nonfinite_numbers(parsed, path="pause_manifest")
        manifest_parent = None
    else:
        raise FreeTierFirewallError(
            "PAUSE_MANIFEST_MISSING",
            violations=[{"code": "PAUSE_MANIFEST_MISSING", "location": "pause_manifest"}],
        )

    if not isinstance(parsed, Mapping):
        raise FreeTierFirewallError(
            "PAUSE_MANIFEST_OBJECT_REQUIRED",
            violations=[{"code": "PAUSE_MANIFEST_OBJECT_REQUIRED", "location": "pause_manifest"}],
        )
    return parsed, manifest_source, manifest_parent


def verify_pause_manifest_for_dec15_unpause(
    manifest_or_path: Path | str | Mapping[str, Any],
    *,
    now_utc: datetime | str,
    control_dir: Path | str | None = None,
    min_unpause_utc: datetime | str = DEC15_FREE_UNPAUSE_EARLIEST_UTC,
    allow_already_restored: bool = False,
) -> dict[str, Any]:
    """Fail closed on missing/malformed/stale pause manifests or premature pre-15-Dec unpause."""
    now_dt = parse_strict_utc(now_utc, field_name="now_utc")
    min_unpause_dt = parse_strict_utc(min_unpause_utc, field_name="min_unpause_utc")

    parsed, manifest_source, manifest_parent = _load_pause_manifest_object(manifest_or_path)
    assert_no_silent_waivers(parsed, path="pause_manifest")

    # Enforce FREE_ONLY_MODE on the pause manifest itself (reject paywall flags, paid tiers, non-zero prices).
    verify_free_only_mode(parsed, now_utc=now_dt, path="pause_manifest")

    violations: list[dict[str, str]] = []
    required_keys = (
        "authority",
        "paused_at_utc",
        "resume_at_utc",
        "cause",
        "suspended_destinations",
        "tasks",
        "stop_files",
    )
    for key in required_keys:
        if key not in parsed or parsed[key] is None:
            violations.append({
                "code": "PAUSE_MANIFEST_REQUIRED_FIELD_MISSING",
                "location": f"pause_manifest.{key}",
            })
    if violations:
        raise FreeTierFirewallError(violations[0]["code"], violations=violations)

    for text_key in ("authority", "cause"):
        if not isinstance(parsed[text_key], str) or not parsed[text_key].strip():
            violations.append({
                "code": "PAUSE_MANIFEST_FIELD_EMPTY",
                "location": f"pause_manifest.{text_key}",
            })
    if not isinstance(parsed["suspended_destinations"], list) or not parsed["suspended_destinations"]:
        violations.append({
            "code": "PAUSE_MANIFEST_DESTINATIONS_REQUIRED",
            "location": "pause_manifest.suspended_destinations",
        })
    else:
        for idx, dest_item in enumerate(parsed["suspended_destinations"]):
            if not isinstance(dest_item, str) or not dest_item.strip():
                violations.append({
                    "code": "PAUSE_MANIFEST_DESTINATIONS_INVALID_ELEMENT",
                    "location": f"pause_manifest.suspended_destinations[{idx}]",
                })
    if not isinstance(parsed["tasks"], list):
        violations.append({
            "code": "PAUSE_MANIFEST_TASKS_LIST_REQUIRED",
            "location": "pause_manifest.tasks",
        })
    else:
        for idx, task_item in enumerate(parsed["tasks"]):
            if not isinstance(task_item, Mapping):
                violations.append({
                    "code": "PAUSE_MANIFEST_TASKS_INVALID_ELEMENT",
                    "location": f"pause_manifest.tasks[{idx}]",
                })
    if not isinstance(parsed["stop_files"], list):
        violations.append({
            "code": "PAUSE_MANIFEST_STOP_FILES_LIST_REQUIRED",
            "location": "pause_manifest.stop_files",
        })
    else:
        for idx, stop_item in enumerate(parsed["stop_files"]):
            valid_str = isinstance(stop_item, str) and bool(stop_item.strip())
            valid_map = (
                isinstance(stop_item, Mapping)
                and isinstance(stop_item.get("path"), str)
                and bool(stop_item["path"].strip())
            )
            if not (valid_str or valid_map):
                violations.append({
                    "code": "PAUSE_MANIFEST_STOP_FILES_INVALID_ELEMENT",
                    "location": f"pause_manifest.stop_files[{idx}]",
                })
    if violations:
        raise FreeTierFirewallError(violations[0]["code"], violations=violations)

    paused_dt = parse_strict_utc(parsed["paused_at_utc"], field_name="pause_manifest.paused_at_utc")
    resume_dt = parse_strict_utc(parsed["resume_at_utc"], field_name="pause_manifest.resume_at_utc")
    if resume_dt <= paused_dt:
        violations.append({
            "code": "PAUSE_MANIFEST_CLOCK_ORDER_INVALID",
            "location": "pause_manifest.resume_at_utc",
        })

    # Stale pre-15-Dec pause manifest guard (e.g. old 25 Nov or 29 Nov resume manifest).
    if resume_dt < min_unpause_dt:
        violations.append({
            "code": "PAUSE_MANIFEST_STALE_PRE_DEC15",
            "location": "pause_manifest.resume_at_utc",
            "detail": f"resume_at_utc={_iso_utc(resume_dt)} < required_min={_iso_utc(min_unpause_dt)}",
        })

    cause = str(parsed["cause"])
    if _STALE_PRE_DEC15_CAUSE_RE.search(cause):
        violations.append({
            "code": "PAUSE_MANIFEST_STALE_CAUSE",
            "location": "pause_manifest.cause",
            "detail": cause[:100],
        })

    # Explicit FREE_ONLY_MODE + CC-024 declaration required on the Dec-15 unpause manifest (zero silent defaults!).
    if parsed.get("unpause_mode") != FREE_ONLY_MODE:
        violations.append({
            "code": "PAUSE_MANIFEST_FREE_ONLY_MODE_REQUIRED",
            "location": "pause_manifest.unpause_mode",
            "detail": repr(parsed.get("unpause_mode")),
        })
    if parsed.get("cc024_clean_required") is not True:
        violations.append({
            "code": "PAUSE_MANIFEST_CC024_FLAG_REQUIRED",
            "location": "pause_manifest.cc024_clean_required",
            "detail": repr(parsed.get("cc024_clean_required")),
        })

    # Premature unpause guard: ContentOps stays strictly PAUSED through 30 Nov - 14 Dec.
    if now_dt < min_unpause_dt or now_dt < resume_dt:
        violations.append({
            "code": "UNPAUSE_BEFORE_DEC15_WINDOW",
            "location": "now_utc",
            "detail": f"now={_iso_utc(now_dt)}, resume_at={_iso_utc(resume_dt)}",
        })

    # Hard-stop checks in control_dir AND restored.json alongside the manifest file itself.
    restored_checked: set[Path] = set()
    if not allow_already_restored and manifest_parent is not None:
        sibling_restored = manifest_parent / "restored.json"
        if sibling_restored.exists():
            restored_checked.add(sibling_restored.resolve())
            violations.append({
                "code": "PAUSE_MANIFEST_ALREADY_RESTORED",
                "location": str(sibling_restored),
            })

    if control_dir is not None:
        ctrl = Path(control_dir)
        if (ctrl / "KILL_SWITCH").exists():
            violations.append({
                "code": "GLOBAL_KILL_SWITCH_PRESENT",
                "location": str(ctrl / "KILL_SWITCH"),
            })
        if (ctrl / "llm_operator_pause.flag").exists():
            violations.append({
                "code": "LLM_OPERATOR_PAUSE_FLAG_PRESENT",
                "location": str(ctrl / "llm_operator_pause.flag"),
            })
        if (ctrl / "agy_neo_routes.json").exists():
            violations.append({
                "code": "AGY_NEO_ROUTES_PRESENT_FORBIDDEN_CC801",
                "location": str(ctrl / "agy_neo_routes.json"),
            })
        ctrl_restored = ctrl / "restored.json"
        if not allow_already_restored and ctrl_restored.exists() and ctrl_restored.resolve() not in restored_checked:
            violations.append({
                "code": "PAUSE_MANIFEST_ALREADY_RESTORED",
                "location": str(ctrl_restored),
            })

    if violations:
        raise FreeTierFirewallError(
            violations[0]["code"],
            violations=violations,
            details={"source": manifest_source},
        )

    return {
        "status": "PASS",
        "source": manifest_source,
        "paused_at_utc": _iso_utc(paused_dt),
        "resume_at_utc": _iso_utc(resume_dt),
        "unpause_mode": FREE_ONLY_MODE,
        "cc024_clean_required": True,
        "suspended_destination_count": len(parsed["suspended_destinations"]),
        "manifest_sha256": sha256_canonical(dict(parsed)),
    }


def run_free_tier_unpause_preflight(
    *,
    now_utc: datetime | str,
    pause_manifest: Path | str | Mapping[str, Any],
    outbound_payloads: Sequence[Mapping[str, Any] | str],
    track_record_citation: Mapping[str, Any],
    track_record_chain: Path | str | Sequence[Mapping[str, Any]] | None = None,
    runtime_config: Mapping[str, Any] | None = None,
    control_dir: Path | str | None = None,
    scheduled_tasks: Sequence[Mapping[str, Any]] | None = None,
    editorial_agent: str | None = "codex",
    digest_driver: str | None = "python-neo",
    live_provider: str | None = None,
    private_texts: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
    check_instruments: bool = True,
    require_notice: bool = False,
    min_unpause_utc: datetime | str = DEC15_FREE_UNPAUSE_EARLIEST_UTC,
) -> dict[str, Any]:
    """Run all four fail-closed V2.1-C6 ~15 Dec FREE-only CC-024 unpause preflight gates.

    Zero silent waivers (Rule A3): missing outbound payloads, stale manifests,
    paid markers, CC-024 violations, broken SHA-256 hash chains, or active
    Claude/agy dependencies all raise FreeTierFirewallError immediately.
    """
    now_dt = parse_strict_utc(now_utc, field_name="now_utc")
    if not isinstance(outbound_payloads, Sequence) or isinstance(outbound_payloads, (str, bytes)) or not outbound_payloads:
        raise FreeTierFirewallError(
            "OUTBOUND_PAYLOADS_REQUIRED",
            violations=[{"code": "OUTBOUND_PAYLOADS_REQUIRED", "location": "outbound_payloads"}],
        )

    gate_1 = verify_pause_manifest_for_dec15_unpause(
        pause_manifest,
        now_utc=now_dt,
        control_dir=control_dir,
        min_unpause_utc=min_unpause_utc,
    )
    parsed_manifest, _, _ = _load_pause_manifest_object(pause_manifest)
    manifest_tasks = list(parsed_manifest.get("tasks") or ())
    if scheduled_tasks is None:
        effective_tasks: Sequence[Mapping[str, Any]] | None = manifest_tasks
    else:
        if not isinstance(scheduled_tasks, Sequence) or isinstance(scheduled_tasks, (str, bytes)):
            raise FreeTierFirewallError(
                "SCHEDULED_TASKS_SEQUENCE_REQUIRED",
                violations=[{"code": "SCHEDULED_TASKS_SEQUENCE_REQUIRED", "location": "scheduled_tasks"}],
            )
        effective_tasks = [*scheduled_tasks, *manifest_tasks]

    gate_2 = verify_zero_claude_and_agy_dependencies(
        now_utc=now_dt,
        runtime_config=runtime_config,
        control_dir=control_dir,
        scheduled_tasks=effective_tasks,
        editorial_agent=editorial_agent,
        digest_driver=digest_driver,
        live_provider=live_provider,
        env=env,
    )
    gate_3 = verify_track_record_citation_lineage(
        track_record_citation,
        now_utc=now_dt,
        chain_records_or_path=track_record_chain,
        private_texts=private_texts,
    )

    outbound_results: list[dict[str, Any]] = []
    for idx, item in enumerate(outbound_payloads):
        dest = item.get("destination") if isinstance(item, Mapping) else None
        res = verify_outbound_free_payload(
            item,
            now_utc=now_dt,
            destination=dest,
            private_texts=private_texts,
            check_instruments=check_instruments,
            check_public_time=True,
            require_notice=require_notice,
        )
        outbound_results.append({"index": idx, **res})

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "mode": FREE_ONLY_MODE,
        "cc024_clean": True,
        "public_write_performed": False,
        "checked_at_utc": _iso_utc(now_dt),
        "gates": {
            "gate_1_pause_manifest": gate_1,
            "gate_2_zero_claude_and_agy": gate_2,
            "gate_3_track_record_hash_chain": gate_3,
            "gate_4_outbound_payloads": {
                "status": "PASS",
                "payload_count": len(outbound_results),
                "results": outbound_results,
            },
        },
    }
    return {**report_body, "report_sha256": sha256_canonical(report_body)}
