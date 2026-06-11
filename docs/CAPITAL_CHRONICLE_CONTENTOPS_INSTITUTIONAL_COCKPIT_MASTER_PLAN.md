# Capital Chronicle ContentOps Institutional Cockpit Master Plan

## Path to a 95–98/100 Operator-Grade UI

## 0. Executive Decision

Capital Chronicle ContentOps should not attempt to reach a 95–98/100 UI score by adding more screens, more visual decoration, or more platform capabilities.

The correct path is to harden the existing institutional shell into a true operator cockpit.

The product target is not:

* a pretty dashboard;
* a social media scheduler;
* a startup SaaS admin panel;
* an AI writing toy;
* a trading terminal;
* a publish automation console.

The target is:

**A local-first, evidence-grade institutional cockpit for macro content governance, forecast-readiness discipline, content safety, manual approval, and future supervised publishing readiness.**

It is explicitly not a pretty dashboard, not a social media scheduler, and not a trading terminal. It is read-only by default and remains local-first and evidence-grade.

To reach 95–98/100, the UI must become:

1. Truth-consistent.
2. Evidence-backed.
3. Operator-clear in under 10 seconds.
4. Layout-robust across desktop viewports.
5. Read-only by default.
6. Strictly local/static/fixture-safe until explicit future gates.
7. Designed around blockers, evidence, and next allowed actions.
8. Free of stale metadata, fake-click affordances, and ambiguous current-vs-historical state.

The current design direction is good. The current execution is not yet cockpit-grade.

The project should now enter a dedicated:

**Institutional Operator Cockpit Hardening Track**

This is separate from feature expansion, platform automation, Telegram pilot work, publishing adapters, or content generation.

---

# 0b. Mandatory Worker-Platform Discipline

This master plan is repo-native design authority. Every future build/design task
must treat it as mandatory reading.

* Future Cline CLI frontend/design/build tasks must read this master plan before
  editing any UI/design files.
* Cline CLI performs implementation, docs, and tests. It does not run browser QA.
* Antigravity IDE performs browser QA, visible viewport checks, and
  screenshot/evidence capture. It does not perform implementation.
* ChatGPT audits between Cline CLI and Antigravity and does not accept
  worker PASS claims without repo/evidence verification.
* Antigravity visual judgment is advisory; screenshots/evidence and the ChatGPT
  audit are authoritative.

---


# 1. Current UI Assessment

## 1.1 Current Score

Estimated score: **68/100**

The UI is directionally strong but operationally noisy.

It has the right atmosphere, the right safety posture, and the right screen taxonomy. However, it still feels like a promising institutional prototype rather than a production-grade operator cockpit.

## 1.2 What Is Already Strong

### Visual Identity

The “Technical Matte Operator” aesthetic is appropriate.

Strengths:

* dark matte cockpit feel;
* compact typography;
* mono-data treatment for machine-like state;
* rigid panels and gridlines;
* strong local-only / live-disabled visual vocabulary;
* no consumer SaaS softness;
* no colorful market-gambling tone;
* no trading-signal aesthetic.

This is a good foundation. Do not throw it away.

### Safety Visibility

The UI repeatedly communicates:

* local only;
* dry-run only;
* review only;
* live disabled;
* not public-postable;
* kill switch active;
* manual review required.

This is correct. ContentOps must show safety before action.

### Screen Architecture

The screen map is conceptually right:

* Command Center;
* Content Studio;
* Publish Readiness Tower;
* Evidence Vault;
* Calendar / Workflow Board;
* Visual Export;
* Settings / Safety Policy.

This is the correct family of institutional screens.

## 1.3 Main Weaknesses

### Weakness 1 — Current Truth and Historical Provenance Are Mixed

The UI currently risks confusing:

* current accepted baseline;
* historical screen baseline;
* task provenance;
* screenshot reference state;
* previous gate;
* current gate;
* accepted code baseline;
* evidence-only browser QA state.

This is the most serious issue.

An institutional cockpit cannot display historical metadata in a way that looks like current operational truth.

### Weakness 2 — Operator Hierarchy Is Too Noisy

The UI contains many cards, chips, banners, and badges, but it does not yet consistently answer:

* What is the current state?
* What is blocked?
* Why is it blocked?
* What evidence supports that?
* What is the next allowed action?
* What is forbidden?
* What changed since the last accepted state?

A strong cockpit must make these answers immediate.

### Weakness 3 — Status Badges Are Not Evidence-Grade

Many PASS / REVIEW REQUIRED / LIVE DISABLED / MANUAL ONLY states look like badges.

A 95+ UI cannot have decorative badges.

Every status must have:

* reason;
* evidence reference;
* last validation;
* current-vs-historical classification;
* allowed action;
* blocked action;
* caveat, if any.

### Weakness 4 — Layout Is Not Robust Enough

The Publish Readiness Tower screenshot shows obvious layout failure:

