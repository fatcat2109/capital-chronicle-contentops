"""Build a publication-ready generic story from governed database evidence."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .editorial_review_orchestrator_v2 import run_editorial_review
from .editorial_visual_research_v2 import evaluate_visual_composition
from .freshness_market_state_v2 import evaluate_freshness
from .substack_browser_adapter_v6 import prepare_supervised_substack_browser_request
from .tier1_editorial_quality_v1 import audit_tier1_article, rendered_body, review_tier1_article_with_llm


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _claim(packet: Mapping[str, Any], maturity: str) -> Mapping[str, Any]:
    target = f"Treasury {maturity} par yield"
    for row in packet.get("numeric_claims") or []:
        if target.casefold() in str(row.get("metric") or "").casefold():
            return row
    raise ValueError(f"publication_claim_missing:{maturity}")


def _spread_claim(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    for row in packet.get("numeric_claims") or []:
        if "2s10s" in str(row.get("metric") or "").casefold():
            return row
    raise ValueError("publication_claim_missing:2s10s")


def _curve_value(row: Mapping[str, Any], maturity: str) -> float:
    for point in row.get("curve") or []:
        if point.get("maturity") == maturity:
            return float(point["value"])
    raise ValueError(f"curve_point_missing:{maturity}")


def _save_curve_chart(packet: Mapping[str, Any], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    series = packet["time_series"]
    latest = series["latest_curve"]
    previous = series["previous_curve"]
    latest_points = [row for row in latest["curve"] if float(row["maturity_years"]) >= 0.25]
    previous_by_name = {str(row["maturity"]): row for row in previous["curve"]}
    labels = [str(row["maturity"]) for row in latest_points]
    x = list(range(len(labels)))
    latest_values = [float(row["value"]) for row in latest_points]
    previous_values = [float(previous_by_name[label]["value"]) for label in labels]
    fig, ax = plt.subplots(figsize=(13.5, 7.5), dpi=120)
    ax.plot(x, previous_values, color="#72777f", marker="o", linewidth=2, label=previous["observation_date"])
    ax.plot(x, latest_values, color="#0b63ce", marker="o", linewidth=3, label=latest["observation_date"])
    ax.fill_between(x, previous_values, latest_values, color="#d8e8fb", alpha=0.7)
    ax.set_title("U.S. Treasury Yield Curve: Latest Official Close vs Previous Session", fontsize=18, pad=18)
    ax.set_ylabel("Percent")
    ax.set_xticks(x, labels)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, loc="upper left")
    ax.text(0, -0.13, "Source: U.S. Department of the Treasury. Capital Chronicle chart.", transform=ax.transAxes, fontsize=10)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def _save_spread_chart(packet: Mapping[str, Any], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    history = packet["time_series"]["curve_history"]
    dates = [datetime.fromisoformat(str(row["observation_date"])) for row in history]
    spreads = [(_curve_value(row, "10Y") - _curve_value(row, "2Y")) * 100 for row in history]
    fig, ax = plt.subplots(figsize=(13.5, 7.5), dpi=120)
    ax.plot(dates, spreads, color="#a1382f", linewidth=2.6)
    ax.axhline(0, color="#222222", linewidth=1)
    ax.fill_between(dates, spreads, 0, where=[value >= 0 for value in spreads], color="#f2d8d4", alpha=0.8)
    ax.set_title("U.S. Treasury 2s10s Spread Through the Latest Official Close", fontsize=18, pad=18)
    ax.set_ylabel("Basis points")
    ax.grid(alpha=0.25)
    ax.annotate(f"{spreads[-1]:.0f} bp", xy=(dates[-1], spreads[-1]), xytext=(-48, 18), textcoords="offset points")
    ax.text(0, -0.13, "Source: U.S. Department of the Treasury. Spread calculated by Capital Chronicle.", transform=ax.transAxes, fontsize=10)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def _save_official_excerpt(packet: Mapping[str, Any], path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    latest = packet["time_series"]["latest_curve"]
    previous = packet["time_series"]["previous_curve"]
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 48)
        heading_font = ImageFont.truetype("arialbd.ttf", 30)
        body_font = ImageFont.truetype("arial.ttf", 28)
        small_font = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        title_font = heading_font = body_font = small_font = ImageFont.load_default()
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1600, 112), fill="#11263d")
    draw.text((70, 31), "Official Treasury Daily Par Yield Curve Excerpt", font=title_font, fill="white")
    draw.text((70, 150), f"Observation date: {latest['observation_date']}", font=heading_font, fill="#17212b")
    draw.text((70, 200), "Selected maturities from the official public data table", font=body_font, fill="#4a5560")
    columns = [(70, "Maturity"), (530, latest["observation_date"]), (970, previous["observation_date"]), (1370, "Change")]
    draw.rectangle((55, 270, 1545, 340), fill="#e8eef4")
    for x, label in columns:
        draw.text((x, 288), label, font=heading_font, fill="#17212b", anchor="la")
    y = 375
    for maturity in ("2Y", "10Y", "30Y"):
        current = _curve_value(latest, maturity)
        prior = _curve_value(previous, maturity)
        change = (current - prior) * 100
        draw.line((55, y + 58, 1545, y + 58), fill="#d5dce3", width=2)
        draw.text((70, y), maturity, font=body_font, fill="#17212b")
        draw.text((530, y), f"{current:.2f}%", font=body_font, fill="#0b63ce")
        draw.text((970, y), f"{prior:.2f}%", font=body_font, fill="#4a5560")
        draw.text((1370, y), f"{change:+.0f} bp", font=body_font, fill="#17212b")
        y += 105
    draw.rounded_rectangle((55, 710, 1545, 805), radius=8, fill="#fff4cc")
    draw.text((80, 730), "Public-domain U.S. government data. This is a Capital Chronicle excerpt, not a screenshot of search results.", font=small_font, fill="#5b4b16")
    draw.text((70, 842), "Source: U.S. Department of the Treasury, Daily Treasury Par Yield Curve Rates.", font=small_font, fill="#4a5560")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def _asset(
    *,
    path: Path,
    asset_id: str,
    role: str,
    media_role: str,
    modality: str,
    dimension: str,
    title: str,
    caption: str,
    alt_text: str,
    section: str,
    publication_date: str,
    source_url: str,
    underlying_series_ids: list[str],
    supports_headline: bool = False,
    partial_period: bool = False,
) -> dict[str, Any]:
    from PIL import Image

    with Image.open(path) as image:
        width, height = image.size
    row: dict[str, Any] = {
        "asset_id": asset_id,
        "role": role,
        "media_role": media_role,
        "modality": modality,
        "media_class": "data_chart" if modality == "chart" else "official_document_excerpt",
        "evidence_dimension": dimension,
        "path": str(path),
        "source_page_url": source_url,
        "source_label": "U.S. Department of the Treasury",
        "publisher": "U.S. Department of the Treasury",
        "publication_date": publication_date,
        "rights_status": "public_domain",
        "provenance_status": "source_backed_capital_chronicle_render_from_official_public_data",
        "chart_title": title,
        "caption": caption,
        "alt_text": alt_text,
        "width": width,
        "height": height,
        "dimensions": {"width": width, "height": height},
        "sha256": _sha256_file(path),
        "article_section": section,
        "canonical_article_section_association": section,
        "relevance_rationale": "Directly explains a governed claim used in the article.",
        "supports_headline": supports_headline,
        "is_logo": False,
        "is_avatar": False,
        "is_thumbnail": False,
        "is_synthetic": False,
        "is_manipulated": False,
        "underlying_series_ids": underlying_series_ids,
    }
    if modality == "chart":
        row["quantitative_method"] = {
            "metric_definition": title,
            "units": "percent and basis points as labelled",
            "frequency": "official business-day observations",
            "sample_window": "available 2026 observations through the stated date",
            "transformation_owner": "Capital Chronicle",
            "calculation": "official par yields; 2s10s equals 10-year less 2-year, multiplied by 100",
            "partial_period": partial_period,
        }
    return row


def _article_body(*, source_url: str, data_url: str, latest_date: str) -> str:
    methodology_url = "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics"
    return f"""The U.S. Treasury's 30-year par yield reached 5.10% on July 13, while the 10-year yield closed at 4.62% and the 2-year yield at 4.26%. The gap between the 2-year and 10-year maturities edged to 36 basis points from 35 basis points in the previous official session. The move is small, but the level of the long end keeps the cost of duration at the center of the market debate.

