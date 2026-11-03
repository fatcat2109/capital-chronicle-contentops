"""Render only the actual MAX editor's chosen frozen facts through the media owner."""
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[3]))

RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc107-midterm-preview-20261103-v1")


def render():
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart
    selected = json.loads((RUNTIME / "desktop_response_visual-edit.json").read_bytes())["output"]
    assert len(selected["charts"]) == 1
    choice = selected["charts"][0]
    spec = choice["data_spec"]
    assert spec["chart_form"] == "fact_card"
    documents = json.loads((RUNTIME / "editorial_media_plan_required.json").read_bytes())["source_pack"]
    doc = documents[0]
    text = doc["canonical_content_text"]
    excerpt = next(p for p in text.split("\n\n") if "PollCheck has Democrats" in p)
    match = re.search(r"PollCheck has Democrats at (\d+\.\d+%) and Republicans at (\d+\.\d+%)", excerpt)
    assert match
    displays = match.groups()
    assert [float(t.rstrip("%")) for t in displays] == [r["value"] for r in spec["data"]]
    points = []
    for row, display in zip(spec["data"], displays):
        points.append({"period": row["label"], "value": float(display.rstrip("%")),
            "display_value": display, "observation_kind": "ESTIMATE", "transform": "IDENTITY",
            "inputs": [{"document_id": doc["document_id"], "support_excerpt": excerpt,
                "value_text": display.rstrip("%"), "source_period_text": "updated 2 November",
                "source_content_sha256": sha256(text.encode()).hexdigest(),
                "metric": spec["metric"], "unit": "percent", "prepared_period": "2 November 2026",
                "period_basis": {"source_display": "updated 2 November", "source_known_at_utc": doc["published_at_utc"]}}]})
    packet = {"asset_id": choice["asset_id"], "chart_type": "fact_card", "question": choice["question"],
        "title": spec["title"], "subtitle": spec["subtitle"], "unit": "percent",
        "series": [{"label": spec["metric"], "points": points}],
        "fact_card_note": "Voting intentions, not chamber-control probabilities.",
        "fact_card_footer": spec["event_timing"]["display"],
        "source_caption": "PollCheck (2 November 2026); poll-closing time: 270toWin.",
        "caption": spec["caption"], "alt_text": spec["alt_text"],
        "placement_after": choice["placement_after"],
        "destination_subset": list(selected["channel_media"]), "missingness": spec["missingness"]}
    chart = build_editorial_data_chart(packet, documents, output_dir=ROOT / "render-r2")
    photo = json.loads((ROOT / "media/photo-asset.json").read_bytes())
    planner = json.loads((RUNTIME / "desktop_response_media-plan.json").read_bytes())
    binding = {"plan": {"native_plan_run_id": "cc107-midterm-preview-20261103-v1", "native_plan_stage": "media-plan",
        "native_plan_request_sha256": planner["request_sha256"], "story_plan": planner["output"]["story_plan"]},
        "assets": [chart, photo]}
    (ROOT / "media-binding-response.json").write_text(json.dumps(binding, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"asset_id": chart["asset_id"], "path": chart["path"], "sha256": chart["sha256"],
                      "computed_values": chart["computed_values"]}))


if __name__ == "__main__":
    render()
