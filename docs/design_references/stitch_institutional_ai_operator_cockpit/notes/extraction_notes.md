# Stitch Reference — Extraction Notes

Distilled from the quarantined raw Stitch reference files in `../raw/`. These
notes are the Cline-readable summary of the visual tokens and patterns. They
are advisory visual reference only and carry no runtime authority.

## Color Palette Observed

- Base background: `#121417` (Level 0). DESIGN.md also lists `#141313`.
- Panel surface: `#1A1D23` (Level 1).
- Inset surface: `#000000` (Level 2, inputs / sunken data).
- Technical border: `#2A2E35` (1px stroke). DESIGN.md outline-variant `#45474A`.
- Text on surface: `#e5e2e1`; variant `#c6c6ca`; dim `#8f9094`.

## Functional Accent Tokens (system status only)

- Cyan/blue `#a3defe` / primary `#c6c6ca`: metadata, info nodes, active nav.
- Amber `#ffd54f`: review-required / pending (cautionary, not warning).
- Red `#ffb4ab` / error: kill-switch active, blockers, critical failures.
- Green: validation pass / safe state.
- Semantics: color never implies market sentiment (no bull/bear). It only
  communicates governance/software gate health.

## Typography / Font Stack Observed

- UI typeface: Inter (loaded via Google Fonts in raw reference).
- Data/mono typeface: JetBrains Mono (Google Fonts in raw reference).
- Compact scale: 10px–20px. Uppercase for global safety statuses and labels.
- Hierarchy via color and mono-spacing more than weight.

## Spacing / Radius / Grid

- Safety ribbon height: 32px. Left nav width: 220px.
- Gutter: 1rem. Panel padding: 1.25rem. Tight 4px baseline rhythm.
- Radius: sharp 0px (brutalist). Only small status pills are circular.
- Column-based grid with 1px gridlines separating logical groupings.

## Sidebar / Header Observations

- Persistent 32px top safety ribbon (never scrolls) with safety chips.
- 220px left vertical nav; active item = cyan text + 2px left bar.
- Secondary system header strip below the ribbon exposing global state
  (system mode, accepted head, kill switch, current gate, next action).
- A fixed bottom directive bar appears in the Command Center reference.

## Card / Table / Gate-Matrix Patterns

- Modules/cards: 1px border, 1.25rem padding, no shadows, flat tonal depth.
- Data tables: no row striping, 1px horizontal dividers, mono for IDs/numbers.
- Publish readiness uses a platform capability registry grid with per-platform
  gate states (dry-run / live disabled / scheduling disabled / not public).
- Evidence vault uses an evidence packet index table with mono-label headers.

## Status Chip Patterns

- Mono-spaced text inside a sharp 1px border.
- Background is a low-opacity version of the status color; border/text full.
- Severity-coded (info/ok/review/block).

## Evidence / Caveat Panel Patterns

- Grouped evidence cards with a mono-label header describing source/hash.
- Tag strips of safety states (LOCAL ONLY, REVIEW ONLY, NOT PUBLIC POSTABLE,
  LIVE DISABLED, KILL SWITCH ACTIVE, SECRET REDACTED, NO FINANCIAL ADVICE,
  NO SIGNAL LANGUAGE, etc.).

## Disabled / Future-Only Control Style

- Reduced opacity, lock icon, low-contrast borders.
- Read-only policy text; no actionable affordance.

## Adopted Patterns

- Dark Technical Matte cockpit aesthetic; flat tonal depth.
- Fixed 32px safety ribbon; 220px left nav with cyan active indicator.
- System header strip exposing global state.
- Sharp 0px corners, 1px technical borders, compact mono data.
- Status chip grammar; gate-matrix and evidence-index tables.
- Locked/disabled blocked-action tiles.

## Adapted Patterns

- Color constrained strictly to system safety (no market direction).
- Remote Inter / JetBrains Mono -> local system font stacks.
- Tailwind utilities/config -> small local CSS with variables.
- Material Symbols remote icon font -> local text/CSS-only marks.
- Global metadata reworked to separate Current Repo Baseline from
  Last Product Code Baseline and from historical screen provenance.

## Rejected Runtime Patterns (and why)

- Tailwind CDN script: external runtime dependency.
- Google Fonts links: remote font dependency.
- Material Symbols remote font: remote icon dependency.
- "ACCEPTED HEAD 444ef2c" / "SCREEN BASELINE 1c03ca0" shown as current:
  mixes historical provenance with current truth.
- Footer "ACKNOWLEDGE & PROCEED" button and platform send/close icons:
  action-looking affordances implying live capability.
- Gradient accent line: DESIGN.md mandates zero gradients.
- Stale gate copy (0161/0164/0170 browser QA) shown as current.
