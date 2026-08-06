# ContentOps V6/Post-v1 Next Task Pointer

## Current pointer

Current product-direction classification:

`CONTENTOPS_NEWSROOM_AND_CONTENT_FACTORY_SCOPE_OWNER_APPROVED`

Jim approved the final ContentOps product plan on 2026-08-06. No further owner approval is required to start the task below.

Current durable prerequisite status:

`COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE`

Wave 02 — the durable operational store and canonical state machine — is complete, merged into `master`, and accepted as the minimum durable prerequisite. Do not redesign, re-audit, retest, or re-merge it.

### Required next action

`TASK_CONTENTOPS_CORE_V0_REPEATED_SHADOW_SOAK_AND_RECOVERY_V1`

This is the current routing authority. Work package D passed independent audit
`PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE` and is fast-forward merged into `master`, so
work package D status is `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT` and this task — work
package E — is `READY_NOT_STARTED`.

Work package C (dual-lane CORE V0 shadow newsroom) is complete, accepted, and fast-forward
merged into `master` with a truthful caveat. Its status is
`COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`, independent audit
`PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE`, accepted implementation commit
`6dc38ed32d2c55ebe63314d3cddfef3da34bbb4e`, accepted canonical correction commit
`c8d6837368dee37e73c807e897cc751e37210801`. Do not re-audit, retest, or re-merge it.

Work package D is accepted and fast-forward merged into `master` from branch
`agent/contentops-core-v0-diversity-seo-image-chart-closure-v1`. Its status is
`COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`, independent audit
`PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE`, accepted source HEAD
`f83bd5c97479ef0001bac141e78d85eacdaa1cc9`, accepted correction commit
`1088bfb82d29d40fba4d3db1e910bf5d292bd522`, merge method `FAST_FORWARD_ONLY`, starting master
`6788298a9592bc6b7e632fd21b35b8b3514a564e`. Do not re-audit, retest, or re-merge it.

The accepted work package D caveats remain truthful: no full-suite PASS is claimed, no CI PASS
is claimed, the full-suite failures are a noisy pre-existing baseline including two
pointer-consistency failures already present at source parent `3166bb69`, and Browser QA has
committed screenshot evidence, hashes, DOM assertions, and zero console/page errors but no
independent pixel-perfect visual PASS.

Work package D extends the same command rather than adding a second runner:

```text
python -m live_contentops.cli core-v0-shadow-demo --evaluation-corpus \
  --store <sqlite> --output <dir>
```

One local command processes a committed governed evaluation corpus of ten cases covering all
nine required domain families across both input lanes. Both lanes now reach a genuine
canonical `PASS` with all eight editorial roles green — the visual-requirement block that
caveated work package C is resolved by a story-type visual-policy resolver plus committed
rights-cleared assets, not by manufacturing an editorial exception. The other eight cases
terminate truthfully as review-blocked, permission-blocked, evidence-blocked,
visual-rights-blocked, duplicate-suppressed, or explicit `NO_PUBLICATION`; no blocked case
reaches `REVIEW_READY`.

Work package D also closes the three Tier-1 destinations CORE V0 reported as unsupported —
`discord`, `instagram_business`, and `threads` — on the same canonical package builder, with
Instagram failing closed when no rights-cleared visual asset exists. One deterministic chart
is produced solely from authorized governed values and passes methodology QA. Browser QA
screenshots are supplied as auditable files at
`docs/automation/CORE_V0_WPD_CLOSURE/browser_qa/`.

### Mode

`SHADOW_ONLY`

### Final build sequence

```text
dual-lane CORE V0 in SHADOW_ONLY   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ diversity, SEO, image, and chart closure   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ repeated shadow soak and recovery   [CURRENT — READY, NOT STARTED]
→ exact authorized live cohort
→ final acceptance and new release identity
```

### Execution boundary

