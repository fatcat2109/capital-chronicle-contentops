# ContentOps Final Product Roadmap (After 0174AO)

**Task authority:** `CAPITAL_CHRONICLE_CONTENTOPS_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AFTER_0174AO.md`
**Principle:** Build the rails. Keep live dispatch disabled until each gate is real.
**Standing rules:** local-only · fail-closed · no network · no credential/env reads ·
no live posting · V4 UI frozen until contracts are reconciled.

---

## TASK_CONTENTOPS_0174AP_DOMAIN_MODEL_UNIFICATION_FOR_SUPERVISED_CONTENT_DISTRIBUTION_OS_V0

**Objective:** Unify the legacy Content Studio and Publish Automation models into one
coherent domain model: `ContentIntentPacket`, `CanonicalSocialPost`, `PlatformPayload`,
`ApprovalPacket`, `DispatchPacket`, `RedactedAuditEvent`, `MetricsRecord`.

**Allowed scope:** JSON schemas; fixtures (pass/block/review paths); deterministic
local validators; tests. Docs that describe the contracts.

**Forbidden scope:** live calls; platform credentials; network; provider/LLM API; UI
changes; scheduler.

**Acceptance:** all seven schemas validate; fixtures cover PASS / BLOCKED /
REVIEW_REQUIRED / UNKNOWN; no credentials; no network; tests green.

**Stop conditions:** stop if any schema requires a network fetch, credential read, or a
live platform identity to validate.

---

## TASK_CONTENTOPS_0174AQ_BOUNDED_LLM_EDITORIAL_WORKBENCH_CONTRACT_V0

**Objective:** Define the bounded human-grade editorial layer as a contract: prompt
contract, editorial voice profiles, audience modes, hook taxonomy, claim-risk
preservation, limitation preservation, hallucination checks, before/after critique
packet.

**Allowed scope:** contract docs; schemas; deterministic validators; fixtures including
unsafe/hallucinated examples; tests.

**Forbidden scope:** provider/LLM API calls (no key, no network); inventing facts/
citations/metrics; removing limitations; approving content; market calls.

**Acceptance:** a deterministic validator proves LLM output cannot remove limitations or
invent authority; unsafe fixtures are blocked; operator review remains required; no
provider call exists.

**Stop conditions:** stop if a provider API key or network call is required. Provider
integration is a separate future live/provider gate.

---

## TASK_CONTENTOPS_0174AR_PLATFORM_PAYLOAD_COMPILER_DRY_RUN_V0

**Objective:** Rebuild platform dry-run payload renderers around `CanonicalSocialPost`
for: Telegram, LinkedIn, X, Threads, Substack (markdown/export), Facebook Page,
Instagram, TikTok placeholder.

**Allowed scope:** renderers; payload schemas; platform constraint tables; warnings;
fixtures; tests. Dry-run only.

**Forbidden scope:** real platform API dispatch; network; credentials; live eligibility
flips to true.

**Acceptance:** each platform produces an exact payload preview reflecting character
limits, media requirements, disclosure fields, unsupported-feature flags, and warnings;
all `dry_run`; no network.

**Stop conditions:** stop if any renderer formulates a payload for actual dispatch or
requires a live destination identity.

---

## TASK_CONTENTOPS_0174AS_APPROVAL_LEDGER_AND_ONE_BUTTON_MOCK_DISPATCH_V0

**Objective:** Implement the one-button concept safely in mock mode: signed operator
approval record, immutable packet hash, revocation, kill-switch gate, mock dispatch
controller, redacted audit record.

**Allowed scope:** approval ledger module; packet hashing; revocation; kill-switch gate;
mock dispatch controller; redacted audit writer; tests. Button state
`Approve & Mock Dispatch` only.

**Forbidden scope:** real platform API; live dispatch; credential reads; network;
scheduler.

**Acceptance:** missing approval blocks; changed payload hash blocks; active kill switch
blocks; unsafe content blocks; all actions are audit-logged with redaction;
mock-only dispatch succeeds and records a synthetic result.

**Stop conditions:** stop if dispatch attempts a real network request or reads a real
credential.

---

## TASK_CONTENTOPS_0174AT_CREDENTIAL_ENVELOPE_AND_REDACTED_PRESENCE_GATES_V0

**Objective:** Prepare real credentials without exposing secrets: credential slot
registry, redacted presence check, fake-token redaction tests, operator setup guide.

**Allowed scope:** slot registry; redacted presence checks; fake-token tests; redaction
validators; env var name conventions; operator local setup guide docs; tests.

**Forbidden scope:** reading real `.env` or operator secrets; printing/committing
secrets; sending credentials to ChatGPT; storing raw responses with tokens.

**Acceptance:** secret scans pass; no real token printed; platform readiness can
distinguish absent / present / validated without exposing values; fake-token tests pass.

**Stop conditions:** stop if any step parses a real `.env` against operator state or
emits a secret value.

---

## TASK_CONTENTOPS_0174AU_TELEGRAM_SUPERVISED_LIVE_PILOT_DESIGN_GATE_V0

**Objective:** Design (plan only) the first real one-platform supervised live dispatch
for Telegram channel. No token, no API call in this task.

**Allowed scope:** design docs; GO/NO-GO packet; blocker matrix; rollback/manual
fallback plan; readiness checklist.

**Forbidden scope:** real Telegram API call; token reads; live posting; scheduler; DMs;
replies; any other platform.

**Acceptance:** a complete supervised-live design exists with preconditions, kill-switch
requirement, redacted audit requirement, one-post-at-a-time scope, and documented
rollback; remains NO-GO until an explicit future operator GO.

**Stop conditions:** stop if the task is asked to call the Telegram API, read a real
token, or post.

---

## Later — Platform-by-platform GO/NO-GO and feedback

- **Phase 7 — Multi-platform supervised dispatch:** LinkedIn → X → Threads → Substack
  (export/API if safe) → Facebook Page / Instagram → TikTok last. Each platform requires
  a separate GO/NO-GO task with its own objective, allowed/forbidden scope, acceptance,
  and stop conditions. No platform starts live.
- **Phase 8 — Metrics sync and performance review:** URL capture; read-only metrics
  import/API where safe; manual metrics fallback; per-platform performance reports;
  content quality scoring; topic/hook/audience attribution. No scraping.
- **Phase 9 — Content-to-product feedback loop:** topic demand map; best-performing
  wedge analysis; subscriber funnel; product roadmap signal extraction; monetization
  readiness.

---

## Forward sequence at a glance

| Order | Task | Type | Live? |
|---|---|---|---|
| 0 | 0174AO reconcile master plan | docs-only | no |
| 1 | 0174AP domain model unification | schemas/tests | no |
| 2 | 0174AQ bounded LLM editorial contract | contract/tests | no |
| 3 | 0174AR platform payload compiler | dry-run | no |
| 4 | 0174AS approval ledger + mock dispatch | mock | no |
| 5 | 0174AT credential envelope + presence gates | fake-token | no |
| 6 | 0174AU Telegram supervised live pilot design | plan-only | no |
| 7+ | multi-platform GO/NO-GO, metrics, feedback | gated | per-gate only |

**Exact next recommended task:**
`TASK_CONTENTOPS_0174AP_DOMAIN_MODEL_UNIFICATION_FOR_SUPERVISED_CONTENT_DISTRIBUTION_OS_V0`
