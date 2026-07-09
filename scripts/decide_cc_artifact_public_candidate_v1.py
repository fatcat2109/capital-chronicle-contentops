from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.cc_artifact_packet_intake_v0 import load_packet  # noqa: E402
from live_contentops.cc_artifact_packet_operator_decision_v1 import (  # noqa: E402
    DEFAULT_INTAKE_DIR,
    DEFAULT_OUTPUT_DIR,
    OperatorDecisionError,
    load_existing_intake_artifacts,
    write_operator_decision_outputs,
)
from live_contentops.cc_artifact_packet_public_candidate_gate_v1 import FAIL_SCOPE_BREACH  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate CC artifact packet public-candidate decision gate V1.")
    parser.add_argument("--intake-dir", default=str(DEFAULT_INTAKE_DIR), help="Existing V0 intake output directory.")
    parser.add_argument("--packet", required=True, help="CC artifact packet JSON to evaluate.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Decision output directory.")
    parser.add_argument("--operator-go", action="store_true", help="Record Jim GO for decision gate only.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        packet = load_packet(args.packet)
        artifacts = load_existing_intake_artifacts(args.intake_dir)
        if artifacts.get("artifact_load_errors"):
            raise OperatorDecisionError(";".join(artifacts["artifact_load_errors"]))
        result = write_operator_decision_outputs(
            packet=packet,
            artifacts=artifacts,
            output_dir=args.output_dir,
            operator_go=args.operator_go,
            packet_path=args.packet,
            intake_dir=args.intake_dir,
        )
    except (OSError, json.JSONDecodeError, OperatorDecisionError, ValueError) as exc:
        print(f"CC artifact operator decision failed: {exc}", file=sys.stderr)
        return 2

    decision = result["decision_packet"]
    gate = result["gate_packet"]
    print("CC artifact packet operator decision complete")
    print(f"classification={decision['classification']}")
    print(f"gate_status={gate['gate_status']}")
    print(f"public_ready={str(decision['public_ready']).lower()}")
    print(f"operator_go_scope={decision['operator_go_scope']}")
    print(f"blocker_count={len(decision['blockers'])}")
    print("public_dispatch_performed=false")
    print("platform_api_call_performed=false")
    print("network_call_performed=false")
    return 3 if gate["gate_status"] == FAIL_SCOPE_BREACH else 0


if __name__ == "__main__":
    raise SystemExit(main())
