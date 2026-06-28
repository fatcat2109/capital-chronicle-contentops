"""V6 Real Source Pack Operator Approval Gate Coordinator.

Coordinates setup and validation of the unapproved operator approval state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import real_source_pack_operator_approval_template_v6 as template_builder
from live_contentops import real_source_pack_operator_approval_validator_v6 as validator

TASK_LABEL = "TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE")


def make_approval_readiness_matrix() -> list[dict[str, Any]]:
    """Generates the approval readiness matrix mapping source entries."""
    requirements = [
        {"id": "req_67a5db6704f5", "type": "treasury_yield_series", "binding": True},
        {"id": "req_bfcb46cc38cc", "type": "yield_curve_calculation", "binding": True},
        {"id": "req_e6edaf8e7750", "type": "historical_volatility", "binding": True},
        {"id": "req_af610e135cf8", "type": "chart_table_data", "binding": False},
        {"id": "req_91a0125c71fd", "type": "limitations_disclaimer", "binding": False}
    ]

    matrix = []
    for req in requirements:
        matrix.append({
            "source_requirement_id": req["id"],
            "required_source_type": req["type"],
            "redacted_presence_available": True,
            "hash_presence_available": True,
            "claim_binding_present": req["binding"],
            "operator_approval_required": True,
            "operator_approval_present": False,
            "valid_for_draft_generation": False,
            "valid_for_publication": False,
            "blockers": [
                "operator_approval_missing",
                "approval_signature_missing",
                "source_pack_hash_approval_missing",
                "draft_generation_blocked",
                "publication_blocked",
                "dispatch_blocked"
            ]
        })
    return matrix


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Real Source Pack Operator Approval Gate Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate packets and templates
    gate_packet = {
        "approval_gate_status": "OPERATOR_APPROVAL_REQUIRED",
        "runtime_truth": False,
        "redacted_fixture_available": True,
        "redacted_fixture_validated": True,
        "operator_approval_created": False,
        "operator_signature_present": False,
        "source_pack_hash_present": False,
        "approved_source_requirement_ids": [],
        "approved_claim_ids": [],
        "valid_for_draft_generation": False,
        "valid_for_article_use": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "human_review_required": True,
        "kill_switch_active": True
    }

    template = template_builder.make_operator_approval_template()
    matrix = make_approval_readiness_matrix()

    # 2. Validation report
    validation_report, blockers = validator.validate_operator_approval_gate(
        gate_packet, template, matrix
    )

    # 3. Write files
    artifacts = {
        "source_pack_operator_approval_gate_packet.json": gate_packet,
        "source_pack_operator_approval_template.json": template,
        "source_pack_approval_readiness_matrix.json": matrix,
        "source_pack_operator_approval_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # Blocker report
    blocker_bullets = "\n".join(f"- `{b}`" for b in blockers)
    blocker_md = f"""# Operator Approval Blocker Report

- **Task Label**: {TASK_LABEL}
- **Active Blockers Count**: {len(blockers)}

## Active Blockers
{blocker_bullets}
"""
    Path(out_dir / "source_pack_approval_blocker_report.md").write_text(blocker_md, encoding="utf-8")

    # Runbook
    runbook_md = """# Operator Approval Gate Runbook

Establishes unapproved operator approval states and validation checks.

## Instructions
1. Operator sign-off is required to unblock draft generation.
2. Confirm the redacted approval templates are blank by default.
"""
    Path(out_dir / "source_pack_approval_runbook.md").write_text(runbook_md, encoding="utf-8")

    # Implementation report
    impl_md = f"""# Operator Approval Implementation Report

- **Task Label**: {TASK_LABEL}
- **Safety posture**: offline approval validator ready; no credentials or sign-offs are active.
"""
    Path(out_dir / "implementation_report.md").write_text(impl_md, encoding="utf-8")

    # Next task pointer
    next_task_pointer_md = """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_CANONICAL_DRAFT_FROM_APPROVED_REDACTED_SOURCE_PACK_DRY_RUN_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task_pointer_md, encoding="utf-8")

    print(json.dumps({
        "approval_gate_status": gate_packet["approval_gate_status"],
        "blockers": blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
