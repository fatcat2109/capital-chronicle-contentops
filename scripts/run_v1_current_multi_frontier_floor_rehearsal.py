"""Stateful zero-write rehearsal for at most four current maximum-12 frontiers.

The script deliberately stops at each native Desktop editorial boundary. ``probe`` captures
the exact governed worker request without using a legacy writer; ``complete`` consumes one
fresh isolated XHIGH return and lets the canonical deterministic validators and package builder
resume.  It never calls a publisher, browser, transport, or production store.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
    _run_rolling_x_newsroom_cycle,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)
from live_contentops.newsroom_assignment_scheduler_v1 import (
    DEFAULT_X_SIDECAR_GLOB,
    build_prepared_rolling_x_candidate_state,
    load_rolling_x_headline_sidecars,
)
from live_contentops.newsroom_production_day_v1 import (
    newsroom_production_day_id,
    persist_qualified_article_record,
    qualify_zero_write_article,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    GroundedArticleBuilderError,
)

SCHEMA = "contentops.v1_current_multi_frontier_floor_rehearsal.v1"
TASK = "TASK_V1_CURRENT_EVIDENCE_YIELD_REACHABILITY_AND_MULTI_FRONTIER_DAILY_FLOOR_CLOSURE_V1"
MAX_FRONTIERS = 4
MAX_QUALIFIED = 4
MAX_XHIGH_ATTEMPTS = 8


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"artifact_not_object:{path}")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=True, separators=(",", ":"), sort_keys=True, default=str
        ).encode("utf-8")
    ).hexdigest()


def _ready() -> dict[str, Any]:
    return {
        "all_required_destinations_ready": True,
        "destinations": {
            destination: {
                "readiness_state": "READY_REHEARSAL_OVERRIDE_NO_WRITE_AUTHORITY",
                "write_eligible": True,
                "identity_match": True,
            }
            for destination in V1_REQUIRED_PUBLICATION_DESTINATIONS
        },
        "fixture_bound": True,
        "publication_authority": False,
    }


def _state_path(root: Path) -> Path:
    return root / "multi_frontier_rehearsal_state_v1.json"


def _new_state(root: Path, sidecar_glob: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    rolling = load_rolling_x_headline_sidecars(
        cutoff_utc=now,
        sidecar_glob=sidecar_glob,
    )
    rolling_path = root / "frozen_current_rolling_input_v1.json"
    _write(rolling_path, rolling)
    state = {
        "schema_version": SCHEMA,
        "task_label": TASK,
        "created_at_utc": now.isoformat().replace("+00:00", "Z"),
        "production_day_id": newsroom_production_day_id(now),
        "cutoff_utc": rolling["cutoff_time_utc"],
        "sidecar_glob": sidecar_glob,
        "rolling_input_path": str(rolling_path),
        "rolling_input_sha256": _sha(rolling),
        "full_current_headline_count": int((rolling.get("counts") or {}).get("accepted") or 0),
        "evaluated_headline_ids": [],
        "qualified_article_records": [],
        "frontiers": [],
        "xhigh_attempt_count": 0,
        "xhigh_revision_count": 0,
        "pending_frontier": None,
        "classification": "IN_PROGRESS",
        "public_write_count": 0,
        "publication_provider_write_count": 0,
        "unknown_write_count": 0,
        "production_store_reset_count": 0,
        "fifth_automation_created_count": 0,
    }
    _write(_state_path(root), state)
    return state


def _state(root: Path, sidecar_glob: str) -> dict[str, Any]:
    path = _state_path(root)
    return _load(path) if path.exists() else _new_state(root, sidecar_glob)


def _attempted_headline_ids(result: Mapping[str, Any]) -> list[str]:
    rows = (result.get("ranked_viability") or {}).get("rank_attempts") or []
    return sorted(
        {
            str(headline_id)
            for row in rows
            if isinstance(row, Mapping)
            for headline_id in row.get("headline_ids") or []
            if str(headline_id)
        }
    )


def _frontier_row(
    *, number: int, prepared: Mapping[str, Any], result: Mapping[str, Any], path: Path
) -> dict[str, Any]:
    viability = dict(result.get("ranked_viability") or {})
    attempted = _attempted_headline_ids(result)
    selected_evidence = dict(viability.get("selected_evidence") or {})
    return {
        "frontier": number,
        "prepared_candidate_count": int(prepared.get("prepared_candidate_count") or 0),
        "prepared_headline_ids": list(
            (prepared.get("prepared_frontier") or {}).get("selected_headline_ids") or []
        ),
        "prepared_candidate_logical_hash": prepared.get("prepared_candidate_logical_hash"),
        "attempted_headline_ids": attempted,
        "attempted_distinct_candidate_count": int(viability.get("attempted_candidate_count") or len(attempted)),
        "selected_rank": viability.get("selected_rank"),
        "selected_cluster_id": viability.get("selected_cluster_id"),
        "evidence_status": selected_evidence.get("status"),
        "result_classification": result.get("classification"),
        "exact_next_blocker": result.get("exact_next_blocker"),
        "cycle_evidence_path": str(path / "rolling_x_newsroom_cycle_evidence_v1.json"),
        "public_write_performed": bool(result.get("public_write_performed")),
        "publishing_adapter_called": bool(result.get("publishing_adapter_called")),
        "unknown_write_detected": bool(result.get("unknown_write_detected")),
    }


def _summary(state: Mapping[str, Any]) -> dict[str, Any]:
    evaluated = set(str(value) for value in state.get("evaluated_headline_ids") or [])
    full = int(state.get("full_current_headline_count") or 0)
    qualified = list(state.get("qualified_article_records") or [])
    completed = len(state.get("frontiers") or [])
    classification = (
        "FLOOR_MET"
        if len(qualified) >= MAX_QUALIFIED
        else "DEGRADED_DAILY_OUTPUT_DEFICIT"
        if completed >= MAX_FRONTIERS and not state.get("pending_frontier")
        else "IN_PROGRESS"
    )
    return {
        **dict(state),
        "classification": classification,
        "frontier_count": completed,
        "distinct_candidate_count": len(evaluated),
        "remaining_held_identity_count": max(0, full - len(evaluated)),
        "qualified_count": len(qualified),
        "remaining_build_deficit": max(0, MAX_QUALIFIED - len(qualified)),
        "no_repeat_proof": len(evaluated)
        == sum(len(row.get("attempted_headline_ids") or []) for row in state.get("frontiers") or []),
        "safety": {
            "public_writes": int(state.get("public_write_count") or 0),
            "publication_provider_writes": int(state.get("publication_provider_write_count") or 0),
            "unknown_write": int(state.get("unknown_write_count") or 0),
            "production_store_reset": int(state.get("production_store_reset_count") or 0),
            "fifth_automation_created": int(state.get("fifth_automation_created_count") or 0),
        },
    }


def probe(root: Path, sidecar_glob: str) -> dict[str, Any]:
    state = _state(root, sidecar_glob)
    if state.get("pending_frontier"):
        raise ValueError("pending_frontier_must_be_completed_first")
    if len(state.get("frontiers") or []) >= MAX_FRONTIERS:
        raise ValueError("four_frontier_budget_exhausted")
    if len(state.get("qualified_article_records") or []) >= MAX_QUALIFIED:
        raise ValueError("daily_floor_already_met")
    number = len(state.get("frontiers") or []) + 1
    rolling = _load(Path(str(state["rolling_input_path"])))
    prepared = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling,
        prepared_at_utc=state["cutoff_utc"],
        evaluated_headline_ids=state.get("evaluated_headline_ids") or [],
    )
    frontier_root = root / f"frontier_{number}"
    prepared_path = frontier_root / "prepared_candidate_state_v1.json"
    _write(prepared_path, prepared)
    probe_dir = frontier_root / "route_probe"
    if (probe_dir / "rolling_x_newsroom_cycle_evidence_v1.json").exists():
        suffix = 2
        while (
            frontier_root
            / f"route_probe_attempt_{suffix}"
            / "rolling_x_newsroom_cycle_evidence_v1.json"
        ).exists():
            suffix += 1
        probe_dir = frontier_root / f"route_probe_attempt_{suffix}"
    result = _run_rolling_x_newsroom_cycle(
        run_id=f"v1-current-floor-frontier-{number}-route-probe",
        output_dir=probe_dir,
        cutoff_utc=str(state["cutoff_utc"]),
        rolling_input=rolling,
        prepared_candidate_state=prepared,
        publication_enabled=True,
        operating_mode="KILL_SWITCH",
        destination_readiness_override=_ready(),
    )
    route = dict(result.get("editorial_worker_routing") or {})
    row = _frontier_row(number=number, prepared=prepared, result=result, path=probe_dir)
    row["prepared_state_path"] = str(prepared_path)
    if route.get("decision") == "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER":
        if int(state.get("xhigh_attempt_count") or 0) >= MAX_XHIGH_ATTEMPTS:
            raise ValueError("xhigh_attempt_budget_exhausted")
        request_path = frontier_root / "editorial_worker_request_v1.json"
        _write(request_path, dict(route.get("worker_request") or {}))
        state["xhigh_attempt_count"] = int(state.get("xhigh_attempt_count") or 0) + 1
        state["pending_frontier"] = {
            **row,
            "prepared_state_path": str(prepared_path),
            "worker_request_path": str(request_path),
            "governed_input_hash": route.get("governed_input_hash"),
            "probe_cycle_evidence_path": row["cycle_evidence_path"],
        }
        _write(_state_path(root), state)
        return {"status": "XHIGH_REQUIRED", **dict(state["pending_frontier"])}

    state["evaluated_headline_ids"] = sorted(
        set(state.get("evaluated_headline_ids") or []).union(row["attempted_headline_ids"])
    )
    state["frontiers"] = [*list(state.get("frontiers") or []), row]
    state["pending_frontier"] = None
    state = _summary(state)
    _write(_state_path(root), state)
    _write(root / "multi_frontier_floor_rehearsal_summary_v1.json", state)
    return {"status": "FRONTIER_COMPLETE_NO_XHIGH", **row, "summary": state}


def complete(root: Path, worker_return_path: Path) -> dict[str, Any]:
    state = _load(_state_path(root))
    pending = dict(state.get("pending_frontier") or {})
    if not pending:
        raise ValueError("no_pending_frontier")
    receipt = _load(worker_return_path)
    expected_hash = str(pending.get("governed_input_hash") or "")
    if str(receipt.get("governed_input_hash") or "") != expected_hash:
        raise ValueError("worker_return_governed_input_hash_mismatch")
    rolling = _load(Path(str(state["rolling_input_path"])))
    prepared = _load(Path(str(pending["prepared_state_path"])))

    def builder(value: Mapping[str, Any]) -> dict[str, Any]:
        request = dict(value.get("editorial_worker_request") or {})
        if str(request.get("governed_input_hash") or "") != expected_hash:
            raise GroundedArticleBuilderError("TRIGGER_V1_CODEX_EDITORIAL_BRAIN_VERTICAL_SLICE")
        return {
            "schema_version": "contentops.rolling_x_grounded_article_media_builder.v1",
            "article": dict(receipt.get("article") or {}),
            "media": {"assets": []},
            "critical_path_telemetry": {
                "article_writer_semantic_calls": 1,
                "article_writer_owner": "FRESH_NATIVE_CODEX_DESKTOP_XHIGH",
            },
            "editorial_worker_receipt": receipt,
        }

    number = int(pending["frontier"])
    final_dir = root / f"frontier_{number}" / "canonical_zero_write_rehearsal"
    result = _run_rolling_x_newsroom_cycle(
        run_id=f"v1-current-floor-frontier-{number}-canonical-zero-write",
        output_dir=final_dir,
        cutoff_utc=str(state["cutoff_utc"]),
        rolling_input=rolling,
        prepared_candidate_state=prepared,
        article_builder=builder,
        publication_enabled=True,
        operating_mode="KILL_SWITCH",
        destination_readiness_override=_ready(),
    )
    row = _frontier_row(number=number, prepared=prepared, result=result, path=final_dir)
    row["prepared_state_path"] = pending["prepared_state_path"]
    row["governed_input_hash"] = expected_hash
    row["worker_return_path"] = str(worker_return_path)
    row["worker_return_sha256"] = _sha(receipt)
    row["bounded_revision_count"] = int(receipt.get("bounded_revision_count") or 0)
    state["xhigh_revision_count"] = int(state.get("xhigh_revision_count") or 0) + row[
        "bounded_revision_count"
    ]
    state["evaluated_headline_ids"] = sorted(
        set(state.get("evaluated_headline_ids") or []).union(row["attempted_headline_ids"])
    )
    if result.get("classification") == "PASS_PUBLICATION_PLAN_READY":
        record = qualify_zero_write_article(
            result=result,
            output_dir=final_dir,
            production_day_id=str(state["production_day_id"]),
            parent_window_id=f"bounded-rehearsal-frontier-{number}",
        )
        row["qualification"] = record
        if record.get("qualified") is True:
            record_path = persist_qualified_article_record(final_dir, record)
            state["qualified_article_records"] = [
                *list(state.get("qualified_article_records") or []),
                {**record, "record_path": str(record_path)},
            ]
    state["public_write_count"] = int(state.get("public_write_count") or 0) + int(
        bool(result.get("public_write_performed"))
    )
    state["unknown_write_count"] = int(state.get("unknown_write_count") or 0) + int(
        bool(result.get("unknown_write_detected"))
    )
    state["frontiers"] = [*list(state.get("frontiers") or []), row]
    state["pending_frontier"] = None
    state = _summary(state)
    _write(_state_path(root), state)
    _write(root / "multi_frontier_floor_rehearsal_summary_v1.json", state)
    return {"status": "FRONTIER_COMPLETE", "frontier": row, "summary": state}


def repair_empty_last_frontier(root: Path) -> dict[str, Any]:
    """Remove only a harness-produced empty frontier when held identities still exist."""
    state = _load(_state_path(root))
    rows = list(state.get("frontiers") or [])
    if not rows:
        raise ValueError("no_frontier_to_repair")
    last = dict(rows[-1])
    if (
        int(last.get("prepared_candidate_count") or 0) != 0
        or int(state.get("full_current_headline_count") or 0)
        <= len(state.get("evaluated_headline_ids") or [])
        or last.get("attempted_headline_ids")
    ):
        raise ValueError("last_frontier_not_repairable_empty_harness_result")
    state["frontiers"] = rows[:-1]
    state = _summary(state)
    _write(_state_path(root), state)
    _write(root / "multi_frontier_floor_rehearsal_summary_v1.json", state)
    return {"status": "EMPTY_HARNESS_FRONTIER_REMOVED", "removed": last, "summary": state}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--action",
        choices=("probe", "complete", "summary", "repair-empty-last"),
        required=True,
    )
    parser.add_argument("--sidecar-glob", default=DEFAULT_X_SIDECAR_GLOB)
    parser.add_argument("--worker-return", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == "probe":
        result = probe(root, args.sidecar_glob)
    elif args.action == "complete":
        if args.worker_return is None:
            raise ValueError("worker_return_required")
        result = complete(root, args.worker_return.resolve(strict=True))
    elif args.action == "repair-empty-last":
        result = repair_empty_last_frontier(root)
    else:
        result = _summary(_load(_state_path(root)))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