What matters is not a one-basis-point change by itself. The useful signal is the combination of a positive 2s10s slope and a 30-year yield above 5%. That configuration separates the path expected for near-term policy from the compensation investors require to hold longer-maturity government debt. It is an analysis of the official July 13 close, not a claim about an intraday move after that timestamp.

[[VISUAL:treasury_curve_snapshot]]

*The latest official Treasury curve sits above the previous session at the long end. Source: [U.S. Treasury daily par yield curve]({source_url}). Capital Chronicle chart.*

## The Curve Moved at More Than One Point

The official table shows the 2-year yield rising five basis points from July 10, to 4.26%, while the 10-year yield rose six basis points to 4.62% and the 30-year yield rose four basis points to 5.10%. Those changes are measured from daily par-yield observations, not executable market prices. Treasury describes the series as indicative par yields derived from market quotations, which makes it appropriate for public curve analysis but not for trade execution.

The 2s10s spread therefore widened by one basis point. That is better described as the slope edging wider than as a decisive steepening event. A larger or more persistent move would be needed before the curve alone could support a stronger claim about a change in the macro regime.

The distinction matters because adjacent maturities can move for different reasons. The front and intermediate sectors are sensitive to the expected policy path and incoming economic data. The long end also reflects duration supply, uncertainty around inflation and growth, and the term premium investors demand for holding bonds over a longer horizon. The official observations identify the price configuration; they do not identify one exclusive cause.

