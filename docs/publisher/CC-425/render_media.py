"""Render a source-separated CPI comparison through the existing chart owner."""
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.cpi_reaction_page_v1 import tables, digest
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_editorial_data_chart, validate_source_value_chart,
)

OP = Path(r"C:\Users\bullw\AppData\Local\CapitalChronicle\ContentOps\editorial-previews\cc425-cpi-reaction-history-20261111-v1")
OUT = Path(__file__).resolve().parent


def main():
    source = json.loads((OP / "editorial_media_plan_required.json").read_bytes())["source_pack"][0]
    projection = source["cpi_reaction_page"]
    original = tables(source["canonical_content_text"])[4]
    rows = original.splitlines()[2:]
    selected = {}
    for index, row in enumerate(rows):
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if cells[:2] == ["CPI_HEADLINE_MOM", "investing"] and cells[3:5] == ["XAUUSD", "HISTDATA:XAUUSD"]:
            selected[cells[2], cells[5]] = (index, row, cells)
    periods = [("5m", "5 minutes"), ("30m", "30 minutes"),
               ("session_close", "Close"), ("next_session_close", "Next close")]
    series = []
    for bucket, label in (("HOT", "Hot: n=4; next close n=3"), ("COOL", "Cool: n=3")):
        points = []
        for horizon, period in periods:
            index, row, cells = selected[bucket, horizon]
            token = cells[7]
            operand = {"document_id": source["document_id"], "support_excerpt": row,
                "value_text": token, "metric": "Mean", "unit": "percent",
                "source_period_text": horizon, "prepared_period": period,
                "source_content_sha256": source["canonical_content_sha256"],
                "period_basis": {"basis": "CC425_EXACT_TABLE_CELL", "row_index": index,
                    "column_index": 7, "source_table_sha256": digest(original)}}
            points.append({"period": period, "value": float(token[:-1]), "transform": "IDENTITY",
                "observation_kind": "REPORTED_ACTUAL", "inputs": [operand]})
        series.append({"name": label, "points": points})
    packet = {"asset_id": "cpi-gold-horizons-5aec0a3da914-v1", "chart_type": "grouped_bar",
        "title": "Gold: the first move can differ from the close",
        "question": "How did gold's mean move change across the four horizons?",
        "placement_after": "The first move and the close",
        "unit": "percent", "series": series, "value_label_decimals": 4,
        "source_caption": "Capital Chronicle calculations. Investing headline CPI forecast buckets; HistData gold/USD, January–December 2024.\nDescriptive means (%); hot n=4 (next close n=3), cool n=3. Samples and sources stay separate.",
        "caption": "Mean gold changes in the HistData sample, January–December 2024, grouped by the Investing headline CPI forecast. Hot: four observations, three at the next close; cool: three. Descriptive changes around releases.",
        "alt_text": "Gold's mean changes across four release horizons, separated into hot and cool headline CPI buckets. Cool-print means are negative early and positive at the close; next-close sample counts differ.",
        "cpi_reaction_source": {k: projection[k] for k in ("record_id", "export_bytes_sha256", "source_body_sha256")}}
    asset = build_editorial_data_chart(packet, [source], output_dir=OUT / "media")
    validate_source_value_chart(asset, [source])
    assets = [asset]
    (OUT / "rendered-assets.json").write_text(json.dumps(assets, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": asset["path"], "sha256": asset["sha256"],
        "source_export_sha256": projection["export_bytes_sha256"], "computed_values": asset["computed_values"]}))


if __name__ == "__main__":
    main()
