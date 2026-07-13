# Canonical Command and File Map

## 1. Repository identity and baseline commands

### Git verification commands used in Phase 1

```text
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git rev-parse @{upstream}
git rev-parse origin/master
git worktree list --porcelain
git status --short
git diff --stat
git diff --cached --name-only
git ls-files --others --exclude-standard
git tag --points-at HEAD
git diff --check
```

### Baseline results

- repo root: `A:/Capital Chronicle/tools/cc-live-contentops-editorial-qa`
- branch: `master`
- local/upstream/origin master all matched `821450d0f2b5a18051a1bc684bea2a4709a5ba01`
- dirty file: `exports/daily_contentops/fed_funds_policy_signal_article_v1.md`
- tags at HEAD: none

### Read-only upstream authority verification

```text
git -C "A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion" rev-parse HEAD
git -C "A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion" rev-parse origin/main
```

Both resolved to `c14e5a7f48d1d949da60c217c4467c2418f1fbf6`. The final database evidence packet reports a complete public/free v1 foundation and analyzer handoff, but its `dqr=BLOCKED` and other explicit limitations keep ContentOps live publication fail-closed. Canonical pause state: `FROZEN_WAITING_FOR_PUBLICATION_ELIGIBLE_UPSTREAM_EVIDENCE`.

## 2. Canonical generalized prepare-only command

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id <run_id> \
  --output-dir <output_dir> \
  --prepare-generic-fabric \
  --capital-chronicle-root <ingestion_repo> | --cc-evidence-packet <packet> \
  --generic-story-request <story_request.json> \
  --generic-as-of-utc <timestamp>
```

### Parser module

- `live_contentops/eight_platform_substack_first_pipeline_v1.py`

### Runner branch

- `main()` → `--prepare-generic-fabric`
- calls `live_contentops.generic_editorial_fabric_v2.run_generic_prepare_only`

### Required inputs

- `--run-id`
- `--output-dir`
- `--generic-story-request`
- exactly one of:
  - `--capital-chronicle-root`
  - `--cc-evidence-packet`
- optional `--generic-as-of-utc`

### Evidence source

- `live_contentops.cc_evidence_bridge_v2.build_evidence_packet_from_cc_root`
- or prebuilt packet path

### Gates

- story capability resolution
- freshness/market-state
- visual composition
- eight-role editorial review

### Produced files

- `capital_chronicle_content_evidence_packet_v2.json`
- `freshness_market_state_decision_v2.json`
- `visual_composition_decision_v2.json`
- `editorial_review_orchestrator_v2.json`
- `google_visual_discovery_request_rehearsal_v2.json`
- `generic_fabric_prepare_only_result_v2.json`

### Public write risk

- none by design
- `public_write_performed=false`
- browser/CDP/platform adapters not called

### Safe while paused?

- yes; this should remain available under a future lane lock

### Relevant tests

- `tests/test_generic_evidence_freshness_visual_editorial_fabric_v2.py`

### Common failure modes

- missing generic story request
- invalid evidence input mode
- stale DQR/freshness / publication ineligible
- visual diversity or methodology block
- editorial structured-review block

## 3. Canonical text/image release-candidate preparation command

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id <run_id> \
  --output-dir <output_dir> \
  --prepare-only \
  --allow-legacy-topic-adapter
```

### Purpose

Prepare and freeze a text/image RC packet without public writes.

### Parser module

- `live_contentops/eight_platform_substack_first_pipeline_v1.py`

### Runner branch

- `main()` → `prepare_text_image_release_candidate()`

### Produced files

- `native_payloads_rehearsal_v1.json`
- `release_candidate_lock_v1.json`
- `no_write_rehearsal_v1.json`
- plus staged article/media/context artifacts from prep pipeline

### Public write risk

- none when used as intended

### Safe while paused?

- yes, but still legacy-backed and not the canonical future generalized route

### Relevant tests

- `tests/test_eight_platform_substack_first_pipeline_v1.py`

### Common failure modes

- missing canonical Edge profile auth
- missing derivative credential capabilities
- non-unique media set
- payload length/layout failures
- duplicate hotspot block

## 4. Canonical public text/image live run command

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id <run_id> \
  --output-dir <output_dir> \
  --operator-approved-full-live-run \
  --allow-legacy-topic-adapter
```

### Parser module

- `live_contentops/eight_platform_substack_first_pipeline_v1.py`

### Runner branch

- `main()` → `run_eight_platform_substack_first_pipeline()`

### Required inputs

- authenticated canonical Edge profile
- prepared Substack request/context or ability to generate them
- valid delivery media manifest
- credentials / session readiness per destination

### Produced files

- `run_evidence_v1.json`
- `native_payloads_v1.json`
- `delivery_media_manifest_v1.json`
- `platform_dispatch_ledger_v1.jsonl`
- `final_platform_matrix_v1.json`
- `README.md`
- possibly `operator_manual_audit_packet_v1.json`

### Public write risk

- yes; this is the canonical live text/image dispatch path

### Safe while paused?

- **no**; this is the primary surface a Phase 2 lane lock must block

### Relevant tests

- `tests/test_eight_platform_substack_first_pipeline_v1.py`
- `tests/test_edge_cdp_publishing_adapter_v1.py`
- adapter-specific tests

### Common failure modes

- canonical Edge profile not attached
- release-candidate lock mismatch
- Substack publish/readback failure
- wrong destination identity
- public URL readback uncertainty
- malformed Threads/X continuation chain
- image-only or malformed LinkedIn result

## 5. Derivative resume command

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id <run_id> \
  --output-dir <output_dir> \
  --resume-derivatives \
  --resume-platform <platform> [--resume-platform <platform> ...]
```

