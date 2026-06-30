# V6 Unified Capability Env Readiness Contract

This packet is the Fast Ship presence-only readiness model for Discord, Telegram, Substack, AI provider, browser operator, and manual fallback lanes.

## Safety

- Reads process env and/or local `.env` key names only when task-scoped.
- Emits key names and presence booleans only.
- Never emits raw values, full env lines, value length, prefix, suffix, hash, digest, or redacted fragments.
- Missing `.env` is informational and not a blocker.
- Provider/live writes require a separate scoped live pilot or supervised dispatch task.

## Statuses

- `unavailable`: required key names are absent.
- `configured_for_dry_run`: enough local capability exists for dry-run, browser, AI, or manual work.
- `configured_for_supervised_live_scope_candidate`: key-name presence supports a future explicitly scoped supervised live candidate task.

## Next Product Lane

Recommended next task: `TASK_CONTENTOPS_V6_DISCORD_DRY_RUN_OUTBOX_AND_OPERATOR_APPROVAL_SPINE_HEAVY_BATCH_V0`.
