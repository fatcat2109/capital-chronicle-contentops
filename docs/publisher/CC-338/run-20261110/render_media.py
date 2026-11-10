"""Render MAX's CPI preview choices with the existing admitted chart owner."""
from copy import deepcopy
import json
from pathlib import Path

from live_contentops.official_release_history_v1 import history_chart_packet
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart
from live_contentops.published_images_v1 import PublishedImages, _active, fingerprint, near

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc338-cpi-preview-20261110-v1")


def main():
    decision = json.loads((ROOT / "desktop_response_visual-edit.json").read_bytes())["output"]
    sources = json.loads((ROOT / "editorial_media_plan_required.json").read_bytes())["source_pack"]
    original = json.loads((ROOT.parent / "cc216-cpi-background-20261105-v1" / "official_release_history_v1.json").read_bytes())
    history = deepcopy(original)
    history["series"] = [d["official_release_history"]["series"] for d in sources if d.get("official_release_history")]
    assert len(history["series"]) == 4
    assets = []
    for selected in decision["charts"]:
        aid = selected["asset_id"]
        if "monthly" in aid:
            packet = history_chart_packet(history, series_names=["CPI_HEADLINE_MOM", "CPI_CORE_MOM"],
                asset_id=aid, title=selected.get("title") or "The monthly baseline for October CPI",
                question=selected["question"], placement_after=selected["placement_after"])
            packet.update(chart_type="line", history_axis_limits=[-0.5, 1.0],
                caption="BLS dated first releases, October 2024–September 2026. Monthly seasonally adjusted changes; missing observations stay gaps.",
                source_caption="Source: BLS dated first releases. Monthly SA percent changes; October/November 2025 are gaps.",
                alt_text="Twenty-four months of headline and core CPI monthly changes through September 2026, with missing months left as gaps.")
            for series, label in zip(packet["series"], ("Headline CPI", "Core CPI")):
                series["name"] = label
        elif "component" in aid:
            doc = next(d for d in sources if d.get("release_component_effects"))
            points = []
            for effect in doc["release_component_effects"]["effects"]:
                if effect["official_series_id"] not in {"CUSR0000SA0E", "CUSR0000SA0L1E", "CUSR0000SAF1"}:
                    continue
                line = next(line for line in doc["canonical_content_text"].splitlines() if effect["official_series_id"] in line)
                points.append({"period": effect["name"], "value": effect["value"], "observation_kind": "REPORTED_ACTUAL",
                    "inputs": [{"document_id": doc["document_id"], "support_excerpt": line,
                        "value_text": effect["native_value"], "source_period_text": "2026-09",
                        "source_content_sha256": doc["canonical_content_sha256"], "metric": effect["name"],
                        "unit": "percentage points", "prepared_period": "2026-09",
                        "period_basis": {"basis": "BLS_REPORTED_TABLE_6_EFFECT_ON_ALL_ITEMS",
                            "capture_sha256": doc["release_component_effects"]["capture_sha256"], "period": "2026-09"}}]})
            if not points:
                raise ValueError("EXACT_COMPONENT_SERIES_REQUIRED")
            packet = {"asset_id": aid, "chart_type": "grouped_bar",
                "title": selected.get("title") or "September: the starting composition",
                "question": selected["question"], "placement_after": selected["placement_after"],
                "unit": "percentage points", "series": [{"name": "Reported effect on all items", "points": points}],
                "value_label_decimals": 3, "source_caption": "Source: BLS, September 2026 CPI, Table 6. Reported effects; no normalization to the rounded headline.",
                "caption": "September 2026 monthly CPI, seasonally adjusted. BLS-reported effects on all-items CPI, in percentage points.",
                "alt_text": "September CPI effects: energy 0.377, core 0.265 and food 0.006 percentage points."}
        else:
            raise ValueError("UNRECOGNIZED_MAX_CHART:" + aid)
        built = build_editorial_data_chart(packet, sources, output_dir=ROOT / "media")
        assets.append(built)
    photo = json.loads((ROOT / "media/contextual-photo-asset.json").read_bytes())
    if photo["asset_id"] in decision.get("contextual_photo_ids", []):
        assets.append(photo)
    snapshot = json.loads((ROOT / "media/tradingview/neo-snapshot-asset.json").read_bytes())
    snapshot.update(article_inclusion=True, canonical_article_media=True, delivery_only=False,
        placement_after="standfirst", canonical_article_section_association="introduction")
    if snapshot["asset_id"] in decision.get("tradingview_snapshot_asset_ids", []):
        assets.append(snapshot)
    prior = _active(PublishedImages(Path(r"A:\Capital Chronicle\Runtime\ContentOps\published_images_v1.jsonl")).records())
    for asset in assets:
        fp = fingerprint(asset["path"])
        assert fp["sha256"] == asset["sha256"]
        asset["prior_image_near_matches"] = sum(near(fp, image) for row in prior for image in row["images"])
    path = ROOT / "rendered-assets.json"
    path.write_text(json.dumps(assets, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(path), "assets": [{"asset_id": a["asset_id"], "path": a["path"],
        "sha256": a["sha256"], "prior_image_near_matches": a["prior_image_near_matches"]} for a in assets]}))


if __name__ == "__main__":
    main()
