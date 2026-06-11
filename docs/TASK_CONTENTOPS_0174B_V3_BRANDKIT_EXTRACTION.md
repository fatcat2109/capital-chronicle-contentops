# 0174B V3 Brandkit Extraction

Task: TASK_CONTENTOPS_0174B_OPERATOR_COCKPIT_V3_BRANDKIT_GROUNDED_CLEAN_ROOM_REBUILD_V0

This document is a PRE-CODE hard gate. V3 runtime files were not created until
this doc and the taste alignment plan existed and were read back.

## Source Confirmation (read before any code)

- DESIGN.md read: YES.
  Path: `docs/design_references/stitch_institutional_ai_operator_cockpit/raw/technical_matte_operator/DESIGN.md`
- All three raw Stitch HTML files read: YES.
  - `raw/command_center_capital_chronicle/command_center_capital_chronicle.html`
  - `raw/publish_readiness_tower_capital_chronicle/publish_readiness_tower_capital_chronicle.html`
  - `raw/evidence_vault_capital_chronicle/evidence_vault_capital_chronicle.html`
- Supporting notes read: STITCH_OPERATOR_COCKPIT_CLINE_README.md, manifest.json,
  extraction_notes.md, quarantine_policy.md, TASK_CONTENTOPS_0174R_STITCH_REFERENCE_EXTRACTION.md.
- V2 + browser QA context read: V2 README, 0174A qa_manifest/report/viewport_matrix,
  0174A2 visible_browser_qa_report/manifest/viewport_matrix.

Proof of reading (specific facts only present in those files):
- DESIGN.md front-matter names the system "Technical Matte Operator" and lists
  surface tokens `#141313`, `surface-container-lowest #0e0e0e`, `outline-variant #45474a`,
  `error #ffb4ab`, and typography `mono-label`/`mono-data` at 11/12px.
- DESIGN.md prose: "Zero Gradients", "Flat Depth", "Minimalist Brutalism",
  Level 0 `#121417` / Level 1 `#1A1D23` / Level 2 `#000000`, 1px border `#2A2E35`,
  sharp 0px shape language, cyan active 2px left nav bar.
- Raw command_center HTML loads `cdn.tailwindcss.com`, Google Fonts Inter +
  JetBrains Mono, and Material Symbols Outlined; safety ribbon chips read
  LOCAL ONLY / DRY RUN ONLY / REVIEW ONLY / MANUAL REVIEW REQUIRED / NOT PUBLIC
  POSTABLE / LIVE DISABLED; system header shows stale "ACCEPTED HEAD 444ef2c"
  and "CURRENT GATE 0170 browser qa evidence" plus action-looking history/refresh
  buttons.
- Raw publish_readiness HTML has a decorative gradient top-accent line
  (`bg-gradient-to-r ... via-primary`) and a `max-w-[1400px]` workspace.
- Raw evidence_vault HTML uses a `brutal-border` table "TASK EVIDENCE PACKET INDEX"
  with columns Task / Classification / HEAD / Artifact / Focused / Full Suite /
  Forbidden Scope, a diagonal-hatch safety banner, and a wrap-flex tag strip
  including KILL SWITCH ACTIVE (error) and MISSING DATA VISIBLE.


## Extracted Color Tokens

- Foundation (reference): base `#121417`, panel `#1A1D23`, inset `#000000`,
  border `#2A2E35`, outline-variant `#45474a`, on-surface `#e5e2e1`,
  on-surface-variant `#c6c6ca`, outline `#8f9094`.
- Functional accents (system safety only, never market direction):
  - cyan/blue: metadata, info nodes, active nav/focus.
  - amber: review-required / pending (cautionary, not warning).
  - red `#ffb4ab`: kill-switch active, blockers, critical failures.
  - green: validation pass / safe state.

## Backgrounds & Tonal Hierarchy

- Dark-mode-only. Depth is architectural via tonal stepping + 1px borders,
  never shadows or blur. Level 0 base / Level 1 panels / Level 2 insets.

## Typography System

- Inter for UI/labels; JetBrains Mono for variable data, hash IDs, evidence refs.
- Compact 10-20px scale. Roles: headline-lg 20px/600/-0.01em, headline-md 16px/600,
  body-md 13px/400/18px, body-sm 11px/400/16px, mono-label 11px/500/0.02em,
  mono-data 12px/400/16px, safety-status 10px/700 uppercase.
