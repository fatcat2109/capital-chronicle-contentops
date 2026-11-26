"""CC-760 (decision 82): fail-closed cached TradingView chart fallback on canonical plan-page timeout.

When a canonical plan page's own bounded TradingView capture times out or expires
(e.g., TRADINGVIEW_CAPTURE_WAIT_EXPIRED, TRADINGVIEW_SNAPSHOT_TIMEOUT,
TRADINGVIEW_WORKER_STEP_TIMEOUT:*, TRADINGVIEW_WORKER_BUDGET_SPENT:*), reuse an
already-bound same-plan TradingView chart ONLY IF ALL FIVE invariants hold:

  1. Exact symbol (market asset, TradingView symbol, interval, 16:9 ratio, chart URL, scale check)
  2. Exact plan_id (explicitly bound, unanimous across candidate metadata)
  3. Valid source_window & freshness cap (within [frozen_at, entry_deadline/close], <= max_age_seconds)
  4. Matching revision (registration_hash, plus analysis_result_hash/run_id/freeze/revision when present,
     and exact SHA256 PNG byte integrity)
  5. Explicit public_use_rights & zero private-text / R-multiple / profit-target leak

If ANY invariant fails, fail closed cleanly, preserve the capture cause, and never
substitute a mismatched, stale, rights-unverified, or leaky chart.

Operator: T3 Code, Gemini 4 Neon xhigh, antigravity_14
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

POLICY = "CC760_CACHED_TV_CHART_FALLBACK_V1"
DEFAULT_MAX_CACHE_AGE_SECONDS = 60 * 60
MAX_ALLOWED_CACHE_AGE_SECONDS = 6 * 60 * 60
MIN_IMAGE_DIMENSION_PX = 400

TIMEOUT_EXACT_CAUSES = frozenset({
    "TRADINGVIEW_CAPTURE_WAIT_EXPIRED",
    "TRADINGVIEW_SNAPSHOT_TIMEOUT",
})
TIMEOUT_CAUSE_PREFIXES = (
    "TRADINGVIEW_WORKER_STEP_TIMEOUT:",
    "TRADINGVIEW_WORKER_BUDGET_SPENT:",
)

ALLOWED_PUBLIC_RIGHTS = frozenset({
    "PUBLIC_FREE_PAGE",
    "TRADINGVIEW_FREE_PUBLIC_SNAPSHOT",
    "ALLOWED",
    "VERIFIED_PUBLIC",
    "PUBLIC",
})
DENIED_PUBLIC_RIGHTS = frozenset({
    "INTERNAL_ONLY",
    "PRIVATE",
    "LICENSE_REQUIRED",
    "RESTRICTED",
    "PAID_ONLY",
    "DENIED",
    "NONE",
    "FORBIDDEN",
    "UNVERIFIED",
})

FORBIDDEN_PRIVATE_KEYS = frozenset({
    "account",
    "account_id",
    "account_number",
    "balance",
    "equity",
    "mt4",
    "mt5",
    "exness",
    "metatrader",
    "ticket",
    "ticket_id",
    "lot_size",
    "lots",
    "position_size",
    "risk_allocation",
    "r_multiple",
    "r_multiples",
    "result_r",
    "expected_r",
    "expectancy",
    "best_r",
    "worst_r",
    "total_r",
    "avg_r",
    "private_text",
    "private_texts",
    "x_list",
    "jim_x_list",
    "secret",
    "api_key",
    "access_token",
    "password",
})

_R_MULTIPLE_RE = re.compile(
    r"(?<![A-Za-z0-9])[+\-\u2212]?\d+(?:\.\d+)?\s*R(?![A-Za-z0-9])"
    r"|\b(?:r[-_ ]?multiples?|expected[-_ ]?r|reward[-_ ]?to[-_ ]?risk"
    r"|result[-_ ]?r|best[-_ ]?r|worst[-_ ]?r|total[-_ ]?r|avg[-_ ]?r"
    r"|expectancy|risk[-_ ]?r)\b",
    re.I,
)
_TARGET_LEAK_RE = re.compile(
    r"(?<!inflation )\b(?:(?:profit|price|model)[- ]?targets?|target[- ]?level"
    r"|take[- ]?profits?|TP\d+)\b",
    re.I,
)

INVARIANTS_VERIFIED = (
    "symbol",
    "plan_id",
    "source_window",
    "revision",
    "public_use_rights_and_privacy",
)


class CachedChartFallbackError(ValueError):
    """Fail-closed rejection of a cached TradingView chart fallback candidate."""

    def __init__(self, cause: str, **details: Any) -> None:
        super().__init__(cause)
        self.cause = cause
        self.details = details


def _parse_utc(value: Any, *, error_cause: str = "CC760_SOURCE_WINDOW_INVALID") -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value.strip():
        try:
            dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise CachedChartFallbackError(error_cause, value=str(value)) from exc
    else:
        raise CachedChartFallbackError(error_cause, value=value)
    if dt.tzinfo is None:
        raise CachedChartFallbackError(error_cause, reason="NAIVE_TIMESTAMP", value=str(value))
    return dt.astimezone(timezone.utc)


def is_timeout_cause(cause: Any) -> bool:
    if not isinstance(cause, str):
        return False
    text = cause.strip()
    return text in TIMEOUT_EXACT_CAUSES or text.startswith(TIMEOUT_CAUSE_PREFIXES)


def is_timeout_capture_state(
    state: Mapping[str, Any] | None,
    *,
    expected_key: str | None = None,
    expected_market: str | None = None,
) -> tuple[bool, str | None]:
    """Return (True, timeout_cause) only for an exhausted timeout/expiry capture state."""
    from . import tradingview_snapshot_v1 as tv

    if not isinstance(state, Mapping):
        return False, None
    if state.get("status") != "TEXT_ONLY":
        return False, None
    if expected_key is not None and state.get("key") != expected_key:
        return False, None
    if expected_market is not None and state.get("market") != expected_market:
        return False, None
    primary = state.get("cause")
    first = state.get("first_cause")
    if is_timeout_cause(primary):
        return True, str(primary).strip()
    if is_timeout_cause(first):
        return True, str(first).strip()
    attempt_causes = state.get("attempt_causes")
    if isinstance(attempt_causes, list) and (
        primary == tv.CAPTURE_INTERRUPTED or first == tv.CAPTURE_INTERRUPTED
    ):
        for item in attempt_causes:
            if is_timeout_cause(item):
                return True, str(primary or first).strip()
    return False, None


def _read_json_mapping(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _collect_strings(value: Any, *, _depth: int = 0) -> list[str]:
    if _depth > 8 or value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Mapping):
        out: list[str] = []
        for item in value.values():
            out.extend(_collect_strings(item, _depth=_depth + 1))
        return out
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            out.extend(_collect_strings(item, _depth=_depth + 1))
        return out
    return []


def _find_forbidden_keys(value: Any, *, prefix: str = "", _depth: int = 0) -> list[str]:
    if _depth > 8 or not isinstance(value, Mapping):
        return []
    hits: list[str] = []
    for raw_key, item in value.items():
        key = str(raw_key).strip().lower()
        path = f"{prefix}.{raw_key}" if prefix else str(raw_key)
        if key in FORBIDDEN_PRIVATE_KEYS:
            hits.append(path)
        elif isinstance(item, Mapping):
            hits.extend(_find_forbidden_keys(item, prefix=path, _depth=_depth + 1))
    return hits


def _extract_snapshot(candidate: Mapping[str, Any]) -> dict[str, Any]:
    asset = candidate.get("asset") if isinstance(candidate.get("asset"), Mapping) else candidate
    snap = candidate.get("snapshot")
    if not isinstance(snap, Mapping):
        snap = asset.get("tradingview_snapshot") if isinstance(asset, Mapping) else None
    if not isinstance(snap, Mapping) and isinstance(asset, Mapping):
        tmpl = asset.get("image_template")
        if isinstance(tmpl, Mapping) and isinstance(tmpl.get("snapshot"), Mapping):
            snap = tmpl["snapshot"]
    if not isinstance(snap, Mapping):
        raise CachedChartFallbackError("CC760_SYMBOL_MISMATCH", reason="SNAPSHOT_MISSING")
    return dict(snap)


def _extract_binding_records(candidate: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records: list[Mapping[str, Any]] = []
    seen_ids: set[int] = set()

    def add(obj: Any) -> None:
        if isinstance(obj, Mapping) and id(obj) not in seen_ids:
            seen_ids.add(id(obj))
            records.append(obj)

    add(candidate)
    for key in ("plan_binding", "setup_record", "source_plan", "revision", "asset", "capture_state"):
        add(candidate.get(key))
    asset = candidate.get("asset") if isinstance(candidate.get("asset"), Mapping) else candidate
    if isinstance(asset, Mapping):
        for key in ("plan_binding", "cached_chart_binding", "source_plan"):
            add(asset.get(key))
        tmpl = asset.get("image_template")
        if isinstance(tmpl, Mapping):
            inp = tmpl.get("input")
            if isinstance(inp, Mapping):
                sb = inp.get("source_binding")
                if isinstance(sb, Mapping):
                    rec = sb.get("record")
                    add(rec)
                    if isinstance(rec, Mapping):
                        add(rec.get("source_plan"))
    setup = candidate.get("setup_record")
    if isinstance(setup, Mapping):
        add(setup.get("source_plan"))
    return records


def _expected_plan_interval(plan: Mapping[str, Any], run: Mapping[str, Any]) -> str:
    from . import plan_status_posts_v1 as posts
    from . import tradingview_snapshot_v1 as tv

    levels = posts._display_plan(posts._built_plan(plan))
    at_utc = (run.get("freeze") or {}).get("frozen_at_utc") or plan.get("registered_at_utc")
    return tv.interval_for(levels.get("valid_until_utc"), at_utc)


def _validate_public_rights_value(value: Any) -> None:
    if isinstance(value, bool):
        if not value:
            raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_FORBIDDEN", public_use_rights=value)
        return
    if isinstance(value, str):
        norm = value.strip().upper()
        if norm in DENIED_PUBLIC_RIGHTS or norm not in ALLOWED_PUBLIC_RIGHTS:
            raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_FORBIDDEN", public_use_rights=value)
        return
    if isinstance(value, Mapping):
        for bad_flag in ("internal_only", "paid_only", "restricted", "private", "paywall"):
            if value.get(bad_flag) is True:
                raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_FORBIDDEN", flag=bad_flag)
        allowed = value.get("allowed")
        status = str(value.get("status") or "").strip().upper()
        if allowed is False or status in DENIED_PUBLIC_RIGHTS:
            raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_FORBIDDEN", public_use_rights=dict(value))
        if allowed is True or status in ALLOWED_PUBLIC_RIGHTS:
            return
        raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_INVALID", public_use_rights=dict(value))
    raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_INVALID", public_use_rights=value)


def _check_privacy_and_r_leaks(
    *,
    candidate: Mapping[str, Any],
    asset: Mapping[str, Any],
    snap: Mapping[str, Any],
    private_texts: Sequence[str],
    check_targets: bool = True,
) -> None:
    from .plan_analysis_pages_v1 import public_filter

    # 1. Inspect snapshot & public metadata keys for private/account/R-multiple fields.
    forbidden = _find_forbidden_keys(snap, prefix="tradingview_snapshot")
    if isinstance(candidate.get("public_metadata"), Mapping):
        forbidden.extend(_find_forbidden_keys(candidate["public_metadata"], prefix="public_metadata"))
    if forbidden:
        raise CachedChartFallbackError("CC760_PRIVATE_OR_R_MULTIPLE_LEAK", forbidden_keys=forbidden)

    # 2. Collect all display/public text fields on the candidate asset and snapshot.
    display_texts: list[tuple[str, str]] = []
    for field in ("caption", "alt_text", "title", "attribution", "notes", "public_notes"):
        for text in _collect_strings(asset.get(field)):
            display_texts.append((field, text))
        if asset is not candidate:
            for text in _collect_strings(candidate.get(field)):
                display_texts.append((f"candidate.{field}", text))

    for field in ("texts", "notes"):
        for text in _collect_strings(asset.get(field)):
            display_texts.append((field, text))

    overlay = asset.get("plan_overlay")
    if isinstance(overlay, Mapping):
        for field in ("basis_label",):
            for text in _collect_strings(overlay.get(field)):
                display_texts.append((f"plan_overlay.{field}", text))
        ov_src = overlay.get("source")
        if isinstance(ov_src, Mapping):
            for field in ("phase_terms", "result_text"):
                for text in _collect_strings(ov_src.get(field)):
                    display_texts.append((f"plan_overlay.source.{field}", text))

    tmpl = asset.get("image_template")
    if isinstance(tmpl, Mapping):
        for field in ("alt_text", "texts", "notes"):
            for text in _collect_strings(tmpl.get(field)):
                display_texts.append((f"image_template.{field}", text))

    snap_texts: list[tuple[str, str]] = []
    for field in ("page_title", "legend", "notes"):
        for text in _collect_strings(snap.get(field)):
            snap_texts.append((f"snapshot.{field}", text))

    for label, text in [*display_texts, *snap_texts]:
        if _R_MULTIPLE_RE.search(text):
            raise CachedChartFallbackError("CC760_PRIVATE_OR_R_MULTIPLE_LEAK", field=label, reason="R_MULTIPLE_LEAK")
        if check_targets and label not in {"snapshot.page_title", "snapshot.legend"} and _TARGET_LEAK_RE.search(text):
            raise CachedChartFallbackError("CC760_PRIVATE_OR_R_MULTIPLE_LEAK", field=label, reason="TARGET_LEAK")
        try:
            public_filter(text, private_texts=private_texts)
        except ValueError as exc:
            raise CachedChartFallbackError(
                "CC760_PRIVATE_OR_R_MULTIPLE_LEAK",
                field=label,
                filter_cause=str(exc),
            ) from exc


def validate_cached_chart_candidate(
    candidate: Mapping[str, Any],
    *,
    plan: Mapping[str, Any],
    run: Mapping[str, Any],
    manuscript: Mapping[str, Any] | None = None,
    now: datetime | str | None = None,
    final_status: Mapping[str, Any] | None = None,
    max_age_seconds: float = DEFAULT_MAX_CACHE_AGE_SECONDS,
) -> dict[str, Any]:
    """Strictly verify ALL 5 CC-760 invariants on one cached chart candidate; raise on any failure."""
    from PIL import Image
    from . import plan_analysis_pages_v1 as pages
    from . import publication_image_contract_v1 as contract
    from . import tradingview_plan_overlay_v1 as overlay
    from . import tradingview_snapshot_v1 as tv

    if not isinstance(candidate, Mapping):
        raise CachedChartFallbackError("CC760_CANDIDATE_INVALID")
    asset = candidate.get("asset") if isinstance(candidate.get("asset"), Mapping) else candidate
    snap = _extract_snapshot(candidate)
    records = _extract_binding_records(candidate)

    # ------------------------------------------------------------------
    # Invariant (a): Exact symbol, TradingView feed, interval, ratio, scale
    # ------------------------------------------------------------------
    market = plan.get("asset_id")
    if not isinstance(market, str) or market not in tv.SYMBOLS:
        raise CachedChartFallbackError("CC760_SYMBOL_MISMATCH", market=market)
    expected_tv_symbol = tv.SYMBOLS[market]

    declared_markets: list[str] = []
    for rec in records:
        for field in ("symbol", "market", "asset_id", "market_asset"):
            val = rec.get(field)
            if val is not None:
                declared_markets.append(str(val))
    psc = snap.get("price_scale_check")
    if isinstance(psc, Mapping) and psc.get("market") is not None:
        declared_markets.append(str(psc.get("market")))
    if any(m != market for m in declared_markets):
        raise CachedChartFallbackError(
            "CC760_SYMBOL_MISMATCH",
            expected_market=market,
            observed_markets=sorted(set(declared_markets)),
        )

    if snap.get("tv_symbol") != expected_tv_symbol:
        raise CachedChartFallbackError(
            "CC760_SYMBOL_MISMATCH",
            expected_tv_symbol=expected_tv_symbol,
            observed_tv_symbol=snap.get("tv_symbol"),
        )

    capture_ratio = snap.get("capture_ratio", "16:9")
    if capture_ratio != "16:9":
        raise CachedChartFallbackError("CC760_INTERVAL_OR_RATIO_MISMATCH", capture_ratio=capture_ratio)

    interval = snap.get("interval")
    expected_interval = _expected_plan_interval(plan, run)
    if interval not in tv.INTERVAL_LABELS or interval != expected_interval:
        raise CachedChartFallbackError(
            "CC760_INTERVAL_OR_RATIO_MISMATCH",
            expected_interval=expected_interval,
            observed_interval=interval,
        )

    expected_url = tv.chart_url(expected_tv_symbol, interval)
    if snap.get("chart_url") != expected_url:
        raise CachedChartFallbackError(
            "CC760_SYMBOL_MISMATCH",
            expected_chart_url=expected_url,
            observed_chart_url=snap.get("chart_url"),
        )

    suggested = snap.get("suggested_filename")
    if suggested is not None:
        ticker = expected_tv_symbol.split(":", 1)[1]
        if not re.fullmatch(re.escape(ticker) + r"_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.png", str(suggested)):
            raise CachedChartFallbackError("CC760_SYMBOL_MISMATCH", suggested_filename=str(suggested))

    if snap.get("plain_price_scale_cause"):
        raise CachedChartFallbackError(
            "CC760_PRICE_SCALE_INVALID",
            plain_price_scale_cause=snap.get("plain_price_scale_cause"),
        )

    # ------------------------------------------------------------------
    # Invariant (b): Exact plan_id (explicitly present and unanimous)
    # ------------------------------------------------------------------
    expected_plan_id = plan.get("plan_id")
    if not isinstance(expected_plan_id, str) or not expected_plan_id.strip():
        raise CachedChartFallbackError("CC760_PLAN_ID_MISSING")

    observed_plan_ids: list[str] = []
    for rec in records:
        pid = rec.get("plan_id")
        if pid is not None and str(pid).strip():
            observed_plan_ids.append(str(pid).strip())
        key = rec.get("key")
        if isinstance(key, str) and key.startswith("plan-analysis-"):
            observed_plan_ids.append(key.removeprefix("plan-analysis-"))
    if not observed_plan_ids:
        raise CachedChartFallbackError("CC760_PLAN_ID_MISSING")
    if any(pid != expected_plan_id for pid in observed_plan_ids):
        raise CachedChartFallbackError(
            "CC760_PLAN_ID_MISMATCH",
            expected_plan_id=expected_plan_id,
            observed_plan_ids=sorted(set(observed_plan_ids)),
        )

    # If both capture_state and setup_record/source_key are present, they must refer to the same key.
    capture_state = candidate.get("capture_state") if isinstance(candidate.get("capture_state"), Mapping) else None
    source_key = candidate.get("source_key")
    if capture_state and source_key and capture_state.get("key") and capture_state.get("key") != source_key:
        raise CachedChartFallbackError(
            "CC760_PLAN_ID_MISMATCH",
            reason="SOURCE_KEY_CONFLICT",
            source_key=source_key,
            capture_key=capture_state.get("key"),
        )

    # ------------------------------------------------------------------
    # Invariant (c): Valid source_window & freshness cap
    # ------------------------------------------------------------------
    if (
        isinstance(max_age_seconds, bool)
        or not isinstance(max_age_seconds, (int, float))
        or not math.isfinite(max_age_seconds)
        or not (0 < float(max_age_seconds) <= MAX_ALLOWED_CACHE_AGE_SECONDS)
    ):
        raise CachedChartFallbackError("CC760_SOURCE_WINDOW_INVALID", max_age_seconds=max_age_seconds)
    max_age = float(max_age_seconds)

    freeze = run.get("freeze") or {}
    frozen_at = _parse_utc(freeze.get("frozen_at_utc"), error_cause="CC760_SOURCE_WINDOW_INVALID")
    captured_at = _parse_utc(snap.get("captured_at_utc"), error_cause="CC760_SOURCE_WINDOW_INVALID")
    now_utc = _parse_utc(now if now is not None else datetime.now(timezone.utc), error_cause="CC760_SOURCE_WINDOW_INVALID")

    window_start = frozen_at
    if captured_at < window_start:
        raise CachedChartFallbackError(
            "CC760_SOURCE_WINDOW_MISMATCH",
            reason="CAPTURED_BEFORE_PLAN_FREEZE",
            captured_at_utc=captured_at.isoformat(),
            frozen_at_utc=frozen_at.isoformat(),
        )
    if captured_at > now_utc:
        raise CachedChartFallbackError(
            "CC760_SOURCE_WINDOW_MISMATCH",
            reason="CAPTURED_IN_FUTURE",
            captured_at_utc=captured_at.isoformat(),
            now_utc=now_utc.isoformat(),
        )

    deadline_raw = pages.entry_deadline(plan)
    deadline_utc = _parse_utc(deadline_raw, error_cause="CC760_SOURCE_WINDOW_INVALID") if deadline_raw else None
    window_end = deadline_utc
    if deadline_utc is not None and captured_at > deadline_utc:
        raise CachedChartFallbackError(
            "CC760_SOURCE_WINDOW_MISMATCH",
            reason="CAPTURED_AFTER_ENTRY_DEADLINE",
            captured_at_utc=captured_at.isoformat(),
            entry_deadline_utc=deadline_utc.isoformat(),
        )

    if isinstance(final_status, Mapping) and final_status.get("status_at_utc"):
        closed_at = _parse_utc(final_status["status_at_utc"], error_cause="CC760_SOURCE_WINDOW_INVALID")
        if window_end is None or closed_at < window_end:
            window_end = closed_at
        if captured_at > closed_at:
            raise CachedChartFallbackError(
                "CC760_SOURCE_WINDOW_MISMATCH",
                reason="CAPTURED_AFTER_PLAN_CLOSE",
                captured_at_utc=captured_at.isoformat(),
                closed_at_utc=closed_at.isoformat(),
            )

    # Check explicit source_window metadata if supplied on candidate / asset / plan_binding.
    source_windows = [
        rec["source_window"]
        for rec in records
        if "source_window" in rec and rec["source_window"] is not None
    ]
    plan_window_ends = set()
    for field in ("entry_deadline_utc", "expires_at_utc", "time_exit_utc", "valid_until_utc"):
        if plan.get(field):
            plan_window_ends.add(_parse_utc(plan[field]))
    for sw in source_windows:
        if not isinstance(sw, Mapping):
            raise CachedChartFallbackError("CC760_SOURCE_WINDOW_INVALID")
        if sw.get("frozen_at_utc") is not None:
            if _parse_utc(sw["frozen_at_utc"]) != frozen_at:
                raise CachedChartFallbackError("CC760_SOURCE_WINDOW_MISMATCH", reason="FROZEN_AT_MISMATCH")
        if sw.get("start_utc") is not None:
            sw_start = _parse_utc(sw["start_utc"])
            if sw_start < frozen_at or captured_at < sw_start:
                raise CachedChartFallbackError("CC760_SOURCE_WINDOW_MISMATCH", reason="WINDOW_START_MISMATCH")
        if sw.get("end_utc") is not None:
            sw_end = _parse_utc(sw["end_utc"])
            if captured_at > sw_end:
                raise CachedChartFallbackError("CC760_SOURCE_WINDOW_MISMATCH", reason="WINDOW_END_EXCEEDED")
            if plan_window_ends and sw_end not in plan_window_ends and (
                deadline_utc is not None and sw_end > deadline_utc
            ):
                raise CachedChartFallbackError("CC760_SOURCE_WINDOW_MISMATCH", reason="WINDOW_END_MISMATCH")
        if sw.get("valid_until_utc") is not None and plan_window_ends:
            if _parse_utc(sw["valid_until_utc"]) not in plan_window_ends:
                raise CachedChartFallbackError("CC760_SOURCE_WINDOW_MISMATCH", reason="VALID_UNTIL_MISMATCH")
        if sw.get("window_id") is not None:
            expected_wid = plan.get("source_window_id") or plan.get("run_id")
            if str(sw["window_id"]) != str(expected_wid):
                raise CachedChartFallbackError("CC760_SOURCE_WINDOW_MISMATCH", reason="WINDOW_ID_MISMATCH")

    age_seconds = (now_utc - captured_at).total_seconds()
    if age_seconds > max_age:
        raise CachedChartFallbackError(
            "CC760_SOURCE_WINDOW_STALE",
            age_seconds=round(age_seconds, 3),
            max_age_seconds=max_age,
        )

    # ------------------------------------------------------------------
    # Invariant (d): Matching revision & exact chart bytes integrity
    # ------------------------------------------------------------------
    expected_reg = plan.get("registration_hash")
    if not isinstance(expected_reg, str) or not expected_reg.strip():
        raise CachedChartFallbackError("CC760_REVISION_MISSING")

    observed_regs: list[str] = []
    for rec in records:
        for field in ("registration_hash", "source_plan_registration"):
            val = rec.get(field)
            if val is not None and str(val).strip():
                observed_regs.append(str(val).strip())
    if not observed_regs:
        raise CachedChartFallbackError("CC760_REVISION_MISSING")
    if any(reg != expected_reg for reg in observed_regs):
        raise CachedChartFallbackError(
            "CC760_REVISION_MISMATCH",
            expected_registration_hash=expected_reg,
            observed_registration_hashes=sorted(set(observed_regs)),
        )

    expected_analysis_hash = plan.get("analysis_result_hash")
    if expected_analysis_hash:
        for rec in records:
            val = rec.get("analysis_result_hash")
            if val is not None and str(val) != str(expected_analysis_hash):
                raise CachedChartFallbackError("CC760_REVISION_MISMATCH", field="analysis_result_hash")

    expected_run_id = plan.get("run_id")
    if expected_run_id:
        for rec in records:
            val = rec.get("run_id")
            if val is not None and str(val) != str(expected_run_id):
                raise CachedChartFallbackError("CC760_REVISION_MISMATCH", field="run_id")

    expected_freeze_hash = freeze.get("immutable_hash")
    if expected_freeze_hash:
        for rec in records:
            for field in ("freeze_immutable_hash", "immutable_hash"):
                val = rec.get(field)
                if val is not None and str(val) != str(expected_freeze_hash):
                    raise CachedChartFallbackError("CC760_REVISION_MISMATCH", field=field)
            sub_freeze = rec.get("freeze")
            if isinstance(sub_freeze, Mapping) and sub_freeze.get("immutable_hash") is not None:
                if str(sub_freeze["immutable_hash"]) != str(expected_freeze_hash):
                    raise CachedChartFallbackError("CC760_REVISION_MISMATCH", field="freeze.immutable_hash")

    expected_plan_rev = plan.get("plan_revision") if plan.get("plan_revision") is not None else plan.get("revision")
    for rec in records:
        for field in ("plan_revision", "revision"):
            val = rec.get(field)
            if val is None or isinstance(val, Mapping):
                continue
            if expected_plan_rev is not None:
                if str(val) != str(expected_plan_rev):
                    raise CachedChartFallbackError("CC760_REVISION_MISMATCH", field=field)
            elif str(val) != expected_reg:
                raise CachedChartFallbackError("CC760_REVISION_MISMATCH", field=field)

    if isinstance(manuscript, Mapping):
        ms_rev = manuscript.get("reader_revision")
        ms_lvl = manuscript.get("level_contract")
        for rec in records:
            if ms_rev is not None and rec.get("reader_revision") is not None and rec.get("reader_revision") != ms_rev:
                raise CachedChartFallbackError("CC760_REVISION_MISMATCH", field="reader_revision")
            if ms_lvl is not None and rec.get("level_contract") is not None and rec.get("level_contract") != ms_lvl:
                raise CachedChartFallbackError("CC760_REVISION_MISMATCH", field="level_contract")

    # Verify exact bytes and PNG dimensions of the raw TradingView download.
    raw_path_str = snap.get("path")
    expected_sha = snap.get("sha256")
    if not raw_path_str or not expected_sha:
        raise CachedChartFallbackError("CC760_CHART_BYTES_MISMATCH", reason="PATH_OR_SHA_MISSING")
    raw_path = Path(str(raw_path_str))
    if not raw_path.is_file() or tv._sha256(raw_path) != str(expected_sha):
        raise CachedChartFallbackError("CC760_CHART_BYTES_MISMATCH", path=str(raw_path))
    try:
        with Image.open(raw_path) as img:
            if img.format != "PNG" or min(img.size) < MIN_IMAGE_DIMENSION_PX:
                raise CachedChartFallbackError("CC760_CHART_BYTES_MISMATCH", reason="INVALID_PNG_OR_SIZE")
            img_w, img_h = img.size
    except CachedChartFallbackError:
        raise
    except OSError as exc:
        raise CachedChartFallbackError("CC760_CHART_BYTES_MISMATCH", reason="UNREADABLE_PNG") from exc
    if (snap.get("width") is not None and snap.get("width") != img_w) or (
        snap.get("height") is not None and snap.get("height") != img_h
    ):
        raise CachedChartFallbackError("CC760_CHART_BYTES_MISMATCH", reason="DIMENSIONS_MISMATCH")

    # If the candidate asset itself carries a distinct rendered file path + sha256, verify it too.
    if asset.get("path") and asset.get("sha256"):
        asset_path = Path(str(asset["path"]))
        if not asset_path.is_file() or tv._sha256(asset_path) != str(asset["sha256"]):
            raise CachedChartFallbackError("CC760_CHART_BYTES_MISMATCH", reason="ASSET_BYTES_MISMATCH")

    # Re-validate the bound price-scale check against market and snapshot SHA256.
    try:
        contract.validate_scale(market, snap)
    except ValueError as exc:
        raise CachedChartFallbackError("CC760_PRICE_SCALE_INVALID", scale_cause=str(exc)) from exc

    # ------------------------------------------------------------------
    # Invariant (e): Explicit public_use_rights & zero private/R leak
    # ------------------------------------------------------------------
    for container in (plan, manuscript or {}, candidate, asset):
        if isinstance(container, Mapping) and (
            container.get("paid")
            or container.get("paywall")
            or container.get("audience") in {"paid", "paid_subscribers"}
        ):
            raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_FORBIDDEN", reason="PUBLIC_REDISTRIBUTION_NOT_LICENSED")

    rights_basis = asset.get("rights_basis") if asset.get("rights_basis") is not None else candidate.get("rights_basis")
    credit = asset.get("credit") if asset.get("credit") is not None else candidate.get("credit")
    provenance = (
        asset.get("provenance_status")
        if asset.get("provenance_status") is not None
        else candidate.get("provenance_status")
    )
    if rights_basis != tv.RIGHTS_BASIS:
        raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_INVALID", reason="RIGHTS_BASIS_INVALID")
    if credit != tv.CREDIT:
        raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_INVALID", reason="CREDIT_INVALID")
    if provenance != "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE":
        raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_INVALID", reason="PROVENANCE_INVALID")

    for holder in (candidate, asset, snap):
        if isinstance(holder, Mapping) and "public_use_rights" in holder and holder["public_use_rights"] is not None:
            _validate_public_rights_value(holder["public_use_rights"])

    if snap.get("policy") is not None and snap.get("policy") != tv.POLICY:
        raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_INVALID", reason="POLICY_MISMATCH")
    if snap.get("target_drawn") is True or overlay.target_drawn(asset):
        raise CachedChartFallbackError("CC760_PRIVATE_OR_R_MULTIPLE_LEAK", reason="TARGET_DRAWN_FORBIDDEN")
    if snap.get("levels_drawn") not in (None, []):
        raise CachedChartFallbackError("CC760_PUBLIC_RIGHTS_INVALID", reason="RAW_LEVELS_DRAWN_FORBIDDEN")

    private_texts = pages.private_source_texts(run) if run.get("documents") else []
    _check_privacy_and_r_leaks(candidate=candidate, asset=asset, snap=snap, private_texts=private_texts)

    return {
        "market": market,
        "tv_symbol": expected_tv_symbol,
        "interval": interval,
        "snapshot": snap,
        "captured_at_utc": captured_at,
        "window_start_utc": window_start,
        "window_end_utc": window_end,
        "age_seconds": round(age_seconds, 3),
        "max_age_seconds": max_age,
        "now_utc": now_utc,
        "source_kind": str(candidate.get("source_kind") or "bound_candidate"),
        "source_key": candidate.get("source_key"),
    }


def discover_setup_post_candidates(
    setup_post_dir: Path | str | None,
    *,
    setup_record: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Collect candidate chart records from a same-plan setup post directory (read-only)."""
    if setup_post_dir is None:
        return []
    folder = Path(setup_post_dir)
    if not folder.is_dir():
        return []

    context = _read_json_mapping(folder / "run_context_v1.json") or {}
    plan_binding = _read_json_mapping(folder / "plan_binding_v1.json")
    source_key = context.get("plan_status_post") or (
        setup_record.get("key") if isinstance(setup_record, Mapping) else None
    ) or folder.name

    # If a store-bound setup_record was provided, refuse mismatched folder keys immediately.
    bound_setup = None
    if isinstance(setup_record, Mapping) and setup_record.get("key"):
        if setup_record["key"] == folder.name and (
            not context.get("plan_status_post") or context.get("plan_status_post") == setup_record["key"]
        ):
            bound_setup = dict(setup_record)

    candidates: list[dict[str, Any]] = []
    seen_snapshots: set[tuple[str, str]] = set()

    # 1. Inspect media assets recorded in run_context_v1.json (preserves exact rights & source_binding).
    assets = (context.get("media") or {}).get("assets") if isinstance(context.get("media"), Mapping) else []
    if isinstance(assets, list):
        for asset in assets:
            if not isinstance(asset, Mapping):
                continue
            snap = asset.get("tradingview_snapshot")
            if not isinstance(snap, Mapping):
                tmpl = asset.get("image_template")
                if isinstance(tmpl, Mapping) and isinstance(tmpl.get("snapshot"), Mapping):
                    snap = tmpl["snapshot"]
            if not isinstance(snap, Mapping):
                continue
            sig = (str(snap.get("path") or ""), str(snap.get("sha256") or ""))
            seen_snapshots.add(sig)
            candidates.append({
                "source_kind": "setup_post_run_context",
                "source_key": source_key,
                "asset": dict(asset),
                "snapshot": dict(snap),
                **({"plan_binding": plan_binding} if plan_binding else {}),
                **({"setup_record": bound_setup} if bound_setup else {}),
                **({"source_plan": context["source_plan"]} if isinstance(context.get("source_plan"), Mapping) else {}),
            })

    # 2. Inspect 16:9 capture state files in setup_post_dir not already covered by run_context.
    for filename in ("tradingview_capture_v1.json", "tradingview_capture_cc465_v1.json"):
        state = _read_json_mapping(folder / filename)
        if not state or state.get("status") != "CAPTURED" or not isinstance(state.get("snapshot"), Mapping):
            continue
        snap = state["snapshot"]
        sig = (str(snap.get("path") or ""), str(snap.get("sha256") or ""))
        if sig in seen_snapshots:
            continue
        seen_snapshots.add(sig)
        # Never invent missing rights_basis or plan_id: only carry what exists in state/plan_binding/setup_record.
        entry: dict[str, Any] = {
            "source_kind": f"setup_post_{filename}",
            "source_key": state.get("key") or source_key,
            "capture_state": state,
            "snapshot": dict(snap),
        }
        if plan_binding:
            entry["plan_binding"] = plan_binding
        if bound_setup:
            entry["setup_record"] = bound_setup
        if isinstance(context.get("source_plan"), Mapping):
            entry["source_plan"] = context["source_plan"]
        for field in ("rights_basis", "public_use_rights", "credit", "provenance_status"):
            if state.get(field) is not None:
                entry[field] = state[field]
            elif plan_binding and plan_binding.get(field) is not None:
                entry[field] = plan_binding[field]
        candidates.append(entry)

    return candidates


