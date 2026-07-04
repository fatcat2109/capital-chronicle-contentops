# Capital Chronicle ContentOps — Reconciled Final Product Master Plan (After 0174AO)

**Task:** `TASK_CONTENTOPS_0174AO_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AND_STRATEGY_RECOVERY_V0`
**Status:** CURRENT STRATEGY AUTHORITY (supersedes prior roadmap authority for product direction)
**Branch:** master · local-only · supervised · fail-closed
**Supersedes for strategy:** `CONTENTOPS_RECONCILED_ROADMAP_AFTER_0126.md`, `FINAL_MASTER_PLAN_PRE_ALPHA_CONTENT_AND_API_AUTOMATION_READINESS_AFTER_0077.md` (both retained as historical reference)
**Sibling authorities (still binding):**
- `docs/CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md`
- `docs/CAPITAL_CHRONICLE_CONTENTOPS_INSTITUTIONAL_COCKPIT_MASTER_PLAN.md`
- `docs/CURRENT_STATE_SUMMARY_AFTER_0174AM.md`

---

## 0. Executive Decision

Capital Chronicle ContentOps now returns from the completed V4 visual-hardening track
to the original product north star:

**The final product is a local-first supervised content distribution operating system
for Capital Chronicle.**

It is not an autonomous posting bot. It is a workstation where the system prepares,
validates, compiles, and audits content packets, and the operator (Jim) may
approve/dispatch only after every gate passes.

The target action is:

**"One approved operator action may dispatch only a prevalidated, evidence-backed,
platform-constrained content packet."**

**The system is powerful because it is controlled, not because it is autonomous.**

This document reconciles owner intent (appended ChatGPT strategy report, 0174AO) with
repo evidence: the accepted 0174AM V4 baseline, the 0126 reconciled roadmap, the 0077
final master plan, and the existing dry-run automation docs (platform adapters,
approval ledger, kill switch, redacted audit, mock publish, credential envelope,
Telegram pilot gate). Owner intent is planning input; repo files and git history remain
authority.

---

## 1. Final Product Definition

ContentOps is the operational layer between Capital Chronicle's research artifacts and
public distribution. It lets the operator:

1. ingest approved Capital Chronicle artifacts or approved grounded-news briefs;
2. generate human-grade drafts through a bounded LLM editorial layer;
3. validate claims, risk language, citations, platform constraints, and safety rules;
4. assemble an evidence-backed approval packet;
5. preview exact per-platform payloads;
6. approve with one explicit operator action;
7. dispatch only the approved payloads through gated platform adapters;
8. record redacted audit events, URLs, metrics, and performance feedback.

It preserves Capital Chronicle's wedge: data sufficiency, source trust, forecast
readiness, missing/degraded/proxy transparency, refusal discipline, forecast/paper
outcome forensics, and compare-to-improve learning.

---

## 2. Correct Meaning of "One Button"

The "one button" does NOT mean "AI writes anything → system posts everywhere."

It means:

```text
System prepares a complete approval-ready dispatch packet
→ Jim reviews the packet
→ Jim clicks one explicit approval/dispatch action
→ system posts only the exact approved payloads
→ audit ledger records the operator-approved action.
```

The control should be named like **"Approve & Dispatch This Packet"**, never
"Publish Everything."

### Required one-button preconditions (all must hold)

1. packet state is `dispatch_packet_ready`;
2. every included post has `guardrail_pass = true`;
3. no post has unresolved `BLOCKED`, `UNKNOWN`, or `REVIEW_REQUIRED` state;
4. exact payload text/media is frozen (hash-pinned);
5. platform destinations are explicit;
6. all limitations and citations are visible;
7. approval ledger can create a signed operator decision;
8. kill switch is inactive only for this approved operation;
9. credentials are referenced only by redacted slot ID;
10. platform live gate is open;
11. request/response audit redaction is guaranteed;
12. rollback/manual fallback exists.

If any precondition fails, the button renders as **blocked** and explains why.

---

## 3. Supervised Content Distribution OS — Architecture

```text
Artifact / Brief Intake
→ Content Intent Plan
→ LLM Editorial Writer (bounded)
→ Deterministic Guardrail Validation
→ Platform Payload Compiler
→ Approval Packet
→ Operator One-Button Approval / Dispatch
→ Supervised Platform Adapter (dry_run | mock_live | supervised_live)
→ Redacted Audit Ledger
→ Metrics Sync
→ Performance Review
→ Better Content Strategy
```

The accepted V4 cockpit is the operator shell for this engine; it is not the engine.

---

## 4. Core System Layers

### 4.1 Source / Artifact / Brief Intake
Decides what the content is allowed to be based on evidence maturity. Input types:
approved CC artifact packet, grounded news research brief, general/process brief,
forecast readiness summary, data-sufficiency/audit artifact, paper/shadow outcome
packet, forensics packet, product/build milestone packet.

