"""Export the ten-channel engagement section for the weekly digest, read-only."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import json
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.channel_engagement_v1 import weekly_channel_engagement, render_engagement_digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--week-ending", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    target = args.output_dir.resolve()
    root = Path(__file__).resolve().parents[1]
    if target == root or not target.is_relative_to(root):
        raise ValueError("DIGEST_OUTPUT_MUST_BE_INSIDE_BACKLOG_WORKTREE")
    with sqlite3.connect(args.store.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        def rows(table):
            return [dict(r) for r in connection.execute("SELECT * FROM " + table)]
        value = weekly_channel_engagement(dispatches=rows("platform_dispatches"), reconciliations=rows("reconciliations"),
            readbacks=rows("readbacks"), observations=rows("performance_observations"), week_ending=args.week_ending)
    value["recorded_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    value["input_store_read_only"] = True
    target.mkdir(parents=True, exist_ok=True)
    (target / "engagement.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    (target / "engagement.md").write_text(render_engagement_digest(value), encoding="utf-8")
    print(json.dumps({"channels": len(value["channels"]), "digest": str(target / "engagement.md")}))


if __name__ == "__main__":
    main()
