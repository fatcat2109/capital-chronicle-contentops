"""Read-only audit of exact Capital Chronicle publication surfaces against the failed 40.

The script reads committed bytes through ``git show`` so the result is tied to one upstream
commit even when the operator's checkout is on another clean commit.  It performs no checkout,
fetch, database query, network content retrieval, or upstream write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


PUBLICATION_PACKET = (
    "docs/research/publication_evidence/current/"
    "CapitalChroniclePublicationEvidencePacketV1.json"
)
NEWSROOM_POOL = (
    "docs/research/newsroom_candidate_pool_v1/"
    "CapitalChronicleNewsroomCandidatePoolV1.json"
)
SOURCE_INVENTORY = "config/data_foundation/NEWSROOM_CANDIDATE_SOURCES_V1.json"
PUBLICATION_SCHEMA = (
    "schemas/publication/CapitalChroniclePublicationEvidencePacketV1.schema.json"
)
CANDIDATE_SCHEMA = (
    "schemas/publication/CapitalChronicleNewsroomCandidatePoolV1.schema.json"
)


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
    ).stdout


def _show(repo: Path, commit: str, path: str) -> tuple[dict[str, Any], str]:
    payload = _git(repo, "show", f"{commit}:{path}")
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"upstream_object_required:{path}")
    return value, hashlib.sha256(payload).hexdigest()


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def build_audit(
    *,
    upstream_repo: Path,
    upstream_commit: str,
    failure_matrix: Mapping[str, Any],
    audit_as_of_utc: str,
) -> dict[str, Any]:
    resolved_commit = _git(upstream_repo, "rev-parse", f"{upstream_commit}^{{commit}}").decode().strip()
    if resolved_commit != upstream_commit:
        raise ValueError("upstream_commit_resolution_mismatch")
    status_before = _git(upstream_repo, "status", "--porcelain=v1").decode("utf-8")
    head_before = _git(upstream_repo, "rev-parse", "HEAD").decode().strip()

    inventory, inventory_sha = _show(upstream_repo, upstream_commit, SOURCE_INVENTORY)
    packet, packet_sha = _show(upstream_repo, upstream_commit, PUBLICATION_PACKET)
    pool, pool_sha = _show(upstream_repo, upstream_commit, NEWSROOM_POOL)
    publication_schema, publication_schema_sha = _show(
        upstream_repo, upstream_commit, PUBLICATION_SCHEMA
    )
    candidate_schema, candidate_schema_sha = _show(
        upstream_repo, upstream_commit, CANDIDATE_SCHEMA
    )

    stories = [
        dict(row) for row in (failure_matrix.get("stories") or [])
        if isinstance(row, Mapping)
    ]
    if len(stories) != 40:
        raise ValueError(f"exact_failed_story_count_invalid:{len(stories)}")
    story_type_counts = Counter(
        str(row.get("story_type") or "general_public_event") for row in stories
    )
    families = {
        str(row.get("family_id")): dict(row)
        for row in (inventory.get("source_families") or [])
        if isinstance(row, Mapping) and row.get("family_id")
    }

    def coverage(family_id: str) -> dict[str, Any]:
        family = families[family_id]
        supported_types = {
            str(value) for value in (family.get("story_families") or [])
        }
        counts = {
            story_type: count
            for story_type, count in sorted(story_type_counts.items())
            if story_type in supported_types
        }
        return {
            "family_id": family_id,
            "upstream_status": family.get("status"),
            "family_compatible_failed_story_count": sum(counts.values()),
            "family_compatible_story_type_counts": counts,
            "blocker_codes": list(family.get("blocker_codes") or []),
            "authority_granted_by_family_compatibility": False,
        }

    packet_binding = packet.get("rolling_x_story_binding")
    packet_binding = packet_binding if isinstance(packet_binding, Mapping) else {}
    failed_cluster_ids = {str(row.get("cluster_id") or "") for row in stories}
    failed_headline_sets = {
        tuple(str(value) for value in (row.get("headline_ids") or [])) for row in stories
    }
    binding_match = bool(
        packet_binding
        and str(packet_binding.get("cluster_id") or "") in failed_cluster_ids
        and tuple(str(value) for value in (packet_binding.get("headline_ids") or []))
        in failed_headline_sets
    )
    as_of = _parse_utc(audit_as_of_utc)
    packet_as_of = _parse_utc(str(packet.get("as_of_utc")))
    packet_age_hours = round((as_of - packet_as_of).total_seconds() / 3600, 3)
    family_coverage = [
        coverage(family_id)
        for family_id in (
            "story_scoped_publication_evidence_v1",
            "governed_point_in_time_handoff_v1",
            "official_catalyst_sidecars_hb8",
            "headline_and_x_sidecars",
            "macro_state_phase_b",
            "weather_energy_sanctions_trade_calendar",
        )
    ]
    supported = next(
        row for row in family_coverage
        if row["family_id"] == "story_scoped_publication_evidence_v1"
    )

    status_after = _git(upstream_repo, "status", "--porcelain=v1").decode("utf-8")
    head_after = _git(upstream_repo, "rev-parse", "HEAD").decode().strip()
    if status_after != status_before or head_after != head_before:
        raise RuntimeError("upstream_checkout_changed_during_read_only_audit")

    audit = {
        "schema_version": "contentops.v1_cc_publication_interop_audit.v1",
        "audit_as_of_utc": audit_as_of_utc,
        "upstream_authority": {
            "repository": "fatcat2109/Headline-Raw-data-json",
            "commit": upstream_commit,
            "exact_commit_object_verified": True,
            "local_checkout_head_before_and_after": head_before,
            "local_checkout_status_before_and_after": (
                "CLEAN" if not status_before else "PRESERVED_DIRTY"
            ),
            "checkout_or_branch_mutation_performed": False,
            "capital_chronicle_file_write_performed": False,
            "database_opened": False,
            "provider_or_model_calls": 0,
        },
        "committed_surface_identities": {
            SOURCE_INVENTORY: inventory_sha,
            PUBLICATION_PACKET: packet_sha,
            NEWSROOM_POOL: pool_sha,
            PUBLICATION_SCHEMA: publication_schema_sha,
            CANDIDATE_SCHEMA: candidate_schema_sha,
        },
        "failed_day_universe": {
            "failed_story_count": 40,
            "held_identity_count": int(
                failure_matrix.get("held_identity_universe_count") or 0
            ),
            "story_type_counts": dict(sorted(story_type_counts.items())),
            "held_story_family_classification": (
                "NOT_AVAILABLE_IN_COMMITTED_FAILED_DAY_ARTIFACTS"
            ),
            "representative_held_sample_count": int(
                failure_matrix.get("representative_held_sample_count") or 0
            ),
        },
        "current_exact_surfaces": {
            "publication_packet": {
                "schema_version": packet.get("schema_version"),
                "packet_id": packet.get("packet_id"),
                "packet_status_at_generation": packet.get("status"),
                "packet_as_of_utc": packet.get("as_of_utc"),
                "packet_age_hours_at_audit": packet_age_hours,
                "assignment_story_type": (packet.get("assignment") or {}).get(
                    "story_type"
                ),
                "assignment_duplicate_key": (packet.get("assignment") or {}).get(
                    "duplicate_key"
                ),
                "rolling_x_story_binding_present": bool(packet_binding),
                "matches_any_failed_story_binding": binding_match,
                "numeric_claim_count": len(packet.get("numeric_claims") or []),
                "official_source_document_count": len(
                    packet.get("official_source_documents") or []
                ),
            },
            "candidate_pool": {
                "schema_version": pool.get("schema_version"),
                "producer_version": pool.get("producer_version"),
                "generated_at_utc": pool.get("generated_at_utc"),
                "counts": dict(pool.get("counts") or {}),
                "status": pool.get("status"),
                "eligible_candidate_ids": [
                    row.get("candidate_id")
                    for row in (pool.get("eligible_candidates") or [])
                    if isinstance(row, Mapping)
                ],
            },
            "publication_schema_required_numeric_claim_minimum": (
                (publication_schema.get("properties") or {})
                .get("numeric_claims", {})
                .get("minItems")
            ),
            "candidate_schema_exact_source_family": (
                (candidate_schema.get("$defs") or {})
                .get("candidate", {})
                .get("properties", {})
                .get("source_family", {})
                .get("enum", [])
            ),
        },
        "coverage": {
            "exact_current_packet_matches_failed_40": 1 if binding_match else 0,
            "exact_current_packet_matches_held_453": 0,
            "story_scoped_supported_family_compatible_failed_stories": supported[
                "family_compatible_failed_story_count"
            ],
            "story_scoped_supported_family_compatible_fraction": (
                f"{supported['family_compatible_failed_story_count']}/40"
            ),
            "family_compatibility_is_not_packet_availability_or_authority": True,
            "family_coverage": family_coverage,
        },
        "reusable_existing_components": [
            "Capital Chronicle publication_evidence_fabric_v1.build_publication_packet",
            "Capital Chronicle newsroom_candidate_pool_v1.build_candidate_pool",
            "Capital Chronicle NEWSROOM_CANDIDATE_SOURCES_V1 source-family inventory",
            "ContentOps capital_chronicle_data_catalog_v1 governed-surface discovery",
            "ContentOps cc_evidence_bridge_v2 exact compatible packet projection",
            "ContentOps cc_publication_authority_v1 exact story/use resolver",
            "ContentOps rolling_x_targeted_evidence_adapter_v1 freshness and evidence gate",
        ],
        "missing_interop_requirements": [
            {
                "requirement": "exact_rolling_x_story_binding",
                "fields": ["cluster_id", "headline_ids", "request_logical_hash"],
                "why": "The committed packet has no rolling_x_story_binding, so family similarity cannot become story authority.",
            },
            {
                "requirement": "fresh_per_story_publication_packet",
                "fields": [
                    "generated_at_utc", "as_of_utc", "events[].event_time_utc",
                    "official_source_documents[].published_at_utc",
                    "numeric_claims[].known_at_utc", "numeric_claims[].observation_time_utc",
                ],
                "why": "The only committed packet is July-dated and does not provide current failed-day readiness.",
            },
            {
                "requirement": "exact_source_and_claim_provenance",
                "fields": [
                    "official_source_documents[].source_url",
                    "official_source_documents[].raw_sha256",
                    "numeric_claims[].source_url", "numeric_claims[].metric",
                    "numeric_claims[].value", "numeric_claims[].unit", "citation_map",
                ],
                "why": "ContentOps must reuse exact bytes and mappings; it may not synthesize numeric or citation authority.",
            },
            {
                "requirement": "exact_consumer_and_use_permission",
                "fields": [
                    "consumer_class", "story_authority.decision",
                    "public_claim_permissions.decision",
                    "public_claim_permissions.reporting_allowed",
                    "public_claim_permissions.llm_numeric_authority",
                ],
                "why": "Authority must remain story-scoped with no global DQR override and no model numeric authority.",
            },
            {
                "requirement": "capability_mapping_for_contentops",
                "fields": ["provided_evidence_capabilities"],
                "why": "A packet should state which unchanged ContentOps evidence capabilities its exact documents satisfy; the adapter remains final authority.",
            },
        ],
        "expected_utility": {
            "current_realized_failed_story_authority_coverage": "0/40",
            "current_realized_held_authority_coverage": "0/453",
            "maximum_observed_family_compatible_failed_story_ceiling": (
                f"{supported['family_compatible_failed_story_count']}/40"
            ),
            "expected_request_or_model_savings": (
                "UNMEASURED_UNTIL_FRESH_EXACT_STORY_BOUND_PACKETS_EXIST_AND_A_REPLAY_IS_RUN"
            ),
            "ordinary_public_evidence_path_remains_available_when_packet_absent": True,
        },
        "authority": {
            "family_compatibility_grants_authority": False,
            "context_grants_authority": False,
            "contentops_mutated_capital_chronicle": False,
            "publication_or_public_write_authority_granted": False,
        },
    }
    audit["audit_sha256"] = hashlib.sha256(
        json.dumps(audit, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return audit


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-repo", type=Path, required=True)
    parser.add_argument("--upstream-commit", required=True)
    parser.add_argument("--failure-matrix", type=Path, required=True)
    parser.add_argument("--audit-as-of-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    failure_matrix = json.loads(args.failure_matrix.read_text(encoding="utf-8"))
    audit = build_audit(
        upstream_repo=args.upstream_repo.resolve(),
        upstream_commit=args.upstream_commit,
        failure_matrix=failure_matrix,
        audit_as_of_utc=args.audit_as_of_utc,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "audit_sha256": audit["audit_sha256"],
        "current_realized_failed_story_authority_coverage": audit[
            "expected_utility"
        ]["current_realized_failed_story_authority_coverage"],
        "family_compatible_failed_story_ceiling": audit["expected_utility"][
            "maximum_observed_family_compatible_failed_story_ceiling"
        ],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
