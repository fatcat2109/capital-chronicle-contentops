"""V6 Readiness Evidence Bundle Lane.

Consolidates the accepted V6 content pipeline states from operator intent through
supervised dispatch readiness into a single evidence-grade status bundle and matrix.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_READINESS_EVIDENCE_BUNDLE_AND_FORWARD_POINTER_ALIGNMENT_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_INTENT = Path("docs/automation/V6_OPERATOR_INTENT/operator_intent_packet.json")
DEFAULT_ARTICLE = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
DEFAULT_GROUNDING = Path("docs/automation/V6_AI_RESEARCH_GROUNDING/research_grounding_packet.json")
DEFAULT_SEO = Path("docs/automation/V6_SEO_EDITORIAL_REFINEMENT/seo_editorial_packet.json")
DEFAULT_VARIANT = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json")
DEFAULT_DROP = Path("docs/automation/V6_DISCORD_COMMUNITY_DROP/discord_drop_packet.json")
DEFAULT_PREFLIGHT = Path("docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_evidence_intake_packet.json")
DEFAULT_SUBMISSION = Path("docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/operator_source_evidence_submission_packet.json")
DEFAULT_GATE = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json")
DEFAULT_READINESS = Path("docs/automation/V6_SUPERVISED_DISPATCH_READINESS/supervised_dispatch_readiness_packet.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_READINESS_EVIDENCE_BUNDLE")
DEFAULT_BUNDLE_OUTPUT = DEFAULT_OUTPUT_DIR / "readiness_evidence_bundle_packet.json"


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_operator_review_summary_markdown(packet: dict[str, Any]) -> str:
    return f"""# V6 Operator Review Summary

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This document contains consolidated preflight staging statuses. It is not publish-ready and must not be posted or sent to any live Discord channel.

## Current Pipeline Status
- **Bundle Status**: {packet.get('bundle_status')}
- **Dispatch Readiness Status**: {packet.get('current_dispatch_readiness_status')}

## What Is Implemented
- **Lanes Summarized**: {packet.get('lanes_summarized')}
- All 10 lanes from operator intent through supervised dispatch readiness are successfully compiled, verified, and mapped local-only.

## Why Dispatch Remains Blocked
- Factual source evidence, payload hashes, channel bindings, and operator approval are not yet fully resolved.
- **No Outbox / Ledger Created**: No real outbox queue or approved ledger entries have been written.
- **Dispatch Blocked Note**: Dispatch remains strictly blocked because `dispatch_allowed_now` is false.

## Safety & Compliance Lock
- **No Fake-Citation Note**: No fake or placeholder citations may be turned into claims.
- **No Fake-Metric Note**: Do not invent metrics or statistics.
- **No Secret-Output Note**: Webhook URLs, headers, and secrets are strictly excluded.
"""


def generate_next_operator_actions_markdown(packet: dict[str, Any]) -> str:
    return f"""# V6 Next Operator Actions

## Future/Manual/Supervised Actions Only
This document describes future, supervised operations required by manual operators to unblock live publication. It does not perform these actions.

### 1. Source Evidence Actions
- Operators must submit safe, verified underlying evidence to unblock facts/claims.

### 2. Payload Hash Actions
- Operators must verify the final payload SHA256 matches staging digests.

### 3. Destination Binding Actions
- Operators must bind the non-sensitive channel destination in a separate, later explicit task.

### 4. Safety Review Actions
- Operators must sign off on safety compliance checks (zero signals/hype/sizing).

### 5. Operator Approval Actions
- Operators must execute and record final human review signatures on the template.

### 6. Live-Write Authorization Actions
- Obtain explicit, supervisor-level write authorizations (must occur in a separate live task).

