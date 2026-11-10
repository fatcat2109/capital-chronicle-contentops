"""Export CC-338's public-call projection using the existing feed and outbox."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore  # noqa: E402
from live_contentops.public_call_scorecard_v1 import SINCE, build_scorecard, render_scorecard  # noqa: E402
from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--feed", type=Path, default=DEFAULT_FEED)
    parser.add_argument("--since", default=SINCE)
    parser.add_argument("--as-of")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--attach-freeze", metavar="EVENT_ID")
    parser.add_argument("--freeze-file", type=Path)
    parser.add_argument("--freeze-sha256")
    parser.add_argument("--stamp-freeze", metavar="EVENT_ID", help="stamp exact Main public bytes without opening the store")
    parser.add_argument("--upgrade-timestamp", action="store_true")
    parser.add_argument("--timestamp-root", type=Path)
    parser.add_argument("--event-pack", choices=("preview", "arrival", "review"))
    parser.add_argument("--pack-inputs", type=Path)
    parser.add_argument("--resume-pack")
    parser.add_argument("--pack-command", choices=("resume", "readback", "begin", "submit"), default="resume")
    parser.add_argument("--native-invocation-id", default="event-pack-cli-cc404")
    parser.add_argument("--request-sha256")
    parser.add_argument("--response", type=Path)
    parser.add_argument("--attach-arrival", metavar="EVENT_ID")
    parser.add_argument("--arrival-file", type=Path)
    parser.add_argument("--arrival-sha256")
    parser.add_argument("--plan-status-file", type=Path)
    args = parser.parse_args(argv)
    if args.attach_arrival:
        from datetime import datetime, timezone
        from hashlib import sha256
        from live_contentops.contentops_editorial_desk_v1 import STORY_PREPARATION, record_pre_event_preparation
        from live_contentops.event_pack_v1 import PACK_ROOT, STATUS_PATH, _snapshot_inputs, compose
        if not args.arrival_file or not args.arrival_sha256:
            parser.error("--attach-arrival requires --arrival-file and --arrival-sha256")
        store = ContentOpsDurableStore(str(args.store), auto_migrate=False)
        with store.get_read_only_connection() as conn:
            rows = conn.execute("SELECT payload FROM outbox_messages WHERE destination=? ORDER BY rowid", (STORY_PREPARATION,)).fetchall()
        packets = [json.loads(row[0]) for row in rows if json.loads(row[0]).get("event_id") == args.attach_arrival]
        if not packets:
            raise ValueError("PREPARATION_EVENT_NOT_FOUND")
        packet = packets[-1]
        arrival = {"path": str(args.arrival_file.resolve()), "sha256": args.arrival_sha256}
        if packet.get("event_arrival_record"):
            if packet["event_arrival_record"]["sha256"] != args.arrival_sha256:
                raise ValueError("EVENT_PUBLIC_ARRIVAL_IMMUTABLE")
            print(json.dumps({"status": "EXACT_ARRIVAL_ALREADY_ATTACHED", "event_id": args.attach_arrival}))
            return 0
        status_file = args.plan_status_file or STATUS_PATH
        status = {"path": str(status_file.resolve()), "sha256": sha256(status_file.read_bytes()).hexdigest()}
        now = datetime.now(timezone.utc)
        packet.update(event_arrival_record=arrival, plan_status_record=status, known_at_utc=now.isoformat())
        packet = _snapshot_inputs(packet, PACK_ROOT / ("arrival-"+args.attach_arrival) / "sources")
        compose(packet, "arrival", now=now)  # Verify before admitting any public event claim.
        receipt = record_pre_event_preparation(store, packet)
        print(json.dumps({**receipt, "status": "EVENT_ARRIVAL_ATTACHED", "sha256": args.arrival_sha256}))
        return 0
    if args.event_pack or args.resume_pack:
        from live_contentops.event_pack_v1 import PACK_ROOT, register_pack, resume_pack, stage_status, register_derivatives
        store = ContentOpsDurableStore(str(args.store), auto_migrate=False)
        if args.event_pack:
            if not args.pack_inputs:
                parser.error("--event-pack requires --pack-inputs")
            value = register_pack(store, json.loads(args.pack_inputs.read_bytes()), args.event_pack,
                                  root=args.output_dir or PACK_ROOT)
            print(json.dumps(stage_status(store, value)))
        else:
            row = store.get_outbox_message(args.resume_pack)
            if not row:
                raise ValueError("EVENT_PACK_NOT_FOUND")
            value = json.loads(row["payload"])
            result = resume_pack(store, value, invocation_id=args.native_invocation_id, command=args.pack_command,
                request_hash=args.request_sha256, response=json.loads(args.response.read_bytes()) if args.response else None)
            if not value.get("canonical_parent") and stage_status(store, value)["canonical_url"]:
                result = {"canonical": result, "derivatives": register_derivatives(store, value)}
            print(json.dumps(result, default=str))
        return 0
    if args.attach_freeze or args.stamp_freeze:
        from datetime import datetime, timezone
        from live_contentops.contentops_editorial_desk_v1 import STORY_PREPARATION, record_pre_event_preparation
        from live_contentops.event_public_record_v1 import load_record
        from live_contentops.event_timestamp_v1 import ROOT, retain_and_stamp
        if not args.freeze_file or not args.freeze_sha256:
            parser.error("--attach-freeze requires --freeze-file and Ops Live's --freeze-sha256")
        now = datetime.now(timezone.utc).isoformat()
        spec = {"path": str(args.freeze_file.resolve()), "sha256": args.freeze_sha256}
        doc = json.loads(args.freeze_file.read_bytes())
        event_id = args.attach_freeze or args.stamp_freeze
        record = load_record(spec, event_id=event_id, event_time_utc=doc["event_time_utc"], cutoff_utc=now)
        timestamp = retain_and_stamp(spec, event_id=event_id, frozen_at_utc=record["frozen_at_utc"],
            event_time_utc=record["event_time_utc"], root=args.timestamp_root or ROOT,
            upgrade=args.upgrade_timestamp)
        observed = {k: timestamp.get(k) for k in ("status", "proof_path", "proof_sha256", "submitted_at_utc",
                    "submission_before_release", "bitcoin_verified", "cause")}
        if args.stamp_freeze:
            print(json.dumps({"timestamp": observed, "sha256": record["sha256"]}))
            return 0 if timestamp.get("proof_path") else 1
        store = ContentOpsDurableStore(str(args.store), auto_migrate=False)
        with store.get_read_only_connection() as conn:
            rows = conn.execute("SELECT payload FROM outbox_messages WHERE destination=? ORDER BY rowid",
                                (STORY_PREPARATION,)).fetchall()
        packets = [json.loads(row[0]) for row in rows if json.loads(row[0]).get("event_id") == args.attach_freeze]
        if not packets:
            raise ValueError("PREPARATION_EVENT_NOT_FOUND")
        packet = packets[-1]
        if packet["planned_release_utc"] != record["event_time_utc"]:
            raise ValueError("FROZEN_PUBLIC_RECORD_EVENT_OR_SCHEMA_INVALID")
        if (packet.get("frozen_public_record") or {}).get("sha256") == spec["sha256"]:
            print(json.dumps({"status": "EXACT_FREEZE_ALREADY_ATTACHED", "sha256": record["sha256"], "timestamp": observed}))
            return 0
        if packet.get("frozen_public_record"):
            raise ValueError("EXISTING_EVENT_PUBLIC_FREEZE_IMMUTABLE")
        packet.update(frozen_public_record=spec, known_at_utc=now, event_pack_enabled=True, event_pack_live_sources=True)
        from live_contentops.event_pack_v1 import freeze_ledger
        packet = freeze_ledger(packet)
        receipt = record_pre_event_preparation(store, packet)
        print(json.dumps({**receipt, "sha256": record["sha256"], "frozen_at_et": record["frozen_at_et"], "timestamp": observed}))
        return 0
    if not args.output_dir:
        parser.error("--output-dir is required for the scorecard export")
    store = ContentOpsDurableStore(str(args.store), auto_migrate=False)
    scorecard = build_scorecard(store, feed_path=args.feed, since_utc=args.since, as_of_utc=args.as_of)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "public-call-scorecard.json").write_text(
        json.dumps(scorecard, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "public-call-scorecard.md").write_text(render_scorecard(scorecard), encoding="utf-8")
    print(json.dumps({"total_calls": scorecard["total_calls"], "state_counts": scorecard["state_counts"],
                      "output_dir": str(args.output_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
