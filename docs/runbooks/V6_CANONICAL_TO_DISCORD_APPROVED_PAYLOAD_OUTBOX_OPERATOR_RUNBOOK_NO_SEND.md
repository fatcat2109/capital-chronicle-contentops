# V6 Canonical to Discord Approved Payload Outbox Operator Runbook - No Send

No live send occurs from this runbook. Future separate explicit live task required.

## Operator Use

1. Review canonical content reference outside this no-send bridge.
2. Confirm payload hash only; do not include raw live payload body here.
3. Keep destination binding absent in this task.
4. Keep credential handling symbolic only.
5. Produce local non-executable outbox packet.

## Required Future Live Task

- Exact operator GO phrase.
- Exact payload preview and hash.
- Destination binding.
- Credential presence membership-only proof for `DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK`.
- Payload hash revalidation.
- Kill switch.
- Redacted audit.
- Single request budget.
- Zero hidden retry.
- Stop on uncertainty.
- Manual fallback.

## Prohibited Here

- Env or `.env` reads.
- Credential values.
- Provider calls.
- Browser sessions.
- Executable request snippets.
- Public URLs or metrics.
- Publication readiness claims.
- Financial advice or signal-service framing.