### Purpose

Resume only failed derivatives while keeping canonical and successful destinations frozen.

### Safe while paused?

- **should be blocked by future lane lock**, except possibly for explicitly whitelisted read-only reconciliation submodes

### Hidden dispatch concerns

This command can still publish to:
- Telegram
- Discord
- X
- Threads
- LinkedIn
- Facebook Page
- Instagram Business
- YouTube Community

It is not enough to block only the default live run; a pause mechanism must also cover derivative resume.

### Relevant code

- `resume_eight_platform_derivatives()` in `live_contentops/eight_platform_substack_first_pipeline_v1.py`

## 6. Read-only reconciliation command

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id <run_id> \
  --output-dir <output_dir> \
  --reconcile-readbacks
```

### Purpose

Resolve derivative state through read-only provider reconciliation.

### Public write risk

- intended none

### Safe while paused?

- yes, and Phase 2 should preserve this

### Relevant code

- `reconcile_existing_derivative_readbacks()`

## 7. LinkedIn pair reconciliation command

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id <run_id> \
  --output-dir <output_dir> \
  --reconcile-linkedin-pair \
  --linkedin-accepted-url <url> \
  --linkedin-accepted-id <id> \
  --linkedin-latest-url <url> \
  --linkedin-latest-id <id>
```

### Public write risk

- yes, can edit latest malformed activity in place

### Safe while paused?

- no, unless the future lock explicitly authorizes repair-only exceptions

## 8. Operator audit packet builder

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id <run_id> \
  --output-dir <output_dir> \
  --build-operator-audit-packet
```

### Public write risk

- no; reads public pages and writes local audit artifacts

### Safe while paused?

- yes

### Produced files

- `operator_manual_audit_packet_v1.json`
- screenshots under `audit_screenshots/`

## 9. Historical closure repair command

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id <run_id> \
  --output-dir <output_dir> \
  --closure-historical-repair \
  --operator-approved-full-live-run
```

### Public write risk

- yes; edits/deletes exact historical social records

### Safe while paused?

- no; future pause design must explicitly block this unless separately authorized

### Produced files

- `historical_repair_plan_v1.json`
- `linkedin_historical_integrity_v1.json`
- `threads_exact_deletion_receipts_v1.json`
- `facebook_copy_repair_v1.json`
- `historical_repair_result_v1.json`

## 10. Release verifier command

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id <run_id> \
  --output-dir <output_dir> \
  --closure-release-verify \
  --closure-generic-result <generic_result.json>
```

### Public write risk

- none

### Safe while paused?

- yes

### Produced files

- `final_release_readiness_v1.json`

## 11. Release tag finalizer command

### Command shape

```text
python -m live_contentops.eight_platform_substack_first_pipeline_v1 \
  --run-id contentops-v1.0.0 \
  --output-dir <closure_dir> \
  --finalize-v1-tag \
  --operator-final-acceptance ACCEPT
```

### Public write risk

- no platform write, but **git tag + push**

### Safe while paused?

- no

### Produced effects

- creates and pushes `contentops-v1.0.0`

## 12. Existing video/media commands

## 12.1 Video capability audit

### Command

```text
python -m live_contentops.video_platform_capability_matrix_v1 --output <json>
```

### Module

- `live_contentops/video_platform_capability_matrix_v1.py`

### Produced file

- `video_platform_capability_matrix_v1.json`

### Public write risk

- none

### Safe while paused?

- yes

### Relevant tests

- `tests/test_video_platform_capability_matrix_v1.py`

## 12.2 Local chart-sequence video renderer

### Command

```text
python -m live_contentops.source_chart_short_video_v1 \
  --chart <path1> --chart <path2> --chart <path3> \
  --output <mp4>
```

### Module

- `live_contentops/source_chart_short_video_v1.py`

### Produced file

- local MP4 only

### Public write risk

- none

### Safe while paused?

- yes

### Relevant tests

- `tests/test_source_chart_short_video_v1.py`

### Common failure modes

- missing charts
- missing FFmpeg
- FFmpeg nonzero output

## 12.3 Hidden/indirect video dispatch paths present in code

These are not wired into the default text/image runner, but they do exist and must remain explicit-mode only:

- `live_contentops.edge_cdp_publishing_adapter_v1.publish_youtube_short_via_edge`
- `live_contentops.edge_cdp_publishing_adapter_v1.publish_tiktok_video_via_edge`
- `live_contentops.edge_cdp_publishing_adapter_v1.edit_youtube_video_metadata_via_edge`
- `live_contentops.edge_cdp_publishing_adapter_v1.set_youtube_video_public_via_edge`

Phase 2 must ensure any new canonical video runner is the only supported entrypoint for these capabilities.

## 13. Important hidden or indirect dispatch paths to guard in Phase 2

A future lane lock must consider all of these, not just the top-level live run:

- default canonical public text/image run
- `--resume-derivatives`
- `--reconcile-linkedin-pair`
- `--closure-historical-repair`
- any direct invocation of browser adapters from future helper modules

Read-only safe paths that should remain available:

- `--prepare-generic-fabric`
- `--build-operator-audit-packet`
- `--reconcile-readbacks`
- `--closure-release-verify`
- video capability audit
- local chart-sequence rendering

## 14. Phase 2 command-shape implication

Phase 2 is not authorized by this Phase 1 closeout.

Do **not** add video to the default text/image command.
Instead, add a dedicated canonical video runner with explicit modes such as:

- local proof render only
- request-builder only
- provider-ready metadata bundle only
- future explicit upload mode behind lane lock and separate authorization

That keeps existing command surfaces comprehensible and preserves the default YouTube Community text/image contract.
