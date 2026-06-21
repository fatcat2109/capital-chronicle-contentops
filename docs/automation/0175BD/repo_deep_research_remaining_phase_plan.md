# Repository Deep Research & Remaining Phase Plan

Audited repository HEAD `2265841efaa3af9177fbb58f2def53ac6cfa807a` at 2026-06-22 03:00:42.

## 1. Executive Decision Summary

* **Decision**: **PAUSE the 0175 stub-chain immediately.**
* **Why**: The 0175 stub-chain has devolved into a circular, redundant loop of micro-contracts (0175AT through 0175BC) that sequentially convert one stub object into another with zero functional impact or dynamic data bindings. It represents a mock treadmill that consumes pipeline resources without providing real leverage.
* **Highest-Leverage Next Phase**: **TASK_CONTENTOPS_0175BE_CONTRACT_CHAIN_LIFECYCLE_SPINE_AND_OPERATOR_REVIEW_READ_MODEL_PRECHECK_V0**
* **Rationale**: Consolidating the circular mock contracts into a single unified Content Lifecycle Engine (representing Ingestion, Composition, Approval, Dispatch/Metrics, and Feedback) collapses 20+ redundant files into a robust state machine. This clean domain spine can then be dynamically bound to the V5 cockpit read-models, converting the V5 UI from a visual mockup into a real supervised cockpit.

---

## 2. Capability Inventory Table

