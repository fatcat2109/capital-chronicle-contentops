# 0174UE/UF/UG Telegram Read-Only Identity Pilot

Task: `TASK_CONTENTOPS_0174UE_UF_UG_TELEGRAM_OPERATOR_OWNED_CREDENTIAL_AND_READ_ONLY_IDENTITY_PILOT_BATCH_V0`

Model: `TELEGRAM_READ_ONLY_IDENTITY_PILOT_0174UE_UF_UG` version `0174UE_UF_UG_TELEGRAM_READ_ONLY_IDENTITY_PILOT_V1`

Baseline commit: `824352c99eecf9c1e463250a5226d4bb68ba6c71`

## Role

This batch is the FIRST controlled, live-capable read-only Telegram step. It is NOT a posting task: there is NO `sendMessage` anywhere. The ONLY platform method recognised is the read-only identity method `getMe`. By default the pilot is `dry_run_only` and performs NO env read and NO network.

## 0174UE Request plan + credential boundary

`build_identity_pilot_request_plan(...)` validates host (`https://api.telegram.org`), method (`getMe` only), budget (exactly 1), and timeout (`10`s), and blocks these forbidden methods: `getUpdates`, `sendMessage`, `setWebhook`. `hydrate_telegram_credential_handle(...)` reads ONLY the environment variable `CAPITAL_CHRONICLE_TELEGRAM_BOT_TOKEN`, and ONLY when `operator_live_read_only_enabled=True`. It returns a REDACTED credential proof (fingerprint + length class); the raw token is NEVER returned, logged, or persisted. Missing variable => blocked `credential_missing`; suspicious shape => redacted reason only.

## 0174UF Controlled read-only execution

`execute_read_only_identity_pilot(...)` performs NO network unless `operator_live_read_only_enabled=True` AND the credential proof is ok. With live disabled it returns `identity_pilot_not_run_dry_run_only`. With live enabled it performs EXACTLY one `getMe` request through an injectable transport (a mock in tests; a lazy stdlib `urllib` transport otherwise) -- NO retry, NO scheduler, NO webhook, NO polling. Provider error and network exception both fail closed to redacted proofs.

## 0174UG Redacted proof + immutable audit

`build_redacted_identity_proof(...)` classifies ok / provider status code / bot identity + username PRESENCE only, and stores request + response checksums + a timestamp placeholder class -- never the raw body, raw bot id, raw username, raw URL, headers, or cookies. `build_identity_pilot_audit_packet(...)` records the operator gate id, credential handle id, plan checksum, identity-proof checksum, and budget used, and stores no token / raw response / raw URL / header / cookie.

## Hard invariants

  * `first_controlled_live_read_only_step_not_posting`
  * `no_sendmessage_anywhere`
  * `no_posting_or_platform_write`
  * `no_getupdates_or_setwebhook`
  * `no_webhook_or_polling`
  * `no_auto_retry`
  * `no_scheduler`
  * `no_autonomous_reply_or_dm`
  * `only_get_me_method_allowed`
  * `only_telegram_api_host_allowed`
  * `request_budget_is_exactly_one`
  * `explicit_short_timeout`
  * `default_mode_is_dry_run_only_no_env_no_network`
  * `live_requires_explicit_operator_flag`
  * `reads_only_one_explicit_env_var_name`
  * `no_arbitrary_env_scan`
  * `no_dotenv_or_credential_file_read`
  * `token_never_returned_logged_or_persisted`
  * `credential_stored_as_fingerprint_and_length_class_only`
  * `suspicious_token_shape_is_redacted_reason_not_value`
  * `response_redacted_to_classes_and_checksums_only`
  * `no_raw_response_body_bot_id_username_url_header_cookie_stored`
  * `audit_stores_no_token_raw_response_url_header_cookie`
  * `redaction_runs_on_every_emitted_artifact`
  * `no_financial_advice_or_signal_framing`
  * `missing_or_unsafe_input_blocks`

Packet checksum: `3bf2a08520eff6dc4ee33ddc3c0a014e3ff448db9b9d6264c2ee0f0f1fc7e3aa`
