"""Stateful zero-write rehearsal for four qualified current frontiers.

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
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    CANONICAL_PRODUCTION_OUTPUT_ROOT,
    CANONICAL_PRODUCTION_STORE_PATH,
    load_terminal_editorial_continuity,
    validate_editorial_worker_return,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.editorial_portfolio_v1 import PublishedArticleRef
from live_contentops.newsroom_assignment_scheduler_v1 import (
    DEFAULT_X_SIDECAR_GLOB,
    _logical_hash,
    _rolling_x_canonical_hash_material,
    build_prepared_rolling_x_candidate_state,
    load_rolling_x_headline_sidecars,
)
from live_contentops.newsroom_production_day_v1 import (
    build_production_day_snapshot,
    newsroom_production_day_id,
    persist_production_day_snapshot,
    persist_qualified_article_record,
    qualify_zero_write_article,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    GroundedArticleBuilderError,
    resolve_editorial_worker_article_for_public_lock,
)
from live_contentops.mvp_canary_acceptance_v1 import (
    MVP_CANARY_ACCEPTANCE_PROFILE,
    is_mvp_canary_profile,
)
from live_contentops.published_corpus_read_model_v1 import load_published_corpus

SCHEMA = "contentops.v1_distinct_story_frontier_floor_rehearsal.v1"
TASK = "TASK_V1_PREPARED_FRONTIER_PUBLISHABILITY_POOL_REUSE_4_32_AND_ONE_CANARY_V1"
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


def _evidence_request_identity(
    request: Mapping[str, Any],
) -> tuple[str, tuple[str, ...], str, str]:
    return (
        str(request.get("cluster_id") or ""),
        tuple(sorted(str(value) for value in request.get("headline_ids") or [])),
        str(request.get("story_evidence_scope_id") or ""),
        str(
            request.get("effective_article_mode")
            or request.get("resolved_article_mode")
            or ""
        ),
    )


class _StageAEvidenceReuseAcquirer:
    """Reuse exact Stage A receipts, falling back to the canonical evidence adapter."""

    def __init__(
        self,
        *,
        stage_a_root: Path,
        evaluation_as_of_utc: str,
    ) -> None:
        from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
            RollingXTargetedEvidenceAdapter,
        )

        self._stage_a_root = stage_a_root
        self._receipts: dict[
            tuple[str, tuple[str, ...], str, str], dict[str, Any]
        ] = {}
        self._reuse_hits: list[dict[str, Any]] = []
        self._fallback_calls: list[dict[str, Any]] = []
        latest_health: dict[str, Any] = {}
        for cycle_path in sorted(
            stage_a_root.glob(
                "frontier_*/rolling_x_newsroom_cycle_evidence_v1.json"
            )
        ):
            cycle = _load(cycle_path)
            health = cycle.get("source_route_health")
            if isinstance(health, Mapping):
                latest_health = dict(health)
            for attempt in (
                (cycle.get("ranked_viability") or {}).get("rank_attempts")
                or []
            ):
                if not isinstance(attempt, Mapping):
                    continue
                request = attempt.get("request")
                receipt = attempt.get("evidence_receipt")
                if not isinstance(request, Mapping) or not isinstance(
                    receipt, Mapping
                ):
                    continue
                identity = _evidence_request_identity(request)
                if not identity[0] or not identity[1] or not identity[2] or not identity[3]:
                    continue
                self._receipts[identity] = {
                    "receipt": json.loads(json.dumps(receipt)),
                    "original_request_logical_hash": str(
                        request.get("request_logical_hash") or ""
                    ),
                }
        self._fallback = RollingXTargetedEvidenceAdapter(
            evaluation_as_of_utc=evaluation_as_of_utc,
            source_route_health=latest_health,
        )

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
        identity = _evidence_request_identity(request)
        cached_record = self._receipts.get(identity)
        if cached_record is not None:
            receipt = json.loads(json.dumps(cached_record["receipt"]))
            current_request_hash = str(
                request.get("request_logical_hash") or ""
            )
            for document in receipt.get("evidence_documents") or []:
                if isinstance(document, dict):
                    document["request_logical_hash"] = current_request_hash
            original_receipt_sha256 = _sha(cached_record["receipt"])
            receipt["stage_a_evidence_reuse"] = {
                "schema_version": "contentops.stage_a_evidence_reuse_binding.v1",
                "story_evidence_scope_id": identity[2],
                "effective_article_mode": identity[3],
                "original_request_logical_hash": cached_record[
                    "original_request_logical_hash"
                ],
                "current_request_logical_hash": current_request_hash,
                "original_evidence_receipt_sha256": original_receipt_sha256,
                "source_document_content_hashes_unchanged": True,
                "source_or_factual_authority_granted": False,
                "publication_authority_granted": False,
            }
            self._reuse_hits.append(
                {
                    "story_identity": identity[0],
                    "headline_ids": list(identity[1]),
                    "story_evidence_scope_id": identity[2],
                    "effective_article_mode": identity[3],
                    "original_request_logical_hash": cached_record[
                        "original_request_logical_hash"
                    ],
                    "current_request_logical_hash": current_request_hash,
                    "evidence_receipt_sha256": _sha(receipt),
                }
            )
            return receipt
        self._fallback_calls.append(
            {
                "story_identity": identity[0],
                "headline_ids": list(identity[1]),
                "story_evidence_scope_id": identity[2],
                "effective_article_mode": identity[3],
                "request_logical_hash": request.get("request_logical_hash"),
            }
        )
        return dict(self._fallback(request))

    def source_route_health_snapshot(self) -> dict[str, Any]:
        return dict(self._fallback.source_route_health_snapshot())

    def manifest(self) -> dict[str, Any]:
        ready_receipts = sum(
            (row.get("receipt") or {}).get("status") == "PASS"
            and not (row.get("receipt") or {}).get("blockers")
            for row in self._receipts.values()
        )
        return {
            "schema_version": "contentops.stage_a_evidence_reuse.v1",
            "stage_a_root": str(self._stage_a_root),
            "cached_exact_request_count": len(self._receipts),
            "cached_ready_receipt_count": ready_receipts,
            "reuse_hit_count": len(self._reuse_hits),
            "fallback_call_count": len(self._fallback_calls),
            "reuse_hits": list(self._reuse_hits),
            "fallback_calls": list(self._fallback_calls),
            "request_identity_requires_cluster_headlines_scope_and_mode": True,
            "diagnostic_request_hash_may_rebind_within_exact_scope": True,
            "cached_model_output_grants_factual_or_publication_authority": False,
        }


def _stage_a_ready_frontiers(stage_a_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cycle_path in sorted(
        stage_a_root.glob(
            "frontier_*/rolling_x_newsroom_cycle_evidence_v1.json"
        )
    ):
        cycle = _load(cycle_path)
        candidates = [
            dict(row)
            for row in (cycle.get("evidence_ready_pool") or {}).get(
                "candidates"
            )
            or []
            if isinstance(row, Mapping) and row.get("cluster_id")
        ]
        if not candidates:
            continue
        prepared_path = (
            cycle_path.parent / "rolling_x_prepared_candidate_state_v1.json"
        )
        if not prepared_path.is_file():
            raise ValueError("stage_a_ready_frontier_prepared_state_missing")
        rows.append(
            {
                "stage_a_frontier": int(
                    str(cycle_path.parent.name).rsplit("_", 1)[-1]
                ),
                "cycle_evidence_path": str(cycle_path),
                "cycle_evidence_sha256": _sha(cycle),
                "prepared_state_path": str(prepared_path),
                "prepared_state_sha256": _sha(_load(prepared_path)),
                "ready_candidate_ids": [
                    str(row.get("cluster_id")) for row in candidates
                ],
                "ready_candidate_count": len(candidates),
            }
        )
    return rows


def _current_durable_state() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Read the canonical continuity and published corpus without mutating either."""
    continuity = load_terminal_editorial_continuity(
        store_path=CANONICAL_PRODUCTION_STORE_PATH,
        output_root=CANONICAL_PRODUCTION_OUTPUT_ROOT,
    )
    store = ContentOpsDurableStore(CANONICAL_PRODUCTION_STORE_PATH, auto_migrate=False)
    corpus = load_published_corpus(store, output_root=CANONICAL_PRODUCTION_OUTPUT_ROOT)
    articles = [article.to_dict() for article in corpus.get("articles") or []]
    snapshot = {
        "schema_version": "contentops.v1_current_durable_proof_input.v1",
        "store_path": str(CANONICAL_PRODUCTION_STORE_PATH),
        "output_root": str(CANONICAL_PRODUCTION_OUTPUT_ROOT),
        "store_open_mode": "SQLITE_URI_MODE_RO_QUERY_ONLY",
        "database_writes_performed": False,
        "filesystem_writes_performed": False,
        "continuity_state": continuity.get("state"),
        "continuity_logical_hash": continuity.get("continuity_logical_hash"),
        "terminal_window_id": continuity.get("terminal_window_id"),
        "last_terminal_cutoff_utc": continuity.get("last_terminal_cutoff_utc"),
        "evaluated_headline_ids": list(continuity.get("evaluated_headline_ids") or []),
        "evaluated_headline_count": int(continuity.get("evaluated_headline_count") or 0),
        "confirmed_canonical_count": int(corpus.get("article_count") or 0),
        "published_articles": articles,
        "italy_canary_matches": [
            {
                "story_identity": article.get("story_identity"),
                "article_identity": article.get("article_identity"),
                "title": article.get("title"),
                "published_at_utc": article.get("published_at_utc"),
                "content_status": article.get("content_status"),
                "source_work_item_id": article.get("source_work_item_id"),
            }
            for article in articles
            if "apkws ii sale to italy" in str(article.get("title") or "").casefold()
        ],
    }
    snapshot["snapshot_sha256"] = _sha(snapshot)
    return snapshot, articles


