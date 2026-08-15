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


TASK_ID = "TASK_CONTENTOPS_V2_TREASURY_SHORT_LONGFORM_VISUAL_MATERIAL_RICHNESS_REPAIR_V1"
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


def beat(layout: str, family: str, purpose: str, *, asset: str | None = None,
         label: str = "", detail: str = "", focus: str = "center") -> dict[str, Any]:
    return {"layout": layout, "family": family, "purpose": purpose, "asset": asset,
            "label": label, "detail": detail, "focus": focus}


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
FED_FSR = "fed-fsr-2026-page-38.png"


def _photo(asset: str, label: str, detail: str, purpose: str = "institutional_context", focus: str = "center") -> dict[str, Any]:
    return beat("photo_full", "documentary_photo", purpose, asset=asset, label=label, detail=detail, focus=focus)


def _doc(asset: str, label: str, detail: str, purpose: str = "source_evidence", crop: bool = False, focus: str = "center") -> dict[str, Any]:
    return beat("document_crop" if crop else "document_full", "primary_document", purpose, asset=asset, label=label, detail=detail, focus=focus)


def _figure(asset: str, label: str, detail: str, purpose: str = "source_figure", crop: bool = False, focus: str = "center") -> dict[str, Any]:
    return beat("figure_crop" if crop else "figure_full", "primary_source_figure", purpose, asset=asset, label=label, detail=detail, focus=focus)


def _native(layout: str, family: str, label: str, detail: str, purpose: str) -> dict[str, Any]:
    return beat(layout, family, purpose, label=label, detail=detail)


POSITION = lambda label, detail: _native("position_chart", "native_data", label, detail, "cftc_position_comparison")
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


def material_plan(scenes: Sequence[Mapping[str, Any]], durations: Mapping[str, float]) -> dict[str, list[dict[str, Any]]]:
    """Split each frozen narration segment into equal 2–4 second material beats."""
    result: dict[str, list[dict[str, Any]]] = {}
    for scene in scenes:
        scene_id = str(scene["scene_id"])
        duration = float(durations[scene_id])
        recipe = RECIPES.get(scene_id)
        if not recipe:
            raise KeyError(f"missing_material_recipe:{scene_id}")
        count = max(2, round(duration / 3.4))
        beat_duration = duration / count
        if not 2.0 <= beat_duration <= 4.0:
            raise ValueError(f"microbeat_duration_out_of_range:{scene_id}:{beat_duration}")
        beats: list[dict[str, Any]] = []
        prior_asset: str | None = None
        abstract_run = 0.0
        for index in range(count):
            recipe_index = index % len(recipe)
            candidate = recipe[recipe_index]
            for offset in range(len(recipe)):
                trial = recipe[(recipe_index + offset) % len(recipe)]
                same_asset = bool(trial.get("asset") and trial.get("asset") == prior_asset)
                too_abstract = not trial.get("asset") and abstract_run + beat_duration > 10.5
                if not same_asset and not too_abstract:
                    candidate = trial
                    break
            row = dict(candidate)
            start = index * beat_duration
            end = duration if index == count - 1 else (index + 1) * beat_duration
            row.update({"beat_id": f"{scene_id}_B{index + 1:02d}", "start_seconds": round(start, 6),
                        "end_seconds": round(end, 6), "duration_seconds": round(end - start, 6)})
            beats.append(row)
            prior_asset = str(row["asset"]) if row.get("asset") else None
            abstract_run = 0.0 if row.get("asset") else abstract_run + beat_duration
        result[scene_id] = beats
    return result


