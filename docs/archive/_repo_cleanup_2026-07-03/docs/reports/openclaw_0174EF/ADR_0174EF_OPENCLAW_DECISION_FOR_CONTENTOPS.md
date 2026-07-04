# ADR 0174EF: OpenClaw Decision for ContentOps

Task: TASK_CONTENTOPS_0174EF_OPENCLAW_FRAMEWORK_FIT_RESEARCH_AND_DECISION_PACK_V0
Date: 2026-06-16
Status: Accepted
Mode: Research + docs-only. No OpenClaw was installed, cloned, run, or added as a dependency. No source/test/CLI/UI/config/dependency/lockfile changes were made.

## Context

ContentOps is a deterministic, local-first, **supervised publishing cockpit**. Its safety thesis: no side-effecting write occurs without a fresh, payload-hash-bound operator GO, account-binding proof, redacted credential handling, one-request/no-auto-retry execution, and a redacted, immutable audit trail. Autonomous posting is forbidden; manual posting is the fallback; supervised automation is the build path. Structural invariants are enforced by `tests/test_security_scans.py` (denylist on network/provider/env imports) and fail-closed redaction scanners in the automation-core modules.

OpenClaw (`github.com/openclaw/openclaw`, `openclaw.ai`) is a self-hosted, autonomous, messaging-driven AI agent platform: a long-lived local **Gateway** owns chat-app connections, routes messages to an agentic LLM runtime, and executes **skills** (shell/files/browser/cron) packaged as markdown and installable from the **ClawHub** registry. State persists as filesystem agent memory (`SOUL.md`, `USER.md`, `memory/*`). Its documented trust model is a single trusted operator, explicitly **not** a boundary against untrusted input. Third-party security analysis documents prompt-injection→RCE, skill poisoning, persistent-memory poisoning, and unauthenticated gateway RCE.

The question for this task: **is OpenClaw useful for any part of ContentOps?**

## Decision

**`APPROVE_AS_REFERENCE_ARCHITECTURE_ONLY`**, with a secondary role of **`APPROVE_AS_SECURITY_ANTI_PATTERN_REFERENCE`**.

- OpenClaw is **rejected as a runtime dependency, sidecar, installed component, or executed skill/agent/gateway inside ContentOps.**
- OpenClaw is **accepted as study material** for three concepts only: (1) skill/capability *packaging/metadata* shape, (2) control-plane-as-single-source-of-truth, (3) messaging-channel adapter normalization.
- OpenClaw is **accepted as a catalogue of anti-patterns** to drive ContentOps' future security red-team harness (skill poisoning, memory poisoning, prompt-injection→RCE, gateway RCE).

## Rationale

OpenClaw's core operating model conflicts with nearly every ContentOps invariant:

| ContentOps invariant | OpenClaw behavior | Verdict |
|---|---|---|
| No autonomous posting | Agentic loop acts without per-action GO | Conflict |
| No broad tool/host access | Shell/files/browser/cron by default | Conflict |
| No plugin marketplace install | ClawHub / GitHub-link installable skills | Conflict |
| No persistent memory as authority | `SOUL.md`/`memory/*` read as standing instructions | Conflict |
| No publish-bypass command channel | Chat message can trigger execution | Conflict |
| Symbolic credential handle, no hydration | Real keys captured into config/workspace | Conflict |
| No network control plane / fail-closed | Exposable gateway, `none` auth mode exists | Conflict |
| Treat external input as untrusted | Explicitly not a boundary for untrusted input | Conflict |

The three borrowable ideas are *concepts*, re-expressible deterministically in ContentOps (capability manifest as JSON schema, single dispatch choke point, preflight-bound channel adapters) without importing any OpenClaw code or runtime.

## Consequences

- The existing automation-core roadmap (supervised dispatch, Telegram/X gated pilots) continues unchanged; no OpenClaw work is scheduled into the live path.
- A future, optional, fully-isolated lab may study OpenClaw packaging/control-plane/channel patterns, quarantined from ContentOps repo, credentials, accounts, filesystem, and network.
- OpenClaw's documented attacks become negative test cases for a future red-team harness.
- `tests/test_security_scans.py` remains the structural guarantee; any attempt to add OpenClaw-style network/env/autonomy capability would fail it by design.

## Alternatives Considered

- **Adopt OpenClaw as the automation runtime**: rejected — violates every invariant above; introduces RCE/poisoning surface.
- **Embed OpenClaw as a sidecar/gateway for messaging pilots**: rejected — messaging-command execution is a publish-bypass channel; AGPL components also create hosting-copyleft risk.
- **Install select ClawHub skills**: rejected — unvetted supply-chain surface with documented skill poisoning.
- **Ignore OpenClaw entirely**: rejected — its packaging/control-plane/channel concepts and its anti-patterns have genuine reference value.

## Compliance / Constraints Honored

- No install, clone, run, dependency, or runtime integration of OpenClaw.
- No source code, test, CLI, UI, config, dependency, or lockfile changes.
- No credential/env/secret store reads; no live/network/provider/platform calls from ContentOps runtime.
- Deliverables are docs-only and advisory; this ADR holds no runtime authority over the dispatch path.

## References

- [openclaw_framework_fit_assessment_0174EF.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/research/openclaw_framework_fit_assessment_0174EF.md)
- [openclaw_reference_patterns_for_contentops_0174EF.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/architecture/openclaw_reference_patterns_for_contentops_0174EF.md)
- [openclaw_source_manifest_0174EF.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/research/openclaw_source_manifest_0174EF.md)
- [openclaw_followup_roadmap_after_0174EF.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/roadmaps/openclaw_followup_roadmap_after_0174EF.md)
- [ADR_0174EA_AUTOMATION_NOW_SUPERVISED_NOT_AUTONOMOUS.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/decisions/ADR_0174EA_AUTOMATION_NOW_SUPERVISED_NOT_AUTONOMOUS.md)
