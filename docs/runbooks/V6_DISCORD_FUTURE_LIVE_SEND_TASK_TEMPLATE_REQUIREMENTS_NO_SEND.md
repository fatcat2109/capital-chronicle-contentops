# V6 Discord Future Live Send Task Template Requirements - No Send

No live send occurs from this template. Separate explicit live task required.

## Required Future Task Contents

- Exact operator GO phrase.
- Destination binding declaration.
- Credential-presence membership-only check for `DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK`.
- Payload hash revalidation.
- Kill switch confirmation.
- Redacted audit writing.
- Single request budget.
- Zero hidden retry.
- Stop on uncertainty.

## Prohibited In This Template

- Env or `.env` reads.
- Credential values.
- Provider calls.
- Browser sessions.
- Executable request artifacts or request snippets.
- Public URLs or metrics.
- Publication readiness claims.
