"""CC-377: inspect the installed consumer and frozen digest; no store writes."""
import hashlib
import inspect
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator


def main():
    rollout = json.loads((ROOT / "config/native_desktop_rollout_v1.json").read_bytes())
    db = Path(rollout["store_path"])
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as conn:
        conn.execute("PRAGMA query_only=ON")
        raw_packets = [row[0] for row in conn.execute(
            "SELECT payload FROM outbox_messages WHERE destination=?",
            ("internal:substack-daily-digest",))]
        packets = [json.loads(raw) for raw in raw_packets]
        packet = next(p for p in packets if p["digest_id"] == "cc143-digest-2026-11-09")
        raw_packet = next(raw for raw, p in zip(raw_packets, packets) if p == packet)
        missed = next(a for a in packet["articles"] if a["content_id"] == "substack:224085585")
        allocations = sum(a["url"] == missed["url"] for p in packets for a in p["articles"])
        assert allocations == 1
        canonical = conn.execute(
            "SELECT status,public_object_url FROM platform_dispatches "
            "WHERE platform='substack' AND public_object_id=?", ("224085585",)).fetchone()
        assert canonical == ("DISPATCH_CONFIRMED", missed["url"])
        dispatch_id = DurablePublicationCoordinator._ids(
            packet["digest_id"], packet["plan"]["plan_hash"], "substack")["dispatch_id"]
        digest_dispatch = conn.execute(
            "SELECT status,public_object_id,public_object_url FROM platform_dispatches "
            "WHERE dispatch_id=?", (dispatch_id,)).fetchone()
    guard = inspect.getsource(DurablePublicationCoordinator.recovery_blocks_new_publication)
    recovery = inspect.getsource(DurablePublicationCoordinator.recover_pending)
    assert "self._recovery_messages()" in guard and "self._recovery_messages()" in recovery
    source = Path(inspect.getfile(DurablePublicationCoordinator))
    assert source.resolve().is_relative_to(ROOT.resolve())
    result = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "operating_root": str(ROOT),
        "head": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "consumer": str(source),
        "consumer_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "recovery_and_guard_share_scope": True,
        "digest_id": packet["digest_id"],
        "frozen_packet_sha256": hashlib.sha256(raw_packet.encode()).hexdigest(),
        "cutoff_utc": packet["cutoff_utc"],
        "missed_article": missed,
        "allocated_digest_count": allocations,
        "digest_dispatch": digest_dispatch,
        "scheduled_acceptance_pending": "10 Nov 2026 19:00 GMT+7 cc-contentops-digest-1900-bp",
        "public_write_performed": False,
        "schedule_changed": False,
    }
    output = Path(__file__).with_name("live-consumer.json")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
