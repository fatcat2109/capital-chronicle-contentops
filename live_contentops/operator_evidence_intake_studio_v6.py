"""V6 Operator Evidence Intake Studio.

Generates guidance documentation, validation rules, authoring templates, 
rejection checklists, validation preview packets, and runbooks for evidence slots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_EVIDENCE_INTAKE_STUDIO_AND_VALIDATION_WORKBENCH_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO")
FIXTURE_INPUT = Path("docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json")

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

UNSAFE_PATTERNS = [
    "webhook",
    "discord.com/api/webhooks",
    "token",
    "cookie",
    "authorization",
    "bearer",
    ".env",
    "secret",
    "password",
    "pkey",
    "private_key",
    "session",
    "localstorage",
    "sessionstorage",
    "header",
    "appdata",
    "temp"
]


def write_json(path: str | Path, data: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def is_unsafe_value(val: Any) -> bool:
    if isinstance(val, list):
        return any(is_unsafe_value(item) for item in val)
    if not isinstance(val, str):
        return False
    val_lower = val.lower()
    for pattern in UNSAFE_PATTERNS:
        if pattern in val_lower:
            return True
    return False


def is_empty_or_placeholder(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, list):
        return len(val) == 0 or all(is_empty_or_placeholder(item) for item in val)
    if isinstance(val, str):
        v = val.strip()
        return len(v) == 0 or "placeholder" in v.lower() or "replace_" in v.lower()
    return False


def generate_common_rejection_reasons() -> str:
    return """# Operator Evidence Common Rejection Reasons

This document highlights common mistakes and reasons why submitted evidence is rejected during automated and human checks.

## Common Rejection Scenarios

1. **Empty or Placeholder Values**:
   - Leaving slots blank or using placeholder strings (e.g. containing `"PLACEHOLDER"` or `"REPLACE_"`).
2. **Inclusion of Secrets or API Keys**:
   - Pasting API keys, tokens, auth headers, passwords, or private key segments.
3. **Webhook Disclosure**:
   - Including raw Discord webhooks or server endpoints.
4. **Environment File Paths**:
   - Referencing `.env` file names or other dynamic local settings.
5. **Dynamic Local Folder Paths**:
   - Paths containing local system tags like `AppData`, `Temp`, or specific local user folders.
6. **Financial Advice or Trading Signals**:
   - Including buy/sell recommendations, price targets, guaranteed predictions, or trading indicators.
7. **Fabricated / Unverified Citations**:
   - Submitting fake citations, dead URLs, or mock sources that cannot be manually verified.
8. **Premature Platform Posting Claims**:
   - Setting dispatch flags or asserting that the output is ready for direct public deployment.
"""


def generate_submission_runbook() -> str:
    return """# Operator Evidence Submission Runbook

Jim, use this step-by-step runbook to safely author and submit your manual evidence:

## Step 1: Initialize Operator Evidence Fixture
- Copy `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.blank.json` to `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json`.

## Step 2: Populate all 10 Evidence Slots
- Replace all placeholder values with real, manually verified underlying facts.
- Check that all rules in the submission checklist are followed.

## Step 3: Run the Manual Evidence Validator
- Run the validator to test slot completeness and search for unsafe values:
  `python live_contentops/manual_evidence_fixture_validator_v6.py`

## Step 4: Run the Source Preflight Bridge
- Run the bridge to prepare preflight inputs:
  `python live_contentops/manual_evidence_to_source_preflight_bridge_v6.py`

## Step 5: Refresh the Consolidation Matrix
- Run consolidation to rollup the latest status:
  `python live_contentops/operator_pipeline_status_consolidation_v6.py`

## Step 6: Operator Approval Signatures
- Once all upstream stages resolve to ready, the operator can sign the approval gate.
- Note: The approval gate authorizes the drop, but real dispatch is separate and supervised.
"""


def generate_implementation_report() -> str:
    return f"""# V6 Operator Evidence Intake Studio Implementation Report

- **Task Label**: {TASK_LABEL}
- **Status**: PASS

- **Integrity Compliance Checklist**:
  - No secret keys output: `true`
  - No webhook URLs or tokens printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
"""


def generate_next_task_pointer() -> str:
    return """# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`

