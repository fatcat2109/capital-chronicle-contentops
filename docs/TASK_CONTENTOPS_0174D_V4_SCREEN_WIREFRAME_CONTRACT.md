# Operator Cockpit V4 — Screen Wireframe Contract

Task: TASK_CONTENTOPS_0174D_OPERATOR_COCKPIT_V4_NORTH_STAR_GAP_MAP_AND_COMPOSITION_BLUEPRINT_V0

Text wireframes only. No images, no frontend runtime code, none authorized in 0174D.
Each screen lists: first-fold target, primary operator question, hero/current-decision
region, state panel, blocker panel, evidence panel, screen-specific body,
matrix/timeline/registry elements, bottom/action discipline, visible-at-1366x768,
may-move-below-fold, forbidden controls, expected status objects.

Conventions: [BAND] full-width; [RAIL] labeled strip; [MATRIX] table; [STACK] ordered
list; [GUTTER] reserved bottom space; all controls are inspect-only/disabled-with-reason.

## Screen 1 — Command Center

```
[SAFETY RAIL: LOCAL ONLY | REVIEW ONLY | NOT PUBLIC POSTABLE | LIVE DISABLED |
              KILL SWITCH ACTIVE | NO FINANCIAL ADVICE | NO SIGNAL LANGUAGE | (+locks 6)]
[TRUTH RAIL: Current Product HEAD <label:hash> | Tested HEAD <label:hash> |
             Current Gate: <full text> | Next Allowed Action: <full text>]
[BAND  CURRENT VERDICT: "<one-line verdict>"   <STATUS TOKEN>  <severity color>]
[ROW   WHAT CHANGED SINCE LAST ACCEPTED STATE: <delta summary>]
[STACK ACTIVE BLOCKERS: 1) <label> — reason — [evidence: EV-###] ... ]
[GRID  EVIDENCE DEPENDENCY MAP: verdict <- EV-### <- validation/test refs]
[ROW   SAFETY COUNTERS: locks N | gates open N | blockers N | review items N]
[GUTTER]
```
- first-fold target: verdict band + truth rail + top blocker visible without scroll.
- primary operator question: "Can anything proceed, and if not, why?"
- hero/current-decision region: CURRENT VERDICT band.
- state panel: truth rail (labeled HEAD roles).
- blocker panel: active blocker stack.
- evidence panel: evidence dependency map.
- screen-specific body: what-changed + safety counters.
- matrix/timeline/registry: dependency map (mini-graph as labeled rows).
- bottom/action discipline: next-action in TRUTH RAIL + in-flow; no fixed overlap.
- visible at 1366x768: rail, truth rail, verdict, first blocker.
- may move below fold: full dependency map, full counters.
- forbidden controls: publish/post/send/schedule/dispatch/API/credential/env.
- expected status objects: command_verdict, each blocker (full token contract).

## Screen 2 — Content Studio

```
[SAFETY RAIL]
[TRUTH RAIL]
[BAND  STUDIO STATE: review_only | not_public_postable | manual review required]
[LANES (separated columns/sections):
   PRE-ALPHA PROCESS | GROUNDED NEWS CONTEXT | FUTURE ARTIFACT-BACKED (BLOCKED) |
   FAILURE FORENSICS | MACRO EDUCATION | PRODUCT UPDATE]
[PER LANE PANEL: source/brief | claim-risk classifier | forbidden-language result |
   limitation builder | platform-fit dry-run | manual-review checklist | evidence refs]
[GUTTER]
```
- first-fold target: studio state band + lane headers + first lane's claim-risk.
- primary operator question: "What is each item's claim risk and review gate?"
- hero/current-decision region: STUDIO STATE band.
- state panel: per-lane state (not_public_postable).
- blocker panel: future artifact-backed lane shown BLOCKED with reason.
- evidence panel: evidence refs per lane.
- screen-specific body: lane panels with classifiers.
- matrix/registry: claim-risk classifier + forbidden-language result panels.
- bottom/action discipline: no fixed bar; in-flow.
- visible at 1366x768: state band + lane headers.
- may move below fold: lower lanes, limitation builder detail.
- forbidden controls: final public-ready copy, send/publish, financial advice.
- expected status objects: per-lane status (claim_risk, review gate) with reasons.

## Screen 3 — Publish Readiness Tower

```
[SAFETY RAIL]
[TRUTH RAIL]
[BAND  READINESS VERDICT: "Supervised publishing is BLOCKED. Next blocker: <x>"]
[MATRIX GATE MATRIX (FIRST):
   rows = platforms; cols = official docs | dry-run renderer | approval ledger |
   credential slot | credential read | credential validation | redacted audit |
   kill switch | live adapter | scheduler | posting | next blocker]
[BELOW: platform readiness records (inspect-only)]
[GUTTER]
```
- first-fold target: readiness verdict + gate matrix header + first platform row.
- primary operator question: "What must be true before supervised publishing?"
- hero/current-decision region: READINESS VERDICT band.
- state panel: matrix cell states (PASS/REVIEW_REQUIRED/BLOCKED/FUTURE_ONLY/LIVE_DISABLED).
- blocker panel: next blocker column + verdict.
- evidence panel: evidence refs per gate.
- screen-specific body: gate matrix first, platform records second.
- matrix/registry: the gate matrix is the centerpiece.
- bottom/action discipline: no dispatch affordance; in-flow.
- visible at 1366x768: verdict + matrix first rows.
- may move below fold: lower platform rows, record detail.
- forbidden controls: publish/post/send/schedule/dispatch/API/credential-validation.
- expected status objects: per-gate status with reason + evidence + blocked_actions.