* content clipped horizontally;
* sidebar/header overlap risk;
* large unexplained blank region;
* compressed panels;
* partially hidden content;
* insufficient responsive hardening.

This alone prevents a score above the low 80s.

### Weakness 5 — Too Many Action-Looking Controls

Some controls look actionable even though the system is review-only:

* refresh icons;
* history icons;
* acknowledge/proceed button;
* platform cards;
* publish-readiness panels;
* hoverable cards;
* status chips;
* navigation elements.

In a local-only system, any control that looks like it might mutate state must be clearly classified as:

* inspect-only;
* disabled with reason;
* future-only;
* blocked;
* manual external action only.

Ambiguous affordances are dangerous.

### Weakness 6 — Publish Readiness Tower Still Feels Too Platform-Dashboard-Like

The Publish Readiness Tower should not feel like a platform control panel.

It should feel like a gate matrix.

It must communicate:

* platform readiness does not mean publish readiness;
* credential presence does not mean credential validation;
* dry-run render support does not mean live API permission;
* manual approval does not mean public-ready;
* kill switch active blocks all outbound behavior;
* future live adapter is disabled until explicit gate.

---

# 2. Target Definition: What 95–98/100 Means

## 2.1 What 95/100 Means

A 95/100 UI means:

* no stale current metadata;
* no current/historical baseline ambiguity;
* no obvious layout clipping at common desktop widths;
* every screen has a visible next allowed action;
* every important status has reason and evidence;
* no active forbidden controls;
* no fake live/publish/schedule controls;
* no credential or secret exposure;
* no external network dependency;
* no unclear “proceed” action;
* operator can understand current state in under 10 seconds.

## 2.2 What 98/100 Means

A 98/100 UI means:

* the cockpit feels production-grade despite being local/static;
* the operator can inspect why every status exists;
* every blocker is explainable;
* Evidence Vault behaves like a compliance room;
* Publish Readiness Tower behaves like a safety-gated control model;
* Content Studio clearly separates pre-alpha process content, grounded-news context, and future artifact-backed content;
* browser QA finds no critical UI/layout/affordance issues;
* automated tests catch stale metadata, forbidden controls, and missing evidence references;
* screenshot-safe mode is credible enough for investor/product walkthroughs without misleading public viewers.

## 2.3 What 100/100 Would Require

A literal 100/100 is not realistic at this stage because the product is still:

* static/local-only;
* fixture-driven;
* without real Capital Chronicle alpha artifacts;
* without real operator usage history;
* without real workflow telemetry;
* without future approved live-gate behavior.

Therefore, the practical target is:

**95–98/100 static institutional cockpit readiness.**

---

# 3. Core Product Principle

## State Before Action

Every screen must start with state, not buttons.

Before an operator sees any possible action, the UI must answer:

1. What mode is the system in?
2. Is the kill switch active?
3. Is live behavior disabled?
4. Is the content public-postable?
5. What is the current gate?
6. What is the current accepted baseline?
7. What is historical provenance?
8. What is blocked?
9. Why is it blocked?
10. What evidence supports this?
11. What is the next allowed action?

The UI should not invite action before it proves state.

---

# 4. Canonical Truth Model

## 4.1 Problem

The current UI has signs of current state and historical provenance being mixed.

Examples of risky language patterns:

* “Accepted HEAD” used for historical screen baseline.
* Old task gates shown near current header.
* Screenshot reference metadata shown like runtime state.
* Screen-level provenance shown with insufficient hierarchy.
* Global metadata not clearly separated from historical screen metadata.

This must be fixed first.

## 4.2 Required Model

Create or enforce one canonical view model.

Recommended structure:

```yaml
global_current_state:
  repo_path: string
  branch: string
  current_head_full: string
  current_head_short: string
  accepted_product_baseline: string
  accepted_product_baseline_short: string
  current_gate: string
  kill_switch_status: active | inactive
  public_state: not_public_postable | review_only | future_public_candidate
  live_state: disabled | future_disabled | gated
  platform_api_state: disabled | future_disabled | gated
  scheduler_state: disabled
  credential_read_state: disabled
  next_allowed_action:
    label: string
    task_label: string | null
    action_type: await_audit | inspect | manual_operator_step | future_task
    reason: string
    evidence_refs: array

screen_provenance:
  screen_id: string
  screen_name: string
  historical_task_label: string
  historical_head_short: string
  provenance_label: "historical screen provenance"
  runtime_authority: false
  display_priority: secondary

evidence_refs:
  evidence_id: string
  evidence_type: task_packet | schema | validator | test_result | browser_qa | doc
  label: string
  status: pass | pass_with_caveat | blocked | fail
  caveat: string | null
  source_path: string | null
  last_validated: string | null

status_tokens:
  token_id: string
  status: pass | degraded | blocked | review_required | live_disabled | not_public_postable | unknown
  severity: info | safe | caution | blocked | critical
  label: string
  reason: string
  evidence_ref_ids: array
  allowed_actions: array
  blocked_actions: array
  current_truth: boolean
  historical_provenance: boolean
```

