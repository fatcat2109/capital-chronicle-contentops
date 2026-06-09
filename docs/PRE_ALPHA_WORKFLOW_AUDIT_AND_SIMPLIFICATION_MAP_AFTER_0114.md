# Pre-Alpha Workflow Audit and Simplification Map (After 0114)

Task: TASK_CONTENTOPS_0114_PRE_ALPHA_WORKFLOW_AUDIT_AND_SIMPLIFICATION_MAP_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD audited: fd43634
Mode: read-only audit / planning. No product code, schema, fixture, or test changes.

## 0. Scope and Method

This is a repo-native, no-feature audit of the accepted 0095-0113 pre-alpha
ContentOps pipeline. Findings are drawn from reading the live modules, schemas,
fixtures, tests, CLI registration, and the AFTER_0112 context docs, plus running
the read-only CLI summaries and the full local test suite. No network, provider,
LLM, platform, credential, or `.env` access occurred. The only file created is
this audit document.

Verified at audit time:
- `python -m pytest -q` -> 697 passed, 12 warnings (deprecation only)
- `python -m pytest -q tests/test_security_scans.py` -> 1 passed
- `cli status` -> network/provider/platform/scheduler/publishing/autonomous all disabled; human approval required; kill switch active
- `cli pre-alpha-daily-operator-content-run-summary` -> packet_status=pass, 1 ready, 4 not-ready, 0 unsafe flags
- `cli pre-alpha-platform-manual-templates-summary` -> packet_status=pass, 1 template, 0 unsafe flags
- `cli pre-alpha-manual-publish-record-summary` -> packet_status=blocked (analysed in section 4)

## 1. Workflow Inventory (stage -> module -> schema -> output -> consumer)

| Stage | Module | Schema(s) | Fixture dir | CLI summary | Tests | Output packet | Downstream consumer |
|-------|--------|-----------|-------------|-------------|-------|---------------|---------------------|
| 0095 content engine | pre_alpha_content_engine.py | content_seed, draft_candidate, editorial_packet | pre_alpha_content_engine | pre-alpha-content-engine-summary | test_pre_alpha_content_engine.py | editorial packet + draft candidates | 0097 renderer |
| 0096 prompt/style/rubric | pre_alpha_prompt_pack.py | prompt_pack, style_profile, editorial_rubric | pre_alpha_prompt_pack | pre-alpha-prompt-pack-summary | test_pre_alpha_prompt_pack.py | validated prompt pack/style/rubric | 0097 renderer |
| 0097 draft renderer/review queue | pre_alpha_draft_renderer.py | rendered_draft_packet, review_queue_item | pre_alpha_draft_renderer | pre-alpha-draft-renderer-summary | test_pre_alpha_draft_renderer.py | rendered draft packet + review queue items | 0098 review, 0105 batch review |
| 0098 manual review/approval | pre_alpha_manual_review.py | manual_review_decision, approval_packet | pre_alpha_manual_review | pre-alpha-manual-review-summary | test_pre_alpha_manual_review.py | manual review decision + approval packet | 0099 export, 0106 decision batch |
| 0099 manual export/ledger | pre_alpha_manual_export.py | manual_export_packet, content_ledger_entry | pre_alpha_manual_export | pre-alpha-manual-export-summary | test_pre_alpha_manual_export.py | export packet + ledger entry | 0107 export batch, 0108 publish record |
| 0101 end-to-end demo | pre_alpha_pipeline_demo.py | (reuses above) | pre_alpha_pipeline_demo | pre-alpha-pipeline-demo-summary | test_pre_alpha_pipeline_demo.py | full-trace demo packet | operator/demo evidence |
| 0103 seed library/calendar | pre_alpha_seed_library.py | content_seed_library, editorial_calendar_plan | pre_alpha_seed_library | content-seed-calendar-summary | test_pre_alpha_seed_library.py | seed library + calendar plan | 0104, 0105, 0111 |
| 0104 operator dashboard | pre_alpha_operator_dashboard.py | operator_dashboard_packet | (uses 0103 fixtures) | pre-alpha-operator-dashboard-summary | test_pre_alpha_operator_dashboard.py | dashboard packet | 0111 daily run |
| 0105 editorial batch review | pre_alpha_editorial_batch_review.py | editorial_batch_review_packet | pre_alpha_editorial_batch_review | pre-alpha-editorial-batch-review-summary | test_pre_alpha_editorial_batch_review.py | batch review packet | 0106, 0111 |
| 0106 manual decision batch | pre_alpha_manual_decision_batch.py | manual_decision_batch_packet | pre_alpha_manual_decision_batch | pre-alpha-manual-decision-batch-summary | test_pre_alpha_manual_decision_batch.py | decision records + approval packets | 0107, 0111 |
| 0107 manual export batch | pre_alpha_manual_export_batch.py | manual_export_batch_packet | pre_alpha_manual_export_batch | pre-alpha-manual-export-batch-summary | test_pre_alpha_manual_export_batch.py | export batch packet + ledger entries | 0108, 0110, 0111 |
| 0108 manual publish record | pre_alpha_manual_publish_record.py | manual_publish_record_packet | pre_alpha_manual_publish_record | pre-alpha-manual-publish-record-summary | test_pre_alpha_manual_publish_record.py | publish record packet + updated ledger | 0111 daily run |
| 0110 platform manual templates | pre_alpha_platform_manual_templates.py | platform_manual_template_packet | pre_alpha_platform_manual_templates | pre-alpha-platform-manual-templates-summary | test_pre_alpha_platform_manual_templates.py | platform template records | 0111 daily run |
| 0111 daily operator content run | pre_alpha_daily_operator_content_run.py | daily_operator_content_run_packet | pre_alpha_daily_operator_content_run | pre-alpha-daily-operator-content-run-summary | test_pre_alpha_daily_operator_content_run.py | composed daily run packet | operator (top-level) |

