# Stitch Visual Reference Extraction — 0174R

Task: TASK_CONTENTOPS_0174R_REFERENCE_DRIVEN_OPERATOR_COCKPIT_V2_FRONTEND_REBUILD_V0

This document records the visual tokens and patterns extracted from the
operator-supplied local Stitch governance terminal folder and how they were
adopted, adapted, or rejected when building the clean-room Operator Cockpit V2
under `ui/institutional_operator_cockpit_v2/`.

The Stitch folder was treated as advisory visual reference ONLY. No Stitch HTML
was imported as runtime UI. No Stitch file was copied into the repo. No CDN /
remote font / remote icon / remote script dependency was carried over.

## Reference Folder Inspected

`C:\Users\bullw\Downloads\stitch_capital_chronicle_governance_terminal\stitch_capital_chronicle_governance_terminal`

Files inspected (read-only):
- `technical_matte_operator/DESIGN.md` (design tokens + system notes)
- `command_center_capital_chronicle/command_center_capital_chronicle.html`
- `publish_readiness_tower_capital_chronicle/publish_readiness_tower_capital_chronicle.html`
- `evidence_vault_capital_chronicle/evidence_vault_capital_chronicle.html`
- `*.png` screenshots present but used only as visual reference (not copied).

## Visual Tokens Extracted

- Colors: dark graphite base `#121417`, panel black-blue `#1A1D23`, inset
  `#000000`, technical border `#2A2E35`, outline-variant `#45474A`.
- Backgrounds: tonal layering (Level 0 base, Level 1 panel, Level 2 inset);
  zero gradients; flat depth.
- Panels/cards: 1px border, 1.25rem padding, sharp 0px corners.
- Borders: consistent 1px stroke for panels, inputs, table dividers.
- Typography: Inter-like UI + JetBrains-Mono-like data. Reference used remote
  Inter / JetBrains Mono via Google Fonts; we REJECTED remote fonts and mapped
  to local system stacks (Segoe UI / system-ui; Cascadia Mono / Consolas).
  Scale kept compact: 10-20px.
- Spacing: safety ribbon 32px, nav width 220px, gutter 1rem, panel padding
  1.25rem, tight 4px baseline rhythm.
- Radius: sharp 0px (brutalist), per DESIGN.md "Sharp (0px)".
- Sidebar/header: fixed 32px safety ribbon (never scrolls), 220px left nav,
  system header strip below ribbon, fixed bottom directive bar.
- Card/grid/table patterns: column grids with 1px gridlines, no row striping,
  monospace for IDs/data, 1px horizontal dividers.
- Status chip patterns: mono-spaced text inside a 1px border; color-coded by
  severity (low-opacity background, full-opacity border/text).
- Evidence/caveat patterns: grouped containers with mono-label headers; evidence
  index tables; tag strips of safety states.
- Disabled/future-only control patterns: reduced opacity, lock/×-marked rows,
  read-only policy text only — no actionable affordance.

## Adopted Patterns

- Technical Matte dark institutional aesthetic; flat depth via tonal layers.
- Fixed 32px top safety ribbon with safety chips.
- 220px left navigation with cyan active left-border indicator.
- System header strip exposing global state.
- Sharp 0px corners, 1px technical borders, compact mono data.
- Status chip grammar (status + severity + reason).
- Gate matrix table and evidence index table layouts.
- Blocked/forbidden action matrix as locked, read-only tiles.

## Adapted Patterns

- Color semantics constrained strictly to system safety (cyan info, green pass,
  amber review/pending, red block/kill switch). No bull/bear semantics.
- Remote Inter / JetBrains Mono replaced with local system font stacks.
- Tailwind utility classes and the Tailwind config replaced with a small local
  stylesheet using CSS variables.
- Material Symbols icon font replaced with text/CSS marks (e.g. "×") so no
  remote icon dependency is required.
- Global metadata reworked to separate Current Repo Baseline (`680d03d`) and
  Last Product Code Baseline (`496591f`) from historical screen provenance.

## Rejected Patterns (and why)

- Tailwind CDN script (`cdn.tailwindcss.com`): external runtime dependency.
- Google Fonts `<link>` for Inter / JetBrains Mono: remote font dependency.
- Material Symbols Outlined remote font: remote icon dependency.
- Stitch "ACCEPTED HEAD 444ef2c" and per-screen "SCREEN BASELINE 1c03ca0" shown
  as current: mixes historical provenance with current truth. Rejected; these
  heads appear only under explicitly labelled historical provenance.
- Footer "ACKNOWLEDGE & PROCEED" action button and platform "send/close" icons:
  action-looking affordances implying live capability. Rejected; replaced with
  read-only directive text and disabled/locked rows.
- Decorative gradient accent line on the tower header: DESIGN.md mandates zero
  gradients; rejected for consistency.
- Stale gate copy referencing 0161/0164/0170 browser QA as current: rejected;
  current gate reflects 0174R audit-pending state only.

## Safety Confirmations

- No Stitch HTML imported as runtime; no Stitch file copied into the repo.
- No remote dependency, CDN, remote font, remote icon, or remote script.
- No runtime network (`fetch` / `XMLHttpRequest` / `WebSocket` / `EventSource`).
- No env/credential reads; no secrets displayed.
- Existing `ui/institutional_shell/` preserved and unmodified.
