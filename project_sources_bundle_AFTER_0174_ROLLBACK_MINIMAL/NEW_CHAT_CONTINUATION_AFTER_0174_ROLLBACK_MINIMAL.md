# New Chat Continuation — paste-ready prompt (after 0174 rollback)

Copy the block below into a new ChatGPT Project chat.

---

You are continuing the Capital Chronicle ContentOps project. Do not rely on old chat
history; treat uploaded Project Sources as context, not repo authority.

Current accepted state:
- Accepted current HEAD is 496591f ("test: add institutional shell view model drift guard").
- The interrupted text-only 0174 Operator Cockpit V2 spike was uncommitted and has been
  fully rolled back. No 0174 artifacts remain. The old institutional shell is untouched.
- 0172 (view-model source-of-truth + drift guard) is accepted PASS.

Next task:
- TASK_CONTENTOPS_0174R_REFERENCE_DRIVEN_OPERATOR_COCKPIT_V2_FRONTEND_REBUILD_V0.
- This must be a reference-driven frontend rebuild using the operator's local Stitch
  folder for visual fidelity (advisory reference only, not imported as runtime, not copied
  wholesale):
  C:\Users\bullw\Downloads\stitch_capital_chronicle_governance_terminal\stitch_capital_chronicle_governance_terminal
- Do not use design_reference/ as the primary source. Do not import Stitch HTML directly.
  Do not add remote dependencies/CDNs/Google Fonts/Material Symbols remote links.

Hard boundaries (preserved):
- Static/local-only, no backend, no dependencies, no network/fetch/sockets.
- No env/credential reads, no API calls, no live posting/scheduler/scraping.
- No browser/Antigravity in build tasks, no screenshots/exports, not public-postable.
- No financial advice/signal/trading framing, no market-direction color semantics, no secrets.
- Preserve 0172 source-of-truth/drift-guard semantics; current vs historical metadata stays separated.
- Do not replace the existing ui/institutional_shell/.

Working agreement:
- When I paste a Cline evidence packet, audit it first before proposing next steps.
- When I ask for a worker prompt, produce a bounded, scoped Cline prompt with explicit
  allowed/forbidden scope, validation commands, and a FINAL EVIDENCE PACKET contract.
- Reserve room for me to upload Stitch HTML/CSS and browser/Antigravity screenshots
  separately when visual review is needed.

---
