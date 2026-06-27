# V6 Fast Ship Operating Profile

This document establishes the new default operating posture for Capital Chronicle ContentOps V6. It removes repeated dry-run/local-only ceremony and replaces it with a live-capable, execution-first architecture while retaining strict safety stop conditions.

## 1. Default Execution Posture
* **Heavy Batch by Default**: Execute complex setups, validation steps, and tests in combined batch tasks to maintain speed.
* **Fast Ship Over Ceremony**: Prefer direct code/evidence implementation over long repetitive state discussions or documentation.
* **Autopilot-Capable Implementation**: Antigravity builds, tests, self-debugs, commits, and pushes changes without requiring small, intermediary manual confirmation steps.
* **Progress-First Focus**: Focus on shipping functional lanes rather than repeatedly restating past status lanes.

## 2. Live / Env / Provider / Browser Posture
* **Environment Access**: Access to `.env` or system variables is permitted when a task explicitly scopes credential/permission validation, or live adapter setup.
* **Live Probes**: Read-only live calls or bounded write tests are allowed if explicitly named in the task scope.
* **Live Writes**: Live publishing actions are permitted only when explicitly scoped with platform/write family, request budgets, timeouts, payload hashes, explicit operator approvals, and redacted audits.
* **Browser/CDP Capability**: Allowed for QA validation, composition steps, post-publication checkpoints, and supervised adapter loops.
* **AI Provider Calls**: Allowed for AI grounding/writer tasks when scoped with request budgets, redaction policies, prompt templates, and schema validation.
* **Fallback Status**: Manual fallback playbooks and dry-runs remain fallback or blocked states, not the target production posture.

## 3. Hard Stop Conditions (Pipeline Blockers)
Pipeline execution must stop immediately if:
- Repository, branch, or current HEAD mismatches task parameters.
- Drift is detected on protected master files or plans.
- A raw secret key, token, auth header, or private cookie is printed/exposed.
- Unauthorized live platform writes are attempted without operator approval.
- Relevant unit or regression tests fail after bounded repair attempts.
- Contradictions are detected against official platform API documentation.
- Payload hash mismatch or destination binding mismatch occurs.
- Financial signals, advice, entry/exit indicators, or price predictions are generated.

## 4. Prompt Ceremony Reduction
Future tasks must omit long repeated disclaimers prohibiting live access, environment reads, browser usage, or provider APIs, unless a task is specifically a red-team security or compliance audit task. Safety boundaries are preserved through structural design rather than repeated chat instructions.
