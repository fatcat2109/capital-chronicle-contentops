# TASK_CONTENTOPS_0174AI → 0174AM — Premium Quality-System Roadmap (95–98)

Status: APPROVED ROADMAP (build authority)
Owner surface: Operator Cockpit V4 (ui/institutional_operator_cockpit_v4)
Branch: master · local-only · static · read-only
Sibling authorities: CAPITAL_CHRONICLE_CONTENTOPS_INSTITUTIONAL_COCKPIT_MASTER_PLAN.md,
CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md,
TASK_CONTENTOPS_0174AD_DASHBOARD_PREMIUM_TRANSITION_PLAN.md,
TASK_CONTENTOPS_0174D_V4_COMPOSITION_BLUEPRINT.md

---

## 0. Why this roadmap exists

From 0174AH onward, the gap to 95–98 is **not** "more boxes, more inspector,
more type scale, more wow." The gap is **interaction model + object model +
product choreography**.

95–98 does not come from more animation, more color, more screens, or more wow
effect. It comes from hardening the current shell into a true cockpit:
truth-consistent, evidence-backed, operator-clear in under 10 seconds,
local/static/read-only, blocker/evidence/next-action driven, no fake
affordance, no current/historical ambiguity.

This is a **quality system**, not a visual tweak. That is why it is split into
five conceptual leaps (0174AI → 0174AM) instead of one task. One mega-task
risks: object model without screen polish; screen polish without accessibility;
motion without selected state; diffs too large to audit; or safety/evidence
regressions.

---

## 1. Diagnosis after 0174AH

0174AH reached a good milestone: workspace shell + screen-specific inspector.
That progress is real. Measured against a 95–98 bar, five large gaps remain.

1. **Still screen-centric, not object-centric.** The operator sees blockers,
   lanes, gates, evidence refs, workflow cards, policy groups, redaction proofs,
   but does not yet feel "I selected one object and the whole cockpit explains
   that object."
2. **Inspector is screen-specific but not context-synchronized.** It says the
   right thing per screen, but does not yet react to the selected
   blocker/lane/gate/evidence/policy.
3. **Motion is not yet a system language.** Carbon treats motion as guidance
   through complex experiences and state transitions; productive motion must be
   subtle, efficient, used for button state, dropdowns, revealing information,
   and table/data interactions — not decoration.
4. **Accessibility/focus is not yet treated as part of premium feel.** With
   local command controls, the WAI-ARIA button pattern requires role/function/
   visual to match; toggle/select state should use `aria-pressed`; Space/Enter
   activation must be explicit. Disclosure needs `aria-expanded` (+ optional
   `aria-controls`).
5. **Audit is not extreme enough.** Governance requires a visual audit stricter
   than the worker: read real screenshots; check institution-grade first glance;
   hierarchy in 5 seconds; safety/current truth; typography; mono usage; table
   containment; current/historical/reference separation; no cyberpunk/toy/SaaS/
   student aesthetics.

---

## 2. The ten ideas behind 95–98

### 2.1 Object-centric cockpit (most important)
Today the UI has screens. Add **objects**: blocker, evidence ref, publish gate,
content lane, workflow item, policy group, redaction proof, safety lock.

Each object carries an internal shape:

```text
kind
id
label
state
severity
reason
evidence_refs
allowed_local_action
blocked_action
caveat
current_or_historical_or_reference_only
```

No backend, no new data. Build from the existing `MODEL`. When the operator
selects an object, the inspector changes to that object. This is the leap from
"beautiful page" to "workstation."

### 2.2 Selected state + evidence path
The selected object must be clearly visible without glow: semantic left edge,
matte highlight, active trace chip, inspector title sync, and an evidence path
row: `Selected object → evidence refs → gate/blocker/caveat`. CSS hairline +
chips is enough; this gives a real investigation/audit feel.

