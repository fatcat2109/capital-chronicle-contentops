from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.cc_artifact_packet_intake_v0 import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SCHEMA_PATH,
    PacketValidationError,
    intake_packet,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Intake a CC Content Artifact Packet V0 in dry-run mode.")
    parser.add_argument("--packet", required=True, help="Path to CC artifact packet JSON.")
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA_PATH),
        help="Path to copied CC artifact packet V0 schema.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for deterministic local intake output.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Required; no public or provider action is available.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.dry_run:
        parser.error("--dry-run is required; V0 intake never publishes or calls platform adapters")

    try:
        summary = intake_packet(
            packet_path=args.packet,
            schema_path=args.schema,
            output_dir=args.output_dir,
            dry_run=True,
        )
    except (PacketValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"CC artifact packet intake failed: {exc}", file=sys.stderr)
        return 2

    print("CC artifact packet intake dry-run complete")
    print(f"classification={summary['classification']}")
    print(f"packet_id={summary['packet_id']}")
    print(f"approval_hash={summary['approval_hash']}")
    print(f"internal_draft_path={summary['internal_draft_path']}")
    print("public_dispatch_performed=false")
    print("platform_api_call_performed=false")
    print("network_call_performed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
