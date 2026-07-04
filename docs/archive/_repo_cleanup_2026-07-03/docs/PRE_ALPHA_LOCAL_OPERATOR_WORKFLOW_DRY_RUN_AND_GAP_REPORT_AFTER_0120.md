# Pre-Alpha Local Operator Workflow Dry Run & Gap Report (After 0120)

**Task:** `TASK_CONTENTOPS_0120_PRE_ALPHA_LOCAL_OPERATOR_WORKFLOW_DRY_RUN_AND_GAP_REPORT_V0`

## 1. Current Baseline
- **Repo path:** `A:\Capital Chronicle\tools\cc-live-contentops`
- **Branch:** `master`
- **Starting HEAD:** `10c2211`

## 2. Dry-Run Command Outputs Summary

### `status`
- **Status:** `local skeleton status`
- **Human Approval:** `required`
- **Unsafe Flags:** All APIs, networks, and autonomous agents are `disabled`.

### `operator-command-summary`
- **Usability:** High. Clearly partitions commands into `operator_daily`, `operator_manual_publish_record`, `operator_optional_post_publish`, and isolates internal debug scaffolding.

### `pre-alpha-daily-operator-content-run-summary`
- **Packet Status:** `pass`
- **Operator Ready:** 1 ready, 4 blocked/not-ready, 3 review items.
- **Safety Boundaries:** Preserved (no network, local only, no fake alpha).

### `pre-alpha-platform-manual-templates-summary`
- **Packet Status:** `pass`
- **Operator Ready:** 1 platform template record count.
- **Safety Boundaries:** Preserved (manual copy-paste only, no platform API payload generated).

### `pre-alpha-manual-publish-record-summary`
- **Packet Status:** `pass`
- **Counts:** 1 eligible export packet, 1 updated ledger entry, 1 not recorded.
- **Usability Note:** Blocked/fail-closed mechanism is now explicit and understandable.

### `pre-alpha-manual-performance-record-summary`
- **Packet Status:** `pass`
- **Counts:** 1 record count, 1 linked manual publish record count.
- **Usability:** Strict schema ensures metrics must be entered by the operator.

### `pre-alpha-content-performance-review-summary`
- **Packet Status:** `pass`
- **Counts:** 3 included records, 2 conservative findings, 1 editorial hypothesis.
- **Safety boundaries:** `statistical_significance_claimed=false`

## 3. End-to-End Workflow Usability Summary

| Workflow Step | Command | Output Packet | Status | Action Required | Inference Risk | Usability Rating | Recommended Fix |
|---|---|---|---|---|---|---|---|
| 1. System Check | `status` | Local Skeleton Status | PASS | Observe | None | Good | None |
| 2. Operator Content Run | `pre-alpha-daily-operator-content-run-summary` | Operator Content Run | PASS | Select item | None | Good | Output is somewhat JSON-heavy. Consider Markdown export. |
| 3. Template Generation | `pre-alpha-platform-manual-templates-summary` | Platform Manual Templates | PASS | Copy/Paste | None | Good | Same as above. |
| 4. External Publish | (Manual external action) | N/A | N/A | Post manually | None | Good | N/A |
| 5. Publish Record | `pre-alpha-manual-publish-record-summary` | Publish Record Packet | PASS | Record URL/ID | None | Acceptable | 0115 fixture clarify resolved negative test confusion. |
| 6. Performance Record | `pre-alpha-manual-performance-record-summary` | Performance Record Packet | PASS | Record Metrics | None | Acceptable | Good local contract. |
| 7. Performance Review | `pre-alpha-content-performance-review-summary` | Content Performance Review | PASS | Read Hypotheses| None | Acceptable | Good local contract. |

## 4. Required vs Optional Command Summary

**Minimum Required Daily Command Set (Solo Operator):**
1. `status`
2. `pre-alpha-daily-operator-content-run-summary`
3. `pre-alpha-platform-manual-templates-summary`
4. `pre-alpha-manual-publish-record-summary`

**Optional Post-Publish Command Set:**
1. `pre-alpha-manual-performance-record-summary`
2. `pre-alpha-content-performance-review-summary`

