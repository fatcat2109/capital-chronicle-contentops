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
    DEFAULT_PUBLIC_PREVIEW_OUTPUT_DIR,
    OperatorDecisionError,
    load_existing_intake_artifacts,
    write_operator_decision_outputs,
)
from live_contentops.cc_artifact_packet_public_candidate_gate_v1 import FAIL_SCOPE_BREACH  # noqa: E402
from live_contentops.public_permissive_supervised_mode_v0 import (  # noqa: E402
    PUBLIC_MODE_CANDIDATE_COMMENTARY,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate CC artifact packet public-candidate decision gate V1.")
    parser.add_argument("--intake-dir", default=str(DEFAULT_INTAKE_DIR), help="Existing V0 intake output directory.")
    parser.add_argument("--packet", required=True, help="CC artifact packet JSON to evaluate.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Decision output directory.")
    parser.add_argument("--operator-go", action="store_true", help="Record Jim GO for decision gate only.")
    parser.add_argument("--operator-public-override", action="store_true", help="Allow candidate-commentary public preview path.")
    parser.add_argument(
        "--public-mode",
        default=PUBLIC_MODE_CANDIDATE_COMMENTARY,
        choices=[PUBLIC_MODE_CANDIDATE_COMMENTARY],
        help="Public preview mode. Only candidate_commentary is supported.",
    )
    parser.add_argument(
        "--public-preview-output-dir",
        default=str(DEFAULT_PUBLIC_PREVIEW_OUTPUT_DIR),
        help="Output directory for supervised public-permissive preview artifacts.",
    )
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
            operator_public_override=args.operator_public_override,
            public_mode=args.public_mode,
            public_preview_output_dir=args.public_preview_output_dir,
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
    print(f"operator_public_override={str(args.operator_public_override).lower()}")
    print(f"public_mode={decision.get('public_mode', 'block_first')}")
    print(f"blocker_count={len(decision['blockers'])}")
    print(f"warning_count={len(decision.get('warnings') or [])}")
    print("public_dispatch_performed=false")
    print("platform_api_call_performed=false")
    print("network_call_performed=false")
    return 3 if gate["gate_status"] == FAIL_SCOPE_BREACH else 0


if __name__ == "__main__":
    raise SystemExit(main())
