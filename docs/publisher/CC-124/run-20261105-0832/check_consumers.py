"""Verify the existing publication feed, day record and accepted CC-122 reader."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_newsroom_volume_v1 import persist_native_day_measurement
from live_contentops.published_content_v1 import DEFAULT_FEED, read_records

ROOT = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-b")
binding = json.loads((RUN / "binding.json").read_bytes())
rollout = json.loads((OPERATING / "config/native_desktop_rollout_v1.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
operation = NativeReviewedPublication(store, binding, native_invocation_id="/root", rollout=rollout)
projection = operation.projection()
canonical = next(d for d in projection["destinations"] if d["destination"] == "substack")
assert canonical["status"] == "DISPATCH_CONFIRMED"
assert canonical["reconciliation_status"] == "RECONCILED_CONFIRMED"
day_path = Path(persist_native_day_measurement(store, binding))
day = json.loads(day_path.read_bytes())
feed = [r for r in read_records(DEFAULT_FEED)
    if r["content_id"] == "substack:" + str(canonical["public_object_id"])]
assert len(feed) == 1
measurement = day["native_volume_measurement"]
assert measurement["distinct_canonical_items_published"] >= 2
evidence = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "run_id": binding["run_id"],
    "canonical_feed_path": str(DEFAULT_FEED), "canonical_feed_row": feed[0],
    "production_day_path": str(day_path), "production_day_sha256": hashlib.sha256(day_path.read_bytes()).hexdigest(),
    "production_day_measurement": measurement, "publication": projection,
    "schedule_changed": False, "digest_dispatched": False}
(ROOT / "live-consumer-acceptance.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")

REPOSITORY = Path(r"A:\Capital Chronicle\Worktrees\codex-main-exec")
COMMIT = "e8f565d8f8"
def source(path):
    return subprocess.run(["git", "show", COMMIT + ":" + path], cwd=REPOSITORY,
        capture_output=True, text=True, encoding="utf-8", check=True).stdout

consumer_source = source("tools/product/contentops_digest_v1.py")
consumer = types.ModuleType("accepted_cc122_contentops_reader")
exec(compile(consumer_source, "<accepted-cc122-contentops-reader>", "exec"), consumer.__dict__)
main_source = source("tools/product/main_daily_digest_v1.py")
reader_node = next(n for n in ast.parse(main_source).body if isinstance(n, ast.ClassDef) and n.name == "Reader")
namespace = {"Path": Path, "hashlib": hashlib, "json": json}
exec(compile(ast.Module(body=[reader_node], type_ignores=[]), "<accepted-cc122-reader>", "exec"), namespace)
record = consumer.default_production_record(datetime(2026, 11, 6, 0, 0, tzinfo=timezone.utc))
assert record == day_path
result = consumer.collect_contentops(namespace["Reader"](), record=record,
    store=consumer.STORE, now=datetime.now(timezone.utc))
assert result["state"] == "SAVED_RECORD"
assert result["distinct_articles_published"] == measurement["distinct_canonical_items_published"]
accepted_commit = subprocess.run(["git", "rev-parse", COMMIT], cwd=REPOSITORY,
    capture_output=True, text=True, check=True).stdout.strip()
digest = {"consumer_accepted_commit": accepted_commit,
    "consumer_source_sha256": hashlib.sha256(consumer_source.encode()).hexdigest(),
    "checked_at_utc": datetime.now(timezone.utc).isoformat(), "next_0700_record": str(record),
    "observed_reader_result": result, "schedule_changed": False, "digest_dispatched": False}
(ROOT / "digest-consumer-acceptance.json").write_text(json.dumps(digest, indent=2), encoding="utf-8")
print(json.dumps({"canonical": canonical["public_object_url"],
    "day_count": result["distinct_articles_published"], "reader_state": result["state"],
    "confirmed_copies": result["confirmed_copies_by_channel"],
    "unknown_write_count": projection["unknown_write_count"], "pending_requests": len(projection["pending_requests"])}))
