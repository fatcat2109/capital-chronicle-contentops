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

## Completeness correction A

Correction source HEAD: `b943614916e10bbae37fd092d0046c457638d93f`.

An exhaustive bounded filesystem/Git scan replaced the original collector's assumption that its
two named clone roots were exhaustive. The scan encountered 266 candidate Git roots under
`A:\Capital Chronicle`, identified 157 nonmatching repositories without inspecting their contents,
and found 109 ContentOps candidate roots that deduplicate to exactly two Git common directories.
Those two common directories register exactly 114 worktrees, including five primary-clone
worktrees outside the `A:` scan root that were discovered through supported `git worktree list`
readback. No additional ContentOps clone/common-dir or registered worktree was found relative to
the original packet.

Remote/tag correction truth:

- original sweep epoch: 149 fetched `origin/*` refs before this evidence branch existed remotely;
- correction epoch: 150 fetched refs;
- the sole addition is `origin/codex/final-architecture-truth-sweep-v1` at the accepted evidence
  commit; genuine product-branch drift is zero;
- the repository has one tag, annotated `refs/tags/v1.0`;
- its peeled commit is exactly `6983bfb3ef300414b744f3f8f97ca81ff699348b`;
- no other materially unique tag lineage exists.

Ignored-material correction truth:

- 1,249 collapsed ignored paths were enumerated across all 114 registered worktrees using Git's
  ignored-file facilities;
- 1,121 were pruned as ordinary dependency/build/cache/transient bulk;
- 128 material ignored entries survived the filter and all 128 were reviewed/dispositioned;
- three ignored `.env` paths were recorded only as `SENSITIVE_PATH_NOT_READ`;
- ignored runtime/evidence roots, generated UI configuration/epoch files, local CodeGraph databases,
  and historical/current product source-asset roots exposed no new material architecture;
- the known 30,119,681-byte documentary asset was observed through eight worktree/runtime aliases
  resolving to two physical identities, every observed copy carrying SHA-256
  `01a1d3b34fb1c812a769fabe480f976640684158dc5b94e750a72c2d3d4eb998`.

The asset is a legitimate ignored runtime/test dependency and a clean-checkout portability caveat.
It does not change `V2_03_FREEFORM_REMOTION_SUBSTRATE`; current dependency-root/render proof remains
required after V2 reconciliation.

Both commits absent all fetched remotes remain the already-known duplicate-clone commits. Both were
reviewed path-by-path and remain fully product-subsumed/superseded; no recovery is authorized.

Correction conclusion:

- capability rows changed: `0` — total remains 59;
- classification totals changed: `0`;
- `NEW_IMPLEMENTATION_GAP` rows changed: `0` — the same three gaps remain;
- V1 roadmap ordering changed: `false`;
- V2 donor/reconciliation conclusion changed: `false`;
- `MASTER_PLAN_LOCK_INPUT_REMAINS_VALID_UNCHANGED`.

Exact completeness counters are all zero:

- `unaccounted_matching_git_common_dir_count=0`;
- `unaccounted_registered_worktree_count=0`;
- `unreviewed_material_ignored_path_count=0`;
- `unreviewed_local_only_commit_count=0`;
- `unclassified_material_capability_count=0`.

The prior `185 passed / 1 failed` test result was not rerun because product code is unchanged. It is
retained only as `BUILDER_REPORTED_PREVIOUS_RUN_NOT_REEXECUTED_IN_CORRECTION`. Exact current
commands, timestamps, exit codes, output digests, structured scan receipts, and staged-diff evidence
are recorded in `validation_receipt.json`.

Correction artifacts:

- `collect_completeness_correction_a.py` — bounded discovery/ignored/tag/validation collector;
- `workspace_repository_discovery.json` — exhaustive candidate/common-dir/worktree/tag truth;
- `ignored_material_inventory.json` — metadata-first ignored inventory and dispositions;
- `validation_receipt.json` — actual command and structured-operation evidence.
