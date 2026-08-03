# ContentOps Wave 02 — Durable Operational Store & Canonical State Machine v1

Worker Classification:
`PASS_WAVE02_MIGRATION_REPLAY_ASSIGNMENT_AND_EVIDENCE_FINAL_ACCEPTANCE_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

## 1. Executive Summary

Wave 02 establishes the single authoritative SQLite WAL operational store (`ContentOpsDurableStore`) and 29-state canonical state machine for Capital Chronicle ContentOps.

This final acceptance correction task (`TASK_CONTENTOPS_WAVE02_MIGRATION_REPLAY_ASSIGNMENT_AND_EVIDENCE_FINAL_ACCEPTANCE_CORRECTION_V1`) closes the remaining durable-authority blockers:

- Semantic migration checksums bind SQL SHA-256, transform version, and canonical transform source hash.
- Populated v1 histories migrate through production v2/v3 logic with deterministic ordering, lossless row/hash proofs, fail-closed ambiguity handling, and usable final projections.
- One canonical event envelope/verifier covers genesis, migration, transitions, and replay; an internal connection-local append gate rejects direct SQL inserts.
- Receipt-backed artifacts require independently resolved immutable bytes/object evidence and carry explicit `WORK_ITEM_EXACT`, `STORY_EXACT`, or `GLOBAL_REUSABLE` reuse scope.
- Fake-clock lease, assignment, heartbeat, release, expiry, and reclaim semantics preserve monotonic fencing and exactly one ACTIVE assignment per work item.
- The orchestrator owns explicit output and restart contracts, deterministic output canonicalization, truthful blocked events, and explicit pending-work resume decisions.
- The state-surface inventory contains 12 AST/import-verified rows with real readers, writers, dispositions, and superseding durable entities.

## 2. Base Authority & Commit Roles

- Accepted master authority: `origin/master` at `c87e338f25922f4d03454ba199139353ca7198ff` (Wave 01 accepted/merged).
- Final-correction starting branch HEAD: `615a96fb20aa97fd76bb3343e9150daec40d9031`.
- Candidate branch: `agent/contentops-wave02-durable-operational-store-v1`.
- Candidate status: `COMPLETE_AWAITING_INDEPENDENT_AUDIT`; this branch is not merged authority.
- Completing commit SHA: `null` until the required final commit is created.
- Schema version: `3`.

## 3. Validation Summary

- Final focused Wave 02 suites: **32 passed** (`28` store/resilience + `4` Wave 02 authority/evidence).
- Compatibility/quarantine/closure suites: **110 passed** (`38` quarantine + `65` compatibility + `7` closure).
- Master-byte Wave 01 suite: restored exactly to `origin/master`; **4 passed, 1 expected branch-role failure** because that historical suite requires Wave 02 to remain the next not-started task.
- Aggregate final candidate PASS count used by the packet: **142 passed**; the role-conflicting Wave 01 assertion is disclosed separately and is not reported as a candidate PASS.
- Monolithic repository suite: **not run**.
- CI/status checks and workflow evidence: **not run / not available in this local correction**.
- Compilation, JSON parsing, diff hygiene, protected-boundary, and secret/machine-path/mutable-database scans are recorded in `validation_results.md` after final execution.

## 4. Authority Boundary and Required Next Action

Wave 02 performs no approval grant, outbox dispatch, platform publication, provider call, browser/CDP action, credential read, network fetch, or public write. Schema-ready Wave 03+ tables grant no live authority.

Required next task after independent acceptance:
`TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1`

Wave 03 remains `NEXT_NOT_STARTED`.