## Screen 4 — Evidence Vault

```
[SAFETY RAIL]
[TRUTH RAIL]
[BAND  EVIDENCE STATE: "Audit trail complete to <HEAD>. Confidence: <legend>."]
[MATRIX VALIDATION MATRIX (first-fold or immediately below):
   rows = checks; cols = expected | observed | status | evidence ref]
[TIMELINE EVIDENCE TIMELINE: commit | task | classification(current/historical/evidence-only)]
[REGISTRY CAVEAT REGISTRY | FORBIDDEN-SCOPE REGISTRY | ACTIVE BLOCKER REGISTRY]
[ROW   0174C BROWSER QA EVIDENCE: captured PASS; worker visual judgment REJECTED]
[GUTTER]
```
- first-fold target: evidence state band + validation matrix header.
- primary operator question: "What is the audit trail and how confident are we?"
- hero/current-decision region: EVIDENCE STATE band.
- state panel: evidence confidence legend.
- blocker panel: active blocker registry.
- evidence panel: validation matrix + timeline.
- screen-specific body: registries.
- matrix/timeline/registry: all three present.
- bottom/action discipline: no fixed bar; in-flow.
- visible at 1366x768: state band + validation matrix top rows.
- may move below fold: full timeline, full registries.
- forbidden controls: evidence mutation, export/upload.
- expected status objects: per-check validation status; 0174C evidence row with caveat.

## Screen 5 — Content Calendar / Workflow

```
[SAFETY RAIL]
[TRUTH RAIL]
[BAND  PLAN STATE: "Manual planning only. No scheduling. No auto-post."]
[LANES DATE/CADENCE COLUMNS (week or day) with item cards by manual state]
[LEGEND ALLOWED STATES: idea | source-needed | research-brief-ready | draft-review |
   blocked | operator-approved-for-manual | manually-posted | metrics-entered]
[LOCKED FORBIDDEN STATES (disabled/future-only): scheduled | queued for auto-post |
   auto-publish ready | live campaign | API dispatch ready | bot reply ready]
[GUTTER]
```
- first-fold target: plan state band + date lanes + allowed-state legend.
- primary operator question: "What is the manual plan and each item's stage?"
- hero/current-decision region: PLAN STATE band.
- state panel: allowed-state legend.
- blocker panel: blocked items lane.
- evidence panel: per-item evidence/brief refs.
- screen-specific body: date/cadence lanes + metrics tracking.
- matrix/registry: forbidden-state locked registry.
- bottom/action discipline: no scheduling control; in-flow.
- visible at 1366x768: plan band + first date lanes.
- may move below fold: later weeks, forbidden-state registry detail.
- forbidden controls: schedule/queue/auto-publish/dispatch/bot-reply.
- expected status objects: per-item manual state; forbidden states as FUTURE_ONLY.

## Screen 6 — Visual Export / Screenshot-Safe

```
[SAFETY RAIL]
[TRUTH RAIL]
[BAND  EXPORT STATE: "Screenshot-safe preparation only. No export/download/upload."]
[CARDS SCREENSHOT-SAFE REPORT CARDS (redaction-applied previews)]
[PANEL REDACTION PREVIEW | LIMITATION STRIP]
[PLACEHOLDERS DATA SUFFICIENCY | FORECAST READINESS (blocked-forecast explainer)]
[CARD  FAILURE-FORENSICS]
[GUTTER]
```
- first-fold target: export state band + first report card + redaction preview.
- primary operator question: "Is this safe to screenshot for a briefing?"
- hero/current-decision region: EXPORT STATE band.
- state panel: secret-redaction confirmation.
- blocker panel: blocked-forecast explainer.
- evidence panel: limitation strip + evidence refs.
- screen-specific body: report cards + placeholders + forensics.
- matrix/registry: data sufficiency / forecast readiness placeholders.
- bottom/action discipline: no export automation; in-flow.
- visible at 1366x768: export band + first report card.
- may move below fold: forensics card, lower placeholders.
- forbidden controls: export/download/upload/screenshot-automation/public-ready caption.
- expected status objects: redaction status (SECRET_REDACTED), forecast FUTURE_ONLY.

## Screen 7 — Settings / Safety Policy

```
[SAFETY RAIL]
[TRUTH RAIL]
[BAND  POLICY STATE: "Hard boundaries enforced. Credentials never displayed."]
[MATRIX POLICY MATRIX: policy | value | enforcement | rationale]
[REGISTRY CREDENTIAL NEVER-DISPLAY REGISTRY]
[ROWS  PLATFORM GATE POLICY | FINANCIAL-ADVICE PROHIBITION |
       SIGNAL-LANGUAGE PROHIBITION | LIVE BEHAVIOR DISABLEMENT | FUTURE GATE REQUIREMENTS]
[GUTTER]
```
- first-fold target: policy state band + policy matrix top rows.
- primary operator question: "What are the hard boundaries and what is never shown?"
- hero/current-decision region: POLICY STATE band.
- state panel: enforcement column.
- blocker panel: future gate requirements (FUTURE_ONLY).
- evidence panel: rationale column.
- screen-specific body: policy matrix + never-display registry.
- matrix/registry: policy matrix + never-display registry.
- bottom/action discipline: no credential reveal control; in-flow.
- visible at 1366x768: policy band + matrix top rows.
- may move below fold: lower policies, future gate detail.
- forbidden controls: display of real token/API key/chat ID/env path/raw response.
- expected status objects: per-policy status; never-display entries as SECRET_REDACTED.
```

```