## 4.3 Hard Rule

**No UI component may hardcode current baseline, current gate, kill switch status, public state, or next allowed action.**

All current operational state must come from the canonical global model.

Historical commits may appear only inside explicitly labeled provenance components.

## 4.4 Required Labels

Use strict labels:

* “Current Accepted Baseline”
* “Current Gate”
* “Current Product State”
* “Historical Screen Provenance”
* “Evidence Packet Provenance”
* “Screenshot Reference Only”
* “Not Runtime Authority”
* “Future Gate”
* “Disabled by Kill Switch”
* “Manual Review Required”

Avoid ambiguous labels:

* “Accepted HEAD” inside screen cards unless it truly means current accepted baseline.
* “Baseline” without qualifier.
* “Current” for historical screen task.
* “Ready” without specifying ready for what.
* “Proceed” without exact action type.

---

# 5. Screen Grammar Standard

Every screen should use a consistent grammar.

## 5.1 Required Screen Sections

Each screen should contain:

1. **Global Header**

   * current mode;
   * current accepted baseline;
   * kill switch;
   * current gate;
   * next allowed action.

2. **Screen State Panel**

   * what this screen is for;
   * whether it is current, historical, fixture-only, or review-only;
   * whether it has runtime authority.

3. **Primary Blocker / Gate Panel**

   * main blocker;
   * reason;
   * evidence;
   * next allowed action.

4. **Evidence Reference Panel**

   * evidence IDs;
   * validation sources;
   * task packet references;
   * caveats.

5. **Disabled / Future Action Matrix**

   * forbidden actions;
   * disabled actions;
   * future-only gates;
   * reason for each.

6. **Historical Provenance Card**

   * screen build task;
   * historical commit;
   * not runtime authority label.

7. **Screen-Specific Body**

   * content relevant to that screen.

## 5.2 Standard Screen Header Template

Recommended copy pattern:

```text
[Screen Name]

Mode: static / local / fixture-driven
Runtime Authority: no
Public State: not_public_postable
Live State: disabled
Current Gate: [global current gate]
Primary Blocker: [reason]
Next Allowed Action: [exact instruction]
Evidence: [refs]
Historical Screen Provenance: [task/head, not runtime authority]
```

## 5.3 Standard Card Template

Every critical card should follow this model:

```text
Title
Status: BLOCKED / PASS / REVIEW REQUIRED / LIVE DISABLED
Reason: [human-readable reason]
Evidence: [evidence ref or fixture source]
Current Truth: yes/no
Allowed: [inspect/manual review/etc.]
Blocked: [publish/schedule/API/env/etc.]
Caveat: [if relevant]
```

This prevents badge-only UI.

---

# 6. Status Token System

## 6.1 Current Problem

The UI currently uses many labels:

* PASS
* LIVE DISABLED
* REVIEW REQUIRED
* MANUAL ONLY
* ACTIVE
* not_public_postable
* disabled
* static/local/fixture-driven

These are correct concepts, but they need a normalized severity model.

## 6.2 Required Status Vocabulary

Use a strict status registry:

### PASS

Meaning:

* validation passed;
* safe local state;
* evidence-backed.

Never means:

* publish-ready;
* forecast-ready;
* live-ready;
* market-positive.

### DEGRADED

Meaning:

* usable with caveat;
* evidence gap;
* partial validation.

### BLOCKED

Meaning:

* cannot proceed until blocker is resolved.

### REVIEW_REQUIRED

Meaning:

* human decision needed;
* no automated approval.

### LIVE_DISABLED

Meaning:

* live adapter/API/scheduler/posting is disabled.

### NOT_PUBLIC_POSTABLE

Meaning:

* content or screen is not allowed to be represented as public-ready.

### FUTURE_ONLY

Meaning:

* capability exists conceptually but is not active.

### UNKNOWN

Meaning:

* evidence missing;
* cannot infer safe state.

### SECRET_REDACTED

Meaning:

* credential state may be represented only as redacted presence/absence, never value.

## 6.3 Color Rules

Color must communicate system safety only.

Never use color for:

* bullish/bearish meaning;
* market direction;
* asset movement;
* trading conviction;
* performance implication.

Recommended semantics:

* blue/cyan: informational / current selection / metadata;
* amber: review required / caution / pending;
* red: blocked / kill switch / live disabled / critical safety block;
* green: validation pass only;
* grey: disabled / unavailable / future-only.

---

# 7. Command Center Redesign

## 7.1 Purpose

The Command Center should answer:

**Can anything proceed, and if not, why?**

It is the operator’s first screen. It should not be a generic dashboard.

## 7.2 Required Modules

### Global State Strip

Show:

* system mode;
* current accepted baseline;
* kill switch;
* live state;
* public state;
* current gate;
* next allowed action.

### Primary Decision Panel

Large top panel:

