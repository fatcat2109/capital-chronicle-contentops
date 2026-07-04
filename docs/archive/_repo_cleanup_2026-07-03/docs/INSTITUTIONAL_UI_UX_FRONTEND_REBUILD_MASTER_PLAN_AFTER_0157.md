# Institutional UI/UX + Front-End Rebuild Master Plan (After 0157)

Task label: TASK_CONTENTOPS_0157_INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD before this task: 995df49 — "feat: add telegram credential validation gate"
Scope: planning/spec only. This task creates committed repo authority for the
institutional UI/UX + front-end rebuild. It does NOT implement active front-end
code, does NOT run a backend, does NOT run Antigravity or any browser automation,
does NOT read credentials/env, and does NOT call any platform/provider/network API.

## 1. Owner Decision

The owner has decided to pivot the next build focus of Capital Chronicle
ContentOps toward an institutional-grade local control terminal UI/UX. The
existing static prototypes (`ui/daily_content_studio/`,
`static_prototypes/contentops_operator_console/`) proved the fixture-driven,
review-only, no-secret approach works. The decision is to converge those
fragments into a single, futuristic-institutional-fintech front-end that makes
Capital Chronicle's evidence-discipline wedge visible.

This document is committed repo authority for that rebuild. It governs future
tasks 0158–0168. It does not authorize any live, networked, credentialed, or
publish-capable behavior. Telegram live-gate sequencing (0155/0156 and any
future GO gate) is unchanged and is NOT superseded by this plan; this plan only
pivots the next *build* focus to UI planning and, later, UI implementation.

## 2. Current Baseline After 0156

- HEAD: 995df49.
- 0155 implemented a redacted Telegram credential presence check (booleans/shape
  only, no values).
- 0156 implemented a Telegram official-docs + bounded getMe-only credential
  validation gate. No live getMe was run in that session; no sendMessage, no
  post, no live adapter, no scheduler.
- Kill switch: active (`status` reports `kill_switch_halt: active`).
- Live posting: disabled. Network/provider/platform APIs: disabled.
- Test suite at baseline: 1287 passed, 28 skipped.
- Existing UI assets:
  - `ui/daily_content_studio/` — static, fixture-embedded, review-only HTML/CSS/JS
    rendering the accepted 0145 UI data contract. No backend, no fetch, no CDN,
    no storage, no publish/schedule/connect buttons.
  - `static_prototypes/contentops_operator_console/` — earlier static operator
    console prototype.
- Existing UI contracts/specs already in repo:
  - `schemas/daily_content_studio_ui_data_contract_packet.schema.json`
  - `schemas/frontend_static_prototype_packet.schema.json`
  - `schemas/operator_ui_ux_spec_packet.schema.json`
  - `schemas/content_calendar_spec_packet.schema.json`
  - `docs/OPERATOR_UI_UX_AND_CONTENT_CALENDAR_SPEC_AFTER_0135.md`
  - `docs/FRONTEND_STATIC_PROTOTYPE_SPEC_AND_FIXTURES_AFTER_0136.md`
  - `docs/TASK_CONTENTOPS_0145..0147` UI data-contract/static-frontend/review docs.

## 3. Why The Current Static UI Is Insufficient

The current static UI is a valid v0 proof, but it is not an institutional control
terminal:

- It renders a single Daily Content Studio data-contract fixture. It is not a
  multi-screen terminal with Mission Control, Publish Readiness, Evidence Vault,
  Calendar, or Telegram pilot gate views.
- Visual language is functional, not institutional. It does not yet express the
  futuristic-institutional-fintech direction (dark terminal base, dense readable
  tables, semantic state system, low-noise motion).
- State semantics are partial. There is no single, enforced, repo-wide status
  vocabulary rendered consistently across every screen.
- There is no shared view-model contract that drives the whole terminal from
  CLI-generated, schema-validated JSON. Each prototype embeds its own fixture.
- There is no screenshot/briefing-safe mode guarantee enforced as a contract
  across all screens.
- There is no defined QA pass (Antigravity browser walkthrough) gated behind a
  Cline-built, locally testable UI.

The wedge — evidence discipline, refusal modes, missing/degraded/proxy data
visibility, forecast-readiness gates, failure forensics, supervised publishing
gates, and explicit no-signal-service framing — is only partially visible. The
rebuild makes it the spine of the interface.


## 4. North-Star Product Experience

Capital Chronicle ContentOps should feel like an institutional local control
terminal, not a SaaS template, not a crypto casino, and not a trading-signal
terminal.

- Institutional local control terminal: an operator opens it locally and within
  seconds sees global safety status, what is blocked and why, and what is ready
  for human review.
