"""Decision 93: exact-object event card placement; prose and image bytes stay bound."""
from copy import deepcopy
import json

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

POLICY = "JIM_DECISION_93_EVENT_MEDIA_ORDER"


def ordered_view(result, reaction_card):
    view = deepcopy(result)
    article = view["article"]
    if article.get("article_type") not in {"EVENT_PREVIEW", "EVENT_REVIEW"}:
        raise ValueError("EVENT_MEDIA_ORDER_EVENT_REQUIRED")
    assets = view["media_assets"]
    from live_contentops.post_visuals_v1 import validate_post_data_card
    validate_post_data_card(reaction_card, article, view.get("evidence", []))
    lead = deepcopy(reaction_card)
    snapshot = next((a for a in assets if a.get("modality") == "tradingview_chart_snapshot"
        and a.get("article_inclusion") is not False), None)
    if not lead or lead.get("modality") not in {"source_backed_chart", "source_bound_data_card"} or not snapshot:
        raise ValueError("EVENT_MEDIA_ORDER_BOUND_CARD_AND_SNAPSHOT_REQUIRED")
    lead.update(placement_after="standfirst", article_inclusion=True, canonical_article_media=True)
    snapshot["placement_after"] = "standfirst"
    assets = [lead, snapshot, *(a for a in assets if a["asset_id"] not in {lead["asset_id"], snapshot["asset_id"]})]
    decision = article.get("visual_editorial_decision") or {}
    decision["article_media_order"] = [a["asset_id"] for a in assets]
    article["lead_image_asset_id"] = lead["asset_id"]
    article["visual_editorial_decision"] = decision
    view.update(media_assets=assets, visual_editorial_decision=decision)
    return view


def build(store, *, run_id, result, owner_authority_ref, reaction_card):
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
    if owner_authority_ref != "human:BACKLOG_CC338_JIM_DECISIONS_53_93":
        raise ValueError("EVENT_MEDIA_ORDER_OWNER_SCOPE_REQUIRED")
    dispatches = [d for d in store.get_dispatches_for_work_item(run_id)
        if d["platform"] == "substack" and d["status"] == "DISPATCH_CONFIRMED" and d.get("public_object_url")]
    if len(dispatches) != 1:
        raise ValueError("EVENT_MEDIA_ORDER_EXACT_CONFIRMED_OBJECT_REQUIRED")
    dispatch = dispatches[0]
    identity = {k: dispatch[k] for k in ("message_id", "dispatch_id", "platform", "public_object_id", "public_object_url")}
    intent = json.loads(store.get_outbox_message(dispatch["message_id"])["payload"])
    ordered_view(result, reaction_card)
    return {"policy": POLICY, "run_id": run_id, "article_identity": result["article_identity"],
        "owner_authority_ref": owner_authority_ref, "base_result_sha256": sha256_of(result),
        "source_sha256": sha256_of(result.get("evidence", [])), "prior_revision": native_review_revision(result),
        "body_before": result["article"]["substack_body_markdown"],
        "body_after": result["article"]["substack_body_markdown"],
        "reaction_card": reaction_card,
        "objects": {"substack": identity}, "payloads": {},
        "original_intent_sha256": {"substack": sha256_of(intent)}}


def revision_view(store, *, run_id, result, revision):
    if revision != build(store, run_id=run_id, result=result, owner_authority_ref=revision.get("owner_authority_ref"),
            reaction_card=revision.get("reaction_card")):
        raise ValueError("EVENT_MEDIA_ORDER_EXACT_UNCHANGED_PACKAGE_REQUIRED")
    return ordered_view(result, revision["reaction_card"])