```text
Current Decision: BLOCKED / AWAITING AUDIT / LOCAL REVIEW ONLY

Reason:
[reason]

Evidence:
[evidence refs]

Next Allowed Action:
[exact task or await audit instruction]
```

### Safety Counters

Show only meaningful counters:

* active blockers;
* evidence packets;
* disabled live capabilities;
* pending audit items;
* visible caveats.

### Blocked Action Matrix

Rows:

* live posting;
* scheduler;
* platform API;
* provider LLM API;
* scraping;
* autonomous replies/DMs;
* one-button publish-all;
* public-ready final copy;
* credential display;
* env read;
* evidence mutation.

Each row must show:

* status;
* reason;
* allowed alternative.

### Build / Provenance Panel

Separate current baseline from historical screen provenance.

```text
Current Product Baseline:
[HEAD/task]

Screen Provenance:
[screen build task/head]
Not runtime authority.
```

## 7.3 What to Remove or Reduce

Reduce:

* repeated safety chips;
* ambiguous PASS cards;
* duplicated baseline cards;
* action-looking “Acknowledge & Proceed” unless it is clearly inspect-only.

---

# 8. Evidence Vault Redesign

## 8.1 Purpose

Evidence Vault should feel like a compliance-grade evidence room.

It should not feel like a table dump.

## 8.2 Required Modules

### Evidence Packet Index

Columns:

* task;
* classification;
* current/historical;
* commit;
* evidence type;
* validation result;
* caveat;
* forbidden scope status;
* next action discipline.

### Commit Timeline

Show:

* accepted commits;
* evidence-only events;
* caveated passes;
* current baseline;
* historical screen tasks.

### Validation Matrix

Rows:

* full test suite;
* focused tests;
* CLI summary;
* node syntax;
* git diff check;
* secret scan;
* forbidden scope scan;
* browser QA, if applicable.

### Caveat Registry

Every caveat must have:

* caveat ID;
* severity;
* source evidence;
* affected screen;
* whether blocking;
* resolution task.

### Next Task Discipline Panel

Show:

* exact next task;
* who authorized it;
* whether browser/API/env/network is allowed;
* what is forbidden.

## 8.3 Critical Rule

Evidence Vault must be the source of confidence.

Every critical status elsewhere should be traceable to an Evidence Vault object.

---

# 9. Publish Readiness Tower Redesign

## 9.1 Purpose

Publish Readiness Tower should answer:

**What would need to be true before supervised publishing could ever happen?**

It should not imply publishing is available now.

## 9.2 Required Gate Matrix

For each platform:

* platform contract exists;
* dry-run renderer exists;
* official docs verified;
* credential slot defined;
* credential presence checked;
* credential validation completed;
* manual approval ledger ready;
* redacted audit logging ready;
* kill switch pass;
* live adapter enabled;
* scheduler enabled;
* posting enabled;
* next blocker.

Most rows should currently be disabled, blocked, future-only, or review-required.

## 9.3 Platform Card Standard

Each platform card should show:

```text
Platform: Telegram / X / LinkedIn / Threads / Substack / etc.

Current capability:
dry-run only / future-only / disabled

Live API:
disabled

Credential:
not read / redacted presence only / future operator setup required

Posting:
disabled

Scheduler:
disabled

Next blocker:
[official docs / credential policy / live gate / kill switch / manual approval]

Allowed now:
inspect / dry-run preview / manual review

Forbidden now:
API call / live post / schedule / scrape / autonomous reply
```

## 9.4 Remove Any Publish-Like Ambiguity

Avoid:

* “send” icons as if active;
* “post” button language;
* publish-all affordances;
* enabled-looking platform actions;
* credential validation controls;
* green “ready” states that could imply publish-ready.

Use:

* “inspect contract”;
* “view dry-run shape”;
* “future gate”;
* “disabled by kill switch”;
* “manual review only”.

---

# 10. Content Studio Redesign

## 10.1 Purpose

Content Studio should make content safety inspectable.

It must separate:

* pre-alpha process content;
* grounded news context;
* future artifact-backed content.

## 10.2 Required Lanes

### Lane A — Pre-Alpha General / Process

Allowed:

* product philosophy;
* build-in-public;
* macro education;
* data sufficiency education;
* forecast readiness education;
* failure forensics philosophy.

Must not imply:

* Capital Chronicle alpha output;
* live forecast;
* signal service;
* market advice.

### Lane B — Grounded News Context

Allowed:

* news as hook;
* educational interpretation;
* source-cited discussion;
* data sufficiency questions;
* forecast readiness questions.

Must not imply:

* signal;
* prediction;
* trade;
* buy/sell/hold;
* target;
* model forecast.

### Lane C — Future Artifact-Backed Content

Blocked until:

* real approved Capital Chronicle artifacts exist;
* artifact IDs exist;
* lineage exists;
* freshness and limitations exist;
* DQR/readiness state exists;
* missing/degraded/proxy data is visible.

## 10.3 Required Components

