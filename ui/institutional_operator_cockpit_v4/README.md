# Operator Cockpit V4 — Clean-Room Frontend

Task: TASK_CONTENTOPS_0174E_OPERATOR_COCKPIT_V4_NORTH_STAR_CLEAN_ROOM_FRONTEND_BUILD_V0

A local-first, static, evidence-grade institutional cockpit. Clean-room build
(not a patch of V3). Implements the accepted north-star chain: the Institutional
Cockpit Master Plan, the 0174D V4 blueprint chain, and the Technical Matte
Operator brandkit translated into local CSS.

## How to open

Open `index.html` directly from the local filesystem (file://). No server, no
build step, no install. It loads only local `styles.css`, `view_model.js`, and
`cockpit.js`.

## Architecture

- `index.html` — shell: safety rail, truth rail, nav, screen body, in-flow footer.
- `view_model.js` — `window.CC_OPERATOR_COCKPIT_V4_MODEL`, the single canonical
  truth model (global state, safety locks, labeled truth rail, evidence refs,
  blocker stack, screen provenance, status tokens, seven screens).
- `cockpit.js` — render functions and nav switching only.
- `styles.css` — all local CSS, technical-matte identity, layout hardening.

## Seven screens

1. Command Center — full-width verdict band, blocker stack, evidence dependency map.
2. Content Studio — six governed lanes with claim-risk / forbidden-language /
   limitation / platform-fit / checklist panels.
3. Publish Readiness Tower — gate-matrix-first; platform rows are readiness
   records, not controls.
4. Evidence Vault — compliance room: validation matrix, timeline, caveat /
   forbidden-scope / active-blocker registries, confidence legend.
5. Content Calendar / Workflow — manual planning only; forbidden automated
   states shown disabled / future-only.
6. Visual Export / Screenshot-Safe — report cards, redaction preview, limitation
   strip, blocked-forecast explainer. Preparation only, no export.
7. Settings / Safety Policy — policy matrix + credential never-display registry.

## Safety boundaries (hard)

This frontend is local-only and static. It has:

- no runtime network, no fetch/XMLHttpRequest/WebSocket/EventSource/sendBeacon;
- no CDN, no remote scripts/stylesheets/fonts, no Material Symbols runtime;
- no localStorage/sessionStorage;
- no forms, no submit buttons;
- no platform/provider/Telegram API;
- no credential/env reads, no secrets (credentials render as SECRET_REDACTED);
- no live posting, no scheduler, no scraping;
- no financial advice, no signal/trading language, no market-direction color.

Color communicates governance safety only. PASS means validation-safe only —
never publish-ready, live-ready, forecast-ready, or market-positive.

## Provenance discipline

The truth rail distinguishes the current product HEAD and gate from historical
builds (V2/V3), the reference quarantine (Stitch), and evidence-only browser QA.
V3 is a failed candidate, not accepted as north-star UI. The 0174C browser QA
capture is accepted as evidence; the worker visual judgment is rejected.

## QA status

No browser QA, screenshots, or Antigravity were run in this task. Static
deterministic tests live in `tests/test_institutional_operator_cockpit_v4.py`
and `tests/test_institutional_operator_cockpit_v4_brandkit_taste.py`.
Visible browser QA is a future Antigravity task after the next build milestone.

## Brandkit / taste authority (0174F)

No dedicated repo "taste skill" doc was found (searched: taste, taste skill,
brandkit, Technical Matte, typography, block grammar, matte operator). Taste
authority for the 0174F hardening pass is therefore the accepted chain:
Institutional Cockpit Master Plan + DESIGN.md (Technical Matte Operator) + raw
Stitch HTML references + V3 failure evidence.

Typography follows DESIGN.md: Inter for UI/labels, JetBrains Mono for variable
data / hash IDs / evidence refs, compact 10-20px scale, hierarchy via color and
mono-spacing more than weight. Fonts are local preference stacks only
(`--font-ui`, `--font-mono`) with safe system fallback — no remote fonts, no
`@import`, no font links, no content networks. Surfaces use DESIGN.md tonal
layers (surface #141313, outline-variant #45474a), flat depth (no shadows/glow),
1px gridlines, and zero border radius. Color communicates governance safety
only — never market direction.