- Uppercase reserved for global safety statuses and labels.

## Spacing System

- safety-ribbon-height 32px, nav-width 220px, gutter 1rem, panel-padding 1.25rem,
  stack-sm 0.25rem, stack-md 0.75rem, 4px baseline rhythm.

## Radius / Shape Language

- Reference is Sharp (0px). V3 ADAPTS to a near-sharp 2-3px technical radius for
  a slightly more modern futuristic feel while staying non-decorative. Circular
  pills only for small binary status lights.

## Border / Stroke Language

- Consistent 1px strokes define panels/inputs/tables. Active state = cyan accent
  (2px left bar on nav; 1px cyan focus ring on inputs).

## Layout System

- Fixed-fluid hybrid console: persistent 32px safety ribbon (never scrolls),
  220px left nav, system header strip, column grid with 1px gridlines, fixed
  directive/status rail. Workspace centered with a max-width container.


## Component Grammar

- Safety ribbon chips: small rectangular tags, color-coded by severity.
- Status chips: mono text in a sharp border, low-opacity status-color fill,
  full-opacity border/text.
- Data tables: no row striping, 1px horizontal dividers, mono for IDs/numbers.
- Vertical nav: text list, cyan active text + 2px left bar.
- Evidence cards: grouped container with a mono-label header naming source/hash.
- Disabled/future-only controls: reduced opacity, lock/×, read-only policy text.

## Table / Matrix Grammar

- Evidence index table (Task/Classification/HEAD/Artifact/...).
- Publish readiness as a per-platform gate matrix (readiness records, not
  dispatch controls).

## Status / Severity Language

- Severity drives color only: info=cyan, ok=green, review=amber, block=red.
- PASS = system/validation-safe only; never publish/live/forecast/market-ready.

## Evidence Vault Patterns

- Evidence mode strip, tag strip, evidence packet index table, audit timeline,
  validation matrix, caveat registry, forbidden-scope registry, active blockers.

## Publish Readiness Tower Patterns

- Header panel with safety label, per-platform readiness rows, gate columns
  (docs/credential/approval/audit/kill switch/live/scheduler/posting), next blocker.

## Adopted Patterns

- Technical Matte dark institutional aesthetic; flat tonal depth.
- 32px safety ribbon, 220px nav with cyan active bar, system header strip.
- 1px borders, compact mono data, status chip grammar.
- Evidence index + gate matrix table grammar; safety tag strips.

## Adapted Patterns

- Color constrained strictly to system safety (no market direction).
- Remote Inter / JetBrains Mono -> local system font stacks.
- Tailwind utilities/config -> hand-written local CSS with variables.
- Material Symbols remote icon font -> local CSS-only marks / text glyphs.
- Sharp 0px -> near-sharp 2-3px + disciplined cool-accent glow on active surfaces
  only (futuristic, still conservative).
- Global metadata reworked to current lineage (c56ccd9 + dd55114/1024cdf/75f9d47).

## Rejected Runtime Patterns (and why)

- Tailwind CDN script: external runtime dependency.
- Google Fonts links: remote font dependency.
- Material Symbols remote font: remote icon dependency.
- Stale "ACCEPTED HEAD 444ef2c" / "CURRENT GATE 0170" / "0164" labels: stale
  current metadata; mixes historical provenance with current truth.
- Action-looking history/refresh buttons and footer publish affordances: imply
  live capability.
- Decorative gradient top-accent line: DESIGN.md mandates zero gradients.

## Exact V3 Implementation Mapping

- DESIGN tokens -> CSS custom properties in `styles.css` (`--surface-*`,
  `--accent-*`, `--font-ui/mono`, spacing scale).
- Ribbon/header/nav/main/directive -> semantic regions in `index.html`,
  rendered from `view_model.js` by `cockpit.js` (no network).
- Evidence index/gate matrix/tag strips -> DOM-built tables and chip rows.
- Severity -> CSS classes `sev-info/ok/review/block`; PASS caveat enforced in
  fixture text.
- Stale heads appear only under an explicitly labelled historical block.
