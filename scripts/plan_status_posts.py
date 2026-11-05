"""CC-306: queue one post per new plan-state change for the six markets (one run, then exit).

    python scripts/plan_status_posts.py [--dry-run] [--export-dir DIR] [--store PATH]
                                        [--window-minutes N] [--main-root DIR]

Reads Main's plan-status export through CC-307's own reader (read_public_status and
read_public_transitions, run in Main's live root) and registers one READY_FOR_PUBLISHER outbox
row per new transition in the ContentOps store. Repeats change nothing. --dry-run writes no
shared state and prints the rows it would queue. No public write here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore  # noqa: E402
from live_contentops.plan_status_posts_v1 import (  # noqa: E402
    EXPORT_DIR, MAIN_ROOT, POSTING_WINDOW_MINUTES, queue_posts,
)
from live_contentops.published_content_v1 import PRODUCTION_STORE  # noqa: E402


def child_python() -> str:
    # Under pythonw the reader child still needs a console-less interpreter with jsonschema.
    here = Path(sys.executable)
    sibling = here.with_name("python.exe")
    return str(sibling if here.name.lower() == "pythonw.exe" and sibling.is_file() else here)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--export-dir", type=Path, default=EXPORT_DIR)
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--window-minutes", type=int, default=POSTING_WINDOW_MINUTES)
    parser.add_argument("--main-root", type=Path, default=MAIN_ROOT)
    parser.add_argument("--publish", action="store_true",
                        help="after queueing, post queued rows through the coordinator (X waits for an agent turn)")
    parser.add_argument("--pending-x", action="store_true", help="list status posts' X requests for an agent")
    parser.add_argument("--x-begin", nargs=2, metavar=("KEY", "REQUEST_SHA256"))
    parser.add_argument("--x-submit", nargs=3, metavar=("KEY", "REQUEST_SHA256", "RESPONSE_JSON"))
    parser.add_argument("--native-invocation-id", default="")
    args = parser.parse_args(argv)
    store = ContentOpsDurableStore(str(args.store), auto_migrate=False)
    from live_contentops import plan_status_posts_v1 as posts
    if args.pending_x or args.x_begin or args.x_submit:
        if args.pending_x:
            result = {"status": "OK", "pending_x": posts.pending_x(store)}
        elif not args.native_invocation_id:
            result = {"status": "NATIVE_INVOCATION_ID_REQUIRED"}
        elif args.x_begin:
            result = {"status": "OK", "begin": posts.begin_x(store, *args.x_begin,
                                                             native_invocation_id=args.native_invocation_id)}
        else:
            key, request_hash, response = args.x_submit
            result = {"status": "OK", "submit": posts.submit_x(
                store, key, request_hash, json.loads(Path(response).read_text(encoding="utf-8")),
                native_invocation_id=args.native_invocation_id)}
    else:
        result = queue_posts(store, args.export_dir, window_minutes=args.window_minutes, dry_run=args.dry_run,
                             main_root=args.main_root, python=child_python())
        if args.publish and not args.dry_run and result["status"] == "OK":
            result["publication"] = posts.publish_ready(store, latest_states=result.get("latest_states"))
    if sys.stdout is not None:  # pythonw has no stdout; the outbox rows are the record
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=1) + "\n")
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