### 2.3 Productive motion grammar
Not "add animation." Motion must resolve context:
- hover/focus: 70–110ms
- select object → inspector update: 120–150ms
- drilldown: 150–240ms
- selected trace / evidence path: 120–150ms
- no bounce, no spring, no glow, no parallax drama
- `prefers-reduced-motion` must disable transforms

Carbon duration tokens: 70ms micro-interactions (button/toggle), 110ms fade,
150ms small expansion / short movement, 240ms expansion / system communication.
Avoid distracting/decorative easing; no bounce/stretch/sudden stops.

### 2.4 Progressive view transitions, guarded
The View Transition API can reduce cognitive load and keep users in-context
across state/view changes. This repo is static local governance UI, so it may be
used **only** as progressive enhancement if safe:

```js
if (document.startViewTransition && !prefersReducedMotion) {
  document.startViewTransition(() => renderSelectedObject(...));
} else {
  renderSelectedObject(...);
}
```

No dependency. Not used if it raises risk.

### 2.5 Command Center decision spine
Command Center is still report-like. It needs a clear spine:

```text
Decision: BLOCKED
Top Blocker: BLK-VISUAL
Evidence: EV-0174D / EV-TESTS-V4
Allowed Local Action: inspect + manual review + await audit
Disabled Surface: live/API/scheduler/posting/credential
```

"What Changed" becomes a **delta strip**, not a big ledger list. Active Blocker
Stack becomes a **selectable blocker board**.

### 2.6 Content Studio review queue
Content Studio is still a card wall. Move toward: Review Queue, Risk Watch,
Citation Needed, Future Artifact Blocked, Safe Education Lane. Lane cards are
preserved but no longer equal-weight. Default selected object should be a future
artifact-backed blocker or a citation-dependent lane.

### 2.7 Publish Readiness gate object model
The best screen today. To reach 95 it needs selectable gate objects: Live
adapter, Scheduler, Posting, Credential read, Platform API. Each gate inspects
to: disabled, reason, evidence, next blocker, forbidden action.

### 2.8 Evidence Vault provenance graph-lite
No fancy chart. A "graph-lite":

```text
Evidence confidence → validation matrix → timeline → registry → QA caveat
```

Chips + hairline + selected state. The vault should read like an audit room, not
just confidence cards.

### 2.9 Settings policy control map
Settings needs a policy object model: Runtime boundaries, Content boundaries,
Credential never-display, Platform gates, Redaction posture, Future
requirements. Select a policy group → inspector update. Credential registry
stays visible but is no longer the main wall.

### 2.10 Extreme audit harness
After each build task, audit cannot be just "10 screenshots." Add: selected
blocker, selected lane, selected gate, selected evidence/caveat, selected
policy, keyboard/focus, compact density, reduced-motion source/test proof, and a
GitHub source audit for forbidden APIs/storage/fake buttons.

---

## 3. Task plan (0174AI → 0174AM)

### Task 0174AI — Object-Centric Inspection Model
Largest build task; must come first.
Deliverable: selected object registry; object selection state in vanilla JS;
inspector sync; selected visual state; evidence path; local-only command
controls; ARIA/focus baseline; productive motion tokens.
Expected score after clean implementation: **93–94**.

### Task 0174AJ — Executive Command Surface Rewrite
Only after the object model exists.
Deliverable: Command Center decision spine; blocker board; Content Studio review
queue; Publish gate object map; Evidence graph-lite; Settings policy map; Visual
Export briefing package preview.
Expected score: **94–96**.

### Task 0174AK — Motion, Accessibility, Density, Responsive Hardening
Design-system maturity, not visual candy.
Deliverable: motion tokens; selected/update transitions; `prefers-reduced-motion`;
focus states; ARIA attributes; keyboard behavior; real comfortable/compact
density; 1366/1440/1536/1920 hardening.
Expected score: **95–97** if clean.

