#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to build daily platform variant candidate copy."""

import argparse
import sys
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from live_contentops.daily_platform_variant_candidate_copy_v0 import generate_platform_variant_copy

def main():
    parser = argparse.ArgumentParser(description="Daily Platform Variant Candidate Copy (Step 7)")
    parser.add_argument(
        "--article-metadata",
        type=str,
        default="docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/article_draft_metadata_v0.json",
        help="Path to article draft metadata JSON file."
    )
    parser.add_argument(
        "--media-plan",
        type=str,
        default="docs/automation/DAILY_MEDIA_PLAN_SPEC_V0/media_plan_spec_v0.json",
        help="Path to media plan specification JSON file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/automation/DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0",
        help="Directory to write output files."
    )

    args = parser.parse_args()

    print("Running daily platform variant copy builder:")
    print(f"  Article Metadata: {args.article_metadata}")
    print(f"  Media Plan: {args.media_plan}")
    print(f"  Output Dir: {args.output_dir}")

    try:
        res = generate_platform_variant_copy(
            article_metadata_file=args.article_metadata,
            media_plan_file=args.media_plan,
            output_dir=args.output_dir
        )
        evidence = res["evidence"]
        copy_json = res["copy_json"]

        print("\nSuccess: Daily Platform Variant Candidate Copy generated:")
        print(f"  Variant Count: {len(copy_json['variants'])}")
        print(f"  Classification: {evidence['classification']}")
        print(f"  Platform Copy Status: {copy_json['platform_copy_status']}")
        print(f"  Dispatch Allowed: {copy_json['dispatch_allowed_now']}")
        print(f"  Run Evidence: {evidence['output_paths']['run_evidence']}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
