# TASK_CONTENTOPS_0068_LOCAL_REVIEW_PACKET_BUNDLE_MANIFEST_AND_PROJECT_SOURCE_EXPORT_V0

## Title & scope
Local-only review packet bundle manifest and Project Sources export (v0).
Deterministic, safe, Project Sources-ready bundle metadata for local
review/handoff artifacts: which docs are safe to upload, which must be excluded,
why, and what accepted state the next chat should use. Prepares local manifest
artifacts ONLY; it uploads nothing.

## Project intent guardrails
Local-first ContentOps control-plane sidecar. Not a live posting engine.
Grounded search is research context only, not authority, approval, execution,
publishing power, or market truth.

## What this task built
- `live_contentops/review_bundle_manifest.py`
  - `build_manifest()` deterministic Project Sources manifest.
  - `validate_manifest(...)` bundle safety validation.
  - `build_summary()` CLI summary.
- `tests/test_review_bundle_manifest.py` deterministic tests.
- Docs: `NEW_CHAT_CONTINUATION_AFTER_0068.md`,
  `UPLOAD_BUNDLE_MANIFEST_AFTER_0068.md`, `PROJECT_SOURCE_EXPORT_AFTER_0068.md`.
- `live_contentops/cli.py` new `project-source-export-summary` command.
- `live_contentops/status.py` next-task pointer advanced to 0069.

## Manifest contract
Each included file entry: path, artifact_type, reason_for_inclusion,
authority_role, safety_status, contains_secrets=false, contains_live_ids=false,
contains_raw_logs=false, contains_provider_outputs=false,
contains_public_postable_content=false, upload_recommended. Manifest also
carries accepted_head, next_task, accepted_chain_summary, hard_boundaries,
known_caveats, project_sources_cleanup_guidance, included_files,
excluded_categories, supersedes_older_source_bundles=true, and the standard
safety flags.

## Recommended uploads
- docs/NEW_CHAT_CONTINUATION_AFTER_0068.md (continuation_packet)
- docs/UPLOAD_BUNDLE_MANIFEST_AFTER_0068.md (upload_manifest)
- docs/PROJECT_SOURCE_EXPORT_AFTER_0068.md (project_source_export)
- docs/TASK_CONTENTOPS_0068_..._V0.md (completed_task_summary)
- docs/TASK_CONTENTOPS_0067_..._V0.md (dashboard_handoff_report)

## Excluded categories (never upload)
env_files, credentials_tokens_secrets, raw_logs, provider_outputs, platform_ids,
private_memory_files, pycache_compiled, full_output_history, large_fixture_dumps,
raw_vendor_data, public_postable_fake_content, sibling_or_core_repo_files,
gitignore_operator_drift.

## Bundle safety validation (block/warn)
Recommended upload with env/secret/raw-log/provider-output/platform-ID/pycache/
full-output-history path fragment; artifact flagged with unsafe content; artifact
claiming publish/approval/platform authority; public-postable content; missing
accepted_head; missing next_task; missing hard_boundaries; missing required
exclusion categories; .gitignore or sibling/core repo path.

## Verification
- `python -m pytest -q` -> 257 passed.
- `python -m pytest -q tests/test_review_bundle_manifest.py` -> 14 passed.
- `python -m live_contentops.cli project-source-export-summary` ->
  project_source_export_enabled/upload_manifest_enabled/
  new_chat_continuation_enabled true; accepted_head=68b041c; next_task=0069;
  contains_secrets/contains_live_ids/contains_public_postable_content false;
  all_exports_safe_for_project_sources true; validation_rules_enabled true.

## Risks / warnings
- Manifest is advisory; it uploads nothing. Excludes secrets/env/raw logs/
  provider outputs/platform IDs/pycache/full outputs/.gitignore/sibling-core
  repo files by category and by path-fragment validation.
- No network/provider/LLM/search/platform/credential/scheduling/posting/DM/
  browser capability was introduced.

## Open items
- None blocking. The `.gitignore` working-tree change is operator-owned, was
  not staged/committed/touched.

## Suggested next steps
- TASK_CONTENTOPS_0069_LOCAL_BUNDLE_REFRESH_AND_NEXT_PHASE_SELECTION_V0
