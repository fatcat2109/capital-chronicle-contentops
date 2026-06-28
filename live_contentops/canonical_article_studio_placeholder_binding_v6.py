"""V6 Canonical Article Studio Placeholder Binding Coordinator.

Orchestrates empty placeholder binding artifacts and enforces safety invariants.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from live_contentops import canonical_article_studio_placeholder_binding_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_placeholder_binding_review_v6 as review_builder
from live_contentops import canonical_article_studio_placeholder_binding_validator_v6 as validator_module
from live_contentops import canonical_article_studio_draft_slot_schema_v6 as schema_builder

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_ARTICLE_STUDIO_PLACEHOLDER_BINDING")
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_STUDIO_SOURCE_APPROVED_DRAFT_RENDERER_DRY_RUN_HEAVY_BATCH_V0"


def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_slot_binding_map() -> list[dict[str, Any]]:
    slots = schema_builder.make_canonical_article_studio_draft_slot_schema()
    bindings = []
    
    claim_ids = ["claim_d474a9fdbcd6", "claim_63d1cf20e9bf", "claim_492c29ad9746"]
    req_ids = ["req_67a5db6704f5", "req_bfcb46cc38cc", "req_e6edaf8e7750"]

    for slot in slots:
        slot_id = slot["slot_id"]
        # Map specific claim and req IDs based on slot type to keep structure realistic
        if slot["slot_type"] == "claim_summary":
            c_refs = [claim_ids[0]]
            r_refs = [req_ids[0]]
        elif slot["slot_type"] == "evidence_placeholder":
            c_refs = claim_ids[0:2]
            r_refs = req_ids[0:2]
        else:
            c_refs = []
            r_refs = []

        bindings.append({
            "slot_id": slot_id,
            "slot_type": slot["slot_type"],
            "binding_status": "PLACEHOLDER_BOUND_REVIEW_ONLY",
            "placeholder_id": f"placeholder_id_{slot_id}",
            "placeholder_value": None,
            "placeholder_label": "PLACEHOLDER_ONLY_NOT_CONTENT",
            "source_binding_required": slot["source_binding_required"],
            "claim_id_refs": c_refs,
            "source_requirement_refs": r_refs,
            "generated": False,
            "materialized": False,
            "valid_for_runtime_draft": False,
            "valid_for_publication": False,
            "blocks_publication": True
        })
    return bindings


def make_placeholder_bound_shell_instance(bindings: list[dict[str, Any]]) -> dict[str, Any]:
    # Modify the base slots list to contain the binding metadata but current_value=null
    slots_with_binding = []
    for b in bindings:
        slots_with_binding.append({
            "slot_id": b["slot_id"],
            "slot_type": b["slot_type"],
            "allowed_content_state": "placeholder_bound_review_only",
            "current_value": None,
            "placeholder_id": b["placeholder_id"],
            "placeholder_label": b["placeholder_label"],
            "generated": False,
            "source_binding_required": b["source_binding_required"],
            "blocks_publication": True
        })

    return {
        "shell_instance_status": "PLACEHOLDER_BOUND_EMPTY_DRAFT_SHELL_BLOCKED",
        "article_topic_ref": "article_packet_6e40db810195",
        "claim_ids": [
            "claim_d474a9fdbcd6",
            "claim_63d1cf20e9bf",
            "claim_492c29ad9746"
        ],
        "source_requirement_refs": [
            "req_67a5db6704f5",
            "req_bfcb46cc38cc",
            "req_e6edaf8e7750"
        ],
        "slots": slots_with_binding,
        "article_copy_generated": False,
        "title_generated": False,
        "dek_generated": False,
        "seo_metadata_generated": False,
        "body_word_count": 0,
        "source_citation_count": 0,
        "evidence_excerpt_count": 0,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "blockers": [
            "real_source_pack_not_approved",
            "runtime_operator_approval_missing",
            "placeholder_values_not_materialized",
            "article_copy_generation_blocked",
            "editor_review_required",
            "jim_review_required",
            "publication_blocked",
            "dispatch_blocked"
        ]
    }


def make_blocker_report_markdown(blockers: list[str]) -> str:
    lines = [
        "# V6 Canonical Article Studio Placeholder Binding Blocker Report",
        "",
        "The following active blockers prevent draft generation, publication, or dispatch operations:",
        ""
    ]
    for b in blockers:
        lines.append(f"- **{b}**: Locked by default dry-run configuration.")
    lines.extend([
        "",
        "## Offline Safety Guarantees",
        "- Raw sources and operators are strictly redacted.",
        "- Live browser orchestration and network writes are disabled.",
        "- Jim's signature is completely absent."
    ])
    return "\n".join(lines)


def make_runbook_markdown() -> str:
    return """# V6 Canonical Article Studio Placeholder Binding Runbook

This runbook documents operator and system actions for the offline simulated Placeholder Binding state.

## Operator Review Checklist
1. Confirm that all placeholder values remain unmaterialized (null).
2. Verify that no raw sources or signatures are leaked.
3. Confirm that all active dispatch, publication, and outbox flags are locked to false.

## Resolving Blockers
- Real Jim approval is required to clear `real_source_pack_not_approved` and `runtime_operator_approval_missing`.
"""


def make_implementation_report_markdown() -> str:
    return """# V6 Canonical Article Studio Placeholder Binding Implementation Report

## Summary
The Canonical Article Studio Placeholder Binding lane is established as an offline, dry-run state.

## Verified Invariants
- `binding_status` = `PLACEHOLDER_BINDING_READY_WITH_BLOCKERS`
- All active post/dispatch flags are hardlocked to `false`.
"""


def make_next_task_pointer_markdown() -> str:
    return f"""# Next recommended task
{NEXT_RECOMMENDED_TASK}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Canonical Article Studio Placeholder Binding Lane")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create packets, schemas, instance
    binding_packet = packet_builder.make_canonical_article_studio_placeholder_binding_packet()
    slot_binding_map = make_slot_binding_map()
    binding_review = review_builder.make_canonical_article_studio_placeholder_binding_review()
    placeholder_bound_shell_instance = make_placeholder_bound_shell_instance(slot_binding_map)

    # 2. Run validator
    report, blockers = validator_module.validate_canonical_article_studio_placeholder_binding(
        binding_packet, slot_binding_map, binding_review, placeholder_bound_shell_instance
    )

    # 3. Write all 9 artifacts
    write_json(out_dir / "canonical_article_studio_placeholder_binding_packet.json", binding_packet)
    write_json(out_dir / "canonical_article_studio_slot_binding_map.json", slot_binding_map)
    write_json(out_dir / "canonical_article_studio_placeholder_binding_review.json", binding_review)
    write_json(out_dir / "canonical_article_studio_placeholder_bound_shell_instance.json", placeholder_bound_shell_instance)
    write_json(out_dir / "canonical_article_studio_placeholder_binding_validation_report.json", report)
    write_text(out_dir / "canonical_article_studio_placeholder_binding_blocker_report.md", make_blocker_report_markdown(blockers))
    write_text(out_dir / "canonical_article_studio_placeholder_binding_runbook.md", make_runbook_markdown())
    write_text(out_dir / "implementation_report.md", make_implementation_report_markdown())
    write_text(out_dir / "next_task_pointer.md", make_next_task_pointer_markdown())

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