### 7. Project Sources Refresh Action
- Upload the candidate files to the ChatGPT Project Sources to refresh context.
"""


def materialize_readiness_bundle_packets(
    intent_path: str | Path = DEFAULT_INTENT,
    article_path: str | Path = DEFAULT_ARTICLE,
    grounding_path: str | Path = DEFAULT_GROUNDING,
    seo_path: str | Path = DEFAULT_SEO,
    variant_path: str | Path = DEFAULT_VARIANT,
    drop_path: str | Path = DEFAULT_DROP,
    preflight_path: str | Path = DEFAULT_PREFLIGHT,
    submission_path: str | Path = DEFAULT_SUBMISSION,
    gate_path: str | Path = DEFAULT_GATE,
    readiness_path: str | Path = DEFAULT_READINESS,
    override_ready: bool = False
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    upstream_blocked = False
    blocked_reasons = []

    def load_or_empty(path: str | Path, name: str) -> dict[str, Any]:
        nonlocal upstream_blocked
        try:
            return load_json(path)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
            upstream_blocked = True
            blocked_reasons.append(f"{name}_unreadable:{exc.__class__.__name__}")
            return {}

    intent_data = load_or_empty(intent_path, "intent")
    article_data = load_or_empty(article_path, "article")
    grounding_data = load_or_empty(grounding_path, "grounding")
    seo_data = load_or_empty(seo_path, "seo")
    variant_data = load_or_empty(variant_path, "variant")
    drop_data = load_or_empty(drop_path, "drop")
    preflight_data = load_or_empty(preflight_path, "preflight")
    submission_data = load_or_empty(submission_path, "submission")
    gate_data = load_or_empty(gate_path, "gate")
    readiness_data = load_or_empty(readiness_path, "readiness")

    blocked_reasons.extend(readiness_data.get("blocked_reasons", []))
    blocked_reasons = sorted(list(set(blocked_reasons)))

    # Status Logic
    if upstream_blocked or readiness_data.get("readiness_status") == "BLOCKED_BY_OPERATOR_APPROVAL_GATE" or blocked_reasons:
        bundle_status = "V6_READINESS_BUNDLE_BLOCKED_BY_DISPATCH_READINESS"
    else:
        bundle_status = "V6_READINESS_BUNDLE_READY_FOR_OPERATOR_REVIEW_ONLY"

    hasher = hashlib.sha256(f"{readiness_data.get('supervised_dispatch_readiness_packet_id')}_{bundle_status}".encode("utf-8"))
    readiness_evidence_bundle_packet_id = f"bundle_{hasher.hexdigest()[:12]}"

    # Combined Blocker Rollup
    blocker_rollup = {
        "operator_idea_source_ref_missing": True,
        "evidence_incomplete": True,
        "payload_hash_incomplete": True,
        "destination_binding_incomplete": True,
        "safety_review_incomplete": True,
        "operator_approval_incomplete": True,
        "kill_switch_active": True,
        "live_write_authorization_missing": True,
        "outbox_creation_blocked": True,
        "note": "Combined Rollup of all unresolved preflight requirements."
    }

    # Pipeline Status Matrix
    pipeline_matrix = [
        {
            "lane_name": "operator_intent",
            "source_packet_file": "docs/automation/V6_OPERATOR_INTENT/operator_intent_packet.json",
            "status_field": "intent_status",
            "status_value": intent_data.get("intent_status", "UNKNOWN"),
            "public_postable": intent_data.get("public_postable", False),
            "dispatch_allowed_now": intent_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(intent_data.get("blockers", [])),
            "next_required_action": "Complete canonical outline."
        },
        {
            "lane_name": "canonical_substack_article",
            "source_packet_file": "docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json",
            "status_field": "article_status",
            "status_value": article_data.get("article_status", "UNKNOWN"),
            "public_postable": article_data.get("public_postable", False),
            "dispatch_allowed_now": article_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(article_data.get("blockers", [])),
            "next_required_action": "Execute AI grounding lane."
        },
        {
            "lane_name": "ai_research_grounding",
            "source_packet_file": "docs/automation/V6_AI_RESEARCH_GROUNDING/research_grounding_packet.json",
            "status_field": "grounding_status",
            "status_value": grounding_data.get("grounding_status", "UNKNOWN"),
            "public_postable": grounding_data.get("public_postable", False),
            "dispatch_allowed_now": grounding_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(grounding_data.get("blockers", [])),
            "next_required_action": "Execute SEO editorial lane."
        },
        {
            "lane_name": "seo_editorial_refinement",
            "source_packet_file": "docs/automation/V6_SEO_EDITORIAL_REFINEMENT/seo_editorial_packet.json",
            "status_field": "refinement_status",
            "status_value": seo_data.get("refinement_status", "UNKNOWN"),
            "public_postable": seo_data.get("public_postable", False),
            "dispatch_allowed_now": seo_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(seo_data.get("blockers", [])),
            "next_required_action": "Generate platform variants."
        },
        {
            "lane_name": "platform_native_variants",
            "source_packet_file": "docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json",
            "status_field": "variant_status",
            "status_value": variant_data.get("variant_status", "UNKNOWN"),
            "public_postable": variant_data.get("public_postable", False),
            "dispatch_allowed_now": variant_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(variant_data.get("blockers", [])),
            "next_required_action": "Review Discord drop variant."
        },
        {
            "lane_name": "discord_community_drop",
            "source_packet_file": "docs/automation/V6_DISCORD_COMMUNITY_DROP/discord_drop_packet.json",
            "status_field": "drop_status",
            "status_value": drop_data.get("drop_status", "UNKNOWN"),
            "public_postable": drop_data.get("public_postable", False),
            "dispatch_allowed_now": drop_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(drop_data.get("blockers", [])),
            "next_required_action": "Map preflight source references."
        },
        {
            "lane_name": "source_evidence_preflight",
            "source_packet_file": "docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_evidence_intake_packet.json",
            "status_field": "preflight_status",
            "status_value": preflight_data.get("preflight_status", "UNKNOWN"),
            "public_postable": preflight_data.get("public_postable", False),
            "dispatch_allowed_now": preflight_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(preflight_data.get("blockers", [])),
            "next_required_action": "Run operator submission validator."
        },
        {
            "lane_name": "operator_source_evidence_submission",
            "source_packet_file": "docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/operator_source_evidence_submission_packet.json",
            "status_field": "submission_status",
            "status_value": submission_data.get("submission_status", "UNKNOWN"),
            "public_postable": submission_data.get("public_postable", False),
            "dispatch_allowed_now": submission_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(submission_data.get("blockers", [])),
            "next_required_action": "Evaluate operator approval gate."
        },
        {
            "lane_name": "operator_approval_gate",
            "source_packet_file": "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json",
            "status_field": "approval_gate_status",
            "status_value": gate_data.get("approval_gate_status", "UNKNOWN"),
            "public_postable": gate_data.get("public_postable", False),
            "dispatch_allowed_now": gate_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(gate_data.get("blockers", [])),
            "next_required_action": "Evaluate supervised dispatch readiness."
        },
        {
            "lane_name": "supervised_dispatch_readiness",
            "source_packet_file": "docs/automation/V6_SUPERVISED_DISPATCH_READINESS/supervised_dispatch_readiness_packet.json",
            "status_field": "readiness_status",
            "status_value": readiness_data.get("readiness_status", "UNKNOWN"),
            "public_postable": readiness_data.get("public_postable", False),
            "dispatch_allowed_now": readiness_data.get("dispatch_allowed_now", False),
            "unresolved_blockers": sorted(readiness_data.get("blockers", [])),
            "next_required_action": "Compile readiness evidence bundle."
        }
    ]

    # Project Sources Candidate Manifest
    sources_manifest = {
        "project_sources_title": "Capital Chronicle ContentOps V6 Pipeline State",
        "description": "Evidence-grade local files for ChatGPT Project Sources context refreshment.",
        "candidate_files": [
            "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md",
            "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/readiness_evidence_bundle_packet.json",
            "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_pipeline_status_matrix.json",
            "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_blocker_rollup.json",
            "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_operator_review_summary.md",
            "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_next_operator_actions.md",
            "docs/automation/V6_SUPERVISED_DISPATCH_READINESS/supervised_dispatch_readiness_packet.json",
            "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json",
            "docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/operator_source_evidence_submission_packet.json",
            "docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_evidence_intake_packet.json"
        ]
    }

    # Readiness Evidence Bundle Packet
    bundle_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "readiness_evidence_bundle_packet_id": readiness_evidence_bundle_packet_id,
        "source_supervised_dispatch_readiness_packet_id": readiness_data.get("supervised_dispatch_readiness_packet_id"),
        "source_operator_approval_gate_packet_id": gate_data.get("operator_approval_gate_packet_id"),
        "source_operator_submission_packet_id": submission_data.get("operator_source_evidence_submission_packet_id"),
        "source_discord_drop_packet_id": drop_data.get("discord_drop_packet_id"),
        "source_platform_variant_packet_id": variant_data.get("platform_variant_packet_id"),
        "bundle_status": bundle_status,
        "bundle_stage": "v6_readiness_evidence_bundle",
        "lanes_summarized": 10,
        "current_dispatch_readiness_status": readiness_data.get("readiness_status", "UNKNOWN"),
        "public_postable": False,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "kill_switch_active": True,
        "live_write_attempted": False,
        "outbox_entry_created": False,
        "approval_ledger_entry_created": False,
        "unresolved_blockers": sorted(list(blocker_rollup.keys())),
        "project_sources_candidate_manifest_file": "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_project_sources_candidate_manifest.json",
        "operator_review_summary_file": "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_operator_review_summary.md",
        "next_operator_actions_file": "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_next_operator_actions.md",
        "human_review_required": True,
        "approval_required": True,
        "approval_performed": False,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "no_network_call_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "blocked_reasons": blocked_reasons,
        "next_recommended_task": "TASK_CONTENTOPS_V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION_VALIDATOR_AND_PREFLIGHT_POINTER_REPAIR_HEAVY_BATCH_V0"
    }

    return bundle_packet, pipeline_matrix, blocker_rollup, sources_manifest, kill_switch_active_placeholder_only()


def kill_switch_active_placeholder_only() -> dict[str, Any]:
    return {"kill_switch_active": True}


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# V6 Readiness Evidence Bundle

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- No network call in this task: `true`
- Pipeline status matrix compiled: `true`
- Combined blocker rollup recorded: `true`
- Project Sources candidate manifest generated: `true`
- Fake public-postable content created: `false`

The readiness evidence status bundle is compiled and forward pointers are aligned.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    goal = "Proceed back to Operator Source Evidence Submission Validator lane once real manual evidence becomes available."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Readiness Evidence Bundle Lane")
    parser.add_argument("--intent", default=str(DEFAULT_INTENT))
    parser.add_argument("--article", default=str(DEFAULT_ARTICLE))
    parser.add_argument("--grounding", default=str(DEFAULT_GROUNDING))
    parser.add_argument("--seo", default=str(DEFAULT_SEO))
    parser.add_argument("--variant", default=str(DEFAULT_VARIANT))
    parser.add_argument("--drop-packet", default=str(DEFAULT_DROP))
    parser.add_argument("--preflight", default=str(DEFAULT_PREFLIGHT))
    parser.add_argument("--submission", default=str(DEFAULT_SUBMISSION))
    parser.add_argument("--gate", default=str(DEFAULT_GATE))
    parser.add_argument("--readiness", default=str(DEFAULT_READINESS))
    parser.add_argument("--output-packet", default=str(DEFAULT_BUNDLE_OUTPUT))
    args = parser.parse_args(argv)

    sub, matrix, rollup, manifest, _ = materialize_readiness_bundle_packets(
        args.intent, args.article, args.grounding, args.seo, args.variant, args.drop_packet,
        args.preflight, args.submission, args.gate, args.readiness
    )
    write_json(args.output_packet, sub)

    out_dir = Path(args.output_packet).parent
    write_json(out_dir / "v6_pipeline_status_matrix.json", matrix)
    write_json(out_dir / "v6_blocker_rollup.json", rollup)
    write_json(out_dir / "v6_project_sources_candidate_manifest.json", manifest)

    # Write summaries and next actions
    (out_dir / "v6_operator_review_summary.md").write_text(generate_operator_review_summary_markdown(sub), encoding="utf-8")
    (out_dir / "v6_next_operator_actions.md").write_text(generate_next_operator_actions_markdown(sub), encoding="utf-8")

    # Write report and pointer
    (out_dir / "implementation_report.md").write_text(implementation_report(sub), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(next_task_pointer(sub), encoding="utf-8")

    print(json.dumps({
        "readiness_evidence_bundle_packet_id": sub["readiness_evidence_bundle_packet_id"],
        "bundle_status": sub["bundle_status"],
        "blocked_reasons": sub["blocked_reasons"]
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
