#!/usr/bin/env python
"""Run the operator-approved supervised live Daily ContentOps dispatch."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from live_contentops.operator_approved_supervised_live_daily_run_v0 import (
    TASK_LABEL,
    run_operator_approved_supervised_live_daily_run,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=TASK_LABEL)
    parser.add_argument("--operator-approved-live-run", action="store_true")
    parser.add_argument("--max-send-attempts-per-platform", type=int, default=1)
    args = parser.parse_args()

    result = run_operator_approved_supervised_live_daily_run(
        operator_approved_live_run=args.operator_approved_live_run,
        max_send_attempts_per_platform=args.max_send_attempts_per_platform,
    )
    summary = {
        "classification": result["classification"],
        "attempted_platforms": result["dispatch_results"]["attempted_platforms"],
        "successful_platforms": result["dispatch_results"]["successful_platforms"],
        "skipped_platforms": result["dispatch_results"]["skipped_platforms"],
        "failed_platforms": result["dispatch_results"]["failed_platforms"],
        "all_secret_values_redacted": result["dispatch_results"]["all_secret_values_redacted"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if result["classification"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
