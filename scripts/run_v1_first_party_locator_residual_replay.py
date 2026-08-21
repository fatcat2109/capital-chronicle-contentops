"""Replay the committed 17-story residual matrix through the canonical official loader.

This is a zero-write evidence harness.  It does not search for new public-secondary sources,
qualify an article, call an editorial worker, or grant any factual/publication authority.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.official_primary_evidence_loader_v1 import (
    BoundedOfficialPrimaryEvidenceLoader,
)
from live_contentops.official_primary_source_locator_v1 import (
    LOCATOR_SURFACES,
    routed_official_locator_surface_ids,
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("residual_replay_json_object_required")
    return value


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _cluster_for_row(parent_root: Path, row: Mapping[str, Any]) -> dict[str, Any]:
    frontier = int(row.get("frontier") or 0)
    assignment_path = (
        parent_root
        / "genuine_current_production_day_rehearsal"
        / f"frontier_{frontier}"
        / "route_probe"
        / "rolling_x_assignment_v1.json"
    )
    assignment = _read(assignment_path)
    expected = [str(value) for value in row.get("headline_ids") or []]
    for cluster in assignment.get("ranked_clusters") or []:
        if not isinstance(cluster, Mapping):
            continue
        if [str(value) for value in cluster.get("headline_ids") or []] == expected:
            return dict(cluster)
    raise ValueError("residual_replay_cluster_binding_missing")


def replay(*, parent_root: Path, closure_path: Path) -> dict[str, Any]:
    closure = _read(closure_path)
    matrix = (
        (closure.get("forensic_second_phase") or {})
        .get("residual_source_reachability_matrix")
        or []
    )
    if len(matrix) != 17:
        raise ValueError("residual_replay_requires_exactly_17_committed_stories")
    frozen = _read(
        parent_root
        / "genuine_current_production_day_rehearsal"
        / "frozen_current_rolling_input_v1.json"
    )
    evaluation_as_of_utc = str(frozen.get("cutoff_time_utc") or "")
    surface_by_id = {
        str(row["surface_id"]): dict(row) for row in LOCATOR_SURFACES
    }
    results: list[dict[str, Any]] = []
    for prior in matrix:
        if not isinstance(prior, Mapping):
            raise ValueError("residual_replay_row_invalid")
        cluster = _cluster_for_row(parent_root, prior)
        story = str(prior.get("story") or "")
        story_context = {**cluster, "leaf_summaries": [story]}
        surface_ids = routed_official_locator_surface_ids(
            {"story_context": story_context}
        )
        common = {
            "frontier": int(prior.get("frontier") or 0),
            "rank": int(prior.get("rank") or 0),
            "cluster_id": str(cluster.get("cluster_id") or ""),
            "headline_ids": [str(value) for value in prior.get("headline_ids") or []],
            "story": story,
            "prior_classification": [
                str(value) for value in prior.get("forensic_classification") or []
            ],
            "prior_exact_blockers": [
                str(value) for value in prior.get("exact_blockers") or []
            ],
        }
        if not surface_ids:
            results.append({
                **common,
                "locator_surface_selected": None,
                "locator_requests": 0,
                "exact_candidate_url_discovered": None,
                "evidence_get_count": 0,
                "accepted_documents": [],
                "capabilities_verified": [],
                "final_evidence_disposition": (
                    "NO_EXACT_FIRST_PARTY_ROUTE_RETAIN_PRIOR_ABSTENTION"
                ),
                "public_secondary_reopened": False,
            })
            continue
        surface_id = surface_ids[0]
        family = str(surface_by_id[surface_id]["family"])
        request = {
            "cluster_id": common["cluster_id"],
            "headline_ids": common["headline_ids"],
            "source_adapter_families": [family],
            "required_evidence_capabilities": [],
            "evaluation_as_of_utc": evaluation_as_of_utc,
            "story_context": story_context,
        }
        request["request_logical_hash"] = _logical_hash(request)
        packet = BoundedOfficialPrimaryEvidenceLoader(
            evaluation_as_of_utc=evaluation_as_of_utc
        )(request)
        provenance = dict(packet.get("provenance") or {})
        locator = dict(provenance.get("locator") or {})
        documents = [
            {
                "document_id": str(document.get("document_id") or ""),
                "source_url": str(document.get("source_url") or ""),
                "canonical_content_sha256": str(
                    document.get("canonical_content_sha256") or ""
                ),
                "published_at_utc": document.get("published_at_utc"),
                "public_claim_allowed": bool(document.get("public_claim_allowed")),
            }
            for document in packet.get("official_source_documents") or []
            if isinstance(document, Mapping)
        ]
        passed = packet.get("status") == "PASS" and bool(documents)
        results.append({
            **common,
            "locator_surface_selected": surface_id,
            "source_adapter_family": family,
            "locator_requests": int(provenance.get("locator_request_count") or 0),
            "locator_query_logical_hash": locator.get("locator_query_logical_hash"),
            "exact_candidate_url_discovered": locator.get("candidate_official_url"),
            "evidence_get_count": int(provenance.get("official_evidence_get_count") or 0),
            "accepted_documents": documents,
            "capabilities_verified": list(
                packet.get("provided_evidence_capabilities") or []
            ),
            "final_evidence_disposition": (
                "OFFICIAL_BYTES_VERIFIED_FOR_EXISTING_EVIDENCE_GATES"
                if passed
                else "FIRST_PARTY_REPLAY_BLOCKED"
            ),
            "blockers": list(packet.get("blockers") or []),
            "public_secondary_reopened": False,
            "locator_grants_factual_numeric_or_publication_authority": False,
        })
    selected = [row for row in results if row["locator_surface_selected"]]
    verified = [
        row
        for row in results
        if row["final_evidence_disposition"]
        == "OFFICIAL_BYTES_VERIFIED_FOR_EXISTING_EVIDENCE_GATES"
    ]
    return {
        "schema_version": "contentops.v1_first_party_locator_residual_replay.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evaluation_as_of_utc": evaluation_as_of_utc,
        "committed_parent_closure": _portable_path(closure_path),
        "committed_residual_story_count": len(results),
        "exact_first_party_surface_story_count": len(selected),
        "official_bytes_verified_story_count": len(verified),
        "locator_requests": sum(int(row["locator_requests"]) for row in results),
        "evidence_get_count": sum(int(row["evidence_get_count"]) for row in results),
        "network_request_count": sum(
            int(row["locator_requests"]) + int(row["evidence_get_count"])
            for row in results
        ),
        "request_budget_changed": False,
        "public_secondary_reopened": False,
        "public_writes": 0,
        "provider_writes": 0,
        "unknown_write": 0,
        "locator_output_grants_authority": False,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-root", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(
        parent_root=args.parent_root.resolve(strict=True),
        closure_path=args.closure.resolve(strict=True),
    )
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        key: value for key, value in result.items() if key != "results"
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