### Task 0174AL — Extreme Visual QA + Source Audit
Read-only. No source edits.
Audit: GitHub diff; source safety; object model; screenshots; selected object
states; motion/reduced-motion evidence; keyboard/focus; every screen score;
first-fold 5-second test; no fake affordance; no current/historical ambiguity.
Expected result: **final score 95–98 if no blockers**.

### Task 0174AM — Findings Repair
Repair only the findings from 0174AL. No redesign.
Expected final: **96–98** if findings are small.

---

## 4. Detailed plan for 0174AI

0174AI focuses ONLY on object-centric inspection; it does not attempt a full UI
rewrite.

In scope:
```text
selected object registry
→ selected object state
→ inspector sync
→ selected visual state
→ evidence path
→ local-only command controls
→ ARIA/focus
→ motion tokens
→ tests
→ selected-state screenshot set
```

Out of scope:
```text
full redesign
new screens
live action
scheduler
publish controls
new data
external deps
massive color/theme change
```

Success conditions:
- operator clicks/selects a blocker/lane/gate/evidence/policy object
- the object is highlighted
- the inspector changes content accordingly
- the evidence path is visible
- no fake operational control
- motion is subtle and reduced-motion safe
- screenshots show the real selected state

---

## 5. Extreme audit standard (from 0174AI onward) — 8 layers

1. **GitHub authority:** commit, diff, files, protected paths.
2. **Runtime safety:** no network/storage/API/env/credential/live controls.
3. **Object model:** selected object data has reason/evidence/caveat/action.
4. **Inspector sync:** selected object truly changes the inspector.
5. **Visual:** selected state, first fold, hierarchy, density, no glow.
6. **Accessibility:** button/disclosure semantics, focus, keyboard, ARIA.
7. **Motion:** tokenized, purposeful, reduced-motion safe.
8. **Product truth:** current/historical/reference-only never mixed.

---

## 6. Recommendation / build sequence

1. Lock roadmap 0174AI → 0174AM (this document).
2. Operator confirms the roadmap.
3. Write a precise 0174AI prompt (architecture + screenshot requirements, not
   bureaucracy).
4. After 0174AI, audit deeper: GitHub + source + screenshots + interaction
   states.

If the goal is truly 95–98, start with **0174AI Object-Centric Inspection
Model** — the step most likely to turn the UI from "very beautiful and safe"
into a real institutional command cockpit.

---

## 7. Build-log status (live)

> [!NOTE]
> 0174AI has already been implemented and pushed ahead of this roadmap being
> committed. Commit `152b855` (feat: add V4 object-centric inspection model)
> landed the selected-object registry, per-screen default objects, inspector
> sync, selected visual state, evidence path, local-only controls, ARIA/focus,
> and motion + reduced-motion tokens. Static gates: 271/271 passing. Capture:
> 12 PNGs, network egress 0, console errors 0. Remaining: 0174AJ → 0174AM.

### Source authorities to read before each task
- docs/CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md
- docs/CAPITAL_CHRONICLE_CONTENTOPS_INSTITUTIONAL_COCKPIT_MASTER_PLAN.md
- docs/TASK_CONTENTOPS_0174AD_DASHBOARD_PREMIUM_TRANSITION_PLAN.md
- docs/TASK_CONTENTOPS_0174D_V4_COMPOSITION_BLUEPRINT.md
- docs/TASK_CONTENTOPS_0174D_V4_SCREEN_WIREFRAME_CONTRACT.md
- docs/TASK_CONTENTOPS_0174D_V4_NORTH_STAR_GAP_MAP.md

### External design references (principles only — never copy code/brand/assets)
- Carbon Design System — Motion overview (duration tokens, productive motion)
- W3C WAI-ARIA APG — Button pattern (`aria-pressed`, Space/Enter)
- W3C WAI-ARIA APG — Disclosure pattern (`aria-expanded`, `aria-controls`)
- MDN — View Transition API (guarded progressive enhancement only)
