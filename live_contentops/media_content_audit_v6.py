"""Media content audit and source-backed chart generation for ContentOps V6.

This module checks whether a selected visual is editorially fit for the article,
not merely whether it downloaded. For current macro topics, unstructured search
images without machine-readable coverage/provenance fail closed so the pipeline
can prefer a source-backed generated chart instead of a stale screenshot.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Mapping

DEFAULT_MEDIA_DIR = Path("docs/automation/V6_MEDIA_SYSTEM/downloads")
WTI_SERIES_ID = "DCOILWTICO"
WTI_FRED_CSV_URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={WTI_SERIES_ID}"
WTI_FRED_SERIES_URL = f"https://fred.stlouisfed.org/series/{WTI_SERIES_ID}"
EIA_WTI_SOURCE_URL = "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm"
EIA_HORMUZ_CONTEXT_URL = "https://www.eia.gov/todayinenergy/detail.php?id=65504"
DFF_SERIES_ID = "DFF"
DFF_FRED_CSV_URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={DFF_SERIES_ID}"
DFF_FRED_SERIES_URL = f"https://fred.stlouisfed.org/series/{DFF_SERIES_ID}"
FED_RATES_FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF,DFEDTARL,DFEDTARU,IORB,SOFR,DGS2,DGS10,DGS30"
FED_RATES_FRED_SERIES_IDS = ("DFF", "DFEDTARL", "DFEDTARU", "IORB", "SOFR", "DGS2", "DGS10", "DGS30")
FED_H15_URL = "https://www.federalreserve.gov/releases/h15/"
FED_OPENMARKET_URL = "https://www.federalreserve.gov/monetarypolicy/openmarket.htm"
FED_IORB_URL = "https://www.federalreserve.gov/monetarypolicy/reserve-balances.htm"
FED_IMPLEMENTATION_NOTE_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20251210a1.htm"
NYFED_SOFR_URL = "https://www.newyorkfed.org/markets/reference-rates/sofr"


def _looks_like_oil_topic(text: str) -> bool:
    return any(term in text for term in ("oil", "wti", "crude", "energy", "petroleum", "hormuz"))


def _looks_like_fed_funds_topic(text: str) -> bool:
    terms = (
        "effective fed funds",
        "fed funds rate",
        "federal funds",
        "policy corridor",
        "iorb",
        "sofr",
        "overnight rate",
        "overnight rates",
        "fomc target",
        "rates candidate",
    )
    return any(term in text for term in terms)


def _fed_funds_fixture_scope() -> dict[str, Any]:
    """Describe the legacy deterministic Fed fixture without granting source authority."""
    return {
        "content_authority_scope": "TEMPORARY_CONTENTOPS_FALLBACK_FIXTURE",
        "future_numeric_source_authority": "FUTURE_CAPITAL_CHRONICLE_DATABASE_AUTHORITY",
        "contentops_role": "temporary deterministic fallback fixture for dry-run/public-candidate readiness only",
        "future_required_input": "CC_CONTENT_ARTIFACT_PACKET",
        "source_truth_boundary": (
            "ContentOps does not own Fed/FRED/NY Fed/Treasury rates source truth; "
            "it must consume approved Capital Chronicle artifacts later."
        ),
        "no_new_source_family_rule": (
            "No additional source families should be added directly to ContentOps unless explicitly approved."
        ),
    }


def _as_of_year(as_of_date: str | None = None) -> int:
    if as_of_date:
        try:
            return int(str(as_of_date)[:4])
        except Exception:
            pass
    return int(time.strftime("%Y", time.gmtime()))


def _tokens(text: str) -> set[str]:
    stop = {"the", "and", "for", "with", "that", "this", "from", "into", "are", "is", "as", "of", "to", "in", "on"}
    return {tok for tok in re.findall(r"[a-z0-9]+", text.lower()) if len(tok) > 2 and tok not in stop}


def infer_visual_requirements(article_title: str, article_text: str = "", as_of_date: str | None = None) -> dict[str, Any]:
    text = f"{article_title} {article_text}".lower()
    metric = "general_macro"
    if _looks_like_fed_funds_topic(text):
        metric = "fed_funds_policy_rates"
    elif _looks_like_oil_topic(text):
        metric = "oil"
    if "volatility" in text or "volatile" in text:
        metric = "oil_volatility" if metric == "oil" else "volatility"

    direction = "none"
    if any(term in text for term in ("rising", "rise", "rises", "spike", "spikes", "surge", "jumps", "moving up", "higher")):
        direction = "up"
    if any(term in text for term in ("falling", "falls", "decline", "declining", "moving down", "lower")):
        direction = "down" if direction == "none" else "mixed"

    historical_only = any(term in text for term in ("historical-only", "historical only", "long-run history", "prior cycles only"))
    year = _as_of_year(as_of_date)
    return {
        "as_of_year": year,
        "requires_current_coverage": not historical_only,
        "minimum_end_year": year - 1,
        "expected_metric": metric,
        "expected_direction": direction,
    }


def _metadata_year(metadata: dict[str, Any]) -> int | None:
    for key in ("latest_observation_year", "time_coverage_end_year", "data_end_year", "visible_end_year"):
        value = metadata.get(key)
        try:
            return int(value)
        except Exception:
            continue
    for key in ("latest_observation_date", "data_end_date", "time_coverage_end_date"):
        value = str(metadata.get(key) or "")
        if re.match(r"^\d{4}", value):
            return int(value[:4])
    return None


def _source_label(metadata: dict[str, Any], public_image_url: str | None) -> str:
    label = str(metadata.get("canonical_source_label") or metadata.get("source_label") or "").strip()
    if label:
        return label
    if public_image_url:
        return urllib.parse.urlparse(public_image_url).netloc
    return ""


def _is_search_or_upload_source(metadata: dict[str, Any], public_image_url: str | None) -> bool:
    source = " ".join(
        str(metadata.get(key) or "")
        for key in ("source_label", "canonical_source_label", "url", "source_url", "retrieval_method")
    ).lower()
    if public_image_url:
        source += " " + public_image_url.lower()
    return any(marker in source for marker in ("google", "wikimedia", "upload.", "encrypted-tbn", "image search", "commons"))


def audit_media_candidate(
    *,
    article_title: str,
    article_text: str = "",
    image_path: str | Path | None = None,
    public_image_url: str | None = None,
    source_metadata: dict[str, Any] | None = None,
    as_of_date: str | None = None,
) -> dict[str, Any]:
    metadata = dict(source_metadata or {})
    requirements = infer_visual_requirements(article_title, article_text, as_of_date)
    blockers: list[str] = []
    warnings: list[str] = []

    if not image_path and not public_image_url:
        blockers.append("media_missing")

    label = _source_label(metadata, public_image_url)
    if "generated fallback" in label.lower() or "branded text cover" in str(metadata.get("visual_metric") or "").lower():
        blockers.append("media_generated_fallback_not_editorial_visual")
    if label in {"upload.wikimedia.org", "commons.wikimedia.org"} and not metadata.get("canonical_source_label"):
        blockers.append("media_provenance_weak_upload_host")

    latest_year = _metadata_year(metadata)
    if requirements["requires_current_coverage"]:
        if latest_year is None:
            if _is_search_or_upload_source(metadata, public_image_url):
                blockers.append("media_time_coverage_unverified_for_current_topic")
            else:
                warnings.append("media_time_coverage_missing")
        elif latest_year < requirements["minimum_end_year"]:
            blockers.append(f"media_outdated_time_coverage:{latest_year}<{requirements['minimum_end_year']}")

    expected_metric = str(requirements["expected_metric"])
    visual_metric = str(metadata.get("visual_metric") or metadata.get("media_subject") or metadata.get("query") or "").lower()
    if expected_metric == "oil_volatility":
        if "volatility" not in visual_metric and "range" not in visual_metric:
            blockers.append("media_metric_mismatch:expected_oil_volatility_context")
    elif expected_metric == "oil" and "oil" not in visual_metric and "wti" not in visual_metric and "crude" not in visual_metric:
        warnings.append("media_metric_weak_match")
    elif expected_metric == "fed_funds_policy_rates":
        allowed = ("fed funds", "federal funds", "policy corridor", "iorb", "sofr", "overnight", "rates", "interest rate", "treasury")
        if not any(term in visual_metric for term in allowed):
            blockers.append("media_metric_mismatch:expected_fed_funds_policy_rates_context")
        if any(term in visual_metric for term in ("oil", "wti", "crude", "hormuz", "petroleum", "energy supply")):
            blockers.append("media_family_mismatch:oil_visual_for_fed_funds_topic")

    expected_direction = str(requirements["expected_direction"])
    actual_direction = str(metadata.get("recent_direction") or metadata.get("visual_direction") or "").lower()
    if expected_direction in {"up", "down"}:
        if actual_direction in {"up", "down"} and actual_direction != expected_direction:
            blockers.append(f"media_direction_mismatch:expected_{expected_direction}_actual_{actual_direction}")
        elif not actual_direction and _is_search_or_upload_source(metadata, public_image_url):
            warnings.append("media_direction_unverified_for_directional_article")

    relevance_tokens = _tokens(article_title) & _tokens(
        " ".join(str(metadata.get(key) or "") for key in ("query", "visual_metric", "caption", "alt_text", "source_url", "url"))
    )
    if len(relevance_tokens) < 2 and expected_metric != "general_macro":
        warnings.append("media_relevance_weak_token_match")

    return {
        "audit_status": "FAIL" if blockers else "PASS",
        "blockers": blockers,
        "warnings": warnings,
        "requirements": requirements,
        "latest_detected_year": latest_year,
        "source_label": label,
        "llm_review_recommended": bool(blockers or warnings),
    }


def _read_fred_csv(fetch_url: str = WTI_FRED_CSV_URL, timeout_seconds: int = 15) -> list[tuple[date, float]]:
    req = urllib.request.Request(fetch_url, headers={"User-Agent": "CapitalChronicleContentOps/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
        text = response.read().decode("utf-8", errors="ignore")
    rows: list[tuple[date, float]] = []
    for row in csv.DictReader(text.splitlines()):
        raw_date = row.get("DATE") or row.get("observation_date") or ""
        raw_value = row.get(WTI_SERIES_ID) or row.get("value") or ""
        if not raw_date or raw_value in {"", "."}:
            continue
        try:
            rows.append((datetime.strptime(raw_date, "%Y-%m-%d").date(), float(raw_value)))
        except Exception:
            continue
    rows.sort(key=lambda item: item[0])
    return rows


def _recent_direction(points: list[tuple[date, float]], lookback: int = 90) -> str:
    if len(points) < 2:
        return "unknown"
    latest = points[-1][1]
    prior = points[max(0, len(points) - lookback)][1]
    if prior <= 0:
        return "unknown"
    change = (latest - prior) / prior
    if change > 0.03:
        return "up"
    if change < -0.03:
        return "down"
    return "mixed"


def _rolling_abs_change(points: list[tuple[date, float]], window: int = 30) -> list[tuple[date, float]]:
    changes: list[tuple[date, float]] = []
    pct: list[float] = []
    prev = None
    for dt, value in points:
        if prev and prev > 0:
            pct.append(abs((value - prev) / prev) * 100.0)
            if len(pct) >= window:
                changes.append((dt, sum(pct[-window:]) / window))
        prev = value
    return changes


def _write_metadata(path: Path, metadata: dict[str, Any]) -> None:
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _retrieved_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def render_current_wti_visual_pack(
    *,
    article_title: str,
    output_dir: str | Path = DEFAULT_MEDIA_DIR,
    as_of_date: str | None = None,
    fetch_url: str = WTI_FRED_CSV_URL,
) -> list[dict[str, Any]]:
    points = _read_fred_csv(fetch_url)
    if len(points) < 60:
        return []

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return []

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = hashlib.sha256(article_title.lower().encode("utf-8")).hexdigest()[:12]
    latest_date, latest_value = points[-1]
    prior_date, prior_value = points[-2]
    latest_year = latest_date.year
    vol_points = _rolling_abs_change(points)
    price_dir = _recent_direction(points)
    vol_dir = _recent_direction(vol_points) if len(vol_points) >= 2 else "unknown"

    cutoff_year = max(latest_year - 5, points[0][0].year)
    recent_points = [(dt, val) for dt, val in points if dt.year >= cutoff_year]
    recent_vol = [(dt, val) for dt, val in vol_points if dt.year >= cutoff_year]

    assets: list[dict[str, Any]] = []

    primary_path = out_dir / f"wti_current_volatility_context_{safe}.png"
    fig, (ax_price, ax_vol) = plt.subplots(2, 1, figsize=(11.5, 7.2), dpi=150, sharex=True)
    ax_price.plot([dt for dt, _ in recent_points], [val for _, val in recent_points], color="#1d4ed8", linewidth=2.1)
    ax_price.set_title("WTI Crude Oil: Current Price Context and Realized Volatility")
    ax_price.set_ylabel("Dollars per barrel")
    ax_price.grid(True, alpha=0.22)
    ax_price.annotate(f"Latest: ${latest_value:.2f}\n{latest_date.isoformat()}", xy=(latest_date, latest_value), xytext=(-95, 18), textcoords="offset points", fontsize=8, arrowprops={"arrowstyle": "->", "color": "#64748b"})
    ax_vol.plot([dt for dt, _ in recent_vol], [val for _, val in recent_vol], color="#dc2626", linewidth=1.9)
    ax_vol.set_ylabel("30-day avg abs daily move (%)")
    ax_vol.grid(True, alpha=0.22)
    ax_vol.set_xlabel("Source: FRED series DCOILWTICO; underlying source: U.S. Energy Information Administration")
    fig.tight_layout()
    fig.savefig(primary_path, facecolor="white")
    plt.close(fig)
    primary_meta = {
        "asset_id": "primary",
        "media_class": "data_chart",
        "media_role": "primary_chart",
        "chart_title": "WTI Crude Oil: Current Price Context and Realized Volatility",
        "canonical_article_section_association": "current_market_signal_and_supply_repricing",
        "url": WTI_FRED_SERIES_URL,
        "source_url": WTI_FRED_SERIES_URL,
        "source_page_url": WTI_FRED_SERIES_URL,
        "source_domain": "fred.stlouisfed.org",
        "image_url": None,
        "source_label": "FRED / U.S. Energy Information Administration",
        "canonical_source_label": "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration",
        "query": article_title,
        "recency_days": 365,
        "time_filter": "current_source_series_latest_available_observation",
        "retrieval_timestamp": _retrieved_at(),
        "rights_status": "source_backed_generated_visual_cc_owned",
        "provenance_status": "source_backed_generated_from_public_data",
        "operator_review_required": False,
        "why_selected": "Primary source-backed chart with current WTI endpoint and realized-volatility context for the article thesis.",
        "visual_metric": "oil_volatility wti crude oil current price realized volatility",
        "media_subject": "WTI crude oil current price and volatility context",
        "latest_observation_date": latest_date.isoformat(),
        "latest_observation_year": latest_year,
        "latest_observation_value": latest_value,
        "prior_observation_date": prior_date.isoformat(),
        "prior_observation_value": prior_value,
        "time_coverage_end_year": latest_year,
        "recent_direction": vol_dir,
        "recent_price_direction": price_dir,
        "caption": f"WTI crude oil price and 30-day realized volatility through {latest_date.isoformat()}. Source: FRED series DCOILWTICO; underlying source: U.S. Energy Information Administration.",
        "alt_text": "Two-panel chart showing current WTI crude oil price and rolling absolute daily moves using FRED data.",
        "local_path": str(primary_path),
        "public_url": None,
    }
    _write_metadata(primary_path, primary_meta)
    assets.append(primary_meta)

    secondary_path = out_dir / f"wti_recent_price_context_{safe}.png"
    one_year_points = recent_points[-260:] if len(recent_points) > 260 else recent_points
    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=150)
    ax.plot([dt for dt, _ in one_year_points], [val for _, val in one_year_points], color="#0f766e", linewidth=2.3)
    ax.set_title("WTI Crude Oil: Recent Price Path")
    ax.set_ylabel("Dollars per barrel")
    ax.set_xlabel("Source: FRED series DCOILWTICO; U.S. Energy Information Administration")
    ax.grid(True, alpha=0.24)
    ax.annotate(f"${latest_value:.2f}\n{latest_date.isoformat()}", xy=(latest_date, latest_value), xytext=(-84, 20), textcoords="offset points", fontsize=8, arrowprops={"arrowstyle": "->", "color": "#64748b"})
    fig.tight_layout()
    fig.savefig(secondary_path, facecolor="white")
    plt.close(fig)
    secondary_meta = {
        **primary_meta,
        "asset_id": "recent_price",
        "media_role": "supporting_chart",
        "chart_title": "WTI Crude Oil: Recent Price Path",
        "canonical_article_section_association": "hormuz_flow_and_price_mechanism",
        "visual_metric": "wti crude oil current recent price path",
        "media_subject": "WTI crude oil recent price path",
        "recent_direction": price_dir,
        "recent_volatility_direction": vol_dir,
        "caption": f"Recent WTI price path through {latest_date.isoformat()}. Source: FRED series DCOILWTICO; underlying source: U.S. Energy Information Administration.",
        "alt_text": "Line chart showing the recent WTI crude oil price path using FRED data.",
        "why_selected": "Supporting chart gives a narrower recent-price view so platforms are not repeating the same volatility chart only.",
        "local_path": str(secondary_path),
    }
    _write_metadata(secondary_path, secondary_meta)
    assets.append(secondary_meta)

    range_path = out_dir / f"wti_multi_year_range_context_{safe}.png"
    by_year: dict[int, list[float]] = {}
    for dt, value in recent_points:
        by_year.setdefault(dt.year, []).append(value)
    years = sorted(by_year)
    averages = [sum(by_year[year]) / len(by_year[year]) for year in years]
    lows = [min(by_year[year]) for year in years]
    highs = [max(by_year[year]) for year in years]
    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=150)
    ax.fill_between(years, lows, highs, color="#bfdbfe", alpha=0.55, label="Annual low-high range")
    ax.plot(years, averages, color="#1d4ed8", marker="o", linewidth=2.2, label="Annual average")
    ax.set_title("WTI Crude Oil: Multi-Year Price Range Context")
    ax.set_ylabel("Dollars per barrel")
    ax.set_xlabel("Source: FRED series DCOILWTICO; U.S. Energy Information Administration")
    ax.grid(True, alpha=0.24)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(range_path, facecolor="white")
    plt.close(fig)
    range_meta = {
        **primary_meta,
        "asset_id": "multi_year_range",
        "media_role": "supporting_chart",
        "chart_title": "WTI Crude Oil: Multi-Year Price Range Context",
        "canonical_article_section_association": "cross_asset_and_historical_regime_context",
        "visual_metric": "wti crude oil multi year price range context",
        "media_subject": "WTI crude oil multi-year annual range and average",
        "recent_direction": price_dir,
        "recent_volatility_direction": vol_dir,
        "caption": f"WTI annual price range and average context through {latest_date.isoformat()}. Source: FRED series DCOILWTICO; underlying source: U.S. Energy Information Administration.",
        "alt_text": "Chart showing recent annual WTI crude oil low-high ranges and annual averages using FRED data.",
        "why_selected": "Third FRED-backed chart gives multi-year context without using a custom static card or non-chart schematic.",
        "local_path": str(range_path),
    }
    _write_metadata(range_path, range_meta)
    assets.append(range_meta)

    return assets


def _read_fred_multi_series(
    fetch_url: str = FED_RATES_FRED_CSV_URL,
    series_ids: tuple[str, ...] = FED_RATES_FRED_SERIES_IDS,
) -> dict[str, list[tuple[date, float]]]:
    """Read current FRED series, including its ZIP multi-frequency response."""
    request = urllib.request.Request(fetch_url, headers={"User-Agent": "CapitalChronicleContentOps/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read()
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            csv_texts = [
                archive.read(name).decode("utf-8", errors="ignore")
                for name in archive.namelist()
                if name.lower().endswith(".csv")
            ]
    else:
        csv_texts = [raw.decode("utf-8", errors="ignore")]

    output: dict[str, list[tuple[date, float]]] = {series_id: [] for series_id in series_ids}
    for text in csv_texts:
        for row in csv.DictReader(text.splitlines()):
            raw_date = row.get("DATE") or row.get("observation_date") or ""
            try:
                observation_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                continue
            for series_id in series_ids:
                raw_value = str(row.get(series_id) or "").strip()
                if raw_value in {"", "."}:
                    continue
                try:
                    output[series_id].append((observation_date, float(raw_value)))
                except ValueError:
                    continue
    for series_id, points in output.items():
        output[series_id] = sorted({item_date: value for item_date, value in points}.items())
    return output


def _latest_at_or_before(points: list[tuple[date, float]], cutoff: date) -> tuple[date, float] | None:
    for item in reversed(points):
        if item[0] <= cutoff:
            return item
    return None


def _bounded_points(points: list[tuple[date, float]], as_of_date: str | None) -> list[tuple[date, float]]:
    if not as_of_date:
        return points
    try:
        cutoff = datetime.strptime(as_of_date[:10], "%Y-%m-%d").date()
    except ValueError:
        return points
    return [item for item in points if item[0] <= cutoff]


def render_current_fed_funds_visual_pack(
    *,
    article_title: str,
    output_dir: str | Path = DEFAULT_MEDIA_DIR,
    as_of_date: str | None = None,
    fetch_url: str = FED_RATES_FRED_CSV_URL,
    series_loader: Callable[[str], Mapping[str, list[tuple[date, float]]]] | None = None,
) -> list[dict[str, Any]]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return []

    loader = series_loader or _read_fred_multi_series
    try:
        source_series = {
            series_id: _bounded_points(list(points), as_of_date)
            for series_id, points in loader(fetch_url).items()
        }
    except Exception:
        return []
    points = source_series.get("DFF") or []
    if len(points) < 2:
        return []
    latest_date, latest_value = points[-1]
    prior_date, prior_value = points[-2]
    lower_point = _latest_at_or_before(source_series.get("DFEDTARL") or [], latest_date)
    upper_point = _latest_at_or_before(source_series.get("DFEDTARU") or [], latest_date)
    iorb_point = _latest_at_or_before(source_series.get("IORB") or [], latest_date)
    sofr_point = _latest_at_or_before(source_series.get("SOFR") or [], latest_date)
    two_year_point = _latest_at_or_before(source_series.get("DGS2") or [], latest_date)
    ten_year_point = _latest_at_or_before(source_series.get("DGS10") or [], latest_date)
    thirty_year_point = _latest_at_or_before(source_series.get("DGS30") or [], latest_date)
    if not all((lower_point, upper_point, iorb_point, sofr_point, two_year_point, ten_year_point, thirty_year_point)):
        return []

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = hashlib.sha256(article_title.lower().encode("utf-8")).hexdigest()[:12]
    latest_year = latest_date.year
    target_lower = lower_point[1]
    target_upper = upper_point[1]
    iorb = iorb_point[1]
    recent_points = points[-90:]
    target_floor_points = [(_latest_at_or_before(source_series["DFEDTARL"], item_date) or lower_point)[1] for item_date, _value in recent_points]
    target_ceiling_points = [(_latest_at_or_before(source_series["DFEDTARU"], item_date) or upper_point)[1] for item_date, _value in recent_points]

    base_meta = {
        "content_authority_scope": "SOURCE_BACKED_FRED_VISUAL_CONSTRUCTION",
        "capital_chronicle_database_role": "Capital Chronicle remains the durable numeric and context authority; this run retrieves official FRED series only to render cited charts.",
        "url": DFF_FRED_SERIES_URL,
        "source_url": DFF_FRED_SERIES_URL,
        "source_page_url": DFF_FRED_SERIES_URL,
        "source_domain": "fred.stlouisfed.org",
        "image_url": None,
        "source_label": "FRED / Board of Governors of the Federal Reserve System",
        "canonical_source_label": "FRED series DFF, DFEDTARL, DFEDTARU, IORB, SOFR, DGS2, DGS10, and DGS30; Board of Governors and Federal Reserve Bank of New York sources",
        "query": article_title,
        "recency_days": 365,
        "time_filter": "current_source_series_latest_available_observation",
        "retrieval_timestamp": _retrieved_at(),
        "source_data_fetch_url": fetch_url,
        "source_series_ids": list(FED_RATES_FRED_SERIES_IDS),
        "data_fetch_method": "fred_csv_live_or_injected_fixture",
        "rights_status": "source_backed_generated_visual_cc_owned",
        "provenance_status": "source_backed_generated_from_public_federal_reserve_data",
        "operator_review_required": False,
        "latest_observation_date": latest_date.isoformat(),
        "latest_observation_year": latest_year,
        "latest_observation_value": latest_value,
        "prior_observation_date": prior_date.isoformat(),
        "prior_observation_value": prior_value,
        "target_lower": target_lower,
        "target_upper": target_upper,
        "iorb_value": iorb,
        "time_coverage_end_year": latest_year,
        "public_url": None,
        "dry_run_fixture_asset": str(fetch_url).startswith("file:"),
    }

    assets: list[dict[str, Any]] = []

    primary_path = out_dir / f"fed_funds_policy_corridor_context_{safe}.png"
    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=150)
    ax.plot([dt for dt, _ in recent_points], [value for _, value in recent_points], color="#1d4ed8", linewidth=2.4, marker="o", markersize=3.4, label="Effective fed funds")
    ax.fill_between([dt for dt, _ in recent_points], target_floor_points, target_ceiling_points, color="#dbeafe", alpha=0.72, label="Target range")
    ax.axhline(iorb, color="#7c3aed", linewidth=1.8, linestyle="--", label="IORB")
    ax.set_title("Effective Fed Funds Rate Inside the Policy Corridor")
    ax.set_ylabel("Percent")
    ax.set_xlabel("Source: FRED DFF, DFEDTARL, DFEDTARU, and IORB")
    ax.set_ylim(min(target_floor_points + [latest_value, iorb]) - 0.10, max(target_ceiling_points + [latest_value, iorb]) + 0.10)
    ax.grid(True, alpha=0.24)
    ax.annotate(f"{latest_value:.2f}%\n{latest_date.isoformat()}", xy=(latest_date, latest_value), xytext=(-92, 24), textcoords="offset points", fontsize=8, arrowprops={"arrowstyle": "->", "color": "#64748b"})
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(primary_path, facecolor="white")
    plt.close(fig)
    primary_meta = {
        **base_meta,
        "asset_id": "primary",
        "media_class": "data_chart",
        "media_role": "primary_chart",
        "chart_title": "Effective Fed Funds Rate Inside the Policy Corridor",
        "canonical_article_section_association": "lede_and_current_policy_signal",
        "why_selected": "Primary source-backed chart showing the effective fed funds rate inside the Federal Reserve policy corridor for the selected non-oil topic.",
        "visual_metric": "fed funds policy rates effective federal funds rate policy corridor iorb interest rate context",
        "media_subject": "Effective federal funds rate and policy corridor context",
        "recent_direction": "flat",
        "prior_observation_date": prior_date.isoformat(),
        "prior_observation_value": prior_value,
        "caption": f"Effective federal funds rate at {latest_value:.2f}% on {latest_date.isoformat()}, compared with {prior_value:.2f}% on {prior_date.isoformat()}, inside the {target_lower:.2f}% to {target_upper:.2f}% target range. Source: FRED DFF, DFEDTARL, DFEDTARU, and IORB.",
        "alt_text": "Line chart showing the effective federal funds rate inside the Federal Reserve target range with an IORB reference line.",
        "local_path": str(primary_path),
    }
    _write_metadata(primary_path, primary_meta)
    assets.append(primary_meta)

    corridor_path = out_dir / f"fed_funds_administered_rates_context_{safe}.png"
    fig, ax = plt.subplots(figsize=(10.8, 6.0), dpi=150)
    rate_rows = [
        ("Target lower", target_lower, "#0f766e"),
        ("DFF", latest_value, "#1d4ed8"),
        ("IORB", iorb, "#7c3aed"),
        ("Target upper", target_upper, "#dc2626"),
    ]
    labels = [item[0] for item in rate_rows]
    values = [item[1] for item in rate_rows]
    colors = [item[2] for item in rate_rows]
    bars = ax.barh(labels, values, color=colors, alpha=0.9)
    ax.axvspan(target_lower, target_upper, color="#dbeafe", alpha=0.72, label="Target range")
    ax.set_xlim(min(values) - 0.10, max(values) + 0.10)
    ax.set_xlabel("Percent")
    ax.set_title("Federal Reserve Administered Rates and Effective Fed Funds")
    ax.grid(True, axis="x", alpha=0.22)
    for bar, value in zip(bars, values):
        ax.text(value + 0.008, bar.get_y() + bar.get_height() / 2, f"{value:.2f}%", va="center", fontsize=9, color="#0f172a")
    ax.legend(loc="lower right", fontsize=8)
    fig.text(
        0.5,
        0.01,
        "Sources: FRED DFF, DFEDTARL, DFEDTARU, and IORB; Board of Governors of the Federal Reserve System.",
        ha="center",
        fontsize=8.3,
        color="#475569",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(corridor_path, facecolor="white")
    plt.close(fig)
    corridor_meta = {
        **base_meta,
        "asset_id": "policy_corridor",
        "media_class": "data_chart",
        "media_role": "supporting_policy_rates_chart",
        "chart_title": "Federal Reserve Administered Rates and Effective Fed Funds",
        "canonical_article_section_association": "policy_transmission_mechanism",
        "url": DFF_FRED_SERIES_URL,
        "source_url": DFF_FRED_SERIES_URL,
        "source_page_url": FED_OPENMARKET_URL,
        "source_domain": "fred.stlouisfed.org",
        "source_label": "FRED / Board of Governors of the Federal Reserve System",
        "canonical_source_label": "FRED series DFF, DFEDTARL, DFEDTARU, and IORB policy-corridor comparison",
        "why_selected": "Source-backed administered-rates chart gives the policy mechanism without a decorative schematic or fixed-rate fallback.",
        "visual_metric": "fed funds target range dff iorb administered rates data chart",
        "media_subject": "Federal Reserve target range, IORB, and effective fed funds comparison",
        "recent_direction": "current_level_comparison",
        "caption": f"Policy-corridor comparison on the latest DFF date: target lower {target_lower:.2f}%, DFF {latest_value:.2f}%, IORB {iorb:.2f}%, and target upper {target_upper:.2f}%. Sources: FRED DFF, DFEDTARL, DFEDTARU, and IORB.",
        "alt_text": "Horizontal bar chart comparing the Federal Reserve target lower bound, effective fed funds rate, IORB, and target upper bound using FRED data.",
        "local_path": str(corridor_path),
    }
    _write_metadata(corridor_path, corridor_meta)
    assets.append(corridor_meta)

    sofr_path = out_dir / f"fed_funds_sofr_context_{safe}.png"
    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=150)
    labels = ["DFF", "SOFR", "2Y Treasury", "10Y Treasury", "30Y Treasury"]
    values = [latest_value, sofr_point[1], two_year_point[1], ten_year_point[1], thirty_year_point[1]]
    colors = ["#1d4ed8", "#0f766e", "#b45309", "#7c2d12", "#7c3aed"]
    ax.bar(labels, values, color=colors, alpha=0.88)
    ax.set_ylim(min(values) - 0.15, max(values) + 0.25)
    ax.set_ylabel("Percent")
    ax.set_title("Rates Context: Overnight Policy Rate vs Treasury Curve Points")
    ax.set_xlabel("Sources: FRED DFF, SOFR, DGS2, DGS10, and DGS30")
    ax.grid(True, axis="y", alpha=0.24)
    for idx, value in enumerate(values):
        ax.text(idx, value + 0.04, f"{value:.2f}%", ha="center", fontsize=9, color="#0f172a")
    ax.text(
        0.04,
        min(values) - 0.09,
        f"Latest available dates: DFF {latest_date.isoformat()}; SOFR {sofr_point[0].isoformat()}; Treasury yields {two_year_point[0].isoformat()}.",
        fontsize=8.4,
        color="#475569",
    )
    fig.tight_layout()
    fig.savefig(sofr_path, facecolor="white")
    plt.close(fig)
    sofr_meta = {
        **base_meta,
        "asset_id": "sofr_context",
        "media_class": "data_chart",
        "media_role": "supporting_rates_chart",
        "chart_title": "Rates Context: Overnight Policy Rate vs Treasury Curve Points",
        "canonical_article_section_association": "cross_asset_and_treasury_curve_context",
        "url": NYFED_SOFR_URL,
        "source_url": NYFED_SOFR_URL,
        "source_page_url": NYFED_SOFR_URL,
        "source_domain": "fred.stlouisfed.org",
        "source_label": "FRED / Federal Reserve Bank of New York / Board of Governors",
        "canonical_source_label": "FRED series DFF, SOFR, DGS2, DGS10, and DGS30; Federal Reserve Bank of New York and Board of Governors sources",
        "why_selected": "Supporting rates-context visual distinguishes DFF, SOFR, and Treasury yields using current source data rather than fixed values.",
        "visual_metric": "fed funds sofr treasury rates overnight policy interest rate context",
        "media_subject": "SOFR methodology and Treasury rates context for fed funds article",
        "recent_direction": "contextual",
        "caption": f"Latest available rates: DFF {latest_value:.2f}% ({latest_date.isoformat()}), SOFR {sofr_point[1]:.2f}% ({sofr_point[0].isoformat()}), 2-year Treasury {two_year_point[1]:.2f}%, 10-year Treasury {ten_year_point[1]:.2f}%, and 30-year Treasury {thirty_year_point[1]:.2f}% ({two_year_point[0].isoformat()}). Sources: FRED DFF, SOFR, DGS2, DGS10, and DGS30.",
        "alt_text": "Bar chart comparing the effective fed funds rate, SOFR, and 2-year, 10-year, and 30-year Treasury yields using FRED data.",
        "local_path": str(sofr_path),
    }
    _write_metadata(sofr_path, sofr_meta)
    assets.append(sofr_meta)
    return assets


def build_current_macro_visual_pack(
    article_title: str,
    output_dir: str | Path = DEFAULT_MEDIA_DIR,
    as_of_date: str | None = None,
    fed_fetch_url: str = FED_RATES_FRED_CSV_URL,
) -> list[dict[str, Any]]:
    lowered = article_title.lower()
    if _looks_like_fed_funds_topic(lowered):
        return render_current_fed_funds_visual_pack(
            article_title=article_title,
            output_dir=output_dir,
            as_of_date=as_of_date,
            fetch_url=fed_fetch_url,
        )
    if _looks_like_oil_topic(lowered):
        return render_current_wti_visual_pack(article_title=article_title, output_dir=output_dir, as_of_date=as_of_date)
    return []