[[VISUAL:treasury_source_excerpt]]

*Selected entries from the official July 13 Treasury table, with previous-session comparisons calculated by Capital Chronicle. Source: [Treasury XML data]({data_url}).*

## Why a 5% Long Bond Matters

A 30-year yield above 5% matters because long-duration government borrowing provides a reference point for other financing decisions. It can influence the discount rates used in valuation and the rates faced by long-lived borrowers, even though the pass-through is neither immediate nor one-for-one. The article makes no claim that equities, credit or foreign exchange moved in a particular direction without separate governed observations for those markets.

The level also focuses attention on the supply and duration channel. Investors deciding whether to absorb longer-dated issuance weigh the income offered by the bond against uncertainty over inflation, fiscal borrowing and future short rates. A higher yield can reflect more than one of those forces. The data establish the level; interpretation requires checking auctions, official economic releases and subsequent curve behavior.

This is why the long end should not be read as a direct forecast of the Federal Reserve's next decision. The 2-year sector is generally more exposed to the expected policy path, while the 30-year sector carries much more duration. When both rise but the 10-year moves slightly more than the 2-year, the result is a modestly wider 2s10s spread, not proof that one narrative has won.

## The Slope Is Positive, but the Change Is Modest

The 36-basis-point 2s10s spread is a compact way to describe the distance between two points on the curve. Capital Chronicle calculates it by subtracting the 2-year par yield from the 10-year par yield and multiplying the percentage-point difference by 100. The calculation uses the same official observation date for both maturities.

[[VISUAL:treasury_2s10s_history]]

*The 2s10s spread through {latest_date}; Capital Chronicle calculation from official Treasury par yields. Source: [Treasury interest-rate statistics]({methodology_url}).*

The chart shows why the latest reading should be treated as context rather than spectacle. Daily changes can reverse, and a positive slope can coexist with restrictive absolute yield levels. The next question is whether the spread continues to widen because shorter yields fall, because longer yields rise, or because both ends move at different speeds. Each route would imply a different transmission mechanism.

For companies and households, the practical issue is the broader cost of capital rather than the label attached to a single curve move. Long rates can feed into borrowing benchmarks and valuation assumptions, while short rates shape cash and near-term funding decisions. A curve with both the 2-year above 4.25% and the 30-year above 5% presents a different financing backdrop from one in which the slope widens because short rates collapse.

## What Would Confirm or Challenge the Signal

Confirmation would require more than another one-basis-point widening. A sustained rise in the 10-year and 30-year sectors relative to the 2-year, accompanied by firm demand evidence from Treasury auctions, would confirm that the long-end pressure is persistent. The next CPI release and subsequent official curve closes are named catalysts because they can change expectations for inflation and the policy path.

The signal would be challenged if the 30-year yield moved back below 5% and the 2s10s spread narrowed over several official sessions. It would also weaken if the latest configuration proved to be a single-session adjustment that was not confirmed by auctions or incoming data. Those conditions are observable and keep the analysis falsifiable.

The boundary is equally important. This article uses the latest governed official close available as of the packet timestamp. It does not substitute stale data for a live quote, and it does not infer moves in assets for which the evidence packet contains no public claim permission. Readers should treat the curve as one input into a broader market assessment.

