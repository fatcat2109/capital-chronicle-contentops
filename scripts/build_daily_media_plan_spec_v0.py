#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to build daily media plan specification."""

import argparse
import sys
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from live_contentops.daily_media_plan_spec_v0 import generate_media_plan_spec

def main():
    parser = argparse.ArgumentParser(description="Daily Media Plan Specification (Step 6)")
    parser.add_argument(
        "--article-draft",
        type=str,
        default="docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/article_draft_v0.md",
        help="Path to article draft file."
    )
    parser.add_argument(
        "--article-metadata",
        type=str,
        default="docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/article_draft_metadata_v0.json",
        help="Path to article draft metadata JSON file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/automation/DAILY_MEDIA_PLAN_SPEC_V0",
        help="Directory to write output files."
    )

    args = parser.parse_args()

    print("Running daily media plan spec builder:")
    print(f"  Article Draft: {args.article_draft}")
    print(f"  Article Metadata: {args.article_metadata}")
    print(f"  Output Dir: {args.output_dir}")

    try:
        res = generate_media_plan_spec(
            article_draft_file=args.article_draft,
            article_metadata_file=args.article_metadata,
            output_dir=args.output_dir
        )
        evidence = res["evidence"]
        spec = res["spec_json"]

        print("\nSuccess: Daily Media Plan Spec generated:")
        print(f"  Editorial Title: {spec['editorial_title']}")
        print(f"  Asset Count: {len(spec['assets'])}")
        print(f"  Classification: {evidence['classification']}")
        print(f"  Media Gen Status: {spec['media_generation_status']}")
        print(f"  Generation Allowed: {spec['generation_allowed_now']}")
        print(f"  Run Evidence: {evidence['output_paths']['run_evidence']}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
