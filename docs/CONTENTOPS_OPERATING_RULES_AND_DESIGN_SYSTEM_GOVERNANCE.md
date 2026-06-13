# Capital Chronicle ContentOps — Standing Operating Rules for ChatGPT + Antigravity

## 1. Evidence Audit Rule: GitHub Must Be Checked After Every Worker Evidence Packet

After the user provides any task evidence packet claiming PASS, BLOCKED, FAIL, pushed commit, validation, or final HEAD, ChatGPT must not accept the pasted packet at face value.

For every completed task evidence packet, ChatGPT must verify through GitHub before acceptance:

1. Confirm repository and branch:

   * Repository: `fatcat2109/capital-chronicle-contentops`
   * Branch: `master`

2. Verify final commit:

   * Fetch or inspect the final commit SHA.
   * Confirm the commit message matches the evidence packet.
   * Confirm local/remote HEAD if the packet claims a push.

3. Compare starting HEAD to final HEAD:

   * Use GitHub compare or commit diff.
   * Verify changed files exactly match the declared scope.
   * Check that forbidden/protected paths were not modified.

4. Fetch changed source files or documentation where needed:

   * Do not rely only on changed filenames.
   * Read the actual changed content for safety, design, and regression implications.

5. Check protected path discipline:

   * V2 must remain untouched unless explicitly authorized.
   * V3 must remain untouched unless explicitly authorized.
   * `ui/institutional_shell` must remain untouched unless explicitly authorized.
   * `docs/design_references` must remain reference-only unless explicitly authorized.
   * `docs/browser_qa` must not be mutated by implementation tasks.
   * Core Capital Chronicle ingestion repo must not be mutated by ContentOps tasks.

6. Visual PASS requires actual browser screenshot evidence:

   * Cline/implementation packets may claim static validation only.
   * A visual PASS can only be accepted after Antigravity Browser QA screenshots are inspected.
   * ChatGPT must independently review screenshots against the north-star plan, design references, brandkit, layout, typography, color system, density, and user experience.
   * Worker visual judgement is evidence, not authority.

Acceptance labels must distinguish:

* `PASS_IMPLEMENTATION_PATCH_READY_FOR_BROWSER_QA`
* `PASS_STATIC_VALIDATION_ONLY`
* `PASS_FINAL_QA_READY_WITH_MINOR_CAVEATS`
* `PASS_FINAL_VISUAL_ACCEPTED`
* `BLOCKED_FOR_TARGETED_PATCH`
* `FAIL`
* `PASS_WITH_PROCESS_CAVEAT`
* `PASS_WITH_MINOR_EVIDENCE_GAP`

No task may be promoted to final visual acceptance based only on pasted text, unit tests, or self-reported screenshots.

---

## 2. Antigravity-Only Execution Rule

Use Antigravity IDE by default for ContentOps repo execution.

Two modes must remain separate:

### Antigravity Implementation Mode

Allowed:

* bounded source edits;
* tests;
* static validation;
* local visual sanity inspection;
* commit and push;
* final evidence packet.

Not allowed:

* claiming final visual PASS;
* editing browser QA evidence as proof;
* live/platform/provider/API/credential behavior;
* Project Sources refresh unless explicitly authorized.

### Antigravity Browser QA Mode

Allowed:

* browser inspection;
* screenshots;
* visual report;
* audit-only evidence packet.

Not allowed:

* source edits;
* commits;
* implementation patches;
* Project Sources refresh;
* live/platform/provider/API/credential behavior.

A task must clearly declare which mode it is using before work begins.

---

## 3. Design-System Rule: Build the Brandkit Like a Real System, Not a CSS Patch

Future visual/design tasks must be written as design-system work, not vague “make it look better” styling.

Every serious UI polish task must define and/or audit:

1. Design tokens

   * semantic surfaces;
   * semantic colors;
   * type scale;
   * spacing scale;
   * radius scale;
   * border scale;
   * elevation/material;
   * density modes;
   * motion/easing;
   * state semantics.

