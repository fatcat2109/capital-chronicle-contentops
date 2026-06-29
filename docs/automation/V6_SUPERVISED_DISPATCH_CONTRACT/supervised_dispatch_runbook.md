# V6 Supervised Dispatch Runbook

This runbook guides operators on dealing with a blocked supervised dispatch contract.

## Overview
The V6 Supervised Dispatch Contract protects target platforms by blocking dispatch until:
1. A valid outbox entry is created.
2. Credentials and endpoint allowlists stage properly.
3. Operator and Jim dispatch approvals are signed and verified.
4. The global kill-switch is verified open.

## Resolution
If this lane blocks:
- Confirm that the outbox entry contract validation report is clean.
- Verify that credentials and token proofs are fully staged in dry-run mode.
- Trigger explicit operator dispatch authorization flags.
