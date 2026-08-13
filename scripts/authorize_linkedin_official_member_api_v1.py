"""Bounded operator OAuth helper for the official LinkedIn member transport."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.linkedin_official_member_api_v1 import (
    LinkedInOfficialApiError,
    authorize_interactively,
    env_name_presence,
)


CANONICAL_EDGE_PROFILE = Path(
    r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
)
EDGE_EXECUTABLE_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
)


def _open_with_canonical_edge(authorization_url: str) -> bool:
    executable = next((path for path in EDGE_EXECUTABLE_CANDIDATES if path.is_file()), None)
    if executable is None or not CANONICAL_EDGE_PROFILE.is_dir():
        raise LinkedInOfficialApiError("CANONICAL_PUBLISHING_BROWSER_UNAVAILABLE")
    subprocess.Popen(
        [
            str(executable),
            "--remote-debugging-port=9223",
            f"--user-data-dir={CANONICAL_EDGE_PROFILE}",
            "--new-window",
            authorization_url,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--no-open-browser", action="store_true")
    parser.add_argument("--canonical-edge", action="store_true")
    args = parser.parse_args()
    print(json.dumps({"env_name_presence": env_name_presence()}, sort_keys=True), flush=True)
    print("OPERATOR_ACTION_REQUIRED_LINKEDIN_OAUTH", flush=True)
    try:
        authorize_options = {
            "timeout_seconds": args.timeout_seconds,
            "open_browser": not args.no_open_browser,
        }
        if args.canonical_edge:
            authorize_options["browser_opener"] = _open_with_canonical_edge
        result = authorize_interactively(**authorize_options)
    except LinkedInOfficialApiError as exc:
        print(json.dumps({"status": exc.classification}, sort_keys=True), flush=True)
        return 2
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