## 5. Gap Report Summary

- **Is the daily operator path usable today?** Yes, as a manual, fixture-driven control plane, the sequence is logical and clearly documented after 0118.
- **Are manual publish/performance records and review behaviors understandable?** Yes, the 0115-0117 tasks resolved the major ambiguity and enforced strict fail-closed requirements.
- **Are there still too many commands?** There are many internal commands, but `operator-command-summary` cleanly isolates the 6 operator-facing ones.
- **Are any outputs too JSON-heavy for a solo operator?** Yes. All summaries emit JSON objects. For daily use, an operator must scroll through dense JSON structures. 
- **What should be fixed before adding any new features?** The JSON output format is the biggest barrier to actual human usability right now. 
- **Should next task be artifact intake, experiment planner, or UX polishing?** UX polishing (specifically, Markdown exports for the daily workflow). Adding real artifact intake while the output is raw JSON will make the JSON larger and harder to read.

## 6. Recommended Next Tasks

### Recommendation 1
- **Task Label:** `TASK_CONTENTOPS_0121_OPERATOR_READABLE_MARKDOWN_EXPORTS_FOR_DAILY_WORKFLOW_V0`
- **Objective:** Convert the primary `pre-alpha-daily-operator-content-run-summary` and `pre-alpha-platform-manual-templates-summary` JSON outputs into clean, copy-paste-ready Markdown.
- **Why Now:** The current JSON summaries are difficult for a human to parse quickly. Before attaching real content pipelines, the output must be operator-friendly.
- **Risk:** Low. Formatting change only.
- **Allowed Scope:** Modifying the CLI summary output format for operator commands.
- **Forbidden Scope:** No new packets, no network/LLM/API features.
- **Validation:** Visual inspection of CLI output.

### Recommendation 2
- **Task Label:** `TASK_CONTENTOPS_0121_APPROVED_CAPITAL_CHRONICLE_ARTIFACT_INTAKE_CONTRACT_V0`
- **Objective:** Create a secure, local-only JSON schema/contract to ingest "approved" articles from the core Capital Chronicle repository into this local control plane.
- **Why Now:** If the operator accepts JSON-heavy UX, the next architectural step is replacing mock `content_seeds` with real approved content.
- **Risk:** Medium. Requires strict boundary enforcement to prevent coupling or auto-publishing.
- **Allowed Scope:** New schema `pre_alpha_artifact_intake.schema.json`, fixture, and basic adapter logic.
- **Forbidden Scope:** No live repo scraping. Must be a local file drop/fixture process.
- **Validation:** Validation against new intake schema and security scans.

### Recommendation 3
- **Task Label:** `TASK_CONTENTOPS_0121_PRE_ALPHA_EDITORIAL_EXPERIMENT_PLANNER_V0`
- **Objective:** Create a packet that takes the `editorial_hypotheses` generated in the content performance review and surfaces them as constraints/suggestions in the next day's operator run.
- **Why Now:** Completes the local feedback loop defined in the architecture.
- **Risk:** Medium. Must avoid creating an autonomous loop.
- **Allowed Scope:** Schema, module, and integration into the daily run packet.
- **Forbidden Scope:** No autonomous LLM re-prompting.
- **Validation:** End-to-end dry run.

## 7. Safety Findings

All components currently completely preserve the hard boundaries:
- **`local_only`**: Strictly enforced.
- **No network/provider/LLM/web/search**: Strictly enforced.
- **No platform API/scraping/automatic metrics ingestion**: Strictly enforced.
- **No credential/.env reads**: Validated via codebase scan; none present in the execution path.
- **No fake alpha / inferred publication / statistical significance**: Explicitly blocked in schemas and fixtures.

## 8. "Do Not Build Yet" List
- **Do not build** any automated platform API integration (X, LinkedIn).
- **Do not build** any LLM "auto-drafter" or "auto-reviewer" loops.
- **Do not build** live scraping or automated metrics fetching.
- **Do not build** integrations that modify the core Capital Chronicle repository.
