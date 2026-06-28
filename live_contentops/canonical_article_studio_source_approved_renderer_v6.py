"""V6 Canonical Article Studio Source Approved Renderer Coordinator.

Orchestrates empty renderer gate artifacts and enforces safety invariants.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from live_contentops import canonical_article_studio_renderer_gate_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_renderer_input_contract_v6 as contract_builder
from live_contentops import canonical_article_studio_renderer_validator_v6 as validator_module
from live_contentops import canonical_article_studio_draft_slot_schema_v6 as schema_builder

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_ARTICLE_STUDIO_SOURCE_APPROVED_RENDERER")
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_STUDIO_EDITORIAL_REFINEMENT_QUEUE_DRY_RUN_HEAVY_BATCH_V0"


def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_blocked_renderer_output() -> dict[str, Any]:
    return {
        "renderer_output_status": "BLOCKED_NO_DRAFT_RENDERED",
        "runtime_truth": False,
        "renderer_execution_performed": False,
        "article_copy_generated": False,
        "title": None,
        "dek": None,
        "body": None,
        "seo_title": None,
        "seo_meta_description": None,
        "citations": [],
        "evidence_refs": [],
        "source_names": [],
        "body_word_count": 0,
        "source_citation_count": 0,
        "evidence_excerpt_count": 0,
        "public_postable": False,
        "allowed_for_publication": False,
        "dispatch_allowed_now": False,
        "blockers": [
            "real_source_pack_not_approved",
            "runtime_operator_approval_missing",
            "source_approval_hash_missing",
            "renderer_execution_blocked",
            "article_copy_generation_blocked",
            "jim_review_required",
            "publication_blocked",
            "dispatch_blocked"
        ]
    }


def make_renderer_slot_status_matrix() -> list[dict[str, Any]]:
    slots = schema_builder.make_canonical_article_studio_draft_slot_schema()
    matrix = []
    
    claim_ids = ["claim_d474a9fdbcd6", "claim_63d1cf20e9bf", "claim_492c29ad9746"]
    req_ids = ["req_67a5db6704f5", "req_bfcb46cc38cc", "req_e6edaf8e7750"]

    for slot in slots:
        slot_id = slot["slot_id"]
        if slot["slot_type"] == "claim_summary":
            c_refs = [claim_ids[0]]
            r_refs = [req_ids[0]]
        elif slot["slot_type"] == "evidence_placeholder":
            c_refs = claim_ids[0:2]
            r_refs = req_ids[0:2]
        else:
            c_refs = []
            r_refs = []

        matrix.append({
            "slot_id": slot_id,
            "slot_type": slot["slot_type"],
            "placeholder_id": f"placeholder_id_{slot_id}",
            "renderer_input_status": "blocked_missing_source_approval",
            "placeholder_value": None,
            "rendered_value": None,
            "source_binding_required": slot["source_binding_required"],
            "claim_id_refs": c_refs,
            "source_requirement_refs": r_refs,
            "source_values_materialized": False,
            "generated": False,
            "valid_for_publication": False,
            "blocks_publication": True
        })
    return matrix


def make_blocker_report_markdown(blockers: list[str]) -> str:
    lines = [
        "# V6 Canonical Article Studio Source Approved Renderer Blocker Report",
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
    return """# V6 Canonical Article Studio Source Approved Renderer Runbook

This runbook documents operator and system actions for the offline simulated Renderer Gate state.

## Operator Review Checklist
1. Confirm that all rendered values remain unpopulated (null).
2. Verify that no raw sources or signatures are leaked.
3. Confirm that all active dispatch, publication, and outbox flags are locked to false.

## Resolving Blockers
- Real Jim approval is required to clear `real_source_pack_not_approved` and `runtime_operator_approval_missing`.
"""


def make_implementation_report_markdown() -> str:
    return """# V6 Canonical Article Studio Source Approved Renderer Implementation Report

## Summary
The Canonical Article Studio Source Approved Renderer lane is established as an offline, dry-run state.

## Verified Invariants
- `renderer_gate_status` = `SOURCE_APPROVED_RENDERER_BLOCKED_WAITING_FOR_REAL_APPROVAL`
- All active post/dispatch flags are hardlocked to `false`.
"""


def make_next_task_pointer_markdown() -> str:
    return f"""# Next recommended task
{NEXT_RECOMMENDED_TASK}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Canonical Article Studio Source Approved Renderer Lane")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create packets, schemas, instance
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = make_blocked_renderer_output()
    renderer_slot_status_matrix = make_renderer_slot_status_matrix()

    # 2. Run validator
    report, blockers = validator_module.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )

    # 3. Write all 9 artifacts
    write_json(out_dir / "canonical_article_studio_renderer_gate_packet.json", renderer_gate_packet)
    write_json(out_dir / "canonical_article_studio_renderer_input_contract.json", renderer_input_contract)
    write_json(out_dir / "canonical_article_studio_blocked_renderer_output.json", blocked_renderer_output)
    write_json(out_dir / "canonical_article_studio_renderer_slot_status_matrix.json", renderer_slot_status_matrix)
    write_json(out_dir / "canonical_article_studio_renderer_validation_report.json", report)
    write_text(out_dir / "canonical_article_studio_renderer_blocker_report.md", make_blocker_report_markdown(blockers))
    write_text(out_dir / "canonical_article_studio_renderer_runbook.md", make_runbook_markdown())
    write_text(out_dir / "implementation_report.md", make_implementation_report_markdown())
    write_text(out_dir / "next_task_pointer.md", make_next_task_pointer_markdown())

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