def _published_corpus_from_state(state: Mapping[str, Any]) -> list[PublishedArticleRef]:
    records = []
    for value in state.get("published_corpus") or []:
        row = dict(value)
        row["entities"] = tuple(row.get("entities") or ())
        row["derivative_public_objects"] = tuple(
            dict(item) for item in row.get("derivative_public_objects") or []
        )
        records.append(PublishedArticleRef(**row))
    return records


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


def _load_parent_cycle_replay_input(parent_cycle_root: Path) -> dict[str, Any]:
    paths = sorted(
        parent_cycle_root.glob(
            "frontier_*/route_probe/rolling_x_newsroom_cycle_evidence_v1.json"
        ),
        key=lambda path: int(path.parents[1].name.rsplit("_", 1)[-1]),
    )
    if len(paths) != MAX_FRONTIERS:
        raise ValueError("parent_cycle_replay_requires_exactly_four_frontiers")
    cycles = [_load(path) for path in paths]
    rows_by_id: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    for cycle in cycles:
        for row in (cycle.get("intake") or {}).get("headlines") or []:
            headline_id = str(row.get("headline_id") or "")
            if not headline_id or headline_id in rows_by_id:
                continue
            rows_by_id[headline_id] = dict(row)
            ordered_ids.append(headline_id)
    if len(ordered_ids) != 48:
        raise ValueError("parent_cycle_replay_requires_exactly_48_headline_identities")
    first = dict(cycles[0].get("intake") or {})
    rolling = {
        **first,
        "unique_headline_ids": ordered_ids,
        "headlines": [rows_by_id[headline_id] for headline_id in ordered_ids],
        "counts": {**dict(first.get("counts") or {}), "accepted": len(ordered_ids)},
        "complete_input_coverage": True,
        "parent_cycle_replay_source_paths": [str(path) for path in paths],
    }
    rolling["canonical_input_hash"] = _logical_hash(
        _rolling_x_canonical_hash_material(rolling)
    )
    return rolling


