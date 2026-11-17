"""Append the confirmed CC-425 target through the existing reader revision owner."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    NativeDesktopTurn, DesktopInputRequired, build_reader_presentation_revision,
    native_artifact_key, request_final_visual_review,
)
from live_contentops.cpi_reaction_page_v1 import LINK_POLICY

root = Path(__file__).resolve().parent
run = "cc338-cpi-preview-20261110-v1"
store = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
result = json.loads(store.get_outbox_message(native_artifact_key(store, run, "cc-editorial-final-"))["payload"])
original = store.get_platform_dispatch("dispatch_9aab37332626d663aadd8d8a631c300e")
target = store.get_platform_dispatch("dispatch_873dddf89422b103efe92b1b5f469f1c")
suffix = "\n\n## Historical CPI comparisons\n\n[Compare the market reactions in our CPI history tables](" + target["public_object_url"] + ")."
proposal = {"policy": LINK_POLICY, "run_id": run,
    "reference_dispatch_id": target["dispatch_id"], "reference_url": target["public_object_url"],
    "objects": {"substack": {k: original[k] for k in ("dispatch_id", "message_id", "platform", "public_object_id", "public_object_url")}},
    "body_after": result["article"]["substack_body_markdown"].rstrip() + suffix}
revision = build_reader_presentation_revision(store, run_id=run, proposal=proposal, owner_authority_ref="human:BACKLOG_CC425")
(root / "cpi-crosslink-revision.json").write_text(json.dumps(revision, indent=2), encoding="utf-8")
turn = NativeDesktopTurn(store, run_id=run, output_dir=root / "cpi-crosslink-review", owner_manual_validation=True)
try:
    request_final_visual_review(turn, renders=None, reader_presentation_revision=revision)
except DesktopInputRequired as pending:
    request = pending.request
    (root / "cpi-crosslink-review-request.json").write_text(json.dumps(request, indent=2), encoding="utf-8")
    summary = {"stage": request["stage"], "request_sha256": request["request_sha256"],
        "output_dir": str(turn.root), "reference_url": target["public_object_url"],
        "original_post": original["public_object_url"], "review_policy": request["governed_input"]["binding"].get("review_policy"),
        "automated_media_check": request["governed_input"]["binding"].get("automated_media_check")}
    (root / "cpi-crosslink-review-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))
