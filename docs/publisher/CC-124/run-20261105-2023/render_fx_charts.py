"""Render the accepted MAX FX plan using exact admitted source operands; no public action."""
from decimal import Decimal, localcontext
from hashlib import sha256
from pathlib import Path
import json
import re
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart, validate_editorial_data_chart

OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
request = json.loads((OP / "desktop_request_visual-edit.json").read_bytes())
decision = json.loads((OP / "desktop_response_visual-edit.json").read_bytes())["output"]
recovered = json.loads((OP / "editorial_media_plan_required.json").read_bytes())
docs = recovered["source_pack"]
assert {d["document_id"] for d in docs} == {"cc124-treasury-nominal-20261104", "cc124-bls-november-calendar", "cc124-fed-h10-20261102-fx"}
summary = json.loads((Path(__file__).parent / "fx-official-data-summary.json").read_bytes())
for name, expected in summary["source_hashes"].items():
    assert sha256((OP / "source-editions-fx" / name).read_bytes()).hexdigest() == expected, name
for d in docs:
    name = {"cc124-treasury-nominal-20261104": "nominal-admission.json",
        "cc124-bls-november-calendar": "bls-admission.json", "cc124-fed-h10-20261102-fx": "fed-h10-admission.json"}[d["document_id"]]
    admitted = json.loads((OP / "source-editions-fx" / name).read_bytes())["official_source_documents"][0]
    assert d["canonical_content_sha256"] == sha256(d["canonical_content_text"].encode()).hexdigest()
    assert all(span in admitted["canonical_content_text"] for span in d["canonical_content_text"].split("\n\n"))
fx = next(d for d in docs if d["document_id"] == "cc124-fed-h10-20261102-fx")
treasury = next(d for d in docs if d["document_id"] == "cc124-treasury-nominal-20261104")
dates = [f"2026-10-{d}" for d in range(26, 31)]
fx_text = fx["canonical_content_text"]
header = "| COUNTRY | CURRENCY | Oct. 26 | Oct. 27 | Oct. 28 | Oct. 29 | Oct. 30 |"
assert header in fx_text


def fx_row(label, currency):
    match = re.search(r"\| " + re.escape(label) + r" \| " + currency + r" \|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|", fx_text)
    assert match
    return [v.strip() for v in match.groups()], match.group(0)


def operand(doc, value, unit, date, excerpt, metric, basis):
    assert excerpt in doc["canonical_content_text"] and value in excerpt
    return {"document_id": doc["document_id"],
        "source_content_sha256": sha256(doc["canonical_content_text"].encode()).hexdigest(),
        "support_excerpt": excerpt, "value_text": value, "metric": metric, "unit": unit,
        "source_period_text": date if doc is treasury else "Oct. " + date[-2:],
        "prepared_period": date, "period_basis": basis}


eur_values, eur_row = fx_row("*EMU MEMBERS", "EURO")
jpy_values, jpy_row = fx_row("JAPAN", "YEN")
fx_series = []
with localcontext() as ctx:
    ctx.prec = 40
    for sid, name, values, row, unit, inverse in [
        ("USD_VS_EUR", "Dollar vs euro", eur_values, eur_row, "USD per EUR", True),
        ("USD_VS_JPY", "Dollar vs yen", jpy_values, jpy_row, "JPY per USD", False)]:
        points = []
        for i, date in enumerate(dates):
            ops = []
            for j in ([0, i] if inverse else [i, 0]):
                # Header and exact row stay contiguous in the admitted canonical text.
                left, right = fx_text.index(header), fx_text.index(row) + len(row)
                excerpt = fx_text[left:right]
                ops.append(operand(fx, values[j], unit, dates[j], excerpt, name + " observed reference quote",
                    {"kind": "EXACT_OFFICIAL_TABLE_COLUMN", "period_index": j,
                     "source_column": "Oct. " + dates[j][-2:], "source_row": row,
                     "source_table_header": header, "series_periods": dates,
                     "source_release_date": "2026-11-02"}))
            # Reciprocal normalized change simplifies exactly to baseline/current - 1.
            # PERCENT_CHANGE supports this operand order directly; no synthetic source value.
            numerator, denominator = (Decimal(values[0]), Decimal(values[i])) if inverse else (Decimal(values[i]), Decimal(values[0]))
            exact = (numerator / denominator - 1) * 100
            points.append({"period": date, "value": float(exact), "value_decimal": str(exact),
                "transform": "PERCENT_CHANGE", "scale": 1, "observation_kind": "REPORTED_ACTUAL",
                "inputs": ops, "calculation_formula": "100 * (EURUSD_baseline / EURUSD_current - 1)" if inverse
                    else "100 * (USDJPY_current / USDJPY_baseline - 1)",
                "transformation_explanation": "Exact normalized reciprocal EUR-per-USD change; inputs remain observed USD-per-EUR quotes." if inverse
                    else "Normalized observed JPY-per-USD change."})
        fx_series.append({"series_id": sid, "name": name, "points": points})

