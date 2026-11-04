"""Render this item's exact MAX choices through the existing chart/media owners."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.official_release_history_v1 import history_chart_packet
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart, validate_source_value_chart
from live_contentops.visual_asset_discovery_v1 import validate_contextual_photo

BASE = Path("A:/Capital Chronicle/Runtime/ContentOps/daily_app_outputs/owner-manual")
HERE = Path(__file__).resolve().parent


def main(name, repair=False):
    root = BASE / ("cc216-" + name + "-background-20261105-v1")
    media = root / "media"
    media.mkdir(exist_ok=True)
    pending = json.loads((root / "editorial_media_plan_required.json").read_bytes())
    sources = pending["source_pack"]
    history = json.loads((root / "official_release_history_v1.json").read_bytes())
    choice = json.loads((root / "desktop_response_visual-edit.json").read_bytes())["output"]
    assets = []
    previous_path = root / "rendered-assets.json"
    previous = {a["asset_id"]: a for a in json.loads(previous_path.read_bytes())} if previous_path.exists() else {}
    if name == "nfp":
        donor = BASE / "cc124-next-article-20261104-a"
        research = RetainedSourceResearch(donor / "source-recovery-september-employment")
        assert not research.gaps
        record = research.records["cc124-bls-september-employment-original"]
        full = {**record["document"], "document_id": record["headline_id"],
            "url": record["source_url"], "canonical_content_text": record["permitted_source_text"],
            "canonical_content_sha256": sha256(record["permitted_source_text"].encode()).hexdigest()}
        sources = [*sources, full]
    for selected in choice["charts"]:
        spec, aid = selected["data_spec"], selected["asset_id"]
        if name == "nfp" and aid == "september_sector_breakdown":
            old = next(a for a in json.loads((donor / "rendered-assets.json").read_bytes()) if a["asset_id"] == aid)
            packet = deepcopy(old["editorial_data_packet"])
            packet.update(title=spec["title"], question=selected["question"],
                placement_after=selected["placement_after"], caption=spec["caption"])
            binding = json.loads((donor / "sector-chart-source-binding.json").read_bytes())
        elif name == "cpi" and "component" in aid:
            doc = next(d for d in sources if d["document_id"].startswith("official-components-"))
            effects = history["components"]
            points = []
            for row in spec["series"]:
                effect = next(e for e in effects["effects"] if e["official_series_id"] == row["official_series_id"])
                assert effect["value"] == row["value"]
                line = next(l for l in doc["canonical_content_text"].splitlines() if effect["official_series_id"] in l)
                points.append({"period": row["label"], "value": row["value"], "observation_kind": "REPORTED_ACTUAL",
                    "inputs": [{"document_id": doc["document_id"], "support_excerpt": line,
                        "value_text": row["native_value"], "source_period_text": "2026-09",
                        "source_content_sha256": doc["canonical_content_sha256"],
                        "metric": effect["name"], "unit": "percentage points", "prepared_period": "2026-09",
                        "period_basis": {"basis": "BLS_REPORTED_TABLE_6_EFFECT_ON_ALL_ITEMS",
                            "capture_sha256": effects["capture_sha256"], "period": "2026-09"}}]})
            packet = {"asset_id": aid, "chart_type": "horizontal_diverging_bar",
                "title": selected["title"], "question": selected["question"],
                "placement_after": selected["placement_after"], "unit": "percentage points",
                "series": [{"name": "Reported effect on all items", "points": points}],
                "value_label_decimals": 3,
                "source_caption": "Source: BLS, September 2026 CPI, Table 6. Reported effects; no normalization to the rounded headline.",
                "caption": "September 2026, seasonally adjusted. BLS-reported effects on all-items CPI; percentage points.",
                "alt_text": "BLS September component effects: energy 0.377, core 0.265 and food 0.006 percentage points."}
            binding = None
        else:
            raw_names = spec.get("series")
            names = [s["series_id"] for s in raw_names] if isinstance(raw_names, list) else [raw_names]
            if name == "ppi" and not names[0]:
                names = ["PPI_FINAL_DEMAND_MOM", "PPI_CORE_EX_FOOD_ENERGY_TRADE_MOM"]
            packet = history_chart_packet(history, series_names=names, asset_id=aid,
                title=selected.get("title") or spec.get("title") or selected["question"],
                question=selected["question"], placement_after=selected["placement_after"])
            packet.update(caption=spec.get("caption") or "BLS dated first releases, October 2024–September 2026. Missing observations remain gaps.",
                alt_text=selected["question"])
            if name == "cpi":
                packet["chart_type"] = "grouped_bar" if "monthly" in aid else "line"
                packet["history_axis_limits"] = [-0.5, 1.0] if "monthly" in aid else [0, 5]
                for s, proposal in zip(packet["series"], spec["series"]):
                    s["name"] = proposal["label"]
                if "monthly" in aid:
                    packet["history_point_labels"] = [
                        {"series_index": 0, "period": "2026-08", "dx": -23, "dy": 17},
                        {"series_index": 1, "period": "2026-08", "dx": -30, "dy": -20},
                        {"series_index": 0, "period": "2026-09", "dx": 0, "dy": 20},
                        {"series_index": 1, "period": "2026-09", "dx": 28, "dy": -20},
                        {"series_index": 1, "period": "2026-06", "dx": -20, "dy": -24}]
                packet["source_caption"] = ("Source: BLS dated first releases. October 2024–September 2026. "
                    + ("SA monthly changes; October/November 2025 are gaps." if "monthly" in aid else "NSA annual changes; October 2025 is a gap."))
            elif name == "nfp":
                packet["chart_type"] = "line" if "unemployment" in aid else "grouped_bar"
                if "unemployment" in aid:
                    packet["history_axis_limits"] = [0, 5]
                packet["series"][0]["name"] = {
                    "NFP_PAYROLL_CHANGE": "Nonfarm payroll change",
                    "UNEMPLOYMENT_RATE": "Civilian unemployment rate",
                    "AHE_MOM": "Average hourly earnings, monthly change"}[names[0]]
                packet["subtitle"] = ("Seasonally adjusted monthly change in jobs" if "payroll" in aid else
                    "Civilian unemployment rate, seasonally adjusted" if "unemployment" in aid else
                    "Nominal average hourly earnings, seasonally adjusted; percent month on month")
                if "unemployment" not in aid:
                    packet["history_point_labels"] = [{"series_index": 0, "period": "2026-09",
                        "decimals": 0 if "payroll" in aid else 1, "dx": -35, "dy": 17}]
                packet["source_caption"] = "Source: BLS dated first releases. October 2024–September 2026; each month retains its first print."
                if "earnings" in aid:
                    packet["source_caption"] += " Hatched bars: October 2025 and July 2026 computed from published levels, rounded to one decimal."
                if "unemployment" in aid:
                    packet["source_caption"] += " October 2025 is absent from the retained series; no interpolation."
                    for gap in packet["missingness"]:
                        gap["reader_note"] = "NO_SAVED_OBSERVATION_FOR_PERIOD; absent from retained series"
            binding = None
        packet["destination_subset"] = [d for d, ids in choice["channel_media"].items() if aid in ids]
        asset = build_editorial_data_chart(packet, sources, output_dir=root / "visual-repair-r1" if repair else root,
            **({"retained_source_binding": binding} if binding else {}))
        delivery = media / (aid + ".png")
        shutil.copyfile(asset["path"], delivery)
        asset["path"] = str(delivery)
        validate_source_value_chart(asset, sources)
        assets.append(asset)
    photo_records = {
        "cc074-archive-warsh-20260522": HERE.parent / "CC-074-private-20261101/media/photo-asset.json",
        "cpi-usda-supermarket-archive": HERE.parents[2] / "tests/evidence/cc-142/media/photo-asset-canonical-date.json",
    }
    for aid in choice.get("contextual_photo_ids", []):
        record_path = photo_records[aid]
        asset = json.loads(record_path.read_bytes())
        validate_contextual_photo(asset)
        original = Path(asset["path"])
        target = media / (aid + original.suffix)
        if not target.exists():
            shutil.copyfile(original, target)
        assert sha256(target.read_bytes()).hexdigest() == asset["sha256"]
        rights = Path(asset["rights_evidence_path"])
        rights_target = media / (aid + "-rights.json")
        if not rights_target.exists():
            shutil.copyfile(rights, rights_target)
        asset.update(path=str(target), rights_evidence_path=str(rights_target),
            caption=("Federal Reserve Chair Kevin Warsh at his May 22, 2026 swearing-in ceremony. Archive context for monetary policy; not an image of the forthcoming release."
                if name == "nfp" else "Dry beans at Papaya Supermarket in Dearborn, Michigan, June 2023. Archive context; not an observation of October 2026 prices."))
        if name == "nfp":
            asset["relevance_rationale"] = "Archive portrait of the Federal Reserve chair supplies institutional context for the preview's conditional transmission from labor data to monetary policy; it does not corroborate the forthcoming report."
        assets.append(asset)
    for asset in assets:
        prior = previous.get(asset["asset_id"], {})
        if prior.get("sha256") == asset["sha256"] and prior.get("visual_review"):
            asset["visual_review"] = prior["visual_review"]
    (root / "rendered-assets.json").write_text(json.dumps(assets, indent=2), encoding="utf-8")
    proof = {"operation_id": root.name, "assets": [{k:a[k] for k in ("asset_id", "path", "sha256", "width", "height", "modality")} for a in assets],
        "source_value_validators": "PASS", "pixels_reviewed_this_run": False}
    (HERE / (name + "-rendered-assets.json")).write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps(proof))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=["nfp", "cpi", "ppi"])
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()
    main(args.name, args.repair)
