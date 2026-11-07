"""Read the retained NFP operation and installed publication consumers."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
TREE = HERE.parents[3]
sys.path.insert(0, str(LIVE))

from live_contentops import published_images_v1 as images
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.published_content_v1 import read_records

now = datetime.now(timezone.utc)
operation = RUNTIME / "daily_app_outputs/owner-manual/cc124-nfp-arrival-review-20261106-v1"
binding_path = operation / "binding.json"
request_path = operation / "desktop_request_write.json"
binding = json.loads(binding_path.read_bytes())
request = json.loads(request_path.read_bytes())
assert request["request_sha256"] == sha256_of({k: v for k, v in request.items() if k != "request_sha256"})
feed_path = RUNTIME / "published_content_v1.jsonl"
feed = read_records(feed_path)
register = images.PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=feed_path)
daily = register._daily_pieces(register.records(), now)
connection = sqlite3.connect(Path(binding["store_path"]).as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
with connection:
    leases = [dict(row) for row in connection.execute(
        "SELECT lease_id,lease_key,status,expires_at FROM leases "
        "WHERE status='ACTIVE' AND expires_at>?", (now.isoformat().replace("+00:00", "Z"),))]
connection.close()
governed = request.get("governed_input", {})
summary = {
    "observed_at_utc": now.isoformat(), "item": "CC-124",
    "operating_head": subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip(),
    "production_date": images.day_of(now), "article_limit": images.daily_limit(now),
    "occupied_article_slots": len(daily), "active_leases": leases,
    "operation_id": binding["run_id"], "binding_path": str(binding_path),
    "binding_file_sha256": sha256(binding_path.read_bytes()).hexdigest(),
    "cutoff_utc": binding["cutoff_utc"], "writer_request_sha256": request["request_sha256"],
    "writer_request_file_sha256": sha256(request_path.read_bytes()).hexdigest(),
    "writer_return_present": (operation / "desktop_response_write.json").exists(),
    "governed_input_keys": sorted(governed),
    "source_pack": [{k: source.get(k) for k in ("source_id", "title", "source_url", "url", "known_at_utc", "published_at_utc", "content_path")} for source in governed.get("source_pack", [])],
    "latest_published": [{k: row.get(k) for k in ("content_id", "title", "published_at_utc")} for row in feed[-5:]],
    "configured_launch": json.loads(Path(r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\codex-exec\publisher-cc-124-20261107T0832\launch.json").read_bytes()),
    "inherited_files_sha256": {str(path.relative_to(TREE)): sha256(path.read_bytes()).hexdigest() for path in (
        TREE / "docs/automation/V6_LIVE_TELEMETRY/live_telemetry_registry_v6.jsonl",
        TREE / "docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl")},
}
(HERE / "resume-check.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: summary[k] for k in ("observed_at_utc", "production_date", "article_limit", "occupied_article_slots", "active_leases", "operation_id", "writer_return_present", "source_pack")}))
