"""CLI build script for Daily X CDP Headline Capture Packet."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from live_contentops.daily_x_cdp_headline_capture_packet_v0 import capture_headlines

def main() -> None:
    parser = argparse.ArgumentParser(description="Build daily X CDP headline capture packet.")
    parser.add_argument(
        "--source-file",
        type=str,
        default="headline_ingestion/data/intake/headline_sidecars/step1_headline_sidecar_2026_07_08.jsonl",
        help="Path to raw source sidecar file"
    )
    parser.add_argument(
        "--checkpoint-file",
        type=str,
        default="docs/automation/DAILY_X_CDP_HEADLINE_CAPTURE_PACKET_V0/checkpoint_state_v0.json",
        help="Path to previous checkpoint file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/automation/DAILY_X_CDP_HEADLINE_CAPTURE_PACKET_V0",
        help="Path to output directory"
    )
    parser.add_argument(
        "--date",
        type=str,
        default="2026-07-09",
        help="Reference date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--force-mode",
        type=str,
        default="fixture_local",
        help="Override capture mode description"
    )

    args = parser.parse_args()

    source_path = Path(args.source_file)
    output_path = Path(args.output_dir)
    checkpoint_path = Path(args.checkpoint_file) if args.checkpoint_file else None

    print(f"Running daily X CDP headline capture packet:")
    print(f"  Source: {source_path}")
    print(f"  Checkpoint: {checkpoint_path}")
    print(f"  Output Dir: {output_path}")
    print(f"  Reference Date: {args.date}")

    res = capture_headlines(
        source_file=source_path,
        checkpoint_file=checkpoint_path,
        output_dir=output_path,
        target_date=args.date,
        force_mode=args.force_mode
    )

    print(f"Success: Captured {len(res['headlines'])} headlines.")
    print(f"  Headlines Raw: {res['evidence']['output_paths']['headlines_raw']}")
    print(f"  Checkpoint State: {res['evidence']['output_paths']['checkpoint_state']}")
    print(f"  Run Evidence: {res['evidence']['output_paths']['run_evidence']}")

if __name__ == "__main__":
    main()
