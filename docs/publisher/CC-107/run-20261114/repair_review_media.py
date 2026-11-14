"""Apply the same MAX writer's four pixel findings without changing source data."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops.post_visuals_v1 import build_post_data_card
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart
from live_contentops.published_images_v1 import PublishedImages, _active, fingerprint, near

ROOT = Path(r"C:\Users\bullw\AppData\Local\CapitalChronicle\ContentOps\editorial-previews\cc107-nfp-dated-review-20261114-v1")
sources = json.loads((ROOT / "desktop_request_write.json").read_bytes())["governed_input"]["source_pack"]
original = json.loads((ROOT / "media-plan-binding.json").read_bytes())["assets"]
assets, changes = [], []
for old in original:
    if old["asset_id"] == "nfp_review_october_industries":
        assets.append(old)
        continue
    if old.get("editorial_data_packet"):
        packet = deepcopy(old["editorial_data_packet"])
        packet["asset_id"] += "_r2"
        if "payroll_history" in packet["asset_id"]:
            packet["series"][0]["name"] = "Payroll change"
        elif "unemployment_history" in packet["asset_id"]:
            packet["series"][0]["name"] = "Unemployment rate"
        elif "reactions" in packet["asset_id"]:
            for series in packet["series"]:
                for point in series["points"]:
                    if point["period"] == "US 500 reference":
                        point["period"] = "S&P 500 reference"
            packet["alt_text"] = packet["alt_text"].replace("US 500 reference", "S&P 500 reference")
        new = build_editorial_data_chart(packet, sources, output_dir=ROOT / "media/repair-1")
    else:
        facts = ["Payrolls: **+165K**", "Unemployment rate: **4.1%**"]
        new = build_post_data_card({"title": "October jobs: our Strong release condition held",
            "substack_body_markdown": "\n\n".join(facts), "article_type": "EVENT_REVIEW",
            "display_date": "November 14, 2026", "event_article_packet": {"event_time_utc": "2026-11-06T13:30:00Z"}},
            [{"claim_id": "main-arrival-" + str(i), "claim_text": fact, "support_excerpt": fact,
                "source_id": "SOURCE_1"} for i,fact in enumerate(facts)], sources, output_dir=ROOT / "media/repair-1")
        new.update(placement_after="standfirst", article_inclusion=True, canonical_article_media=True)
    assert sha256(Path(old["path"]).read_bytes()).hexdigest() == old["sha256"]
    changes.append({"old_asset_id": old["asset_id"], "old_sha256": old["sha256"],
        "new_asset_id": new["asset_id"], "new_sha256": new["sha256"], "old_bytes_preserved": True})
    assets.append(new)
published = _active(PublishedImages(Path(r"A:\Capital Chronicle\Runtime\ContentOps\published_images_v1.jsonl")).records())
for asset in assets:
    fp = fingerprint(asset["path"])
    asset["prior_image_near_matches"] = sum(near(fp,image) for row in published for image in row["images"])
(ROOT / "repaired-assets.json").write_text(json.dumps(assets,indent=2),encoding="utf-8")
result = {"operation_id": ROOT.name, "repair_rounds": 1, "findings_owner": "/root/native_write_a97e7232eeeb",
    "changes": changes, "unchanged_asset": "nfp_review_october_industries", "asset_manifest": str(ROOT / "repaired-assets.json"),
    "data_values_unchanged": True, "max_reinspection_pending": True, "public_write_performed": False}
(REPO / "docs/publisher/CC-107/run-20261114/media-repair-result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result))
