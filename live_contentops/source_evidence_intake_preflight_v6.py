"""V6 Source Evidence Intake and Approval Preflight Lane.

Consumes Discord drop, operator review, research grounding, and platform variant packets
to output deterministic source reference registries and approval preflight checklists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_SOURCE_EVIDENCE_INTAKE_AND_APPROVAL_PREFLIGHT_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_DROP_PACKET = Path("docs/automation/V6_DISCORD_COMMUNITY_DROP/discord_drop_packet.json")
DEFAULT_REVIEW_PACKET = Path("docs/automation/V6_DISCORD_COMMUNITY_DROP/operator_review_packet.json")
DEFAULT_GROUNDING_PACKET = Path("docs/automation/V6_AI_RESEARCH_GROUNDING/research_grounding_packet.json")
DEFAULT_VARIANT_PACKET = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT")
DEFAULT_INTAKE_OUTPUT = DEFAULT_OUTPUT_DIR / "source_evidence_intake_packet.json"


def path_text(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_source_checklist_markdown(packet: dict[str, Any]) -> str:
    missing_source_refs = packet.get("missing_source_refs", [])
    missing_str = ", ".join(f"`{r}`" for r in missing_source_refs) or "None"

    return f"""# Source Evidence Checklist

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This document contains preflight checklists. It is not publish-ready and must not be posted or used to trigger public dispatch.

## Preflight Status
- **Intake Status**: {packet.get('intake_status')}
- **Missing Source References**: {missing_str}

## Operator Instructions
- To supply evidence, the operator must provide local file paths, repository files, screenshots, or verified URL notes.
- Update the registry by mapping real sources to the missing reference slots.

## Safety & Compliance Reminder
- **No-Live / No-Dispatch Warning**: Dispatch remains strictly blocked because `dispatch_allowed_now` is false.
- **No Fake-Citation Warning**: Do not invent sources, citations, CPC statistics, user numbers, latency totals, or market data.
"""


def generate_approval_checklist_markdown(packet: dict[str, Any], preflight: dict[str, Any]) -> str:
    unresolved_source_refs = preflight.get("unresolved_source_refs", [])
    unresolved_str = ", ".join(f"`{r}`" for r in unresolved_source_refs) or "None"

    return f"""# Approval Preflight Checklist

## Preflight Check
- **Review Status**: {preflight.get('review_status')}
- **Unresolved Source References**: {unresolved_str}

## Preflight Review Areas

### 1. Source Evidence Checklist
- [ ] Ensure all missing source references are mapped to verified operator evidence.
- [ ] Confirm `evidence_complete` is true.

### 2. Exact Payload Hash Checklist
- [ ] Generate exact payload hash of content drafts.
- [ ] Confirm `exact_payload_hash_present` is updated to true.

### 3. Destination Binding Checklist
- [ ] Ensure non-sensitive channel family matches a valid local registry layout.
- [ ] Confirm `destination_binding_present` is true.

### 4. Safety Constraints Checklist
- [ ] Confirm no hype language is present.
- [ ] Confirm no trading signals, stop loss/take profit, position sizing, or price predictions are present.
- [ ] Confirm no webhook URLs, raw tokens, or credential variables exist in any file.

