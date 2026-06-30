# V6 Outbox Preparation Gate Operator Runbook - No Provider No Dispatch No Live

Outbox preparation only. No provider. No dispatch. No live send. No executable request. No public URL or metrics. Future dispatch gate required.

## Operator Flow

1. Start with accepted exact Jim approval intake bundle.
2. Validate approval intake status and hard false side-effect flags.
3. Generate local non-executable outbox records bound to approved preview IDs and payload hashes.
4. Do not include payload body, endpoint, webhook, token, channel, account, cookie, session, browser profile, env value, credential value, public URL, or metrics.
5. Do not dispatch, publish, or live send.

## Required Later

- Destination binding.
- Credential handle.
- Separate future dispatch gate.
- Separate future live-send gate if ever authorized.

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