* lane selector;
* source/brief panel;
* claim risk classifier;
* forbidden language results;
* limitation builder;
* platform fit preview;
* manual decision checklist;
* evidence references;
* not-public-postable state.

## 10.4 Draft Review Rules

No draft should be visually framed as final public copy unless future gates explicitly allow it.

Use labels:

* “Draft for review”
* “Not public-postable”
* “Requires manual review”
* “General/process content”
* “Source needed”
* “Citation incomplete”
* “Blocked: market-sensitive claim”

---

# 11. Calendar / Workflow Board Redesign

## 11.1 Purpose

The Calendar should plan manual content workflow only.

It must not imply scheduling.

## 11.2 Allowed Workflow States

* idea;
* source-needed;
* research-brief-ready;
* draft-review;
* blocked;
* operator-approved-for-manual;
* manually-posted;
* metrics-entered.

## 11.3 Forbidden Workflow States

Do not use:

* scheduled;
* queued for auto-post;
* auto-publish ready;
* live campaign;
* API dispatch ready;
* bot reply ready.

Unless a future explicit live scheduling gate approves them.

## 11.4 Required Visual Pattern

Each content item should display:

* content type;
* lane;
* source status;
* claim risk;
* review status;
* manual approval status;
* public-postable status;
* platform fit;
* next action.

---

# 12. Visual Export / Screenshot-Safe Mode

## 12.1 Purpose

Visual Export is not an export engine yet.

It is a screenshot-safe preparation and inspection screen.

## 12.2 Requirements

Every screenshot-safe view must include:

* local-only label;
* not-public-postable label;
* live-disabled label;
* no financial advice label;
* evidence reference;
* limitation note;
* freshness note if relevant;
* secret redaction confirmation;
* source/artifact status.

## 12.3 Forbidden

Do not add:

* actual image export;
* PDF generation;
* platform upload;
* file download;
* screenshot automation;
* public-ready caption generation;
* live sharing.

Unless explicitly approved in a future task.

## 12.4 Quality Target

Screenshots should be suitable for:

* internal review;
* product discussion;
* build-in-public meta discussion;
* investor walkthrough;
* UI QA evidence.

They should not be framed as public market research output.

---

# 13. Settings / Safety Policy Screen

## 13.1 Purpose

Settings should not be a credential screen.

It should be a safety policy inspection screen.

## 13.2 Required Sections

* active hard boundaries;
* forbidden actions;
* credential policy;
* redaction policy;
* platform gate policy;
* content safety policy;
* financial advice prohibition;
* signal language prohibition;
* live behavior disablement;
* future gate requirements.

## 13.3 Credential Treatment

Never display:

* real token;
* API key;
* chat ID if sensitive;
* env path with secrets;
* raw platform response.

Allowed:

* credential slot exists: yes/no;
* credential read allowed now: no;
* validation enabled now: no;
* future operator setup required: yes/no;
* redacted presence only, if explicitly scoped.

---

# 14. Affordance Discipline

## 14.1 Problem

Review-only systems are damaged by fake action affordances.

If a user sees a button, icon, hover card, or call-to-action, they may assume the product can do something.

## 14.2 Control Taxonomy

Every control must be one of:

### Real Enabled Action

Rare. Only if the repo actually supports it safely.

Example:

* navigate to screen;
* expand inspector;
* copy local fixture ID, if safe.

### Inspect-Only

Allowed.

Must be labeled:

* “Inspect”
* “View evidence”
* “View gate”
* “View provenance”

### Disabled With Reason

Allowed.

Must show:

* disabled status;
* reason;
* future gate.

### Future-Only

Allowed.

Must show:

* future task required;
* not enabled now;
* no live behavior.

### Forbidden

Should not look like a control.

Represent as a blocked row, not a button.

## 14.3 Specific Fixes

### Refresh / History Icons

If non-functional, convert to:

* disabled;
* inspect-only;
* tooltip/static label;
* or remove.

### Acknowledge & Proceed

Dangerous phrase.

Replace with:

* “Inspect Next Gate”
* “View Evidence Packet”
* “Manual Audit Required”
* “No Action Available”

### Platform Cards

Cards should not look like dispatch controls.

They should look like readiness records.

### Publish Controls

Do not display enabled “publish”, “post”, “send”, “schedule”, or “dispatch” controls.

Use disabled gate rows instead.

---

# 15. Layout Robustness

## 15.1 Required Viewports

The shell must be checked at minimum:

* 1366 × 768;
* 1440 × 900;
* 1536 × 864;
* 1920 × 1080.

## 15.2 Must Fix

* sidebar overlay;
* header overlap;
* title clipping;
* horizontal content cutoff;
* large blank panels;
* table compression;
* footer overlay;
* card text overflow;
* uncontrolled horizontal scroll;
* insufficient scroll container boundaries.

## 15.3 Layout Rules

* Global header height must be fixed and accounted for.
* Sidebar width must be fixed and content offset must match exactly.
* Main content should use a max-width container where appropriate.
* Dense tables should scroll inside their own panel, not break the page.
* Platform cards should wrap cleanly.
* Long task labels should truncate with accessible full text in an inspector, not destroy layout.
* Safety ribbon should not consume too much vertical space.