## Final Review Check
- **Dispatch Blocked Note**: Dispatch remains strictly blocked. `dispatch_allowed_now` is false.
"""


def materialize_intake_packets(
    drop_packet_path: str | Path = DEFAULT_DROP_PACKET,
    review_packet_path: str | Path = DEFAULT_REVIEW_PACKET,
    grounding_packet_path: str | Path = DEFAULT_GROUNDING_PACKET,
    variant_packet_path: str | Path = DEFAULT_VARIANT_PACKET
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    upstream_blocked = False
    blocked_reasons = []

    try:
        drop_data = load_json(drop_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"drop_packet_unreadable:{exc.__class__.__name__}")
        drop_data = {}

    try:
        review_data = load_json(review_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"review_packet_unreadable:{exc.__class__.__name__}")
        review_data = {}

    try:
        grounding_data = load_json(grounding_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"grounding_packet_unreadable:{exc.__class__.__name__}")
        grounding_data = {}

    try:
        variant_data = load_json(variant_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"variant_packet_unreadable:{exc.__class__.__name__}")
        variant_data = {}

    source_article_id = drop_data.get("source_article_id") or variant_data.get("source_article_id")
    source_intent_id = drop_data.get("source_intent_id") or variant_data.get("source_intent_id")
    source_mode = drop_data.get("source_mode") or variant_data.get("source_mode") or "unknown"
    source_variant_status = drop_data.get("source_variant_status") or variant_data.get("variant_status")

    missing_source_refs = list(drop_data.get("missing_source_refs") or variant_data.get("missing_source_refs") or [])
    source_needed = drop_data.get("source_needed") or variant_data.get("source_needed") or False
    source_evidence_required = drop_data.get("source_evidence_required") or variant_data.get("source_evidence_required") or False
    
    blocked_reasons.extend(drop_data.get("blocked_reasons", []))
    blocked_reasons.extend(variant_data.get("blocked_reasons", []))
    blocked_reasons = sorted(list(set(blocked_reasons)))

    # Evaluate Status
    if upstream_blocked or "BLOCKED" in str(source_variant_status) or blocked_reasons:
        intake_status = "BLOCKED_BY_UPSTREAM_PACKET"
    elif missing_source_refs or source_needed:
        intake_status = "AWAITING_OPERATOR_SOURCE_EVIDENCE"
    else:
        intake_status = "SOURCE_EVIDENCE_READY_FOR_HUMAN_REVIEW"

    evidence_complete = (not missing_source_refs) and (not source_needed) and (intake_status != "BLOCKED_BY_UPSTREAM_PACKET")

    hasher = hashlib.sha256(f"{drop_data.get('discord_drop_packet_id')}_{intake_status}".encode("utf-8"))
    source_evidence_intake_packet_id = f"intake_{hasher.hexdigest()[:12]}"
    approval_preflight_packet_id = f"preflight_{hasher.hexdigest()[:8]}"

    # Build reference registry
    registry = []
    for ref in missing_source_refs:
        registry.append({
            "source_ref_id": ref,
            "required": True,
            "status": "MISSING_OPERATOR_SUPPLIED_EVIDENCE",
            "accepted_evidence_types": [
                "local_doc_path",
                "repo_file_path",
                "screenshot_path",
                "official_source_url_to_be_reviewed_later",
                "operator_note"
            ],
            "supplied_value": None,
            "verified": False,
            "verification_notes": None
        })

    # Intake Packet
    intake_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "source_evidence_intake_packet_id": source_evidence_intake_packet_id,
        "source_discord_drop_packet_id": drop_data.get("discord_drop_packet_id"),
        "source_operator_review_packet_id": review_data.get("operator_review_packet_id"),
        "source_platform_variant_packet_id": variant_data.get("platform_variant_packet_id"),
        "source_research_packet_id": grounding_data.get("research_packet_id"),
        "intake_status": intake_status,
        "intake_stage": "source_evidence_preflight",
        "missing_source_refs": missing_source_refs,
        "registered_source_refs": [r["source_ref_id"] for r in registry if r.get("verified")],
        "unresolved_source_refs": missing_source_refs,
        "source_needed": source_needed,
        "source_evidence_required": source_evidence_required,
        "evidence_complete": evidence_complete,
        "approval_preflight_file": "docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/approval_preflight_packet.json",
        "source_reference_registry_file": "docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_reference_registry.json",
        "dispatch_readiness_snapshot_file": "docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/dispatch_readiness_snapshot.json",
        "public_postable": False,
        "human_review_required": True,
        "approval_required": True,
        "approval_performed": False,
        "dispatch_allowed_now": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "no_network_call_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "blocked_reasons": blocked_reasons,
        "next_recommended_task": "TASK_CONTENTOPS_V6_SOURCE_EVIDENCE_INTAKE_AND_APPROVAL_PREFLIGHT_HEAVY_BATCH_V0" if intake_status == "BLOCKED_BY_UPSTREAM_PACKET" else "TASK_CONTENTOPS_V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION_VALIDATOR_AND_PREFLIGHT_POINTER_REPAIR_HEAVY_BATCH_V0"
    }

    # Approval Preflight Packet
    preflight_packet = {
        "approval_preflight_packet_id": approval_preflight_packet_id,
        "source_evidence_intake_packet_id": source_evidence_intake_packet_id,
        "review_status": "AWAITING_SOURCE_EVIDENCE" if missing_source_refs else "READY_FOR_PREFLIGHT_REVIEW",
        "evidence_complete": evidence_complete,
        "exact_payload_hash_required": True,
        "exact_payload_hash_present": False,
        "destination_binding_required": True,
        "destination_binding_present": False,
        "source_refs_required": True,
        "unresolved_source_refs": missing_source_refs,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "not_approved": True,
        "not_dispatchable": True,
        "blockers": ["missing_source_references", "payload_hash_uncalculated", "destination_binding_unconfirmed"] if missing_source_refs else ["payload_hash_uncalculated", "destination_binding_unconfirmed"]
    }

    # Dispatch Readiness Snapshot
    snapshot = {
        "dispatch_readiness_status": "BLOCKED_SOURCE_EVIDENCE_MISSING" if missing_source_refs else "BLOCKED_AWAITING_OPERATOR_APPROVAL",
        "source_evidence_complete": evidence_complete,
        "operator_approval_complete": False,
        "destination_binding_complete": False,
        "payload_hash_complete": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "next_required_operator_action": "Supply local file, screenshot, or verified URL reference evidence to unblock missing references checklist." if missing_source_refs else "Perform human operator review checklist approval signatures."
    }

    return intake_packet, registry, preflight_packet, snapshot


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# V6 Source Evidence Preflight

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- No network call in this task: `true`
- Source evidence registry placeholders created: `true`
- Preflight readiness checkpoints built: `true`
- Fake public-postable content created: `false`

The source evidence intake registries and approval preflight locks are successfully initialized.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent, source evidence, grounding, refinement, variant, or staging block conditions."
    else:
        goal = "Point forwarding to Platform Native Variant Lane / Real Evidence Supplier workflows."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Source Evidence Intake and Preflight")
    parser.add_argument("--drop-packet", default=str(DEFAULT_DROP_PACKET))
    parser.add_argument("--review-packet", default=str(DEFAULT_REVIEW_PACKET))
    parser.add_argument("--grounding-packet", default=str(DEFAULT_GROUNDING_PACKET))
    parser.add_argument("--variant-packet", default=str(DEFAULT_VARIANT_PACKET))
    parser.add_argument("--output-packet", default=str(DEFAULT_INTAKE_OUTPUT))
    args = parser.parse_args(argv)

    intake, registry, preflight, snapshot = materialize_intake_packets(
        args.drop_packet, args.review_packet, args.grounding_packet, args.variant_packet
    )
    write_json(args.output_packet, intake)

    out_dir = Path(args.output_packet).parent
    write_json(out_dir / "source_reference_registry.json", registry)
    write_json(out_dir / "approval_preflight_packet.json", preflight)
    write_json(out_dir / "dispatch_readiness_snapshot.json", snapshot)

    # Write checklists
    (out_dir / "source_evidence_checklist.md").write_text(generate_source_checklist_markdown(intake), encoding="utf-8")
    (out_dir / "approval_preflight_checklist.md").write_text(generate_approval_checklist_markdown(intake, preflight), encoding="utf-8")

    # Write report and pointer
    (out_dir / "implementation_report.md").write_text(implementation_report(intake), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(next_task_pointer(intake), encoding="utf-8")

    print(json.dumps({
        "source_evidence_intake_packet_id": intake["source_evidence_intake_packet_id"],
        "intake_status": intake["intake_status"],
        "blocked_reasons": intake["blocked_reasons"]
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
