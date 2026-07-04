# Project Sources Delete/Replace Guide (After 0153)

## Step 1 — Review Existing Project Sources
Open your ChatGPT Project Sources list. Decide whether to keep historical context
(older AFTER_0137 docs) or replace with the current AFTER_0153 baseline only.

## Step 2 — Delete or Archive Old Sources
If replacing, delete or archive the older bundle docs:
- Earlier CURRENT_STATE_SUMMARY / PROJECT_SOURCE_EXPORT / NEW_CHAT_CONTINUATION docs
- Earlier UPLOAD_BUNDLE_MANIFEST / REPLACEMENT_INDEX / DELETE_REPLACE_GUIDE docs
- Earlier IDE_CLI_QUICKSTART / BUNDLE_README / BUNDLE_FILE_LIST files

Keeping them is optional and only for historical context; the AFTER_0153 set is the
current authority.

## Step 3 — Upload The New AFTER_0153 Bundle Files
Upload the 9 mandatory docs from project_sources_bundle_AFTER_0153/ (see
UPLOAD_BUNDLE_MANIFEST_AFTER_0153.md for order). Optionally upload the 7 schema files
for richer grounding.

## Step 4 — Verify The Project Sources List
Confirm Project Sources contains only the intended current files. Remove anything
unexpected.

## Step 5 — Do Not Upload Secrets
- Do NOT upload .env.
- Do NOT upload the real operator env file or its path.
- Do NOT upload screenshots/logs containing secrets.
- Do NOT upload token/chat ID values.
- Do NOT upload credential files.

## Step 6 — Open A New Chat
Open a new ChatGPT Project chat and paste the contents of
NEW_CHAT_CONTINUATION_AFTER_0153.md to resume with the correct authority and next task.

## Reminder
Credential values remain local only and out-of-band. The next task
(TASK_CONTENTOPS_0155_TELEGRAM_REDACTED_CREDENTIAL_PRESENCE_CHECK_LOCAL_ONLY_V0) reads
only an approved local env source and returns boolean/redacted evidence — no values, no
Telegram API call.
