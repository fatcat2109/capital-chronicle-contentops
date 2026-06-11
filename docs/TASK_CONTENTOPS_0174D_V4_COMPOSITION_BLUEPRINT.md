# Operator Cockpit V4 — Composition Blueprint

Task: TASK_CONTENTOPS_0174D_OPERATOR_COCKPIT_V4_NORTH_STAR_GAP_MAP_AND_COMPOSITION_BLUEPRINT_V0

No-code task. This document is a composition contract for a future V4 build
(TASK_CONTENTOPS_0174E). It contains NO runtime frontend code and authorizes none
in 0174D. V4 must be a clean-room build under ui/institutional_operator_cockpit_v4/.

## 1. V4 Product Thesis

A local-first, evidence-grade institutional cockpit for macro content governance.
The operator opens it locally and within 10 seconds knows: what mode we are in,
what is blocked and why, what evidence backs that, and what the single next allowed
action is. It is not a SaaS dashboard, not a terminal table dump, not a social
scheduler, not a trading terminal. It is a governance instrument: calm, cold,
hyper-logical, auditable. Evidence is the interface; state precedes action.

## 2. V4 Information Architecture

Seven screens, one canonical truth model, one shared shell:
- Command Center (mission control / verdict)
- Content Studio (editorial governance)
- Publish Readiness Tower (gate matrix)
- Evidence Vault (compliance room)
- Content Calendar / Workflow (manual planning)
- Visual Export / Screenshot-Safe (briefing studio)
- Settings / Safety Policy (policy inspection)

## 3. Global Shell Model

- Top: compact grouped Safety Rail (NOT a 2-line chip wrap). Critical chips
  (KILL SWITCH ACTIVE, LIVE DISABLED, NOT PUBLIC POSTABLE, NO FINANCIAL ADVICE,
  NO SIGNAL LANGUAGE) always visible; remaining states grouped into a single
  "system locks" cluster with a count. Fixed height, never wraps to two lines at
  1366 width, never causes horizontal scroll.
- Left: 220px vertical nav, sharp, cyan active left-bar (per DESIGN.md).
- Header: canonical truth strip with LABELED HEAD roles (see section 5).
- Body: screen-specific composed surface.
- Bottom: NO fixed overlapping directive bar. The next-allowed-action lives inside
  the body flow (Command Center verdict band) and/or a non-fixed footer that
  participates in layout. The body reserves a bottom gutter so nothing is clipped.

## 4. Canonical Truth Model

One object is the single source of operational truth (carry forward V3's
single-model discipline). Every screen and the header read from it. No component
hardcodes current baseline / current gate / kill switch / public state
independently. Historical and Stitch provenance are separate, explicitly labeled
"Not Runtime Authority".

## 5. Current-vs-Historical Labeling Model

The header must distinguish, each with an explicit role label (no bare hashes):
- Current Product HEAD (the V4 build commit, set at build time)
- Tested HEAD (browser QA evidence commit)
- Current Gate (full text, NEVER truncated)
- Next Allowed Action (full text, NEVER truncated)
- V2 Historical Build Candidate (labeled historical)
- V3 Failed-Candidate Build (labeled historical / not accepted)
- Reference Quarantine commit (labeled reference-only)
- Visible Browser QA Evidence commit (labeled evidence-only)
- Historical Screen Provenance (15b87ff / 1c03ca0 / 444ef2c — not runtime authority)

The stale V3 string "Awaiting ChatGPT audit of 0174B V3 clean-room rebuild evidence"
must NOT appear as the V4 current gate.

## 6. First-Fold Composition Standard

At 1366x768 the operator must see, without scrolling, on every screen:
- the Safety Rail,
- the labeled truth strip,
- the screen's primary operator question + dominant answer/verdict,
- the primary blocker (if any) with reason + evidence ref.
Screen-specific detail tables/registries may extend below the fold but their
headers/first rows should be visible. No fixed element may overlap first-fold body.

## 7. Responsive Layout Standard

Support 1366x768, 1440x900, 1536x864, 1920x1080.
- html/body: overflow-x hidden; no uncontrolled horizontal page scroll.
- Main content scrolls internally; the shell frame is fixed.
- Grid children use min-width: 0; grids use minmax(0, 1fr).
- Reserved bottom gutter (>= directive/footer height) so content is never clipped.
- Long task labels wrap or use full-width bands, never truncate critical truth.

## 8. No-Bottom-Overlap Rule

V3's fixed bottom directive bar overlapped first-fold body at 1366/1440. V4
forbids any fixed-position element that overlaps body content. The next-action is
rendered in-flow. If a persistent footer is used, the body container adds matching
bottom padding so nothing is hidden.

## 9. Status Token Standard

Allowed vocabulary only: PASS, DEGRADED, BLOCKED, REVIEW_REQUIRED, LIVE_DISABLED,
NOT_PUBLIC_POSTABLE, FUTURE_ONLY, UNKNOWN, SECRET_REDACTED.
Color communicates system safety only — never market direction. PASS means
system/validation-safe only; never publish-ready, live-ready, forecast-ready,
or market-positive.

## 10. Evidence-Backed Status Component Standard

