# Operator Next Action Runbook

Jim, follow these steps to resolve the blocked pipeline status:

## Step 1: Copy Operator Evidence Fixture
* Copy the file `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.blank.json` to `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json`.

## Step 2: Fill All 10 Evidence Slots
* Populate each required slot in `operator_evidence_fixture.json` with verified evidence.
* Ensure there are no placeholders remaining.

## Step 3: Run Validator Lane
* Execute the manual evidence validator script:
  `python live_contentops/manual_evidence_fixture_validator_v6.py`

## Step 4: Staging Gates Preflight
* Run the manual evidence to source preflight bridge script:
  `python live_contentops/manual_evidence_to_source_preflight_bridge_v6.py`
* Verify that validation and source preflight stages resolve to ready states. Only then can the pipeline move to the operator approval gate.

## Step 5: Operator Approval Signatures
* Real dispatch is separate and supervised. The approval gate does NOT trigger dispatch automatically.

> [!IMPORTANT]
> **PIPELINE IS BLOCKED**: The pipeline is not approval-ready and not dispatch-ready because the operator evidence fixture is empty or missing.