## 15.4 No Grey Dead Zones

Large blank areas should be eliminated unless explicitly labeled as:

* reserved preview area;
* disabled output pane;
* empty state;
* no eligible items;
* future-only area.

Blankness must be meaningful.

---

# 16. Accessibility and Readability

## 16.1 Typography

Keep compact typography, but improve readability:

* section headers should be scannable;
* task labels should not dominate primary status;
* line height should be sufficient for dense content;
* low-contrast grey-on-black text should be reduced.

## 16.2 Contrast

Ensure:

* disabled text remains readable;
* red warning text is legible;
* amber review states are legible;
* small mono text is not below practical readability;
* borders are visible but not noisy.

## 16.3 Keyboard and Focus

Even in static mode:

* focus states should be visible;
* nav items should be understandable;
* disabled controls should not trap focus;
* inspect-only controls should have clear labels.

## 16.4 Copy Clarity

Replace technical ambiguity with operator clarity.

Bad:

```text
0170 browser qa evidence + metadata reconciliation
```

Better:

```text
Current Gate:
Awaiting audit of 0170 metadata reconciliation evidence.
No Project Sources refresh or next task until accepted.
```

Bad:

```text
accepted head 1c03ca0
```

Better:

```text
Historical Screen Provenance:
Built in task 0160 at 1c03ca0.
Not current runtime authority.
```

---

# 17. Automated UI Quality Gates

To reach 95–98, visual review is not enough.

The repo must include deterministic tests.

## 17.1 Metadata Tests

Fail if:

* stale accepted HEAD appears as current;
* historical screen head appears under current baseline label;
* current gate is inconsistent across screens;
* next allowed action differs across global components;
* screenshot reference metadata is labeled as current runtime truth.

## 17.2 Status Tests

Fail if:

* status token lacks reason;
* blocker lacks evidence;
* critical card lacks allowed/blocked actions;
* PASS appears without validation reference;
* REVIEW_REQUIRED appears without human gate explanation;
* LIVE_DISABLED appears near an enabled live action.

## 17.3 Forbidden Control Tests

Fail if enabled-looking controls exist for:

* publish;
* post;
* send;
* schedule;
* API call;
* credential validation;
* env read;
* scrape;
* auto reply;
* DM;
* evidence mutation;
* export/upload.

## 17.4 Safety Label Tests

Fail if any screen lacks:

* local-only;
* live-disabled;
* not-public-postable or equivalent;
* manual review required where relevant;
* no financial advice where content appears;
* no signal language where market-related content appears.

## 17.5 Secret and Network Tests

Fail if:

* `.env` appears in visible UI text except as forbidden policy text;
* token-like values appear;
* API key patterns appear;
* raw request/response payloads appear;
* external fetch calls exist in shell JS;
* remote URLs are required for runtime behavior.

## 17.6 Layout Static Tests

Where possible, scan for:

* fixed widths that exceed container;
* content panels wider than viewport minus sidebar;
* body overflow hidden where content needs scroll;
* absolute positioning that can overlay content;
* unbounded long strings;
* missing truncation classes.

Browser QA should validate what static tests cannot.

---

# 18. Browser QA Plan

## 18.1 Purpose

Browser QA should validate operator experience, not design taste.

## 18.2 Scope

Allowed:

* open local static file;
* navigate all screens;
* inspect visible layout;
* check disabled controls;
* check safety labels;
* check no secrets;
* check no active forbidden actions;
* check viewport behavior;
* capture evidence if explicitly approved.

Forbidden:

* external URLs;
* network;
* platform APIs;
* env reads;
* credentials;
* live posting;
* screenshots unless explicitly approved;
* file export unless explicitly approved.

## 18.3 Browser QA Checklist

For each screen:

* title visible;
* global safety visible;
* current state visible;
* current/historical metadata not confused;
* next allowed action visible;
* evidence reference visible;
* no clipping;
* no sidebar overlay;
* no header overlap;
* no active forbidden controls;
* no secret visible;
* no public-ready misleading content;
* no market-direction color semantics;
* disabled/future actions clearly labeled.

## 18.4 Expected Browser QA Evidence Packet

Must include:

* task label;
* PASS/BLOCKED/FAIL;
* repo path;
* branch;
* HEAD;
* local file URL;
* browser used;
* whether external URL opened;
* whether network observed;
* whether screenshots captured;
* screen-by-screen result;
* viewport checks;
* forbidden controls count;
* secret visibility result;
* layout defects;
* blockers;
* exact next task.

---

# 19. Execution Roadmap to 95–98

## Phase 1 — Truth Model Rebuild

Target score movement: **68 → 78**

### Objective

Eliminate stale metadata and current/historical ambiguity.

### Work

