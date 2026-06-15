# ContentOps Reconciled Roadmap (After 0126)

**Task:** `TASK_CONTENTOPS_0126_STRATEGY_RECOVERY_AND_ROADMAP_RECONCILIATION_V0`

## Meta Architecture Guidelines
- **No Project Sources refresh after every task.** Project Sources refresh only occurs at milestone/new-chat/major-architecture boundaries or by explicit operator request.
- **Recovered historical docs (`recovered_strategy_docs/`) are reference material only**, not runtime product files.
- **Current accepted repo evidence wins** over recovered historical docs for runtime truth.
- **UI/UX/front-end design is part of the roadmap**, not an optional afterthought.
- **Front-end implementation must remain local-only** and fixture/mock-data-only until explicit GO.

---

## Forward Task Sequence

### `TASK_CONTENTOPS_0127_PRE_ALPHA_CONTENT_LANE_POLICY_RECOVERY_V0`
- **Objective:** Formalize the three content lanes (Pre-Alpha Process, Grounded News, Future Artifacts) as a codified local policy.
- **Allowed Scope:** Docs, schemas, local validation logic defining lane boundaries.
- **Forbidden Scope:** Live publishing, API integration, public-ready fake social generation.
- **Acceptance Criteria:** Policy enforced in local validation; rejects invalid lane mixing.
- **Stop Conditions:** Block if network access or credential reads are attempted.
- **Type:** Restores an old recovered capability.

### `TASK_CONTENTOPS_0128_GROUNDED_RESEARCH_BRIEF_CONTRACT_RECOVERY_V0`
- **Objective:** Re-integrate the Grounded Research Brief schema into the local validation flow to ensure news hooks are treated only as context, not signals.
- **Allowed Scope:** `grounded_research_brief` modules, schemas, tests.
- **Forbidden Scope:** Automated scraping, web search, LLM fetching.
- **Acceptance Criteria:** Manual grounded research brief fixtures pass validation while signal-language fails.
- **Stop Conditions:** Block if live web search or scraping is required.
- **Type:** Restores an old recovered capability.

### `TASK_CONTENTOPS_0129_LLM_ASSISTED_DRAFT_REVIEW_PACKET_RECOVERY_V0`
- **Objective:** Recover the deterministic review packet for externally generated drafts, enforcing style and safety boundaries.
- **Allowed Scope:** Draft review schemas, phase1_review tests, local validator functions.
- **Forbidden Scope:** API calls to LLMs for generation.
- **Acceptance Criteria:** A locally supplied, external LLM draft fixture is successfully audited and passed/blocked based on rules.
- **Stop Conditions:** Block if an LLM provider API key is requested.
- **Type:** Restores an old recovered capability.

### `TASK_CONTENTOPS_0130_CANONICAL_SOCIAL_POST_AND_PLATFORM_DRY_RUN_RECOVERY_V0`
- **Objective:** Establish the canonical social post object and integrate multi-platform dry-run renderers (X, LinkedIn, Telegram, etc.) based on platform adapter contracts.
- **Allowed Scope:** `platform_adapter_contracts.py`, rendering logic, mock payload schemas.
- **Forbidden Scope:** Real platform API dispatch.
- **Acceptance Criteria:** A canonical post renders correctly to platform-specific mock JSON payloads reflecting character limits and constraints.
- **Stop Conditions:** Block if external network payloads are formulated for dispatch.
- **Type:** Restores an old recovered capability.

### `TASK_CONTENTOPS_0131_APPROVAL_LEDGER_KILL_SWITCH_REDACTED_AUDIT_RECOVERY_V0`
- **Objective:** Re-implement the cryptographically safe local approval ledger, the master kill switch logic, and the redacted audit log.
- **Allowed Scope:** Security modules, local logging, state management.
- **Forbidden Scope:** Remote telemetry, internal IDE/brain log reads.
- **Acceptance Criteria:** Approved states are immutably logged; kill switch halts dry-run execution; secrets are provably redacted from logs.
- **Stop Conditions:** Block if internal logs are used as a backend.
- **Type:** Restores an old recovered capability.