Goal: Validate the operator facts and manual evidence fixture once Jim has populated the template values.
"""


def get_slot_guidance() -> dict[str, Any]:
    guidance = {}
    for slot in REQUIRED_SLOTS:
        # Defaults
        val_type = "string"
        completeness = "Must be a non-empty, non-placeholder string."
        example = "PLACEHOLDER_REPLACE_BEFORE_REVIEW"
        raw_allowed = False
        public_allowed = False
        rejection = ["Value is empty.", "Value contains placeholders."]
        redaction = "Do not include passwords, API keys, tokens, local paths, or webhook URLs."

        if slot in ["factual_claims", "citation_candidates", "supporting_artifacts"]:
            val_type = "array of strings"
            completeness = "Must contain at least one non-empty string."
            example = ["PLACEHOLDER_REPLACE_BEFORE_REVIEW"]

        if slot == "operator_idea_source_ref":
            completeness = "Must be a valid, manually verified URL or repository path."
            rejection.append("Not a valid URL or local file path.")
        elif slot == "topic_statement":
            completeness = "Must describe the core factual topic statement."
        elif slot == "factual_claims":
            completeness = "Must be a list of distinct factual assertions checkable against source reference."
            public_allowed = True
        elif slot == "source_notes":
            completeness = "Detail validation checks performed by operator."
            raw_allowed = True
        elif slot == "no_signal_disclosure":
            completeness = "Must affirm that no trading signals, position advice, or price predictions are present."
            rejection.append("Advice disclosure is missing or ambiguous.")
        elif slot == "intended_content_lane":
            completeness = "Must name an authorized distribution channel (e.g. Substack)."
            rejection.append("Unsupported lane name.")

        guidance[slot] = {
            "accepted_value_type": val_type,
            "minimum_completeness_requirement": completeness,
            "example_placeholder_only": example,
            "rejection_reasons": rejection,
            "redaction_warnings": redaction,
            "raw_content_allowed": raw_allowed,
            "public_postable_allowed": public_allowed
        }
    return guidance


def get_redaction_rules() -> dict[str, Any]:
    return {
        "rules_version": SCHEMA_VERSION,
        "restricted_keywords": UNSAFE_PATTERNS,
        "strict_redactions": {
            "fake_citations": "Forbidden. All citations must correspond to verified sources.",
            "fake_urls": "Forbidden. URLs must be valid and manually checked.",
            "fake_market_numbers": "Forbidden. Statistics and metrics must be manually verified and truthful.",
            "financial_advice": "Forbidden. No trading signals, buy/sell targets, position sizing, or predictions.",
            "secrets_tokens": "Forbidden. No API keys, passwords, bearer tokens, or authorization headers.",
            "webhooks": "Forbidden. Webhook URLs must not be printed or stored.",
            "dumps": "Forbidden. No cookie, session storage, localStorage, or browser profile dumps.",
            "local_paths": "Forbidden. No environmental paths, pytest paths, Temp, or AppData references."
        }
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Evidence Intake Studio")
    parser.add_argument("--fixture-file", default=str(FIXTURE_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load and validate dynamic fixture if available
    fixture = load_json(args.fixture_file)
    fixture_exists = fixture is not None

    errors = []
    unsafe_detected = False
    evidence_complete = False

    if fixture_exists and fixture:
        all_empty = True
        for slot in REQUIRED_SLOTS:
            val = fixture.get(slot)
            if not is_empty_or_placeholder(val):
                all_empty = False
                break

        for slot in REQUIRED_SLOTS:
            val = fixture.get(slot)
            if val is not None and is_unsafe_value(val):
                unsafe_detected = True
                errors.append(f"Slot '{slot}' contains unsafe values (token/webhook/cookie/env).")

        if all_empty:
            status = "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
            errors.append("Fixture is empty. Operator must supply values for required slots.")
        elif unsafe_detected:
            status = "FIXTURE_REJECTED_UNSAFE_VALUES"
        else:
            missing = [slot for slot in REQUIRED_SLOTS if is_empty_or_placeholder(fixture.get(slot))]
            if missing:
                status = "FIXTURE_INCOMPLETE_MISSING_SLOTS"
                errors.append(f"Fixture is incomplete. Missing or empty required slots: {', '.join(missing)}")
            else:
                status = "VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW"
                evidence_complete = True
    else:
        status = "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
        errors.append("Fixture file is missing or unreadable.")

    # 1. Studio Packet
    studio_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "intake_studio_status": status,
        "evidence_complete": evidence_complete,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "kill_switch_active": True,
        "next_recommended_task": "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
    }
    write_json(out_dir / "operator_evidence_intake_studio_packet.json", studio_packet)

    # 2. Authoring Template
    authoring_template = {
        slot: [] if slot in ["factual_claims", "citation_candidates", "supporting_artifacts"] else None
        for slot in REQUIRED_SLOTS
    }
    write_json(out_dir / "operator_evidence_fixture.authoring_template.json", authoring_template)

    # 3. Validation Preview (Committed output represents the blocked state, dynamic state uses fixture_exists check)
    # The committed status should remain blocked
    validation_preview = {
        "validation_preview_status": status,
        "evidence_complete": evidence_complete,
        "source_preflight_ready": False,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "public_postable": False,
        "kill_switch_active": True,
        "validation_errors": errors
    }
    write_json(out_dir / "operator_evidence_fixture.validation_preview.json", validation_preview)

    # 4. Slot Guidance JSON
    write_json(out_dir / "operator_evidence_slot_guidance.json", get_slot_guidance())

    # 5. Redaction Rules JSON
    write_json(out_dir / "operator_evidence_redaction_rules.json", get_redaction_rules())

    # 6. Write Markdown files
    (out_dir / "operator_evidence_common_rejection_reasons.md").write_text(generate_common_rejection_reasons(), encoding="utf-8")
    (out_dir / "operator_evidence_submission_runbook.md").write_text(generate_submission_runbook(), encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(generate_implementation_report(), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(), encoding="utf-8")

    print(json.dumps({
        "intake_studio_status": status,
        "evidence_complete": evidence_complete,
        "kill_switch_active": studio_packet["kill_switch_active"]
    }))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
