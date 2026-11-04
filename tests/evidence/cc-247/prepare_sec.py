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
prefix = "cpi" if "--cpi" in sys.argv else "sec"
run = "cc124-prepare-20261103-a" if prefix == "cpi" else "cc124-next-article-20261103-b"
store = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
result = json.loads(store.get_outbox_message(native_artifact_key(store, run, "cc-editorial-final-"))["payload"])
request = json.loads((HERE / (prefix + "-editor-request.json")).read_bytes())
response = json.loads((HERE / (prefix + "-editor-response.json")).read_bytes())
assert response["decision"] == "ACCEPT"
assets = deepcopy(request.get("media_assets") or [request["replacement_asset"]])
if prefix == "sec":
    assets[0]["visual_review"] = {"asset_sha256": assets[0]["sha256"], "pixels_inspected": True,
        "labels_and_units_legible": True, "reviewer": response["native_invocation_id"],
        "evidence_ref": str(HERE / "sec-editor-response.json")}
observation = {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": response["native_invocation_id"],
    "model": None, "reasoning_effort": None, "configured_model": "gpt-6.1-sol",
    "configured_reasoning_effort": "max", "configuration_status": "CONFIGURED_NOT_OBSERVED",
    "configuration_source": "collaboration.spawn_agent explicit gpt-6.1-sol/max, fork_turns=none",
    "actual_configuration_unavailable": True, "speed": "standard",
    "observation_source": "Supported native subagent final return and saved exact response"}
base = result
if request.get("canonical_review_reference"):
    from live_contentops.native_desktop_editorial_v1 import reader_presentation_acceptance
    _, base, _ = reader_presentation_acceptance(store, run_id=run, reference=request["canonical_review_reference"])
canonical = store.get_platform_dispatch("dispatch_61e1c3551501afee92efad2c69c2b1d1" if prefix == "cpi" else "dispatch_27fa5f84bd333d9cc480ceba5d8c4f9c")
intent = json.loads(store.get_outbox_message(canonical["message_id"])["payload"])
intent["canonical_url"] = canonical["public_object_url"]
payloads = derivative_base_payloads(store, run_id=run, accepted=base, canonical_intent=intent)
objects = {"substack": {k:canonical[k] for k in ("dispatch_id", "message_id", "platform", "public_object_id", "public_object_url")}}
originals = {}
for d in SOCIAL_DESTINATIONS:
    ids = DurablePublicationCoordinator._ids(run, intent["plan_hash"], d)
    dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
    objects[d] = {"dispatch_id": ids["dispatch_id"], "message_id": ids["message_id"], "platform": d,
        "public_object_id": dispatch.get("public_object_id"), "public_object_url": dispatch.get("public_object_url")}
    original = json.loads(store.get_outbox_message(ids["message_id"])["payload"])
    originals[d] = sha256_of(original)
    payloads[d]["media_asset_ids"] = response["channel_media"][d]
    for i, post in enumerate(payloads[d].get("posts", [])):
        if isinstance(post, dict): post["media_asset_ids"] = response["channel_media"][d] if i == 0 else []
decision = deepcopy(base.get("visual_editorial_decision") or base["article"].get("visual_editorial_decision"))
article = deepcopy(base["article"])
if decision:
    if prefix == "sec":
        for chart in decision["charts"]: chart["asset_id"] = assets[0]["asset_id"]
    decision["channel_media"] = response["channel_media"]
    article["visual_editorial_decision"] = decision
proposal = {"policy": MEDIA_REPAIR_POLICY, "run_id": run, "article_identity": result["article_identity"],
    "article": article, "media_assets": assets,
    "plan_hash": intent["plan_hash"], "objects": objects, "original_intent_sha256": originals,
    "payloads": payloads, "channel_media": response["channel_media"], "amendment_writer": {
        "request_path": str(HERE / (prefix + "-editor-request.json")), "request_sha256": sha256((HERE / (prefix + "-editor-request.json")).read_bytes()).hexdigest(),
        "response_path": str(HERE / (prefix + "-editor-response.json")), "response_sha256": sha256((HERE / (prefix + "-editor-response.json")).read_bytes()).hexdigest(),
        "invocation_observation": observation}}
if request.get("canonical_review_reference"):
    proposal["canonical_review_reference"] = request["canonical_review_reference"]
revision = build_reader_presentation_revision(store, run_id=run, proposal=proposal, owner_authority_ref="human:BACKLOG_CC247")
(HERE / (prefix + "-media-revision.json")).write_text(json.dumps(revision, indent=2), encoding="utf-8")
binding = json.loads((Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual") / run / "binding.json").read_bytes())
turn = NativeDesktopTurn(store, run_id=run, output_dir=binding["output_dir"], owner_manual_validation=True)
try:
    request_final_visual_review(turn, renders=None, reader_presentation_revision=revision)
except DesktopInputRequired as pending:
    packet = pending.request
    (HERE / (prefix + "-final-review-request.json")).write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print(json.dumps({k:packet.get(k) for k in ("stage", "request_sha256")}))
