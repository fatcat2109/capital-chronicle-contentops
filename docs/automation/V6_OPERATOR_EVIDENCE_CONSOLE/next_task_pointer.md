# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`

Goal: Run the validator lane after the operator has supplied the manual evidence fixture in operator_evidence_fixture.json.

Workflow Steps:
1. Step 1: Jim copies/fills operator_evidence_fixture.json with verified evidence slots.
2. Step 2: Antigravity runs the manual evidence fixture validator lane after the filled fixture is available.
3. Step 3: The validator dynamically parses, scans for unsafe values, and refreshes the evidence/source submission status.
