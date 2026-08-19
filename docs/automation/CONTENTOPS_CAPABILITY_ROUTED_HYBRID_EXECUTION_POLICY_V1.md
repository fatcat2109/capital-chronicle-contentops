# Capital Chronicle ContentOps — Capability-Routed Hybrid Execution Policy V1

Authority date: 2026-08-19
Status: `CURRENT_EXECUTION_POLICY`

This policy changes only **how engineering work is executed**. It does not change the ContentOps product sequence, Capital Chronicle/Core Analyzer authority, V1/V2 boundaries, public-write authority, numeric authority, rights rules, KILL_SWITCH behavior, destination identity, readback/reconciliation, or protected release history.

Jim explicitly authorized this method on 2026-08-19. It is now current execution-routing authority under root `AGENTS.md` and the current authority/supersession map. Older `MAIN_CODEX only` execution statements remain superseded for execution routing only where the current authority map says so.

## 1. Execution model

The execution model is `CAPABILITY_ROUTED_HYBRID` with four classes.

### `WEB_STATIC`

Use standard ChatGPT Web + the connected GitHub App for repository-static work whose correctness can be established from fresh GitHub bytes and static reasoning without a development runtime.

Typical scope:

- fresh ref/authority verification;
- repo archaeology, code search, call-site discovery, diff/PR review;
- documentation and authority maintenance when owner-authorized;
- bounded source/config/schema edits that do not require runtime truth;
- branch/file/commit/PR/review operations through GitHub;
- CI result/log/artifact interpretation where the connector exposes the required evidence.

`WEB_STATIC` may claim only what GitHub/static evidence proves. It may not claim tests pass, runtime behavior, browser behavior, external-state correctness, deployment health, visual quality, or public-write success without separate evidence.

### `WEB_CI`

Use ChatGPT Web + GitHub for bounded implementation and GitHub Actions for deterministic machine validation when the target repository has an appropriate safe workflow.

Eligible deterministic work may include:

- lint/format checks;
- type checks;
- unit/focused integration tests;
- builds;
- schema/contract validation;
- deterministic code generation and smoke tests;
- machine-readable validation artifacts.

A GitHub commit is not execution evidence. `WEB_CI` may claim CI PASS only from the exact workflow run bound to the exact commit or PR merge ref under review.

Normal Web/CI validation must remain `NO_SECRET / NO_PUBLIC_WRITE / NO_PRODUCTION_MUTATION` unless a separate exact owner-gated workflow explicitly grants otherwise. Agent-modified code must not automatically receive powerful production credentials.

### `CODEX_EXECUTION`

Use Codex when correctness materially requires an interactive execution environment or repeated observe-debug-edit-run feedback.

Typical scope:

- local/repository shell and environment setup;
- dependency/package migration diagnosis;
- runtime reproduction;
- services, Docker, databases, stateful integration;
- current network/source behavior when deterministic CI is insufficient;
- browser/DOM/runtime inspection;
- complex multi-round failing-test diagnosis;
- performance profiling;
- real rendered UI/video/audio mechanics where execution is required;
- long autonomous debugging where runtime interpretation is the work.

Codex is the execution-feedback lane, not the default repository reader, transport, editor, or deterministic test runner.

### `OWNER_GATED_EXTERNAL`

Require explicit owner scope for:

- secrets/credentials/session material boundaries;
- live/public writes and exact destination/account identity;
- destructive canonical or production-store changes;
- provider/browser publication expansion;
- legal/rights release boundaries;
- material Capital Chronicle/Core Analyzer numeric-authority changes;
- broker/live execution or equivalent irreversible external actions.

Changing execution lane never widens these permissions.

## 2. Routing rule

Before implementation, classify the task by the strongest evidence needed for its correctness claim:

1. Can fresh GitHub bytes/static reasoning establish correctness? -> `WEB_STATIC`.
2. Can static reasoning plus deterministic safe CI establish correctness? -> `WEB_CI`.
3. Does correctness require an interactive runtime/environment/browser/debug loop? -> `CODEX_EXECUTION`.
4. Does the work cross secrets/live/public/destructive/numeric-authority/rights boundaries? -> `OWNER_GATED_EXTERNAL` for that boundary.

Use the cheapest lane that can produce evidence strong enough for the actual claim. Route by information deficit, not quota pressure or habit.

## 3. No automatic capability downgrade

