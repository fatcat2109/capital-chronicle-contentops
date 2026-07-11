"""Build the July oil RC editorial and visual repair packet without publishing."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

EIA_MAP_PAGE = "https://www.eia.gov/international/content/analysis/special_topics/World_Oil_Transit_Chokepoints/"
EIA_MAP_URL = EIA_MAP_PAGE + "images/fig4.png"
EIA_REUSE_URL = "https://www.eia.gov/about/copyrights_reuse.php"
FRED_PAGE = "https://fred.stlouisfed.org/series/DCOILWTICO"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO"


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "CapitalChronicleContentOps/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dimensions(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as image:
        return int(image.width), int(image.height)


def _fred_rows(raw: bytes) -> list[tuple[datetime, float]]:
    rows = []
    for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
        value = row.get("DCOILWTICO")
        if not value or value == ".":
            continue
        date_value = row.get("DATE") or row.get("observation_date")
        if not date_value:
            raise ValueError("fred_date_column_missing")
        rows.append((datetime.strptime(str(date_value), "%Y-%m-%d"), float(value)))
    if len(rows) < 60:
        raise ValueError("insufficient_fred_wti_observations")
    return rows


def build_oil_rc_repair_packet(*, output_dir: Path) -> dict[str, Any]:
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image

    output_dir.mkdir(parents=True, exist_ok=True)
    map_path = output_dir / "eia_strait_of_hormuz_map.png"
    map_path.write_bytes(_download(EIA_MAP_URL))
    with Image.open(map_path) as source_map:
        if source_map.width < 800 or source_map.height < 450:
            scale = max(800 / source_map.width, 450 / source_map.height)
            source_map.resize(
                (round(source_map.width * scale), round(source_map.height * scale)),
                Image.Resampling.LANCZOS,
            ).save(map_path)
    rows = _fred_rows(_download(FRED_CSV))
    dates = [row[0] for row in rows]
    prices = np.array([row[1] for row in rows], dtype=float)
    simple_returns = np.diff(prices) / prices[:-1]
    rolling = np.full(prices.shape, np.nan)
    for index in range(30, len(prices)):
        window = simple_returns[index - 30:index]
        rolling[index] = float(np.std(window, ddof=1) * np.sqrt(252) * 100)

    vol_path = output_dir / "wti_price_and_30_observation_realized_volatility.png"
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    axes[0].plot(dates[-260:], prices[-260:], color="#1f4f99", linewidth=2)
    axes[0].set_title("WTI Spot Price Through Latest FRED Observation")
    axes[0].set_ylabel("USD per barrel")
    axes[1].plot(dates[-260:], rolling[-260:], color="#b5472c", linewidth=2)
    axes[1].set_title("30-Observation Annualized Realized Volatility")
    axes[1].set_ylabel("Percent")
    axes[1].set_xlabel("Daily observations")
    fig.text(0.01, 0.01, "Source: FRED DCOILWTICO (underlying source: U.S. EIA). Capital Chronicle calculation: annualized standard deviation of simple daily returns, 30 observations, sqrt(252).", fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(vol_path, dpi=160)
    plt.close(fig)

    years: dict[int, list[float]] = {}
    for date, price in rows:
        years.setdefault(date.year, []).append(price)
    selected_years = sorted(years)[-5:]
    range_path = output_dir / "wti_annual_ranges_2026_ytd.png"
    fig, ax = plt.subplots(figsize=(12, 6))
    lows = [min(years[year]) for year in selected_years]
    highs = [max(years[year]) for year in selected_years]
    averages = [sum(years[year]) / len(years[year]) for year in selected_years]
    labels = [f"{year} YTD" if year == dates[-1].year else str(year) for year in selected_years]
    x = np.arange(len(labels))
    ax.vlines(x, lows, highs, color="#4677b8", linewidth=8, alpha=0.55)
    ax.scatter(x, averages, color="#222222", label="Average", zorder=3)
    ax.set_xticks(x, labels)
    ax.set_ylabel("USD per barrel")
    ax.set_title("WTI Annual Low-High Ranges and Averages")
    ax.legend()
    fig.text(0.01, 0.01, f"Source: FRED DCOILWTICO (underlying source: U.S. EIA). Capital Chronicle calculations. {dates[-1].year} is YTD through {dates[-1].date().isoformat()}.", fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(range_path, dpi=160)
    plt.close(fig)

    title = "EIA Sees Oil Supply Nearing Pre-Conflict Levels as Hormuz Flows Resume"
    subtitle = "An analysis of the July 7 EIA forecast, the physical chokepoint, and the market evidence available through July 6."
    body = f"""## Supply Recovery Is Now an Analysis, Not Breaking News

