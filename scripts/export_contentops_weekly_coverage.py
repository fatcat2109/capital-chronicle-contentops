"""Export the ContentOps coverage section for the weekly digest; read-only, no model."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import json
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.newsroom_coverage_v1 import weekly_newsroom_coverage, render_coverage_digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--week-ending", required=True, help="Inclusive production date, YYYY-MM-DD")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = args.output_dir.resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError("DIGEST_OUTPUT_MUST_BE_INSIDE_BACKLOG_WORKTREE")
    with sqlite3.connect(args.store.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        def rows(table):
            return [dict(r) for r in connection.execute("SELECT * FROM " + table)]
        value = weekly_newsroom_coverage(outbox=rows("outbox_messages"), dispatches=rows("platform_dispatches"),
            reconciliations=rows("reconciliations"), readbacks=rows("readbacks"), week_ending=args.week_ending)
    value["recorded_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    value["input_store_read_only"] = True
    target.mkdir(parents=True, exist_ok=True)
    (target / "coverage.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    (target / "coverage.md").write_text(render_coverage_digest(value), encoding="utf-8")
    print(json.dumps({"status": value["status"], "digest": str(target / "coverage.md"), "source_walks": value["source_walks"]}))


if __name__ == "__main__":
    main()
