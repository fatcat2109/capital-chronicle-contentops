"""Project retained accepted CPI correction into exact social-amendment inputs.

This reads the existing editorial owner. It selects no channel media, grants no
review, alters no frozen packet and performs no public action.
"""
from pathlib import Path
import json, sys
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import reader_presentation_acceptance
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

root = Path(__file__).resolve().parent
run = "cc124-prepare-20261103-a"
store = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
with store.get_read_only_connection() as conn:
    rows = conn.execute("SELECT payload,status FROM outbox_messages WHERE work_item_id=? AND destination='internal:native-reader-presentation'", (run,)).fetchall()
note = next((json.loads(r[0]) for r in rows if r[1] == "PRESENTATION_EDIT_CONFIRMED"), None)
if not note:
    raise ValueError("CONFIRMED_ACCEPTED_CANONICAL_AMENDMENT_REQUIRED")
revision, view, acceptance = reader_presentation_acceptance(store, run_id=run, reference=note["review_reference"])
canonical = revision["objects"]["substack"]
destinations = []
canonical_intent = json.loads(store.get_outbox_message(canonical["message_id"])["payload"])
for destination in ("telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube"):
    ids = DurablePublicationCoordinator._ids(run, canonical_intent["plan_hash"], destination)
    row = store.get_outbox_message(ids["message_id"])
    if row is None:
        payload = next(p["payload"] for p in view["previews"] if p["destination"] == destination)
        destinations.append({"destination": destination, "message_id": ids["message_id"],
            "original_intent_sha256": None, "original_intent_state": "NOT_CREATED",
            "original_payload_sha256": sha256_of(payload), "plan_hash": canonical_intent["plan_hash"],
            "current_status": "NOT_DISPATCHED", "public_object_id": None, "public_object_url": None,
            "required_action": "CREATE_FROM_EXISTING_PLAN_ONLY_AFTER_SAME_MAX_REVIEW", "proposed_channel_media": None})
        continue
    intent = json.loads(row["payload"])
    dispatch = next((d for d in store.get_dispatches_for_work_item(run) if d["message_id"] == row["message_id"]), {})
    payload = _durable_intent_inputs(intent)["payloads"][row["destination"]]
    status = dispatch.get("status") or row["status"]
    action = ("EXACT_EXISTING_OBJECT_EDIT_AFTER_SAME_MAX_REVIEW" if status == "DISPATCH_CONFIRMED" else
        "READBACK_ONLY_BEFORE_AMENDMENT" if status == "UNKNOWN_WRITE" else
        "REJECT_OLD_REVISION_REQUEST_AND_BIND_REVIEWED_AMENDMENT_BEFORE_FIRST_SEND")
    destinations.append({"destination": row["destination"], "message_id": row["message_id"],
        "original_intent_sha256": sha256_of(intent), "original_payload_sha256": sha256_of(payload),
        "plan_hash": intent["plan_hash"], "current_status": status,
        "public_object_id": dispatch.get("public_object_id"), "public_object_url": dispatch.get("public_object_url"),
        "required_action": action, "proposed_channel_media": None})
assert len(destinations) == 8 and len({d["destination"] for d in destinations}) == 8
result = {"state": "REVIEW_INPUT_ONLY_NOT_ACCEPTED_OR_BOUND", "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "run_id": run, "canonical_identity": canonical, "canonical_review_reference": note["review_reference"],
    "accepted_canonical_article_revision": acceptance["article_revision"],
    "required_native_writer": acceptance["invocation_observation"]["invocation_id"],
    "required_model": "gpt-6.1-sol", "required_effort": "max",
    "same_writer_available_in_current_run": False,
    "media_assets": [{k:a.get(k) for k in ("asset_id", "path", "sha256", "modality", "placement_after", "source_page_url")}
        for a in view["media_assets"]],
    "official_history": {k:revision["official_history"].get(k) for k in ("dataset_sha256", "cutoff_utc", "window")},
    "destinations": sorted(destinations, key=lambda d:d["destination"]),
    "blocker": "SAME_MAX_DERIVATIVE_SELECTION_AND_REVIEW_REQUIRED",
    "engineering_limit": "Current reader amendment is canonical-only; extend it for exact destination media after the designated writer supplies channel selections. Do not mutate the dispatched base packet.",
    "public_write_performed": False, "frozen_packet_changed": False}
path = root / "cpi-derivative-amendment-input.json"
path.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"path": str(path), "state": result["state"], "destinations": len(destinations),
    "assets": len(view["media_assets"]), "required_native_writer": result["required_native_writer"], "public_write_performed": False}))
