"""Strictly private-only ContentOps newsroom summary feed for PrivateApp (Decision 184).

Emits a compact, read-only ``contentops-newsroom-summary.private.json`` payload
(``ContentOpsNewsroomPrivateSummaryV1``) covering:
- Hardened, zero-N+1 CC-153 store & pipeline reads (eliminates the live 3.001s
  ``CONTENTOPS_STORE_READ_FAILED`` timeout on un-indexed multi-GB stores while
  preserving bounded fail-closed outage reporting).
- Drafts, confirmed Substack wraps/articles, recent post queue, mobile X reply
  desk, Vietnamese gold note (CC-406), and image register telemetry.
- Fast header telemetry for ``x_list_feed_v1.json`` (never dumps 24h raw tweet rows).
- CC-711 X_List_Feed keepalive and BrowserOS Neo health summary.
- CC-817 Market Forces Attention Map summary with defense-in-depth stripping and
  echo verification ensuring zero ``_private_texts`` or book/wire leaks.
- Publisher pause/unpause window, lane ``.stop`` files, route suspensions,
  ``KILL_SWITCH``, and ``llm_operator_pause.flag`` control state.
- Clean executive human status pills on every primary display field (zero raw
  ``*_NOT_WRITTEN``, ``*_MISSING``, or ``SNAKE_CASE`` codes outside ``diagnostics``).

Strictly read-only against ContentOps/PrivateApp sources; zero network calls
(delegates optional local loopback probes to ``cc711_xfeed_neo_keepalive_v1``),
zero LLM calls, zero public writes, and refuses writing to any public tree.

Operator: T3 Code, Gemini 4 Neon xhigh, antigravity_13
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import time
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

SCHEMA_VERSION = "ContentOpsNewsroomPrivateSummaryV1"
OUTPUT_FILENAME = "contentops-newsroom-summary.private.json"
CC153_SCHEMA = "PrivateContentOpsPipelineV1"

GMT7 = timezone(timedelta(hours=7))
ET = ZoneInfo("America/New_York")

MAX_JSON_FILE_BYTES = 16 * 1024 * 1024
MAX_X_FEED_HEADER_BYTES = 65536
MAX_CC153_ROWS = 2000
DEFAULT_CC153_TIMEOUT_SECONDS = 3.0
DEFAULT_CC153_RETRY_DELAYS = (0.0, 0.1, 0.25, 0.5)
SQLITE_BATCH_SIZE = 200

DEFAULT_CONTENTOPS_RUNTIME_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
DEFAULT_CODEX_EXEC_DIR = Path(r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\codex-exec")
DEFAULT_PRIVATEAPP_DATA_DIR = Path(r"A:\Capital Chronicle\PrivateApp\data")
DEFAULT_ATTENTION_MAP_LIVE_PATH = Path(
    r"A:\Capital Chronicle\Runtime\MarketAttentionMap\market_attention_map_live_v1.json"
)
DEFAULT_PUBLISHER_STOP_NAMES = (
    "runner-publisher.stop",
    "runner-publisher-b.stop",
    "runner-publisher-c.stop",
)

ALL_DESTINATIONS = (
    "substack",
    "substack_notes",
    "x",
    "threads",
    "telegram",
    "discord",
    "linkedin",
    "linkedin_company",
    "instagram_business",
    "facebook_page",
    "youtube",
)
DESTINATION_LABELS: Mapping[str, str] = {
    "substack": "Substack",
    "substack_notes": "Substack Notes",
    "x": "X",
    "threads": "Threads",
    "telegram": "Telegram",
    "discord": "Discord",
    "linkedin": "LinkedIn",
    "linkedin_company": "LinkedIn Company",
    "instagram_business": "Instagram",
    "facebook_page": "Facebook Page",
    "youtube": "YouTube",
}
PLATFORM_ALIASES: Mapping[str, str] = {
    "facebook_page": "facebook",
    "instagram_business": "instagram",
    "substack_notes": "substack_notes",
}

POST_TYPE_LABELS: Mapping[str, str] = {
    "setup": "Call",
    "call": "Call",
    "conditional_call": "Call",
    "event_preview": "Event",
    "event": "Event",
    "event_review": "Result",
    "result": "Result",
    "closed": "Result",
    "exit": "Result",
    "scorecard": "Scorecard",
    "weekly_scorecard": "Scorecard",
    "map": "Map",
    "morning_map": "Map",
    "reply": "Reply",
    "sourced_reply": "Reply",
}

FORBIDDEN_PRIVATE_KEYS = frozenset({
    "_private_texts",
    "x_list_posts",
    "raw_x_posts",
    "x_posts",
    "wire_headlines",
    "raw_headlines",
    "private_headlines",
    "private_notes",
    "open_positions",
    "open_position_impacts",
    "positions",
    "book",
    "portfolio",
    "prepared_responses",
    "pre_armed_plans",
    "armed_plans",
    "surprise_map",
    "linked_odds_markets",
    "private_watch_items",
    "internal_notes",
    "account_id",
    "lot_size",
    "margin",
    "balance",
    "equity",
    "credentials",
    "secrets",
})
_PRIVATE_WATCH_KINDS = frozenset({
    "x_account",
    "x_list",
    "wire_headline",
    "private_feed",
    "odds_market_number",
})
_OWN_PROBABILITY_SOURCES = frozenset({
    "capital_chronicle",
    "cc_model_estimate",
    "capital_chronicle_estimate",
    "desk",
    "analyst",
})
_MARKET_PROBABILITY_SOURCES = frozenset({
    "kalshi",
    "polymarket",
    "fedwatch",
    "cme_fedwatch",
    "prediction_market",
    "options",
    "market_implied",
    "futures",
    "market",
})
_BRANCH_KIND_LABELS: Mapping[str, tuple[str, str]] = {
    "base": ("base_case", "Base Case"),
    "base_case": ("base_case", "Base Case"),
    "bull": ("bull_case", "Bull Case"),
    "bull_case": ("bull_case", "Bull Case"),
    "upside": ("bull_case", "Bull Case"),
    "bear": ("bear_case", "Bear Case"),
    "bear_case": ("bear_case", "Bear Case"),
    "downside": ("bear_case", "Bear Case"),
    "alternative": ("alternative", "Alternative"),
    "main_alternative": ("alternative", "Alternative"),
}

RAW_DEBUG_ENUM_RE = re.compile(
    r"\b(?:[A-Z][A-Z0-9_]*_(?:NOT_WRITTEN|NOT_ADMITTED|NOT_SUPPLIED|NOT_FOUND|NOT_BOUND|"
    r"NOT_CONFIGURED|NOT_ESTABLISHED|NOT_VERIFIED|NOT_RETAINED|NOT_RECORDED|NOT_COLLECTED|"
    r"MISSING|UNREADABLE|UNAVAILABLE|RETRY_EXHAUSTED|READ_FAILED|READ_TIMEOUT)"
    r"|VIEWS_UNSUPPORTED|VIEWS_UNAVAILABLE|CONTENTOPS_STORE_[A-Z0-9_]+"
    r"|NOT_IN_NEWSROOM_PUBLISHED_RECORD|NO_COLLECTED_OBSERVATION_IN_WINDOW"
    r"|CC402_NO_COLLECTED_OBSERVATION_IN_WINDOW|CC464_MOBILE_DRAFT_NOT_WRITTEN"
    r"|REVIEWED_PACKAGE_NOT_FOUND|DIGEST_BODY_FROM_NATIVE_PUBLISH_REQUEST)\b"
)

_WRAP_WORK_ITEM_RE = re.compile(r"^cc689-(?:daily|weekly)-", re.IGNORECASE)
_WRAP_TITLE_RE = re.compile(r"market wrap|daily digest|weekend wrap|week ahead", re.IGNORECASE)


class InvalidSource(ValueError):
    """Raised on malformed, oversized, or contract-violating local inputs."""


class PrivateLeakError(RuntimeError):
    """Raised when forbidden private keys or canary strings leak into output."""


class DisplayHygieneError(RuntimeError):
    """Raised when raw debug enums leak onto primary display fields."""


# ---------------------------------------------------------------------------
# Strict JSON / time / path / URL helpers
# ---------------------------------------------------------------------------


def _canonical_bytes(value: Any, *, ensure_ascii: bool = True) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=ensure_ascii,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_obj(value: Any, *, ensure_ascii: bool = True) -> str:
    return sha256(_canonical_bytes(value, ensure_ascii=ensure_ascii)).hexdigest()


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in pairs:
        if key in out:
            raise InvalidSource("DUPLICATE_JSON_KEY")
        out[key] = val
    return out


def _reject_nonfinite(_token: str) -> Any:
    raise InvalidSource("NONFINITE_JSON")


def _strict_decode(raw: bytes | str) -> Any:
    return json.loads(raw, object_pairs_hook=_strict_pairs, parse_constant=_reject_nonfinite)


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _require_utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise InvalidSource("UTC_CLOCK_REQUIRED")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidSource("UTC_CLOCK_REQUIRED") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise InvalidSource("UTC_CLOCK_REQUIRED")
    return parsed.astimezone(timezone.utc)


def _iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _format_gmt7(value: str | datetime | None) -> str | None:
    dt = value if isinstance(value, datetime) else _parse_utc(value)
    if dt is None:
        return None
    local = dt.astimezone(GMT7)
    return local.strftime("%Y-%m-%d %H:%M GMT+7")


def _format_et_date(value: str | datetime | None) -> str | None:
    dt = value if isinstance(value, datetime) else _parse_utc(value)
    if dt is None:
        return None
    local = dt.astimezone(ET)
    return f"{local.strftime('%B')} {local.day}, {local.year}"


def production_date_bangkok(value: str | datetime) -> str:
    """Producer rule: 01:00 GMT+7 belongs to the prior date; production day rolls at 02:00."""
    dt = value.astimezone(timezone.utc) if isinstance(value, datetime) else _require_utc(value)
    local = dt.astimezone(GMT7)
    prod = local.date() - timedelta(days=1) if local.hour < 2 else local.date()
    return prod.isoformat()


def _valid_https(value: Any) -> bool:
    if not isinstance(value, str) or len(value) > 2000:
        return False
    if any(c.isspace() or ord(c) < 32 for c in value):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
    )


def _valid_x_intent_url(value: Any, expected_post_id: str | None = None) -> str | None:
    if not isinstance(value, str) or len(value) > 2000:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.hostname != "x.com" or parsed.path != "/intent/post":
        return None
    params = parse_qs(parsed.query, keep_blank_values=False)
    reply_to = params.get("in_reply_to", [None])[0]
    if not reply_to or not str(reply_to).isdigit():
        return None
    if expected_post_id is not None and str(reply_to) != str(expected_post_id):
        return None
    return value


def _safe_num(value: Any) -> float | None:
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _safe_int(value: Any) -> int | None:
    if type(value) is int:
        return value
    return None


def _nonneg_int(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise InvalidSource("COUNT_FIELD_INVALID")
    return value


def _req_text(value: Any, limit: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise InvalidSource("TEXT_FIELD_INVALID")
    return value


def _safe_read_bytes(path: Path, *, max_bytes: int = MAX_JSON_FILE_BYTES) -> bytes:
    resolved = Path(path).resolve()
    if any(re.search(r"(?i)credential|secret|2fa|^\.env(?:\.|$)", part) for part in resolved.parts):
        raise InvalidSource("SOURCE_PATH_FORBIDDEN")
    if resolved.stat().st_size > max_bytes:
        raise InvalidSource("SOURCE_SIZE_LIMIT")
    with resolved.open("rb") as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise InvalidSource("SOURCE_SIZE_LIMIT")
    return raw


def _make_pill(label: str, tone: str, detail: str | None = None) -> dict[str, Any]:
    normalized_tone = tone if tone in {"emerald", "amber", "rose", "neutral"} else "neutral"
    return {"label": label, "tone": normalized_tone, "detail": detail}


# ---------------------------------------------------------------------------
# Exhaustive Raw Debug Enum -> Executive UI Pill Mapping
# ---------------------------------------------------------------------------

_EXACT_STATUS_PILLS: Mapping[str, tuple[str, str, str]] = {
    "HEALTH_RECORD_NOT_WRITTEN": (
        "Awaiting Feed",
        "neutral",
        "Health heartbeat exporter is not yet wired; source clocks are shown directly.",
    ),
    "HEALTH_NOT_WRITTEN": (
        "Partial Telemetry",
        "neutral",
        "Aggregated health summary is absent; individual component clocks are shown.",
    ),
    "IMAGE_QA_SCORE_NOT_WRITTEN": (
        "Unscored",
        "neutral",
        "Automated image QA score was not attached to this dispatch record.",
    ),
    "IMAGE_CHECKLIST_NOT_WRITTEN": (
        "No Checklist",
        "neutral",
        "Visual review checklist was not recorded for this asset.",
    ),
    "IMAGE_NOT_SUPPLIED": (
        "Text Only",
        "neutral",
        "No image asset attached to this post record.",
    ),
    "IMAGE_PATH_OR_HASH_NOT_SUPPLIED": (
        "Image Unavailable",
        "amber",
        "Local image path or SHA-256 hash was not supplied.",
    ),
    "IMAGE_FILE_NOT_FOUND": (
        "Image Unavailable",
        "amber",
        "Local image file is missing on disk.",
    ),
    "IMAGE_FILE_UNREADABLE": (
        "Image Unavailable",
        "amber",
        "Local image file could not be read.",
    ),
    "IMAGE_BYTES_CHANGED": (
        "Image Changed",
        "amber",
        "Local image bytes no longer match the recorded SHA-256 hash.",
    ),
    "PUBLISHED_IMAGES_NOT_WRITTEN": (
        "Image Log Pending",
        "neutral",
        "Published image register has not been written yet.",
    ),
    "PUBLISHED_IMAGES_UNREADABLE": (
        "Image Log Degraded",
        "amber",
        "Published image register could not be read.",
    ),
    "IMAGE_REGISTER_INVALID_ROW": (
        "Image Log Degraded",
        "amber",
        "Published image register contains at least one malformed line.",
    ),
    "CC464_MOBILE_DRAFT_NOT_WRITTEN": (
        "No Reply Drafts",
        "neutral",
        "No mobile X reply pack generated in the last 48 hours.",
    ),
    "X_LIST_FEED_NOT_WRITTEN": (
        "X Feed Offline",
        "rose",
        "X-list feed export file has not been written.",
    ),
    "X_LIST_FEED_UNREADABLE": (
        "X Feed Offline",
        "rose",
        "X-list feed export could not be read.",
    ),
    "X_LIST_FEED_CLOCK_INVALID": (
        "X Feed Clock Error",
        "rose",
        "X-list feed export contains an invalid UTC timestamp.",
    ),
    "PRODUCTION_DAY_RECORD_MISSING": (
        "No Production Day Yet",
        "neutral",
        "No production day summary saved yet for the current Bangkok production day.",
    ),
    "PRODUCTION_DAY_ROOT_NOT_BOUND": (
        "Not Configured",
        "neutral",
        "Production day folder is not configured.",
    ),
    "PRODUCTION_DAY_RECORD_INVALID": (
        "Day Record Invalid",
        "amber",
        "Saved production day summary failed schema or seal verification.",
    ),
    "CONTENTOPS_STORE_READ_TIMEOUT": (
        "Store Timeout",
        "amber",
        "Read-only SQLite query exceeded its bounded timeout budget.",
    ),
    "CONTENTOPS_STORE_READ_FAILED": (
        "Store Unavailable",
        "rose",
        "Read-only SQLite store failed to open or query cleanly.",
    ),
    "CONTENTOPS_STORE_READ_FAILED_OR_BUSY": (
        "Store Unavailable",
        "amber",
        "Read-only SQLite store encountered an error or transient lock.",
    ),
    "CONTENTOPS_STORE_BUSY_RETRY_EXHAUSTED": (
        "Store Busy",
        "amber",
        "Read-only SQLite snapshot exhausted busy retries within the bounded budget.",
    ),
    "CONTENTOPS_STORE_MISSING": (
        "Store Missing",
        "rose",
        "Configured ContentOps SQLite store file was not found.",
    ),
    "CONTENTOPS_STORE_NOT_BOUND": (
        "Store Not Configured",
        "neutral",
        "ContentOps SQLite store path is not configured.",
    ),
    "CONTENTOPS_STORE_RECORD_INVALID": (
        "Store Record Invalid",
        "amber",
        "A store row failed strict schema or hash verification.",
    ),
    "NO_OWNER_DAILY_DIGEST_RECORD_BOUND_CC143": (
        "No Digest Today",
        "neutral",
        "Daily email digest is not bound for today's production day.",
    ),
    "BOUND_DAILY_DIGEST_RECORD_MISSING": (
        "No Digest Today",
        "neutral",
        "Bound daily digest record was not found in the store.",
    ),
    "BOUND_DAILY_DIGEST_RECORD_OTHER_DAY": (
        "Prior Day Digest",
        "neutral",
        "Bound daily digest record belongs to an earlier production day.",
    ),
    "CC135_FEED_MISSING": (
        "Feed Pending",
        "neutral",
        "Published content feed file has not been written yet.",
    ),
    "CC135_FEED_INVALID": (
        "Feed Invalid",
        "amber",
        "Published content feed failed seal or contract validation.",
    ),
    "CC135_FEED_READ_FAILED": (
        "Feed Unavailable",
        "amber",
        "Published content feed could not be read.",
    ),
    "DIGEST_NOT_WRITTEN": (
        "Digest Pending",
        "neutral",
        "Ops Live 07:00 digest file has not been written yet.",
    ),
    "DIGEST_SOURCE_NOT_CONFIGURED": (
        "Digest Not Configured",
        "neutral",
        "Ops Live 07:00 digest path is not configured.",
    ),
    "REVIEWED_PACKAGE_NOT_FOUND": (
        "External Link Only",
        "neutral",
        "Confirmed on Substack; local reviewed body archive is not attached.",
    ),
    "NOT_IN_NEWSROOM_PUBLISHED_RECORD": (
        "External Link Only",
        "neutral",
        "Confirmed via store dispatch outside the sealed newsroom feed.",
    ),
    "EVENT_ARTICLES_NOT_SUPPLIED": (
        "No Event Pieces",
        "neutral",
        "No event preview or review pieces in the current desk export.",
    ),
    "CC402_NO_COLLECTED_OBSERVATION_IN_WINDOW": (
        "No Views Data",
        "neutral",
        "No native platform view counts collected in the 7-day rolling window.",
    ),
    "NO_COLLECTED_OBSERVATION_IN_WINDOW": (
        "No Views Data",
        "neutral",
        "No view observations collected in the current window.",
    ),
    "AUDIENCE_NUMBERS_NOT_COLLECTED": (
        "No Views Data",
        "neutral",
        "Audience metrics have not been collected yet.",
    ),
    "VIEWS_UNSUPPORTED": (
        "Unsupported",
        "neutral",
        "Platform API does not expose native view counts.",
    ),
    "VIEWS_UNAVAILABLE": (
        "Unavailable",
        "neutral",
        "Native view count was unavailable at collection time.",
    ),
    "ATTENTION_MAP_LIVE_FILE_ABSENT": (
        "Awaiting Live Feed",
        "neutral",
        "Market attention map feed (CC-807 / CC-817) is not active yet.",
    ),
    "GOLD_NOTE_MISSING": (
        "No Gold Note",
        "neutral",
        "Latest daily Vietnamese gold note was not found.",
    ),
}


def map_status_pill(raw_code: str | None, *, paused: bool = False) -> dict[str, Any]:
    """Translate any raw producer/reader status code into a clean executive pill."""
    if not raw_code:
        return _make_pill("Active", "emerald", "Operating normally.")
    code = str(raw_code).strip()
    if code == "PRODUCTION_DAY_RECORD_MISSING" and paused:
        return _make_pill(
            "Paused · No Run Today",
            "neutral",
            "Publishing is paused; no production day record is expected yet.",
        )
    if code in _EXACT_STATUS_PILLS:
        label, tone, detail = _EXACT_STATUS_PILLS[code]
        return _make_pill(label, tone, detail)
    upper = code.upper()
    if upper.endswith(("_NOT_WRITTEN", "_NOT_ADMITTED", "_NOT_SUPPLIED", "_MISSING", "_NOT_CONFIGURED", "_NOT_BOUND")):
        return _make_pill("Pending", "neutral", "Upstream record has not been written yet.")
    if upper.endswith(("_UNREADABLE", "_FAILED", "_ERROR", "_INVALID")):
        return _make_pill("Unavailable", "amber", "Upstream telemetry could not be read cleanly.")
    if "TIMEOUT" in upper or "BUSY" in upper or "STARVED" in upper:
        return _make_pill("Busy · Retrying", "amber", "Upstream service was transiently busy.")
    if "STOP" in upper or "PAUSED" in upper or "SUSPEND" in upper:
        return _make_pill("Paused", "amber", "Paused by operator control.")
    if upper in {"OK", "HEALTHY", "READY", "RUNNING", "AVAILABLE", "LIVE", "DISPATCH_CONFIRMED"}:
        return _make_pill("Live", "emerald", "Healthy and verified.")
    return _make_pill("Status Recorded", "neutral", "Inspect diagnostics drawer for exact raw state.")


# ---------------------------------------------------------------------------
# Hardened CC-153 Read-Only Store Reader (Zero N+1, Bounded Fail-Closed)
# ---------------------------------------------------------------------------


def _source_evidence(
    path: Path | str | None,
    now_utc: str,
    *,
    state: str = "AVAILABLE",
    reason: str | None = None,
    latest: str | None = None,
    byte_hash: str | None = None,
) -> dict[str, Any]:
    age: float | None = None
    freshness = "UNKNOWN"
    if latest:
        age = round((_require_utc(now_utc) - _require_utc(latest)).total_seconds(), 3)
        freshness = "FUTURE_CLOCK" if age < 0 else "OLDER_THAN_6H" if age > 21600 else "WITHIN_6H"
    return {
        "source": str(path) if path else "Not configured",
        "state": state,
        "reason": reason,
        "latest_at_utc": latest,
        "read_at_utc": now_utc,
        "age_seconds": age,
        "freshness": freshness,
        "sha256": byte_hash,
    }


def _bounded_rows(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
    *,
    max_rows: int = MAX_CC153_ROWS,
) -> list[dict[str, Any]]:
    rows = conn.execute(sql, params).fetchmany(max_rows + 1)
    if len(rows) > max_rows:
        raise InvalidSource("STORE_ROW_LIMIT")
    return [dict(row) for row in rows]


def _decode_store_payload(row: Mapping[str, Any] | None) -> dict[str, Any]:
    if row is None or not isinstance(row.get("payload"), str):
        raise InvalidSource("STORE_PAYLOAD_MISSING_OR_OVERSIZED")
    raw = row["payload"].encode("utf-8")
    if len(raw) > MAX_JSON_FILE_BYTES:
        raise InvalidSource("STORE_PAYLOAD_MISSING_OR_OVERSIZED")
    value = _strict_decode(raw)
    if not isinstance(value, dict):
        raise InvalidSource("STORE_PAYLOAD_INVALID")
    return value


def _day_prefilter_bounds(day: str) -> tuple[str, str]:
    """Conservative ISO-8601 date-string prefilter around a Bangkok production day.

    Bangkok production day ``YYYY-MM-DD`` runs from ``(day-1)T19:00:00Z`` to
    ``dayT19:00:00Z``. Widening SQL prefilters to ``[day-2, day+2)`` captures any
    UTC or timezone-offset ISO string safely; exact ``production_date_bangkok``
    filtering in Python preserves exact CC-153 boundaries.
    """
    parsed = date.fromisoformat(day)
    return (parsed - timedelta(days=2)).isoformat(), (parsed + timedelta(days=2)).isoformat()


def _load_cc153_admissions(
    conn: sqlite3.Connection,
    bindings: list[dict[str, Any]],
    day: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items: dict[tuple[str, str], dict[str, Any]] = {}
    gaps: list[dict[str, Any]] = []
    for row in bindings:
        binding = _decode_store_payload(row)
        if production_date_bangkok(binding["cutoff_utc"]) != day:
            continue
        run_id = _req_text(binding["run_id"], 200)
        window_id = binding.get("window_id") or "standing"
        work_id = "cc-opportunity-" + _sha256_obj(run_id)
        req_id = "native-desktop-" + _sha256_obj([work_id, "select", "request"])
        res_id = "native-desktop-" + _sha256_obj([work_id, "select", "response"])
        req_rows = _bounded_rows(
            conn,
            "SELECT message_id,work_item_id,destination,status,payload,created_at "
            "FROM outbox_messages WHERE message_id=?",
            (req_id,),
            max_rows=2,
        )
        res_rows = _bounded_rows(
            conn,
            "SELECT message_id,work_item_id,destination,status,payload,created_at "
            "FROM outbox_messages WHERE message_id=?",
            (res_id,),
            max_rows=2,
        )
        req_row = req_rows[0] if req_rows else None
        res_row = res_rows[0] if res_rows else None
        if res_row is None:
            gaps.append({"run_id": run_id, "reason": "NATIVE_SELECTION_RETURN_NOT_RECORDED"})
            continue
        try:
            req = _decode_store_payload(req_row)
            res = _decode_store_payload(res_row)
            if (
                req.get("stage") != "select"
                or req.get("run_id") != run_id
                or req.get("request_sha256") != _sha256_obj({k: v for k, v in req.items() if k != "request_sha256"})
                or res.get("request_sha256") != req["request_sha256"]
            ):
                raise InvalidSource("NATIVE_SELECTION_BINDING_INVALID")
            candidates = {c["candidate_id"]: c for c in req["governed_input"]["candidates"]}
            plan = res["output"]["ordered_candidate_plan"]
            if not isinstance(plan, list) or len({p["candidate_id"] for p in plan}) != len(plan):
                raise InvalidSource("NATIVE_SELECTION_PLAN_INVALID")
            current = []
            for entry in plan:
                cid = _req_text(entry["candidate_id"], 200)
                original = candidates[cid]
                current.append((
                    (window_id, cid),
                    {
                        "candidate_id": cid,
                        "window_id": window_id,
                        "run_id": run_id,
                        "headline": _req_text(original["headline_text"], 2000),
                        "selected_at_utc": res_row["created_at"],
                        "source_message_id": res_row["message_id"],
                    },
                ))
            for key, item in current:
                items.setdefault(key, item)
        except (InvalidSource, ValueError, KeyError, TypeError):
            gaps.append({"run_id": run_id, "reason": "NATIVE_SELECTION_BINDING_INVALID"})
    return list(items.values()), gaps


def _load_cc153_dispatches_zero_n_plus_1(
    conn: sqlite3.Connection,
    day: str,
) -> list[dict[str, Any]]:
    """Bounded, zero-N+1 CC-153 dispatch + verified-readback projection for ``day``.

    Preserves exact CC-153 semantics: includes every dispatch whose ``dispatched_at``
    falls on ``day`` OR that received a ``verified: true`` readback on ``day``,
    returning the earliest verified readback timestamp for each shown dispatch —
    without scanning all historical dispatches or running N+1 ``readbacks`` queries.
    """
    pre_start, pre_end = _day_prefilter_bounds(day)

    # 1. Bounded dispatches in the day prefilter window.
    window_dispatches = _bounded_rows(
        conn,
        "SELECT d.dispatch_id,d.platform,d.status,d.dispatched_at,d.public_object_url,o.work_item_id "
        "FROM platform_dispatches d JOIN outbox_messages o ON o.message_id=d.message_id "
        "WHERE d.dispatched_at >= ? AND d.dispatched_at < ? "
        "ORDER BY d.dispatched_at DESC",
        (pre_start, pre_end),
    )
    by_dispatch_id: dict[str, dict[str, Any]] = {}
    day_dispatch_ids: set[str] = set()
    for row in window_dispatches:
        if production_date_bangkok(row["dispatched_at"]) == day:
            did = str(row["dispatch_id"])
            by_dispatch_id[did] = row
            day_dispatch_ids.add(did)

    # 2. Single-pass readbacks in the day prefilter window (ZERO N+1 queries!).
    window_readbacks = _bounded_rows(
        conn,
        "SELECT dispatch_id,readback_data,read_at FROM readbacks "
        "WHERE read_at >= ? AND read_at < ? ORDER BY read_at",
        (pre_start, pre_end),
    )
    verified_on_day_ids: set[str] = set()
    earliest_verified_by_dispatch: dict[str, str] = {}
    for rb in window_readbacks:
        data = _strict_decode(rb["readback_data"])
        if not isinstance(data, dict) or data.get("verified") is not True:
            continue
        did = str(rb["dispatch_id"])
        read_at = rb["read_at"]
        if production_date_bangkok(read_at) == day:
            verified_on_day_ids.add(did)
        prev = earliest_verified_by_dispatch.get(did)
        if prev is None or _require_utc(read_at) < _require_utc(prev):
            earliest_verified_by_dispatch[did] = read_at

    # 3. Fetch dispatch headers for earlier-day dispatches verified on ``day``.
    extra_ids = sorted(verified_on_day_ids - day_dispatch_ids)
    for offset in range(0, len(extra_ids), SQLITE_BATCH_SIZE):
        chunk = extra_ids[offset : offset + SQLITE_BATCH_SIZE]
        marks = ",".join("?" for _ in chunk)
        rows = _bounded_rows(
            conn,
            f"SELECT d.dispatch_id,d.platform,d.status,d.dispatched_at,d.public_object_url,o.work_item_id "
            f"FROM platform_dispatches d JOIN outbox_messages o ON o.message_id=d.message_id "
            f"WHERE d.dispatch_id IN ({marks})",
            tuple(chunk),
        )
        for row in rows:
            by_dispatch_id[str(row["dispatch_id"])] = row

    # 4. For any shown dispatch (typically 0..50), check if an earlier verified readback
    #    preceded ``pre_start`` so ``verified_readback_at_utc`` matches CC-153's earliest
    #    readback timestamp exactly (batched IN query, never N+1).
    all_shown_ids = sorted(by_dispatch_id.keys())
    if all_shown_ids:
        for offset in range(0, len(all_shown_ids), SQLITE_BATCH_SIZE):
            chunk = all_shown_ids[offset : offset + SQLITE_BATCH_SIZE]
            marks = ",".join("?" for _ in chunk)
            earlier_rbs = _bounded_rows(
                conn,
                f"SELECT dispatch_id,readback_data,read_at FROM readbacks "
                f"WHERE dispatch_id IN ({marks}) AND read_at < ? ORDER BY read_at",
                (*chunk, pre_start),
            )
            for rb in earlier_rbs:
                data = _strict_decode(rb["readback_data"])
                if not isinstance(data, dict) or data.get("verified") is not True:
                    continue
                did = str(rb["dispatch_id"])
                read_at = rb["read_at"]
                prev = earliest_verified_by_dispatch.get(did)
                if prev is None or _require_utc(read_at) < _require_utc(prev):
                    earliest_verified_by_dispatch[did] = read_at

    ordered = sorted(
        by_dispatch_id.values(),
        key=lambda r: _require_utc(r["dispatched_at"]),
        reverse=True,
    )
    shown: list[dict[str, Any]] = []
    for row in ordered:
        did = str(row["dispatch_id"])
        url = row["public_object_url"] if _valid_https(row["public_object_url"]) else None
        shown.append({
            "dispatch_id": did,
            "platform": row["platform"],
            "status": row["status"],
            "dispatched_at": row["dispatched_at"],
            "work_item_id": row["work_item_id"],
            "url": url,
            "verified_readback_at_utc": earliest_verified_by_dispatch.get(did),
        })
    return shown


def _read_cc153_digest(
    conn: sqlite3.Connection,
    store_path: Path,
    *,
    digest_message_id: str | None,
    digest_destination: str | None,
    day: str,
    now_utc: str,
) -> dict[str, Any]:
    source_ref = f"{store_path}#outbox_messages/{digest_message_id}" if digest_message_id else None
    if not digest_message_id:
        return {
            "owner_state": None,
            "email_send": "NOT_ESTABLISHED",
            "evidence": _source_evidence(
                source_ref,
                now_utc,
                state="NOT_CONFIGURED",
                reason="NO_OWNER_DAILY_DIGEST_RECORD_BOUND_CC143",
            ),
        }
    rows = _bounded_rows(
        conn,
        "SELECT message_id,work_item_id,destination,status,payload,created_at "
        "FROM outbox_messages WHERE message_id=?",
        (digest_message_id,),
        max_rows=2,
    )
    if not rows:
        return {
            "owner_state": None,
            "email_send": "NOT_ESTABLISHED",
            "evidence": _source_evidence(
                source_ref,
                now_utc,
                state="MISSING",
                reason="BOUND_DAILY_DIGEST_RECORD_MISSING",
            ),
        }
    row = rows[0]
    if digest_destination and row["destination"] != digest_destination:
        raise InvalidSource("DIGEST_DESTINATION_MISMATCH")
    if production_date_bangkok(row["created_at"]) != day:
        return {
            "owner_state": None,
            "email_send": "NOT_ESTABLISHED",
            "evidence": _source_evidence(
                source_ref,
                now_utc,
                state="MISSING",
                reason="BOUND_DAILY_DIGEST_RECORD_OTHER_DAY",
                latest=row["created_at"],
            ),
        }
    return {
        "owner_state": _req_text(row["status"], 160),
        "email_send": "NOT_ESTABLISHED",
        "evidence": _source_evidence(source_ref, now_utc, latest=row["created_at"]),
    }


def _open_readonly_sqlite(
    store_path: Path,
    *,
    timeout_seconds: float,
    immutable_snapshot: bool = False,
) -> tuple[sqlite3.Connection, str]:
    """Open SQLite strictly read-only. Only honors ``immutable_snapshot=True`` when WAL is absent/empty."""
    resolved = Path(store_path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(str(resolved))
    wal = resolved.with_name(resolved.name + "-wal")
    wal_bytes = wal.stat().st_size if wal.is_file() else 0
    use_immutable = bool(immutable_snapshot and wal_bytes == 0)
    uri = resolved.as_uri() + ("?mode=ro&immutable=1" if use_immutable else "?mode=ro")
    conn = sqlite3.connect(uri, uri=True, timeout=max(0.0, timeout_seconds))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn, ("RO_IMMUTABLE_ZERO_WAL" if use_immutable else "RO_STANDARD")


def _read_cc153_store_once(
    store_path: Path | None,
    *,
    day: str,
    now_utc: str,
    deadline: float,
    digest_message_id: str | None = None,
    digest_destination: str | None = None,
    immutable_snapshot: bool = False,
    mono_fn: Callable[[], float] = time.monotonic,
    stage_hook: Callable[[str], None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    empty = {
        "admissions": None,
        "selection_gaps": None,
        "first_causes": None,
        "dispatches": None,
        "indexes_present": None,
        "operating_control": None,
    }
    stage = "connect"
    try:
        if store_path is None:
            raise FileNotFoundError("STORE_NOT_BOUND")
        if mono_fn() >= deadline:
            err = sqlite3.OperationalError("interrupted")
            raise err
        remaining = max(0.0, deadline - mono_fn())
        conn, read_mode = _open_readonly_sqlite(
            store_path,
            timeout_seconds=min(0.2, remaining),
            immutable_snapshot=immutable_snapshot,
        )
        try:
            conn.set_progress_handler(lambda: int(mono_fn() > deadline), 1000)
            conn.execute("BEGIN")

            stage = "bindings"
            if stage_hook:
                stage_hook(stage)
            bindings = _bounded_rows(
                conn,
                "SELECT message_id,payload,created_at FROM outbox_messages "
                "WHERE message_id >= 'native-operation-binding-' AND message_id < 'native-operation-binding.' "
                "ORDER BY rowid",
            )
            admissions, gaps = _load_cc153_admissions(conn, bindings, day)

            stage = "outcomes"
            if stage_hook:
                stage_hook(stage)
            pre_start, pre_end = _day_prefilter_bounds(day)
            outcomes = _bounded_rows(
                conn,
                "SELECT message_id,work_item_id,payload,created_at FROM outbox_messages "
                "WHERE destination='internal:native-story-outcome' AND created_at >= ? AND created_at < ? "
                "ORDER BY created_at, message_id",
                (pre_start, pre_end),
            )
            causes: dict[tuple[str, Any], dict[str, Any]] = {}
            for row in outcomes:
                if production_date_bangkok(row["created_at"]) != day:
                    continue
                payload = _decode_store_payload(row)
                if payload.get("schema_version") != "contentops.native_pre_writer_outcome.v1":
                    raise InvalidSource("STORY_OUTCOME_CONTRACT_INVALID")
                key = (payload["run_id"], payload.get("candidate_id"))
                causes.setdefault(
                    key,
                    {
                        "run_id": _req_text(payload["run_id"], 200),
                        "candidate_id": payload.get("candidate_id"),
                        "outcome": _req_text(payload["outcome"], 100),
                        "primary_cause": _req_text(payload["primary_cause"], 160),
                        "recorded_at_utc": row["created_at"],
                        "source_message_id": row["message_id"],
                    },
                )

            stage = "dispatches_and_readbacks"
            if stage_hook:
                stage_hook(stage)
            shown_dispatches = _load_cc153_dispatches_zero_n_plus_1(conn, day)

            stage = "digest"
            if stage_hook:
                stage_hook(stage)
            try:
                daily_digest = _read_cc153_digest(
                    conn,
                    store_path,
                    digest_message_id=digest_message_id,
                    digest_destination=digest_destination,
                    day=day,
                    now_utc=now_utc,
                )
            except (InvalidSource, ValueError, KeyError, TypeError, AttributeError):
                daily_digest = {
                    "owner_state": None,
                    "email_send": "NOT_ESTABLISHED",
                    "evidence": _source_evidence(
                        f"{store_path}#outbox_messages/{digest_message_id}",
                        now_utc,
                        state="INVALID",
                        reason="BOUND_DAILY_DIGEST_RECORD_INVALID",
                    ),
                }

            stage = "append_clock_and_metadata"
            if stage_hook:
                stage_hook(stage)
            last_row = conn.execute(
                "SELECT created_at FROM outbox_messages ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
            latest_clock = last_row[0] if last_row else None

            idx_names = {
                str(r[0])
                for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
            }
            indexes_present = {
                "outbox_work_destination_index": "idx_outbox_work_destination_read" in idx_names,
                "outbox_destination_order_index": "idx_outbox_destination_order_read" in idx_names,
                "readbacks_dispatch_index": "idx_readbacks_dispatch_read_at_read" in idx_names,
                "dispatches_time_index": "idx_platform_dispatches_dispatched_at_read" in idx_names,
                "readbacks_time_index": "idx_readbacks_read_at_dispatch_read" in idx_names,
            }

            operating_control = None
            has_controls = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='operating_controls'"
            ).fetchone()
            if has_controls:
                ctrl_row = conn.execute(
                    "SELECT operating_mode, state_version, updated_at_utc, control_source "
                    "FROM operating_controls ORDER BY rowid DESC LIMIT 1"
                ).fetchone()
                if ctrl_row is not None:
                    operating_control = dict(ctrl_row)

            evidence = _source_evidence(store_path, now_utc, latest=latest_clock)
            evidence["clock_kind"] = "LAST_APPENDED_MESSAGE_CREATED_AT"
            evidence["read_mode"] = read_mode
            evidence["query_strategy"] = "BOUNDED_ZERO_N_PLUS_1_V1"
            return (
                {
                    "admissions": admissions,
                    "selection_gaps": gaps,
                    "first_causes": list(causes.values()),
                    "dispatches": shown_dispatches,
                    "indexes_present": indexes_present,
                    "operating_control": operating_control,
                    "evidence": evidence,
                },
                daily_digest,
            )
        finally:
            conn.close()
    except FileNotFoundError:
        state = "MISSING" if store_path else "NOT_CONFIGURED"
        reason = "CONTENTOPS_STORE_MISSING" if store_path else "CONTENTOPS_STORE_NOT_BOUND"
        extra: dict[str, Any] = {"failed_stage": stage}
    except (InvalidSource, ValueError, KeyError, TypeError, AttributeError) as exc:
        state, reason = "INVALID", "CONTENTOPS_STORE_RECORD_INVALID"
        extra = {"failed_stage": stage, "detail": str(exc)[:160]}
    except sqlite3.OperationalError as exc:
        code = getattr(exc, "sqlite_errorcode", 0) & 0xFF
        if code in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
            raise
        is_interrupt = (
            code == getattr(sqlite3, "SQLITE_INTERRUPT", 9)
            or "interrupted" in str(exc).lower()
            or mono_fn() >= deadline
        )
        state = "UNAVAILABLE"
        reason = "CONTENTOPS_STORE_READ_TIMEOUT" if is_interrupt else "CONTENTOPS_STORE_READ_FAILED"
        extra = {"failed_stage": stage, "sqlite_errorcode": code or None, "detail": str(exc)[:160]}
    except (OSError, sqlite3.Error) as exc:
        state, reason = "UNAVAILABLE", "CONTENTOPS_STORE_READ_FAILED"
        extra = {
            "failed_stage": stage,
            "sqlite_errorcode": (getattr(exc, "sqlite_errorcode", 0) & 0xFF) or None,
            "detail": str(exc)[:160],
        }
    ev = _source_evidence(store_path, now_utc, state=state, reason=reason)
    ev.update(extra)
    return (
        {**empty, "evidence": ev},
        {"owner_state": None, "email_send": "NOT_ESTABLISHED", "evidence": dict(ev)},
    )


def read_cc153_store_hardened(
    store_path: Path | None,
    *,
    day: str,
    now_utc: str,
    digest_message_id: str | None = None,
    digest_destination: str | None = None,
    timeout_seconds: float = DEFAULT_CC153_TIMEOUT_SECONDS,
    retry_delays: tuple[float, ...] = DEFAULT_CC153_RETRY_DELAYS,
    immutable_snapshot: bool = False,
    mono_fn: Callable[[], float] = time.monotonic,
    sleep_fn: Callable[[float], None] = time.sleep,
    stage_hook: Callable[[str], None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bounded, read-only CC-153 store snapshot with zero-N+1 queries and fail-closed errors.

    - Retries ONLY genuine SQLite lock contention (``SQLITE_BUSY`` / ``SQLITE_LOCKED``)
      within ``timeout_seconds``.
    - Fails closed immediately on ``SQLITE_INTERRUPT`` (``CONTENTOPS_STORE_READ_TIMEOUT``),
      corruption/IO errors (``CONTENTOPS_STORE_READ_FAILED``), missing files
      (``CONTENTOPS_STORE_MISSING``), or invalid records (``CONTENTOPS_STORE_RECORD_INVALID``).
    - Never opens a write transaction, never runs migrations, and never masks real outages.
    """
    budget = max(0.05, float(timeout_seconds))
    start = mono_fn()
    deadline = start + budget
    delays = retry_delays or (0.0,)
    for attempt, delay in enumerate(delays, 1):
        if delay:
            wait = min(delay, max(0.0, deadline - mono_fn()))
            if wait > 0:
                sleep_fn(wait)
        try:
            store, digest_record = _read_cc153_store_once(
                store_path,
                day=day,
                now_utc=now_utc,
                deadline=deadline,
                digest_message_id=digest_message_id,
                digest_destination=digest_destination,
                immutable_snapshot=immutable_snapshot,
                mono_fn=mono_fn,
                stage_hook=stage_hook,
            )
            elapsed = round(max(0.0, mono_fn() - start), 4)
            store["evidence"].update(
                read_attempts=attempt,
                read_elapsed_seconds=elapsed,
                timeout_budget_seconds=budget,
            )
            digest_record["evidence"].update(
                read_attempts=attempt,
                read_elapsed_seconds=elapsed,
                timeout_budget_seconds=budget,
            )
            return store, digest_record
        except sqlite3.OperationalError:
            if attempt < len(delays) and mono_fn() < deadline:
                continue
            elapsed = round(max(0.0, mono_fn() - start), 4)
            ev = _source_evidence(
                store_path,
                now_utc,
                state="UNAVAILABLE",
                reason="CONTENTOPS_STORE_BUSY_RETRY_EXHAUSTED",
            )
            ev.update(
                read_attempts=attempt,
                read_elapsed_seconds=elapsed,
                timeout_budget_seconds=budget,
            )
            return (
                {
                    "admissions": None,
                    "selection_gaps": None,
                    "first_causes": None,
                    "dispatches": None,
                    "indexes_present": None,
                    "operating_control": None,
                    "evidence": ev,
                },
                {"owner_state": None, "email_send": "NOT_ESTABLISHED", "evidence": dict(ev)},
            )
    raise AssertionError("unreachable")


