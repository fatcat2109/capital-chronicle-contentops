#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to build daily database support gap repair plan."""

import argparse
import sys
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from live_contentops.daily_database_support_gap_repair_plan_v0 import build_database_support_gap_repair_plan

def main():
    parser = argparse.ArgumentParser(description="Build Daily Database Support Gap Repair Plan (Step 3b)")
    parser.add_argument(
        "--support-packet-file",
        type=str,
        default="docs/automation/DAILY_DATABASE_SUPPORT_PACKET_V0/database_support_packet_v0.json",
        help="Path to Step 3 database support packet file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/automation/DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0",
        help="Directory to write output files."
    )

    args = parser.parse_args()

    print("Running daily database support gap repair plan builder:")
    print(f"  Support Packet File: {args.support_packet_file}")
    print(f"  Output Dir: {args.output_dir}")

    try:
        res = build_database_support_gap_repair_plan(
            support_packet_file=args.support_packet_file,
            output_dir=args.output_dir
        )
        evidence = res["evidence"]
        plan = res["plan"]

        print("\nSuccess: Database Support Gap Repair Plan generated:")
        print(f"  Idea ID: {plan['selected_idea_id']}")
        print(f"  Title: {plan['selected_title']}")
        print(f"  Classification: {evidence['classification']}")
        print(f"  Draft Blocked: {plan['article_draft_blocked']}")
        print(f"  Run Evidence: {evidence['output_paths']['run_evidence']}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
