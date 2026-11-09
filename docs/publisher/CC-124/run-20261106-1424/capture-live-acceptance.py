"""Capture existing live consumers and exact public readbacks for this one article."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_content_v1 import PRODUCTION_STORE
from live_contentops.native_newsroom_volume_v1 import persist_native_day_measurement
from live_contentops.neo_destination_handoff_v1 import _text

BASE = Path(__file__).resolve().parent
WORK = "cc124-six-markets-20261106-v1"
binding = json.loads(Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-six-markets-20261106-v1\binding.json").read_bytes())
store = ContentOpsDurableStore(PRODUCTION_STORE, auto_migrate=False)
packet = json.loads((BASE / "publication-resume-07-expanded.json").read_bytes())
publication = packet["publication"]
assert publication["state"] == "RECONCILED"
assert not publication["pending_requests"] and publication["unknown_write_count"] == 0
rows = []
with store.get_read_only_connection() as conn:
    records = conn.execute("SELECT d.dispatch_id,d.platform,d.status,d.public_object_id,d.public_object_url "
        "FROM platform_dispatches d JOIN outbox_messages m ON d.message_id=m.message_id "
        "WHERE m.work_item_id=? ORDER BY d.platform", (WORK,)).fetchall()
    for record in records:
        item = dict(record)
        readbacks = []
        for r in conn.execute("SELECT read_at,readback_data FROM readbacks WHERE dispatch_id=? ORDER BY read_at", (item["dispatch_id"],)):
            saved = json.loads(r["readback_data"])
            rb = saved.get("readback") or saved
            readbacks.append({"read_at_utc": r["read_at"], **{k: rb[k] for k in ["verified", "source_status", "identity_match",
                "meaningful_media_visible", "observed_public_object_id", "observed_public_object_url", "content_binding_checks"] if k in rb}})
        item["readbacks"] = readbacks
        assert item["status"] == "DISPATCH_CONFIRMED" and readbacks
        assert readbacks[-1].get("verified") is True, item["platform"]
        rows.append(item)
assert len(rows) == 10
# Native rich text inserts the full lawful photo credit and alt text between body
# paragraphs. Check every exact approved paragraph, in order, against actual readback.
payload = json.loads((BASE / "substack-native-payload.json").read_bytes())
observed = json.loads((BASE / "substack-readback-response.json").read_bytes())["result"]["observed_text"]
remaining = _text(observed)
paragraphs = payload["body_markdown"].split("\n\n")
for paragraph in paragraphs:
    wanted = _text(paragraph)
    assert wanted in remaining, wanted[:70]
    remaining = remaining.split(wanted, 1)[1]
assert _text(payload["title"]) in _text(observed)
assert _text(payload["subtitle"]) in _text(observed)
day_path = Path(persist_native_day_measurement(store, binding))
day = json.loads(day_path.read_bytes())
measurement = day["native_volume_measurement"]
assert measurement["distinct_canonical_items_published"] >= 2
assert any(r.get("public_object_id") == "223739949" and r["channel"] == "substack" for r in measurement["reader_counts"])
digest = json.loads((BASE / "digest-live-consumer.json").read_bytes())
assert digest["eligible_for_next_daily_digest"] and digest["published_feed_rows"] == 1
result = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "operation_id": WORK,
    "state": publication["state"], "canonical_url": publication["canonical_url"],
    "unknown_write_count": 0, "pending_requests": [], "confirmed_destinations": rows,
    "substack_exact_prose": {"approved_paragraphs": len(paragraphs), "all_present_in_order": True,
        "title_match": True, "subtitle_match": True,
        "native_binding_limitation": "The saved native contiguous-text check is false because the public full photo credit and image alt text interrupt the body. All approved prose paragraphs match in order; source-bound public originals hash-match. The stored result is preserved."},
    "production_day": {"path": str(day_path), "day": day["newsroom_production_day_id"],
        "distinct_canonicals": measurement["distinct_canonical_items_published"], "new_canonical_in_consumer": True},
    "digest_consumer": {"evidence": "digest-live-consumer.json", "next_cutoff_utc": digest["next_cutoff_utc"], "email_sent": False},
    "publication_timing": {"first_text_approval_utc": json.loads((BASE / "editor-check-result.json").read_bytes())["first_text_approval_utc"], "canonical_publish_utc": "2026-11-06T08:42:20.275Z",
        "latest_observed_browser_send_click_utc": "2026-11-06T09:11:15.871Z",
        "last_API_destination_readback_utc": "2026-11-06T09:12:12.747126+00:00", "all_channels_within_15_minutes": False,
        "cause": "Native editor upload handling, browser continuation after task tabs disappeared, and serialized browser distribution exceeded the target; original approval clock retained."},
    "schedule_changed": False, "site_published": False, "source_trace": "source-claim-trace.json",
    "telegram_readback": "telegram-public-readback.json", "editorial_review": "review-response.json"}
(BASE / "live-acceptance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
(BASE / "production-day-refresh.json").write_text(json.dumps(result["production_day"], indent=2) + "\n", encoding="utf-8")
print(json.dumps({"state": result["state"], "verified_destinations": len(rows), "body_paragraphs": len(paragraphs),
    "production_day": result["production_day"], "digest_eligible": True}))
