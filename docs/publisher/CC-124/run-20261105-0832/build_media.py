"""Render MAX's exact filing-fact choice through the installed card owner."""
import json
from pathlib import Path
import sys

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.post_visuals_v1 import build_post_data_card
from live_contentops.native_desktop_editorial_v1 import validate_release_media

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-b")
packet = json.loads((ROOT / "editorial_media_plan_required.json").read_bytes())
decision = json.loads((ROOT / "desktop_response_visual-edit.json").read_bytes())["output"]
plan = decision["post_data_card_plan"]
source = next(d for d in packet["source_pack"] if d["source_id"] == "SOURCE_1")
text = source["canonical_content_text"]
excerpts = [
    text[text.index("The cash proceeds"):text.index("Approximately $36")].strip(),
    text[text.index("Approximately $36"):text.index("As of June")].strip(),
    text[text.index("As of June"):text.index("See Note 4")].strip(),
]
claims = [{"claim_id": "southwest-clock-" + str(i + 1), "claim_text": fact["text"],
    "source_id": fact["source_id"], "support_excerpt": excerpt}
    for i, (fact, excerpt) in enumerate(zip(plan["facts"], excerpts))]
article = {"title": plan["title"], "substack_body_markdown": "\n\n".join(f["text"] for f in plan["facts"]),
    "visual_editorial_decision": decision, "resolved_article_mode": "DATA_OR_DOCUMENT_LENS",
    "news_item_kind": "ANALYSIS", "display_date": "November 5, 2026"}
asset = build_post_data_card(article, claims, packet["source_pack"], output_dir=ROOT)
counts = validate_release_media({"media_assets": [asset], "evidence": packet["source_pack"],
    "visual_editorial_decision": decision}, prewriter=True)
assert len(asset["data_card_packet"]["facts"]) == 3
(ROOT / "selected-card.json").write_text(json.dumps(asset, indent=2), encoding="utf-8")
(ROOT / "card-claims.json").write_text(json.dumps(claims, indent=2), encoding="utf-8")
light = json.loads((ROOT / "desktop_response_media-plan.json").read_bytes())
binding = {"plan": {"native_plan_run_id": ROOT.name, "native_plan_stage": "media-plan",
    "native_plan_request_sha256": light["request_sha256"], "story_plan": light["output"]["story_plan"]},
    "assets": [asset]}
(ROOT / "media-plan-binding.json").write_text(json.dumps(binding, indent=2), encoding="utf-8")
print(json.dumps({"asset_path": asset["path"], "sha256": asset["sha256"], "counts": counts,
    "facts": len(asset["data_card_packet"]["facts"]), "pixels_inspected": False}))
