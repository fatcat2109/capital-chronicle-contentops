# V6 Substack Manual Publication URL Audit Import Runbook

Use the canonical V5 dashboard only: `ui/contentops_v5/`.

## Purpose

This lane imports an operator-supplied Substack publication URL and manual publication metadata after a human operator published outside ContentOps. The URL is text evidence only and is not proof of reachability.

## Required operator review steps

1. Confirm the URL was supplied by the operator after manual publication outside ContentOps.
2. Confirm the imported URL audit packet binds the operator handoff packet ID/hash.
3. Confirm the bound export payload hash and approval/export evidence hash match the handoff packet.
4. Confirm `operator_supplied_url_verification_status = operator_supplied_not_network_verified`.
5. Confirm `url_network_verified = false` and `network_call_made = false`.

## Prohibited actions

- Do not open, browse, fetch, scrape, or network-verify the URL.
- Do not call Substack API.
- Do not publish live from ContentOps.
- Do not send, dispatch, schedule, approve, or enqueue a platform action.
- Do not read credentials, env values, browser session data, cookies, localStorage, tokens, provider keys, or webhook URLs.
- Do not use provider APIs or platform APIs.

## Required safety flags

- `url_network_verified = false`
- `substack_api_used = false`
- `provider_call_made = false`
- `network_call_made = false`
- `credential_read_made = false`
- `env_value_read_made = false`
- `browser_session_used = false`
- `live_publish_performed_by_contentops = false`
- `manual_publication_claim_operator_supplied = true`

The URL audit import packet is evidence for human review only. It is not ContentOps publishing proof and not approval to publish.