def validate_material_plan(plan: Mapping[str, Sequence[Mapping[str, Any]]], selected_asset_hashes: Mapping[str, str]) -> dict[str, Any]:
    errors: list[str] = []
    family_seconds: Counter[str] = Counter()
    asset_seconds: Counter[str] = Counter()
    total = 0.0
    real_source_seconds = 0.0
    longest_abstract_run = 0.0
    for scene_id, beats in plan.items():
        if not beats:
            errors.append(f"empty_scene:{scene_id}")
            continue
        abstract_run = 0.0
        prior_asset: str | None = None
        for row in beats:
            duration = float(row["duration_seconds"])
            total += duration
            family = str(row["family"])
            asset = row.get("asset")
            family_seconds[family] += duration
            if not 1.99 <= duration <= 4.01:
                errors.append(f"microbeat_out_of_range:{row['beat_id']}:{duration}")
            if asset:
                if asset not in selected_asset_hashes:
                    errors.append(f"asset_not_selected:{row['beat_id']}:{asset}")
                asset_seconds[str(asset)] += duration
                real_source_seconds += duration
                abstract_run = 0.0
                if asset == prior_asset:
                    errors.append(f"consecutive_asset_reuse:{row['beat_id']}:{asset}")
            else:
                abstract_run += duration
                longest_abstract_run = max(longest_abstract_run, abstract_run)
            prior_asset = str(asset) if asset else None
    if total <= 0:
        errors.append("no_screen_time")
    if total and real_source_seconds / total < 0.38:
        errors.append(f"insufficient_real_source_screen_time:{real_source_seconds / total:.3f}")
    if len(family_seconds) < 8:
        errors.append(f"insufficient_material_families:{len(family_seconds)}")
    if longest_abstract_run > 12.1:
        errors.append(f"prolonged_abstract_run:{longest_abstract_run:.3f}")
    must_use = ({PHOTO_CFTC, PHOTO_TREASURY, PHOTO_FED, ROWS, SCHEDULE, FED_NOTE, FED_FIG1, FED_FIG3, FED_FIG4, FED_FSR}
                if total > 300 else {PHOTO_CFTC, ROWS, FED_FIG3, FED_FIG4, FED_FSR})
    missing = sorted(must_use - set(asset_seconds))
    if missing:
        errors.append(f"must_use_assets_absent:{','.join(missing)}")
    return {
        "status": "PASS" if not errors else "FAIL", "errors": errors, "total_seconds": round(total, 3),
        "real_source_seconds": round(real_source_seconds, 3),
        "real_source_share": round(real_source_seconds / total, 4) if total else 0,
        "longest_abstract_run_seconds": round(longest_abstract_run, 3),
        "family_seconds": {key: round(value, 3) for key, value in sorted(family_seconds.items())},
        "asset_seconds": {key: round(value, 3) for key, value in sorted(asset_seconds.items())},
    }


def dependency_manifest(plans: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]], selected_asset_hashes: Mapping[str, str]) -> dict[str, Any]:
    family: Counter[str] = Counter()
    asset: Counter[str] = Counter()
    purpose: Counter[str] = Counter()
    per_scene: dict[str, Any] = {}
    total = 0.0
    for variant, plan in plans.items():
        for scene_id, beats in plan.items():
            scene_families: Counter[str] = Counter()
            scene_assets: Counter[str] = Counter()
            for row in beats:
                duration = float(row["duration_seconds"])
                total += duration
                family[str(row["family"])] += duration
                purpose[str(row["purpose"])] += duration
                scene_families[str(row["family"])] += duration
                if row.get("asset"):
                    asset[str(row["asset"])] += duration
                    scene_assets[str(row["asset"])] += duration
            per_scene[f"{variant}:{scene_id}"] = {
                "duration_seconds": round(sum(float(row["duration_seconds"]) for row in beats), 3),
                "microbeats": len(beats), "families": dict(scene_families), "assets": dict(scene_assets),
            }
    return {
        "schema": "contentops.v2.actual_render_dependency_manifest.v2", "task_id": TASK_ID, "story_id": JOB_ID,
        "total_screen_seconds": round(total, 3), "selected_asset_hashes": dict(selected_asset_hashes),
        "asset_screen_seconds": {key: round(value, 3) for key, value in sorted(asset.items())},
        "family_screen_seconds": {key: round(value, 3) for key, value in sorted(family.items())},
        "purpose_screen_seconds": {key: round(value, 3) for key, value in sorted(purpose.items())},
        "per_scene": per_scene, "external_runtime_fetches": 0, "generated_person_media": 0,
    }


def validate_audio_freeze(observed: Mapping[str, str], chatterbox_sha256: str) -> dict[str, Any]:
    errors = [f"frozen_audio_hash_mismatch:{key}" for key, expected in FROZEN_AUDIO_SHA256.items() if observed.get(key) != expected]
    if chatterbox_sha256 != CHATTERBOX_DIAGNOSTIC_SHA256:
        errors.append("chatterbox_diagnostic_hash_mismatch")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "frozen_audio_sha256": dict(observed), "chatterbox_diagnostic_sha256": chatterbox_sha256,
            "new_tts_synthesis": 0, "voice_bakeoff": False, "build_tts_selection": "UNRESOLVED_AFTER_FROZEN_KOKORO_AB"}