Work package E extends the accepted and merged CORE V0 slice. It runs in `SHADOW_ONLY` and grants no
credential or environment-value read, provider call, browser/CDP action, network intake,
scheduler/outbox execution, dispatch, publication, or public write. It must not mutate the
Capital Chronicle main project, fabricate numeric or analytical truth, or modify accepted
`v1.0` artifacts.

### Current product-direction authority

- `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`
- `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/FINAL_PRODUCT_SCOPE_OVERLAY_V2.md`
- `docs/automation/CONTENTOPS_FINAL_PRODUCT_SCOPE_CLOSEOUT_AND_LAUNCH_MASTER_PLAN_V1.md`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`

### Superseded automatic routing

The older automatic Wave 03 sequence is no longer the current next-task authority. Approval-envelope, transactional-outbox, and expiry work is revisited only when the CORE V0 vertical slice or a launch gate directly requires it. Wave 03 language retained in historical plans and ledgers below remains historical program lineage, not current routing.

## Historical program lineage

The sections below are retained as accepted program lineage. They are not the current pointer.

Latest accepted historical release:

`TASK_CONTENTOPS_V1_0_FINAL_AUCTION_LOGIC_REPAIR_ACCEPTANCE_AND_TAG_V1`

Accepted release classification:

`PASS_CONTENTOPS_V1_0_OPERATOR_ACCEPTED`

Accepted master operational classification:

`PASS_WAVE01_CANONICAL_ORCHESTRATOR_BOUNDARY_ACCEPTED_AND_MERGED`

Historical correction classification:

`PASS_WAVE01_CANONICAL_ORCHESTRATOR_ENFORCEMENT_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

Historical Wave 01 worker classification:

`PASS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1_AWAITING_INDEPENDENT_AUDIT`

Completed Wave 01 acceptance task:

`TASK_CONTENTOPS_WAVE01_ACCEPTANCE_MASTER_MERGE_AND_CLI_COVERAGE_RECONCILIATION_V1`

Working branch:

`master`

Pre-merge target master HEAD:

`a0c9d0a67e39c614d5a80cd758f219dcac9b11ff`

Accepted source HEAD:

`7d7d55039a68b4dbaec631ac75af6b7e418f7500`

Merge commit:

`d5c53655435e8340b3b79ddc3779e1f833eeb311`

Accepted master HEAD before Wave 01 reconciliation:

`5c90e6d243b705f74cac40547083565f4899197b`

The independent audit accepted the executable Wave 01 boundary for merge. The post-merge acceptance commit reconciled minor test/evidence coverage to exhaustively cover all 12 mutation-capable CLI argument families.

### Historical Wave 02 record

Completed Wave 02 task:

`TASK_CONTENTOPS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_V1`

Wave 02 worker classification:

`PASS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

Wave 01 Status: `COMPLETE_ACCEPTED_AND_MERGED`
Wave 02 Status: `COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE`

Wave 02 implemented the SQLite WAL durable store, schema version 4, lineage metadata, event envelope v1, hash-chain replay, WAL-safe backups, and external-writer threat boundaries. Migrations verify and roll back on failure, and the canonical JSON encoder is shared by the migration writer and the replay verifier so writer and verifier hashes cannot diverge.

Byte-exact evidence verification depends on JSON files being stored and checked out with LF line endings. This is enforced by `.gitattributes` (`*.json text eol=lf`), never by normalising bytes inside verification code.

### Historical horizontal hardening routing

The earlier institutional hardening plan routed Wave 03 to exact approval envelopes, the transactional outbox, and expiry enforcement. That routing is superseded by the owner-approved final product plan and is not the current next task. The historical Wave 03 task identity is retained in the institutional hardening plan and maturity ledger, not in this current pointer.

## Preserved boundaries

- no unauthorized provider, browser/CDP, platform, scheduler, dispatch, publication, or public write;
- no raw credential or session access;
- no fabricated numeric or analytical truth;
- no mutation of the Capital Chronicle main project;
- no modification or retagging of accepted `v1.0`;
- no second runner, state store, approval engine, outbox, scheduler, provider gateway, dashboard, or analysis engine.
