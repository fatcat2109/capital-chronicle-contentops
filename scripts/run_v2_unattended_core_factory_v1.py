"""Explicit stage interface for the Codex Desktop-session-native V2 core factory."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from video.unattended_core_factory_v1.creative import hash_value, validate_input_packet
from video.unattended_core_factory_v1.desktop_session import DesktopSessionProvenance
from video.unattended_core_factory_v1.store import V2JobStore
from video.unattended_core_factory_v1.supervisor import DesktopSessionV2Factory, FactoryConfig


DEFAULT_RUNTIME = REPO / ".task-runtime" / "v2-desktop-session-core-proof-v1"
DEFAULT_INPUT = (
    REPO
    / "video"
    / "unattended_core_factory_v1"
    / "frozen_without_breaking_proof_input_v1.json"
)
DEFAULT_SCAFFOLD = REPO / "video" / "unattended_core_factory_v1" / "scaffold"
SOURCE_FILES = ("src/index.tsx", "src/Root.tsx", "src/Short.tsx")


def _head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True, encoding="utf-8"
    ).strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _store(runtime: Path) -> V2JobStore:
    return V2JobStore(runtime / "v2_jobs.sqlite3")


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _load_motion(manifest_path: Path, source_root: Path) -> dict[str, Any]:
    motion = _load_object(manifest_path)
    motion["files"] = {
        relative: (source_root / Path(relative)).read_text(encoding="utf-8")
        for relative in SOURCE_FILES
    }
    return motion


def _load_review(review_path: Path, replacement_source_root: Path | None) -> dict[str, Any]:
    review = _load_object(review_path)
    if review.get("decision") == "MATERIAL_REVISION_REQUIRED":
        if replacement_source_root is None:
            raise ValueError("--replacement-source-root is required for material revision")
        review["replacement_files"] = {
            relative: (replacement_source_root / Path(relative)).read_text(encoding="utf-8")
            for relative in SOURCE_FILES
        }
    else:
        review["replacement_files"] = {}
    return review


def _add_factory_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dependency-root", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--kokoro-model", type=Path, required=True)
    parser.add_argument("--kokoro-voices", type=Path, required=True)
    parser.add_argument("--worker-id", default="v2-desktop-session-core-proof")
    parser.add_argument("--implementation-head", default=None)


def _factory(args: argparse.Namespace, runtime: Path, store: V2JobStore) -> DesktopSessionV2Factory:
    config = FactoryConfig(
        runtime_root=runtime,
        scaffold_root=DEFAULT_SCAFFOLD,
        dependency_root=args.dependency_root.resolve(),
        asset_root=args.asset_root.resolve(),
        kokoro_model=args.kokoro_model.resolve(),
        kokoro_voices=args.kokoro_voices.resolve(),
        implementation_head=args.implementation_head or _head(),
        worker_id=args.worker_id,
    )
    return DesktopSessionV2Factory(store=store, config=config)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME)
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="Seed exactly one content-addressed shadow job")
    seed.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    seed.add_argument("--video-job-id")
    seed.add_argument("--priority", type=int, default=100)

    start = sub.add_parser("start", help="Atomically claim and lock the governed input")
    _add_factory_args(start)
    start.add_argument("--proof-run-started-at", default=None)

    creative = sub.add_parser(
        "submit-creative", help="Submit this Desktop task's initial creative artifacts"
    )
    _add_factory_args(creative)
    creative.add_argument("--video-job-id", required=True)
    creative.add_argument("--run-id", required=True)
    creative.add_argument("--editorial", type=Path, required=True)
    creative.add_argument("--source-manifest", type=Path, required=True)
    creative.add_argument("--source-root", type=Path, required=True)
    creative.add_argument("--session-label", required=True)

    advance = sub.add_parser(
        "advance", help="Run deterministic stages until the next Desktop-session gate or terminal"
    )
    _add_factory_args(advance)
    advance.add_argument("--video-job-id", required=True)
    advance.add_argument("--run-id", required=True)

    review = sub.add_parser(
        "submit-review", help="Submit this same Desktop task's actual-media review"
    )
    _add_factory_args(review)
    review.add_argument("--video-job-id", required=True)
    review.add_argument("--run-id", required=True)
    review.add_argument("--review", type=Path, required=True)
    review.add_argument("--replacement-source-root", type=Path)
    review.add_argument("--session-label", required=True)

    status = sub.add_parser("status", help="Read isolated V2 job and immutable ledger")
    status.add_argument("--video-job-id", required=True)

    args = parser.parse_args()
    runtime = args.runtime_root.resolve()
    store = _store(runtime)
    if args.command == "seed":
        packet_path = args.input.resolve()
        packet = _load_object(packet_path)
        validate_input_packet(packet)
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
        result = {"job": store.job(args.video_job_id), "events": store.events(args.video_job_id)}
    else:
        factory = _factory(args, runtime, store)
        if args.command == "start":
            result = factory.run_once(proof_run_started_at=args.proof_run_started_at)
        elif args.command == "submit-creative":
            result = factory.submit_initial_creative(
                video_job_id=args.video_job_id,
                run_id=args.run_id,
                editor=_load_object(args.editorial.resolve()),
                motion=_load_motion(args.source_manifest.resolve(), args.source_root.resolve()),
                provenance=DesktopSessionProvenance(session_label=args.session_label),
            )
        elif args.command == "submit-review":
            result = factory.submit_actual_media_review(
                video_job_id=args.video_job_id,
                run_id=args.run_id,
                review=_load_review(
                    args.review.resolve(),
                    args.replacement_source_root.resolve()
                    if args.replacement_source_root
                    else None,
                ),
                provenance=DesktopSessionProvenance(session_label=args.session_label),
            )
        else:
            result = factory.resume(video_job_id=args.video_job_id, run_id=args.run_id)
        result["command_completed_at"] = _utc_now()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
