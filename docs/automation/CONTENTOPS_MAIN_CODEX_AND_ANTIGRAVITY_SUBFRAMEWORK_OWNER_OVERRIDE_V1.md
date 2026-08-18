# ContentOps Main (Codex) and Sub (Antigravity) Execution Frameworks — Owner Override

Authority date: 2026-08-18  
Status: `OWNER_OVERRIDE_ACTIVE`  
Supersedes: Prior requirement that native Codex Desktop HIGH/XHIGH availability is a mandatory prerequisite during an explicitly selected `SUB_ANTIGRAVITY` run, and clarifies single-conversation SUB_ANTIGRAVITY architecture.

---

## 1. Owner Decision & Execution Framework Hierarchy

ContentOps recognizes two canonical execution frameworks with fundamentally distinct orchestration architectures:

### 1.1 MAIN FRAMEWORK (`MAIN_CODEX`) — Default (Multi-Session Orchestration)
- **Role**: Primary execution and newsroom orchestration framework whenever Codex quota, capacity, and Desktop tooling are available.
- **Orchestration**: Multi-session. Primary Codex Desktop conversation owns the task and may invoke separate authorized model conversations/workers:
  - Coordinator reasoning operates on `gpt-5.6-sol` / `HIGH`.
  - Editorial and consequential creative roles operate on fresh isolated `gpt-5.6-sol` / `XHIGH` workers.
  - Grounded research / evidence assistance follows the deterministic 9Router ladder (`vx/gemini-3.1-pro-preview(high)` → `vx/gemini-3.5-flash(high)`).
- **Invariants**: Existing V1 and V2 deterministic authority, four-task pause state, and safety contracts remain exact.

### 1.2 SUB FRAMEWORK (`SUB_ANTIGRAVITY`) — Explicit Fallback (Single-Session Orchestration)
- **Role**: Secondary execution framework used strictly when Codex quota or capacity is unavailable.
- **Precondition**: Explicit owner / task selection required. It is **never** auto-switched on exception, timeout, rate-limit, or provider error.
- **Orchestration**: Single-session. **ONE already-configured Antigravity conversation performs the ENTIRE task.**
  - There is no second Antigravity chat.
  - There is no model spawning.
  - There is no model switching.
  - There is no Codex call.
  - There is no separate XHIGH worker.
  - There is no runtime model routing.
  - There is no requirement for ContentOps to know or bind the Antigravity model identity.
  - The active Antigravity conversation itself performs every LLM-intelligence step required by the task: research judgment, filtering, story selection, editorial reasoning, article writing, review/revision, creative decisions, and task orchestration.
  - No legacy 9Router article-writer fallback.
  - Deterministic ContentOps code performs its normal non-model duties: source/evidence validation, numeric authority, rights, readiness, media contracts, rendering mechanics, `DurablePublicationCoordinator`, `UNKNOWN_WRITE`, destination identity, readback, reconciliation, etc.

---

## 2. Framework Isolation & Integrity Rules

1. **No Opportunity Mixing**: A single editorial opportunity or newsroom cycle is executed entirely within one framework (`MAIN_CODEX` or `SUB_ANTIGRAVITY`). Switching frameworks mid-opportunity is strictly forbidden and fails closed.
2. **Framework Binding**: The active framework identity (`MAIN_CODEX` or `SUB_ANTIGRAVITY`) is persisted at opportunity start (`rolling_x_framework_binding_v1.json`) to prevent mid-opportunity switching.
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
