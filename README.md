# Capital Chronicle ContentOps

Capital Chronicle ContentOps is the local-first institutional editorial operating system and supervisor console.

---

## Current Status: Pre-Launch
We have transitioned from passive waiting-state and planning mode to **Active Pre-Launch**.
- The current flagship product surface is **V5** (React/Vite/Tailwind).
- The legacy **V4** shell remains frozen as a fallback and visual/safety baseline reference.
- **Default Runtime Agency:** Antigravity is the default implementation and Browser QA agent.

---

## Core Authority Documentation
- **Pre-Launch Operating Policy:** [CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md](docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md)
- **Cleanup Manifest:** [PRELAUNCH_REPO_DOCS_AND_RULES_CLEANUP_MANIFEST_0174CG.md](docs/governance/PRELAUNCH_REPO_DOCS_AND_RULES_CLEANUP_MANIFEST_0174CG.md)
- **V5 Master Plan & North Star:** [CAPITAL_CHRONICLE_CONTENTOPS_V5_FINAL_MASTER_PLAN_AND_NORTH_STAR.md](docs/CAPITAL_CHRONICLE_CONTENTOPS_V5_FINAL_MASTER_PLAN_AND_NORTH_STAR.md)
- **Standing Operating Rules:** [CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md](docs/CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md)
- **Latest Accepted Evidence Folder:** [qa_evidence_0174AM](qa_evidence_0174AM/)

---

## How to Run local V5
The V5 frontend is located under `ui/contentops_v5/`.

1. Navigate to the V5 directory:
   ```bash
   cd ui/contentops_v5
   ```
2. Install build-time dependencies:
   ```bash
   npm install
   ```
3. Start the Vite local development server:
   ```bash
   npm run dev
   ```

---

## Credential Readiness Policy
Under the **Pre-Launch Operating Policy**, scoped local-only `.env` presence and shape checks are permitted:
- Explicit pre-launch credential readiness tasks/modules may inspect `.env` keys.
- Real secret values must **never** be printed, logged, committed, screenshotted, or rendered in the browser.
- Only redacted shape classification tokens (e.g. `present_redacted_telegram_bot_token_like`) may be surfaced.
- The browser runtime/UI must never read or access `.env` or `process.env`.

---

## Live-Gate Constraints
All live/network behaviors remain strictly disabled by default until an explicit platform live-gate task authorizes them:
- **Telegram Live Gate:** First candidate, requires operator GO phrase, approval ledger, and active kill switch.
- **Other Platforms (X, LinkedIn, Meta, TikTok):** Future gated.
- **Autonomous Behaviors:** Unsupervised schedulers, autonomous replies/DMs, and automated public posting are strictly forbidden.
