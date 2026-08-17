from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from video.unattended_core_factory_v1.creative import hash_value, validate_input_packet
from video.unattended_core_factory_v1.store import V2JobStore
from video.unattended_core_factory_v1.supervisor import FactoryConfig, UnattendedV2Supervisor


DEFAULT_RUNTIME = REPO / ".task-runtime" / "v2-unattended-core-factory-v1"
DEFAULT_INPUT = (
    REPO
    / "video"
    / "unattended_core_factory_v1"
    / "frozen_without_breaking_proof_input_v1.json"
)
DEFAULT_SCAFFOLD = REPO / "video" / "unattended_core_factory_v1" / "scaffold"


def _head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True, encoding="utf-8"
    ).strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _store(runtime: Path) -> V2JobStore:
    return V2JobStore(runtime / "v2_jobs.sqlite3")


def _load_packet(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    validate_input_packet(value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME)
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="Seed exactly one content-addressed shadow job")
    seed.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    seed.add_argument("--video-job-id")
    seed.add_argument("--priority", type=int, default=100)

    run = sub.add_parser("run-once", help="Claim and execute one eligible V2 job")
    run.add_argument("--dependency-root", type=Path, required=True)
    run.add_argument("--asset-root", type=Path, required=True)
    run.add_argument("--kokoro-model", type=Path, required=True)
    run.add_argument("--kokoro-voices", type=Path, required=True)
    run.add_argument("--worker-id", default="v2-unattended-run-once")
    run.add_argument("--implementation-head", default=None)
    run.add_argument("--proof-run-started-at", default=None)
    run.add_argument("--max-new-stages", type=int)

    status = sub.add_parser("status", help="Read isolated V2 job and ledger state")
    status.add_argument("--video-job-id", required=True)

    args = parser.parse_args()
    runtime = args.runtime_root.resolve()
    store = _store(runtime)
    if args.command == "seed":
        packet_path = args.input.resolve()
        packet = _load_packet(packet_path)
        packet_hash = hash_value(packet)
        job_id = args.video_job_id or f"v2_fwb_{packet_hash[:20]}"
        result = store.seed_job(
            video_job_id=job_id,
            input_packet_path=packet_path,
            input_packet_hash=packet_hash,
            target_format="SHORT_9_16_1080X1920_30FPS",
            priority=args.priority,
        )
        result["input_packet_hash"] = packet_hash
        result["public_write_authority"] = False
    elif args.command == "status":
        result = {
            "job": store.job(args.video_job_id),
            "events": store.events(args.video_job_id),
        }
    else:
        implementation_head = args.implementation_head or _head()
        config = FactoryConfig(
            runtime_root=runtime,
            scaffold_root=DEFAULT_SCAFFOLD,
            dependency_root=args.dependency_root.resolve(),
            asset_root=args.asset_root.resolve(),
            kokoro_model=args.kokoro_model.resolve(),
            kokoro_voices=args.kokoro_voices.resolve(),
            implementation_head=implementation_head,
            worker_id=args.worker_id,
        )
        result = UnattendedV2Supervisor(store=store, config=config).run_once(
            proof_run_started_at=args.proof_run_started_at,
            max_new_stages=args.max_new_stages,
        )
        result["run_once_invoked_at"] = _utc_now()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