def read_cc153_production_day(root: Path | None, day: str, now_utc: str) -> dict[str, Any]:
    day_id = f"newsroom-production-day-{day}-bangkok"
    path = Path(root) / day_id / "newsroom_production_day_v1.json" if root else None
    empty = {"summary": None, "windows": [], "first_blocking_causes": None}
    try:
        if path is None:
            return {
                **empty,
                "evidence": _source_evidence(
                    path, now_utc, state="NOT_CONFIGURED", reason="PRODUCTION_DAY_ROOT_NOT_BOUND"
                ),
            }
        raw = _safe_read_bytes(path)
        doc = _strict_decode(raw)
        if (
            not isinstance(doc, dict)
            or doc.get("schema_version") != "contentops.newsroom_production_day.v1"
            or doc.get("newsroom_production_day_id") != day_id
            or doc.get("record_sha256") != _sha256_obj({k: v for k, v in doc.items() if k != "record_sha256"})
        ):
            raise InvalidSource("PRODUCTION_DAY_IDENTITY_OR_SEAL_INVALID")
        measurement = doc["native_volume_measurement"]
        observed = measurement["observed_at_utc"]
        _require_utc(observed)
        summary = {
            k: _nonneg_int(measurement[k])
            for k in ("admitted_items", "source_qualified_items", "distinct_canonical_items_published")
        }
        summary["confirmed_copies_by_channel"] = {
            _req_text(k, 160): _nonneg_int(v)
            for k, v in measurement["confirmed_copies_by_channel"].items()
        }
        windows = [
            {
                "window_id": _req_text(win_id, 200),
                **{
                    k: _nonneg_int(row[k])
                    for k in ("admitted_count", "distinct_canonical_published", "source_request_count")
                },
                "brief_only": row.get("brief_only") is True,
            }
            for win_id, row in measurement["windows"].items()
        ]
        first_causes = {
            _req_text(k, 160): _nonneg_int(v)
            for k, v in measurement["first_blocking_causes"].items()
        }
        return {
            "summary": summary,
            "windows": windows,
            "first_blocking_causes": first_causes,
            "evidence": _source_evidence(
                path, now_utc, latest=observed, byte_hash=sha256(raw).hexdigest()
            ),
        }
    except FileNotFoundError:
        state, reason = "MISSING", "PRODUCTION_DAY_RECORD_MISSING"
    except (InvalidSource, ValueError, KeyError, TypeError, AttributeError):
        state, reason = "INVALID", "PRODUCTION_DAY_RECORD_INVALID"
    except OSError:
        state, reason = "UNAVAILABLE", "PRODUCTION_DAY_READ_FAILED"
    return {**empty, "evidence": _source_evidence(path, now_utc, state=state, reason=reason)}


