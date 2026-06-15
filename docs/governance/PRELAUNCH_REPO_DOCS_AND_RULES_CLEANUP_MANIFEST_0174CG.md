# Pre-Launch Repo Docs and Rules Cleanup Manifest (0174CG)

- **Scan Date:** 2026-06-15
- **Starting HEAD:** `914222d157bde13f5652318e22289621427e4414`
- **Repo:** `A:\Capital Chronicle\tools\cc-live-contentops`
- **Branch:** `master`
- **GitHub Repository:** `fatcat2109/capital-chronicle-contentops`

---

## 1. Active Authority Docs
These documents represent the active authority after cleanup:
- [CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md)
- [CAPITAL_CHRONICLE_CONTENTOPS_V5_FINAL_MASTER_PLAN_AND_NORTH_STAR.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/CAPITAL_CHRONICLE_CONTENTOPS_V5_FINAL_MASTER_PLAN_AND_NORTH_STAR.md)
- [CAPITAL_CHRONICLE_CONTENTOPS_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AFTER_0174AO.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/CAPITAL_CHRONICLE_CONTENTOPS_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AFTER_0174AO.md)
- [CONTENTOPS_FINAL_PRODUCT_ROADMAP_AFTER_0174AO.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/CONTENTOPS_FINAL_PRODUCT_ROADMAP_AFTER_0174AO.md)
- [CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md)
- [CONTENTOPS_LLM_QUOTA_RETRY_DISCIPLINE_ADDENDUM_AFTER_0174AY.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/CONTENTOPS_LLM_QUOTA_RETRY_DISCIPLINE_ADDENDUM_AFTER_0174AY.md)
- [CONTENTOPS_STRATEGY_RECOVERY_INDEX_AFTER_0174AO.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/CONTENTOPS_STRATEGY_RECOVERY_INDEX_AFTER_0174AO.md)

---

## 2. Stale Docs Found & Archived
The following stale files have been moved to [docs/archive/stale_prelaunch_reset_0174CG/](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/archive/stale_prelaunch_reset_0174CG/):
- `docs/ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_AFTER_0073.md` (passive wait-state runbook, stale)
- `docs/ANTIGRAVITY_BROWSER_QA_STRATEGY_AFTER_0157.md` (superseded Browser QA constraints)
- `docs/AUTOMATION_POLICY_MODES_AFTER_0086.md` (stale automation policy mode description)
- `docs/CURRENT_STATE_SUMMARY_AFTER_*.md` (12 historical summaries from 0073 to 0174AM)
- `docs/IDE_CLI_QUICKSTART_AFTER_*.md` (11 historical quickstarts)
- `docs/NEW_CHAT_CONTINUATION_AFTER_*.md` (17 historical resume files)
- `docs/PROJECT_SOURCE_EXPORT_AFTER_*.md` (15 historical exports)
- `docs/UPLOAD_BUNDLE_MANIFEST_AFTER_*.md` (15 historical manifests)
- `docs/PROJECT_SOURCES_DELETE_REPLACE_GUIDE_AFTER_*.md` (3 guides)
- `docs/PROJECT_SOURCES_REPLACEMENT_INDEX_AFTER_*.md` (3 indices)
- `docs/Capital Chronicle ContentOps — Final Master Plan for Pre-Alpha Content + API Automation Readiness.md` (duplicate of 0077 master plan)
- `docs/APPROVAL_LEDGER_KILL_SWITCH_REDACTED_AUDIT_AFTER_0131.md` (superseded safety doc)
- `docs/CREDENTIAL_ENVELOPE_AND_SECRET_POLICY_AFTER_0134.md` (superseded by new policy)
- `docs/PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK_AFTER_0133.md` (superseded by pre-launch policy)
- `docs/MOCK_PUBLISH_AND_MANUAL_METRICS_READINESS_AFTER_0132.md` (superseded by pre-launch policy)
- `docs/CANONICAL_SOCIAL_POST_AND_PLATFORM_DRY_RUN_AFTER_0130.md` (superseded)
- `docs/LLM_ASSISTED_DRAFT_REVIEW_PACKET_AFTER_0129.md` (superseded)
- `docs/GROUNDED_RESEARCH_BRIEF_CONTRACT_AFTER_0128.md` (superseded)
- `docs/PRE_ALPHA_CONTENT_LANE_POLICY_AFTER_0127.md` (superseded)
- `docs/CONTENTOPS_RECONCILED_ROADMAP_AFTER_0126.md` (superseded)
- `docs/CONTENTOPS_STRATEGY_RECOVERY_MAP_AFTER_0126.md` (superseded)

---