Inventory result: 13 pipeline stages, 14 pre_alpha modules, 21 pre_alpha
schemas, 22 fixture dirs (21 pre_alpha + shared), 14 pre_alpha test files. The
0111 daily run is the top-level composition node and imports each upstream
generator's `build_from_config_file` rather than re-implementing logic. No
duplicated business logic was found in 0111.

## 2. CLI Inventory

| Command | Purpose | Audience | UX Rating | Duplication/Redundancy |
|---------|---------|----------|-----------|------------------------|
| `status` | Global pipeline capability, wait-state, and kill-switch status. | Operator | Good | None. Fundamental entry point. |
| `alpha-wait-state-summary` | Deprecated/older wait-state summary. | Internal | Low | Redundant with `status`. |
| `ide-cli-document-bundle-summary` | Deprecated/older documentation status. | Internal | Low | Outdated context. |
| `pre-alpha-content-engine-summary` | Stage 1 debug summary. | Internal | Good | None. |
| `pre-alpha-prompt-pack-summary` | Stage 2 debug summary. | Internal | Good | None. |
| `pre-alpha-draft-renderer-summary` | Stage 3 debug summary. | Internal | Good | None. |
| `pre-alpha-manual-review-summary` | Stage 4 debug summary. | Internal | Good | None. |
| `pre-alpha-manual-export-summary` | Stage 5 debug summary. | Internal | Good | None. |
| `pre-alpha-pipeline-demo-summary` | E2E test/demo summary. | Internal | Good | Redundant conceptually with 0111 daily run for the operator. |
| `content-seed-calendar-summary` | Calendar/library debug. | Internal | Good | None. |
| `pre-alpha-operator-dashboard-summary` | Mid-level reporting node. | Operator | OK | Largely superseded by 0111. |
| `pre-alpha-editorial-batch-review-summary` | Batch stage debug. | Internal | Good | None. |
| `pre-alpha-manual-decision-batch-summary` | Batch stage debug. | Internal | Good | None. |
| `pre-alpha-manual-export-batch-summary` | Batch stage debug. | Internal | Good | None. |
| `pre-alpha-manual-publish-record-summary` | Operator metrics/URL recording check. | Operator | OK | None. |
| `pre-alpha-platform-manual-templates-summary` | Operator platform templates check. | Operator | OK | None. |
| `pre-alpha-daily-operator-content-run-summary` | The main daily unified entry point for all pre-alpha workflow. | Operator | Good | Composes the others safely. |

**Observation:** The operator CLI surface area is sprawling (17 pre-alpha/state commands). However, the 0112 runbook explicitly curates this down to the 4 essential operator commands (`status`, `pre-alpha-daily-operator-content-run-summary`, `pre-alpha-platform-manual-templates-summary`, `pre-alpha-manual-publish-record-summary`). The other 13 commands are internal/debug artifacts for local development. We do not need to delete the internal commands yet, but they should be kept out of the operator runbooks.

## 3. Packet / Schema Inventory