2. Component primitives

   * `CommandHero`
   * `SignalLockStrip`
   * `OperationalTruthRail`
   * `EvidenceCard`
   * `AuditTable`
   * `DrilldownPanel`
   * `StatusToken`
   * `BlockerCard`
   * `ReviewLane`
   * `PolicyMatrix`
   * `ProvenanceChip`
   * `SafetyCounterStrip`

3. Layout primitives

   * shell grid;
   * left navigation;
   * operator scan layer;
   * evidence/detail stack;
   * table scroll container;
   * section rhythm;
   * responsive breakpoints;
   * first-fold containment.

4. State semantics

   * current authority;
   * historical evidence;
   * reference-only;
   * blocked;
   * review-required;
   * future-only;
   * verified pass;
   * degraded;
   * redacted;
   * not-runtime-authority.

5. Brand-quality criteria

   * institutional fintech;
   * matte graphite;
   * premium evidence cockpit;
   * restrained accents;
   * no cyberpunk glow;
   * no raw terminal wall;
   * no generic SaaS;
   * no amateur red/pink palette;
   * no table dump.

---

## 4. Correct Technical Language for This Repo

This repo does not need React, Tailwind, Material Web, Fluent UI, Carbon, package managers, web fonts, or external dependencies for the current V4 cockpit.

The correct implementation language is:

* CSS custom properties for design tokens;
* semantic component classes for primitives;
* vanilla JavaScript renderer for deterministic local UI;
* static HTML shell;
* no runtime network;
* no CDN;
* no external font import;
* no framework dependency.

The design system should still be written like a real system.

Use token names such as:

```css
:root {
  --surface-base: ...;
  --surface-subtle: ...;
  --surface-raised: ...;
  --surface-command: ...;

  --border-hairline: ...;
  --border-authority: ...;

  --accent-authority: ...;
  --accent-evidence: ...;
  --warning-review: ...;
  --danger-verified: ...;
  --success-verified: ...;
  --state-future: ...;
  --state-redacted: ...;

  --type-display: ...;
  --type-title: ...;
  --type-body: ...;
  --type-small: ...;
  --type-micro: ...;
  --line-readable: ...;

  --space-1: ...;
  --space-2: ...;
  --space-3: ...;
  --space-4: ...;
  --space-6: ...;
  --space-8: ...;

  --radius-panel: ...;
  --radius-card: ...;
  --radius-token: ...;

  --shadow-subtle: ...;
  --shadow-elevated: ...;
  --shadow-authority: ...;
}
```

Use semantic classes such as:

```css
.CommandHero {}
.SignalLockStrip {}
.OperationalTruthRail {}
.EvidenceCard {}
.AuditTable {}
.DrilldownPanel {}
.StatusToken {}
.BlockerCard {}
.ReviewLane {}
.PolicyMatrix {}
.ProvenanceChip {}
.SafetyCounterStrip {}
```

Do not write one-off visual hacks unless the task is explicitly a tiny bugfix.

---

## 5. Real Design-System Benchmark Rule

When referencing mature design systems, use their operating model, not their codebase directly.

Examples:

* IBM Carbon: tokens, themes, grid, type, motion, component primitives, React/Web Components/Sass implementation.
* Fluent UI: component primitives, accessibility, TypeScript-heavy React/Web Components ecosystem.
* Material 3 / Material Web: semantic color roles, elevation, tokens, Web Components.
* Apple Human Interface quality: restraint, hierarchy, spacing, typography, material subtlety.
* Bloomberg-style professional density: data credibility, dense but structured, strong table discipline.
* NVIDIA/enterprise AI feel: graphite, controlled luminosity, technical confidence.
* Threads/social surface readability: human-readable rhythm and reduced cognitive load.

For this repo, translate those principles into:

* CSS tokens;
* vanilla JS rendering;
* static deterministic local UI;
* no external dependencies.

Never blindly copy another design system’s code or visual identity.

---

## 6. Visual Audit Rule: Be More Severe Than the Worker

Visual audit must inspect screenshots, not just reports.

Audit criteria:

1. Does the UI look institution-grade at first glance?
2. Does it look like a premium fintech governance workstation?
3. Is there a clear visual hierarchy within 5 seconds?
4. Does the first fold answer the operator’s primary question?
5. Are safety and current truth visible without becoming a wall?
6. Is cyan reserved for authority/current/evidence rather than decoration?
7. Are red/amber/green used only for verified state semantics?
8. Is typography readable for a normal operator, not only a developer?
9. Is mono reserved for IDs, hashes, paths, status codes, timestamps, evidence refs, and tabular data?
10. Do tables feel like controlled audit surfaces rather than raw dumps?
11. Does the layout avoid page-level horizontal scroll?
12. Are dense details progressively disclosed or placed below the scan layer?
13. Are historical, current, and reference-only states visually separated?
14. Are forbidden/live/platform/credential states impossible to misread?
15. Does the design avoid cyberpunk, toy AI, generic SaaS, and student-project aesthetics?

If screenshots look amateur despite passing tests, classify as:
`BLOCKED_FOR_VISUAL_SYSTEM_REBUILD`
or
`BLOCKED_FOR_TARGETED_VISUAL_PATCH`.

---

## 7. No Feature Deletion Rule

Reducing cognitive overload must not mean deleting governance capability.

Allowed:

* progressive disclosure;
* hierarchy changes;
* typography improvements;
* density modes;
* visual grouping;
* table scroll containers;
* summary-first scan layers;
* better labels;
* refined component primitives;
* moving detail below first fold.

Forbidden unless explicitly authorized:

* deleting evidence refs;
* deleting blocker registries;
* deleting matrices;
* deleting policy rows;
* deleting caveats;
* deleting provenance;
* deleting safety locks;
* deleting disabled/future-only records;
* hiding current-vs-historical distinction;
* removing redaction proof;
* removing no-live/no-platform/no-credential constraints.

The correct design pattern is:
summary first, evidence preserved, drilldown available.

---

## 8. North-Star Read Rule Before Any Visual Task

Before any visual/frontend/design/build task, the worker must read:

1. `docs/CAPITAL_CHRONICLE_CONTENTOPS_INSTITUTIONAL_COCKPIT_MASTER_PLAN.md`
2. `docs/TASK_CONTENTOPS_0174D_V4_COMPOSITION_BLUEPRINT.md`
3. `docs/TASK_CONTENTOPS_0174D_V4_SCREEN_WIREFRAME_CONTRACT.md`
4. `docs/TASK_CONTENTOPS_0174D_V4_NORTH_STAR_GAP_MAP.md`
5. Stitch/brandkit reference docs and raw HTML:

   * `docs/design_references/STITCH_OPERATOR_COCKPIT_CLINE_README.md`
   * `docs/design_references/stitch_institutional_ai_operator_cockpit/manifest.json`
   * `docs/design_references/stitch_institutional_ai_operator_cockpit/raw/technical_matte_operator/DESIGN.md`
   * raw Command Center HTML
   * raw Publish Readiness HTML
   * raw Evidence Vault HTML

The worker must summarize what visual principles it extracted before editing.

---

## 9. Prompt Quality Rule for Visual Tasks

A visual implementation prompt must not stop at rules and forbiddens.

It must also specify:

* desired palette direction;
* semantic color roles;
* type scale direction;
* spacing rhythm;
* component-level defects;
* exact blocks to improve;
* layout problems by screen;
* before/after intent;
* screenshots to inspect;
* acceptance criteria by viewport;
* examples of what “bad” looks like;
* examples of what “good” should feel like.

A prompt that only says “follow safety rules” is insufficient for visual work.

---

## 10. Screenshot Acceptance Rule

For visual QA, screenshots must cover at minimum:

* Command Center at 1366x768
* Command Center at 1440x900
* Command Center at 1536x864
* Command Center at 1920x1080
* Content Studio at 1440x900
* Publish Readiness Tower at 1440x900
* Evidence Vault at 1440x900
* Content Calendar / Workflow at 1440x900
* Visual Export / Screenshot-Safe at 1440x900
* Settings / Safety Policy at 1440x900

