"""CC-711 CLI: OS-lock-guarded X_List_Feed PT15M keepalive and BrowserOS Neo health check.

Defaults strictly to --dry-run (zero process launches, zero live Task Scheduler edits,
zero public writes). Pass --apply explicitly to permit a detached start when safe.

Examples:
    python -B scripts/run_cc711_keepalive.py x-feed               # dry-run (default)
    python -B scripts/run_cc711_keepalive.py neo-health           # dry-run (default)
    python -B scripts/run_cc711_keepalive.py status               # strictly read-only summary
    python -B scripts/run_cc711_keepalive.py render-xml --target x-feed
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.cc711_xfeed_neo_keepalive_v1 import (  # noqa: E402
    DEFAULT_NEO_KEEPALIVE_LOCK,
    DEFAULT_NEO_STOP,
    DEFAULT_PYTHONW,
    DEFAULT_REPO_ROOT,
    DEFAULT_TASK_USER_ID,
    DEFAULT_X_FEED_CDP_PORT,
    DEFAULT_X_FEED_JSON,
    DEFAULT_X_FEED_KEEPALIVE_LOCK,
    DEFAULT_X_FEED_LOCK,
    DEFAULT_X_FEED_STOP,
    keepalive_x_list_feed,
    probe_browseros_neo,
    recover_browseros_neo,
    render_neo_health_keepalive_xml,
    render_x_list_feed_keepalive_xml,
    status_x_list_feed,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_xfeed = sub.add_parser("x-feed", help="Check/keepalive X_List_Feed runner (dry-run by default)")
    p_xfeed.add_argument("--apply", action="store_true", help="Permit detached runner launch when safe")
    p_xfeed.add_argument("--dry-run", action="store_true", help="Force dry-run (default)")
    p_xfeed.add_argument("--cdp-port", type=int, default=DEFAULT_X_FEED_CDP_PORT)
    p_xfeed.add_argument("--lock-path", type=Path, default=DEFAULT_X_FEED_LOCK)
    p_xfeed.add_argument("--keepalive-lock-path", type=Path, default=DEFAULT_X_FEED_KEEPALIVE_LOCK)
    p_xfeed.add_argument("--stop-path", type=Path, default=DEFAULT_X_FEED_STOP)
    p_xfeed.add_argument("--feed-path", type=Path, default=DEFAULT_X_FEED_JSON)
    p_xfeed.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    p_xfeed.add_argument("--pythonw", type=Path, default=DEFAULT_PYTHONW)

    p_neo = sub.add_parser("neo-health", help="Check/cold-start BrowserOS Neo (dry-run by default)")
    p_neo.add_argument("--apply", action="store_true", help="Permit cold-start ONLY when process & ports are down")
    p_neo.add_argument("--dry-run", action="store_true", help="Force dry-run (default)")
    p_neo.add_argument("--cdp-port", type=int, default=None)
    p_neo.add_argument("--mcp-endpoint", default=None)
    p_neo.add_argument("--config-path", type=Path, default=None)
    p_neo.add_argument("--keepalive-lock-path", type=Path, default=DEFAULT_NEO_KEEPALIVE_LOCK)
    p_neo.add_argument("--stop-path", type=Path, default=DEFAULT_NEO_STOP)

    p_status = sub.add_parser("status", help="Strictly read-only combined X_List_Feed + BrowserOS Neo status")
    p_status.add_argument("--x-cdp-port", type=int, default=DEFAULT_X_FEED_CDP_PORT)
    p_status.add_argument("--x-lock-path", type=Path, default=DEFAULT_X_FEED_LOCK)
    p_status.add_argument("--x-stop-path", type=Path, default=DEFAULT_X_FEED_STOP)
    p_status.add_argument("--x-feed-path", type=Path, default=DEFAULT_X_FEED_JSON)
    p_status.add_argument("--neo-cdp-port", type=int, default=None)
    p_status.add_argument("--neo-mcp-endpoint", default=None)
    p_status.add_argument("--neo-config-path", type=Path, default=None)

    p_xml = sub.add_parser("render-xml", help="Print disabled-by-default Task Scheduler XML to stdout")
    p_xml.add_argument("--target", choices=("x-feed", "neo-health"), required=True)
    p_xml.add_argument("--user-id", default=DEFAULT_TASK_USER_ID)
    p_xml.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    p_xml.add_argument("--pythonw", type=Path, default=DEFAULT_PYTHONW)

    args = parser.parse_args(argv)

    if args.command == "render-xml":
        if args.target == "x-feed":
            sys.stdout.write(
                render_x_list_feed_keepalive_xml(
                    repo_root=args.repo_root, pythonw=args.pythonw, user_id=args.user_id, enabled=False
                )
            )
        else:
            sys.stdout.write(
                render_neo_health_keepalive_xml(
                    repo_root=args.repo_root, pythonw=args.pythonw, user_id=args.user_id, enabled=False
                )
            )
        return 0

    if args.command == "x-feed":
        dry_run = (not args.apply) or args.dry_run
        result = keepalive_x_list_feed(
            dry_run=dry_run,
            lock_path=args.lock_path,
            keepalive_lock_path=args.keepalive_lock_path,
            stop_path=args.stop_path,
            feed_path=args.feed_path,
            repo_root=args.repo_root,
            python_exe=args.pythonw,
            cdp_port=args.cdp_port,
        )
    elif args.command == "neo-health":
        dry_run = (not args.apply) or args.dry_run
        result = recover_browseros_neo(
            dry_run=dry_run,
            keepalive_lock_path=args.keepalive_lock_path,
            stop_path=args.stop_path,
            config_path=args.config_path,
            cdp_port=args.cdp_port,
            mcp_endpoint=args.mcp_endpoint,
        )
    else:
        result = {
            "x_list_feed": status_x_list_feed(
                lock_path=args.x_lock_path,
                stop_path=args.x_stop_path,
                feed_path=args.x_feed_path,
                cdp_port=args.x_cdp_port,
            ),
            "browseros_neo": probe_browseros_neo(
                cdp_port=args.neo_cdp_port,
                mcp_endpoint=args.neo_mcp_endpoint,
                config_path=args.neo_config_path,
            ),
            "read_only": True,
            "dry_run": True,
            "public_write_performed": False,
            "live_task_mutated": False,
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
