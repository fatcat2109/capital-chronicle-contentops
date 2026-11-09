"""CC-359's supplied correction, using the existing status-post package and publisher."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from live_contentops import plan_status_posts_v1 as posts

KEY = "cc359-zone-correction-20261109"
ORIGINAL_KEYS = ("plan-status-post-a47bf553fcd41d7cecd0ba4f2aa3a6ea",
                 "plan-status-post-7de05797da876f17c7392552e64d2f22")
BODY = ("Correction: our 04:16 ET EUR/USD and 04:18 ET US crude oil updates said price had reached "
        "the entry zone. It had not: at those times both plans were still waiting for price to reach "
        "their zones, EUR/USD 1.1166–1.117 and US crude oil 90.2–90.45.")
TEXT = BODY + "\n\n" + posts.PUBLIC_NOTICE + " " + posts.CONFLICTS_NOTICE
ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\plan-status-posts")


def prepare(store, *, root=ROOT, host=None):
    """Freeze once. Originals are read, never amended; one durable dispatch per destination."""
    existing = store.get_outbox_message(KEY)
    if not existing:
        originals = {d: [] for d in posts.POST_DESTINATIONS}
        for key in ORIGINAL_KEYS:
            original = store.get_outbox_message(key)
            if not original or original["destination"] != posts.DESTINATION:
                raise ValueError("CC359_ORIGINAL_STATUS_ROW_REQUIRED:" + key)
            for dispatch in store.get_dispatches_for_work_item(key):
                if dispatch["status"] != "DISPATCH_CONFIRMED":
                    continue
                destination = dispatch["platform"]
                if destination in originals:
                    originals[destination].append({"work_item_id": key,
                        "public_object_id": dispatch["public_object_id"],
                        "public_object_url": dispatch.get("public_object_url")})
        store.create_work_item(story_id=KEY, title="Correct the 9 November zone updates",
                               target_surface="MULTI_PLATFORM", work_item_id=KEY)
        row = {"schema_version": posts.SCHEMA, "key": KEY, "symbol": "EURUSD", "state": "CORRECTION",
               "at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
               "text": TEXT, "conditional_calls": [], "correction_of": originals,
               "authority": "BACKLOG CC-359; supplied text; Jim decisions 40 and 83",
               "placement": {"discord": "NEW_POST_WEBHOOK_HAS_NO_NATIVE_MESSAGE_REPLY",
                             "x": "NEW_POST_IF_NO_CONFIRMED_ORIGINAL",
                             "substack_notes": "NEW_POST_IF_NO_CONFIRMED_ORIGINAL"}}
        store.register_outbox_message(message_id=KEY, work_item_id=KEY, destination=posts.DESTINATION,
                                      payload=json.dumps(row, ensure_ascii=False), status="CORRECTION_PREPARED")
    row = posts._row_payload(store, KEY)
    if row["text"] != TEXT:
        raise ValueError("CC359_SUPPLIED_CORRECTION_CHANGED")
    return posts.prepare_post(store, KEY, root=root, host=host)


def bind(store, *, root=ROOT, invocation):
    from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator
    coordinator, executor = bind_native_neo_coordinator(store, operation_id=KEY,
        output_dir=Path(root) / KEY / "native-neo", native_invocation_id=invocation, allow_publish=True)
    posts.scope_to_post(coordinator, KEY, {"plan_status_post": KEY})
    return coordinator, executor
