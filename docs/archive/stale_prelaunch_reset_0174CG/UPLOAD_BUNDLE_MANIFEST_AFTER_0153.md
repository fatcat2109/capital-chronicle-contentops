# Upload Bundle Manifest (After 0153)

## Bundle Purpose
Provide a clean, secret-free set of files for the operator to manually upload as
ChatGPT Project Sources after accepted baseline 0153 (HEAD a644f82). Cline does not
refresh Project Sources directly; it only generates local files for manual upload.

## Files Created (docs/)
- CURRENT_STATE_SUMMARY_AFTER_0153.md
- PROJECT_SOURCE_EXPORT_AFTER_0153.md
- NEW_CHAT_CONTINUATION_AFTER_0153.md
- UPLOAD_BUNDLE_MANIFEST_AFTER_0153.md
- PROJECT_SOURCES_REPLACEMENT_INDEX_AFTER_0153.md
- PROJECT_SOURCES_DELETE_REPLACE_GUIDE_AFTER_0153.md
- IDE_CLI_QUICKSTART_AFTER_0153.md
- BUNDLE_README_AFTER_0153.md
- BUNDLE_FILE_LIST_AFTER_0153.txt

## Files Copied Into project_sources_bundle_AFTER_0153/
Mandatory docs:
- CURRENT_STATE_SUMMARY_AFTER_0153.md
- PROJECT_SOURCE_EXPORT_AFTER_0153.md
- NEW_CHAT_CONTINUATION_AFTER_0153.md
- UPLOAD_BUNDLE_MANIFEST_AFTER_0153.md
- PROJECT_SOURCES_REPLACEMENT_INDEX_AFTER_0153.md
- PROJECT_SOURCES_DELETE_REPLACE_GUIDE_AFTER_0153.md
- IDE_CLI_QUICKSTART_AFTER_0153.md
- BUNDLE_README_AFTER_0153.md
- BUNDLE_FILE_LIST_AFTER_0153.txt

Useful schemas (optional grounding):
- telegram_credential_setup_operator_guide_packet.schema.json
- telegram_live_pilot_gate_packet.schema.json
- redacted_publish_audit_log_packet.schema.json
- publish_adapter_credential_secret_policy_packet.schema.json
- dry_run_publish_batch_manifest_packet.schema.json
- publish_automation_readiness_packet.schema.json
- platform_capability_registry_packet.schema.json

## Upload Order Recommendation
1. PROJECT_SOURCE_EXPORT_AFTER_0153.md (mandatory, authority)
2. CURRENT_STATE_SUMMARY_AFTER_0153.md (mandatory)
3. NEW_CHAT_CONTINUATION_AFTER_0153.md (mandatory)
4. PROJECT_SOURCES_REPLACEMENT_INDEX_AFTER_0153.md (mandatory)
5. PROJECT_SOURCES_DELETE_REPLACE_GUIDE_AFTER_0153.md (mandatory)
6. IDE_CLI_QUICKSTART_AFTER_0153.md (mandatory)
7. UPLOAD_BUNDLE_MANIFEST_AFTER_0153.md (mandatory)
8. BUNDLE_README_AFTER_0153.md (mandatory)
9. BUNDLE_FILE_LIST_AFTER_0153.txt (mandatory)
10. Schemas (optional, upload if richer grounding is wanted)

## Mandatory vs Optional
- Mandatory: all 9 docs files.
- Optional: the 7 schema files.

## Safety Statements
- No secrets included in this bundle.
- No real operator env path included in this bundle.
- No Project Sources refresh was performed by Cline; manual upload only.
