"""CLI build script for Daily Headline Cluster & Rank Article Idea Packet."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from live_contentops.daily_headline_cluster_rank_article_idea_packet_v0 import build_article_idea_packet

def main() -> None:
    parser = argparse.ArgumentParser(description="Build daily headline cluster rank article idea packet.")
    parser.add_argument(
        "--headlines-file",
        type=str,
        default="docs/automation/DAILY_X_CDP_HEADLINE_CAPTURE_PACKET_V0/headlines_raw_v0.json",
        help="Path to Step 1 normalized headlines raw JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/automation/DAILY_HEADLINE_CLUSTER_RANK_ARTICLE_IDEA_PACKET_V0",
        help="Path to output directory"
    )
    parser.add_argument(
        "--recently-published",
        type=str,
        nargs="*",
        default=["energy_commodities"],
        help="List of topic families that were recently published to prevent repetition"
    )
    parser.add_argument(
        "--force-fallback-topic-balance",
        action="store_true",
        help="Forces fallback classification mode"
    )

    args = parser.parse_args()

    headlines_path = Path(args.headlines_file)
    output_path = Path(args.output_dir)

    print(f"Running daily headline cluster and rank:")
    print(f"  Headlines File: {headlines_path}")
    print(f"  Output Dir: {output_path}")
    print(f"  Recently Published Families: {args.recently_published}")

    res = build_article_idea_packet(
        headlines_file=headlines_path,
        output_dir=output_path,
        recently_published_families=args.recently_published,
        force_fallback_topic_balance=args.force_fallback_topic_balance
    )

    print(f"Success: Selected Article Idea:")
    print(f"  Idea ID: {res['selection']['selected_idea_id']}")
    print(f"  Title: {res['selection']['selected_title']}")
    print(f"  Topic Family: {res['selection']['selected_topic_family']}")
    print(f"  Why Selected: {res['selection']['why_selected']}")
    print(f"  Run Evidence: {res['evidence']['output_paths']['run_evidence']}")

if __name__ == "__main__":
    main()
