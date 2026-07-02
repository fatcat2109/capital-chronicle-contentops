# V6 Operator Recovery to Explicit Live Scope Gate Source Candidate Runbook

This guide documents the preflight checks, parser rules, and safety posture for the live-scope gate and source normalization phase.

## Preflight Verification Checklist
1. **Assert inbox directory exists** and is write-restricted to local operator.
2. **Confirm credential presence states** report only key existence (`present`/`missing`), with zero secret/token value visible.
3. **Validate endpoint allowlist** conforms to the Discord webhook host and POST path shape.
4. **Ensure the normalized candidate** contains no placeholders or forbidden signal words.

## Intake Normalization Rules
* Place operator source drafts under `inbox/`.
* The parser will process JSON or MD extensions.
* Any compliance failure automatically marks the candidate with `safety_scan = failed` and lists reasons in `blocked_reasons`.
* A missing intake source yields `normalized_candidate_status = blocked_missing_operator_source_artifact`.

## Rollback & Stop Criteria
* **Env variable leakage**: Stop immediately if any token value is printed in logs.
* **Invalid Webhook schema**: Halt if host matches non-Discord domains.
* **Signal detection**: Reject drafts containing financial advice.

## Safety and Lockdown Checks
* All live dispatch and publishing triggers are disabled.
* The kill-switch parameter `kill_switch_active` is hardcoded to `true`.
