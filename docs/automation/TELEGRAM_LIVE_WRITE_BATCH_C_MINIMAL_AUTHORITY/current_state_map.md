# Current State Map — Batch C

## Baseline

- Starting HEAD: `30144c7bc83068fc4d84328fb66209d70a611f81`
- Branch: `master`
- Repo: `A:\Capital Chronicle\tools\cc-live-contentops`
- Task: `TASK_CONTENTOPS_TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY_AND_SUPERVISED_SENDMESSAGE_PILOT_V0`

## Authority

- Platform: Telegram only
- Read-only probes: `getMe`, `getChat`
- Live write: exactly one `sendMessage`
- No retry
- No second send
- No raw secret persistence

## Protected Paths

No modification intended for V2, V3, `ui/institutional_shell`, `docs/design_references`, `docs/browser_qa`, or Capital Chronicle ingestion repo.

## Unrelated Working Tree

Pre-existing unrelated changes remain excluded from Batch C commit.