- Macro content governance: content is governed, not generated-and-shipped.
  Every artifact carries source lineage, limitations, and a review gate.
- Evidence-first: evidence is the interface. The default view of any artifact is
  its sources, its limitations, and its data-sufficiency state.
- Refusal-mode visible: when the system refuses (missing data, degraded data,
  proxy-only data, forecast-not-ready), the refusal is a first-class, explained,
  visible state — never a silent omission.
- No signal-service posture: no buy/sell/hold, no position sizing, no guaranteed
  prediction, no P&L framing, no "alpha signal" language anywhere in the UI.

## 5. Design Language

- Futuristic institutional fintech. Restrained, precise, high-information-density.
- Dark terminal base. Deep neutral background, layered surface elevations.
- High-contrast cards for primary state and decisions.
- Dense, readable tables for evidence, lineage, and audit rows.
- Semantic state colors (see section 6) applied consistently and only for state —
  never decoratively.
- Low-noise motion: subtle transitions for state changes only. No animated
  marketing flourishes, no pulsing "live" glows, no confetti.
- No crypto casino aesthetic: no neon gradients-as-identity, no coin/rocket
  iconography, no hype typography.
- No trading-signal / P&L color semantics: green/red must NOT be used to imply
  gains/losses or buy/sell. Green/red are reserved for PASS / BLOCKED *operational*
  states only, with a text label always accompanying any color.

## 6. Color / Status Semantics

A single status vocabulary is enforced repo-wide. Every status token renders with
an accessible label + icon + color (color is never the only signal). Exact hex
values are defined in the 0158 design-system task.

| Token | Meaning | Color family (label always shown) |
| --- | --- | --- |
| PASS | Validated, contract-clean, review-ready | calm green |
| DEGRADED | Works but inputs are partial / lower quality | amber |
| BLOCKED | Fail-closed; action not permitted | red |
| REVIEW_REQUIRED | Awaiting mandatory human review | blue |
| NOT_PUBLIC_POSTABLE | Never public-postable in current state | slate + lock |
| LIVE_DISABLED | Live capability is intentionally off | slate + lock |
| UNKNOWN | State could not be determined | neutral gray + "?" |
| PROXY_ONLY | Data is a proxy, not the real source | violet |
| STALE | Data is past freshness threshold | amber + clock |
| SECRET_REDACTED | A value exists but is intentionally hidden | slate + shield |

Rules:
- Red is BLOCKED (operational), never "loss".
- Green is PASS (operational), never "gain" or "buy".
- DEGRADED, PROXY_ONLY, STALE, and UNKNOWN must never be hidden or collapsed into
  PASS. Missing stays visible.
- SECRET_REDACTED must never reveal value, snippet, length, or hash.

## 7. Core UX Principles

1. State before action. Every screen shows its safety/validation state before it
   offers any control. Controls that are not permitted render disabled with an
   explanation, never hidden in a way that implies they would work.
2. Evidence is the interface. The primary content of an artifact view is its
   sources, lineage, limitations, and data-sufficiency — not the polished copy.
3. Missing stays visible. Missing/degraded/proxy/stale/unknown data is always
   shown explicitly with its reason. No silent gaps.
4. Review-only by default. Nothing is public-postable by default. Public posting,
   scheduling, and live adapters are out of scope for the entire 0158–0168
   sequence and render as visually gated, disabled, explained future states.
5. Screenshot / briefing-safe mode. A mode in which the operator can capture or
   present the terminal with zero secrets, zero env paths, and no false readiness
   claims. Safe mode never invents a PASS it does not have.

## 8. Target Information Architecture

Top-level terminal areas (left-nav or command palette):

1. Mission Control — global safety, kill-switch, blocked summary, what's ready.
2. Content Studio — daily run, drafts, angles, external-LLM handoff (no execution).
3. Grounded News Workbench — grounded-news angle lab, source-backed only.
4. Publish Readiness Tower — dry-run readiness, capability registry, gates (no live).
5. Telegram Pilot Gate — read-only redacted gate status (no getMe/sendMessage here).
6. Approval Queue — items awaiting mandatory human review.
7. Content Calendar — planning view; never marks anything public-ready.
8. Evidence Vault — source artifacts, lineage, limitations, data-sufficiency.
9. Visual Export Studio — screenshot/briefing-safe export of redacted views.
10. Settings / Safety Policy — read-only policy + safety posture display.

## 9. Screen Inventory