Every critical status object carries: status, severity, label, reason,
evidence_ref_ids, allowed_actions, blocked_actions, current_truth (bool),
historical_provenance (bool), and an optional caveat. A status with no reason and
no evidence_ref_ids is invalid and must fail tests.

## 11. Screen-by-Screen Composition Blueprint

### 11.1 Command Center
Primary question: "Can anything proceed, and if not, why?"
- Full-width CURRENT VERDICT band (dominant, top of body): one-line operational
  verdict + status token + severity color.
- Labeled truth rail: current product HEAD, tested HEAD, current gate (full),
  next allowed action (full), with role labels.
- What-changed-since-last-accepted-state module.
- Active blocker stack (ordered by severity), each with reason + evidence ref.
- Evidence dependency map (which evidence backs the current verdict).
- Safety counters (locks active / gates open / blockers / review items).
- Zero ambiguous abbreviations in first fold.

### 11.2 Content Studio
Primary question: "What content exists, what is its claim risk, and what must be
true before a human may review it?"
- Lane separation: pre-alpha process, grounded news context, future
  artifact-backed (blocked until real artifacts), failure forensics, macro
  education, product update.
- Per lane: source/brief panel, claim-risk classifier, forbidden-language result
  panel, limitation builder, platform-fit dry-run preview, manual-review checklist,
  evidence refs, not_public_postable state.
- No final public-ready copy. No financial advice / signal language.

### 11.3 Publish Readiness Tower
Primary question: "What must be true before supervised publishing is even possible?"
- GATE MATRIX FIRST (above platform cards). Columns: official docs, dry-run
  renderer, approval ledger, credential slot, credential read, credential
  validation, redacted audit, kill switch, live adapter, scheduler, posting,
  next blocker.
- Platform rows as readiness records (not dispatch controls).
- States: PASS / REVIEW_REQUIRED / BLOCKED / FUTURE_ONLY / LIVE_DISABLED.
- No publish/post/send/schedule/dispatch affordance anywhere.

### 11.4 Evidence Vault
Primary question: "What is the audit trail and how confident are we?"
- Compliance-room layout. First-fold or immediately-below: validation matrix.
- Evidence timeline with current / historical / evidence-only classification.
- Caveat registry, forbidden-scope registry, active blocker registry.
- Evidence confidence legend.
- 0174C browser QA evidence row WITH explicit caveat: capture accepted, worker
  visual judgment rejected.

### 11.5 Content Calendar / Workflow
Primary question: "What is the manual plan and what stage is each item at?"
- Manual workflow board AND/OR date lanes with cadence (week/day columns).
- Allowed states only: idea, source-needed, research-brief-ready, draft-review,
  blocked, operator-approved-for-manual, manually-posted, metrics-entered.
- metrics-needed and manually-posted tracking.
- Forbidden automated states (scheduled, queued for auto-post, auto-publish ready,
  live campaign, API dispatch ready, bot reply ready) shown as disabled/future-only.

### 11.6 Visual Export / Screenshot-Safe
Primary question: "Is this surface safe to screenshot for a briefing?"
- Screenshot-safe report-card mode.
- Redaction preview surface, limitation strip.
- Data sufficiency placeholder, forecast readiness placeholder, blocked-forecast
  explainer, failure-forensics card.
- No actual export / download / upload / screenshot automation / public-ready caption.

### 11.7 Settings / Safety Policy
Primary question: "What are the hard boundaries and what is never displayed?"
- Policy matrix (not a bullet list).
- Credential never-display registry, platform gate policy.
- Financial-advice prohibition, signal-language prohibition, live behavior
  disablement, future gate requirements.
- Never display real token / API key / chat ID / env path / raw platform response.

## 12. What Changes Materially From V3

- Command Center gains a dominant full-width verdict band + evidence dependency
  map (V3 had generic equal-weight cards).
- Header gains LABELED HEAD roles; no bare hashes, no truncated gate.
- Publish Readiness leads with the gate matrix (V3 buried it below platform cards).
- Evidence Vault becomes a compliance room with first-fold validation matrix and
  registries (V3 had a lineage list).
- Content Studio gains claim-risk / forbidden-language / limitation / fit panels
  per lane (V3 had lane cards).
- Calendar becomes date-lane / cadence planning (V3 had rows).
- Visual Export becomes a report-card + redaction preview studio (V3 had a checklist).
- Settings becomes a policy matrix + never-display registry (V3 had bullets).
- Safety rail becomes a compact grouped cluster (V3 wrapped to two lines).
- Bottom directive bar removed as a fixed overlapping element; next-action is in-flow.
- Truth model refreshed so no stale 0174B gate appears.

## 13. What Must NOT Be Reused From V3

- The fixed bottom directive bar that overlaps first-fold body.
- The two-line-wrapping safety chip ribbon.
- The per-screen generic "screen state" card as the dominant first-fold element.
- Bare unlabeled HEAD hashes in the header.
- The truncated current-gate string.
- Flat equal-weight card grids as the primary Command Center composition.
- Platform-cards-first Publish Readiness ordering.
- Any copied V3 CSS skeleton that reproduces the terminal/table-dump grammar.
V4 is a clean-room rebuild; V3 is reference-for-what-failed only.
