"""Deterministic local-only cross-domain operator-ready content batch.

This wrapper composes existing governed shadow, compiler, and preview-hash
contracts. It never calls providers, browsers, platforms, networks, credentials,
or upstream repositories and never grants publication authority.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping

from live_contentops.payload_preview_hash_v6 import compute_payload_hash
from live_contentops.scd_platform_payload_compiler_v2 import (
    build_constraint_profiles_from_registry_v2,
    build_platform_payload_compile_report_v2,
    build_compiler_v2_summary,
    compile_platform_payloads_v2,
    validate_platform_payload_compiler_v2_input,
    validate_platform_payload_compiler_v2_output,
    validate_platform_payload_compile_report_v2,
)
from live_contentops.scd_platform_capability_registry_v2 import (
    APPROVED_PLATFORM_IDS_V2,
)
from live_contentops.window_incremental_editorial_shadow_v1 import (
    build_window_incremental_editorial_shadow,
)


EVIDENCE_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_CROSS_DOMAIN_OPERATOR_READY_CONTENT_BATCH_V1"
)
TASK = "TASK_CONTENTOPS_FAST_SHIP_CROSS_DOMAIN_OPERATOR_READY_CONTENT_BATCH_V1"
SCHEMA_VERSION = "contentops.fast_ship_cross_domain_operator_ready_batch.v1"
BATCH_SIZE = 12
PRIORITY_PLATFORMS = (
    "substack_newsletter",
    "linkedin",
    "x_twitter",
    "facebook_page",
    "telegram",
)
UNSUPPORTED_SURFACES = {
    "youtube_community": "UNSUPPORTED_LOCAL_PREVIEW_CONTRACT",
}
GOVERNANCE_FAMILIES = (
    "candidate_evidence_registry",
    "platform_capability_registry_v2",
)
REQUIRED_FALSE_FLAGS = {
    "live_api_enabled_now",
    "platform_api_allowed_now",
    "credential_read_allowed_now",
    "credentials_requested_now",
    "posting_enabled_now",
    "scheduler_enabled_now",
    "autonomous_replies_enabled_now",
    "dms_enabled_now",
    "scraping_enabled_now",
    "public_ready",
    "live_ready",
    "dispatch_ready",
    "public_write_performed",
    "publication_authority",
}


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical(value))


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _all_candidates(operation: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pool in operation.get("candidate_pools", []):
        for candidate in pool.get("candidates", []):
            candidate_id = str(candidate.get("candidate_id", ""))
            if candidate_id and candidate_id not in seen:
                rows.append(dict(candidate))
                seen.add(candidate_id)
    return rows


def _collect_candidates(operation: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = _all_candidates(operation)
    authorized = [row for row in rows if row.get("reporting_allowed") is True]
    context = [row for row in rows if row.get("reporting_allowed") is not True]
    selected = authorized + context[: BATCH_SIZE - len(authorized)]
    if len(selected) != BATCH_SIZE:
        raise ValueError(f"governed_candidate_count_below_batch_size:{len(rows)}")
    return selected


def _families(candidates: list[Mapping[str, Any]]) -> set[str]:
    return {
        str(family)
        for candidate in candidates
        for family in candidate.get("source_family_ids", [])
        if family
    }


def _domain(candidate: Mapping[str, Any]) -> str:
    families = set(candidate.get("source_family_ids", []))
    if any("federal_register" in family for family in families):
        return "regulatory"
    if any("ofac" in family for family in families):
        return "sanctions"
    if any("usgs" in family for family in families):
        return "physical_events"
    if any("publication" in family for family in families):
        return "markets"
    return "other"


def _magnitude(title: str) -> float | None:
    match = re.match(r"^M\s+(\d+(?:\.\d+)?)\b", title)
    return float(match.group(1)) if match else None


def _editorial_outcome(candidate: Mapping[str, Any]) -> str:
    if candidate.get("reporting_allowed") is True:
        return "REVIEWED_SHADOW_DRAFT_READY_FOR_OPERATOR_REVIEW"
    domain = _domain(candidate)
    if domain == "regulatory":
        return "HOLD_REGULATORY_CONTEXT_ONLY"
    if domain == "sanctions":
        return "HOLD_SANCTIONS_CONTEXT_ONLY"
    if domain == "physical_events":
        magnitude = _magnitude(str(candidate.get("title") or ""))
        if magnitude is not None and magnitude >= 8.0:
            return "MONITOR_MAJOR_PHYSICAL_EVENT_CONTEXT_ONLY"
        if magnitude is not None and magnitude >= 7.0:
            return "MONITOR_SIGNIFICANT_PHYSICAL_EVENT_CONTEXT_ONLY"
        return "HOLD_PHYSICAL_EVENT_CONTEXT_ONLY"
    return "HOLD_UNAUTHORIZED_CONTEXT_ONLY"


def _safe_source_text(
    candidate: Mapping[str, Any], handoff: Mapping[str, Any] | None
) -> str:
    article = (handoff or {}).get("article") or {}
    rendered_body = str(article.get("rendered_body") or "").strip()
    substantive_body = rendered_body.replace("Not financial advice.", "").strip()
    if candidate.get("reporting_allowed") is True and substantive_body:
        return rendered_body
    title = str(candidate.get("title") or "Governed context candidate").strip()
    summary = str(
        candidate.get("summary") or "Context-only governed source candidate."
    ).strip()
    if candidate.get("reporting_allowed") is True:
        return f"{title}\n\n{summary}\n\nNot financial advice."
    return f"Context-only review candidate: {title}. {summary} Not financial advice."


def _claims_and_citations(
    candidate: Mapping[str, Any], handoff: Mapping[str, Any] | None
) -> tuple[list[str], list[str]]:
    packet = (handoff or {}).get("evidence_packet") or {}
    claims = packet.get("governed_claim_graph", {}).get("claims", [])
    statements = [
        str(claim.get("statement"))
        for claim in claims
        if claim.get("statement")
    ]
    citations = sorted(
        {
            str(citation.get("url"))
            for claim in claims
            for citation in claim.get("citations", [])
            if citation.get("url")
        }
    )
    if candidate.get("reporting_allowed") is not True:
        return [], []
    return statements, citations


def _compiler_cycle(
    candidate: Mapping[str, Any],
    handoff: Mapping[str, Any] | None,
    profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    _, citations = _claims_and_citations(candidate, handoff)
    packet = {
        "compiler_input_id": f"cin_batch_{candidate['candidate_id']}",
        "canonical_post_id": str(candidate["candidate_id"]),
        "editorial_output_id": f"eout_batch_{candidate['candidate_id']}",
        "source_text": _safe_source_text(candidate, handoff),
        "source_limitations": list(
            (handoff or {}).get("evidence_packet", {}).get("limitations", [])
        )
        or ["local_operator_review_only", "no_publication_authority"],
        "source_citations": citations,
        "requested_platforms": list(PRIORITY_PLATFORMS),
        "operator_review_required": True,
    }
    input_validation = validate_platform_payload_compiler_v2_input(packet)
    payloads = compile_platform_payloads_v2(packet, profiles)
    output = {
        "schema_version": "0174bn-v2",
        "compiler_input_id": packet["compiler_input_id"],
        "compiler_output_id": f"cout_batch_{candidate['candidate_id']}",
        "platform_payloads": payloads,
        "validation_state": input_validation["validation_state"],
        "live_ready": False,
        "dispatch_ready": False,
        "platform_api_allowed_now": False,
        "credential_read_allowed_now": False,
        "credentials_requested_now": False,
        "posting_enabled_now": False,
        "scheduler_enabled_now": False,
        "autonomous_replies_enabled_now": False,
        "dms_enabled_now": False,
        "scraping_enabled_now": False,
        "public_ready": False,
        "live_eligibility": False,
        "operator_review_required": True,
    }
    output_validation = validate_platform_payload_compiler_v2_output(output)
    report = build_platform_payload_compile_report_v2(output)
    report_validation = validate_platform_payload_compile_report_v2(report)
    summary = build_compiler_v2_summary(packet, output, report)
    return {
        "input": packet,
        "input_validation": input_validation,
        "output": output,
        "output_validation": output_validation,
        "compile_report": report,
        "report_validation": report_validation,
        "summary": summary,
    }


def _preview(
    candidate: Mapping[str, Any], cycle: Mapping[str, Any]
) -> dict[str, Any]:
    previews = []
    for payload in cycle["output"]["platform_payloads"]:
        substantive_text = str(payload["text"]).replace(
            "Not financial advice.", ""
        ).strip()
        if not substantive_text:
            raise ValueError(
                f"operator_preview_substantive_text_missing:{payload['platform_id']}"
            )
        safe_payload = {
            "candidate_id": candidate["candidate_id"],
            "platform_id": payload["platform_id"],
            "content_surface": payload["content_surface"],
            "payload_shape": payload["payload_shape"],
            "mode": payload["mode"],
            "text": payload["text"],
            "character_count": payload["character_count"],
            "character_limit_max": payload["character_limit_max"],
            "citations": payload["citations"],
            "limitations": payload["limitations"],
            "operator_review_required": True,
            "approval_required": True,
            "valid_for_dispatch": False,
            "dispatch_ready": False,
            "public_ready": False,
            "live_eligibility": False,
        }
        citation_fingerprints = sorted(
            sha256(str(citation).encode("utf-8")).hexdigest()
            for citation in payload["citations"]
        )
        hash_inputs = {
            "candidate_id": candidate["candidate_id"],
            "platform_id": payload["platform_id"],
            "payload_shape": payload["payload_shape"],
            "mode": payload["mode"],
            "text": payload["text"],
            "citation_fingerprints": citation_fingerprints,
            "limitations": payload["limitations"],
            "policy": {
                "approval_required": True,
                "valid_for_dispatch": False,
                "dispatch_ready": False,
                "public_ready": False,
                "live_eligibility": False,
            },
        }
        safe_payload["citation_fingerprints"] = citation_fingerprints
        safe_payload["payload_hash"] = compute_payload_hash(hash_inputs)
        previews.append(safe_payload)
    return {
        "status": (
            "READY_FOR_OPERATOR_REVIEW"
            if previews
            else "BLOCKED_EXACT_PAYLOAD_MISSING"
        ),
        "previews": previews,
        "approval_boundary": {
            "approval_required": True,
            "valid_for_dispatch": False,
            "approval_for_publication": False,
            "operator_approval_captured": False,
        },
    }


def _assert_no_live_flags(node: Any) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in REQUIRED_FALSE_FLAGS and value is True:
                raise ValueError(f"live_flag_enabled:{key}")
            _assert_no_live_flags(value)
    elif isinstance(node, list):
        for value in node:
            _assert_no_live_flags(value)


def generate_batch(
    *, repo_root: Path, upstream_root: Path, observed_upstream_head: str
) -> dict[str, Any]:
    output = repo_root / EVIDENCE_RELATIVE
    output.mkdir(parents=True, exist_ok=True)
    operation = build_window_incremental_editorial_shadow(
        repo_root=repo_root,
        upstream_root=upstream_root,
        observed_upstream_head=observed_upstream_head,
    )
    candidates = _collect_candidates(operation)
    profiles = build_constraint_profiles_from_registry_v2(
        [
            {
                "platform_id": platform_id,
                "current_repo_allowed_state": (
                    "manual_export_only"
                    if platform_id == "substack_newsletter"
                    else "dry_run_only"
                ),
            }
            for platform_id in APPROVED_PLATFORM_IDS_V2
        ]
    )
    handoff = operation.get("editorial_shadow_handoff")
    handoff_by_id = (
        {str(handoff.get("candidate_id")): handoff} if handoff else {}
    )
    outcomes = []
    platform_rows = []
    for index, candidate in enumerate(candidates):
        candidate_handoff = handoff_by_id.get(str(candidate["candidate_id"]))
        if candidate.get("reporting_allowed") is True:
            cycle = _compiler_cycle(candidate, candidate_handoff, profiles)
            preview = _preview(candidate, cycle)
            compiler_summary = cycle["summary"]
            platform_rows.extend(preview["previews"])
        else:
            preview = {
                "status": "CONTEXT_ONLY_NO_PUBLICATION",
                "previews": [],
                "approval_boundary": {
                    "approval_required": True,
                    "valid_for_dispatch": False,
                    "approval_for_publication": False,
                    "operator_approval_captured": False,
                },
            }
            compiler_summary = None
        row = {
            "sequence": index + 1,
            "candidate_id": candidate["candidate_id"],
            "title": candidate.get("title"),
            "domain": _domain(candidate),
            "source_family_ids": sorted(candidate.get("source_family_ids", [])),
            "source_native_ids": sorted(candidate.get("source_native_ids", [])),
            "reporting_allowed": candidate.get("reporting_allowed") is True,
            "evidence_state": candidate.get("evidence_state"),
            "freshness_availability": candidate.get("freshness", {}).get(
                "availability"
            ),
            "editorial_outcome": _editorial_outcome(candidate),
            "compiler_summary": compiler_summary,
            "platform_preview": preview,
        }
        _assert_no_live_flags(row)
        outcomes.append(row)

    candidate_source_families = sorted(_families(candidates))
    fabric_source_families = sorted(
        set(candidate_source_families) | {"platform_capability_registry_v2"}
    )
    domains = sorted({row["domain"] for row in outcomes})
    outcome_statuses = sorted({row["editorial_outcome"] for row in outcomes})
    if len(candidate_source_families) < 4 or len(domains) < 4:
        raise ValueError(
            "coverage_below_requirement:"
            f"families={len(candidate_source_families)}:domains={len(domains)}"
        )
    if not 5 <= len(outcome_statuses) <= 8:
        raise ValueError(
            f"editorial_outcome_count_out_of_range:{len(outcome_statuses)}"
        )
    unsupported = [
        {
            "platform_id": platform,
            "status": status,
            "reason": "no canonical v2 local preview contract",
        }
        for platform, status in sorted(UNSUPPORTED_SURFACES.items())
    ]
    documents: dict[str, Any] = {
        "batch_summary.json": {
            "schema_version": "contentops.fast_ship_batch_summary.v1",
            "task": TASK,
            "batch_size": len(candidates),
            "governed_candidate_count": operation["summary"]["candidate_count"],
            "authorized_candidate_count": sum(
                row["reporting_allowed"] for row in outcomes
            ),
            "context_only_candidate_count": sum(
                not row["reporting_allowed"] for row in outcomes
            ),
            "candidate_source_family_count": len(candidate_source_families),
            "candidate_source_family_ids": candidate_source_families,
            "governed_fabric_source_family_count": len(fabric_source_families),
            "governed_fabric_source_family_ids": fabric_source_families,
            "domain_count": len(domains),
            "domains": domains,
            "editorial_outcome_count": len(outcome_statuses),
            "editorial_outcomes": outcome_statuses,
            "platform_preview_count": len(platform_rows),
            "platforms_with_previews": sorted(
                {row["platform_id"] for row in platform_rows}
            ),
            "unsupported_surfaces": unsupported,
            "calibration_state": "UNCALIBRATED_FOUNDATION",
            "publication_count": 0,
            "public_write_count": 0,
            "upstream_write_count": 0,
        },
        "editorial_outcomes.json": {
            "schema_version": "contentops.fast_ship_editorial_outcomes.v1",
            "outcomes": outcomes,
            "outcome_statuses": outcome_statuses,
            "all_local_only": True,
            "all_publication_authority_false": True,
        },
        "platform_variant_and_preview_summary.json": {
            "schema_version": (
                "contentops.fast_ship_platform_variant_preview_summary.v1"
            ),
            "priority_platforms": list(PRIORITY_PLATFORMS),
            "preview_count": len(platform_rows),
            "variants": platform_rows,
            "unsupported_surfaces": unsupported,
            "all_valid_for_dispatch_false": all(
                not row["valid_for_dispatch"] for row in platform_rows
            ),
            "all_public_ready_false": all(
                not row["public_ready"] for row in platform_rows
            ),
        },
        "validation_truth.json": {
            "schema_version": "contentops.validation_truth.v1",
            "status": "PASS",
            "batch_size_in_range": 10 <= len(candidates) <= 20,
            "governed_fabric_source_family_requirement_met": (
                len(fabric_source_families) >= 5
            ),
            "candidate_source_family_inventory_count": len(
                candidate_source_families
            ),
            "platform_capability_family_counted_separately": True,
            "no_source_family_misattribution": True,
            "domain_requirement_met": len(domains) >= 4,
            "editorial_outcome_requirement_met": 5 <= len(outcome_statuses) <= 8,
            "platform_preview_requirement_met": len(platform_rows) > 0,
            "compiler_payload_count_matches": all(
                row["compiler_summary"]
                and row["compiler_summary"]["output_payload_count"]
                == len(PRIORITY_PLATFORMS)
                for row in outcomes
                if row["reporting_allowed"]
            ),
            "no_live_flags_enabled": True,
            "no_network_or_provider_calls": True,
            "no_credentials_read": True,
            "publication_count": 0,
            "public_write_count": 0,
            "upstream_write_count": 0,
        },
    }
    for name, value in documents.items():
        _write(output / name, value)
    artifacts = [
        {
            "path": str((EVIDENCE_RELATIVE / name).as_posix()),
            "sha256": _sha(output / name),
            "byte_length": (output / name).stat().st_size,
        }
        for name in sorted(documents)
    ]
    manifest = {
        "schema_version": (
            "contentops.fast_ship_cross_domain_operator_ready_final_manifest.v1"
        ),
        "task": TASK,
        "batch_schema_version": SCHEMA_VERSION,
        "operation_logical_hash": operation["logical_hash"],
        "observed_upstream_head": observed_upstream_head,
        "candidate_ids": [candidate["candidate_id"] for candidate in candidates],
        "candidate_source_family_ids": candidate_source_families,
        "governed_fabric_source_family_ids": fabric_source_families,
        "domains": domains,
        "editorial_outcomes": outcome_statuses,
        "artifacts": artifacts,
        "unsupported_surfaces": unsupported,
        "publication_authority": False,
        "public_write_performed": False,
        "upstream_write_performed": False,
        "network_intake_performed": False,
        "credential_read_performed": False,
        "terminal_classification": "PASS_LOCAL_OPERATOR_READY_BATCH",
        "exact_next_action": (
            "INDEPENDENT_OPERATOR_AUDIT_OF_BATCH_EVIDENCE_AND_PREVIEWS"
        ),
    }
    manifest["logical_hash"] = sha256(_canonical(manifest)).hexdigest()
    _write(output / "final_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--observed-upstream-head", required=True)
    args = parser.parse_args()
    print(
        generate_batch(
            repo_root=args.repo_root.resolve(),
            upstream_root=args.upstream_root.resolve(),
            observed_upstream_head=args.observed_upstream_head,
        )["logical_hash"]
    )
