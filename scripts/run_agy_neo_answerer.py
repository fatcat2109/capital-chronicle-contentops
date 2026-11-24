"""CC-798: the per-platform dry run of the Antigravity Neo answerer, and the switch's state.

dry-run: agy fills the composer for one saved native Neo PUBLISH request (<hash>.request.json) and
reads it back; code compares the texts and the account. It never clicks Post, claims, submits or
writes the store. routes: prints which platforms the switch gives to agy (default Codex).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.tool_output_v1 import safe_print as print

from live_contentops.agy_neo_answerer_v1 import AGY_DESTINATIONS, AgyRunner, dry_run, platform_routes, route_for
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_neo_executor_v1 import SCHEMA


def load_packet(path: Path) -> dict:
    packet = json.loads(path.read_bytes())
    packet.pop("request_path", None)
    request = packet.get("request") or {}
    if (packet.get("schema_version") != SCHEMA
            or packet.get("tool_request_sha256") != sha256_of({k: v for k, v in packet.items() if k != "tool_request_sha256"})
            or request.get("request_sha256") != sha256_of({k: v for k, v in request.items() if k != "request_sha256"})):
        raise ValueError("NATIVE_NEO_REQUEST_FILE_INVALID")
    return packet


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("dry-run", "routes"))
    parser.add_argument("--request-file", type=Path)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--scratch-root", type=Path, help="where agy's empty working folder is made")
    args = parser.parse_args(argv)
    if args.command == "routes":
        routes = platform_routes()
        result = {d: route_for(d, routes) for d in sorted(AGY_DESTINATIONS)}
    else:
        if not args.request_file or not args.report_dir:
            parser.error("dry-run needs --request-file and --report-dir")
        result = dry_run(load_packet(args.request_file), runner=AgyRunner(scratch_root=args.scratch_root),
                         report_dir=args.report_dir)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