yield_points = []
for date in dates:
    match = re.search(re.escape(date) + r" ([0-9]+\.[0-9]+)", treasury["canonical_content_text"])
    assert match
    value = match[1]
    yield_points.append({"period": date, "value": float(Decimal(value)), "transform": "IDENTITY", "scale": 1,
        "observation_kind": "REPORTED_ACTUAL", "inputs": [operand(treasury, value, "Percent", date,
            match.group(0), "Nominal 10-year Treasury par yield",
            {"kind": "EXACT_OFFICIAL_CSV_DATE_ROW", "source_column": "10 Yr",
             "source_file_sha256": "653c51f4ab54bc97634b53793ad5f362e7822c96f9535752cc3bc5c9d0cc05cc"})]})

assets = []
for choice in decision["charts"]:
    base = {"asset_id": choice["asset_id"], "question": choice["question"],
        "placement_after": choice["placement_after"],
        "destination_subset": [d for d, ids in decision["channel_media"].items() if choice["asset_id"] in ids],
        "source_vintage_note": "Dated official observations, 26-30 October 2026; not live executable prices.",
        "missingness": "All five dates present. No imputation, additional dates or fitted relationship."}
    if choice["asset_id"] == "cc124-fx-dollar-directions":
        packet = {**base, "chart_type": "direct_labelled_two_line", "title": "One dollar, two currency directions",
            "subtitle": "Fed reference rates · 26-30 Oct 2026 · 26 Oct = 0%", "unit": "Percent change from 26 Oct",
            "series": fx_series, "history_axis_limits": [-0.16, 0.48], "value_label_decimals": 2,
            "endpoint_label_decimals": 2,
            "source_caption": "Source: Federal Reserve H.10, released 2 November 2026. Calculations/chart: Capital Chronicle.",
            "caption": "Above zero: stronger dollar. Below zero: weaker dollar. Euro quotes are inverted to EUR per USD before normalization; yen uses JPY per USD. Endpoint changes: +0.13% versus euro; -0.07% versus yen.",
            "alt_text": "Five dated dollar changes against the euro and yen from October 26 to 30, 2026. The dollar ends 0.13 percent stronger versus the euro and 0.07 percent weaker versus the yen. Both start at zero; rates are dated Fed references."}
    elif choice["asset_id"] == "cc124-fx-matched-treasury":
        packet = {**base, "chart_type": "line", "title": "Yields fell overall, with a midweek rise",
            "subtitle": "US Treasury nominal 10-year par yield · 26-30 Oct 2026", "unit": "Percent",
            "series": [{"series_id": "US10Y_PAR", "name": "Nominal 10-year: 5.00% to 4.94%", "points": yield_points}],
            "source_caption": "Source: U.S. Department of the Treasury. Independent chart: Capital Chronicle.",
            "caption": "The nominal 10-year par yield fell from 5.00% to 4.94%, a six-basis-point decline. Same calendar dates do not establish synchronized pricing or causation.",
            "alt_text": "Treasury nominal 10-year par yields are 5.00, 4.99, 5.05, 4.98 and 4.94 percent on October 26 to 30 respectively. The endpoint decline is six basis points."}
    else:
        raise ValueError("Unexpected MAX asset identity")
    # Preserve earlier immutable packet/PNG revisions while keeping MAX's asset IDs.
    asset = build_editorial_data_chart(packet, docs, output_dir=OP / "media_assets/fx-source-bound-r2")
    validate_editorial_data_chart(asset, docs)
    assets.append(asset)
manifest = OP / "media_assets/fx-chart-assets-unreviewed.json"
bound_docs_path = OP / "media_assets/fx-chart-source-documents.json"
bound_docs_path.write_text(json.dumps(docs, indent=2) + "\n", encoding="utf-8")
manifest.write_text(json.dumps({"operation_id": OP.name, "visual_request_sha256": request["request_sha256"],
    "media_assets": assets, "pixel_review": "PENDING_ACTUAL_IMAGE_INSPECTION",
    "source_documents_path": str(bound_docs_path),
    "source_documents_sha256": sha256(bound_docs_path.read_bytes()).hexdigest(),
    "recovered_source_packet_request_sha256": recovered["request_sha256"],
    "formula_owner_change_required": False,
    "formula_binding": "Existing PERCENT_CHANGE with observed EURUSD baseline numerator and current denominator exactly represents normalized inverse dollar change.",
    "renderer_limits": "FX endpoint labels use the owner-supported signed two-decimal inside-edge repair. Treasury endpoints are explicit in the series label and caption."}, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"manifest_path": str(manifest), "manifest_sha256": sha256(manifest.read_bytes()).hexdigest(),
    "assets": [{k: a[k] for k in ["asset_id", "path", "sha256", "width", "height"]} for a in assets]}))