Each input declares: source type; authority level; current/historical/reference-only
classification; evidence IDs; allowed content lanes; forbidden transformations;
limitation requirements; freshness status; artifact-backed or non-artifact-backed
status.

### 4.2 Content Intent Planner
Converts evidence into a content plan before any writing: content lane, audience mode,
channel mix, post objective, allowed claims, required citations, required limitations,
platform fit, content risk tier, and whether a draft is allowed.
Output: **`ContentIntentPacket`** (deterministic, reviewable).

### 4.3 Bounded Human-Grade LLM Editorial Writer
**Can:** rewrite, summarize, generate hooks, create platform variants, suggest
titles/subtitles, propose hashtags/keywords, improve narrative tension, adapt tone by
audience, produce first-comment suggestions, generate newsletter sections, critique
drafts, score editorial quality.

**Cannot:** invent facts, citations, metrics, or source IDs; certify data sufficiency;
approve content; remove limitations; override blockers; make market calls; imply CC
forecast authority when not present.

Voice target: human, sharp, credible, founder/operator voice; no hype, no trader-bait,
no signal language; clear wedge "trust before forecast." No provider/API call exists
yet; any future provider integration must pass a dedicated live/provider gate.

### 4.4 Deterministic Content Safety Compiler
Turns safety rules into enforceable gates. Checks: financial-advice wording;
buy/sell/hold phrasing; forecast/signal framing; unsupported numbers; fake-artifact
language; source/citation linkage; missing limitation labels; platform policy risk;
duplicate/cross-post risk; public-postable status; LLM hallucination risk;
token/secret leakage; raw vendor-data leakage.

Output states: `PASS`, `REVIEW_REQUIRED`, `BLOCKED`, `UNKNOWN`. Only `PASS` may move
toward approval.

### 4.5 Canonical Social Post Object
Every draft becomes a canonical object — the unit of review, approval, dispatch, and
metrics:

```text
post_id
source_packet_id
content_lane
audience_mode
platform_targets
canonical_text
platform_variants
citations
limitations
claim_risk
guardrail_results
approval_state
dispatch_state
audit_refs
metrics_refs
```

### 4.6 Platform Payload Compiler
Produces exact per-platform payload previews. Target platforms: Telegram, LinkedIn, X,
Threads, Substack, Facebook Page, Instagram, TikTok (later), YouTube/Shorts (later).
Each payload includes: exact text; media requirements; character limits; disclosure
fields; destination identity; warnings; rate-limit metadata; unsupported-feature flags;
dry-run render; mock response; live-eligibility state.

### 4.7 Approval Packet and Operator Decision Ledger
Makes operator approval explicit, inspectable, reversible, auditable. Packet contains:
all source evidence; full draft text; platform variants; variant differences; guardrail
report; limitation checklist; claim-risk summary; exact destinations; dispatch
preconditions; kill-switch state; redacted credential slots; rollback/manual fallback;
operator approval field.

Approval states:

```text
draft_review_only
platform_dry_run_ready
operator_review_required
operator_approved_for_mock_dispatch
operator_approved_for_live_dispatch
blocked
revoked
dispatched
dispatch_failed
metrics_recorded
```

Approval is append-only and revocable.

### 4.8 One-Button Dispatch Controller
Executes only a fully approved packet: read approved packet → revalidate payload hashes
→ recheck guardrails → recheck kill switch → recheck credential slot availability
without exposing secrets → recheck platform live gate → dispatch platform-by-platform →
store redacted request/response audit → store returned URLs/IDs → mark partial failures
→ trigger metrics follow-up queue. No dispatch without a current approval record.

### 4.9 Platform Adapter Modes
Every adapter has three modes and **never starts in live**:

```text
dry_run        # render + validate only, no network
mock_live      # simulated responses, no real API
supervised_live # real API, one approved packet, kill-switch + audit required
```

Build order: Telegram → LinkedIn → X → Threads → Substack (markdown/export first) →
Facebook Page / Instagram → TikTok → YouTube/Shorts.

### 4.10 Credential and Secret Boundary
Credentials remain outside the repo.
**Allowed:** credential slot IDs; redacted presence checks; fake-token tests; redaction
validators; env var name conventions; operator local setup guides.
**Forbidden:** reading real credentials without an explicit task; printing secrets;
committing secrets; sending credentials to ChatGPT; storing raw responses containing
secrets; hidden credential-dependent behavior.

### 4.11 Redacted Audit Ledger
Append-only, redacted request/response records; returned URLs/IDs; partial-failure
markers; operator decision linkage. No secrets, no raw vendor payloads with tokens.

### 4.12 Metrics / Performance Feedback Loop
After posting, collect or import: post URL; platform post ID; impressions/views;
engagement; profile visits; newsletter clicks/signups; paid conversion indicators;
reply/comment quality; content type; topic; hook type; audience mode; platform variant.
Feeds content performance review, best/worst structure analysis, calendar suggestions,
product learning, monetization funnel. **No scraping.**

---

## 5. Content Strategy Lanes