For final visual acceptance, ChatGPT must inspect the actual screenshots and compare against:

* master plan;
* design references;
* brandkit;
* current-vs-historical truth model;
* safety posture;
* typography and density;
* color semantics;
* first-fold cognitive load.

---

## 11. Runtime Safety Rule

The V4 cockpit remains a static local governance UI.

Forbidden:

* runtime network calls;
* platform APIs;
* provider APIs;
* Telegram APIs;
* scheduler;
* live posting;
* scraping;
* upload/export actions;
* credential reads;
* `.env` reads;
* Project Sources refresh;
* buy/sell/hold advice;
* price targets;
* forecast readiness claims;
* signal language;
* fake market data.

Required:

* local-only;
* review-only;
* not public-postable;
* live disabled;
* kill switch active;
* no financial advice;
* no signal language;
* secret redaction proof;
* current-vs-historical truth separation.

---

## 12. Evidence Hierarchy Rule

Trust order:

1. GitHub commits, diffs, and fetched changed files.
2. Browser screenshots inspected by ChatGPT.
3. Committed docs/tests/runbooks.
4. Local validation logs from worker.
5. Worker evidence packet.
6. Worker visual judgement.
7. Scratch files.
8. Chat memory.

Do not promote worker judgement above screenshot or GitHub evidence.

---

## 13. Final Acceptance Rule

A final acceptance record can only be created after:

1. implementation commit is verified on GitHub;
2. changed files are audited;
3. protected paths are confirmed untouched;
4. tests/static validation are plausible and scoped;
5. browser QA screenshots are inspected;
6. visual quality is judged against the north-star plan and design system;
7. remaining caveats are explicitly categorized as blocking or non-blocking.

Documentation-only acceptance records must not claim new visual verification. They may only record a prior accepted browser QA result.


## Antigravity + Gemini 3.1 Pro Preview Prompting Notes

### Observed Strengths
Gemini 3.1 Pro Preview inside Antigravity is strong for high-throughput bounded implementation. It correctly interprets highly scoped boundary contracts, strictly applies zero-trust principles when prompted, and maintains explicit execution safety boundaries effectively.

### Observed Weaknesses
Do not assume an initial PASS is promotion-ready. Common misses include edge-case invariant gaps, policy-widening bugs, path containment bugs, too-synthetic fixtures, report overclaim, weak first-pass adversarial tests, and visual self-assessment without screenshots.

### Prompting Strategy
Prompts should be concrete: build exactly this, inspect these files first, edit only these files, prove these invariants, add hostile tests, run validation, commit only scoped paths, push only audit branch, stop after evidence. Avoid abstract behavioral guidance in favor of hard mechanical invariants.

### Required Workflow Adjustment
For safety-chain modules, verifier/gate modules, data authority modules, and security-sensitive tasks: never promote initial PASS directly to main; require ChatGPT remote audit and expect one repair loop.

### Prompt Shape for Gemini
Explicitly pass the starting baseline, the allowed paths, the forbidden paths, and the exact validation commands. Gemini performs better with explicit hostile cases than abstract safety language. List exactly what edge cases to verify in the test suite.

### Reports Are Not Authority
Reports are useful summaries, but reports are not authority; source/tests must prove the report. Always verify the implementation in the repository diff.

### Internal Antigravity Logs
Internal Antigravity .gemini/antigravity-ide/brain/.system_generated/... logs may be surfaced by tool behavior but must not be requirements, implementation authority, evidence, committed files, quoted proof, or substitute for git/test/read-back evidence.

### Best Use
Targeted logic patching, single-module isolation, deterministic data structures, deterministic test suites, and strict mechanical refactoring. One task at a time. No self-promotion. No next-phase continuation inside the same worker task.

### Default Gemini Task Rule
Default lifecycle: Prompt -> Audit branch implementation -> ChatGPT remote audit -> Repair prompt -> ChatGPT re-audit -> Promotion prompt -> Remote main read-back -> Stop.
