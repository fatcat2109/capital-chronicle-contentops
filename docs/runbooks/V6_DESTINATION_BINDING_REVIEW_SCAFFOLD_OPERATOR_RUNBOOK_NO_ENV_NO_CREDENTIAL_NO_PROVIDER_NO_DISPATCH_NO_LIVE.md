# V6 Destination Binding Review Scaffold Operator Runbook - No Env No Credential No Provider No Dispatch No Live

Destination binding review scaffold only. No env read. No .env read. No credential value read. No provider. No network. No browser. No dispatch. No live send. No executable request. No endpoint, webhook, channel, account, token, payload body, public URL, or metrics. Credential presence membership task later. Dispatch execution task separate.

## Operator Flow

1. Start with an accepted dispatch gate scaffold bundle.
2. Validate every dispatch review record.
3. Create symbolic destination binding placeholder IDs only.
4. Create symbolic credential handle placeholder IDs only.
5. Require payload hash revalidation later and exact operator dispatch go later.
6. Do not bind a destination, hydrate credentials, check credential presence, dispatch, publish, call provider, or live send.

## Required Later

- Credential presence membership task later.
- Destination binding proof later.
- Credential handle membership proof later.
- Payload hash revalidation later.
- Exact operator dispatch go later.
- Redacted audit later.
- Manual fallback and kill switch later.
- Dispatch execution task separate.

## Prohibited

- Env or .env reads.
- Credential value reads.
- Credential presence checks in this task.
- Provider calls.
- Network calls.
- Browser sessions.
- Executable request artifacts.
- Endpoint, webhook, channel, account, token, or payload body.
- Public URL or metrics creation.
- Dispatch readiness claim.
- Publication readiness claim.
- Live send.
- Financial advice or signal-service framing.
