#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to build daily article brief."""

import argparse
import sys
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from live_contentops.daily_article_brief_generation_v0 import generate_article_brief

def main():
    parser = argparse.ArgumentParser(description="Daily Article Brief Generation (Step 4)")
    parser.add_argument(
        "--reselection-packet",
        type=str,
        default="docs/automation/SUPPORT_AWARE_ARTICLE_IDEA_RESELECTION_V0/reselection_packet_v0.json",
        help="Path to reselection packet file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/automation/DAILY_ARTICLE_BRIEF_GENERATION_V0",
        help="Directory to write output files."
    )

    args = parser.parse_args()

    print("Running daily article brief generator:")
    print(f"  Reselection Packet: {args.reselection_packet}")
    print(f"  Output Dir: {args.output_dir}")

    try:
        res = generate_article_brief(
            reselection_packet_file=args.reselection_packet,
            output_dir=args.output_dir
        )
        evidence = res["evidence"]
        brief = res["brief_json"]

        print("\nSuccess: Daily Article Brief generated:")
        print(f"  Selected Idea ID: {brief['selected_idea_id']}")
        print(f"  Editorial Title: {brief['editorial_title']}")
        print(f"  Topic Family: {brief['topic_family']}")
        print(f"  Classification: {evidence['classification']}")
        print(f"  Draft Readiness: {brief['draft_readiness']}")
        print(f"  Run Evidence: {evidence['output_paths']['run_evidence']}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
