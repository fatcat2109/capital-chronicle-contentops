# V6 Dispatch Gate Scaffold Operator Runbook - No Provider No Dispatch No Live

Dispatch gate scaffold only. No provider. No dispatch. No live send. No executable request. No public URL or metrics. Destination binding later. Credential handle later. Future dispatch execution task separate.

## Operator Flow

1. Start with accepted outbox preparation gate bundle.
2. Validate every local non-executable outbox record.
3. Create dispatch review records for future destination binding and credential handle review.
4. Require payload hash revalidation later and exact operator dispatch go later.
5. Do not dispatch, publish, call provider, or live send.

## Required Later

- Destination binding later.
- Credential handle later.
- Payload hash revalidation later.
- Exact operator dispatch go later.
- Redacted audit later.
- Manual fallback and kill switch later.
- Future dispatch execution task separate.

## Prohibited

- Provider calls.
- Env or `.env` reads.
- Credential value reads.
- Network calls.
- Browser sessions.
- Executable request artifacts.
- Public URL or metrics creation.
- Dispatch readiness claim.
- Publication readiness claim.
- Live send.
- Financial advice or signal-service framing.