def read_cc135_published_feed(path: Path | None, day: str, now_utc: str) -> dict[str, Any]:
    try:
        if path is None:
            return {
                "items": None,
                "total_records": 0,
                "evidence": _source_evidence(
                    path, now_utc, state="NOT_CONFIGURED", reason="CC135_FEED_NOT_BOUND"
                ),
            }
        raw = _safe_read_bytes(Path(path))
        if raw and not raw.endswith(b"\n"):
            raise InvalidSource("TORN_FEED_TAIL")
        items: list[dict[str, Any]] = []
        identities: set[str] = set()
        canonicals: set[str] = set()
        clocks: list[str] = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            row = _strict_decode(line)
            if (
                not isinstance(row, dict)
                or row.get("schema_version") != "contentops.published_content.v1"
                or row.get("content_sha256")
                != _sha256_obj({k: v for k, v in row.items() if k != "content_sha256"}, ensure_ascii=False)
                or row.get("type") not in {"ARTICLE", "EVENT_PREVIEW", "EVENT_REVIEW", "DESK_NOTE"}
                or row.get("rights_class") not in {"CC_OWN_ANALYSIS", "PUBLIC_FACT_IDENTITY"}
                or row.get("visibility") != "public"
            ):
                raise InvalidSource("CC135_RECORD_INVALID")
            cid = _req_text(row["content_id"], 200)
            if cid in identities or _require_utc(row["recorded_at_utc"]) < _require_utc(row["published_at_utc"]):
                raise InvalidSource("CC135_DUPLICATE_OR_CLOCK_INVALID")
            identities.add(cid)
            clocks.append(row["recorded_at_utc"])
            outlets_raw = row.get("outlets")
            if not isinstance(outlets_raw, list) or not outlets_raw:
                raise InvalidSource("CC135_OUTLETS_MISSING")
            outlets: list[dict[str, str]] = []
            names: set[str] = set()
            urls: set[str] = set()
            for outlet in outlets_raw:
                name = _req_text(outlet["name"], 80)
                url = outlet["url"]
                if not _valid_https(url) or name in names or url in urls:
                    raise InvalidSource("CC135_OUTLET_INVALID")
                names.add(name)
                urls.add(url)
                outlets.append({"name": name, "url": url})
            canonical_url = next((o["url"] for o in outlets if o["name"] == "substack"), None)
            if not canonical_url or canonical_url in canonicals:
                raise InvalidSource("CC135_CANONICAL_MISSING_OR_DUPLICATE")
            canonicals.add(canonical_url)
            if production_date_bangkok(row["published_at_utc"]) == day:
                items.append({
                    "content_id": cid,
                    "type": row["type"],
                    "title": _req_text(row["title"]),
                    "standfirst": _req_text(row["standfirst"], 2000),
                    "published_at_utc": row["published_at_utc"],
                    "published_at_gmt7": _format_gmt7(row["published_at_utc"]),
                    "recorded_at_utc": row["recorded_at_utc"],
                    "outlets": outlets,
                })
        items.sort(key=lambda r: _require_utc(r["published_at_utc"]), reverse=True)
        latest_clock = max(clocks, key=_require_utc) if clocks else None
        return {
            "items": items,
            "total_records": len(identities),
            "evidence": _source_evidence(
                path, now_utc, latest=latest_clock, byte_hash=sha256(raw).hexdigest()
            ),
        }
    except FileNotFoundError:
        state, reason = "MISSING", "CC135_FEED_MISSING"
    except (InvalidSource, ValueError, KeyError, TypeError, AttributeError):
        state, reason = "INVALID", "CC135_FEED_INVALID"
    except OSError:
        state, reason = "UNAVAILABLE", "CC135_FEED_READ_FAILED"
    return {
        "items": None,
        "total_records": 0,
        "evidence": _source_evidence(path, now_utc, state=state, reason=reason),
    }


