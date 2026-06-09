# Upload Bundle Manifest - After TASK_CONTENTOPS_0101

LOCAL ONLY | SAFE CONTEXT DOCS/SCHEMAS ONLY | NO SECRETS

Bundle name: `project_sources_bundle_AFTER_0101`
Generated location (external, untracked):
`A:\Capital Chronicle\tools\project_sources_bundle_AFTER_0101`

This manifest lists the exact files gathered for ChatGPT Project Sources upload.
Every entry is a markdown context doc or a JSON schema. None contain secrets,
tokens, channel IDs, raw logs, vendor data, or public-postable content.

## Included - context docs
| File | authority_role | safety |
| --- | --- | --- |
| CURRENT_STATE_SUMMARY_AFTER_0101.md | CURRENT_CONTEXT | SAFE |
| NEW_CHAT_CONTINUATION_AFTER_0101.md | CURRENT_CONTINUATION_CONTEXT | SAFE |
| PROJECT_SOURCE_EXPORT_AFTER_0101.md | EXPORT_GUIDANCE | SAFE |
| UPLOAD_BUNDLE_MANIFEST_AFTER_0101.md | MANIFEST | SAFE |
| IDE_CLI_QUICKSTART_AFTER_0101.md | OPERATIONAL_QUICKSTART | SAFE |
| PRE_ALPHA_CONTENT_ENGINE_AFTER_0095.md | ADVISORY_CONTEXT | SAFE |
| PRE_ALPHA_PROMPT_PACK_AND_STYLE_PROFILE_AFTER_0096.md | ADVISORY_CONTEXT | SAFE |
| PRE_ALPHA_DRAFT_RENDERER_AND_REVIEW_QUEUE_AFTER_0097.md | ADVISORY_CONTEXT | SAFE |
| PRE_ALPHA_MANUAL_REVIEW_WORKFLOW_AFTER_0098.md | ADVISORY_CONTEXT | SAFE |
| PRE_ALPHA_MANUAL_EXPORT_PACKETS_AND_CONTENT_LEDGER_AFTER_0099.md | ADVISORY_CONTEXT | SAFE |
| PRE_ALPHA_END_TO_END_LOCAL_DEMO_PACKET_AFTER_0101.md | ADVISORY_CONTEXT | SAFE |

## Included - schemas (pre_alpha pipeline contracts)
| File | safety |
| --- | --- |
| pre_alpha_content_seed.schema.json | SAFE |
| pre_alpha_draft_candidate.schema.json | SAFE |
| pre_alpha_editorial_packet.schema.json | SAFE |
| pre_alpha_prompt_pack.schema.json | SAFE |
| pre_alpha_style_profile.schema.json | SAFE |
| pre_alpha_editorial_rubric.schema.json | SAFE |
| pre_alpha_review_queue_item.schema.json | SAFE |
| pre_alpha_rendered_draft_packet.schema.json | SAFE |
| pre_alpha_manual_review_decision.schema.json | SAFE |
| pre_alpha_approval_packet.schema.json | SAFE |
| pre_alpha_manual_export_packet.schema.json | SAFE |
| pre_alpha_content_ledger_entry.schema.json | SAFE |

## Per-file safety attributes (all entries)
- contains_secrets = false
- contains_live_ids = false
- contains_raw_logs = false
- contains_provider_outputs = false
- contains_public_postable_content = false

## Excluded categories (must never be uploaded)
- `.env`, `.env.*`, credentials, secrets, tokens, channel IDs
- raw Telegram/API responses, raw logs with secrets
- `project_sources_bundle_AFTER_0074/` (stale)
- vendor/raw data, caches, `__pycache__/`, `.pytest_cache/`, `.git/`
- binary artifacts, large generated files
- any file with a real token or private channel ID

## Upload instruction
Upload only the AFTER_0101 bundle files into a new ChatGPT Project Sources set.
Remove older AFTER_0073/AFTER_0074/AFTER_0099 bundles to prevent stale-authority
drift.