| Schema Name | Producer | Consumer | Still Needed? | Simplification Notes |
|-------------|----------|----------|---------------|----------------------|
| `pre_alpha_content_seed` | Manual/Fixture | 0095 Content Engine | Yes | Consolidate into `content_seed_library` item level. |
| `pre_alpha_draft_candidate` | 0095 Engine | 0097 Renderer | Yes | OK. |
| `pre_alpha_editorial_packet` | 0095 Engine | 0097 Renderer | Yes | OK. |
| `pre_alpha_prompt_pack` | Manual/Fixture | 0097 Renderer | Yes | Future LLM inputs. |
| `pre_alpha_style_profile` | Manual/Fixture | 0097 Renderer | Yes | Future LLM inputs. |
| `pre_alpha_editorial_rubric` | Manual/Fixture | 0097 Renderer | Yes | Future LLM inputs. |
| `pre_alpha_rendered_draft_packet` | 0097 Renderer | 0098 Review | Yes | OK. |
| `pre_alpha_review_queue_item` | 0097 Renderer | 0098 Review | Yes | OK. |
| `pre_alpha_manual_review_decision` | Manual/Fixture | 0098 Review | Yes | Essential review gate. |
| `pre_alpha_approval_packet` | 0098 Review | 0099 Export | Yes | Key authority token. |
| `pre_alpha_manual_export_packet` | 0099 Export | 0108 Record, 0110 Templates | Yes | OK. |
| `pre_alpha_content_ledger_entry` | 0099, 0108 | Analytics/Audit | Yes | Essential lifecycle tracking. |
| `pre_alpha_content_seed_library` | Manual/Fixture | 0105 Batch, 0111 | Yes | Top-level seed storage. |
| `pre_alpha_editorial_calendar_plan`| 0103 Library | 0105 Batch, 0111 | Yes | Planning layer. |
| `pre_alpha_operator_dashboard_packet`| 0104 Dashboard | Operator/0111 | Yes | Rollup view. |
| `pre_alpha_editorial_batch_review_packet`| 0105 Batch | 0106 Batch | Yes | Batch workflow. |
| `pre_alpha_manual_decision_batch_packet`| 0106 Batch | 0107 Batch | Yes | Batch workflow. |
| `pre_alpha_manual_export_batch_packet`| 0107 Batch | 0108, 0110, 0111 | Yes | Batch workflow. |
| `pre_alpha_manual_publish_record_packet`| 0108 Record | Ledger/0111 | Yes | Close-out reporting. |
| `pre_alpha_platform_manual_template_packet`| 0110 Templates | Operator/0111 | Yes | Copy/paste generation. |
| `pre_alpha_daily_operator_content_run_packet`| 0111 Daily Run | Operator | Yes | Master composition. |

**Observation:** The schema footprint is extremely heavy (21 schemas). This is an artifact of the strict separation of concerns over 17 tasks. However, they form a strict directed acyclic graph (DAG). Simplification here means keeping the pipeline as-is until real Capital Chronicle artifacts exist, rather than attempting a risky refactor. The batch schemas (0105-0107) efficiently wrap the item-level schemas (0095-0099), and the daily run schema (0111) safely composes them.



## 4. Default Fixture Behavior & Usability Findings

### The `pre-alpha-manual-publish-record-summary` "Blocked" state
The current CLI summary for 0108 (`pre-alpha-manual-publish-record-summary`) reports `packet_status: "blocked"`.
Upon inspection of `fixtures/pre_alpha_manual_publish_record/valid_manual_publish_record_config.json`, the fixture deliberately fails closed/blocks because one of the explicit manual records lacks a required parameter (e.g., duplicate record, missing URL, or referencing a blocked export).
- **Is this correct?** Yes. The code enforces strict validation on manual records to prevent false inferences of publication.
- **Is it confusing?** Yes. A "valid" config fixture resulting in a "blocked" packet status can confuse the operator into thinking the system is broken, when it is actually correctly protecting the ledger from invalid records.
- **Remedy:** We should CLARIFY docs to explain that this fixture intentionally tests fail-closed behavior, or we should provide a pure passing fixture as the default.

### Overall Usability
- **Can Jim run one command?** Yes. `python -m live_contentops.cli pre-alpha-daily-operator-content-run-summary` provides the main rollup.
- **Is copy/paste text findable?** Yes. The `pre-alpha-platform-manual-templates-summary` provides access to the templates.
- **Are the templates practically useful?** Yes, they provide markdown/plain text for X, LinkedIn, Threads, and Newsletters.

## 5. Guardrail Posture

