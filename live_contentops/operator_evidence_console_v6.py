"""V6 Operator Evidence Console Lane.

Generates the interactive operator evidence console scaffolding to let Jim fill
the required 10 slots without touching generated source files directly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_ADAPTER_RECONCILIATION_FIELD_NORMALIZATION_AND_OPERATOR_EVIDENCE_CONSOLE_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE")

REQUIRED_SLOTS = [
    "operator_idea_source_ref",
    "topic_statement",
    "factual_claims",
    "source_notes",
    "citation_candidates",
    "supporting_artifacts",
    "limitation_notes",
    "no_signal_disclosure",
    "intended_content_lane",
    "intended_canonical_article_angle"
]


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate_fill_instructions() -> str:
    return """# Operator Evidence Fill Instructions

Jim, please use this console folder to submit verified evidence.

## Core Workflow Steps
* **Step 1**: Jim copies the file `operator_evidence_fixture.blank.json` to `operator_evidence_fixture.json` and fills it with verified manual evidence.
* **Step 2**: Antigravity runs the validator lane after the filled fixture is available.
* **Step 3**: The validator scans the inputs and refreshes evidence/source submission status.

Note: Filling out the fixture does NOT automatically trigger approval, outbox posting, payload hash generation, or live dispatch.

## Slots to Complete
* `operator_idea_source_ref`: Reference link or path to the original source.
* `topic_statement`: Short summary statement of facts.
* `factual_claims`: List of assertions made.
* `source_notes`: Notes detailing manual grounding checks.
* `citation_candidates`: List of citations for verification.
* `supporting_artifacts`: Local screenshot or documents.
* `limitation_notes`: Caveats or bounds of current claims.
* `no_signal_disclosure`: Affirmation that no financial signals or advice are present.
* `intended_content_lane`: Distribution target (e.g. Substack).
* `intended_canonical_article_angle`: Rationale or framing.
"""


def generate_validation_checklist() -> str:
    return """# Operator Evidence Validation Checklist

Before submitting, check the following guidelines:
- [ ] No raw secrets or API keys are written.
- [ ] No webhook URLs are pasted.
- [ ] No configuration environment file paths are referenced.
- [ ] No cookie, session, or token strings are included.
- [ ] No fake market numbers or fabricated citations are used.
"""


def generate_next_task_pointer() -> str:
    return """# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`

Goal: Run the validator lane after the operator has supplied the manual evidence fixture in operator_evidence_fixture.json.

Workflow Steps:
1. Step 1: Jim copies/fills operator_evidence_fixture.json with verified evidence slots.
2. Step 2: Antigravity runs the manual evidence fixture validator lane after the filled fixture is available.
3. Step 3: The validator dynamically parses, scans for unsafe values, and refreshes the evidence/source submission status.
"""


def generate_implementation_report() -> str:
    return f"""# V6 Operator Evidence Console Implementation Report

- **Task Label**: {TASK_LABEL}
- **Status**: PASS

- **Compliance Rules**:
  - No secrets or credentials printed: `true`
  - No webhook URLs printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
  - No browser/CDP session launched: `true`
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Evidence Console Scaffold")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Blank fixture template
    blank_fixture = {
        slot: [] if slot in ["factual_claims", "citation_candidates", "supporting_artifacts"] else None
        for slot in REQUIRED_SLOTS
    }
    write_json(out_dir / "operator_evidence_fixture.blank.json", blank_fixture)

    # 2. Safe placeholder example
    example_fixture = {
        slot: ["PLACEHOLDER_REPLACE_BEFORE_REVIEW"] if slot in ["factual_claims", "citation_candidates", "supporting_artifacts"] else "PLACEHOLDER_REPLACE_BEFORE_REVIEW"
        for slot in REQUIRED_SLOTS
    }
    write_json(out_dir / "operator_evidence_fixture.example.safe_placeholder.json", example_fixture)

    # 3. Console packet
    hasher = hashlib.sha256(b"operator_evidence_console")
    console_packet_id = f"console_{hasher.hexdigest()[:12]}"
    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "operator_evidence_console_packet_id": console_packet_id,
        "evidence_complete": False,
        "operator_idea_source_ref_resolved": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "kill_switch_active": True,
        "public_postable": False,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "operator_next_action": "Jim fills operator_evidence_fixture.json with verified evidence.",
        "validator_next_task": "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0",
        "next_recommended_task": "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0",
        "next_task_pointer_is_soft": True
    }
    write_json(out_dir / "operator_evidence_console_packet.json", packet)

    # 4. Write text documents
    (out_dir / "operator_evidence_fill_instructions.md").write_text(generate_fill_instructions(), encoding="utf-8")
    (out_dir / "operator_evidence_validation_checklist.md").write_text(generate_validation_checklist(), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(), encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(generate_implementation_report(), encoding="utf-8")

    print(json.dumps({
        "operator_evidence_console_packet_id": console_packet_id,
        "evidence_complete": packet["evidence_complete"],
        "kill_switch_active": packet["kill_switch_active"]
    }))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
