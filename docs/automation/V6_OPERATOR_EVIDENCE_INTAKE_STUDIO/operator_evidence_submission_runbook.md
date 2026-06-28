# Operator Evidence Submission Runbook

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
