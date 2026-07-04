# Project Source Export — after 0174 rollback (minimal)

## Authority hierarchy (most authoritative first)
1. Future pasted Cline evidence packets and committed repo evidence.
2. Current accepted repo state after rollback (HEAD 496591f).
3. Capital Chronicle ContentOps Institutional Cockpit Master Plan.
4. The Stitch folder as **advisory visual reference only** (not runtime authority,
   not imported directly).
5. Older AFTER_0169 sources as historical context only.

Chat history is not authority. Uploaded Project Sources are context, not repo truth.

## Hard boundaries (non-negotiable)
- Static/local-only UI. No backend/server, no dependencies, no remote CDNs/fonts.
- No network, fetch, XMLHttpRequest, WebSocket, EventSource in runtime assets.
- No env/credential reads. No API calls (platform/provider/Telegram/web/search/market).
- No live posting, scheduler, scraping, autonomous replies/DMs, one-button publish-all.
- No active export/capture/upload controls. No browser/Antigravity in build tasks.
- Kill switch active. Not public-postable. No public-ready final copy.
- No financial advice / buy-sell-hold / signal-service / trading-bot / execution /
  broker / order-routing / price-target / guaranteed-prediction framing.
- No market-direction color semantics. No secrets in files/evidence.
- Current vs historical metadata must be explicitly separated (0172 drift guard).

## Why the text-only 0174 spike was aborted
- The first 0174 attempt was built mostly from a textual design contract.
- That is no longer accepted as sufficient for visual fidelity.
- It was uncommitted, then fully rolled back. HEAD remained 496591f.

## Why 0174R must be reference-driven
- The operator wants a frontend build driven by the local Stitch HTML/CSS reference,
  to achieve real visual fidelity instead of text-only approximation.
- Primary reference (local path, not copied, not imported as runtime):
  `C:\Users\bullw\Downloads\stitch_capital_chronicle_governance_terminal\stitch_capital_chronicle_governance_terminal`

## Constraints for 0174R
- Do **not** use `design_reference/` as the primary source.
- Do **not** import Stitch HTML directly as runtime UI.
- Do **not** add remote dependencies, CDNs, Google Fonts, or Material Symbols remote links.
- Preserve the 0172 source-of-truth / drift-guard semantics and all hard boundaries.
- Preserve and do not replace the existing `ui/institutional_shell/`.
