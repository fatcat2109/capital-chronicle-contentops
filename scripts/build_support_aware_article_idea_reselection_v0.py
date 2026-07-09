#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to build support-aware article idea reselection."""

import argparse
import sys
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from live_contentops.support_aware_article_idea_reselection_v0 import reselect_article_idea

def main():
    parser = argparse.ArgumentParser(description="Support-Aware Article Idea Reselection (Step 3c)")
    parser.add_argument(
        "--idea-file",
        type=str,
        default="docs/automation/DAILY_HEADLINE_CLUSTER_RANK_ARTICLE_IDEA_PACKET_V0/article_idea_selection_v0.json",
        help="Path to original article idea selection file."
    )
    parser.add_argument(
        "--gap-file",
        type=str,
        default="docs/automation/DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0/support_gap_repair_plan_v0.json",
        help="Path to database support gap repair plan file."
    )
    parser.add_argument(
        "--clusters-file",
        type=str,
        default="docs/automation/DAILY_HEADLINE_CLUSTER_RANK_ARTICLE_IDEA_PACKET_V0/headline_clusters_v0.json",
        help="Path to headline clusters file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/automation/SUPPORT_AWARE_ARTICLE_IDEA_RESELECTION_V0",
        help="Directory to write output files."
    )

    args = parser.parse_args()

    print("Running support-aware article idea reselection:")
    print(f"  Idea File: {args.idea_file}")
    print(f"  Gap File: {args.gap_file}")
    print(f"  Clusters File: {args.clusters-file if hasattr(args, 'clusters-file') else args.clusters_file}")
    print(f"  Output Dir: {args.output_dir}")
    try:
        res = reselect_article_idea(
            idea_selection_file=args.idea_file,
            gap_repair_plan_file=args.gap_file,
            headline_clusters_file=args.clusters_file,
            output_dir=args.output_dir
        )
        evidence = res["evidence"]
        packet = res["packet"]

        print("\nSuccess: Support-Aware Article Idea Reselection completed:")
        print(f"  Original Idea Blocked: {packet['original_idea_blocked']}")
        print(f"  Reselected Title: {packet['reselected_title']}")
        print(f"  Topic Family: {packet['reselected_topic_family']}")
        print(f"  Classification: {evidence['classification']}")
        print(f"  Ready for brief: {packet['ready_for_article_brief']}")
        print(f"  Run Evidence: {evidence['output_paths']['run_evidence']}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
