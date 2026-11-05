"""CC-124 native MAX visual decision and exact retained-source chart preparation.

Local files only. No network, publication, operation-store or core-source mutation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-d")
REQUEST_PATH = ROOT / "desktop_request_visual-edit.json"
RESPONSE_PATH = ROOT / "desktop_response_visual-edit.json"
REQUEST_HASH = "614cb1caef28be561c63bfb2a637f9a2be3d6f6e724a50e5759304fcc6275fdf"
INVOCATION = "/root/native_max_eia_614cb1caef28"
PHOTO_ID = "cc124-archive-texas-refinery-fws"
IDS = {
    "crude": "cc124-eia-crude-106w",
    "gasoline": "cc124-eia-gasoline-106w",
    "changes": "cc124-eia-weekly-product-draws",
    "averages": "cc124-eia-stock-average-gaps",
}


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"EXISTING_ARTIFACT_DIFFERS: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def decision(request: dict) -> dict:
    plans = request["governed_input"]["actual_light_preparation"]["story_plan"]["chart_plan"]
    common = {
        "window_start": "2024-10-25", "window_end": "2026-10-30",
        "frequency": "weekly", "observations": 106, "source_unit": "Thousand Barrels",
        "chart_unit": "Thousand barrels", "transform": "IDENTITY; no resampling or interpolation",
        "observation_kind": "REPORTED_ACTUAL",
        "vintage": "Retained downloaded EIA history; no first-print or historical-PIT claim",
    }
    charts = []
    for key, index, heading, question, why in [
        ("crude", 0, "Crude stocks in context", "Where does the latest crude-stock draw sit in two years of weekly observations?",
         "Shows the modest latest draw beside the much larger movement in the level of commercial crude stocks; prevents a single-week change being mistaken for a structural shortage."),
        ("gasoline", 1, "Gasoline is a different signal", "Does the gasoline-stock history tell the same story as crude?",
         "Shows the distinct gasoline seasonal pattern on its own labelled scale, instead of treating every petroleum inventory as one demand signal."),
    ]:
        source = plans["proposals"][index]
        charts.append({
            "asset_id": IDS[key], "question": question, "why_useful": why,
            "placement_after": heading,
            "data_spec": {**common, "chart_form": "line", "source_id": source["source_id"],
                "series_id": source["series_id"], "metric": source["metric"],
                "source_url": source["source_url"], "source_workbook_sha256": source["source_workbook_sha256"],
                "latest_raw": source["latest_raw"], "latest_cells": source["latest_cells"],
                "previous_raw": source["previous_raw"], "previous_cells": source["previous_cells"],
                "latest_change_thousand_barrels": source["latest_change_raw"],
                "caption_million_barrel_scaling": "Displayed caption equivalence = raw thousand barrels / 1000; the plotted series remains in thousand barrels.",
                "axis_rule": "One independent y-axis; all 106 actual weekly observations; no zero-baseline implication, price overlay or five-year band."},
        })
    charts.extend([
        {"asset_id": IDS["changes"],
         "question": "Which petroleum products had the largest reported weekly draws?",
         "why_useful": "Makes the 3.6-million-barrel distillate draw visibly distinct from the 0.9-million crude and 0.2-million gasoline draws, without inventing a full balance decomposition.",
         "placement_after": "The sharper squeeze is in distillates",
         "data_spec": {"chart_form": "horizontal_diverging_bar", "source_id": "SOURCE_1",
             "source_url": "https://ir.eia.gov/secure/wpsr/summary.txt", "reference_week": "2026-10-30",
             "unit": "Million barrels", "series": [{"product": "Crude (excludes SPR)", "change": -0.9},
                 {"product": "Gasoline", "change": -0.2}, {"product": "Distillate", "change": -3.6}],
             "transform": "Reported rounded changes; sign is negative because the source says inventories decreased; no subtraction of rounded stock levels.",
             "observation_kind": "REPORTED_ACTUAL", "display_precision": 1,
             "comparison_rule": "Zero baseline, same units and precision. Selected products only; not an additive decomposition of the reported total-commercial-petroleum draw."}},
        {"asset_id": IDS["averages"],
         "question": "How far below their five-year averages were the three product inventories?",
         "why_useful": "Distinguishes the reported relative tightness in distillate stocks from the smaller crude and gasoline shortfalls; provides context that weekly flow changes cannot supply.",
         "placement_after": "The sharper squeeze is in distillates",
         "data_spec": {"chart_form": "horizontal_diverging_bar", "source_id": "SOURCE_1",
             "source_url": "https://ir.eia.gov/secure/wpsr/summary.txt", "reference_week": "2026-10-30",
             "unit": "Percent", "series": [{"product": "Crude (excludes SPR)", "gap_percent": -4},
                 {"product": "Gasoline", "gap_percent": -2}, {"product": "Distillate", "gap_percent": -13}],
             "transform": "EIA reported percentage distance from five-year average; below = negative. No implied reconstruction of five-year levels or historical bands.",
             "observation_kind": "REPORTED_ACTUAL", "display_precision": 0,
             "comparison_rule": "Zero baseline; percentage gaps have their own scale, separate from weekly barrel changes."}},
    ])
    return {
        "reader_first_version": "DATA_JOURNALISM_V1",
        "slug": "eia-oil-inventories-distillate-tightness-treasury-yields-november-2026",
        "story_kind": "ANALYSIS", "analysis_scope": "RELEASE_OR_POLICY",
        "editorial_thesis": "The EIA's 4 November report for the week ending 30 October shows a more pronounced distillate squeeze than the small crude and gasoline draws. That can matter for oil-specific scarcity and inflation concerns, but divergent product-supplied measures and a changing refinery balance prevent a simple broad-demand conclusion. Treasury yields are a conditional macro cross-check, not an observed reaction in this evidence.",
        "countercase": "Four-week gasoline product supplied was down 0.4% year on year, while distillate was up 8.7%. Inventories also reflect processing, trade and supply; product supplied is a demand proxy, and one US weekly report cannot establish a persistent global shortage or the cause of a Treasury-yield move.",
        "proposed_section_headings": ["Crude stocks in context", "Gasoline is a different signal", "The sharper squeeze is in distillates", "Read oil alongside Treasury yields"],
        "charts": charts, "contextual_photo_ids": [PHOTO_ID],
        "contextual_photo_placement": {"asset_id": PHOTO_ID, "placement": "After the opening argument, before the first section", "archive_context": True,
            "caption": "Archive context: a coastal Texas oil refinery. Photo: U.S. Fish and Wildlife Service, via Wikimedia Commons (public domain).",
            "capture_date": None, "capture_date_state": "NOT_GIVEN_BY_SOURCE", "supports_current_inventory_claims": False},
        "channel_media": {
            "telegram": [IDS["changes"]], "discord": [IDS["changes"], IDS["averages"]],
            "x": [IDS["changes"]], "linkedin": [IDS["averages"]],
            "facebook_page": [IDS["changes"]], "instagram_business": [IDS["changes"], IDS["averages"]],
            "threads": [IDS["changes"]], "youtube": [IDS["changes"]],
        },
        "rejected_visuals": [
            {"visual": "US10Y yield or oil-price reaction chart", "reason": "No admitted price/yield series or observed market reaction is in the frozen packet; conditional mechanism belongs in prose."},
            {"visual": "Distillate history or invented five-year band", "reason": "The admitted packet has the latest draw and percentage gap, not distillate levels/history or a five-year reference series."},
            {"visual": "A summed petroleum-draw waterfall", "reason": "Selected products omit other components of the total-commercial-petroleum balance; a partial sum would imply a false reconciliation."},
            {"visual": "A mixed inventory/daily-flow/utilization axis", "reason": "Weekly stock changes, barrels per day and percentage utilization measure different things."},
        ],
        "essential_gaps": [],
        "source_limits": ["Release date is 4 November 2026, date only; reference week ends 30 October. Do not infer an intraday release clock.",
            "Historical workbooks are downloaded vintages and do not demonstrate first-print availability. This is a dated release analysis, not a PIT event replay.",
            "The retained set has no distillate level history or current US10Y/oil-price series. Those absent quantities are not claimed or required for the bounded argument.",
            "The archive photograph is contextual; its capture date is not supplied and the Commons upload date is not its capture date."],
        "photo_pixel_review": {"reviewer_invocation_id": INVOCATION, "method": "view_image of exact local asset",
            "sha256": "38f6b090a3ef11a5967e4f7d46fa56a1b7a58cf4bc3edee9fffd32faadd79d4c",
            "findings": "Storage tanks and coastal industrial waterways are clearly visible; relevant archive infrastructure context. No current-stock, current-operation or date claim is inferred."},
        "publication_speed_policy": {"policy": "JIM_DECISION_53", "path": "WRITER_ONE_EDITOR_CHECK_PUBLISH", "all_chart_work_before_text_approval": True},
    }


def main() -> None:
    request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    if request["request_sha256"] != REQUEST_HASH:
        raise ValueError("REQUEST_HASH_CHANGED")
    output = decision(request)
    from live_contentops.native_desktop_editorial_v1 import validate_visual_decision
    validate_visual_decision(output)
    response = {"request_sha256": REQUEST_HASH, "output": output, "invocation_observation": {
        "invocation_id": INVOCATION, "surface": "CODEX_NATIVE_SUBAGENT", "model": None, "reasoning_effort": None,
        "speed": "standard", "configuration_status": "CONFIGURED_NOT_OBSERVED",
        "configuration_authority": "JIM_DECISIONS_20261030_DECISION_16", "configured_model": "gpt-6.1-sol",
        "configured_reasoning_effort": "max", "actual_configuration_unavailable": True,
        "configuration_source": "Frozen native request requested_model/requested_reasoning_effort and parent role assignment; no runtime model/effort telemetry exposed to this child.",
        "observation_source": "Supported collaboration native child task identity /root/native_max_eia_614cb1caef28; this exact child read the governed request and chose the returned visual plan.",
    }}
    write_json(RESPONSE_PATH, response)
    print(json.dumps({"response_path": str(RESPONSE_PATH), "response_file_sha256": sha_file(RESPONSE_PATH), "charts": len(output["charts"])}))


if __name__ == "__main__":
    main()