def resolve_cached_plan_chart(
    plan: Mapping[str, Any],
    run: Mapping[str, Any],
    folder: Path | str,
    manuscript: Mapping[str, Any],
    *,
    setup_post_dir: Path | str | None = None,
    setup_record: Mapping[str, Any] | None = None,
    candidates: Sequence[Mapping[str, Any]] | None = None,
    final_status: Mapping[str, Any] | None = None,
    now: datetime | str | None = None,
    max_age_seconds: float = DEFAULT_MAX_CACHE_AGE_SECONDS,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """On capture timeout/expiry, return (verified_asset, refusals) or (None, refusals) fail-closed."""
    from . import plan_analysis_pages_v1 as pages
    from . import publication_image_contract_v1 as contract
    from . import tradingview_snapshot_v1 as tv

    folder_path = Path(folder)
    key = "plan-analysis-" + str(plan.get("plan_id") or "")
    market = plan.get("asset_id")
    capture_state = _read_json_mapping(folder_path / "tradingview_capture_v1.json")
    timed_out, timeout_cause = is_timeout_capture_state(
        capture_state,
        expected_key=key,
        expected_market=market,
    )
    if not timed_out or not timeout_cause:
        return None, []

    pool: list[Mapping[str, Any]] = []
    if candidates is not None:
        pool.extend(candidates)
    if setup_post_dir is not None:
        pool.extend(discover_setup_post_candidates(setup_post_dir, setup_record=setup_record))
    if not pool:
        return None, []

    refusals: list[dict[str, Any]] = []
    private_texts = pages.private_source_texts(run) if run.get("documents") else []

    for index, candidate in enumerate(pool):
        try:
            verified = validate_cached_chart_candidate(
                candidate,
                plan=plan,
                run=run,
                manuscript=manuscript,
                now=now,
                final_status=final_status,
                max_age_seconds=max_age_seconds,
            )
            clean_snap = deepcopy(verified["snapshot"])
            # Strip any stale framing/overlay hints from another surface so the canonical page frames
            # the exact uncropped original TradingView PNG cleanly.
            clean_snap.pop("framing", None)
            clean_snap["policy"] = tv.POLICY
            clean_snap["levels_drawn"] = []
            clean_snap["target_drawn"] = False

            asset = tv.snapshot_asset(
                verified["market"],
                manuscript["title"],
                clean_snap,
                folder_path / "media_assets",
                ratio="16:9",
            )
            tv.validate_snapshot_asset(asset, {"market_asset": verified["market"]})
            contract.validate_scale(verified["market"], asset["tradingview_snapshot"])
            _check_privacy_and_r_leaks(
                candidate=asset,
                asset=asset,
                snap=asset["tradingview_snapshot"],
                private_texts=private_texts,
            )

            audit = {
                "policy": POLICY,
                "capture_key": key,
                "capture_cause": timeout_cause,
                "plan_id": plan["plan_id"],
                "registration_hash": plan["registration_hash"],
                "analysis_result_hash": plan.get("analysis_result_hash"),
                "run_id": plan.get("run_id"),
                **(
                    {"plan_revision": plan.get("plan_revision") if plan.get("plan_revision") is not None else plan.get("revision")}
                    if (plan.get("plan_revision") is not None or plan.get("revision") is not None)
                    else {}
                ),
                "symbol": verified["market"],
                "tv_symbol": verified["tv_symbol"],
                "interval": verified["interval"],
                "source_kind": verified["source_kind"],
                "source_key": verified["source_key"],
                "source_captured_at_utc": verified["captured_at_utc"].isoformat(),
                "source_chart_sha256": verified["snapshot"]["sha256"],
                "source_window_start_utc": verified["window_start_utc"].isoformat(),
                "source_window_end_utc": (
                    verified["window_end_utc"].isoformat() if verified["window_end_utc"] else None
                ),
                "cache_age_seconds": verified["age_seconds"],
                "max_cache_age_seconds": verified["max_age_seconds"],
                "public_use_rights_verified": True,
                "rights_basis": tv.RIGHTS_BASIS,
                "invariants_verified": list(INVARIANTS_VERIFIED),
                "substituted_at_utc": verified["now_utc"].isoformat(),
            }
            asset["cached_chart_fallback"] = audit
            tv.record_outcome({
                "status": "CACHED_CHART_FALLBACK_USED",
                "policy": POLICY,
                "key": key,
                "plan_id": plan["plan_id"],
                "market": verified["market"],
                "cause": timeout_cause,
                "source_kind": verified["source_kind"],
                "source_key": verified["source_key"],
                "source_chart_sha256": verified["snapshot"]["sha256"],
                "cache_age_seconds": verified["age_seconds"],
            })
            return asset, refusals
        except CachedChartFallbackError as exc:
            refusals.append({
                "candidate_index": index,
                "source_kind": candidate.get("source_kind") if isinstance(candidate, Mapping) else None,
                "source_key": candidate.get("source_key") if isinstance(candidate, Mapping) else None,
                "cause": exc.cause,
            })
        except (OSError, ValueError, KeyError, TypeError) as exc:
            refusals.append({
                "candidate_index": index,
                "source_kind": candidate.get("source_kind") if isinstance(candidate, Mapping) else None,
                "source_key": candidate.get("source_key") if isinstance(candidate, Mapping) else None,
                "cause": f"CC760_FALLBACK_ERROR:{type(exc).__name__}",
            })

    if refusals:
        tv.record_outcome({
            "status": "CACHED_CHART_FALLBACK_REFUSED",
            "policy": POLICY,
            "key": key,
            "plan_id": plan.get("plan_id"),
            "market": market,
            "cause": timeout_cause,
            "refusal_causes": [item["cause"] for item in refusals],
        })
    return None, refusals


def validate_cached_fallback_asset(
    asset: Mapping[str, Any],
    plan: Mapping[str, Any],
    run: Mapping[str, Any],
    *,
    manuscript: Mapping[str, Any] | None = None,
    folder: Path | str,
    final_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-verify a bound cached TradingView chart fallback at registration and write boundaries."""
    from . import plan_analysis_pages_v1 as pages
    from . import publication_image_contract_v1 as contract
    from . import tradingview_snapshot_v1 as tv

    binding = asset.get("cached_chart_fallback")
    if not isinstance(binding, Mapping):
        raise CachedChartFallbackError("CC760_FALLBACK_BINDING_INVALID")

    key = "plan-analysis-" + str(plan.get("plan_id") or "")
    market = plan.get("asset_id")
    folder_path = Path(folder)
    capture_state = _read_json_mapping(folder_path / "tradingview_capture_v1.json")
    timed_out, timeout_cause = is_timeout_capture_state(
        capture_state,
        expected_key=key,
        expected_market=market,
    )
    if not timed_out or not timeout_cause:
        raise CachedChartFallbackError("CC760_FALLBACK_CAPTURE_NOT_TIMED_OUT")

    substituted_at = _parse_utc(binding.get("substituted_at_utc"), error_cause="CC760_FALLBACK_BINDING_INVALID")
    started_at = _parse_utc(capture_state.get("started_at_utc"), error_cause="CC760_FALLBACK_BINDING_INVALID")
    elapsed = (substituted_at - started_at).total_seconds()
    if substituted_at < started_at or not (capture_state.get("attempts", 0) >= 2 or elapsed >= 300):
        raise CachedChartFallbackError("CC760_FALLBACK_CAPTURE_NOT_EXHAUSTED")

    max_age = binding.get("max_cache_age_seconds")
    if (
        isinstance(max_age, bool)
        or not isinstance(max_age, (int, float))
        or not math.isfinite(max_age)
        or not (0 < float(max_age) <= MAX_ALLOWED_CACHE_AGE_SECONDS)
    ):
        raise CachedChartFallbackError("CC760_SOURCE_WINDOW_INVALID", max_cache_age_seconds=max_age)

    if (
        binding.get("policy") != POLICY
        or binding.get("capture_key") != key
        or binding.get("capture_cause") != timeout_cause
        or binding.get("public_use_rights_verified") is not True
        or binding.get("rights_basis") != tv.RIGHTS_BASIS
        or list(binding.get("invariants_verified") or []) != list(INVARIANTS_VERIFIED)
    ):
        raise CachedChartFallbackError("CC760_FALLBACK_BINDING_INVALID")

    snap = asset.get("tradingview_snapshot") or {}
    if binding.get("source_chart_sha256") != snap.get("sha256"):
        raise CachedChartFallbackError("CC760_CHART_BYTES_MISMATCH")

    # Re-run all 5 invariants using the recorded substitution clock so historical readback stays deterministic
    # while any tampered symbol/plan/window/revision/rights/leak fails closed.
    candidate_view = {
        "asset": asset,
        "snapshot": snap,
        "plan_id": binding.get("plan_id"),
        "symbol": binding.get("symbol"),
        "registration_hash": binding.get("registration_hash"),
        "analysis_result_hash": binding.get("analysis_result_hash"),
        "run_id": binding.get("run_id"),
        **(
            {"plan_revision": binding["plan_revision"]}
            if "plan_revision" in binding
            else {}
        ),
        "rights_basis": binding.get("rights_basis"),
        "public_use_rights": binding.get("public_use_rights_verified"),
        "source_key": binding.get("source_key"),
        "source_kind": binding.get("source_kind"),
    }
    verified = validate_cached_chart_candidate(
        candidate_view,
        plan=plan,
        run=run,
        manuscript=manuscript,
        now=substituted_at,
        final_status=final_status,
        max_age_seconds=float(max_age),
    )

    expected_end = verified["window_end_utc"].isoformat() if verified["window_end_utc"] else None
    if (
        binding.get("tv_symbol") != verified["tv_symbol"]
        or binding.get("interval") != verified["interval"]
        or _parse_utc(binding.get("source_captured_at_utc")) != verified["captured_at_utc"]
        or _parse_utc(binding.get("source_window_start_utc")) != verified["window_start_utc"]
        or (
            (binding.get("source_window_end_utc") is None) != (expected_end is None)
            or (
                binding.get("source_window_end_utc") is not None
                and _parse_utc(binding.get("source_window_end_utc")) != verified["window_end_utc"]
            )
        )
        or abs(float(binding.get("cache_age_seconds", -1)) - verified["age_seconds"]) > 1.0
    ):
        raise CachedChartFallbackError("CC760_FALLBACK_BINDING_INVALID")

    tv.validate_snapshot_asset(asset, {"market_asset": verified["market"]})
    contract.validate_scale(verified["market"], snap)
    private_texts = pages.private_source_texts(run) if run.get("documents") else []
    _check_privacy_and_r_leaks(candidate=asset, asset=asset, snap=snap, private_texts=private_texts)
    return dict(binding)


def validate_write_cached_fallback(
    store: Any,
    intent: Mapping[str, Any],
    article: Mapping[str, Any],
    asset: Mapping[str, Any],
    folder: Path,
    now: datetime,
) -> dict[str, Any]:
    """Enforce CC-760 cached fallback binding at publication_image_contract_v1.validate_write."""
    from . import plan_analysis_pages_v1 as pages
    from . import publication_image_contract_v1 as contract

    page_id = str(intent.get("plan_analysis_page") or "")
    held = store.get_outbox_message(page_id) if page_id else None
    packet = json.loads(held["payload"]) if held else {}
    plan = packet.get("source_plan") or {}
    if not plan or packet.get("page_id") != page_id:
        raise contract.ImageContractError("CC760_FALLBACK_BINDING_INVALID")
    run = pages.load_run(plan, run_root=Path(packet["run_root"]))
    state = contract.exhausted_capture_state(article, folder, now=now)
    if not state:
        raise contract.ImageContractError("CC760_FALLBACK_CAPTURE_NOT_EXHAUSTED")
    try:
        return validate_cached_fallback_asset(
            asset,
            plan,
            run,
            manuscript=packet.get("manuscript"),
            folder=folder,
            final_status=packet.get("final_status"),
        )
    except CachedChartFallbackError as exc:
        raise contract.ImageContractError(exc.cause, **exc.details) from exc
