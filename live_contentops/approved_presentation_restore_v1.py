"""Restore an approved Substack presentation without changing its copy or media."""
import json

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of


def restore_intent(store, dispatch_id):
    dispatch = store.get_platform_dispatch(dispatch_id) or {}
    message = store.get_outbox_message(dispatch.get("message_id", "")) or {}
    destination = dispatch.get('platform')
    if (destination not in {"substack", "substack_notes"} or dispatch.get("status") != "DISPATCH_CONFIRMED"
            or not dispatch.get("public_object_id") or not dispatch.get("public_object_url")
            or message.get("destination") != destination):
        raise ValueError("APPROVED_PRESENTATION_EXACT_CONFIRMED_SUBSTACK_REQUIRED")
    original = json.loads(message["payload"])
    if destination == 'substack_notes':
        from .plan_status_posts_v1 import _row_payload, validate_status_post_intent
        row = _row_payload(store, original.get('plan_status_post') or '')
        if row.get('cc603_contract') != 'CC603_V1' or row.get('kind') != 'call_followup':
            raise ValueError('CC603_EXACT_FOLLOWUP_RESTORE_REQUIRED')
        validate_status_post_intent(store, original)
    else:
        from live_contentops.native_desktop_editorial_v1 import require_current_final_visual_review
        require_current_final_visual_review(store, run_id=original["work_item_id"])
    return {**original, "approved_presentation_restore": {
        "reason": "RESTORE_APPROVED_MEDIA_PRESENTATION",
        "dispatch_id": dispatch_id, "original_intent_sha256": sha256_of(original)}}