* Create canonical global state model.
* Move historical screen baselines into provenance cards.
* Remove “Accepted HEAD” from historical contexts.
* Make global header current-only.
* Add metadata consistency tests.
* Add stale metadata regression tests.

### Acceptance Criteria

* One current baseline displayed globally.
* Historical baselines clearly labeled.
* No screenshot reference data appears as current.
* No old gate appears as current gate.
* Tests fail on current/historical mixing.

---

## Phase 2 — Operator Grammar Standardization

Target score movement: **78 → 86**

### Objective

Make every screen follow the same cockpit grammar.

### Work

* Add screen state panel.
* Add primary blocker panel.
* Add evidence reference panel.
* Add next allowed action panel.
* Add disabled/future action matrix.
* Add historical provenance card.
* Normalize copy and labels.

### Acceptance Criteria

Every screen answers:

* What is this screen?
* What is current state?
* What is blocked?
* Why?
* What evidence supports it?
* What is next allowed?
* What is forbidden?

---

## Phase 3 — Evidence-Backed Status Components

Target score movement: **86 → 91**

### Objective

Replace decorative badges with evidence-grade status objects.

### Work

* Define status token model.
* Add reason/evidence/actions to every critical status.
* Add status explanation inspector or static explanation panel.
* Link Command Center statuses to Evidence Vault references.
* Add tests for status-without-reason.

### Acceptance Criteria

* No PASS/BLOCKED/REVIEW badge appears without reason.
* Every blocker has evidence.
* Every critical status has allowed/blocked actions.
* Evidence Vault can explain all top-level statuses.

---

## Phase 4 — Layout and Affordance Hardening

Target score movement: **91 → 94**

### Objective

Make the UI robust and non-ambiguous.

### Work

* Fix Publish Readiness Tower clipping.
* Fix sidebar/header/content layout.
* Remove or relabel action-looking controls.
* Convert fake actions to inspect-only or disabled-with-reason.
* Add responsive layout checks.
* Improve empty states.
* Remove meaningless blank panels.

### Acceptance Criteria

* No obvious clipping at common desktop widths.
* No enabled-looking publish/schedule/API controls.
* No ambiguous “proceed” action.
* Empty areas are labeled.
* Long labels do not break layout.

---

## Phase 5 — Publish Readiness Gate Matrix

Target score movement: **94 → 96**

### Objective

Make Publish Readiness Tower a gate matrix.

### Work

* Redesign platform cards as gate records.
* Add official docs gate.
* Add credential redacted/future-only gate.
* Add credential validation disabled gate.
* Add manual approval gate.
* Add kill-switch gate.
* Add live adapter disabled gate.
* Add next blocker for each platform.

### Acceptance Criteria

* No platform appears live-ready.
* Telegram can be first future candidate but remains disabled.
* Credential state is redacted and non-operational.
* Every platform has next blocker.
* Dry-run readiness is clearly separate from live readiness.

---

## Phase 6 — Evidence Vault Compliance Upgrade

Target score movement: **96 → 97**

### Objective

Turn Evidence Vault into the source of trust.

### Work

* Add caveat registry.
* Add validation matrix.
* Add commit/evidence timeline.
* Add forbidden scope matrix.
* Add active blocker registry.
* Add next task discipline panel.
* Add evidence classification legend.

### Acceptance Criteria

* Caveats are visible and traceable.
* PASS_WITH_MINOR_EVIDENCE_GAP is not hidden.
* Current accepted baseline is clear.
* Evidence-only events are labeled.
* Next task cannot be invented by UI.

---

## Phase 7 — Browser QA and Regression Lock

Target score movement: **97 → 98**

### Objective

Validate the cockpit with browser/operator QA.

### Work

* Run local browser QA only after explicit approval.
* Inspect all screens.
* Check responsive widths.
* Check safety labels.
* Check disabled controls.
* Check layout.
* Record evidence.
* Fix any BLOCKED/FAIL findings in a follow-up task.

### Acceptance Criteria

* Browser QA passes with no major layout defects.
* No active forbidden controls.
* No visible secrets.
* No external network.
* No stale global metadata.
* No current/historical ambiguity.
* No misleading publish-ready state.

---

# 20. Scoring Rubric

## 20.1 Target Rubric

| Category                           | Weight |
| ---------------------------------- | -----: |
| Truth/state consistency            |     20 |
| Operator clarity under 10 seconds  |     15 |
| Evidence linkage and auditability  |     15 |
| Safety and forbidden-scope clarity |     15 |
| Layout robustness                  |     10 |
| Workflow realism                   |     10 |
| Visual identity                    |      7 |
| Accessibility/readability          |      5 |
| Screenshot-safe presentation       |      3 |
| Total                              |    100 |

## 20.2 Required Score for 95+

Minimum expectations:

* Truth/state consistency: 19/20
* Operator clarity: 14/15
* Evidence linkage: 14/15
* Safety clarity: 15/15
* Layout robustness: 9/10
* Workflow realism: 9/10
* Visual identity: 6/7
* Accessibility: 4/5
* Screenshot-safe: 3/3

