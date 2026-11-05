"""Save bounded terminal evidence, without dispatching or changing schedules."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
names = ["x-composed-response", "youtube-composed-response", "linkedin-company-composed-response",
    "substack-credit-edit-response", "substack-credit-final-readback-response", "x-final-readback-response",
    "linkedin-company-final-readback-response", "youtube-final-readback-response",
    "linkedin-absence-current-final-readback-response", "social-public-image-verification",
    "credit-restore-current", "x-link-resolution-observed", "linkedin-company-link-resolution-observed"]
artifacts = []
for name in names:
    source = ROOT / (name + ".json")
    raw = source.read_bytes()
    assert len(raw) < 256_000 and b"data:image/" not in raw and b'"screenshot_base64"' not in raw, source
    shutil.copyfile(source, HERE / source.name)
    artifacts.append({"path": source.name, "size_bytes": len(raw), "sha256": sha256(raw).hexdigest()})
consumer = json.loads((HERE / "live-consumer-acceptance.json").read_bytes())
projection = consumer["publication"]
assert projection["unknown_write_count"] == 0 and not projection["pending_requests"]
restore = json.loads((ROOT / "credit-restore-current.json").read_bytes())
assert restore["readback"]["verified"] is True and restore["new_post_calls"] == 0
outcome = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(), "operation_id": ROOT.name,
    "article_identity": "e8c284c6d4b67e7ec32cfe4f99432ef5052b0a027a84ad976bd010bcdb4d5f96",
    "canonical_url": consumer["canonical_feed_row"]["canonical_url"] if "canonical_url" in consumer["canonical_feed_row"] else consumer["canonical_feed_row"].get("url"),
    "published_at_utc": consumer["canonical_feed_row"]["published_at_utc"],
    "distinct_articles_published": consumer["production_day_measurement"]["distinct_canonical_items_published"],
    "unknown_write_count": 0, "pending_requests": 0, "standing_item_status": "OPEN",
    "destinations": [{k: d.get(k) for k in ("destination", "status", "reconciliation_status", "public_object_id", "public_object_url")}
        for d in projection["destinations"]],
    "limitations": ["YOUTUBE_EXISTING_TEXT_POST_CANNOT_ATTACH_MEDIA: text published; chart absent and not counted as complete delivery",
        "LinkedIn personal API post absent in authenticated activity feed; company copy confirmed",
        "15-minute dispatch target missed; first text approval remains 2026-11-05T14:45:42.461172+00:00"],
    "schedules_changed": False, "chat_messages_sent": False, "artifacts": artifacts}
outcome["canonical_url"] = next(d["public_object_url"] for d in projection["destinations"] if d["destination"] == "substack")
(HERE / "run-outcome.json").write_text(json.dumps(outcome, indent=2), encoding="utf-8")
print(json.dumps({"files": len(artifacts), "bytes": sum(a["size_bytes"] for a in artifacts),
    "day_count": outcome["distinct_articles_published"], "unknown_write_count": 0, "pending_requests": 0}))
