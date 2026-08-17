# CodeGraph discovery and verification

Task: `TASK_CONTENTOPS_V2_DEPENDENCY_ROOT_PREFLIGHT_GUARD_AND_FRESH_OWNER_REVIEW_MEDIA_PROOF_V1`

Starting authority HEAD: `84017001dbc9fd5ec81908ab771711834d9b7ab7`.

## Before implementation

The deterministic context was stale at the freshly verified authority HEAD, so it was regenerated
before source inspection. The writable worktree then initialized a local CodeGraph index over 2,037
files with 48,096 nodes and 124,058 edges.

Active graph queries established:

- `scripts/run_v2_unattended_core_factory_v1.py::_factory` is the singular canonical CLI
  construction path for `FactoryConfig` and `DesktopSessionV2Factory`;
- `DesktopSessionV2Factory.__init__` calls `FactoryConfig.validate()` before `run_once()` can call
  `V2JobStore.claim_next()`, making the existing validator the pre-claim insertion point;
- the old `FactoryConfig.validate()` proved only path existence, implementation identity, worker
  identity, and HIGH-parent provenance;
- `prepare_project()` projects the configured dependency root to generated
  `<project>/node_modules` through a junction;
- `typecheck_project()` requires `<dependency-root>/.bin/tsc.cmd` on Windows and
  `render_project()` requires `<dependency-root>/.bin/remotion.cmd`;
- `resolve_remotion_browser_executable()` is the accepted singular browser resolver. It proves
  canonical identity, rejects zero/multiple executable matches, blocks path escape, and enforces the
  259-character Windows executable-path ceiling;
- `scripts/run_v2_remotion_short_path_smoke_v1.py` already exercises project projection, the
  canonical browser, the Remotion CLI, and a real non-creative render;
- focused coverage belongs in `tests/test_v2_unattended_core_factory_v1.py`, which already covers
  the canonical config/factory, job claim, Windows browser resolution, narration timing before
  motion, locked-narration audio reuse, locked-placement captions, HIGH/XHIGH provenance,
  forbidden creative seams, and deterministic `OWNER_REVIEW_READY` E2E;
- no existing generic preflight subsystem was a better fit. Reusing `FactoryConfig.validate()`,
  the media resolver, and the smoke runner keeps configuration and media execution singular.

## After implementation

CodeGraph synchronized six changed indexed files and 277 modified nodes. Active verification found:

- the canonical CLI still constructs one `FactoryConfig` through `_factory`, and every factory
  command constructs `DesktopSessionV2Factory` before dispatch;
- `FactoryConfig.validate()` now calls the narrowly named media
  `validate_dependency_root()`, wraps its fail-closed error, and stores the successful receipt on
  the factory before `run_once()` can call `claim_next()`;
- `validate_dependency_root()` requires the exact directory to be named `node_modules`, rejects a
  project root with an actionable `use_node_modules` error, resolves both `.bin/remotion.cmd` and
  `.bin/tsc.cmd` on Windows, then reuses the accepted canonical browser resolver;
- the smoke runner calls the same preflight before it materializes source or prepares a project;
- no second config-validation framework, alternate proof runner, or parallel media resolver was
  introduced;
- the accepted narration architecture is unchanged: `synthesize_narration` has one supervisor
  caller in `ACTUAL_NARRATION_TIMING_LOCKED`, `build_audio_mix` has one caller and receives the
  immutable timing lock, and `build_captions` has one caller and receives its locked placements;
- the focused deterministic E2E still proves timing lock before motion, one synthesis, locked audio
  reuse, locked caption placements, HIGH parent / bounded-XHIGH provenance, and zero creative
  CLI/SDK/API/provider substitution;
- `CodexCliExecutor` and routed/9Router creative seams remain confined to their negative tests and
  historical modules, with no canonical runner/supervisor import or call path.

Mechanical evidence before the real proof:

- invalid project root: deterministic preflight failure before claim, run row, proof epoch, stage
  event, or XHIGH opportunity;
- correct real `node_modules`: preflight PASS with Remotion CLI, TypeScript CLI, and unique
  canonical browser at a 222-character Windows path;
- non-creative Remotion smoke: PASS, one 320x568/30fps/30-frame H.264 render, canonical browser
  launched at 222 characters, projected same-file path at 126 characters, and zero creative proof
  consumption;
- focused factory suite: `24 passed, 1 skipped`.
