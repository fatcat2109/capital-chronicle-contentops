# Operator Platform Quickstart

Fast commands for proven platform operations. All examples use placeholders. Do not paste real tokens, webhook URLs, chat IDs, cookies, `localStorage`, `sessionStorage`, browser profile secrets, or private draft URLs into docs or chat.

## Safe Status Summary

| Platform | Status | Boundary |
|---|---|---|
| Discord | Proven one-shot supervised send | No autonomous dispatch, queue, scheduler, or retry loop |
| Telegram | Proven one-shot supervised `sendMessage` | No autonomous dispatch, queue, scheduler, or retry loop |
| Substack draft | Proven supervised CDP draft compose | Draft only; no publish, schedule, or email send |
| Substack publish | Not proven and hard-locked | Current confirmation phrase intentionally blocks before CDP publish |

## Discord

Dry-run:

```powershell
python -m live_contentops.discord_operator_send_cli `
  --message "<EXACT_OPERATOR_APPROVED_MESSAGE>" `
  --target announcements `
  --task-id <TASK_ID> `
  --output docs/automation/V6_DISCORD_OPERATOR_SEND_COMMAND/<TASK_ID>_dry_run_evidence.json
```

Exact one-shot execute:

```powershell
python -m live_contentops.discord_operator_send_cli `
  --message "<EXACT_OPERATOR_APPROVED_MESSAGE>" `
  --target announcements `
  --task-id <TASK_ID> `
  --execute `
  --output docs/automation/V6_DISCORD_OPERATOR_SEND_COMMAND/<TASK_ID>_send_evidence.json
```

## Telegram

Dry-run:

```powershell
python -m live_contentops.telegram_operator_send_cli `
  --message "<EXACT_OPERATOR_APPROVED_MESSAGE>" `
  --task-id <TASK_ID> `
  --output docs/automation/V6_TELEGRAM_OPERATOR_SEND_COMMAND/<TASK_ID>_dry_run_evidence.json
```

Exact one-shot execute:

```powershell
python -m live_contentops.telegram_operator_send_cli `
  --message "<EXACT_OPERATOR_APPROVED_MESSAGE>" `
  --task-id <TASK_ID> `
  --execute `
  --output docs/automation/V6_TELEGRAM_OPERATOR_SEND_COMMAND/<TASK_ID>_send_evidence.json
```

## Substack Draft

Dry-run:

```powershell
python -m live_contentops.substack_operator_draft_cli `
  --title "<DRAFT_TITLE>" `
  --body "<DRAFT_BODY>" `
  --task-id <TASK_ID> `
  --output docs/automation/V6_SUBSTACK_OPERATOR_DRAFT_COMMAND/<TASK_ID>_dry_run_evidence.json
```

Exact draft execute:

```powershell
python -m live_contentops.substack_operator_draft_cli `
  --title "<DRAFT_TITLE>" `
  --body "<DRAFT_BODY>" `
  --task-id <TASK_ID> `
  --execute `
  --output docs/automation/V6_SUBSTACK_OPERATOR_DRAFT_COMMAND/<TASK_ID>_draft_evidence.json
```

## Substack Publish Preflight

Dry-run only:

```powershell
python -m live_contentops.substack_operator_publish_preflight_cli `
  --draft-url "<PLACEHOLDER_DRAFT_URL>" `
  --task-id <TASK_ID> `
  --output docs/automation/V6_SUBSTACK_OPERATOR_DRAFT_COMMAND/<TASK_ID>_publish_preflight_dry_run_evidence.json
```

Do not use `--execute` for publish preflight unless a future task explicitly authorizes a no-publish live preflight.

## Substack Publish CLI Hard Lock

Do not live publish. Publish is not proven and remains hard-locked.

Current phrase:

```text
PUBLISH_BOUNDARY_NOT_YET_APPROVED
```

This phrase is intentionally a lock, not approval. Even with `--allow-publication --execute --i-understand-this-can-publish --operator-confirmation PUBLISH_BOUNDARY_NOT_YET_APPROVED`, the CLI must block before CDP publish with:

```text
blocker=publish_boundary_not_approved
publish_attempted=false
request_count_attempted=0
```

Only a future exact task may change this boundary.