# V6 LinkedIn Manual Export Runbook

Use the canonical V5 dashboard only: `ui/contentops_v5/`.

## Purpose

This lane prepares fixture-only LinkedIn manual copy text. No LinkedIn API, browser automation, credentials, env values, browser sessions, URL fetches, posting, reactions, comments, DMs, dispatch, scheduling, send, or approval actions are allowed.

## Required operator review steps

1. Confirm packet IDs and hashes bind to the prior LinkedIn evidence packet.
2. Confirm all publication URLs and metrics are operator-supplied fixture text/numbers only.
3. Confirm blocked controls include approve, send, publish, dispatch, and schedule.
4. Confirm `enabled_publish_send_dispatch_approve_controls = false`.

## Prohibited actions

- Do not use LinkedIn API.
- Do not use LinkedIn browser automation.
- Do not open, browse, fetch, scrape, or network-verify LinkedIn URLs.
- Do not publish, dispatch, send, approve, schedule, retry, DM, comment, like, or react.
- Do not read credentials, env values, browser session data, cookies, localStorage, sessionStorage, tokens, provider keys, or webhook URLs.

## Required safety flags

- `linkedin_api_used = false`
- `provider_call_made = false`
- `network_call_made = false`
- `credential_read_made = false`
- `env_value_read_made = false`
- `browser_session_used = false`
- `enabled_publish_send_dispatch_approve_controls = false`
- URL lanes: `url_network_verified = false`
- Metrics lanes: `metrics_network_verified = false` and `metrics_provider_api_used = false`

This evidence is local deterministic fixture/operator evidence only. It is not proof of public reachability and not ContentOps publishing proof.
