# TASK_CONTENTOPS_0152 — One-Platform Live Pilot Gate: Telegram Readiness (V0)

## Objective
Build a local-only One-Platform Live Pilot Gate for Telegram readiness. It
evaluates whether Telegram should be the first future live adapter candidate and
whether the repo has enough local safety rails to later ask Jim for Telegram
credential setup. It collects, requests, reads, validates, stores, prints, and uses
no real Telegram credential. It models why Telegram is the first candidate, future
operator prerequisites as placeholders only, future credential slot names only,
readiness gates that must pass before credential collection, safety dependencies
from 0148/0149/0150/0151, a go/no-go readiness state, and the explicit reason why
Telegram live posting is NOT ENABLED now.

This is a live-pilot readiness gate only. It is explicitly:
- NOT a Telegram bot setup / credential collection / API-key / OAuth / credential
  validation task
- NOT a live Telegram adapter / posting / scheduling task
- NOT a backend/server / provider-LLM / web/search/news/RSS/scraping task
- NOT a public-ready approval task

## No Telegram Token/Chat ID Needed From Operator Now
- platform API/key/token needed from operator now: no
- Telegram bot token/chat ID needed from operator now: no
- platform API/key/token needed from operator later: yes, only if a later explicitly
  approved Telegram credential setup or Telegram live-adapter pilot task is authorized
- Telegram bot token/chat ID needed from operator later: yes, only after explicit
  operator/ChatGPT GO

Credential setup remains FUTURE_ONLY, NOT_REQUESTED_NOW, NOT_READ_NOW,
NOT_VALIDATED_NOW, NEVER_COMMIT_SECRETS. The packet carries a required
`operator_warning_no_token_needed_now` and fails closed if missing.

## Implementation Note (naming deviation)
The accepted baseline already contains `live_contentops/telegram_live_pilot_gate.py`
and `tests/test_telegram_live_pilot_gate.py` from the accepted task 0083 (Telegram
Supervised Live Pilot Design Gate), imported by `telegram_live_pilot.py` and
`cli.py`. To avoid clobbering accepted code and breaking the baseline, this task's
new module and test use non-colliding names:
- `live_contentops/telegram_one_platform_live_pilot_gate.py`
- `tests/test_telegram_one_platform_live_pilot_gate.py`
The new schema `schemas/telegram_live_pilot_gate_packet.schema.json` and the CLI
command `pre-alpha-telegram-live-pilot-gate-summary` do not collide with anything in
the baseline and use the names specified by the task.

## Allowed Scope (built in this task)
- `schemas/telegram_live_pilot_gate_packet.schema.json`
- `live_contentops/telegram_one_platform_live_pilot_gate.py` — validator, secret
  detector, and `summary()`.
- `fixtures/telegram_live_pilot_gate/` — valid fixture + 19 negative fixtures.
- CLI command `pre-alpha-telegram-live-pilot-gate-summary`.
- Tests in `tests/test_telegram_one_platform_live_pilot_gate.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Telegram live adapter, Telegram API client, BotFather workflow, OAuth/bot setup.
- API key/token setup, credential loading, `.env` reads, OS env reads, credential
  validation. Backend/server, publish button, one-click publish-all, scheduler,
  live posting. Provider/LLM API calls, web/search/news/RSS fetch, scraping,
  market-data API. Newsletter/SMTP/CMS, autonomous replies/DMs. Public-ready final
  copy generation, public-ready approval system.

## Why Telegram Is Only a Candidate First Live Pilot
Telegram is modeled as the first candidate because it has a simple
single-destination posting shape suited to a supervised one-message dry-run
preview before any live action. This gate does NOT make Telegram live. It only
records that, given satisfied safety dependencies, the repo may later prepare a
separate Telegram credential setup gate.

## Future-Only Telegram Credential Slot Names
`future_telegram_credential_requirements` lists slot NAMES only:
TELEGRAM_BOT_TOKEN and TELEGRAM_TARGET_CHAT_ID, each with
`credential_requirement_status=future_only_not_requested`,
`operator_action_required_now=false`, `real_secret_value_present=false`,
`secret_value_placeholder_only=true`, and only safe placeholder markers
(FUTURE_ONLY_NOT_REQUESTED, PLACEHOLDER_SLOT_NAME_ONLY). No real or realistic token
values appear in the valid fixture, docs, or tests. The secret detector fails closed
on any realistic Telegram-token-shaped value.

## Future-Only Operator Prerequisite Checklist
`future_operator_prerequisite_checklist` models steps such as selecting a
destination, confirming it is a test channel/private group, creating the bot only
after explicit GO, collecting the token/chat id only after explicit GO, storing
credentials only in a future approved secret mechanism, never committing or pasting
secrets, and keeping the kill switch active until the live adapter gate passes.
Every item has `operator_action_required_now=false`; the gate fails closed if any
item requests action now.

## Official Telegram Docs Verification Is Required Later
This task does not browse. `future_official_docs_verification_gate` keeps
`official_docs_verification_completed_now=false`,
`official_docs_verification_required_later=true`, `docs_verified_by_repo_now=false`,
and `live_adapter_spec_may_not_claim_current_api_facts_now=true`. Claiming docs
verification done now fails closed.

## Relationship to 0148/0149/0150/0151
`dependency_gate_status` requires "satisfied" for publish_automation_readiness_0148,
dry_run_publish_batch_manifest_0149, credential_secret_policy_0150, and
redacted_publish_audit_log_0151. Missing or unsatisfied dependencies fail closed.
The kill-switch gate, redacted audit gate, dry-run manifest gate, credential policy
gate, and evidence guard gate are all linked by id and required.

## Gate Decision Meaning
A valid packet uses `gate_decision=ready_to_prepare_future_credential_setup_task`.
This means only that the next ChatGPT/Cline task MAY be a credential setup gate
prompt, if the operator explicitly says GO. It does NOT mean ready to post live,
ready to ask Jim for the token now, ready to call the Telegram API, or ready to
enable the adapter. Telegram live posting remains disabled now.

## Safety / North Star Guarantees
- No backend/server. No Telegram API. No repo web search/scraping/news/market-data.
- No provider/LLM API calls. No platform API/live posting/scheduler/OAuth.
- No newsletter/CMS/email provider action. No public-ready content generation.
- No credential/env reads. No OS-env reads. No credential validation.
- The kill-switch gate keeps `current_live_execution_status=disabled` and
  `live_execution_blocked_until_future_gate=true`.
- The safety policy blocks buy/sell/hold, long/short, target price, position sizing,
  model-prediction/signal language, alpha/artifact claims without real approval, and
  Bloomberg-replacement/AI-trading-bot/signal-service framing.
- This supports a future one-platform Telegram live pilot by proving local safety
  rails exist before any credential collection, amplifying macro thesis QA, data
  sufficiency, forecast readiness, and failure forensics.

## Capability Statement
No live posting, Telegram API, platform API, credential/env read, OS-env read, API
key/OAuth, credential validation, scheduler, scraping, web search,
news/RSS/market-data API, newsletter sending, CMS/email-provider integration, LLM
provider call, backend server, live adapter, publish button, one-button publish-all,
publish approval, or public-ready copy capability was added by this task. The layer
is a local, fail-closed Telegram one-platform live pilot readiness gate model
holding no real secrets.

