# V6 Exact Env-Key Membership Check Gate Operator Runbook - Membership Only No Value No Provider No Dispatch No Live

Membership check only. Exact key names only. No values. No .env. No credential values. No provider. No network. No browser. No executable request artifact. No endpoint, webhook, channel, account, token, or payload body. No public URL. No metrics. No dispatch. No live send. Future destination binding proof task separate.

## Operator Flow

1. Start with an accepted credential presence membership scaffold.
2. Confirm required key names are allowlisted.
3. If no explicit process-env membership flag is provided, do not check anything and remain blocked_not_checked.
4. If explicit process-env membership flag is provided, check only exact key-name membership.
5. Record required key names and present or missing booleans only.
6. Never read, print, log, store, hash, digest, redact, length-check, prefix-check, or suffix-check values.
7. Never iterate over all env vars.
8. Never use .env, dotenv, keyring, config secret files, provider APIs, network, or browser.

## Required Later

- Future destination binding proof task separate.
- Future dispatch execution task separate.
- Exact operator dispatch go separate.
- Redacted audit separate.
- Manual fallback and kill switch separate.

## Prohibited

- Credential value reads.
- Env value reads.
- Env iteration.
- Value length, prefix, suffix, hash, digest, or redacted fragment.
- .env reads.
- Provider calls.
- Network calls.
- Browser sessions.
- Executable request artifacts.
- Endpoint, webhook, channel, account, token, or payload body.
- Public URL or metrics.
- Publication readiness claim.
- Dispatch readiness claim.
- Live send.
- Financial advice or signal-service framing.