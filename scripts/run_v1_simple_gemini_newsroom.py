"""CLI boundary for one zero-write simple Gemini V1 newsroom opportunity.

The script is intentionally not a scheduler and never crosses a public-write boundary. A
future local scheduler may call this exact entrypoint only after the zero-write host canary
is accepted. Until then it is a manual/proof runner over the canonical production
orchestrator operation.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

# Direct-file execution sets sys.path[0] to ``scripts/`` rather than the repository root.
# Bootstrap only the repository import root so the documented ``python scripts/...`` entrypoint
# behaves the same as an installed/package invocation without changing runtime authority.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_repo_root_text = str(_REPO_ROOT)
if _repo_root_text not in sys.path:
    sys.path.insert(0, _repo_root_text)

from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one zero-write V1 simple Gemini newsroom opportunity."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Explicit isolated output directory for the opportunity.",
    )
    parser.add_argument(
        "--cutoff-utc",
        default=None,
        help="ISO-8601 UTC cutoff. Defaults to the current UTC instant.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional stable run identity. Defaults to the output directory name.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cutoff_utc = str(args.cutoff_utc or _utc_now())
    result = ContentOpsProductionOrchestrator().execute(
        "run_v1_simple_gemini_newsroom",
        output_dir=output_dir,
        cutoff_utc=cutoff_utc,
        run_id=args.run_id or output_dir.name,
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if str(result.get("classification") or "").startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