| Screen | Purpose | Key states surfaced |
| --- | --- | --- |
| Command Center | Global posture landing | PASS/DEGRADED/BLOCKED, LIVE_DISABLED, kill switch |
| Content Lane Control | Lane separation (process / macro-edu / grounded-news / artifact-backed) | lane policy, NOT_PUBLIC_POSTABLE |
| Daily Content Studio | Daily run packet view | REVIEW_REQUIRED, source lineage, limitations |
| Draft Inspector | One draft, deep | sources, limitations, forbidden-action gating |
| Grounded News Angle Lab | Angle ideas from grounded sources | PROXY_ONLY, source-backed only, no signal framing |
| Publish Automation Readiness | Dry-run readiness matrix | LIVE_DISABLED, BLOCKED reasons, capability registry |
| Telegram Pilot Gate | Redacted gate status | SECRET_REDACTED, LIVE_DISABLED, next-gate-required |
| Approval Queue | Human review queue | REVIEW_REQUIRED, decision history |
| Content Calendar | Planning calendar | never public-ready; planning only |
| Evidence Vault | Evidence + lineage | STALE, PROXY_ONLY, UNKNOWN, data sufficiency |
| Visual Export Studio | Safe capture/briefing | screenshot-safe, no secrets, no false readiness |
| Settings / Safety Policy | Posture + policy | read-only; all live flags false |

## 10. Front-End Architecture Direction

- Local-only. The UI opens from `file://` or a trivial static file open. No
  backend, no server, no API routes — until an explicit, separate future GO.
- No backend until explicit GO. The 0158–0168 sequence never introduces a server.
- Fixture/mock data first. All screens render from deterministic local fixtures.
- JSON / view-model driven. A single view-model contract (0159) drives all screens.
- CLI-generated view models. View models are produced by deterministic CLI
  summaries from existing repo packets/fixtures, then embedded for `file://` use.
- Strict schema validation. Every view model validates against a JSON schema;
  fail-closed on violation.
- No secrets in browser state. No tokens, chat IDs, env values, or env paths ever
  enter the view model or the DOM. SECRET_REDACTED only.
- No platform API calls from browser. No `fetch`, no CDN, no external scripts, no
  storage that could carry secrets.
- Deterministic fixtures. Same fixture in → same render out, for reproducible QA.
- No new front-end framework dependency. Vanilla HTML/CSS/JS only, consistent with
  the existing `ui/daily_content_studio/` prototype. No React/Vue/Svelte/Next/Vite.

## 11. Cline vs Antigravity Role Split

- Cline builds and validates architecture, schemas, view-model contracts, static
  front-end code, fixtures, and tests. Cline is the source of truth for structure.
- Antigravity is used ONLY for browser QA AFTER Cline has produced a locally
  testable UI (task 0167). Antigravity opens the built UI in a browser, navigates
  screen-by-screen against expected states, captures screenshots, records a
  walkthrough, and reports visual bugs.
- Antigravity must not design architecture, must not broaden scope, must not call
  platform APIs, and must not inspect secrets. It receives narrow, screen-by-screen
  QA scripts only.


## 12. Detailed Phase Roadmap

| Task | Title | Builder | Antigravity | Credentials/API |
| --- | --- | --- | --- | --- |
| 0158 | Design System + Futuristic Fintech Visual Contract | Cline | No | No |
| 0159 | UI View-Model Contract v2 | Cline | No | No |
| 0160 | Institutional Shell Prototype | Cline | No | No |
| 0161 | Command Center Screen | Cline | No | No |
| 0162 | Content Studio Rebuild | Cline | No | No |
| 0163 | Publish Readiness Tower | Cline | No | No |
| 0164 | Evidence Vault | Cline | No | No |
| 0165 | Calendar + Workflow Board | Cline | No | No |
| 0166 | Visual Export / Screenshot-Safe Mode | Cline | No | No |
| 0167 | Antigravity Browser QA Pass | Antigravity QA (Cline-built UI) | Yes (QA only) | No |
| 0168 | Cline Institutional Polish Pass | Cline | No | No |

Each phase is fully specified in
`docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_BACKLOG_AFTER_0157.md`.

Sequencing rules:
- 0158–0166 build the design system, view-model contract, shell, and screens.
  Antigravity is NOT allowed in these tasks.
- 0167 is the only task in this sequence where Antigravity is allowed, and only
  for browser QA against a Cline-built, locally testable UI.
- 0168 is a Cline polish pass that fixes visual issues found in the 0167
  Antigravity evidence. Antigravity is not used in 0168.
- No task in 0158–0168 may create live posting, a scheduler, autonomous
  replies/DMs, scraping, a live adapter, or a real publish-all button.

## 13. Institutional Quality Bar

