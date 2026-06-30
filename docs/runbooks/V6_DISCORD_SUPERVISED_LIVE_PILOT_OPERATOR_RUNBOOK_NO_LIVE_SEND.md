# V6 Discord Supervised Live Pilot Operator Runbook - No Live Send

Purpose: operator review guide for local-only adapter scaffold.

## Hard Boundary

- Do not send Discord messages from this runbook.
- Do not read env or `.env` values.
- Do not read webhook values, tokens, channel IDs, headers, methods, paths, or bodies.
- Do not open browser sessions.
- Do not create executable HTTP artifacts, curl commands, fetch snippets, or provider requests.
- Do not claim publication readiness or live dispatch approval.

## Operator Steps

1. Review adapter packet locally.
2. Confirm `live_execution_enabled_now` is `false`.
3. Confirm `dispatch_allowed` is `false`.
4. Confirm `publication_ready` is `false`.
5. Confirm `future_live_execution_blockers` remain present.
6. Stop. Wait for separate explicit future live execution task.

## Required Future Gates

- Exact operator confirmation.
- Credential-presence membership-only proof.
- Destination binding.
- Payload hash revalidation.
- Kill switch.
- Redacted audit.
- Manual fallback.
