# V6 Publication Audit Record Runbook

This runbook guides operators on dealing with a blocked publication audit record contract.

## Overview
The V6 Publication Audit Record Contract protects target platforms by blocking confirmation until:
1. Supervised dispatch succeeds.
2. A dispatch response proof exists.
3. Destination binding and payload hashes stage properly.
4. A public URL proof is retrieved.
5. Jim's audit review is completed.

## Resolution
If this lane blocks:
- Confirm that the supervised dispatch contract validation report is clean.
- Verify that destination bindings are fully verified.
- Confirm audit redaction policy is correctly staged in dry-run mode.
