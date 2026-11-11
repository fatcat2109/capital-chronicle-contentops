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


def export_weekly_engagement(store, week_ending, target):
    """The minute consumer refreshes this existing digest export; no new schedule."""
    target = Path(target).resolve()
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
        observed_ids = {o["dispatch_id"] for o in observations}
        bindings = {d["dispatch_id"]: dispatch_call_ids(ReadSnapshot(), d) for d in dispatches if d["dispatch_id"] in observed_ids}
        value = weekly_channel_engagement(dispatches=dispatches, reconciliations=rows("reconciliations"),
            readbacks=rows("readbacks"), observations=observations, week_ending=week_ending, call_bindings=bindings)
    value["recorded_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    value["input_store_read_only"] = True
    value["digest_lines"] = weekly_audience_lines(value)
    target.mkdir(parents=True, exist_ok=True)
    for filename, payload in [("engagement.json", json.dumps(value, indent=2) + "\n"),
                              ("engagement.md", "\n".join(value["digest_lines"]) + "\n\n" + render_engagement_digest(value))]:
        temporary = target / (filename + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(target / filename)
    return {"channels": len(value["channels"]), "digest": str(target / "engagement.md"), "week_ending": week_ending}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--week-ending", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_weekly_engagement(args.store, args.week_ending, args.output_dir)))


if __name__ == "__main__":
    main()
