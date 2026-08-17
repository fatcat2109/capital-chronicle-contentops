# CodeGraph discovery and verification

Task: `TASK_CONTENTOPS_V2_ACTUAL_NARRATION_TIMING_LOCK_AND_FRESH_OWNER_REVIEW_MEDIA_PROOF_V1`

Starting authority HEAD: `e5ddbdedc1649f15c1eefd3cd7f72891835e29d2`.

## Before implementation

The committed context generator was regenerated and returned `CODEGRAPH_CURRENT`. The writable
worktree did not initially contain `.codegraph/`; the owner-authorized mandatory discovery gate
therefore initialized a local index (`2,037` files, `48,079` nodes, `123,886` edges) and queried
the active pipeline before edits.

The graph showed:

- `DesktopSessionV2Factory.submit_initial_creative` and `CREATIVE_EDITOR_LOCKED` validated editor
  and motion together;
- `validate_editor_artifact` treated a word-count estimate and editor-authored duration as the
  motion timing contract;
- `MOTION_SOURCE_LOCKED` preceded real waveform generation;
- the sole active `synthesize_narration` call was in `AUDIO_BUILT`, after `PICTURE_LOCKED`;
- `build_audio_mix` immediately followed that late synthesis and correctly rejected narration
  longer than picture;
- `build_captions` later used placements from the same late receipt but used the editor duration as
  media duration;
- `video/native_multiformat_multilingual_package_factory_v1/localized_audio_builder_v1.py`
  contained the reusable pattern: voice/text-bound segment cache identities, exact generated
  waveform duration, stable segment placement, and captions derived from measured placements;
- the canonical caller/test surface was `scripts/run_v2_unattended_core_factory_v1.py`,
  `video/unattended_core_factory_v1/{creative,desktop_session,media,supervisor}.py`, and
  `tests/test_v2_unattended_core_factory_v1.py`, with shared caption coverage in
  `tests/test_v2_multiformat_multilingual_package_factory_v1.py`.

## After implementation

CodeGraph was synced after the implementation (`6` changed indexed files, `228` modified nodes),
and the deterministic repository graph was regenerated (`7,178` nodes, `13,480` edges) with
`CODEGRAPH_CURRENT`.

Active-call verification:

- callers of `synthesize_narration`: exactly one, `DesktopSessionV2Factory._execute_stage`;
- callers of `build_audio_mix`: exactly one, the same canonical stage executor;
- callers of `build_captions`: exactly one, the same canonical stage executor;
- the single synthesis call is inside `ACTUAL_NARRATION_TIMING_LOCKED`, before the separate
  `MOTION_VISUAL_AUTHORSHIP` submission can be accepted;
- `submit_motion_visual` and `MOTION_SOURCE_LOCKED` both validate the editorial hash, immutable
  timing-lock hash, segment text/audio hashes, exact placements, waveform-derived frame duration,
  and source `durationInFrames`/30 fps lock;
- `PICTURE_LOCKED` probes the actual render and rejects a picture ending before the locked
  narration;
- `AUDIO_BUILT` has no synthesis call and passes the already locked narration artifact to
  `build_audio_mix`;
- captions consume the same timing-lock segment placements, and the package carries the same
  segment IDs/text hashes/timings for later transcript/SEO derivation;
- no direct editor-to-motion or editor-to-picture bypass remains in `STAGES` or the runner;
- `CodexCliExecutor` is confined to the fail-closed historical module and its negative test;
  `routed_v2_creative_invocation` is confined to the generic seam and its negative test; neither is
  imported or reachable from the canonical runner, Desktop-session contract, or supervisor.

Focused verification: `21 passed, 1 skipped` in the V2 unattended factory file, plus the two shared
caption timing/guard tests and the explicit deterministic `OWNER_REVIEW_READY` E2E (`3 passed`).
CodeGraph's conservative `affected` command reported no inferred tests because the media backend is
dependency-injected; the explicit graph-routed tests above cover the seams through `FakeMedia`.
