# V6 Substack Manual Export Operator Handoff Runbook

Use the canonical V5 dashboard only: `ui/contentops_v5/`.

## Purpose

This packet packages the canonical article source, Substack manual export payload, approval/export evidence packet, checklist, blockers, hashes, and manual-copy instructions for operator review.

## Required operator review steps

1. Open canonical V5 Manual Export and inspect the handoff packet ID and handoff hash.
2. Confirm the article source packet and source article hash match the packet.
3. Confirm the Substack manual export packet ID and payload hash match the packet.
4. Confirm the approval/export evidence packet ID and hash match the packet.
5. Confirm every checklist item remains `pending_review` until a human operator reviews it.
6. If separately approved outside this packet, manually copy the payload into Substack outside ContentOps.

## Prohibited actions

- Do not call Substack API.
- Do not publish live.
- Do not send, dispatch, schedule, or enqueue a platform action.
- Do not read credentials, env values, browser session data, cookies, localStorage, tokens, provider keys, or webhook URLs.
- Do not use provider APIs or platform APIs.

## Required safety flags

- `manual_copy_only = true`
- `live_publish_allowed = false`
- `live_publish_performed = false`
- `substack_api_used = false`
- `provider_call_made = false`
- `network_call_made = false`
- `credential_read_made = false`
- `env_value_read_made = false`
- `browser_session_used = false`
- `sample_scope = sample_fixture_only`

The handoff packet is evidence for human review only. It is not approval to publish.
