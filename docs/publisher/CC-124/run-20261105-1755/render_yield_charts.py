"""Render the MAX-selected yield visuals from their exact admitted CSV rows."""
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import csv
import json
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart, validate_editorial_data_chart

OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-gold-yields-20261105-e")
request = json.loads((OP / "desktop_request_visual-edit.json").read_bytes())
decision = json.loads((OP / "desktop_response_visual-edit.json").read_bytes())["output"]
docs = request["governed_input"]["source_packet"]["source_pack"]
series = {}
for kind, column in [("nominal", "10 Yr"), ("real", "10 YR")]:
    path = OP / "source-editions-treasury" / (kind + ".csv")
    rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
    rows.sort(key=lambda r: datetime.strptime(r["Date"], "%m/%d/%Y"))
    doc = next(d for d in docs if d["document_id"] == "cc124-treasury-" + kind + "-20261104")
    points = []
    for row in rows:
        date = datetime.strptime(row["Date"], "%m/%d/%Y").date().isoformat()
        excerpt = date + " " + row[column]
        assert excerpt in doc["canonical_content_text"]
        operand = {"document_id": doc["document_id"], "source_content_sha256": sha256(doc["canonical_content_text"].encode()).hexdigest(),
            "support_excerpt": excerpt, "value_text": row[column], "metric": kind + " 10-year Treasury par yield",
            "unit": "Percent", "source_period_text": date, "prepared_period": date,
            "period_basis": {"kind": "EXACT_OFFICIAL_CSV_DATE_ROW", "source_column": column,
                "source_file_sha256": sha256(path.read_bytes()).hexdigest()}}
        points.append({"period": date, "value": float(Decimal(row[column])), "transform": "IDENTITY", "scale": 1,
                       "observation_kind": "REPORTED_ACTUAL", "inputs": [operand]})
    assert len(points) == 212 and points[-1]["period"] == "2026-11-04"
    series[kind] = {"series_id": "US_TREASURY_10Y_" + kind.upper(),
                    "name": "Nominal 10-year" if kind == "nominal" else "Real 10-year (TIPS)", "points": points}

assets = []
for choice in decision["charts"]:
    form = choice["data_spec"]["chart_form"]
    base = {"asset_id": choice["asset_id"], "question": choice["question"],
        "placement_after": choice["placement_after"],
        "destination_subset": [k for k, ids in decision["channel_media"].items() if choice["asset_id"] in ids],
        "source_caption": "U.S. Department of the Treasury. Independent chart: Capital Chronicle.",
        "source_vintage_note": "Downloaded official daily history. No first-print claim; no 5 November close included.",
        "missingness": "212 matching published observation dates; weekends and market holidays are absent. No values filled or interpolated."}
    if form == "line":
        packet = {**base, "chart_type": "line", "title": "Two different 10-year yields",
            "subtitle": "Official daily par yields · 2 Jan–4 Nov 2026", "unit": "Percent",
            "series": [series["nominal"], series["real"]],
            "caption": "Treasury's 10-year nominal and real par yield estimates on matching dates. The latest observations are 4.90% and 2.64% on 4 November 2026.",
            "alt_text": "Two lines show nominal and real 10-year Treasury par yields from 2 January through 4 November 2026, ending at 4.90 percent and 2.64 percent. These are daily estimates, not live quotes."}
    elif form == "horizontal_diverging_bar":
        comparisons = []
        for kind in ["nominal", "real"]:
            latest, previous = series[kind]["points"][-1], series[kind]["points"][-2]
            value = (Decimal(str(latest["value"])) - Decimal(str(previous["value"]))) * 100
            comparisons.append({"period": "Nominal 10-year" if kind == "nominal" else "Real 10-year (TIPS)",
                "reference_period": "2026-11-03/2026-11-04", "value": float(value),
                "transform": "DIFFERENCE", "scale": 100, "observation_kind": "REPORTED_ACTUAL",
                "inputs": [latest["inputs"][0], previous["inputs"][0]]})
        packet = {**base, "chart_type": form, "title": "The nominal yield fell more",
            "subtitle": "Change from 3 to 4 Nov 2026 · daily observations", "unit": "Basis points",
            "series": [{"series_id": "TEN_YEAR_DAILY_YIELD_CHANGE", "name": "Daily change", "points": comparisons}],
            "value_label_decimals": 0,
            "caption": "From 3 to 4 November, the nominal 10-year par yield fell 5 basis points and the real 10-year yield fell 1 basis point. A basis point is 0.01 percentage point.",
            "alt_text": "Two bars compare the latest daily decline: 5 basis points for the nominal 10-year yield, and 1 basis point for the real 10-year yield. Zero is the baseline."}
    else:
        raise ValueError("Unsupported MAX-selected form: " + form)
    asset = build_editorial_data_chart(packet, docs, output_dir=OP)
    validate_editorial_data_chart(asset, docs)
    assets.append(asset)
result = {"operation_id": "cc124-gold-yields-20261105-e", "visual_request_sha256": request["request_sha256"],
          "media_assets": assets, "pixel_review": "PENDING_ACTUAL_IMAGE_INSPECTION"}
path = OP / "media_assets/yield-chart-assets-unreviewed.json"
path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"manifest_path": str(path), "assets": [{k: a[k] for k in ["asset_id", "path", "sha256", "width", "height"]} for a in assets]}))