### `TASK_CONTENTOPS_0132_MOCK_PUBLISH_AND_MANUAL_METRICS_READINESS_RECOVERY_V0`
- **Objective:** Wire end-to-end mock publishing flow that simulates API responses and updates metrics-readiness schemas.
- **Allowed Scope:** Local dry-run pipeline, mock adapters.
- **Forbidden Scope:** Real metrics ingestion from live platforms.
- **Acceptance Criteria:** A successful mock publish generates a synthetic URL and a manual metrics ingestion placeholder.
- **Stop Conditions:** Block if actual platform scraping is attempted.
- **Type:** Restores an old recovered capability.

### `TASK_CONTENTOPS_0133_PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK_V0`
- **Objective:** Create the advisory verification pack/checklists for operator validation of live platform API specs prior to unlocking live capabilities.
- **Allowed Scope:** Docs, markdown checklists, validation schemas.
- **Forbidden Scope:** Executing live verifications.
- **Acceptance Criteria:** Comprehensive checklists for X, LinkedIn, Telegram, FB, IG, TikTok exist and fail-closed by default.
- **Stop Conditions:** Block if live platform APIs are called.
- **Type:** Creates a new spec / Restores old concepts.

### `TASK_CONTENTOPS_0134_CREDENTIAL_ENVELOPE_AND_SECRET_POLICY_DESIGN_V0`
- **Objective:** Design the safe credential injection layer ensuring least-privilege, uppercase conventions, and env-var isolation.
- **Allowed Scope:** Architecture docs, mock env loader tests.
- **Forbidden Scope:** Reading real `.env` or operator secrets.
- **Acceptance Criteria:** Tests verify that synthetic secrets are correctly injected and instantly redacted from any output.
- **Stop Conditions:** Block if real `.env` file parsing is executed against operator state.
- **Type:** Creates a new spec / Restores old concepts.

### `TASK_CONTENTOPS_0135_OPERATOR_UI_UX_AND_CONTENT_CALENDAR_SPEC_V0`
- **Objective:** Draft the specification for the future front-end dashboard, approval queue visualizer, preview cards, and content calendar layout.
- **Allowed Scope:** Wireframe docs, markdown layout specs, JSON schemas for UI state.
- **Forbidden Scope:** Writing active front-end code (React/Vue/etc.).
- **Acceptance Criteria:** Detailed technical spec mapping API/mock payloads to UI components.
- **Stop Conditions:** Block if web server dependencies are added.
- **Type:** Creates a new spec.

### `TASK_CONTENTOPS_0136_FRONT_END_STATIC_PROTOTYPE_SPEC_V0`
- **Objective:** Build a local-only, interactive HTML/JS/CSS static prototype demonstrating the UI/UX spec using mock fixtures.
- **Allowed Scope:** Static front-end assets, binding to existing local JSON fixtures.
- **Forbidden Scope:** Backend server integration, live endpoints.
- **Acceptance Criteria:** A functional local dashboard displays preview cards and calendar views populated strictly by local fixtures.
- **Stop Conditions:** Block if network calls are made.
- **Type:** Creates a new spec.

### `TASK_CONTENTOPS_0137_SEO_NEWSLETTER_CONTENT_ARCHITECTURE_SPEC_V0`
- **Objective:** Define the architecture mapping for SEO metadata and Substack/Newsletter long-form distribution.
- **Allowed Scope:** Docs, schemas, template definitions.
- **Forbidden Scope:** Substack API integrations, SEO scraping.
- **Acceptance Criteria:** Clear mapping defined from grounded research briefs to long-form blog/newsletter templates.
- **Stop Conditions:** Block if live web scraping is required.
- **Type:** Creates a new spec.

### `Later: Supervised Live Pilot Design Gates`
- **Objective:** Unlock platforms one at a time via explicit operator GO only.
- **Allowed Scope:** Platform by platform capability unlocking.
- **Forbidden Scope:** Autonomous non-supervised posting.
- **Type:** Future milestone.
