# ContentOps Main (Codex) and Sub (Antigravity) Execution Frameworks — Owner Override

Authority date: 2026-08-18  
Status: `OWNER_OVERRIDE_ACTIVE`  
Supersedes: Prior requirement that native Codex Desktop HIGH/XHIGH availability is a mandatory prerequisite during an explicitly selected `SUB_ANTIGRAVITY` run.

---

## 1. Owner Decision & Execution Framework Hierarchy

ContentOps now recognizes two canonical execution frameworks:

### 1.1 MAIN FRAMEWORK (`MAIN_CODEX`) — Default
- **Role**: Primary execution and newsroom orchestration framework.
- **Precondition**: Used whenever Codex quota, capacity, and Desktop tooling are available.
- **Model Seam**:
  - Coordinator reasoning operates on `gpt-5.6-sol` / `HIGH`.
  - Editorial and consequential creative roles operate on fresh isolated `gpt-5.6-sol` / `XHIGH` workers.
  - Grounded research / evidence assistance follows the deterministic 9Router ladder (`vx/gemini-3.1-pro-preview(high)` → `vx/gemini-3.5-flash(high)`).
- **Invariants**: Existing V1 and V2 deterministic authority, four-task pause state, and safety contracts remain exact.

### 1.2 SUB FRAMEWORK (`SUB_ANTIGRAVITY`) — Explicit Fallback
- **Role**: Secondary execution framework used strictly when Codex quota or capacity is unavailable.
- **Precondition**: Explicit owner / task selection required. It is **never** auto-switched on exception, timeout, rate-limit, or provider error.
- **Model Seam**:
  - The currently selected Antigravity model performs **all** model-driven roles required by the active task (coordinator reasoning, grounded evaluation, and final editorial authorship/review).
  - Codex is neither called, required, nor fallen back to during a `SUB_ANTIGRAVITY` opportunity.
  - Fresh-isolated child session requirements that are inherently Codex Desktop-specific are waived for `SUB_ANTIGRAVITY`, while logical role separation and exact governed-input hash binding remain strictly enforced.
  - No legacy 9Router article-writer fallback.
  - No spoofing or fake Sol / XHIGH model receipts; evidence packets must truthfully declare `SUB_ANTIGRAVITY` and the actual bound Antigravity model identity.

---

## 2. Framework Isolation & Integrity Rules

1. **No Opportunity Mixing**: A single editorial opportunity or newsroom cycle is executed entirely within one framework (`MAIN_CODEX` or `SUB_ANTIGRAVITY`). Switching frameworks mid-opportunity is strictly forbidden and fails closed.
2. **Actual Model Binding**: No specific Antigravity model name is permanently hard-coded into durable authority. Each `SUB_ANTIGRAVITY` execution packet must bind and record the actual active model identity.
3. **Probationary Status**: The `SUB_ANTIGRAVITY` framework is currently **probationary** until real V1/V2 acceptance evidence confirms adequate quality, consistency, and compliance.
4. **Gate Failure Protocol**: If a `SUB_ANTIGRAVITY` run fails any factual, numeric, Institutional Edge, evidence, SEO, or reader-value gate, the system must **stop and return to MAIN_CODEX** when Codex capacity is restored. Gates, thresholds, and evidence standards must **never** be weakened to accommodate model differences.

---

## 3. Critical Non-Model Authority (Immutable)

Under both `MAIN_CODEX` and `SUB_ANTIGRAVITY`, models and frameworks possess zero authority over:

- **Factual truth**;
- **Numeric calculations and data series**;
- **Capital Chronicle proprietary analytical models, scenarios, and forecasts**;
- **Rights, licensing, and provenance**;
- **Credentials and session management**;
- **Destination and browser identity**;
- **Publication and public-write operations**.

Authoritative source records, Capital Chronicle read-only catalog data, deterministic validators, destination readiness checks, `DurablePublicationCoordinator`, browser profile locks, `UNKNOWN_WRITE` fail-closed handling, and strict readback/reconciliation remain outside all model surfaces.
