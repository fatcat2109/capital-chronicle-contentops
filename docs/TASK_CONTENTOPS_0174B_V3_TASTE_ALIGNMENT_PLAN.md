# 0174B V3 Taste Alignment Plan

Task: TASK_CONTENTOPS_0174B_OPERATOR_COCKPIT_V3_BRANDKIT_GROUNDED_CLEAN_ROOM_REBUILD_V0

PRE-CODE hard gate. No V3 runtime code was written before this plan existed and
was read back. Confirmation: "no code until this plan exists" — SATISFIED.

## Taste / Design-Review Skill Availability

- Real taste/design-review skill/tool/instruction available: NO.
  Checked: no `.clinerules`, no `.kiro`, no taste/design-review markdown in repo.
- Therefore a fallback Taste Gate Checklist was created (below), grounded in
  raw Stitch DESIGN.md, all three raw Stitch HTML files, the Stitch Cline README,
  Project Sources north-star guidance, V2 visible QA findings, and safety
  constraints.

## North-Star Visual Target

A futuristic institutional fintech macro research / content-governance control
room: a local Bloomberg/Palantir-style evidence command center (without claiming
Bloomberg replacement), high-end but conservative, evidence-first / blocker-first
/ safety-first, suitable for PM/analyst/operator walkthrough screenshots. Not a
legacy terminal table dump, not generic SaaS, not a social scheduler, not an AI toy.

## Why V2 Failed The Visual/Taste Audit

- Read like a legacy sysadmin terminal / flat table dump (equal-weight boxes,
  weak hierarchy).
- Safety ribbon could overflow horizontally at common desktop widths.
- Stale current gate/state (referenced 0174R/pre-QA) lingered.
- Evidence lineage over-focused on 680d03d; did not represent dd55114/1024cdf/
  75f9d47/c56ccd9.
- Visual language under the north star: no composition rhythm, no command-center
  "decision" focal point, no designed evidence/gate matrices.

## How V3 Looks Materially Different From V2

- Deep layered navy-black environment (not flat graphite) with a precision grid
  and disciplined cool-accent glow on active/focused surfaces only.
- A dominant "Current Decision" focal module on Command Center (answers can-it-
  proceed in <10s), not a row of equal cards.
- A designed lineage timeline strip with build-vs-evidence-vs-historical
  classification, not a 2-row table.
- Stronger section composition: hero state band, decision module, evidence/
  blocker module, then supporting matrices.
- Overflow-safe wrapping safety rail; kill switch always visible.
- Near-sharp 2-3px radius + thin cool gridlines for a modern instrument feel
  while keeping zero playful gradients / no neon overload.


## Safety-Preserving Futuristic Visual Principles

- Color communicates system safety only: cyan=info/active, green=validation PASS,
  amber=review/manual, red=blocker/kill switch. Never market direction.
- No playful gradients, no neon overload, no crypto/casino aesthetic, no generic
  SaaS admin cards.
- Glow is disciplined: only active/focused surfaces get a faint cool ring.
- Every critical status is evidence-backed (status/severity/reason/evidence/
  allowed/blocked/current_truth/historical_provenance).
- No enabled controls implying post/send/schedule/publish/dispatch/API/env read.

## Screen-By-Screen Composition Plan

- Command Center: hero state band -> Current Decision focal module -> blocker +
  evidence module -> lineage strip -> safety counters.
- Content Studio: lane cards (pre-alpha process, grounded news context, future
  artifact-backed, failure forensics, macro education, product update) with
  claim-risk/source/artifact/manual-review/not-public-postable flags.
- Publish Readiness: gate matrix (per-platform readiness rows x gate columns) +
  next blocker. No dispatch affordances.
- Evidence Vault: evidence mode strip -> lineage timeline -> evidence index ->
  validation matrix -> caveat registry -> forbidden-scope registry -> active
  blockers -> next-task discipline.
- Content Calendar: manual workflow board (allowed states) + forbidden/unavailable
  auto states shown as locked.
- Visual Export: screenshot-safe checklist + forbidden export list + limitation
  notes + redaction confirmation.
- Settings: hard boundaries + policies + never-display list.

## PASS / FAIL Taste Gate (fallback checklist)

PASS requires ALL:
1. Deep layered environment with clear surface hierarchy (>=3 tonal levels).
2. A dominant decision/focal module on Command Center (not equal-weight cards).
3. Designed lineage timeline distinguishing build/evidence/historical.
4. Overflow-safe safety rail; kill switch always visible at all four widths.
5. Evidence/gate matrices look designed (mono headers, 1px dividers, severity chips).
6. Zero gradients used as decoration; glow only on active/focus.
7. No market-direction color semantics anywhere.
8. No enabled forbidden controls; disabled/future-only styled as read-only.
9. Current state aligned to 0174B V3 audit; 680d03d historical only.
10. No remote deps / no runtime network.

FAIL if ANY:
- Flat equal-weight table dump with no focal hierarchy.
- Horizontal body overflow or clipped safety chips.
- Stale current gate (0174R/444ef2c/0170/0164) shown as current.
- Action-looking publish/send/schedule/API controls.
- Remote CDN/font/icon or fetch/XHR/WebSocket/EventSource.

## No-Code-Until-Plan Confirmation

This plan and the brandkit extraction doc were both created and read back BEFORE
any V3 runtime file (index.html/styles.css/view_model.js/cockpit.js) was created.
