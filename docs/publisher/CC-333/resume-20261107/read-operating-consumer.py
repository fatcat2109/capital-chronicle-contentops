"""Read installed consumers and their actual inputs without a runtime mutation."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))

from live_contentops import article_publication_quality_v1 as quality
from live_contentops import published_images_v1 as images
from live_contentops import tradingview_snapshot_v1 as tradingview
from live_contentops.event_article_guard_v1 import event_writer_guidance
from live_contentops.native_publication_promotion_v1 import ReadOnlyStore
from live_contentops.published_content_v1 import read_records

HERE = Path(__file__).resolve().parent
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
OPERATION = RUNTIME / "daily_app_outputs/owner-manual/cc124-nfp-arrival-review-20261106-v1"
FEED = RUNTIME / "published_content_v1.jsonl"
REGISTER = RUNTIME / "published_images_v1.jsonl"
now = datetime.now(timezone.utc)
rows = read_records(FEED)
register = images.PublishedImages(REGISTER, published_feed=FEED)
registry_rows = register.records()
daily = register._daily_pieces(registry_rows, now)
store = ReadOnlyStore(RUNTIME / "contentops_daily_app_v1.sqlite3")
request_path = OPERATION / "desktop_request_write.json"
request = json.loads(request_path.read_bytes())
run_id = request["run_id"]
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
work = "cc-opportunity-" + sha256_of(run_id)
dispatches = [{"platform": row["platform"], "status": row["status"]}
              for identity in (work, run_id) for row in store.get_dispatches_for_work_item(identity)]
modules = [quality, images, tradingview]
result = {"observed_at_utc": now.isoformat(), "operating_root": str(LIVE),
    "operating_head": subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip(),
    "installed_modules": [{"path": m.__file__, "sha256": sha256(Path(m.__file__).read_bytes()).hexdigest()} for m in modules],
    "publication_feed": str(FEED), "feed_sha256": sha256(FEED.read_bytes()).hexdigest(),
    "latest_canonical_publication_utc": max(row["published_at_utc"] for row in rows),
    "feed_articles": len(rows), "image_register": str(REGISTER), "image_observation_records": len(registry_rows),
    "production_date": images.day_of(now), "daily_article_limit": images.daily_limit(now),
    "occupied_article_slots": len(daily), "remaining_capacity": max(0, images.daily_limit(now) - len(daily)),
    "free_ram_skip_removed": "MIN_FREE_RAM_GB" not in Path(tradingview.__file__).read_text(encoding="utf-8"),
    "event_review_guidance_has_writing_notice": "Retrospective analysis, written on " in event_writer_guidance({"article_type": "EVENT_REVIEW"}),
    "retained_operation": run_id, "binding_path": str(OPERATION / "binding.json"),
    "binding_sha256": sha256((OPERATION / "binding.json").read_bytes()).hexdigest(),
    "pending_request_path": str(request_path), "pending_request_sha256": request["request_sha256"],
    "pending_request_file_sha256": sha256(request_path.read_bytes()).hexdigest(), "operation_dispatches": dispatches,
    "new_public_piece_readbacks": 0, "required_public_piece_readbacks": 2,
    "first_cause": "JIM_DECISION_94_CC124_NOT_DUE", "next_existing_run_utc": "2026-11-07T08:01:00Z",
    "next_existing_run_gmt7": "7 Nov 2026 15:01 GMT+7",
    "next_action": "Codex Publisher resumes the retained CC-124 binding at its due run under decision 94; retain exact Substack and social readbacks for the next two compliant pieces.",
    "new_public_writes": 0, "schedules_changed": False, "process_restarts": 0, "reads_only": True}
(HERE / "operating-consumer-read.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in ("operating_head", "production_date", "daily_article_limit",
    "occupied_article_slots", "remaining_capacity", "new_public_piece_readbacks", "first_cause")}))
