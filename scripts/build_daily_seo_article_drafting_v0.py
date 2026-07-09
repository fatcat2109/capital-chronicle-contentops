#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to build daily SEO article draft."""

import argparse
import sys
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from live_contentops.daily_seo_article_drafting_v0 import generate_article_draft

def main():
    parser = argparse.ArgumentParser(description="Daily SEO Article Drafting (Step 5)")
    parser.add_argument(
        "--article-brief",
        type=str,
        default="docs/automation/DAILY_ARTICLE_BRIEF_GENERATION_V0/article_brief_v0.json",
        help="Path to article brief file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0",
        help="Directory to write output files."
    )

    args = parser.parse_args()

    print("Running daily SEO article draft generator:")
    print(f"  Article Brief: {args.article_brief}")
    print(f"  Output Dir: {args.output_dir}")

    try:
        res = generate_article_draft(
            article_brief_file=args.article_brief,
            output_dir=args.output_dir
        )
        evidence = res["evidence"]
        metadata = res["metadata"]

        print("\nSuccess: Daily SEO Article Draft generated:")
        print(f"  Selected Idea ID: {metadata['selected_idea_id']}")
        print(f"  Editorial Title: {metadata['editorial_title']}")
        print(f"  Classification: {evidence['classification']}")
        print(f"  Draft Status: {metadata['draft_status']}")
        print(f"  Word Count Estimate: {metadata['word_count_estimate']}")
        print(f"  Run Evidence: {evidence['output_paths']['run_evidence']}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
