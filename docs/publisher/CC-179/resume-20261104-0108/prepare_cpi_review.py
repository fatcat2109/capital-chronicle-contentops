"""Read the retained CPI owner and prepare this run's exact amendment review.

No store writes, new model invocation, transport, or external action.
"""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    build_reader_presentation_revision, reader_presentation_acceptance, reader_presentation_revision_view,
)
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from live_contentops.release_chart_revision_v1 import (
    DERIVATIVE_POLICY, derivative_base_payloads, derivative_missing_intent,
)

root = Path(__file__).resolve().parent
run = "cc124-prepare-20261103-a"
store = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
with store.get_read_only_connection() as conn:
    rows = conn.execute("SELECT payload,status FROM outbox_messages WHERE work_item_id=? "
        "AND destination='internal:native-reader-presentation'", (run,)).fetchall()
note = next(json.loads(r[0]) for r in rows if r[1] == "PRESENTATION_EDIT_CONFIRMED")
base = json.loads(store.get_outbox_message("cc-editorial-final-" + sha256_of(run))["payload"])
parent, accepted, acceptance = reader_presentation_acceptance(store, run_id=run, reference=note["review_reference"])
canonical = json.loads(store.get_outbox_message(parent["objects"]["substack"]["message_id"])["payload"])
canonical["canonical_url"] = parent["objects"]["substack"]["public_object_url"]
payloads = derivative_base_payloads(store, run_id=run, accepted=accepted, canonical_intent=canonical)
request = {"item": "CC-179", "task": "Review the unchanged accepted CPI article and exact canonical-bound social copy, then choose useful accepted media in this run. Preserve source dates and original approval; confirmed objects are edited, uncertain attempts are readback-only.",
    "canonical_review_reference": note["review_reference"], "accepted_canonical_revision": acceptance["article_revision"],
    "article_title": accepted["article"]["title"], "article_body": accepted["article"]["substack_body_markdown"],
    "media": [{k: a.get(k) for k in ("asset_id", "path", "sha256", "modality", "caption", "alt_text", "source_page_url")}
        for a in accepted["media_assets"]], "payloads": payloads,
    "cutoff_utc": parent["official_history"]["cutoff_utc"], "history_window": parent["official_history"]["window"],
    "original_approval_not_refreshed": True}


def save(name, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    if b"data:image" in data or b";base64," in data:
        raise ValueError("BINARY_MEDIA_MUST_STAY_IN_FILES")
    (root / name).write_bytes(data)


if sys.argv[1:] == ["request"]:
    save("cpi-amendment-review-request.json", request)
    print(json.dumps({"path": str(root / "cpi-amendment-review-request.json"), "payloads": {
        d: {"length": len(p.get("text", "")), "canonical_pending": "pending-publication" in json.dumps(p),
            "text": p.get("text", "")[:1000]} for d, p in payloads.items()}}))
else:
    response_path = root / "cpi-amendment-review-response.json"
    response = json.loads(response_path.read_bytes())
    proposal = {"policy": DERIVATIVE_POLICY, "run_id": run, "article_identity": base["article_identity"],
        "canonical_review_reference": note["review_reference"], "accepted_canonical_revision": acceptance["article_revision"],
        "article": deepcopy(accepted["article"]), "plan_hash": canonical["plan_hash"],
        "objects": {"substack": parent["objects"]["substack"]}, "original_intent_sha256": {}, "missing_intents": {},
        "channel_media": response["channel_media"], "payloads": {}, "amendment_writer": {
            "request_path": str(root / "cpi-amendment-review-request.json"),
            "request_sha256": sha256((root / "cpi-amendment-review-request.json").read_bytes()).hexdigest(),
            "response_path": str(response_path), "response_sha256": sha256(response_path.read_bytes()).hexdigest(),
            "invocation_observation": response["invocation_observation"]}}
    dispatches = {d["platform"]: d for d in store.get_dispatches_for_work_item(run)}
    for d, payload in payloads.items():
        ids = DurablePublicationCoordinator._ids(run, canonical["plan_hash"], d)
        row = store.get_outbox_message(ids["message_id"])
        proposal["original_intent_sha256"][d] = sha256_of(json.loads(row["payload"])) if row else None
        if row is None:
            proposal["missing_intents"][d] = derivative_missing_intent(canonical, d, payload)
        dispatch = dispatches.get(d, {})
        confirmed = dispatch.get("status") == "DISPATCH_CONFIRMED"
        proposal["objects"][d] = {"message_id": ids["message_id"], "dispatch_id": ids["dispatch_id"], "platform": d,
            "public_object_id": dispatch.get("public_object_id") if confirmed else None,
            "public_object_url": dispatch.get("public_object_url") if confirmed else None}
        amended = deepcopy(payload)
        amended["media_asset_ids"] = proposal["channel_media"][d]
        for i, post in enumerate(amended.get("posts", [])):
            if isinstance(post, dict):
                post["media_asset_ids"] = proposal["channel_media"][d] if i == 0 else []
        proposal["payloads"][d] = amended
    revision = build_reader_presentation_revision(store, run_id=run, proposal=proposal, owner_authority_ref="human:BACKLOG_CC179")
    view = reader_presentation_revision_view(store, run_id=run, result=base, revision=revision)
    save("cpi-derivative-revision.json", revision)
    save("cpi-derivative-view.json", view)
    save("cpi-revision-validation.json", {"observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "VALIDATED_REVIEW_INPUT_NOT_BOUND_OR_DISPATCHED", "run_id": run,
        "canonical_url": canonical["canonical_url"], "eight_payloads": len(revision["payloads"]),
        "channel_media": revision["channel_media"], "public_write_performed": False,
        "production_store_written": False, "invocation_id": os.environ.get("CODEX_THREAD_ID")})
    print(json.dumps({"state": "VALIDATED_REVIEW_INPUT_NOT_BOUND_OR_DISPATCHED", "media": len(view["media_assets"]),
        "destinations": len(revision["payloads"]), "public_write_performed": False}))
