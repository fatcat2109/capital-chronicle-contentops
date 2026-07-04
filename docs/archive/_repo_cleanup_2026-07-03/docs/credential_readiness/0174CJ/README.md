# Pre-Launch Telegram Credential Readiness (0174CJ)

`TASK_CONTENTOPS_0174CJ_PRELAUNCH_TELEGRAM_CREDENTIAL_READINESS_DRY_RUN_AND_REDACTION_HARNESS_V0`

## Purpose

A scoped, local-only harness that answers a narrow pre-launch question: is the
repo-local environment *shaped* such that a **future, separately-gated** Telegram
live validation task could proceed?

It is allowed to read a repo-local `.env` / `.env.local` source (or, only when
explicitly selected, the process environment) for **presence + redacted shape
classification** of the Telegram credential slots. It emits only redacted
readiness classes and never calls the Telegram API.

Module: `live_contentops/prelaunch_telegram_credential_readiness.py`

## What it answers

- Is a Telegram bot token present?
- Does it look like a Telegram bot token *shape*?
- Is a Telegram target chat ID present?
- Does it look like an integer / private chat ID / channel handle *shape*?
- Is the repo ready for a future, separate Telegram live-gate validation task?

## What it must NOT answer (and cannot)

- What is the token? What is the chat ID?
- What is the token length?
- What are the first/last characters (prefix/suffix)?
- What hash/digest identifies the secret?
- Can we post live now? (No — that is a separate gate.)

## How to run

```
python -m live_contentops.cli telegram-credential-readiness
```

or, equivalently:

```
python -m live_contentops.prelaunch_telegram_credential_readiness
```

Optional process-env fallback (only used if no local env file exists):

```
python -m live_contentops.cli telegram-credential-readiness --process-env
```

The command prints **only** the redacted JSON summary below — no raw token, no
raw chat ID, no prefix/suffix, no length, no hash/digest, no filesystem path, and
no unknown env key names.

## What is allowed

- Read repo-root `.env`, then `.env.local`, for presence + shape only.
- Optionally read approved process-env slots (`--process-env`) if no file exists.
- Emit redacted shape classes and locked policy booleans.

## What remains blocked

- No Telegram Bot API call (no `getMe`, no `sendMessage`).
- No network / provider / platform / SDK imports in the harness.
- No posting, scheduling, scraping, replies/DMs, or metrics fetching.
- No rendering of credentials in the browser/UI.
- No committing `.env` / `.env.local` or any raw output.

## Sample redacted output shape

```json
{
  "task_label": "TASK_CONTENTOPS_0174CJ_PRELAUNCH_TELEGRAM_CREDENTIAL_READINESS_DRY_RUN_AND_REDACTION_HARNESS_V0",
  "check_mode": "local_redacted_credential_readiness_check_only",
  "candidate_platform_id": "telegram",
  "env_source_read_attempted": true,
  "env_source_read_succeeded": true,
  "env_source_missing_or_unavailable": false,
  "env_source_label": "REPO_LOCAL_DOTENV_REDACTED",
  "telegram_bot_token_present": true,
  "telegram_bot_token_shape_class": "present_redacted_telegram_bot_token_like",
  "telegram_target_chat_id_present": true,
  "telegram_target_chat_id_shape_class": "present_redacted_integer_like",
  "readiness_status": "ready_for_future_live_gate_validation",
  "live_api_allowed_now": false,
  "telegram_api_called": false,
  "live_posting_allowed_now": false,
  "scheduler_allowed_now": false,
  "credential_values_printed": false,
  "token_snippet_reported": false,
  "chat_id_snippet_reported": false,
  "exact_length_reported": false,
  "hash_or_digest_reported": false,
  "raw_path_reported": false,
  "manual_review_required": true,
  "future_live_gate_required": true
}
```

### Readiness status values

| Status | Meaning |
| --- | --- |
| `blocked_missing_env_source` | No `.env` / `.env.local` (or process-env slot) found. |
| `blocked_missing_required_slot` | Token or chat ID slot absent / empty. |
| `review_shape_nonclassifiable` | Slots present but shape needs human review (e.g. channel handle, malformed token). |
| `ready_for_future_live_gate_validation` | Token-like + integer chat ID present; ready for the *next, separate* live gate. |

### Shape classes

- Token: `absent`, `present_redacted_telegram_bot_token_like`,
  `present_redacted_empty_or_whitespace`, `present_redacted_nonempty_nonclassifiable`
- Chat ID: `absent`, `present_redacted_integer_like`,
  `present_redacted_channel_handle_like`, `present_redacted_empty_or_whitespace`,
  `present_redacted_nonempty_nonclassifiable`

## No live API / no posting / no scheduler

Credential readiness does **not** imply network, provider, or platform
permission. Presence/shape readiness and live API validation are separate gates.
This harness is fail-closed: every live/posting/scheduler flag is a hard `false`
literal, and `manual_review_required` / `future_live_gate_required` are hard
`true`.

## Next live gate after this task

`TASK_CONTENTOPS_0174CK_TELEGRAM_LIVE_GATE_READ_ONLY_BOT_ID_VALIDATION_V0`
— a separate, explicitly authorized read-only bot-identity validation gate.
