"""Render a local card from the exact retained Main passage; no model or public write."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from live_contentops import fact_card_design_v1 as design
from live_contentops.post_visuals_v1 import build_post_data_card, validate_post_data_card

HERE = Path(__file__).resolve().parent
SOURCE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-nfp-arrival-review-20261106-v1\desktop_request_write.json")
request = json.loads(SOURCE.read_bytes())
document = request["governed_input"]["source_pack"][0]
source_before = sha256(SOURCE.read_bytes()).hexdigest()
passage = document["canonical_content_text"].split("\n\n")[0]
article = {"title": "The retained NFP report", "dek": passage, "substack_body_markdown": passage,
           "display_date": "Capital Chronicle · November 6, 2026"}
claims = [{"claim_id": "held-main-release", "claim_text": passage, "source_id": document["source_id"],
           "support_excerpt": passage}]
drawn = []
render = design.render_fact_card

def capture(path, spec, **kwargs):
    drawn.append({"key_label": spec.key_label, "key_value": spec.key_value,
                  "facts": spec.facts, "source_line": spec.source_line})
    return render(path, spec, **kwargs)

design.render_fact_card = capture
started = time.perf_counter()
card = build_post_data_card(article, claims, [document], output_dir=HERE / "media")
validate_post_data_card(card, article, [document])
assert drawn[-1]["key_value"] == "+165,000"
assert card["data_card_packet"]["facts"][0]["text"] == passage
assert sha256(SOURCE.read_bytes()).hexdigest() == source_before
result = {"purpose": "Exact held Main passage through the actual card consumer; local replay",
    "source_request_path": str(SOURCE), "source_request_sha256": source_before,
    "source_document_id": document["document_id"], "source_content_sha256": document["canonical_content_sha256"],
    "source_clock_utc": document["published_at_utc"], "rendered": drawn[-1],
    "asset": {k: card[k] for k in ("asset_id", "path", "sha256", "width", "height")},
    "seconds": round(time.perf_counter() - started, 3), "source_unchanged": True,
    "model_calls": 0, "public_writes": 0, "does_not_count_as_public_acceptance": True}
(HERE / "held-nfp-card-replay.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"path": card["path"], "sha256": card["sha256"], "key_value": drawn[-1]["key_value"],
                  "seconds": result["seconds"]}))