## 20.3 Why Visual Identity Alone Cannot Reach 95

The UI already has a strong style.

Improving style may move the score from 68 to 72.

The path to 95 is not visual decoration.

The path is:

* truth discipline;
* evidence discipline;
* blocker discipline;
* layout discipline;
* affordance discipline;
* QA discipline.

---

# 21. Non-Negotiable Safety Boundaries

Throughout this hardening track, the following remain forbidden:

* no live posting;
* no scheduler;
* no platform API;
* no provider LLM API;
* no network;
* no scraping;
* no credential/env reads;
* no credential display;
* no autonomous replies/DMs;
* no one-button publish-all;
* no public-ready final copy;
* no fake Capital Chronicle alpha output;
* no financial advice;
* no buy/sell/hold;
* no position sizing;
* no signal-service framing;
* no market-direction color semantics;
* no hidden missing/degraded/proxy state.

The UI may show these concepts only as disabled, blocked, forbidden, or future-gated.

---

# 22. Recommended Task Sequence

## Task 0174 — Near-100 Cockpit Hardening

Label:

```text
TASK_CONTENTOPS_0174_INSTITUTIONAL_OPERATOR_COCKPIT_NEAR_100_HARDENING_V0
```

Purpose:

* canonical truth model;
* metadata reconciliation;
* screen grammar;
* status explanation model;
* read-only affordance discipline;
* layout hardening;
* tests.

Expected result:

* code/UI commit;
* no browser required;
* no live/API/env/network;
* score target: 90–94.

## Task 0175 — Publish Readiness + Evidence Vault Deep Hardening

Label:

```text
TASK_CONTENTOPS_0175_PUBLISH_READINESS_AND_EVIDENCE_VAULT_GATE_MATRIX_HARDENING_V0
```

Purpose:

* Publish Readiness Tower gate matrix;
* Evidence Vault compliance model;
* caveat registry;
* blocker registry;
* validation matrix.

Expected result:

* score target: 94–96.

## Task 0176 — Browser QA Near-100 Cockpit Walkthrough

Label:

```text
TASK_CONTENTOPS_0176_OPERATOR_APPROVED_BROWSER_QA_NEAR_100_COCKPIT_WALKTHROUGH_V0
```

Purpose:

* browser QA all screens;
* viewport inspection;
* no network;
* no screenshots unless approved;
* evidence packet.

Expected result:

* score target: 96–98 if clean.

## Task 0177 — Browser QA Findings Repair

Label:

```text
TASK_CONTENTOPS_0177_BROWSER_QA_FINDINGS_REPAIR_AND_REGRESSION_LOCK_V0
```

Purpose:

* fix findings;
* add regression tests;
* final static local cockpit hardening.

Expected result:

* score target: 97–98.

---

# 23. What Not To Do

Do not pursue 95–98 by doing any of the following:

* adding more screens;
* adding live Telegram capability;
* adding credentials;
* adding platform integrations;
* adding scheduler UI;
* adding social metrics ingestion;
* adding export/download behavior;
* making the UI more colorful;
* adding animations;
* adding market charts;
* adding “AI generated content” demos;
* adding fake public-ready posts;
* making it look like Bloomberg;
* making it look like a trading terminal;
* making it look like a SaaS scheduler.

All of those would either fail safety boundaries or distract from the real quality gap.

---

# 24. Final Definition of Done

The institutional cockpit reaches 95–98/100 when:

1. Current product truth is unambiguous.
2. Historical provenance is clearly labeled.
3. Every screen has current state, blocker, evidence, and next action.
4. Every critical status has reason and evidence.
5. No screen has active forbidden controls.
6. No screen implies live posting or public readiness.
7. Publish Readiness Tower is a gate matrix.
8. Evidence Vault is a compliance-grade audit room.
9. Content Studio separates lanes and blocks signal language.
10. Calendar remains manual workflow only.
11. Visual Export remains screenshot-safe preparation only.
12. Settings shows policy, not secrets.
13. Layout does not clip at common desktop widths.
14. Browser QA passes.
15. Tests prevent stale metadata regressions.
16. Tests prevent current/historical state mixing.
17. Tests prevent secret/network/API/live behavior leakage.
18. Operator can understand system status in under 10 seconds.
19. The UI feels like a serious institutional control surface.
20. The product remains local-only, review-only, and safe.

---

# 25. Bottom Line

The current UI has the correct strategic DNA.

It should not be redesigned from scratch.

It should be hardened.

The path to 95–98/100 is:

```text
Canonical truth model
→ current/historical separation
→ evidence-backed statuses
→ consistent screen grammar
→ no ambiguous controls
→ responsive layout hardening
→ Publish Readiness gate matrix
→ Evidence Vault compliance upgrade
→ automated UI regression tests
→ browser QA pass
```

This is how Capital Chronicle ContentOps moves from a strong prototype to an institutional-grade operator cockpit.