If a task requires `CODEX_EXECUTION` and Codex is unavailable, Web must not substitute static reasoning for missing runtime evidence. The task remains blocked or waits for an execution-capable lane.

Likewise, CI PASS never substitutes for:

- external runtime truth;
- current public-write/readback truth;
- visual/audio quality acceptance;
- Capital Chronicle/Core Analyzer deterministic numeric authority;
- production browser/account identity;
- real canary or unattended/cold-start acceptance.

Quota optimization is subordinate to truth.

## 4. Web/GitHub mutation discipline

Default Web implementation policy:

`fresh master -> dedicated agent/web-* branch -> scoped edits -> deterministic validation when available -> draft PR -> owner/reviewer decision`

Rules:

- no direct `master` mutation from the Web lane;
- no force push;
- no silent unrelated changes;
- no merge without explicit owner authorization;
- exact base SHA, changed paths, commit SHA, CI/runtime scope and caveats must remain observable;
- broad changes requiring working-tree atomicity or runtime iteration move to Codex rather than abusing low-level Git primitives merely because they exist.

## 5. Repair and escalation

The default Web/CI repair budget is bounded. Two Web repair rounds are a heuristic, not a hard invariant.

Escalate earlier when the first failure shows an execution/environment information deficit. Continue a bounded Web repair when the failure is mechanically clear from deterministic evidence. Never create an unbounded speculative commit loop.

## 6. GitHub Actions boundary

GitHub Actions is deterministic compute, not an authority engine and not an autonomous publication lane.

Preferred safe workflow classes:

- `CI_FAST`: focused lint/typecheck/tests/schema checks;
- `CI_FULL`: broader deterministic tests/build when justified;
- `CI_ARTIFACT`: compact machine-readable summaries/logs/artifacts.

Workflows should prefer ordinary push/PR events already controllable through GitHub. Do not insert a paid model/API loop into every CI run merely to recreate Codex elsewhere.

Actions that use secrets or can mutate external systems require a separate owner-gated trust boundary and must not be triggered by arbitrary agent-authored code by default.

## 7. Product authority remains unchanged

This execution policy does not alter:

- the current product priority and exact lane sequencing in root V3 authority;
- Capital Chronicle/Core Analyzer ownership of proprietary analytical/numeric/decision truth;
- the three ContentOps CC authority classes;
- V1 canonical Substack-first plus eight derivative publication model;
- `UNKNOWN_WRITE: STOP RETRY -> READ BACK -> RECONCILE`;
- Chrome 9222 ingestion-only and Edge 9223 publication/media/readback boundaries;
- V2 isolation and zero video public-write authority;
- actual rendered artifact review for UI/video/audio acceptance;
- no-publication / zero images / zero video as valid outcomes;
- protected `v1.0` at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

Execution efficiency must never redefine evidence.

## 8. Pilot and measurement

Run this architecture prospectively on real eligible engineering tasks before treating efficiency claims as proven. Approximately 10 representative tasks is a useful target, not a quota that justifies invented work.

Track at minimum:

- execution lane;
- whether Codex was used or avoided;
- Web repair rounds;
- CI result/runtime where available;
- Web -> Codex escalation and reason;
- time to accepted change where observable;
- revert/escaped-defect signal;
- unsupported-PASS incidents;
- operator burden;
- Codex usage/credits where observable.

The pilot succeeds only if it reduces scarce Codex execution meaningfully without lowering evidence quality, safety, product correctness, or owner confidence.

## 9. Evidence contract

Every implementation should record enough evidence for its lane, including:

- repository and fresh base ref/SHA;
- branch and final commit(s);
- execution lane and why it was sufficient;
- authority files read;
- exact changed paths;
- write/network/browser/provider/publication scope;
- deterministic validation/CI evidence where applicable;
- runtime verification status;
- Codex escalation status;
- secret/external-write scope;
- hard-stop status;
- final classification and caveats.

Allowed task classifications remain `PASS`, `PASS_WITH_CAVEAT`, `BLOCKED`, and `FAIL` unless a lane-specific runtime contract defines a more precise truthful sub-classification.

## 10. North Star

**ChatGPT reasons and controls GitHub; GitHub Actions performs deterministic machine work; Codex is spent when the engineering problem requires a real execution environment and iterative runtime feedback; external/live authority remains explicitly owner-gated.**
