"""After integration, bind the retained MAX return through the existing owner.

No send, new model call, source refresh, replacement binding, or scheduler.
Exact source/render changes require a new review rather than a fabricated return.
"""
import json
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    DesktopInputRequired, NativeDesktopTurn, reader_presentation_acceptance, request_final_visual_review,
)
from live_contentops.native_finished_publication_v1 import newsroom_lease

root = Path(__file__).resolve().parent
run = "cc124-prepare-20261103-a"
revision = json.loads((root / "cpi-derivative-revision.json").read_bytes())
saved = json.loads((root / "cpi-final-review-response.json").read_bytes())
binding = json.loads((Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual") / run / "binding.json").read_bytes())
renders = json.loads((root / "cpi-final-render-binding.json").read_bytes())
if saved["binding_sha256"] != sha256_of(renders):
    raise ValueError("INSPECTED_RENDER_BYTES_OR_REVISION_CHANGED")
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
with newsroom_lease(store):
    turn = NativeDesktopTurn(store, run_id=run, output_dir=binding["output_dir"], owner_manual_validation=True)
    try:
        request_final_visual_review(turn, renders=renders["renders"], reader_presentation_revision=revision)
        # Already accepted: the matching immutable request is reused below.
        stage = "final-visual-" + sha256_of(renders)
        request = turn.frozen_request(stage)
    except DesktopInputRequired as pending:
        request = pending.request
        stage = request["stage"]
    governed = turn.frozen_request(stage)["governed_input"]
    if sha256_of(governed["binding"]) != saved["binding_sha256"]:
        raise ValueError("INSPECTED_RENDER_BYTES_OR_REVISION_CHANGED")
    turn.submit(stage, {"request_sha256": request["request_sha256"], "output": saved["output"],
        "invocation_observation": saved["invocation_observation"]})
    reference = {"stage": stage, "request_sha256": request["request_sha256"], "output_dir": str(turn.root)}
    _, _, acceptance = reader_presentation_acceptance(store, run_id=run, reference=reference)
    (root / "cpi-bound-review-reference.json").write_text(json.dumps(reference, indent=2) + "\n")
    for destination in revision["payloads"]:
        (root / (destination + "-continuation-input.json")).write_text(json.dumps({
            "destination": destination, "review_reference": reference}, indent=2) + "\n")
print(json.dumps({"status": "EXACT_RETAINED_MAX_REVIEW_BOUND", "review_reference": reference,
    "article_revision": acceptance["article_revision"], "new_model_calls": 0, "public_write_performed": False}))
