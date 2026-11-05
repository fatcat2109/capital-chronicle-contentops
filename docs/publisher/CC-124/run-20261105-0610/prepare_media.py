"""Render this article's MAX choices through the existing media owners."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.official_release_history_v1 import history_chart_packet
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_editorial_data_chart, validate_source_value_chart,
)
from live_contentops.visual_asset_discovery_v1 import validate_contextual_photo

HERE = Path(__file__).resolve().parent
ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-a")
DONOR = ROOT.parent / "cc216-ppi-background-20261105-v1"
MEDIA = ROOT / "media"
MEDIA.mkdir(exist_ok=True)
sources = json.loads((ROOT / "editorial_media_plan_required.json").read_bytes())["source_pack"]
history = json.loads((ROOT / "official_release_history_v1.json").read_bytes())
decision = json.loads((ROOT / "desktop_response_visual-edit.json").read_bytes())["output"]
facts = json.loads((ROOT / "september-component-values.json").read_bytes())
doc = next(d for d in sources if d["document_id"] == "cc124-bls-september-ppi-original")
research = RetainedSourceResearch(ROOT / "source-recovery-september-ppi")
assert not research.gaps
record = research.records[doc["document_id"]]
binding = {"research_root": str(ROOT / "source-recovery-september-ppi"),
    "research_revision": research.revision,
    "source_capture_hashes": {doc["document_id"]: record["source_capture_sha256"]}}
(ROOT / "chart-source-binding.json").write_text(json.dumps(binding, indent=2), encoding="utf-8")


def point(fact, label):
    assert fact["support_excerpt"] in doc["canonical_content_text"]
    assert fact["source_content_sha256"] == doc["canonical_content_sha256"]
    excerpt = fact["support_excerpt"]
    if "September" not in excerpt:
        pos = doc["canonical_content_text"].index(excerpt)
        month_pos = doc["canonical_content_text"].rfind("September", 0, pos)
        assert month_pos >= 0 and pos - month_pos < 1200
        excerpt = doc["canonical_content_text"][month_pos:pos + len(excerpt)]
    return {"period": label, "value": fact["value"], "observation_kind": "REPORTED_ACTUAL",
        "inputs": [{"document_id": doc["document_id"], "support_excerpt": excerpt,
            "value_text": fact["value_text"], "source_period_text": "September",
            "source_content_sha256": doc["canonical_content_sha256"], "metric": fact["label"],
            "unit": "percent", "prepared_period": "2026-09",
            "period_basis": {"basis": "BLS_ORIGINAL_SEPTEMBER_PPI_REPORTED_MONTHLY_RATE",
                "capture_sha256": fact["source_capture_sha256"], "reference_period": "2026-09"}}]}


assets = []
repair_nested = "--repair-nested" in sys.argv
previous = {a["asset_id"]: a for a in json.loads((ROOT / "rendered-assets.json").read_bytes())} if repair_nested else {}
for selected in decision["charts"]:
    aid, spec = selected["asset_id"], selected["data_spec"]
    if repair_nested and aid != "ppi_september_nested_rates":
        assets.append(previous[aid])
        continue
    base = {"asset_id": aid, "title": selected["title"], "question": selected["question"],
        "placement_after": selected["placement_after"], "unit": "percent",
        "subtitle": "September 2026 monthly change, seasonally adjusted",
        "source_caption": spec["source_note"], "value_label_decimals": 1,
        "destination_subset": [d for d, ids in decision["channel_media"].items() if aid in ids]}
    if aid == "ppi_headline_core_24m":
        packet = history_chart_packet(history,
            series_names=[s["name"] for s in spec["series"]], asset_id=aid,
            title=selected["title"], question=selected["question"], placement_after=selected["placement_after"])
        packet.update(base, chart_type="direct_labelled_two_line",
            subtitle="Monthly change, seasonally adjusted · as first reported",
            caption="October 2024–September 2026. Each month retains its dated first release. Underlying excludes foods, energy and trade services; later revisions are not substituted.",
            alt_text="Two years of first-reported monthly PPI changes; September headline 1.3%, underlying 0.5%.")
        for series, proposed in zip(packet["series"], spec["series"]):
            assert [(p["period"], p["value"]) for p in series["points"]] == [
                (p["period"], p["value"]) for p in proposed["observations"]]
            series["name"] = proposed["label"]
        packet["history_point_labels"] = [
            {"series_index": 0, "period": "2026-09", "dx": -22, "dy": 18},
            {"series_index": 1, "period": "2026-09", "dx": -22, "dy": -18}]
    elif aid == "ppi_september_component_rates":
        rows = spec["observations"]
        assert [r["value"] for r in rows] == [f["value"] for f in facts[:4]]
        packet = {**base, "chart_type": "horizontal_diverging_bar", "zero_based": True,
            "series": [{"name": "September monthly change", "points": [
                point(f, row["label"]) for f, row in zip(facts[:4], rows)]}],
            "caption": "Separate monthly rates, not percentage-point contributions. The underlying measure overlaps goods and services; the bars do not add to the headline.",
            "alt_text": "September PPI: final demand 1.3%, goods 2.6%, services 0.8%, excluding foods, energy and trade services 0.5%."}
    elif aid == "ppi_september_nested_rates":
        goods = [facts[5], facts[4], facts[6]]
        services = facts[7:10]
        groups = spec["groups"]
        packet = {**base, "chart_type": "SMALL_MULTIPLE_HORIZONTAL_DIVERGING_BARS", "zero_based": True, "series": [],
            "caption": "Nested category rates, not contributions. Both panels use the same percent scale. Trade services measure margins; no category weights are inferred.",
            "alt_text": "Goods: foods 1.2%, energy 10.8%, excluding foods and energy 0.3%. Services: trade margins 1.4%, transport and warehousing 3.4%, other services 0.3%."}
        for group, values in zip(groups, [goods, services]):
            assert [row["value"] for row in group["observations"]] == [f["value"] for f in values]
            packet["series"].append({"name": group["label"], "points": [
                point(f, row["label"]) for f, row in zip(values, group["observations"])]})
    else:
        raise ValueError("Unrecognised MAX chart: " + aid)
    asset = build_editorial_data_chart(packet, sources,
        output_dir=ROOT / "visual-repair-r1" if repair_nested else ROOT, retained_source_binding=binding)
    target = MEDIA / (aid + ("-r1.png" if repair_nested else ".png"))
    shutil.copyfile(asset["path"], target)
    asset["path"] = str(target)
    validate_source_value_chart(asset, sources)
    assets.append(asset)

donor_assets = json.loads((DONOR / "media-plan-binding.json").read_bytes())["assets"]
for aid in decision["contextual_photo_ids"]:
    if repair_nested:
        assets.append(previous[aid])
        continue
    asset = deepcopy(next(a for a in donor_assets if a["asset_id"] == aid))
    validate_contextual_photo(asset)
    target = MEDIA / (aid + Path(asset["path"]).suffix)
    shutil.copyfile(asset["path"], target)
    rights = MEDIA / (aid + "-rights.json")
    shutil.copyfile(asset["rights_evidence_path"], rights)
    asset.update(path=str(target), rights_evidence_path=str(rights))
    assert sha256(target.read_bytes()).hexdigest() == asset["sha256"]
    assets.append(asset)

(ROOT / "rendered-assets.json").write_text(json.dumps(assets, indent=2), encoding="utf-8")
summary = {"source_value_validators": "PASS", "history_cutoff_utc": history["cutoff_utc"],
    "assets": [{k: a[k] for k in ("asset_id", "path", "sha256", "width", "height", "modality")}
        for a in assets], "pixels_reviewed_this_run": False}
(HERE / "rendered-assets-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary))
