"""Material-plan and validation contract for the Treasury visual repair.

The frozen story and audio remain owned by the preceding vertical slice.  This
module describes only viewer-facing visual material and deterministic truth
checks for the repaired short and longform.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


TASK_ID = "TASK_CONTENTOPS_V2_TREASURY_OWNER_VISUAL_INTEGRITY_AND_ASSET_DIVERSITY_REPAIR_V1"
JOB_ID = "CFTC_TREASURY_POSITIONING_20260811_SHORT_LONGFORM_V1"
RESULT = "PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW"
FROZEN_AUDIO_SHA256 = {
    "short": "1f3ddccb3a124affbdf36875513195757208d73ca807a1f5186a63779cab70e2",
    "longform": "68098235078d1553a2948b683d3a64eca281c37dcba9dd68575159626de99d84",
}
CHATTERBOX_DIAGNOSTIC_SHA256 = "5f9ef050fa5d931ba301fdbf971e9c87333c771acd2c12346259b18061affd69"


def validate_creative_source_sandbox(source: Path, project_root: Path) -> dict[str, Any]:
    """Validate the task-owned Remotion source and its import boundary."""
    resolved = source.resolve()
    root = project_root.resolve()
    errors: list[str] = []
    if root not in resolved.parents:
        errors.append("creative_source_outside_project_root")
    if not source.is_file():
        return {"status": "FAIL", "errors": errors + ["creative_source_missing"], "source": str(resolved)}
    text = source.read_text(encoding="utf-8")
    forbidden = {
        "network": r"\b(fetch|XMLHttpRequest|WebSocket)\b",
        "environment": r"process\.env",
        "filesystem": r"\b(node:fs|child_process|require\(['\"]fs['\"]\))\b",
        "browser": r"\b(playwright|puppeteer|cdp)\b",
        "remote_import": r"from\s+['\"]https?://",
        "fixed_scene_renderer": r"\bSceneRenderer\b",
    }
    for label, pattern in forbidden.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(f"forbidden_source:{label}")
    if "CODEX_VIEWER_FACING_AUTHORSHIP" not in text:
        errors.append("missing_viewer_facing_authorship_marker")
    imports = re.findall(r"from\s+['\"]([^'\"]+)['\"]", text)
    allowed_imports = {"react", "remotion"}
    for module in imports:
        if module not in allowed_imports:
            errors.append(f"unapproved_import:{module}")
    dependencies = [source, root / "src" / "root.tsx"]
    hashes: dict[str, str] = {}
    for path in dependencies:
        if not path.is_file():
            errors.append(f"missing_creative_dependency:{path.name}")
            continue
        hashes[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "source": str(resolved),
        "imports": imports,
        "allowed_imports": sorted(allowed_imports),
        "dependency_hashes": hashes,
    }


STATIC_FULL_CONTEXT = "STATIC_FULL_CONTEXT"
PHOTO_EDITORIAL_REFRAME = "PHOTO_EDITORIAL_REFRAME"
NATIVE_GOVERNED_MOTION = "NATIVE_GOVERNED_MOTION"
SEMANTIC_COMPONENT_MOTION = "SEMANTIC_COMPONENT_MOTION"
STATIC_EDITORIAL_FRAME = "STATIC_EDITORIAL_FRAME"
STATIC_OBJECT_CLASSES = {"primary_chart", "primary_source_figure", "numeric_table", "primary_data"}


def beat(layout: str, family: str, purpose: str, *, asset: str | None = None,
         label: str = "", detail: str = "", focus: str = "center",
         evidence_object_class: str | None = None, motion_policy: str | None = None,
         source_material_family: str | None = None, presentation_grammar: str | None = None,
         readability_hold: bool = False) -> dict[str, Any]:
    object_class = evidence_object_class or (
        "documentary_photo" if family == "documentary_photo" else
        "primary_source_figure" if family == "primary_source_figure" else
        "primary_document" if family == "primary_document" else
        "native_cc_data_visual" if family == "native_data" else
        "diagram" if family in {"mechanism_diagram", "transmission_diagram", "monitoring_framework"} else
        "editorial_typography"
    )
    policy = motion_policy or (
        PHOTO_EDITORIAL_REFRAME if object_class == "documentary_photo" else
        STATIC_FULL_CONTEXT if object_class in STATIC_OBJECT_CLASSES | {"primary_document"} else
        NATIVE_GOVERNED_MOTION if object_class == "native_cc_data_visual" else
        SEMANTIC_COMPONENT_MOTION if object_class == "diagram" else STATIC_EDITORIAL_FRAME
    )
    return {
        "layout": layout,
        "family": family,
        "source_material_family": source_material_family or family,
        "presentation_grammar": presentation_grammar or layout,
        "purpose": purpose,
        "asset": asset,
        "label": label,
        "detail": detail,
        "focus": focus,
        "evidence_object_class": object_class,
        "motion_policy": policy,
        "readability_hold": readability_hold,
    }


PHOTO_CFTC = "cftc-entrance-2026.jpg"
PHOTO_TREASURY = "treasury-building-highsmith.jpg"
PHOTO_FED = "fed-eccles-building-1937.jpg"
ROWS = "cftc-exact-rows-2026-08-11.png"
SCHEDULE = "cftc-release-schedule-derivative.png"
FED_NOTE = "fed-note-cover-derivative.png"
TREASURY_REMARKS = "treasury-remarks-derivative.png"
FED_FIG1 = "fed-2026-fig1-exposures-repo-turnover.png"
FED_FIG3 = "fed-2026-fig3-uses.png"
FED_FIG4 = "fed-2026-fig4-basis-trade.png"
FED_FIG2 = "fed-2026-fig2-holdings-share.png"
FED_FIG5 = "fed-2026-fig5-swap-spread.png"
FED_2024_FIG2 = "fed-2024-basis-fig2-leveraged-short-tenors.png"
FED_2024_FIG5 = "fed-2024-basis-fig5-net-repo.png"
FED_2024_FIG6 = "fed-2024-basis-fig6-proxy-comparison.png"
FED_2023_FIG4 = "fed-2023-fig4-treasury-tenor-positioning.png"
FED_FSR = "fed-fsr-2026-page-38.png"
FED_FSR_DEALER = "fed-fsr-2026-page-37.png"
FED_FSR_LEVERAGE = "fed-fsr-2026-page-39.png"
CFTC_NOTES_1 = "cftc-tff-explanatory-notes-page-1.png"
CFTC_NOTES_4 = "cftc-tff-explanatory-notes-page-4.png"
FED_BASIS_NOTE = "fed-basis-note-2024-derivative.png"
FED_POSITIONING_NOTE = "fed-positioning-note-2023-derivative.png"


ASSET_SOURCE_FAMILY = {
    PHOTO_CFTC: "cftc_institutional_context",
    PHOTO_TREASURY: "treasury_institutional_context",
    PHOTO_FED: "fed_institutional_context",
    ROWS: "cftc_governed_snapshot",
    SCHEDULE: "cftc_official_document",
    CFTC_NOTES_1: "cftc_official_document",
    CFTC_NOTES_4: "cftc_official_document",
    FED_NOTE: "fed_2026_exposure_research",
    TREASURY_REMARKS: "treasury_official_document",
    FED_FIG1: "fed_2026_exposure_research",
    FED_FIG2: "fed_2026_exposure_research",
    FED_FIG3: "fed_2026_exposure_research",
    FED_FIG4: "fed_2026_exposure_research",
    FED_FIG5: "fed_2026_exposure_research",
    FED_2024_FIG2: "fed_2024_basis_proxy_research",
    FED_2024_FIG5: "fed_2024_basis_proxy_research",
    FED_2024_FIG6: "fed_2024_basis_proxy_research",
    FED_2023_FIG4: "fed_2023_treasury_positioning_research",
    FED_BASIS_NOTE: "fed_2024_basis_proxy_research",
    FED_POSITIONING_NOTE: "fed_2023_treasury_positioning_research",
    FED_FSR: "fed_2026_financial_stability_report",
    FED_FSR_DEALER: "fed_2026_financial_stability_report",
    FED_FSR_LEVERAGE: "fed_2026_financial_stability_report",
}


def _photo(asset: str, label: str, detail: str, purpose: str = "institutional_context", focus: str = "center") -> dict[str, Any]:
    return beat("photo_full", "documentary_photo", purpose, asset=asset, label=label, detail=detail, focus=focus,
                evidence_object_class="documentary_photo", motion_policy=PHOTO_EDITORIAL_REFRAME,
                source_material_family=ASSET_SOURCE_FAMILY[asset])


def _doc(asset: str, label: str, detail: str, purpose: str = "source_evidence", crop: bool = False, focus: str = "center") -> dict[str, Any]:
    object_class = "primary_data" if asset == ROWS else "primary_document"
    return beat("document_full", "primary_document", purpose, asset=asset, label=label, detail=detail, focus=focus,
                evidence_object_class=object_class, motion_policy=STATIC_FULL_CONTEXT,
                source_material_family=ASSET_SOURCE_FAMILY[asset], readability_hold=True)


def _figure(asset: str, label: str, detail: str, purpose: str = "source_figure", crop: bool = False, focus: str = "center") -> dict[str, Any]:
    return beat("figure_full", "primary_source_figure", purpose, asset=asset, label=label, detail=detail, focus=focus,
                evidence_object_class="primary_source_figure", motion_policy=STATIC_FULL_CONTEXT,
                source_material_family=ASSET_SOURCE_FAMILY[asset], readability_hold=True)


def _native(layout: str, family: str, label: str, detail: str, purpose: str) -> dict[str, Any]:
    is_data = family == "native_data"
    is_diagram = family in {"mechanism_diagram", "transmission_diagram", "monitoring_framework"}
    return beat(layout, family, purpose, label=label, detail=detail,
                evidence_object_class="native_cc_data_visual" if is_data else "diagram" if is_diagram else "editorial_typography",
                motion_policy=NATIVE_GOVERNED_MOTION if is_data else SEMANTIC_COMPONENT_MOTION if is_diagram else STATIC_EDITORIAL_FRAME,
                source_material_family="governed_cftc_values" if is_data else "capital_chronicle_analysis")


POSITION = lambda label, detail: _native("position_chart", "native_data", label, detail, "cftc_position_comparison")
MATURITY = lambda label, detail: _native("maturity_data", "native_data", label, detail, "cftc_maturity_detail")
WEEKLY = lambda label, detail: _native("weekly_delta", "native_data", label, detail, "weekly_change")
MECHANISM = lambda label, detail: _native("mechanism", "mechanism_diagram", label, detail, "physical_market_mechanics")
BOUNDARY = lambda label, detail: _native("boundary", "editorial_boundary", label, detail, "evidence_boundary")
TIMING = lambda label, detail: _native("source_clock", "timeline", label, detail, "source_timing")
STRESS = lambda label, detail: _native("stress_chain", "transmission_diagram", label, detail, "stress_transmission")
MONITOR = lambda label, detail: _native("monitoring", "monitoring_framework", label, detail, "confirmation_invalidation")
MONTAGE = lambda label, detail: _native("montage", "material_montage", label, detail, "editorial_synthesis")


RECIPES: dict[str, list[dict[str, Any]]] = {
    "S01_GIANT_OFFSET": [_photo(PHOTO_CFTC, "THE OFFICIAL SNAPSHOT", "CFTC · Washington · positions as of 11 Aug 2026"), POSITION("A GIANT OFFSET", "Asset managers long · leveraged funds short"), MONTAGE("ONE MARKET · DIFFERENT JOBS", "CFTC rows · Treasury collateral · Fed plumbing")],
    "S02_THREE_CONTRACTS": [_doc(ROWS, "THE LONG SIDE", "+1,680,389 · +2,883,977 · +2,554,411", crop=True, focus="left"), POSITION("ASSET MANAGERS", "Net long across 2Y · 5Y · 10Y"), _photo(PHOTO_TREASURY, "SYNTHETIC DURATION", "Large institutions can add Treasury duration with futures")],
    "S03_SHORT_MIRROR": [_doc(ROWS, "THE SHORT SIDE", "−1,359,521 · −2,147,744 · −2,163,714", crop=True, focus="right"), POSITION("LEVERAGED FUNDS", "A near-mirror short — not matched counterparties"), _photo(PHOTO_CFTC, "CATEGORY TOTALS", "The report aggregates; it does not pair firms trade-for-trade")],
    "S04_PRIMARY_ROW": [_doc(ROWS, "WHAT THE FILE SAYS", "Exact governed rows · exact hashes · exact arithmetic"), BOUNDARY("WHAT IT CANNOT SAY", "No firm identity · no individual motive"), _photo(PHOTO_CFTC, "PRIMARY DATA", "Classification is evidence; motive remains an inference")],
    "S05_BASIS_MECHANISM": [_figure(FED_FIG4, "THE BASIS TRADE", "$830bn estimated as of Sep 2025", crop=True, focus="right"), MECHANISM("THE PACKAGE", "Repo cash → cash Treasury → short future"), _photo(PHOTO_FED, "FINANCING IS THE FULCRUM", "Small spread · large balance sheet")],
    "S06_NOT_IDENTITY": [_figure(FED_FIG3, "MORE THAN ONE STRATEGY", "Basis · swap spread · curve · liquidity uses"), BOUNDARY("PROXY ≠ IDENTITY", "Short futures can also hedge or express relative value"), _doc(FED_NOTE, "THE FED'S DECOMPOSITION", "Basis is substantial — not the whole book")],
    "S07_STRESS_TEST": [_doc(FED_FSR, "LEVERAGE NEAR RECORD HIGHS", "Federal Reserve Financial Stability Report · May 2026", crop=True, focus="center"), STRESS("THE UNWIND PATH", "Margin ↑ · repo tightens · positions shrink · depth falls"), _photo(PHOTO_FED, "VULNERABILITY ≠ ACTIVE BREAK", "Funding and dealer capacity decide the transmission")],
    "S08_CLOSE": [MONITOR("WATCH THE PAIRING", "Positioning + financing + basis + liquidity"), MONTAGE("VERIFY THE PLUMBING", "CFTC data · Fed evidence · Treasury market context"), _doc(ROWS, "A MAP — NOT A MOTIVE DETECTOR", "The offset is real. Its meaning has to be earned.")],

    "L01_COLD_OPEN": [_photo(PHOTO_CFTC, "AN OFFICIAL WEEKLY SNAPSHOT", "CFTC · Washington · 11 August 2026"), POSITION("MILLIONS LONG", "Asset managers across the curve"), POSITION("MILLIONS SHORT", "Leveraged funds across the curve"), _doc(ROWS, "THE OFFSET IN THE FILE", "Three contracts · one structural-looking pattern"), _photo(PHOTO_TREASURY, "THE BENCHMARK BOND MARKET", "Collateral · policy transmission · global reference price"), MONTAGE("ONE MARKET · DIFFERENT JOBS", "Positioning, financing and liquidity share the frame")],
    "L02_SOURCE_CLOCK": [_photo(PHOTO_CFTC, "START AT THE SOURCE", "Commodity Futures Trading Commission"), _doc(SCHEDULE, "TUESDAY → FRIDAY", "August 11 positions · August 14 release"), TIMING("A WEEKLY MAP", "Measured Tuesday · published Friday · market keeps moving"), _doc(ROWS, "REPORT DATE: 11 AUGUST 2026", "Governed raw row bytes, not a live terminal"), BOUNDARY("CATEGORY TOTALS", "Dealer · asset manager · leveraged fund · other reportables"), _photo(PHOTO_CFTC, "NOT A MOTIVE DETECTOR", "No named firms · no individual intent")],
    "L03_TWO_YEAR": [_doc(ROWS, "2-YEAR · RAW ROW", "Open interest 4,377,812", crop=True, focus="left"), POSITION("ASSET MANAGER NET", "+1,680,389 contracts"), POSITION("LEVERAGED FUND NET", "−1,359,521 contracts"), _doc(ROWS, "LONG 2,342,975 · SHORT 662,586", "Arithmetic produces the governed net", crop=True, focus="left"), _photo(PHOTO_CFTC, "STRUCTURAL-LOOKING · NOT IDENTIFIED", "Scale is observable; motive is not"), BOUNDARY("$200,000 FACE VALUE", "Face value is context — not economic risk")],
    "L04_FIVE_YEAR": [_doc(ROWS, "5-YEAR · RAW ROW", "Open interest 6,442,950", crop=True, focus="center"), POSITION("CENTER OF GRAVITY", "+2,883,977 asset manager net"), POSITION("THE OTHER SIDE", "−2,147,744 leveraged fund net"), _doc(ROWS, "DEALER NET ≈ −819,000", "Category totals clear through the market", crop=True, focus="center"), _photo(PHOTO_TREASURY, "ONE CONTRACT: $100,000 FACE", "Exposure context, not clean capital-at-risk"), BOUNDARY("NOTIONAL ≠ RISK", "Duration, margin and hedge package matter")],
    "L05_TEN_YEAR": [_doc(ROWS, "10-YEAR · RAW ROW", "Open interest 5,458,890", crop=True, focus="right"), POSITION("A NEAR-MIRROR", "+2,554,411 vs −2,163,714"), _photo(PHOTO_TREASURY, "CLEARING NETS THE MARKET", "The report does not disclose matched counterparties"), BOUNDARY("VISUALLY STRIKING ≠ PROOF", "Parallel totals are not a trade-for-trade match"), _doc(ROWS, "THE OBSERVED FACT", "Large opposing category nets", crop=True, focus="right"), POSITION("THE EVIDENCE LINE", "Describe the pattern; do not invent the pairing")],
    "L06_WEEKLY_CHANGE": [_doc(ROWS, "THE STOCK STAYED HUGE", "Weekly flow moved differently", crop=True), WEEKLY("5-YEAR WEEKLY Δ", "Asset manager −79,277 · leveraged fund +63,695"), WEEKLY("10-YEAR WEEKLY Δ", "Asset manager −40,268 · leveraged fund +67,956"), POSITION("BOTH SIDES TRIMMED", "A giant stock without a simple new pile-on"), _photo(PHOTO_CFTC, "ONE WEEK OF FLOW", "Do not confuse change with total position"), _doc(ROWS, "STOCK ≠ FLOW", "Read the level and weekly change together")],
    "L07_ASSET_MANAGER_JOB": [_photo(PHOTO_TREASURY, "WHY LONG FUTURES?", "Treasury duration without moving the full cash amount"), _doc(TREASURY_REMARKS, "TREASURIES DO MANY JOBS", "Funding · collateral · benchmark · monetary policy"), MECHANISM("SYNTHETIC DURATION", "Keep cash → add futures → receive rate exposure"), POSITION("OPERATIONAL EFFICIENCY", "Liquid futures can bridge inflows or benchmarks"), _photo(PHOTO_TREASURY, "PLAUSIBLE DEMAND · NOT ONE MOTIVE", "Pensions, insurers and funds may use the tool differently"), BOUNDARY("AGGREGATE CATEGORY", "The CFTC row does not identify the portfolio mandate")],
    "L08_BASIS_SETUP": [_photo(PHOTO_FED, "THE MOST-DISCUSSED SHORT", "Cash–futures basis trade"), _figure(FED_FIG4, "ESTIMATED BASIS POSITION", "About $830bn as of September 2025"), MECHANISM("CONVERGENCE PACKAGE", "Buy cash Treasury · short relatively rich future"), MECHANISM("THE GAP IS SMALL", "Scale and leverage make the return meaningful"), _figure(FED_FIG4, "THE TRADE RESURGED", "Fed estimate, not a CFTC-column identity", crop=True, focus="right"), BOUNDARY("ESTIMATE DATE MATTERS", "September 2025 portfolio estimate ≠ August 2026 live total")],
    "L09_REPO_FINANCING": [_figure(FED_FIG1, "REPO CASH BORROWING", "About $3tn by September 2025", crop=True, focus="left"), MECHANISM("PLEDGE THE TREASURY", "Borrow most of its value · supply an equity cushion"), _photo(PHOTO_FED, "THE FINANCING FULCRUM", "Availability · haircuts · rollover terms"), MECHANISM("TWO LIQUIDITY LEGS", "Repo funding + futures variation margin"), _figure(FED_FIG1, "MARKET-NEUTRAL ≠ LIQUIDITY-NEUTRAL", "Gross books can still demand cash quickly"), STRESS("A THIN SPREAD · A LARGE BOOK", "Small price move → large margin demand")],
    "L10_FED_SCALE": [_doc(FED_NOTE, "THE FED'S PORTFOLIO VIEW", "$4.0tn gross Treasury exposure · Sep 2025"), _figure(FED_FIG1, "$2.4tn LONG · $1.6tn SHORT", "Physical and derivatives exposures"), _figure(FED_FIG1, "ABOUT $3tn REPO CASH BORROWING", "Source: SEC Form PF · author analysis", crop=True, focus="left"), _figure(FED_FIG4, "ABOUT $830bn BASIS", "Substantial — not the whole book"), _photo(PHOTO_FED, "PORTFOLIO ESTIMATES", "Regulatory data, methodology and explicit dates"), BOUNDARY("DO NOT BACK-SOLVE THE CFTC COLUMN", "The two datasets answer different questions")],
    "L11_PROXY_BOUNDARY": [_figure(FED_FIG3, "SEVEN USES FOR LONG EXPOSURE", "Basis is one component of a broader book"), _doc(FED_NOTE, "A DECOMPOSITION — NOT A MONOCULTURE", "Basis · swap spread · curve · liquidity uses"), BOUNDARY("USEFUL PROXY", "Leveraged-fund shorts can flag possible basis activity"), BOUNDARY("IMPERFECT IDENTIFICATION", "Hedges and other relative-value strategies also appear"), _figure(FED_FIG4, "PRECISE TOTALS REQUIRE BETTER DATA", "One CFTC column cannot produce a basis total", crop=True), _photo(PHOTO_CFTC, "STOP AT THE EVIDENCE LINE", "Classification is not strategy attribution")],
    "L12_BENEFIT": [_doc(TREASURY_REMARKS, "WHY MARKET FUNCTION MATTERS", "Treasuries are collateral and a global benchmark"), _photo(PHOTO_TREASURY, "ARBITRAGE CAN HELP", "Pull cash and futures prices back together"), MECHANISM("INTERMEDIATION", "Asset managers ↔ futures ↔ hedge funds ↔ dealers"), _figure(FED_FIG3, "RELATIVE VALUE HAS MANY FORMS", "Price discovery and liquidity are real services"), _photo(PHOTO_FED, "THE CONCERN IS STRUCTURE", "Financing and adjustment speed under stress"), MONTAGE("SERVICE + VULNERABILITY", "Both can be true at once")],
    "L13_STRESS_CHAIN": [_doc(FED_FSR, "HEDGE-FUND LEVERAGE ELEVATED", "Financial Stability Report · May 2026", crop=True), STRESS("VOLATILITY JUMPS", "Variation margin arrives first"), STRESS("REPO TERMS TIGHTEN", "More collateral · less balance-sheet capacity"), _figure(FED_FIG1, "A LARGE FINANCED BOOK", "Repo and Treasury exposure grew together"), STRESS("SYNCHRONIZED UNWIND", "Sell cash · cut futures · reduce elsewhere"), _photo(PHOTO_TREASURY, "MARKET DEPTH CAN FALL", "Individually sensible actions become system-wide pressure")],
    "L14_DEALER_CAPACITY": [_doc(FED_FSR, "THE CURRENT COUNTERWEIGHT", "Dealer intermediation robust; hedge-fund leverage high", crop=True), _photo(PHOTO_FED, "VULNERABILITY · NOT A BREAK", "The report does not say a crisis is underway"), STRESS("DEALERS SIT IN THE MIDDLE", "Finance clients · make cash markets · intermediate hedges"), _doc(FED_FSR, "FIGURE 3.13", "Most dealers reported no change in client leverage use", crop=True, focus="center"), MECHANISM("ABSORB OR AMPLIFY", "Dealer capacity + repo conditions decide the outcome"), BOUNDARY("STATE THE CONDITION", "Elevated leverage becomes stress only through a transmission path")],
    "L15_WHAT_TO_WATCH": [MONITOR("1 · POSITIONING", "Are leveraged shorts persistent across contracts?"), _doc(ROWS, "2 · THE CFTC MAP", "Levels + weekly changes + category boundary", crop=True), _figure(FED_FIG1, "3 · FINANCING", "Repo borrowing · rates · haircuts", crop=True, focus="left"), _figure(FED_FIG4, "4 · CASH–FUTURES GAP", "Widening or converging?", crop=True, focus="right"), _doc(FED_FSR, "5 · MARKET LIQUIDITY", "Dealer capacity · depth · leverage"), MONITOR("THE SIGNAL IS AGREEMENT", "Positioning + financing + basis + liquidity")],
    "L16_CONFIRM": [_figure(FED_FIG3, "CONFIRM WITH PORTFOLIO EVIDENCE", "Which strategies actually own the exposure?"), MONITOR("CONFIRM", "Shorts + repo + widening basis + weaker depth"), BOUNDARY("CHALLENGE", "Shorts unwind while funding stays calm"), _figure(FED_FIG4, "THE BASIS MEASURE", "Use a direct estimate, not an assumed identity"), _doc(ROWS, "THE CFTC CATEGORY IS BROAD", "The dramatic narrative is not automatically correct"), MONTAGE("MULTIPLE SURFACES · ONE JUDGMENT", "Confirmation and invalidation carry equal weight")],
    "L17_BALANCE_SHEET": [_photo(PHOTO_TREASURY, "THE ASSET-MANAGER JOB", "Obtain duration efficiently"), POSITION("THE FUTURES OFFSET", "Huge nets need not mean opposite rate forecasts"), _figure(FED_FIG1, "THE HEDGE-FUND BOOK", "Cash · derivatives · repo · turnover"), MECHANISM("THE CONNECTORS", "Dealers + repo lenders + clearing"), _photo(PHOTO_FED, "THE LIQUIDITY CONSEQUENCE", "Volatility concentrates cash demands"), MONTAGE("MECHANISM BEFORE MORAL", "See the service · then see the vulnerability")],
    "L18_CLOSE": [_doc(ROWS, "THE PRECISE SNAPSHOT", "Enormous longs · enormous shorts · both sides trimming"), _photo(PHOTO_CFTC, "WHAT THE REPORT GIVES", "A governed weekly category map"), BOUNDARY("WHAT IT DOES NOT GIVE", "Motive · live risk gauge · crisis countdown"), MONITOR("IDENTIFY THE ROUTE", "Repo + portfolio + basis + liquidity evidence"), POSITION("THE GIANT OFFSET IS REAL", "+2.88m vs −2.15m in the five-year"), MONTAGE("ITS MEANING HAS TO BE EARNED", "Source · mechanism · boundary · test"), _photo(PHOTO_TREASURY, "POSITIONING IS A MAP", "Not a motive detector")],
}


def _end(ratio: float, item: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(item)
    row["semantic_end_ratio"] = ratio
    return row


# The owner candidate uses explicitly authored narration/information boundaries.
# RECIPES remains only as a legacy reference for older fixtures; it is never
# consulted by material_plan().  End ratios were authored scene by scene and
# intentionally produce unequal beat durations and longer evidence holds.
SEMANTIC_SEQUENCES: dict[str, list[dict[str, Any]]] = {
    "S01_GIANT_OFFSET": [
        _end(.28, _photo(PHOTO_CFTC, "THE OFFICIAL SNAPSHOT", "CFTC · positions as of 11 Aug 2026")),
        _end(.72, POSITION("A GIANT OFFSET", "Asset managers long · leveraged funds short")),
        _end(1, MONTAGE("ONE MARKET · DIFFERENT JOBS", "Positioning · financing · liquidity")),
    ],
    "S02_THREE_CONTRACTS": [
        _end(.43, MATURITY("2Y · ASSET MANAGER", "+1,680,389 net contracts")),
        _end(.78, MATURITY("5Y · ASSET MANAGER", "+2,883,977 net contracts")),
        _end(1, POSITION("THE LONG SIDE", "Governed values across the curve")),
    ],
    "S03_SHORT_MIRROR": [
        _end(.36, MATURITY("2Y · LEVERAGED FUND", "−1,359,521 net contracts")),
        _end(.72, MATURITY("5Y · LEVERAGED FUND", "−2,147,744 net contracts")),
        _end(1, BOUNDARY("A NEAR-MIRROR · NOT A MATCH", "Category totals do not identify counterparties")),
    ],
    "S04_PRIMARY_ROW": [
        _end(.31, _doc(CFTC_NOTES_1, "WHAT THE REPORT CLASSIFIES", "Four trader categories · Tuesday positions")),
        _end(.73, _doc(ROWS, "SOURCE VERIFICATION", "Full governed 2Y · 5Y · 10Y rows")),
        _end(1, _doc(CFTC_NOTES_4, "WHAT IT CANNOT IDENTIFY", "Trader category does not reveal each trading motive")),
    ],
    "S05_BASIS_MECHANISM": [
        _end(.29, _doc(FED_BASIS_NOTE, "THE BASIS PACKAGE", "Federal Reserve · 8 Mar 2024")),
        _end(.73, MECHANISM("THE THREE LEGS", "Repo cash → cash Treasury → short future")),
        _end(1, _figure(FED_FIG4, "PORTFOLIO ESTIMATE", "$830bn as of Sep 2025 · not a live CFTC identity")),
    ],
    "S06_NOT_IDENTITY": [
        _end(.33, _figure(FED_2024_FIG2, "THE TIMELY PROXY", "Leveraged-fund shorts by Treasury tenor")),
        _end(.70, _figure(FED_2024_FIG6, "MULTIPLE MEASURES", "Futures · repo · TRACE do not coincide")),
        _end(1, BOUNDARY("PROXY ≠ IDENTITY", "Funds also hedge and run other relative-value trades")),
    ],
    "S07_STRESS_TEST": [
        _end(.36, _doc(FED_FSR_LEVERAGE, "LEVERAGE NEAR RECORD HIGHS", "Federal Reserve FSR · May 2026 · full page")),
        _end(.76, STRESS("THE UNWIND PATH", "Margin ↑ · repo tightens · positions shrink · depth falls")),
        _end(1, _figure(FED_2024_FIG5, "FINANCING IS THE FULCRUM", "Net repo is a separate monitoring surface")),
    ],
    "S08_CLOSE": [
        _end(.43, MONITOR("WATCH THE PAIRING", "Positioning + financing + basis + liquidity")),
        _end(.74, MONTAGE("VERIFY THE PLUMBING", "Source · mechanism · boundary · test")),
        _end(1, BOUNDARY("A MAP — NOT A MOTIVE DETECTOR", "The offset is real. Its meaning has to be earned.")),
    ],

    "L01_COLD_OPEN": [
        _end(.12, _photo(PHOTO_CFTC, "AN OFFICIAL WEEKLY SNAPSHOT", "CFTC · 11 August 2026")),
        _end(.27, POSITION("MILLIONS LONG", "Asset managers across the Treasury curve")),
        _end(.42, POSITION("MILLIONS SHORT", "Leveraged funds across the Treasury curve")),
        _end(.56, _figure(FED_2023_FIG4, "THE PAIRING HAS HISTORY", "Federal Reserve · contract-tenor context · 2023")),
        _end(.70, _doc(FED_POSITIONING_NOTE, "DIFFERENT USERS · SAME INSTRUMENT", "Historical mechanism context · not the 2026 snapshot")),
        _end(.84, MECHANISM("TWO BALANCE-SHEET JOBS", "Synthetic duration ↔ financed relative value")),
        _end(1, MONTAGE("THE WORLD'S BENCHMARK BOND MARKET", "Positioning · collateral · policy transmission")),
    ],
    "L02_SOURCE_CLOCK": [
        _end(.13, _doc(CFTC_NOTES_1, "START WITH THE SOURCE", "TFF categories and Tuesday open interest")),
        _end(.27, _doc(SCHEDULE, "TUESDAY → FRIDAY", "August 11 positions · August 14 release")),
        _end(.42, TIMING("A WEEKLY MAP", "Measured Tuesday · published Friday")),
        _end(.56, BOUNDARY("NOT A LIVE SCREEN", "The market keeps moving after the snapshot")),
        _end(.70, _doc(CFTC_NOTES_4, "CLASSIFY THE TRADER", "CFTC staff assigns predominant business category")),
        _end(.84, BOUNDARY("NOT THE INDIVIDUAL TRADE", "Category does not disclose firm or motive")),
        _end(1, MONTAGE("SOURCE CLOCK · CATEGORY · LIMIT", "Three conditions before interpretation")),
    ],
    "L03_TWO_YEAR": [
        _end(.16, _doc(ROWS, "SOURCE VERIFICATION · 2Y", "Full governed table · open interest 4,377,812")),
        _end(.31, MATURITY("2Y · ASSET MANAGER LONG", "2,342,975 long · 662,586 short")),
        _end(.46, MATURITY("2Y · ASSET MANAGER NET", "+1,680,389")),
        _end(.61, MATURITY("2Y · LEVERAGED FUND NET", "−1,359,521")),
        _end(.75, POSITION("A STRUCTURAL-LOOKING OFFSET", "Scale is observable; motive is not")),
        _end(.88, BOUNDARY("$200,000 FACE VALUE", "Contract size is context — not capital at risk")),
        _end(1, MONTAGE("OBSERVATION BEFORE INTERPRETATION", "Open interest · gross legs · governed nets")),
    ],
    "L04_FIVE_YEAR": [
        _end(.15, MATURITY("5Y · OPEN INTEREST", "6,442,950 contracts")),
        _end(.31, MATURITY("5Y · ASSET MANAGER NET", "+2,883,977")),
        _end(.47, MATURITY("5Y · LEVERAGED FUND NET", "−2,147,744")),
        _end(.61, MATURITY("5Y · DEALER NET", "Approximately −819,000")),
        _end(.75, _doc(TREASURY_REMARKS, "THE BENCHMARK MARKET", "Treasuries serve funding, collateral and policy transmission")),
        _end(.88, BOUNDARY("$100,000 FACE VALUE", "Notional context is not clean economic risk")),
        _end(1, POSITION("THE CENTER OF GRAVITY", "The largest asset-manager net in the set")),
    ],
    "L05_TEN_YEAR": [
        _end(.16, MATURITY("10Y · OPEN INTEREST", "5,458,890 contracts")),
        _end(.33, MATURITY("10Y · ASSET MANAGER NET", "+2,554,411")),
        _end(.50, MATURITY("10Y · LEVERAGED FUND NET", "−2,163,714")),
        _end(.66, POSITION("A NEAR-MIRROR", "Visually striking · not a matched trade")),
        _end(.82, _doc(CFTC_NOTES_4, "CFTC CLASSIFIES TRADERS", "It does not identify matched counterparties")),
        _end(1, BOUNDARY("CLEARING NETS THE MARKET", "Describe the pattern; do not invent the pairing")),
    ],
    "L06_WEEKLY_CHANGE": [
        _end(.15, WEEKLY("5-YEAR WEEKLY Δ", "Asset manager −79,277")),
        _end(.30, WEEKLY("5-YEAR WEEKLY Δ", "Leveraged fund +63,695 · short less negative")),
        _end(.45, WEEKLY("10-YEAR WEEKLY Δ", "Asset manager −40,268")),
        _end(.60, WEEKLY("10-YEAR WEEKLY Δ", "Leveraged fund +67,956 · short less negative")),
        _end(.74, _figure(FED_2023_FIG4, "STOCKS CAN STAY LARGE", "Historical contract-tenor context")),
        _end(.87, _doc(FED_POSITIONING_NOTE, "FLOW NEEDS CONTEXT", "Pair weekly change with the level")),
        _end(1, BOUNDARY("STOCK ≠ FLOW", "Both sides trimmed parts of the offset")),
    ],
    "L07_ASSET_MANAGER_JOB": [
        _end(.14, _photo(PHOTO_TREASURY, "WHY LONG FUTURES?", "Institutional Treasury-market context")),
        _end(.29, _doc(TREASURY_REMARKS, "TREASURIES DO MANY JOBS", "Funding · collateral · benchmark · monetary policy")),
        _end(.45, MECHANISM("SYNTHETIC DURATION", "Keep cash → add futures → receive rate exposure")),
        _end(.60, POSITION("OPERATIONAL EFFICIENCY", "Liquid futures can bridge inflows or benchmarks")),
        _end(.74, MECHANISM("MULTIPLE PORTFOLIO USES", "Pension · insurer · mutual fund · other institution")),
        _end(.87, BOUNDARY("PLAUSIBLE DEMAND", "Not one universal motive")),
        _end(1, MONTAGE("AGGREGATE CATEGORY", "The row does not identify the portfolio mandate")),
    ],
    "L08_BASIS_SETUP": [
        _end(.14, _doc(FED_BASIS_NOTE, "THE CASH–FUTURES BASIS", "Federal Reserve · mechanism and measurement")),
        _end(.29, MECHANISM("THE CONVERGENCE PACKAGE", "Buy cash Treasury · short relatively rich future")),
        _end(.44, MECHANISM("DELIVERY LINKS THE PRICES", "The cash bond and future should converge")),
        _end(.59, MECHANISM("THE GAP IS SMALL", "Scale and leverage make the return meaningful")),
        _end(.74, _figure(FED_FIG4, "THE TRADE RESURGED", "$830bn portfolio estimate · September 2025")),
        _end(.87, BOUNDARY("ESTIMATE DATE MATTERS", "Not an August 2026 live total")),
        _end(1, MONTAGE("CASH · FUTURE · FINANCING", "Three legs — one convergence thesis")),
    ],
    "L09_REPO_FINANCING": [
        _end(.14, _figure(FED_2024_FIG5, "NET REPO POSITIONING", "A distinct financing proxy")),
        _end(.29, MECHANISM("PLEDGE THE TREASURY", "Borrow most of its value")),
        _end(.44, MECHANISM("SUPPLY AN EQUITY CUSHION", "A thin spread can become attractive on equity")),
        _end(.58, _photo(PHOTO_FED, "THE FINANCING FULCRUM", "Availability · haircuts · rollover terms")),
        _end(.73, MECHANISM("TWO LIQUIDITY LEGS", "Repo funding + futures variation margin")),
        _end(.87, STRESS("MARKET-NEUTRAL", "Can still be liquidity-sensitive")),
        _end(1, BOUNDARY("BOTH LEGS DEMAND CASH", "Financing conditions govern the package")),
    ],
    "L10_FED_SCALE": [
        _end(.14, _doc(FED_NOTE, "THE FED'S PORTFOLIO VIEW", "June 2026 note · estimates as of Sep 2025")),
        _end(.29, _figure(FED_FIG1, "$4.0tn GROSS TREASURY EXPOSURE", "$2.4tn long · $1.6tn short · about $3tn repo")),
        _end(.44, _figure(FED_FIG2, "8.5% OF PRIVATELY HELD TREASURIES", "Estimated hedge-fund holdings share · Sep 2025")),
        _end(.59, _figure(FED_FIG4, "$830bn ESTIMATED BASIS", "Substantial — not the whole book")),
        _end(.73, POSITION("PORTFOLIO ESTIMATES", "Regulatory data + explicit methodology")),
        _end(.87, BOUNDARY("NOT A LIVE CFTC IDENTITY", "The datasets answer different questions")),
        _end(1, MONTAGE("SCALE · DATE · METHOD", "Keep every estimate inside its boundary")),
    ],
    "L11_PROXY_BOUNDARY": [
        _end(.14, _figure(FED_2024_FIG2, "THE TIMELY FUTURES PROXY", "Leveraged shorts across Treasury tenors")),
        _end(.29, _figure(FED_2024_FIG6, "THE PROXIES DIVERGE", "Futures · net repo · TRACE")),
        _end(.44, _figure(FED_FIG3, "SEVEN USES FOR LONG EXPOSURE", "Basis is one component of a broader book")),
        _end(.58, _figure(FED_FIG5, "SWAP-SPREAD ARBITRAGE", "A separate relative-value strategy")),
        _end(.72, _doc(FED_BASIS_NOTE, "THE FED'S WARNING", "Leveraged shorts may overestimate basis activity")),
        _end(.86, BOUNDARY("USEFUL PROXY · IMPERFECT IDENTITY", "Hedges and other relative-value trades also appear")),
        _end(1, BOUNDARY("STOP AT THE EVIDENCE LINE", "One CFTC column cannot produce a precise basis total")),
    ],
    "L12_BENEFIT": [
        _end(.14, _doc(TREASURY_REMARKS, "WHY MARKET FUNCTION MATTERS", "Treasuries are collateral and a global benchmark")),
        _end(.29, MECHANISM("ARBITRAGE CAN HELP", "Pull cash and futures prices back together")),
        _end(.44, MECHANISM("PRICE DISCOVERY", "Demand transmits between instruments")),
        _end(.58, MECHANISM("INTERMEDIATION", "Asset managers ↔ futures ↔ hedge funds ↔ dealers")),
        _end(.72, _figure(FED_FIG3, "RELATIVE VALUE HAS MANY FORMS", "Liquidity and price alignment are real services")),
        _end(.86, BOUNDARY("THE CONCERN IS STRUCTURE", "Financing and adjustment speed under stress")),
        _end(1, MONTAGE("SERVICE + VULNERABILITY", "Both can be true at once")),
    ],
    "L13_STRESS_CHAIN": [
        _end(.14, _doc(FED_FSR, "FROM FUNDING TO LEVERAGE", "Federal Reserve FSR · May 2026 · full page")),
        _end(.29, STRESS("VOLATILITY JUMPS", "Variation margin arrives first")),
        _end(.44, STRESS("CASH TREASURIES LOSE VALUE", "Collateral needs can rise")),
        _end(.59, STRESS("REPO TERMS TIGHTEN", "More collateral · less balance-sheet capacity")),
        _end(.73, _figure(FED_2024_FIG5, "THE FINANCING SURFACE", "Net repo provides separate context")),
        _end(.87, STRESS("SYNCHRONIZED UNWIND", "Sell cash · cut futures · reduce elsewhere")),
        _end(1, MONTAGE("SMALL BASIS · LARGE GROSS BOOK", "Individually sensible actions can become market pressure")),
    ],
    "L14_DEALER_CAPACITY": [
        _end(.14, _doc(FED_FSR_DEALER, "DEALER LEVERAGE REMAINED LOW", "Federal Reserve FSR · report page 29")),
        _end(.29, _photo(PHOTO_FED, "DEALERS SIT IN THE MIDDLE", "Finance clients · make cash markets · intermediate hedges")),
        _end(.44, MECHANISM("THE NORMAL-TIMES BUFFER", "Capacity to absorb client repositioning")),
        _end(.59, _doc(FED_FSR_LEVERAGE, "HEDGE-FUND LEVERAGE ELEVATED", "Figures 3.11–3.13 · full page")),
        _end(.73, STRESS("ABSORB OR AMPLIFY", "Dealer capacity + repo conditions decide the outcome")),
        _end(.87, BOUNDARY("VULNERABILITY ≠ ACTIVE BREAK", "The report does not say a crisis is underway")),
        _end(1, MONTAGE("STATE THE CONDITION", "Funding and balance-sheet capacity govern transmission")),
    ],
    "L15_WHAT_TO_WATCH": [
        _end(.14, MONITOR("1 · POSITIONING", "Are leveraged shorts persistent across contracts?")),
        _end(.28, _figure(FED_2024_FIG2, "2 · CONTRACT TENORS", "Short futures across the curve")),
        _end(.42, _figure(FED_2024_FIG5, "3 · FINANCING", "Repo borrowing · rates · haircuts")),
        _end(.56, _figure(FED_2024_FIG6, "4 · CASH–FUTURES GAP", "Compare direct and proxy measures")),
        _end(.70, WEEKLY("5 · ASSET-MANAGER DEMAND", "Watch levels and weekly changes")),
        _end(.84, MONITOR("6 · MARKET LIQUIDITY", "Dealer capacity · depth · leverage")),
        _end(1, MONTAGE("THE SIGNAL IS AGREEMENT", "Positioning + financing + basis + liquidity")),
    ],
    "L16_CONFIRM": [
        _end(.14, _figure(FED_FIG3, "CONFIRM WITH PORTFOLIO EVIDENCE", "Which strategies own the exposure?")),
        _end(.29, MONITOR("CONFIRM", "Shorts + repo + widening basis + weaker depth")),
        _end(.44, BOUNDARY("CHALLENGE", "Shorts unwind while funding stays calm")),
        _end(.58, _figure(FED_FIG4, "USE A DIRECT ESTIMATE", "Do not assume the futures column is the basis total")),
        _end(.72, _doc(CFTC_NOTES_4, "THE CFTC CATEGORY IS BROAD", "CFTC classifies traders, not each trading activity")),
        _end(.86, BOUNDARY("INVALIDATION MATTERS", "The most dramatic narrative is not automatically correct")),
        _end(1, MONTAGE("MULTIPLE SURFACES · ONE JUDGMENT", "Confirmation and challenge carry equal weight")),
    ],
    "L17_BALANCE_SHEET": [
        _end(.14, _doc(FED_POSITIONING_NOTE, "DIFFERENT BALANCE-SHEET JOBS", "Historical pairing and mechanism context")),
        _end(.29, _photo(PHOTO_TREASURY, "THE ASSET-MANAGER JOB", "Obtain duration efficiently")),
        _end(.44, POSITION("THE FUTURES OFFSET", "Huge nets need not mean opposite rate forecasts")),
        _end(.58, _figure(FED_FIG2, "THE HEDGE-FUND BOOK", "Large holdings inside a broader Treasury market")),
        _end(.72, MECHANISM("THE CONNECTORS", "Dealers + repo lenders + clearing")),
        _end(.86, STRESS("THE LIQUIDITY CONSEQUENCE", "Volatility concentrates cash demands")),
        _end(1, MONTAGE("MECHANISM BEFORE MORAL", "See the service · then see the vulnerability")),
    ],
    "L18_CLOSE": [
        _end(.14, _doc(ROWS, "SOURCE VERIFICATION · CLOSE", "Full governed snapshot · both sides trimming")),
        _end(.28, _doc(CFTC_NOTES_1, "WHAT THE REPORT GIVES", "A governed weekly category map")),
        _end(.42, _doc(CFTC_NOTES_4, "WHAT IT DOES NOT GIVE", "Motive · live risk gauge · crisis countdown")),
        _end(.57, MONITOR("IDENTIFY THE ROUTE", "Repo + portfolio + basis + liquidity")),
        _end(.71, POSITION("THE GIANT OFFSET IS REAL", "+2.88m vs −2.15m in the five-year")),
        _end(.85, MONTAGE("ITS MEANING HAS TO BE EARNED", "Source · mechanism · boundary · test")),
        _end(1, _photo(PHOTO_CFTC, "POSITIONING IS A MAP", "Not a motive detector")),
    ],
}


def material_plan(scenes: Sequence[Mapping[str, Any]], durations: Mapping[str, float]) -> dict[str, list[dict[str, Any]]]:
    """Bind explicit story-specific semantic boundaries to frozen audio durations."""
    result: dict[str, list[dict[str, Any]]] = {}
    for scene in scenes:
        scene_id = str(scene["scene_id"])
        duration = float(durations[scene_id])
        sequence = SEMANTIC_SEQUENCES.get(scene_id)
        if not sequence:
            raise KeyError(f"missing_semantic_sequence:{scene_id}")
        beats: list[dict[str, Any]] = []
        start = 0.0
        prior_ratio = 0.0
        for index, authored in enumerate(sequence):
            ratio = float(authored["semantic_end_ratio"])
            if not prior_ratio < ratio <= 1.0:
                raise ValueError(f"invalid_semantic_boundary:{scene_id}:{ratio}")
            row = {key: value for key, value in authored.items() if key != "semantic_end_ratio"}
            end = duration if index == len(sequence) - 1 else duration * ratio
            row.update({"beat_id": f"{scene_id}_B{index + 1:02d}", "start_seconds": round(start, 6),
                        "end_seconds": round(end, 6), "duration_seconds": round(end - start, 6),
                        "boundary_authority": "EXPLICIT_NARRATION_INFORMATION_CHANGE"})
            beats.append(row)
            start = end
            prior_ratio = ratio
        if abs(prior_ratio - 1.0) > 1e-9:
            raise ValueError(f"semantic_sequence_does_not_end_at_one:{scene_id}:{prior_ratio}")
        result[scene_id] = beats
    return result


def validate_evidence_motion_contract(plan: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    errors: list[str] = []
    static_assets: set[str] = set()
    governed_native_visuals = 0
    for beats in plan.values():
        for row in beats:
            object_class = str(row["evidence_object_class"])
            policy = str(row["motion_policy"])
            layout = str(row["layout"])
            if object_class in STATIC_OBJECT_CLASSES and policy != STATIC_FULL_CONTEXT:
                errors.append(f"primary_evidence_not_static:{row['beat_id']}:{policy}")
            if object_class in STATIC_OBJECT_CLASSES and ("crop" in layout or layout not in {"document_full", "figure_full"}):
                errors.append(f"primary_evidence_not_full_context:{row['beat_id']}:{layout}")
            if object_class == "primary_document" and policy != STATIC_FULL_CONTEXT:
                errors.append(f"primary_document_not_static:{row['beat_id']}:{policy}")
            if policy == STATIC_FULL_CONTEXT and row.get("asset"):
                static_assets.add(str(row["asset"]))
            if object_class == "native_cc_data_visual":
                governed_native_visuals += 1
                if policy != NATIVE_GOVERNED_MOTION:
                    errors.append(f"native_data_motion_disabled:{row['beat_id']}:{policy}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "policy": "Primary charts, source figures, numeric tables/data and source documents are static full-context objects. Governed native CC data visuals may animate.",
        "static_full_context_assets": sorted(static_assets),
        "governed_native_visual_count": governed_native_visuals,
    }


def validate_material_plan(plan: Mapping[str, Sequence[Mapping[str, Any]]], selected_asset_hashes: Mapping[str, str]) -> dict[str, Any]:
    errors: list[str] = []
    source_family_seconds: Counter[str] = Counter()
    presentation_seconds: Counter[str] = Counter()
    asset_seconds: Counter[str] = Counter()
    total = 0.0
    real_source_seconds = 0.0
    longest_abstract_run = 0.0
    durations: list[float] = []
    for scene_id, beats in plan.items():
        if not beats:
            errors.append(f"empty_scene:{scene_id}")
            continue
        abstract_run = 0.0
        prior_asset: str | None = None
        expected_start = 0.0
        for row in beats:
            duration = float(row["duration_seconds"])
            durations.append(duration)
            total += duration
            source_family = str(row["source_material_family"])
            presentation = str(row["presentation_grammar"])
            asset = row.get("asset")
            presentation_seconds[presentation] += duration
            if abs(float(row["start_seconds"]) - expected_start) > 1e-5:
                errors.append(f"semantic_timeline_gap:{row['beat_id']}:{expected_start}:{row['start_seconds']}")
            expected_start = float(row["end_seconds"])
            if duration <= 0:
                errors.append(f"nonpositive_semantic_beat:{row['beat_id']}:{duration}")
            if duration > 7.0 and not (row.get("readability_hold") and row.get("motion_policy") == STATIC_FULL_CONTEXT):
                errors.append(f"unjustified_long_semantic_hold:{row['beat_id']}:{duration}")
            if asset:
                if asset not in selected_asset_hashes:
                    errors.append(f"asset_not_selected:{row['beat_id']}:{asset}")
                asset_seconds[str(asset)] += duration
                source_family_seconds[source_family] += duration
                real_source_seconds += duration
                abstract_run = 0.0
                if asset == prior_asset:
                    errors.append(f"consecutive_asset_reuse:{row['beat_id']}:{asset}")
            else:
                if row.get("evidence_object_class") == "editorial_typography":
                    abstract_run += duration
                    longest_abstract_run = max(longest_abstract_run, abstract_run)
                else:
                    abstract_run = 0.0
            prior_asset = str(asset) if asset else None
    if total <= 0:
        errors.append("no_screen_time")
    if total and real_source_seconds / total < 0.34:
        errors.append(f"insufficient_real_source_screen_time:{real_source_seconds / total:.3f}")
    if total > 300 and len(source_family_seconds) < 8:
        errors.append(f"insufficient_source_material_families:{len(source_family_seconds)}")
    if longest_abstract_run > 12.1:
        errors.append(f"prolonged_abstract_run:{longest_abstract_run:.3f}")
    motion = validate_evidence_motion_contract(plan)
    errors.extend(motion["errors"])
    must_use = set(ASSET_SOURCE_FAMILY) if total > 300 else {
        PHOTO_CFTC, ROWS, CFTC_NOTES_1, CFTC_NOTES_4, FED_BASIS_NOTE,
        FED_FIG4, FED_2024_FIG2, FED_2024_FIG5, FED_2024_FIG6, FED_FSR_LEVERAGE,
    }
    missing = sorted(must_use - set(asset_seconds))
    if missing:
        errors.append(f"must_use_assets_absent:{','.join(missing)}")
    return {
        "status": "PASS" if not errors else "FAIL", "errors": errors, "total_seconds": round(total, 3),
        "real_source_seconds": round(real_source_seconds, 3),
        "real_source_share": round(real_source_seconds / total, 4) if total else 0,
        "longest_abstract_run_seconds": round(longest_abstract_run, 3),
        "source_material_family_seconds": {key: round(value, 3) for key, value in sorted(source_family_seconds.items())},
        "presentation_grammar_seconds": {key: round(value, 3) for key, value in sorted(presentation_seconds.items())},
        "asset_seconds": {key: round(value, 3) for key, value in sorted(asset_seconds.items())},
        "semantic_beat_duration_seconds": {
            "minimum": round(min(durations), 3), "maximum": round(max(durations), 3),
            "distinct_rounded_tenths": len({round(value, 1) for value in durations}),
            "note": "2–4 seconds is a heuristic, not a quota; boundaries follow narration/information changes.",
        },
        "evidence_motion_contract": motion,
    }


def dependency_manifest(plans: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]], selected_asset_hashes: Mapping[str, str]) -> dict[str, Any]:
    source_family: Counter[str] = Counter()
    presentation: Counter[str] = Counter()
    asset: Counter[str] = Counter()
    purpose: Counter[str] = Counter()
    per_scene: dict[str, Any] = {}
    asset_occurrences: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    family_occurrences: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    total = 0.0
    for variant, plan in plans.items():
        variant_cursor = 0.0
        prior_source_asset: str | None = None
        for scene_id, beats in plan.items():
            scene_source_families: Counter[str] = Counter()
            scene_presentations: Counter[str] = Counter()
            scene_assets: Counter[str] = Counter()
            for row in beats:
                duration = float(row["duration_seconds"])
                total += duration
                family_name = str(row["source_material_family"])
                grammar = str(row["presentation_grammar"])
                presentation[grammar] += duration
                purpose[str(row["purpose"])] += duration
                scene_presentations[grammar] += duration
                if row.get("asset"):
                    filename = str(row["asset"])
                    start = variant_cursor + float(row["start_seconds"])
                    source_family[family_name] += duration
                    scene_source_families[family_name] += duration
                    asset[filename] += duration
                    scene_assets[filename] += duration
                    occurrence = {
                        "variant": variant, "scene_id": scene_id, "beat_id": row["beat_id"],
                        "start_seconds": round(start, 3), "duration_seconds": round(duration, 3),
                        "semantic_purpose": row["purpose"], "adjacent_source_asset_reuse": filename == prior_source_asset,
                    }
                    asset_occurrences[filename].append(occurrence)
                    family_occurrences[family_name].append(occurrence | {"asset": filename})
                    prior_source_asset = filename
            per_scene[f"{variant}:{scene_id}"] = {
                "duration_seconds": round(sum(float(row["duration_seconds"]) for row in beats), 3),
                "semantic_beats": len(beats),
                "source_material_families": {key: round(value, 3) for key, value in scene_source_families.items()},
                "presentation_grammars": {key: round(value, 3) for key, value in scene_presentations.items()},
                "assets": {key: round(value, 3) for key, value in scene_assets.items()},
            }
            variant_cursor += sum(float(row["duration_seconds"]) for row in beats)

    asset_usage: dict[str, Any] = {}
    for filename, occurrences in sorted(asset_occurrences.items()):
        short_window = 0
        for prior, current in zip(occurrences, occurrences[1:]):
            if prior["variant"] == current["variant"] and current["start_seconds"] - prior["start_seconds"] <= 30:
                short_window += 1
        asset_usage[filename] = {
            "sha256": selected_asset_hashes[filename],
            "source_material_family": ASSET_SOURCE_FAMILY[filename],
            "scenes_used": sorted({f"{row['variant']}:{row['scene_id']}" for row in occurrences}),
            "scene_count": len({f"{row['variant']}:{row['scene_id']}" for row in occurrences}),
            "occurrence_count": len(occurrences),
            "cumulative_screen_seconds": round(asset[filename], 3),
            "adjacent_source_asset_reuse_count": sum(bool(row["adjacent_source_asset_reuse"]) for row in occurrences),
            "short_window_recurrence_30s_count": short_window,
            "semantic_purposes": sorted({str(row["semantic_purpose"]) for row in occurrences}),
            "occurrences": occurrences,
            "prior_recent_video_reuse": "KNOWN_PARENT_TREASURY_CANDIDATE" if filename in {
                PHOTO_CFTC, PHOTO_TREASURY, PHOTO_FED, ROWS, SCHEDULE, FED_NOTE,
                TREASURY_REMARKS, FED_FIG1, FED_FIG3, FED_FIG4, FED_FSR,
            } else "NEW_TO_THIS_TREASURY_REPAIR_LINE",
        }

    family_usage: dict[str, Any] = {}
    for name, occurrences in sorted(family_occurrences.items()):
        family_usage[name] = {
            "cumulative_screen_seconds": round(source_family[name], 3),
            "assets": sorted({str(row["asset"]) for row in occurrences}),
            "scenes_used": sorted({f"{row['variant']}:{row['scene_id']}" for row in occurrences}),
            "occurrence_count": len(occurrences),
        }
    return {
        "schema": "contentops.v2.serialized_render_dependency_manifest.v3", "task_id": TASK_ID, "story_id": JOB_ID,
        "total_screen_seconds": round(total, 3), "selected_asset_hashes": dict(selected_asset_hashes),
        "asset_screen_seconds": {key: round(value, 3) for key, value in sorted(asset.items())},
        "source_material_family_screen_seconds": {key: round(value, 3) for key, value in sorted(source_family.items())},
        "presentation_grammar_screen_seconds": {key: round(value, 3) for key, value in sorted(presentation.items())},
        "purpose_screen_seconds": {key: round(value, 3) for key, value in sorted(purpose.items())},
        "asset_usage": asset_usage,
        "source_material_family_usage": family_usage,
        "per_scene": per_scene, "external_runtime_fetches": 0, "generated_person_media": 0,
        "taxonomy_separation": {
            "source_material_family": "Actual source provenance/semantic universe only.",
            "presentation_grammar": "Layout/composition vocabulary only; never counted as source-material diversity.",
        },
        "dependency_proof_level": "DECLARATIVE_STORYBOARD_PLUS_EXACT_SERIALIZABLE_ASSET_REFERENCES; serialized-props and actual-file observations are attached by the runner",
    }


def validate_audio_freeze(observed: Mapping[str, str], chatterbox_sha256: str) -> dict[str, Any]:
    errors = [f"frozen_audio_hash_mismatch:{key}" for key, expected in FROZEN_AUDIO_SHA256.items() if observed.get(key) != expected]
    if chatterbox_sha256 != CHATTERBOX_DIAGNOSTIC_SHA256:
        errors.append("chatterbox_diagnostic_hash_mismatch")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "frozen_audio_sha256": dict(observed), "chatterbox_diagnostic_sha256": chatterbox_sha256,
            "new_tts_synthesis": 0, "voice_bakeoff": False, "build_tts_selection": "UNRESOLVED_AFTER_FROZEN_KOKORO_AB"}
