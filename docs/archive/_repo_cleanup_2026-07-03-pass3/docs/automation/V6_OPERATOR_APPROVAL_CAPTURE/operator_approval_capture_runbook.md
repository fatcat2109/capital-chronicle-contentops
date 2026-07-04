# Operator Approval Capture Runbook

Follow these steps to run the approval capture lane and generate your signature locally:

## Signature Generation Steps

1. Run the preview command to inspect the exact payload title, body, and hash:
   ```powershell
   python -m live_contentops.operator_approval_capture_v6 --preview
   ```
2. Confirm the payload hash matches `4bcbbf4eeab1bdfa2f3f94b4dbb042877c67efdb515f7feecaac5ffa3a2e71ff`.
3. If correct, execute the approval command with your operator ID:
   ```powershell
   python -m live_contentops.operator_approval_capture_v6 --approve --operator-id JIM_OPERATOR --write-signature
   ```
4. Re-run validation to verify that the local signature is bound and valid.
