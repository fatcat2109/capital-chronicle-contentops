"""CLI runner script for Fast One-Cycle Automation Wrapper V0."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.fast_one_cycle_automation_v0 import run_fast_one_cycle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Fast One-Cycle Automation Pipeline V0.")
    parser.add_argument("--packet", help="Path to CC artifact packet JSON.")
    parser.add_argument("--dispatch-live", action="store_true", help="Attempt live platform dispatch if safe.")
    args = parser.parse_args(argv)

    kwargs = {}
    if args.packet:
        kwargs["packet_path"] = args.packet
    kwargs["dispatch_live"] = args.dispatch_live

    try:
        res = run_fast_one_cycle(**kwargs)
        evidence = res["run_evidence"]
        print("Fast One-Cycle Automation Run complete.")
        print(f"topic={evidence['topic']}")
        print(f"intake_status={evidence['intake_status']}")
        print(f"decision_status={evidence['decision_status']}")
        print(f"public_ready={str(evidence['public_ready']).lower()}")
        print(f"dispatch_status={evidence['dispatch_status']}")
        print(f"dispatch_platform={evidence['dispatch_platform']}")
        print(f"dispatch_id={evidence['dispatch_id']}")
        return 0
    except Exception as exc:
        print(f"Automation execution failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
