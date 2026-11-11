"""Compile one Metaculus round using held Main outputs. Makes no HTTP calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.metaculus_forecast_v1 import compile_round, event_forecasts, plan_forecasts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--plan-export", required=True, type=Path)
    parser.add_argument("--event-matrix", action="append", default=[], type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    question_input = json.loads(args.questions.read_bytes())
    inventories = [plan_forecasts(args.plan_export)]
    inventories.extend(event_forecasts(path, observed_at_utc=now) for path in args.event_matrix)
    result = compile_round(question_input, inventories, as_of_utc=now)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8") + b"\n")
    print(json.dumps({k: result[k] for k in ("round_id", "question_count", "matched_count", "abstained_count",
          "submission_count", "network_call_count")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