def _new_state(
    root: Path,
    sidecar_glob: str,
    rolling_input_path: Path | None = None,
    parent_cycle_root: Path | None = None,
    cycle_artifact_path: Path | None = None,
    task_label: str = TASK,
    acceptance_profile: str | None = None,
    current_durable_state: bool = False,
    stage_a_evidence_root: Path | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    rolling = (
        _load(rolling_input_path)
        if rolling_input_path is not None
        else dict(_load(cycle_artifact_path).get("intake") or {})
        if cycle_artifact_path is not None
        else _load_parent_cycle_replay_input(parent_cycle_root)
        if parent_cycle_root is not None
        else load_rolling_x_headline_sidecars(
            cutoff_utc=now,
            sidecar_glob=sidecar_glob,
        )
    )
    rolling_path = root / "frozen_current_rolling_input_v1.json"
    _write(rolling_path, rolling)
    stage_a_binding: dict[str, Any] = {}
    if stage_a_evidence_root is not None:
        stage_a_input_path = (
            stage_a_evidence_root / "frozen_current_rolling_input_v1.json"
        )
        stage_a_input = _load(stage_a_input_path)
        if _sha(stage_a_input) != _sha(rolling):
            raise ValueError("stage_a_evidence_rolling_input_identity_mismatch")
        ready_frontiers = _stage_a_ready_frontiers(stage_a_evidence_root)
        if sum(
            int(row.get("ready_candidate_count") or 0)
            for row in ready_frontiers
        ) < MAX_QUALIFIED:
            raise ValueError("stage_a_four_ready_candidates_required")
        stage_a_binding = {
            "stage_a_evidence_root": str(stage_a_evidence_root),
            "stage_a_frozen_input_path": str(stage_a_input_path),
            "stage_a_frozen_input_sha256": _sha(stage_a_input),
            "same_frozen_universe_required": True,
            "ready_frontiers": ready_frontiers,
            "ready_frontier_cursor": 0,
            "prepared_and_router_checkpoint_reuse_required": True,
        }
    current_headline_ids = sorted(
        {
            str(row.get("headline_id") or row.get("id"))
            for row in rolling.get("headlines") or []
            if isinstance(row, Mapping) and (row.get("headline_id") or row.get("id"))
        }
    )
    durable_snapshot: dict[str, Any] = {}
    published_corpus: list[dict[str, Any]] = []
    evaluated_headline_ids: list[str] = []
    if current_durable_state:
        durable_snapshot, published_corpus = _current_durable_state()
        evaluated_headline_ids = list(durable_snapshot["evaluated_headline_ids"])
        _write(root / "current_durable_state_readonly_v1.json", durable_snapshot)
    state = {
        "schema_version": SCHEMA,
        "task_label": task_label,
        "acceptance_profile": acceptance_profile,
        "created_at_utc": now.isoformat().replace("+00:00", "Z"),
        "production_day_id": newsroom_production_day_id(now),
        "cutoff_utc": rolling["cutoff_time_utc"],
        "sidecar_glob": sidecar_glob,
        "input_mode": (
            "FROZEN_REPLAY"
            if rolling_input_path
            else "COMMITTED_FRONTIER_ARTIFACT_REPLAY"
            if cycle_artifact_path
            else "PARENT_FOUR_FRONTIER_REPLAY"
            if parent_cycle_root
            else "GENUINE_CURRENT_INPUT"
        ),
        "source_rolling_input_path": str(rolling_input_path) if rolling_input_path else None,
        "source_parent_cycle_root": str(parent_cycle_root) if parent_cycle_root else None,
        "source_cycle_artifact_path": (
            str(cycle_artifact_path) if cycle_artifact_path else None
        ),
        "rolling_input_path": str(rolling_path),
        "rolling_input_sha256": _sha(rolling),
        "full_current_headline_count": len(current_headline_ids),
        "current_headline_ids": current_headline_ids,
        "evaluated_headline_ids": evaluated_headline_ids,
        "initial_evaluated_headline_count": len(evaluated_headline_ids),
        "current_durable_state_bound": current_durable_state,
        "current_durable_state_snapshot": durable_snapshot,
        "stage_a_evidence_binding": stage_a_binding,
        "stage_a_evidence_reuse_hits": [],
        "stage_a_evidence_fallback_calls": [],
        "published_corpus": published_corpus,
        "published_canonical_article_count": len(published_corpus),
        "italy_canary_published_memory_count": len(
            durable_snapshot.get("italy_canary_matches") or []
        ),
        "qualified_article_records": [],
        "mvp_canary_artifact_records": [],
        "frontiers": [],
        "xhigh_attempt_count": 0,
        "xhigh_worker_return_count": 0,
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


def _state(
    root: Path,
    sidecar_glob: str,
    rolling_input_path: Path | None = None,
    parent_cycle_root: Path | None = None,
    cycle_artifact_path: Path | None = None,
    task_label: str = TASK,
    acceptance_profile: str | None = None,
    current_durable_state: bool = False,
    stage_a_evidence_root: Path | None = None,
) -> dict[str, Any]:
    path = _state_path(root)
    return (
        _load(path)
        if path.exists()
        else _new_state(
            root,
            sidecar_glob,
            rolling_input_path,
            parent_cycle_root,
            cycle_artifact_path,
            task_label,
            acceptance_profile,
            current_durable_state,
            stage_a_evidence_root,
        )
    )


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


def _semantic_resume_checkpoints_from_probe(
    probe: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], dict[str, str]]:
    """Rebuild hash-bound semantic checkpoints from the accepted worker-request probe.

    A worker return is bound to the exact candidate selected by its probe.  Re-running the
    live semantic selectors during ``complete`` would allow a different current ranking to
    strand that valid return before its deterministic article validation.  The probe already
    records the accepted, provider-verified leaf and global router receipts, so reuse only
    those exact receipts.  This changes no source/evidence/publication gate and grants no
    model output factual or publication authority.
    """
    assignment = dict(probe.get("assignment") or {})
    canonical_input_hash = str((assignment.get("input_binding") or {}).get("canonical_input_hash") or "")
    global_input = dict(assignment.get("compact_global_editor_input") or {})
    leaf_partitions = [
        dict(row) for row in assignment.get("leaf_partitions") or [] if isinstance(row, Mapping)
    ]
    leaf_clusters = [
        dict(row) for row in assignment.get("leaf_clusters") or [] if isinstance(row, Mapping)
    ]
    router_calls = [
        dict(row) for row in assignment.get("router_calls") or [] if isinstance(row, Mapping)
    ]
    global_summary = dict(assignment.get("router_summary") or {})
    story_routing = dict(probe.get("story_routing") or {})
    story_types = {
        str(key): str(value)
        for key, value in dict(story_routing.get("story_type_by_cluster") or {}).items()
    }
    if (
        not canonical_input_hash
        or not global_input
        or not leaf_partitions
        or not leaf_clusters
        or not global_summary
        or global_summary.get("terminal_disposition") != "ACCEPTED"
        or not story_types
    ):
        raise ValueError("probe_semantic_resume_checkpoint_missing_or_unaccepted")

    leaf_checkpoints: dict[str, dict[str, Any]] = {}
    for partition in leaf_partitions:
        partition_id = str(partition.get("partition_id") or "")
        if not partition_id:
            raise ValueError("probe_semantic_resume_checkpoint_partition_missing")
        summaries = [
            row
            for row in router_calls
            if row.get("role_task_id") == "rolling_x_newsroom_leaf_scan"
            and row.get("work_item_id") == partition_id
            and row.get("terminal_disposition") == "ACCEPTED"
        ]
        clusters = [
            row for row in leaf_clusters if str(row.get("partition_id") or "") == partition_id
        ]
        if len(summaries) != 1 or not clusters:
            raise ValueError("probe_semantic_resume_leaf_checkpoint_invalid")
        leaf_checkpoints[partition_id] = {
            "canonical_input_hash": canonical_input_hash,
            "partition_id": partition_id,
            "partition_index": partition.get("partition_index"),
            "headline_ids": list(partition.get("headline_ids") or []),
            "router_summary": summaries[0],
            "output": {"clusters": clusters},
        }

    global_attempts = [
        dict(row) for row in global_summary.get("attempts") or [] if isinstance(row, Mapping)
    ]
    accepted_attempts = [row for row in global_attempts if row.get("disposition") == "accepted"]
    if len(accepted_attempts) != 1:
        raise ValueError("probe_semantic_resume_global_checkpoint_invalid")
    accepted_attempt = accepted_attempts[0]
    ranked_clusters = [
        dict(row) for row in assignment.get("ranked_clusters") or [] if isinstance(row, Mapping)
    ]
    global_output = {
        "decision": assignment.get("decision"),
        "selection_rationale": assignment.get("selection_rationale"),
        "selected_cluster_id": assignment.get("selected_cluster_id"),
        "selected_headline_ids": list(assignment.get("selected_headline_ids") or []),
        "ranked_clusters": ranked_clusters,
        "shortlist_count": len(ranked_clusters),
        "evaluated_leaf_cluster_count": len(leaf_clusters),
        "global_editor_used_compact_leaf_summaries_only": True,
        "attention_used_as_factual_truth": False,
        "router_output_grants_publication_authority": False,
    }
    global_output["global_result_logical_hash"] = _logical_hash(global_output)
    global_checkpoint = {
        "canonical_input_hash": canonical_input_hash,
        "cutoff_time_utc": global_input.get("cutoff_time_utc"),
        "global_input_logical_hash": _logical_hash(global_input),
        "ordered_leaf_cluster_ids": [
            str(row.get("id") or "") for row in global_input.get("leaf_cluster_summaries") or []
        ],
        "global_invocation_id": global_summary.get("logical_invocation_id"),
        "work_item_id": global_summary.get("work_item_id"),
        "role_task_id": global_summary.get("role_task_id"),
        "prompt_template": accepted_attempt.get("prompt_template"),
        "prompt_version": accepted_attempt.get("prompt_version"),
        "governed_input_hash": accepted_attempt.get("governed_input_hash"),
        "terminal_disposition": global_summary.get("terminal_disposition"),
        "selected_model": global_summary.get("selected_model"),
        "router_summary": global_summary,
        "output": global_output,
        "accepted_provider_identity": {
            "gateway": accepted_attempt.get("gateway"),
            "requested_model": accepted_attempt.get("requested_model"),
            "resolved_model": accepted_attempt.get("resolved_model"),
            "provider_invocation_id": accepted_attempt.get("provider_invocation_id"),
            "model_identity_provider_verified": accepted_attempt.get(
                "model_identity_provider_verified"
            ),
        },
        "global_result_logical_hash": global_output["global_result_logical_hash"],
    }
    return leaf_checkpoints, global_checkpoint, story_types


def _validated_probe_viability_checkpoint(value: Mapping[str, Any]) -> dict[str, Any]:
    """Accept only the exact hash-bound viable candidate selected before XHIGH dispatch."""
    checkpoint = dict(value)
    claimed_hash = str(checkpoint.pop("viability_logical_hash") or "")
    if (
        not claimed_hash
        or claimed_hash != _sha(checkpoint)
        or checkpoint.get("status") != "SUCCESS"
        or checkpoint.get("decision") != "SELECT_STORY"
        or not str(checkpoint.get("selected_cluster_id") or "")
        or not isinstance(checkpoint.get("selected_evidence"), Mapping)
    ):
        raise ValueError("probe_viability_checkpoint_invalid")
    return {**checkpoint, "viability_logical_hash": claimed_hash}


def _frontier_row(
    *, number: int, prepared: Mapping[str, Any], result: Mapping[str, Any], path: Path
) -> dict[str, Any]:
    viability = dict(result.get("ranked_viability") or {})
    pool = dict(result.get("publishability_candidate_pool") or {})
    attempted = _attempted_headline_ids(result)
    selected_evidence = dict(viability.get("selected_evidence") or {})
    request_rows = []
    for attempt in viability.get("rank_attempts") or []:
        receipt = dict(attempt.get("evidence_receipt") or {})
        provenance = dict(receipt.get("evidence_acquisition_provenance") or {})
        grounded = dict(provenance.get("grounded_research") or {})
        official = dict((provenance.get("official") or {}).get("provenance") or {})
        request_rows.append({
            "rank": attempt.get("rank"),
            "cluster_id": attempt.get("cluster_id"),
            "headline_ids": list(attempt.get("headline_ids") or []),
            "public_requests": int(grounded.get("public_retrieval_requests") or 0),
            "official_requests": int(official.get("locator_request_count") or 0)
            + int(official.get("official_evidence_get_count") or 0),
            "status": attempt.get("status"),
            "blockers": list(attempt.get("blockers") or []),
            "story_evidence_scope_id": attempt.get("story_evidence_scope_id"),
            "network_requests_performed": int(
                attempt.get("story_evidence_network_requests") or 0
            ),
            "network_reads_avoided": int(
                attempt.get("story_evidence_network_reads_avoided") or 0
            ),
            "delta_acquisition_count": int(
                attempt.get("story_evidence_delta_acquisition_count") or 0
            ),
            "mode_attempts": [
                {
                    "effective_mode": row.get("effective_mode"),
                    "status": row.get("status"),
                    "evidence_acquisition_action": row.get(
                        "evidence_acquisition_action"
                    ),
                    "network_requests_performed": int(
                        row.get("network_requests_performed") or 0
                    ),
                    "network_reads_avoided": int(
                        row.get("network_reads_avoided") or 0
                    ),
                    "delta_evidence_requirements": dict(
                        row.get("delta_evidence_requirements") or {}
                    ),
                }
                for row in attempt.get("mode_attempts") or []
                if isinstance(row, Mapping)
            ],
        })
    story_frontier = dict(result.get("prepared_story_frontier") or {})
    return {
        "frontier": number,
        "prepared_candidate_count": int(prepared.get("prepared_candidate_count") or 0),
        "prepared_headline_ids": list(
            (prepared.get("prepared_frontier") or {}).get("selected_headline_ids") or []
        ),
        "prepared_candidate_logical_hash": prepared.get("prepared_candidate_logical_hash"),
        "attempted_headline_ids": attempted,
        "attempted_distinct_candidate_count": int(viability.get("attempted_candidate_count") or len(attempted)),
        "prepared_headline_identity_count": story_frontier.get(
            "prepared_headline_identity_count"
        ),
        "distinct_story_opportunity_count": story_frontier.get(
            "distinct_story_opportunity_count"
        ),
        "global_editor_shortlist_count": int(
            pool.get("source_ranked_candidate_count")
            or story_frontier.get("evidence_candidate_count")
            or 0
        ),
        "unused_semantic_leaf_reserve_count": int(
            pool.get("reserve_candidate_count") or 0
        ),
        "final_publishability_pool_count": int(
            pool.get("combined_candidate_count") or 0
        ),
        "publishability_pool_status": pool.get("status"),
        "prepared_frontier_pool_reused": pool.get("prepared_frontier_only"),
        "candidate_slots_saved_by_semantic_clustering": story_frontier.get(
            "candidate_slots_saved_by_semantic_clustering"
        ),
        "exact_headline_identity_coverage": story_frontier.get(
            "exact_headline_identity_coverage"
        ),
        "duplicate_update_chain_collapse_matrix": list(
            story_frontier.get("duplicate_update_chain_collapse_matrix") or []
        ),
        "requests_by_distinct_story": request_rows,
        "public_request_total": sum(row["public_requests"] for row in request_rows),
        "official_request_total": sum(row["official_requests"] for row in request_rows),
        "story_scoped_network_request_total": sum(
            row["network_requests_performed"] for row in request_rows
        ),
        "story_scoped_network_reads_avoided": sum(
            row["network_reads_avoided"] for row in request_rows
        ),
        "story_scoped_delta_acquisition_count": sum(
            row["delta_acquisition_count"] for row in request_rows
        ),
        "selected_rank": viability.get("selected_rank"),
        "selected_cluster_id": viability.get("selected_cluster_id"),
        "evidence_status": selected_evidence.get("status"),
        "evidence_qualified": selected_evidence.get("status") == "PASS",
        "ranked_viability_reason_code": viability.get("reason_code"),
        "publishability_pool_exhausted": bool(
            viability.get("publishability_pool_exhausted")
        ),
        "result_classification": result.get("classification"),
        "exact_next_blocker": result.get("exact_next_blocker"),
        "cycle_evidence_path": str(path / "rolling_x_newsroom_cycle_evidence_v1.json"),
        "public_write_performed": bool(result.get("public_write_performed")),
        "publishing_adapter_called": bool(result.get("publishing_adapter_called")),
        "unknown_write_detected": bool(result.get("unknown_write_detected")),
    }


def _persist_candidate_blocker_ledger(
    root: Path, frontiers: list[Mapping[str, Any]]
) -> tuple[Path, dict[str, Any]]:
    """Project the exact terminal candidate walk into one compact audit ledger."""
    frontier_records: list[dict[str, Any]] = []
    candidate_count = 0
    for frontier in frontiers:
        evidence_path = Path(str(frontier.get("cycle_evidence_path") or ""))
        cycle = _load(evidence_path) if evidence_path.is_file() else {}
        walk = dict(cycle.get("candidate_walk") or {})
        viability_by_rank = {
            int(row.get("rank") or 0): row
            for row in (cycle.get("ranked_viability") or {}).get("rank_attempts")
            or []
            if isinstance(row, Mapping)
        }
        candidates = []
        for attempt in walk.get("candidate_attempts") or []:
            if not isinstance(attempt, Mapping):
                continue
            viability_row = viability_by_rank.get(int(attempt.get("rank") or 0), {})
            row = {
                "rank": attempt.get("rank"),
                "cluster_id": attempt.get("cluster_id"),
                "headline_ids": list(
                    attempt.get("headline_ids")
                    or viability_row.get("headline_ids")
                    or []
                ),
                "candidate_title": attempt.get("article_title")
                or attempt.get("candidate_title"),
                "effective_article_mode": attempt.get("effective_article_mode"),
                "evidence_result": attempt.get("evidence_result"),
                "evidence_blockers": list(attempt.get("evidence_blockers") or []),
                "writer_invocation_result": attempt.get("writer_invocation_result"),
                "writer_blockers": list(attempt.get("writer_blockers") or []),
                "deterministic_validation_blockers": list(
                    attempt.get("deterministic_validation_blockers") or []
                ),
                "reader_value_blockers": list(
                    attempt.get("reader_value_blockers") or []
                ),
                "terminal_reason": attempt.get("terminal_reason"),
            }
            candidates.append(row)
            candidate_count += 1
        frontier_records.append(
            {
                "frontier": frontier.get("frontier"),
                "cycle_evidence_path": str(evidence_path),
                "result_classification": frontier.get("result_classification"),
                "exact_next_blocker": frontier.get("exact_next_blocker"),
                "candidate_count": len(candidates),
                "candidates": candidates,
            }
        )
    ledger = {
        "schema_version": "contentops.v1_4_32_candidate_blocker_ledger.v1",
        "frontier_count": len(frontier_records),
        "candidate_count": candidate_count,
        "frontiers": frontier_records,
        "public_write_authority": False,
    }
    ledger["ledger_sha256"] = _sha(ledger)
    path = root / "candidate_blocker_ledger_v1.json"
    _write(path, ledger)
    return path, ledger


def _summary(state: Mapping[str, Any], root: Path | None = None) -> dict[str, Any]:
    evaluated = set(str(value) for value in state.get("evaluated_headline_ids") or [])
    current_headline_ids = {
        str(value) for value in state.get("current_headline_ids") or [] if str(value)
    }
    if not current_headline_ids and root is not None:
        rolling_path = root / "frozen_current_rolling_input_v1.json"
        if rolling_path.exists():
            rolling = _load(rolling_path)
            current_headline_ids = {
                str(row.get("headline_id") or row.get("id"))
                for row in rolling.get("headlines") or []
                if isinstance(row, Mapping)
                and (row.get("headline_id") or row.get("id"))
            }
    full = len(current_headline_ids) or int(
        state.get("full_current_headline_count") or 0
    )
    qualified = list(state.get("qualified_article_records") or [])
    canary_records = list(state.get("mvp_canary_artifact_records") or [])
    frontiers = list(state.get("frontiers") or [])
    completed = len(frontiers)
    remaining_held = (
        len(current_headline_ids.difference(evaluated))
        if current_headline_ids
        else max(0, full - len(evaluated))
    )
    attempted_headline_ids = [
        str(value)
        for row in frontiers
        for value in row.get("attempted_headline_ids") or []
        if str(value)
    ]
    bounded_useful_universe_exhausted = bool(
        completed and remaining_held == 0 and not state.get("pending_frontier")
    )
    if is_mvp_canary_profile(state.get("acceptance_profile")):
        classification = (
            "MVP_CANARY_ARTIFACTS_READY_JIT_PENDING"
            if canary_records
            else "MVP_CANARY_CURRENT_WALK_EXHAUSTED_NO_ACCEPTED_EVIDENCE"
            if completed >= MAX_FRONTIERS and not state.get("pending_frontier")
            else "IN_PROGRESS"
        )
    else:
        classification = (
            "FLOOR_MET"
            if len(qualified) >= MAX_QUALIFIED
            else "DEGRADED_DAILY_OUTPUT_DEFICIT"
            if (
                completed >= MAX_FRONTIERS
                or bounded_useful_universe_exhausted
            ) and not state.get("pending_frontier")
            else "IN_PROGRESS"
        )
    summary = {
        **dict(state),
        "schema_version": SCHEMA,
        "task_label": state.get("task_label") or TASK,
        "classification": classification,
        "current_headline_ids": sorted(current_headline_ids),
        "full_current_headline_count": full,
        "frontier_count": completed,
        "prepared_headline_identity_slot_count": sum(
            int(row.get("prepared_headline_identity_count") or 0)
            for row in frontiers
        ),
        "stage_a_evidence_reuse_hit_count": len(
            state.get("stage_a_evidence_reuse_hits") or []
        ),
        "stage_a_evidence_fallback_call_count": len(
            state.get("stage_a_evidence_fallback_calls") or []
        ),
        "stage_a_evidence_reuse_grants_authority": False,
        "distinct_story_opportunity_count": sum(
            int(row.get("distinct_story_opportunity_count") or 0)
            for row in frontiers
        ),
        "candidate_slots_saved_by_semantic_clustering": sum(
            int(row.get("candidate_slots_saved_by_semantic_clustering") or 0)
            for row in frontiers
        ),
        "global_editor_shortlist_count": sum(
            int(row.get("global_editor_shortlist_count") or 0)
            for row in frontiers
        ),
        "unused_semantic_leaf_reserve_count": sum(
            int(row.get("unused_semantic_leaf_reserve_count") or 0)
            for row in frontiers
        ),
        "final_publishability_pool_count": sum(
            int(row.get("final_publishability_pool_count") or 0)
            for row in frontiers
        ),
        "attempted_distinct_story_count": sum(
            int(row.get("attempted_distinct_candidate_count") or 0)
            for row in frontiers
        ),
        "attempted_headline_identity_count": len(set(attempted_headline_ids)),
        "distinct_candidate_count": len(current_headline_ids.intersection(evaluated))
        if current_headline_ids
        else len(evaluated),
        "remaining_held_identity_count": remaining_held,
        "bounded_useful_universe_exhausted": bounded_useful_universe_exhausted,
        "qualified_count": len(qualified),
        "qualified_derivative_intent_count": len(qualified) * 8,
        "mvp_canary_artifact_count": len(canary_records),
        "mvp_canary_does_not_count_toward_4_32": True,
        "daily_qualified_article_floor": MAX_QUALIFIED,
        "daily_derivative_intent_floor": MAX_QUALIFIED * 8,
        "daily_floor_is_post_launch_only": is_mvp_canary_profile(
            state.get("acceptance_profile")
        ),
        "build_floor_satisfied": len(qualified) >= MAX_QUALIFIED,
        "remaining_build_deficit": max(0, MAX_QUALIFIED - len(qualified)),
        "no_repeat_proof": bool(frontiers)
        and len(attempted_headline_ids) == len(set(attempted_headline_ids)),
        "exact_headline_identity_coverage_all_frontiers": bool(frontiers)
        and all(row.get("exact_headline_identity_coverage") is True for row in frontiers),
        "public_request_total": sum(
            int(row.get("public_request_total") or 0) for row in frontiers
        ),
        "official_request_total": sum(
            int(row.get("official_request_total") or 0) for row in frontiers
        ),
        "story_scoped_network_request_total": sum(
            int(row.get("story_scoped_network_request_total") or 0)
            for row in frontiers
        ),
        "story_scoped_network_reads_avoided": sum(
            int(row.get("story_scoped_network_reads_avoided") or 0)
            for row in frontiers
        ),
        "story_scoped_delta_acquisition_count": sum(
            int(row.get("story_scoped_delta_acquisition_count") or 0)
            for row in frontiers
        ),
        "exact_next_blocker_taxonomy": sorted(
            {
                str(row.get("exact_next_blocker") or "")
                for row in frontiers
                if str(row.get("exact_next_blocker") or "")
            }
        ),
        "safety": {
            "public_writes": int(state.get("public_write_count") or 0),
            "publication_provider_writes": int(state.get("publication_provider_write_count") or 0),
            "unknown_write": int(state.get("unknown_write_count") or 0),
            "production_store_reset": int(state.get("production_store_reset_count") or 0),
            "fifth_automation_created": int(state.get("fifth_automation_created_count") or 0),
        },
    }
    # Do not carry a previously emitted terminal snapshot across a corrected or resumed
    # in-progress state. A fresh canonical production-day record is emitted only at a real
    # terminal boundary below.
    summary.pop("canonical_production_day_record_path", None)
    summary.pop("canonical_production_day", None)
    if root is not None and classification in {
        "FLOOR_MET",
        "DEGRADED_DAILY_OUTPUT_DEFICIT",
    }:
        ledger_path, ledger = _persist_candidate_blocker_ledger(root, frontiers)
        summary["candidate_blocker_ledger_path"] = str(ledger_path)
        summary["candidate_blocker_ledger_sha256"] = ledger["ledger_sha256"]
        production_day = build_production_day_snapshot(
            reference=str(state.get("created_at_utc") or state.get("cutoff_utc")),
            output_root=root,
            published_corpus=(),
            routine_opportunities_used_override=min(MAX_FRONTIERS, completed),
            bounded_useful_universe_exhausted=bounded_useful_universe_exhausted,
        )
        production_day_path = persist_production_day_snapshot(root, production_day)
        summary["canonical_production_day_record_path"] = str(production_day_path)
        summary["canonical_production_day"] = production_day.to_dict()
    return summary


def probe(
    root: Path,
    sidecar_glob: str,
    rolling_input_path: Path | None = None,
    parent_cycle_root: Path | None = None,
    cycle_artifact_path: Path | None = None,
    task_label: str = TASK,
    acceptance_profile: str | None = None,
    current_durable_state: bool = False,
    stage_a_evidence_root: Path | None = None,
) -> dict[str, Any]:
    state = _state(
        root,
        sidecar_glob,
        rolling_input_path,
        parent_cycle_root,
        cycle_artifact_path,
        task_label,
        acceptance_profile,
        current_durable_state,
        stage_a_evidence_root,
    )
    if state.get("pending_frontier"):
        raise ValueError("pending_frontier_must_be_completed_first")
    if len(state.get("frontiers") or []) >= MAX_FRONTIERS:
        raise ValueError("four_frontier_budget_exhausted")
    if len(state.get("qualified_article_records") or []) >= MAX_QUALIFIED:
        raise ValueError("daily_floor_already_met")
    number = len(state.get("frontiers") or []) + 1
    rolling = _load(Path(str(state["rolling_input_path"])))
    stage_binding = dict(state.get("stage_a_evidence_binding") or {})
    ready_frontiers = list(stage_binding.get("ready_frontiers") or [])
    ready_cursor = int(stage_binding.get("ready_frontier_cursor") or 0)
    stage_frontier_reuse: dict[str, Any] = {}
    leaf_checkpoints = None
    global_checkpoint = None
    stage_story_types = None
    if ready_cursor < len(ready_frontiers):
        stage_frontier_reuse = dict(ready_frontiers[ready_cursor])
        prepared = _load(
            Path(str(stage_frontier_reuse["prepared_state_path"]))
        )
        stage_cycle = _load(
            Path(str(stage_frontier_reuse["cycle_evidence_path"]))
        )
        leaf_checkpoints, global_checkpoint, stage_story_types = (
            _semantic_resume_checkpoints_from_probe(stage_cycle)
        )
        stage_binding["ready_frontier_cursor"] = ready_cursor + 1
        state["stage_a_evidence_binding"] = stage_binding
    else:
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
    reuse_root_value = (
        (state.get("stage_a_evidence_binding") or {}).get(
            "stage_a_evidence_root"
        )
    )
    reuse_acquirer = (
        _StageAEvidenceReuseAcquirer(
            stage_a_root=Path(str(reuse_root_value)),
            evaluation_as_of_utc=str(state["cutoff_utc"]),
        )
        if reuse_root_value
        else None
    )
    result = _run_rolling_x_newsroom_cycle(
        run_id=f"v1-current-floor-frontier-{number}-route-probe",
        output_dir=probe_dir,
        cutoff_utc=str(state["cutoff_utc"]),
        rolling_input=rolling,
        prepared_candidate_state=prepared,
        publication_enabled=True,
        operating_mode="KILL_SWITCH",
        destination_readiness_override=_ready(),
        acceptance_profile=state.get("acceptance_profile"),
        published_corpus=_published_corpus_from_state(state),
        evidence_acquirer=reuse_acquirer,
        leaf_checkpoints=leaf_checkpoints,
        global_checkpoint=global_checkpoint,
        story_type_by_cluster=stage_story_types,
    )
    route = dict(result.get("editorial_worker_routing") or {})
    row = _frontier_row(number=number, prepared=prepared, result=result, path=probe_dir)
    row["prepared_state_path"] = str(prepared_path)
    if stage_frontier_reuse:
        row["stage_a_prepared_frontier_reuse"] = stage_frontier_reuse
        row["stage_a_router_checkpoints_reused"] = True
    if reuse_acquirer is not None:
        reuse_manifest = reuse_acquirer.manifest()
        manifest_path = frontier_root / "stage_a_evidence_reuse_v1.json"
        _write(manifest_path, reuse_manifest)
        row["stage_a_evidence_reuse_path"] = str(manifest_path)
        row["stage_a_evidence_reuse_sha256"] = _sha(reuse_manifest)
        row["stage_a_evidence_reuse_hit_count"] = int(
            reuse_manifest.get("reuse_hit_count") or 0
        )
        row["stage_a_evidence_fallback_call_count"] = int(
            reuse_manifest.get("fallback_call_count") or 0
        )
        state["stage_a_evidence_reuse_hits"] = [
            *list(state.get("stage_a_evidence_reuse_hits") or []),
            *list(reuse_manifest.get("reuse_hits") or []),
        ]
        state["stage_a_evidence_fallback_calls"] = [
            *list(state.get("stage_a_evidence_fallback_calls") or []),
            *list(reuse_manifest.get("fallback_calls") or []),
        ]
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
            "viability_checkpoint_path": str(
                probe_dir / "rolling_x_ranked_viability_v1.json"
            ),
        }
        _write(_state_path(root), state)
        return {"status": "XHIGH_REQUIRED", **dict(state["pending_frontier"])}

    state["evaluated_headline_ids"] = sorted(
        set(state.get("evaluated_headline_ids") or []).union(row["attempted_headline_ids"])
    )
    state["frontiers"] = [*list(state.get("frontiers") or []), row]
    state["pending_frontier"] = None
    state = _summary(state, root)
    _write(_state_path(root), state)
    _write(root / "multi_frontier_floor_rehearsal_summary_v1.json", state)
    return {"status": "FRONTIER_COMPLETE_NO_XHIGH", **row, "summary": state}


