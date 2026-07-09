#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to build daily database support packet."""

import argparse
import sys
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from live_contentops.daily_database_support_packet_v0 import build_database_support_packet

def main():
    parser = argparse.ArgumentParser(description="Build Daily Database Support Packet (Step 3)")
    parser.add_argument(
        "--idea-file",
        type=str,
        default="docs/automation/DAILY_HEADLINE_CLUSTER_RANK_ARTICLE_IDEA_PACKET_V0/article_idea_selection_v0.json",
        help="Path to Step 2 article idea selection file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/automation/DAILY_DATABASE_SUPPORT_PACKET_V0",
        help="Directory to write output files."
    )
    parser.add_argument(
        "--main-db-repo",
        type=str,
        default="A:/Capital Chronicle/Headline Raw data local json/capital-chronicle-ingestion",
        help="Path to main database repository."
    )

    args = parser.parse_args()

    print("Running daily database support packet builder:")
    print(f"  Idea File: {args.idea_file}")
    print(f"  Output Dir: {args.output_dir}")
    print(f"  Main DB Repo: {args.main_db_repo}")

    try:
        res = build_database_support_packet(
            idea_selection_file=args.idea_file,
            output_dir=args.output_dir,
            main_db_repo=args.main_db_repo
        )
        evidence = res["evidence"]
        packet = res["packet"]
        
        print("\nSuccess: Database Support Packet generated:")
        print(f"  Idea ID: {packet['selected_idea_id']}")
        print(f"  Title: {packet['selected_title']}")
        print(f"  Classification: {evidence['classification']}")
        print(f"  Available: {evidence['available_count']}, Partial: {evidence['partial_count']}, Missing: {evidence['missing_count']}")
        print(f"  Ready for draft: {packet['ready_for_article_draft']}")
        print(f"  Run Evidence: {evidence['output_paths']['run_evidence']}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
