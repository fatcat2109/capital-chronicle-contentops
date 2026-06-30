# V6 Payload Hash Preview and Approval Prep Operator Runbook - No Provider / No Send

Review-only runbook. No provider call. No live send. No approval granted now. No outbox/dispatch readiness.

## Operator Flow

1. Start with accepted draft inspection bundle and content production review bundle.
2. Generate platform payload previews and computed non-secret hashes.
3. Review generated previews and the approval ledger prep candidate.
4. Verify the candidate's hashes match the previews.
5. Forward the consolidated bundle to future operator approval tasks.

## Prohibited

- Provider calls.
- Web browsing.
- Env or `.env` reads.
- Credential values.
- Platform API calls.
- Browser sessions.
- Executable request artifacts.
- Public URLs or metrics.
- Publication approval claims.
- Personal financial guidance or alert-service framing.