## 3. Files Edited (in 0174CG)
- [CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md) - Updated React/Tailwind/V5 constraints and credential policy language.
- [README.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/README.md) - Pointed to V5 app, pre-launch operating policy, and added instructions on running V5.
- [tests/test_security_scans.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_security_scans.py) - Exempted pre-launch credential readiness/presence check modules from strict zero-env check.
- **Validation and Handoff Path Expectation Modules:** Updated path expectations and legacy selectors to fallback resolve moved docs to the archive directory:
  - [live_contentops/final_bundle_manifest.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/live_contentops/final_bundle_manifest.py)
  - [live_contentops/ide_cli_document_bundle.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/live_contentops/ide_cli_document_bundle.py)
  - [live_contentops/institutional_ui_ux_frontend_rebuild_plan.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/live_contentops/institutional_ui_ux_frontend_rebuild_plan.py)
  - [tests/test_alpha_wait_state.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_alpha_wait_state.py)
  - [tests/test_ide_cli_document_bundle.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_ide_cli_document_bundle.py)
  - [tests/test_institutional_ui_ux_frontend_rebuild_plan.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_institutional_ui_ux_frontend_rebuild_plan.py)
  - [tests/test_next_phase_selection.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_next_phase_selection.py)
  - [tests/test_pipeline_trace.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_pipeline_trace.py)
  - [tests/test_review_bundle_manifest.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_review_bundle_manifest.py)

---

## 4. Files Deleted
- None. (To prevent accidental loss of important historical evidence, all candidate stale docs were archived instead of deleted.)

---

## 5. Files Intentionally Preserved
- All `qa_evidence_*` folders (G. Evidence artifact)
- All schemas under `schemas/`
- All files under `ui/`
- All active authority plans and roadmaps under `docs/`

---

## 6. Unknown / Defer List
- None.

---

## 7. Old Rule Replaced
- **Old Rule:** No `.env` reads ever; no environment variable or credential loading/presence checks allowed anywhere; no React/Tailwind frontend dependencies allowed.
- **New Pre-Launch Rule:** “ContentOps pre-launch tasks may perform explicitly scoped, local-only .env presence and shape checks. Raw secret values must never be printed, logged, committed, screenshotted, rendered in the browser, or included in evidence packets. The browser UI must not read .env. Live platform/provider calls remain disabled until a separate platform/provider gate explicitly authorizes a bounded validation or posting task.”

---

## 8. Tests Updated
- `tests/test_security_scans.py`: Modified `test_no_forbidden_imports_or_env_vars` to split checks into separate allowlists/denylists for env access and forbidden imports.
- `tests/test_telegram_live_pilot.py`: Modified to mock test flags and clear real env variables during token absence check.

---

## 9. Validation Commands Run
- `python run_validation.py`

---

## 10. Caveats
- 0174CG accepted as directionally correct policy reset, but 0174CG_A tightens the security scan split before any real credential-readiness execution.

---

## 11. 0174CG_A Corrective Guardrail Patch
To prevent the pre-launch credential policy from becoming a generic loophole for network/provider/platform libraries or credential leakage:
- **Tightened Security Scan Split:** Split the security checks in [tests/test_security_scans.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_security_scans.py) into separate policies:
  - **A. Env-read allowlist:** Only local/redacted readiness/presence modules (or explicitly authorized live-gate modules) may access env-like inputs or `os.environ`/`os.getenv`.
  - **B. Network/provider/platform import denylist:** Stricter check blocks readiness/presence modules from importing `requests`, `httpx`, `urllib`, `socket`, `openai`, `anthropic`, `tweepy`, `selenium`, `playwright`, browser/network clients, and platform/provider SDKs.
  - **C. Live-gate allowlist:** Only explicitly allowlisted live-gate modules (e.g. `telegram_live_pilot.py`) are allowed to import urllib/socket or run network targets.
- **Legacy Live Pilot Hardening:** Modified [live_contentops/telegram_live_pilot.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/live_contentops/telegram_live_pilot.py) to raise a fail-closed exception by default under the pre-launch operating policy, and completely removed token suffix/prefix/length leakage.
- **Files Edited in 0174CG_A:**
  - [tests/test_security_scans.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_security_scans.py)
  - [live_contentops/telegram_live_pilot.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/live_contentops/telegram_live_pilot.py)
  - [tests/test_telegram_live_pilot.py](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/tests/test_telegram_live_pilot.py)
  - [docs/governance/PRELAUNCH_REPO_DOCS_AND_RULES_CLEANUP_MANIFEST_0174CG.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/governance/PRELAUNCH_REPO_DOCS_AND_RULES_CLEANUP_MANIFEST_0174CG.md)
  - [docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md)
