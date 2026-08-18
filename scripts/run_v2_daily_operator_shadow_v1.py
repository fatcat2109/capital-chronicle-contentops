"""Run or inspect the V1-read-only / V2-durable Daily Operator shadow spine."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from video.daily_operator_v1 import run_daily_operator  # noqa: E402
from video.unattended_core_factory_v1.creative import (  # noqa: E402
    hash_value,
    validate_input_packet,
)
from video.unattended_core_factory_v1.store import V2JobStore  # noqa: E402


DEFAULT_V1_STORE = Path(
    r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3"
)
DEFAULT_V2_RUNTIME = Path(
    r"A:\Capital Chronicle\Runtime\ContentOpsV2\daily_operator_shadow_v1"
)


def _head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True, encoding="utf-8"
    ).strip()


def _store(runtime: Path) -> V2JobStore:
    return V2JobStore(runtime.resolve() / "v2_daily_operator_shadow.sqlite3")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required:{path}")
    return value


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_immutable(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.is_file():
        existing = _load(path)
        if hash_value(existing) != hash_value(value):
            raise ValueError(f"immutable_automation_result_conflict:{path}")
        return
    path.write_text(payload, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_V2_RUNTIME)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Read genuine V1 state and record one daily shadow result")
    run.add_argument("--v1-store", type=Path, default=DEFAULT_V1_STORE)
    run.add_argument("--v1-output-root", type=Path)
    run.add_argument("--operator-run-id", required=True)
    run.add_argument("--implementation-head")
    run.add_argument("--parent-session-label", required=True)
    run.add_argument("--parent-task-id")
    run.add_argument("--now-utc")
    run.add_argument("--max-qualified", type=int, default=1)

    activate = sub.add_parser(
        "activate-job",
        help="Bind a HIGH-validated governed factory packet to a qualified candidate job",
    )
    activate.add_argument("--video-job-id", required=True)
    activate.add_argument("--governed-input", type=Path, required=True)

    handoff = sub.add_parser(
        "record-handoff",
        help="Record actual native fresh-XHIGH child provenance after app readback",
    )
    handoff.add_argument("--handoff-id", required=True)
    handoff.add_argument("--operator-run-id", required=True)
    handoff.add_argument("--parent-task-id")
    handoff.add_argument("--child-task-id", required=True)
    handoff.add_argument("--child-worktree", required=True)
    handoff.add_argument("--purpose", required=True)
    handoff.add_argument("--governed-input-hash", required=True)
    handoff.add_argument("--result-text", required=True)
    handoff.add_argument("--candidate-version-id")
    handoff.add_argument("--video-job-id")

    finalize = sub.add_parser(
        "finalize-automation",
        help="Bind the native automation identity, handoff, and durable review queue",
    )
    finalize.add_argument("--operator-run-id", required=True)
    finalize.add_argument("--automation-id", required=True)
    finalize.add_argument("--automation-name", required=True)
    finalize.add_argument("--schedule-proof", required=True)
    finalize.add_argument("--parent-task-id", required=True)

    sub.add_parser("review-queue", help="Read the durable Daily Operator review queue")
    sub.add_parser("status", help="Read decisions, jobs, runs, and native handoffs")

    args = parser.parse_args()
    runtime = args.runtime_root.resolve()
    if args.command == "run":
        now = (
            datetime.fromisoformat(args.now_utc.replace("Z", "+00:00"))
            if args.now_utc
            else None
        )
        result = run_daily_operator(
            v1_store_path=args.v1_store,
            v1_output_root=args.v1_output_root,
            runtime_root=runtime,
            operator_run_id=args.operator_run_id,
            implementation_head=args.implementation_head or _head(),
            parent_session_label=args.parent_session_label,
            parent_task_id=args.parent_task_id,
            now=now,
            max_qualified=args.max_qualified,
        )
    else:
        store = _store(runtime)
        if args.command == "activate-job":
            packet_path = args.governed_input.resolve()
            packet = _load(packet_path)
            validate_input_packet(packet)
            result = store.activate_candidate_job(
                video_job_id=args.video_job_id,
                governed_input_packet_path=packet_path,
                governed_input_packet_hash=hash_value(packet),
            )
        elif args.command == "record-handoff":
            result = store.record_native_handoff(
                handoff_id=args.handoff_id,
                operator_run_id=args.operator_run_id,
                parent_task_id=args.parent_task_id,
                child_task_id=args.child_task_id,
                child_model="gpt-5.6-sol",
                child_reasoning_effort="xhigh",
                child_worktree=args.child_worktree,
                purpose=args.purpose,
                governed_input_hash=args.governed_input_hash,
                result_hash=_sha256_text(args.result_text),
                candidate_version_id=args.candidate_version_id,
                video_job_id=args.video_job_id,
            )
        elif args.command == "review-queue":
            result = store.daily_review_queue()
        elif args.command == "finalize-automation":
            runs = {
                str(row["operator_run_id"]): row for row in store.operator_runs()
            }
            if args.operator_run_id not in runs:
                raise ValueError("operator_run_not_found")
            handoffs = [
                row
                for row in store.native_handoffs()
                if str(row["operator_run_id"]) == args.operator_run_id
            ]
            if not handoffs:
                raise ValueError("native_xhigh_handoff_not_recorded")
            decisions = store.candidate_decisions()
            jobs = store.jobs()
            result = {
                "schema": "contentops.v2.native_automation_shadow_review_result.v1",
                "result": "READY_FOR_OWNER_APP_UI_AUDIT",
                "owner_app_ui_acceptance_claimed": False,
                "operator_run_id": args.operator_run_id,
                "automation": {
                    "id": args.automation_id,
                    "name": args.automation_name,
                    "schedule_proof": args.schedule_proof,
                    "standalone_new_task_per_run": True,
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "high",
                },
                "parent_task_id": args.parent_task_id,
                "parent_model": "gpt-5.6-sol",
                "parent_reasoning_effort": "high",
                "v1_read_snapshot_hash": runs[args.operator_run_id][
                    "v1_read_snapshot_hash"
                ],
                "candidate_decision_ids": [
                    str(row["candidate_version_id"]) for row in decisions
                ],
                "video_job_ids": [str(row["video_job_id"]) for row in jobs],
                "native_handoffs": handoffs,
                "review_queue": store.daily_review_queue(),
                "idempotence": {
                    "operator_run_count": len(runs),
                    "candidate_decision_count": len(decisions),
                    "video_job_count": len(jobs),
                    "duplicate_video_job_count": len(jobs)
                    - len({str(row["video_job_id"]) for row in jobs}),
                },
                "zero_write": {
                    "v1_write_count": 0,
                    "platform_public_write_count": 0,
                    "v1_scheduler_mutation_count": 0,
                    "creative_cli_invocation_count": 0,
                    "creative_sdk_api_invocation_count": 0,
                    "creative_9router_invocation_count": 0,
                    "public_write_authority": False,
                },
            }
            result_path = (
                runtime
                / "runs"
                / args.operator_run_id
                / "automation_review_result.json"
            )
            _write_immutable(result_path, result)
            result["result_path"] = str(result_path)
            result["result_hash"] = hash_value(_load(result_path))
        else:
            result = {
                "schema": "contentops.v2.daily_operator_status.v1",
                "candidate_decisions": store.candidate_decisions(),
                "jobs": store.jobs(),
                "operator_runs": store.operator_runs(),
                "native_handoffs": store.native_handoffs(),
                "review_queue": store.daily_review_queue(),
                "public_write_authority": False,
            }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
