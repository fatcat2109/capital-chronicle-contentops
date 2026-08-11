# ContentOps V1 first real 5–8 article production day

Task: `TASK_CONTENTOPS_V1_FIRST_REAL_5_8_ARTICLE_PRODUCTION_DAY_V1`

Result: `NO_PUBLICATION_GOVERNED_EVIDENCE_BLOCK`

This was the first owner-authorized real V1 newsroom production-day run in
`AUTONOMOUS_DEFAULT`. It used the canonical Daily App supervisor, the durable schema-9
store, the continuous rolling-X intake lane, the hierarchical assignment/preselection
seam, and the canonical publication gates. It did not use the quarantined
`POST /api/run-pipeline`, a second runner, or any Tier-2/video path.

## Outcome

Three sequential opportunities completed: two durable `OPERATOR_REQUESTED` Run Now
decisions and one scheduled noon decision. The first exposed and safely stopped on a
local public-facade signature defect; the bounded reversible fix was committed and pushed
before the next decision. The second stopped during leaf assignment after bounded router
fallback exhaustion. The scheduled decision completed assignment, story routing, and
preselection, then stopped before targeted evidence because all 12 ranked stories were
evidence-blocked. No article, visual, platform package, adapter call, public dispatch,
public object, unknown write, or readback/reconciliation was created by this task.

The 5–8 band is a target, not a filler quota. Publishing zero was the correct governed
result because evidence gates did not pass.

Machine-readable evidence is in [production_day_evidence_v1.json](production_day_evidence_v1.json).

## Demo / verification path

1. Keep the canonical Daily App running from `Start_ContentOps_Daily_App.cmd`.
2. Open `http://127.0.0.1:5174/api/daily-app/snapshot` and verify
   `AUTONOMOUS_DEFAULT`, `HEALTHY`, kill switch clear, no active cycle, zero unknown or
   pending readbacks/recovery, and published-today count `0`.
3. Inspect the three immutable output directories recorded in the JSON evidence. The
   scheduled decision contains intake, 16-leaf assignment, preselection, story routing,
   ranked viability, and cycle-evidence artifacts; its terminal reason is
   `ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED`.

## Measured utility and bounded cost

- Rolling intake accepted 989 headlines at the start and 1,033 unique headlines in the
  final live snapshot; the scheduled decision accepted 1,023 source-event-time-valid
  headlines from 3,929 source rows.
- The scheduled decision produced 16 leaf partitions, 718 leaf clusters, a valid 12-item
  preselection shortlist, and zero dropped/duplicated/unknown IDs. All 12 ranked stories
  were `BREAKING_NEW_STORY` / `BREAKING_BRIEF`; 11 update chains were incremental and one
  was a duplicate.
- Decision 2 used 14 logical router calls, 19 provider attempts, 4 fallback transitions,
  and 1,033,832 tokens. Decision 3 used 18 logical calls including routing, 23 provider
  attempts, 3 fallback transitions, and 1,452,475 tokens. Provider cost metadata was
  unavailable; no secret or credential value was persisted.
- The only source change was the canonical facade forwarding the supervisor's already
  accepted operating-mode, published-memory, Capital Chronicle catalog, and readiness
  arguments, plus a regression test. It is commit
  `6f8a1788f094c607896b8304161dfea783a20c64`, verified on remote `master`.

## Next blocker

The next viable production opportunity requires genuinely fresh ranked stories with
launch-supported, point-in-time official evidence documents and the required evidence
capabilities (including authority, timeline, affected entities, filings/releases, and
market snapshots where applicable). Do not weaken those gates or manufacture a post.

The durable FDA-G calendar-time soak remains active and is not accepted by this task.
