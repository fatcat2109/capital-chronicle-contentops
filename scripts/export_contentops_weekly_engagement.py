"""Export the ten-channel engagement section for the weekly digest, read-only."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import json
import sqlite3
import sys
from contextlib import nullcontext

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.channel_engagement_v1 import weekly_channel_engagement, render_engagement_digest, weekly_audience_lines
from live_contentops.audience_collection_v1 import dispatch_call_ids
from live_contentops.audience_feedback_v1 import SCHEMA, post_type, project_audience


def export_weekly_engagement(store, week_ending, target):
    """The minute consumer refreshes this existing digest export; no new schedule."""
    target = Path(target).resolve()
    desk_target = Path(store).resolve().parent / "audience-weekly/latest.json"
    try:
        previous = json.loads(desk_target.read_bytes())
        if previous.get("schema_version") != SCHEMA or previous.get("input_store") != str(Path(store).resolve()):
            previous = None
    except (OSError, ValueError):
        previous = None
    with sqlite3.connect(Path(store).resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        def rows(table):
            return [dict(r) for r in connection.execute("SELECT * FROM " + table)]
        class ReadSnapshot:
            def get_outbox_message(self, message_id):
                row = connection.execute("SELECT * FROM outbox_messages WHERE message_id=?", (message_id,)).fetchone()
                return dict(row) if row else None
            def get_read_only_connection(self):
                return nullcontext(connection)
        dispatches = rows("platform_dispatches")
        observations = rows("performance_observations")
        reconciliations, readbacks = rows("reconciliations"), rows("readbacks")
        observed_ids = {o["dispatch_id"] for o in observations}
        bindings = {d["dispatch_id"]: dispatch_call_ids(ReadSnapshot(), d) for d in dispatches if d["dispatch_id"] in observed_ids}
        value = weekly_channel_engagement(dispatches=dispatches, reconciliations=reconciliations,
            readbacks=readbacks, observations=observations, week_ending=week_ending, call_bindings=bindings)
        metadata = {}
        snapshot = ReadSnapshot()
        for dispatch in dispatches:
            intent = json.loads((snapshot.get_outbox_message(dispatch["message_id"]) or {}).get("payload") or "{}")
            source = snapshot.get_outbox_message(intent.get("plan_status_post") or intent.get("work_item_id"))
            metadata[dispatch["dispatch_id"]] = post_type(intent, json.loads((source or {}).get("payload") or "{}"))
        desk = project_audience(dispatches=dispatches, reconciliations=reconciliations, readbacks=readbacks,
            observations=observations, metadata=metadata, now=datetime.now(timezone.utc), previous=previous)
    value["recorded_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    value["input_store_read_only"] = True
    value["digest_lines"] = weekly_audience_lines(value)
    desk.update(input_store=str(Path(store).resolve()), week_ending=week_ending,
                digest_lines=value["digest_lines"], channels=value["channels"])
    target.mkdir(parents=True, exist_ok=True)
    for filename, payload in [("engagement.json", json.dumps(value, indent=2) + "\n"),
                              ("engagement.md", "\n".join(value["digest_lines"]) + "\n\n" + render_engagement_digest(value))]:
        temporary = target / (filename + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(target / filename)
    desk_target.parent.mkdir(parents=True, exist_ok=True)
    temporary = desk_target.with_suffix(".tmp")
    temporary.write_text(json.dumps(desk, indent=2) + "\n", encoding="utf-8")
    temporary.replace(desk_target)
    return {"channels": len(value["channels"]), "digest": str(target / "engagement.md"),
            "desk": str(desk_target), "week_ending": week_ending}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--week-ending", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_weekly_engagement(args.store, args.week_ending, args.output_dir)))


if __name__ == "__main__":
    main()