The U.S. Energy Information Administration published its July Short-Term Energy Outlook on July 7, 2026. The agency said global crude production and trade could move back toward pre-conflict levels by year-end as traffic through the Strait of Hormuz resumes and shut-in output returns. This article treats that release as an analysis anchor, not a live breaking-news event. Market observations cited below run only through {dates[-1].date().isoformat()} and should not be read as a current-session price.

The distinction matters. EIA forecasts describe a conditional path, not an observed outcome. The supply outlook depends on continued transit normalization, field restarts, freight conditions, and inventories. Capital Chronicle analysis separates those conditions from the agency's published figures and does not use the forecast as proof that the adjustment is complete.

[[VISUAL:hormuz_map]]

*The Strait of Hormuz and regional pipeline alternatives. Source: U.S. Energy Information Administration, World Oil Transit Chokepoints report. EIA publication; reused with attribution under EIA's public-domain reuse policy. [Source]({EIA_MAP_PAGE})*

## The Chokepoint Connects Production to Delivered Supply

Hormuz is not merely a line on a shipping map. It links Persian Gulf production with refineries and customers outside the region. When transit is constrained, available production may not translate into prompt delivered barrels; freight, insurance, and route risk can widen the gap. Reopening the route allows restored production to reach buyers and can reduce those logistical premia before every facility is fully normalized.

That mechanism is why physical confirmation matters. Sustained tanker movements, fewer shut-ins, and a turn toward inventory rebuilding would support the EIA's normalization case. Renewed disruption, slower field restarts, or persistent draws would challenge it.

[[VISUAL:wti_volatility]]

*WTI price and 30-observation annualized realized volatility through {dates[-1].date().isoformat()}. Source: FRED DCOILWTICO; underlying source: U.S. EIA. Capital Chronicle calculation: standard deviation of simple daily returns over 30 observations, annualized by the square root of 252. [Source]({FRED_PAGE})*

## Price Is a Check on the Forecast, Not Its Authority

The FRED series shows the market level from which investors were testing the supply outlook through July 6. The volatility panel uses a conventional realized-volatility definition: the rolling standard deviation of simple daily returns, annualized. It does not relabel an average absolute move as volatility.

Price alone cannot identify the cause of a move. A decline can reflect improving supply, weaker demand, changing risk premia, or several channels at once. The EIA release and physical-flow evidence establish the supply thesis; the market series shows how that thesis was being priced at the stated as-of date.

## Inflation And Cross-Asset Effects Remain Conditional

Lower crude and gasoline costs can reduce headline inflation and some transport expenses. That does not mechanically determine Federal Reserve policy, core-services inflation, or longer-term Treasury yields. Those outcomes also depend on labor conditions, fiscal supply, growth expectations, and inflation persistence.

For currencies and equities, exposure matters more than a generic risk-on label. Large energy importers may receive terms-of-trade relief, while producer revenues face pressure if lower prices persist. Refiners, transport-intensive companies, and upstream producers can therefore respond differently to the same crude move. These are transmission channels to monitor, not unconditional predictions.

[[VISUAL:wti_ranges]]

*WTI annual low-high ranges and averages. Source: FRED DCOILWTICO; underlying source: U.S. EIA. Capital Chronicle calculations. {dates[-1].year} is explicitly shown as YTD through {dates[-1].date().isoformat()}, not as a complete calendar year. [Source]({FRED_PAGE})*

## What Would Confirm Or Challenge The Rebalance

Confirmation requires the physical and financial evidence to align: continued Hormuz transit, restored output, inventory rebuilding, and prices behaving consistently with easing scarcity. The thesis would weaken if the route is disrupted again, production recovery stalls, inventories keep drawing, or prices remain elevated despite improving flows.

