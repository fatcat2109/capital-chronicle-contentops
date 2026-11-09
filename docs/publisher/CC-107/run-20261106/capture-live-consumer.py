"""Read this event's public record through production-day and installed digest owners."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_newsroom_volume_v1 import persist_native_day_measurement
from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE, read_records


def main(binding_path):
    binding = json.loads(Path(binding_path).read_bytes())
    store = ContentOpsDurableStore(PRODUCTION_STORE, auto_migrate=False)
    with store.get_read_only_connection() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT d.dispatch_id,d.platform,d.status,d.public_object_id,d.public_object_url,d.dispatched_at "
            "FROM platform_dispatches d JOIN outbox_messages m ON m.message_id=d.message_id "
            "WHERE m.work_item_id=? ORDER BY d.platform", (binding["run_id"],))]
    canonical = [r for r in rows if r["platform"] == "substack" and r["status"] == "DISPATCH_CONFIRMED"]
    if len(canonical) != 1:
        raise ValueError("ONE_CONFIRMED_CANONICAL_REQUIRED_FOR_CONSUMER_READBACK")
    url = canonical[0]["public_object_url"]
    records = [r for r in read_records(DEFAULT_FEED)
        if any(o["name"] == "substack" and o["url"] == url for o in r["outlets"])]
    if len(records) != 1 or records[0]["type"] != "EVENT_PREVIEW":
        raise ValueError("ONE_EVENT_PREVIEW_REQUIRED_IN_LIVE_PUBLISHED_FEED")
    record = Path(persist_native_day_measurement(store, binding))
    day = json.loads(record.read_bytes())
    # Resolve the installed version through shared Git metadata; never open or
    # mutate the Main operating-root checkout.
    git = r"A:\Capital Chronicle\Worktrees\codex-main-exec"
    metadata = subprocess.check_output(["git", "-C", git, "worktree", "list", "--porcelain"], text=True)
    block = next(b for b in metadata.strip().split("\n\n") if b.splitlines()[0].lower()
        == "worktree a:/capital chronicle/main-jim-research-dashboard-20261025")
    head = next(line[5:] for line in block.splitlines() if line.startswith("HEAD "))
    source = subprocess.check_output(["git", "-C", git, "show", head + ":tools/product/contentops_digest_v1.py"])
    caller = subprocess.check_output(["git", "-C", git, "show", head + ":tools/product/main_daily_digest_v1.py"])
    module = types.ModuleType("cc107_installed_digest")
    exec(compile(source, "installed-contentops-digest@" + head, "exec"), module.__dict__)

    class Reader:
        def __init__(self):
            self.evidence = {}

        def read(self, path, label):
            raw = Path(path).read_bytes()
            self.evidence[str(path)] = {"label": label, "state": "READ", "sha256": sha256(raw).hexdigest()}
            return json.loads(raw)

    reader = Reader()
    now = datetime.now(timezone.utc)
    consumer = module.collect_contentops(reader, record=record, store=Path(PRODUCTION_STORE), now=now)
    count = day["native_volume_measurement"]["distinct_canonical_items_published"]
    if consumer["state"] != "SAVED_RECORD" or consumer["distinct_articles_published"] != count:
        raise ValueError("INSTALLED_DIGEST_MUST_CONSUME_THE_CURRENT_PRODUCTION_RECORD")
    wiring = [{"line": i, "source": line.strip()} for i, line in enumerate(caller.decode().splitlines(), 1)
        if "contentops_digest_v1 import" in line or "contentops = collect_contentops(" in line
        or "newsroom['distinct_articles_published']" in line]
    if len(wiring) != 3:
        raise ValueError("INSTALLED_DIGEST_WIRING_CHANGED")
    result = {"observed_at_utc": now.isoformat(), "operation_id": binding["run_id"], "canonical_url": url,
        "published_feed_rows": len(records), "article_type": records[0]["type"],
        "public_dispatch_states": rows, "production_record": str(record), "distinct_canonicals": count,
        "installed_main_commit": head, "installed_digest_sha256": sha256(source).hexdigest(),
        "installed_main_digest_sha256": sha256(caller).hexdigest(), "installed_wiring": wiring,
        "consumer": consumer, "reader_evidence": reader.evidence, "email_sent": False,
        "schedule_changed": False}
    (HERE / "live-consumer-readback.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["canonical_url", "article_type", "published_feed_rows",
        "distinct_canonicals", "installed_main_commit", "email_sent"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--binding", required=True)
    main(parser.parse_args().binding)