# ---------------------------------------------------------------------------
# Domain Readers: Pause Control, X-List Feed, CC-711, CC-817, Queue/Wraps
# ---------------------------------------------------------------------------


def read_publisher_pause_control(
    *,
    control_dir: Path | None,
    codex_exec_dir: Path | None = None,
    operating_control: Mapping[str, Any] | None = None,
    now_dt: datetime,
) -> dict[str, Any]:
    """Read-only Publisher pause/unpause, lane stop files, route suspensions, and kill switches."""
    control_root = Path(control_dir) if control_dir else None
    kill_switch_path = control_root / "KILL_SWITCH" if control_root else None
    llm_pause_path = control_root / "llm_operator_pause.flag" if control_root else None
    suspended_routes_path = control_root / "suspended_routes.json" if control_root else None

    kill_switch_file = bool(kill_switch_path and kill_switch_path.exists())
    llm_operator_paused = bool(llm_pause_path and llm_pause_path.exists())
    store_mode = str((operating_control or {}).get("operating_mode") or "")
    kill_switch_active = kill_switch_file or store_mode == "KILL_SWITCH"

    suspended_map: dict[str, str] = {}
    suspended_error: str | None = None
    if suspended_routes_path and suspended_routes_path.is_file():
        try:
            raw_routes = json.loads(_safe_read_bytes(suspended_routes_path, max_bytes=256 * 1024))
            if isinstance(raw_routes, dict):
                suspended_map = {str(k): str(v) for k, v in raw_routes.items()}
            else:
                suspended_error = "SUSPENDED_ROUTES_NOT_OBJECT"
        except (OSError, ValueError) as exc:
            suspended_error = f"SUSPENDED_ROUTES_UNREADABLE:{type(exc).__name__}"

    # Read latest pause-*/manifest.json + sibling restored.json (bounded to control_dir/pause-*).
    pause_manifest: dict[str, Any] | None = None
    pause_manifest_path: Path | None = None
    restored_doc: dict[str, Any] | None = None
    restored_path: Path | None = None
    if control_root and control_root.is_dir():
        manifests = sorted(control_root.glob("pause-*/manifest.json"), reverse=True)
        if manifests:
            pause_manifest_path = manifests[0]
            try:
                parsed = json.loads(_safe_read_bytes(pause_manifest_path, max_bytes=256 * 1024))
                if isinstance(parsed, dict):
                    pause_manifest = parsed
            except (OSError, ValueError):
                pause_manifest = None
            candidate_restored = pause_manifest_path.with_name("restored.json")
            if candidate_restored.is_file():
                restored_path = candidate_restored
                try:
                    parsed_r = json.loads(_safe_read_bytes(candidate_restored, max_bytes=256 * 1024))
                    if isinstance(parsed_r, dict):
                        restored_doc = parsed_r
                except (OSError, ValueError):
                    restored_doc = {}

    # Read publisher runner .stop files (3 fixed filenames, zero dir scanning).
    stopped_lanes: list[dict[str, Any]] = []
    if codex_exec_dir:
        exec_root = Path(codex_exec_dir)
        for stop_name in DEFAULT_PUBLISHER_STOP_NAMES:
            sp = exec_root / stop_name
            if sp.is_file():
                try:
                    note = sp.read_text(encoding="utf-8", errors="replace").strip()[:300]
                except OSError:
                    note = ""
                stopped_lanes.append({"file": stop_name, "path": str(sp), "note": note})

    pause_window_active = bool(pause_manifest is not None and restored_path is None)
    paused_at_utc = pause_manifest.get("paused_at_utc") if pause_manifest else None
    resume_at_utc = pause_manifest.get("resume_at_utc") if pause_manifest else None
    restored_at_utc = (
        (restored_doc or {}).get("ended_at_utc") or (restored_doc or {}).get("started_at_utc")
        if restored_doc is not None
        else None
    )

    all_suspended = len(ALL_DESTINATIONS) > 0 and all(d in suspended_map for d in ALL_DESTINATIONS)
    some_suspended = bool(suspended_map) and not all_suspended
    lanes_stopped = len(stopped_lanes)
    total_lanes = len(DEFAULT_PUBLISHER_STOP_NAMES)
    is_paused = pause_window_active or lanes_stopped == total_lanes or all_suspended

    if kill_switch_active:
        state = "kill_switch"
        pill = _make_pill(
            "Kill Switch Active",
            "rose",
            "Public writes are halted by operator kill switch; readback remains active.",
        )
    elif is_paused:
        state = "paused"
        resume_gmt7 = _format_gmt7(resume_at_utc)
        detail_parts = []
        if resume_gmt7:
            detail_parts.append(f"Scheduled resume {resume_gmt7}")
        if lanes_stopped:
            detail_parts.append(f"{lanes_stopped}/{total_lanes} publisher lanes stopped")
        if suspended_map:
            detail_parts.append(f"{len(suspended_map)}/{len(ALL_DESTINATIONS)} routes suspended")
        pill = _make_pill(
            "Publishing Paused",
            "amber",
            " · ".join(detail_parts) if detail_parts else "Operator publishing pause is active.",
        )
    elif llm_operator_paused:
        state = "llm_paused"
        pill = _make_pill(
            "LLM Operator Paused",
            "amber",
            "Editorial LLM operator pause flag is active.",
        )
    elif some_suspended:
        state = "partial_suspension"
        pill = _make_pill(
            f"Live · {len(suspended_map)} Route{'s' if len(suspended_map) != 1 else ''} Suspended",
            "amber",
            "Unaffected publishing destinations remain active.",
        )
    else:
        state = "live"
        resumed_gmt7 = _format_gmt7(restored_at_utc)
        detail = f"Resumed {resumed_gmt7}." if resumed_gmt7 else "All publishing destinations active."
        pill = _make_pill("Live", "emerald", detail)

    destinations = []
    for dest in ALL_DESTINATIONS:
        is_susp = dest in suspended_map
        destinations.append({
            "destination": dest,
            "label": DESTINATION_LABELS.get(dest, dest.replace("_", " ").title()),
            "status": "suspended" if is_susp else "active",
            "pill": _make_pill(
                "Route Suspended" if is_susp else "Active",
                "amber" if is_susp else "emerald",
                "Suspended by operator or platform control." if is_susp else "Destination eligible for delivery.",
            ),
        })

    mode_labels = {
        "AUTONOMOUS_DEFAULT": "Autonomous Default",
        "SUPERVISED_OPERATOR_GATE": "Supervised Operator Gate",
        "SHADOW_ONLY": "Shadow Only",
        "KILL_SWITCH": "Kill Switch",
    }
    operating_mode_label = mode_labels.get(store_mode) if store_mode else None

    return {
        "state": state,
        "pill": pill,
        "is_paused": is_paused,
        "kill_switch_active": kill_switch_active,
        "llm_operator_paused": llm_operator_paused,
        "operating_mode_label": operating_mode_label,
        "pause_window": {
            "active": pause_window_active,
            "paused_at_utc": paused_at_utc,
            "paused_at_gmt7": _format_gmt7(paused_at_utc),
            "resume_at_utc": resume_at_utc,
            "resume_at_gmt7": _format_gmt7(resume_at_utc),
            "restored_at_utc": restored_at_utc,
            "restored_at_gmt7": _format_gmt7(restored_at_utc),
            "paused_tasks_count": len(pause_manifest.get("tasks") or []) if pause_manifest else 0,
        },
        "publisher_lanes": {
            "total_expected": total_lanes,
            "stopped_count": lanes_stopped,
            "active_count": max(0, total_lanes - lanes_stopped),
            "pill": _make_pill(
                f"{lanes_stopped}/{total_lanes} Lanes Stopped" if lanes_stopped else f"{total_lanes}/{total_lanes} Lanes Active",
                "amber" if lanes_stopped else "emerald",
            ),
        },
        "destinations": destinations,
        "suspended_count": len(suspended_map),
        "active_destination_count": len(ALL_DESTINATIONS) - len(suspended_map),
        "checked_at_utc": _iso_utc(now_dt),
        "diagnostics": {
            "control_dir": str(control_root) if control_root else None,
            "pause_manifest_path": str(pause_manifest_path) if pause_manifest_path else None,
            "pause_cause": pause_manifest.get("cause") if pause_manifest else None,
            "routes_before_sha256": pause_manifest.get("routes_before_sha256") if pause_manifest else None,
            "restored_path": str(restored_path) if restored_path else None,
            "suspended_routes": suspended_map,
            "suspended_routes_error": suspended_error,
            "kill_switch_file_present": kill_switch_file,
            "llm_operator_pause_file_present": llm_operator_paused,
            "publisher_stop_files": stopped_lanes,
            "operating_control": dict(operating_control) if operating_control else None,
        },
    }


