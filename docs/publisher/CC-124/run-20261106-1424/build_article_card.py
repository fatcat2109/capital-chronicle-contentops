"""Build this article's card through the existing source-bound renderer."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.post_visuals_v1 import build_post_data_card, validate_post_data_card

HERE = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-six-markets-20261106-v1")
cycle = json.loads((RUN / "native_desktop_result.json").read_bytes())
result = cycle.get("report_workspace_result", cycle)
stage = "revise" if cycle.get("revision_performed") or result.get("simple_result", {}).get("revision_performed") else "write"
response = json.loads((RUN / ("desktop_response_" + stage + ".json")).read_bytes())
article = result["article"]
documents = result["evidence"]
claims = response["output"]["material_claim_bindings"]
card = build_post_data_card(article, claims, documents, output_dir=HERE / "media")
validate_post_data_card(card, article, documents)
photo = json.loads((HERE / "media/photo-asset.json").read_bytes())
packet = {"article_identity": result["article_identity"], "assets": [card, photo]}
(HERE / "media-binding.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
(HERE / "media/card-asset.json").write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
proof = {"article_identity": result["article_identity"], "article_body_sha256": hashlib.sha256(
    article["substack_body_markdown"].encode()).hexdigest(), "builder": "build_post_data_card",
    "uses_actual_written_article": True, "card_sha256": card["sha256"],
    "fact_texts": [fact["text"] for fact in card["data_card_packet"].get("facts", [])]}
(HERE / "card-source-check.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"card": card["path"], "sha256": card["sha256"], "fact_count": len(proof["fact_texts"])}))
