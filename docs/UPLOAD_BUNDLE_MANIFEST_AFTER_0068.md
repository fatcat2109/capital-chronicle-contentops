# Upload Bundle Manifest - After TASK_CONTENTOPS_0068

LOCAL ONLY | ADVISORY ONLY | HUMAN REVIEW REQUIRED | NOT PUBLIC POSTABLE

This manifest lists which local files are recommended for upload to ChatGPT
Project Sources and which categories must be excluded. It does not upload
anything. It supersedes older continuation/source bundles.

## Accepted HEAD
68b041c

## Next task
TASK_CONTENTOPS_0069_LOCAL_BUNDLE_REFRESH_AND_NEXT_PHASE_SELECTION_V0

## Recommended uploads (safe, advisory)
- docs/NEW_CHAT_CONTINUATION_AFTER_0068.md
  - artifact_type: continuation_packet
  - authority_role: ADVISORY_CONTINUATION_CONTEXT
  - reason: current accepted state + next task brief for a fresh chat.
- docs/UPLOAD_BUNDLE_MANIFEST_AFTER_0068.md
  - artifact_type: upload_manifest
  - authority_role: ADVISORY_UPLOAD_GUIDANCE
  - reason: lists which files to upload/exclude and why.
- docs/PROJECT_SOURCE_EXPORT_AFTER_0068.md
  - artifact_type: project_source_export
  - authority_role: ADVISORY_CLEANUP_GUIDANCE
  - reason: Project Sources cleanup guidance + supersession note.
- docs/TASK_CONTENTOPS_0068_LOCAL_REVIEW_PACKET_BUNDLE_MANIFEST_AND_PROJECT_SOURCE_EXPORT_V0.md
  - artifact_type: completed_task_summary
  - authority_role: ADVISORY_TASK_RECORD
  - reason: completed-task summary for 0068.
- docs/TASK_CONTENTOPS_0067_LOCAL_PACKET_DASHBOARD_EXPORT_AND_OPERATOR_HANDOFF_V0.md
  - artifact_type: dashboard_handoff_report
  - authority_role: ADVISORY_TASK_RECORD
  - reason: prior dashboard/handoff report for review context.

Each recommended file is marked: contains_secrets=false, contains_live_ids=false,
contains_raw_logs=false, contains_provider_outputs=false,
contains_public_postable_content=false, safety_status=SAFE_FOR_PROJECT_SOURCES.

## Excluded categories (never upload)
- env_files (.env / .env.*)
- credentials_tokens_secrets
- raw_logs
- provider_outputs
- platform_ids
- private_memory_files (browser/brain/IDE)
- pycache_compiled (__pycache__ / .pyc)
- full_output_history
- large_fixture_dumps
- raw_vendor_data
- public_postable_fake_content
- sibling_or_core_repo_files (cc-contentops / core repo)
- gitignore_operator_drift (operator-owned .gitignore)

## Safety posture
approval_granted=false. publish_ready=false. provider_call_allowed=false.
search_call_allowed=false. platform_action_allowed=false.
all_exports_safe_for_project_sources=true.
