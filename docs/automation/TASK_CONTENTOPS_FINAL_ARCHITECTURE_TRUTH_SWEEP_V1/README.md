# TASK_CONTENTOPS_FINAL_ARCHITECTURE_TRUTH_SWEEP_V1

Classification: `PASS_FINAL_ARCHITECTURE_TRUTH_SWEEP_COMPLETE`

This is a non-authoritative, evidence-only architecture archaeology packet. It does not implement
product code, rewrite current authority, mutate runtime/store/browser state, change a Codex
Automation, or perform a public write.

## Repository truth

- repository: `fatcat2109/capital-chronicle-contentops`;
- task-start expected/observed remote master:
  `f7c5543e08381f7f529e1b391a80a59f2032d76f`;
- evidence branch: `codex/final-architecture-truth-sweep-v1`;
- evidence worktree:
  `A:\Capital Chronicle\Worktrees\ContentOps\final-architecture-truth-sweep-v1`;
- protected `v1.0` was not moved, rerun, or modified;
- product code and current authority files were not modified.

`remote_master_truth.json` records the fetched master parents, first-parent lineage, all PRs exposed
by GitHub, and remote-branch counts. The final remote ref/commit is recorded after the last fetch in
the final manifest.

## Scope accounted

- 149 fetched `origin/*` branch refs; 58 contain commits not in current master;
- GitHub PRs 1–17, including frozen open PR #12 and merged PR #17;
- primary clone: 108 worktrees, 117 local branches, two stashes, 33 reflog-only commits, 43
  unreachable commits, and zero commits reachable only locally and absent every remote;
- duplicate full clone at `A:\Capital Chronicle\tools\cc-live-contentops`: six worktrees, 32 local
  branches, eight stashes, 57 reflog-only commits, 243 unreachable commits, and two commits absent
  every remote;
- all dirty worktrees, tracked modifications, visible untracked roots, ignored `.task-runtime` and
  `artifacts` roots, and the material uncommitted V2 implementation;
- current production SQLite schema/count/state metadata, runtime/output roots, supported V1
  Automation inventory, and sanitized process/listener truth;
- current CodeGraph coverage plus intentional exclusions and branch/runtime blind spots.

The duplicate clone's two local-only commits are product-subsumed by current master; its original
durable-store evidence files are already present, mostly byte-identical, while current code/tests
have evolved. No local commit recovery is required.

## Capability totals

| Classification | Count |
| --- | ---: |
| `CURRENTLY_PROVEN_AND_REUSE` | 34 |
| `HISTORICALLY_PROVEN_CURRENT_REVALIDATION_ONLY` | 9 |
| `CURRENT_HOST_RUNTIME_PROOF_REQUIRED` | 7 |
| `NEW_IMPLEMENTATION_GAP` | 3 |
| `SUPERSEDED_DO_NOT_REUSE` | 6 |
| **Total** | **59** |

Every material capability has exactly one row in `capability_matrix.json`. The three true new
implementation gaps are:

1. V1 quota-efficient batch/tail discovery;
2. selective current-master reconciliation of branch-proven V2 substrate;
3. an integrated V2 qualification/observation/bounded-learning loop.

## Most material findings

1. Current master already contains a real owner-scoped nine-surface canary at `5327be9`, all nine
   reconciled with `UNKNOWN_WRITE=0`; current V3 plan wording still routes as if publication were
   pending.
2. Production-day accounting and bounded catch-up are implemented and were used by a real four-
   opportunity 4/32 proof at `d763ae1`; the proof failed truthfully at `0/4 / 0/32` after 40
   distinct stories.
3. The later evidence foundation at `330f197` produced four distinct evidence-ready candidates and
   fixed source-route/redirect/worker-transport gaps, but its 35 URL-discovery calls consumed
   10,237,897 tokens. The capability is reusable; the per-trigger production default is not.
4. Exactly four native V1 Automations currently exist and are paused with correct model/effort/
   schedules. Their prompt hashes remain different from the configured intent; calendar-time
   execution is unproven.
5. Current master has the V2 free-form/package/publication substrates, while the 48-commit
   `task/v2-native-staggered-automation-relay-shadow-correction-v1` lineage holds proven unattended,
   Windows-recovery, locale, read-only-trigger, and native-relay capabilities absent from master.
6. The material uncommitted V2 breaking-news tree is incomplete and authority-incompatible; it
   should not be revived wholesale.
7. CodeGraph is current by deterministic source digest, but intentionally cannot see Git topology,
   runtime/store/Automation truth, actual media, broad historical packets, or the accepted V2 donor
   lineage.

## Runtime/host snapshot

The production store was opened via SQLite URI `mode=ro` only:

- `quick_check=ok`;
- 31 physical tables; schema version 78; WAL observed;
- 9 destination-readiness rows, all identity-matched and in a ready state;
- `UNKNOWN_WRITE=0`;
- 31 platform-dispatch rows and 31 reconciliation rows;
- 97 performance observations and 11 learning-policy versions, one active.

At the observation epoch no matching Daily App process and no port-5174 listener existed. This is
a truthful at-rest snapshot, not a cold-start/unattended PASS.

## Packet map

- `remote_master_truth.json` — fetched master/parents/lineage/PR summary;
- `local_repo_topology.json` — both clones, worktrees, dirty paths, stashes, reflogs, unreachable
  objects, and sanitized fingerprints;
- `local_remote_delta_matrix.json` — complete local/remote branch divergence and any-remote
  reachability;
- `capability_matrix.json` — 59 exactly classified material capabilities;
- `historical_proof_index.json` — compact capability-to-branch/commit/evidence map;
- `runtime_host_truth.json` — sanitized runtime/store/Automation/process/CodeGraph metadata;
- `duplicate_orphan_matrix.json` — duplicate, orphan, branch-only, and quarantined systems;
- `authority_conflict_matrix.json` — exact stale/current conflicts and lock actions;
- `codegraph_coverage_gap.json` — what the graph sees/excludes and the bounded improvement;
- `MASTER_PLAN_LOCK_INPUT.md` — owner-facing answers and shortest capability roadmap;
- `evidence_manifest.json` — final hashes, validation, and mutation/safety receipt;
- `collect_evidence.py` — reproducible sanitized collector used for the dynamic JSON files.

## Safety receipt

- production/store mutation: `0`;
- browser/CDP/session interaction: `0`;
- public/provider write: `0`;
- Automation create/update/enable/delete: `0`;
- fifth Automation: `0`;
- Capital Chronicle mutation: `0`;
- V2 publication authority expansion: `0`;
- secrets/cookies/tokens/session/private-key reads: `0`;
- product-code edits: `0`;
- current authority edits: `0`.

Sensitive locations, where relevant to topology, are represented only as
`SENSITIVE_PATH_NOT_READ`.
