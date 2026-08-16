# Validation

- `python -m pytest -q tests/test_codex_context_index.py tests/test_v2_freeform_chapter_pipeline_v1.py`: `25 passed`.
- Pytest emitted a post-exit Windows `pytest-current` symlink-cleanup `PermissionError`; the test process returned zero and no test failed.
- `npx --no-install tsc --noEmit` from `video/projects/frozen_without_breaking_v1`: exit `0`.
- Pipeline hard-contract validation: `PASS_HARD_CONTRACT`, seven chapters, 25,451 frames, 848.367 seconds, no public-write authority, no V1 mutation authority, no 4K.
- Final owner-master full video+audio decode: exit `0`.
- Final owner-master frame count: `25,451`.
- Assembled and muxed demuxed-video hashes match exactly.
- CodeGraph generation: `6,827` nodes, `12,819` edges, `17` authority documents; ignored runtime/vendor node leak check clean.
- CodeGraph deterministic check: `CODEGRAPH_CURRENT`.
- `git diff --check`: no whitespace errors; line-ending conversion notices only.
- Final XHIGH whole-film visual critic: no material picture repair justified; human audio playback remains required before publication.
