# Pre-Alpha General/Process and Grounded-News Master Plan - After TASK_CONTENTOPS_0075

LOCAL ONLY | ADVISORY ONLY | DOCS/POLICY ONLY | HUMAN REVIEW REQUIRED | NOT PUBLIC POSTABLE
NO PROVIDER CALL | NO SEARCH CALL | NO PLATFORM ACTION | NO SCHEDULER | NO CREDENTIALS

This is a strategy/policy document. It adds no runtime capability. It does not
generate, post, schedule, or call any external service. It describes how Capital
Chronicle ContentOps should operate during the pre-alpha period.

## 1. Current wait-state baseline
- Repo: A:\Capital Chronicle\tools\cc-live-contentops
- Accepted wait-state commit: f9c4d69 (0073); latest docs-bundle commit: 4fd7237 (0074)
- Wait-state status: WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS
- Pointer: WAIT_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS_OR_OPERATOR_SELECTED_LOCAL_MAINTENANCE
- Enforced flags: local_only, advisory_only, fixture_only, human_review_required all true;
  public_content_allowed_now, live_integration_allowed_now, approval_granted, publish_ready,
  provider_call_allowed, search_call_allowed, platform_action_allowed all false.
- The complete local review stack (intake/readiness gate, bridge/route guard,
  pipeline trace, editorial QA/preview/selection, packet export, audit, review
  queue, decision/history, registry/ledger, dashboard/handoff, Project Sources
  bundle) exists and is ready to receive future approved artifacts. Real alpha
  artifacts do not exist in this sidecar yet and must never be faked.

## 2. Strategic decision
- Do NOT pause completely. A full pause wastes the cheapest pre-alpha window to
  build audience and credibility.
- Do NOT build public-posting automation. No generator, no scheduler, no platform
  API, no auto-posting, no autonomous replies/DMs.
- DO open a tiny, manual, pre-alpha content strategy lane for genuinely general
  first-party content, plus a grounded-news/research-context lane where the
  operator (or ChatGPT Deep Research) supplies sources from outside the repo.
- Sequence: build guardrails and source/claim review BEFORE any generator or
  export. Keep artifact-backed Capital Chronicle content blocked until real
  approved alpha artifacts exist.

## 3. Two-lane model
Two content classes that are never merged.

### Lane A: pre_alpha_general_process
- Real first-party authorship about you, your process, and evergreen concepts.
- No source artifact IDs, no DQR/data-sufficiency/forecast-readiness fields, no
  artifact lineage.
- Structurally barred from the real-artifact intake gate and the
  artifact-to-packet bridge. It can never claim artifact lineage or route to
  APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE.
- Manually authored, manually reviewed, manually posted by Jim.

### Lane B: future_artifact_backed
- Requires a real approved Capital Chronicle alpha artifact.
- Requires source IDs, lineage, freshness, limitations, and explicit
  DQR/data-sufficiency/forecast-readiness states.
- Must pass the existing readiness gate to READY_FOR_LOCAL_REVIEW_ONLY, never
  directly to public-ready.
- BLOCKED until real alpha artifacts exist. This plan does not unblock it.


## 4. Grounded news / research context lane
- News is a HOOK, not a SIGNAL. Current events may frame education and
  perspective; they are never a basis for a market call or recommendation.
- Current news may support: macro education, data sufficiency, forecast
  readiness, failure forensics, and product philosophy.
- Grounded research is operator-supplied / manual for now. The operator (or
  ChatGPT Deep Research) gathers and cites sources OUTSIDE the repo.
- The repo does NOT call web/search/provider APIs. ContentOps may later validate
  metadata and claims of an operator-supplied research brief LOCALLY, but never
  fetch anything itself.
- Any news-anchored claim must carry a dated, attributable source supplied by the
  operator. No unverified numeric market claims.

## 5. Safe content pillars
- Build-in-public: what we are building, what we discarded, and why.
- Macro education: evergreen explanations of economic/data concepts.
- Data sufficiency: what must be true before a number is worth publishing.
- Forecast readiness: why we will not publish premature forecasts.
- Failure forensics: how data/process can silently mislead (own or
  well-documented public post-mortems, framed as lessons, not advice).
- Product philosophy: positioning, including why we refuse to be a signal service.
- Grounded news explainers: current event used as a teaching hook with cited,
  operator-supplied sources.

## 6. Forbidden content (hard stop)
- Buy / sell / hold.
- Position sizing.
- Entries / exits.
- Price targets.
- Signal-service framing.
- AI trading bot framing.
- Broker / order / execution language.
- Guaranteed prediction.
- Unverified numeric market claims.
- Fixture/demo content made public-postable.
- Claiming Capital Chronicle alpha exists before real approved artifacts.

## 7. Manual-only workflow
1. Operator / ChatGPT Deep Research gathers sources outside the repo.
2. Operator creates or supplies a research brief (with cited, dated sources).
3. ContentOps can later validate brief metadata/claims LOCALLY (no fetching).
4. Jim reviews and manually posts.
5. No auto-posting, no platform API, no scheduling, no autonomous replies/DMs.

## 8. Proposed future backlog
- 0076: local grounded research brief schema/template. Defines the brief
  structure (sources, dates, claims, limitations, pillar, forbidden-language
  checklist). No network, no fetching, docs/schema only.
- 0077: review-only packet for Jim-authored / LLM-assisted drafts. Local review
  artifact only; produces NO final public copy and grants no publish authority.
- 0078: manual publishing and metrics log guide. Documents how Jim manually posts
  and records results by hand. No scraping, no platform API, no scheduling.
- Real alpha artifact resume path remains SEPARATE and unchanged (see
  ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_AFTER_0073.md). This backlog does not touch it.

## 9. Clear rule
- Build guardrails BEFORE any generator.
- Build source/claim review BEFORE any export.
- Keep artifact-backed content BLOCKED until real approved alpha artifacts exist.
- Lane A (general/process) and Lane B (artifact-backed) never merge; a general
  item that contains a market call must be blocked by QA, not waved through.
