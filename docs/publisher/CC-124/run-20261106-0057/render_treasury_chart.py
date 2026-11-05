"""Render the actual MAX choice from the retained official Treasury rows."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart, validate_editorial_data_chart

HERE = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-bitcoin-rates-20261106-h")
decision = json.loads((RUN / "desktop_response_visual-edit.json").read_bytes())["output"]
documents = json.loads((RUN / "editorial_media_plan_required.json").read_bytes())["source_pack"]
doc = next(d for d in documents if d["document_id"] == "cc124-treasury-nominal-20261104")
assert hashlib.sha256(doc["canonical_content_text"].encode()).hexdigest() == doc["canonical_content_sha256"]
choice = decision["charts"][0]
spec = choice["data_spec"]
points = []
values = {}
for match in re.finditer(r"^(2026-\d\d-\d\d) (\d+\.\d+)$", doc["canonical_content_text"], re.M):
    period, value = match.groups()
    if not spec["period_start"] <= period <= spec["period_end"]:
        continue
    assert period not in values
    values[period] = value
    points.append({"period": period, "value": float(value), "transform": "IDENTITY", "scale": 1,
        "observation_kind": "REPORTED_ACTUAL", "inputs": [{"document_id": doc["document_id"],
            "source_content_sha256": doc["canonical_content_sha256"], "support_excerpt": match[0],
            "value_text": value, "metric": spec["metric"], "unit": "Percent", "source_period_text": period,
            "prepared_period": period, "period_basis": {"kind": "EXACT_OFFICIAL_TABLE_OR_DATE_ROW", "source_period": period}}]})
assert len(points) == spec["observation_count"] == 212
assert points[0]["period"] == "2026-01-02" and points[-1]["period"] == "2026-11-04"
change_bp = (Decimal(values["2026-11-04"]) - Decimal(values["2026-11-03"])) * 100
assert change_bp == -5
packet = {"asset_id": choice["asset_id"], "question": choice["question"], "placement_after": choice["placement_after"],
    "destination_subset": [d for d, ids in decision["channel_media"].items() if choice["asset_id"] in ids],
    "title": spec["title"], "subtitle": spec["subtitle"], "unit": "Percent", "chart_type": "line",
    "series": [{"series_id": "US10Y_PAR", "name": "Nominal 10-year; final 4.90%", "points": points}],
    "source_caption": "Source: U.S. Department of the Treasury. Independent chart: Capital Chronicle.",
    "caption": spec["caption"], "alt_text": "Nominal 10-year Treasury par yield, reported daily observations from January 2 to November 4, 2026, ending at 4.90 percent. This is a Treasury series, not Bitcoin performance.",
    "missingness": spec["missingness"], "source_vintage_note": "Retained official observations through 4 November 2026; original capture 5 November. No later points or current-price claim.",
    "value_label_decimals": 2}
asset = build_editorial_data_chart(packet, documents, output_dir=RUN / "media_assets/treasury-chart")
validate_editorial_data_chart(asset, documents)
out = RUN / "media_assets/chart-unreviewed.json"
out.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
checks = {"chart": {k: asset[k] for k in ("asset_id", "path", "sha256", "width", "height")},
    "source_document_id": doc["document_id"], "source_sha256": doc["canonical_content_sha256"],
    "reported_observation_count": len(points), "final_date": points[-1]["period"], "final_value_percent": values["2026-11-04"],
    "previous_value_percent": values["2026-11-03"], "change_basis_points": str(change_bp),
    "pixels_reviewed": False, "new_source_requests": 0}
(HERE / "chart-computation-acceptance.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
print(json.dumps(checks))
