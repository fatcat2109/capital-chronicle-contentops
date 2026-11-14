"""Render the accepted Light plan with the existing source-bound media owners."""
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops.official_release_history_v1 import history_chart_packet
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart
from live_contentops.post_visuals_v1 import build_post_data_card
from live_contentops.published_images_v1 import PublishedImages, _active, fingerprint, near

ROOT = Path(r"C:\Users\bullw\AppData\Local\CapitalChronicle\ContentOps\editorial-previews\cc107-nfp-dated-review-20261114-v1")
sources = json.loads((ROOT / "editorial_media_plan_required.json").read_bytes())["source_pack"]
history = json.loads((ROOT / "official_release_history_v1.json").read_bytes())
assets = []
for name, aid, title, question, placement in [
    ("NFP_PAYROLL_CHANGE", "nfp_review_payroll_history", "The payroll baseline before October",
     "How unusual was the latest jobs print against earlier first releases?", "What the jobs report resolved"),
    ("UNEMPLOYMENT_RATE", "nfp_review_unemployment_history", "The unemployment baseline before October",
     "How did the household survey frame the October result?", "What the jobs report resolved"),
]:
    packet = history_chart_packet(history, series_names=[name], asset_id=aid, title=title,
        question=question, placement_after=placement)
    packet.update(caption="BLS dated first releases, October 2024–September 2026. October's new result is separate; gaps remain gaps.",
        alt_text=title + ". Twenty-four calendar months of first-print BLS observations, with missing periods left as gaps.")
    assets.append(build_editorial_data_chart(packet, sources, output_dir=ROOT / "media"))

doc = next(d for d in sources if d["source_id"] == "SOURCE_3")
points = []
for label in ["Mining and logging", "Construction", "Manufacturing", "Private service-providing"]:
    match = re.search(r"\| " + re.escape(label) + r" \|((?:[^|]*\|){9})", doc["canonical_content_text"])
    if not match:
        raise ValueError("EXACT_OCTOBER_INDUSTRY_ROW_ABSENT:" + label)
    cells = [v.strip() for v in match[1].split("|") if v.strip()]
    token = cells[-1]
    points.append({"period": label, "value": float(token.replace(",", "")), "observation_kind": "REPORTED_ACTUAL",
        "inputs": [{"document_id": doc["document_id"], "support_excerpt": doc["canonical_content_text"],
            "value_text": token, "source_period_text": "Oct. 2026", "source_content_sha256": doc["canonical_content_sha256"],
            "metric": "October seasonally adjusted employment change: " + label, "unit": "thousands of jobs",
            "prepared_period": "2026-10", "period_basis": {"basis": "BLS_TABLE_B1_LAST_CHANGE_COLUMN_SEPT_TO_OCT_2026",
                "original_row": match[0], "native_unit": "thousands of jobs"}}]})
packet = {"asset_id": "nfp_review_october_industries", "chart_type": "grouped_bar",
    "title": "Where October's hiring changed", "question": "Which disjoint industry groups added or lost jobs?",
    "placement_after": "What the jobs report resolved", "unit": "thousands of jobs",
    "series": [{"name": "October monthly change", "points": points}], "value_label_decimals": 0,
    "source_caption": "Source: BLS October 2026 employment report, Table B-1. Selected disjoint groups; not a total.",
    "caption": "October 2026 seasonally adjusted change, in thousands of jobs. Government and other categories are not shown; bars do not form a complete total.",
    "alt_text": "October jobs changes: mining and logging minus one thousand, construction minus three thousand, manufacturing plus nineteen thousand and private services plus one hundred forty-four thousand."}
assets.append(build_editorial_data_chart(packet, sources, output_dir=ROOT / "media"))

doc = sources[0]
series = []
for horizon, label in [("+5m", "08:35 ET"), ("+60m", "09:30 ET")]:
    points = []
    for market, public_label in [("EURUSD", "EUR/USD"), ("USDJPY", "USD/JPY"), ("XAUUSD", "Gold"), ("US500", "US 500 reference"), ("USOIL", "Oil reference")]:
        excerpt = next(line for line in doc["canonical_content_text"].splitlines() if f": {market} observed" in line)
        token = re.search(re.escape(horizon) + r": (-?\d+(?:\.\d+)?)%", excerpt)[1]
        points.append({"period": public_label, "value": float(token), "observation_kind": "ESTIMATE", "inputs": [{
            "document_id": doc["document_id"], "support_excerpt": excerpt, "source_content_sha256": doc["canonical_content_sha256"],
            "value_text": token, "source_period_text": "2026-11-06", "prepared_period": horizon,
            "metric": market + " computed return", "unit": "percent", "period_basis": {
                "basis": "MAIN_COMPUTED_EVENT_RETURN", "event_id": "US_NFP_20261106", "baseline_utc": "2026-11-06T13:30:00Z"}}]})
    series.append({"name": label, "points": points})
packet = {"asset_id": "nfp_review_first_hour_reactions", "chart_type": "grouped_bar",
    "title": "The first observed response", "question": "Did the first observed response last through the first hour?",
    "placement_after": "What moved, and when", "unit": "percent", "series": series, "value_label_decimals": 2,
    "source_caption": "Capital Chronicle model estimate. Changes from November 6, 2026, 08:30 ET; reference series, not execution returns.",
    "caption": "Capital Chronicle model estimate: computed reference-series changes from the November 6, 2026 release baseline. Co-movement does not establish causation. No first-day observation is implied.",
    "alt_text": "Capital Chronicle model estimate compares five-minute and sixty-minute changes: the euro, gold and the US 500 reference were lower; dollar-yen was higher; oil reversed its initial rise."}
assets.append(build_editorial_data_chart(packet, sources, output_dir=ROOT / "media"))

doc = next(d for d in sources if d["source_id"] == "SOURCE_2")
fact = "Total nonfarm payroll employment rose by 165,000 in October, and the unemployment rate changed little at 4.1 percent, the U.S. Bureau of Labor Statistics reported today."
assert fact in doc["canonical_content_text"]
card = build_post_data_card({"title": "October jobs: the release result", "substack_body_markdown": fact},
    [{"claim_id": "official-october-release", "claim_text": fact, "support_excerpt": fact, "source_id": doc["source_id"]}],
    sources, output_dir=ROOT / "media")
card.update(placement_after="standfirst", article_inclusion=True, canonical_article_media=True)
assets.insert(0, card)
published = _active(PublishedImages(Path(r"A:\Capital Chronicle\Runtime\ContentOps\published_images_v1.jsonl")).records())
for asset in assets:
    fp = fingerprint(asset["path"])
    asset["prior_image_near_matches"] = sum(near(fp, image) for row in published for image in row["images"])
response = json.loads((ROOT / "desktop_response_media-plan.json").read_bytes())
binding = {"plan": {"native_plan_run_id": "cc107-nfp-dated-review-20261114-v1", "native_plan_stage": "media-plan",
    "native_plan_request_sha256": response["request_sha256"], "story_plan": response["output"]["story_plan"]}, "assets": assets}
(ROOT / "media-plan-binding.json").write_text(json.dumps(binding, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"binding": str(ROOT / "media-plan-binding.json"), "assets": [{k:a.get(k) for k in ["asset_id","path","sha256","width","height","prior_image_near_matches"]} for a in assets]}))
