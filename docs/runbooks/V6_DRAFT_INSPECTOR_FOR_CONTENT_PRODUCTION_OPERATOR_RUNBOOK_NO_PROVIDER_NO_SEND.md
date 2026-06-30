# V6 Draft Inspector for Content Production Operator Runbook - No Provider / No Send

Review-only runbook. No provider call. No live send. No publication readiness.

## Operator Flow

1. Start from accepted content production review bundle.
2. Run local draft inspection.
3. Review blockers, warnings, missing evidence, citation status, and caveat preservation.
4. Use outputs only for future payload hash preview or approval ledger preparation.
5. Keep publication, dispatch, and live send blocked.

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
