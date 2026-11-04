"""CC-258: run the X-list feed (one runner per machine).

    pythonw scripts/run_x_list_feed.py           # every minute until the STOP file appears
    python  scripts/run_x_list_feed.py --once    # one capture and export, printed

Writes A:\\Capital Chronicle\\Runtime\\ContentOps\\x_list_feed\\x_list_feed_v1.json. To stop the
runner, create the file STOP in that folder; it exits within a minute and the file stays
until someone removes it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.x_list_feed_v1 import FeedRunner, run_forever  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="one capture and export, then print the result")
    args = parser.parse_args(argv)
    if args.once:
        print(json.dumps(FeedRunner().iterate(), ensure_ascii=False, indent=1))
        return 0
    result = run_forever()
    return 0 if result.get("state") in {"STOPPED", "ALREADY_RUNNING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
