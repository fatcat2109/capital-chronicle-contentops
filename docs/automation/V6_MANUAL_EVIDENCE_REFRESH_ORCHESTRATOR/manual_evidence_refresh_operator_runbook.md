# Manual Evidence Refresh Operator Runbook

Jim, follow this workflow to refresh the evidence pipeline:

## Step-by-Step Instructions

1. **Step 1: Populate the console fixture**
   - Copy `operator_evidence_fixture.blank.json` to `operator_evidence_fixture.json` in `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/`.
   - Complete all 10 required factual slots (refer to `operator_evidence_fill_instructions.md` for guidance).

2. **Step 2: Run the Orchestrator**
   - Execute: `python live_contentops/manual_evidence_refresh_orchestrator_v6.py`

3. **Step 3: Review the Rollup**
   - Verify `manual_evidence_refresh_rollup.json` inside the orchestrator directory.
   - If `evidence_complete` is `true` and the rollup status is `PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL`, proceed to the operator approval gate lane.

4. **Step 4: Approval & Dispatch**
   - Signing approval does not trigger auto-dispatch. All publishing actions remain supervised.
