# Next Task Pointer: Discord Operator Review UI/CLI or Future Live Authorization Design

## Recommended Next Task

Build a non-live operator review UI/CLI for Discord ledger and outbox entries.

## Scope Recommendation

- Display ledger records and outbox entries by payload hash and binding IDs.
- Let operator mark dry-run review status only.
- Keep `valid_for_dispatch=false`.
- Keep webhook URL hydration disabled.
- Keep network calls disabled.
- Keep Discord bot deferred.

## Future Live Task Boundary

Only a separate explicit live authorization task should introduce webhook URL hydration or dispatch. That future task must require fresh approval, exact hash revalidation, kill switch checks, and post-request redacted audit design.