def read_x_list_feed_header(feed_path: Path | None, *, now_dt: datetime) -> dict[str, Any]:
    """Fast header-only parse of ``x_list_feed_v1.json`` (never dumps 24h raw tweet rows)."""
    if feed_path is None:
        return {
            "available": False,
            "pill": map_status_pill("X_LIST_FEED_NOT_WRITTEN"),
            "generated_at_utc": None,
            "generated_at_gmt7": None,
            "age_seconds": None,
            "window_hours": None,
            "row_count": None,
            "newest_posted_utc": None,
            "newest_age_seconds": None,
            "median_ingest_lag_seconds": None,
            "market_hours": None,
            "failure_streak": None,
            "last_good_capture_utc": None,
            "last_good_age_seconds": None,
            "p1_active": False,
            "p1_summary": None,
            "last_heal_at_utc": None,
            "diagnostics": {"source_path": None, "raw_cause": "X_LIST_FEED_NOT_WRITTEN"},
        }
    path = Path(feed_path)
    try:
        if not path.is_file():
            raise FileNotFoundError(str(path))
        with path.open("rb") as stream:
            head_bytes = stream.read(MAX_X_FEED_HEADER_BYTES)
        marker = b', "rows": ['
        if marker in head_bytes:
            header_doc = json.loads(head_bytes.split(marker, 1)[0] + b"}")
        else:
            # Small feed without split marker (e.g. unit test fixture); parse whole file bounded.
            header_doc = json.loads(_safe_read_bytes(path, max_bytes=4 * 1024 * 1024))
        if not isinstance(header_doc, dict):
            raise ValueError("X_LIST_FEED_NOT_OBJECT")
    except FileNotFoundError:
        return {
            "available": False,
            "pill": map_status_pill("X_LIST_FEED_NOT_WRITTEN"),
            "generated_at_utc": None,
            "generated_at_gmt7": None,
            "age_seconds": None,
            "window_hours": None,
            "row_count": None,
            "newest_posted_utc": None,
            "newest_age_seconds": None,
            "median_ingest_lag_seconds": None,
            "market_hours": None,
            "failure_streak": None,
            "last_good_capture_utc": None,
            "last_good_age_seconds": None,
            "p1_active": False,
            "p1_summary": None,
            "last_heal_at_utc": None,
            "diagnostics": {"source_path": str(path), "raw_cause": "X_LIST_FEED_NOT_WRITTEN"},
        }
    except (OSError, ValueError) as exc:
        return {
            "available": False,
            "pill": map_status_pill("X_LIST_FEED_UNREADABLE"),
            "generated_at_utc": None,
            "generated_at_gmt7": None,
            "age_seconds": None,
            "window_hours": None,
            "row_count": None,
            "newest_posted_utc": None,
            "newest_age_seconds": None,
            "median_ingest_lag_seconds": None,
            "market_hours": None,
            "failure_streak": None,
            "last_good_capture_utc": None,
            "last_good_age_seconds": None,
            "p1_active": False,
            "p1_summary": None,
            "last_heal_at_utc": None,
            "diagnostics": {
                "source_path": str(path),
                "raw_cause": "X_LIST_FEED_UNREADABLE",
                "error": str(exc)[:160],
            },
        }

    generated_at = header_doc.get("generated_at_utc")
    gen_dt = _parse_utc(generated_at)
    age_seconds = round(max(0.0, (now_dt - gen_dt).total_seconds()), 1) if gen_dt else None
    health = header_doc.get("health") if isinstance(header_doc.get("health"), dict) else {}
    capture = header_doc.get("capture") if isinstance(header_doc.get("capture"), dict) else {}
    use_info = header_doc.get("use") if isinstance(header_doc.get("use"), dict) else {}

    raw_health_state = str(health.get("state") or "").upper() or None
    stale_after = _safe_num(health.get("stale_after_seconds")) or 180.0
    p1_obj = health.get("p1") if isinstance(health.get("p1"), dict) else None
    p1_active = p1_obj is not None or raw_health_state == "P1"
    is_stale = bool(health.get("stale")) or (age_seconds is not None and age_seconds > max(stale_after, 180.0))

    if gen_dt is None:
        pill = map_status_pill("X_LIST_FEED_CLOCK_INVALID")
    elif p1_active:
        pill = _make_pill("P1 Alert", "rose", "X-list feed reported consecutive capture failures.")
    elif is_stale or raw_health_state == "STALE":
        pill = _make_pill(
            "Stale",
            "amber",
            f"Last export was {int(age_seconds)}s ago." if age_seconds is not None else "Feed export is stale.",
        )
    else:
        pill = _make_pill(
            "Live",
            "emerald",
            f"Updated {int(age_seconds)}s ago." if age_seconds is not None else "Capture healthy.",
        )

    last_heal = health.get("last_heal") if isinstance(health.get("last_heal"), dict) else {}
    last_heal_at = last_heal.get("replaced_utc") or last_heal.get("at_utc") or last_heal.get("attempted_utc")
    row_count = _safe_int(header_doc.get("row_count"))
    if row_count is None and isinstance(header_doc.get("rows"), list):
        row_count = len(header_doc["rows"])

    return {
        "available": gen_dt is not None,
        "pill": pill,
        "generated_at_utc": generated_at if gen_dt else None,
        "generated_at_gmt7": _format_gmt7(gen_dt),
        "age_seconds": age_seconds,
        "window_hours": _safe_num(header_doc.get("window_hours")),
        "row_count": row_count,
        "newest_posted_utc": header_doc.get("newest_posted_utc"),
        "newest_age_seconds": _safe_num(header_doc.get("newest_age_seconds")),
        "median_ingest_lag_seconds": _safe_num(header_doc.get("ingest_lag_seconds_median_last_hour")),
        "market_hours": health.get("market_hours") if isinstance(health.get("market_hours"), bool) else None,
        "failure_streak": _safe_int(health.get("failure_streak")),
        "last_good_capture_utc": health.get("last_good_capture_utc"),
        "last_good_age_seconds": _safe_num(health.get("last_good_age_seconds")),
        "p1_active": p1_active,
        "p1_summary": str(p1_obj.get("plain"))[:240] if p1_obj and p1_obj.get("plain") else None,
        "last_heal_at_utc": last_heal_at,
        "diagnostics": {
            "source_path": str(path),
            "schema_version": header_doc.get("schema_version"),
            "raw_health_state": raw_health_state,
            "raw_capture_state": capture.get("state"),
            "failure_cause": health.get("failure_cause"),
            "stale_after_seconds": stale_after,
            "interval_seconds": _safe_num(health.get("interval_seconds")),
            "last_p1": health.get("last_p1"),
            "source_grant": use_info.get("source_grant") if use_info else (
                header_doc.get("use") if isinstance(header_doc.get("use"), str) else None
            ),
        },
    }


def read_keepalive_and_neo_health(
    *,
    x_feed_dir: Path | None,
    probe_live: bool = False,
    x_status_fn: Callable[[], Mapping[str, Any]] | None = None,
    neo_probe_fn: Callable[[], Mapping[str, Any]] | None = None,
    cached_neo_reply_status: Mapping[str, Any] | None = None,
    now_dt: datetime,
) -> dict[str, Any]:
    """Read-only CC-711 X-list keepalive and BrowserOS Neo health summary."""
    from live_contentops import cc711_xfeed_neo_keepalive_v1 as cc711

    x_raw: dict[str, Any]
    if x_status_fn is not None:
        x_raw = dict(x_status_fn())
    elif x_feed_dir is not None:
        root = Path(x_feed_dir)
        x_raw = dict(
            cc711.status_x_list_feed(
                lock_path=root / "runner_v1.lock",
                stop_path=root / "STOP",
                feed_path=root / "x_list_feed_v1.json",
                now_fn=lambda: now_dt,
            )
        )
    else:
        x_raw = {"state": "UNAVAILABLE", "runner_alive": False, "stop_present": False, "feed": {}}

    x_state = str(x_raw.get("state") or "UNAVAILABLE").upper()
    x_pill_map = {
        "RUNNING": _make_pill("Runner Active", "emerald", "X-list feed runner OS lock is held."),
        "STOP_FILE_PRESENT": _make_pill("Stopped", "amber", "Operator STOP file is present."),
        "READY": _make_pill("Chrome Ready · Idle", "amber", "CDP 9222 responds, but runner lock is not held."),
        "CDP_PROBE_STARVED": _make_pill("Chrome Busy", "amber", "Canonical Chrome 9222 is alive under load; duplicate launch held."),
        "RUNNING_WITHOUT_CDP": _make_pill("No CDP Port", "amber", "Canonical Chrome profile active without CDP 9222."),
        "PORT_OWNER_UNPROVEN": _make_pill("Port Unproven", "amber", "Port 9222 listener is not proven canonical Chrome."),
        "UNAVAILABLE": _make_pill("Offline", "rose", "X-list runner and Chrome CDP 9222 are not active."),
    }
    x_pill = x_pill_map.get(x_state, map_status_pill(x_state))

    neo_raw: dict[str, Any] | None = None
    probe_mode = "NOT_PROBED"
    if neo_probe_fn is not None:
        neo_raw = dict(neo_probe_fn())
        probe_mode = "INJECTED_PROBE"
    elif probe_live:
        neo_raw = dict(cc711.probe_browseros_neo(now_fn=lambda: now_dt))
        probe_mode = "LIVE_LOOPBACK_PROBE"

    if neo_raw is not None:
        neo_state = str(neo_raw.get("state") or "DOWN").upper()
        neo_pill_map = {
            "HEALTHY": _make_pill("Healthy", "emerald", "BrowserOS Neo CDP and MCP SSE both respond cleanly."),
            "READY": _make_pill("Healthy", "emerald", "BrowserOS Neo CDP and MCP SSE both respond cleanly."),
            "DEGRADED_MCP_CDP_ALIVE": _make_pill("MCP Degraded", "amber", "CDP responds while MCP endpoint is degraded."),
            "DEGRADED_MCP_DOWN": _make_pill("MCP Degraded", "amber", "CDP responds while MCP endpoint is down."),
            "DEGRADED_CDP_MCP_ALIVE": _make_pill("CDP Degraded", "amber", "MCP responds while CDP port is degraded."),
            "NEO_PROBE_STARVED": _make_pill("Busy · Starved", "amber", "BrowserOS process is alive under load; restart held."),
            "PROCESS_PROBE_UNPROVEN": _make_pill("Probe Unproven", "amber", "Process presence could not be proven; restart held."),
            "DOWN": _make_pill("Offline", "rose", "BrowserOS Neo CDP, MCP, and processes are down."),
        }
        neo_pill = neo_pill_map.get(neo_state, map_status_pill(neo_state))
        cdp_info = neo_raw.get("cdp") if isinstance(neo_raw.get("cdp"), Mapping) else {}
        mcp_info = neo_raw.get("mcp") if isinstance(neo_raw.get("mcp"), Mapping) else {}
        ports_info = neo_raw.get("ports") if isinstance(neo_raw.get("ports"), Mapping) else {}
        neo_section = {
            "pill": neo_pill,
            "probed": True,
            "cdp_alive": bool(cdp_info.get("cdp_alive") or cdp_info.get("ok")),
            "mcp_alive": bool(mcp_info.get("mcp_alive") or mcp_info.get("ok")),
            "process_alive": bool(neo_raw.get("process_alive")),
            "browseros_version": ports_info.get("browseros_version"),
            "mcp_server_version": mcp_info.get("server_version") or None,
            "checked_at_utc": neo_raw.get("checked_at_utc") or _iso_utc(now_dt),
            "checked_at_gmt7": _format_gmt7(neo_raw.get("checked_at_utc") or now_dt),
            "ports": {
                "cdp_port": ports_info.get("cdp_port"),
                "mcp_port": ports_info.get("mcp_port"),
                "server_port": ports_info.get("server_port"),
            },
            "diagnostics": {
                "probe_mode": probe_mode,
                "raw_state": neo_state,
                "cdp": dict(cdp_info),
                "mcp": dict(mcp_info),
                "process_count": neo_raw.get("process_count"),
                "process_probe_ok": neo_raw.get("process_probe_ok"),
                "listener_pids": neo_raw.get("listener_pids"),
                "cached_reply_tabs": dict(cached_neo_reply_status) if cached_neo_reply_status else None,
            },
        }
    else:
        ports = cc711.load_browseros_ports()
        neo_section = {
            "pill": _make_pill("Not Probed", "neutral", "Run with --probe-live-neo for live loopback CDP/MCP check."),
            "probed": False,
            "cdp_alive": None,
            "mcp_alive": None,
            "process_alive": None,
            "browseros_version": ports.get("browseros_version"),
            "mcp_server_version": None,
            "checked_at_utc": None,
            "checked_at_gmt7": None,
            "ports": {
                "cdp_port": ports.get("cdp_port"),
                "mcp_port": ports.get("mcp_port"),
                "server_port": ports.get("server_port"),
            },
            "diagnostics": {
                "probe_mode": probe_mode,
                "raw_state": None,
                "config_found": ports.get("config_found"),
                "cached_reply_tabs": dict(cached_neo_reply_status) if cached_neo_reply_status else None,
            },
        }

    # Combined summary pill for the status strip.
    if x_pill["tone"] == "emerald" and (not neo_section["probed"] or neo_section["pill"]["tone"] == "emerald"):
        combined_pill = _make_pill(
            "Healthy" if neo_section["probed"] else "X-Feed Active",
            "emerald",
            "CC-711 keepalive and BrowserOS Neo checks are healthy."
            if neo_section["probed"]
            else "X-list runner active; Neo live probe not requested.",
        )
    elif x_pill["tone"] == "rose" or neo_section["pill"]["tone"] == "rose":
        combined_pill = _make_pill("Attention Needed", "rose", "One or more local browser/feed services are offline.")
    else:
        combined_pill = _make_pill("Degraded", "amber", "Inspect keepalive and BrowserOS Neo details.")

    feed_sub = x_raw.get("feed") if isinstance(x_raw.get("feed"), Mapping) else {}
    return {
        "pill": combined_pill,
        "x_feed_keepalive": {
            "pill": x_pill,
            "runner_alive": bool(x_raw.get("runner_alive")),
            "stop_present": bool(x_raw.get("stop_present")),
            "feed_age_seconds": _safe_num(feed_sub.get("age_seconds")),
            "checked_at_utc": x_raw.get("checked_at_utc") or _iso_utc(now_dt),
            "checked_at_gmt7": _format_gmt7(x_raw.get("checked_at_utc") or now_dt),
            "diagnostics": {
                "raw_state": x_state,
                "cdp": x_raw.get("cdp"),
                "feed": dict(feed_sub),
            },
        },
        "browseros_neo": neo_section,
    }


def _collect_private_canaries(obj: Any, bucket: set[str], *, inside_private: bool = False) -> None:
    """Harvest private canary strings from input documents so the final leak gate verifies zero echo."""
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            key_l = str(k).lower()
            is_priv = inside_private or key_l in FORBIDDEN_PRIVATE_KEYS
            if key_l == "watch_items" or key_l == "watch_signals":
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, Mapping) and str(item.get("kind") or "").lower() in _PRIVATE_WATCH_KINDS:
                            _collect_private_canaries(item, bucket, inside_private=True)
                    continue
            _collect_private_canaries(v, bucket, inside_private=is_priv)
    elif isinstance(obj, list):
        for item in obj:
            _collect_private_canaries(item, bucket, inside_private=inside_private)
    elif isinstance(obj, str) and inside_private:
        cleaned = " ".join(obj.split())
        if len(cleaned) >= 8:
            bucket.add(cleaned)


