# Operator Cockpit V4 — Dashboard Premium Transition Plan (0174AD)

Task authority: TASK_CONTENTOPS_0174AD_DASHBOARD_INFORMATION_ARCHITECTURE_AND_MODERN_MATTE_DESIGN_LANGUAGE_PASS

This document preserves the operator-supplied 0174AD roadmap inside the repo so it
becomes repo-native design authority for this and future passes. It is committed as
part of 0174AD. It contains no runtime frontend code.

## 1. Purpose

The V4 cockpit must move from an evidence-dense static audit surface into a premium
institutional dashboard cockpit. This is NOT a redesign from scratch and NOT a new
feature pass. It is a **composition refactor**:

> Move from "all data visible at once" to "summary first, evidence preserved,
> drilldown available."

The cockpit should stop feeling like an audit log rendered as one long page and start
feeling like a premium local institutional governance cockpit where evidence is
available, but not cognitively dumped.

## 2. Roadmap (task authority)

- **0174AC** — finished current truth/state hygiene: current-state truth aligned,
  stale blocker language removed, residual blue/cyber frame removed/verified clean.
  Committed at `4ffe650`.
- **0174AD** — dashboard information architecture + progressive disclosure + modern
  matte visual language (this task). Begin the real dashboard composition pass; stop
  placing all available data in the first fold; preserve all evidence, blockers,
  matrices, provenance, caveats, redaction proof, and safety states; move dense detail
  into second/third layers, drilldowns, tabs, segmented panels, or below-fold audit
  areas. Add tokenized matte depth, subtle gradient, material, and micro-motion as a
  design system.
- **0174AF** — Browser QA + score against the institutional cockpit rubric.

## 3. Layer Model (target IA)

### First fold (scan layer)
- Current State
- Primary Blockers
- Next Allowed Action
- Evidence Confidence / Validation Snapshot

### Second layer (screen-specific summary modules)
- key counters
- lane/gate summaries
- current decision panels

### Third layer (drilldown / below scan)
- detailed audit tables
- provenance
- raw matrices
- historical timeline
- caveat registries
- validation matrices

## 4. Non-Negotiable: No Feature Deletion

Reducing cognitive overload must NOT delete governance capability. Do not delete
evidence refs, blocker registries, matrices, policy rows, caveats, provenance, safety
locks, disabled/future-only records, redaction proof, or current-vs-historical
distinction. The correct pattern is: **summary first, evidence preserved, drilldown
available.** Dense detail is recomposed into `DrilldownPanel` disclosure regions and
below-scan audit surfaces — never removed.

## 5. Per-Screen Direction

| Screen | Must read as | First fold | Detail moves to |
|---|---|---|---|
| Command Center | executive state cockpit | verdict / blockers / next action / evidence confidence | full blocker stack + evidence dependency map drilldowns |
| Publish Readiness | gate-control surface | gate-summary strip + readiness verdict | full gate matrix + platform records drilldowns |
| Evidence Vault | provenance/compliance room | evidence state + confidence legend + QA caveat | validation matrix + timeline + registry triad drilldowns |
| Content Studio | lane/card editorial control | lane summary strip + lane verdict cards | per-lane limitation/checklist drilldowns |
| Calendar / Workflow | manual workflow board | plan state + allowed-state legend + date lanes | forbidden automated-state registry drilldown |
| Visual Export | screenshot-safe report surface | export state + report cards + redaction preview | forecast/forensics drilldown |
| Settings / Safety | policy matrix | policy state + credential never-display registry | full policy matrix + future-gate drilldown |

## 6. Modern Design Language (allowed effects, as system language only)

These are tokens and component grammar, never decoration:

- **Matte graphite gradients** for surface layering (hierarchy, not ornament).
- **Subtle warm-neutral radial** attention behind the **primary command panel only**
  (Command Center scan layer). Barely visible, graphite/neutral.
- **1px hairline highlight** for active/current surfaces (nav active, current truth
  cells, open drilldowns).
- **Depth by tonal stepping**: `#0e0e0e → #141313 → #1c1b1c → #201f20 → #2a2a2a`.
- **Micro motion 120–180ms** for hover/focus only.
- Gradient borders only for selected/current authority, not everywhere.
- Restrained frosted/matte slab only if it improves hierarchy.

### Semantic color discipline (unchanged)
- red only for verified danger/blockers/kill switch/live-disabled;
- amber only for review/caution;
- green only for verified pass;
- grey/near-white for authority/evidence/current.

## 7. Forbidden Visual Patterns

- no blue cyber edge / browser-default blue accent;
- no neon;
- no rainbow gradients;
- no random glassmorphism;
- no generic SaaS dashboard polish;
- no raw terminal wall / giant table dump as the first fold;
- color must never communicate market direction.

## 8. Operating Models to Learn From (not copy)

Apple (restraint, spacing, fewer first-fold items), Claude/Anthropic (calm trust,
low-noise copy), OpenAI/ChatGPT (task focus, minimal chrome, progressive disclosure),
SpotGamma / institutional finance (density, confidence bands, signal separation, table
legitimacy), Bloomberg-style (disciplined density), IBM Carbon / Material / Fluent
(tokens, state roles, surfaces, elevation, component primitives), NVIDIA enterprise AI
(graphite confidence, controlled luminosity). Extract operating models only — tokens,
hierarchy, grid, type, motion, semantic color, progressive disclosure. Do not copy
code, identity, or branding.

## 9. Component Grammar to Strengthen

CommandHero, SignalLockStrip, OperationalTruthRail, EvidenceCard, AuditTable,
DrilldownPanel, StatusToken, BlockerStack, GateMatrix, PolicyMatrix, ProvenanceChip,
SafetyCounterStrip, SummaryStrip, DetailDrawer/DrilldownPanel. Use existing stable
DOM/classes where possible; the design system must be visible in tokens/classes.

## 10. 0174AD Success Definition

- First fold of Command Center is understandable in under 10 seconds.
- Dense details are below the scan layer or in drilldown/disclosure.
- Evidence is preserved and easier to inspect.
- No active current-state stale HEAD/task language; no 0174Z as a current blocker.
- No blue/cyber glow.
- Publish Readiness reads as gate summary first, matrix second.
- Evidence Vault reads as a compliance/provenance room.
- Screens look more modern and premium without becoming SaaS/AI toy.

## 11. Runtime Safety (unchanged)

Static local governance UI only. No runtime network, platform/provider/Telegram APIs,
scheduler, live posting, scraping, export/upload, credential/env reads, or Project
Sources refresh. No external frontend dependencies. No protected-path drift. No final
visual PASS claim from the builder — screenshots + recommendation only.