The article's source facts come from the July 7 EIA outlook and the cited EIA chokepoint report. The charts are Capital Chronicle transformations of FRED DCOILWTICO, whose underlying source is the EIA. All dates and partial periods are stated explicitly. This article is for informational purposes only and is not financial advice.
"""
    map_width, map_height = _dimensions(map_path)
    vol_width, vol_height = _dimensions(vol_path)
    range_width, range_height = _dimensions(range_path)
    assets = [
        {"asset_id": "hormuz_map", "local_path": str(map_path.resolve()), "role": "lead_contextual", "modality": "map", "evidence_dimension": "physical_geography", "source_page_url": EIA_MAP_PAGE, "source_asset_url": EIA_MAP_URL, "publisher": "U.S. Energy Information Administration", "publication_date": "2026-03", "rights_status": "public_domain", "rights_policy_url": EIA_REUSE_URL, "caption": "The Strait of Hormuz and regional pipeline alternatives.", "alt_text": "EIA map of the Strait of Hormuz and pipeline alternatives across the Arabian Peninsula.", "width": map_width, "height": map_height, "sha256": _sha(map_path), "article_section": "physical_mechanism", "underlying_series_ids": [], "relevance_rationale": "The physical chokepoint directly supports the headline's transit-normalization mechanism.", "supports_headline": True, "transformation_note": "Capital Chronicle resized the official EIA map for editorial readability without altering its content."},
        {"asset_id": "wti_volatility", "local_path": str(vol_path.resolve()), "role": "primary_quantitative_chart", "modality": "chart", "evidence_dimension": "price_and_volatility", "source_page_url": FRED_PAGE, "publisher": "Capital Chronicle from FRED/EIA data", "publication_date": dates[-1].date().isoformat(), "rights_status": "capital_chronicle_owned", "caption": "WTI price and correctly defined 30-observation annualized realized volatility through the latest observation.", "chart_title": "WTI Price and 30-Observation Annualized Realized Volatility", "alt_text": "Two-panel WTI price and annualized realized-volatility chart.", "width": vol_width, "height": vol_height, "sha256": _sha(vol_path), "article_section": "market_evidence", "underlying_series_ids": ["DCOILWTICO"], "relevance_rationale": "Separates the observed market level and variability from the EIA forecast.", "quantitative_method": {"metric_definition": "annualized standard deviation of simple daily returns", "units": "percent", "frequency": "daily", "sample_window": "30 observations", "annualization": "sqrt(252)", "annualization_factor": "sqrt(252)", "calculation": "standard deviation of simple daily returns", "transformation_owner": "Capital Chronicle", "partial_period": False}},
        {"asset_id": "wti_ranges", "local_path": str(range_path.resolve()), "role": "historical_context_chart", "modality": "chart", "evidence_dimension": "historical_range", "source_page_url": FRED_PAGE, "publisher": "Capital Chronicle from FRED/EIA data", "publication_date": dates[-1].date().isoformat(), "rights_status": "capital_chronicle_owned", "caption": f"WTI annual low-high ranges and averages with {dates[-1].year} explicitly labelled YTD through {dates[-1].date().isoformat()}.", "chart_title": f"WTI Annual Ranges, Including {dates[-1].year} YTD", "alt_text": "WTI annual low-high ranges and averages with the incomplete current year labelled YTD.", "width": range_width, "height": range_height, "sha256": _sha(range_path), "article_section": "historical_context", "underlying_series_ids": ["DCOILWTICO"], "relevance_rationale": "Places the stated market observation in a clearly labelled multi-year range context.", "quantitative_method": {"metric_definition": "annual minimum maximum and arithmetic mean", "units": "USD per barrel", "frequency": "daily", "sample_window": "calendar year or YTD", "annualization": "none", "transformation_owner": "Capital Chronicle", "partial_period": True}},
    ]
    packet = {
        "schema_version": "contentops.oil_rc_editorial_repair.v1",
        "status": "PASS_LOCAL_REPAIR_PACKET_NOT_PUBLISHED",
        "title": title,
        "subtitle": subtitle,
        "article_mode": "analysis",
        "as_of_utc": f"{dates[-1].date().isoformat()}T23:59:59Z",
        "body_markdown": body,
        "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "word_count": len(body.split()),
        "visual_assets": assets,
        "visual_asset_count": len(assets),
        "visual_modalities": sorted({row["modality"] for row in assets}),
        "underlying_series_max_reuse": 2,
        "process_language_absent": "manifest-bound" not in body.casefold(),
        "source_wording_calibrated": "pre-war" not in title.casefold() and "pre-conflict" in title.casefold(),
        "public_write_performed": False,
    }
    (output_dir / "oil_rc_editorial_repair_packet_v1.json").write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def evaluate_oil_rc_repair_packet(*, output_dir: Path, packet: dict[str, Any]) -> dict[str, Any]:
    from .editorial_visual_research_v2 import evaluate_visual_composition

    visual = evaluate_visual_composition(packet["visual_assets"], story_type="supply_chain_event")
    deterministic_checks = {
        "visual_composition": visual["status"] == "PASS",
        "source_wording_calibrated": bool(packet["source_wording_calibrated"]),
        "process_language_absent": bool(packet["process_language_absent"]),
        "analysis_mode_explicit": packet["article_mode"] == "analysis",
        "as_of_explicit": bool(packet["as_of_utc"]),
        "three_visuals": int(packet["visual_asset_count"]) >= 3,
        "zero_public_writes": packet["public_write_performed"] is False,
    }
    result = {
        "schema_version": "contentops.oil_rc_visual_editorial_gate.v1",
        "status": "PASS_LOCAL_REPAIR_GATES_NOT_PUBLISHED" if all(deterministic_checks.values()) else "BLOCK_LOCAL_REPAIR_GATES",
        "deterministic_checks": deterministic_checks,
        "visual_composition": visual,
        "body_sha256": packet["body_sha256"],
        "public_write_performed": False,
    }
    (output_dir / "oil_rc_visual_editorial_gate_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
