# ADR 0174EA: Automation Now, Supervised — Not Autonomous

Task: TASK_CONTENTOPS_0174EA_SOCIAL_AUTOMATION_RESEARCH_AND_ARCHITECTURE_CONTEXT_PACK_V0
Mode: Implementation Mode, docs-only.

## Status
Accepted for **roadmap direction**, not runtime implementation. This ADR introduces no live posting code, credential reads, OAuth execution, scheduler, browser automation, or network behavior.

## Context
Prior ContentOps work trended toward building manual-publishing UI as the core product. Manual posting is easy to build, which risks losing momentum on the genuinely hard problems: OAuth, token handling, account binding, queueing, idempotency, rate/spend limits, app review, paid APIs, and audit trails.

Benchmarking five open-source projects (Postiz, autopost-social-media, Free-AI-Social-Media-Scheduler, laravel-social-auto-post, owlstack-laravel) showed a common short path: `.env` token -> scheduler/queue -> API call -> log. None surfaced the ContentOps-grade safety set: redacted credential presence checks, operator-GO per live write, payload-hash approvals, one-request/no-auto-retry writes, redirect/final-host hardening, idempotency ledgers, spend/rate budgets, and redacted audit.

Official platform docs confirm "access exists" is not "safe to automate": X charges per write, LinkedIn/TikTok/YouTube gate behind scopes/review/audit, Discord enforces strict rate headers, Mastodon supports idempotency, Reddit requires exact redirect matching, and Meta-family/Substack readiness could not be verified from authenticated docs in the source research session.

The prior X live-read-only identity proof work (0174DE) exists on master but is **not accepted as product baseline** due to redirect/final-host hardening concerns. This ADR and context pack do **not** accept or continue the X live chain.

## Decision
ContentOps will **build automation now, as supervised automation, not autonomous posting**. Manual posting remains a fallback / emergency / manual-public path, not the core build target. Every side-effecting write requires a fresh, payload-hash-bound operator GO, an account binding proof, platform preflight, a single live request against an exact host allowlist, no automatic retry, and a redacted audit closure.

## Consequences
- The build focus shifts to the platform-agnostic automation core: account binding, credential handle + redaction boundary, approval ledger + payload hash, outbox + idempotency, rate/spend/retry policy, redacted dispatch audit, and a fake-provider CI harness.
- First live pilot targets Telegram (lower app-review and paid-risk burden), then Discord/Mastodon/Bluesky, then X/LinkedIn after spend/review/account gates, then TikTok/YouTube after audit readiness, then the Meta family after authenticated official-doc re-check.
- Manual fallback tooling is retained but de-prioritized as the strategic destination.
- A corrective task (0174DE_R1) is required before any X live chain proceeds.
- CI must never carry live secrets; posting paths are exercised only via fake providers.

## Rejected Alternatives
- **Pure manual-only product** — avoids the hard problems and caps the product's value; rejected.
- **Autonomous scheduler / bot** — unacceptable risk of unintended paid, duplicate, or policy-violating public posts; rejected.
- **Copy open-source `.env` + scheduler pattern directly** — weak secret hygiene, no operator GO, no redaction/audit boundary; rejected.
- **Third-party all-in-one API abstraction without an audit boundary** — moves the trust boundary off-system, harder to audit and reason about during failures; rejected.
- **X-first live posting before spend/redirect/account gates** — economically stateful writes without budget and redirect hardening; rejected.
- **Meta-family implementation before authenticated official-doc verification** — source docs were gated/429 and unresolved; rejected until re-verified.
