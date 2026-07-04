# TASK_CONTENTOPS_0150 — Credential and Secret Policy for Publish Adapters (V0)

## Objective
Build a local-only Credential and Secret Policy for future publish adapters. It
defines how future platform credentials, API keys, OAuth tokens, bot tokens, page
tokens, refresh tokens, and related secrets must be named, handled, redacted,
structurally validated, and protected before any live adapter exists. The repo
must not request, read, store, validate, print, or use any real credential. The
policy models future env-slot naming, per-platform credential requirement
placeholders, redaction, never-commit-secrets, no-secret-value fixtures, no .env
read, future operator setup gate, future credential validation gate, audit
evidence requirements, and why real API/key/token setup is NOT NEEDED NOW.

This is a credential policy task only. It is explicitly:
- NOT a credential collection task
- NOT an API-key setup task
- NOT an OAuth setup task
- NOT a credential validation task
- NOT a live platform adapter task
- NOT a posting/scheduling/backend/provider/web/search/scraping task
- NOT a public-ready approval task

## No Platform API/Key/Token Needed From Operator Now
- platform API/key/token needed from operator now: no
- platform API/key/token needed from operator later: yes, only in a later
  explicitly approved live-adapter or credential-setup gate

Credential setup is marked FUTURE_ONLY, NOT_REQUESTED_NOW, NOT_READ_NOW,
NOT_VALIDATED_NOW, NEVER_COMMIT_SECRETS. The packet carries
`operator_warning_no_keys_needed_now` and fails closed if that warning is missing.

## Allowed Scope (built in this task)
- `schemas/publish_adapter_credential_secret_policy_packet.schema.json`
- `live_contentops/publish_adapter_credential_secret_policy.py` — validator,
  secret-value detector, and `summary()`.
- `fixtures/publish_adapter_credential_secret_policy/` — valid fixture + negatives.
- CLI command `pre-alpha-publish-adapter-credential-secret-policy-summary`.
- Tests in `tests/test_publish_adapter_credential_secret_policy.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Live platform adapter, platform API client, OAuth flow, API key/token setup.
- Credential loading, `.env` reads, OS environment reads, credential validation.
- Backend/server, publish button, one-click publish-all, scheduler, live posting.
- Provider/LLM API calls, web/search/news/RSS fetch, scraping, market-data API.
- Newsletter sender/SMTP/CMS integration, autonomous replies/DMs.
- Public-ready final copy generation, public-ready approval system.

## Future-Only Env Slot Naming Policy
`future_env_slot_policy` lists slot NAMES only (e.g. TELEGRAM_BOT_TOKEN,
LINKEDIN_CLIENT_ID, X_API_KEY, SUBSTACK_OR_NEWSLETTER_API_TOKEN), with
`slot_names_only_no_values=true` and `values_future_only=true`. Only the safe
placeholder markers FUTURE_ONLY_NOT_REQUESTED, REDACTED_NEVER_COMMIT, and
PLACEHOLDER_SLOT_NAME_ONLY may appear in any value position.

## Per-Platform Credential Requirement Placeholders
Each platform entry (telegram, linkedin, x, manual_external_posting in the valid
fixture; registry set telegram/linkedin/x/threads/substack_or_newsletter/
manual_external_posting allowed) carries
`credential_requirement_status=future_only_not_requested`,
`operator_action_required_now=false`, `secret_value_placeholder_only=true`,
`real_secret_value_present=false`, `redaction_required=true`,
`never_commit_secrets=true`, and `requires_future_official_docs_verification=true`.
Any unsupported platform target fails closed.

## No Real Secrets In Repo
`real_secret_values_allowed_in_repo` and `real_secret_values_present` are false and
fail closed if true. The module includes a secret-value detector that scans the
entire packet for private keys, AWS/GitHub/Slack tokens, telegram bot-token
shapes, Google OAuth tokens, bearer tokens, and JWTs; any match fails closed.

## No .env Reads, No OS Environment Reads, No Credential Validation Now
`no_env_read_policy` keeps `env_read_allowed_now`, `os_env_read_allowed_now`, and
`dotenv_read_allowed_now` false. `future_credential_validation_gate` keeps
`credential_validation_enabled_now=false` with shape/presence checks deferred to a
later explicit GO. The repo reads no `.env`, no OS environment values, and runs no
credential validation.

## Redaction Policy
`redaction_policy` requires redacting all credential values and never printing,
logging, committing, or including secrets in evidence, screenshots, or pastes into
ChatGPT/Cline. Evidence may include slot names only.

## Never-Commit-Secrets Policy
`never_commit_secrets_policy` requires `never_commit_secrets_required=true` and a
future `.gitignore` for secrets. Packet-level `never_commit_secrets_required` fails
closed if false.

## Evidence Packet Rules For Secrets
Secrets are never placed in evidence packets, logs, screenshots, or chat. Only env
slot NAMES (never values) may appear. This task's evidence contains no real or
realistic secret values, confirmed by the secret scan below.

## Future Operator Setup — Only After Explicit GO
`future_operator_setup_gate` models that the operator gathers credentials only
after explicit ChatGPT/operator GO, places them only in an approved local secret
storage mechanism defined by a future task, has the repo verify presence/shape
only (never print values), blocks the live adapter if redaction/audit/kill-switch
gates fail, and limits the first live adapter to one platform only.

## Relationship to 0148 and 0149
This policy links the 0148 publish automation readiness packet and the 0149
dry-run publish batch manifest by id reference. It supplies the credential/secret
contract that the readiness future_task_sequence requires before any live adapter
or approved-only publish-all gate.

## Safety / North Star Guarantees
- No backend/server. No repo web search/scraping/news API/market-data API.
- No provider/LLM API calls. No platform API/live posting/scheduler.
- No newsletter/CMS/email provider action. No public-ready content generation.
- No credential/env reads. No OAuth flow. No credential validation.
- This supports future approved-only publish automation by defining how secrets
  must be handled before any live capability exists. It amplifies macro thesis QA,
  data sufficiency, forecast readiness, and failure forensics, and never frames
  Capital Chronicle as a Bloomberg replacement, AI trading bot, signal service,
  execution system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, OS-env read, API key/OAuth,
credential validation, scheduler, scraping, web search, news/RSS/market-data API,
newsletter sending, CMS/email-provider integration, LLM provider call, backend
server, live adapter, publish button, one-button publish-all, publish approval, or
public-ready copy capability was added by this task. The layer is a local,
fail-closed credential and secret policy model holding no real secrets.

