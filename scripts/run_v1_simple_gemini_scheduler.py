"""Run the lightweight local zero-write Simple-Gemini V1 scheduler."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_repo_root_text = str(_REPO_ROOT)
if _repo_root_text not in sys.path:
    sys.path.insert(0, _repo_root_text)

from live_contentops.daily_app_launcher_v1 import (
    CANONICAL_PRODUCTION_OUTPUT_ROOT,
    CANONICAL_PRODUCTION_STORE_PATH,
)
from live_contentops.v1_simple_gemini_scheduler_process_v1 import (
    CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT,
    restart_scheduler_process,
    run_owned_scheduler_forever,
    scheduler_process_state,
    start_scheduler_process,
    stop_scheduler_process,
)
from live_contentops.v1_simple_gemini_scheduler_v1 import SimpleGeminiLocalScheduler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tick the four-window local zero-write Simple-Gemini scheduler."
    )
    parser.add_argument(
        "--scheduler-root",
        default=str(CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT),
        help="Persistent production root by default; override only for isolated tests/proofs.",
    )
    parser.add_argument(
        "--tick-utc",
        default=None,
        help="Injected ISO-8601 UTC clock for deterministic one-tick proof.",
    )
    parser.add_argument(
        "--published-memory-store",
        default=str(CANONICAL_PRODUCTION_STORE_PATH),
    )
    parser.add_argument(
        "--published-memory-output-root",
        default=str(CANONICAL_PRODUCTION_OUTPUT_ROOT),
    )
    lifecycle = parser.add_mutually_exclusive_group()
    lifecycle.add_argument("--run-forever", action="store_true")
    lifecycle.add_argument("--start-detached", action="store_true")
    lifecycle.add_argument("--status", action="store_true")
    lifecycle.add_argument("--stop", action="store_true")
    lifecycle.add_argument("--restart", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=60.0)
    parser.add_argument("--max-ticks", type=int, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.run_forever and args.tick_utc:
        raise SystemExit("--tick-utc cannot be combined with --run-forever")
    lifecycle_kwargs = {
        "scheduler_root": args.scheduler_root,
        "published_memory_store": args.published_memory_store,
        "published_memory_output_root": args.published_memory_output_root,
        "poll_seconds": args.poll_seconds,
    }
    if args.start_detached:
        result = start_scheduler_process(**lifecycle_kwargs)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if result.get("outcome") in {"STARTED", "ALREADY_RUNNING"} else 2
    if args.status:
        result = scheduler_process_state(scheduler_root=args.scheduler_root)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    if args.stop:
        result = stop_scheduler_process(scheduler_root=args.scheduler_root)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if result.get("outcome") in {"STOPPED", "ALREADY_STOPPED"} else 2
    if args.restart:
        result = restart_scheduler_process(**lifecycle_kwargs)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if result.get("outcome") == "RESTARTED" else 2
    scheduler = SimpleGeminiLocalScheduler(
        scheduler_root=args.scheduler_root,
        published_memory_store=args.published_memory_store,
        published_memory_output_root=args.published_memory_output_root,
    )
    if args.run_forever:
        result = run_owned_scheduler_forever(
            scheduler,
            scheduler_root=args.scheduler_root,
            poll_seconds=args.poll_seconds,
            max_ticks=args.max_ticks,
            on_tick=lambda value: print(
                json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False),
                flush=True,
            ),
        )
        print(
            json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False), flush=True
        )
        return (
            0 if result.get("outcome") in {"STOPPED_CLEANLY", "ALREADY_RUNNING"} else 2
        )
    result = scheduler.tick(now=args.tick_utc)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