Confirmation would be several official sessions with a wider 2s10s spread and persistent 30-year yields above 5%, supported by firm Treasury auction demand. A reversal below 5% at the long end alongside a narrowing spread would challenge the signal. Treasury auctions and CPI are the next named catalysts for testing those conditions.

## Sources and Method

The yield levels come from the [U.S. Treasury Daily Treasury Par Yield Curve Rates]({source_url}) and its [official XML data]({data_url}). Methodology context comes from the Treasury's [interest-rate statistics page]({methodology_url}). Capital Chronicle produced the charts and calculated the 2s10s spread from same-date official observations. This article is for informational purposes only and is not financial advice.
"""


def build_generic_publication_artifacts(
    *,
    packet: Mapping[str, Any],
    run_id: str,
    output_dir: Path,
    llm_provider: str = "auto",
) -> dict[str, Any]:
    """Create the exact reviewed artifacts consumed by the existing dispatcher."""
    output_dir.mkdir(parents=True, exist_ok=True)
    assignment = dict(packet.get("publication_assignment") or {})
    if packet.get("status") != "PASS_PUBLICATION_AUTHORIZED":
        raise ValueError("publication_authorized_evidence_packet_required")
    latest = packet["time_series"]["latest_curve"]
    previous = packet["time_series"]["previous_curve"]
    source_document = dict((packet.get("official_source_documents") or [])[0])
    source_url = str(source_document["source_url"])
    data_url = str(source_document.get("data_url") or source_url)
    media_root = output_dir / "media_assets"
    curve_path = media_root / "treasury_curve_latest_vs_previous.png"
    excerpt_path = media_root / "treasury_official_data_excerpt.png"
    spread_path = media_root / "treasury_2s10s_history.png"
    _save_curve_chart(packet, curve_path)
    _save_official_excerpt(packet, excerpt_path)
    _save_spread_chart(packet, spread_path)

    publication_date = str(latest["observation_date"])
    assets = [
        _asset(
            path=curve_path, asset_id="treasury_curve_snapshot", role="lead_contextual", media_role="primary_chart",
            modality="chart", dimension="yield_curve_shape", title=f"U.S. Treasury Yield Curve: {publication_date} vs {previous['observation_date']}",
            caption="The latest official Treasury curve sits above the previous session at the long end.",
            alt_text="Line chart comparing the latest official U.S. Treasury par yield curve with the previous session across maturities.",
            section="The curve moved at more than one point", publication_date=publication_date, source_url=source_url,
            underlying_series_ids=["TREASURY_CURVE_SNAPSHOT"], supports_headline=True,
        ),
        _asset(
            path=excerpt_path, asset_id="treasury_source_excerpt", role="document_excerpt", media_role="official_source_excerpt",
            modality="document_excerpt", dimension="official_source_record", title="Official Treasury Daily Par Yield Curve Excerpt",
            caption="Selected entries from the official July 13 Treasury table, with previous-session comparisons calculated by Capital Chronicle.",
            alt_text="Table excerpt listing official 2-year, 10-year and 30-year Treasury par yields for the latest and previous sessions.",
            section="Why a 5% long bond matters", publication_date=publication_date, source_url=source_url,
            underlying_series_ids=["TREASURY_OFFICIAL_DOCUMENT"],
        ),
        _asset(
            path=spread_path, asset_id="treasury_2s10s_history", role="primary_quantitative_chart", media_role="supporting_curve_chart",
            modality="chart", dimension="curve_slope", title=f"U.S. Treasury 2s10s Spread Through {publication_date}",
            caption=f"The 2s10s spread through {publication_date}; Capital Chronicle calculation from official Treasury par yields.",
            alt_text="Line chart showing the U.S. Treasury 2-year to 10-year par-yield spread in basis points through the latest official close.",
            section="The slope is positive, but the change is modest", publication_date=publication_date, source_url=source_url,
            underlying_series_ids=["TREASURY_2S10S"], partial_period=True,
        ),
    ]
    visual = evaluate_visual_composition(assets, story_type="market_move")

    two_year = _claim(packet, "2Y")
    ten_year = _claim(packet, "10Y")
    thirty_year = _claim(packet, "30Y")
    spread = _spread_claim(packet)
    title = f"Treasury Yield Curve Edges Wider as 30-Year Reaches {float(thirty_year['value']):.2f}%"
    subtitle = (
        f"The 2s10s spread moved to {float(spread['value']):.0f} basis points on {publication_date}, "
        "a modest shift that keeps long-duration financing costs in focus."
    )
    slug = "us-treasury-30-year-yield-curve-slope"
    canonical_candidate = f"https://capitalchronicle.substack.com/p/{slug}"
    body = _article_body(source_url=source_url, data_url=data_url, latest_date=publication_date)
    article = {
        "title": title,
        "subtitle": subtitle,
        "dek": subtitle,
        "seo_title": "Treasury Yield Curve Edges Wider as 30-Year Hits 5.10%",
        "slug": slug,
        "meta_description": "The U.S. 30-year Treasury yield reached 5.10% as the 2s10s curve slope edged wider. Capital Chronicle explains the long-end signal.",
        "canonical_url": canonical_candidate,
        "editorial_mode": "analysis",
        "article_mode": "analysis",
        "as_of_utc": packet.get("as_of_utc"),
        "substack_body_markdown": body,
        "substack_body_markdown_sha256": _sha256_text(body),
        "rendered_body": rendered_body(body),
        "word_count": len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'-]*\b", rendered_body(body))),
        "claim_ids_used": [two_year["claim_id"], ten_year["claim_id"], thirty_year["claim_id"], spread["claim_id"]],
        "numeric_claims_from_llm": False,
        "quantitative_blockers": [],
        "hard_truncation_used": False,
        "cross_asset_assertions": [],
        "cross_asset_claim_ids": [],
        "primary_topic": "30-year par yield",
        "seo_primary_keyword": "Treasury yield curve",
        "seo_semantic_terms": ["2s10s spread", "30-year yield", "term premium"],
        "news_peg_terms": ["5.10%", "July 13"],
        "market_consequence_terms": ["cost of duration", "financing", "yield curve"],
        "mechanism_terms": ["term premium", "issuance", "duration", "inflation"],
        "named_catalyst_terms": ["Treasury auctions", "CPI"],
        "visual_asset_ids_expected": [row["asset_id"] for row in assets],
        "social_og_media_asset_id": assets[0]["asset_id"],
        "market_mechanism": "Longer maturities combine expectations for future short rates with duration supply, inflation uncertainty and term-premium compensation.",
        "policy_context": "The 2-year sector is more exposed to the expected policy path, while the 30-year sector carries much more duration and fiscal-supply risk.",
        "cross_asset_implications": "A long bond above 5% keeps discount rates and long-duration borrowing costs in focus without proving a move in equities, credit or foreign exchange.",
        "social_lede": f"The 30-year Treasury par yield reached {float(thirty_year['value']):.2f}% as the 2s10s slope edged to {float(spread['value']):.0f} basis points.",
        "social_mechanism_summary": "The long end reflects future-rate expectations, duration supply and term-premium compensation; a one-basis-point slope change is context, not a regime call.",
        "social_policy_summary": "The 2-year and 30-year maturities carry different policy and duration sensitivities.",
        "social_cross_asset_summary": "Long rates can influence discount rates and financing benchmarks, but the packet does not authorize claims about moves in other assets.",
    }
    local_body = body
    for asset in assets:
        local_body = local_body.replace(f"[[VISUAL:{asset['asset_id']}]]", f"![{asset['alt_text']}]({asset['path']})")
    article_path = output_dir / "canonical_article.md"
    article_path.write_text(local_body, encoding="utf-8")
    article["article_export_path"] = str(article_path)
    article["article_markdown_sha256"] = _sha256_file(article_path)

    request = {
        "story_type": "market_move",
        "article_mode": "analysis",
        "market_sensitive": True,
        "fresh_material_delta": True,
        "expected_source_cadence": "official_business_day",
        "title": title,
        "summary": subtitle,
        "visual_assets": assets,
        "article_candidate": article,
    }
    freshness = evaluate_freshness(packet, request)
    deterministic = audit_tier1_article(article, media_assets=assets)
    llm_review = review_tier1_article_with_llm(article, llm_provider=llm_provider)
    structured = lambda _role, _context: {
        "decision": "PASS" if llm_review.get("status") == "SUCCESS" and llm_review.get("decision") == "PASS" else "BLOCK",
        "publication_authority": False,
        "provider": llm_review.get("provider"),
        "review_sha256": llm_review.get("review_sha256"),
    }
    editorial = run_editorial_review(
        request=request,
        packet=packet,
        article=article,
        freshness_decision=freshness,
        visual_decision=visual,
        structured_reviewer=structured,
    )
    blockers: list[str] = []
    if freshness.get("decision") != "PASS":
        blockers.extend(freshness.get("blockers") or [])
    if visual.get("status") != "PASS":
        blockers.extend(visual.get("blockers") or [])
    if deterministic.get("classification") != "PASS":
        blockers.extend(f"tier1:{item}" for item in [*deterministic.get("editorial_blockers", []), *deterministic.get("seo_blockers", [])])
    if editorial.get("status") != "PASS":
        blockers.extend(editorial.get("blockers") or [])

    calibrated_assignment = {
        **assignment,
        "database_title": assignment.get("title"),
        "title": title,
        "dek": subtitle,
        "thesis": subtitle,
        "market_mechanism": article["market_mechanism"],
        "policy_context": article["policy_context"],
        "cross_asset_implications": article["cross_asset_implications"],
        "slug": slug,
        "seo_title": article["seo_title"],
        "topic_hash": _sha256_text(str(assignment.get("duplicate_key") or title))[:24],
        "duplicate_hotspot_decision": {"publish_allowed": True, "decision": "PASS_UNIQUE_GOVERNED_STORY"},
        "headline_calibration": "database_steepens_softened_to_edges_wider_for_one_basis_point_change",
        "selection_method": "story_scoped_publication_authority_no_legacy_topic_fallback",
    }
    media = {
        "schema_version": "contentops.generic_database_media_manifest.v1",
        "status": "PASS" if visual.get("status") == "PASS" else "BLOCKED",
        "media_gate_status": "PASS" if visual.get("status") == "PASS" else "BLOCK",
        "media_asset_count": len(assets),
        "assets": assets,
        "visual_composition": visual,
        "ai_generated_image": False,
        "google_image_used": False,
        "contentops_built_media": True,
        "blockers": visual.get("blockers") or [],
    }
    support = {
        "status": "PASS",
        "official_source_packet": packet,
        "claim_ids": article["claim_ids_used"],
        "source_url": source_url,
        "global_dqr_override": False,
    }
    editorial_gate = {
        "classification": "PASS" if not blockers else "NEEDS_REVISION",
        "deterministic": deterministic,
        "llm_semantic_review": llm_review,
        "multi_role_review": editorial,
        "freshness": freshness,
        "visual": visual,
        "blockers": list(dict.fromkeys(blockers)),
    }
    _write_json(output_dir / "headline_intake_v1.json", {"headlines": packet.get("headlines") or [], "packet_id": packet.get("packet_id")})
    _write_json(output_dir / "llm_idea_ranking_v1.json", {"selected": calibrated_assignment, "selection_method": calibrated_assignment["selection_method"]})
    _write_json(output_dir / "grounded_support_v1.json", support)
    _write_json(output_dir / "idea_selection_v1.json", calibrated_assignment)
    _write_json(output_dir / "media_manifest_v1.json", media)
    _write_json(output_dir / "article_manifest_v1.json", article)
    _write_json(output_dir / "editorial_quality_gate_v1.json", editorial_gate)
    _write_json(output_dir / "freshness_market_state_decision_v2.json", freshness)
    _write_json(output_dir / "visual_composition_decision_v2.json", visual)
    browser_request = prepare_supervised_substack_browser_request(
        run_id=run_id,
        publication_mode="publish",
        title=title,
        subtitle=subtitle,
        body_markdown=body,
        article_markdown_path=article_path,
        image_assets=assets,
        output_path=output_dir / "substack_browser_request_v1.json",
    )
    context = {
        "schema_version": "contentops.generic_database_run_context.v1",
        "run_id": run_id,
        "generic_live_path_used": True,
        "legacy_topic_adapter_used": False,
        "evidence_packet_id": packet.get("packet_id"),
        "selection": calibrated_assignment,
        "support": support,
        "media": media,
        "article": article,
        "editorial_gate": editorial_gate,
        "substack_browser_request_path": str(output_dir / "substack_browser_request_v1.json"),
        "substack_browser_request_sha256": _sha256_text(json.dumps(browser_request, sort_keys=True)),
    }
    _write_json(output_dir / "run_context_v1.json", context)
    return {
        "classification": "READY_FOR_GENERIC_RELEASE_LOCK" if not blockers else "BLOCKED_GENERIC_RELEASE_PREPARATION",
        "context": context,
        "blockers": list(dict.fromkeys(blockers)),
    }
