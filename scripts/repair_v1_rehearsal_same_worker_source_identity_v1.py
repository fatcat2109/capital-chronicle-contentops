"""Restore one hash-bound rehearsal frontier for its permitted same-worker repair.

This is deliberately narrower than a generic retry.  It accepts only the observed
reader-visible source-identity failure, proves that the revised return is from the
same governed worker contract, preserves the failed attempt as evidence, and then
restores the pre-completion checkpoint for one deterministic resume.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_v1_current_multi_frontier_floor_rehearsal as rehearsal


EXPECTED_TERMINAL_REASON = "GROUNDED_ARTICLE_BUILDER_FAIL_CLOSED"
EXPECTED_BLOCKER = "article_source_identity_reference_missing"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"artifact_not_object:{path}")
    return value


def repair(root: Path, original_return_path: Path, revision_return_path: Path) -> dict[str, Any]:
    state_path = root / "multi_frontier_rehearsal_state_v1.json"
    state = _load(state_path)
    frontiers = list(state.get("frontiers") or [])
    if len(frontiers) != 1 or state.get("pending_frontier"):
        raise ValueError("repair_requires_one_completed_frontier_and_no_pending_frontier")
    if state.get("qualified_article_records"):
        raise ValueError("repair_forbidden_after_qualification")
    if int(state.get("public_write_count") or 0) != 0 or int(
        state.get("unknown_write_count") or 0
    ) != 0:
        raise ValueError("repair_requires_zero_write_state")

    failed_row = dict(frontiers[0])
    failed_cycle_path = Path(str(failed_row.get("cycle_evidence_path") or ""))
    failed_cycle = _load(failed_cycle_path)
    if (
        failed_cycle.get("classification") != "NO_PUBLICATION"
        or failed_cycle.get("exact_next_blocker") != "ALL_BOUNDED_CANDIDATES_EXHAUSTED"
    ):
        raise ValueError("repair_requires_exact_failed_candidate_walk")
    failed_attempts = [
        dict(row)
        for row in (failed_cycle.get("candidate_walk") or {}).get("candidate_attempts") or []
        if row.get("terminal_reason") == EXPECTED_TERMINAL_REASON
        and EXPECTED_BLOCKER in (row.get("writer_blockers") or [])
    ]
    if len(failed_attempts) != 1:
        raise ValueError("repair_requires_single_exact_source_identity_failure")

    original_return = _load(original_return_path)
    revision_return = _load(revision_return_path)
    original_hash = rehearsal._sha(original_return)
    if original_hash != str(failed_row.get("worker_return_sha256") or ""):
        raise ValueError("original_worker_return_hash_mismatch")
    governed_hash = str(original_return.get("governed_input_hash") or "")
    if (
        revision_return.get("same_worker_revision_of_return_hash") != original_hash
        or revision_return.get("governed_input_hash") != governed_hash
        or int(revision_return.get("bounded_revision_count") or 0) != 1
        or revision_return.get("model") != original_return.get("model")
        or revision_return.get("reasoning_effort") != original_return.get("reasoning_effort")
        or revision_return.get("fresh") is not True
        or revision_return.get("isolated") is not True
        or revision_return.get("resume_existing") is not False
    ):
        raise ValueError("same_worker_bounded_revision_contract_invalid")

    frontier_root = root / "frontier_1"
    prepared_path = frontier_root / "prepared_candidate_state_v1.json"
    probe_dir = frontier_root / "route_probe"
    probe_cycle_path = probe_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
    viability_path = probe_dir / "rolling_x_ranked_viability_v1.json"
    request_path = frontier_root / "editorial_worker_request_v1.json"
    prepared = _load(prepared_path)
    probe = _load(probe_cycle_path)
    row = rehearsal._frontier_row(
        number=1,
        prepared=prepared,
        result=probe,
        path=probe_dir,
    )
    if row.get("selected_rank") != failed_attempts[0].get("rank"):
        raise ValueError("failed_worker_candidate_does_not_match_probe_selection")
    row["prepared_state_path"] = str(prepared_path)
    snapshot = _load(root / "current_durable_state_readonly_v1.json")

    repair_receipt = {
        "schema_version": "contentops.v1_rehearsal_same_worker_source_identity_repair.v1",
        "repair_scope": "ONE_FAILED_FRONTIER_ONE_SAME_WORKER_REVISION",
        "failed_cycle_evidence_path": str(failed_cycle_path),
        "failed_cycle_sha256": rehearsal._sha(failed_cycle),
        "failed_terminal_reason": EXPECTED_TERMINAL_REASON,
        "failed_blocker": EXPECTED_BLOCKER,
        "failed_candidate_rank": failed_attempts[0].get("rank"),
        "failed_candidate_cluster_id": failed_attempts[0].get("cluster_id"),
        "original_worker_return_path": str(original_return_path),
        "original_worker_return_sha256": original_hash,
        "revision_worker_return_path": str(revision_return_path),
        "revision_worker_return_sha256": rehearsal._sha(revision_return),
        "governed_input_hash": governed_hash,
        "bounded_revision_count": 1,
        "same_worker_contract_verified": True,
        "failed_attempt_preserved": True,
        "public_write_count": 0,
        "unknown_write_count": 0,
    }
    repair_receipt["receipt_sha256"] = rehearsal._sha(repair_receipt)
    receipt_path = frontier_root / "same_worker_source_identity_repair_receipt_v1.json"
    rehearsal._write(receipt_path, repair_receipt)

    state["evaluated_headline_ids"] = list(snapshot.get("evaluated_headline_ids") or [])
    state["frontiers"] = []
    state["qualified_article_records"] = []
    state["xhigh_worker_return_count"] = 0
    state["xhigh_revision_count"] = 0
    state["pending_frontier"] = {
        **row,
        "prepared_state_path": str(prepared_path),
        "worker_request_path": str(request_path),
        "governed_input_hash": governed_hash,
        "probe_cycle_evidence_path": str(probe_cycle_path),
        "viability_checkpoint_path": str(viability_path),
        "same_worker_repair_receipt_path": str(receipt_path),
    }
    state = rehearsal._summary(state, root)
    rehearsal._write(state_path, state)
    rehearsal._write(root / "multi_frontier_floor_rehearsal_summary_v1.json", state)
    return {
        "status": "SAME_WORKER_SOURCE_IDENTITY_REVISION_READY",
        "pending_frontier": state["pending_frontier"],
        "repair_receipt_path": str(receipt_path),
        "repair_receipt": repair_receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--original-worker-return", type=Path, required=True)
    parser.add_argument("--revision-worker-return", type=Path, required=True)
    args = parser.parse_args()
    result = repair(
        args.root.resolve(strict=True),
        args.original_worker_return.resolve(strict=True),
        args.revision_worker_return.resolve(strict=True),
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
