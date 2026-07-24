"""Compatibility projection of the governed continuous cross-domain shadow."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from live_contentops.cross_domain_continuous_shadow_v1 import (
    FIVE_WINDOWS,
    _build_dbh2_candidate as _context_candidate,
    build_continuous_shadow_operation,
)
from live_contentops.universal_news_candidate_fabric_v2 import logical_hash


CANARY_SCHEMA = "contentops.cross_domain_assignment_canary.v1"
CANARY_CUTOFF = "2026-07-14T00:00:00Z"
CANARY_SCHEDULE_DATE = "2026-07-14"
V1_POOL_PRODUCER_COMMIT = "8c63faca0603f81bebfbb68380a0dc4ad51ab87d"


def build_real_cross_domain_canary(
    *,
    upstream_root: Path,
    observed_head: str,
) -> dict[str, Any]:
    """Return the accepted static-canary shape from the governed replay.

    The V1-facing canary no longer constructs authority-bearing source-family
    records. It selects the matching cutoff from the receipt-bound continuous
    operation and therefore preserves compatibility without reopening the
    caller-authority gap.
    """

    repo_root = Path(__file__).parents[1]
    operation = build_continuous_shadow_operation(
        repo_root=repo_root,
        upstream_root=upstream_root,
        observed_upstream_head=observed_head,
    )
    pool = next(
        row
        for row in operation["multi_cutoff_candidate_pools"]
        if row["cutoff_time_utc"] == CANARY_CUTOFF
    )
    checkpoint_assignment = next(
        row
        for row in operation["five_window_shadow_decisions"]
        if row["cutoff_utc"] == CANARY_CUTOFF
    )
    assignment = {
        "schema_version": "contentops.universal_newsroom_assignment_schedule.v2",
        "schedule_date": CANARY_SCHEDULE_DATE,
        "candidate_pool_id": pool["pool_id"],
        "windows": list(FIVE_WINDOWS),
        "decisions": checkpoint_assignment["decisions"],
        "summary": {
            "window_count": len(checkpoint_assignment["decisions"]),
            "internal_assignment_count": checkpoint_assignment[
                "internal_assignment_count"
            ],
            "publication_count": checkpoint_assignment["publication_count"],
            "public_write_count": checkpoint_assignment["public_write_count"],
        },
        "publication_authority": False,
        "public_write_performed": False,
    }
    assignment["logical_hash"] = logical_hash(assignment)
    claim_counts: dict[str, int] = {}
    for candidate in pool["candidates"]:
        for claim in candidate["claims"]:
            claim_type = str(claim["claim_type"])
            claim_counts[claim_type] = claim_counts.get(claim_type, 0) + 1
    result: dict[str, Any] = {
        "schema_version": CANARY_SCHEMA,
        "generated_at_utc": CANARY_CUTOFF,
        "upstream_observed_head": observed_head,
        "pool": pool,
        "assignment": assignment,
        "selected_real_categories": [
            "numeric_macro_release",
            "official_regulatory_document",
            "corporate_filing",
            "sanctions_entity_context",
            "central_bank_official_document",
            "physical_event",
        ],
        "source_target_authority": {
            str(record["source_family_id"]): {
                "authority_class": record["authority_class"],
                "permission_ceiling": record["permission_ceiling"],
            }
            for record in pool["source_family_registry"]["records"]
        },
        "candidate_counts": {
            "total": pool["counts"]["candidates"],
            "reporting_eligible": pool["counts"]["reporting_eligible"],
            "held_context_only": pool["counts"]["held"],
            "rejected_contract_invalid": pool["counts"]["rejected"],
        },
        "claim_counts_by_type": dict(sorted(claim_counts.items())),
        "publication_authority": False,
        "public_write_performed": False,
        "upstream_write_performed": False,
        "browser_or_provider_call_performed": False,
        "classification": "PASS_REAL_CROSS_DOMAIN_CANARY_NO_PUBLICATION",
        "compatibility_projection": (
            "GOVERNED_CONTINUOUS_SHADOW_AT_2026_07_14_CUTOFF"
        ),
    }
    result["logical_hash"] = logical_hash(result)
    return result