def _project_attention_theme_allowlist(raw_theme: Mapping[str, Any]) -> dict[str, Any]:
    """Strict allow-list projection of a CC-807/CC-817 theme (zero private keys or market odds numbers)."""
    status_raw = str(raw_theme.get("status") or "active").lower()
    status_pill_map = {
        "active": _make_pill("Active", "emerald"),
        "emerging": _make_pill("Emerging", "amber"),
        "watching": _make_pill("Watching", "neutral"),
        "resolving": _make_pill("Resolving", "amber"),
        "fading": _make_pill("Fading", "neutral"),
        "resolved": _make_pill("Resolved", "neutral"),
    }
    status_pill = status_pill_map.get(status_raw, _make_pill(status_raw.title(), "neutral"))

    branches_out: list[dict[str, Any]] = []
    for raw_br in raw_theme.get("branches") or []:
        if not isinstance(raw_br, Mapping):
            continue
        raw_kind = str(raw_br.get("kind") or raw_br.get("role") or "alternative").lower()
        kind_code, kind_label = _BRANCH_KIND_LABELS.get(raw_kind, ("alternative", "Alternative"))
        prob_source = str(raw_br.get("probability_source") or "").lower()
        prob_pct = _safe_num(raw_br.get("probability_pct"))
        # Strict CC-817 rule: NEVER expose numeric market-implied odds (Kalshi/Polymarket/FedWatch).
        if prob_source in _MARKET_PROBABILITY_SOURCES:
            prob_pct = None
            prob_label = None
        elif prob_pct is not None and (not prob_source or prob_source in _OWN_PROBABILITY_SOURCES):
            prob_label = str(raw_br.get("probability_label") or f"{int(prob_pct) if prob_pct.is_integer() else prob_pct}% (Capital Chronicle estimate)")
        else:
            prob_pct = None
            prob_label = None
        branches_out.append({
            "kind": kind_code,
            "label": kind_label,
            "summary": str(raw_br.get("summary") or raw_br.get("description") or "").strip()[:280],
            "probability_pct": prob_pct,
            "probability_label": prob_label,
            "invalidation": str(raw_br.get("invalidation") or "").strip()[:200] or None,
        })

    dp_out: list[dict[str, Any]] = []
    for dp in raw_theme.get("decision_points") or []:
        if not isinstance(dp, Mapping):
            continue
        at_utc = dp.get("at_utc") or dp.get("scheduled_at_utc")
        dp_status = str(dp.get("status") or "upcoming").lower()
        dp_out.append({
            "id": str(dp.get("id") or dp.get("event_id") or "")[:120] or None,
            "title": str(dp.get("title") or dp.get("name") or "").strip()[:160],
            "at_utc": at_utc if _parse_utc(at_utc) else None,
            "date_et": str(dp.get("date_et") or _format_et_date(at_utc) or "") or None,
            "status": "hit" if dp_status in {"hit", "triggered", "released", "confirmed", "passed", "occurred"} else "upcoming",
        })

    affected = [
        str(m).upper()
        for m in (raw_theme.get("affected_markets") or [])
        if isinstance(m, str) and m.strip()
    ][:10]
    updated_at = raw_theme.get("updated_at_utc")
    return {
        "theme_id": str(raw_theme.get("theme_id") or raw_theme.get("id") or "")[:120],
        "name": str(raw_theme.get("name") or raw_theme.get("title") or "Untitled Theme").strip()[:160],
        "one_line": str(raw_theme.get("one_line") or raw_theme.get("summary") or "").strip()[:280],
        "status": status_raw,
        "status_pill": status_pill,
        "rank": _safe_int(raw_theme.get("rank")),
        "lead_market": str(raw_theme.get("lead_market") or "").upper() or None,
        "affected_markets": affected,
        "updated_at_utc": updated_at if _parse_utc(updated_at) else None,
        "updated_at_et": str(raw_theme.get("updated_at_et") or _format_et_date(updated_at) or "") or None,
        "market_lean_words": str(raw_theme.get("market_lean_words") or "").strip()[:200] or None,
        "priced_in_words": str(raw_theme.get("priced_in_words") or "").strip()[:200] or None,
        "branches": branches_out[:4],
        "decision_points": dp_out[:6],
    }


def read_attention_map_summary(
    *,
    live_map_path: Path | None,
    ledger_path: Path | None = None,
    pulse_path: Path | None = None,
    now_dt: datetime,
) -> tuple[dict[str, Any], set[str]]:
    """Read optional CC-807/CC-817 attention map, high-interval ledger, and session-sync pulse.

    Returns ``(section_dict, captured_private_canaries)``. Guarantees zero ``_private_texts``
    or forbidden private keys enter the summary.
    """
    canaries: set[str] = set()
    map_doc: dict[str, Any] | None = None
    map_state = "MISSING"
    map_reason = "ATTENTION_MAP_LIVE_FILE_ABSENT"
    if live_map_path and Path(live_map_path).is_file():
        try:
            raw_doc = json.loads(_safe_read_bytes(Path(live_map_path), max_bytes=8 * 1024 * 1024))
            if isinstance(raw_doc, dict):
                _collect_private_canaries(raw_doc, canaries)
                map_doc = raw_doc
                map_state = "AVAILABLE"
                map_reason = None
            else:
                map_state, map_reason = "INVALID", "ATTENTION_MAP_NOT_OBJECT"
        except (OSError, ValueError):
            map_state, map_reason = "UNAVAILABLE", "ATTENTION_MAP_UNREADABLE"

    ledger_doc: dict[str, Any] | None = None
    if ledger_path and Path(ledger_path).is_file():
        try:
            raw_led = json.loads(_safe_read_bytes(Path(ledger_path), max_bytes=4 * 1024 * 1024))
            if isinstance(raw_led, dict):
                _collect_private_canaries(raw_led, canaries)
                ledger_doc = raw_led
        except (OSError, ValueError):
            ledger_doc = None

    pulse_doc: dict[str, Any] | None = None
    if pulse_path and Path(pulse_path).is_file():
        try:
            raw_pulse = json.loads(_safe_read_bytes(Path(pulse_path), max_bytes=1 * 1024 * 1024))
            if isinstance(raw_pulse, dict):
                _collect_private_canaries(raw_pulse, canaries)
                pulse_doc = raw_pulse
        except (OSError, ValueError):
            pulse_doc = None

    if map_doc is None:
        return (
            {
                "available": False,
                "pill": map_status_pill(map_reason),
                "as_of_utc": None,
                "as_of_et": None,
                "as_of_gmt7": None,
                "age_minutes": None,
                "theme_count": 0,
                "live_theme_ids": [],
                "top_themes": [],
                "cadence_interval_minutes": None,
                "last_poll_pill": _make_pill("Not Active Yet", "neutral", "High-interval poller has not written a ledger yet."),
                "dispatched_flash_count": 0,
                "suppressed_cooldown_count": 0,
                "latest_session_pulse": None,
                "diagnostics": {
                    "map_path": str(live_map_path) if live_map_path else None,
                    "map_state": map_state,
                    "map_reason": map_reason,
                    "ledger_path": str(ledger_path) if ledger_path else None,
                    "pulse_path": str(pulse_path) if pulse_path else None,
                },
            },
            canaries,
        )

    as_of_utc = map_doc.get("as_of_utc") or map_doc.get("generated_at_utc")
    as_of_dt = _parse_utc(as_of_utc)
    age_minutes = round(max(0.0, (now_dt - as_of_dt).total_seconds()) / 60.0, 1) if as_of_dt else None
    raw_themes = map_doc.get("themes") if isinstance(map_doc.get("themes"), list) else []
    projected = [_project_attention_theme_allowlist(t) for t in raw_themes if isinstance(t, Mapping)]
    projected.sort(key=lambda t: (t["rank"] is None, t["rank"] if t["rank"] is not None else 999, t["theme_id"]))
    live_ids = [t["theme_id"] for t in projected if t["status"] in {"active", "emerging", "resolving", "watching"}]
    top_themes = projected[:5]

    cadence = map_doc.get("cadence_metadata") if isinstance(map_doc.get("cadence_metadata"), Mapping) else {}
    interval_min = _safe_int(cadence.get("interval_minutes"))
    is_stale = age_minutes is not None and age_minutes > 90.0
    if is_stale:
        pill = _make_pill(
            f"Stale · {len(top_themes)} Theme{'s' if len(top_themes) != 1 else ''}",
            "amber",
            f"Last updated {int(age_minutes)}m ago.",
        )
    else:
        pill = _make_pill(
            f"Live · {len(top_themes)} Theme{'s' if len(top_themes) != 1 else ''}",
            "emerald",
            f"As of {_format_gmt7(as_of_dt)}." if as_of_dt else "Attention map loaded.",
        )

    dispatched_flashes = (
        len(ledger_doc.get("dispatched_events") or {})
        if isinstance(ledger_doc, Mapping) and isinstance(ledger_doc.get("dispatched_events"), Mapping)
        else 0
    )
    suppressed_count = (
        len(ledger_doc.get("suppressed_events") or [])
        if isinstance(ledger_doc, Mapping) and isinstance(ledger_doc.get("suppressed_events"), list)
        else 0
    )
    last_poll_utc = ledger_doc.get("last_poll_as_of_utc") if isinstance(ledger_doc, Mapping) else None
    last_poll_pill = (
        _make_pill("Polled", "emerald", f"Last poll {_format_gmt7(last_poll_utc)}.")
        if _parse_utc(last_poll_utc)
        else _make_pill("No Poll Ledger", "neutral", "High-interval poll ledger not present.")
    )

    pulse_summary = None
    if isinstance(pulse_doc, Mapping):
        pulse_summary = {
            "session": pulse_doc.get("session"),
            "session_label": pulse_doc.get("session_label"),
            "heading": pulse_doc.get("heading"),
            "as_of_utc": pulse_doc.get("as_of_utc"),
            "as_of_et": pulse_doc.get("as_of_et") or _format_et_date(pulse_doc.get("as_of_utc")),
            "flash_count": _safe_int(pulse_doc.get("flash_count")),
            "top_lines": [str(line)[:220] for line in (pulse_doc.get("top_lines") or [])[:5]],
        }

    return (
        {
            "available": True,
            "pill": pill,
            "as_of_utc": as_of_utc if as_of_dt else None,
            "as_of_et": str(map_doc.get("as_of_et") or _format_et_date(as_of_dt) or "") or None,
            "as_of_gmt7": _format_gmt7(as_of_dt),
            "age_minutes": age_minutes,
            "theme_count": len(projected),
            "live_theme_ids": live_ids[:10],
            "top_themes": top_themes,
            "cadence_interval_minutes": interval_min,
            "last_poll_pill": last_poll_pill,
            "dispatched_flash_count": dispatched_flashes,
            "suppressed_cooldown_count": suppressed_count,
            "latest_session_pulse": pulse_summary,
            "diagnostics": {
                "map_path": str(live_map_path) if live_map_path else None,
                "map_state": map_state,
                "map_reason": map_reason,
                "schema_version": map_doc.get("schema_version"),
                "register_sha256": map_doc.get("register_sha256"),
                "ledger_path": str(ledger_path) if ledger_path else None,
                "last_poll_as_of_utc": last_poll_utc,
                "pulse_path": str(pulse_path) if pulse_path else None,
                "private_canaries_stripped_count": len(canaries),
            },
        },
        canaries,
    )


def _format_reply_filter_summary(filter_causes: Mapping[str, Any] | None) -> str | None:
    if not isinstance(filter_causes, Mapping) or not filter_causes:
        return None
    label_map = {
        "NO_SIX_MARKET_OR_MACRO_TOPIC": "off-topic",
        "TARGET_OVER_15_MINUTES_AT_SEND": "older than 15m",
        "TARGET_TOO_OLD": "too old",
        "DUPLICATE_TARGET": "duplicate",
        "LOW_SIGNAL": "low signal",
    }
    total = 0
    parts: list[str] = []
    for raw_k, raw_v in sorted(filter_causes.items()):
        count = _safe_int(raw_v)
        if count is None or count <= 0:
            continue
        total += count
        human = label_map.get(str(raw_k), "other checks")
        parts.append(f"{count:,} {human}")
    if total == 0:
        return None
    return f"{total:,} filtered (" + " · ".join(parts[:4]) + ")"


def _classify_wrap_category(piece: Mapping[str, Any]) -> str:
    raw_kind = str(piece.get("kind") or "ARTICLE").upper()
    work_item = str(piece.get("work_item") or "")
    title = str(piece.get("title") or "")
    if raw_kind in {"WEEKEND_WRAP", "DAILY_DIGEST"} or _WRAP_WORK_ITEM_RE.search(work_item) or _WRAP_TITLE_RE.search(title):
        return "wrap_or_digest"
    if raw_kind == "EVENT_PREVIEW":
        return "event_preview"
    if raw_kind == "EVENT_REVIEW":
        return "event_review"
    return "article"


def _read_image_register_summary(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "pill": map_status_pill("PUBLISHED_IMAGES_NOT_WRITTEN"),
            "record_count": 0,
            "latest_at_utc": None,
            "latest_at_gmt7": None,
            "diagnostics": {"path": None, "raw_cause": "PUBLISHED_IMAGES_NOT_WRITTEN"},
        }
    p = Path(path)
    active: dict[str, Any] = {}
    latest_dt: datetime | None = None
    latest_raw: str | None = None
    raw_cause: str | None = None
    try:
        with p.open(encoding="utf-8-sig") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict) or row.get("schema_version") != "contentops.published_images.v1":
                        raise ValueError("schema")
                    active[str(row["record_id"])] = True
                    ts = row.get("recorded_at_utc")
                    dt = _parse_utc(ts)
                    if dt and (latest_dt is None or dt > latest_dt):
                        latest_dt = dt
                        latest_raw = ts
                except (ValueError, KeyError):
                    raw_cause = "IMAGE_REGISTER_INVALID_ROW"
    except FileNotFoundError:
        raw_cause = "PUBLISHED_IMAGES_NOT_WRITTEN"
    except OSError:
        raw_cause = "PUBLISHED_IMAGES_UNREADABLE"

    pill = (
        map_status_pill(raw_cause)
        if raw_cause
        else _make_pill(f"{len(active):,} Images Logged", "emerald", "Published image register verified.")
    )
    return {
        "pill": pill,
        "record_count": len(active),
        "latest_at_utc": latest_raw,
        "latest_at_gmt7": _format_gmt7(latest_dt),
        "diagnostics": {"path": str(p), "raw_cause": raw_cause},
    }


def _read_desk_state_optional(path: Path | None) -> dict[str, Any]:
    if path is None or not Path(path).is_file():
        return {}
    try:
        parsed = json.loads(_safe_read_bytes(Path(path), max_bytes=8 * 1024 * 1024))
        return parsed if isinstance(parsed, dict) else {}
    except (OSError, ValueError):
        return {}


