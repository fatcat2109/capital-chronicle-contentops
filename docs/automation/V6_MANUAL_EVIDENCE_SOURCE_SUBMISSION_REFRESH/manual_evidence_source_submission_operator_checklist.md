# Operator Evidence Submission Checklist

Jim, please complete this checklist before proceeding:

## Action Checklist

- [ ] **Step 1**: Copy `operator_evidence_fixture.blank.json` to `operator_evidence_fixture.json` inside the `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/` folder.
- [ ] **Step 2**: Populate all 10 required slots with verified facts.
- [ ] **Step 3**: Verify that **NO** restricted items are included:
  - No secrets, tokens, cookies, or auth headers.
  - No webhook URLs or channel integration paths.
  - No local folders (`AppData`, `Temp`, user directories).
  - No fake URLs or fabricated citations.
  - No fake market numbers or business performance statistics.
  - No trading signals, stock advice, or buy/sell calls.
- [ ] **Step 4**: Run the source submission refresh command.
- [ ] **Step 5**: Review the output refresh packet and blocker rollup.
- [ ] **Step 6**: Rerun or adjust if any validation checks fail.
- [ ] **Step 7**: Proceed to approval gate signing task ONLY when `evidence_complete=true` and `source_preflight_ready=true`.
