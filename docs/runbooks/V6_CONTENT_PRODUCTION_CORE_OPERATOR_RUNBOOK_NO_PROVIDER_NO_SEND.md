# V6 Content Production Core Operator Runbook - No Provider / No Send

Review-only runbook. No provider call. No live send. No publication readiness.

## Operator Flow

1. Provide safe operator intent with no secrets and no market-call framing.
2. Generate local review bundle.
3. Inspect research gaps, caveats, limitations, and disclosure.
4. Keep output blocked from publication and dispatch.
5. Use later separate task for draft inspection or payload hash approval.

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
