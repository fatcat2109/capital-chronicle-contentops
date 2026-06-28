# V6 Supervised Dispatch Readiness Revalidation Runbook

This runbook guides Jim and automated validators to perform the revalidation checks before final publishing is approved.

## 1. Upstream Signature and Binding Checks
- Ensure the local operator signature binding is verified under `V6_OPERATOR_APPROVAL_SIGNATURE_BINDING`.
- Destination binding must confirm review-only state is mapped correctly.

## 2. Safety Contamination Scan
- Under no circumstances should webhook URLs, host patterns, token values, session parameters, local system directories, or fake prediction metrics be included in committed outputs.
- Run the revalidation script to perform scanning checks.
