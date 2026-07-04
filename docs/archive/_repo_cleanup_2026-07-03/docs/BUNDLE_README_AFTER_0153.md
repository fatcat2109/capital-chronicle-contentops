# Bundle README (After 0153)

## What This Bundle Is
A secret-free Project Sources upload bundle reflecting the accepted Capital Chronicle
ContentOps baseline after task 0153 (HEAD a644f82). It consolidates current authority,
state, continuation prompt, and upload/replace guidance for ChatGPT Project Sources.

## What To Upload
- The 9 mandatory docs in project_sources_bundle_AFTER_0153/ (see
  UPLOAD_BUNDLE_MANIFEST_AFTER_0153.md).
- Optionally the 7 schema files for richer grounding.

## What NOT To Upload
- .env, the operator env file or its path, credential/token/chat-id values,
  screenshots/logs with secrets, old bundles (AFTER_0074), recovered_strategy_docs,
  raw vendor data, or generated caches.

## Current State
- Accepted through 0153. Full suite: 1254 passed, 28 skipped.
- All Content Studio and Publish Automation dry-run summaries pass.
- Telegram readiness gate decision: ready_to_prepare_future_credential_setup_task.
- No live posting, no platform/provider API, no credential reads. Kill-switch active.

## Next Task
TASK_CONTENTOPS_0155_TELEGRAM_REDACTED_CREDENTIAL_PRESENCE_CHECK_LOCAL_ONLY_V0
