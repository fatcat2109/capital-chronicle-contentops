# TASK_CONTENTOPS_0153 — Telegram Credential Setup Operator Guide and Env-Slot Stub (V0)

## Objective
Create a safe Telegram credential setup operator guide and placeholder-only env-slot
stub/checklist for future Telegram live adapter work, preparing the operator-side
credential setup path after 0152's Telegram readiness gate. This task receives,
reads, prints, stores, commits, validates, and uses no real Telegram credentials. It
models an operator guide, approved future env slot names, a placeholder-only env-slot
stub/template, no-secret evidence rules, a redacted credential handling checklist, a
future credential presence-check task boundary, a future Telegram live adapter task
boundary, and the explicit warning that real values stay local only and never appear
in ChatGPT/Cline/repo/evidence.

This is a Telegram credential setup guide and env-slot stub task only. It is NOT a
credential loading / validation / Telegram API / live adapter / posting / scheduling
/ backend-server / provider-LLM / public-ready approval task.

## Operator Local Env File Handling
The operator referenced a local env file out-of-band. This task did NOT open, read,
parse, load, or echo it. It is referred to only as
`OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND`. The real env file path is not
committed into docs, fixtures, schema, or tests. The repo/Cline must not read it in
this task. A future explicitly approved redacted credential presence-check task may
check only slot presence, never values.

## No Token/Chat ID Needed By Cline/ChatGPT Now
- platform API/key/token needed from operator now: no, not for Cline/ChatGPT/repo/evidence
- Telegram bot token/chat ID needed from operator now: no
- Telegram bot token/chat ID may exist locally already: possible, but not read in this task
- Telegram bot token/chat ID needed later: yes, only by a future explicitly approved
  local credential presence-check or live-adapter task
- Cline must not ask the operator to paste credentials, and must not load, read, or
  validate credentials.

Credential setup status: OPERATOR_LOCAL_ONLY, NOT_REQUESTED_IN_CHAT,
NOT_READ_BY_CLINE_NOW, NOT_VALIDATED_NOW, NEVER_COMMIT_SECRETS, REDACT_VALUES_ALWAYS.

## Allowed Scope (built in this task)
- `schemas/telegram_credential_setup_operator_guide_packet.schema.json`
- `live_contentops/telegram_credential_setup_operator_guide.py` — validator, secret
  detector (token-shaped and chat-id-shaped value detection), and `summary()`.
- `fixtures/telegram_credential_setup_operator_guide/` — valid + 14 negative fixtures.
- `docs/examples/telegram_credentials.env.example` — placeholder-only template.
- CLI command `pre-alpha-telegram-credential-setup-guide-summary`.
- Tests in `tests/test_telegram_credential_setup_operator_guide.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Telegram live adapter, Telegram API client, BotFather automation, OAuth/bot setup.
- API key/token loading, credential parsing, `.env` reads, operator env file reads,
  OS env reads, credential validation. Backend/server, publish button, one-click
  publish-all, scheduler, live posting. Provider/LLM API, web/search/news/RSS fetch,
  scraping, market-data API. Newsletter/SMTP/CMS, autonomous replies/DMs. Public-ready
  final copy generation, public-ready approval system.

## Future-Only Telegram Credential Slot Names
`credential_slot_policy` lists slot NAMES only: TELEGRAM_BOT_TOKEN and
TELEGRAM_TARGET_CHAT_ID, each with `value_status=placeholder_only`,
`real_value_present=false`, `operator_action_required_now=false`,
`read_allowed_now=false`, `validation_allowed_now=false`, and only safe placeholder
markers (REDACTED_NEVER_COMMIT, PLACEHOLDER_SLOT_NAME_ONLY). Optional future slots
TELEGRAM_DRY_RUN_TARGET_LABEL and TELEGRAM_ADAPTER_ENABLED are documented as
names-only too. The validator fails closed on any realistic Telegram-token-shaped
value or realistic `-100…` chat-id-shaped value in any field.

## Placeholder-Only Env Slot Template
`docs/examples/telegram_credentials.env.example` contains only placeholder values:
`TELEGRAM_BOT_TOKEN=REDACTED_NEVER_COMMIT` and
`TELEGRAM_TARGET_CHAT_ID=REDACTED_NEVER_COMMIT`. It is an EXAMPLE only; the operator
copies it to a LOCAL env file out-of-band. No real `.env` is created or modified. No
realistic credential values appear.

## Operator Safety Rules
- Never paste the token/chat ID into ChatGPT, Cline, the repo, fixtures, docs, tests,
  or evidence (`never_paste_secrets_warning`, required and fails closed if missing).
- Never commit the env file or include token/chat ID in evidence.
- Rotate the token out-of-band if it was ever printed, logged, committed, or exposed
  (`rotation_warning`, required and fails closed if missing).

## No-Secret Evidence Policy
Evidence may include slot names, boolean states, redaction status, future task
labels, and no-secret scan status, plus the generic statement
`OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND`. Evidence must NOT include real token
values, partial token snippets, real chat IDs, real env file contents, the real local
env path, screenshots/logs with secrets, OAuth callback values, platform API
responses, or BotFather output containing token values.

## Future Credential Presence-Check Boundary
`future_presence_check_boundary` defines a future task that may check ONLY whether the
required env slots are present. It must not print values, must redact values, must not
validate against Telegram unless a later live gate explicitly permits, must not post,
and must return boolean/redacted evidence only — blocked until explicit GO.

## Future Telegram Live Adapter Boundary
`future_live_adapter_boundary` keeps `live_adapter_enabled_now=false`,
`one_platform_only_first=true`, and remains blocked until the presence-check, official
docs verification, and kill-switch gates pass.

## Relationship to Prior Tasks
- 0152 Telegram live pilot gate: this guide is the operator-side credential setup path
  that 0152's `ready_to_prepare_future_credential_setup_task` decision pointed to.
- 0150 credential/secret policy: this guide reuses the future-only env-slot and
  redaction/never-commit principles.
- 0151 redacted audit/evidence guard: this guide reuses no-secret evidence rules and
  rotation guidance.

## Safety / North Star Guarantees
- No `.env` reads, no operator env file reads, no OS-env reads, no credential
  validation, no Telegram API call. No platform API/live posting/scheduler/OAuth.
- No backend/server. No repo web search/scraping/news/market-data API. No provider/LLM
  API calls. No newsletter/CMS/email provider action. No public-ready content
  generation. No publish approval system. No one-button publish-all.
- Official Telegram docs verification is required later and not completed now.
- The safety policy blocks buy/sell/hold, long/short, target price, position sizing,
  model-prediction/signal language, and alpha/artifact claims without real approval.
- This supports a future one-platform Telegram live pilot by preparing the operator
  credential path with fail-closed safety, amplifying macro thesis QA, data
  sufficiency, forecast readiness, and failure forensics.

## Capability Statement
No live/API/credential/scheduler/scraping capability was added by this task. The layer
is a local, fail-closed Telegram credential setup operator guide and placeholder-only
env-slot stub holding no real secrets and reading no credentials.

