"""One CC-247 amendment in the existing run; no public send."""
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_desktop_editorial_v1 import (
    native_artifact_key, build_reader_presentation_revision, NativeDesktopTurn,
    request_final_visual_review, DesktopInputRequired,
)
from live_contentops.release_chart_revision_v1 import MEDIA_REPAIR_POLICY, SOCIAL_DESTINATIONS, derivative_base_payloads
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

HERE = Path(__file__).resolve().parent
run = "cc124-next-article-20261103-b"
store = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
result = json.loads(store.get_outbox_message(native_artifact_key(store, run, "cc-editorial-final-"))["payload"])
request = json.loads((HERE / "sec-editor-request.json").read_bytes())
response = json.loads((HERE / "sec-editor-response.json").read_bytes())
assert response["decision"] == "ACCEPT"
asset = deepcopy(request["replacement_asset"])
asset["visual_review"] = {"asset_sha256": asset["sha256"], "pixels_inspected": True,
    "labels_and_units_legible": True, "reviewer": response["native_invocation_id"],
    "evidence_ref": str(HERE / "sec-editor-response.json")}
observation = {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": response["native_invocation_id"],
    "model": None, "reasoning_effort": None, "configured_model": "gpt-6.1-sol",
    "configured_reasoning_effort": "max", "configuration_status": "CONFIGURED_NOT_OBSERVED",
    "configuration_source": "collaboration.spawn_agent explicit gpt-6.1-sol/max, fork_turns=none",
    "actual_configuration_unavailable": True, "speed": "standard",
    "observation_source": "Supported native subagent final return and saved exact response"}
canonical = next(d for d in store.list_platform_dispatches() if d["message_id"] ==
    next(m["message_id"] for m in store.list_outbox_messages() if m["work_item_id"] == run and m["destination"] == "substack"))
intent = json.loads(store.get_outbox_message(canonical["message_id"])["payload"])
intent["canonical_url"] = canonical["public_object_url"]
payloads = derivative_base_payloads(store, run_id=run, accepted=result, canonical_intent=intent)
objects = {"substack": {k:canonical[k] for k in ("dispatch_id", "message_id", "platform", "public_object_id", "public_object_url")}}
originals = {}
for d in SOCIAL_DESTINATIONS:
    ids = DurablePublicationCoordinator._ids(run, intent["plan_hash"], d)
    dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
    objects[d] = {"dispatch_id": ids["dispatch_id"], "message_id": ids["message_id"], "platform": d,
        "public_object_id": dispatch.get("public_object_id"), "public_object_url": dispatch.get("public_object_url")}
    original = json.loads(store.get_outbox_message(ids["message_id"])["payload"])
    originals[d] = sha256_of(original)
    payloads[d]["media_asset_ids"] = [asset["asset_id"]]
    for i, post in enumerate(payloads[d].get("posts", [])):
        if isinstance(post, dict): post["media_asset_ids"] = [asset["asset_id"]] if i == 0 else []
decision = deepcopy(result["visual_editorial_decision"])
for chart in decision["charts"]: chart["asset_id"] = asset["asset_id"]
decision["channel_media"] = response["channel_media"]
proposal = {"policy": MEDIA_REPAIR_POLICY, "run_id": run, "article_identity": result["article_identity"],
    "article": {**result["article"], "visual_editorial_decision": decision}, "media_assets": [asset],
    "plan_hash": intent["plan_hash"], "objects": objects, "original_intent_sha256": originals,
    "payloads": payloads, "channel_media": response["channel_media"], "amendment_writer": {
        "request_path": str(HERE / "sec-editor-request.json"), "request_sha256": sha256((HERE / "sec-editor-request.json").read_bytes()).hexdigest(),
        "response_path": str(HERE / "sec-editor-response.json"), "response_sha256": sha256((HERE / "sec-editor-response.json").read_bytes()).hexdigest(),
        "invocation_observation": observation}}
revision = build_reader_presentation_revision(store, run_id=run, proposal=proposal, owner_authority_ref="human:BACKLOG_CC247")
(HERE / "sec-media-revision.json").write_text(json.dumps(revision, indent=2), encoding="utf-8")
binding = json.loads((Path(intent["output_dir"]) / "binding.json").read_bytes())
turn = NativeDesktopTurn(store, run_id=run, output_dir=binding["output_dir"], owner_manual_validation=True)
try:
    request_final_visual_review(turn, renders=None, reader_presentation_revision=revision)
except DesktopInputRequired as pending:
    packet = pending.request
    (HERE / "sec-final-review-request.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print(json.dumps({k:packet.get(k) for k in ("stage", "request_sha256")}))
