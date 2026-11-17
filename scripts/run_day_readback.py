"""CC-639: write the evening digest run's day_readback.json and day_readback.md.

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

from live_contentops.day_readback_v1 import build_report, write_report
from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path, help="This 19:15 run's existing route-1900/<stamp> folder")
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--feed", type=Path, default=DEFAULT_FEED)
    parser.add_argument("--since", help="Explicit inclusive-cut UTC boundary; selection is strictly after it")
    parser.add_argument("--until", help="Inclusive UTC end; default is result.json's clock, otherwise now")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.run_dir, store_path=args.store, feed_path=args.feed,
                              since=args.since, until=args.until)
        paths = write_report(args.run_dir, report)
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        # Exception strings may contain account paths, input copy or private URLs.
        print(json.dumps({"state": "READBACK_COMMAND_FAILED", "first_cause": type(exc).__name__}))
        return 1
    print(json.dumps({"state": "READBACK_WRITTEN", "files": [str(p) for p in paths],
                      "pieces": len(report["pieces"]), "exception_count": report["exception_count"],
                      "exceptions": report["exceptions"]}, ensure_ascii=False))
    return 0  # Named destination exceptions belong in the notice, not a retry loop.


if __name__ == "__main__":
    raise SystemExit(main())
