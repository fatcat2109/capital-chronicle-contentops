# Capital Chronicle ContentOps Pre-Launch Operating Policy

This document is the authoritative pre-launch operating policy for the `cc-live-contentops` repository. It governs all development, implementation, testing, QA, and operator procedures during the pre-launch phase.

---

## 1. Project State and Product Surface
- **Active Pre-Launch State:** The project has moved beyond early pre-alpha wait-state and planning postures. It is actively approaching pre-launch readiness.
- **Active Product Surface:** Capital Chronicle ContentOps V5 (located at `ui/contentops_v5/`) is the primary active product surface. It is a modern React/Vite/Tailwind-based application implementing the flagship operational screens.
- **Legacy Fallback:** The V4 shell (`ui/institutional_operator_cockpit_v4/`) is frozen and remains as a fallback and visual/safety baseline reference only.

---

## 2. Execution Agency & Tooling
- **Default Agent:** Antigravity is the default implementation and Browser QA agent for this repository.
- **Two Execution Modes:**
  1. **Implementation Mode:** Allowed to make bounded source edits, run tests, verify static conditions, make local visual checks, and commit/push. Cannot claim final visual PASS or modify browser QA evidence.
  2. **Browser QA Mode:** Allowed to run the browser subagent, capture screenshots, compile visual reports, and generate audit-only evidence packets. Cannot edit source code or commit changes.

---

## 3. Repo Authority Hierarchy
To resolve conflicting rules or strategy models, the hierarchy of authority is:
1. This document (`docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md`) for operating rules and runtime boundaries.
2. The V5 Master Plan (`docs/CAPITAL_CHRONICLE_CONTENTOPS_V5_FINAL_MASTER_PLAN_AND_NORTH_STAR.md`) for product scope and flagship view specifications.
3. Reconciled Roadmap (`docs/CAPITAL_CHRONICLE_CONTENTOPS_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AFTER_0174AO.md`).
4. Other strategy and historical recovery indices (treated as historical context/references only).

---

## 4. Credential & .env Readiness Policy
“ContentOps pre-launch tasks may perform explicitly scoped, local-only .env presence and shape checks. Raw secret values must never be printed, logged, committed, screenshotted, rendered in the browser, or included in evidence packets. The browser UI must not read .env. Live platform/provider calls remain disabled until a separate platform/provider gate explicitly authorizes a bounded validation or posting task.”

- **Redacted Shape Checks:** Pre-launch readiness modules may check for the presence/absence of required keys in `.env` and validate their formats minimally (e.g., matching known patterns like Telegram bot token structures) without loading or printing the actual secret value.
- **Fingerprints only:** Only non-leaking, redacted shape classes (e.g. `present_redacted_telegram_bot_token_like`) may be persisted or reported. Never print prefixes, suffixes, lengths, or cryptographic digests of real secrets.
- **UI Constraint:** The browser runtime/UI must remain completely free of `.env` or `process.env` access.
- **No Commits:** Never stage or commit a `.env` file containing real secret values.
- **No Screenshots:** Never capture browser screenshots or QA logs showing raw credentials.

---

## 5. Provider, Platform, and Live Gate Policy
- **Live Gated by Default:** All live provider API calls and platform publishing adapters remain disabled in general tasks.
- **Platform-by-Platform Enabling:** Each target platform (Telegram, X, LinkedIn, Meta, TikTok, etc.) must be enabled separately. Telegram is the first candidate; others will follow.
- **Automation Constraints:**
  - Any future platform dispatch requires a manual "operator GO" confirmation, active kill switch, redacted audit trail, rate-limiting/error handling, and manual fallback/rollback plans.
  - No autonomous replies or DMs.
  - No unsupervised schedulers or auto-posting.

---

## 6. Manual Publish and Metrics Policy
- **Operator Execution:** Operators must publish social posts manually using rendered platform previews.
- **Audit Trails:** Every manual publication must be recorded in the local audit log with the exact manual publication timestamp, destination URL, and subsequent metrics captures.

---

## 7. Content Safety and Compliance
Content safety is non-negotiable. Content generated, reviewed, or previewed within ContentOps must strictly avoid:
- **No Financial Advice:** Never issue buy/sell/hold directives, asset allocations, or position sizing.
- **No Signal-Service Framing:** Avoid price targets, execution calls, order-routing language, and claims of "guaranteed returns" or "model predictions."
- **Data Sufficiency:** Maintain discipline in citing official sources, explaining data limitations, and clarifying that market data is context/teaching material, not a call.
- **No Public Fixtures:** Never post local/synthetic fixture content to public channels.

---

## 8. Allowed Local Scope & Forbidden Behaviors
- **Allowed Scope:** Local filesystem operations, local testing, UI assembly, local mock data generation, and offline pre-launch validation checks.
- **Forbidden Behaviors:** Unsupervised web scraping, unauthorized network requests, external provider API execution, and direct mutation of the Capital Chronicle core ingestion repository.

---

## 9. Evidence & Commit Discipline
- **Zero-Trust Validation:** Never accept PASS claims at face value.
- **Evidence Verification:** Every task must document its starting/final HEAD, files changed, and validation command outputs.
- **Clean Commits:** Do not stage unrelated cache files or local build noise.
- **No Deletion of QA Evidence:** Never delete past browser QA screenshots, visual verification records, or accepted task evidence packages.

---

## 10. Next-Task Handoff Discipline
- Every completed task must explicitly specify the exact next recommended task matching the pre-launch roadmap.
- The next recommended task for credential readiness validation is:
  `TASK_CONTENTOPS_0174CH_PRELAUNCH_CREDENTIAL_READINESS_DRY_RUN_AND_REDACTION_HARNESS_V0`
