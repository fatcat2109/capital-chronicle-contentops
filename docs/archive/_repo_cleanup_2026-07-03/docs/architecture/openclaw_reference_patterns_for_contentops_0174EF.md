# OpenClaw Reference Patterns for ContentOps (0174EF)

Task: TASK_CONTENTOPS_0174EF_OPENCLAW_FRAMEWORK_FIT_RESEARCH_AND_DECISION_PACK_V0
Mode: Research + docs-only. Reference architecture for study only. No OpenClaw code, dependency, install, or runtime is introduced. No source/test/CLI/UI change is made.

> [!IMPORTANT]
> Nothing here authorizes adopting OpenClaw at runtime. These are study notes: which OpenClaw ideas are worth borrowing as *concepts*, which to reject, and the safety wrappers that would be mandatory if the topic is ever revisited. The companion decision is `APPROVE_AS_REFERENCE_ARCHITECTURE_ONLY` — see [ADR_0174EF](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/decisions/ADR_0174EF_OPENCLAW_DECISION_FOR_CONTENTOPS.md).

## Useful Reference Patterns

1. **Control-plane as single source of truth.** OpenClaw's Gateway owns all external connections and routing. ContentOps already has the analogous idea in its dispatch gate chain; the lesson is to keep one auditable choke point for every side-effecting action rather than scattering send logic across adapters.
2. **Channel adapter normalization.** OpenClaw normalizes many messaging platforms into one internal message shape. ContentOps' per-platform preflight + canonical-post contracts (`scd_canonical_social_post`, platform capability registry) are the deterministic equivalent; the pattern validates the adapter-abstraction direction.
3. **Skills-as-markdown packaging (concept only).** A skill = a directory + a declarative `SKILL.md` (metadata + instructions + allowlists). The *packaging/metadata* idea (declare capabilities, allowlists, and intent up front) is a clean way to describe a unit of capability. ContentOps can borrow the *descriptive* shape (a manifest per capability) without borrowing the *executable/installable* part.
4. **Explicit auth modes + a security-audit command.** OpenClaw ships `openclaw security audit` and named auth modes. ContentOps' analogue is `tests/test_security_scans.py` plus the redaction scanners; the lesson is to keep a first-class, runnable "footgun" check as the codebase grows.

## Patterns to Avoid

1. **Autonomous agent loop.** An LLM loop that decides and acts without a per-action human GO. ContentOps forbids autonomous posting and unsupervised schedulers.
2. **Direct LLM-to-host tool execution.** Shell/files/browser/cron driven by reasoning. ContentOps stays stdlib-only, no-network, no-env-read except in a tiny audited live-gate allowlist.
3. **Installable third-party skills / registry install path (ClawHub).** A supply-chain surface with documented skill-poisoning. ContentOps permits no plugin marketplace install path.
4. **Persistent agent memory as authority.** `SOUL.md`/`memory/*` read as standing instructions invites memory poisoning and hidden state mutation. ContentOps audit logs are redacted, immutable, and never executable authority.
5. **Messaging command channel that can act.** A chat message triggering execution is a publish-bypass channel. ContentOps must never let a message bypass operator approval.
6. **Credentials captured into config/workspace.** ContentOps uses a symbolic credential handle with no live hydration; real-key-in-config is a regression.
7. **Exposable gateway with a `none` auth mode.** Documented unauthenticated-RCE risk. ContentOps has no network-listening control plane.

## Possible Translation Into ContentOps Architecture

If any concept is borrowed, it must be re-expressed in ContentOps terms, deterministically:

- **Capability manifest, not executable skill.** A ContentOps "capability" could be described by a JSON-schema-backed manifest (like existing `schemas/*.json`) declaring inputs/outputs/allowlists — but it is implemented as a reviewed, deterministic Python module, never a hot-loaded markdown skill.
- **Control choke point, not daemon.** Keep the single dispatch gate as the only path to a side effect, exercised via CLI under operator GO — never a long-lived network listener.
- **Channel adapters stay preflight-bound.** Each adapter keeps platform-specific preflight + account binding + payload hash + budget 1 + no auto-retry + redacted audit. Normalization is fine; send-on-message autonomy is not.
- **Audit, not memory.** Persisted state is redacted audit evidence consumed by humans, never instructions fed back to a model as authority.

## How OpenClaw-Style Skills Differ From ContentOps Deterministic Modules

| Dimension | OpenClaw skill | ContentOps module |
|---|---|---|
| Form | Markdown (`SKILL.md`) + instructions, hot-loaded | Reviewed Python in `live_contentops/`, imported |
| Source | Local + community (ClawHub / GitHub link) | Repo-only, code-reviewed, GitHub-audited |
| Authority | LLM interprets instructions at runtime | Deterministic code; LLM never executes via it |
| Capability | Shell/files/browser by default | Stdlib-only; no network/env by default |
| Trust | Install-time trust in third party | Commit-time trust via review + tests |
| Safety check | Optional audit command | Enforced `test_security_scans.py` + redaction scanners + fail-closed validators |

The core difference: OpenClaw skills are *runtime-interpreted, installable instructions*; ContentOps modules are *compile/commit-time-reviewed deterministic code* with hard fail-closed invariants.

## Why OpenClaw Messaging UX Must Not Become a Publish-Bypass Command Channel

ContentOps' entire safety model assumes a single, auditable approval path: draft → guardrail scan → operator GO bound to a payload hash → account binding → preflight → one request → redacted audit. A messaging command channel that can trigger a send would:

- bypass the payload-hash-bound GO (approval no longer maps to exact content),
- bypass account-binding proof (wrong-account fail-closed defeated),
- bypass the request budget and no-auto-retry rule,
- create an injection path (a crafted inbound message becomes a command),
- and leave no redacted, immutable audit of *why* the send happened.

Therefore a chat/messaging interface in ContentOps may, at most, *notify* or *queue a draft for human review*; it must never itself be sufficient to cause a live write. Telegram/Discord pilots remain destinations of supervised dispatch, not command inputs that authorize dispatch.

## How a Future Isolated Lab Could Test OpenClaw-Like Skills Without Touching Live ContentOps Runtime

If the team ever wants hands-on study, it must be fully quarantined from ContentOps:

- A separate machine/VM/container with no ContentOps repo, no ContentOps credentials, no production accounts.
- No shared filesystem, env, keyring, or network path to ContentOps.
- Throwaway accounts and dummy data only; no real platform credentials.
- Treat all outputs as untrusted; nothing flows back into ContentOps except a written human summary.
- The lab is a *comparison/taxonomy exercise* (how OpenClaw packages skills, shapes its gateway, abstracts channels) — never an integration spike.

## Required Safety Wrappers If Ever Revisited

Should OpenClaw (or an OpenClaw-like pattern) ever be reconsidered for anything closer than reference, ALL of the following are non-negotiable preconditions, each its own gated task:

- No autonomous action: every side effect requires a fresh, payload-hash-bound operator GO.
- No broad tool permissions: explicit per-capability allowlist, default-deny shell/files/browser/network.
- No third-party/installable skills: repo-reviewed deterministic modules only; no marketplace install path.
- No persistent memory as authority: state is redacted audit only, never fed back as instructions.
- No messaging-command execution: chat may notify/queue, never authorize a write.
- No raw credential capture: symbolic handle + operator-owned, short-lived, zero-logged hydration only.
- No network-listening control plane by default; if ever present, strong auth, loopback binding, no `none` mode, and a kill switch.
- Mandatory red-team coverage for prompt-injection→RCE, skill poisoning, and memory poisoning before any adoption.

Until every wrapper exists and is tested, OpenClaw stays reference-only.

