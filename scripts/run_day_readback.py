"""Write the evening readback or CC-692's standing 24-hour sweep.

Run as the existing cc-contentops-digest-1900-bp task's final step, after result.json.
This command does not publish, reconcile, change schedules or start a browser.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.day_readback_v1 import DECISION_CHECKS_NAME, build_report, write_decision_checks, write_report
from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, help="This 19:15 run's existing route-1900/<stamp> folder")
    parser.add_argument("--sweep", action="store_true", help="Use CC-692's rolling 24-hour window and Notes watch")
    parser.add_argument("--sweep-started-at", help="UTC start from the first pass, for classifying exact owner refreshes")
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--feed", type=Path, default=DEFAULT_FEED)
    parser.add_argument("--since", help="Exclusive UTC start; default is the preceding digest run's folder clock")
    parser.add_argument("--until", help="Inclusive UTC end; default is result.json's clock, otherwise now")
    parser.add_argument("--stored-only", action="store_true", help="Replay retained records without public HTTP")
    parser.add_argument("--plan-export-dir", type=Path, help="Use this retained Main public plan snapshot for the report")
    parser.add_argument("--decisions-only", action="store_true", help="Write only decision_checks.json")
    parser.add_argument("--output-dir", type=Path, help="Write to a replay folder instead of the existing run folder")
    args = parser.parse_args(argv)
    if args.sweep:
        if not args.output_dir or args.since or args.run_dir or args.decisions_only:
            parser.error("--sweep requires --output-dir and sets its own report window")
    elif args.run_dir is None or args.sweep_started_at:
        parser.error("provide --run-dir for the evening report, or --sweep for the rolling window")
    try:
        source = {"fetcher": None} if args.stored_only else {}
        report = build_report(args.run_dir or args.output_dir, store_path=args.store, feed_path=args.feed,
                              since=args.since, until=args.until, plan_export_dir=args.plan_export_dir,
                              sweep=args.sweep, sweep_started_at=args.sweep_started_at, **source)
        folder = args.output_dir or args.run_dir
        decisions = report["decision_checks"]
        if args.decisions_only:
            paths = (write_decision_checks(folder, decisions),)
        else:
            paths = (*write_report(folder, report), folder / DECISION_CHECKS_NAME)
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        # Exception strings may contain account paths, input copy or private URLs.
        print(json.dumps({"state": "READBACK_COMMAND_FAILED", "first_cause": type(exc).__name__}))
        return 1
    if args.sweep:
        sweep = report["sweep"]
        print(json.dumps({"state": "SWEEP_WRITTEN", "files": [str(p) for p in paths],
                          "window": report["window"], "started_at_utc": sweep["started_at_utc"],
                          "next_due_utc": sweep["next_due_utc"], "platforms": sweep["platforms"],
                          "readback_targets": len(sweep["readback_targets"]),
                          "defect_groups": len(sweep["defect_groups"]),
                          "notes_watch": sweep["notes_watch"]}, ensure_ascii=False))
        return 0
    print(json.dumps({"state": "READBACK_WRITTEN", "files": [str(p) for p in paths],
                      "pieces": len(report["pieces"]), "exception_count": report["exception_count"],
                      "exceptions": sorted(report["exceptions"], key=lambda issue: "decision" not in issue),
                      "decision_failure_count": decisions["failure_count"]}, ensure_ascii=False))
    return 0  # Named destination exceptions belong in the notice, not a retry loop.


if __name__ == "__main__":
    raise SystemExit(main())