def _read_wraps_from_store_or_desk(
    *,
    store_path: Path | None,
    desk_js_path: Path | None,
    immutable_snapshot: bool = False,
) -> tuple[list[dict[str, Any]], str]:
    """Read confirmed Substack pieces from desk.js wraps snapshot (if present) or SQLite store."""
    if desk_js_path and Path(desk_js_path).is_file():
        try:
            raw = _safe_read_bytes(Path(desk_js_path), max_bytes=16 * 1024 * 1024).decode("utf-8")
            start = raw.index("{")
            end = raw.rindex("}") + 1
            desk = json.loads(raw[start:end])
            wraps = desk.get("wraps") if isinstance(desk, dict) else None
            pieces = wraps.get("pieces") if isinstance(wraps, dict) else None
            if isinstance(pieces, list):
                return [p for p in pieces if isinstance(p, dict)], "desk.js"
        except (OSError, ValueError):
            pass

    if store_path and Path(store_path).is_file():
        try:
            conn, _ = _open_readonly_sqlite(
                Path(store_path), timeout_seconds=1.5, immutable_snapshot=immutable_snapshot
            )
            try:
                rows = conn.execute(
                    "SELECT d.platform, d.dispatched_at, d.public_object_url, m.work_item_id, m.payload "
                    "FROM platform_dispatches d JOIN outbox_messages m ON m.message_id = d.message_id "
                    "WHERE d.status = 'DISPATCH_CONFIRMED' ORDER BY d.dispatched_at DESC"
                ).fetchall()
            finally:
                conn.close()
            by_url: dict[str, dict[str, Any]] = {}
            for row in rows:
                platform = str(row["platform"] or "")
                url = str(row["public_object_url"] or "")
                try:
                    payload = json.loads(row["payload"] or "{}")
                except ValueError:
                    payload = {}
                req = payload.get("request") if isinstance(payload.get("request"), dict) else {}
                canonical = url if platform == "substack" and url else (req.get("canonical_url") or payload.get("canonical_url"))
                if not canonical or not str(canonical).startswith("https://capitalchronicle.substack.com/p/"):
                    continue
                entry = by_url.setdefault(
                    str(canonical),
                    {
                        "url": str(canonical),
                        "slug": str(canonical).rsplit("/p/", 1)[-1],
                        "title": str(canonical).rsplit("/p/", 1)[-1].replace("-", " ").capitalize(),
                        "dek": None,
                        "kind": "ARTICLE",
                        "published_at_utc": None,
                        "work_item": row["work_item_id"],
                        "outlets": [],
                        "_outlet_map": {},
                        "package": None,
                        "package_gap": "REVIEWED_PACKAGE_NOT_FOUND",
                        "scenario_analysis": None,
                        "copy_sha256": None,
                    },
                )
                if platform == "substack" and row["dispatched_at"]:
                    entry["published_at_utc"] = row["dispatched_at"]
                if _valid_https(url):
                    entry["_outlet_map"].setdefault(platform, url)
            out = []
            for entry in by_url.values():
                if not entry["published_at_utc"]:
                    continue
                om = entry.pop("_outlet_map")
                entry["outlets"] = [{"name": "substack", "url": entry["url"]}] + [
                    {"name": k, "url": v} for k, v in sorted(om.items()) if k != "substack"
                ]
                out.append(entry)
            out.sort(key=lambda r: _parse_utc(r["published_at_utc"]) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            return out, "sqlite_store"
        except (OSError, sqlite3.Error, ValueError):
            pass
    return [], "unavailable"


def _build_posts_section(desk_state: Mapping[str, Any], *, paused: bool) -> dict[str, Any]:
    queues_data = ((desk_state.get("sections") or {}).get("queues") or {}).get("data") or {}
    raw_posts = queues_data.get("posts") if isinstance(queues_data.get("posts"), list) else []
    items: list[dict[str, Any]] = []
    today_count = 0
    prior_day_retained = False
    for post in raw_posts[:20]:
        if not isinstance(post, Mapping):
            continue
        is_prior = bool(post.get("prior_day"))
        if is_prior:
            prior_day_retained = True
        else:
            today_count += 1
        raw_status = str(post.get("status") or "Queued")
        status_tone = (
            "emerald"
            if raw_status == "Posted"
            else "amber"
            if raw_status in {"Waiting for chart", "Held by check"}
            else "neutral"
        )
        qa_score = _safe_num(post.get("qa_score"))
        has_image = bool(post.get("image"))
        image_cause = post.get("image_cause")
        image_pill = (
            _make_pill("Chart Attached", "emerald")
            if has_image
            else map_status_pill(str(image_cause)) if image_cause else _make_pill("Text Only", "neutral")
        )
        raw_platforms = post.get("platforms") if isinstance(post.get("platforms"), Mapping) else {}
        clean_platforms = {
            str(k): str(v)
            for k, v in raw_platforms.items()
            if str(v) in {"posted", "queued", "held", "failed"}
        }
        items.append({
            "id": str(post.get("id") or "")[:160],
            "type": str(post.get("type") or "Note")[:40],
            "market": str(post.get("market"))[:40] if post.get("market") else None,
            "title": str(post.get("title") or "Untitled Post")[:200],
            "status_pill": _make_pill(
                f"{raw_status} · Prior Day" if is_prior and raw_status == "Posted" else raw_status,
                status_tone,
            ),
            "at_utc": post.get("at"),
            "at_gmt7": _format_gmt7(post.get("at")),
            "prior_day": is_prior,
            "qa_score": qa_score,
            "has_image": has_image,
            "image_pill": image_pill,
            "href": post.get("href") if _valid_https(post.get("href")) else None,
            "platforms": clean_platforms,
            "diagnostics": {
                "qa_cause": post.get("qa_cause"),
                "image_cause": image_cause,
                "image_sha256": post.get("image_sha256"),
                "checklist_count": len(post.get("checklist") or []) if isinstance(post.get("checklist"), list) else 0,
                "dispatches": post.get("dispatches") if isinstance(post.get("dispatches"), list) else [],
            },
        })

    last_post_at = queues_data.get("last_post_at") or (items[0]["at_utc"] if items else None)
    post_cause = queues_data.get("post_cause")
    if items:
        pill_label = (
            f"{today_count} Today"
            if today_count > 0
            else f"Paused · {len(items)} Recent" if paused else f"{len(items)} Recent"
        )
        pill = _make_pill(pill_label, "emerald" if today_count > 0 else "neutral")
    elif post_cause:
        pill = map_status_pill(str(post_cause))
    else:
        pill = _make_pill("Paused · Queue Quiet" if paused else "Queue Empty", "neutral")

    return {
        "pill": pill,
        "count": len(items),
        "today_count": today_count,
        "prior_day_retained": prior_day_retained,
        "last_post_at_utc": last_post_at,
        "last_post_at_gmt7": _format_gmt7(last_post_at),
        "items": items,
        "diagnostics": {
            "posts_at_utc": queues_data.get("posts_at"),
            "raw_post_cause": post_cause,
        },
    }


def _build_wraps_section(raw_pieces: list[dict[str, Any]], source_kind: str) -> dict[str, Any]:
    counts = Counter({"wrap_or_digest": 0, "article": 0, "event_preview": 0, "event_review": 0})
    recent: list[dict[str, Any]] = []
    for piece in raw_pieces:
        cat = _classify_wrap_category(piece)
        counts[cat] += 1
        if len(recent) < 15:
            outlets = piece.get("outlets") if isinstance(piece.get("outlets"), list) else []
            outlet_names = [
                str(o.get("name"))
                for o in outlets
                if isinstance(o, Mapping) and o.get("name")
            ]
            scenarios = piece.get("scenario_analysis")
            scenario_count = len(scenarios) if isinstance(scenarios, list) else 0
            link_only = not bool(piece.get("package")) and not bool(piece.get("in_record"))
            recent.append({
                "slug": str(piece.get("slug") or "")[:160],
                "title": str(piece.get("title") or "Untitled Piece")[:200],
                "dek": str(piece.get("dek"))[:280] if piece.get("dek") else None,
                "category": cat,
                "category_label": {
                    "wrap_or_digest": "Wrap / Digest",
                    "article": "Article",
                    "event_preview": "Event Preview",
                    "event_review": "Event Review",
                }[cat],
                "published_at_utc": piece.get("published_at_utc"),
                "published_at_gmt7": _format_gmt7(piece.get("published_at_utc")),
                "url": piece.get("url") if _valid_https(piece.get("url")) else None,
                "outlet_names": outlet_names,
                "link_only": link_only,
                "scenario_count": scenario_count,
                "diagnostics": {
                    "raw_kind": piece.get("kind"),
                    "work_item": piece.get("work_item"),
                    "package_gap": piece.get("package_gap"),
                    "copy_sha256": piece.get("copy_sha256"),
                },
            })

    total = len(raw_pieces)
    pill = (
        _make_pill(f"{total} Confirmed", "emerald", f"{counts['wrap_or_digest']} wraps/digests · {counts['article']} articles")
        if total > 0
        else _make_pill("No Confirmed Pieces", "neutral", "No confirmed Substack pieces in snapshot.")
    )
    return {
        "pill": pill,
        "total": total,
        "counts": {
            "wraps_and_digests": counts["wrap_or_digest"],
            "articles": counts["article"],
            "event_previews": counts["event_preview"],
            "event_reviews": counts["event_review"],
        },
        "recent": recent,
        "diagnostics": {"source": source_kind},
    }


def _build_replies_section(desk_state: Mapping[str, Any]) -> dict[str, Any]:
    queues_data = ((desk_state.get("sections") or {}).get("queues") or {}).get("data") or {}
    raw_replies = queues_data.get("replies") if isinstance(queues_data.get("replies"), list) else []
    items: list[dict[str, Any]] = []
    for row in raw_replies[:15]:
        if not isinstance(row, Mapping):
            continue
        pid = str(row.get("post_id") or "")
        if not pid.isdigit():
            continue
        status_text = str(row.get("status") or "Drafted")
        tone = "emerald" if status_text in {"On your phone", "Opened"} else "amber" if status_text == "Expired" else "neutral"
        items.append({
            "post_id": pid,
            "author_handle": str(row.get("author_handle") or "")[:80],
            "post_time_utc": row.get("post_time_utc"),
            "draft_preview": str(row.get("draft_text") or "")[:240],
            "intent_url": _valid_x_intent_url(row.get("intent_url"), pid),
            "good_until_utc": row.get("good_until"),
            "good_until_gmt7": _format_gmt7(row.get("good_until")),
            "status_pill": _make_pill(status_text, tone),
            "target_replies": _safe_int(row.get("target_replies")),
            "diagnostics": {
                "source_message_id": row.get("source_message_id"),
                "image_sha256": row.get("image_sha256"),
                "image_cause": row.get("image_cause"),
            },
        })

    filter_causes = queues_data.get("filter_causes") if isinstance(queues_data.get("filter_causes"), Mapping) else {}
    last_pack_at = queues_data.get("last_pack_at")
    reply_cause = queues_data.get("reply_cause")
    if items:
        pill = _make_pill(f"{len(items)} Active Draft{'s' if len(items) != 1 else ''}", "emerald", "Manual mobile X reply drafts ready.")
    else:
        last_gmt7 = _format_gmt7(last_pack_at)
        detail = f"Automated X replies parked; last manual pack {last_gmt7}." if last_gmt7 else "Automated X replies parked; no active drafts."
        pill = _make_pill("Quiet · No Active Drafts", "neutral", detail)

    return {
        "pill": pill,
        "active_count": len(items),
        "automated_replies_parked": True,
        "last_pack_at_utc": last_pack_at,
        "last_pack_at_gmt7": _format_gmt7(last_pack_at),
        "filtered_summary": _format_reply_filter_summary(filter_causes),
        "items": items,
        "diagnostics": {
            "raw_reply_cause": reply_cause,
            "replies_at_utc": queues_data.get("replies_at"),
            "filter_causes": dict(filter_causes),
        },
    }


def _build_gold_note_section(desk_state: Mapping[str, Any]) -> dict[str, Any]:
    gn = ((desk_state.get("sections") or {}).get("gold_note") or {}).get("data") or {}
    if not isinstance(gn, Mapping) or gn.get("state") != "READ" or not gn.get("text"):
        return {
            "available": False,
            "pill": map_status_pill("GOLD_NOTE_MISSING"),
            "date": None,
            "headline": None,
            "preview": None,
            "has_chart": False,
            "diagnostics": {"raw_state": gn.get("state") if isinstance(gn, Mapping) else None},
        }
    lines = [line.strip() for line in str(gn.get("text") or "").splitlines() if line.strip()]
    headline = lines[0][:160] if lines else "Daily Gold Note"
    preview = " ".join(lines[1:3])[:260] if len(lines) > 1 else headline
    chart = gn.get("chart") if isinstance(gn.get("chart"), Mapping) else {}
    source = gn.get("source") if isinstance(gn.get("source"), Mapping) else {}
    note_date = str(gn.get("date") or "") or None
    return {
        "available": True,
        "pill": _make_pill(f"Gold Note · {note_date}" if note_date else "Gold Note Ready", "emerald"),
        "date": note_date,
        "headline": headline,
        "preview": preview,
        "has_chart": bool(chart.get("path") or chart.get("href")),
        "diagnostics": {
            "item": gn.get("item"),
            "raw_state": gn.get("state"),
            "source_path": source.get("path"),
            "chart_path": chart.get("path"),
        },
    }


def _build_audience_and_calls_section(desk_state: Mapping[str, Any]) -> dict[str, Any]:
    score = ((desk_state.get("sections") or {}).get("score") or {}).get("data") or {}
    ledger = score.get("calls_ledger") if isinstance(score.get("calls_ledger"), Mapping) else {}
    audience = score.get("audience") if isinstance(score.get("audience"), Mapping) else {}

    total_calls = _safe_int(ledger.get("total"))
    resolved_calls = _safe_int(ledger.get("with_result_record"))
    ledger_at = ledger.get("at_utc")
    ledger_pill = (
        _make_pill(f"{total_calls} Calls · {resolved_calls or 0} Resolved", "emerald")
        if total_calls is not None
        else _make_pill("Ledger Pending", "neutral")
    )

    rows_summary = []
    platforms_with_views: set[str] = set()
    for row in audience.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        med = _safe_num(row.get("median_views"))
        raw_cause = str(row.get("cause") or "") or None
        unsupported = raw_cause is not None and "VIEWS_UNSUPPORTED" in raw_cause
        if med is not None:
            platforms_with_views.add(str(row.get("platform") or ""))
        rows_summary.append({
            "type": str(row.get("type") or "Note"),
            "platform": str(row.get("platform") or ""),
            "median_views": med,
            "display": f"{int(round(med)):,}" if med is not None else "—",
            "sample_size": _safe_int(row.get("n")) or 0,
            "unsupported": unsupported,
            "diagnostics": {"raw_cause": raw_cause, "updated_at_utc": row.get("updated_at")},
        })

    aud_cause = score.get("audience_cause") or audience.get("cause")
    aud_pill = (
        _make_pill(f"7d Views · {len(platforms_with_views)} Platform{'s' if len(platforms_with_views) != 1 else ''}", "emerald")
        if platforms_with_views
        else map_status_pill(str(aud_cause) if aud_cause else "NO_COLLECTED_OBSERVATION_IN_WINDOW")
    )
    return {
        "calls_ledger": {
            "pill": ledger_pill,
            "total": total_calls,
            "with_result_record": resolved_calls,
            "today": _safe_int(ledger.get("today")),
            "at_utc": ledger_at,
            "at_gmt7": _format_gmt7(ledger_at),
            "diagnostics": {"chain_tip": ledger.get("chain_tip")},
        },
        "audience_7d": {
            "pill": aud_pill,
            "updated_at_utc": score.get("audience_at") or audience.get("updated_at"),
            "updated_at_gmt7": _format_gmt7(score.get("audience_at") or audience.get("updated_at")),
            "platforms_with_views": sorted(p for p in platforms_with_views if p),
            "rows": rows_summary[:30],
            "diagnostics": {
                "raw_cause": aud_cause,
                "window_start": audience.get("window_start"),
                "window_end": audience.get("window_end"),
            },
        },
    }


# ---------------------------------------------------------------------------
# Defense-in-Depth Leak & Display Hygiene Verifiers
# ---------------------------------------------------------------------------


def strip_forbidden_private_keys(value: Any) -> Any:
    """Recursively remove ``_private_texts`` and all forbidden private/book/secret keys."""
    if isinstance(value, Mapping):
        return {
            str(k): strip_forbidden_private_keys(v)
            for k, v in value.items()
            if str(k).lower() not in FORBIDDEN_PRIVATE_KEYS
        }
    if isinstance(value, list):
        return [strip_forbidden_private_keys(item) for item in value]
    return value


def assert_no_private_text_leaks(
    payload: Mapping[str, Any],
    *,
    forbidden_texts: Iterable[str] = (),
) -> None:
    """Fail closed if any forbidden private key or captured private canary echoes in payload."""

    def _walk_keys(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for k, v in node.items():
                if str(k).lower() in FORBIDDEN_PRIVATE_KEYS:
                    raise PrivateLeakError(f"FORBIDDEN_PRIVATE_KEY_LEAK:{path}.{k}")
                _walk_keys(v, f"{path}.{k}")
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                _walk_keys(item, f"{path}[{idx}]")

    _walk_keys(payload, "$")

    serialized = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    normalized_blob = " ".join(serialized.lower().split())
    for canary in forbidden_texts:
        cleaned = " ".join(str(canary).lower().split())
        if len(cleaned) >= 8 and cleaned in normalized_blob:
            raise PrivateLeakError("PRIVATE_TEXT_CANARY_ECHO_DETECTED")


def assert_clean_primary_display(payload: Mapping[str, Any]) -> None:
    """Fail closed if any raw debug enum leaks onto primary display fields outside ``diagnostics``."""

    def _walk(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for k, v in node.items():
                key = str(k)
                if key == "diagnostics":
                    continue
                _walk(v, f"{path}.{key}")
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                _walk(item, f"{path}[{idx}]")
        elif isinstance(node, str):
            match = RAW_DEBUG_ENUM_RE.search(node)
            if match:
                raise DisplayHygieneError(f"RAW_DEBUG_ENUM_ON_PRIMARY_FIELD:{path}={match.group(0)}")

    _walk(payload, "$")


# ---------------------------------------------------------------------------
# Public Entry Point & Strictly Private Writer
# ---------------------------------------------------------------------------


def build_privateapp_newsroom_summary(
    *,
    runtime_root: Path | None = DEFAULT_CONTENTOPS_RUNTIME_ROOT,
    store_path: Path | None = None,
    production_day_root: Path | None = None,
    published_feed_path: Path | None = None,
    published_images_path: Path | None = None,
    x_list_feed_path: Path | None = None,
    control_dir: Path | None = None,
    codex_exec_dir: Path | None = DEFAULT_CODEX_EXEC_DIR,
    desk_state_path: Path | None = None,
    desk_js_path: Path | None = None,
    attention_map_live_path: Path | None = DEFAULT_ATTENTION_MAP_LIVE_PATH,
    attention_map_ledger_path: Path | None = None,
    attention_map_pulse_path: Path | None = None,
    digest_message_id: str | None = None,
    digest_destination: str | None = None,
    day: str | None = None,
    now: datetime | None = None,
    cc153_timeout_seconds: float = DEFAULT_CC153_TIMEOUT_SECONDS,
    immutable_store_snapshot: bool = False,
    probe_live_neo: bool = False,
    x_keepalive_status_fn: Callable[[], Mapping[str, Any]] | None = None,
    neo_probe_fn: Callable[[], Mapping[str, Any]] | None = None,
    stage_hook: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Assemble and validate ``ContentOpsNewsroomPrivateSummaryV1`` (strictly read-only)."""
    now_dt = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    now_utc = _iso_utc(now_dt)
    assert now_utc is not None
    prod_day = day or production_date_bangkok(now_dt)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", prod_day) or date.fromisoformat(prod_day).isoformat() != prod_day:
        raise InvalidSource("EXACT_PRODUCTION_DATE_REQUIRED")

    root = Path(runtime_root) if runtime_root else None
    resolved_store = store_path if store_path is not None else (root / "contentops_daily_app_v1.sqlite3" if root else None)
    resolved_day_root = production_day_root if production_day_root is not None else (root / "daily_app_outputs" if root else None)
    resolved_published = published_feed_path if published_feed_path is not None else (root / "published_content_v1.jsonl" if root else None)
    resolved_images = published_images_path if published_images_path is not None else (root / "published_images_v1.jsonl" if root else None)
    resolved_x_feed = x_list_feed_path if x_list_feed_path is not None else (root / "x_list_feed" / "x_list_feed_v1.json" if root else None)
    resolved_control = control_dir if control_dir is not None else (root / "control" if root else None)
    resolved_x_dir = resolved_x_feed.parent if resolved_x_feed is not None else (root / "x_list_feed" if root else None)

    # 1. Hardened CC-153 store + day + sealed CC-135 published feed reads.
    cc153_store, cc153_digest = read_cc153_store_hardened(
        resolved_store,
        day=prod_day,
        now_utc=now_utc,
        digest_message_id=digest_message_id,
        digest_destination=digest_destination,
        timeout_seconds=cc153_timeout_seconds,
        immutable_snapshot=immutable_store_snapshot,
        stage_hook=stage_hook,
    )
    cc153_day = read_cc153_production_day(resolved_day_root, prod_day, now_utc)
    cc135_published = read_cc135_published_feed(resolved_published, prod_day, now_utc)

    # 2. Publisher pause / route suspension / kill switch control state.
    publisher_control = read_publisher_pause_control(
        control_dir=resolved_control,
        codex_exec_dir=codex_exec_dir,
        operating_control=cc153_store.get("operating_control"),
        now_dt=now_dt,
    )
    paused = bool(publisher_control["is_paused"])

    # 3. Optional desk_state & desk.js snapshots for recent posts, wraps, replies, gold note, score.
    desk_state = _read_desk_state_optional(desk_state_path)
    posts_section = _build_posts_section(desk_state, paused=paused)
    raw_wraps, wraps_source = _read_wraps_from_store_or_desk(
        store_path=resolved_store,
        desk_js_path=desk_js_path,
        immutable_snapshot=immutable_store_snapshot,
    )
    wraps_section = _build_wraps_section(raw_wraps, wraps_source)
    replies_section = _build_replies_section(desk_state)
    gold_note_section = _build_gold_note_section(desk_state)
    image_register_section = _read_image_register_summary(resolved_images)
    audience_and_calls = _build_audience_and_calls_section(desk_state)

    # 4. Fast header X-list feed + CC-711 keepalive & BrowserOS Neo health.
    x_list_feed = read_x_list_feed_header(resolved_x_feed, now_dt=now_dt)
    cached_neo = (((desk_state.get("sections") or {}).get("queues") or {}).get("data") or {}).get("neo")
    keepalive_and_neo = read_keepalive_and_neo_health(
        x_feed_dir=resolved_x_dir,
        probe_live=probe_live_neo,
        x_status_fn=x_keepalive_status_fn,
        neo_probe_fn=neo_probe_fn,
        cached_neo_reply_status=cached_neo if isinstance(cached_neo, Mapping) else None,
        now_dt=now_dt,
    )

    # 5. CC-817 Market Forces Attention Map summary (zero _private_texts leaks).
    attention_map, captured_canaries = read_attention_map_summary(
        live_map_path=attention_map_live_path,
        ledger_path=attention_map_ledger_path,
        pulse_path=attention_map_pulse_path,
        now_dt=now_dt,
    )

    # 6. Assemble clean CC-153 pipeline view (zero raw enums on primary fields).
    store_ev = cc153_store["evidence"]
    store_ok = store_ev["state"] == "AVAILABLE"
    elapsed_ms = round((store_ev.get("read_elapsed_seconds") or 0.0) * 1000.0, 1)
    store_pill = (
        _make_pill(f"Connected · {elapsed_ms:.0f} ms", "emerald", "Bounded read-only store query succeeded.")
        if store_ok
        else map_status_pill(store_ev.get("reason"), paused=paused)
    )
    day_ev = cc153_day["evidence"]
    day_pill = (
        _make_pill("Active Day Recorded", "emerald", "Sealed production day summary available.")
        if day_ev["state"] == "AVAILABLE"
        else map_status_pill(day_ev.get("reason"), paused=paused)
    )
    digest_ev = cc153_digest["evidence"]
    digest_pill = (
        _make_pill(str(cc153_digest["owner_state"]).replace("_", " ").title(), "emerald")
        if digest_ev["state"] == "AVAILABLE" and cc153_digest.get("owner_state")
        else map_status_pill(digest_ev.get("reason"), paused=paused)
    )
    today_pub_items = cc135_published["items"] or []
    pipeline_cc153 = {
        "pill": store_pill if not store_ok else day_pill,
        "production_date": prod_day,
        "production_day_id": f"newsroom-production-day-{prod_day}-bangkok",
        "production_day_rollover_gmt7": "02:00",
        "day_summary": cc153_day["summary"],
        "today_published_count": len(today_pub_items),
        "total_sealed_published_count": cc135_published["total_records"],
        "today_published_items": today_pub_items[:10],
        "today_admissions_count": len(cc153_store["admissions"]) if isinstance(cc153_store["admissions"], list) else None,
        "today_first_causes_count": len(cc153_store["first_causes"]) if isinstance(cc153_store["first_causes"], list) else None,
        "today_dispatches_count": len(cc153_store["dispatches"]) if isinstance(cc153_store["dispatches"], list) else None,
        "digest_pill": digest_pill,
        "store_health": {
            "pill": store_pill,
            "connected": store_ok,
            "read_elapsed_ms": elapsed_ms,
            "read_attempts": store_ev.get("read_attempts"),
            "latest_store_activity_utc": store_ev.get("latest_at_utc"),
            "latest_store_activity_gmt7": _format_gmt7(store_ev.get("latest_at_utc")),
            "indexes_present": cc153_store.get("indexes_present"),
        },
        "diagnostics": {
            "cc153_schema": CC153_SCHEMA,
            "day_evidence": day_ev,
            "day_windows": cc153_day["windows"],
            "day_first_blocking_causes": cc153_day["first_blocking_causes"],
            "published_evidence": cc135_published["evidence"],
            "store_evidence": store_ev,
            "digest_evidence": digest_ev,
            "admissions": cc153_store["admissions"],
            "selection_gaps": cc153_store["selection_gaps"],
            "first_causes": cc153_store["first_causes"],
            "dispatches": cc153_store["dispatches"],
        },
    }

    # 7. Executive Top Status Strip (4-6 crisp KPI tiles for PrivateApp Content & Newsroom).
    status_strip = {
        "overall": publisher_control["pill"],
        "publishing": {
            "pill": publisher_control["pill"],
            "paused": paused,
            "last_post_at_utc": posts_section["last_post_at_utc"],
            "last_post_at_gmt7": posts_section["last_post_at_gmt7"],
            "stopped_lanes_count": publisher_control["publisher_lanes"]["stopped_count"],
            "scheduled_resume_utc": publisher_control["pause_window"]["resume_at_utc"],
            "scheduled_resume_gmt7": publisher_control["pause_window"]["resume_at_gmt7"],
        },
        "x_list_feed": {
            "pill": x_list_feed["pill"],
            "age_seconds": x_list_feed["age_seconds"],
            "row_count_24h": x_list_feed["row_count"],
            "median_ingest_lag_seconds": x_list_feed["median_ingest_lag_seconds"],
        },
        "confirmed_pieces": {
            "pill": wraps_section["pill"],
            "total": wraps_section["total"],
            "wraps_and_digests": wraps_section["counts"]["wraps_and_digests"],
            "articles": wraps_section["counts"]["articles"],
            "event_pieces": wraps_section["counts"]["event_previews"] + wraps_section["counts"]["event_reviews"],
            "today_published": len(today_pub_items),
        },
        "keepalive_neo": {
            "pill": keepalive_and_neo["pill"],
            "x_runner_alive": keepalive_and_neo["x_feed_keepalive"]["runner_alive"],
            "neo_probed": keepalive_and_neo["browseros_neo"]["probed"],
            "neo_cdp_alive": keepalive_and_neo["browseros_neo"]["cdp_alive"],
            "neo_mcp_alive": keepalive_and_neo["browseros_neo"]["mcp_alive"],
        },
        "attention_map": {
            "pill": attention_map["pill"],
            "available": attention_map["available"],
            "theme_count": attention_map["theme_count"],
        },
        "cc153_store": {
            "pill": store_pill,
            "connected": store_ok,
            "read_elapsed_ms": elapsed_ms,
        },
    }

    summary = strip_forbidden_private_keys({
        "schema_version": SCHEMA_VERSION,
        "private_only": True,
        "read_only": True,
        "public_export": False,
        "robots": "noindex,nofollow",
        "generated_at_utc": now_utc,
        "generated_at_gmt7": _format_gmt7(now_dt),
        "production_date": prod_day,
        "production_day_id": f"newsroom-production-day-{prod_day}-bangkok",
        "status_strip": status_strip,
        "publisher_control": publisher_control,
        "publishing_queue": {
            "posts": posts_section,
            "wraps": wraps_section,
            "replies": replies_section,
            "gold_note": gold_note_section,
            "image_register": image_register_section,
            "pipeline_cc153": pipeline_cc153,
        },
        "x_list_feed": x_list_feed,
        "keepalive_and_neo": keepalive_and_neo,
        "attention_map": attention_map,
        "audience_and_calls": audience_and_calls,
    })

    # Final mandatory fail-closed defense-in-depth gates before returning.
    assert_no_private_text_leaks(summary, forbidden_texts=captured_canaries)
    assert_clean_primary_display(summary)
    return summary


def _validate_private_output_path(output_path: Path) -> Path:
    resolved = Path(output_path).resolve()
    parts = tuple(part.casefold() for part in resolved.parts)
    if any(parts[i : i + 2] in (("ui", "public"), ("ui", "dist")) for i in range(len(parts) - 1)):
        raise PrivateLeakError("PRIVATE_SUMMARY_IN_PUBLIC_TREE_FORBIDDEN")
    name_l = resolved.name.casefold()
    if ".public." in name_l or name_l.endswith("public.json"):
        raise PrivateLeakError("PRIVATE_SUMMARY_PUBLIC_FILENAME_FORBIDDEN")
    if any(re.search(r"(?i)credential|secret|2fa|^\.env(?:\.|$)", part) for part in resolved.parts):
        raise PrivateLeakError("OUTPUT_PATH_FORBIDDEN")
    return resolved


def write_privateapp_newsroom_summary(output_path: Path, summary: Mapping[str, Any]) -> Path:
    """Atomically write ``contentops-newsroom-summary.private.json`` with strict LF (CR=0, BOM=False)."""
    if summary.get("private_only") is not True or summary.get("public_export") is not False:
        raise PrivateLeakError("PRIVATE_ONLY_FLAGS_REQUIRED")
    assert_no_private_text_leaks(summary)
    assert_clean_primary_display(summary)
    target = _validate_private_output_path(Path(output_path))
    target.parent.mkdir(parents=True, exist_ok=True)
    payload_text = json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    payload_bytes = payload_text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    tmp = target.with_name(f".{target.name}.{time.time_ns()}.tmp")
    try:
        tmp.write_bytes(payload_bytes)
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate strictly private-only PrivateApp ContentOps newsroom summary.")
    parser.add_argument("--output", type=Path, help="Output JSON path (must be private, never in ui/public or *.public.json).")
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_CONTENTOPS_RUNTIME_ROOT)
    parser.add_argument("--store-path", type=Path, default=None)
    parser.add_argument("--codex-exec-dir", type=Path, default=DEFAULT_CODEX_EXEC_DIR)
    parser.add_argument("--desk-state", type=Path, default=DEFAULT_PRIVATEAPP_DATA_DIR / "desk_state_v1.json")
    parser.add_argument("--desk-js", type=Path, default=DEFAULT_PRIVATEAPP_DATA_DIR / "desk.js")
    parser.add_argument("--attention-map", type=Path, default=DEFAULT_ATTENTION_MAP_LIVE_PATH)
    parser.add_argument("--attention-ledger", type=Path, default=None)
    parser.add_argument("--attention-pulse", type=Path, default=None)
    parser.add_argument("--day", type=str, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_CC153_TIMEOUT_SECONDS)
    parser.add_argument("--immutable-store-snapshot", action="store_true")
    parser.add_argument("--probe-live-neo", action="store_true")
    args = parser.parse_args(argv)

    summary = build_privateapp_newsroom_summary(
        runtime_root=args.runtime_root,
        store_path=args.store_path,
        codex_exec_dir=args.codex_exec_dir,
        desk_state_path=args.desk_state,
        desk_js_path=args.desk_js,
        attention_map_live_path=args.attention_map,
        attention_map_ledger_path=args.attention_ledger,
        attention_map_pulse_path=args.attention_pulse,
        day=args.day,
        cc153_timeout_seconds=args.timeout_seconds,
        immutable_store_snapshot=args.immutable_store_snapshot,
        probe_live_neo=args.probe_live_neo,
    )
    if args.output:
        written = write_privateapp_newsroom_summary(args.output, summary)
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": SCHEMA_VERSION,
                    "output": str(written),
                    "bytes": written.stat().st_size,
                    "store_connected": summary["status_strip"]["cc153_store"]["connected"],
                    "store_read_elapsed_ms": summary["status_strip"]["cc153_store"]["read_elapsed_ms"],
                    "overall_pill": summary["status_strip"]["overall"]["label"],
                },
                ensure_ascii=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
