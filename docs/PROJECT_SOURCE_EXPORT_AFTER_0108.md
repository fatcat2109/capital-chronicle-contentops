# Project Source Export - After TASK_CONTENTOPS_0108

LOCAL ONLY | DOCS/CONTEXT ONLY | NO UPLOAD PERFORMED BY THIS REPO

This document defines what is safe to upload to ChatGPT Project Sources after
0108, and what must be excluded. It supersedes the
0073/0074/0099/0101 export guidance.

## Purpose
Give a future ChatGPT/IDE session clean, minimal, repo-grounded context without
stale or unsafe artifacts.

## Safe to upload (context docs)
- CURRENT_STATE_SUMMARY_AFTER_0108.md
- NEW_CHAT_CONTINUATION_AFTER_0108.md
- PROJECT_SOURCE_EXPORT_AFTER_0108.md
- UPLOAD_BUNDLE_MANIFEST_AFTER_0108.md
- IDE_CLI_QUICKSTART_AFTER_0108.md
- PRE_ALPHA_CONTENT_ENGINE_AFTER_0095.md
- PRE_ALPHA_PROMPT_PACK_AND_STYLE_PROFILE_AFTER_0096.md
- PRE_ALPHA_DRAFT_RENDERER_AND_REVIEW_QUEUE_AFTER_0097.md
- PRE_ALPHA_MANUAL_REVIEW_WORKFLOW_AFTER_0098.md
- PRE_ALPHA_MANUAL_EXPORT_PACKETS_AND_CONTENT_LEDGER_AFTER_0099.md
- PRE_ALPHA_END_TO_END_LOCAL_DEMO_PACKET_AFTER_0101.md
- PRE_ALPHA_CONTENT_SEED_LIBRARY_AND_EDITORIAL_CALENDAR_AFTER_0103.md
- PRE_ALPHA_OPERATOR_DASHBOARD_PACKET_AFTER_0104.md
- PRE_ALPHA_EDITORIAL_BATCH_REVIEW_PACKET_AFTER_0105.md
- PRE_ALPHA_MANUAL_DECISION_BATCH_PACKET_AFTER_0106.md
- PRE_ALPHA_MANUAL_EXPORT_BATCH_PACKET_AFTER_0107.md
- PRE_ALPHA_MANUAL_PUBLISH_RECORD_PACKET_AFTER_0108.md

## Safe to upload (schemas, pre_alpha pipeline contracts)
- schemas/pre_alpha_content_seed.schema.json
- schemas/pre_alpha_content_seed_library.schema.json
- schemas/pre_alpha_draft_candidate.schema.json
- schemas/pre_alpha_editorial_packet.schema.json
- schemas/pre_alpha_editorial_calendar_plan.schema.json
- schemas/pre_alpha_prompt_pack.schema.json
- schemas/pre_alpha_style_profile.schema.json
- schemas/pre_alpha_editorial_rubric.schema.json
- schemas/pre_alpha_review_queue_item.schema.json
- schemas/pre_alpha_rendered_draft_packet.schema.json
- schemas/pre_alpha_manual_review_decision.schema.json
- schemas/pre_alpha_approval_packet.schema.json
- schemas/pre_alpha_manual_export_packet.schema.json
- schemas/pre_alpha_content_ledger_entry.schema.json
- schemas/pre_alpha_operator_dashboard_packet.schema.json
- schemas/pre_alpha_editorial_batch_review_packet.schema.json
- schemas/pre_alpha_manual_decision_batch_packet.schema.json
- schemas/pre_alpha_manual_export_batch_packet.schema.json
- schemas/pre_alpha_manual_publish_record_packet.schema.json

## MUST EXCLUDE
- `.env`, `.env.*`
- credentials, secrets, tokens, channel IDs
- raw Telegram responses or any raw API responses
- raw logs containing secrets
- `project_sources_bundle_AFTER_0074/` (stale prior bundle)
- vendor data / raw data
- caches: `__pycache__/`, `.pytest_cache/`
- `.git/`
- binary artifacts and large generated files
- any file containing a real token or private channel ID

## Note on stale bundles
The AFTER_0108 bundle supersedes AFTER_0073, AFTER_0074, AFTER_0099, and
AFTER_0101. Remove older bundles from Project Sources to avoid stale-authority
drift.