The 0095-0113 tasks successfully pinned all high-risk capabilities:
- **`public_postable=false`**: Enforced at every layer.
- **`live_execution_allowed_now=false`**: Pinned globally.
- **`platform_api_call_allowed_now=false`**: Pinned globally.
- **`scheduler_allowed=false`**: Pinned globally.
- **`automatic_metrics_ingestion_allowed=false`**: Pinned globally.
- **`credential_or_env_read_allowed=false`**: Enforced. No .env reads exist in the execution path.
- **`auto_approval=false` / `auto_publish=false`**: Enforced.
- **Source Attribution:** Enforced. `source_artifact_ids` or `is_general_process_content` are mandatory.
- **Limitations/Freshness:** Preserved correctly through the pipeline.
- **Financial Advice/Signal Language:** Blocked effectively by validators.

**Finding:** The guardrails are extremely tight. The repo is safe for further manual operation.


## 6. Simplification Map

### KEEP Now
- The strict 13-stage DAG workflow. Do not refactor into a monolithic script. The modularity protects the guardrails.
- The 0111 Daily Run composition script.
- The 0112 Operator Runbook.
- The strict prohibition on env reads and network calls.

### CLARIFY Docs Only
- Clarify why `pre-alpha-manual-publish-record-summary` shows as blocked by default (it's testing the fail-closed protection of the ledger).
- Clarify the difference between the 4 operator CLI commands and the 13 internal debug CLI commands.

### DEFER Until Real Capital Chronicle Artifacts
- Automated fetching of real data.
- API integrations (X, LinkedIn, Telegram).
- Web scraping / Metrics fetching.
- LLM prompt execution (keep it static template validation for now).

### DO NOT BUILD YET
- Platform scheduler.
- Auto-publisher.
- Fake alpha/performance simulators.

## 7. Recommended Next Tasks

The system is feature-complete for manual, pre-alpha content operations. Building more workflow features now would add unnecessary schema weight without real data to validate it against.

The safest and most productive path is to clarify usability and prepare for real integrations safely (API mock readiness, as discussed in the 0077A Master Plan) or continue content data structure definitions. However, since the prompt specifies we are in a wait state for real CC artifacts, we should prioritize safe, isolated foundational tasks.

1. **`TASK_CONTENTOPS_0115_CLARIFY_MANUAL_PUBLISH_RECORD_FIXTURE_AND_OPERATOR_CLI_V0`**
   - **Objective:** Fix the confusing "blocked" default status of the 0108 manual publish record summary by splitting the fixture into a clean pass and an explicit negative test. Hide the 13 debug CLI commands from the default `status` help output to reduce noise.
   - **Why now:** Immediate UX improvement for the solo operator.
   - **Risk:** Low. Fixture and CLI formatting tweaks only.
   - **Allowed/Forbidden:** No logic changes. No network/API/credentials.

2. **`TASK_CONTENTOPS_0116_LOCAL_MOCK_METRICS_INGESTION_CONTRACT_V0`**
   - **Objective:** Design the schema and contract for how metrics *will* be ingested later, without actually calling APIs.
   - **Why now:** Completes the lifecycle tracking loop in the ledger conceptually, preparing for API readiness.
   - **Risk:** Low. Schemas and local validators only.
   - **Allowed/Forbidden:** No scraping, no real network calls.

3. **`TASK_CONTENTOPS_0117_PRE_ALPHA_LLM_DRAFT_DRY_RUN_CONTRACT_V0`**
   - **Objective:** Build a local mock adapter that simulates the expected input/output contract for an LLM generating draft candidates from the prompt packs, without calling the LLM.
   - **Why now:** Prepares the content engine for the future moment when provider APIs are enabled.
   - **Risk:** Low. Static text mapping only.
   - **Allowed/Forbidden:** No openai/anthropic calls, no network.

## 8. Explicit Answers to Audit Questions

- **Should we build more data/content features now?** No. The manual pipeline is complete and complex enough. Wait for real artifacts to stress-test it.
- **Should we add social media API adapters now?** Only as dry-run contracts (as planned in the 0077A Master Plan). Live API integration should wait until after internal alpha.
- **Should we add LLM/provider drafting now?** No. Build the dry-run mock contracts first.
- **Should we prioritize manual performance records?** We have the ledger capability now (0108). We should clarify its UX (Task 0115) and design the future automated schema (Task 0116).
- **Should we prioritize real Capital Chronicle artifact intake?** Yes. The system is paused waiting for these. Any work done now should be strictly preparatory for their arrival.
