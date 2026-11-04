"""Render this run's exact MAX choices with the existing chart owner."""
import json
from pathlib import Path

from live_contentops.official_release_history_v1 import history_chart_packet
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_editorial_data_chart, validate_source_value_chart,
)

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261104-a")
source = json.loads((ROOT / "editorial_media_plan_required.json").read_bytes())["source_pack"]
history = json.loads((ROOT / "official_release_history_v1.json").read_bytes())
decision = json.loads((ROOT / "desktop_response_visual-edit.json").read_bytes())["output"]
binding = json.loads((ROOT / "sector-chart-source-binding.json").read_bytes())
assets = []
names = {
    "payroll_first_print_trend": "NFP_PAYROLL_CHANGE",
    "unemployment_first_print_trend": "UNEMPLOYMENT_RATE",
    "earnings_first_print_trend": "AHE_MOM",
}
for chart in decision["charts"]:
    spec, aid = chart["data_spec"], chart["asset_id"]
    if aid == "september_sector_breakdown":
        doc, points = source[0], []
        for row in spec["rows"]:
            points.append({"period": row["label"], "value": row["value"],
                "observation_kind": "REPORTED_ACTUAL", "inputs": [{
                    "document_id": doc["document_id"], "support_excerpt": doc["canonical_content_text"],
                    "value_text": str(row["value"]), "source_period_text": "Sept. 2026",
                    "source_content_sha256": doc["canonical_content_sha256"],
                    "metric": "Seasonally adjusted August to September payroll change, " + row["label"],
                    "unit": "thousands of persons", "prepared_period": "2026-09",
                    "period_basis": {"basis": "BLS_TABLE_B1_PRINTED_AUGUST_TO_SEPTEMBER_CHANGE_COLUMN",
                        "capture_sha256": spec["source_raw_sha256"],
                        "column_header": "Change from: Aug.2026 - Sept.2026"}}]})
        packet = {"asset_id": aid, "chart_type": "horizontal_diverging_bar",
            "title": "Private hiring offset government job losses",
            "subtitle": "September 2026: +29,000 total payroll jobs; +46,000 private jobs, -17,000 government jobs.",
            "question": chart["question"], "placement_after": chart["placement_after"],
            "unit": "thousands of persons", "series": [{"name": "September payroll change", "points": points}],
            "value_label_decimals": 0,
            "source_caption": "Source: BLS, October 2, 2026, Table B-1. Seasonally adjusted initial estimates. Disjoint groups: 18 + 28 - 17 = 29 thousand.",
            "caption": spec["caption"],
            "alt_text": "September payroll change in thousands: goods-producing +18; private service-providing +28; government -17. Total nonfarm +29."}
    else:
        name = names[aid]
        titles = {"NFP_PAYROLL_CHANGE": "September payrolls: a small gain of 29,000",
            "UNEMPLOYMENT_RATE": "Unemployment was 4.2% in September",
            "AHE_MOM": "Monthly pay growth eased to 0.1%"}
        packet = history_chart_packet(history, series_names=[name], asset_id=aid,
            title=titles[name], question=chart["question"], placement_after=chart["placement_after"])
        packet["caption"] = spec["caption"]
        packet["subtitle"] = {"NFP_PAYROLL_CHANGE": "Monthly change in nonfarm payroll jobs. Seasonally adjusted initial estimates.",
            "UNEMPLOYMENT_RATE": "Civilian unemployment rate, seasonally adjusted. October 2025 stays missing.",
            "AHE_MOM": "Nominal average hourly earnings, all private nonfarm employees; seasonally adjusted."}[name]
        packet["series"][0]["name"] = {"NFP_PAYROLL_CHANGE": "Nonfarm payroll change",
            "UNEMPLOYMENT_RATE": "Civilian unemployment rate", "AHE_MOM": "Average hourly earnings, monthly change"}[name]
        packet["source_caption"] = "Source: BLS dated first releases. October 2024–September 2026; each month retains its first print."
        if name == "AHE_MOM":
            packet["source_caption"] += " October 2025 and July 2026 rates are calculated from published levels, rounded to one decimal."
        if name == "UNEMPLOYMENT_RATE":
            packet["source_caption"] += " October 2025 is a gap; no interpolation."
            packet["history_axis_limits"] = [0, 5]
        else:
            packet["chart_type"] = "grouped_bar"
        packet["alt_text"] = spec["caption"]
    packet["destination_subset"] = [d for d, ids in decision["channel_media"].items() if aid in ids]
    asset = build_editorial_data_chart(packet, source, output_dir=ROOT,
        **({"retained_source_binding": binding} if aid == "september_sector_breakdown" else {}))
    validate_source_value_chart(asset, source)
    assets.append(asset)
(ROOT / "rendered-assets.json").write_text(json.dumps(assets, indent=2), encoding="utf-8")
proof = {"assets": [{k: a[k] for k in ("asset_id", "path", "sha256", "width", "height", "computed_values")} for a in assets],
    "validators": "validate_source_value_chart passed for all four", "new_network_requests": 0}
Path(__file__).with_name("chart-build.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
print(json.dumps({"assets": [{k: a[k] for k in ("asset_id", "path", "sha256", "width", "height")} for a in assets],
    "validation": proof["validators"]}))
