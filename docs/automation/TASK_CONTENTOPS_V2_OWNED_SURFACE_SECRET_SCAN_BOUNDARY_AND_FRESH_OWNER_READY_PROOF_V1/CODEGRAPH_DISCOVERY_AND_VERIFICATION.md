# CodeGraph discovery and verification

Task: `TASK_CONTENTOPS_V2_OWNED_SURFACE_SECRET_SCAN_BOUNDARY_AND_FRESH_OWNER_READY_PROOF_V1`

Starting authority HEAD: `72bbc2dcdf11321cdcbf79cd5d546e8ed64e0b0e`.

## Before implementation

The writable task worktree initialized a local CodeGraph index at the exact starting HEAD over
2,037 files with 48,103 nodes and 124,097 edges.

Active graph queries established:

- `_secret_scan()` had one caller, `DesktopSessionV2Factory._execute_stage()`, with active calls at
  both `PACKAGE_QA_PASSED` and `OWNER_REVIEW_READY`;
- the scanner used `paths["root"].rglob("*")`, so its trust boundary was the whole job tree rather
  than an owned-artifact contract;
- `_paths()` places Capital Chronicle-authored/governed text under `artifacts/`,
  `desktop_session_inbox/`, `generated_project/src/`, `package/`, and `review/`;
- `prepare_project()` calls `_ensure_junction()` to project the external canonical dependency root
  into `generated_project/node_modules`;
- `node_modules`, browser/Remotion caches, media, audio, and other binary outputs are not owned text
  surfaces; their identity and integrity are governed by separate dependency, hash, and media QA;
- the focused impact radius is `video/unattended_core_factory_v1/supervisor.py` and
  `tests/test_v2_unattended_core_factory_v1.py`;
- that test module already covers dependency-root preflight, narration timing before motion,
  locked narration reuse, timing-bound captions, HIGH-parent/bounded-XHIGH provenance, forbidden
  creative substitution, zero-write safety, package QA, and deterministic `OWNER_REVIEW_READY`;
- no second active scanner implementation or safer V2 owned-surface scanner existed to reuse.

## After implementation

CodeGraph synchronized the two changed indexed Python files and 139 modified nodes. The current
index contains 2,037 files, 48,118 nodes, and 124,158 edges.

Active verification established:

- `_secret_scan()` remains the singular canonical V2 scanner; its only production caller remains
  `_execute_stage()`, and source inspection confirms calls at both `PACKAGE_QA_PASSED` and
  `OWNER_REVIEW_READY`;
- both calls now pass the complete path contract rather than `paths["root"]`;
- `_owned_text_surfaces()` declares exactly five roots: `artifacts`, `desktop_session_inbox`,
  `generated_project_src`, `package`, and `review`;
- no `rglob()` or whole-job recursive scanner remains in the canonical supervisor;
- the scanner resolves every owned root/file against the job root, fails closed on missing or
  unreadable owned roots, and rejects symlink/junction traversal before reading a target;
- `generated_project/node_modules`, external dependency/vendor trees, Remotion/browser caches,
  media, and audio are unreachable from the declared text roots;
- tests call the real scanner for all five owned surfaces, the Zod-shaped vendor regression, and
  external projection containment; the deterministic E2E records two successful scans through the
  real package and owner-ready stages;
- no parallel scanner, orphan scanner, filename exception, vendor allowlist, or relaxed pattern
  path was added;
- the dependency preflight still flows through `FactoryConfig.validate()` before job claim;
- `validate_narration_timing_lock()` remains active in motion submission and stage execution, while
  the same immutable timing lock continues into audio and captions;
- bounded creative receipts remain produced only by the four Desktop-session submission methods;
  HIGH parent / bounded-XHIGH provenance and zero CLI/SDK/API/9Router creative substitution remain
  covered by the unchanged canonical E2E and negative-path tests.

Mechanical validation before the real proof:

- focused scanner regressions: five owned-surface hard failures, vendor false-positive exclusion,
  and external junction/symlink containment all pass without printing marker contents;
- full V2 factory suite: `33 passed, 1 skipped`;
- deterministic E2E reaches `OWNER_REVIEW_READY`, preserves the timing lock and zero-write state,
  and executes the same owned-surface scan at both final stages.
- deterministic context-generator suite: `12 passed`; generated graph check:
  `CODEGRAPH_CURRENT` at starting authority HEAD `72bbc2dc...` plus the implementation tree digest.