- **Lane A — Build-in-Public / Process** (use now): why missing data blocks forecasts,
  why CC refuses bad forecasts, why official sources matter, why proxy-only must be
  labeled, why forecast readiness is a gate, what was built.
- **Lane B — Grounded News Context** (use now, carefully): news is a hook, not a signal.
  Allowed: explain uncertainty, what evidence would be needed, why one headline is
  insufficient, data/source discipline. Forbidden: actionable direction, target prices,
  "asset X will move," "our model predicts," "watch this level."
- **Lane C — Artifact-Backed** (only after approved artifacts exist): requires artifact
  ID, lineage, freshness, limitations, DQR/sufficiency/readiness state, missing/proxy/
  degraded labels, review state, non-advisory framing.
- **Lane D — Forecast Readiness Reports** (after readiness artifacts): public teaser +
  readiness map + blocked/degraded/pass explanation, no advice; paid weekly macro
  readiness report + source gap table + catalyst watch + limitations.
- **Lane E — Shadow Forecast / Paper Outcome Review** (after outcomes): post-outcome
  review preferred, explain what was known/changed/why, no trade signal.
- **Lane F — Forecast Forensics** (after forensics artifacts): failed forecast library,
  failure class, data state at forecast time, repair candidate, compare-to-improve.

---

## 6. UI Implication — V4 Cockpit as Accepted Shell, Not Build Frontier

The accepted 0174AM V4 cockpit (96/100, locked by 0174AN) is the operator shell. It is
**not** the current build frontier. The next frontier is the product engine behind the
cockpit. Future screens may eventually map to operating rooms: Command Center, Artifact/
Brief Intake, LLM Writer Studio, Draft Inspector, Approval Queue, Platform Payload
Compiler, Dispatch Control Tower, Credential Safety Room, Evidence Vault, Metrics &
Performance Review, Content Calendar, Screenshot/Report Export.

**No new UI work begins until backend/domain contracts are reconciled.** The UI must not
invent capabilities the contracts do not support. Any UI change must justify itself
against the accepted 0174AM baseline.

---

## 7. Reconciled Tensions (explicit)

| Tension | Reconciliation |
|---|---|
| Automation readiness vs no live posting yet | Build the rails (dry_run/mock_live); live stays disabled until each gate is real. |
| Human-like LLM writer vs no provider/API call yet | Define bounded editorial contract + deterministic validators now; provider integration only behind a dedicated live/provider gate. |
| One-button approval/dispatch vs no autonomous posting | One button = approve a prevalidated frozen packet; never "publish everything." |
| Multi-platform management vs no platform API until gates | Canonical post + payload compiler in dry-run; per-platform supervised-live GO/NO-GO. |
| V4 visual baseline accepted vs engine not built | Cockpit frozen as shell; engine built behind contracts first. |
| Grounded/process content allowed vs no artifact-backed claims yet | Lanes A/B usable now; Lanes C–F gated on real artifacts. |
| Final-product ambition vs strict safety | Automation allowed only when supervised, source-aware, evidence-backed, approval-gated, kill-switch protected, reversible, redacted, per-platform constrained, logged, testable, explicitly scoped. |

---

## 8. Non-Negotiable Boundaries

ContentOps must never become: a financial-advice engine; a buy/sell/hold generator; a
signal service; a trading execution system; an autonomous engagement bot; a cross-
platform spammer; a fake-alpha marketing machine; a hidden credential executor; a
scheduler that publishes without current approval; a system that turns missing data into
confidence.

---

## 9. Phased Roadmap (summary)

0. **Reconcile & recover strategy authority** (this task, 0174AO) — docs only.
1. **0174AP Domain model unification** — ContentIntentPacket, CanonicalSocialPost,
   PlatformPayload, ApprovalPacket, DispatchPacket, RedactedAuditEvent, MetricsRecord.
2. **0174AQ Bounded LLM editorial workbench contract** — no provider calls, preserves
   limitations, blocks hallucinated authority.
3. **0174AR Platform payload compiler dry-run** — Telegram, LinkedIn, X, Threads,
   Substack, Facebook Page, Instagram, TikTok placeholder.
4. **0174AS Approval ledger + one-button mock dispatch** — signed approval, immutable
   packet hash, revocation, kill switch, mock only.
5. **0174AT Credential envelope + redacted presence gates** — fake-token tests only, no
   real env reads.
6. **0174AU Telegram supervised live pilot design gate** — plan only, no token, no API.
7. **Later** — multi-platform supervised dispatch (platform-by-platform GO/NO-GO),
   metrics sync, content-to-product feedback loop.

Detail for each task lives in
`docs/CONTENTOPS_FINAL_PRODUCT_ROADMAP_AFTER_0174AO.md`.

---

## 10. Final Operating Principle

Build the automation rails. Keep live dispatch disabled until each gate is real. Allow
the operator's one-button approval only after the packet is already deterministic,
evidence-backed, platform-constrained, policy-clean, and audit-ready. The final product
should feel powerful because it is controlled, not because it is autonomous.
