# CLI Reference — V6 Operator Approval Capture

The `operator_approval_capture_v6` CLI allows operators to preview the exact payload details and deterministically sign the payload hash.

## Usage

```powershell
# Display help and preview the current payload hash
python -m live_contentops.operator_approval_capture_v6 --help

# Preview payload body and details
python -m live_contentops.operator_approval_capture_v6 --preview

# Interactively or non-interactively approve and save the signature locally
python -m live_contentops.operator_approval_capture_v6 --approve --operator-id JIM_OPERATOR --write-signature
```

## Security Invariant

This tool runs locally and writes to gitignored files only. It has no capabilities to post to external APIs or dispatch webhooks.
