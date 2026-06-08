# Project Source Export - After TASK_CONTENTOPS_0068

LOCAL ONLY | ADVISORY ONLY | HUMAN REVIEW REQUIRED | NOT PUBLIC POSTABLE

## Purpose
Guidance for refreshing ChatGPT Project Sources after task 0068. This export is
local and advisory only. It does not upload, post, or call any external service.

## Supersession note
This 0068 bundle supersedes older continuation/source bundles. Remove stale
TASK_CONTENTOPS source bundles from Project Sources before uploading this set so
a future chat resumes from clean authority.

## Cleanup steps (manual, operator-performed)
1. Delete older TASK_CONTENTOPS_00xx continuation/source bundles from Project
   Sources.
2. Upload only the recommended docs from UPLOAD_BUNDLE_MANIFEST_AFTER_0068.md.
3. Confirm no .env, credentials, raw logs, provider outputs, or platform IDs are
   present.
4. Confirm no __pycache__/compiled files or large fixture dumps are present.
5. Confirm .gitignore is NOT uploaded (operator-owned working-tree drift).
6. Confirm no sibling (cc-contentops) or core repo files are present.

## Accepted state for the next chat
- repo: A:\Capital Chronicle\tools\cc-live-contentops
- bundle_base_head: 68b041c (pre-0068 base; not the current accepted state)
- task_0068_completed_head: cd72ee4 (0068 completed here; current accepted state)
- next_task: TASK_CONTENTOPS_0069_LOCAL_BUNDLE_REFRESH_AND_NEXT_PHASE_SELECTION_V0

Task 0068 is COMPLETED at cd72ee4. Do not resume from 68b041c as current state.

## Safety posture
No secrets. No live API. No posting. approval_granted=false. publish_ready=false.
provider_call_allowed=false. search_call_allowed=false.
platform_action_allowed=false. all_exports_safe_for_project_sources=true.