def probe_locator_recovery(
    root: Path,
    continuity_root: Path,
    sidecar_glob: str,
    task_label: str,
) -> dict[str, Any]:
    """Run one canary-only slice from the prior walk's held current continuity.

    This does not append a fifth 4/32 frontier. It starts a separate single-slice canary state,
    binds the exact prior frozen input/evaluated identities, and lets the unchanged frontier and
    publishability builders choose from held identities using current evidence-path priority.
    """
    if _state_path(root).exists():
        raise ValueError("locator_recovery_root_must_be_new")
    source_summary_path = continuity_root / "multi_frontier_floor_rehearsal_summary_v1.json"
    source_input_path = continuity_root / "frozen_current_rolling_input_v1.json"
    source_summary = _load(source_summary_path)
    source_input = _load(source_input_path)
    if int(source_summary.get("frontier_count") or 0) != MAX_FRONTIERS:
        raise ValueError("locator_recovery_four_frontier_continuity_required")
    if str(source_summary.get("rolling_input_sha256") or "") != _sha(source_input):
        raise ValueError("locator_recovery_rolling_input_binding_invalid")
    if source_summary.get("pending_frontier"):
        raise ValueError("locator_recovery_pending_parent_frontier_forbidden")

    state = _new_state(
        root,
        sidecar_glob,
        rolling_input_path=source_input_path,
        task_label=task_label,
        acceptance_profile=MVP_CANARY_ACCEPTANCE_PROFILE,
    )
    state["evaluated_headline_ids"] = sorted(
        str(value) for value in source_summary.get("evaluated_headline_ids") or []
    )
    state["input_mode"] = "GENUINE_CURRENT_HELD_CONTINUITY_RECOVERY"
    state["locator_recovery_slice"] = True
    state["locator_recovery_does_not_extend_4_32_frontiers"] = True
    state["continuity_binding"] = {
        "source_root": str(continuity_root),
        "source_summary_sha256": _sha(source_summary),
        "source_rolling_input_sha256": _sha(source_input),
        "source_evaluated_headline_ids_sha256": _sha(state["evaluated_headline_ids"]),
        "source_frontier_count": MAX_FRONTIERS,
        "source_attempted_distinct_story_count": int(
            source_summary.get("attempted_distinct_story_count") or 0
        ),
        "source_remaining_held_identity_count": int(
            source_summary.get("remaining_held_identity_count") or 0
        ),
    }
    _write(_state_path(root), state)
    return probe(root, sidecar_glob)


