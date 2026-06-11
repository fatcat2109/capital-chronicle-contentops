# Stitch Operator Cockpit — Cline README (Read First)

This is the primary document future Cline tasks should read first before any
Operator Cockpit V2 frontend work.

## 1. Status

- Quarantined visual reference only.
- Not runtime authority.
- Not product UI.
- Do not import raw HTML directly.
- Do not copy into `ui/`.
- Read this file before any Operator Cockpit V2 frontend task.

## 2. Source and Destination

- Original local Stitch folder:
  `C:\Users\bullw\Downloads\stitch_capital_chronicle_governance_terminal\stitch_capital_chronicle_governance_terminal`
- Repo quarantine destination:
  `docs/design_references/stitch_institutional_ai_operator_cockpit/`
- Manifest:
  `docs/design_references/stitch_institutional_ai_operator_cockpit/manifest.json`
- Raw references:
  `docs/design_references/stitch_institutional_ai_operator_cockpit/raw/`
- Extraction notes:
  `docs/design_references/stitch_institutional_ai_operator_cockpit/notes/extraction_notes.md`
- Quarantine policy:
  `docs/design_references/stitch_institutional_ai_operator_cockpit/notes/quarantine_policy.md`

## 3. What Cline Should Use

Adopt these patterns (translated into local code):

- Dark technical matte operator cockpit aesthetic.
- Fixed top safety ribbon.
- Left navigation.
- Global state header.
- Dense evidence panels.
- Gate matrix layouts.
- Compact status tokens.
- Sharp panel grid.
- Mono data typography.
- Clear disabled/future-only control treatment.
- Compliance/evidence-vault table patterns.
- Screenshot-safe local-only labels.

## 4. What Cline Must Not Use

Reject these patterns:

- CDN/Tailwind runtime imports.
- Google Fonts remote dependency.
- Material Symbols remote dependency.
- Direct raw HTML runtime import.
- Action-looking publish/send/schedule controls.
- Stale current metadata.
- Ambiguous accepted HEAD labels.
- Platform dashboard affordances that imply live posting.
- Browser/API/platform/network behavior.
- Public-ready copy.
- Market-direction colors.
- Decorative SaaS polish that weakens operator clarity.

## 5. Runtime Translation Rules

- Raw reference may use Tailwind/CDN/fonts/icons, but V2 runtime must not.
- Translate visual tokens into local CSS (variables, system font stacks).
- Replace remote icons with local text/inline-safe symbols or CSS-only
  indicators.
- Convert action-looking controls into inspect-only, disabled-with-reason, or
  future-only records.
- Convert platform cards into gate matrix records.
- Keep state-before-action grammar (state/gate before any action surface).
- Keep current vs historical provenance separated. Current truth comes from a
  single canonical global state; historical/reference provenance is explicitly
  labelled "Not Runtime Authority".

## 6. Previous Prototype Failure Modes

Why copying the reference style directly would fail:

- External runtime dependencies (CDN, fonts, icons) break local-only,
  offline, no-network guarantees.
- Raw prototype links/CDNs would be flagged by runtime dependency scans.
- Active-looking refresh/history/send controls imply live capability.
- Stale accepted HEAD / current gate labels (e.g. 444ef2c, 1c03ca0,
  0161/0164/0170 gates) misrepresent current truth.
- Current truth mixed with historical provenance creates audit ambiguity.
- Platform cards that look dispatch-capable imply live posting.
- Layout clipping/overflow risk at common desktop widths.
- Large unlabeled dead zones reduce operator clarity.
- Status badges without evidence/reason/allowed/blocked actions are not
  evidence-grade.
- Insufficient distinction between dry-run readiness and live publish
  readiness invites unsafe assumptions.

## 7. Required Future 0174R Behavior

Future 0174R (or any cockpit frontend task) must:

- Read this CLINE README first.
- Inspect `manifest.json` and the `raw/` references.
- Extract visual tokens (see `notes/extraction_notes.md`).
- Implement clean local static V2 under `ui/institutional_operator_cockpit_v2/`.
- Preserve `ui/institutional_shell/`.
- Use current repo baseline and product/code baseline labels correctly
  (current repo baseline vs last product/code baseline vs historical
  provenance, all distinct).
- Commit/push to GitHub.
- Not run browser/Antigravity.

Note: an accepted static V2 already exists under
`ui/institutional_operator_cockpit_v2/` from the accepted 0174R commit. This
quarantine import does not modify it; it provides the durable in-repo
reference for future iterations.

## 8. Evidence References

- `stitch_institutional_ai_operator_cockpit/manifest.json`
- `stitch_institutional_ai_operator_cockpit/notes/quarantine_policy.md`
- `stitch_institutional_ai_operator_cockpit/notes/extraction_notes.md`

