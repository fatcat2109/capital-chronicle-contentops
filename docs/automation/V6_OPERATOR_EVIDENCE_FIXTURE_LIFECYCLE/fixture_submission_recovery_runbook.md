# Operator Evidence Submission Recovery Runbook

Jim, use this runbook to diagnose and recover from fixture-validation issues:

## Recovery Scenarios

1. **Error: Missing Fixture File**
   - *Issue*: `operator_evidence_fixture.json` does not exist in `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/`.
   - *Action*: Copy `operator_evidence_fixture.blank.json` to that path.

2. **Error: Placeholder Values Detected**
   - *Issue*: One or more fields contains `"PLACEHOLDER_REPLACE_BEFORE_REVIEW"` or `"REPLACE_"`.
   - *Action*: Replace them with actual, verified factual details.

3. **Error: Restricted / Unsafe Keywords Detected**
   - *Issue*: Contains words like `webhook`, `token`, `cookie`, `secret`, `password`, or paths like `AppData`, `Temp`.
   - *Action*: Remove sensitive variables or local folder tags.

4. **Error: Financial Advice or Signal Indicators**
   - *Issue*: Contains phrases like `buy`, `sell`, `hold`, `price target`, or position guidance.
   - *Action*: Rephrase content to remain strictly factual and educational.

5. **Error: Validator / Preflight Bridge Mismatch**
   - *Issue*: The source preflight bridge indicates missing upstream validator packet.
   - *Action*: Re-run the manual validator script first before executing the preflight bridge.

> [!IMPORTANT]
> **No Dispatch Authorization**: Correcting validation or lifecycle errors does not authorize approval signatures or dispatch. Dispatch remains separate and supervised.