def complete(
    root: Path,
    worker_return_path: Path,
    semantic_review_receipt_path: Path | None = None,
) -> dict[str, Any]:
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
    probe = _load(Path(str(pending["probe_cycle_evidence_path"])))
    leaf_checkpoints, global_checkpoint, story_type_by_cluster = (
        _semantic_resume_checkpoints_from_probe(probe)
    )
    viability_checkpoint_path = Path(
        str(
            pending.get("viability_checkpoint_path")
            or Path(str(pending["probe_cycle_evidence_path"])).parent
            / "rolling_x_ranked_viability_v1.json"
        )
    )
    probe_viability = _validated_probe_viability_checkpoint(_load(viability_checkpoint_path))
    revision_contract_path = pending.get("same_xhigh_worker_revision_contract_path")
    if revision_contract_path:
        probe_viability["same_xhigh_worker_revision_contract"] = _load(
            Path(str(revision_contract_path))
        )
        probe_viability.pop("viability_logical_hash", None)
        probe_viability["viability_logical_hash"] = _sha(probe_viability)
    builder_invoked = False
    editorial_reviewer = None
    if semantic_review_receipt_path is not None:
        semantic_replay = _load(semantic_review_receipt_path)
        semantic_receipt = dict(
            (semantic_replay.get("after") or {}).get("semantic_review_receipt")
            or {}
        )
        expected_prompt_sha256 = str(semantic_receipt.get("prompt_sha256") or "")
        if not expected_prompt_sha256 or semantic_receipt.get("decision") != "PASS":
            raise ValueError("semantic_review_replay_receipt_not_pass")

        def replay_editorial_reviewer(article: Mapping[str, Any]) -> dict[str, Any]:
            from live_contentops.tier1_editorial_quality_v1 import (
                build_llm_editorial_review_prompt,
            )

            prompt = build_llm_editorial_review_prompt(article)
            if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != expected_prompt_sha256:
                raise ValueError("semantic_review_replay_prompt_hash_mismatch")
            return dict(semantic_receipt)

        editorial_reviewer = replay_editorial_reviewer

    def builder(value: Mapping[str, Any]) -> dict[str, Any]:
        nonlocal builder_invoked
        builder_invoked = True
        request = dict(value.get("editorial_worker_request") or {})
        if str(request.get("governed_input_hash") or "") != expected_hash:
            raise GroundedArticleBuilderError("NEXT_NATIVE_XHIGH_WORKER_REQUIRED")
        worker_validation = validate_editorial_worker_return(
            worker_return=receipt,
            expected_governed_input_hash=expected_hash,
        )
        resolved_article = resolve_editorial_worker_article_for_public_lock(
            dict(receipt.get("article") or {}), viability=probe_viability
        )
        return {
            "schema_version": "contentops.rolling_x_grounded_article_media_builder.v1",
            "article": resolved_article,
            "media": {"assets": []},
            "critical_path_telemetry": {
                "article_writer_semantic_calls": 1,
                "article_writer_owner": "FRESH_NATIVE_CODEX_DESKTOP_XHIGH",
            },
            "editorial_worker_receipt": receipt,
            "editorial_worker_validation": worker_validation,
        }

    number = int(pending["frontier"])
    final_dir = root / f"frontier_{number}" / "canonical_zero_write_rehearsal"
    if (final_dir / "rolling_x_newsroom_cycle_evidence_v1.json").exists():
        suffix = 2
        while (
            root
            / f"frontier_{number}"
            / f"canonical_zero_write_rehearsal_attempt_{suffix}"
            / "rolling_x_newsroom_cycle_evidence_v1.json"
        ).exists():
            suffix += 1
        final_dir = root / f"frontier_{number}" / f"canonical_zero_write_rehearsal_attempt_{suffix}"
    _write(final_dir / "rolling_x_ranked_viability_v1.json", probe_viability)
    result = _run_rolling_x_newsroom_cycle(
        run_id=f"v1-current-floor-frontier-{number}-canonical-zero-write",
        output_dir=final_dir,
        cutoff_utc=str(state["cutoff_utc"]),
        rolling_input=rolling,
        prepared_candidate_state=prepared,
        leaf_checkpoints=leaf_checkpoints,
        global_checkpoint=global_checkpoint,
        story_type_by_cluster=story_type_by_cluster,
        article_builder=builder,
        editorial_reviewer=editorial_reviewer,
        publication_enabled=True,
        operating_mode="KILL_SWITCH",
        destination_readiness_override=_ready(),
        acceptance_profile=state.get("acceptance_profile"),
        published_corpus=_published_corpus_from_state(state),
    )
    if not builder_invoked:
        raise ValueError("bound_editorial_worker_return_not_reached_by_reused_probe_selection")
    row = _frontier_row(number=number, prepared=prepared, result=result, path=final_dir)
    row["prepared_state_path"] = pending["prepared_state_path"]
    row["governed_input_hash"] = expected_hash
    row["worker_return_path"] = str(worker_return_path)
    row["worker_return_sha256"] = _sha(receipt)
    row["bounded_revision_count"] = int(receipt.get("bounded_revision_count") or 0)
    state["xhigh_worker_return_count"] = int(
        state.get("xhigh_worker_return_count") or 0
    ) + 1
    state["xhigh_revision_count"] = int(state.get("xhigh_revision_count") or 0) + row[
        "bounded_revision_count"
    ]
    if result.get("exact_next_blocker") == "SAME_XHIGH_WORKER_REVISION_REQUIRED":
        revision_contract = dict(
            result.get("same_xhigh_worker_revision_contract") or {}
        )
        if not revision_contract:
            raise ValueError("same_xhigh_worker_revision_contract_missing")
        contract_path = final_dir / "same_xhigh_worker_revision_contract_v1.json"
        request_path = final_dir / "same_xhigh_worker_revision_request_v1.json"
        _write(contract_path, revision_contract)
        _write(request_path, dict(revision_contract.get("worker_request") or {}))
        state["pending_frontier"] = {
            **pending,
            "worker_request_path": str(request_path),
            "same_xhigh_worker_revision_contract_path": str(contract_path),
            "prior_worker_return_path": str(worker_return_path),
            "prior_worker_return_sha256": _sha(receipt),
            "viability_checkpoint_path": str(
                final_dir / "rolling_x_ranked_viability_v1.json"
            ),
            "last_cycle_evidence_path": row["cycle_evidence_path"],
        }
        _write(_state_path(root), state)
        return {
            "status": "SAME_XHIGH_WORKER_REVISION_REQUIRED",
            "frontier": row,
            "revision_contract_path": str(contract_path),
            "worker_request_path": str(request_path),
        }
    if result.get("exact_next_blocker") == "NEXT_NATIVE_XHIGH_WORKER_REQUIRED":
        route = dict(result.get("editorial_worker_routing") or {})
        if route.get("decision") != "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER":
            raise ValueError("candidate_continuation_worker_route_missing")
        if int(state.get("xhigh_attempt_count") or 0) >= MAX_XHIGH_ATTEMPTS:
            raise ValueError("xhigh_attempt_budget_exhausted")
        next_rank = int((result.get("ranked_viability") or {}).get("selected_rank") or 0)
        request_path = final_dir / (
            f"editorial_worker_request_candidate_{next_rank}_v1.json"
        )
        _write(request_path, dict(route.get("worker_request") or {}))
        state["xhigh_attempt_count"] = int(state.get("xhigh_attempt_count") or 0) + 1
        state["pending_frontier"] = {
            **pending,
            "worker_request_path": str(request_path),
            "governed_input_hash": route.get("governed_input_hash"),
            "viability_checkpoint_path": str(
                final_dir / "rolling_x_ranked_viability_v1.json"
            ),
            "last_cycle_evidence_path": row["cycle_evidence_path"],
            "candidate_continuation_from_rank": row.get("selected_rank"),
        }
        state["pending_frontier"].pop("same_xhigh_worker_revision_contract_path", None)
        _write(_state_path(root), state)
        return {
            "status": "XHIGH_REQUIRED_FOR_CANDIDATE_CONTINUATION",
            "frontier": row,
            "worker_request_path": str(request_path),
        }
    state["evaluated_headline_ids"] = sorted(
        set(state.get("evaluated_headline_ids") or []).union(row["attempted_headline_ids"])
    )
    if (
        result.get("classification") == "PASS_PUBLICATION_PLAN_READY"
        and is_mvp_canary_profile(state.get("acceptance_profile"))
    ):
        release = dict(result.get("release_candidate") or {})
        payloads = dict(release.get("payloads") or {})
        canary_record = {
            "schema_version": "contentops.mvp_canary_zero_write_artifact_record.v1",
            "classification": "MVP_CANARY_ARTIFACTS_READY_JIT_PENDING",
            "acceptance_profile": MVP_CANARY_ACCEPTANCE_PROFILE,
            "frontier": number,
            "selected_rank": row.get("selected_rank"),
            "selected_cluster_id": row.get("selected_cluster_id"),
            "cycle_evidence_path": row.get("cycle_evidence_path"),
            "worker_return_path": str(worker_return_path),
            "worker_return_sha256": row["worker_return_sha256"],
            "derivative_destinations": sorted(payloads),
            "derivative_intent_count": len(payloads),
            "public_write_performed": bool(result.get("public_write_performed")),
            "unknown_write_detected": bool(result.get("unknown_write_detected")),
            "counts_toward_post_launch_4_32": False,
            "owner_public_write_grant_present": False,
            "publication_authority": False,
        }
        row["mvp_canary_artifact_record"] = canary_record
        state["mvp_canary_artifact_records"] = [
            *list(state.get("mvp_canary_artifact_records") or []),
            canary_record,
        ]
    elif result.get("classification") == "PASS_PUBLICATION_PLAN_READY":
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
    state = _summary(state, root)
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
    state = _summary(state, root)
    _write(_state_path(root), state)
    _write(root / "multi_frontier_floor_rehearsal_summary_v1.json", state)
    return {"status": "EMPTY_HARNESS_FRONTIER_REMOVED", "removed": last, "summary": state}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--action",
        choices=(
            "probe", "probe-locator-recovery", "complete", "summary", "repair-empty-last"
        ),
        required=True,
    )
    parser.add_argument("--sidecar-glob", default=DEFAULT_X_SIDECAR_GLOB)
    parser.add_argument("--rolling-input", type=Path)
    parser.add_argument("--parent-cycle-root", type=Path)
    parser.add_argument("--cycle-artifact", type=Path)
    parser.add_argument("--worker-return", type=Path)
    parser.add_argument("--semantic-review-receipt", type=Path)
    parser.add_argument("--task-label", default=TASK)
    parser.add_argument("--acceptance-profile")
    parser.add_argument("--continuity-root", type=Path)
    parser.add_argument("--stage-a-evidence-root", type=Path)
    parser.add_argument(
        "--current-durable-state",
        action="store_true",
        help="Bind read-only production continuity and reconciled canonical published memory.",
    )
    args = parser.parse_args()
    if sum(bool(value) for value in (
        args.rolling_input, args.parent_cycle_root, args.cycle_artifact
    )) > 1:
        raise ValueError("rolling_input_parent_cycle_root_and_cycle_artifact_are_mutually_exclusive")
    root = args.root.resolve()
    if args.action == "probe":
        result = probe(
            root,
            args.sidecar_glob,
            args.rolling_input.resolve(strict=True) if args.rolling_input else None,
            args.parent_cycle_root.resolve(strict=True) if args.parent_cycle_root else None,
            args.cycle_artifact.resolve(strict=True) if args.cycle_artifact else None,
            args.task_label,
            args.acceptance_profile,
            args.current_durable_state,
            (
                args.stage_a_evidence_root.resolve(strict=True)
                if args.stage_a_evidence_root
                else None
            ),
        )
    elif args.action == "probe-locator-recovery":
        if args.continuity_root is None:
            raise ValueError("continuity_root_required")
        if any((args.rolling_input, args.parent_cycle_root, args.cycle_artifact)):
            raise ValueError("locator_recovery_uses_bound_continuity_input_only")
        result = probe_locator_recovery(
            root,
            args.continuity_root.resolve(strict=True),
            args.sidecar_glob,
            args.task_label,
        )
    elif args.action == "complete":
        if args.worker_return is None:
            raise ValueError("worker_return_required")
        result = complete(
            root,
            args.worker_return.resolve(strict=True),
            (
                args.semantic_review_receipt.resolve(strict=True)
                if args.semantic_review_receipt is not None
                else None
            ),
        )
    elif args.action == "repair-empty-last":
        result = repair_empty_last_frontier(root)
    else:
        result = _summary(_load(_state_path(root)), root)
        _write(_state_path(root), result)
        _write(root / "multi_frontier_floor_rehearsal_summary_v1.json", result)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
