# Pre-Alpha Content Lane Policy (After 0127)

**Task:** `TASK_CONTENTOPS_0127_PRE_ALPHA_CONTENT_LANE_POLICY_RECOVERY_V0`

## Purpose
This policy formalizes the strategic boundaries for Capital Chronicle's ContentOps during the pre-alpha wait state. It defines what can be built and processed now, and what remains strictly blocked.

### Why Build Audience Before Internal Alpha?
ContentOps should aggressively build an audience during the wait state by focusing on educational and process-oriented content. Building trust through transparency (e.g., explaining our data sufficiency standards, failure forensics, and macroeconomic realities) creates a receptive audience for when the real alpha signals arrive.

### Why Artifact-Backed Content Remains Blocked
Any content claiming to be backed by Capital Chronicle's internal models or data signals is strictly blocked until real, approved artifacts exist. Promoting a "signal" without the formal cryptographic and data lineage proofs violates the core product philosophy. 

### Core Rule: News is a Hook, Not a Signal
When current events are discussed, they must strictly serve as educational hooks. A news event may be used to explain why markets overreact or how data is incomplete. It must **never** be used to issue a market call. News is a hook, not a signal.

## Content Lane Definitions
1. **`pre_alpha_general_process`:** Safe audience-building content focusing on education, philosophy, and build-in-public process notes. No artifact claims.
2. **`grounded_news_context`:** Current events used purely as context for educational commentary. Strict prohibition on signal language.
3. **`future_artifact_backed_cc`:** The restricted lane for actual alpha artifacts. Blocked unconditionally unless accompanied by verified `source_artifact_ids` that have passed formal intake.

## Safe Content Subtypes
The validator explicitly recognizes these subtypes:
- `build_in_public`
- `macro_education`
- `data_sufficiency`
- `forecast_readiness`
- `failure_forensics`
- `product_philosophy`
- `official_data_explainer`
- `policy_process_commentary`
- `macro_education_from_news`
- `forecast_readiness_from_news`
- `data_sufficiency_from_news`
- `failure_forensics_from_news`
- `product_update`

## Forbidden Language and Constraints
The local deterministic validator fails closed if it detects:
- `public_postable`, `publish_ready`, or `auto_publish` set to true.
- Use of live credentials, `.env` reads, or platform payload generation.
- Claims of "artifact-backed" status without real references.
- Financial signal or advisory language (e.g., buy, sell, hold, long, short, entry, exit, target, position sizing, signal, model says, execution, broker, order-routing).
- Pre-alpha lane content claiming DQR, lineage, or forecast readiness.

## Architectural Relationships
- **Task 0128 (Grounded Research Brief):** This policy governs how news hooks are structured before they are formalized into grounded research briefs.
- **Task 0129 (LLM-Assisted Draft Review):** Defines the boundary for what external drafts are allowed to discuss before deterministic review.
- **Task 0130 (Platform Dry-Run):** Enforces that valid policy packets can only proceed to dry-run mock payloads, never live API dispatch.

## Milestone Status
*Note: There is no Project Sources refresh after this task. Refresh bundles are reserved for major architectural milestones.*
