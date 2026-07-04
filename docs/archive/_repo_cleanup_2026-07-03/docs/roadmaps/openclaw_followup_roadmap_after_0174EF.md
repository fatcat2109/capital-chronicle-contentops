# OpenClaw Follow-up Roadmap (after 0174EF)

Task: TASK_CONTENTOPS_0174EF_OPENCLAW_FRAMEWORK_FIT_RESEARCH_AND_DECISION_PACK_V0
Date: 2026-06-16
Mode: Research + docs-only. Advisory roadmap. No OpenClaw install/clone/run/dependency. Nothing here schedules OpenClaw into the live ContentOps path.

> [!IMPORTANT]
> The accepted decision is `APPROVE_AS_REFERENCE_ARCHITECTURE_ONLY` (see [ADR_0174EF](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/decisions/ADR_0174EF_OPENCLAW_DECISION_FOR_CONTENTOPS.md)). Every item below is optional, reference-only, and must not touch ContentOps runtime, credentials, accounts, or the dispatch path. None of these are committed work; they are candidate follow-ups for the operator to prioritize.

## Guiding Constraints (apply to every item)

- No OpenClaw runtime, dependency, sidecar, or installed skill inside ContentOps.
- No change to the no-autonomy / supervised-publishing invariants.
- Any hands-on study happens only in a fully isolated lab (separate VM/container, no ContentOps repo/credentials/accounts/filesystem/network).
- Outputs flow back as written human summaries only; never as code, memory, or instructions fed to a model.
- `tests/test_security_scans.py` remains the structural guarantee; nothing here may weaken it.

## Near-Term (reference / docs only)

1. **Capability-manifest concept spike (docs only).** Sketch how a ContentOps "capability" could be described by a JSON-schema manifest (inputs/outputs/allowlists) inspired by OpenClaw's `SKILL.md` *metadata* shape — implemented, if ever, as reviewed deterministic Python, never a hot-loaded skill. Deliverable: a short design note; no code.
2. **Red-team negative-case catalogue.** Translate OpenClaw's documented attacks (prompt-injection→RCE, skill poisoning, memory poisoning, gateway RCE) into a written list of negative test cases ContentOps' future red-team harness should cover. Deliverable: a checklist doc.
3. **Control-plane choke-point review.** Compare OpenClaw's gateway-as-single-source-of-truth with ContentOps' dispatch gate chain; confirm ContentOps keeps exactly one auditable path to any side effect. Deliverable: an architecture note, no code.

## Mid-Term (optional, isolated lab)

4. **Isolated packaging study.** In a quarantined lab only, observe how OpenClaw packages skills, shapes its gateway, and normalizes channels — as a taxonomy exercise, not an integration spike. Deliverable: written comparison; nothing imported.
5. **Channel-adapter pattern validation.** Use lab observations to sanity-check ContentOps' per-platform preflight + canonical-post + capability-registry direction. Deliverable: notes feeding the existing automation-core roadmap.

## Explicitly Out of Scope (not planned)

- Installing, cloning, running, or depending on OpenClaw anywhere near ContentOps.
- Adopting ClawHub or any third-party skill install path.
- Any messaging-command channel that can authorize or trigger a live write.
- Persisting agent memory (`SOUL.md`/`memory/*`) as behavioral authority.
- Capturing real platform/provider credentials into any config/workspace.
- Standing up a network-listening control plane for ContentOps.

## Preconditions Before Any Status Change

If OpenClaw (or an OpenClaw-like pattern) is ever reconsidered for anything beyond reference, each safety wrapper in [openclaw_reference_patterns_for_contentops_0174EF.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/architecture/openclaw_reference_patterns_for_contentops_0174EF.md) ("Required Safety Wrappers If Ever Revisited") must be implemented and tested first, each as its own gated task with operator GO. Until then, OpenClaw stays reference-only.

## References

- [ADR_0174EF_OPENCLAW_DECISION_FOR_CONTENTOPS.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/decisions/ADR_0174EF_OPENCLAW_DECISION_FOR_CONTENTOPS.md)
- [openclaw_framework_fit_assessment_0174EF.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/research/openclaw_framework_fit_assessment_0174EF.md)
- [openclaw_reference_patterns_for_contentops_0174EF.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/architecture/openclaw_reference_patterns_for_contentops_0174EF.md)
- [openclaw_source_manifest_0174EF.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/research/openclaw_source_manifest_0174EF.md)
- [social_automation_execution_roadmap_after_0174EA.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/roadmaps/social_automation_execution_roadmap_after_0174EA.md)
