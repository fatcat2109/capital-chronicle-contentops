"""Render only the four accepted CC-124 charts from exact retained local sources."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from prepare_eia_visuals import ROOT, REPO, IDS, INVOCATION, sha_file, write_json

sys.path.insert(0, str(REPO))
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_editorial_data_chart, validate_editorial_data_chart,
)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_operand(doc: dict, *, token: str, excerpt: str, metric: str,
                   unit: str, source_period: str, prepared_period: str, basis: dict) -> dict:
    return {"document_id": doc["document_id"], "source_content_sha256": content_hash(doc["canonical_content_text"]),
        "support_excerpt": excerpt, "value_text": token, "metric": metric, "unit": unit,
        "source_period_text": source_period, "prepared_period": prepared_period, "period_basis": basis}


def history_packet(doc: dict, history: dict, chart: dict) -> dict:
    points = []
    lines = doc["canonical_content_text"].splitlines()
    for observation in history["observations"]:
        period = observation["date"]
        raw = observation["raw_value_thousand_barrels"]
        row = next(line for line in lines if line.startswith(period + " | "))
        if row.split(" | ")[1] != str(raw):
            raise ValueError("CANONICAL_HISTORY_ROW_CHANGED")
        points.append({"period": period, "value": raw, "transform": "IDENTITY", "scale": 1,
            "observation_kind": "REPORTED_ACTUAL", "inputs": [source_operand(doc,
                token=str(raw), excerpt=row, metric=history["series_header"], unit="Thousand barrels",
                source_period=period, prepared_period=period,
                basis={"kind": "EXACT_EIA_WORKBOOK_ROW", "series_id": history["sourcekey"],
                    "sheet": history["sheet"], "date_cell": observation["source_date_cell"],
                    "value_cell": observation["source_value_cell"], "source_workbook_sha256": history["sha256"]})]})
    crude = history["sourcekey"] == "WCESTUS1"
    name = "Crude stocks excluding SPR" if crude else "Total gasoline stocks"
    latest = history["observations"][-1]["raw_value_thousand_barrels"]
    return {"asset_id": chart["asset_id"], "chart_type": "line", "question": chart["question"],
        "title": "Two years of US commercial crude stocks" if crude else "Two years of US gasoline stocks",
        "subtitle": "Weekly ending stocks · 25 Oct 2024–30 Oct 2026" + (" · Excludes SPR" if crude else ""),
        "unit": "Thousand barrels", "series": [{"series_id": history["sourcekey"], "name": name, "points": points}],
        "placement_after": chart["placement_after"], "destination_subset": [],
        "source_caption": "U.S. Energy Information Administration · 25 Oct 2024–30 Oct 2026. Independent chart: Capital Chronicle.",
        "caption": f"{name}, 25 October 2024–30 October 2026. Latest: {latest:,} thousand barrels ({latest / 1000:,.3f} million; raw / 1,000).",
        "alt_text": f"Line chart of 106 weekly observations of {name.lower()} from 25 October 2024 to 30 October 2026. The latest level is {latest:,} thousand barrels. The y-axis is in thousand barrels.",
        "missingness": "106 actual weekly observations; contiguous seven-day intervals; no missing values, filled values or interpolation.",
        "source_series_id": history["sourcekey"], "source_workbook_sha256": history["sha256"],
        "source_window": {"start": history["first_date"], "end": history["last_date"]},
        "source_vintage_note": "Downloaded historical vintage; no first-print or historical-PIT claim.",
        "caption_scaling": {"source_unit": "Thousand Barrels", "caption_unit": "Million barrels", "operation": "raw / 1000", "factor": .001, "plot_values_scaled": False}}


def comparison_packet(doc: dict, chart: dict, *, averages: bool) -> dict:
    text = doc["canonical_content_text"]
    period = "For the week ending October 30, 2026"
    products = ["Crude (excl. SPR)", "Gasoline", "Distillate"]
    tokens = ["4%", "2%", "13%"] if averages else ["0.9", "0.2", "3.6"]
    values = [-4, -2, -13] if averages else [-.9, -.2, -3.6]
    unit = "Percent" if averages else "Million barrels"
    points = []
    for product, token, value in zip(products, tokens, values):
        points.append({"period": product, "reference_period": "2026-10-30", "value": value,
            "transform": "IDENTITY", "scale": -1,
            "sign_presentation_reason": "The source reports below the five-year average; below is plotted negative." if averages else "The source reports inventories decreased; a stock draw is plotted negative.",
            "observation_kind": "REPORTED_ACTUAL",
            "inputs": [source_operand(doc, token=token, excerpt=text,
                metric=f"{product}: reported percentage below the five-year average" if averages else f"{product}: reported weekly inventory decrease",
                unit=unit, source_period=period, prepared_period="2026-10-30",
                basis={"kind": "EIA_SUMMARY_DOCUMENT_REFERENCE_WEEK", "week_ending": "2026-10-30", "product": product,
                    "reported_precision": "whole percent" if averages else "one decimal million barrels"})]})
    return {"asset_id": chart["asset_id"], "chart_type": "horizontal_diverging_bar",
        "question": chart["question"], "title": "Distillate stocks sit furthest below average" if averages else "The larger weekly draw was in distillates",
        "subtitle": "Distance below each product's five-year average · Week ending 30 Oct 2026" if averages else "Reported weekly stock changes · Week ending 30 Oct 2026 · Selected products",
        "unit": unit, "series": [{"series_id": "EIA_REPORTED_FIVE_YEAR_AVERAGE_GAPS" if averages else "EIA_REPORTED_WEEKLY_INVENTORY_CHANGES",
            "name": "Reported gap from five-year average" if averages else "Reported weekly inventory changes", "points": points}],
        "value_label_decimals": 0 if averages else 1,
        "placement_after": chart["placement_after"],
        "destination_subset": [key for key, selected in json.loads((ROOT / "desktop_response_visual-edit.json").read_text(encoding="utf-8"))["output"]["channel_media"].items() if chart["asset_id"] in selected],
        "source_caption": "U.S. Energy Information Administration · 4 Nov 2026 report, week ending 30 Oct. Independent chart: Capital Chronicle.",
        "caption": "EIA reported inventories 4% below their five-year average for crude excluding SPR, 2% below for gasoline and 13% below for distillate. This is a percentage comparison, not a barrel-volume comparison." if averages else "EIA reported weekly stock declines of 0.9 million barrels for crude excluding SPR, 0.2 million for gasoline and 3.6 million for distillate. Selected products do not constitute a full decomposition of the total petroleum-stock change.",
        "alt_text": "Horizontal bars show crude inventories 4% below their five-year average, gasoline 2% below and distillate 13% below for the week ending 30 October 2026. All bars share a percentage scale and zero reference." if averages else "Horizontal bars show weekly inventory changes for the week ending 30 October 2026: crude excluding SPR minus 0.9 million barrels, gasoline minus 0.2 million, and distillate minus 3.6 million. All bars share a million-barrel scale and zero reference.",
        "missingness": "Exact reported summary observations only; no missing products inferred, summed, filled or interpolated.",
        "reference_week": "2026-10-30", "release_date": "2026-11-04", "release_date_precision": "DATE_ONLY"}


def main() -> None:
    request = json.loads((ROOT / "desktop_request_visual-edit.json").read_text(encoding="utf-8"))
    decision = json.loads((ROOT / "desktop_response_visual-edit.json").read_text(encoding="utf-8"))["output"]
    docs = request["governed_input"]["source_packet"]["source_pack"]
    by_id = {d["source_id"]: d for d in docs}
    research_root = ROOT / "source-editions-eia"
    research = RetainedSourceResearch(research_root)
    if research.gaps:
        raise ValueError(f"RETAINED_RESEARCH_GAPS: {research.gaps}")
    summary = by_id["SOURCE_1"]
    record = next(r for r in research.records.values() if (r["document"].get("document_id") or r["headline_id"]) == summary["document_id"])
    binding = {"research_root": str(research_root), "research_revision": research.revision,
        "source_capture_hashes": {summary["document_id"]: record["source_capture_sha256"]}}
    write_json(HERE / "eia-retained-chart-source-binding.json", binding)
    history_path = ROOT / "source-captures" / "eia_weekly_history_normalized.json"
    normalized = json.loads(history_path.read_text(encoding="utf-8"))
    import xlrd
    checks = []
    for history in normalized["series"]:
        raw_path = ROOT / "source-captures" / history["filename"]
        if sha_file(raw_path) != history["sha256"]:
            raise ValueError("EIA_WORKBOOK_BYTES_CHANGED")
        workbook = xlrd.open_workbook(str(raw_path))
        sheet = workbook.sheet_by_name(history["sheet"])
        observations = history["observations"]
        if len(observations) != 106 or observations[0]["date"] != "2024-10-25" or observations[-1]["date"] != "2026-10-30":
            raise ValueError("HISTORY_WINDOW_CHANGED")
        for index, observation in enumerate(observations):
            row_num = int(observation["source_value_cell"][1:]) - 1
            raw = sheet.cell_value(row_num, 1)
            observed_date = xlrd.xldate.xldate_as_datetime(sheet.cell_value(row_num, 0), workbook.datemode).date().isoformat()
            if raw != observation["raw_value_thousand_barrels"] or observed_date != observation["date"]:
                raise ValueError("EIA_NORMALIZED_CELL_MISMATCH")
            if index and date.fromisoformat(observation["date"]) - date.fromisoformat(observations[index - 1]["date"]) != timedelta(days=7):
                raise ValueError("EIA_NONCONTIGUOUS_WEEK")
            if observation["value_million_barrels"] != observation["raw_value_thousand_barrels"] / 1000:
                raise ValueError("EIA_SCALE_MISMATCH")
        checks.append({"series_id": history["sourcekey"], "workbook_sha256": history["sha256"], "observations_checked": len(observations),
            "latest_raw": observations[-1]["raw_value_thousand_barrels"],
            "weekly_change_raw": observations[-1]["raw_value_thousand_barrels"] - observations[-2]["raw_value_thousand_barrels"],
            "source_cell_mismatches": 0})
    charts = {c["asset_id"]: c for c in decision["charts"]}
    packets = [history_packet(by_id["SOURCE_2"], normalized["series"][0], charts[IDS["crude"]]),
        history_packet(by_id["SOURCE_3"], normalized["series"][1], charts[IDS["gasoline"]]),
        comparison_packet(summary, charts[IDS["changes"]], averages=False),
        comparison_packet(summary, charts[IDS["averages"]], averages=True)]
    assets = []
    for packet in packets:
        asset = build_editorial_data_chart(packet, docs, output_dir=ROOT,
            retained_source_binding=binding if packet["asset_id"] in {IDS["changes"], IDS["averages"]} else None)
        validate_editorial_data_chart(asset, docs)
        assets.append(asset)
    manifest = {"schema_version": "contentops.cc124_eia_chart_assets.v1", "operation_id": "cc124-next-article-20261105-d",
        "visual_request_sha256": request["request_sha256"], "reviewer_invocation_id": INVOCATION,
        "normalized_data_path": str(history_path), "normalized_data_sha256": sha_file(history_path),
        "source_checks": checks, "media_assets": assets, "pixel_review": {"status": "PENDING_LOCAL_IMAGE_INSPECTION"},
        "public_write_performed": False}
    write_json(ROOT / "media_assets" / "eia-chart-assets-unreviewed.json", manifest)
    print(json.dumps({"manifest": str(ROOT / "media_assets" / "eia-chart-assets-unreviewed.json"),
        "source_checks": checks, "assets": [{"asset_id": a["asset_id"], "path": a["path"], "sha256": a["sha256"], "width": a["width"], "height": a["height"]} for a in assets]}))


if __name__ == "__main__":
    main()