| Capability | Ledger Status | Backing Module | Backing Test | UI Binding | Class | Confidence | Gaps |
|---|---|---|---|---|---|---|---|
| Platform Universe Registry | TESTED | [platform_universe_registry_v2.py](file:///live_contentops/platform_universe_registry_v2.py) | [test_platform_universe_registry_v2.py](file:///tests/test_platform_universe_registry_v2.py) | [CommandCenter.tsx](file:///ui/contentops_v5/src/views/CommandCenter.tsx) | `local/real` | `high` | Lack of live status queries to targets. |
| Content Idea Intake | TESTED | [content_idea_intent_parser_contract.py](file:///live_contentops/content_idea_intent_parser_contract.py) | [test_content_idea_intent_parser_contract.py](file:///tests/test_content_idea_intent_parser_contract.py) | [WriterStudio.tsx](file:///ui/contentops_v5/src/views/WriterStudio.tsx) | `local/symbolic` | `high` | Only accepts mock intents; no real RSS/ingestion pipelines. |
| Writer Studio | TESTED | [editorial_brief_ai_writer_output_contract.py](file:///live_contentops/editorial_brief_ai_writer_output_contract.py) | [test_editorial_brief_ai_writer_output_contract.py](file:///tests/test_editorial_brief_ai_writer_output_contract.py) | [WriterStudio.tsx](file:///ui/contentops_v5/src/views/WriterStudio.tsx) | `local/symbolic` | `high` | Editorial brief generation is dry-run only; no live synchronizer. |
| AI Writer / SEO Lab | TESTED | [llm_content_writer_workbench.py](file:///live_contentops/llm_content_writer_workbench.py) | [test_llm_content_writer_workbench.py](file:///tests/test_llm_content_writer_workbench.py) | [AiWriterSeoLab.tsx](file:///ui/contentops_v5/src/views/AiWriterSeoLab.tsx) | `local/symbolic` | `high` | No real LLM provider endpoint integrated. |
| Draft Inspector | TESTED | [citation_guardrail.py](file:///live_contentops/citation_guardrail.py) | [test_citation_guardrail.py](file:///tests/test_citation_guardrail.py) | [DraftInspector.tsx](file:///ui/contentops_v5/src/views/DraftInspector.tsx) | `local/real` | `high` | Rules engine evaluates static dictionary structures; no dynamic check runtime. |
| Platform Payload Preview | TESTED | [platform_payload_preview_contract.py](file:///live_contentops/platform_payload_preview_contract.py) | [test_platform_payload_preview_contract.py](file:///tests/test_platform_payload_preview_contract.py) | [PlatformPayloadPreview.tsx](file:///ui/contentops_v5/src/views/PlatformPayloadPreview.tsx) | `local/symbolic` | `high` | Payload formats verified via static checks, no real API sandbox rendering. |
| Manual Publish / Metrics | TESTED | [manual_publish_record_metrics_ledger_contract.py](file:///live_contentops/manual_publish_record_metrics_ledger_contract.py) | [test_manual_publish_record_metrics_ledger_contract.py](file:///tests/test_manual_publish_record_metrics_ledger_contract.py) | [ManualPublishMetrics.tsx](file:///ui/contentops_v5/src/views/ManualPublishMetrics.tsx) | `local/real` | `high` | No metrics retrieval API integrated; manual operator logs only. |
| Manual Export / Pilot | TESTED | [v5_manual_export_pilot_verification_contract.py](file:///live_contentops/v5_manual_export_pilot_verification_contract.py) | [test_v5_manual_export_pilot_verification_contract.py](file:///tests/test_v5_manual_export_pilot_verification_contract.py) | [ManualExportPilotVerification.tsx](file:///ui/contentops_v5/src/views/ManualExportPilotVerification.tsx) | `local/real` | `high` | None. Manual copy-paste capability verified. |
| Operator Review Queue | TESTED | [v5_operator_review_queue_manual_pilot_trail_contract.py](file:///live_contentops/v5_operator_review_queue_manual_pilot_trail_contract.py) | [test_v5_operator_review_queue_manual_pilot_trail_contract.py](file:///tests/test_v5_operator_review_queue_manual_pilot_trail_contract.py) | [OperatorReviewQueue.tsx](file:///ui/contentops_v5/src/views/OperatorReviewQueue.tsx) | `local/real` | `high` | Queue is decoupled from active platform dispatch triggers. |
| Manual Pilot Reconciliation | TESTED | [v5_manual_pilot_trail_reconciliation_contract.py](file:///live_contentops/v5_manual_pilot_trail_reconciliation_contract.py) | [test_v5_manual_pilot_trail_reconciliation_contract.py](file:///tests/test_v5_manual_pilot_trail_reconciliation_contract.py) | [ManualPilotTrailReconciliation.tsx](file:///ui/contentops_v5/src/views/ManualPilotTrailReconciliation.tsx) | `local/real` | `high` | Requires operator manual inputs; no background polling of platform status. |
| Approval / Dispatch Control | TESTED | [approval_queue.py](file:///live_contentops/approval_queue.py) | [test_approval_queue.py](file:///tests/test_approval_queue.py) | [ApprovalQueue.tsx](file:///ui/contentops_v5/src/views/ApprovalQueue.tsx) | `local/real` | `high` | Does not integrate production cryptographic key vaults. |
| Evidence Vault | TESTED | [redacted_immutable_audit_ledger_v2_contract.py](file:///live_contentops/redacted_immutable_audit_ledger_v2_contract.py) | [test_redacted_immutable_audit_ledger_v2_contract.py](file:///tests/test_redacted_immutable_audit_ledger_v2_contract.py) | [EvidenceVault.tsx](file:///ui/contentops_v5/src/views/EvidenceVault.tsx) | `local/real` | `high` | No validation check runs against a live blockchain audit ledger. |
| Preflight Bundle | TESTED | [local_preflight_bundle_v5_read_model_precheck_contract.py](file:///live_contentops/local_preflight_bundle_v5_read_model_precheck_contract.py) | [test_local_preflight_bundle_v5_read_model_precheck_contract.py](file:///tests/test_local_preflight_bundle_v5_read_model_precheck_contract.py) | [PreflightBundle.tsx](file:///ui/contentops_v5/src/views/PreflightBundle.tsx) | `local/real` | `high` | Checks presence of key names only; no active token validation. |
| Local Operator Runbook | TESTED | [v5_local_operator_runbook_index_contract.py](file:///live_contentops/v5_local_operator_runbook_index_contract.py) | [test_v5_local_operator_runbook_index_contract.py](file:///tests/test_v5_local_operator_runbook_index_contract.py) | [OperatorRunbookIndex.tsx](file:///ui/contentops_v5/src/views/OperatorRunbookIndex.tsx) | `local/real` | `high` | Runbook index relies on manual checkpoint verification. |
| Lane C Artifact Intake Validation | TESTED | [lane_c_artifact_intake_validation_contract.py](file:///live_contentops/lane_c_artifact_intake_validation_contract.py) | [test_lane_c_artifact_intake_validation_contract.py](file:///tests/test_lane_c_artifact_intake_validation_contract.py) | [CommandCenter.tsx](file:///ui/contentops_v5/src/views/CommandCenter.tsx) | `local/real` | `high` | Validates schema format only; no active filesystem connector active. |
| Lane C Artifact Connector Index | TESTED | [lane_c_artifact_connector_index_contract.py](file:///live_contentops/lane_c_artifact_connector_index_contract.py) | [test_lane_c_artifact_connector_index_contract.py](file:///tests/test_lane_c_artifact_connector_index_contract.py) | [CommandCenter.tsx](file:///ui/contentops_v5/src/views/CommandCenter.tsx) | `local/real` | `high` | Index is populated with symbolic path limits; no active ingestion loop. |
| Lane C Artifact Ingestion Foundation | TESTED | [lane_c_artifact_ingestion_foundation_contract.py](file:///live_contentops/lane_c_artifact_ingestion_foundation_contract.py) | [test_lane_c_artifact_ingestion_foundation_contract.py](file:///tests/test_lane_c_artifact_ingestion_foundation_contract.py) | [CommandCenter.tsx](file:///ui/contentops_v5/src/views/CommandCenter.tsx) | `local/real` | `high` | Simulates folder scanning via local fixtures; no file system watcher. |
| Telegram Channel Destination | TESTED | [telegram_first_supervised_live_post_gate.py](file:///live_contentops/telegram_first_supervised_live_post_gate.py) | [test_telegram_first_supervised_live_post_gate.py](file:///tests/test_telegram_first_supervised_live_post_gate.py) | [ApprovalQueue.tsx](file:///ui/contentops_v5/src/views/ApprovalQueue.tsx) | `live/supervised` | `high` | Requires CLI flags and direct getpass interactions; no admin UI send. |
| X supervised live-read gate | TESTED | [x_oauth_live_read_only_identity_proof_gate.py](file:///live_contentops/x_oauth_live_read_only_identity_proof_gate.py) | [test_x_oauth_live_read_only_identity_proof_gate.py](file:///tests/test_x_oauth_live_read_only_identity_proof_gate.py) | [PreflightBundle.tsx](file:///ui/contentops_v5/src/views/PreflightBundle.tsx) | `live/supervised` | `high` | OAuth flow validated for read-only user context; CLI getpass only. |
| X supervised live-write gate | LOCAL_CONTRACT_READY | [x_oauth_supervised_live_readiness_bridge_bundle_gate.py](file:///live_contentops/x_oauth_supervised_live_readiness_bridge_bundle_gate.py) | [test_x_oauth_supervised_live_readiness_bridge_bundle_gate.py](file:///tests/test_x_oauth_supervised_live_readiness_bridge_bundle_gate.py) | [PreflightBundle.tsx](file:///ui/contentops_v5/src/views/PreflightBundle.tsx) | `local/symbolic` | `high` | Dry-run readiness contract only; no live write endpoint verified. |

---

## 3. Phase Completion Map

### Completed with Evidence
- Platform Universe Registry
- Draft Inspector
- Manual Publish / Metrics
- Manual Export / Pilot
- Operator Review Queue
- Manual Pilot Reconciliation
- Approval / Dispatch Control
- Evidence Vault
- Preflight Bundle
- Local Operator Runbook
- Lane C Artifact Intake Validation
- Lane C Artifact Connector Index
- Lane C Artifact Ingestion Foundation
- Telegram Channel Destination
- X supervised live-read gate
- Pre-Alpha Ingestion Connector (tested)

### Implemented but Needs Consolidation
- Content feedback stub chain (0175AT-0175BC loop)

### Implemented but Needs Browser QA
- Platform Universe Registry
- Content Idea Intake
- Writer Studio
- AI Writer / SEO Lab
- Draft Inspector
- Platform Payload Preview
- Manual Publish / Metrics
- Manual Export / Pilot
- Operator Review Queue
- Manual Pilot Reconciliation
- Approval / Dispatch Control
- Evidence Vault
- Preflight Bundle
- Local Operator Runbook
- Lane C Artifact Intake Validation
- Lane C Artifact Connector Index
- Lane C Artifact Ingestion Foundation
- Telegram Channel Destination
- X supervised live-read gate
- X supervised live-write gate

### Symbolic Only
- Content Idea Intake
- Writer Studio
- AI Writer / SEO Lab
- Platform Payload Preview
- X supervised live-write gate
- LinkedIn / Meta / TikTok / YouTube expansion gates (not started or placeholder only)

### Missing
- Live RSS parser
- Real database binding
- Production KMS credentials

### Stale / Duplicate
- 0175AT-0175BC stub chain duplicate prechecks (overclaims progress without utility)

### Risky / Overclaimed
- X supervised live-write gate (claimed ready but symbolic only)

---

## 4. Remaining Phase Plan

Here is the concise strategic roadmap of the next 5-10 tasks needed to get ContentOps to a real supervised multi-platform editorial OS:

### Task 1: TASK_CONTENTOPS_0175BE_CONTRACT_CHAIN_LIFECYCLE_SPINE_AND_OPERATOR_REVIEW_READ_MODEL_PRECHECK_V0
* **Objective**: Consolidate the 0175 loop of mock contracts into a single unified Content Lifecycle state engine (`content_lifecycle_engine.py`) and a consolidated operator review read-model.
* **Why Now**: Collapses the redundant 20+ file stub-chain into a single maintainable state machine.
* **Likely Files**: `live_contentops/content_lifecycle_engine.py`, `tests/test_content_lifecycle_engine.py`, `live_contentops/cockpit_read_model_contract.py`.
* **Allowed Behavior**: Local memory state operations only.
* **Live/API Policy**: No network, no credentials read.
* **Validation**: Unit tests verifying state transitions (Ingested -> Drafted -> Approved -> Exported -> Published -> Metrics).
* **Acceptance Criteria**: Single Python class manages post state transitions; passes focused pytests.
* **Stop Conditions**: Any live API call or external credentials access.
* **Expected Next Task**: TASK_CONTENTOPS_0175BF_OPERATOR_REVIEW_READ_MODEL_TO_V5_QUEUE_BINDING_V0.

### Task 2: TASK_CONTENTOPS_0175BF_OPERATOR_REVIEW_READ_MODEL_TO_V5_QUEUE_BINDING_V0
* **Objective**: Bind the consolidated Python read-models to the V5 React UI components by writing a TypeScript exporter script that updates the static data packets in `ui/contentops_v5/src/data/`.
* **Why Now**: Moves the V5 UI from a static visual prototype to a dynamic, contract-driven cockpit.
* **Likely Files**: `tools/export_v5_read_model.py`, `ui/contentops_v5/src/data/*.ts`.
* **Allowed Behavior**: File writes under the V5 UI directory.
* **Live/API Policy**: Local filesystem write only.
* **Validation**: Build Vite app and verify that V5 UI displays actual backend post states.
* **Acceptance Criteria**: Running the export tool generates TypeScript packet files that Vite builds without errors.
* **Stop Conditions**: Stale mock data references in the UI.
* **Expected Next Task**: TASK_CONTENTOPS_0175BG_LANE_C_ARTIFACT_INTAKE_BRIDGE_V0.

### Task 3: TASK_CONTENTOPS_0175BG_LANE_C_ARTIFACT_INTAKE_BRIDGE_V0
* **Objective**: Bridge the Lane C intake validators to read actual files from the `capital-chronicle-ingestion` repository instead of using static fixture structures.
* **Why Now**: Enables real editorial content flow based on actual ingestion data.
* **Likely Files**: `live_contentops/lane_c_artifact_ingestion_foundation_contract.py`, `tests/test_lane_c_artifact_ingestion_foundation_contract.py`.
* **Allowed Behavior**: Read-only access to files in the ingestion repository.
* **Live/API Policy**: Local path reads only; no network connections.
* **Validation**: Run ingestion checks using local JSON reports in the raw raw data folder.
* **Acceptance Criteria**: Ingested drafts are verified against actual ingestion files.
* **Stop Conditions**: Any file write to the ingestion repository.
* **Expected Next Task**: TASK_CONTENTOPS_0175BH_MANUAL_EXPORT_AND_METRICS_HARDENING_V0.

### Task 4: TASK_CONTENTOPS_0175BH_MANUAL_EXPORT_AND_METRICS_HARDENING_V0
* **Objective**: Harden the manual export copy-paste flows and metrics logging. Provide a structured checklist inside V5 UI for copying clipboard payloads and recording publish URLs.
* **Why Now**: Establishes final manual publishing capability safety rules.
* **Likely Files**: `live_contentops/v5_manual_export_pilot_verification_contract.py`, `ui/contentops_v5/src/views/ManualExportPilotVerification.tsx`.
* **Allowed Behavior**: Clipboard API and localStorage mapping for manual logs.
* **Live/API Policy**: Local-only client-side logic; no network.
* **Validation**: Manual verification of copy-paste clipboard buffers and URL input validations.
* **Acceptance Criteria**: Clipboard writes format payload correctly for Substack and LinkedIn.
* **Stop Conditions**: Automatic API postings.
* **Expected Next Task**: TASK_CONTENTOPS_0175BI_CREDENTIAL_PRESENCE_INVENTORY_AND_DOTENV_VALIDATOR_V0.

### Task 5: TASK_CONTENTOPS_0175BI_CREDENTIAL_PRESENCE_INVENTORY_AND_DOTENV_VALIDATOR_V0
* **Objective**: Implement a dotenv credential presence checker that scans `.env` for required keys (X, Telegram) and maps them to redacted status objects (`PRESENT`/`MISSING`) without reading/exposing secret values.
* **Why Now**: Crucial prerequisite for future live-read-only gates, ensuring credentials exist without risk of leakage.
* **Likely Files**: `live_contentops/credential_envelope_policy.py`, `tests/test_credential_envelope_policy.py`.
* **Allowed Behavior**: Read redacted presence from `.env`.
* **Live/API Policy**: Redacted presence check only. Hard-blocked from printing or storing values.
* **Validation**: Test suite using mock `.env` files verifying presence maps correct booleans.
* **Acceptance Criteria**: Scanner runs cleanly on local environment and logs REDACTED presence checks.
* **Stop Conditions**: Printing secret prefix, suffix, hash, or raw characters.
* **Expected Next Task**: TASK_CONTENTOPS_0175BJ_X_OAUTH_LIVE_READ_ONLY_VALIDATION_V0.

### Task 6: TASK_CONTENTOPS_0175BJ_X_OAUTH_LIVE_READ_ONLY_VALIDATION_V0
* **Objective**: Run live-read-only validation for the X API using user-context OAuth 2.0 to confirm account identity context GET requests.
* **Why Now**: First real platform endpoint integration validation, strictly bounded to read-only user details.
* **Likely Files**: `live_contentops/x_oauth_live_read_only_identity_proof_gate.py`.
* **Allowed Behavior**: GET request to X user identity API only.
* **Live/API Policy**: Supervised live GET request with explicit operator authorization.
* **Validation**: Executing CLI script with `--operator-go` and `--execute` flags return verified identity status.
* **Acceptance Criteria**: Identity proof passes, returns verified credentials class, no token saved.
* **Stop Conditions**: Any write API action (POST tweet/message) or token persistence.
* **Expected Next Task**: TASK_CONTENTOPS_0175BK_TELEGRAM_BOT_API_LIVE_READ_ONLY_VALIDATION_V0.

### Task 7: TASK_CONTENTOPS_0175BK_TELEGRAM_BOT_API_LIVE_READ_ONLY_VALIDATION_V0
* **Objective**: Run live-read-only validation for the Telegram Bot API (`getMe`, `getChat`, `getChatMember`) to confirm chat channel post permissions.
* **Why Now**: Verifies Telegram bot credentials and admin setup before publishing.
* **Likely Files**: `live_contentops/telegram_live_getme_gate.py`, `tests/test_telegram_live_getme_gate.py`.
* **Allowed Behavior**: GET requests to Telegram API host only.
* **Live/API Policy**: Supervised live GET request with explicit operator authorization.
* **Validation**: Execution returned verified chat metadata and permissions check.
* **Acceptance Criteria**: getMe and getChatMember return success; chat credentials remain redacted in logs.
* **Stop Conditions**: sendMessage calls or updates polling.
* **Expected Next Task**: TASK_CONTENTOPS_0175BL_VISUAL_AND_BROWSER_QA_AUDIT_V0.

### Task 8: TASK_CONTENTOPS_0175BL_VISUAL_AND_BROWSER_QA_AUDIT_V0
* **Objective**: Perform visual screenshot audits and browser QA using Playwright to ensure layout integrity across all V5 operating rooms.
* **Why Now**: Stabilizes the final presentation layout of the operational cockpit before launch.
* **Likely Files**: `tests/test_v5_browser_qa.py`, `docs/browser_qa/TASK_CONTENTOPS_0175BL/`.
* **Allowed Behavior**: Spawn local browser testing sandbox.
* **Live/API Policy**: Local UI testing only; no network.
* **Validation**: Playwright capture of viewport sizes and console logs check.
* **Acceptance Criteria**: Browser QA report passes all layout density and progressive disclosure criteria.
* **Stop Conditions**: Visual regressions or horizontal overflows.

---

## 5. Recommended Immediate Next Implementation Task

### Recommended Task
`TASK_CONTENTOPS_0175BE_CONTRACT_CHAIN_LIFECYCLE_SPINE_AND_OPERATOR_REVIEW_READ_MODEL_PRECHECK_V0`

### Rationale
Consolidating the 20+ micro-contract files into a single unified lifecycle engine collapses the repetitive loop structure, unifies validation rules, and resolves the circular imports treadmill. This provides a robust, maintainable domain model that can be bound directly to the V5 cockpit UI view-models in subsequent phases.