- Global safety status visible within 10 seconds of opening the terminal.
- Every BLOCKED state explains why, in plain language, with the failing reason.
- Every draft shows source/evidence/limitation context before its polished copy.
- Every platform gate shows LIVE_DISABLED status explicitly.
- Every credential state is rendered SECRET_REDACTED (no value/snippet/length/hash).
- Future live features are visually gated (disabled + explained), never active.
- Missing/degraded/proxy-only/stale data is always visible with reason.
- No signal-service framing anywhere (no buy/sell/hold, no P&L, no guaranteed call).
- No automatic public-posting implication anywhere in the UI.
- Screenshot-safe mode shows no secrets and asserts no false readiness.
- The UI is ready for an Antigravity browser walkthrough (deterministic, local).

The detailed, testable form of this bar is in
`docs/INSTITUTIONAL_UI_UX_QUALITY_BAR_AND_ACCEPTANCE_MATRIX_AFTER_0157.md`.

## 14. Testing Strategy

- Schema validation tests for every view-model contract (fail-closed on drift).
- Deterministic fixture render tests: valid fixtures render expected states;
  negative fixtures (live-enabled, secret-visible, public-ready, signal-language)
  fail closed.
- Static-asset safety tests (extending the existing
  `test_daily_content_studio_static_frontend.py` pattern): no `fetch`, no remote
  URLs, no CDN, no external scripts, no storage, no publish/schedule/connect/OAuth
  buttons, no secrets in markup.
- Security scan tests (extending `test_security_scans.py`) over new UI assets and
  fixtures for token/chat-id/secret/env-path/api.telegram.org/sendMessage/getMe
  patterns.
- CLI summary tests for any new view-model summary command, asserting all live/
  credential/api/scheduler/scraping counters are 0 and packet_status is pass only
  when there are no errors.
- Antigravity (0167) browser QA produces evidence only; it does not replace the
  deterministic Cline tests.


## 15. Non-Negotiables

- No backend/server in the 0158–0168 sequence.
- No new front-end framework or dependency (vanilla HTML/CSS/JS only).
- No live posting, scheduling, scraping, metrics auto-ingestion, autonomous
  replies/DMs, live adapter, or real publish-all button.
- No credential/env reads. No secrets/values/snippets/lengths/hashes/paths in any
  file, fixture, view model, DOM, screenshot, or evidence.
- No platform/provider/network/search/news/market-data API calls from the repo or
  the browser.
- No public-ready or publish-ready final copy generation.
- No signal-service / trading / execution / broker / order-routing framing.
- Kill switch remains active; live posting remains disabled.
- Residual drift (`.env`, listed PDFs, old bundles, `recovered_strategy_docs/`)
  remains untouched.

## 16. Explicit Stop Conditions For UI Work

Stop and report BLOCKED (do not proceed) if any of the following would be required:

- Implementing the UI requires a backend/server or a network call.
- A screen cannot render its required safety state from local fixtures alone.
- A view model would need a real secret, env value, or env path to be useful.
- A task would need to enable a live capability to demonstrate a screen.
- Antigravity is requested before a Cline-built, locally testable UI exists.
- A required evidence item would require reading credentials or touching residual
  drift.

## 17. Evidence Requirements For Future UI Tasks

Every 0158–0168 task must return a final evidence packet containing at minimum:

- Task label, PASS/BLOCKED/FAIL, worker, repo path, branch, starting/final HEAD.
- Files inspected / created / changed / explicitly staged.
- Test results (focused + full suite), CLI summary outputs.
- UI scope status (active frontend changed, dependencies added, backend created,
  browser automation used, Antigravity used, screenshots/video captured).
- Credential/API status (env read, Telegram API, getMe, sendMessage, provider,
  platform, network/search/news/market — all expected `no` except where a task
  explicitly scopes Antigravity QA in 0167).
- Safety status (live posting, scheduler, scraping, autonomous replies/DMs,
  one-button publish-all, public-ready copy, signal framing, secrets printed —
  all expected `no`).
- Scan command/results with safe-match classification.
- Kill switch status, residual drift touched (`no`), final git status.

## 18. Relationship To Telegram Live-Gate Sequencing

This task does NOT supersede Telegram live-gate sequencing. The Telegram lane
(0152 readiness gate, 0153 credential setup guide, 0155 presence check, 0156
official-docs + getMe-only validation gate, and any future explicit GO gate)
remains the authoritative path for supervised live posting readiness. This UI
master plan only pivots the next *build* focus to UI planning and, later,
fixture-driven UI implementation. No UI task enables posting. The Telegram Pilot
Gate screen is a read-only, redacted *display* of existing gate state; it never
calls getMe or sendMessage and never reveals credentials.

